# CT-CONSULTANT-UX-PARITY-INDEPENDENT-VERIFY-01

**Independent CoStrict / OHD verification of the CarbonTally consultant UX +
organisation parity + client operating plane implementation**

| | |
|---|---|
| **Task ID** | `CT-CONSULTANT-UX-PARITY-INDEPENDENT-VERIFY-01` |
| **Type** | Independent AUDIT / VERIFICATION (not implementation) |
| **Repository** | `/home/shomonrobie/ct_93d5cdd` |
| **Branch** | `p8-release-reconciled` |
| **Starting SHA** | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` |
| **Ending SHA** | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` (unchanged — no commit) |
| **Environment** | Local Demo Lab only (frontend `:3000`, backend `:8070`, DB `carbontally_demo_local` @ `:54426`, lab GoTrue gateway `:54430`) |
| **Verifier** | Independent (did not author any of the six target changesets) |

---

## 1. Task ID

`CT-CONSULTANT-UX-PARITY-INDEPENDENT-VERIFY-01`

Verification targets (as named in the brief):

1. `CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01`
2. `CT-CONSULTANT-MODEL-IMPLEMENTATION-02`
3. `CT-CONSULTANT-MODEL-IMPLEMENTATION-03`
4. `CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01`
5. `CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A`
6. `CT-CONSULTANT-CLIENT-PLANE-PARITY-REMEDIATION-01`

Immediate target: the combined state after **F-NAV-1** remediation.

---

## 2. Audit scope

**In scope**

* the Consultant Plane → Clients → Client Operating Plane navigation contract;
* consultant reach to the three organisation-plane reporting endpoints (F-NAV-1);
* consultant authorization: admission, capability, relationship lifecycle, tenant
  liveness, cross-firm and cross-tenant isolation;
* the `organization_members` invariant;
* RLS / database posture for the touched surfaces;
* client access-profile semantics as currently implemented;
* Team, Firm Tasks, Client Messages UX;
* direct-customer regression.

**Out of scope (deliberately not performed)**

* production / Render / hosted Supabase (not accessed);
* any repair or redesign of a defect found (audit only);
* RLS, migration, application-source or test modification;
* the frozen D19/D21/N1/N3 UX decisions themselves;
* OCR/email/production capability assessment;
* the client-portal (Plane C) profile matrix end-to-end at the API boundary
  (verified by source inspection instead — see §21).

---

## 3. Authority hierarchy used

1. Ratified Product-Owner decisions (`CT-CONSULTANT-PO-CONSOLIDATION-01.md`,
   `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`)
2. Consultant PO consolidation (§6.1 ceiling, §7.2/§7.3/§7.4, §8.x, §13.1, PO-6,
   PO-9, PO-10, PD-3/PD-7/PD-9/PD-12)
3. Current architecture documents
4. **Current implementation (inspected)**
5. Tests / implementation reports (treated as *claims*)
6. Research / recommendations
7. Historical/superseded documents

Where sources conflicted, the conflict is stated rather than reconciled silently
(no material conflict was found that affects the verdict — see §31).

---

## 4. Starting SHA

`3fec874ca1f170ecb03e7daf69992dbf9e9cd18e`

## 5. Ending SHA

`3fec874ca1f170ecb03e7daf69992dbf9e9cd18e`

No commit was made; the pre-existing dirty worktree was preserved untouched.

## 6. Worktree status

```text
pre-existing modifications : preserved (not reset, not cleaned, not rebased)
tracked files changed by me: NONE
untracked files added by me : docs/architecture/CT-CONSULTANT-UX-PARITY-INDEPENDENT-VERIFY-01.md (this report)
                             /tmp/ctaudit/*  (harness + logs, OUTSIDE the repository)
                             ~/ct_local_env/demo_lab/evidence/browser/indep01_*.png (evidence, outside the repo)
secrets written to the repo: NONE
```

`git status --porcelain` ended at **220 entries** with HEAD and branch unchanged;
no new *modification* to any tracked source file was introduced by this audit. The
only `M backend/api/v3_reporting.py` entry is part of the F-NAV-1 changeset that
already existed before the audit began.

### 6.1 Controlled data mutation (declared, restored, verified)

Three acceptance-gate properties cannot be observed in the pristine lab (no ended
relationship, no suspended tenant, no firm member lacking `can_view_client` exist).
Per AGENTS.md §55 they were tested with a **minimal, fully reverted, verified**
mutation of existing rows — nothing was created, nothing deleted, no relationship
destroyed:

| Purpose | Row touched | Mutation | Restore | Verified |
|---|---|---|---|---|
| D4 capability | `consultant_firm_members.can_view_client` (`consultant.member`) | `true → false` | `→ true` | ✅ `t` |
| D5 ended | `consultant_clients.status` (Client B relationship) | `active → ended` | `→ active` | ✅ `active` |
| D6 suspended | `organizations.is_active` (Demo Lab Client B) | `true → false` | `→ true` | ✅ `t`, **14/14 organisations active** |

One restore initially failed (invalid T-SQL-style boolean literal `is_active=t`);
it was detected by the harness's own restore check and **corrected within the same
session** — the final state table above is the post-correction evidence.
This audit's own probe rows (5 `consultant_tasks`) were deleted afterwards:
`consultant_tasks` total returned to **0**.

---

## 7. Files inspected

Backend (read)

