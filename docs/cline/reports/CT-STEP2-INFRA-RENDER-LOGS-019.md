# CT-STEP2-INFRA-RENDER-LOGS-019 — Render Process-Cycling & Production 503 Infrastructure Forensics

**Task ID:** `CT-STEP2-INFRA-RENDER-LOGS-019` · **Type:** READ-ONLY INFRASTRUCTURE FORENSICS
**Date:** 2026-09-18 · **Verifier:** Cline
**Expected deployed release:** `e88b3942724bf0de79d4a36f870cf7e24d2d83e0` (branch `p8-release-reconciled`)
**Verdict:** `INFRASTRUCTURE FORENSICS BLOCKED`

**One-line reason:** the required Render events, logs and telemetry are **inaccessible from this environment
in any form** (no CLI, no API token, no dashboard, no log drain, no metrics endpoint), so the infrastructure
evidence gap this task exists to close **cannot be closed here**. Everything obtainable by read-only
application-level means is recorded below, with proven/unproven clearly separated.

---

## 1. Task identity

Attempt to determine, from **read-only Render/infrastructure evidence**, what terminates or recycles the
production process before the application-level cancellation handler can run — i.e. why `scan_light_gas.pdf`
keeps becoming claimable at the ~300 s stale-lock boundary with **no interruption record, no failed row and
`attempt_count = 0`**. No remediation was attempted; nothing was changed, restarted, redeployed, requeued,
unlocked or uploaded.

## 2. Investigation scope

* Render deployment history, instance lifecycle, logs, metrics — **sought, none accessible** (§5).
* Process-lifecycle classification: graceful (SIGTERM → lifespan → `worker.stop()` → cancellation handler)
  vs hard termination (SIGKILL/OOM/abrupt replacement) — **not distinguishable here** (§7).
* Origin 503 correlation, OOM, health-check failure, deployment correlation, DB/pool correlation,
  OCR/resource correlation — each classified with an explicit result.
* Source-level verification of the process/worker model and shutdown path (allowed; no code change).
* Job-timeline extension using read-only RLS reads of the existing synthetic rows.

## 3. Time window

