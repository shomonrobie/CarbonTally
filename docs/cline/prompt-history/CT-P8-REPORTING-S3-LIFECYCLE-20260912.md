# CT-P8-REPORTING-S3-LIFECYCLE-20260912

**Prompt ID:** `CT-P8-REPORTING-S3-LIFECYCLE-20260912`
**Date:** 2026-09-12
**Task purpose:** Bounded Phase 8 Reporting **S3** — the report **version lifecycle**
foundation: the ratified state machine, version-scoped guarded transitions, the customer
Owner/Admin authorization boundary, and append-only lifecycle audit events.
**Type:** IMPLEMENTATION (bounded). No narrative overlay, no comments, no frozen PDF/artefact,
no content/PDF hashing, no RLS change, no frontend, no Insight/AI, no billing, no Phase 7.
**Status:** `S3 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`

## Starting Repository State

| Item | Value |
|---|---|
| Branch | `main` |
| Starting HEAD | `b4712865cb4f4bf96cda2b4274f47fd527267110` (docs: Phase 9 baseline) |
| Prior verified S1 commit | `c86b83c6b0535b7033852fc93ccd130f14fc7f3f` (intact) |
| Pre-existing modified | 208 |
| Pre-existing untracked | 52 |
| Staged | 0 |

All pre-existing dirty/untracked work — including
`docs/architecture/CARBONTALLY_PHASE9_SYSTEM_RUNTIME_AND_OPERATIONAL_INTELLIGENCE_BASELINE_20260912.md`
and its Phase 9 prompt-history file — was left untouched.

## Authoritative Sources

1. `CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` §12–§14 (states, transition matrix
   T1–T18), §17–§18 (approval, post-approval change), §21 (audit requirements), §22 (authorization
   matrix), §23 (API design), §25 (schema Option A), §26 (concurrency), §32 (acceptance criteria).
2. `CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md` §10 (ratified lifecycle +
   invariants), §11 (approval model), §17.3 (reuse warnings).
3. `CARBONTALLY_PHASE8_OPEN_DECISION_CLOSURE_AND_IMPLEMENTATION_AUTHORISATION_20260912.md` §7.3
   (S1 boundary), §16 (S3 dependencies: A2/A4/A5/A6/A9).

## Discovery Findings (traced from the implementation)

| # | Finding | Evidence |
|---|---|---|
| 1 | `report_versions` had **no** lifecycle column — the six ratified version states were unrepresentable. A minimal migration was genuinely required (spec §25 Option A) | `init_schema.sql:1003-1016` |
| 2 | `report_generation_queue.status` is the **generation** state machine and is deliberately NOT reused (ratified §10.3 / §17.3) | `data/reports.py` |
| 3 | The canonical audit substrate already exists and is append-only; its action-prefix map already routes any `report*` action to `CAT_REPORT` — no taxonomy change needed | `data/audit.py`, `domain/audit.py`, migration `20260912000000` |
| 4 | `report_versions` **already has RLS enabled** in both local databases — the spec's "no RLS on report tables" note (E20) is outdated. Recorded, not changed | `pg_class.relrowsecurity = true` |
| 5 | Owner/Admin authorization precedent exists (`require_org_admin`, `ensure_org_audit_access`), but `require_org_admin` also admits internal staff → a dedicated customer-only guard was required (PO §6: staff must not approve) | `auth.py:470`, `api/dependencies.py:232` |
| 6 | A real-DB integration harness exists (dedicated `carbontally_test`, `pool`, `make_org`) | `tests/integration/conftest.py` |

## Changes

| File | Change |
|---|---|
| `supabase/migrations/20260913000000_p8_report_lifecycle_status.sql` | **NEW** — additive/idempotent: `report_versions.status VARCHAR(32) NOT NULL DEFAULT 'DRAFT'` + six-state `CHECK`. No RLS/policy change; no other table touched |
| `backend/domain/report_lifecycle.py` | **NEW** — pure state machine: six states, transition table (T3/T7/T8/T11/T12), `resolve_transition`, `allowed_actions`, audit-event names (§21.2), declared authority per action |
| `backend/data/report_versions.py` | `status` in the column/row mapping and `create()` (default `DRAFT`); **NEW** `get_by_number()` (version-scoped read) and `set_status()` (atomic `WHERE id AND report_id AND status = expected` state guard → `None` on mismatch) |
| `backend/api/v3_reports.py` | Version-scoped lifecycle endpoints (submit / request-changes / reject / approve / finalize / new-version), the customer-only authorization guard, and the best-effort append-only audit writer |
| `backend/tests/unit/api/fakes.py` | `MemoryReportVersions` mirrors the new contract (`status`, `get_by_number`, guarded `set_status`) |
| `backend/tests/unit/api/test_v3_report_lifecycle.py` | **NEW** — 31 tests |
| `backend/tests/integration/test_report_lifecycle.py` | **NEW** — 6 real-DB tests |