* [`backend/api/v3_reporting.py`](backend/api/v3_reporting.py) — the F-NAV-1 fix
* [`backend/api/consultant_auth.py`](backend/api/consultant_auth.py) — `resolve_managed_org_ids`, `ensure_consultant_org_access`, `ensure_consultant_permission`, `ensure_customer_approval_authority`
* [`backend/api/dependencies.py`](backend/api/dependencies.py) — `ensure_org_access`
* [`backend/auth.py`](backend/auth.py) — `AuthUser`, `require_org_member()`, `_admit_consultant_principal`, `enforce_org_path_scope`, `is_organization_active`
* [`backend/api/v3_consultants.py`](backend/api/v3_consultants.py) — `_checked_client`, `client_workspace_context`, TaskCreate, access-profile/retention routes, capability route
* [`backend/domain/relationship_access.py`](backend/domain/relationship_access.py) — profile/state model
* [`backend/api/client_portal_auth.py`](backend/api/client_portal_auth.py) — where `profile_allows` is consumed
* [`backend/tools/demo_lab/lab.py`](tools/demo_lab/lab.py) — lab topology, psql, credentials (used, not modified)

Frontend (read)

* [`frontend/src/v3/consultant/ClientOrgShell.jsx`](frontend/src/v3/consultant/ClientOrgShell.jsx)
* [`frontend/src/v3/api.js`](frontend/src/v3/api.js) — `resolveV3Organization`, `getClientWorkspaceContext`, `setActiveConsultantClientId`
* [`frontend/src/v3/consultant/ConsultantClientContext.jsx`](frontend/src/v3/consultant/ConsultantClientContext.jsx)

Documents (read)

* `CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01.md`, `…-01A.md`
* `CT-CONSULTANT-CLIENT-PLANE-PARITY-REMEDIATION-01.md`
* `CT-CONSULTANT-MODEL-IMPLEMENTATION-02.md`
* `CT-CONSULTANT-PO-CONSOLIDATION-01.md` (referenced sections)
* `AGENTS.md`

Database (read-only queries + declared mutation above): `consultant_firm_members`,
`consultant_clients`, `organizations`, `organization_members`, `consultant_tasks`,
`pg_policies`, `pg_proc`/`is_org_consultant`, migration files.

---

## 8. Environment

```text
frontend        http://localhost:3000                     -> 200 (CRA, live)
backend         http://localhost:8070                     -> /health 200, /openapi.json 200
database        carbontally_demo_local @ 127.0.0.1:54426 (docker supabase_db_carbon_ledger)
lab gateway     http://127.0.0.1:54430                    (auth + postgrest + storage)
driver          ~/ct_local_env/pwvenv (Playwright + /usr/bin/google-chrome, headless)
auth            REAL password login against lab GoTrue (no token injection)
```

The environment was **available and live**; no limitation was caused by
unavailability.

---

## 9. Methodology

1. Read the six target documents; recorded their claims.
2. Inspected the current implementation at HEAD (not the worktree only).
3. Built a **new** harness (`/tmp/ctaudit/ctprobe.py`) that logs in to the lab
   GoTrue with every manifest identity and probes the API boundary directly —
   it does not import or reuse the implementation's verifier.
4. Reproduced the F-NAV-1 root cause by calling the **real** guard
   (`/tmp/ctaudit/guard_repro.py`), and the D-7 fail-closed branch.
5. Ran a declared, restored mutation for the three unobservable properties.
6. Ran a **new** independent Playwright walkthrough
   (`/tmp/ctaudit/browser_walkthrough.py`), plus a control experiment for the one
   observation it produced.
7. Ran the relevant regression suites with an independent runner.
8. Inspected RLS/database posture directly against `pg_policies` / `pg_proc`.

Labelling used throughout:

* **IMPLEMENTATION-PROVIDED EVIDENCE** — a claim taken from an implementation
  document/test without independent reproduction.
* **INDEPENDENTLY VERIFIED** — reproduced by this audit with its own
  commands/queries/requests and recorded output.

---

## 10. Implementation claims reviewed

| # | Claim (source) | Verdict |
|---|---|---|
| C1 | F-NAV-1: three `/api/v3/reporting/*` routes were `get_current_user`-only and refused a consultant; the fix swaps to `require_org_member()` (`…-CLIENT-PLANE-PARITY-REMEDIATION-01.md` §6–§7) | **INDEPENDENTLY VERIFIED** (§15, §16) |
| C2 | No frontend change, no RLS/migration/schema change in the F-NAV-1 fix | **INDEPENDENTLY VERIFIED** (§20) |
| C3 | Consultant reaches the same reporting payloads as the customer | **INDEPENDENTLY VERIFIED** (byte-equal, §22) |
| C4 | Admission is capability-gated (`can_view_client`), relationship alone never admits (`MODEL-02` F-1) | **INDEPENDENTLY VERIFIED** (§13) |
| C5 | Consultants are never `organization_members` rows (PD-12) | **INDEPENDENTLY VERIFIED** (§19) |
| C6 | D-7: suspended client tenant serves the consultant nothing | **INDEPENDENTLY VERIFIED** (§18) |
| C7 | D15: ended/pending/suspended grant nothing | **INDEPENDENTLY VERIFIED** (§15 D5) |
| C8 | UX-01: exactly one primary "Back to Consultant"; "Client workspace" tab removed; no global Active client; no Switch client (`…-01.md`, `…-01A.md`) | **INDEPENDENTLY VERIFIED** (§12, §14, browser) |
| C9 | Team: human-readable identity by email; real role vocabulary; role≠capability copy | **INDEPENDENTLY VERIFIED** (§23) |
| C10 | Test/browser suites pass (19/19, 44/44, 20/20, 24/24) | **IMPLEMENTATION-PROVIDED EVIDENCE** — superseded by this audit's own runs (§27, §26) |

**Nothing was accepted on the strength of a claim alone.**

---

## 11. Independent evidence

Commands (all run by this audit; outputs retained under `/tmp/ctaudit/`):

