# CT-CONSULTANT-MODEL-IMPLEMENTATION-02 — Consultant capability admission & approval (change map)

| | |
|---|---|
| **Status** | IMPLEMENTED · TESTED (unit) · LAB-VERIFIED · UI NOT WIRED (follow-on) |
| **Task** | `CT-CONSULTANT-MODEL-IMPLEMENTATION-02` |
| **Predecessor document** | `docs/architecture/CT-CONSULTANT-MODEL-DECISION-AND-IMPLEMENTATION-01.md` |
| **Decision source** | `docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md` — §7.2/§7.3, §7.4, §8.3, §13.1, §17.1 (F-1, F-2), §17.2 (F-10), §20.1 (AC-F-1 / AC-F-2 / AC-F-18), §20.4 (NT-10…NT-12, NT-24) |
| **Repository** | `/home/shomonrobie/ct_93d5cdd` |
| **Git at time of writing** | branch `p8-release-reconciled`, HEAD `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` |
| **Agent** | Cline (implementation) |
| **Date** | 2026-10-06 |

> **Change markers.** Every CT02 hunk carries the literal string
> `CT-CONSULTANT-MODEL-IMPLEMENTATION-02`, so the CT02 delta is mechanically
> separable from the neighbouring uncommitted workstreams that share this
> working tree (§3.3, §14.1). Use
> `grep -rl 'CT-CONSULTANT-MODEL-IMPLEMENTATION-02'` to re-derive the file list.

---

## 1. What this document is

This is the **change map / implementation report** for Phase 1 of the ratified
consultant model, not a new decision record. The business decisions are already
ratified in `CT-CONSULTANT-PO-CONSOLIDATION-01.md`; `…-01.md` recorded them as a
decision + implementation intent. This document records **what was actually
implemented, why each hunk exists, how it was verified, and what remains open**,
in the layout required by AGENTS.md §84.

Findings closed in this increment: **F-1, F-2, F-10**.

---

## 2. Scope

### 2.1 In scope (implemented here)

| Finding | Requirement (PO consolidation) | Delivered |
|---|---|---|
| **F-1** | Consultant **admission** must be capability-gated. Existence of an ACTIVE `consultant_clients` grant must never, by itself, admit a firm member to a client organisation (§7.3 CAP-VIEW-CLIENT, §7.4). | `consultant_firm_members.can_view_client` + deny-by-default gate inside the shared admission resolver |
| **F-2** | A consultant had **no** final-approval capability; only CarbonTally staff flags existed. PO-6 (B+C) / §13.1 makes consultant final approval an explicit capability, separable from processing/mapping. | `consultant_firm_members.can_approve` + `ensure_consultant_approval_authorized` (ACTIVE engagement **and** capability) + customer-review route rewired onto a single shared authority resolver |
| **F-10** | A capability write must **MERGE**, never REPLACE: granting one capability must not silently revoke another. | Allow-listed merge-only repository write + `PATCH /me/team/{member_id}/capabilities` admin surface + denial tests |

Admission is **deny-by-default**: both columns are `NOT NULL DEFAULT false`, so
nothing is granted by omission (AC-F-18).

### 2.2 Explicitly out of scope (still open — see §11/§12)

F-3…F-9 and the other §17 items (client-profile gating, subscription/entitlement
gating, branding, handover, billing, portfolio UX, PE plane). Nothing in this
increment alters them, and nothing here should be read as closing them.

---

## 3. Change map

### 3.1 CT02-attributable files (marker: `CT-CONSULTANT-MODEL-IMPLEMENTATION-02`)

| # | File | Symbols / region | What changed and why |
|---|---|---|---|
| 1 | `supabase/migrations/20261102000000_ct_consultant_model_02_capability_admission.sql` **(new)** | `consultant_firm_members.can_view_client`, `.can_approve`, column COMMENTs, IMPL-1 backfill | Additive columns, `NOT NULL DEFAULT false` (deny-by-default, AC-F-18). Explicit backfill of `can_view_client = true` for already-existing active members (preserve de-facto scope); `can_approve` deliberately **not** backfilled because no consultant path could previously approve (that *is* F-2). **No RLS change.** See §4. |
| 2 | `backend/api/consultant_auth.py` | `CONSULTANT_PERMISSIONS` (+`view_client`→`can_view_client`, `approve`→`can_approve`); `resolve_managed_org_ids` (F-1 gate, 180-186); `ensure_consultant_approval_authorized` (new, 302); `ensure_customer_approval_authority` (new, 348); imports of the shared `auth` decisions (33-44) | F-1: admission is capability-gated — a member without `can_view_client` resolves to an **empty** managed-org scope, so the whole `ensure_org_access` family denies. F-2: one shared FINAL-approval resolver returning the **capacity string** (`"internal_staff"` / `"organisation"` / `"consultant"`), re-using `ADMIN_ROLE_NAMES`, `_org_admin_authority`, `_caller_organization_inactive`, `ORGANIZATION_SUSPENDED_DETAIL` **imported** from `auth` rather than re-implemented (no second definition of "may administer this organisation"). |
| 3 | `backend/api/v3_processing_workflow.py` | `customer_review_item` (968-990) | The route-level `require_org_admin()` dependency is replaced by `get_current_user` + an in-handler call to `ensure_customer_approval_authority` **after** the resource is loaded, because the gate needs the item's *server-derived* `organization_id`. Runs before any workflow/billing mutation (D37 credit consumption stays after the gate → fail-closed preserved). |
| 4 | `backend/api/v3_consultants.py` | `FirmMemberCapabilitiesUpdate` (new model, ~182); `get_my_profile` (+`can_view_client`, `can_approve`, ~258); `list_my_team` (+both flags per roster row, ~984); `update_team_member_capabilities` (new route, ~1115) | F-10 administration surface: `PATCH /api/v3/consultants/me/team/{member_id}/capabilities`. Firm is resolved from the authenticated context (never the request), the target must belong to that firm (else 404), the caller must hold `manage_team`, a member may not edit their **own** set, and the write is a MERGE. |
| 5 | `backend/data/consultants.py` | `_MEMBER_COLUMNS` (+`can_view_client, can_approve`); `_row_to_member` (deny-by-default fallback); `set_firm_member_capabilities` (new, 369) | Read path selects the two new columns; write path is allow-list restricted (`_CAPABILITY_COLUMNS`) and merge-only (`UPDATE … SET <named flags>`), so a caller can never address `role`/`client_access`/`is_active` through the capability path, and cannot revoke by omission. Returns `None` → caller maps to 404. |
| 6 | `backend/domain/partners.py` | `ConsultantFirmMember.can_view_client`, `.can_approve` | Domain fields default `False`, so an object built without the column (legacy fake / un-backfilled row) denies rather than admits. |
| 7 | `backend/tests/unit/api/test_ct_consultant_model_02.py` **(new)** | 28 collected tests (27 functions) in 4 classes | CT02 regression suite — see §8. |
| 8 | `backend/tests/unit/api/test_scope_aware_authorization.py` | expectation updates | Existing scope-aware suite re-pinned against capability-aware admission. |
| 9 | `backend/tests/unit/api/fakes.py` | `seed_firm_member` capability params (1636), fake `set_firm_member_capabilities` (1750) | In-memory mirror of the real repository contract (merge semantics + allow-list) so unit tests exercise the real routers/guards, not a stub. |
| 10 | `tools/demo_lab/provision.py` | capability defaults (304-317) | Lab members are provisioned with `can_view_client` default **True** (a freshly provisioned lab must be usable) and `can_approve` default **False**, overridable per manifest identity. |
| 11 | `tools/demo_lab/verify.py` | 2 capability probes (147-157) + optional `body` expectation in `run_probes` (229-235) | Live probes assert the *server* exposes the two flags (`consultant_owner` → both true; `consultant_member` → view true / approve false) — the negative control that keeps "engagement alone = approval" impossible. |
| 12 | `tools/demo_lab/manifest.json` **(related, no marker)** | `capabilities` per identity (118-132) | `consultant_owner` → `{can_view_client: true, can_approve: true}`; `consultant_member` ("restricted capabilities / least privilege") → `{can_view_client: true, can_approve: false}`. |

