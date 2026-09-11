# CarbonTally P6-2A — Verification Report (Independent Security Gate)

- **Date:** 2026-09-06
- **Mode:** Read-only independent verification. No implementation or repair.
- **Verified implementation:** P6-2A Consultant Processing Authorization
  Contract (`docs/cline/CARBONTALLY_P6_2A_CONSULTANT_PROCESSING_AUTHORIZATION_REPORT.md`
  claims `IMPLEMENTED — READY FOR VERIFICATION`).

## 1. Verification Verdict

`P6-2A VERIFICATION FAILED — BLOCKING FINDINGS`

A blocking capability/D38 bypass was found on the existing automatic-processing
surface (`/api/v3/processing/jobs/{job_id}/confirm` and `…/retry`), which admits
active-grant Consultants via `ensure_processing_org_access` but is **not gated**
by the P6-2A capability flags (in particular `can_confirm_automation`) and whose
`confirm` path writes human corrections directly to the underlying
`manual_extraction_items` row **outside** the P6-2A item-level and D38 gates.
Details in §18. **Documented — not fixed.**

## 2. Scope Verified

- D1 capability flags & enforcement on the consultant path
- D2 active-engagement gating for all engagement states
- Server-derived resource scope / forged-id behaviour
- D3 D38 interaction (item-level, batch-level, assignee-kind, manipulation)
- D38 bypass search across processing/automatic/manual surfaces
- Actor separation (staff / org member / PE / automation)
- Customer Approval boundary
- Scope containment (no P6-2B–F), billing untouched
- Migration safety, database baseline, existing-authority audit
- Tests + full unit suite; git state

## 3. Architectural Authorities

`CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`; P6-2 architecture
(`CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md`);
P6-2 decision register (D1/D2/D3/D10); P6-2A implementation report; P6-1B;
P6-1C; D38 implementation/tests; Gate 3–6 suites.

## 4. D1 Capability Verification

Six flags exist (migration `20260906100000_…permissions.sql`: `ADD COLUMN …
boolean NOT NULL DEFAULT false` ×6 on `consultant_firm_members`), all default
**false**; domain fields + repo columns + `_row_to_member` present;
`CONSULTANT_PERMISSIONS` maps `extract/map/validate/calculate/confirm_automation/
submit` to the six columns; the resolver enforces the flag for the item-stage
actions (start-stage claim, extract, map, validate, calculate). Positive
(pipeline ALLOW) and negative (missing capability DENY) tests exist for
extract/map/validate/calculate.

**Defect:** `can_confirm_automation` (and `can_submit`) are registered but the
**existing** consultant-reachable confirm-automation action
(`POST /api/v3/processing/jobs/{job_id}/confirm`, and `…/retry`) is NOT gated by
them — see §18/B1. The implementation report's claim that these are
"registration only — no existing consultant-reachable action" is inaccurate.

## 5. D2 Engagement Verification

Code + tests confirm: consultant processing actions on `/api/v3/processing/items/*`
deny for `pending`, `rejected`, `suspended`, `ended`, `inactive` (403, loop test)
and allow for `active`; membership must be active; a Firm-A member cannot use
Firm-B's engagement (resource-org engagement re-check). Legacy/Case-A/Case-B
relationships all resolve through the same active-grant rule (P6-1C model). PASS.

## 6. Resource Scope Verification

Item/batch are loaded server-side and the authoritative org comes from the
loaded batch; the resolver denies a caller-supplied org mismatch (no silent
substitution). Tests: cross-client 403, cross-firm 403, fabricated item 404,
no-engagement member 403, forged engagement 403. PASS.

## 7. D3 D38 Verification

`assignee_kind` unchanged (`internal_staff | processing_entity`); no
`consultant` kind. Resolver denies on open item assignment and on batch
assignment carriers (`entity_id`/`assigned_to`). Tests cover open internal and
PE item assignments, PE-defaulted batch, unassigned ALLOW, assignment-route
denial. Internal batch-default (`assigned_to`) shares the same code branch as
`entity_id` (code inspection). PASS for the gated surfaces; **FAIL for the
automatic-processing confirm/retry paths** (see §18/B1), which reach item
correction/re-enqueue without any D38 conflict check.

## 8. D38 Bypass Analysis