Primary: **05:00Z–06:40Z on 2026-09-18** (all timestamps UTC). Extended back to 04:59:20Z (earlier
claims/progress in the same tenant) and forward to **06:36:39Z** (this task's final snapshot). The
September 17 outage window (~15:31–16:0xZ, 09-17) is referenced only for boundary purposes.

## 4. Release / deployment identity

| Item | Value | Source |
| --- | --- | --- |
| Branch | `p8-release-reconciled` | repo |
| Repo HEAD / origin | **`8537aa8e99bdae946e5799ad58406fb1abaa3457`** (identical), tree clean | `git` |
| Operator-deployed release | **`e88b394`** (Render: deploy succeeded/Live; Vercel: Ready/Production) | operator evidence |
| Ancestry containing fixes | `0d14367` (timeout/`to_thread`), `daf7270` (cancellation safety), `28fd82a` (tests) | repo |
| Runtime build identifier | **none exposed** — `/` and `/health` return `version: 3.0.0` only | live probes |

**Statement of record:** *the deployment SHA is known from operator deployment evidence, but the runtime does
not independently expose a build/commit identifier.* (`rndr-id` is request-level and was **not** used as an
instance identifier anywhere here.) Exposing a build identifier is proposed as a separate task (§21) —
**not** implemented in this task.

## 5. Render deployment evidence — **INACCESSIBLE**

Checked read-only, without bypassing anything:

| Channel | Result |
| --- | --- |
| Render CLI (`render`, `render-cli`) | **absent** |
| `RENDER_*` environment variables | **none** (names inspected only; no values sought or printed) |
| Token/config files (`~/.render*`, `~/.config/render*`, `render.yaml`, `render.yml`) | **none present** |
| Log drain / metrics endpoint in repo or backend | **none** (`RENDER_` is not referenced anywhere in `backend/`) |
| Render API over HTTP | needs a token that does not exist here; not attempted with fabricated credentials |
| Render dashboard | human-only; no credentials exist in this environment |

⇒ **`RENDER INFRASTRUCTURE EVIDENCE UNAVAILABLE`** for deployment history/ids/timestamps, deployment trigger
(auto vs manual), instance start/stop/replacement/crash, health-check failures, container termination reason,
OOM events, memory/CPU/request metrics, worker stdout/stderr and platform events. Consequently
**`DEPLOYMENT TRIGGER UNVERIFIED`** and **stop/restart timing UNVERIFIED**.

## 6. Render instance lifecycle — **INACCESSIBLE**

No instance start/stop/restart/replacement/crash events are obtainable, and **instance count cannot be
determined**: it is not derivable from `rndr-id` (explicitly forbidden and not done) and no local service
inventory exists. Recorded as an unresolved infrastructure gap (§20) — not inferred.

## 7. Process lifecycle — classification impossible from available evidence

```
(A) graceful:  SIGTERM -> lifespan shutdown -> worker.stop() -> task.cancel() -> cancellation handler runs
               ==> would now leave "attempt interrupted: ..." in last_error (daf7270 deployed)

(B) hard:      SIGKILL / OOM / abrupt instance replacement -> no Python handler can run
               ==> claim survives with locked_at set; no record of any kind
```

The only product-side witness distinguishing (A) from (B) is an interruption record (A) versus nothing at all
(B) — and **no interruption record exists** (§9). Therefore **`INFRASTRUCTURE EVIDENCE INSUFFICIENT`** for
this question, and neither (A) nor (B) is selected on inference alone.

**Source-level verification (no code change):** the worker is an `asyncio` task started in lifespan startup
(`main.py:295-307`) and cancelled in shutdown (`main.py:426-438` → `worker.stop()` → `self._task.cancel()`),
so a **graceful** Render shutdown *would* deliver `CancelledError` to the running tick and, with `daf7270`
deployed, the per-job handler would release the claim and record the interruption. No such record has ever
appeared ⇒ *either* no graceful shutdown occurred *or* the handler could not run — not distinguishable here.

## 8. Worker lifecycle / process model (source-verified)

```
API process (Render instance)
└── lifespan startup -> get_automatic_processing_worker().start() -> asyncio task _run_loop
    └── tick (poll 1 s, batch 3): heartbeat -> alerting(bg) -> claim_next(FOR UPDATE SKIP LOCKED)
        └── asyncio.gather(_process_one x n) -> process_job -> extraction (asyncio.to_thread)
lifespan shutdown -> worker.stop() -> task.cancel()
```

* Exactly **one** `claim_next` caller; **no** alternate queue consumer; **no** independent worker service,
  cron or scheduler exists in the repository (verified `016`, unchanged).
* Multiple **instances** would each run their own worker task — possible in principle, **unverifiable here**
  (§6).
* Read-only endpoint check in this window: `GET /health` **200 ×3** at 06:35:56Z (794 ms), 06:36:17Z (799 ms),
  06:36:38Z (460 ms), `cf-mitigated` absent, 373-byte valid body (`supabase_connected`, `pool_connected`
  true) — the process was **serving normally** at that time.

## 9. `scan_light_gas.pdf` timeline (read-only; nothing touched)

| # | Claim (`locked_at`) | Expectation under the deployed fixes | Observed afterwards |
| --- | --- | --- | --- |
| 1 | 05:04:17Z | `daf7270` maybe not yet deployed | no failure, no interruption; re-claimed |
| 2 | 05:14:18Z | — | no failure, no interruption; re-claimed |
| 3 | 05:29:20Z | — | no failure, no interruption; re-claimed |
| 4 | 05:39:22Z | — | no failure, no interruption; re-claimed |
| 5 | 05:44:23Z | — | no failure, no interruption; re-claimed |
| 6 | 05:49:23Z | — | no failure, no interruption; re-claimed |
| 7 | 06:07:42Z | deploy boundary not observable | no failure, no interruption; re-claimed |
| 8 | 06:22:43Z | post-deploy (operator evidence) | no failure, no interruption; re-claimed |
| 9 | **06:32:45.206622Z** | post-deploy | at the final snapshot (06:36:39Z): `processing`/`extracting`, `attempt_count = 0`, `last_error` NULL, `lock_token` **SET**, `ai_extraction_method` NULL |

**Inter-claim intervals:** 10 m 01 s, 15 m 02 s, 10 m 02 s, 5 m 01 s, 5 m 00 s, 18 m 19 s, 15 m 01 s,
**10 m 02 s**. Several exceed the 300 s stale threshold and the ~5-minute cadence a *continuously ticking*
1-second worker would produce.

**Derived observation (inference, not proof):** a live, ticking worker re-claims a stale row within ~1 s of
the 300 s boundary; the observed 10–15 minute gaps suggest **the worker is absent for long stretches between
claims** (a process claims, then stops existing). That is consistent with repeated process
termination/replacement but does **not** identify the terminating mechanism — that requires Render events
(§5).

**Crucially:** with both fixes deployed, *any* graceful end would now leave `attempt interrupted:` and *any*
240 s expiry would leave a `failed` row. Across nine claims the tenant shows **0 interruption records,
0 failed rows, 0 `last_error` values** — both expected witnesses are absent, which is precisely the evidence
gap this task was to close and could not.

## 10. API 503 timeline (origin vs Cloudflare)

| UTC | Observation | Classification |
| --- | --- | --- |
| 06:22:23 / 06:22:49 | `/`, `/health`, `/api/v2/health` → **200 / 200 / 200** each round | healthy windows |
| 06:23:15 | 429 on three endpoints with `cf-mitigated: challenge` | **Cloudflare** (probe-rate artefact) |
| 06:23:39 | `/api/v2/health` → **503**, **empty body**, **5.46 s**, `cf-mitigated` absent | **origin** failure |
| 06:23:39 | `/health`, `/` → 429 challenge; `/openapi.json` → 429 challenge | Cloudflare |
| 06:35:56 / 06:36:17 / 06:36:38 | `/health` → **200 ×3**, 794/799/460 ms, no challenge | healthy window |

**Correlation of the origin 503 (06:23:39Z) with the job timeline:** the nearest claim was 06:22:43Z
(≈56 s earlier). Overlap with a claim: **yes, temporally**; overlap with a *process restart, deployment,
health-check failure or resource event*: **`UNKNOWN`** (no Render evidence). Classification of the 503 vs the
process lifecycle: **TEMPORALLY CORRELATED / UNKNOWN** — **not** **DIRECTLY CORRELATED**, and no causation is
claimed. Cloudflare 429s were **not** counted as origin instability, and no further bursts were issued.

## 11. Cloudflare separation (preserved)

`cf-mitigated: challenge` + 429 + 5.6 KB challenge body = **Cloudflare** (caused by this environment's probe
rate; probing stopped on recognition). `503`/`502` with an **empty body**, `rndr-id` present and
`cf-mitigated` **absent** = **origin/Render**. The two are reported separately throughout; the persistent
origin 503s are **not** explained by Cloudflare (`018` established this and it is not re-litigated).

## 12. Memory / resource evidence — **`OOM UNVERIFIED`**

No memory or CPU metrics, and **no termination events** are obtainable. **No OOM event is documented**, and
none is inferred. Per the task's rule, high memory usage alone would not constitute evidence even if the
metric were available — it is not.

## 13. Health-check evidence — **UNVERIFIED**

* Which endpoint Render monitors, its timeout, and any health-check failures **cannot be read** (no Render
  configuration or events).
* Source-level note (no change made): `/health` performs DB/pool checks (`supabase_connected`,
  `pool_connected`) and returned **200 in 460–799 ms** during this task's healthy windows, so the endpoint
  itself was healthy while observed. Since `0d14367`, extraction no longer runs on the event loop
  (`asyncio.to_thread`), so a **worker-induced event-loop block** is a *less* likely cause of a health-check
  failure than before that fix — reasoning, not evidence, and **not** asserted.
* Whether the platform replaced an instance because of a health-check failure: **UNKNOWN**.

## 14. Database / pool evidence — **UNVERIFIED**

`/health` reported `supabase_connected: true` and `pool_connected: true` in every successful sample
(06:22:23Z, 06:22:49Z, 06:35:56Z–06:36:38Z). No pool-exhaustion counter, connection-error log or database
telemetry is accessible (no DB credentials exist here and none may be discovered; **no database query was
executed**). Whether a DB/pool event preceded any 503 is **UNVERIFIED**. No connection configuration was read
or changed.

## 15. OCR / resource correlation — **plausible, unproven**

`scan_light_gas.pdf` is the tenant's only OCR-exercising document (no text layer; pypdfium2 render +
`rapidocr_onnxruntime`/ONNX in the `onnx_ocr` fallback; engine cached in a module global). Source/tests
document that this path is CPU/memory intensive on first use (model load). However: **no memory metric
exists**, no termination event exists, and the OCR job has never completed once, so its production resource
profile is unmeasured. Per the task's explicit rule, **no OOM claim is made from workload type**:
`OOM UNVERIFIED`.

