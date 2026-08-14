# CarbonTally V3 — V3M-1 + V3M-2 Implementation Verification

**Status:** V3M-1 + V3M-2 IMPLEMENTED — APPLICATION PENDING (ENVIRONMENT LIMITATION)
**Date:** 2026-08-10 (implementation) · 2026-08-11 (application attempt) · Branch: `main`
**Scope:** CarbonTally V3 Implementation Phase 1 — Processing Entity foundation
(V3M-1) + Processing Entity relationships to existing work structures (V3M-2).
**Mode:** Implementation of the two approved migrations + integration tests +
read-only verification SQL. **No** customer factors (V3M-3), issues (V3M-5),
deferred providers (V3M-4), storage redesign, legacy RLS hardening, frontend,
API redesign, auto-assignment engine, SLA redesign or new queue subsystem was
implemented.

**Authoritative sources:**
- `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md` (ADR-V3-001 — DECIDED, Option B; ADR-V3-010 — PROVISIONALLY DECIDED)
- `docs/architecture/CarbonTally_V3_Architecture_Specification_v1.0.md` (§7.1 convention; §8–§9)
- `docs/audit/CarbonTally_V3_Database_Implementation_Impact_and_Migration_Plan_v1.0.md` (§3–§4, §9)

---

## 1. Files Changed

| File | Action |
|---|---|
| `supabase/migrations/20260810000000_v3m1_processing_entities.sql` | **NEW** — V3M-1 migration (processing_entities + staff_profiles.entity_id) |
| `supabase/migrations/20260810010000_v3m2_entity_relationships.sql` | **NEW** — V3M-2 migration (manual_review_queue.entity_id, upload_batches.entity_id) |
| `database/v3/verification_v3m1_v3m2.sql` | **NEW** — read-only verification SQL |
| `backend/tests/integration/test_v3m1_v3m2_processing_entities.py` | **NEW** — integration tests (10 invariants) |
| `docs/audit/CarbonTally_V3_V3M1_V3M2_Implementation_Verification.md` | **NEW** — this report |

No historical migration was modified. No backend/API/frontend code was modified.


## 2. Migration Applied

The two migrations were **created** in the implementation task. **Application
attempt (2026-08-11):** the Supabase workflow could **not** be executed this
session because the development shell/terminal is non-functional — every
command (including `echo`, `supabase --version`, and `supabase db reset`)
failed with "Command completion could not be observed; the command may still be
running." This is the same environment limitation recorded throughout Phases
9–10 and D14. The migrations were therefore **not applied to any database in
this session**.

**What was verified by read-only file inspection this session:**

1. **Supabase project configuration intact** — `supabase/config.toml` exists
   with `project_id = "carbon_ledger"`, `[db] port = 54326`,
   `shadow_port = 54320`, `major_version = 17`, `[db.migrations] enabled = true`,
   `[db.seed] enabled = false`.
2. **Migration chain order correct** — the two V3 migrations are the **final**
   files in the chain, correctly ordered after the M1–M8/RC1/RC2 chain:
   - `20260810000000_v3m1_processing_entities.sql` (V3M-1)
   - `20260810010000_v3m2_entity_relationships.sql` (V3M-2)
3. **No unexpected V3 migrations after V3M-2** — search confirms no
   `v3m3…v3m9`, `customer_factors`, or `issues` migration files exist; V3M-3/
   V3M-4/V3M-5 remain documentation-only (deferred/blocked).
4. **Both migration files read and verified correct** — V3M-1 creates
   `processing_entities` (id, name, description, status VARCHAR+CHECK, metadata
   JSONB, timestamps), adds `staff_profiles.entity_id` (nullable FK, ON DELETE
   RESTRICT) + index, and applies the deny-by-default RLS floor. V3M-2 adds
   `entity_id` to `manual_review_queue` and `upload_batches` only (FK RESTRICT +
   index); **no** `entity_id` on dormant/technical queues.

The canonical application commands for a future session are:

```
# Development database (authoritative) — preferred Supabase workflow:
#   cd /d/carbon_ledger && supabase db reset
#   (replays the full migration chain from the supabase/migrations directory)
#
# Fallback (if the repository's documented workflow requires direct SQL):
psql "postgresql://postgres:postgres@127.0.0.1:54326/postgres" \
  -f supabase/migrations/20260810000000_v3m1_processing_entities.sql
psql "postgresql://postgres:postgres@127.0.0.1:54326/postgres" \
  -f supabase/migrations/20260810010000_v3m2_entity_relationships.sql

# Test database (carbontally_test), before running the integration tests:
psql "postgresql://postgres:postgres@127.0.0.1:54326/carbontally_test" \
  -f supabase/migrations/20260810000000_v3m1_processing_entities.sql
psql "postgresql://postgres:postgres@127.0.0.1:54326/carbontally_test" \
  -f supabase/migrations/20260810010000_v3m2_entity_relationships.sql
```

Both migrations are **idempotent** (CREATE TABLE IF NOT EXISTS, ADD COLUMN IF NOT
EXISTS, guarded FK creation, CREATE INDEX IF NOT EXISTS, idempotent grants/RLS),
so re-running is a safe no-op.

## 3. Tables Changed

| Table | Action |
|---|---|
| `processing_entities` | **NEW** — first-class Processing Entity domain (ADR-V3-001 Option B) |
| `staff_profiles` | **EXTEND** — `entity_id` nullable FK (V3M-1) |
| `manual_review_queue` | **EXTEND** — `entity_id` nullable FK (V3M-2) |
| `upload_batches` | **EXTEND** — `entity_id` nullable FK (V3M-2) |

**Deliberately NOT changed** (per the impact plan §4.3 / ADR-V3-016/004):
`processing_queue`/`processing_assignments`/`processing_steps` (dormant —
retirement per ADR-V3-016), `document_processing_queue` (technical state machine —
ADR-V3-004), `report_generation_queue` (technical output store),
`review_assignment_history` (attribution derived, no column).

## 4. Columns Added

| Table | Column | Type | Nullable | Convention |
|---|---|---|---|---|
| `staff_profiles` | `entity_id` | UUID | YES | NULL = CarbonTally internal; populated = Processing Entity staff (Q5) |
| `manual_review_queue` | `entity_id` | UUID | YES | NULL = CarbonTally internal; populated = Processing Entity performing the Work Item |
| `upload_batches` | `entity_id` | UUID | YES | NULL = CarbonTally internal; populated = Processing Entity allocated the batch |

## 5. Constraints Added

| Constraint | Definition | ON DELETE |
|---|---|---|
| `staff_profiles_entity_id_fkey` | `entity_id` FK → `processing_entities(id)` | **RESTRICT** |
| `manual_review_queue_entity_id_fkey` | `entity_id` FK → `processing_entities(id)` | **RESTRICT** |
| `upload_batches_entity_id_fkey` | `entity_id` FK → `processing_entities(id)` | **RESTRICT** |
| `processing_entities_status_check` | `status IN ('active','remediation','suspended','terminated')` | — |

**Rationale for ON DELETE RESTRICT** (V3M-1 migration header): the NULL convention
(`entity_id IS NULL` = CarbonTally internal) must never be corrupted by a SET NULL
that would silently convert entity staff into "CarbonTally internal". Entity rows
are never hard-deleted while referenced (Q6 lifecycle preserves history).

## 6. Indexes Added

| Index | Table | Column |
|---|---|---|
| `idx_staff_profiles_entity_id` | `staff_profiles` | `entity_id` |
| `idx_manual_review_queue_entity_id` | `manual_review_queue` | `entity_id` |
| `idx_upload_batches_entity_id` | `upload_batches` | `entity_id` |

## 7. RLS Changes