## Endpoints (all version-scoped; state guard server-side)

```
POST /api/v3/reports/{id}/versions/{n}/submit          DRAFT            -> REVIEWED
POST /api/v3/reports/{id}/versions/{n}/request-changes REVIEWED         -> CHANGES_REQUESTED
POST /api/v3/reports/{id}/versions/{n}/reject          REVIEWED         -> REJECTED
POST /api/v3/reports/{id}/versions/{n}/approve         REVIEWED         -> APPROVED
POST /api/v3/reports/{id}/versions/{n}/finalize        APPROVED         -> FINAL
POST /api/v3/reports/{id}/versions                     CHANGES_REQUESTED/REJECTED/APPROVED/FINAL -> NEW DRAFT
```

`409` on an invalid transition or a lost concurrency race; `403` on authorization failure;
`404` on unknown report/version. `FINAL` is terminal; an approved/final version is never mutated.

**Authorization:** submit / new-version require an organisation write role (owner/admin/member);
request-changes / reject / approve / finalize require **owner/admin**. Member and Viewer never
approve; Consultants, Processing Entities and CarbonTally internal staff are never lifecycle actors.

## Deliberate scope boundaries (documented, not implemented)

* **revoke-approval** (T13) — PO decision `A6` (§34-A6) is still open, so no revocation endpoint ships.
  A post-approval change is served by the new-version path (ratified §10.2 invariant 2 / §18 Option A).
* **narrative overlay / comments / frozen PDF / hashing / approval columns** — later bounded stages;
  the audit trail is the append-only approval record.
* **finalize** records the lifecycle state + audit event only; producing/storing/hashing the frozen
  artefact is the later S5 stage.
* **RLS** — unchanged; not claimed as fixed (S2 treatment).
* **frontend** — unchanged; `status` is additive to existing version payloads.

## Tests

| Command (from `backend/`) | Result |
|---|---|
| `pytest tests/unit/api/test_v3_report_lifecycle.py` | **31 passed** |
| `pytest tests/unit/api/test_v3_reports.py tests/unit/api/test_reporting.py tests/unit/api/test_v3_report_lifecycle.py` | **118 passed** |
| `pytest tests/unit/api` | **1066 passed** (was 1035 before S3) |
| `pytest tests/integration/test_report_lifecycle.py tests/integration/test_report_versions.py` | 11 passed, **1 pre-existing failure** |
| `pytest tests/integration/test_reports.py` | 6 passed, **3 pre-existing failures** |

**Pre-existing / out of scope (unchanged, not repaired):** `test_create_and_roundtrip_version`,
`test_mark_generating`, `test_mark_failed_persists_error`,
`test_create_request_records_created_by_and_name` — `asyncpg.DataError: invalid input for query
argument ... 'user-1' (invalid UUID ...)`. These pass the non-UUID literal `"user-1"` into UUID
columns in pre-existing test data.

## Database / Migration

* Migration file added and applied **locally** to both `carbontally_test` (dedicated integration DB)
  and the local `postgres` application DB. Additive/idempotent; 16 existing rows converge to `DRAFT`
  via the column default (no row content rewritten).
* `supabase_migrations.schema_migrations` in the local `postgres` DB is **already behind** the
  migration files (latest recorded `20260903010000...`), so no history row was fabricated; the
  migration is idempotent and safe to re-apply by the normal tooling.
* No RLS policy added/removed/disabled. No other table/column/index/constraint touched.

## Scope Confirmation

No report lifecycle UI · no narrative overlay · no comments · no evidence requests · no frozen PDF ·
no PDF SHA-256 · no content hashing · no auditor role/workspace · no RLS change · no CarbonTally
Insight · no AI/RAG/LangChain · no billing · no Phase 7 change · no deployment/env change · no
Phase 9 change · not pushed.

