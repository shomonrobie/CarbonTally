# CarbonTally — P6-2B-4 Mandatory CT-QC Prerequisite (Implementation Report)

- **Workstream:** P6-2B-4 — narrow Phase-6 control remediation
- **Status:** **P6-2B-4 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION**
- **Date:** 10 September 2026
- **Branch / HEAD:** `main` / `1639121` (unchanged; no commit, push or PR)
- **Scope authorisation:** PO scope-freeze message (sections 1–7). This is a bounded
  workflow/security **control** fix. No Evidence Architecture, no provenance
  schema (P2), no diagnostics were implemented.

---

## 1. Defect remediated

The P6-2B-3 independent verification raised **BLOCKER-B1**: a consultant-submitted
`reviewed` item could be moved to `customer_review` and then approved **without any
CarbonTally CT-QC decision**:

```
consultant-submit → reviewed
POST /api/v3/processing/items/{id}/start {"stage":"review"}  → customer_review
org owner approves (POST …/customer-review)                  → approved  (no ct_qc:* event)
```

Root cause (verified against current source):

1. `ITEM_STATUS_FLOW["reviewed"]` still allowed `customer_review`.
2. `_STAGE_WORKING_STATUS["review"] == "customer_review"` in both
   `v3_processing_workflow.py` and `v3_operations.py`.
3. The `review` stage had **no** `_STAGE_PERMISSION` entry, so the consultant
   capability / D38 gate was skipped on that claim.
4. `customer_review_item` accepted `calculated → approved`, so a manual item at
   `calculated` could also be approved with no CT-QC.

---

## 2. Production changes (minimum control logic only)

| File | Change |
| ---- | ------ |
| `backend/domain/partners.py` | Removed the `customer_review` exit from `ITEM_STATUS_FLOW["reviewed"]` (now `("ct_qc", "mapping", "calculated")`). Closes the `reviewed → customer_review` escape **origin-agnostically**: `reviewed` means "awaiting CarbonTally CT-QC". |
| `backend/api/processing_mode.py` *(new)* | P1 containment predicate + shared guard. `item_is_automatic()` is true only when (a) a durable automatic-processing job exists for the item **and** (b) the machine actually produced output (write-once `automation_extracted_data`, or the machine zero-UUID `extracted_by`). `ensure_manual_ct_qc_prerequisite()` raises **403** for MANUAL work not already at `ct_qc_approved`/`customer_review`. |
| `backend/api/v3_processing_workflow.py` | `start_item` (stage `review`) and `customer_review_item` call the shared guard **after** the state-machine check and **before** any mutation / D37 charge. |
| `backend/api/v3_operations.py` | Ops `start_item` (stage `review`) calls the shared guard after the state-machine check. |

No schema, migration, RLS, billing, audit, notification, QC-authority or
permission changes. No new role/permission introduced.

### Guard ordering (preserves existing 403/409 semantics)

- The **state-machine** check (`_require_transition`) runs first, so a status
  that cannot reach the target still returns the existing **409**
  (e.g. `rejected → approved`, `reviewed → customer_review`).
- The **CT-QC prerequisite** then runs, returning **403** only where the
  transition would otherwise be permitted (e.g. manual `calculated → approved`).
- The guard always precedes `charge_processing`: a denied action is zero
  workflow + zero billing mutation.

## 3. Protection checklist (PO §2)

| # | Requirement | Status |
| - | ----------- | ------ |
| 1 | Manual work cannot reach Customer Review/Approval before CT-QC | ✔ |
| 2 | Consultant manual work cannot bypass CT-QC | ✔ (tested) |
| 3 | Internal/ops manual work cannot bypass CT-QC | ✔ (tested) |
| 4 | PE restrictions intact | ✔ (unchanged) |
| 5 | Automatic processing keeps no routine CT-QC | ✔ (tested) |
| 6 | Automatic job-review flow unchanged | ✔ (`/jobs/{id}/review` untouched) |
| 7 | Customer approval remains owner/admin controlled | ✔ (`require_org_admin` unchanged) |
| 8 | Billing remains exclusively at Customer Approval | ✔ (single charge; tested) |
| 9 | Guards execute before mutation/charge | ✔ |
| 10 | Audit-after-successful-mutation intact | ✔ (denials add no audit rows) |
| 11 | `None → 409` CT-QC concurrency protection untouched | ✔ (no change to the decision path) |
| 12 | RLS unchanged | ✔ (no migration; 46 migrations) |
| 13 | Manual rework cannot reuse stale CT-QC approval | ✔ (`reviewed` has no customer exit; CT-QC re-required) |
| 14 | No new role/permission/authority | ✔ |

