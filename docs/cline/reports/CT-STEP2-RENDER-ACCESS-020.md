# CT-STEP2-RENDER-ACCESS-020 — Read-Only Render Evidence Acquisition & Infrastructure Verification

**Task ID:** `CT-STEP2-RENDER-ACCESS-020` · **Type:** READ-ONLY INFRASTRUCTURE EVIDENCE ACQUISITION
**Date:** 2026-09-18 · **Verifier:** Cline
**Expected deployed release:** `e88b3942724bf0de79d4a36f870cf7e24d2d83e0` (branch `p8-release-reconciled`)
**Verdict:** `INFRASTRUCTURE EVIDENCE REMAINS BLOCKED`

**One-line reason:** no authorised read-only Render evidence channel was made available to (or exists in)
this execution environment — no API key, no authenticated CLI, no exported events/logs/metrics, no
operator-supplied artefact. Per §4 of the task, no evidence was manufactured and no application code was
changed to compensate.

---

## 1. Task identity

Attempt to obtain legitimate **read-only Render evidence** (deployment history, instance lifecycle, logs,
metrics) in order to identify what terminates/recycles the production API/worker process in the window
**2026-09-18 05:00Z–06:40Z**, and — if obtained — analyse it. Nothing was modified, restarted, redeployed,
requeued, unlocked, cancelled or uploaded; the `scan_light_gas.pdf` job was only read.

## 2. Access method — **none available**

| Channel sought | Result |
| --- | --- |
| Render CLI (`render`, `render-cli`) | **absent** |
| `RENDER_*` / `RNDR*` environment variables | **none** (env **names** inspected only; no values sought or printed) |
| Render token/config files (`~/.render*`, `~/.config/render*`, `render.yaml`, `render.yml`) | **none** |
| Render API over HTTP | needs a token that does not exist here; **not** attempted with fabricated credentials |
| Operator-supplied exports (events / logs / metrics / screenshots) | **none provided** |
| Log drain / metrics endpoint in the repo or backend | **none** (`RENDER_` is not referenced anywhere in `backend/`) |
| `/tmp` files that looked promising (`ct_render_access.txt`, `ct_phase01_render.txt`, `i3_render.txt`) | **my own earlier scratch files**, not operator data — inspected and discarded as evidence |

The operator's environment does hold `.env*` files inside the **protected** worktree, but acquiring or using
those credentials is **outside this task's authorisation** (and would be credential discovery). The correct
route is an operator-supplied ephemeral read-only credential — which was not provided.

## 3. Credential handling statement

**No credential was received, requested, discovered, read, printed, written to a file, or committed.** No
token value appears in this report, in Git, in command output or in any artefact. Nothing had to be unset
afterwards because nothing was used. Had a read-only key been supplied, it would have been consumed only as
an ephemeral runtime value for read-only `GET`s, never persisted, and removed afterwards.

## 4. Investigation window

Primary: **2026-09-18 05:00Z–06:45Z** (all timestamps UTC), extended to **06:42:19Z** by this task's final
snapshot and back to 04:59:20Z for earlier tenant progress. September 17 (≈15:31–16:0xZ) is referenced only
as a historical boundary (§21).

## 5. Deployment history — **NOT OBTAINABLE**

No deployment list, IDs, timestamps, commit, branch, trigger (manual vs automatic), status or rollback
history could be read. Whether a deployment occurred inside the window, whether it was automatic, and
whether it overlapped a claim cycle or 503 are therefore all **`UNVERIFIED`**; per the rules, no deployment
causality is inferred from timestamps. **`DEPLOYMENT TRIGGER UNVERIFIED`.**

## 6. Instance lifecycle — **NOT OBTAINABLE**

No instance identifiers, start/stop/restart/replacement/crash events, termination reasons or
health-check-replacement events are available. Instance **count** also cannot be established: it is **not**
derivable from `rndr-id` (explicitly forbidden and not done). **`UNVERIFIED`.**

## 7. Process lifecycle — **NOT OBTAINABLE**

Whether the process ended gracefully, was SIGKILLed, was replaced, or exited for another reason is not
readable. The only product-side discriminator remains: a **graceful** end would (with `daf7270` deployed)
leave an `attempt interrupted: …` record, and a **240 s timeout** would leave a `failed` row — **neither
exists** across ten claims (§9). That is consistent with an end in which no Python handler ran, but it is
**inference, not evidence**, and it does not identify the mechanism.

