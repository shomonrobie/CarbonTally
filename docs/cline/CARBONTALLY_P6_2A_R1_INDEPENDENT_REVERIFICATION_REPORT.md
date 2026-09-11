# CarbonTally P6-2A-R1 — Independent B1 Re-Verification Report

- **Date:** 2026-09-06
- **Mode:** Read-only independent security re-verification. No implementation
  or repair was performed; no test was modified.
- **Subject:** B1 remediation (Consultant automation `confirm`/`retry`
  authorization) applied to the P6-2A Consultant Processing Authorization
  Contract.

## 1. Final Verdict

`P6-2A RE-VERIFICATION PASSED — READY FOR PO ACCEPTANCE`

## 2. B1 Root-Cause Closure Assessment

The original defect (active-grant Consultants reaching
`POST /api/v3/processing/jobs/{job_id}/confirm` and `…/retry` with no
`can_confirm_automation` gate and no D38 conflict check, where `confirm` could
mutate the underlying item) is **closed**:

- Both routes now invoke the canonical
  `ensure_consultant_processing_authorized` (through the single helper
  `_authorize_consultant_job_action`) with `permission="confirm_automation"`,
  immediately after the job is loaded and **before** any stage check, item
  write, re-enqueue, or audit.
- The item corrections in `confirm` (`save_extracted_data` /
  `save_mapped_data`) occur strictly after the gate.

## 3. Code-Path Inspection

- `backend/api/consultant_auth.py`
  `ensure_consultant_processing_authorized`: actor-class early-returns for
  internal staff and entity staff and for organisation members (no-op for
  non-Consultant capacities); otherwise resolves active membership, requires an
  ACTIVE `consultant_clients` grant for the authoritative org, requires the
  requested permission flag, enforces server-derived org scope (including a
  job-org vs batch-org cross-guard), then evaluates D38 (open item assignment or
  batch `entity_id`/`assigned_to` → DENY). Signature now accepts optional
  `batch`/`item` and a server-derived `organization_id` (job resource) — one
  resolver, no parallel model.
- `backend/api/v3_automatic_processing.py`
  `_authorize_consultant_job_action`: loads the job's `source_item_id` → item →
  batch server-side and calls the canonical resolver with the job's
  `organization_id`. `confirm_job` (~line 307–313) and `retry_job`
  (~line 422–428) call it immediately after `_checked_job`.
- `_checked_job` still enforces `ensure_processing_org_access` (org isolation,
  consultant active grant) as the outer layer; the P6-2A resolver then applies
  the capability/D38 layer for the Consultant capacity only.
- `POST /jobs/{job_id}/review` remains org owner/admin or internal staff
  (`require_org_admin`) — unchanged.

## 4. Capability Verification

Both `confirm` and `retry` require exactly `can_confirm_automation` for
Consultant actors (resolver → `ensure_consultant_permission(context,
"confirm_automation")` → column `can_confirm_automation`). No fallback to
`can_extract`/`can_map`/`can_validate`/`can_calculate`/`can_submit`. The six
flags remain `NOT NULL DEFAULT false`; live DB shows zero members with any flag
true. `can_submit` remains present, deny-by-default, and unused (no submission
semantics introduced).

## 5. Active-Engagement Verification

Resolver requires an active `consultant_clients` grant (`status='active'`) for
the authoritative org; every other engagement state (`pending`, `rejected`,
`suspended`, `ended`, `inactive`) and inactive membership and cross-firm/no-grant
scenarios are denied (403) — covered by R1 tests for both job actions.

## 6. Server-Derived Resource-Scope Verification

Trace: `job_id` → processing job (`repos.processing.get`) → `job.organization_id`
(authoritative) + `source_item_id` → item → batch (server-side). Client-supplied
org values are not accepted on these routes (no org path/query/body authority).
Resolver denies on: requested-org mismatch, job-org vs batch-org conflict,
cross-client job, and mismatched source-item org (R1 tests). Fabricated job ids
→ 404.

## 7. D38 Verification

For both job actions, when a source item resolves: open item-level D38
assignment (`internal_staff` or `processing_entity`) → DENY; batch-level default
(`entity_id` PE or `assigned_to` internal) → DENY; no effective assignment →
permitted if every other rule passes (positive confirm/retry tests). No
`consultant` value was added to `assignee_kind`; no Consultant assignment type
or PE↔Consultant handoff representation was introduced; D38 schema untouched.

## 8. Authorization-Before-Mutation Trace

- **Confirm:** `_checked_job` (read) → `_authorize_consultant_job_action`
  (deny-or-continue) → stage validation → item corrections → `reenqueue` →
  `sync_item_data` → audit. No mutation precedes the gate.
- **Retry:** `_checked_job` (read) → `_authorize_consultant_job_action` →
  stage validation → `reenqueue` → audit. No mutation precedes the gate.

## 9. Zero-Mutation Denial Evidence

R1 tests assert for a denied `confirm` (capability false): item `extracted_data`
unchanged, job stage `blocked`/status `manual_review` unchanged, and no
`automatic_processing:confirmed` audit entry. For a denied `retry`: stage
`failed`, status unchanged, `reprocess_count` unchanged, no
`automatic_processing:retried` audit entry. All pass.

