# CarbonTally WS4 — Gate 6 — Workstream W1 Implementation Report
**G6-A: Preserve the Original Automated Extraction Output**

- **Date:** 4 September 2026
- **Authority:** Gate 6 readiness review accepted — **GATE 6 IMPLEMENTATION
  REQUIRED — DESIGN READY**. This workstream addresses gap **G6-A only**
  (readiness report §10 G-A, proposal §12 G6-W1 option (a)).
- **Git HEAD:** `1639121`. **No commit. No push.** G6-B/G6-C/G6-D were **not**
  implemented.

---

## 1. Files changed

| File | Change |
|---|---|
| `supabase/migrations/20260906010000_gate6_w1_automation_extracted_output.sql` | **New** additive migration: write-once `automation_extracted_data jsonb` column + dedicated BEFORE UPDATE guard function/trigger on `document_processing_queue`. |
| `backend/domain/automatic_processing.py` | `AutomaticProcessingJob` gains `automation_extracted_data: Optional[dict] = None` (with semantic comment). |
| `backend/data/document_processing.py` | `_JOB_COLUMNS` + row mapper read the new column; `advance_stage` gains a write-once `automation_extracted_data` parameter (COALESCE first-write-wins SQL). |
| `backend/services/automatic_processing.py` | `_extract` persists `automation_extracted_data=extracted` at the SAME extraction→mapping advance that first persists `extracted_data` (deterministic and AI-contributing runs). The idempotent-resume branch intentionally passes nothing, so the preserved original is never re-copied/overwritten. |
| `backend/tests/unit/services/test_automatic_processing.py` | Fake repo mirrors the write-once field; new `TestGate6W1PreserveAutomatedOutput` class (7 focused tests). |
| `docs/architecture/CARBONTALLY_WS4_GATE6_W1_REPORT.md` | This report. |

## 2. Schema changes

One additive, idempotent migration applied to the **main DB** (`postgres`) and the
**test DB** (`carbontally_test`), each verified with a no-op re-application:

- `ALTER TABLE public.document_processing_queue
   ADD COLUMN IF NOT EXISTS automation_extracted_data jsonb;`
- New function `dpq_guard_automation_extracted_data_write_once()` and new
  BEFORE UPDATE trigger of the same name enforcing write-once semantics for
  this column only:
  - NULL → value: always allowed (legitimate first population);
  - populated → identical value: allowed (no-op, COALESCE compatible);
  - populated → different value **or NULL**: raises `check_violation`
    (overwrite and clear are rejected at the database).
- The accepted Gate-5 trigger `dpq_guard_automation_write_once` and the
  `automation_provider` / `automation_model` / `automation_model_version`
  columns were **not** modified.

## 3. Exact preservation mechanism

The worker’s `_extract` stage passes the machine-produced extraction payload to
the repository `advance_stage(..., automation_extracted_data=extracted)` in the
**same** write that first persists `extracted_data` and the Gate-5 automation
block. The repository writes it with
`automation_extracted_data = COALESCE(automation_extracted_data, $n)`, i.e.
first-write-wins, and the database trigger enforces that a populated value can
never be changed or cleared. Human paths (`sync_item_data`, item saves,
`reenqueue`, `complete_review`) do not reference the column at all, so the
preserved original survives every later human edit of the working
`extracted_data`.

## 4. How original vs current output is distinguished

- **Original automated output** = `document_processing_queue.automation_extracted_data`
  (write-once copy made at first machine extraction; immutable).
- **Current / human-editable output** = `document_processing_queue.extracted_data`
  (unchanged semantics — humans correct this through the existing workflow).
- The two are independent columns on the same job row; `source_item_id` and job
  id retain the existing item correlation. This is a **separation**, not
  prohibition of human correction (humans keep full edit rights over the current
  output).
- Gate-5 provenance remains distinct and truthful: a deterministic-only run has
  `automation_extracted_data` populated (the pipeline produced machine output)
  while `automation_provider/model/version` stay NULL (no AI contributed).
  **Decision (documented per test requirement #9): deterministic-only runs ARE
  eligible for preservation** — the automatic pipeline produced that output, and
  the G6-A purpose is human-after-automation distinguishability regardless of
  how the machine produced the output. This is documented in the domain model,
  the migration header/comment, and the test that asserts it.

## 5. Security / RLS impact

None. No RLS policy was added, removed or modified (verified: DPQ policy count
remains **4** on main and test DBs). The new column is not an authorization
input; no new endpoint/authorization path exists; the new trigger is
`SECURITY INVOKER` like the Gate-5 guard; org/PE/role boundaries are unchanged.

## 6. Test commands and results

- **Focused G6 tests** — `backend/tests/unit/services/test_automatic_processing.py`:
  `23 passed` (includes the 7 new G6-W1 tests).
- **Directly affected existing tests**:
  `pytest tests/unit/services tests/unit/domain/test_automatic_processing.py
  tests/unit/api/test_v3_automatic_processing_jobs.py
  tests/unit/api/test_v3_automatic_processing_payload.py`
  → `74 passed`.
- **Module compile:** `py_compile` of the four modified Python files → OK.
- **Migration:** applied twice (idempotent no-op) to main and `carbontally_test`;
  column/function/trigger present; row counts unchanged (main DPQ = 36, all new
  column NULL); no fixture residue.
- **Real-PostgreSQL write-once verification** (rollback transaction on the main
  DB, no residue): first population persisted; overwrite rejected; clear-to-NULL
  rejected; same-value no-op allowed; COALESCE keeps first value; human-sync
  (extracted_data) leaves preserved intact; customer approval leaves preserved
  intact; unrelated DPQ update allowed; Gate-5 automation block untouched;
  rollback restored the count (36/36). **10/10 PASS.**

## 7. Legacy-data treatment

No fabrication or backfill. All pre-existing DPQ rows (36 on main) keep
`automation_extracted_data = NULL` — a preserved original is written only by a
real future automated extraction executed by the worker. Failed/blocked
extraction attempts and rows predating this column remain NULL truthfully.

## 8. G6-B / G6-C / G6-D not implemented

Confirmed: this workstream changes only G6-A. No job human-gate actor exposure
or audit events (G6-B), no resume-marker invalidation (G6-C), and no
item-level extraction-edit audit (G6-D) were introduced.

## 9. Blockers / architectural concerns

None. The mechanism is the minimum viable, architecture-consistent option from
the accepted readiness proposal (additive write-once column mirroring the
accepted Gate-5 T1/T6 schema + guard pattern). One documented design decision:
deterministic automated runs are eligible for preservation (§4). No competing
provenance system was created; the Gate-5 audit event, automation block,
`automatic_pipeline` actor and write-once trigger are unchanged.

**Status: G6-A IMPLEMENTED & TESTED — awaiting PO review/acceptance.**

