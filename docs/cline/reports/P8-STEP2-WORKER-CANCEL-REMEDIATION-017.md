# Phase 8 — Cancellation-Safe Worker Attempt Lifecycle (remediation)

**Task ID:** `CT-STEP2-WORKER-CANCEL-017` · **Type:** IMPLEMENTATION + VERIFICATION + GIT BANKING
**Date:** 2026-09-18 · **Release:** `p8-release-reconciled`
**Verdict:** `IMPLEMENTED + PARTIALLY VERIFIED + BANKED`
(production runtime verification unavailable — the release is not deployed; see §16)

---

## 1. Task identity

Make the worker claim → extraction → persistence/failure lifecycle **cancellation-safe**, remediating the
defect confirmed by `CT-STEP2-WORKER-RUNTIME-DISCREPANCY-016`. No worker redesign, no new queue consumer,
no retry-policy change, no production mutation.

## 2. Baseline SHA

```
branch : p8-release-reconciled      HEAD at start : 5785b45  (== origin)  tree clean
forensic commit (016): 5785b45      previous worker remediation: 0d14367
protected ~/carbon_tally (dirty main): NOT touched
```

## 3. Forensic evidence from `016` (unchanged, not reinterpreted)

* `_process_one` awaited `process_job(...)` with **no** exception handling (2-line body).
* `_run_stage` caught **`Exception`** only — `asyncio.CancelledError` is a `BaseException` (Py ≥3.8).
* `_run_loop` re-raises cancellation, so the post-`gather` failure handling never executes.
* Local reproduction: cancel during extraction → `mark_failed = 0`, `mark_blocked = 0`,
  `advance_stage = 0`, attempt accounting unchanged.
* Production signature: repeated claims (05:04→05:49Z), `attempt_count = 0`, `last_error = NULL`, no
  `failed` rows; deltas of 5 m 0–1 s = the 300 s stale window.
* Exactly **one** `claim_next` caller; **no** alternate queue consumer.
* The `0d14367` 240 s timeout and `asyncio.to_thread` offload are present and must remain intact.

## 4. Confirmed defect

An in-flight attempt receiving `asyncio.CancelledError` (worker shutdown, process restart/recycle,
termination) **bypassed the failure pathway**: nothing was recorded, the claim was not released, and the
job was recovered only after the 300 s stale window — with `attempt_count`/`last_error` never reflecting
the lost attempt and the interruption invisible in the queue.

## 5. Exact remediation (3 files, +75/−1)

| File | Change |
| --- | --- |
| `backend/workers/automatic_processing.py` | `_process_one` handles cancellation: on `CancelledError` it releases the claim **and** records a bounded truthful interruption reason via `asyncio.shield(...)`, then **re-raises** `CancelledError` |
| `backend/data/document_processing.py` | New narrow method `record_interruption_and_release(job_id, lock_token, reason)` — clears `locked_at`/`lock_token` (owner-token scoped) and writes the reason into the existing `last_error` column; `stage`/`status` untouched; **no schema change required** |
| `backend/services/automatic_processing.py` | `_run_stage` gains an explicit `except asyncio.CancelledError: raise` **ahead of** its `except Exception` handler — propagation intent unambiguous; no broad `BaseException` swallowing |

Recorded reason: `attempt interrupted: worker cancelled or shutting down (extraction attempt not
consumed)` — deliberately distinguishable from an ordinary extraction failure.

## 6. Cancellation lifecycle — before / after

```
BEFORE
  claim -> extraction in flight -> CancelledError
        -> nothing catches BaseException -> no failure, no release
        -> lock ages 300 s -> re-claim -> attempt_count stays 0, last_error NULL   <-- silent loss

AFTER
  claim -> extraction in flight -> CancelledError
        -> _process_one catches CancelledError
        -> shielded record_interruption_and_release: locked_at = NULL, lock_token = NULL,
           last_error = "attempt interrupted: worker cancelled or shutting down ..."
           (stage/status unchanged -> immediately claimable; no attempt consumed)
        -> CancelledError re-raised -> worker/task lifecycle still observes it
```