| Table | RLS action |
|---|---|
| `processing_entities` | **ENABLE ROW LEVEL SECURITY** + service_role ALL + authenticated DML (no TRUNCATE/TRIGGER/REFERENCES/MAINTAIN). **NO policies created** — deny-by-default for authenticated. |
| `staff_profiles` | **No change** — already deny-by-default for authenticated (RC2 §8); `entity_id` column does not alter existing posture. |
| `manual_review_queue` / `upload_batches` | **No change** — existing tenant RLS (`*_tenant_*` via `is_org_member`) untouched; no entity-scoped policy added. |

**Why deny-by-default only:** entity-scoped access policies (`is_entity_member()`)
belong to ADR-V3-010 (PROVISIONALLY DECIDED, INVESTIGATE flags). Per the task
instruction, an RLS requirement that cannot be safely implemented without a
decision belonging to ADR-V3-010 is **reported, not invented**. The deny-by-default
floor is the strongest safe posture and satisfies "Processing Entity isolation":
no `authenticated` role can read/write `processing_entities` until ADR-V3-010
defines entity-scoped access.

## 8. Test Results

**Test file:** `backend/tests/integration/test_v3m1_v3m2_processing_entities.py`
(10 async tests against `carbontally_test`; `pytestmark = pytest.mark.asyncio`).

| # | Test | Verifies |
|---|---|---|
| 1 | `test_processing_entities_create_and_fetch` | entity rows can be created |
| 2 | `test_processing_entities_status_check` | lifecycle CHECK rejects invalid status |
| 3 | `test_staff_can_reference_entity` | valid staff → entity FK |
| 4 | `test_staff_null_entity_is_internal` | CarbonTally internal staff stay `entity_id IS NULL` |
| 5 | `test_staff_invalid_entity_rejected` | FK rejects random entity reference |
| 6 | `test_migration_preserves_existing_work_rows` | existing work rows/columns preserved |
| 7 | `test_org_tenant_rls_still_present` | org tenant RLS unchanged |
| 8 | `test_processing_entities_deny_by_default` | RLS enabled, zero policies |
| 9 | `test_entity_fks_and_indexes_exist` | three FKs (RESTRICT) + three indexes |
| 10 | `test_factor_baseline_unchanged` | total 7,049 / DEFRA 7,029 / SEAI 20 |

**Execution status (2026-08-11 attempt):** the integration suite requires
`carbontally_test` to be reachable with the V3M-1/V3M-2 migrations applied.
The development shell could not execute any command this session (terminal
non-functional — same environment limitation recorded throughout Phases 9–10,
D14, and the prior V3M-1/V3M-2 task), so the suite was **not run** here.
The test file itself was verified present and complete (10 invariants) by
read-only inspection. Canonical command for a future session:

```
cd backend && python -m pytest tests/integration/test_v3m1_v3m2_processing_entities.py -q
```

## 9. Factor Baseline Before/After

| Metric | Before | After | Expected |
|---|---|---|---|
| TOTAL `emission_factors` | 7,049 (verified) | 7,049 (unchanged — migrations are additive, no factor DML) | 7,049 |
| DEFRA-DESNZ / GB | 7,029 | 7,029 | 7,029 |
| SEAI / IE | 20 | 20 | 20 |

The V3M-1/V3M-2 migrations contain **no statement touching `emission_factors`**;
the baseline invariant is enforced by the migration design and by
`test_factor_baseline_unchanged`.

## 10. Rollback Considerations

| Change | Rollback |
|---|---|
| `processing_entities` table | `DROP TABLE public.processing_entities;` (after dropping the three entity FKs — RESTRICT prevents orphaned references) |
| `staff_profiles.entity_id` | `ALTER TABLE public.staff_profiles DROP COLUMN entity_id;` (nullable — no data loss) |
| `manual_review_queue.entity_id` / `upload_batches.entity_id` | `DROP COLUMN` — nullable, no data loss |
| RLS on `processing_entities` | `DISABLE ROW LEVEL SECURITY` + revoke grants — reversible |

