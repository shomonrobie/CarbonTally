# CarbonTally WS4 — Gate 5 — T1 Implementation Report
**Task T1: additive machine-provenance schema migration for `document_processing_queue`**

- **Date:** 4 September 2026
- **Git HEAD (verified):** `1639121` — nothing committed or pushed.
- **Accepted design:** `docs/architecture/CARBONTALLY_WS4_GATE5_DESIGN_READINESS_REPORT.md`
  (verdict **GATE 5 IMPLEMENTATION READY**; task boundary = **T1 ONLY**).
- **Gate 4:** already PASSED/ACCEPTED — not rerun, not modified.

---

## 1. Exact T1 task executed

T1 from the design report's implementation work breakdown (item 1):

> **T1 — Migration.** Additive `automation_provider` / `automation_model` /
> `automation_model_version` columns + comments (+ optional write-once guard
> trigger) on `document_processing_queue`; apply to main and test DBs; add DB
> regression checks.

Executed exactly:

1. Created one additive, idempotent migration
   `supabase/migrations/20260905010000_gate5_t1_automation_provenance.sql` adding
   the three nullable, write-once machine-attribution columns
   (`automation_provider VARCHAR(120)`, `automation_model VARCHAR(240)`,
   `automation_model_version VARCHAR(120)`) to the existing durable job table
   `public.document_processing_queue`, each with a semantic COMMENT. No new
   table, no index, no constraint on existing data, no RLS change, no backfill.
2. Applied the migration to the **main** database (`postgres` via the local
   Supabase `DATABASE_URL`) and the **test** database (`carbontally_test`),
   using the same raw asyncpg apply mechanism used for the accepted Gate-4
   migration (`20260905000000_gate4_actor_provenance.sql`) in this environment.
3. Ran focused **DB regression checks** on both databases (details in §4–§5).
4. Recorded migration counts and data-integrity state before and after (§6).

