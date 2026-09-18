# Phase 8 — Production Cancellation-Safety Verification

**Task ID:** `CT-STEP2-WORKER-CANCEL-VERIFY-018` · **Type:** READ-ONLY PRODUCTION VERIFICATION
**Date:** 2026-09-18 · **Verifier:** Cline
**Expected production release:** `e88b3942724bf0de79d4a36f870cf7e24d2d83e0` (branch `p8-release-reconciled`)
**Verdict:** `PRODUCTION DEPLOYMENT VERIFIED — CANCELLATION RUNTIME UNVERIFIABLE`

---

## 1. Task identity

Read-only verification of the cancellation-safe worker remediation (`daf7270` / tests `28fd82a` / report
`e88b394`) in production. **No implementation, no code/test/migration/config change, no production
mutation, no restart/redeploy.** Four verification levels are kept distinct throughout:
**SOURCE VERIFIED · AUTOMATED TEST VERIFIED · DEPLOYMENT VERIFIED · PRODUCTION RUNTIME VERIFIED.**

## 2. Verification scope

Confirm the deployed release identity (read-only); observe API stability with spaced probes; inspect the
existing synthetic queue (`scan_light_gas.pdf` plus the tenant's seven other rows) **without touching it**;
look for a **naturally occurring** cancellation and cancellation-persistence evidence; then choose between
the permitted verdicts. No cancellation was induced; nothing was requeued, unlocked, retried or cancelled.

## 3. Baseline commit (repo)

```
branch : p8-release-reconciled
HEAD   : e88b3942724bf0de79d4a36f870cf7e24d2d83e0
origin : e88b3942724bf0de79d4a36f870cf7e24d2d83e0   (identical)
status : clean
```
The only permitted repository change is this report.

## 4. Expected deployed commit

Render and Vercel are **reported by the operator as deployed at `e88b394`** on branch
`p8-release-reconciled` (Render: deploy succeeded / Live; Vercel: Ready / Latest / Production, domain
`carbontally.co.uk`).

## 5. Deployment evidence (read-only)

| Evidence | Observation | Interpretation |
| --- | --- | --- |
| Backend `GET /`, `GET /health` | `version: 3.0.0`, `routes_count: 49`, `supabase_connected: true`, `pool_connected: true` | serves, but **exposes no commit/build identifier** |
| Frontend `https://carbontally.co.uk/` | 200; bundles **unchanged**: `/static/js/main.9febc8f0.js`, `/static/css/main.8f1cfa49.css` | consistent with a docs/backend-only release; **not** a marker for `e88b394` |
| Render / Vercel APIs, dashboards, CLI | **not available** here; not bypassed | no independent deployment metadata obtainable |

**Statement of record:** *Operator deployment evidence confirms `e88b394` was deployed; application runtime
does not independently expose its commit SHA.* No SHA was invented from a surface that has none, and
`rndr-id` was not used as an identity.

## 6. API stability observations (spaced probes; no bursts)

| UTC | Endpoint(s) | Status | Time | CF challenge? | Body |
| --- | --- | --- | --- | --- | --- |
| 06:22:23 | `/health`, `/api/v2/health`, `/` | **200 / 200 / 200** | 0.95 / 0.34 / 0.28 s | no | 373 / 78 / 168 B (valid) |
| 06:22:49 | `/health`, `/api/v2/health`, `/` | **200 / 200 / 200** | 0.94 / 0.40 / 0.56 s | no | valid |
| 06:23:15 | `/health`, `/api/v2/health`, `/` | 429 / 429 / 429 | 0.15 / 0.23 / 0.06 s | **yes (`cf-mitigated`)** | 5.6 KB challenge pages |
| 06:23:39 | `/health` | 429 | 0.44 s | yes | challenge page |
| 06:23:39 | `/api/v2/health` | **503** | **5.46 s** | **no** | **empty** → **origin** failure |
| 06:23:39 | `/` | 429 | 0.25 s | yes | challenge page |
| 06:23:39 | `/openapi.json` | 429 (challenge) | — | yes | not parseable |

**Mandatory distinction:**
* **Cloudflare challenges (429, `cf-mitigated` present)** began at 06:23:15Z and are attributable to **this
  environment's probe rate** — explicitly **not** counted as API instability; probing was **stopped
  immediately** once recognised.
* **Origin availability:** the first six probes were **all 200** with fast times (0.28–0.95 s) — production
  serves well in that window — while **one genuine origin 503** (`cf-mitigated` absent, empty body,
  **5.46 s** latency) was recorded at 06:23:39Z ⇒ **intermittent origin unavailability/slowness persists**.
* Origin 5xx count in this task: **1**.

## 7. Existing queue/job snapshot (single sparse read, 06:24:31Z)

`rows = 8` · `failed rows = 0` · `rows with last_error = 0` · **`interruption records = 0`**

| File | status | stage | att | `locked_at` | `lock_token` | method | updated |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `mock_uk_fuel_card_messy.csv` | manual_review | blocked | 1 | null | none | `csv` | 15:30:52Z (Sep 17) |
| `mock_uk_utility_bill.csv` | manual_review | blocked | 1 | null | none | `csv` | 15:30:58Z (Sep 17) |
| `mock_scope3.csv` | manual_review | blocked | 1 | null | none | `csv` | 15:30:55Z (Sep 17) |
| `layout_standard_fuel.pdf` | manual_review | blocked | 0 | null | none | — | 15:30:55Z (Sep 17) |
| `layout_standard_elec.pdf` | manual_review | blocked | 0 | null | none | — | 04:59:20Z |
| `multi_fuel.pdf` | manual_review | blocked | 0 | null | none | — | 04:59:20Z |
| **`scan_light_gas.pdf`** | **processing** | **extracting** | **0** | **06:22:43.880376Z** | **SET** | — | 06:22:43.969Z |
| `diff_edge_fuel.pdf` | manual_review | blocked | 1 | null | none | `pdf_text` | 05:00:37Z |

`lock_token` is reported only as present/absent — **the token value is never exposed.** No mutation was
performed (read-only `GET`/`SELECT` only).

## 8. `scan_light_gas.pdf` read-only evidence

* Job/document identity unchanged from the `ACCEPT-011`/`014` bundles (document `91acc68d-…379e`); **no
  re-upload, no requeue**.
* **Fresh claim:** `locked_at = 06:22:43.880376Z` with `lock_token SET` — claimed and not yet released at
  the snapshot (≈1 m 48 s old, inside the 300 s stale window).
* `attempt_count = 0`, `last_error = null`, `ai_extraction_method = null`, `stage = extracting`,
  `status = processing` — the same pathology as before the remediation was deployed.
* No interruption record and no `failed` row exists for it.

## 9. Historical reclaim comparison (pre- vs post-deployment)

| Claim (`locked_at`) | Phase | `attempt_count` after | failure recorded | interruption recorded |
| --- | --- | --- | --- | --- |
| 05:04:17Z | pre-`0d14367`/`017` | 0 | no | n/a (code absent) |
| 05:14:18Z | pre-`017` | 0 | no | n/a |
| 05:29:20Z | pre-`017` | 0 | no | n/a |
| 05:39:22Z | pre-`017` | 0 | no | n/a |
| 05:44:23Z | pre-`017` | 0 | no | n/a |
| 05:49:23Z | pre-`017` | 0 | no | n/a |
| 06:07:42Z | pre/post-deploy boundary **not observable** | 0 | no | no |
| **06:22:43Z** | post-deploy (per operator evidence) | **0 — claim still held at snapshot** | no | **no** |

**Observation:** the pathological pattern — claim → attempt ends with **no failure record** → stale →
re-claim, with `attempt_count` frozen at 0 — **is still observable** after the reported deployment of
`e88b394`. The expected cancellation-safe sequence (interruption recorded + lock released) has **not** been
observed, because **no cancellation record exists at all** (§10).

**Inference (labelled as inference, not proof):** with the remediation live, a *graceful* shutdown would now
leave an `attempt interrupted: …` record, and a *timeout* would leave a `failed` row. **Neither exists.** The
absence of both is consistent with **hard/ungraceful termination** (SIGKILL/OOM or instance replacement
without lifespan shutdown) — exactly the limitation `017` documented — but this is **not proof**, and the
trigger remains unestablished without Render logs.

## 10. Natural cancellation evidence — `UNOBSERVED`

* **Production cancellation event: UNOBSERVED.**
* No tenant row carries an interruption record (`interruption records = 0`), no row is `failed`, and no row
  has any `last_error`.
* No graceful-shutdown artefact is observable through any available read-only surface (no lifespan logs, no
  RLS-readable heartbeat table, no processing-log rows).
* Per the task's rules this is **not** turned into a PASS and **not** turned into a FAIL.

## 11. Cancellation persistence evidence — `UNVERIFIABLE` (no event to observe)

The `017` contract (`record_interruption_and_release`) could not be observed live because no cancellation
occurred. For the **deployed source** (identical to the tested implementation — commit `daf7270`, clean tree,
ancestry-confirmed):

| Contract element | Source | Automated test |
| --- | --- | --- |
| `locked_at` → NULL | ✅ | ✅ Test 7 |
| `lock_token` → NULL | ✅ same statement | ✅ Test 7 |
| interruption reason recorded | ✅ writes `last_error` = `attempt interrupted: …` | ✅ Tests 1 & 2 |
| `stage`/`status` not advanced | ✅ statement never writes them | ✅ Test 7 |
| no false success persisted | ✅ persistence only in the cancelled coroutine | ✅ Tests 3 + 8 |
| not converted to review/failure | ✅ no `mark_blocked`/`mark_failed` on this path | ✅ Tests 1 & 2 |
| cancellation propagated | ✅ `raise` after the shielded release | ✅ Test 8b |

**Production runtime column: UNVERIFIABLE.**

## 12. Claim-release evidence

Runtime release-by-interruption was not observed (§10). Deploy-level corroboration that the deployed worker
still claims normally: `scan_light_gas.pdf` has `lock_token SET` with a fresh `locked_at` (06:22:43Z). What is
absent is any *release-by-interruption* record.

## 13. Attempt-count evidence

**Option B preserved (as approved):** rows in terminal/manual states show `attempt_count` consistent with
genuine stage transitions (CSVs `1`; `diff_edge_fuel.pdf` `1` via its validation path), and the cycling job
shows `0`. **No attempt was consumed by a cancellation**, because no cancellation was recorded. No counter
was altered by this task.

## 14. Late-thread evidence

No production cancellation occurred, so the late-thread path could not be exercised live. Source + automated
evidence (test commit `28fd82a`) remains the basis: `extract_document` is **pure** (returns a dict, writes
nothing) and persistence happens only in the awaiting coroutine, so a cancelled attempt cannot persist stale
results — proven by `test_cancel_before_persistence_never_persists_stale_results` (orphan thread allowed to
finish; **no** persistence call). **Production runtime column: UNVERIFIABLE.**

## 15. Timeout separation

Both paths remain distinct and present: `EXTRACTION_TIMEOUT_S = 240 s` + `asyncio.wait_for` → ordinary failure
pathway (`mark_failed`, `attempt_count + 1`), versus the cancellation path (release + reason + re-raise). The
`017` suite asserts both (timeout still `failed` with attempt + 1 and the cancellation path **not** used;
ordinary failure unchanged). No 240 s production test was run.

## 16. Worker starvation evidence

* `scan_light_gas.pdf` continues to be the only claimed row — consistent with *legitimate* stale re-claim
  (F3), **not** starvation, since every other row has left the claimable set (`blocked`).
* The previously starved `diff_edge_fuel.pdf` remains processed (`blocked`, `pdf_text`, att 1) — the
  starvation symptom is still absent.
* Claimability remains gated on `locked_at IS NULL` after the stale release (source unchanged; `0d14367`
  intact). No requeue/unlock was performed.

## 17. Render process correlation — none available

No Render deployment events, restart history, instance lifecycle, logs or metrics are accessible here, so
process-cycling correlations remain **unavailable** (not merely unproven).
**`RENDER INFRASTRUCTURE EVIDENCE UNAVAILABLE`** (unchanged since `016`).

## 18. Hard-kill / OOM limitation — preserved (not a defect)

Application code **cannot** run a cancellation handler after a hard kill (SIGKILL/OOM/forced termination). The
300 s stale-lock mechanism remains the recovery path for process disappearance. This is a documented
architectural limitation of `017`, **not** an implementation defect; hard-kill recovery would need a separate
PO decision (process isolation / supervisor).

## 19. Verification matrix

| Verification item | Source | Automated test | Deployment | Production runtime | Verdict |
| --- | --- | --- | --- | --- | --- |
| Cancel during extraction | PASS | **PASS** (Test 1) | PASS (operator) | UNVERIFIABLE (no event) | **UNVERIFIABLE** |
| Claim released | PASS | **PASS** (Tests 1, 2, 7) | PASS | UNVERIFIABLE | **UNVERIFIABLE** |
| Interruption recorded | PASS | **PASS** (Tests 1, 2) | PASS | UNVERIFIABLE (0 records) | **UNVERIFIABLE** |
| Cancellation re-raised | PASS | **PASS** (Test 8b) | PASS | UNVERIFIABLE | **UNVERIFIABLE** |
| No successful persistence | PASS | **PASS** (Tests 3, 8) | PASS | UNVERIFIABLE | **UNVERIFIABLE** |
| No blocked transition | PASS | **PASS** (Tests 1, 2) | PASS | UNVERIFIABLE | **UNVERIFIABLE** |
| Attempt-count semantics (Option B) | PASS | **PASS** | PASS | counters consistent in observed data | **PASS (contract honoured)** |
| Late thread cannot persist | PASS | **PASS** (Tests 3, 8) | PASS | UNVERIFIABLE | **UNVERIFIABLE** |
| 240 s timeout preserved | PASS | **PASS** (Test 4) | PASS | NOT APPLICABLE (not run) | **PASS (source+test)** |
| FIFO preserved | PASS | **PASS** | PASS | claim order consistent | **PASS** |
| SKIP LOCKED preserved | PASS | **PASS** | PASS | single claim held, no double-claim seen | **PASS** |
| Worker starvation behaviour | PASS | **PASS** (Test 7) | PASS | no starvation symptom | **PASS** |
| Production cancellation event | — | — | — | **UNOBSERVED** | **UNVERIFIABLE** |
| `scan_light_gas.pdf` behaviour | — | — | — | pathology persists (`att=0`, `method=null`) | **FAIL (pre-existing pathology continues)** |
| API stability | — | — | PASS | 6/6 200, then CF 429 (my probe rate) + 1 origin 503 | **PARTIAL — origin blip recorded** |

## 20. Production mutation-safety statement

```
uploads created: 0          jobs created: 0            jobs requeued: 0
jobs manually unlocked: 0   jobs retried: 0            jobs cancelled manually: 0
jobs deleted: 0             documents deleted: 0       database writes: 0
schema changes: 0           configuration changes: 0   service restarts initiated: 0
deployments initiated by this task: 0
```

Read-only observation only: `git` state queries; spaced read-only HTTP `GET`s (14 requests, ≥4 s spacing with
one ≥26 s gap, no sustained burst — stopped immediately when Cloudflare challenges appeared); one
authenticated session (authorised synthetic Owner) used **exclusively** for RLS-scoped `SELECT`s of that
tenant's own rows. No `POST`/`PUT`/`PATCH`/`DELETE` was issued to the application or the database.

## 21. Test/source evidence (unchanged from `017`; re-verified as the deployed ancestry)

* Source markers verified in the repo: `EXTRACTION_TIMEOUT_S` (240 s) present, `asyncio.to_thread` present,
  **exactly one** `claim_next` caller, **no** `except BaseException`, and
  `record_interruption_and_release` referenced only from the worker/data layer/tests.
* Focused cancellation suite: **8/8 pass** (`tests/unit/workers/test_worker_cancellation_safety.py`).
* Targeted worker/processing subset: **0 failures**. Full backend unit suite: only the 5 **proven
  pre-existing** unrelated failures (documented in `013` via a pristine `7d45b17` clone).

## 22. Remaining limitations

1. **No natural cancellation occurred post-deployment** → cancellation runtime behaviour unobservable (the
   reason the verdict is not the full-verification one).
2. The deployed backend still **exposes no commit/build identifier**, so runtime SHA confirmation rests on
   operator evidence.
3. **No Render telemetry** (logs/events/metrics) → the process-cycling trigger remains unproven.
4. **Hard kills** cannot be handled in application code (documented, unchanged).
5. The pre-existing pathology on `scan_light_gas.pdf` **continues**; the absence of both a `failed` row and an
   interruption record is consistent with hard/ungraceful terminations — inference, not proof.
6. One intermittent **origin 503** (5.46 s) was observed; production serves well in other windows but is not
   demonstrably consistently stable.
7. Cloudflare challenges (429) at 06:23Z are attributable to this environment's probe rate and are **not**
   treated as instability.

## 23. Final verdict

### `PRODUCTION DEPLOYMENT VERIFIED — CANCELLATION RUNTIME UNVERIFIABLE`

* **Deployment verified:** operator evidence confirms `e88b394` live on Render and Vercel (branch
  `p8-release-reconciled`), with repo HEAD matching; source and automated tests are already verified.
* **Cancellation runtime:** **no natural cancellation event occurred** after deployment (**0** interruption
  records, **0** `failed` rows, **0** `last_error`), so the deployed cancellation-safe behaviour could not be
  observed. Stated as `UNVERIFIABLE` — **not** a PASS and **not** a FAIL.
* **Contract integrity:** the deployed source matches the tested implementation, and every element of the
  approved cancellation contract is covered by source + automated tests.
* **No claim** is made that the cancellation fix resolves the historical Render outage (cause still unknown),
  nor that it caused it. The confirmed statement remains: *the cancellation-safety defect is confirmed and
  remediated while the historical Render process-cycling trigger remains unproven.*

## 24. Suggested follow-up (not started; verification-only task)

`CT-STEP2-INFRA-RENDER-LOGS-019` — PO/infra retrieval of Render service events + logs (05:00–06:30Z on
2026-09-18) to identify what cycles the process, plus exposing a build/commit identifier on `/health` so future
verification no longer depends on operator screenshots. No new application defect is asserted by this task.



