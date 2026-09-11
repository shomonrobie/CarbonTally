# CarbonTally WS4 — Gate 5 — T6 Implementation Report
**Task T6: database-level write-once guard for the automated machine-provenance block**

- **Date:** 4 September 2026
- **Git HEAD (verified):** `1639121` — nothing committed or pushed.
- **Accepted design:** `docs/architecture/CARBONTALLY_WS4_GATE5_DESIGN_READINESS_REPORT.md`
  (§5.1 Write-once; §6 optional hardening; T6 = DB guard trigger + immutability
  tests).
- **Predecessors:** T1–T5 COMPLETE/ACCEPTED. **Gate 5 has NOT passed.**

---

## 1. Exact T6 task executed

T6 from the accepted design report's implementation work breakdown (item 6):

> **T6 — Write-once hardening (optional but recommended).** DB guard trigger +
> tests proving automation columns are immutable once set.

Design §6 specifies the exact mechanism:

> optional hardening (T6): `BEFORE UPDATE` guard function/trigger
> `dpq_guard_automation_write_once` that rejects changes to non-NULL
> `automation_*` values (applied to main + test DBs, idempotent).

Executed exactly:

1. Created migration `20260905020000_gate5_t6_automation_write_once_guard.sql`
   adding `public.dpq_guard_automation_write_once()` (BEFORE UPDATE, SECURITY
   INVOKER) + `dpq_guard_automation_write_once` trigger on
   `public.document_processing_queue` guarding only `automation_provider`,
   `automation_model`, `automation_model_version`.
2. Applied it to the **main** (`postgres`) and **test** (`carbontally_test`)
   databases per the established raw-apply convention; idempotent re-apply
   verified on real PostgreSQL.
3. Proved the database invariant directly on real PostgreSQL with disposable
   DPQ fixtures (17/17 checks PASS) and restored the exact baseline.

---

## 2. Existing schema / trigger inspection (before the change)

Inspected on the live main database (`public.document_processing_queue`):

- Columns: the three T1 `automation_*` nullable columns present; every existing
  row (36) carried NULL automation (no backfill).
- Existing triggers: only the standard
  `trg_set_updated_at_document_processing_queue` (BEFORE UPDATE) — no conflict.
- NOT NULL columns (no default) required for inserts:
  `organization_id`, `processing_type`, `file_name`, `file_url`.
- RLS enabled (`relrowsecurity = true`), 4 policies — unchanged throughout.
- Migration-file count on disk: **48 before → 49 after**;
  `supabase_migrations.schema_migrations` rows: **46 before → 46 after**
  (raw-apply convention, consistent with T1/Gate-4).
- Convention review: existing guard-style migrations use
  `CREATE OR REPLACE FUNCTION ... LANGUAGE plpgsql` (SECURITY INVOKER) plus
  `DROP TRIGGER IF EXISTS ... ; CREATE TRIGGER ...` for idempotency (e.g.
  `rc2_functions.sql`, `v3m7_vehicles.sql`, `v3m3_customer_factors.sql`). T6
  follows that convention exactly.

---

## 3. Files changed

| File | Change |
|---|---|
| `supabase/migrations/20260905020000_gate5_t6_automation_write_once_guard.sql` | **New** — guard function + trigger (additive, idempotent). |
| `docs/architecture/CARBONTALLY_WS4_GATE5_T6_REPORT.md` | **New** — this report. |

Applied to both `postgres` and `carbontally_test`. No other file changed;
nothing committed or staged.

---

## 4. Migration / function / trigger details

**Migration:** `20260905020000_gate5_t6_automation_write_once_guard.sql`
(wrapped in `BEGIN/COMMIT`).

**Function:** `public.dpq_guard_automation_write_once()` — `RETURNS trigger`,
`LANGUAGE plpgsql`, SECURITY INVOKER (default; runs with the updating role's
rights). For each of the three columns:

```
IF NEW.<col> IS DISTINCT FROM OLD.<col> AND OLD.<col> IS NOT NULL THEN
    RAISE EXCEPTION 'document_processing_queue.<col> is write-once; '
                    'an already-populated value cannot be overwritten'
        USING ERRCODE = 'check_violation';
END IF;
```

**Trigger:**
```
DROP TRIGGER IF EXISTS dpq_guard_automation_write_once ON public.document_processing_queue;
CREATE TRIGGER dpq_guard_automation_write_once
    BEFORE UPDATE ON public.document_processing_queue
    FOR EACH ROW
    EXECUTE FUNCTION public.dpq_guard_automation_write_once();
```

COMMENT ON FUNCTION documents purpose, NULL semantics, and scope. Idempotency:
`CREATE OR REPLACE FUNCTION` + `DROP TRIGGER IF EXISTS`/`CREATE TRIGGER` make
re-application a no-op (verified live).

---

## 5. Exact write-once semantics

