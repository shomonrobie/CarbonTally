# CarbonTally WS4 — Gate 5 — T5 Implementation Report
**Task T5: API surface — typed `automation` block in the processing job payload**

- **Date:** 4 September 2026
- **Git HEAD (verified):** `1639121` — nothing committed or pushed.
- **Accepted design:** `docs/architecture/CARBONTALLY_WS4_GATE5_DESIGN_READINESS_REPORT.md`
- **Predecessors:** T1 (schema) COMPLETE/ACCEPTED; T2 (attribution facts helper)
  COMPLETE/ACCEPTED; T3 (worker capture) COMPLETE/ACCEPTED; T4 (extraction audit
  event) COMPLETE/ACCEPTED.
- **Gate 4:** PASSED/ACCEPTED — not reopened, not modified. **Gate 5 has NOT
  passed.**

---

## 1. Exact T5 task executed

T5 from the accepted design report's implementation work breakdown (item 5):

> **T5 — API surface.** Add the typed `automation` block to `_job_payload`; update
> module docstring/comments.

Design §6 confirms the change:

> `backend/api/v3_automatic_processing.py` — `_job_payload` adds a typed
> `automation` block (`provider`, `model`, `model_version`) beside the existing
> `ai_extraction`, so evidence/UI consumers can read the durable contract.

Executed exactly (in `backend/api/v3_automatic_processing.py` only):

1. `_job_payload` now returns a typed `automation` block reading the durable
   write-once columns off the domain object (mapped by T3 from
   `document_processing_queue`):

   ```python
   "automation": {
       "provider": job.automation_provider,
       "model": job.automation_model,
       "model_version": job.automation_model_version,
   },
   ```

   It sits beside the existing `ai_extraction` (metadata) surface. No new route,
   no schema change, no behavior change to list/detail/confirm/retry/review.
2. Added an inline comment documenting the block: NULL values = deterministic-
   only/legacy results; non-NULL = an AI pass contributed to the persisted
   extraction (write-once, never overwritten by human processing); machine
   evidence only — never a human/PE/role identity or authorization signal.
3. Updated the module docstring with a short Machine-provenance paragraph
   describing the typed block (task T5 as specified).

Machine-provenance rules maintained: deterministic runs remain NULL in the API
payload, failed AI attempts never appear as contributing automation, no secrets
are exposed, and the block is evidence-only (never an authorization input).

---

## 2. Files changed

| File | Change |
|---|---|
| `backend/api/v3_automatic_processing.py` | **Modified** — typed `automation` block in `_job_payload`; payload comment; module docstring paragraph. |
| `backend/tests/unit/api/test_v3_automatic_processing_payload.py` | **New** — 3 focused payload tests. |
| `docs/architecture/CARBONTALLY_WS4_GATE5_T5_REPORT.md` | **New** — this report. |

No other file changed; nothing committed or staged.

---

## 3. Migrations

**None.** T5 requires no schema change: the `automation_*` columns exist (T1) and
are selected/mapped by the data layer (T3). No migration was created or applied.

---

## 4. Tests executed

Focused verification for T5 only — no Gate-5 acceptance matrix, no DB fixtures:

1. `pytest tests/unit/api/test_v3_automatic_processing_payload.py` (3 new
   payload tests).
2. Router-import regression: the new payload test plus the existing lightweight
   `tests/unit/api/test_v3_processing_workflow.py` (14 tests total) — confirms
   the modified module imports cleanly and existing V3 processing surface tests
   still pass.
3. `py_compile` of the changed module and the new test file.

---

## 5. Results

| Test run | Result |
|---|---|
| `tests/unit/api/test_v3_automatic_processing_payload.py` | **3 passed** (exit 0) |
| Payload + processing-workflow regression (2 files, 14 tests) | **14 passed** (exit 0) |
| `py_compile` of changed modules | PASS (exit 0) |

New T5 assertions green:
- A job with `automation_provider="openai"`, `automation_model="gpt-test"`,
  `model_version=None` yields `payload["automation"] == {provider: "openai",
  model: "gpt-test", model_version: None}`, with the existing `ai_extraction`
  key still present.
- A deterministic/legacy job (all three fields NULL) yields an all-NULL
  `automation` block.
- A truthfully-known model version is carried through
  (`provider="anthropic"`, `model="claude-test"`,
  `model_version="2026-09-05"`).

---

## 6. Data-integrity impact

**None.** T5 only changes the API serialization of already-persisted job fields;
no data, schema, or state was written or read beyond constructing payloads in
unit tests. No demo/investor rows touched; no fixtures created; no migration
applied.

---

## 7. Security impact

- No new authorization path: the `automation` block is served only through the
  existing org-scoped job list/detail endpoints, which already enforce
  `ensure_processing_org_access` (PE staff remain denied; cross-org access
  impossible).
- The payload exposes non-secret machine-provenance identity strings only — no
  credentials, keys, prompt text, or document content.
- The block is descriptive evidence and is not used as an authorization input;
  `automatic_pipeline` remains a non-user, non-principal machine label.
- No RLS/policy/role/D38-D40 change; Gate-4 human-actor mechanism untouched.

---

## 8. Confirmation: T6–T8 were not executed

Confirmed. This session performed **T5 only**. No write-once DB guard
trigger/tests (T6), no full regression suite (T7), and no Gate-5
fixture/acceptance run (T8) were performed. No migration was created or applied;
nothing was committed or pushed.

---

## 9. Remaining Gate 5 work

Per the accepted design report (§12), after T5 the following remain:

- **T6** — Write-once hardening (DB guard trigger + immutability tests) —
  deferred from T1 by design.
- **T7** — Full regression suite (unit + API positive/negative).
- **T8** — Verification-only Gate-5 fixture run + acceptance evidence.

**Gate 5 is NOT passed** and no acceptance claim is made by this report.

---

## 10. Blockers discovered

**None.** No architecture decision beyond the accepted design was required; T5
introduces no conflict with Gate 4 or the frozen architecture.

---

## FINAL VERDICT

**T5 COMPLETE**

Gate 5 has **not** been executed or passed. Nothing was committed or pushed.