### 3.2 Behavioural delta (before → after)

| Situation | Before | After |
|---|---|---|
| Firm member, ACTIVE grant, no `can_view_client` | Admitted to the client organisation ("has relationship = full access", forbidden by §7.4) | Managed-org scope is `()`, every organisation-guard route denies |
| Firm member, ACTIVE grant, `can_view_client` | Admitted | Admitted (unchanged) |
| Grant revoked / `pending` / `ended` / `suspended` (D15) | Not admitted | Not admitted (capability never overrides lifecycle) |
| Consultant, ACTIVE engagement, wants FINAL approval | No consultant path existed → 403 | Admitted **only** with `can_approve`; approval recorded in the `consultant` capacity |
| Consultant, ACTIVE engagement, no `can_approve` | 403 (for the wrong reason) | 403 with an explicit capability detail |
| Consultant, `can_approve`, no ACTIVE engagement | n/a | 403 (capability never substitutes for the engagement) |
| Org owner/admin, internal admin staff | Admitted (D5 / §13) | Admitted, byte-for-byte the previous `require_org_admin` outcome, incl. D-7 suspended-org detail |
| Capability write granting one flag | n/a | Other flags preserved (MERGE, F-10) |

### 3.3 What is *not* CT02 (same working tree)

> ⚠️ **Reviewer note.** This working tree contains other uncommitted
> workstreams: `CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01`,
> `CT-MP-SUB-003/004` (manual-processing routing, consultant coverage,
> notification-implement-04) and `FIN-06`. Files modified by those streams but
> **not** carrying the CT02 marker include `backend/auth.py`,
> `backend/api/dependencies.py`, `backend/api/router.py`,
> `backend/api/v3_operations.py`, `backend/data/organizations.py`,
> `backend/domain/manual_processing.py`,
> `backend/services/manual_processing_*.py`, `backend/services/work_items.py`
> and the `test_manual_processing*` / `test_fin06*` suites.

**CT02 is stacked on the parity workstream, not independent of it.** The F-1
gate lives inside `resolve_managed_org_ids`, a function introduced by
`CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01` (`PD-3/PD-7`; see the
docstring at `consultant_auth.py:167-173`). CT02 changes the *decision* that
function makes but does not own the function. Consequently:

* CT02 cannot be committed or deployed in isolation without also carrying the
  parity workstream (or an equivalent `resolve_managed_org_ids`).
* Reviewer guidance: attribute lines inside those shared files by marker, not
  by file.

---

## 4. Database change

**Migration:** `supabase/migrations/20261102000000_ct_consultant_model_02_capability_admission.sql`
(new file, applies after `20261101000000_ct_mp_sub_003_consultant_coverage.sql`).

### 4.1 DDL

```sql
ALTER TABLE public.consultant_firm_members
    ADD COLUMN IF NOT EXISTS can_view_client boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS can_approve     boolean NOT NULL DEFAULT false;
```

Both columns carry `COMMENT ON COLUMN` text quoting the PO consolidation
sections they implement (§7.3 CAP-VIEW-CLIENT / CAP-APPROVE, §7.4, §13.1). The
migration is **idempotent** (`IF NOT EXISTS`, guarded backfill).

### 4.2 Backfill policy (IMPL-1)

```sql
UPDATE public.consultant_firm_members
   SET can_view_client = true, updated_at = NOW()
 WHERE coalesce(is_active, true) = true
   AND can_view_client = false;
```

* **Rationale:** before this migration an ACTIVE firm member already reached
  every organisation the firm held an ACTIVE grant for. Landing the F-1 gate
  without a backfill would have silently revoked every already-provisioned
  consultant, including the investor-demo roster (AGENTS.md §54/§55 — do not
  destroy legitimate demo relationships). The de-facto scope is therefore
  preserved **explicitly** as a granted CAP-VIEW-CLIENT.