## 16. Causal chain (proven links vs gaps)

```
claim (9 observed)                                     ✅ PROVEN (production data)
  -> attempt ends with NO failure and NO interruption   ✅ PROVEN (0 failed rows, 0 interruption records)
  -> 240 s timeout does not fire a failure              ✅ PROVEN (no failed row >4 min after any claim)
  -> graceful cancellation handler does not run         ⛔ UNPROVEN cause (no logs)
  -> lock remains set, ages out, row re-claimed         ✅ PROVEN (locked_at + re-claim timestamps)
  -> worker absent for 10-15 min between claims         ~ INFERENCE from cadence (not proof)
  -> repeated process termination/replacement           ⛔ UNPROVEN (no Render lifecycle events)
  -> intermittent origin 503                            ~ TEMPORAL CORRELATION ONLY (06:23:39Z, ~56 s after a claim)
  -> platform trigger (OOM / SIGKILL / deploy /         ⛔ UNKNOWN — REQUIRES RENDER EVIDENCE
     health check / other)
```

## 17. Evidence matrix

| Question | Evidence | Result |
| --- | --- | --- |
| What deployed? | Operator evidence: Render + Vercel at `e88b394`; repo HEAD `8537aa8`; runtime exposes no build id | **PARTIALLY PROVEN** |
| Did an instance restart? | No Render events obtainable; cadence suggests worker absence | **UNVERIFIED** |
| Did graceful shutdown occur? | Would now leave an interruption record; none exists | **UNVERIFIED** |
| Was SIGTERM observed? | No logs | **UNVERIFIED** |
| Was SIGKILL observed? | No logs | **UNVERIFIED** |
| Was OOM observed? | No metrics/termination events | **`OOM UNVERIFIED`** |
| Did health checks fail? | `/health` 200 in all samples; no Render check data | **UNVERIFIED** |
| Did a deployment overlap? | No deployment history accessible | **`DEPLOYMENT TRIGGER UNVERIFIED`** |
| Did worker extraction overlap? | Claims 06:22:43Z / 06:32:45Z; extraction never completes | **PROVEN** |
| Did DB/pool failure overlap? | `/health` reports connected; no DB telemetry | **UNVERIFIED** |
| Did the API 503 overlap? | Origin 503 at 06:23:39Z, ~56 s after a claim | **TEMPORALLY CORRELATED** |
| Why did the lock survive? | No handler ran (hard kill) or handler skipped; indistinguishable | **PARTIALLY PROVEN** |
| Why did `attempt_count` remain 0? | Only failure/transition paths increment it; neither ran | **PROVEN** (source) |
| Why did no interruption record appear? | Graceful path would record; it did not run | **PARTIALLY PROVEN** |
| What explains the 300 s reclaim cycle? | Stale-lock release + re-claim on the claim path | **PROVEN** (source + timestamps) |