## 8. Worker lifecycle correlation — **NOT OBTAINABLE**

Worker startup/shutdown lines, heartbeat content and cancellation artefacts are not accessible (no logs;
the heartbeat table is not RLS-readable to the tenant principal). Whether the worker stopped due to
application shutdown, process termination, replacement, deployment or resource termination remains
**`UNVERIFIED`**. Per the rules, **no claim of graceful cancellation** is made — the evidence does not show
the application shutdown path executed.

## 9. `scan_light_gas.pdf` timeline (read-only; the job was never mutated)

Ten claims observed, with the tenant showing **0 failed rows, 0 interruption records, 0 `last_error`
values** throughout:

| # | Claim (`locked_at`) | Interval | State after | Failure? | Interruption? |
| --- | --- | --- | --- | --- | --- |
| 1 | 05:04:17Z | — | extracting, `att=0`, method null | no | no |
| 2 | 05:14:18Z | 10 m 01 s | same | no | no |
| 3 | 05:29:20Z | 15 m 02 s | same | no | no |
| 4 | 05:39:22Z | 10 m 02 s | same | no | no |
| 5 | 05:44:23Z | 5 m 01 s | same | no | no |
| 6 | 05:49:23Z | 5 m 00 s | same | no | no |
| 7 | 06:07:42Z | 18 m 19 s | same | no | no |
| 8 | 06:22:43Z | 15 m 01 s | same | no | no |
| 9 | 06:32:45Z | 10 m 02 s | same | no | no |
| 10 | **06:37:45.731798Z** | **5 m 00 s** | at 06:42:19Z: `processing`/`extracting`, `att=0`, `last_error` NULL, `lock_token` **SET**, method null | no | no |

| Time | Job state | Lock | Worker/process | Render event | API state |
| --- | --- | --- | --- | --- | --- |
| 05:04–06:37 (10 claims) | `extracting`, `att=0`, method null | set on each claim, then persists | **unknown** (no logs) | **not obtainable** | 200s in observed windows; one origin 503 at 06:23:39Z |
| 06:41:35 / 06:41:57 / 06:42:17Z | unchanged (claim 06:37:45Z) | set | unknown | not obtainable | **200 / 200 / 200** (1371 / 471 / 420 ms, no CF challenge) |

## 10. 300-second reclaim analysis (including a correction to `019`)

The application-level chain is **PROVEN**: no handler records anything → the claim survives → the stale
release (300 s) clears `locked_at` → the claim predicate re-selects the row → `attempt_count` stays 0 because
only failure/transition paths increment it.

**Correction to an earlier inference (`019` §9):** the newest interval (06:32:45Z → 06:37:45Z) is **exactly
5 m 00 s** — the claim was re-taken the moment the stale window opened, which indicates a **live, ticking
worker** at that moment rather than process absence. Other intervals (10–18 min) remain unexplained.
Therefore my earlier "worker absent for long stretches" inference is **not reliable and is withdrawn as
evidence**: cadence alone cannot establish process absence. (Recorded openly rather than quietly dropped.)

## 11. API 503 analysis

| UTC | Observation | Classification |
| --- | --- | --- |
| 06:22:23 / 06:22:49 | `/`, `/health`, `/api/v2/health` → 200/200/200 each round (0.28–0.95 s) | healthy windows |
| 06:23:39 | `/api/v2/health` → **503**, **empty body**, **5.46 s**, `cf-mitigated` absent | **origin** failure |
| 06:23:15 / 06:23:39 | 429 + `cf-mitigated: challenge` + 5.6 KB challenge bodies | **Cloudflare** (probe-rate artefact) |
| 06:35:56–06:36:38, 06:41:35–06:42:17 | `/health` → **200 ×6** (420–1371 ms), no challenge | healthy windows |

Correlation of the origin 503: nearest claim was 06:22:43Z (≈56 s earlier) ⇒ overlap with a claim is
**temporal**; overlap with instance lifecycle, deployment, health-check or resource events is **UNKNOWN**
(no Render evidence). Classification: **`TEMPORALLY CORRELATED / UNKNOWN`** — explicitly **not** directly
correlated, and no causation is claimed. Process state at that instant is **unknown**.