Guarantees: no false success, no false failure, no false manual-review gate, no silent disappearance, no
indefinitely-held claim, and no state lie (`stage`/`status` are never rewritten by the interruption path).

## 7. Shutdown behaviour

* The worker remains stoppable and is still started/stopped by the existing lifespan hooks (`main.py`
  startup → `start()`, shutdown → `stop()` → `task.cancel()`); **shutdown was not redesigned**.
* When the loop task is cancelled, `gather` cancels its children, so **each in-flight `_process_one` runs
  its own cancellation handler** and releases its own claim before cancellation propagates.
* The release write is `asyncio.shield`-ed so it completes while the task is being cancelled; if the
  release itself fails it is logged and the cancellation is still re-raised.
* Covered by `test_graceful_worker_stop_releases_the_in_flight_claim` (a real `start()`/`stop()` cycle).

## 8. Interaction with the 240 s timeout (both mechanisms coexist)

| Mechanism | Trigger | Outcome |
| --- | --- | --- |
| **Timeout** (`EXTRACTION_TIMEOUT_S = 240`, `asyncio.wait_for`) | extraction exceeds budget | `TimeoutError` → ordinary failure pathway → `mark_failed` + `attempt_count + 1` → dead-letter |
| **Cancellation** (new) | external interruption (shutdown / process end) | claim released + truthful interruption reason → immediately claimable, **no attempt consumed** |

The timeout was **not** replaced or altered, and cancellation is **not** routed into the failure pathway
(that would falsely report a content/processing failure).

## 9. Interaction with `asyncio.to_thread` and late persistence

* CPU-bound extraction remains offloaded via `asyncio.to_thread` — unchanged.
* Documented limitation: **cancelling the awaiting coroutine does not terminate the underlying Python
  worker thread**; forcibly killing threads is not attempted.
* Late persistence is impossible by construction: `extract_document` is **pure** (returns a dict, writes
  nothing) and persistence happens only in the awaiting coroutine, which is cancelled. Proven by
  `test_cancel_before_persistence_never_persists_stale_results`: after cancelling, the orphan thread was
  allowed to finish (1.5 s wait) and **no** `advance_stage`/`mark_*` call occurred.

## 10. Claim-release semantics

* Single new persistence call: `record_interruption_and_release(job_id, lock_token, reason)`.
* SQL (existing columns only — **no schema change required**):
  `UPDATE document_processing_queue SET locked_at = NULL, lock_token = NULL, last_error = $3,
  updated_at = NOW() WHERE id = $1 AND lock_token = $2`.
* **Owner-token scoped**: only the worker owning the claim can clear it, so a stale worker can never clear
  a newer worker's lock.
* `stage`/`status` are **not** written: the job neither succeeded, failed nor reached a human gate.
* Because the lock is cleared immediately, the job does not wait 300 s and **cannot starve later jobs**.
* No new migration, no new table, no new queue consumer, no new retry model.

## 11. Attempt-count semantics (Option B, limitation documented)

**Chosen: Option B — an interruption does NOT consume a processing attempt.** Rationale from the existing
queue contract: `attempt_count` is written only on genuine stage-failure/transition paths (`mark_failed`),
and the interruption was infrastructure/lifecycle-related, not a processing failure. Consuming an attempt
would misattribute shutdown events to the document and could dead-letter a valid job after a deploy.

**Documented limitation:** the existing contract cannot distinguish *operator/process shutdown* from a
*genuine failed attempt* at the attempt-accounting level, so the interruption is recorded in `last_error`
(truthful trace, operator-readable) while `attempt_count` is untouched. Changing that policy would alter
retry/dead-letter semantics broadly and is explicitly **out of scope**.