## 18. Proven facts

1. Cancellation safety is **implemented and tested** (`daf7270`, tests `28fd82a`, 8/8) — source + automated
   test verified; production runtime unobserved (`018`).
2. Release **`e88b394`** was **operator-deployed** to Render and Vercel; repo HEAD `8537aa8` == origin.
3. The **300 s stale-lock reclaim cycle is fully explained at application level**: no handler records
   anything, the claim survives, stale release + re-claim happens on the claim path, and `attempt_count`
   stays 0 because only failure/transition paths increment it.
4. `scan_light_gas.pdf` has now been claimed **nine** times (05:04:17Z → 06:32:45Z) with **0 failed rows,
   0 interruption records and 0 `last_error` values** across the whole tenant.
5. The runtime exposes **no** build/commit identifier; `rndr-id` was not used as an instance identifier.

## 19. Unproven facts

* The **infrastructure event** that terminates/disappears the process (SIGTERM/SIGKILL vs OOM vs instance
  replacement vs deploy vs health-check failure vs another platform event) — **UNKNOWN**.
* Whether **graceful** or **hard** termination occurred — **not distinguishable** with available evidence.
* Instance **count**, and whether more than one instance/worker ever existed.
* Whether the origin **503** shares a cause with the process cycling (temporal correlation only).
* Whether **OOM** occurred (`OOM UNVERIFIED`), and whether `RapidOCR`/`pypdfium2` resource use is implicated.

