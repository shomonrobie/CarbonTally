# CarbonTally WS4 — Gate 5 — T4 Implementation Report
**Task T4: automatic-processing extraction audit event (`automatic_processing:extracted`)**

- **Date:** 4 September 2026
- **Git HEAD (verified):** `1639121` — nothing committed or pushed.
- **Accepted design:** `docs/architecture/CARBONTALLY_WS4_GATE5_DESIGN_READINESS_REPORT.md`
  (audit event specified in §5.3).
- **Predecessors:** T1 (schema) COMPLETE/ACCEPTED; T2 (attribution facts helper)
  COMPLETE/ACCEPTED; T3 (worker capture) COMPLETE/ACCEPTED.
- **Gate 4:** PASSED/ACCEPTED — not reopened, not modified. **Gate 5 has NOT
  passed.**

---

## 1. Exact T4 task executed

T4 from the accepted design report's implementation work breakdown (item 4):

> **T4 — Extraction audit event.** Add the 5.3 `AuditLogger` call after the
> persisted extraction advance (best-effort, machine actor).

Design §5.3 event contract (implemented exactly):

```
action          = "automatic_processing:extracted"
entity_type     = "document_processing_queue"
entity_id       = job.id
correlation_id  = job.id
actor           = "automatic_pipeline"      # machine label — NOT a user id
after           = { method, pipeline_version, provider, model, model_version,
                    confidence, attempt_count, source_item_id, ai_status }
```

Executed in **`backend/services/automatic_processing.py`** only:

1. Added a module constant `_AUTOMATION_ACTOR = "automatic_pipeline"` (documented
   as a machine label, never a user/PE/role/D38 identity or authorization
   principal).
2. Added the best-effort helper `_audit_extraction(...)` which calls the existing
   `AuditLogger.log_action(...)` with the exact §5.3 action/entity/actor/after
   contract, guards on `self._audit_logger is None`, and swallows/logs audit
   failures so an audit error can never break the job (mirrors the existing
   engine audit-call convention).
3. `_extract` now fires `await self._audit_extraction(...)` **after** the
   extraction→mapping `advance_stage` persists `extracted_data` (and the T3
   automation block), just before returning `"mapping"`. The `after` payload
   carries the actual persisted `method` stamp, `pipeline_version`, the T3
   contributing-run attribution (provider/model/model_version), `confidence`,
   `attempt_count` (the persisted value), `source_item_id`, and `ai_status`
   (None for deterministic-only; `"ok"`/`"error"` for AI passes).

No audit row is written when no extraction output is persisted (e.g. blocked
pre-persistence paths) and no event is written on idempotent resume that does not
re-run extraction — legacy/past executions are not backfilled (truthfulness rule).

---

## 2. Files changed

| File | Change |
|---|---|
| `backend/services/automatic_processing.py` | **Modified** — `_AUTOMATION_ACTOR` constant, `_audit_extraction` helper, call after the persisted extraction advance in `_extract`. |
| `backend/tests/unit/services/test_automatic_processing.py` | **Modified** — `_FakeAuditLogger` sink, `audit_logger` forwarding in `_make_service`/`_run_with_ai`, new `TestT4ExtractionAudit` class (4 tests). |
| `docs/architecture/CARBONTALLY_WS4_GATE5_T4_REPORT.md` | **New** — this report. |

No other file changed; nothing committed or staged.

---

## 3. Migrations

**None.** T4 requires no schema change: the append-only `audit_trail` already
exists and is service-role/deny-by-default; the `automation_*` columns were added
by the accepted T1 migration. No migration was created or applied.

---

## 4. Tests executed

Focused verification for T4 only — no Gate-5 acceptance matrix, no DB fixtures:

1. `pytest tests/unit/services/test_automatic_processing.py` (16 tests — 4 new
   T4 audit tests plus the existing pipeline/AI suite).
2. Focused regression across related modules:
   `pytest tests/unit/domain/test_automatic_processing.py
   tests/unit/services/test_automatic_extraction_text_layer.py
   tests/unit/services/test_automatic_processing.py
   tests/unit/infra/test_audit_logger.py` (48 tests).
3. `py_compile` of the changed modules.

---

## 5. Results

| Test run | Result |
|---|---|
| `tests/unit/services/test_automatic_processing.py` | **16 passed** in 1.54s (exit 0) |
| Related regression (4 files, 48 tests) | **48 passed** (exit 0) |
| `py_compile` of changed modules | PASS (exit 0) |

New T4 assertions green (via `_FakeAuditLogger`):
- Deterministic-only persisted extraction writes exactly one
  `automatic_processing:extracted` entry with `entity_type =
  "document_processing_queue"`, `entity_id = job.id`, `correlation_id = job.id`,
  `actor = "automatic_pipeline"`, and `after` carrying `method`,
  `pipeline_version`, `confidence = 1.0`, `attempt_count = 1`,
  `source_item_id`, `ai_status = None`, and provider/model/model_version all
  NULL (deterministic truthfulness).
- Contributing-AI extraction writes the same event with
  `after.provider = "openai"`, `after.model = "test-model"`,
  `after.model_version = None`, `after.ai_status = "ok"` (T3 block carried
  through).
- Audit failure (`_FakeAuditLogger(fail=True)`) is swallowed — the job still
  reaches `review` and is not marked failed.
- A blocked pre-persistence AI failure writes **no** `extracted` audit event
  (no persisted output, no fabricated history).

---

## 6. Data-integrity impact

**None.** T4 writes no database data directly (audit rows are produced at
runtime by the existing append-only audit sink when a worker persists an
extraction; unit tests use an in-memory fake). No demo/investor rows were
touched, no fixtures were created, no migration was applied. Existing
`document_processing_queue` rows are unaffected; no backfill of audit rows for
past executions.

---

## 7. Security impact

- The machine actor `"automatic_pipeline"` is an audit **string label** only —
  it is never a user id, never inserted into `performed_by`, D38 assignee
  fields, or any human-assignment vocabulary, and grants no authorization.
- The event is written through the existing service-role append-only
  deny-by-default `audit_trail`; no RLS/policy/endpoint/role change; no new
  authorization path.
- The `after` payload carries only non-secret provenance (method/version/
  provider/model/confidence/timestamps); no credentials, document content, or
  prompt text.
- Gate-4 human-actor mechanism and all D38/D39/D40/RLS/frozen-workflow surfaces
  are untouched. Best-effort semantics guarantee audit failure never alters job
  outcomes.

---

## 8. Confirmation: T5–T8 were not executed

Confirmed. This session performed **T4 only**. No API payload change (T5), no
write-once DB guard trigger/tests (T6), no full regression suite (T7), and no
Gate-5 fixture/acceptance run (T8) were performed. No migration was created or
applied; nothing was committed or pushed.

---

## 9. Remaining Gate 5 work

Per the accepted design report (§12), after T4 the following remain:

- **T5** — API surface (`automation` block in `_job_payload`).
- **T6** — Write-once hardening (DB guard trigger + immutability tests) —
  deferred from T1 by design.
- **T7** — Full regression suite (unit + API positive/negative).
- **T8** — Verification-only Gate-5 fixture run + acceptance evidence.

**Gate 5 is NOT passed** and no acceptance claim is made by this report.

---

## 10. Blockers discovered

**None.** No architecture decision beyond the accepted design was required; T4
introduces no conflict with Gate 4 or the frozen architecture. The audit call
reuses the existing `AuditLogger` (same signature/convention as the engine audit
calls), so no new audit infrastructure was needed.

---

## FINAL VERDICT

**T4 COMPLETE**

Gate 5 has **not** been executed or passed. Nothing was committed or pushed.