---

## 4. Tests

New focused suite `backend/tests/unit/api/test_p6_2b_4_ct_qc_prerequisite.py`
(13 tests): flow-map assertion for `reviewed`; MANUAL claim/approval denials
(consultant, internal ops, PE, org) with zero mutation/billing/audit;
`ct_qc_approved` MANUAL proceeding to review + approval (one charge);
AUTOMATIC (job + machine output) claiming/approving without CT-QC; and
fail-closed P1 edge cases (job with no machine output; machine marker without job).

| Suite | Result |
| ----- | ------ |
| `tests/unit/api/test_p6_2b_4_ct_qc_prerequisite.py` | **13 passed** (EXIT 0) |
| Regression group (P6-2B-4/3/2/1, P6-2A/R1, P6-BILL-1, billing, ops, qc, processing-origin, dual-origin domain, workflow, phase-1 core, automatic jobs/payload/services, operations auth, scope-aware authz, PE auth) | **all passed** (EXIT 0) |
| Full `pytest tests/unit -q` | **1,576 collected, EXIT 0** (1,563 prior + 13 new) |

One existing P6-2B-3 assertion initially returned 403 where it expected 409
(`test_rejected_item_cannot_reach_customer_review_or_approval`). Fixed by guard
**ordering** (state machine first). **No test was modified** to make the suite green.

---

## 5. Evidence preserved (not added)

Existing evidence chains were preserved untouched: audit events and actor
stamps, `processing_origin` / `processing_entity_id`, job linkage
(`source_item_id`), CT-QC decisions, customer approval, billing events and
rework history.

---

## 6. Database baseline

Read-only SQL before/after (local investor demo DB) — **identical**:
`organizations` 975 · `consultant_firm_members` 54 · `consultant_profiles` 55 ·
`consultant_clients` 917 · `manual_extraction_items` 260 ·
`work_item_assignments` 0 · `billing_plans` 6 · `customer_subscriptions` 0 ·
`billing_orders` 0 · `billing_credit_ledger` 0 · migrations 46 (unchanged) ·
workflow-state rows (`reviewed`, `consultant_reviewed`, `ct_qc*`,
`customer_review`) 0. No persistent fixture created (suite is in-memory).

---

## 7. Git status

- Branch `main`; HEAD unchanged `1639121`.
- **Modified:** `backend/domain/partners.py`,
  `backend/api/v3_processing_workflow.py`, `backend/api/v3_operations.py`.
- **Added:** `backend/api/processing_mode.py`,
  `backend/tests/unit/api/test_p6_2b_4_ct_qc_prerequisite.py`, this report.
- No secrets introduced; no unrelated changes absorbed.

---

## 8. Known limitations (explicitly deferred, per PO §3/§4)

P1 is a **containment** predicate, not the final provenance architecture:

- **Mixed/corrected cases** (human correction of automatically-extracted data, or
  human change to mapping/factor) may still be classified AUTOMATIC by P1 and
  therefore not acquire routine CT-QC. The PO accepted this as a **future
  provenance (P2/D7)** concern; P2 was not implemented.
- P1 is fail-closed: anything not positively recognised as automatic is MANUAL.
- Automatic-failure-then-human-completion resolves to MANUAL under P1 (no machine
  output), matching the PO's stated intent.
- The customer-review **queue listing** (`GET /processing/customer-review`) was
  left unchanged: a manual `calculated` item may still be listed, but the
  **claim and approval are denied (403)**. Filtering the read view is a UX
  concern, not a security control, and is deferred.
- Explicitly NOT implemented (future D7/Evidence work): Evidence
  Standard/Report, one-click trail, auditor role, evidence API/export,
  document-version architecture, generalized provenance migration, diagnostics,
  AI data-reuse.

---

## 9. Final status

**P6-2B-4 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION**

No independent verification was performed by the implementer; the result is
handed back for an independent gate.

