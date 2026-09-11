# CarbonTally P6-2A — Consultant Processing Authorization Contract (report)

- **Date:** 2026-09-06
- **Status:** Implemented, unit-tested. `IMPLEMENTED — READY FOR VERIFICATION`.
- **Authorities:** PO-ratified P6-2-D1/D2/D3/D10 (P6-2 PO Decision Register);
  P6-1B permission architecture; P6-1C engagement model; D38/D15 unchanged.

## 1. Scope

Implemented ONLY the P6-2A authorization foundation:

1. **Capability flags (D1)** — six additive, deny-by-default processing flags on
   `consultant_firm_members`, wired through the existing permission map.
2. **Engagement scope (D2)** — every consultant processing action is re-checked
   against an ACTIVE `consultant_clients` grant for the server-derived org.
3. **D38 conflict (D3)** — consultants are NOT D38 assignees; an open item
   assignment or a batch-level assignment carrier denies the consultant action.
   No handoff representation was invented (P6-2B deferred).
4. **Org-member preservation (D10)** — organisation-member and internal-staff
   behaviour on the processing surface is unchanged.

NOT implemented: P6-2B..F (handoff, workflow/QC submit states, provenance,
entitlement timing, D39/D40, UI). No Customer Approval change. No billing change.

## 2. Files changed

| File | Change |
| --- | --- |
| `supabase/migrations/20260906100000_p6_2a_consultant_processing_permissions.sql` | **new** — additive, idempotent; six `boolean NOT NULL DEFAULT false` columns |
| `backend/domain/partners.py` | `ConsultantFirmMember` + six deny-by-default capability fields |
| `backend/data/consultants.py` | `_MEMBER_COLUMNS` + `_row_to_member` include the six columns |
| `backend/api/consultant_auth.py` | `CONSULTANT_PERMISSIONS` += `extract/map/validate/calculate/confirm_automation/submit`; new canonical resolver `ensure_consultant_processing_authorized` |
| `backend/api/v3_processing_workflow.py` | `_get_checked_item(permission=…)` + `_STAGE_PERMISSION`; consultant gate applied to stage claim, extract, map, validate, calculate |
| `backend/tests/unit/api/fakes.py` | `seed_firm_member` supports the six capability kwargs |
| `backend/tests/unit/api/test_p6_2a_consultant_processing_authorization.py` | **new** — 18 tests |
| `docs/cline/CARBONTALLY_P6_2A_CONSULTANT_PROCESSING_AUTHORIZATION_REPORT.md` | this report |

## 3. Capability model

Real boolean columns on `consultant_firm_members` (same architecture as
`can_manage_clients` etc.), evaluated server-side via
`ensure_consultant_permission`:

| Capability (action name) | Column | Default |
| --- | --- | --- |
| `extract` | `can_extract` | false |
| `map` | `can_map` | false |
| `validate` | `can_validate` | false |
| `calculate` | `can_calculate` | false |
| `confirm_automation` | `can_confirm_automation` | false (no existing consultant-reachable action yet — registration only) |
| `submit` | `can_submit` | false (no existing consultant submit action yet — registration only) |

Existing memberships receive **no new authority**: migration defaults all six
flags to `false` (verified: `any_true=0` for all 54 live members).

## 4. Authorization flow

Applied at the top of every gated processing action in `/api/v3/processing/*`
(the surface consultants can reach), via the single canonical resolver
`ensure_consultant_processing_authorized`:

```text
identity (AuthUser)
 → actor class (consultant only; internal staff & org members unaffected — D10)
 → active consultant membership (single firm context)
 → active client engagement (consultant_clients.status='active' for the org)
 → capability flag (can_extract / can_map / can_validate / can_calculate)
 → resource scope (authoritative org derived from the loaded batch/item;
   any caller-supplied org mismatch → DENY)
 → D38 conflict (open work_item assignment OR batch entity_id/assigned_to → DENY)
```

Every route loads the item and batch **server-side** first; org id and item
identity are never taken from the client as authority.

## 5. D38 enforcement

- `work_item_assignments.assignee_kind` is untouched (`internal_staff |
  processing_entity` only). No `consultant` assignee kind.