* **`can_approve` is deliberately NOT backfilled.** No consultant code path
  could give final approval before CT02 (that is exactly finding F-2), so
  backfilling it would *invent* an authority nobody held. It must be granted
  explicitly through the capability-write path.
* Rows created after the migration keep both columns at their `false` default
  (deny-by-default, AC-F-18).

### 4.3 RLS

**No RLS policy is added, dropped, disabled or weakened** (AGENTS.md §67). The
two columns are read by the application authorization layer
(`backend/api/consultant_auth.py`), not by RLS. Consultant data scope continues
to be resolved through the existing `public.is_org_consultant(org)` helper.

### 4.4 Migration-order / numbering note

The `20261102000000` timestamp places CT02 immediately after
`20261101000000_ct_mp_sub_003_consultant_coverage.sql` (the in-flight MP-SUB-003
stream, §3.3) and is the newest migration in the tree. Four migration-contract
tests in the existing suite hardcode historical "latest migration" expectations;
they fail for that reason and **not** because of CT02 — see §8.4.

---

## 5. Authorization model

### 5.1 F-1 — capability-gated consultant admission

Admission is resolved **server-side** from authoritative membership rows and
never from client input. The single source of a consultant's organisation scope
is `resolve_managed_org_ids` (`backend/api/consultant_auth.py:155`):

```
authenticated principal
  → _resolve_context(...)            # consultant firm membership (else None)
  → context.firm_member.can_view_client ?      # F-1 GATE (§7.2/§7.4)
        NO  → return ()            # EMPTY scope — every org-guard route denies
        YES → repos.consultants.list_clients(profile.id)
                 → {active grants only}  (D15: pending/ended/suspended grant nothing)
```

```
None ctx → ()        # customer, internal staff, PE staff, brand-new user
no cap   → ()        # has an ACTIVE relationship but no CAP-VIEW-CLIENT
cap      → (org ids of ACTIVE grants)
```

The returned tuple is consumed by the organisation-guard family
(`backend/auth.py` / `backend/api/dependencies.py`, parity workstream) via
`ensure_org_access`, so the gate applies uniformly to **every** route that
reuses the organisation guard — not just consultant-specific endpoints.

**Properties guaranteed by construction:**

* the gate can only ever **narrow** admission (a test asserts it never widens);
* lifecycle beats capability — the capability cannot revive a non-active grant;
* revoking the capability takes effect on the **next** request (no caching in the
  decision path).

### 5.2 F-2 — the shared FINAL-approval resolver

`ensure_customer_approval_authority(current_user, repos, *, organization_id)`
(`consultant_auth.py:348`) returns the **capacity string** in which approval is
taken — one of `"internal_staff"`, `"organisation"`, `"consultant"` — so the
caller can record/display who approved and in what capacity (§13.2 A-1,
DELTA-16). Precedence, failing closed:

| # | Capacity | Rule |
|---|---|---|
| 1 | `internal_staff` | Internal staff **and** (`ADMIN_ROLE_NAMES` role, or role_name in `ADMIN_ROLE_NAMES`, or `is_superuser`) — the platform's pre-existing operational authority, unwidened (AGENTS.md §13/§14) |
| 2 | `organisation` | `_org_admin_authority(user, organization_id)` — D5 owner/admin, **unchanged** |
| 2b | — | Caller's **own** organisation inactive and it *is* this organisation → 403 `ORGANIZATION_SUSPENDED_DETAIL` (D-7 Decision B, preserving the old dependency's pre-data-read denial) |
| 3 | `consultant` | Not staff and not an org member → ACTIVE engagement for that org **and** `ensure_consultant_permission(context, "approve")` (CAP-APPROVE) |
| — | 403 | Anything else → `"Organization admin privileges required"` (identical detail to `require_org_admin`, so no new information is disclosed) |

`ensure_consultant_approval_authorized(...)` (`consultant_auth.py:302`) is the
CAP-APPROVE-only half, used where only the consultant capacity is admissible:
ACTIVE grant first (403, explicit "active consultant-client grant required"
detail), then `can_approve` (403, `consultant lacks permission: approve`).

`ensure_consultant_permission` maps a permission name to its column via
`CONSULTANT_PERMISSIONS`; an unknown name is a **422** (`unknown consultant
permission`), a `False` column is a **403**. CT02 added
`view_client → can_view_client` and `approve → can_approve` to that map.

**The relationship alone never confers approval** (PO-6 B+C, §7.4/A-2): an
engagement without `can_approve` is denied exactly as firmly as a capability
without an engagement.

### 5.3 Where the gate runs

`POST …/items/{item_id}/customer-review` previously used the route-level
`require_org_admin()` dependency. A dependency cannot see the loaded resource's
`organization_id`, so the gate is now invoked **in the handler, immediately
after** `_get_checked_item(...)` resolves the item, and **before** any workflow
or billing mutation:

```
item, batch = await _get_checked_item(current_user, repos, item_id)
ensure_customer_approval_authority(... organization_id=item.organization_id ...)
... status transition ...  →  D37 credit consumption (fail closed, unchanged)
```

Ordering matters and was preserved deliberately: a denied approval performs
**zero** workflow/billing mutation, and the D37 charge still happens before the
item is marked approved.

---

## 6. API surface

Router prefixes (unchanged): consultants `/api/v3/consultants`,
processing workflow `/api/v3/processing`. **No new router was created and no
existing route was renumbered** (AGENTS.md §65).

### 6.1 Changed / added contract

| Method & path | Change | Authorization |
|---|---|---|
| `GET /api/v3/consultants/me` | **+** `can_view_client`, `can_approve` (booleans) | `require_consultant` |
| `GET /api/v3/consultants/me/team` | each roster row **+** `can_view_client`, `can_approve` | `require_consultant` |
| `PATCH /api/v3/consultants/me/team/{member_id}/capabilities` | **new** — partial capability grant/revoke | `require_consultant` + `manage_team` |
| `POST /api/v3/processing/items/{item_id}/customer-review` | authority now resolves through `ensure_customer_approval_authority`; response/state contract unchanged | org owner/admin (D5) **or** internal admin staff **or** consultant with ACTIVE engagement + `can_approve` |