## 20. Remaining infrastructure gaps (what would close this)

1. Render **service event history** for 05:00–06:40Z (deploys, restarts, instance replacement, exit codes).
2. Render **logs/stdout-stderr** for the same window (SIGTERM/SIGKILL, `OOM`/`Killed`, tracebacks,
   application startup/shutdown lines, the worker's `automatic-processing worker started/stopped` lines).
3. Render **metrics** (memory, CPU, restart count, health-check results) and the **health-check path/timeout**.
4. Confirmation of **instance count** and whether the deploy trigger was manual or automatic.
5. A **build/commit identifier** exposed by the runtime, so future verification does not depend on operator
   screenshots.

## 21. Proposed follow-up (documented — NOT authorised or started here)

* **`CT-STEP2-RENDER-ACCESS-020`** (infrastructure, PO/operator): provide **read-only** Render access (API key
  scoped to read, or exported events + logs + metrics for the window) so §§5–14 can be answered, then re-run
  this forensic scope. This is the only route to closing the causal gap — **no application change can reveal
  a platform termination that occurs before any handler can run**.
* **`CT-STEP2-HEALTH-BUILD-ID-021`** (small implementation proposal): expose a `build`/`commit` field on
  `/health` (and optionally worker liveness/identity) so deployment identity and worker presence become
  independently verifiable. **Not implemented here** (this task is read-only).
* No new **application** defect is asserted: the observed product behaviour remains fully explained by the
  already-confirmed cancellation gap plus an unproven platform trigger.

## 22. Production mutation statement

```
uploads created: 0        jobs created: 0          jobs requeued: 0
jobs manually unlocked: 0 jobs retried: 0          jobs cancelled manually: 0
jobs deleted: 0           documents deleted: 0     database writes: 0
schema changes: 0         configuration changes: 0 service restarts initiated: 0
deployments initiated by this task: 0   environment variable changes: 0
timeout/stale-lock/retry policy changes: 0   code changes: 0   test changes: 0
```

Read-only actions: `git` state queries; presence checks for Render tooling/credentials (**names only** — no
values sought, printed or stored); **3** spaced `GET /health` probes (20 s apart, no burst); **1**
authenticated session (authorised synthetic Owner) used exclusively for an RLS-scoped `SELECT` of that
tenant's own queue rows. No `POST`/`PUT`/`PATCH`/`DELETE` was issued to the application or the database.

## 23. Final verdict

### `INFRASTRUCTURE FORENSICS BLOCKED`

The Render events, logs and telemetry required to identify the terminating/recycling mechanism are
**inaccessible from this environment in every available form** (no CLI, no `RENDER_*` variable, no token or
config file, no log drain, no metrics endpoint, no dashboard). Therefore:

* **application-level forensics are complete** — the 300 s reclaim cycle, the frozen `attempt_count` and the
  absence of any interruption record are all explained by source + production data;
* **the platform-level cause remains unestablished**, and no SIGTERM/SIGKILL/OOM/health-check/deployment claim
  is made;
* the **`018` boundary is preserved**: the cancellation-safety defect is confirmed and remediated while the
  historical Render process-cycling trigger remains unproven — with no claim that the remediation caused or
  resolved the September 17 outage.

Closing this requires read-only Render access (`CT-STEP2-RENDER-ACCESS-020`).



