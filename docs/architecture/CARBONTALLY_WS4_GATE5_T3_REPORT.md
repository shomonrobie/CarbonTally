# CarbonTally WS4 — Gate 5 — T3 Implementation Report
**Task T3: capture the write-once automation attribution block in the worker path**

- **Date:** 4 September 2026
- **Git HEAD (verified):** `1639121` — nothing committed or pushed.
- **Accepted design:** `docs/architecture/CARBONTALLY_WS4_GATE5_DESIGN_READINESS_REPORT.md`
- **Predecessors:** T1 (schema columns) COMPLETE/ACCEPTED; T2 (runtime attribution
  facts helper) COMPLETE/ACCEPTED.
- **Gate 4:** PASSED/ACCEPTED — not reopened, not modified. **Gate 5 has NOT
  passed.**

---

## 1. Exact T3 task executed

T3 from the accepted design report's implementation work breakdown (item 3):

> **T3 — Capture in the worker path.** Extend
> `services/automatic_processing.py` (`_extract`/`_run_ai_candidate`) and
> `data/document_processing.advance_stage` to persist the write-once block on the
> extraction->mapping advance; include the attempted model id in AI-failure
> envelopes.

Executed exactly (no reinterpretation, combination, or expansion):

1. **`backend/domain/automatic_processing.py`** — `AutomaticProcessingJob` gains
   three nullable fields mirroring the T1 schema columns: `automation_provider`,
   `automation_model`, `automation_model_version` (all `Optional[str] = None`).
2. **`backend/data/document_processing.py`** —
   - `_JOB_COLUMNS` now selects `automation_provider`, `automation_model`,
     `automation_model_version`; `_row_to_job` maps them onto the domain object.
   - `advance_stage` accepts the three optional attribution values and persists
     them with **write-once COALESCE semantics** (`COALESCE(<col>, $n)`: a NULL
     column is filled on the first write; a non-NULL value is never overwritten).
3. **`backend/services/automatic_processing.py`** —
   - `_extract`: on the extraction->mapping advance, when the AI pass
     **contributed** (`ai_meta.status == "ok"`), the block is populated from the
     accepted T2 helper `configured_ai_attribution()` and passed as
     `automation_provider/model/model_version`. Deterministic-only outputs and
     failed-AI attempts leave the block NULL (truthful: no contribution).
   - `_run_ai_candidate`: every AI-failure envelope (text-layer failure, engine
     exception, non-ok candidate) now records the **attempted model id** (the
     engine's configured `llm_client.model`) instead of `None` — closing design
     gap G5. Success-path model also falls back to the attempted model if the
     candidate omits it.
4. No API, audit, migration, RLS, UI, D38/D39/D40, or workflow change (those
   belong to T4–T8).

Design semantics preserved: contributing-vs-attempted truthfulness, NULL for
deterministic/unknown/legacy, no fabrication, no secrets, `automatic_pipeline`
not introduced (T4), human-save paths never touch the block.

---

## 2. Files changed

| File | Change |
|---|---|
| `backend/domain/automatic_processing.py` | **Modified** — three optional automation fields on `AutomaticProcessingJob`. |
| `backend/data/document_processing.py` | **Modified** — `_JOB_COLUMNS`, `_row_to_job`, `advance_stage` (params + write-once COALESCE SQL). |
| `backend/services/automatic_processing.py` | **Modified** — import T2 helper; attribution capture in `_extract`; attempted-model truthfulness in `_run_ai_candidate` failure envelopes. |
| `backend/tests/unit/services/test_automatic_processing.py` | **Modified** — env-neutralisation fixture, fake-repo write-once mirror, fake-engine `llm_client`, `_full_deterministic` helper, three new T3 tests. |
| `docs/architecture/CARBONTALLY_WS4_GATE5_T3_REPORT.md` | **New** — this report. |

`backend/infra/ai_runtime.py` (T2, untracked in the git snapshot) is imported but
was **not** modified in T3. Nothing was committed or staged.

---

## 3. Migrations

**None.** T3 required no schema change: the `automation_*` columns were added and
applied by the accepted T1 migration. No migration was created or applied in this
task; no database rows were touched.

---

## 4. Tests executed

Focused verification for T3 only — no Gate-5 acceptance matrix, no DB fixtures,
no demo-data mutation:

1. `pytest tests/unit/services/test_automatic_processing.py` (12 tests — 3 new
   T3 tests plus the existing pipeline/AI suite).
2. Focused regression across every module referencing the changed code:
   `pytest tests/unit/domain/test_automatic_processing.py
   tests/unit/services/test_automatic_extraction_text_layer.py
   tests/unit/services/test_automatic_processing.py` (31 tests).
3. `py_compile` of all changed modules.

---

## 5. Results

| Test run | Result |
|---|---|
| `tests/unit/services/test_automatic_processing.py` | **12 passed** in 1.75s (exit 0) |
| Domain + services regression (3 files, 31 tests) | **31 passed** (exit 0) |
| `py_compile` of changed modules | PASS (exit 0) |

New T3 assertions green:
- AI-merge (contributing) -> stored job + extraction advance carry
  `automation_provider="openai"`, `automation_model="test-model"`,
  `automation_model_version=None` (T2 helper values, write-once); a later
  advance with different values **cannot overwrite** the persisted block.
- Deterministic-only run -> automation block stays **NULL** even with a provider
  configured (no AI engine / no AI contribution -> no fabrication).
- Failed-AI attempt (deterministic proceeded) -> durable
  `metadata->'ai_extraction'` records `status:"error"` **with the attempted
  model id** (`"test-model"`), while the automation block stays **NULL**
  (attempted != contributing).

---

## 6. Data-integrity impact

**None.** T3 changes code paths that write the new columns on future automated
extraction advances; it does not mutate existing data. No demo/investor rows were
touched; no fixtures were created; no database interaction occurred in the tests
(fake repositories). The T1 columns already exist (NULL) on all existing rows and
remain NULL — no backfill was performed.

---

## 7. Security impact

- No new authorization path, no RLS/policy change, no new endpoint, no new
  principal. The machine actor `automatic_pipeline` is **not** introduced by T3
  (T4); nothing here can become a user/PE member/D38 assignee/role.
- No secrets: only provider/model/version identity strings are persisted; the
  attempted-model value comes from the engine's non-secret configured model id.
- Write-once COALESCE means later processing (including human-confirm paths,
  which never supply these columns) cannot rewrite automated provenance.
- Gate-4 human-actor mechanism and all D38/D39/D40/RLS/frozen-workflow surfaces
  are untouched.

---

## 8. Confirmation: T4–T8 were not executed

Confirmed. This session performed **T3 only**. No extraction audit event (T4),
no API payload change (T5), no write-once DB guard trigger/tests (T6), no full
regression suite (T7), and no Gate-5 fixture/acceptance run (T8) were performed.
No migration was created/applied. Nothing was committed or pushed.

---

## 9. Remaining Gate 5 work

Per the accepted design report (§12), after T3 the following remain:

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

**None.** No architecture decision beyond the accepted design was required; T3
introduces no conflict with Gate 4 or the frozen architecture. One test-expectation
clarification was resolved during verification: the accepted design's write-once
mechanism is **per-column COALESCE** ("never overwrites non-NULL values", design
5.1), so the write-once test asserts provider/model immutability (the values a
contributing run actually persists) rather than a block-level all-or-nothing rule.

---

## FINAL VERDICT

**T3 COMPLETE**

Gate 5 has **not** been executed or passed. Nothing was committed or pushed.