The exposed capability flags **mirror server state; they do not create
authority** — the UI is never the security boundary (§7.4 / AGENTS.md §44).
They exist so a UI can *present* the same decision the backend already enforces.

### 6.2 Capability write semantics (F-10)

Request body — `FirmMemberCapabilitiesUpdate`, all fields optional:

```json
{ "can_view_client": true, "can_approve": false }
```

| Case | Result |
|---|---|
| Caller holds `manage_team`, target is in the caller's firm | **200** — MERGE applied, returns `{"member": {...}, "changed": {...}}` |
| Caller lacks `manage_team` | **403** (`ensure_consultant_permission` before any write) |
| Caller targets **their own** membership row | **422** — no silent self-escalation to CAP-APPROVE |
| Target member belongs to a different firm / does not exist | **404** — the firm is taken from the authenticated context, never the request |
| Payload `{}` or `{"can_approve": null}` | **422** — a no-op replace is refused rather than silently treated as a revoke |
| A forged non-capability field, e.g. `{"can_manage_team": true}` | **422** — the model ignores unknown fields, so nothing is left to write; the flag is **not** granted |
| Repository called directly with a non-capability column (e.g. `is_active`) | `ValueError` — the write path is allow-list restricted |

Every successful change writes an append-only audit entry
(`entity_type="consultant_firm_member"`,
`action="consultant.team.capabilities_updated"`, `changed_fields={"before": …,
"after": …}`) via `_audit_team_member_capability_change` (§13.1/§13.2 A-1, A-6).

### 6.3 Not exposed

The migration writes only two capabilities, but
`set_firm_member_capabilities` allow-lists seven columns
(`can_view_client`, `can_approve`, `can_manage_clients`, `can_upload_documents`,
`can_generate_reports`, `can_manage_team`, `can_extract`). Only the two CT02
capabilities are addressable through the HTTP surface; the remaining
capabilities are reachable solely through repository-level APIs already used by
provisioning. Whether the rest should become firm-administerable over HTTP is a
follow-on (§12) and is **not** silently granted here.

---

## 7. Demo-lab wiring and runtime evidence

### 7.1 Lab topology (local)

| Surface | Endpoint |
|---|---|
| Database | `carbontally_demo_local` @ `127.0.0.1:54426` |
| Gateway (Supabase auth) | `http://127.0.0.1:54430` |
| Backend | `http://127.0.0.1:8070` |
| Frontend | `http://localhost:3000` |
| Lab state dir | `~/ct_local_env/demo_lab` |

`tools/demo_lab/stack.py` re-applies **all** migrations on bring-up, so the
CT02 migration is exercised by an ordinary lab bring-up (no manual SQL step).

### 7.2 Wiring added by CT02

* `tools/demo_lab/provision.py` (304-317) — reads an optional `capabilities`
  block per manifest identity; `can_view_client` defaults **True**,
  `can_approve` defaults **False**.
* `tools/demo_lab/manifest.json` (118-132) — `consultant_owner` holds both;
  `consultant_member` ("restricted capabilities / least privilege") holds
  admission but **not** approval.
* `tools/demo_lab/verify.py` (147-157, 229-235) — two live probes plus
  optional body expectations in `run_probes`, so a probe can assert **field
  values**, not merely a status code.

### 7.3 Runtime evidence

```
probe database                 : PASS — carbontally_demo_local on 127.0.0.1:54426
probe gateway                  : PASS — GET /auth/v1/health -> 200
probe backend                  : PASS — GET /health -> 200
probe frontend                 : PASS — GET / -> 200 (app shell served: True)
probe frontend_to_backend_cors : PASS — OPTIONS /api/v3/me/context -> 200
supervised backend             : pid=2402309 restarts=0 last_exit_code=None
supervised frontend            : pid=2402311 restarts=0 last_exit_code=None
```

Live probe buckets: **routing 14/14 · authorization 32/32 · isolation 18/18**
(including the two CT02 capability probes and their negative control).

Database evidence (lab):

```
consultant_firm_members:
  can_approve      | boolean | default=false
  can_view_client  | boolean | default=false

identity                                 role     active view  approve
consultant.member@demo-lab…local         consultant  t     t      f   ← admission, no approval
consultant.owner@demo-lab…local          owner       t     t      t
mp.consultant.allel@demo-lab…local       owner       t     t      f
mp.consultant.selected@demo-lab…local    owner       t     t      f

active engagements: 5
```

Read this evidence as: the columns exist with the deny-by-default default; a
member can be admitted to client work **without** holding approval authority;
and the approval capability is genuinely per-member rather than implied by the
firm relationship (the two MP-SUB-003 sponsored consultants hold admission and
**no** approval).

Re-verified live on **2026-10-06**, after the §11–§14 documentation edits:

```
GET /health                      -> 200
GET /auth/v1/health              -> 200
GET / (frontend)                 -> 200
verify.py actor contexts         -> 14/14 correct  (auth: password_grant)
verify.py probes                 -> 32/32 as expected
verify.py isolation rules        -> 18/18
verify.py                        -> no RESULT: FAILED, no KNOWN PRODUCT DEFECT
```

Evidence JSON (outside the repository):
`~/ct_local_env/demo_lab/evidence/verify_20261006T102636Z.json`. The two CT02
probes in that run are *"consultant owner holds CAP-VIEW-CLIENT + CAP-APPROVE"*
and *"consultant member holds CAP-VIEW-CLIENT, not CAP-APPROVE"* (both PASS).
The database rows above were re-read at the same time and matched exactly
(4 firm members: `consultant` and 2× `owner` admitted with approval **false**,
1× `owner` with approval **true**; 5 engagements).

---

## 8. Tests