## 12. Cloudflare separation (preserved)

`cf-mitigated: challenge` + 429 + 5.6 KB challenge body = **Cloudflare** (caused by this environment's probe
rate; probing stopped on recognition, and no burst was repeated). `503`/`502` with an **empty body**,
`rndr-id` present and `cf-mitigated` **absent** = **origin/Render**. The persistent origin failures are **not**
explained by Cloudflare (`018`/`019` established this; not re-litigated).

## 13. Health-check evidence — **NOT OBTAINABLE**

Which endpoint Render monitors, its timeout/interval and any health-check failures cannot be read. The
endpoint itself was healthy while observed (`/health` 200 in 420–1371 ms, `supabase_connected` and
`pool_connected` true). Whether the platform restarted/replaced an instance for a health-check failure is
**`UNVERIFIED`**, and no health-check configuration was read, changed or proposed.

## 14. Resource / OOM evidence — **NOT OBTAINABLE → `OOM UNVERIFIED`**

No memory/CPU metrics, memory limit, restart count or termination events are available, so **no OOM
determination is possible** and none is inferred. High memory alone would not constitute evidence even if
measured; it was not measurable here.

## 15. OCR correlation — **plausible, unproven**

`scan_light_gas.pdf` is the tenant's only OCR-path document (pypdfium2 render + `rapidocr_onnxruntime`/ONNX
fallback; engine cached in a module global). No Render telemetry (memory spikes, CPU saturation, worker
termination, latency) is available for its extraction attempts, and the job has never completed once, so its
production resource profile is **unmeasured**. Per the rules, **no OOM claim is made from workload type**.

## 16. Database / pool evidence — **NOT OBTAINABLE**

`/health` reported `supabase_connected: true` and `pool_connected: true` in every successful sample. No
connection/pool error logs, `asyncpg` errors, timeouts or database restarts are readable. Whether any
database event overlapped the 503 is **`UNVERIFIED`**. No database credentials were read, no query was
executed, and no pool/`DATABASE_URL` setting was touched.

## 17. Multiple-instance evidence — **NOT OBTAINABLE**

No instance inventory exists locally and instance identity is **not** derivable from `rndr-id` (not used).
Whether one or several instances ran (and whether a replacement instance could explain repeated claims) is
**`UNVERIFIED`**.

## 18. Deployment SHA / runtime identity

* Operator evidence: Render and Vercel deployed at **`e88b394`** (branch `p8-release-reconciled`); repo HEAD
  is now `568a8b0` == origin (reports only since `e88b394`).
* The runtime exposes **no commit/build identifier** (`/` and `/health` return `version: 3.0.0` only), and
  Render's deployment records are unreadable, so the runtime SHA **cannot be independently confirmed** and is
  **not** inferred from `rndr-id`.
* **Statement of record:** *operator deployment evidence confirms `e88b394`, but runtime commit identity is
  not independently exposed.* No redeploy was performed to "correct" anything.

## 19. Causal chain (proven links vs gaps)

```
10 claims, each: attempt ends with NO failure and NO interruption   PROVEN (0 failed rows, 0 interruption records, 0 last_error)
  -> the 240 s timeout never fires a failure                        PROVEN (no failed row >4 min after any claim)
  -> the graceful cancellation handler evidently did not run         INFERENCE (absence of its record is the only witness)
  -> claim survives; stale release (300 s) re-claims the row         PROVEN (source + locked_at timestamps)
  -> attempt_count stays 0                                           PROVEN (source: only failure/transition paths increment)
  -> intermittent origin 503                                        TEMPORAL CORRELATION ONLY (06:23:39Z, ~56 s after a claim)
  -> platform trigger (SIGTERM/SIGKILL/OOM/replacement/deploy/       UNKNOWN - RENDER EVIDENCE UNAVAILABLE
     health check/other)
```

## 20. Evidence matrix