All changes are additive and reversible; no existing data is destroyed by
rollback.

## 11. Known Limitations

1. **Migrations not applied this session (2026-08-11)** — the development shell
   could not execute any command (`supabase db reset`, `psql`, pytest all
   failed with "Command completion could not be observed"), so the migrations
   remain un-applied to both the development database and `carbontally_test`.
   Application commands are provided in §2; the Supabase CLI workflow
   (`supabase db reset`) is the repository's established mechanism.
2. **Entity-scoped access policies deferred** — `processing_entities` is
   deny-by-default for `authenticated`; `is_entity_member()` and entity-scoped
   policies are ADR-V3-010 scope (reported, not invented).
3. **Lifecycle state vocabulary is minimal** — `active / remediation / suspended /
   terminated` per Q6; exact values finalized in V3 design.
4. **Contract metadata is generic JSONB** — exact commercial fields deferred (Q1).
5. **No backend/API repository for entities** — database-only per the task scope;
   a `ProcessingEntity` domain/repo/API is future backend work (ADR-V3-001).
6. **Live factor-baseline verification not possible this session** — the read-only
   SQL in `database/v3/verification_v3m1_v3m2.sql` (§5) could not be executed
   (shell non-functional). The prior verified record (7,049 = DEFRA 7,029 +
   SEAI 20) stands, and the migrations contain no `emission_factors` DML.

## 12. Confirmation — Out of Scope NOT Implemented

- **V3M-3 Customer Factors** — NOT implemented (no `customer_factors` table, no
  snapshot-FK change). ✅
- **V3M-5 Issue Management** — NOT implemented (no `issues` table). ✅
- **V3M-4 Deferred providers** — NOT implemented (no country-CHECK/natural-key
  widening). ✅
- **Storage redesign / legacy RLS hardening / frontend / API redesign /
  auto-assignment engine / SLA redesign / new queue subsystem** — NOT implemented. ✅

## 13. Application Execution Record (2026-08-11)

| Step | Attempted | Result |
|---|---|---|
| Supabase CLI availability (`supabase --version`) | Yes | **Could not be verified** — shell non-functional ("Command completion could not be observed") |
| `supabase db reset` (development DB replay) | Yes | **Could not be executed** — shell non-functional |
| Migration replay V3M-1 → V3M-2 | Yes | **Could not be executed** — shell non-functional |
| V3M-1 verification (table/column/FK/RLS) | Yes (read-only file inspection) | **Migration files verified correct**; live DB verification not possible |
| V3M-2 verification (entity_id/FK/index) | Yes (read-only file inspection) | **Migration files verified correct**; live DB verification not possible |
| RLS floor verification (deny-by-default, 0 policies) | Yes (read-only file inspection) | **Migration file verified correct** (ENABLE RLS, no policies); live check pending |
| Factor baseline (7,049 = 7,029 + 20) | Yes (attempted) | **Not live-verified** — read-only SQL could not run; prior verified record stands; migrations contain no factor DML |
| Integration tests (`test_v3m1_v3m2_processing_entities.py`) | Yes | **Not run** — shell non-functional; test file verified present/complete (10 invariants) |
| Report update with actual status | Yes | **Complete** — this document |

**Exact final state:** the V3M-1 + V3M-2 migration files exist, are correctly
ordered as the final files in the Supabase migration chain, are fully verified
by read-only inspection (structure, FKs, RESTRICT, indexes, RLS floor,
idempotency, factor-baseline neutrality), and are **ready to apply** via the
repository's established Supabase workflow (`supabase db reset`) in a session
with a functional shell. They have **not yet been applied** to the development
database or `carbontally_test`, and the integration suite has **not yet been
executed**.

**BEFORE → AFTER summary:** BEFORE — migration files created but not applied.
AFTER (2026-08-11 attempt) — application, verification SQL, and integration
tests **could not be executed** due to the non-functional development shell
(environment limitation, not a migration defect). No migration file was
modified; no failure cause beyond the environment was identified.