### 8.1 New CT02 suite — `backend/tests/unit/api/test_ct_consultant_model_02.py`

28 collected tests in 4 classes (27 test functions — `TestCapabilityAdministrationMerge::test_empty_or_null_payload_is_rejected` is parametrized over two payloads, so that class collects 10). The suite pins `auth.is_organization_active` exactly as
`test_consultant_org_parity.py` does, so the decision under test is the
capability rule rather than store availability.

| Class | Tests |
|---|---|
| `TestCapabilityGatedAdmission` (5) | active grant **without** CAP-VIEW-CLIENT grants no scope; the capability admits the same grant; the capability does **not** override the grant lifecycle; revoking takes effect on the next request; the F-1 gate only ever **narrows** admission |
| `TestConsultantFinalApprovalAuthority` (11) | manager with CAP-APPROVE + active engagement approves; engagement without CAP-APPROVE denied; CAP-APPROVE without engagement denied; approval scoped to the engaged org; deactivated member denied; org owner keeps the organisation capacity; plain org member denied; internal admin keeps staff capacity; operational staff gains none; PE staff gains none; non-consultant denied with the standard detail |
| `TestCapabilityAdministrationMerge` (9 functions · 10 collected) | granting one capability preserves every other; revoking one preserves the other; roster reports both; a member cannot change their own set; the write requires `manage_team`; another firm's member is not addressable (404); forged capability names cannot be written; empty/null payload rejected; the repository rejects a non-capability column |
| `TestCapabilityWiring` (2) | `/me` exposes both capabilities; the customer-review route uses the **shared** approval helper (structural: authority is not re-implemented per route) |

### 8.2 Existing suites re-pinned

`test_scope_aware_authorization.py` and `test_consultant_org_parity.py` continue
to pass with capability-aware admission; the in-memory `fakes.py` repository
mirrors the real merge/allow-list contract, so the guards under test are the
real ones.

### 8.3 Consultant/CT02 delta — GREEN

```
tests/unit/api/test_ct_consultant_model_02.py · test_scope_aware_authorization.py ·
test_consultant_org_parity.py · test_p6_2a … p6_2e (10 files) ·
test_f05_r1_org_scope_authorization.py
→ 306 passed, 0 failed   (0 F / E in the run; re-run after the §11–§14 edits)
```

Selection composition, from `--collect-only` (14 files, 306 collected):

```
test_consultant_org_parity.py                         31
test_ct_consultant_model_02.py  (new, CT02)           28
test_f05_r1_org_scope_authorization.py                35
test_p6_2a_consultant_processing_authorization.py     18
test_p6_2a_r1_b1_automation_confirm_retry.py          14
test_p6_2b_1_consultant_review.py                     16
test_p6_2b_2_consultant_submission.py                 29
test_p6_2b_3_ct_qc_decision.py                        25
test_p6_2b_4_ct_qc_prerequisite.py                    13
test_p6_2c_approval_boundary.py                       30
test_p6_2d_entitlement.py                              2
test_p6_2d_provenance.py                              19
test_p6_2e_consultant_lifecycle.py                    27
test_scope_aware_authorization.py                     19
                                                    ────
                                                     306
```

The interpreter matters: `pytest` lives in the backend virtualenv, so run it as
`./.venv/bin/pytest` from `backend/` (the repo-root `.venv` has no `pytest`
installed — see §13.1).

### 8.4 Whole-suite status and failure attribution

The full backend unit suite contains **8 failures**, all reproduced and
attributed as **not CT02** (reproduced in a clean HEAD worktree at HEAD
`3fec874`, plus a controlled `.env` A/B experiment):

| Count | Failing tests | Cause | Evidence it is not CT02 |
|---|---|---|---|
| 3 | `unit/engines/test_extraction_suggestions.py` | Pre-existing at HEAD | Reproduced in a clean HEAD worktree; `services/extraction_suggestions.py` and the engines module are **unmodified by CT02** |
| 4 | migration-contract / "latest migration" tests | Hardcoded historical expectations (71 migration files, last = `20261007000000_…`) written before **any** in-flight migration | Reproduced in a worktree containing only the pre-existing (unmarked) MP-SUB migrations and **without** the CT02 migration → same 4 failures, same class |
| 1 | `test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` | Local developer configuration: `backend/.env` supplies SMTP/Resend settings, so the fake settings layer reports `verification_delivered = True` where the test documents "email delivery is NOT configured in unit tests" | Decisive A/B: the test **passes** in the clean worktree without `backend/.env` and **fails** in the same worktree as soon as `backend/.env` is copied in. `v3_discovery.py`, `services/v3_email.py` and the settings repository are **unmodified by CT02**; `backend/.env` is gitignored (`.gitignore:83`) |

Net: **CT02 adds 28 passing tests and introduces zero new suite failures.** The
pre-existing failures above are recorded as regression targets for whoever owns
them; they are not acceptance evidence against this increment, and equally they
are **not** fixed by it.

Re-verified after the §11–§14 additions, on **2026-10-06**, with
`cd backend && ./.venv/bin/pytest tests/unit -q`. Collection for the whole
backend unit tree is **5,081 tests**; the run produced exactly the eight
`FAILED` lines below — the same tests as the table, no more and no others:

```
FAILED tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice
FAILED tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved
FAILED tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage
FAILED tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged
FAILED tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration
FAILED tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy
FAILED tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp
FAILED tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin
```