Invariants (task §6) satisfied: a cancelled attempt **cannot** appear as a successful extraction,
**cannot** disappear without trace (reason recorded), and **cannot** remain indefinitely claimable with a
held lock (cleared immediately).

## 12. Retry / dead-letter implications

* `max_attempts`/dead-letter behaviour is **unchanged** for real failures and timeouts.
* A released (interrupted) job becomes claimable again immediately and is re-attempted by the next tick
  with the *same* attempt count (§11). The pre-existing property that `max_attempts` is not consulted on
  the failure path (documented in `013`/`016`) is **not** changed here.
* No duplicate-claim risk: the release is owner-token scoped and the claim predicate still requires
  `locked_at IS NULL` (the `0d14367` F3 fix remains intact).

## 13. Tests added (8 tests, new file)

`backend/tests/unit/workers/test_worker_cancellation_safety.py` (disposable fixtures only — no database,
no storage, no production resource):

| Test (task requirement) | Guards |
| --- | --- |
| `test_cancel_during_extraction_releases_claim_and_records_truth` (Test 1) | cancellation releases the claim, records an `interrupted` reason, no failure/gate, nothing persisted |
| `test_cancel_immediately_after_claim_does_not_orphan_the_job` (Test 2) | cancel at claim time releases the claim |
| `test_cancel_before_persistence_never_persists_stale_results` (Tests 3 + 8) | no stale extraction result is ever persisted, even after the orphan thread finishes |
| `test_timeout_still_uses_the_ordinary_failure_pathway` (Test 4) | a mocked ~0.2 s timeout still routes to `mark_failed` + `attempt_count + 1`; the cancellation path is **not** used |
| `test_ordinary_extraction_failure_is_unchanged` (Test 5) | ordinary failures unchanged (`ValueError` → `mark_failed`, attempt + 1) |
| `test_graceful_worker_stop_releases_the_in_flight_claim` (Test 6) | a real `start()`/`stop()` cycle releases the in-flight claim; worker remains stoppable |
| `test_interruption_release_clears_the_lock_so_later_jobs_are_claimable` (Test 7) | release SQL clears the lock, is owner-scoped, and does **not** write `stage`/`status` |
| `test_worker_re_raises_cancellation_after_releasing` (Test 8b) | cancellation is **re-raised**, never swallowed |

**No existing test was modified, weakened or deleted.**

## 14. Test commands and results

| Run | Command | Result |
| --- | --- | --- |
| Focused (new) | `pytest tests/unit/workers/test_worker_cancellation_safety.py -v` | **8 passed, 0 failed** (7.5 s) |
| Targeted worker/processing subset | `pytest tests/unit -q -k 'csv or xlsx or ocr or p1 or multi_line or enqueue or lifecycle or preview or extract or worker or claim or cancel or interruption'` | **exit 0 — 0 failures** |
| Full backend unit suite | `pytest tests/unit -q` | exit 1 — **5 failures, all pre-existing** (§15) |

## 15. Regression results

The 5 full-suite failures are the **same pre-existing, unrelated** failures documented in
`CT-STEP2-WORKER-TIMEOUT-013`, where they were **proven pre-existing by an independent pristine clone of
`7d45b17`** (identical failures with no working-tree changes):
`test_p6_1b_membership_workspace_authorization.py` (2) and `test_review_sla_surfaces.py` (3) —
route-registration assertions in the commercial/ops-SLA domains, untouched by this task. No new failure
appeared and no test was altered. Frontend tests were **not** run: the change alters no API contract,
response shape or frontend-visible state (worker-internal only).

## 16. Production verification status — **UNVERIFIED (not deployed)**

* Pushing the branch does **not** deploy; Render deployment is an operator action and **no deploy
  authority/access exists in this environment**. No restart or redeploy was performed.