```text
python3 /tmp/ctaudit/ctprobe.py                     -> /tmp/ctaudit/probe_out.txt
python3 /tmp/ctaudit/guard_repro.py                 -> guard matrix (real module)
python3 /tmp/ctaudit/liveness_test.py               -> /tmp/ctaudit/liveness_out.txt
python3 /tmp/ctaudit/d4_and_cleanup.py              -> /tmp/ctaudit/d4_out.txt
~/ct_local_env/pwvenv/bin/python /tmp/ctaudit/browser_walkthrough.py -> /tmp/ctaudit/browser_out.txt
~/ct_local_env/pwvenv/bin/python /tmp/ctaudit/client_b_investigate.py
backend/.venv/bin/python -m pytest tests/unit/api … (targeted + full)
frontend: CI=true npx react-scripts test --testPathPattern="(consultant|manual-processing-coverage)"
```

Database ground truth (read-only) — the demo lab at the time of audit:

```text
consultant_firm_members: 4 rows
  consultant.member   role=consultant active view=t approve=f  (firm_demo)
  consultant.owner    role=owner      active view=t approve=t  (firm_demo)
  owner               role=owner      active view=t approve=f  (firm 1ee24d1d)
  owner               role=owner      active view=t approve=f  (firm caab859a)
consultant_clients: 8 rows, ALL status=active
  firm_demo        -> 5 orgs (Demo Lab Client A read_only, Client B collaborative,
                              CT03 Managed/Off/Retained)
  firm 1ee24d1d    -> 2 orgs (MP-FX …)
  firm caab859a    -> 1 org  (MP-FX Sponsored)
organizations: 14, all is_active=true
organization_members rows whose user_id is a consultant firm member: 0
```

---

## 12. Consultant Plane findings (Part A)

Independently inspected in a real browser as `consultant.owner` (`Demo Lab Carbon
Consultants`).

| Item | Requirement | Result |
|---|---|---|
| A1 | Consultant identity + firm shown; no global client identity on the firm plane | **PASS** — "Consultant" + "Demo Lab Carbon Consultants" |
| A2 | No global "Active client" / "Select active client" on firm surfaces | **PASS** — the string is absent from the Dashboard and Clients; `[aria-label="Select active client"]` count = 0 |
| A3 | Clients is the portfolio (`Clients → row → Open workspace`) | **PASS** — "Open workspace" present per row; both managed clients listed |
| A4 | No competing top-level "Client workspace" destination | **PASS** — the string is absent from the hub |
| A5 | Team / Firm branding / White-label / Manual Processing carry **no** client context | **PASS** — none contains "Working on" or a client-context bar |

Tabs observed: `Consultant dashboard · Clients · Manual Processing · Firm branding ·
White-label · Team · Client messages`.

---

## 13. Client Operating Plane findings (Part B)

Opened as `consultant.owner` at `/consultant/clients/09501808-…/home`.

The `:clientId` route parameter is the **`consultant_clients` relationship-row id**,
not the organisation id ([`backend/api/v3_consultants.py:1603`](backend/api/v3_consultants.py:1603),
[`frontend/src/v3/api.js:120`](frontend/src/v3/api.js:120)). The shell resolves it
server-side to the organisation; `resolveV3Organization()` then feeds the reused
customer pages the correct `organization_id`. This is a non-obvious but coherent
design; it was verified rather than assumed.

| Item | Requirement | Result |
|---|---|---|
| B1 | Actor = consultant firm | **PASS** |
| B2 | Subject = "Working on \<client\>"; no impersonation wording | **PASS** — "Working on Demo Lab Client A"; "Current organization" absent; "logged in as" absent |
| B3 | Exactly ONE primary "Back to Consultant" | **PASS** — body count = **1** on the Home **and** on the deeper Documents page; it returns to `/consultant` |
| B4 | No "Switch client" | **PASS** — string absent, no switch control in the DOM |
| B5 | Context persists deeper in the plane | **PASS** — Documents page still "Working on Demo Lab Client A", one return control |
| B6 | Direct customer shows no consultant context | **PASS** (§26) |

`V3Layout`'s consultant nav entry reads the constant `Consultant` (matching the
01A change), so the context-bar link is the only "Back to Consultant".

---

## 14. Navigation findings

```text
Consultant Plane  -> Clients (Open workspace) -> Client Operating Plane
Client Operating Plane -> [← Back to Consultant] -> /consultant
```

* `Clients` is the authoritative selection point (**Gate 2 PASS**).
* The legacy inline `ClientWorkspace` mini-dashboard is gone; no peer
  "Client workspace" destination exists (**Gate 1/5 PASS**).
* No workspace-level switcher; changing client = return to Clients
  (**Gate 5 PASS**).
* Actor/subject separation is textual and unambiguous (**Gate 3 PASS**).
* No firm page inherits a selected client (**Gate 4 PASS**).
* Legacy `R-NAV-1` route `/consultant/items/:clientId/:itemId` still exists but is
  no longer linked from the hub; its back-link returns *into* the client plane, so
  it does not compete with the single hub return (§31).

---

## 15. F-NAV-1 findings (Part D — route-by-route)

Independently probed at the API boundary with real lab-issued bearer tokens.
`200` was never accepted as sufficient on its own; bodies and tenant ids were
inspected (§22).

| Case | Principal | Organisation | `customer-dashboard` / `emissions-trend` / `member-activity` | Expected | Verdict |
|---|---|---|---|---|---|
| D1 | `consultant.owner` | Client A (managed) | 200 / 200 / 200 | 200 | **PASS** |
| D1b | `consultant.owner` | Client B, CT03 Managed/Off/Retained | 200 / 200 / 200 (5/5 firm clients) | 200 | **PASS** |
| D2 | `consultant.owner` | Org A, Org B (unmanaged) | 403 / 403 / 403 ("Organization access denied") | 403 | **PASS** |
| D3 | `consultant.owner` | clients of firms `caab859a`, `1ee24d1d` | 403 / 403 / 403 | 403 | **PASS** |
| D4 | `consultant.member` with `can_view_client` **revoked** | Client A | 403 / 403 / 403 | 403 | **PASS** (restored → 200) |
| D5 | `consultant.owner` after relationship set **`ended`** | Client B | 403 / 403 / 403 | 403 | **PASS** (restored → 200) |
| D6 | `consultant.owner` with tenant **suspended** | Client B | 403 / 403 / 403 ("This organization is suspended") | 403 | **PASS** (restored → 200) |
| D7 | unauthenticated | Client A | 401 / 401 / 401 | 401 | **PASS** |
| D8 | `client_a_owner` (direct customer) | own org | 200 / 200 / 200 | 200 | **PASS** |
| D9 | `client_a_owner` | Client B / Org A / Org B | 403 / 403 / 403 | 403 | **PASS** |
| D10 | `pe_manager` (Processing Entity) | every org tried | 403 / 403 / 403 ("Organization member access required") | 403 | **PASS** |

