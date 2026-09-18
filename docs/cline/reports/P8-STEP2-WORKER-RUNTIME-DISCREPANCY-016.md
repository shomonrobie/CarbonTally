# Phase 8 — Render Worker Runtime Discrepancy Forensics

**Task ID:** `CT-STEP2-WORKER-RUNTIME-DISCREPANCY-016` · **Type:** READ-ONLY FORENSIC INVESTIGATION
**Date:** 2026-09-18 · **Release:** `p8-release-reconciled` @ `6955679` · **Production:** `77084d4`
**Verdict:** `FORENSIC COMPLETE — RUNTIME CAUSE PARTIALLY CONFIRMED`

**Question:** how can a job claimed at 05:04:17Z repeatedly become claimable again without ever reaching
the deployed 240 s timeout or recording a failure?

**Short answer:** the *signature* is explained and locally reproduced — an in-flight extraction that is
**cancelled** (shutdown / process recycle) **bypasses the failure pathway entirely**, leaving the lock
held and `attempt_count = 0`; 300 s later the stale-lock release re-claims it. What *cancels* the
process in production is **not** established (no Render logs) → partially confirmed.

---

## 1. Task identity

Read-only forensics into why the deployed timeout remediation is not observable at runtime. No code,
tests, migrations, database, RLS, configuration, environment variables, queue state or production data
were modified; nothing was restarted, redeployed, requeued, retried, unlocked, uploaded or deleted.

## 2. Git baseline

```
branch : p8-release-reconciled     HEAD : 69556797b1c51639928467a39f540fa5530cc4fb
origin : 69556797b1c51639928467a39f540fa5530cc4fb  (identical)   status: clean
~/carbon_tally (dirty main worktree): NOT touched
```

## 3. Production deployment identity

Render backend **live at `77084d4`** (branch `p8-release-reconciled`), whose ancestry contains the
remediation `0d14367`; Vercel likewise at `77084d4`. Recorded from the operator-supplied dashboard
evidence; **not** inferred from `rndr-id` (still a per-request identifier, not a process/instance id).

## 4. Investigation time window

