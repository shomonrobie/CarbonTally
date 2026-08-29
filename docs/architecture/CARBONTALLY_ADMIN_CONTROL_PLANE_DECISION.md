# CarbonTally — Canonical Staff / Admin Control Plane (CL-66)

**Status:** Ratified implementation decision (documented, not yet PO-signed for
legacy retirement). Last verified: 2026-08-30.

## 1. Problem (CL-66)

Two staff surfaces coexisted:

| Surface | Routes | Role/perm source | Notes |
|---|---|---|---|
| Legacy admin CRA | `/admin/*` | legacy `/api/admin/*` | separate AuthContext, separate deployment rewrite |
| V3 internal operations | `/ops` | `/api/v3/ops/*` (`staff_profiles` + `staff_roles.permissions`) | the phase 1–2 restored operating model |

The legacy roles endpoint returned `success=true, data=[], total=0` for a
staff-admin while V3 returned the real populated permission set — a split-brain
catalog that is a privilege-drift risk even where current negative probes deny
access.

## 2. Canonical decision

**The V3 internal operations surface (`/ops` in the main React application) is
the single authoritative staff application.** It is the only staff surface that:

1. reads the real staff identity (`staff_profiles`) and role catalog
   (`staff_roles.permissions`) through `/api/v3/ops/me`;
2. enforces every action with resolved permissions
   (`can_process`, `can_review`, `can_manage_staff`, `can_manage_billing`,
   `can_view_all`) via `ensure_staff_permission`, never by name-string
   matching;
3. renders permission-aware navigation (CL-62): a tab is shown only when the
   API it calls is legitimate for the caller's role.

The public/customer website is **not** the administrative interface. The V3
main app has no `/admin` route; `/admin` in the main app resolves to the
customer/404 surface. The legacy admin CRA is **quarantined**, not deleted:

- it is served only by the deployment rewrite (`vercel.json`),
- its legacy endpoints remain mounted until a dependency inventory is complete
  (the AGENTS.md §79 legacy-code rule),
- no new feature is built on it.

## 3. Role / permission vocabulary (single source of truth)

`staff_roles.permissions` (jsonb) is the authoritative permission set:

| Role (seed) | can_process | can_review | can_manage_staff | can_manage_billing | can_view_all |
|---|---|---|---|---|---|
| admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| system_admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| operator | ✅ | — | — | — | ✅ |
| reviewer | — | ✅ | — | — | ✅ |
| qc_specialist | ✅ | ✅ | — | — | ✅ |
| pe_manager | ✅ | ✅ | — | — | ✅ |

`require_admin()` endpoints (`/api/v3/qc/*`, `/api/v3/issues/admin/open`) map
to global admin (`admin`/`system_admin`) — the QC and Issues tabs render only
for those roles (CL-62).

## 4. Migration / deprecation guardrails

- **Never remove** legacy routes without a full dependency inventory
  (AGENTS.md §79).
- **Never disable RLS** or bypass authorization to migrate.
- Regression gates: all staff personas against both old/new URLs during
  migration; role CRUD/read; system-admin settings/commercial/audit; PE and
  customer denials; deployment route smoke tests.

## 5. PO decision required (explicit)

- Approve `/ops` as the canonical staff app and the legacy admin deprecation
  plan (retire after dependency inventory).
- Approve the final role authority (whether QC becomes its own permission or
  remains a global-admin gate).

*Implementation note:* the code has already moved to the V3 canonical surface;
this document records the decision and the guardrails so a later migration can
proceed without reintroducing a split catalog.