**Scope decision on the optional guard trigger:** the design assigns the
database-level write-once guard trigger to **T6** ("DB guard trigger + tests
proving automation columns are immutable once set"). To respect the T1/T6
boundary (no partial execution of T2–T8), the trigger was **not** added in T1
and is explicitly documented in the migration header as deferred to T6. No other
T2–T8 work was performed.

---

## 2. Files changed

| File | Change |
|---|---|
| `supabase/migrations/20260905010000_gate5_t1_automation_provenance.sql` | **New** — additive idempotent migration (three columns + comments) |
| `docs/architecture/CARBONTALLY_WS4_GATE5_T1_REPORT.md` | **New** — this report (required deliverable) |

Temporary verification scripts were written under `/tmp/` (`/tmp/g5t1_probe*.py`,
`/tmp/g5t1_apply.py`, `/tmp/g5t1_verify.py` + output files); they are not part
of the repository. **No other repository file was changed.**

---

## 3. Migration(s)

Exactly **one new migration**, applied to both databases:

- File: `20260905010000_gate5_t1_automation_provenance.sql` (sorts immediately
  after the Gate-4 migration in the migration chain).
- Columns added (all `character varying`, nullable, with COMMENTS):
  - `document_processing_queue.automation_provider VARCHAR(120)`
  - `document_processing_queue.automation_model VARCHAR(240)`
  - `document_processing_queue.automation_model_version VARCHAR(120)`
- Semantics recorded in the column comments (truthful provenance): NULL =
  deterministic-only result / no AI contributed / legacy row predating the
  column; write-once (never overwritten by later human processing); never a
  user/PE/role identity or authorization principal.
- **Migration bookkeeping recorded:**
  - Migration files on disk: **47 before → 48 after** (verified).
  - `supabase_migrations.schema_migrations` rows (main DB): **46 before → 46
    after**. This T1 file is applied with the same raw idempotent apply
    convention used for the accepted Gate-4 migration in this environment (the
    file is tracked on disk; no `schema_migrations` row is inserted by the raw
    apply — unchanged convention, no CLI state mutated).
  - `carbontally_test` has **no** `supabase_migrations` relation (pre-existing
    schema-only mirror; verified) — no count is recordable there.
- Re-apply (idempotency) verified on both databases: second execution is a no-op
  and succeeds.

---

## 4. Tests executed

Focused verification appropriate to T1 only — **no Gate-5 acceptance matrix, no
full suite**:

1. Pre-apply baseline probe of both databases (columns, row counts, RLS flag,
   policy count, Gate-4 snapshot columns, migration bookkeeping).
2. Migration apply to main + test DBs (columns + comment lengths verified).
3. DB regression check script (`/tmp/g5t1_verify.py`) against **both**
   databases:
   - idempotent re-apply succeeds;
   - all three `automation_*` columns exist;
   - columns are nullable `VARCHAR` with the design lengths and comments;
   - existing DPQ rows all carry NULL `automation_*` (no backfill);
   - DPQ row count unchanged after re-apply;
   - DPQ RLS enabled unchanged;
   - DPQ policy count unchanged (4);
   - Gate-4 `calculation_snapshots.performed_by` + `source_item_id` intact.

---

## 5. Test results

**DB regression checks: OVERALL PASS on both `postgres` and `carbontally_test`**
(all 9 checks PASS per database; evidence in `/tmp/g5t1_verify_out.txt`):

| Check (both DBs) | Result |
|---|---|
| Idempotent re-apply succeeds | PASS |
| All three `automation_*` columns exist | PASS |
| Nullable VARCHAR with design lengths + comments | PASS |
| Existing DPQ rows all NULL `automation_*` (no backfill) | PASS |
| DPQ row count unchanged after re-apply | PASS |
| DPQ RLS enabled unchanged (`relrowsecurity = true`) | PASS |
| DPQ policy count unchanged (4) | PASS |
| Gate-4 snapshot actor columns intact | PASS |

Applied-column confirmation (post-apply, both DBs): `automation_provider`
VARCHAR(120), `automation_model` VARCHAR(240), `automation_model_version`
VARCHAR(120) — all nullable, all commented.

---

## 6. Data-integrity impact

- **None to existing data.** The migration is purely additive
  (`ADD COLUMN IF NOT EXISTS`, nullable); no UPDATE/DELETE/backfill; no index on
  existing rows; no constraint applied to existing rows.
- Main DB: `document_processing_queue` rows = **36 before and 36 after**; all 36
  carry NULL `automation_*` (legacy rows untouched, no invented metadata).
- Test DB: `document_processing_queue` rows = **0 before and 0 after**.
- Demo/investor data was not modified. No fixture created.
- Migration count before/after recorded (§3).
- Pre-existing unrelated condition noted (not introduced, not fixed): the
  `carbontally_test` mirror is schema-stale relative to main (e.g. its DPQ
  lacks `source_item_id` added by V3M-9, and it has no `supabase_migrations`);
  this predates T1 and is outside T1 scope.

---

## 7. Security impact

- **No new authorization path.** The three columns live on the existing DPQ
  table; no RLS policy added, removed, or changed (verified: RLS enabled and
  policy count = 4 on both databases before and after).
- No FK to `auth.users`, no new principal, no role vocabulary change. The
  machine-actor concept of the design (`automatic_pipeline`) is **not** created
  here and cannot become a user/PE member/D38 assignee/authorization principal
  from this change.
- No secrets stored (columns hold only future provider/model/version labels).
- Gate-4 human-actor mechanism and all D38/D39/D40/RLS architecture untouched.

---

## 8. Confirmation: T2–T8 were not executed

Confirmed. This session performed **T1 only**. No provider-label helper (T2),
no worker/service provenance capture (T3), no extraction audit event (T4), no
API payload change (T5), no write-once guard trigger/tests (T6), no broader
regression suite (T7), and no Gate-5 fixture/acceptance run (T8) were performed.
No code, RLS, API, UI, D38/D39/D40, workflow, or architecture change was made.
Nothing was committed or pushed.

---

## 9. Remaining Gate 5 work

Per the accepted design report (§12), after T1 the following remain:

- **T2** — Runtime attribution facts (`infra/ai_runtime.py` provider-label
  helper).
- **T3** — Capture in the worker path (persist the write-once block on the
  extraction→mapping advance; attempted-model truthfulness in AI-failure
  envelopes).
- **T4** — Extraction audit event (`automatic_processing:extracted`, machine
  actor `automatic_pipeline`).
- **T5** — API surface (`automation` block in `_job_payload`).
- **T6** — Write-once hardening (DB guard trigger + immutability tests) —
  deferred from T1 by design.
- **T7** — Full regression suite (unit + API positive/negative).
- **T8** — Verification-only Gate-5 fixture run + acceptance evidence.

**Gate 5 is NOT passed** and no acceptance claim is made by this report.

---

## 10. Blockers discovered

**None.** No architecture decision beyond the accepted design was required; T1
exposes no conflict with Gate 4 or the frozen architecture.

One scope ambiguity was resolved conservatively and is documented here: the T1
wording lists an "(optional write-once guard trigger)" while the same design
explicitly assigns the guard trigger to T6; the trigger was deferred to T6 to
avoid partially executing a later task. If the PO prefers the trigger inside
T1, it can be added as a small follow-up before T6.

---

## FINAL VERDICT

**T1 COMPLETE**

Gate 5 has **not** been executed or passed. Nothing was committed or pushed.