- For a consultant actor, the resolver denies when:
  - the item has an **open** D38 assignment row (any assignee kind), or
  - the **batch** carries an assignment default (`entity_id` = PE,
    `assigned_to` = internal).
- No implicit handoff exists; no release/reassign/override is possible from the
  consultant path (assignment routes remain Operations-only → 403).
- Unassigned items (no open row, no batch default) are processable when every
  other rule passes.

## 6. Security matrix

| Scenario | Expected | Result |
| --- | --- | --- |
| Active Consultant + active engagement + capability | ALLOW | PASS (pipeline 200, calc 274.5) |
| Active Consultant + pending/rejected/suspended/ended/inactive engagement | DENY | PASS (403 ×5) |
| Active Consultant + another firm's engagement | DENY | PASS (403) |
| Active Consultant + wrong client resource | DENY | PASS (403) |
| Missing capability | DENY | PASS (403, permission message) |
| Internal-staff open D38 assignment | DENY | PASS (403) |
| PE open D38 assignment | DENY | PASS (403) |
| PE-defaulted batch (no open row) | DENY | PASS (403) |
| Unassigned item (all other rules pass) | ALLOW | PASS |
| Forged org ID / fabricated item | DENY | PASS (403/404) |
| Forged engagement/client id | DENY | PASS (403) |
| Assignment manipulation via ops routes | DENY | PASS (403) |
| Customer Approval (customer-review) | DENY | PASS (403) |
| Unauthenticated | DENY | PASS (401) |
| Inactive membership / no membership | DENY | PASS (403 ×2) |

## 7. Tests

- **New suite:** `backend/tests/unit/api/test_p6_2a_consultant_processing_authorization.py`
  → **18 passed, EXIT 0**.
- **Regression batch A (17 suites incl. consultants, P6-1B/1C, processing
  workflow, ops, D38 effective assignment, processing-origin/QC, scope-aware
  auth, auto-processing, QC, PE auth):** EXIT 0 (100%, no failures).
- **Full unit suite `pytest tests/unit -q`:** FULL_EXIT:0 (1461+ collected tests,
  no failures — completed to 100%).

## 8. Baseline verification (live local DB, read-only probes)

- Before migration: `consultant_firm_members=54`, `consultant_clients=917`,
  `organizations=975`.
- After applying the additive migration (`APPLY_EXIT:0`):
  - `consultant_firm_members=54` (unchanged)
  - `any_true=0` — zero members hold any processing capability (deny-by-default)
  - six new columns present (`cols=6`)
  - `consultant_clients=917`, `organizations=975` (unchanged)
- No organisation/client-relationship/billing/D38 data was modified. Unit tests
  run entirely against the in-memory world; no disposable fixtures were written
  to the live database.

## 9. Known limitations

- `can_confirm_automation` and `can_submit` are registered capabilities with no
  existing consultant-reachable action today; they are deny-by-default and
  unused until P6-2C lands the confirm/submit actions.
- The consultant gate currently applies to the shared `/api/v3/processing/*`
  stage actions only (the surface consultants can reach). Read surfaces remain
  active-engagement-gated (unchanged).
- Org-member and internal-staff callers are intentionally unaffected (D10).

## 10. Deferred P6-2 work

- P6-2B: PE↔Consultant handoff representation — NOT implemented (no implicit
  handoff; open-assignment deny is the fail-closed default).
- P6-2C: consultant workflow state/review/CT-QC submission/origin; Customer
  Approval hardening beyond regression protection — NOT implemented. The
  latent `calculated→approved` transition noted in the P6-2 artifact remains
  documented for P6-2C/D9.
- P6-2D: provenance firm dimension + entitlement timing — NOT implemented.
- P6-2E: D39/D40 — NOT implemented.
- P6-2F: UI/E2E — NOT implemented.

## 11. Git status

- Branch `main`; HEAD unchanged at `1639121`.
- New/untracked: migration, test suite, this report; modified: domain/partners.py,
  data/consultants.py, api/consultant_auth.py, api/v3_processing_workflow.py,
  tests/unit/api/fakes.py.
- No commit, no push, no PR.

## 12. Confirmation

No work outside P6-2A was implemented. No commit, push, or PR was created.