Per-column rule, exactly as the accepted design specifies ("rejects changes to
non-NULL `automation_*` values"):

| OLD value | NEW value | Result |
|---|---|---|
| NULL | NULL | Allowed (remains NULL; deterministic/legacy stays truthful) |
| NULL | value | **Allowed — legitimate first population** of a previously NULL field |
| value | same value | Allowed (no-op; idempotent re-write) |
| value | different value | **Rejected** (`check_violation`) — populated value cannot be overwritten |
| value | NULL | **Rejected** — populated value cannot be cleared |

- Each column is guarded independently, so populating a still-NULL field is
  always possible even after other block fields were set.
- Missing metadata is never converted into a fabricated value: NULL stays NULL.
- The guard only inspects the three `automation_*` columns; all other DPQ column
  updates are unaffected.
- Compatible with T3 `COALESCE` persistence (never produces a
  non-NULL → different-value change) and with future Gate-6
  human-after-automation processing (human saves never write these columns).

---

## 6. Tests executed

Focused verification for T6 only — real PostgreSQL (no mocks for the invariant):

1. Pre-change schema/trigger probe of the main DB (baseline: 36 DPQ rows, only
   the `updated_at` trigger, guard absent, RLS on with 4 policies).
2. Migration apply to `postgres` + `carbontally_test` (function + trigger
   presence verified on both).
3. Idempotent re-apply on real PostgreSQL (no-op success).
4. Real-PostgreSQL invariant script (`/tmp/t6_verify.py`) against the live main
   database using **two disposable DPQ fixture rows** (referencing an existing
   organisation, terminal `failed` stage so no worker claim is possible),
   covering all seven required behaviours, with full fixture cleanup and exact
   baseline restoration.

---

## 7. Real-PostgreSQL evidence

Ran against the live local PostgreSQL (`DATABASE_URL` → `postgres` main
database). Key observed outcomes:

- Idempotent migration re-apply succeeds; function and trigger present.
- `UPDATE ... SET automation_provider='openai', automation_model='gpt-test'`
  on a NULL row **succeeds** (first population); then populating the still-NULL
  `automation_model_version` **succeeds**.
- Overwrite attempts raise `check_violation` with the exact message
  (`...automation_provider is write-once; an already-populated value cannot be
  overwritten`, and the analogous model/model_version messages); the stored
  values remain unchanged.
- Attempting to clear a populated value to NULL is **rejected**.
- Same-value write is a no-op and **succeeds**.
- T3-style `automation_model = COALESCE(automation_model, 'x')` over a populated
  value keeps the value with **no error**; `COALESCE` over a NULL field
  **populates** it (first population allowed).
- An unrelated DPQ column update (`manual_review_reason`) **succeeds**.
- Both fixture rows deleted; DPQ count returned to baseline 36; all remaining
  rows still carry a NULL automation block (no backfill, existing rows
  untouched).

---

## 8. Results

| Item | Result |
|---|---|
| Migration applied to main + test DBs | PASS (function + trigger on both) |
| Idempotent re-apply (real PG) | PASS |
| NULL → value first population (incl. after other block fields set) | PASS |
| Populated value overwrite rejected + unchanged | PASS (provider / model / model_version) |
| Clear-to-NULL rejected | PASS |
| Same-value no-op write | PASS |
| T3 COALESCE compatibility (populated keep / NULL populate) | PASS |
| Unrelated DPQ update allowed | PASS |
| Gate-4 `performed_by` + `source_item_id` intact | PASS |
| RLS + DPQ policy count unchanged (4) | PASS |
| Fixture cleanup + exact baseline (36 → 36) | PASS |
| **Overall invariant script** | **17 PASS / 0 FAIL** (exit 0) |

---

## 9. Data-integrity impact

- Migration is purely additive + idempotent (function replace + trigger
  drop/create); no existing rows were modified, no backfill was performed.
- Existing 36 DPQ rows remain untouched and all carry a NULL automation block
  (verified after the run).
- Two disposable fixture rows were created and fully deleted; DPQ count
  returned to the exact baseline (36 → 36). No demo/investor data was modified.
- Migration bookkeeping: files on disk **48 → 49**;
  `schema_migrations` rows **46 → 46** (raw-apply convention as used for T1 and
  Gate-4); `carbontally_test` is a schema-only mirror without
  `supabase_migrations` (pre-existing condition).

---

## 10. Security impact

- No RLS/authorization change: DPQ `relrowsecurity` remains true and the policy
  count remains 4 (verified before and after).
- The guard is SECURITY INVOKER and fires only on `document_processing_queue`
  UPDATEs; it protects the machine-provenance block from any future
  over-broad/casual write path without adding a privilege or principal.
- `automatic_pipeline` is unchanged: a non-user, non-PE, non-role machine label;
  nothing in this migration touches D38/D39/D40 or Gate-4 human provenance
  (`calculation_snapshots.performed_by` / `source_item_id` intact — verified).
- No secrets are involved; the guard stores/reads no credential material.

---

## 11. Confirmation: T7/T8 were not executed

Confirmed. This session performed **T6 only**. No full regression suite (T7) and
no Gate-5 fixture/acceptance run (T8) were executed. Nothing was committed or
pushed.

---

## 12. Remaining Gate 5 work

Per the accepted design report (§12), after T6 the following remain:

- **T7** — Full regression suite (unit + API positive/negative).
- **T8** — Verification-only Gate-5 fixture run + acceptance evidence.

**Gate 5 is NOT passed** and no acceptance claim is made by this report.

---

## 13. Blockers discovered

**None.** The exact T6 mechanism (design §6:
`dpq_guard_automation_write_once` BEFORE UPDATE guard rejecting changes to
non-NULL `automation_*` values) was implemented without altering the accepted
Gate 5 design. The guard does not conflict with T3 `COALESCE` persistence,
Gate-4 human provenance, or future Gate-6 human-after-automation semantics
(human saves never write the guarded columns; NULL-first-population remains
allowed).

---

## FINAL VERDICT

**T6 COMPLETE**

Gate 5 has **not** been executed or passed. Nothing was committed or pushed.


