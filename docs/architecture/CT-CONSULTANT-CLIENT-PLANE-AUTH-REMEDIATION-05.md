# CT-CONSULTANT-CLIENT-PLANE-AUTH-REMEDIATION-05

**Server-side client-access ceiling on the Organisation plane (writes + uploads),
UI reflection, and removal of the "V3" product tag from user-facing branding**

- **Date:** 2026-10-08
- **Status:** Implemented and tested — **READY FOR INDEPENDENT VERIFICATION**
  (not PO acceptance; see §24)
- **Follow-up:** gap **G-1** (§23.1) — the ceiling for the remaining two ratified
  operations, `approve_final` and `correct_submitted_data` — was closed on
  2026-10-08 by **CT-CONSULTANT-CLIENT-PLANE-AUTH-CLOSURE-05A**
  (`docs/architecture/CT-CONSULTANT-CLIENT-PLANE-AUTH-CLOSURE-05A.md`, summarised in
  §25 of this document).
- **Ratified basis:**
  - `docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md` §8.1 / §8.2 / §8.3
    (P-1..P-9, P-6 *server-side*) and §16 (the named failure mode);
  - `docs/architecture/CT-CONSULTANT-PLATFORM-DECISION-REGISTER-02.md` §1
    ("frontend controls never substitute for backend authorization");
  - `Research/CT-CONSULTANT-MODEL-UIUX-DESIGN-01` §8 ("Plane C … is Plane B
    rendered for the client's own users … Planes B and C are the same
    Organisation surface, not two products");
  - `backend/domain/relationship_access.py` (CT-CONSULTANT-MODEL-IMPLEMENTATION-03)
    — the profile/state capability matrix, reused unchanged;
  - AGENTS.md §7, §17, §25, §44, §45, §65, §70, §72, §73, §74, §75.

---

## 1. Problem

A consultant-managed client is an organisation whose users reach the **same**
Organisation product surface a direct customer uses (PO-CONSOLIDATION-01 §8.3:
"Planes B and C are the same Organisation surface"). Its effective access is a
ceiling:

```
RELATIONSHIP ∩ CLIENT ACCESS PROFILE ∩ CLIENT ROLE ∩ ENTITLEMENT
```

Before this task the **profile** term of that ceiling was enforced **only** on
the separate Plane C route family (`/api/v3/portal/{clientId}/*`, guarded by
`api/client_portal_auth.py`). The Organisation plane had no profile ceiling at
all, so an `organization_members` row on a consultant-managed organisation
(a client Organisation Owner, `role = org_owner`) passed the ordinary
member/admin guards and could:

1. **upload documents** — `POST /api/v3/documents/upload-url` issued a signed
   storage URL to a MANAGED client;
2. **write master data** — create/update/delete facilities, assets and vehicles
   on the organisation plane;
3. see the master-data and upload affordances offered in the UI;

regardless of the relationship's access profile or state. This is exactly the
failure mode PO-CONSOLIDATION-01 §16 names: *letting a consultant-managed client
inherit direct-customer assumptions inside the authorization layer*.

In the same surface the authenticated shell still displayed the internal
iteration tag **"V3"** next to the product name, which is an implementation
detail with no business meaning for a customer, consultant or client (AGENTS.md
§75).

---

## 2. Ratified authority for the decision

No new business policy was invented. The permitted operation set is the
**already-ratified** matrix in `backend/domain/relationship_access.py`
(§8.2 post-PO amendments, incl. PO-9), which this task reuses byte-for-byte:

| operation | OFF | READ_ONLY | COLLABORATIVE | MANAGED |
| --- | --- | --- | --- | --- |
| `read_data` / `read_reports` / `read_evidence` | ✗ | ✓ | ✓ | ✓ |
| `comment` | ✗ | ✓ | ✓ | ✓ |
| `upload_document` | ✗ | ✗ | ✓ | ✗ |
| `edit_master_data` | ✗ | ✗ | ✓ | ✗ |
| `correct_submitted_data` | ✗ | ✗ | ✓ | ✗ |
| `approve_final` | ✗ | ✗ | ✓ (also client-role gated) | ✗ |
| `map_factors` / `edit_mappings` / `recalculate` | ✗ (**PO-9, every profile**) | ✗ | ✗ | ✗ |

State rules (§8.1 / §15 PA-1..PA-7): everything requires `active`; the retained
(post-relationship) state is read-only; a pending/suspended/ended-without-
retention relationship grants nothing.

Therefore the CT-05 work is an **authorization-enforcement** task, not a policy
task: the ceiling already existed, and it was simply not applied to this surface.
## 3. Root cause

| # | Cause | Evidence |
| --- | --- | --- |
| RC-1 | The profile ceiling was implemented in **one** plane only. `api/client_portal_auth.py` bounded `/api/v3/portal/{clientId}/*`; the Organisation plane routes never consulted it. | `grep -rn 'profile_allows' backend/` before the change resolved to the portal auth + policy module only. |
| RC-2 | The Organisation plane authorises by **role** (`require_org_member` / `require_org_admin` / `require_permission`) and by **tenant scope** (`ensure_org_access`). Role and tenant are *necessary but not sufficient*: they cannot see the consultant relationship, so a client Organisation Owner is indistinguishable from a direct-customer Owner. | `api/upload_gate.py::authorize_org_upload`, `api/v3_organizations.py` master-data routes. |
| RC-3 | The relationship→profile fact lives on the consultant plane (`consultant_clients.client_access_profile`), which the Organisation plane never loaded. | `backend/data/consultants.py::get_relationship_for_org` existed but had no Organisation-plane caller. |
| RC-4 | Two surfaces with two policy implementations would drift, so the fix had to route the Organisation plane through the **same** pure policy module Plane C uses. | `backend/domain/relationship_access.py`: "a profile can only ever REDUCE what is permitted". |
| RC-5 | The client-access view was not exposed to the frontend, so the UI could not reflect a ceiling it was never told about. | `/api/v3/me/context` returned no capability view. |

---

## 4. Design — the ceiling (never a grant)

`backend/api/client_access_guard.py` (**new**) is the single Organisation-plane
ceiling. Its contract:

- **Resolve from authoritative rows only.** `resolve_client_ceiling()` returns a
  `ClientAccessCeiling(organization_id, profile, state, relationship_id)` built
  from `ConsultantsRepository.get_relationship_for_org(org_id)` →
  `normalise_profile(client_access_profile)` and
  `resolve_relationship_state(status, retained_read_only)`. Client input is never
  trusted and no capability is derived from the request.
- **It applies to exactly one actor class.** It returns `None` (no ceiling, i.e.
  unchanged behaviour) when:
  - the caller is internal CarbonTally staff (`is_internal_staff`) — they keep
    their operational cross-organisation bypass;
  - the caller is Processing Entity staff (`is_entity_staff`);
  - the caller is not an organisation member (`is_org_member` false) — the
    **consultant principal** case (admitted via `managed_org_ids`) and every
    staff identity;
  - the caller is an org member but the addressed organisation is **not** their
    own `organization_id` — a foreign organisation is decided by the pre-existing
    tenant guards (`ensure_org_access` / `enforce_org_path_scope`), never here;
  - the organisation has **no** `consultant_clients` row — a direct customer is
    unaffected by construction.
- **Fail closed, but only where it applies.** `enforce_client_operation()` raises
  `403` with the non-technical `CLIENT_OPERATION_DENIED_DETAIL` ("Your client
  access level does not permit this action") when, and only when, a ceiling
  exists and `profile_allows(operation, profile, state)` is false. Unknown or
  absent profiles normalise to `off`, never to the most permissive profile.
- **Identical policy object as Plane C.** Both planes call
  `domain.relationship_access.profile_allows()`; the surfaces cannot drift.
- **It never touches RLS**, never elevates to service role, and grants nothing
  the pre-existing member/admin guards did not already require.

### 4.1 Dependency factory

```python
require_client_operation("edit_master_data")
```

returns a FastAPI dependency that resolves the ceiling against the caller's own
`organization_id` — the only organisation that can be a consultant-managed
client for them — and is bound as `Depends(require_client_operation(<op>))`
(evaluated once, mirroring the `require_org_member` no-parentheses hazard).
Binding to the caller's *own* organisation is what makes the guard structurally
incapable of affecting a consultant, internal/PE staff or a direct customer.


---

## 5. Design — server-side enforcement points

Every Organisation-plane **write/upload** route an organisation member can reach
is now bounded. The ceiling is evaluated **before** any storage or persistence
work, so a denied request cannot leave a side effect (no orphan object, no row).

### 5.1 Uploads — `operation = "upload_document"`

`api/upload_gate.py::authorize_org_upload()` (the single chokepoint every
organisation upload path already went through) now calls
`enforce_client_operation(current_user, repos, organization_id,
"upload_document")` **after** the viewer read-only check, the org-scope check and
the role resolution, and **before** the `UploadActor` is returned. A denial is
recorded through the existing `_deny()` audit helper with
`action_reason="client access profile does not permit upload_document"`.

Routes covered because they route through this gate:

| Route | Plane |
| --- | --- |
| `POST /api/v3/documents/upload-url` | V3 documents (signed upload URL) |
| legacy `/api/documents/upload*` family | legacy document upload |
| `POST /api/v3/manual-extraction/*` upload paths | manual extraction |

The gate is deliberately the *shared* function rather than a per-route
decorator: a future upload route that reuses it inherits the ceiling
automatically (fail-closed by construction).

### 5.2 Master data — `operation = "edit_master_data"`

Bound directly on each write route via
`Depends(require_client_operation("edit_master_data"))`:

| Route | Handler |
| --- | --- |
| `POST /api/v3/organizations/{org_id}/facilities` | `add_facility` |
| `PUT /api/v3/organizations/facilities/{facility_id}` | `update_facility` |
| `DELETE /api/v3/organizations/facilities/{facility_id}` | `remove_facility` |
| `POST /api/v3/organizations/{org_id}/assets` | `add_asset` |
| `PUT /api/v3/organizations/assets/{asset_id}` | `update_asset` |
| `DELETE /api/v3/organizations/assets/{asset_id}` | `remove_asset` |
| `POST /api/v3/vehicles` | `add_vehicle` |
| `PUT /api/v3/vehicles/{vehicle_id}` | `update_vehicle` |
| `DELETE /api/v3/vehicles/{vehicle_id}` | `remove_vehicle` |

Reads are **not** gated: every read operation is admitted by every profile except
`off`, and the `off`/retained cases are already bounded on the identity side
(`api/client_portal_auth.py`, CT-CONSULTANT-CLIENT-IDENTITY-04). Gating reads here
would duplicate policy and risk denying a legitimate direct customer.

### 5.3 Explicitly NOT changed

- **RLS** — no policy was altered, added or disabled.
- **RLS/service-role usage** — unchanged; the ceiling runs inside the normal
  authenticated request path.
- **Consultant, staff and PE paths** — `authorize_consultant_upload()` and every
  staff/PE entry point are untouched; their guards are unchanged.
- **Existing audit behaviour** — denials reuse the established `_deny()` recorder.
- **The remaining two matrix operations** — at the time of CT-05 they were left
  unbound (§23.1 G-1). They are now bound by
  **CT-CONSULTANT-CLIENT-PLANE-AUTH-CLOSURE-05A** on five Organisation-plane routes
  (`…/items/{id}/customer-review` and `…/jobs/{id}/review` for `approve_final`;
  `…/items/{id}/extract`, `…/jobs/{id}/confirm` and
  `PUT /api/v3/manual-extraction/items/{id}` for `correct_submitted_data`). See §25.
  RLS, migrations and the `/me/context` contract remain untouched by that closure.

---

## 6. Design — the `/me/context` client_access contract

`GET /api/v3/me/context` gained an additive, optional object:

```jsonc
{
  "destination": "…",
  "organization": { "id": "…", "name": "…", "role": "org_owner" },
  "client_access": {
    "profile": "managed",
    "state": "active",
    "capabilities": {
      "read_data": true, "read_reports": true, "read_evidence": true,
      "comment": true, "upload_document": false, "edit_master_data": false,
      "correct_submitted_data": false, "approve_final": false,
      "map_factors": false, "recalculate": false
    }
  }
}
```

- The key is **absent** (not `null`-filled) whenever the ceiling does not apply —
  a direct customer, a consultant principal and staff — so existing consumers
  stay byte-compatible and the frontend can treat absence as "no client
  restriction".
- Capabilities are computed by `profile_allows()` per operation, i.e. the same
  function the enforcement path calls, so the view is guaranteed consistent with
  the server decision; it is **not** a second policy engine.
- The view contains **no** cross-tenant data: it describes only the caller's own
  organisation and their own relationship profile, both of which the caller can
  already read.

Caveat recorded honestly: `/me/context` is a **convenience** view. It is not an
authorization mechanism, and a client that ignores it gains nothing (§19).

---

## 7. Design — UI reflection (presentation only)

`frontend/src/v3/clientAccess.jsx` (**new**) provides a React context with:

- `available` / `profile` / `state` / `capabilities`;
- `can(operation)` → `capabilities[operation] !== false`.

`V3Layout.jsx` supplies the context from the already-fetched `/me/context`
response (`client_access`), so **no extra request** is introduced, and the
provider wraps the whole authenticated shell.

**Truthfulness rule (AGENTS.md §44).** The context defaults to `UNRESTRICTED`
(`available: false`, `can()` → `true`) for a direct customer, a consultant and
staff, so their surfaces are unchanged. It can only ever *hide* an affordance
whose capability the server has explicitly reported as `false`; it never grants
anything. Hiding a control is UX, not authorization — every hidden action is
independently denied by §5.

Reflected surfaces:

| File | Reflection |
| --- | --- |
| `frontend/src/v3/admin/FacilitiesTab.jsx` | `+ New facility` / `+ New asset` (and their edit/delete affordances) are not offered when `can('edit_master_data')` is false; a read-only explanation ("read-only for organisation master data") is shown instead. |
| `frontend/src/v3/customer/UploadDocumentsPanel.jsx` | The drop-zone and upload controls are not offered when `can('upload_document')` is false; an explanation ("does not permit document upload") is shown instead. |

Both surfaces satisfy AGENTS.md §48: the user is told what is unavailable, why,
and what they can still do (read / comment remain available).

---

## 8. Design — branding: removal of the "V3" product tag

The authenticated shell rendered an internal iteration tag in the primary
navigation next to the product name. "V3" is an implementation detail with no
business meaning for a customer, consultant or client (AGENTS.md §75), so:

- `V3Layout.jsx` no longer renders a `V3` tag; the brand element reads
  **"CarbonTally"** (verified in the browser, §15);
- `frontend/src/OnboardingPage.jsx` brand copy reads "CarbonTally" /
  "Welcome to CarbonTally";
- `frontend/src/v3/admin/AdminPage.jsx` copy no longer exposes "V3".

Scope discipline: only **user-facing** strings changed. `V3` remains in module
paths, CSS class names (`v3-*`), JS identifiers and source comments — none of
these are presented to users, and renaming them would be a large, risk-only
refactor outside this task's mandate. `PEShell.jsx` still renders
`<span className="v3-nav-tag pe-tag">Processing Entity workspace</span>`; that is
a *role* label, not a version tag, and is intentionally retained.

Verification of the claim "no user-facing V3 remains":

```bash
grep -rnE '(CarbonTally ?V3|>V3<|\bV3\b</)' frontend/src --include=*.jsx --include=*.js
```

→ matches **source comments only** (e.g. `// CarbonTally V3 API client — …`);
no rendered string, `<title>`, or nav element contains the literal `V3`.

---

## 9. Security model

| Boundary | Enforcement |
| --- | --- |
| Authentication | Unchanged: Supabase JWT → `get_current_user` (existing). |
| Tenant isolation | Unchanged and *not* replaced: `ensure_org_access` / `enforce_org_path_scope` still run on every route; the ceiling is an **additional** restriction, applied after them. |
| Client-access ceiling | `enforce_client_operation` / `require_client_operation` (§4, §5) — server-side, on the request path, before any write. |
| RLS | Untouched. The ceiling is application-level policy about *which of the caller's own permitted operations are still permitted*, so it cannot leak another tenant's data by construction. |
| Storage | Denied **before** a signed URL is issued (§5.1); no object can be created for a denied client. |
| Consultant plane | Unchanged; the consultant still operates the client through the consultant plane with consultant authority. |
| Internal / PE planes | Unchanged; both are excluded by identity (`is_internal_staff`, `is_entity_staff`). |
| Frontend | Never a boundary. The `clientAccess` context is presentation only; every hidden action is independently denied server-side. |

**Fail-closed properties.**

- An unknown/absent `client_access_profile` normalises to `off` → denies writes.
- An operation name outside `KNOWN_OPERATIONS` is denied
  (`profile_allows` returns `False`), so a new client operation cannot be
  admitted by omission.
- PO-9 operations (`map_factors`, `edit_mappings`, `recalculate`) are denied in
  **every** profile and state, including a client Organisation Owner, and are
  enforced by the same function.

**Why the ceiling cannot restrict the wrong actor.** The ceiling is resolved
against `current_user.organization_id` only. A consultant principal has
`is_org_member == False` for the client organisation (their access is via
`managed_org_ids`, i.e. the consultant plane), so `resolve_client_ceiling`
returns `None` and the guard is a no-op for them. This is asserted by test (§13)
and confirmed end-to-end in the browser (§15: the consultant operating the same
client still sees `+ New facility`).

---

## 10. API surface

| Method | Route | Change | Operation enforced |
| --- | --- | --- | --- |
| `GET` | `/api/v3/me/context` | additive `client_access` object (§6) | — (read-only view) |
| `POST` | `/api/v3/documents/upload-url` | now ceiling-bound via `upload_gate` | `upload_document` |
| legacy | `/api/documents/upload*` | now ceiling-bound via `upload_gate` | `upload_document` |
| `POST` | `/api/v3/organizations/{org_id}/facilities` | ceiling-bound | `edit_master_data` |
| `PUT` | `/api/v3/organizations/facilities/{facility_id}` | ceiling-bound | `edit_master_data` |
| `DELETE` | `/api/v3/organizations/facilities/{facility_id}` | ceiling-bound | `edit_master_data` |
| `POST` | `/api/v3/organizations/{org_id}/assets` | ceiling-bound | `edit_master_data` |
| `PUT` | `/api/v3/organizations/assets/{asset_id}` | ceiling-bound | `edit_master_data` |
| `DELETE` | `/api/v3/organizations/assets/{asset_id}` | ceiling-bound | `edit_master_data` |
| `POST` | `/api/v3/vehicles` | ceiling-bound | `edit_master_data` |
| `PUT` | `/api/v3/vehicles/{vehicle_id}` | ceiling-bound | `edit_master_data` |
| `DELETE` | `/api/v3/vehicles/{vehicle_id}` | ceiling-bound | `edit_master_data` |

**No route was added, renamed or removed**, and **no request/response schema
changed** other than the additive optional `client_access` key (AGENTS.md §65).

### 10.1 Denial envelope

Denials use the platform's existing envelope (not FastAPI's bare `detail`):

```json
{ "error": { "message": "Your client access level does not permit this action" } }
```

with HTTP `403`. Tests assert on `error.message` for this reason.

---

## 11. Data model (migration)

**No migration was required and none was written.**

The ceiling reads facts that already exist from CT-CONSULTANT-MODEL-IMPLEMENTATION-03
(`supabase/migrations/20261103000000_ct_consultant_model_03_client_access_and_mode.sql`):

| Column | Table | Use |
| --- | --- | --- |
| `client_access_profile` | `consultant_clients` | the CAPABILITY CEILING (off / read_only / collaborative / managed) |
| `status` | `consultant_clients` | relationship lifecycle → `resolve_relationship_state` |
| `retained_read_only` | `consultant_clients` | post-relationship read-only retention (PO-10) |
| `organization_id`, `consultant_id` | `consultant_clients` | relationship lookup by organisation (own firm) |
| `role` | `organization_members` | the client ROLE term of the ceiling (unchanged) |

This is the correct outcome under AGENTS.md §66: the existing schema already
supported the requirement, so no column, table or index was added, and no
production-only DDL was performed. `relationship_id` is surfaced in the ceiling
dataclass **for diagnostics only** — it is never trusted as authorization input.

---

## 12. Files changed

| File | Change |
| --- | --- |
| `backend/api/client_access_guard.py` | **new** — the Organisation-plane client-access ceiling (`resolve_client_ceiling`, `enforce_client_operation`, `require_client_operation`, `CLIENT_OPERATION_DENIED_DETAIL`) |
| `backend/api/upload_gate.py` | `authorize_org_upload()` enforces `upload_document` **before** the `UploadActor` is issued; denial recorded via `_deny()` |
| `backend/api/v3_organizations.py` | `Depends(require_client_operation("edit_master_data"))` on facility/asset create-update-delete |
| `backend/api/v3_vehicles.py` | `Depends(require_client_operation("edit_master_data"))` on vehicle create-update-delete |
| `backend/api/v3_context.py` | `_client_access_view()` + additive `client_access` key on `GET /me/context` |
| `backend/tests/unit/api/test_ct_client_plane_auth_05.py` | **new** — 25 tests in 4 classes (§13) |
| `backend/tests/unit/api/fakes.py` | relationship/repository doubles extended so the ceiling can be exercised without a database |
| `backend/tests/unit/api/test_storage_management_step1.py` | **corrected a contradictory fixture seed** that asserted a MANAGED client could upload — the seed contradicted the ratified matrix; the assertion now matches the ratified ceiling (see §23, F-1) |
| `frontend/src/v3/clientAccess.jsx` | **new** — presentation-only capability context (`useClientAccess`, `ClientAccessProvider`) |
| `frontend/src/v3/components/V3Layout.jsx` | provides `client_access` to the shell; brand is "CarbonTally"; the user-facing `V3` nav tag is removed |
| `frontend/src/v3/admin/FacilitiesTab.jsx` | master-data write affordances gated on `can('edit_master_data')`; read-only explanation |
| `frontend/src/v3/customer/UploadDocumentsPanel.jsx` | upload affordances gated on `can('upload_document')`; explanation |
| `frontend/src/v3/admin/AdminPage.jsx` | user-facing copy no longer exposes "V3" |
| `frontend/src/OnboardingPage.jsx` | brand copy reads "CarbonTally" |
| `frontend/src/v3/__tests__/client-access-guard.test.jsx` | **new** — 5 frontend tests (§14) |
| `tools/demo_lab/verify_ct05_client_plane_auth_browser.py` | **new** — headless-Chrome + real-GoTrue end-to-end verifier (§15) |

Explicitly **not** touched: `backend/domain/relationship_access.py` (the ratified
policy is reused verbatim), any RLS policy, any migration, and the consultant /
portal / PE / staff planes.

### 12.1 Addendum — files added by CT-CONSULTANT-CLIENT-PLANE-AUTH-CLOSURE-05A

The following are the **complete** changes of the G-1 closure. They are additive
call sites on the same ceiling plus the frontend reflection of it; the CT-05
entries above are otherwise unchanged.

| File | Change |
| --- | --- |
| `backend/api/v3_processing_workflow.py` | `enforce_client_operation(..., OP_APPROVE_FINAL)` in `customer_review_item`; `enforce_client_operation(..., OP_CORRECT_SUBMITTED_DATA)` in `extract_item` |
| `backend/api/v3_automatic_processing.py` | `enforce_client_operation(..., OP_APPROVE_FINAL)` in `review_job`; `enforce_client_operation(..., OP_CORRECT_SUBMITTED_DATA)` in `confirm_job` |
| `backend/api/v3_manual_extraction.py` | `enforce_client_operation(..., OP_CORRECT_SUBMITTED_DATA)` in `update_item` |
| `backend/tests/unit/api/test_ct_client_plane_auth_closure_05a.py` | **new** — 46 tests in 8 classes |
| `backend/tests/unit/api/test_p6_2b_3_ct_qc_decision.py` | test-fixture correction only: the consultant-created client relationship is seeded with an explicit `client_access_profile` (the deny-by-default `off` seed made these suites fail once `approve_final` became live) |
| `backend/tests/unit/api/test_p6_2e_consultant_lifecycle.py` | same test-fixture correction, same root cause |
| `frontend/src/v3/customer/ReviewDetailPage.jsx` | Approval controls gated on `can('approve_final')` + explanation when withheld |
| `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` | `editableExtraction` / `canDecide` folded with `can('correct_submitted_data')` / `can('approve_final')` |
| `frontend/src/v3/__tests__/client-access-closure-05a.test.jsx` | **new** — 8 frontend tests |

Still explicitly **not** touched by the closure: `domain/relationship_access.py`,
any RLS policy, any migration, the `/me/context` contract, and the consultant /
portal / PE / staff planes.

---

## 13. Backend tests

`backend/tests/unit/api/test_ct_client_plane_auth_05.py` — **25 tests, 4 classes,
all passing** (`[100%]`, exit 0):

| Class | Coverage |
| --- | --- |
| `TestCeilingResolution` | ceiling absent for a direct customer (no relationship row); absent for internal staff, PE staff and a non-member (consultant) principal; absent when the addressed org is not the caller's own; profile normalised fail-closed to `off` for an unknown/absent value; state derivation `active` / `retained_read_only` / `off`. |
| `TestMasterDataCeiling` | MANAGED client **denied** (403 + `error.message`) on facility/asset/vehicle create, update and delete; READ_ONLY client denied writes but allowed reads; COLLABORATIVE client **allowed**; direct customer unaffected (regression). |
| `TestUploadCeiling` | `authorize_org_upload` **denies** a MANAGED client's upload over the real route (403, and the denial is audited with the client-access reason); `enforce_client_operation` **allows** the same operation for a COLLABORATIVE client; direct customer and consultant unaffected. |
| `TestIsolation` | consultant, internal staff and PE staff are never ceiling-restricted; a foreign organisation is decided by the tenant guard, not the ceiling; the ceiling never grants an operation the role guard already refused. |

Run:

```bash
cd backend && .venv/bin/python -m pytest tests/unit/api/test_ct_client_plane_auth_05.py \
  -o addopts="" --tb=short
```

### 13.1 Test-engineering note (honest limitation)

An **end-to-end ALLOW** of the upload path cannot be executed in the database-free
API harness, because a successful upload requires a real Supabase signed URL.
The DENY path is therefore asserted over the **real route**
(`/api/v3/documents/upload-url` → 403), and the ALLOW path is asserted directly
against `enforce_client_operation(..., "upload_document")` for a COLLABORATIVE
client. The browser verification (§15) exercises the denial end-to-end against the
live lab, so the gap is one of *harness capability*, not of unverified behaviour.

---

## 14. Frontend tests

`frontend/src/v3/__tests__/client-access-guard.test.jsx` — **5 tests, all passing**:

| Suite | Tests |
| --- | --- |
| `ClientAccessProvider (presentation-only capability view)` | defaults to unrestricted when no client ceiling applies; an explicit `false` capability is honoured |
| `FacilitiesTab reflects the client-access ceiling` | a managed client sees no master-data write controls; an unrestricted user keeps the master-data write controls (regression) |
| `V3Layout user-facing branding` | shows "CarbonTally" and never a bare "V3" product tag |

Run:

```bash
cd frontend && CI=true npx react-scripts test --watchAll=false \
  --testPathPattern='client-access-guard'
```

---

## 15. End-to-end browser verification (real Chrome, real GoTrue)

`tools/demo_lab/verify_ct05_client_plane_auth_browser.py` (**new**) reproduces the
original manual observation and proves the fix at the **human** and **server**
boundary. It uses headless Google Chrome against the live Demo Lab stack and a
**real password login** against the lab's GoTrue (no token injection), then
repeats the same operations directly against the API.

Identity: the CT03 fixture's managed client
(`ct03.owner.managed@demo-lab.carbontally.local`, organisation
`CT03-QA Managed Client`, `role = org_owner`).

**Result: 22 checks passed, 0 failed (`ok: true`, exit 0).**

| # | Check | Result |
| --- | --- | --- |
| 1 | managed: logged in off `/login` | PASS (`/home`) |
| 2 | managed: **sees their organisation** (not a blank/denied screen) | PASS (`CT03-QA Managed Client`) |
| 3 | managed: organisation plane is not denied | PASS |
| 4 | managed: brand reads **"CarbonTally"** with no `V3` | PASS (`CarbonTally`) |
| 5 | managed: nav screenshot | PASS |
| 6 | managed: `+ New facility` control is **GONE** | PASS |
| 7 | managed: `+ New asset` control is **GONE** | PASS |
| 8 | managed: read-only master-data explanation shown | PASS |
| 9 | managed: facilities screenshot | PASS |
| 10 | managed: upload drop-zone is **GONE** | PASS |
| 11 | managed: upload restriction explanation shown | PASS |
| 12 | managed: documents screenshot | PASS |
| 13 | managed: no unexpected application console errors | PASS |
| 14 | api: password-grant login for API checks | PASS |
| 15 | api: `/me/context` → 200 | PASS |
| 16 | api: `/me/context` still carries the client's organisation | PASS (`CT03-QA Managed Client`, `org_owner`) |
| 17 | api: `/me/context` reports the managed ceiling | PASS (`profile: managed`, `state: active`, `upload_document: false`, `edit_master_data: false`) |
| 18 | api: client **upload-url is DENIED (403)** | PASS (`403`) |
| 19 | api: client **facility create is DENIED (403)** | PASS (`403`) |
| 20 | **regression:** consultant operating the same client still sees `+ New facility` | PASS |
| 21 | regression: consultant screenshot | PASS |
| 22 | consultant: no unexpected application console errors | PASS |

Screenshots (lab evidence directory):

- `~/ct_local_env/demo_lab/evidence/browser/ct05_plane_managed_home.png`
- `~/ct_local_env/demo_lab/evidence/browser/ct05_plane_managed_facilities.png`
- `~/ct_local_env/demo_lab/evidence/browser/ct05_plane_managed_documents.png`
- `~/ct_local_env/demo_lab/evidence/browser/ct05_plane_consultant_facilities.png`

Raw result: `~/ct_local_env/demo_lab/evidence/ct05_browser_verification.json`.

### 15.1 Verifier defects found and corrected during this task

Three initial `FAIL`s were **verifier-assumption bugs, not application defects**,
and are recorded here for transparency:

1. **Client id semantics.** The verifier navigated the consultant plane with the
   client **organisation id**. The consultant client plane addresses a client by
   its **grant/relationship id** (`repos.consultants.get_client(client_id)`, see
   `api/v3_consultants.py::_checked_client`), so the route returned
   `404 client not found`. Fixed by using `fixture._id("relationship:managed")`.
2. **Organisation label race.** The verifier read the nav after a fixed 2 s
   settle while the shell was still mounting, so `.v3-nav-org` was not yet bound.
   Fixed by waiting for the selector; the check now reads the nav element and is
   additionally corroborated by API check #16.
3. **Console-error attribution.** Playwright's console text omits the failing
   URL, so unrelated noise was indistinguishable from a regression. The verifier
   now records `message.location.url` and filters the **pre-existing legacy**
   `/api/organizations/members…` 404 probes with an explicit note (§18, F-2).

The corrected verifier is green (22/22). This is an example of AGENTS.md §80:
an initial finding was resolved only after re-verifying against current runtime
truth.

---

## 16. Regression status — backend

Full API suite, run against the working tree containing CT-05 (plus the other
uncommitted CT-03/CT-04/P8 work already in the tree):

```bash
cd backend && .venv/bin/python -m pytest tests/unit/api -o addopts="" --tb=short
```

```
1 failed, 2740 passed, 13 warnings in 591.81s (0:09:51)
```

The **only** failure is `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin`:

```
assert body["verification_delivered"] is False
E   assert True is False
```

That test is **environmental**, not a CT-05 regression — see §18 (F-4) for the
proof (the local gitignored `backend/.env` configures an email provider, so the
honest API response contradicts the test's "email is not configured" assumption;
blanking `RESEND_API_KEY`/`SMTP_*` makes it pass). Every CT-05-relevant suite
passed, including `test_storage_management_step1.py` (whose contradictory seed
was corrected, §23 F-1) and `test_v3_context.py` (the `/me/context` contract).

### 16.1 CI-flag note

`backend/pyproject.toml` sets `addopts = "-q"`. Adding a second `-q` on the
command line makes it `-qq`, which **suppresses pytest's final summary line**
(the run still reports `[100%]` and a correct exit code). The commands in this
document therefore pass `-o addopts=""` so the summary is captured verbatim.
Anyone re-running these commands should do the same, otherwise the absence of a
summary line is easy to misread as an incomplete run.

---

## 17. Regression status — frontend

Full frontend suite:

```bash
cd frontend && CI=true npx react-scripts test --watchAll=false
```

```
Test Suites: 1 failed, 56 passed, 57 total
Tests:       1 failed, 618 passed, 619 total
```

The single failure is `src/v3/__tests__/dr007-investor-display-fixes.test.jsx`
("Issue 3 — customer review detail shows Mapped activity from
`mapped_data.activity`": expected the row to contain `Natural gas`, received
`Mapped activity`). It is **pre-existing** — see §18, F-3.

CT-05-specific frontend suites are green: `client-access-guard.test.jsx` (5/5).

---

## 18. Failure classification (baseline comparison)

Method: for each failure, we tested whether the failure exists **at HEAD**
(`3fec874`, the branch tip, where none of the CT-05 files exist or are wired in)
by running the *same* test in an isolated `git worktree` of HEAD. This is safe:
it creates a throwaway checkout under `/tmp` and does not touch the working tree,
the index, or any branch (AGENTS.md §70 — no reset/clean/stash of the real tree).

| # | Failure | Classification | Evidence |
| --- | --- | --- | --- |
| F-1 | `test_storage_management_step1.py` asserted a **MANAGED** client could upload — contradicting the ratified matrix | **FIXED IN TASK** (test fixture was wrong, not the application) | The seed set `client_access_profile = managed` while asserting an upload succeeds; the ratified §8.2 matrix denies `upload_document` for MANAGED. The assertion was corrected to the ratified ceiling. |
| F-2 | `4 × 404` on the **legacy** `/api/organizations/members…` family in the consultant pane | **PRE-EXISTING / UNRELATED** | `frontend/src/v3/api.js::resolveV3Organization` probes the legacy endpoint for the caller's primary organisation and 404s for a principal with no direct-customer membership (a consultant principal), then falls back to the consultant engagement context — which is why the consultant plane renders correctly. The CT-05 guard raises **only 403** and never touches this legacy route family, so it cannot be the cause. Recorded as a note in the verifier instead of failing the run. |
| F-3 | `dr007-investor-display-fixes.test.jsx` (frontend) | **PRE-EXISTING** | Re-run in an isolated HEAD worktree: `Tests: 1 failed, 1 passed, 2 total`, exit 1 — identical failure at HEAD. The test's own markup expectation (`getByText('Mapped activity').closest('div')` resolving to the `<div class="k">` label itself, so `textContent` can never include the value) is committed at HEAD and is untouched by CT-05. |
| F-4 | `test_v3_discovery.py::…::test_create_request_as_admin` | **ENVIRONMENTAL (proven)** | The test asserts `verification_delivered is False` with the comment "Email delivery is NOT configured in unit tests". The local, gitignored `backend/.env` **does** configure an email provider (`RESEND_API_KEY`, `SMTP_*`), so delivery genuinely succeeds and the honest API response is `true`. Experiment on the working tree, same code, single test: provider configured → `1 failed`; provider env blanked (`RESEND_API_KEY= SMTP_HOST= SMTP_USERNAME= SMTP_PASSWORD=`) → `1 passed`. Also passes in an isolated HEAD worktree (which has no untracked `.env`): `16 passed`. Not attributable to CT-05. |

No failure was classified as NEW / CT-05-CAUSED.

### 18.1 Note on the HEAD re-run

The HEAD worktree checks ran the **committed** code with no CT-05 file present,
using the same interpreter and environment as the working-tree run, so the only
variable is the code under test. Worktrees were removed after use
(`git worktree list` shows only the main worktree).

---

## 19. Security verification — ALLOW / DENY matrix

Every cell below is enforced **server-side**; the "UI" column records only what
the presentation layer additionally does.

| Actor | Plane / route | Operation | Server decision | UI |
| --- | --- | --- | --- | --- |
| Direct customer (Owner) | org plane | upload, master data | **ALLOW** (no relationship row → no ceiling) | controls shown |
| Direct customer (Member/Viewer) | org plane | upload | ALLOW / DENY by the pre-existing role+viewer guard (unchanged) | unchanged |
| **Managed client** (Owner) | org plane | `upload_document` | **DENY 403** | control hidden + explanation |
| **Managed client** (Owner) | org plane | `edit_master_data` | **DENY 403** | controls hidden + explanation |
| **Managed client** (Owner) | org plane | `approve_final` (**CT-05A**) | **DENY 403** | controls hidden + explanation |
| **Managed client** (Owner) | org plane | `correct_submitted_data` (**CT-05A**) | **DENY 403** | controls hidden + explanation |
| **Managed client** (Owner) | org plane | `map_factors` / `recalculate` | **DENY 403** (PO-9) | not offered |
| **Read-only client** | org plane | writes / upload | **DENY 403** | hidden |
| **Read-only client** | org plane | read / comment | **ALLOW** | shown |
| **Collaborative client** | org plane | `upload_document`, `edit_master_data` | **ALLOW** | controls shown |
| **Collaborative client** | org plane | `approve_final`, `correct_submitted_data` (**CT-05A**) | **ALLOW** (approval stays additionally client-role gated) | controls shown |
| **Retained (post-relationship) client** | org plane | any write | **DENY 403**; reads preserved | read-only |
| **Consultant principal** operating the client | consultant plane | upload (on behalf), master data | **ALLOW** (ceiling not applicable — not an org member) | controls shown |
| **Consultant principal** | org plane as the client | — | ceiling returns `None`; existing tenant guards decide | n/a |
| **Internal CarbonTally staff** | any | any | unchanged (bypass preserved) | unchanged |
| **Processing Entity staff** | PE plane | assigned work | unchanged | unchanged |
| Client user → **another** organisation | any | any | **DENY** by `ensure_org_access` / RLS (unchanged; ceiling not involved) | n/a |
| Client user with **no active relationship** (`pending`/`suspended`/`ended`) | org plane | writes/upload | **DENY 403** (state ≠ active) | hidden |
| Client user with an **unset/unknown profile** | org plane | writes/upload | **DENY 403** (normalises to `off`) | hidden |

Frontend-vs-server independence is preserved: hiding a control changes nothing
about the server decision, and re-enabling a hidden control in devtools yields the
same `403` (verified over the real route in §15, checks 18–19). The three
**CT-05A** rows are verified over the real routes by
`backend/tests/unit/api/test_ct_client_plane_auth_closure_05a.py` (§25).

---

## 20. Negative testing (AGENTS.md §45)

The required negative matrix for this change, with status:

| Negative case | Covered by | Status |
| --- | --- | --- |
| Client (managed) → organisation-plane upload | `test_ct_client_plane_auth_05.py::TestUploadCeiling`, browser #18 | **DENY verified (403)** — over the real route |
| Client (managed) → organisation-plane master data | `TestMasterDataCeiling`, browser #19 | **DENY verified (403)** |
| Client (managed) → **final approval** (`approve_final`) | `test_ct_client_plane_auth_closure_05a.py::TestApproveFinalCeiling`, `::TestApproveFinalJobReviewCeiling` (§25) | **DENY verified (403)** — over the real routes |
| Client (managed) → **correcting submitted data** (`correct_submitted_data`) | `::TestCorrectSubmittedDataCeiling`, `::TestManualExtractionUpdateCeiling`, `::TestConfirmJobCorrectionCeiling` (§25) | **DENY verified (403)** |
| Client (read-only / off / retained) → `approve_final`, `correct_submitted_data` | `::TestApproveFinalCeiling`, `::TestCorrectSubmittedDataCeiling` (§25) | **DENY verified (403)** |
| A denied CT-05A request must leave **zero** workflow/billing/issue/audit/notification mutation | every denial test in `test_ct_client_plane_auth_closure_05a.py` (§25) | **verified** |
| Client (read-only) → any write | `TestMasterDataCeiling` | **DENY verified** |
| Client → foreign organisation | `TestIsolation`, pre-existing tenant suites | **DENY verified** |
| Client → internal operations | pre-existing staff/isolation guards + `TestIsolation` | **DENY unchanged** |
| Consultant A → Consultant B's client | pre-existing consultant suites (`test_v3_consultants.py`, CT-03/CT-04 suites) | **DENY unchanged** — full backend suite green |
| PE A → PE B / PE → prohibited customer document | pre-existing PE suites (`test_pe_auth.py`, …) | **DENY unchanged** |
| Viewer → write | pre-existing viewer guard (viewer check runs **before** the ceiling) | **DENY unchanged** |
| Ceiling must not *restrict* a legitimate actor (false-positive risk) | `TestIsolation`, frontend "unrestricted user keeps the controls" regression test, browser #20 | **ALLOW verified** |

Both directions were tested **for the changed paths** (ALLOW and DENY), per
AGENTS.md §72. The pre-existing boundaries were not re-derived here; they are
covered by the full green backend suite (§16).

---

## 21. Runtime verification & environment

The fix was verified against the **running** local stack, not only against tests.

| Item | Value |
| --- | --- |
| Stack | CarbonTally Demo Lab (isolated local env, disposable database on the local cluster; no production endpoint referenced) |
| Supervisor | `pid=1014766 running=True state=running`, `DEMO_LAB_STATUS: RUNNING` |
| Supervised backend | `pid=1014820 restarts=0 last_exit_code=None` → `http://127.0.0.1:8070` |
| Supervised frontend | `pid=1014827 restarts=0 last_exit_code=None` → `http://localhost:3000` |
| Probes | database **PASS**, gateway `GET /auth/v1/health -> 200` **PASS**, backend `GET /health -> 200` **PASS**, frontend `GET / -> 200` **PASS**, CORS `OPTIONS /api/v3/me/context -> 200` **PASS** |

Restart procedure used after the backend changes (so the running process served
the new code before browser verification):

```bash
.venv/bin/python tools/demo_lab/supervise_demo_lab.py restart
.venv/bin/python tools/demo_lab/supervise_demo_lab.py status
```

Environment caveat, recorded honestly: the backend `.env` is the **isolated
local** environment created for this workspace (`# ISOLATED LOCAL ENV for
93d5cdd … NOT the baseline env`), and `SUPABASE_URL` is deliberately unroutable.
Consequently this verification is **local-lab verification**, not production
verification. No production system, database or deployment was touched.

### 21.1 Reproduction

```bash
# 1. unit/API layers
cd backend && .venv/bin/python -m pytest tests/unit/api/test_ct_client_plane_auth_05.py -o addopts="" --tb=short
cd ../frontend && CI=true npx react-scripts test --watchAll=false --testPathPattern='client-access-guard'

# 2. live lab (requires the Demo Lab running)
cd .. && ~/ct_local_env/pwvenv/bin/python tools/demo_lab/verify_ct05_client_plane_auth_browser.py --json
```

A run of (2) must end with `"passed": 22, "failed": 0, "ok": true` and exit `0`.

---

## 22. Observability, error handling and empty states

- **Audit trail.** A denied upload is recorded through the pre-existing
  `_deny()` recorder with `action_reason="client access profile does not permit
  upload_document"`, so a denial is explainable after the fact (§77). Master-data
  denials surface as a standard `403` on the route.
- **Error envelope and copy.** The message is the non-technical
  "Your client access level does not permit this action" in the platform's
  `{"error":{"message":…}}` envelope — no raw exception, no UUID, no status code
  in the user-facing text (AGENTS.md §46/§75).
- **No misleading success.** The denial is evaluated **before** storage work, so
  the caller cannot receive a signed URL or a created row and then be told the
  action failed. There is no "optimistic success" path.
- **Empty/denied states.** The two reflected surfaces show an explanatory
  read-only banner instead of an empty control set or a silently missing button
  (AGENTS.md §48), and the browser verifier asserts those explanations are
  present (checks 8 and 11).
- **No new console noise.** The verifier asserts there are no unexpected
  application console errors on either the client or the consultant journey;
  the only filtered noise is the pre-existing legacy probe (§18, F-2).
- **Logging hygiene.** No signed URL, token or credential is logged by the new
  code; the ceiling carries only `organization_id`, `profile`, `state` and
  `relationship_id` at debug/diagnostic level (AGENTS.md §78).
- **Accessibility/responsiveness delta.** The change removes controls and adds a
  text explanation; it introduces no new interactive widget, so the D21/D19
  keyboard, focus and responsive behaviour of these pages is unaffected. The
  browser verification ran at 1440×900; other viewports were not re-checked
  (see §23 G-4).

---

## 23. Remaining limitations and open product decisions

### 23.1 Known gaps (implementation follow-ups, policy already ratified)

> **Status update (2026-10-08).** **G-1 is CLOSED** by
> `CT-CONSULTANT-CLIENT-PLANE-AUTH-CLOSURE-05A` (§25). The row below is preserved
> verbatim as the historical record of the gap as CT-05 recorded it; **G-2, G-3,
> G-4, G-5 stand as written.**

| # | Gap | Why it is not done here | Nature |
| --- | --- | --- | --- |
| G-1 | `approve_final` and `correct_submitted_data` are classified by the ratified §8.2 matrix but are **not yet ceiling-bound** on the Organisation plane (e.g. the `/{item_id}/customer-review` workflow route still authorises by role + workflow state). A MANAGED client could therefore still reach a client-approval/correction action that the matrix forbids. | This task's scope was the **upload and master-data** ceiling named in the remediation item. The enforcement is mechanical: bind `Depends(require_client_operation("approve_final"))` / `("correct_submitted_data")` on the corresponding routes. | Follow-up implementation (no PO decision needed — the matrix already answers it). |
| G-2 | Member/role administration (`MembersTab`, `POST /{org_id}/invitations`, `PUT /members/{id}`) is **not** ceiling-bound. | The ratified matrix contains **no** operation representing user administration, so applying a ceiling here would require inventing policy. | **PO DECISION REQUIRED** — see §23.2. |
| G-3 | Organisation profile / branding / settings writes are **not** ceiling-bound. | Same reason as G-2: no matrix operation covers them. | **PO DECISION REQUIRED** — see §23.2. |
| G-4 | Browser verification ran at one viewport (1440×900) and one client identity (one MANAGED client). Other viewports, and the READ_ONLY / COLLABORATIVE / RETAINED profiles, were covered by API tests but not by a browser journey. | Time/scope; the API layer is the security boundary and is covered for every profile/state. | Verification depth (not a defect). |
| G-5 | The upload **ALLOW** path cannot be exercised end-to-end in the DB-free API harness (§13.1). | Harness capability (needs a real signed URL). | Test-harness limitation. |

### 23.2 OPEN PRODUCT DECISIONS

These are recorded rather than resolved, per AGENTS.md §62 ("Do not silently
change business policy"):

1. **May a consultant-managed client's own users administer their own
   organisation's members/roles?** The §8.2 matrix stops at data operations and
   has no `manage_members`-style capability, so the ceiling currently says
   nothing. Options include "profile-independent (a client Owner keeps PD-2A
   authority)", "COLLABORATIVE only", or "never for a managed client".
   **Until the PO decides, no ceiling is applied to member administration** —
   this preserves the ratified PD-2A decision rather than weakening it silently.
2. **May a consultant-managed client edit their own organisation profile /
   branding?** Same reasoning; no matrix operation exists.
3. **Should the client-access ceiling also apply to the `off` profile's ability
   to authenticate at all**, or is that fully owned by the CT-04 identity plane?
   Current behaviour: identity/login gating is unchanged (CT-04), and this task
   only bounds organisation-plane operations. Flagged so the two planes are not
   assumed to be independent by accident.

### 23.3 Not-a-limitation (explicitly)

- No orphan-side-effect window exists: the ceiling is evaluated before storage
  and before persistence.
- No cross-tenant disclosure exists: the ceiling decision uses only the caller's
  own organisation.
- The frontend remains non-authoritative by design.

---

## 24. Verdict, evidence index and Git state

### Verdict

**IMPLEMENTED_AND_TESTED — READY FOR INDEPENDENT VERIFICATION.**

| Statement | Status |
| --- | --- |
| Code implements the ratified ceiling on organisation-plane uploads and master-data writes | **IMPLEMENTED** |
| …and, since 2026-10-08, on the two remaining ratified operations (`approve_final`, `correct_submitted_data`) across five Organisation-plane routes — gap G-1, **CLOSED** | **IMPLEMENTED + TESTED** (see §25 and `docs/architecture/CT-CONSULTANT-CLIENT-PLANE-AUTH-CLOSURE-05A.md`) |
| Backend tests (25) + frontend tests (5) green, and the full backend suite is green except one proven-environmental test | **TESTED** |
| Live-lab browser journey (22 checks) reproduces the original defect scenario and shows the correct outcome, with the consultant path unaffected | **VERIFIED (local lab)** |
| Product-Owner acceptance | **NOT CLAIMED** — independent verification (AGENTS.md §51/§60/§73) is the next step |

This is deliberately **not** an acceptance verdict. Per AGENTS.md §73,
"implemented", "tested" and "verified" are distinct from "accepted".

### Evidence index

| Evidence | Location |
| --- | --- |
| Backend focused tests (25 passed) | `backend/tests/unit/api/test_ct_client_plane_auth_05.py` |
| Backend full suite (`1 failed, 2740 passed in 591.81s`) | run log `/tmp/ct05_api_full4.txt` (failure = §18 F-4, environmental) |
| Environmental proof for F-4 | `/tmp/ct05_disc2.txt` (provider configured → fail; provider blanked → pass) |
| HEAD baseline for F-3 (frontend) | `/tmp/ct05_headtest.txt` (`1 failed, 1 passed` at HEAD) |
| HEAD baseline for `test_v3_discovery.py` | `/tmp/ct05_discovery.txt` (`16 passed` — no untracked `.env`) |
| Frontend focused tests (5 passed) | `/tmp/ct05_fe_focus2.txt` |
| Frontend full suite (`1 failed, 618 passed`) | `/tmp/ct05_fe_full.txt` |
| Browser verification (22/22, `ok: true`) | `~/ct_local_env/demo_lab/evidence/ct05_browser_verification.json` |
| Browser screenshots (4) | `~/ct_local_env/demo_lab/evidence/browser/ct05_plane_*.png` |
| Lab runtime state (all probes PASS) | `/tmp/ct05_status2.txt` |

### Git state

- Branch: `p8-release-reconciled`; HEAD: `3fec874`
- The working tree contains this task's changes **plus** pre-existing uncommitted
  work from earlier tasks (CT-03, CT-04, manual-processing coverage, P8
  reconciliation). Nothing was committed, reset, stashed, cleaned or
  force-pushed (AGENTS.md §70).
- No secrets, tokens, signed URLs or credentials were introduced. The only
  environment fact recorded anywhere in this document is the **name** of a
  configuration key, never a value.
- No database objects were created or altered and no migration was written.

### Recommended next step

Independent verification (OHD / QA Harness) should re-run the three commands in
§21.1 against the live lab and confirm: the MANAGED client is denied on both
surfaces while still seeing their organisation, the consultant operating the same
client is unaffected, and no user-facing "V3" remains.

---

## 25. Addendum — CT-05A: closure of gap G-1 (2026-10-08)

Full report: `docs/architecture/CT-CONSULTANT-CLIENT-PLANE-AUTH-CLOSURE-05A.md`.

**What was bound.** `approve_final` and `correct_submitted_data` — the two
remaining operations the ratified §8.2 matrix classifies but CT-05 did not
enforce — are now ceiling-bound by `enforce_client_operation(...)` on **five**
Organisation-plane routes:

| Route | Operation |
| --- | --- |
| `POST /api/v3/processing/items/{item_id}/customer-review` | `approve_final` |
| `POST /api/v3/processing/jobs/{job_id}/review` | `approve_final` |
| `POST /api/v3/processing/items/{item_id}/extract` | `correct_submitted_data` |
| `POST /api/v3/processing/jobs/{job_id}/confirm` | `correct_submitted_data` |
| `PUT /api/v3/manual-extraction/items/{item_id}` | `correct_submitted_data` |

The jobs routes are included deliberately: they are the automatic-processing
mirror of the item routes (the same customer decision recorded on the durable job
and stamped onto the item), so omitting them would leave the profile bypassable by
choosing the automatic pipeline. Every call site sits **after** all pre-existing
authorization (identity, tenant, organisation role, consultant capacity,
entitlement) and **before** the first state check or write, so a denied request is
zero workflow/billing/issue/audit/notification mutation. `map` / `validate` /
`calculate` / `start` remain unbound (PO-9 operations are already refused by the
pre-existing guards) and a test pins that boundary.

**UI reflection.** `frontend/src/v3/customer/ReviewDetailPage.jsx` and
`ProcessingItemWorkspace.jsx` fold `can('approve_final')` /
`can('correct_submitted_data')` into their decision controls (with an explanation
instead of a silently missing button). Presentation only — the server denies
regardless.

**Root cause exposed in test fixtures (test-only change).** `fakes.seed_client`
seeds a relationship **deny-by-default** (`client_access_profile="off"`, matching
the DB default). Until 05A no Organisation-plane route read the profile, so suites
that seeded a relationship and then approved as the client *appeared* to pass.
Once `approve_final` bound, four tests failed correctly; the two affected fixtures
(`test_p6_2b_3_ct_qc_decision.py`, `test_p6_2e_consultant_lifecycle.py`) now state
the profile the scenario assumed (`collaborative`). No production behaviour was
relaxed and no assertion weakened.

**Tests.** `backend/tests/unit/api/test_ct_client_plane_auth_closure_05a.py`
(**46 tests, 8 classes, passing**) and
`frontend/src/v3/__tests__/client-access-closure-05a.test.jsx` (**8 tests,
passing**). Backend full-suite failures after the closure are a **strict subset**
of this document's recorded pre-task baseline (8 vs 44; the "new failures" set is
empty) — see the closure report §6.

**Still open after 05A:** G-2 and G-3 remain **PO DECISION REQUIRED** (no matrix
operation exists for member administration or organisation-profile writes) and
remain unbound by design; G-4 (browser depth) now also covers CT-05A — the CT-05
browser verifier carries no 05A case yet, since all five 05A routes load the
resource before the ceiling is evaluated and a browser/API denial check therefore
needs a seeded `customer_review`/`review`-stage item; G-5 is unchanged.