**D1–D10: all ten independently verified at the security boundary.**

### 15.1 Root cause independently reproduced (not merely reported)

`/tmp/ctaudit/guard_repro.py` calls the **real** `ensure_org_access`:

```text
consultant (managed_org_ids=None)          -> managed client org   -> DENY 403 (Organization access denied)
consultant (managed_org_ids=[client_a])    -> client_a org         -> ALLOW
consultant (managed_org_ids=[client_a])    -> unrelated org        -> DENY 403
consultant (managed_org_ids=[])            -> client_a org         -> DENY 403
PE staff                                   -> customer org         -> DENY 403 (Processing Entity staff cannot access customer organisations)
org_a owner                                -> own org              -> ALLOW
org_a owner                                -> client_a org         -> DENY 403
```

`managed_org_ids` is populated **only** by `require_org_member()`
([`backend/auth.py:977`](backend/auth.py:977)); `get_current_user` never sets it.
Therefore the pre-fix guard chain on a `get_current_user`-only route denied the
consultant by construction. The F-NAV-1 diagnosis is **confirmed**, and the fix
(`Depends(get_current_user)` → `Depends(require_org_member())` on the three
routes) is the correct minimal change.

The full diff of the fix versus HEAD is exactly those three guard swaps plus
docstrings and one import — **no schema, RLS, or contract change**.

---

## 16. Authorization findings

Guard chain for the three F-NAV-1 routes:

```text
Depends(require_org_member())            # admission
   └─ not an org member -> _admit_consultant_principal()
          └─ resolve_managed_org_ids()   # CAP-VIEW-CLIENT gate + ACTIVE grants only
                 └─ current_user.managed_org_ids = [...]
                        └─ enforce_org_path_scope(request, user)
ensure_org_access(user, organization_id) # the SINGLE tenant decision
   └─ consultant branch: organization_id in managed_org_ids AND is_organization_active()
```

Observations:

* The tenant decision stays in `ensure_org_access`; `require_org_member()` only
  contributes consultant *admission*. No parallel consultant authorization rule
  was introduced — matching the documented design.
* `ensure_org_access` is fail-closed: `managed is None` (non-consultant, no org
  binding) → 403; consultant with a non-matching grant set → 403.
* The uniform denial message ("Organization access denied") is used for
  non-consultant and consultant cross-tenant denials alike, so the reporting
  endpoints expose no consultant-specific oracle.
* The same session's token reaches **5 of 5** of the firm's managed clients and
  **0 of 4** other organisations (2 unmanaged direct customers + 2 other-firm
  clients). Knowing an organisation id confers nothing.

---

## 17. Capability findings (Part F)

Capability ≠ relationship, independently established:

```text
consultant.member  GET /api/v3/consultants/me              200 (can_view_client=T, can_approve=F)
                   GET /api/v3/consultants/me/team         200
                   GET /api/v3/consultants/me/clients      200
                   PATCH /me/team/{id}/capabilities        403 "consultant lacks permission: manage_team"
                   POST /clients/{a}/documents/upload-url   403 "consultant lacks permission: upload_documents"

consultant.owner   POST /clients/{a}/documents/upload-url   422 ('.txt' is not an allowed document extension)
                   -> reached the operation (capability satisfied), blocked by input validation
```

* With `can_view_client` **revoked on the row** (`true → false`), all three
  reporting endpoints returned **403**; restoring it returned **200** on the next
  request. **No caching in the decision path** was observed.
* A member holding only `can_view_client` is denied a *write* operation
  (`upload_documents`) while the owner passes the same gate — the exact
  `role ≠ capability ≠ relationship` property the PO model requires.
* `/me` mirrors the server state (`can_view_client`, `can_approve`) rather than
  inventing authority — presented truthfully.
* `CONSULTANT_ROLES = (owner, manager, consultant, viewer)` and the capability→column
  map live in [`backend/api/consultant_auth.py:49`](backend/api/consultant_auth.py:49).
  **Role alone grants nothing** (a new member is created with all `can_*` false).

**Gate 10 PASS.**

---

## 18. Tenant-isolation findings (Part E) & tenant liveness (Part H)

* **Cross-tenant reads denied:** Org A, Org B, and both other firms' clients →
  403 on all three reporting routes; the response body **never** contains the
  foreign organisation id, a name, emissions, report or member data (checked
  programmatically).
* **Oracle check:** the denial message is uniform; no tenant-existence signal was
  observed on the reporting endpoints.
* **Client-plane context endpoint** (`/api/v3/consultants/clients/{id}/context`):
  own relationship → 200 with the correct `organization_id`; another firm's
  relationship → **403**; a nonexistent id → **404**; **no** foreign org id leaked
  in any response (see F-IND-2).
* **D-7 tenant liveness:** with Client B temporarily suspended, the consultant got
  403 *and* its own owner also got 403 — the consultant relationship does **not**
  bypass tenant suspension.