| Question | Evidence | Classification |
| --- | --- | --- |
| What commit was deployed? | Operator evidence (`e88b394`); runtime exposes no build id; Render records unreadable | **PARTIALLY PROVEN** |
| When was it deployed? | No Render deployment timestamps obtainable | **UNVERIFIED** |
| Did an instance restart? | No lifecycle events available | **UNVERIFIED** |
| Did an instance get replaced? | No lifecycle events available | **UNVERIFIED** |
| Did graceful shutdown occur? | Its only witness (interruption record) is absent; logs unavailable | **UNVERIFIED** |
| Was SIGTERM observed? | No logs | **UNVERIFIED** |
| Was SIGKILL observed? | No logs | **UNVERIFIED** |
| Was OOM observed? | No metrics/termination events | **UNVERIFIED** |
| Did health checks fail? | No Render check data; `/health` healthy when sampled | **UNVERIFIED** |
| Did deployment overlap? | No deployment history | **UNVERIFIED** |
| Did worker shutdown occur? | No worker logs/heartbeat access | **UNVERIFIED** |
| Did worker extraction overlap? | Claims 05:04–06:37Z; extraction never completes | **PROVEN** |
| Did database failure overlap? | `/health` connected; no DB telemetry | **UNVERIFIED** |
| Did API 503 overlap? | Origin 503 at 06:23:39Z ≈ 56 s after a claim | **PARTIALLY PROVEN (temporal only)** |
| What happened to the worker? | Not observable | **UNVERIFIED** |
| Why did the claim survive? | No handler ran (hard end) *or* handler skipped — indistinguishable | **PARTIALLY PROVEN** |
| Why did `attempt_count` remain 0? | Only failure/transition paths increment it; neither ran | **PROVEN** (source) |
| What caused the 300 s reclaim cycle? | Stale-lock release + re-claim on the claim path | **PROVEN** (source + timestamps) |

## 21. Historical September 17 boundary (unchanged)

The September 17 production outage remains **`CAUSE UNKNOWN`**. This task obtained **no** infrastructure
evidence relating the current process-cycling behaviour to that outage, so no stronger historical claim is
made: the remediation is not asserted to have caused or resolved it. The evidence that *would* permit such a
claim is exactly what remains unavailable (§22).

## 22. Evidence still required to close this gap

1. **Read-only Render API access** (a scoped read key supplied ephemerally), or
2. operator-exported files for **2026-09-18 05:00–06:45Z**: service **events** (deploys, restarts, instance
   replacement, exit codes), **logs** (`SIGTERM`/`SIGKILL`, `OOM`/`Killed`, tracebacks, application
   startup/shutdown, `automatic-processing worker started/stopped`) and **metrics** (memory, CPU, restart
   count, health-check results); plus
3. confirmation of the **health-check path/timeout**, **instance count** and **deploy trigger**; and
4. ideally a **runtime build/commit identifier** (proposed separately as `CT-STEP2-HEALTH-BUILD-ID-021`,
   **not** started here).

## 23. Production mutation statement

```
uploads: 0            jobs created: 0        jobs requeued: 0     jobs unlocked: 0
jobs retried: 0       jobs cancelled: 0      jobs deleted: 0      documents deleted: 0
database writes: 0    schema changes: 0      configuration changes: 0
service restarts initiated: 0                deployments initiated: 0
code changes: 0       test changes: 0        credential files written: 0
```

Read-only actions: `git` state queries; presence checks for Render tooling/credentials (**names only**, no
values); **6** spaced `GET /health` probes (20 s apart, no burst); **1** authenticated session (authorised
synthetic Owner) used exclusively for one RLS-scoped `SELECT` of that tenant's own queue rows. No
`POST`/`PUT`/`PATCH`/`DELETE` was issued to the application or the database.

## 24. Final verdict

### `INFRASTRUCTURE EVIDENCE REMAINS BLOCKED`

No usable authorised Render evidence could be obtained: no API key, no authenticated CLI, no exported
events/logs/metrics and no operator-supplied artefact reached this environment, and no credential was
requested, discovered or used. Consequently **no Render root cause is declared** (the task's root-cause
standard requires direct infrastructure evidence), the **platform-level trigger remains UNKNOWN**, and the
application-level explanation stands: the 300 s stale-lock reclaim cycle with no failure and no interruption
record — fully explained at application level, unresolved at platform level.

The forensic boundary from `016`–`019` is preserved: the **cancellation-safety defect is confirmed and
remediated** (`daf7270`), the **deployment of `e88b394` is operator-confirmed**, and the **historical Render
process-cycling trigger remains unproven**.



