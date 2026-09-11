# Phase 5 — WS0 Baseline & Resume Notes (D38 / D39 / D40)

- **Status:** WS0 COMPLETE. WS1–WS5 NOT STARTED.
- **Date:** 2 September 2026
- **Authorisation:** PO approved P5-1..P5-7 (Phase 5 Implementation directive).

This file exists so a continuation session can resume without re-deriving the
baseline. It is documentation only — no implementation was performed.

## WS0 baseline (verified live against the running DB)

| Item | Value |
|---|---|
| `emission_factors` | 7,049 (unchanged) |
| `supabase_migrations.schema_migrations` | 42 (unchanged; do not add until WS1 approved migration) |
| `organizations` | 975 |
| `manual_extraction_items` | 260 |
| `manual_extraction_batches` | 56 |
| `conversations` | 34 |
| `notifications` | 0 |
| DB connection | `backend/.env DATABASE_URL` (local Supabase Postgres) |

## Key schema facts (evidence for WS1–WS3)

- `conversations.organization_id` is **NOT NULL**; `staff_id`/`customer_id`
  nullable; **no** `processing_entity_id` column → D39 Option B requires an
  additive nullable `processing_entity_id` + making `organization_id` (and
  `messages.organization_id`) nullable for entity-only threads, plus
  `conversation_kind` (`org`/`entity`) and RLS that never lets a NULL-org
  entity row satisfy an org policy.
- `messages.organization_id` is NOT NULL (same consideration).
- `notifications` uses generic `recipient_type`/`recipient_id` (NOT NULL) →
  recipient = resolved actor; safe to reuse for PE recipients.
- `review_assignment_history` is review-attribution (staff-centric, legacy);
  `processing_assignments`/`reassignment_history`/`staff_workload` are
  dormant. D38 = additive append-only `work_item_assignments` ledger over
  `manual_extraction_items` (+ partial unique index on open assignment) with
  V3 `audit_trail` records; item `processing_origin`/`processing_entity_id`
  stay immutable.
- Repositories are built from an asyncpg pool (`api/dependencies.py`
  `RepositoryBundle` → `ManualExtractionRepository(pool)`, `AuditRepository`).
  New D38 methods belong on `ManualExtractionRepository` (file
  `backend/data/manual_extraction.py`, class line ~132) or a thin
  `services/work_items.py` delegating to it.

## Suggested WS1 entry points (next session)

1. Migration 43: `supabase/migrations/2026…_phase5_work_item_assignments.sql`
   (append-only ledger + partial unique index; RLS enabled deny-by-default;
   no changes to existing rows/factors).
2. Repository methods on `ManualExtractionRepository`
   (`open_assignment`, `record_assignment`, `close_assignment`,
   `assignment_history`).
3. Ops router (`v3_operations.py`): claim/assign/reassign/release/complete +
   history under `/api/v3/ops/items/{item_id}/work/*` — internal-staff guard
   (`require_internal_staff`), capability `can_process|can_review`, batch/org
   scope, immutable origin.
4. PE router (`v3_pe.py`): claim/release/complete/history under
   `/api/v3/pe/items/{item_id}/work/*` — `require_pe_capability`,
   `_ensure_assigned_item` (own entity only).
5. Audit via `repos.audit.record(AuditEntry(...))` (pattern in `v3_pe.py`
   ct_qc audit and `v3_operations.py` `_record_batch_assignment_audit`).

Then run the WS1 verification gate (ALLOW/DENY matrix in the directive §5.9)
before WS2.