* **Fail-closed proof:** when the organisation-state store was unreachable, the D-7
  predicate returned "not active" and the guard **denied** ("This organization is
  suspended") rather than allowing. An unanswerable store is a denial.

**Gate 9 PASS, Gate 11 PASS.**

---

## 19. `organization_members` invariant (Part G)

```sql
SELECT count(*) FROM public.organization_members om
WHERE om.user_id IN (SELECT user_id FROM public.consultant_firm_members);
-- => 0
```

* **Zero** consultant firm-member users appear in `organization_members`.
* The 5 firm_demo client organisations each have exactly **one** member — their own
  customer owner — and no consultant.
* Consultant access is achieved through **firm membership + `consultant_clients`
  grant + capability + tenant admission**, never by fabricating a customer
  membership.

**Gate 13 PASS.**

---

## 20. RLS / database findings (Part O)

| Check | Result |
|---|---|
| RLS enabled on the touched tables | **Yes** — `consultant_clients` (5 policies), `consultant_firm_members` (2), `organization_members` (4), `organizations` (2), all `relrowsecurity = t` |
| Consultant-aware RLS helper | `public.is_org_consultant(org)` — `SECURITY DEFINER`, active firm membership + `consultant_clients.status='active'` |
| Tenant-scoped policies | **71** policies reference `is_org_consultant`, all `cmd=SELECT` and tenant-keyed — no table-wide/global policy |
| Did the F-NAV-1 fix change RLS? | **No** — the diff touches only `backend/api/v3_reporting.py` |
| Do the untracked migrations weaken RLS? | **No** — they only `ENABLE ROW LEVEL SECURITY` on **new** tables (`manual_processing_processors`, `consultant_mp_allocations`, `consultant_relationship_requests`, `consultant_mode_change_requests`). No `DROP POLICY` / `DISABLE ROW LEVEL SECURITY` anywhere |
| Cross-tenant isolation intact | **Yes** — corroborated by the API matrix (§15) |
| Database globally readable after the fix? | **No** — every read still requires an authenticated principal and passes the application guard |

**Gate 14 PASS**, with the informational observation F-IND-3 (§29).

---

## 21. Access-profile findings (Part I)

Source of truth: [`backend/domain/relationship_access.py`](backend/domain/relationship_access.py)
(pure, no I/O, grants nothing). Consumed by
[`backend/api/client_portal_auth.py:164`](backend/api/client_portal_auth.py:164) and
surfaced via `portal_capabilities` in [`backend/api/v3_client_portal.py:68`](backend/api/v3_client_portal.py:68).

| Profile | Read data/reports/evidence | Comment | Upload doc | Edit master data | Correct submitted | Approve final |
|---|---|---|---|---|---|---|
| `off` | (state-dependent) | — | — | — | — | — |
| `read_only` | yes (ACTIVE state) | yes | — | — | — | — |
| `collaborative` | yes (ACTIVE state) | yes | yes | yes | yes | yes |
| `managed` | yes (ACTIVE state) | yes | — | — | — | — |
| `retained_read_only` (ended + flag) | yes (history) | — | — | — | — | — |

* The profile is the **CEILING**, not a grant: effective permission is
  `CAPABILITY ∩ PROFILE ∩ ENTITLEMENT`; it can only reduce.
* **PO-9 is enforced structurally**: `map_factors`, `edit_mappings`,
  `recalculate` are in `CLIENT_FORBIDDEN_OPERATIONS` — forbidden to a client user
  in **every** profile and state, including a Client Organisation Owner.
* **Fail-closed:** an unknown/absent profile normalises to `off`; an operation
  outside `KNOWN_OPERATIONS` is denied. A new operation is never admitted by
  omission.
* **Important, and consistent with the ratified model:** the profile governs the
  **client-facing ceiling** (the client portal). The **consultant's own operating
  plane** admission is driven by the ACTIVE relationship
  (`ensure_consultant_org_access`), not by the profile. This is exactly what
  `…-01.md` §19 documents ("An OFF `client_access_profile` does **not** stop the
  consultant operating the organisation"), and it matches §6.1 (profile = ceiling)
  and §8.3 P-1 (a profile never confers consultant capability onto a client user).
  No divergence from the binding PO model was found.

Observation recorded for completeness: an `off`-profile client is still operable by
the consultant by design, and the UI says so explicitly.

---

## 22. Reporting parity (Part N)

With the same authorised tenant (Client A), the consultant's response and the
customer owner's response were compared **byte-for-byte**:

```text
customer-dashboard   consultant=200 customer=200 byte_equal=True organization_id==client_a: True
emissions-trend      consultant=200 customer=200 byte_equal=True organization_id==client_a: True
member-activity      consultant=200 customer=200 byte_equal=True organization_id==client_a: True
```

No additional tenant access was granted, and no field differs. Adjacent
organisation-plane endpoints (`audit-readiness`, `audit-activity`) also returned
200 for the consultant via the separate consultant-aware
`ensure_org_audit_access` guard — i.e. they were already parity-correct and did not
need the F-NAV-1 treatment.

**Gate 7/8 PASS.**

---

## 23. Team UX findings (Part K)

Independently inspected in the browser:

* **K1** — Team identity is human-readable: members are shown with an email address;
  no raw `user_id` text box is offered. **PASS**
* **K2** — the rendered role vocabulary matches the backend (`owner`, `manager`,
  `consultant`, `viewer`); the previously-invalid "Consultant team member" option is
  gone. **PASS** (`IMPLEMENTATION-PROVIDED EVIDENCE` for the 422 fix; the absence of
  the invalid option is **INDEPENDENTLY VERIFIED**.)
* **K3** — role/capability distinction is explained in the UI ("role is a firm
  classification; capabilities are enforced by the server"). **PASS**
* **K4** — capability administration is server-enforced: `PATCH …/capabilities`
  returned **403 "consultant lacks permission: manage_team"** for a member without
  the capability. **INDEPENDENTLY VERIFIED**
* **K5** — the current architecture **resolves an existing identity by email** and
  does **not** send a signup invitation. This audit found **no** invitation-email
  subsystem and no user-search endpoint. Adding a member therefore requires the
  person to already have an account. This is consistent with the documented state
  (01A §20 / PD-1A) and is reported as a product question, not a defect.

---

## 24. Firm Tasks findings (Part L)

Semantics confirmed by inspection: a firm task is a firm-scoped follow-up item
(`task_title` required, `task_type`/`priority` free text, `status` in
`open/in_progress/done/blocked`, **optional** `client_id`, free-form `metadata`),
listed per firm and owned by the firm — a reminder queue, not the processing
pipeline. The UI correctly labels it as firm-internal and offers a human-readable
client select sourced from `GET /me/clients`.

Backend validation was then tested **directly**, independent of the UI:

```text
no client_id                          -> 201
authorized client_a (org id)          -> 201
UNAUTHORIZED org_a (org id)           -> 201
NONEXISTENT uuid                      -> 201
UNAUTHORIZED client of ANOTHER firm   -> 201
```

**The backend does not validate `client_id` at all.** The UI now presents a
dropdown of authorised clients, so it *implies* a constraint the backend does not
enforce → **F-IND-1** (§29). Impact is bounded: a firm task is a firm-internal
record and creating one confers **no** access to the referenced organisation. This
is precisely the open item already recorded as **PD-3A** in
`…-01A.md` §20; this audit confirms it at the boundary and does **not** fix it.

---

## 25. Client Messages findings (Part M)

* The client selector is **local to the messages view** (a client-scoped surface by
  nature); the firm-level pages carry no client context (§12 A5).
* **No** global "Active client" selector exists anywhere in the Consultant Plane.
* Selecting a client cannot expose another client's messages: the conversations are
  fetched through the consultant-authorised client endpoints and re-authorised
  server-side; the cross-firm relationship id yields the controlled denial
  (§18).
* No client-to-another-client leak was observed in the browser walkthrough.

---

## 26. Direct-customer regression & browser verification (Part Q)

Independent Playwright walkthrough (real headless Chrome, real password logins),
**49 of 50 checks passed**; the single red check was investigated and resolved as a
**harness defect, not a product defect** (see §9/§31).

Direct customer (`owner.clienta`) on `/home`:

```text
no "Back to Consultant"            PASS
no "Working on" consultant context PASS
no consultant firm string          PASS
"Reporting overview" renders       PASS
```

No consultant context module is mounted outside `ClientOrgShell`, so no customer
page can show consultant wording.

Console/network: the only errors were 6× static-asset `404` (a known lab gateway
behaviour) and the **intentional** 403s produced by this audit's own cross-tenant
probes. **No unexpected application console error and no unexpected ≥400 reporting
response** occurred in the product's own traffic.

**Gate 12 PASS, Gate 15 PASS.**

---

## 27. Test-suite results (Part P)

Reported in the task-required form.

### 27.1 Backend — targeted consultant / authorization / reporting suites

Runner: `backend/.venv/bin/python -m pytest` (independent invocation).

| Suite set | collected | passed | failed | skipped | errors |
|---|---|---|---|---|---|
| `test_consultant_org_parity`, `test_ct_consultant_model_02`, `test_ct_consultant_model_03`, `test_ct_consultant_ux_01a_team_identity`, `test_v3_consultants`, `test_reporting`, `test_f05_r1_org_scope_authorization`, `test_scope_aware_authorization`, `test_consultant_branding`, `test_consultant_revocation` | 312 | **312** | 0 | 0 | 0 |

### 27.2 Backend — full `tests/unit/api`

| | value |
|---|---|
| outcome | exactly **1 failure** — `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` |
| assertion | `assert body["verification_delivered"] is False` → `assert True is False` |
| cause (independently established) | `RESEND_API_KEY` **is configured** in `backend/.env`, so `send_transactional_email` really reports delivery; the test's comment says "Email delivery is NOT configured in unit tests" |
| classification | **environment-dependent, pre-existing, unrelated** |

Independent corroboration of "unrelated": both
`backend/tests/unit/api/test_v3_discovery.py` and `backend/api/v3_discovery.py`
are **unmodified** in the worktree, and the failure is in the discovery/email
domain — no consultant, reporting, capability or tenancy file is in its path.
The implementation's identification of this single failure is therefore
**corroborated**, not merely repeated.

### 27.3 Frontend

| Suite set | suites | tests | passed | failed |
|---|---|---|---|---|
| `consultant-page`, `consultant-client-org-shell`, `consultant-ux-navigation`, `consultant-team-capabilities`, `manual-processing-coverage` | 5 | 47 | **47** | 0 |

The wider frontend suite was **not** re-run in full by this audit; the
implementation reports `593/594` with the one failure being
`dr007-investor-display-fixes` Issue 3. That figure remains
`IMPLEMENTATION-PROVIDED EVIDENCE` and is **not** counted toward this verdict.

**Gate 16 PASS** — no new material regression attributable to the six changesets
was found.

---

## 28. Screenshots / evidence index

Screenshots (outside the repository, under
`~/ct_local_env/demo_lab/evidence/browser/`), captured during the independent
walkthrough:

| File | State shown |
|---|---|
| `indep01_consultant_dashboard.png` | Consultant Plane — firm identity, no Active client |
| `indep01_consultant_clients.png` | Clients portfolio with "Open workspace" |
| `indep01_client_a_home.png` | Client A operating plane — context bar, Reporting overview |
| `indep01_client_a_documents.png` | Deeper page — context preserved, one return control |
| `indep01_client_b_home.png` | Client B operating plane |
| `indep01_unauthorised_denial.png` | Another firm's client → "Client not available" |
| `indep01_team.png` | Team — human-readable identity, role/capability copy |
| `indep01_client_messages.png` | Client messages — local selector |
| `indep01_firm_firm.png`, `indep01_firm_white-label.png`, `indep01_firm_team.png`, `indep01_firm_manual.png` | Firm-level pages with no client context |
| `indep01_direct_customer_home.png` | Direct customer `/home` — no consultant leak |
| `indep01_investigate_consultant_client_b.png`, `…_consultant_client_a.png`, `…_client_b_owner_home.png` | Control experiment for the Client B observation |

Command logs: `/tmp/ctaudit/probe_out.txt`, `liveness_out.txt`, `d4_out.txt`,
`browser_out.txt`. Harness sources: `/tmp/ctaudit/{ctprobe,guard_repro,liveness_test,d4_and_cleanup,browser_walkthrough,client_b_investigate}.py`.

---

## 29. Findings table

| ID | Severity | Area | Expected | Actual | Impact | Blocks acceptance |
|---|---|---|---|---|---|---|
| **F-IND-1** | **LOW** | Firm Tasks `client_id` validation | Backend rejects an `client_id` the firm is not authorised for (or at least a nonexistent id) | `201` for authorised, **unauthorised**, **nonexistent**, and **another firm's** client id — no validation | The UI's authorised-client dropdown implies a guarantee the backend does not enforce. Creating such a task confers **no** access (firm-internal record). Already open as **PD-3A** | **No** |
| **F-IND-2** | **LOW** | Client-plane context endpoint oracle | Uniform "not available" for both "not yours" and "does not exist" | `403 "client belongs to another consultant firm"` vs `404 "client not found"` — distinguishes "exists but not yours" from "absent", revealing relationship existence to a firm that does not own it | Requires knowing a relationship id; no org id, name or data is disclosed. Lab relationship ids are deterministic UUIDv5 (`uuid5("carbontally/demo-lab-t1/engagement:<key>")`), so in the lab they are deriveable — production ids should be random | **No** |
| **F-IND-3** | **INFORMATIONAL** | RLS consultant scope vs application admission | Same scope at both layers | `public.is_org_consultant(org)` gates on active firm membership + active grant but **not** on `can_view_client`; the capability gate exists only in `resolve_managed_org_ids` | Defence-in-depth dilution, **not** an open bypass: all consultant surfaces are served by the FastAPI service-role path where the application gate is authoritative. Only relevant if a surface queried PostgREST directly with the user JWT. Code-level observation; not exploited | **No** |
| **F-IND-4** | **INFORMATIONAL** | Reporting endpoints not in F-NAV-1 | — | `audit-readiness` / `audit-activity` already admit the consultant (separate `ensure_org_audit_access` guard) | None — recorded so the F-NAV-1 scope is not mistaken for the whole org plane | **No** |
| **F-IND-5** | **INFORMATIONAL** | Verification methodology | — | The implementation verifiers and this audit both "passed"; a first-pass false negative on Client B was caused by this audit's own fixed 3 s wait, not by the product | None — recorded for transparency (§31) | **No** |

No **CRITICAL** or **HIGH** finding was identified. No authorization bypass,
cross-tenant leak, consultant access to an unrelated organisation, capability
bypass, RLS weakening, or direct-customer regression was found.

---

## 30. Acceptance-gate matrix

| # | Gate | Result | Basis |
|---|---|---|---|
| 1 | UX architecture: Consultant Plane and Client Operating Plane clearly separated | **PASS** | §12, §13, §14 |
| 2 | Navigation: Clients is the client-selection entry point | **PASS** | §12 A3, §14 |
| 3 | Context: consultant is actor, client is subject | **PASS** | §13 B1/B2 |
| 4 | No global Active Client contaminating firm pages | **PASS** | §12 A2/A5 |
| 5 | No Switch Client inside the client operating plane | **PASS** | §13 B4 |
| 6 | Exactly one primary Back to Consultant | **PASS** | §13 B3 (count = 1, twice) |
| 7 | Functional parity: consultant can operate the managed client workspace | **PASS** | §15 D1, §26, §17 |
| 8 | Reporting parity: all three F-NAV-1 endpoints work for authorised consultants | **PASS** | §15, §22 |
| 9 | Tenant isolation: unauthorised organisations remain inaccessible | **PASS** | §15 D2/D3/D9, §18 |
| 10 | Capability isolation: relationship alone does not bypass capability | **PASS** | §17, §15 D4 |
| 11 | Tenant liveness: suspended/ended clients remain inaccessible | **PASS** | §15 D5/D6, §18 |
| 12 | Direct-customer regression | **PASS** | §26, §15 D8/D9 |
| 13 | Membership invariant | **PASS** | §19 |
| 14 | RLS/security not weakened | **PASS** | §20, §16 |
| 15 | Browser evidence (real authenticated flow) | **PASS** | §26, §28 |
| 16 | No new material regression | **PASS** | §27 |

**All 16 gates pass.** Non-blocking findings F-IND-1…F-IND-3 remain open.

---

## 31. Remaining product decisions

| ID | Question | Status |
|---|---|---|
| **PD-NAV-1** | Dedicated consultant "Firm & Billing" surface | **OPEN — PO decision.** Unchanged by this audit; the firm Manual-Processing coverage tab remains the stand-in. |
| **PD-3A** | Should a firm task's `client_id` be validated server-side against an active grant? | **OPEN — PO decision.** Confirmed live as unvalidated (F-IND-1). |
| **PD-1A** | Team identity lifecycle: resolve-existing-identity by email vs a real invitation/signup email + token flow | **OPEN — PO decision.** No invitation subsystem exists today (§23 K5). |
| **PD-2A** | Should a firm admin be permitted to mint additional `owner`s from the Team surface? | **OPEN — PO decision.** |
| **F-IND-2** | Should the client-context endpoint return a uniform 404 for "not yours" and "absent"? | **Recommendation — small hardening.** |
| **R-NAV-1** | Legacy `/consultant/items/:clientId/:itemId` route consolidation | **OPEN — presentational.** Not reachable from the hub; not a competing destination. |

---

## 32. Limitations

1. **Local Demo Lab only.** No production, Render or hosted Supabase surface was
   contacted, per the brief.
2. **Small fixture population.** 2 primary firms + 2 fixture firms, 14
   organisations, 8 relationships. Result generality is bounded by that.
3. **Controlled, restored mutation was required** to observe D4/D5/D6 (declared in
   §6.1). Those three verdicts are therefore "independent, via a reverted
   mutation", not "independent, passive". The final database state was verified
   restored (14/14 organisations active; capability `t`; relationship `active`; 0
   residual probe tasks).
4. **Access-profile verification is inspection/trace-based.** The five-profile
   matrix was established from the single pure source
   (`relationship_access.py`) and its consumption points; it was **not**
   exercised end-to-end through the client portal at the API boundary.
5. **Frontend full suite not re-run.** Only the five consultant/manual-processing
   suites (47 tests) were run; the wider `593/594` figure remains an
   implementation claim.
6. **Precise backend collection count** could not be extracted from the runner's
   `--collect-only` output in this environment; the full-suite run executed and
   produced exactly one failure, which is the material fact.
7. **OCR/email/production capability** was not assessed (out of scope).
8. `IMPLEMENTATION-PROVIDED EVIDENCE` labels mark the handful of properties this
   audit did not reproduce (noted inline).

---

## 33. Final independent verdict

> **The question:** can an authorised consultant safely and coherently operate an
> authorised client through CarbonTally's **Consultant Plane → Clients → Client
> Operating Plane** flow, including reporting, while every unauthorised tenant,
> capability, relationship and lifecycle boundary remains enforced?
>
> **Answer: YES — established independently.**

* The consultant reaches exactly its firm's **5 active grants** (200) and **no**
  other organisation (403) on all three reporting routes, with **byte-identical**
  payloads to the customer's own read.
* Its reach is gated by an **admission capability**; revoking it closes the plane
  on the next request.
* **Ended** relationships and **suspended** tenants close the plane, and the
  consultant relationship does not bypass suspension; the lifecycle predicate
  **fails closed**.
* **Zero** consultants are `organization_members`; isolation is achieved through
  the firm/grant/capability chain alone.
* The UX clearly names the **consultant firm as actor** and the **client as
  subject**, offers **exactly one** return path, and has **no** global active-client
  or workspace switcher — while a direct customer sees no consultant context at all.
* RLS is intact and was not weakened; the F-NAV-1 fix is a two-token guard swap
  with no schema, contract or frontend change.

Three non-blocking findings remain (two LOW, one informational), all already
tracked as open product decisions or explicit hardening candidates. No blocking
finding exists.

---

## Independent Verdict

```text
VERIFIED_WITH_FINDINGS
```

### Blocking findings

_None._

### Non-blocking findings

1. **F-IND-1 (LOW)** — Firm-task `client_id` is not validated server-side; the UI's
   authorised-client dropdown implies a guarantee the backend does not enforce
   (§24). No access is conferred. Tracked as PD-3A.
2. **F-IND-2 (LOW)** — `/api/v3/consultants/clients/{id}/context` distinguishes
   "another firm's relationship" (403) from "does not exist" (404), a minor
   existence oracle; no org id/name/data leaks (§18). Recommend a uniform 404.
3. **F-IND-3 (INFORMATIONAL)** — `is_org_consultant()` omits the `can_view_client`
   gate that `resolve_managed_org_ids()` applies; application-layer enforcement is
   authoritative today, so this is defence-in-depth dilution, not an open bypass
   (§20). Recommend aligning the RLS helper if any surface will ever read via
   PostgREST with the user JWT.
4. **F-IND-4 (INFORMATIONAL)** — `audit-readiness` / `audit-activity` were already
   consultant-aware and outside the F-NAV-1 scope (§22).
5. **F-IND-5 (INFORMATIONAL)** — One first-pass browser check was a false negative
   caused by this audit's harness timing, not by the product; the control
   experiment disproved it (§26, §31).

### Product decisions remaining

1. **PD-NAV-1** — dedicated consultant "Firm & Billing" surface.
2. **PD-3A** — server-side hardening of firm-task `client_id` (see F-IND-1).
3. **PD-1A** — team invitation/signup-email lifecycle vs today's
   resolve-existing-identity-by-email behaviour.
4. **PD-2A** — whether a firm admin may assign the `owner` role from the Team surface.
5. **F-IND-2 remediation** — uniform denial contract for the client-context endpoint.
6. **R-NAV-1** — consolidation of the legacy `/consultant/items/…` route.

### Evidence summary

```text
API          : PASS  — D1–D10 independently probed with real lab tokens;
                       root cause reproduced against the real guard
Browser      : PASS  — 49/50 independent checks (1 = own harness timing,
                       disproved by control experiment); 16 screenshots
Database/RLS : PASS  — 0 consultants in organization_members; RLS enabled with
                       tenant-scoped policies only; no policies weakened;
                       declared mutation fully restored and verified
Frontend     : PASS  — 47/47 consultant + manual-processing suites;
                       actor/subject/return-path contract verified in a real browser
Regression   : PASS  — backend targeted 312/312; full tests/unit/api = 1 failure
                       (environment-dependent Resend config, unrelated unmodified
                       module); no new material regression
```

### Recommendation

```text
PO ACCEPTANCE
```

The combined implementation may proceed to Product-Owner acceptance: every material
acceptance gate passes and no blocking finding remains. PO acceptance should be
recorded together with **F-IND-1**, **F-IND-2** and **PD-NAV-1/PD-3A/PD-1A/PD-2A** as
open, non-blocking items (a small hardening/decision backlog).

This is **not** a recommendation to deploy to production: this audit was performed
entirely on the local Demo Lab, one backend API-suite failure remains
environment-dependent, and several production-capability questions (OCR parity,
email delivery configuration, deployment topology) are outside its scope and remain
unverified.

---

*End of report — CT-CONSULTANT-UX-PARITY-INDEPENDENT-VERIFY-01.*