Reviewed: `/api/v3/processing/items/*` start/extract/map/validate/calculate
(gated for consultants); `/api/v3/processing/jobs/*`
(`v3_automatic_processing.py` — **NOT gated**, bypass found); batch lifecycle
routes (start/complete/cancel — org-access only, pre-existing, no capability
mapping; recorded as observation B2); legacy `/api/v3/manual-extraction/*`
(requires org member/admin → consultants denied); read surfaces
(list/detail/workspace/queue) remain engagement-gated. Repository-level writes
are reachable only through these API paths (service pool; no public direct repo
endpoint).

## 9. Actor Separation

`ensure_consultant_processing_authorized` early-returns for internal staff and
entity staff, and for org members — only the consultant capacity is gated;
PE staff remain denied by `ensure_processing_org_access` before the helper.
Existing actor authorizations (ops routes, PE routes, customer org routes) are
untouched and their suites pass. PASS (no accidental re-routing of all
processing through consultant authorization).

## 10. Customer Approval Boundary

No P6-2A change reaches approval. `/items/{id}/customer-review` requires
`require_org_admin` (consultant → 403, tested); automatic
`/jobs/{job_id}/review` requires org owner/admin or internal staff. The latent
`calculated → approved` transition remains in the workflow state map, unchanged
and not exposed by P6-2A — recorded as a P6-2C/D9 deferred item. PASS (no new
approval path).

## 11. Scope Containment

Verified changed-file set is exactly: migration, `domain/partners.py`,
`data/consultants.py`, `api/consultant_auth.py`,
`api/v3_processing_workflow.py`, `tests/unit/api/fakes.py`,
`test_p6_2a_…py`, P6-2A report. No P6-2B–F work, no billing, D39/D40, D38
schema, provenance, or seed/demo changes. PASS.

## 12. Database / Migration Verification

Migration: additive, single table, six `boolean NOT NULL DEFAULT false`
columns, `COMMENT`s only; no destructive operations, no data DML, no grants, no
RLS change. Applied to the live local DB (`APPLY_EXIT:0` earlier; verified
columns exist). Baseline unchanged: members 54, profiles 55, clients 917,
organizations 975, billing_plans 6, customer_subscriptions 0, billing_orders 0,
billing_credit_ledger 0, work_item_assignments 0, manual_extraction_items 260.
PASS.

## 13. Security Matrix

| Scenario | Expected | Actual | Result |
| --- | --- | --- | --- |
| Active Consultant + active engagement + capability | ALLOW | pipeline 200 (calc 274.5) | PASS |
| Missing capability (item actions) | DENY | 403 | PASS |
| Pending / Rejected / Suspended / Ended / Inactive engagement | DENY | 403 ×5 | PASS |
| Inactive membership | DENY | 403 | PASS |
| Cross-firm | DENY | 403 | PASS |
| Cross-client | DENY | 403 | PASS |
| Forged organization ID | DENY | 403/404 (server-derived scope) | PASS |
| Forged engagement ID | DENY | 403 | PASS |
| Item-level internal assignment | DENY | 403 | PASS |
| Item-level PE assignment | DENY | 403 | PASS |
| Batch-level assignment (PE default; internal same branch) | DENY | 403 | PASS |
| Unassigned item | ALLOW if otherwise authorized | 200 | PASS |
| Assignment manipulation | DENY | 403 | PASS |
| Customer Approval | DENY | 403 | PASS |
| Unauthenticated | DENY | 401 | PASS |
| **Automation confirm / retry with NO capability (active grant only)** | **DENY** | **200 path open (code)** | **FAIL — B1** |

## 14. Existing Consultant Authority Audit

Live DB: total members 54; `can_extract=true`: 0; `can_map=true`: 0;
`can_validate=true`: 0; `can_calculate=true`: 0;
`can_confirm_automation=true`: 0; `can_submit=true`: 0. No existing member
gained processing authority. PASS.

## 15. Regression Verification

Targeted regression batch (21 suites incl. v3_consultants, P6-1B, P6-1C, D38
effective assignment, scope-aware authorization, PE auth, processing workflow,
phase regressions, Gate 4/5/6 provenance suites, automatic-processing suites)
EXIT 0; full unit suite EXIT 0. No Gate 3–6, P6-1B or P6-1C regression observed.

## 16. Tests and Exit Codes

- `pytest tests/unit/api/test_p6_2a_consultant_processing_authorization.py -q`
  → EXIT 0 (18 tests).