Primary: **05:00Z–05:45Z on 2026-09-18**; extended for the `scan_light_gas.pdf` claim series to
**05:50Z** (this task's readback). Cross-checked against the historical outage windows of
`ACCEPT-010` (~15:31–16:0xZ on 2026-09-17) and `ACCEPT-011` (~15:30–16:0xZ).

## 5. Render evidence availability

**`RENDER INFRASTRUCTURE EVIDENCE UNAVAILABLE`.** No dashboard, API token, CLI session, log stream, log
drain, metrics endpoint or instance/worker identifier exists in this environment, and none may be
discovered. Therefore **unavailable**: deployment history and IDs, service restart events, container
start/stop, process termination, OOM kills, memory/CPU metrics, health-check failures, application
logs, worker stdout/stderr, startup/shutdown messages, crash traces, build logs and autoscaling events.
The investigation therefore proceeds on **source + application-level production evidence only**.

## 6. Worker architecture (source)

| Question | Answer | Source |
| --- | --- | --- |
| Where does the worker start? | Inside the **API process**, in the app **startup** hook: `await get_automatic_processing_worker().start()` | `backend/main.py:295-307` |
| Separate worker process? | **No** — it is an `asyncio` task created in-process | `workers/automatic_processing.py:83-85` |
| How many workers can run? | **One per process** (module-level singleton `get_automatic_processing_worker()`); one per Render instance | `main.py` startup + worker singleton |
| Can multiple workers claim the same queue? | Yes in principle across instances/replicas — mitigated only by `FOR UPDATE SKIP LOCKED` + soft locks | `data/document_processing.py:216-256` |
| Started once or per process? | **Once per process start** (idempotent guard on an existing task) | `workers/automatic_processing.py:78-90` |
| Exceptions terminate the worker? | No — `_run_loop` catches `Exception` and keeps looping; `CancelledError` is re-raised (loop ends) | `:107-115` |
| Exceptions terminate the API process? | No — the same catch keeps the API alive | `:107-115` |
| What happens on shutdown? | `await get_automatic_processing_worker().stop()` → `self._task.cancel()` → awaits the task, swallowing `CancelledError` | `main.py:426-438`, `:92-103` |

## 7. Process lifecycle (as deployed)

```
process start → lifespan startup → worker.start() → asyncio.create_task(_run_loop)
    loop: heartbeat → alerting(bg) → claim_next(limit=3) → gather(_process_one × n) → sleep 1s
process shutdown / restart / kill:
    graceful  → stop() → task.cancel() → CancelledError in the in-flight tick & gathe-red jobs
    ungraceful→ SIGKILL/OOM → nothing runs at all
```

**No immutable worker/process identifier is persisted anywhere** — the claim stores only a per-tick
`lock_token`, the heartbeat table (if any) is not RLS-readable to this principal (`014`), and
`rndr-id` is per-request. So process identity **cannot be reconstructed from product data**; that gap
is itself a finding (§12 of the report's §22 task list).

## 8. Claim timeline (`scan_light_gas.pdf`)

| Claim (`locked_at`) | Resolved within 240 s? | Failure recorded? | Next claim | Delta |
| --- | --- | --- | --- | --- |
| 05:04:17Z | no | no (`att=0`, `err=null`) | 05:14:18Z | 10 m 1 s |
| 05:14:18Z | no | no | 05:29:20Z | 15 m 2 s |
| 05:29:20Z | no | no | 05:39:22Z | 10 m 2 s |
| 05:39:22Z | no | no | 05:44:23Z | **5 m 1 s** |
| 05:44:23Z | no | no | 05:49:23Z | **5 m 0 s** |
| 05:49:23Z | (open at 05:50:10Z) | no | — | — |

Every delta ≥ 5 minutes = **exactly the 300 s stale-lock window**; the two most recent deltas are
5 m 0 s / 5 m 1 s, i.e. the claim is renewed **as soon as it becomes stale again**. Across all claims:
`attempt_count = 0`, `last_error = null`, `ai_extraction_method = null`, `stage='extracting'`.

## 9. `scan_light_gas.pdf` timeline (interpretation)

```
05:04:17 claim → (attempt ends, records nothing) → lock ages → 05:14:18 stale-release + re-claim
05:14:18 … → 05:29:20 … → 05:39:22 … → 05:44:23 … → 05:49:23 (pattern repeats, ~5–15 min cadence)
```

No cycle ever reaches completion, failure, manual review, or a recorded extraction method.

## 10. API 503 correlation — `TEMPORAL CORRELATION ONLY`

| Observation (015 + this task) | Time |
| --- | --- |
| `/api/v3/processing/status` → 503 | ~05:29Z |
| `/health` → 503 | 05:30:07Z |
| `/health` → 503 | 05:40:34Z |
| Claims of the same job | 05:04, 05:14, 05:29, 05:39, 05:44, 05:49 |
| `/health` 200 (18 consecutive, 0.35–1.95 s) | 05:26:53–05:28:46Z |

The 503s and the re-claims occupy the **same window**, and origin 503s (`rndr-id` present,
`cf-mitigated` absent) are consistent with the process being unavailable or replaced — **but no causal
link is proven**. Labelled **TEMPORAL CORRELATION ONLY**. They are not attributed to the worker, the
remediation or Cloudflare (a single 429 challenge at 05:35Z was caused by this environment's probe rate
and is separate).

## 11. Restart evidence

**Unverified.** No Render events, startup/shutdown logs, deployment timeline or process ids. Product
data cannot show restarts (no persisted worker identity, heartbeat not RLS-readable, no processing-log
rows). What *is* established: **no claim ever records a failure**, which is compatible with the process
being cycled or terminated before 240 s — but does not prove it.

## 12. OOM / resource evidence — `OOM / RESOURCE TERMINATION — UNVERIFIED`

No memory/CPU telemetry, no termination reasons, no OOM events. The affected document is an OCR/PDF
workload (pypdfium2 + RapidOCR) which plausibly consumes significant memory, but **inferring OOM from
workload type would be exactly the unproven inference this task forbids**. Unverified.

## 13. Worker multiplicity

* One worker task per process (singleton guard prevents duplicates **within** a process).
* Across Render instances/replicas, **multiple workers are possible in principle**; coordination relies
  on `FOR UPDATE SKIP LOCKED` (row locks held only for the claim statement) plus the **soft** column lock
  (`locked_at`/`lock_token`) — a soft lock does not prevent a second worker from claiming the row once
  the 300 s window passes.
* The observed sequence (`claim → nothing recorded → stale → re-claim`) is equally consistent with
  **(C/D)** the same or a replacement process losing the attempt and a worker re-claiming after stale
  expiry, and with **(E)** no transaction rollback at all (the claim committed; only the attempt was
  abandoned).
* Distinguishing same-process from new-process claims is **impossible from product data** (no identity).

## 14. Cancellation semantics — **the proven core of this finding**

* `_process_one` is two lines with **no exception handling whatsoever**:
  ```python
  async def _process_one(self, job, token: str) -> None:
      await self._service.process_job(job, token)
  ```
  (`backend/workers/automatic_processing.py:176-177`)
* `_run_stage` converts failures to `mark_failed` only for **`Exception`**
  (`except Exception as exc: … mark_failed(… attempt_count + 1) … return "failed"`) — and
  **`asyncio.CancelledError` is a `BaseException`, not an `Exception`** (Python ≥3.8), so it is *not*
  caught (`services/automatic_processing.py`, `_run_stage`).
* `_run_loop` deliberately **re-raises `CancelledError`** (`:111-112`), ending the loop; and the
  `for … zip` block that would call `mark_failed` after `gather(..., return_exceptions=True)`
  (`:164-175`) **never runs**, because when the *enclosing* task is cancelled `gather` raises
  `CancelledError` instead of returning outcomes.
* `stop()` cancels the loop task (`:97`) — the standard path on **lifespan shutdown** (deploy, restart,
  instance recycle).

**Consequence:** an extraction interrupted by cancellation (or by process death) leaves the row
**claimed, unfailed, with `attempt_count` unchanged and `last_error` null** — precisely the production
signature. **Cancellation bypasses the existing failure pathway.**

## 15. Transaction semantics

| Interruption point | Result |
| --- | --- |
| Before extraction | claim committed; nothing recorded; lock ages to stale → re-claim (attempts 0) |
| **During extraction** | same — the `wait_for`/extraction is cancelled; **no failure update**; lock ages to stale → re-claim |
| After extraction, before persistence | same — persisted stage outputs are the only resume markers |
| Before the failure update | same (the failure update never issues) |
| **After** `mark_failed` commits | job would read `failed` with `attempt_count` + 1 — **never observed in production** |
| Hard kill (SIGKILL/OOM) at any point | identical to "during extraction" — nothing recorded |

The claim is a **committed** `UPDATE` (not an open transaction spanning extraction), so rollback is not
the explanation: **only the attempt is abandoned, never the claim** — the row keeps its lock until the
stale window expires.

## 16. Alternate worker-path analysis — **NONE EXISTS**

* `claim_next` has **exactly one caller** in the whole backend: `workers/automatic_processing.py:153`.
* The worker is started **only** from the lifespan startup hook (`main.py:295-307`); no other module
  starts it, and there is no scheduled job, legacy consumer, background thread or second service that
  claims `document_processing_queue`.
* Other modules reference the queue table for **reads only** (retention, reporting, evidence, manual
  extraction, operational health).
* ⇒ **no production worker path can claim a job without going through the new 240 s timeout
  implementation**. The timeout is on the path; it is the **attempt's termination mode** (cancellation /
  process death) that prevents it from ever firing.

## 17. Production job readback (sparse, read-only, no mutation)

| Time | Rows | `failed` rows | Rows with `last_error` | `scan_light_gas.pdf` |
| --- | --- | --- | --- | --- |
| 05:48:39Z | 8 | **0** | **0** | `processing`/`extracting`, `att=0`, locked **05:44:23.161133Z** |
| 05:50:10Z | 8 | **0** | **0** | `processing`/`extracting`, `att=0`, locked **05:49:23.525815Z** |

Both reads: `ai_extraction_method = null`, `last_error = null`. The other seven rows remain in their
previously recorded states (CSVs `blocked` with per-line `no_match` reasons; PDFs `blocked` on
completeness; `diff_edge_fuel.pdf` `blocked` with validation findings). **No row in the tenant has ever
been `failed`, and none carries a `last_error`** — the failure pathway has never executed in production
for this tenant.

## 18. Local safe reproduction (disposable; no DB, no production)

Performed and **decisive** (`/tmp/repro_cancel.py`: in-process, fake repos, nothing external):

```
patch extract_document -> blocking sleep(10s); EXTRACTION_TIMEOUT_S = 60
start service._run_stage(job, token) as a task -> sleep 0.3s (extraction in flight)
task.cancel()                                   # simulates lifespan shutdown / process recycle
await task -> CancelledError

mark_failed calls         : 0
mark_blocked calls        : 0
advance_stage calls       : 0
=> failure pathway ran?   : False
=> attempts would stay 0  : True
```

This reproduces the **exact production signature**: cancellation of an in-flight extraction produces
**no failure record, no attempt increment and no lock release**. No fix was implemented during it.

## 19. Confirmed causal chain (proven ✅ / unproven ⛔)

```
attempt interrupted while extraction is in flight            ✅ source + local reproduction
  -> CancelledError is NOT caught by `except Exception`      ✅ source (Py3.8+ semantics)
  -> _process_one has no handler at all                      ✅ source (2-line body)
  -> gather raises CancelledError, so the post-gather
     mark_failed block never executes                        ✅ source
  -> NOTHING is recorded (attempt_count 0, last_error null)  ✅ reproduction + production data
  -> the claim's lock is NOT released                        ✅ source (release only in mark_*/release_lock)
  -> locked_at ages out (300 s) and the job is re-claimed    ✅ production (deltas 5–15 min; two at 5 m 0–1 s)
  -> the cycle repeats until a process survives >240 s       ⛔ never observed in production

WHAT ends the attempt early in production?                   ⛔ UNPROVEN
  (restart / instance recycle / OOM / health check / deploy — all plausible, none evidenced)
  -> API 503s co-occur in the same window                    ~ TEMPORAL CORRELATION ONLY
```

## 20. Unconfirmed hypotheses

* **H-restart:** the Render instance/process is restarted or replaced roughly every 5–15 min during the
  observed period, cancelling the in-flight extraction each time.
* **H-OOM:** RapidOCR/pypdfium2 memory use on the scanned document triggers termination — plausible,
  unmeasured.
* **H-multi-instance:** two instances (one an older build) alternately claiming the row. A *different
  code path* is ruled out (§16), but a *different instance running an older image* cannot be excluded
  without deploy history.
* **H-503-link:** the origin 503s and the re-claims share one trigger (instance cycling).

None is asserted.

## 21. Unresolved questions

1. What exactly cycles the production process (deploy, platform recycle, OOM, health check)?
2. Is the service a single instance, and was every instance rebuilt from `77084d4`?
3. Why does no attempt ever survive 240 s (process lifetime shorter than the budget)?
4. Would the timeout fire on a stable process? (Source says yes; runtime has never demonstrated it.)
5. Was the Sep 17 outage caused by the same process-cycling behaviour? (Unknown.)

## 22. Does a new application defect exist? — **YES: a cancellation-safety gap (distinct from F1–F4)**

| Item | Detail |
| --- | --- |
| **Root cause** | Work interrupted by **cancellation or process death** is neither failed nor released: `_process_one` has no handler, `_run_stage` catches only `Exception` (not `CancelledError`), and no `finally` releases the claim. The job is only recovered after the 300 s stale window, with `attempt_count`/`last_error` never reflecting the lost attempt. |
| **Evidence** | Source (`workers/automatic_processing.py:97,111,153,161-177`; `services/automatic_processing.py` `_run_stage`), local reproduction (§18), production data (§8, §17). |
| **Affected code** | `backend/workers/automatic_processing.py` (shutdown/`stop`, `_process_one`, post-`gather` outcome handling), `backend/services/automatic_processing.py` (`_run_stage` exception handling), `backend/data/document_processing.py` (claim release semantics). |
| **Covered by `013`?** | **No.** `0d14367` bounds *execution duration* (timeout); it does **not** address **cancellation/shutdown of an in-flight attempt**. The two are complementary — neither replaces the other. |
| **Why it matters** | It defeats attempt accounting and dead-lettering for **any** interruption (deploy, restart, OOM, scale event) and produces exactly the misleading `attempt_count = 0` / `last_error = null` queue state that made this investigation necessary. |
| **Proposed task** | **`CT-STEP2-WORKER-CANCEL-017` — Cancellation-safe attempt lifecycle**: on `CancelledError`/shutdown, release the claim (or record a bounded failure) so the job is immediately re-claimable, record the interruption in bounded metadata, add a shutdown hook that drains/releases in-flight claims, and add tests for cancel-during-extraction, cancel-before-persist and hard-kill-equivalent paths. (Proposed, **not implemented**.) |
| **Not asserted** | That this defect caused the historical Render outage or the API 503s. |

## 23. Recommended next task

In order:

1. **`CT-STEP2-WORKER-CANCEL-017`** (above) — bounded remediation of the cancellation gap; the
   *proximate* blocker for observable failure accounting.
2. **Infrastructure investigation (PO/Render access)** — retrieve service events and logs for
   **05:00–05:55Z on 2026-09-18** (and the Sep 17 window of `ACCEPT-010`) to identify *what* cycles the
   process (deploy / restart reason / OOM / health-check failure) and whether one or several instances
   served traffic. Without it the trigger chain stays "partially confirmed". Recommended sub-item:
   **expose a build/commit + instance identifier** on `/` or `/health` so future verification does not
   depend on dashboard evidence.
3. Then **production stability verification** (re-run `CT-STEP2-PRODUCTION-DEPLOY-VERIFY-015`), and only
   afterwards consider resuming acceptance.

## 24. Impact on Step 2 acceptance

`CT-STEP2-ACCEPT-007` **remains PAUSED**. This task does not clear the blocker: the runtime cause is only
*partially* confirmed (mechanism proven; production trigger unproven), the failure pathway has never been
observed to execute in production, and the API still returns origin 503s. No acceptance step, requeue,
retry or fix was performed.

## 25. Mutation statement

```
new documents = 0 · re-uploads = 0 · requeues/retries/unlocks = 0 · new jobs = 0 · deletions = 0
data mutations = 0 · storage mutations = 0 · config/env/Render changes = 0 · restarts/redeploys = 0
code/tests/migrations modified = none · credentials printed or committed = none
```

Read-only actions: repository/source reading; `git` state queries; two sparse RLS-scoped queue reads
(§17) via the authorised synthetic Owner session; one disposable in-process local reproduction that
touched **no** database, storage or production resource.

## Final verdict

### `FORENSIC COMPLETE — RUNTIME CAUSE PARTIALLY CONFIRMED`

* **Worker defect status:** the F1–F4 remediation (`0d14367`) is present and correctly bounds *execution
  duration*; a **separate, previously unrecorded defect** is now confirmed — an interrupted
  (cancelled/killed) attempt **bypasses the failure pathway** and strands the claim until stale expiry
  (source + local reproduction + production data).
* **Runtime discrepancy status:** the production signature (`attempt_count = 0`, `last_error = null`,
  repeated ~5–15 min re-claims, no `failed` row) is **fully explained** by that cancellation gap —
  **partially confirmed**, because *what* interrupts the process in production remains **unproven** with
  `RENDER INFRASTRUCTURE EVIDENCE UNAVAILABLE`.
* **Historical Render outage causality:** **still unknown**; no claim is made that the remediation or this
  gap caused it.

**Step 2 gate:** next step = bounded remediation `CT-STEP2-WORKER-CANCEL-017` **plus** the Render
infrastructure investigation; acceptance remains paused.