* Read-only production readback after banking (**06:09:14Z**): `rows=8`, **`failed=0`**, **`with_error=0`**,
  and `scan_light_gas.pdf` still `processing`/`extracting` with `attempt_count = 0`, `last_error = null`,
  `ai_extraction_method = null`, **locked at 06:07:42Z** — the **pre-remediation cycling continues in
  production**, independently confirming the fix is **not yet live** there.
* **The defect is therefore NOT fixed in production**; source/tests verify the remediation only. No
  requeue, unlock, upload or production mutation was performed to test it.

## 17. Git commits

| Commit | Content |
| --- | --- |
| **`daf7270`** | `fix(p8): make the worker attempt lifecycle cancellation-safe` — 3 files, +75/−1 |
| **`28fd82a`** | `test(p8): cover cancellation-safe attempt lifecycle and claim release` — 1 file, +269 |
| report commit | `docs: bank cancellation-safe worker remediation report 017` (this file) |

Static verification before committing: `EXTRACTION_TIMEOUT_S` present (5 refs), `asyncio.to_thread`
present (3 refs), **exactly 1 `claim_next` caller**, **0 `except BaseException`**, the new method
referenced only from the worker, the data layer and the new tests, and no credentials/secrets added.

## 18. Final pushed SHA

`origin/p8-release-reconciled` advanced `5785b45 → 28fd82a` (implementation + tests) and then by the report
commit; the exact final SHA is recorded in the completion summary (§20 of the task output).

## 19. Working-tree status

Clean after every commit; `local HEAD == origin/p8-release-reconciled` verified after each push; the dirty
`main` worktree (`~/carbon_tally`) was not touched.

## 20. Remaining limitations

1. **Production unverified / not deployed** (§16) — the runtime behaviour of this fix has not been observed.
2. **Hard kills (SIGKILL/OOM)** still record nothing: no code can run after an abrupt process death. The
   claim is then recovered only by the 300 s stale mechanism (pre-existing behaviour, documented, unchanged).
3. **Threads are not terminated** on cancellation (platform limitation); the orphan thread may finish its
   CPU work, but its result cannot be persisted (§9).
4. **Attempt accounting cannot distinguish** infrastructure interruption from a genuine failure (§11) —
   recorded as a limitation rather than a broad retry-policy change.
5. The interruption `reason` shares the `last_error` column with genuine error text; it is prefixed with
   `attempt interrupted:` so operators can distinguish it.
6. The underlying trigger of the production process cycling (restart/OOM/deploy) remains **unproven** — no
   Render telemetry (`RENDER INFRASTRUCTURE EVIDENCE UNAVAILABLE`, `016` §5).

## 21. Explicit scope exclusions (unchanged)

The September 17 Render outage, OOM/platform-restart causality, Render configuration, worker redesign, new
queue consumers, broad retry-policy change, automatic retry-on-timeout, `max-attempt` policy, P1 active
rollout, PDF/image extraction fidelity beyond cancellation safety, CSV/XLSX extraction, Consultant routing,
`/home`, `/pe`, `/consultant`, reporting lifecycle, retention, RLS/auth, billing and production data were
**not** touched. Frontend functionality was not modified.

## 22. Final verdict

### `IMPLEMENTED + PARTIALLY VERIFIED + BANKED`

* **Implementation:** complete, bounded and minimal (3 files, +75/−1) — cancellation now releases the claim,
  records a truthful interruption reason, and is re-raised rather than swallowed.
* **Verification:** focused cancellation tests **8/8 pass**; targeted worker/processing regression **0
  failures**; the full suite shows only the 5 **proven pre-existing** unrelated failures.
* **Banked:** implementation, tests and this report are committed and pushed; `HEAD == origin` and the tree
  is clean.
* **Verification boundary (why not fully verified):** production runtime verification is **unavailable** —
  the release is not deployed, and a read-only snapshot at 06:09Z shows the pre-remediation cycling
  continues, so the fix cannot yet be observed in production. Per the task's verdict rules this is
  `PARTIALLY VERIFIED`, not `IMPLEMENTED + VERIFIED + BANKED`.