- Targeted regression batch (see §15 for suite list) → **EXIT 0** (100%).
- Full suite `pytest tests/unit -q` → **FULL_EXIT 0**.
- No tests were modified during verification.

## 17. Git Verification

Branch `main`; HEAD `1639121` (unchanged). Expected P6-2A change set only:
migration `20260906100000_p6_2a_consultant_processing_permissions.sql`,
`backend/domain/partners.py`, `backend/data/consultants.py`,
`backend/api/consultant_auth.py`, `backend/api/v3_processing_workflow.py`,
`backend/tests/unit/api/fakes.py`, `test_p6_2a_consultant_processing_authorization.py`,
P6-2A implementation report. This verification adds only
`docs/cline/CARBONTALLY_P6_2A_VERIFICATION_REPORT.md`. No other unexpected file
changed. No commit/push/PR.

## 18. Findings / Defects

**B1 — BLOCKING: Consultant automation-confirmation and retry are not
capability-gated (and bypass the item/D38 gates).**

- Evidence (code inspection, file `backend/api/v3_automatic_processing.py`,
  router prefix `/api/v3/processing`):
  - Module docstring lines 10–14: “list/detail/**confirm/retry** — org member,
    internal staff, **or a consultant with an ACTIVE client grant**
    (`ensure_processing_org_access`)”.
  - `_checked_job` calls only `ensure_processing_org_access(...)`
    (org isolation; admits active-grant consultants).
  - `POST /jobs/{job_id}/confirm` (`require_auth()` + `_checked_job`) — human
    gate that re-enqueues a blocked/failed job and, when corrections are
    supplied, **writes `save_extracted_data`/`save_mapped_data` directly to the
    underlying `manual_extraction_items` row** (the same item type the P6-2A
    gates protect) — with no `can_confirm_automation` check and no D38
    assignment conflict check.
  - `POST /jobs/{job_id}/retry` (`require_auth()` + `_checked_job`) — re-enqueues
    failed/blocked jobs with no capability gate.
- Consequence: an active-grant consultant **without** `can_confirm_automation`
  (or any other processing capability) can confirm blocked automated work and
  re-run processing, and can mutate item extraction/mapping through the confirm
  payload — a capability bypass of D1 and a bypass of the item-level/D38 gates
  the P6-2A resolver enforces on `/processing/items/*`.
- The P6-2A implementation report's statement that `can_confirm_automation`
  has “no existing consultant-reachable action” is incorrect.
- **Not fixed (per gate rules).** Remediation belongs to a P6-2A follow-up or
  P6-2C (gate `confirm`/`retry` on `can_confirm_automation`; apply the D38
  conflict rule before item writes) — PO decision required.

**B2 — OBSERVATION (non-blocking, P6-2C):** shared-surface batch lifecycle
(`/processing/batches/{id}/start|complete|cancel`) and the item `start`
stage-claim for `review`/`qc` (not in `_STAGE_PERMISSION`) remain gated only by
org access for consultants. Pre-existing behaviour, not introduced by P6-2A,
and none of these reach `approved`; workflow-stage gating is P6-2C/D5 scope.
A consultant can move an item into `customer_review` via `start
{"stage":"review"}` without a submit capability; final approval stays
customer-only. Record for P6-2C.

## 19. Deferred P6-2 Work

Confirmed NOT implemented and outside this gate: P6-2B handoff, P6-2C workflow
state/CT-QC submit/origin/approval hardening, P6-2D provenance/entitlement,
P6-2E D39/D40, P6-2F UI/E2E. Latent `calculated → approved` transition remains
deferred (P6-2C/D9).

## 20. Final Recommendation

P6-2A is **not yet ready for PO acceptance**. The capability/D38 contract is
correctly implemented for the `/api/v3/processing/items/*` manual stage actions,
but the existing consultant-reachable automatic-processing confirm/retry actions
bypass the new capability and D38 gates (B1). Recommended next step: a bounded
PO-approved remediation applying the P6-2A contract to `/jobs/{job_id}/confirm`
and `/retry` (gating on `can_confirm_automation` + the D38 conflict rule before
any item write), followed by re-verification of the security matrix. No P6-2B
work should start until B1 is resolved and P6-2A is accepted.

---

*End of verification report. Read-only task — no code, SQL, migration, RLS,
API, frontend, test, billing, provenance, workflow, D38/D39/D40 or data was
modified; no fixtures created; nothing committed or pushed.*