The two attribution claims in the table were independently re-checked against
the tests themselves: `test_i1_migration_is_the_latest_migration` pins the
latest migration to `20261007000000_p8_insight_data_quality_reproducibility.sql`
and `test_d17_provider_ownership_migration_revision.py:264` asserts
`len(names) == 71`, while the live tree holds **101** migration files (newest
`20261102000000_…`, this increment). Both expectations predate every in-flight
migration, so neither can be a CT02 reaction.
(CT02's own file, `test_ct_consultant_model_02.py`, is not among the failures.)

---

## 9. Frontend / UX surface

### 9.1 What the backend now exposes

`GET /api/v3/consultants/me` and `GET /api/v3/consultants/me/team` return
`can_view_client` and `can_approve` per member. These are **presentation
inputs**: the UI may mirror the decision, but the backend is the authority
(AGENTS.md §44).

### 9.2 Current consumer state — verified, and it is a gap

Verified by grep over `frontend/src`:

* **No frontend code reads either flag.** The only hits for
  `can_approve` / `can_view_client` in the whole frontend are **zero**;
  the many hits for the word "capabilities" refer to the unrelated *product*
  capability catalogue (`/api/v3/capabilities`, `CapabilitiesPage`,
  `CapabilityTruthSurface`).
* **No API client function exists** for
  `PATCH /api/v3/consultants/me/team/{member_id}/capabilities`
  (`frontend/src/v3/api.js` exposes only `getConsultantTeam`,
  `addConsultantTeamMember`, `deactivateConsultantTeamMember`,
  `reactivateConsultantTeamMember`).
* `frontend/src/v3/consultant/ConsultantTeamTab.jsx` **already has a
  "Capabilities" column**, but it renders only four flags
  (`can_manage_clients`, `can_upload_documents`, `can_generate_reports`,
  `can_manage_team`). The two CT02 flags are **not** shown, and there is no
  grant/revoke control.

> **Naming trap (recorded so it is not mis-reported).** The route
> `/consultant/clients/:clientId/capabilities` (`frontend/src/App.js:2274`)
> is **not** firm-member capability administration — it renders
> `CapabilitiesPage`, the public "what CarbonTally supports" surface, inside a
> client shell. It is unrelated to CT02 despite the path.

The practical consequence: an internal/consultant operator **cannot currently
see** which firm member is admitted to client work, nor who holds approval
authority, nor grant either — even though the backend enforces both correctly.

### 9.3 Why it is not fixed in this increment

Deliberate scope control, not an oversight:

1. **Authority, not chrome.** F-1/F-2/F-10 are authority-boundary fixes; the
   server-side decision is complete, enforced and tested. A missing control
   cannot grant authority it is denied (§44) — the gap is *visibility*, not
   *security*.
2. **No test can currently catch the change.** `ConsultantTeamTab` is
   **mocked** in the only test that references it
   (`frontend/src/v3/__tests__/consultant-page.test.jsx:21` → `jest.mock(...)`),
   so extending that table would land untested.
3. **Where capability administration belongs in the UI is a product
   decision** — firm-admin-only? internal-only? both? That is
   `PO DECISION REQUIRED` (§62), not an implementation call to improvise.
4. This working tree already carries four uncommitted workstreams (§3.3);
   adding an untested frontend consumer to it would blur attribution further.

---

## 10. Acceptance traceability

Status vocabulary per AGENTS.md §73: **IMPLEMENTED** ≠ **TESTED** ≠ **VERIFIED**
≠ **ACCEPTED**. Nothing in this document claims `ACCEPTED`.

| PO criterion | Text (as ratified) | Where enforced | Test | Lab | Status |
|---|---|---|---|---|---|
| **AC-F-1** | "Consultant admission requires `CAPABILITY ∩ PROFILE ∩ ENTITLEMENT`; relationship existence alone never admits" | `resolve_managed_org_ids` F-1 gate: `can_view_client` **∩** ACTIVE grant ⇒ scope; else `()` | `TestCapabilityGatedAdmission` (5) — incl. "ACTIVE relationship + missing capability ⇒ DENY" and the never-widens property | `consultant_member` provisioned view=true; DM evidence shows the column default `false` | **IMPLEMENTED · TESTED · LAB-VERIFIED** (capability ∩ relationship legs). The **ENTITLEMENT** leg (what the firm has *bought*, §6.2 "COMMERCIAL ENTITLEMENT") is F-3…F-9 and is **not** claimed here — see §2.2 |
| **AC-F-2** | "`CAP-APPROVE` exists for consultant firm members, grantable/revocable, separable from processing and mapping" | `can_approve` column; `ensure_consultant_approval_authorized` / `ensure_customer_approval_authority` (capacity `"consultant"`); grant/revoke via the F-10 route | "Grant/deny pair on the approval endpoint": `TestConsultantFinalApprovalAuthority` (11) | both CT02 capability probes; MP-SUB consultants hold admission with approval **false** (separation is visible in data, not just asserted) | **IMPLEMENTED · TESTED · LAB-VERIFIED** |
| **AC-F-18** | "Capability grant/revoke is per-capability and merges; no wholesale replacement; nothing is granted by omission" | `NOT NULL DEFAULT false` on both columns; `set_firm_member_capabilities` merge-only + allow-list | `TestCapabilityAdministrationMerge` (9) — merging one preserves the other, omitted keys stay at their stored value | column defaults read back as `false`; `verify.py` asserts `member` view=true/**approve=false** | **IMPLEMENTED · TESTED · LAB-VERIFIED** |
| **NT-10** | "Entitled firm, member without the capability" → DENY | F-1 gate returns empty scope | `TestCapabilityGatedAdmission` (deny case) | capability probe negative control | **TESTED · LAB-VERIFIED** |
| **NT-11** | "Capable member, relationship not ACTIVE" → DENY | `list_clients` returns ACTIVE grants only (D15); capability cannot revive | "capability does not override the grant lifecycle" | — | **TESTED** |
| **NT-12** | "Relationship ACTIVE, capability absent" → DENY | "ACTIVE engagement without `can_approve`" → 403 | both admission **and** approval suites | `consultant_member` (view true / approve false) | **TESTED · LAB-VERIFIED** |
| **NT-24** | "Capability write omitting a key, or wholesale" → "Missing keys stay DENY; other keys preserved" | merge-only write; empty/null payload → 422 | `TestCapabilityAdministrationMerge` | — | **TESTED** |
| **INV-A…INV-G / R-1** | F-1 is a live over-permission path, not a gap; "fix admission first … prove it with NT-10…NT-12" | the gate precedes every consumer of `resolve_managed_org_ids` | isolation bucket 18/18 + authorization 32/32 | live probes | **IMPLEMENTED · TESTED · LAB-VERIFIED** |

### 10.1 Security verification shape

Per AGENTS.md §72, the boundary was tested in **both** directions: for each
capability there is an ALLOW case **and** a DENY case, plus a negative control
that the *relationship alone* admits/approves nothing. The never-widens
assertion is the strongest form of that check: admission can only narrow.

Due to an environment constraint, this session may not run the browser-based
negative persona checks; the DENY evidence above is **API/unit + live-lab probe
level**. Independent browser/UX re-testing of the consultant boundary remains
valuable and is listed in §11.

---

## 11. Open items — UI wiring

### 11.1 Frontend consumers for the two capabilities

The verified gap of §9.2. Minimal shape of the follow-on:

1. add an API client function for
   `PATCH /api/v3/consultants/me/team/{member_id}/capabilities`;
2. render `can_view_client` / `can_approve` in
   `ConsultantTeamTab.jsx`'s existing "Capabilities" column;
3. add grant/revoke controls (gated on the caller's own `can_manage_team`,
   presentation only — the server already refuses);
4. add a **real** component test; today `ConsultantTeamTab` is `jest.mock`ed
   (`consultant-page.test.jsx:21`), so nothing covers that table.

**PO DECISION REQUIRED (§62):** where does capability administration live?
Firm-admin self-service in the consultant workspace (implied by §7.3
"grantable/revocable per firm role **by the firm**"), CarbonTally-internal only,
or both? The backend route is compatible with either; the *navigation surface*
is the open question, and D21/D17 placement is frozen UX (§40/§41) that this
increment must not improvise.

### 11.2 Consultant approval control in client workspaces

A consultant with CAP-APPROVE reaches `customer-review` correctly, but no
frontend surface *reflects* that authority (no gating of an approve control on
`can_approve`). Presentation only; the DENY path is already enforced.

### 11.3 Independent browser-level negative retest

The boundary should be re-tested end-to-end through the UI by an independent
agent (AGENTS.md §45/§51): Consultant A → Consultant B's client, member without
CAP-VIEW-CLIENT → client workspace, consultant without CAP-APPROVE → approve.
This session's DENY evidence is API/unit + lab-probe level only (§10.1).

---

## 12. Open items — rollout, governance, PO decisions

### 12.1 Environment rollout

| Environment | Migration applied | Evidence |
|---|---|---|
| Local demo lab (`carbontally_demo_local`) | **Yes** — via ordinary bring-up (`stack.py` re-applies all migrations) | §7.3 column + row evidence |
| Production / shared Supabase | **No** | — |

**Rule (AGENTS.md §66/§67):** apply through a migration on the normal release
path; do not hand-edit a database. Suggested pre-deploy steps:

1. record `count(*)` of `consultant_firm_members` and the split by
   `coalesce(is_active, true)`;
2. confirm the IMPL-1 backfill touched exactly the rows that already had
   de-facto client access (the backfill is a *preservation*, not a grant of
   anything new — §4.2);
3. confirm **no** row has `can_approve = true` immediately after deploy
   (nobody had it before; the increment must not invent authority);
4. confirm RLS is unchanged and `is_org_consultant` still governs data scope.

### 12.2 Do not commit or deploy CT02 in isolation

The F-1 gate lives inside `resolve_managed_org_ids`, introduced by
`CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01` (§3.3). CT02 therefore
harvests with the parity workstream (or an equivalent resolver); a partial
commit would leave the capability decision inert. Reviewer guidance: attribute
by marker, not by file.

### 12.3 PO DECISION REQUIRED (explicitly not decided by this increment)

| # | Question | Why it is a PO call |
|---|---|---|
| P1 | Who administers capabilities — firm-admin self-service, CarbonTally-internal, or both? (§11.1) | §7.3 says grantable "by the firm"; the *surface* and the D21/D17 placement are frozen-UX/product choices |
| P2 | Confirm the IMPL-1 backfill policy: is de-facto access (pre-migration reachability) the same set the business *intends* to hold CAP-VIEW-CLIENT? | A backfill that preserves existing access is only correct if existing access was intended; the alternative (no backfill) would revoke every provisioned consultant until re-granted |
| P3 | Should provisioning default `can_view_client = true`? (the lab does, for usability — §7.2) | Production default is a policy choice; `can_approve` is already deny-by-default everywhere |
| P4 | §7.3 says capabilities are grantable "per **firm role** by the firm"; this increment stores them **per member** (matching AC-F-2's "consultant firm members") | Potential wording/implementation drift; needs PO confirmation before a role-default layer is built |
| P5 | Should the remaining five capabilities also become firm-administerable over HTTP? (§6.3) | Broadens the administrative attack surface; not required by F-1/F-2/F-10 |

### 12.4 Still open from the consolidation (unchanged by CT02)

**F-3 … F-9** and the surrounding §17 items — client-profile gating,
subscription/entitlement gating (the `ENTITLEMENT` leg of AC-F-1), branding,
handover, billing, portfolio UX, PE plane — are **not** touched. In particular
the `ENTITLEMENT` leg is *not* claimed by §10's AC-F-1 row.

---

## 13. How to reproduce the verification

### 13.1 Unit / API (the CT02 delta)

```bash
cd backend
./.venv/bin/pytest \
  tests/unit/api/test_ct_consultant_model_02.py \
  tests/unit/api/test_scope_aware_authorization.py \
  tests/unit/api/test_consultant_org_parity.py \
  tests/unit/api/test_p6_2*.py \
  tests/unit/api/test_f05_r1_org_scope_authorization.py -q
# → 306 passed, 0 failed   (14 files — see §8.3 for the per-file split)
```

Whole-suite run (expect the 8 pre-existing failures catalogued in §8.4, and
confirm no *new* failure):

```bash
cd backend && ./.venv/bin/pytest tests/unit -q
```

> **Interpreter.** Use the *backend* virtualenv. The repository-root `.venv` has
> no `pytest` installed, so `../.venv/bin/python -m pytest` aborts with
> `No module named pytest`. Run from `backend/` with `./.venv/bin/pytest` (or
> equivalently `./.venv/bin/python -m pytest`).

### 13.2 Database

The lab helper already holds the local connection details, so this works from
the repository root without exporting a password:

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, 'tools/demo_lab'); import lab
print(lab.psql_scalar("""SELECT column_name||' | '||data_type||' | default='||coalesce(column_default,'NULL')
                           FROM information_schema.columns
                          WHERE table_name='consultant_firm_members'
                            AND column_name IN ('can_view_client','can_approve')
                          ORDER BY column_name"""))
PY
# can_approve     | boolean | default=false
# can_view_client | boolean | default=false

python3 - <<'PY'
import sys; sys.path.insert(0, 'tools/demo_lab'); import lab
print(lab.psql_scalar("SELECT split_part(coalesce(u.email,'?'),'@',1)"
                      "||' | '||m.role||' | active='||m.is_active"
                      "||' | view='||m.can_view_client||' | approve='||m.can_approve"
                      " FROM consultant_firm_members m"
                      " LEFT JOIN public.users u ON u.id = m.user_id"
                      " ORDER BY m.role, m.can_approve, u.email"))
PY
# consultant.member | consultant | active=true | view=true | approve=false
# mp.consultant.allel | owner | active=true | view=true | approve=false
# mp.consultant.selected | owner | active=true | view=true | approve=false
# consultant.owner | owner | active=true | view=true | approve=true

python3 - <<'PY'
import sys; sys.path.insert(0, 'tools/demo_lab'); import lab
print(lab.psql_scalar("SELECT status||'='||count(*) FROM consultant_clients"
                      " GROUP BY status ORDER BY status"))
PY
# active=5
```

(The engagements table has no `is_active` column — "active" is
`consultant_clients.status = 'active'`, which is 5/5 in the lab.)

Equivalent raw form (needs the lab password from `~/ct_local_env/demo_lab`):

```bash
psql "postgresql://postgres@127.0.0.1:54426/carbontally_demo_local" -c "..."
```

Note: the lab applies migrations by executing the SQL files directly (see
`tools/demo_lab/stack.py`), so the live schema — not a ledger row — is the
evidence that the migration ran.

### 13.3 Live lab

```bash
python3 tools/demo_lab/stack.py                              # bring the lab DB + gateway up
python3 tools/demo_lab/supervise_demo_lab.py status          # RESTARTS / pid / health per process
python3 tools/demo_lab/verify.py                             # server-side routing/authorization/isolation
# expect: actor contexts 14/14 · probes 32/32 · isolation 18/18
#         no "RESULT: FAILED", no KNOWN PRODUCT DEFECT lines
```

`verify.py` writes machine-readable evidence outside the repository (e.g.
`~/ct_local_env/demo_lab/evidence/verify_<UTC>.json`). It does not print
`restarts=` — that is `supervise_demo_lab.py status`.

### 13.4 Re-derive the CT02 file list

```bash
grep -rl 'CT-CONSULTANT-MODEL-IMPLEMENTATION-02' \
  backend supabase tools docs frontend 2>/dev/null | sort
```

Expected result — **11** code/schema/tool files (one per §3.1 rows 1–11) plus
this document itself, which names the marker in its own text:

```
backend/api/consultant_auth.py
backend/api/v3_consultants.py
backend/api/v3_processing_workflow.py
backend/data/consultants.py
backend/domain/partners.py
backend/tests/unit/api/fakes.py
backend/tests/unit/api/test_ct_consultant_model_02.py
backend/tests/unit/api/test_scope_aware_authorization.py
docs/architecture/CT-CONSULTANT-MODEL-IMPLEMENTATION-02.md
supabase/migrations/20261102000000_ct_consultant_model_02_capability_admission.sql
tools/demo_lab/provision.py
tools/demo_lab/verify.py
```

`__pycache__/*.pyc` hits are compiled copies of the same files and carry no
independent change. `tools/demo_lab/manifest.json` (§3.1 row 12) is deliberately
**unmarked**: it is shared configuration consumed by the parity stream, not a
CT02-owned file.

---

## 14. Change-set hygiene

### 14.1 Marker discipline

Every CT02 hunk carries the literal
`CT-CONSULTANT-MODEL-IMPLEMENTATION-02`. That is the mechanism AGENTS.md §84
needs here: four workstreams share one uncommitted working tree (§3.3), so the
delta must be attributable **line-by-line**, not file-by-file.

### 14.2 Safety statement

* **No secrets.** Nothing added contains credentials, tokens, JWTs, signed URLs
  or connection strings; the migration is pure DDL/backfill.
* **No RLS weakened** — not one policy was added, dropped, disabled or altered
  (§4.3, AGENTS.md §67).
* **No demo data destroyed.** The IMPL-1 backfill updates a boolean on existing
  `consultant_firm_members` rows; it deletes nothing and creates no rows
  (AGENTS.md §54/§55). Lab-seeded identities keep their intended access.
* **No unrelated changes absorbed.** The temp verification worktree
  `/tmp/ct_wt2` was removed. Git branch/HEAD are unchanged by this work
  (`p8-release-reconciled` @ `3fec874`), and no branch operation, reset,
  rebase, force-push or history rewrite was performed (AGENTS.md §70).
* **No production mutation.** The migration is applied to the local lab only
  (§12.1).

### 14.3 Remaining limitations (stated plainly)

1. UI does not surface or administer the two capabilities (§9.2/§11.1).
2. Migration not yet applied to production (§12.1).
3. Cannot be committed/deployed independently of the parity workstream (§12.2).
4. Five PO decisions remain open (§12.3).
5. F-3…F-9 untouched (§12.4).
6. Whole-suite run still shows 8 failures that are **pre-existing and not
   CT02** (§8.4) — they are not acceptance evidence for, nor against, this
   increment.

<!-- END -->
