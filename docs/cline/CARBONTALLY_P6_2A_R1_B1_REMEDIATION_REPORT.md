# CarbonTally P6-2A-R1 — B1 Remediation Report (Automation Confirm / Retry Authorization)

- **Date:** 2026-09-06
- **Status:** `B1 REMEDIATED — READY FOR RE-VERIFICATION`
- **Scope:** B1 only. No P6-2B–F, no billing, no D38 schema, no provenance,
  no D39/D40, no UI.

## 1. B1 Finding

Independent P6-2A verification found that Consultant `confirm` / `retry` on
`POST /api/v3/processing/jobs/{job_id}/confirm` and `…/retry` were authorized
only by `ensure_processing_org_access` (active-grant consultant admitted) with
**no** P6-2A capability check and **no** D38 conflict check. `confirm` could
write human corrections to the underlying `manual_extraction_items` record via
`save_extracted_data` / `save_mapped_data` before/without authorization;
`can_confirm_automation` existed but protected nothing reachable.

## 2. Root Cause

The P6-2A capability gate was applied to the manual item-stage surface
(`/processing/items/*` stage actions) but the automatic-processing surface
(`/processing/jobs/*`) — which the module docstring explicitly authorizes for
active-grant Consultants — was not routed through the canonical resolver, and
no authorization helper existed for a job resource (the resolver expected an
item/batch resource).

## 3. Remediation

- **Extended the canonical resolver** `ensure_consultant_processing_authorized`
  (`backend/api/consultant_auth.py`) minimally: `batch` / `item` are now
  optional and a server-derived `organization_id` (job resource) is accepted;
  when both a job org and a batch are supplied they must agree (cross-surface
  guard). D38 evaluation is unchanged for item-based calls and is skipped only
  when no source item/batch resolves.
- **Added one job-surface helper** `_authorize_consultant_job_action`
  (`backend/api/v3_automatic_processing.py`) that resolves the job's source
  item + batch server-side and calls the **same** canonical resolver with
  `permission="confirm_automation"`. No parallel authorization logic was
  created.
- **Wired the gate into both routes** immediately after `_checked_job` and
  **before any** stage/status write, item correction, `reenqueue`, or audit
  side effect.

## 4. Authorization Chain

```text
identity
→ active consultant membership (single firm context)
→ active client engagement (consultant_clients.status='active' for the job's
   authoritative organization)
→ can_confirm_automation = true   (required for confirm AND retry)
→ resource scope (job_id → job → source item/batch → organization, all
   server-derived; caller org conflicts or item/org mismatch → DENY)
→ D38 (open item-level assignment OR batch-level entity_id/assigned_to → DENY;
   no consultant assignee kind; no handoff invented)
→ action (confirm / retry)
→ mutation
```

## 5. Mutation Ordering

The gate is invoked in `confirm_job` / `retry_job` **immediately after
`_checked_job` and before the first mutation**: before any
`save_extracted_data`, `save_mapped_data`, `reenqueue`, `sync_item_data`, or
`_record_human_gate_audit` call. Tests prove denied requests produce **zero**
underlying change (item data, job stage/status/reprocess_count and no
`automatic_processing:confirmed` / `…:retried` audit entry).

## 6. Tests

New suite `backend/tests/unit/api/test_p6_2a_r1_b1_automation_confirm_retry.py`
(14 tests) →
`pytest tests/unit/api/test_p6_2a_r1_b1_automation_confirm_retry.py -q` →
**EXIT 0**.
Regression batch (18 suites incl. original P6-2A, automatic jobs/payload,
processing workflow, consultants, P6-1B/1C, D38 effective assignment,
scope-aware auth, PE auth, processing-origin/QC, phase regressions, Gate 4/5/6
provenance) → **REG_EXIT 0**. Full unit suite `pytest tests/unit -q` →
**FULL_EXIT 0**.

## 7. Security Matrix

| Scenario (confirm / retry) | Expected | Result |
| --- | --- | --- |
| Active + engagement + `can_confirm_automation` + unassigned | ALLOW | PASS (confirm 200; retry 200) |
| Missing `can_confirm_automation` | DENY + zero mutation | PASS (403; item/job/audit unchanged) |
| Pending / Rejected / Suspended / Ended / Inactive engagement | DENY | PASS (403 ×5) |
| Inactive membership | DENY | PASS (403) |
| Another firm (no grant for job org) | DENY | PASS (403) |
| Cross-client job | DENY | PASS (403) |
| Source-item org ≠ job org | DENY | PASS (403) |
| Fabricated job id | DENY | PASS (404) |
| Open item-level internal assignment | DENY | PASS (403) |
| Open item-level PE assignment | DENY | PASS (403) |
| Batch-level PE default (`entity_id`) | DENY | PASS (403) |
| Batch-level internal default (`assigned_to`) | DENY | PASS (403) |
| Unauthenticated | DENY | PASS (401) |

## 8. Regression

See §6. Existing org-member confirm/retry (auto-processing suite) and internal
staff paths remain green — the gate is consultant-capacity-only (actor
separation; D10 preserved). Full unit suite green.

## 9. Database Baseline

No migration and no live data change in this remediation. Live DB (before ==
after): `consultant_firm_members=54`; `any of the six can_* flags = 0`;
`consultant_clients=917`; `organizations=975`;
`work_item_assignments=0`; `customer_subscriptions=0`; `billing_orders=0`.
No fixtures written.

## 10. Scope Containment

Confirmed unchanged: P6-2B (handoff), P6-2C (workflow states / submit / origin),
P6-2D (provenance / entitlement), P6-2E (D39/D40), P6-2F (UI/E2E), billing,
D38 schema/assignment model, Gate 4–6 architecture.

## 11. Known Deferred Findings

- **B2 (P6-2C, non-blocking):** shared-surface batch lifecycle
  (`/processing/batches/{id}/start|complete|cancel`) and item `start` for
  `review`/`qc` stages remain org-access-gated only for Consultants (pre-existing
  behaviour, not introduced by P6-2A, none reach approval). Preserved for
  P6-2C/D5.
- Latent `calculated → approved` transition remains deferred to P6-2C/D9.

## 12. Git State

Branch `main`; HEAD `1639121` (unchanged). Changed files:
`backend/api/consultant_auth.py`, `backend/api/v3_automatic_processing.py`
(modified); `backend/tests/unit/api/test_p6_2a_r1_b1_automation_confirm_retry.py`
and this report (new). No commit, no push, no PR.