## 10. Security Matrix

Capability/engagement/resource/D38 matrix for confirm & retry: capability
present + active + engaged + unassigned → ALLOW (200); capability false →
DENY 403 + zero mutation; extract/map/validate/calculate/submit-only →
DENY 403; inactive membership → 403; each non-active engagement state → 403;
other firm → 403; cross-client → 403; source-item/job org mismatch → 403;
fabricated id → 404; open internal/PE item assignment → 403; batch PE/internal
default → 403; unauthenticated → 401. All rows verified by R1 tests (EXIT 0).

## 11. Original P6-2A Matrix Reassessment

Manual item-stage surface remains fully gated: extraction→`can_extract`,
mapping→`can_map`, validation→`can_validate`, calculation→`can_calculate`
(original P6-2A suite, 18 tests, EXIT 0). Automatic job surface: confirm and
retry → `can_confirm_automation`. `can_submit` reserved deny-by-default. No
other reachable Consultant processing mutation surface equivalent to B1 was
found (job `review` is customer-admin/internal-only; manual-extraction item
routes are org-member/admin-only; ops/PE routes are staff/PE-only).
An observation (non-blocking): the pre-existing upload/enqueue automatic
pipeline path remains `can_upload_documents`-gated (not one of the six D1
flags); it was not part of B1/P6-2A's manual-action contract and is noted for a
future decision rather than this gate.

## 12. Non-Consultant Regression

The gate is consultant-capacity-only (early-return for internal staff and org
members; PE denied earlier by the org-scope layer). Org-member and internal
confirm/retry tests in the automatic-processing suite remain green; customer
member/owner behaviour, PE behaviour and automated pipeline behaviour are
unchanged.

## 13. Gate 3–6 / Consultant Regression Results

18-suite regression batch (original P6-2A, R1, automatic jobs/payload,
processing workflow, consultants, P6-1B/1C, D38 effective assignment,
scope-aware authorization, PE auth, processing-origin/QC, phase regressions,
Gate 4 provenance, evidence traceability/record) → **REG_EXIT 0**. Full unit
suite `pytest tests/unit -q` → **FULL_EXIT 0** (100%, no failures). No tests
were modified.

## 14. Database Baseline

Live read-only probes: `consultant_firm_members=54`; members with any of the six
processing flags true = **0**; `can_confirm_automation=true` count = **0**;
`consultant_profiles=55`; `consultant_clients=917`; `organizations=975`;
`work_item_assignments=0`; `manual_extraction_items=260`; `billing_plans=6`;
`customer_subscriptions=0`; `billing_orders=0`; `billing_credit_ledger=0`.
All match the expected baseline — no remediation-caused mutation, no fixtures.

## 15. Scope-Containment Audit

R1 changed only `backend/api/consultant_auth.py` and
`backend/api/v3_automatic_processing.py` plus a new test suite and this report.
**No migration was added.** No P6-2B–F, no billing, no D38 schema/assignee
change, no provenance redesign, no D39/D40, no UI, no handoff representation.

## 16. Deferred B2 Confirmation

Confirmed deferred (not blockers): B2 (batch lifecycle and item `start`
review/QC-stage Consultant gating), Consultant Review, CT-QC submission, origin
`CONSULTANT`, firm provenance, entitlement availability at submission, D39
vocabulary, D40 notifications, PE↔Consultant handoff, latent `calculated →
approved` hardening. None of the deferred surfaces allows a Consultant to
perform Customer Approval or CarbonTally QC.

## 17. Files / Git State

Branch `main`; HEAD `1639121` (unchanged). R1 files:
`backend/api/consultant_auth.py`, `backend/api/v3_automatic_processing.py`
(modified); `backend/tests/unit/api/test_p6_2a_r1_b1_automation_confirm_retry.py`,
`docs/cline/CARBONTALLY_P6_2A_R1_B1_REMEDIATION_REPORT.md` (new). Verification
added only `docs/cline/CARBONTALLY_P6_2A_R1_INDEPENDENT_REVERIFICATION_REPORT.md`.
Pre-existing dirty working-tree files (automatic-processing domain/services/
worker files etc.) are preserved untouched. No commit, push, or PR.

## 18. Blocking and Non-Blocking Findings

- **Blocking findings:** none.
- **Non-blocking observation (future decision, not P6-2A/B1 scope):** the
  pre-existing upload→enqueue automatic-pipeline trigger remains gated by
  `can_upload_documents`; whether a dedicated capability is needed for
  "enqueue automatic processing" is a later commercial/workflow decision.

## 19. Recommendation to PO

P6-2A satisfies the canonical requirement:
> a Consultant cannot confirm or retry automation unless `can_confirm_automation`
> is granted, membership and engagement are active, resource scope is
> server-derived, and no open D38 assignment exists — with authorization
> enforced before any persistent mutation.

Recommend **PO acceptance of P6-2A**. Proceed to later P6-2 workstreams only
after PO acceptance; do not begin P6-2B before that.

---

*End of report. Read-only task — no code, tests, migrations, schema, RLS,
database data, or architecture was changed; no fixtures created; nothing
committed or pushed.*


