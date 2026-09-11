# CarbonTally WS4 — Gate 6 — Workstream W2 Implementation Report
**G6-B: Human-After-Automation Audit Attribution (job-level human gates)**

- **Date:** 4 September 2026
- **Authority:** G6-A PASSED/ACCEPTED. This workstream addresses **G6-B only**
  (readiness report §10 G-B): job-level human-after-automation actions
  (**confirm**, **retry**, **review** approve/reject) are now explicitly
  attributable through the existing append-only audit trail and distinguishable
  from the preceding machine extraction event.
- **Git HEAD:** `1639121`. **No commit. No push.** G6-C and G6-D were **not**
  implemented.

---

## 1. Files changed

| File | Change |
|---|---|
| `backend/api/v3_automatic_processing.py` | Added the best-effort `_record_human_gate_audit(...)` helper and audit call sites in `confirm_job`, `retry_job` and `review_job` (approve and reject). No authorization logic changed. |
| `backend/tests/unit/api/test_v3_automatic_processing_jobs.py` | Seven focused G6-B API tests appended (module now 15 tests, all in-memory, no DB). |
| `docs/architecture/CARBONTALLY_WS4_GATE6_W2_REPORT.md` | This report. |

No other files were modified. G6-A files (`domain/automatic_processing.py`,
`data/document_processing.py`, `services/automatic_processing.py`, the G6-A
migration and `automation_extracted_data`) were **not** touched.

## 2. Exact human actions now audited

| Endpoint | Audit action | When |
|---|---|---|
| `POST /api/v3/processing/jobs/{id}/confirm` | `automatic_processing:confirmed` | Successful human confirm of a blocked/failed job (re-enqueue after rework) |
| `POST /api/v3/processing/jobs/{id}/retry` | `automatic_processing:retried` | Successful human retry of a failed/blocked job |
| `POST /api/v3/processing/jobs/{id}/review` (approved) | `automatic_processing:approved` | Successful owner/admin customer approval |
| `POST /api/v3/processing/jobs/{id}/review` (rejected) | `automatic_processing:rejected` | Successful owner/admin customer rejection (routes back to manual review) |

These were the actions that previously persisted the human actor only in DPQ
columns (`updated_by`, `customer_reviewed_by/at`) without an audit-trail event.
No duplicate events are created — no other code path records these actions.

## 3. Exact audit-event contract

Written to `public.audit_trail` via the existing append-only audit repository
(the same `repos.audit.record` path used by Gate-4 human item actions):

- `action_type` — one of `automatic_processing:confirmed` /
  `automatic_processing:retried` / `automatic_processing:approved` /
  `automatic_processing:rejected` (new vocabulary under the existing
  `automatic_processing:` prefix; the machine event remains
  `automatic_processing:extracted`).
- `table_name` = `document_processing_queue`; `record_id` = job id.
- `metadata->>'correlation_id'` = job id (same correlation as the machine
  extraction event).
- `metadata->>'actor'` = authenticated human user id; `performed_by` column =
  that user id (the audit repo stores a UUID actor in `performed_by`).
- `performed_at` = timestamp of the human action (`occurred_at`).
- `changes` (JSONB) — human-action context: `status_from`, `status_to`,
  `stage_from`, `stage_to`, `gate` (`confirm`/`retry`/`approve`/`reject`),
  `source_item_id`, plus `approved`/`rejection_reason`/`customer_notes` for
  review and `re_entry_stage` for confirm.
- `old_data`/`new_data` are not populated (consistent with the Gate-4 F1 item
  audit convention); no document content, payloads or secrets are stored.

## 4. Actor-source mechanism

Actor identity comes **only** from the authenticated request context:
`current_user.user_id` (the same authoritative source used by `reenqueue(
updated_by=...)` and `complete_review(reviewer=...)`). No untrusted client
field can supply or override the actor — the endpoint request models do not
accept an actor field, and a client-supplied `"actor"` value is ignored
(verified by test). A human action can therefore never be recorded as
`automatic_pipeline`, and no second identity mechanism was introduced.

## 5. Machine-vs-human provenance distinction

Both event families share the entity/correlation (job) but differ on the actor
and action vocabulary, so an auditor can distinguish and order them:

- **Machine:** `automatic_processing:extracted`, actor `automatic_pipeline`
  (non-UUID label → `performed_by` = system zero UUID, actor in metadata).
- **Human:** `automatic_processing:confirmed|retried|approved|rejected`,
  actor = authenticated human user id.

Ordering is established via `performed_at` (the machine extraction event is
persisted before any human gate can exist on the job) and is asserted in test.
`changed_fields` documents the before/after stage/status of the human action.

## 6. Authorization / security verification

- Events are emitted only inside the already-authorized endpoints **after** the
  existing guards pass: `ensure_processing_org_access` (confirm/retry/review)
  and `require_org_admin` for the customer review decision — the existing
  authorization remains the security boundary.
- Cross-organisation requests remain denied (403) **before** any event is
  created; verified by test (no audit entry is produced for a denied action).
- PE staff and plain org members remain denied on the review surface (existing
  tests unchanged and passing); no PE/Customer operations-authority expansion.
- No new endpoint, RLS policy, role or resource path was added; RLS is
  unchanged (the audit repo writes as the existing service-role path already
  used by Gate-4 human item audits).
- Audit recording is best-effort and can never break the human gate.

## 7. Tests and results

Commands (all from `backend/`):

- `pytest tests/unit/api/test_v3_automatic_processing_jobs.py -q`
  → **15 passed** (8 existing + 7 new G6-B tests).
- Regression: `pytest tests/unit/api/test_gate4_remediation_actor_provenance.py
  tests/unit/api/test_v3_automatic_processing_payload.py
  tests/unit/domain/test_automatic_processing.py
  tests/unit/services/test_automatic_processing.py -q`
  → **38 passed** (Gate-4 human provenance, G6-A service/domain, job payload).
- `py_compile` of the changed modules → OK.

New G6-B tests prove: (1) authorized confirm → `automatic_processing:confirmed`
with the authenticated human actor; (2) retry → `automatic_processing:retried`;
(3) approve → `automatic_processing:approved`; (4) reject →
`automatic_processing:rejected`; (5) actor comes from auth context, never from
a client-supplied field; (6) correct job/resource correlation; (7) machine
event (`automatic_pipeline`) and human event coexist, are distinguishable and
are ordered machine-first; (8) Gate-5 automation block and G6-A
`automation_extracted_data` are unchanged by the human gates; (9) cross-scope
denied actions produce no event.

## 8. Database impact

**No migration was required.** The existing append-only `audit_trail`
infrastructure already supports these events (generic `action_type`,
`table_name`, `record_id`, `performed_by`, `changes`, `metadata` columns). No
RLS, schema or data changes were made to the main or test databases; existing
data is unchanged; no fixture residue.

## 9. Legacy-data treatment

No historical events were fabricated or backfilled. Audit events are written
only when a real human confirm/retry/review action occurs after this change;
older job actions remain as they were (actor columns only, no audit row).

## 10. G6-C and G6-D not implemented

Confirmed: no resume-marker invalidation (G6-C) and no item-level
extraction-edit audit (G6-D) were introduced. G6-A remains frozen and
untouched.

**Status: G6-B IMPLEMENTED & TESTED — awaiting PO review/acceptance.**

