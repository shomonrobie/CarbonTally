# Phase 8 — Production API Availability Incident Investigation

**Task ID:** `CT-STEP2-ACCEPT-010` · **Type:** READ-ONLY PRODUCTION INCIDENT FORENSICS
**Incident:** CarbonTally production backend returned HTTP 502/503 across all endpoints
**Window observed:** 2026-09-17 ~15:31–15:45+ UTC (**still unavailable at the final probe**)
**Release:** `p8-release-reconciled` @ `61e7ba2` (lineage `13cf6e5` → `1517588` → `61e7ba2`)
**Final verdict:** `PRODUCTION STILL UNAVAILABLE — ACCEPTANCE BLOCKED`
**Cause:** `UNKNOWN — INSUFFICIENT INFRASTRUCTURE EVIDENCE`

---

## 1. Task identity

Determine **why** the Render backend returned HTTP 503 across all tested endpoints during the
`CT-STEP2-ACCEPT-007` authenticated acceptance, using only read-only evidence available in this
environment. No remediation was attempted. No credential was requested, discovered or used; the
synthetic acceptance credentials are **not** reproduced anywhere in this report.

## 2. Incident summary

The API was healthy at the start of the acceptance run (`/`, `/health`, `/api/v2/health` → 200;
OpenAPI **570 paths**). Eight synthetic documents uploaded successfully (8 × HTTP 201) at
**15:30:50Z**. **32 seconds later** the first failure appeared: an authenticated
`GET /api/v3/documents` returned **502**. Within ~2 minutes `/api/v3/processing/*` returned **503**.
A concurrent **Cloudflare bot challenge** (HTTP 429, `cf-mitigated: challenge`) then affected some
requests from this environment. After the challenge cleared (`cf-mitigated` absent), **all** probed
endpoints still returned **503** — and at the final probe (**15:45:27Z**) the service was
**still unavailable**. The frontend remained **200** throughout.

## 3. Timeline (UTC; local evidence timestamps are +06:00)

| UTC | Event | Evidence | Interpretation |
| --- | --- | --- | --- |
| ~14:39:45 | Commit `13cf6e5` created (release tip) | `git log %cI` | Pre-incident release |
| ~15:05 | Backend healthy: 200s; OpenAPI 570 paths | earlier probes | Baseline healthy |
| 15:23:15 | Commit `1517588` created (**docs only**), pushed immediately | `git log %cI` + push output | Possible deploy trigger (unverified — §8) |
| 15:30:50 | **8 uploads completed, 8 × HTTP 201** | `/tmp/jj2_results.json` mtime | Ingestion healthy |
| **15:31:22** | Authenticated `GET /api/v3/documents` → **502** | `/tmp/jj3_results.json` mtime | **Onset** |
| 15:32:59 | Browser login: session OK, API calls `net::ERR_FAILED` | `/tmp/jj4_results.json` | API unreachable from browser |
| 15:33:28 | `/health` → **503**; `/api/v2/health` → **429 + cf-mitigated: challenge** | `/tmp/kk1_hdr.txt` | Two conditions coexist |
| ~15:35–15:39 | `/health` 503 with **cf-mitigated absent** (spaced probes) | `/tmp/kk2_hdr.txt` | Backend failure persists without CF |
| 15:39:04 | **All** endpoints → **503**, empty body, `rndr-id` present | `/tmp/kk3_hdr.txt` | Render-side unavailability |
| 15:42:00 | Commit `61e7ba2` created (docs only) | `git log %cI` | During the outage |
| **15:44:58** | `/` → **502 after 10.66 s**; others 503 | `/tmp/qq1_now.txt` | Gateway timeout pattern |
| **15:45:27** | `/health` **503**, `/api/v2/health` **503**; frontend **200** | final probe | **Still unavailable** |
| Recovery | **NOT OBSERVED** | — | No recovery by end of task |

## 4. Production deployment identity

| Surface | Value | Evidence |
| --- | --- | --- |
| Frontend | `https://carbontally.co.uk` — JS `main.9febc8f0.js`, CSS `main.8f1cfa49.css` (F-07 scoped rule present) | live bundle fetch |
| Backend (pre-incident) | `carbontally-api.onrender.com` — 200s, OpenAPI **570 paths** (incl. `/api/v3/organizations`, `/api/v3/me/context`) | probes ~15:05Z |
| Backend (incident) | 502/503, empty bodies, `rndr-id` on every response | §6–§7 |
| Infrastructure-as-code | **`render.yaml` / `render.yml` / `Procfile` / `Dockerfile` NOT PRESENT** | repo scan; corroborated by `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md` |

## 5. Frontend state — **HEALTHY**

`carbontally.co.uk` returned **HTTP 200** at every probe during the window and at the final probe
(15:45:27Z). The frontend therefore stayed serviceable while its API did not — which is why the
browser rendered *"CarbonTally sign-in is temporarily unavailable"* rather than failing to load.

## 6. Backend state — **UNAVAILABLE**

| Probe | `/` | `/health` | `/api/v2/health` | `/openapi.json` |
| --- | --- | --- | --- | --- |
| Pre-incident (~15:05Z) | 200 | 200 | 200 | 200 (570 paths) |
| 15:33:28Z | — | 503 | 429 (CF challenge) | — |
| 15:39:04Z | 503 | 503 | 503 | 503 |
| 15:44:58Z | **502** (10.66 s) | 503 | 503 | 503 |
| 15:45:27Z (final) | — | **503** | **503** | — |

All incident responses had **zero-length bodies** — no FastAPI JSON payload and no framework error
page. Latency was short (0.25–1.0 s) except `/` (10.66 s).

## 7. Render evidence (available)

| Observation | Value | Significance |
| --- | --- | --- |
| `rndr-id` present on **every** response, **different per request** | `50dacb6c-587a-49fe`, `e1c618fe-d09b-45f4`, `93cd674c-f015-4a9b`, `64329faa-4d11-4ae2`, `7a54086a-f8ed-4db7`, `90f056f6-f536-416f` | `rndr-id` is a **per-request** Render identifier, **not** an instance id → proves the response came from Render's edge/proxy, and **cannot** detect a restart (§9) |
| `server: cloudflare` on incident responses | header capture | Cloudflare fronts Render; `rndr-id` is passed through |
| `cf-mitigated` **absent** while 503 persisted | `/tmp/kk2_hdr.txt`, `/tmp/kk3_hdr.txt`, final probe | Separates Condition B from Condition A |
| Empty bodies on **all** routes incl. `/` and `/openapi.json` | body length 0 | Consistent with **Render proxy with no healthy backend instance**; an application-level 503 would carry a body and typically vary by route |
| `/` → 502 after 10.66 s | `/tmp/qq1_now.txt` | Gateway-timeout pattern — an instance that did not answer |
| Render dashboard / API / log access | **NOT AVAILABLE** (no token, no CLI session; credential discovery forbidden) | Deploy history, restart reasons, CPU/memory/OOM **unverifiable** |

## 8. Deployment / restart evidence

* `render.yaml` / `render.yml` / `Procfile` / `Dockerfile`: **absent from the repository**.
* The Render **auto-deploy setting and deploy branch are explicitly "NOT VERIFIED"** in
  `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md`, which records this as the
  project's *highest operational risk* because build/start/health configuration exists **only in the
  Render dashboard**.
* Commits during the window were **documentation-only**: `1517588` (15:23:15Z) and `61e7ba2`
  (15:42:00Z) touched only `docs/`. No application code changed, so any deploy they might have
  triggered would have rebuilt an unchanged application.
* **No deployment or restart can be confirmed or excluded** from this environment. A deploy-triggered
  restart is *temporally plausible* (§21, H1) but **unproven**; whether the release branch is even
  wired to auto-deploy is unknown.

## 9. Process lifecycle — **UNVERIFIABLE**

Whether the API process stayed alive, restarted, crashed, was replaced or failed health checks cannot
be determined here: `rndr-id` is per-request (§7), and no Render instance/worker identifiers, events
or metrics are accessible. No console/SSH access exists for a Render service, and no attempt was made
to obtain one.

## 10. Application logs — **NOT AVAILABLE**

No Render log stream, log drain or application log file exists in this environment; no credential was
sought to obtain one. Therefore no `ERROR` / `Traceback` / `asyncpg` / `pool` / `OOM` / `shutdown` /
`startup` evidence could be examined. **`UNVERIFIABLE — REQUIRED APPLICATION LOG TELEMETRY NOT
AVAILABLE`.** Logging was not modified.

## 11. Database / connection evidence — **UNVERIFIABLE**

**`UNVERIFIABLE — REQUIRED DATABASE TELEMETRY NOT AVAILABLE`.** No production database credentials
are present in this environment (verified: no `.env` in the release worktree) and none may be
discovered, so connection counts, pool exhaustion, waiting/failed connections, timeouts, locks and
query durations could not be measured. No diagnostic query was executed and the database was not
touched. (The release's own `/health` contract reports `supabase_connected` / `pool_connected`, but
`/health` itself returned 503 during the incident, so it could not serve as evidence.)

## 12. Worker evidence — **NOT AVAILABLE**

The worker-liveness surface (`/api/v3/health/realtime` and worker heartbeat records) was unreachable
because the entire API was unavailable. Worker start/stop/restart, heartbeat gaps and dead-letter
activity during the window are **UNVERIFIABLE**. No queue row, job or worker state was modified, and
no process was signalled.

## 13. Eight uploaded synthetic document IDs (preserved)

Recorded at 15:30:50Z; **none was retried, re-uploaded, deleted or otherwise mutated** by this task.

| # | Document | Type | Upload | Document ID |
| --- | --- | --- | --- | --- |
| 1 | `mock_uk_fuel_card_messy.csv` | CSV | 201 | `5178640c-39dc-48f5-a1c4-cbb704e2e9ee` |
| 2 | `mock_uk_utility_bill.csv` | CSV | 201 | `a9b07e05-37ca-4a83-aad3-beb5cf7eaeb6` |
| 3 | `mock_scope3.csv` | CSV | 201 | `31b61ab8-b311-4948-8508-420260368454` |
| 4 | `layout_standard_fuel.pdf` | text-layer PDF | 201 | `cbfc3072-5699-4749-98c7-661bca064052` |
| 5 | `layout_standard_elec.pdf` | text-layer PDF | 201 | `585e4345-5919-41cc-a8ef-319d02f41c71` |
| 6 | `multi_fuel.pdf` | multi-line PDF | 201 | `30f761c6-899d-450a-b744-87c389d6f972` |
| 7 | `scan_light_gas.pdf` | scanned (OCR) | 201 | `91acc68d-baa9-4cd2-9558-251cec01379e` |
| 8 | `diff_edge_fuel.pdf` | difficult/edge | 201 | `3e6dd5d9-0fac-472b-b38b-1b8ecc99fada` |

## 14. Queue / job state — **NOT READABLE**

| Document | Upload | Queue | Processing | Current state | Error |
| --- | --- | --- | --- | --- | --- |
| all 8 | **201 (recorded)** | **UNVERIFIABLE** | **UNVERIFIABLE** | **UNVERIFIABLE** (API down) | **UNVERIFIABLE** |

Their queue rows, processing jobs, extraction status and any error strings sit behind the same
unavailable API. The very call intended to read them — authenticated `GET /api/v3/documents` — is
precisely the call that first returned **502** at 15:31:22Z, so the read-back was lost to the
incident rather than to any document-level failure. Re-reading is deferred to the resumed acceptance.

## 15. OCR load correlation

`scan_light_gas.pdf` (verified earlier as **no text layer**, 2 images) was uploaded at 15:30:50Z.
Whether OCR actually began before the outage **cannot be established**: no worker log, queue record
or job state was readable. **Temporal correlation only — causality NOT established.** Uploading an
OCR document is not evidence that OCR caused resource pressure.

## 16. CSV load correlation

`mock_uk_fuel_card_messy.csv`, `mock_uk_utility_bill.csv` and `mock_scope3.csv` were uploaded
(201) at 15:30:50Z; extraction/processing progress is **not readable**. **Temporal correlation only
— causality NOT established.** They were not re-run and not re-uploaded.

## 17. Cloudflare condition (Condition A — separate)

| Aspect | Finding |
| --- | --- |
| Evidence | HTTP **429** with `cf-mitigated: challenge`, `server-timing: chlray`, and `"Just a moment…"` HTML bodies on `/api/v2/health` and `/api/v3/me/context`; browser API calls appeared as CORS failures |
| Onset / clearance | Observed ~15:33Z; **absent** by 15:35–15:39Z and at every later probe (`cf-mitigated` absent) |
| Cause | Triggered by this environment's scripted burst of ~30 rapid requests; a bot-protection response, not a product behaviour |
| Relationship to Condition B | **Independent.** The CF challenge cleared while the 503s persisted — that divergence is the evidence that the Render 503 was **not** caused by Cloudflare. No evidence links the two beyond temporal overlap |

## 18. Health endpoint comparison

| Endpoint | Pre-incident | During | After CF cleared | Final |
| --- | --- | --- | --- | --- |
| `/` | 200 | 503 | 503 → **502 (10.66 s)** | — |
| `/health` | 200 | 503 | 503 | **503** |
| `/api/v2/health` | 200 | 429 (CF) | 503 | **503** |
| `/openapi.json` | 200 (570 paths) | 503 | 503 | — |

**All** backend routes failed, at every path depth, on every method tried. The failure was therefore
**not route-specific** and **not** an application-level validation/authorization response — it was
whole-service unavailability at the edge/proxy layer.

## 19. Recovery timeline

**No recovery was observed.** Immediately after the timeline above, a dedicated recovery check was
run — **12 spaced probes of `/health` and `/api/v2/health` between 15:46:53Z and 15:49:56Z returned
0 × HTTP 200** (11 × 503, 1 × 502). There is therefore no *first successful request*, no recovery
timestamp, and no post-recovery worker/deployment state to report. The service was **not** restarted,
redeployed or otherwise touched to induce recovery.

## 20. Current production state (as at 15:49:56Z)

| Surface | State |
| --- | --- |
| Frontend | **HEALTHY** — `https://carbontally.co.uk` 200 |
| Backend API | **DOWN** — `/health` and `/api/v2/health` 503 (one 502) across 12 spaced probes; empty bodies; no CF challenge engaged |
| OpenAPI | unreachable (503 at 15:39Z; not re-probed afterwards to limit request volume) |
| Worker liveness | unreachable (API down) |
| Unexpected 5xx | the 502/503 responses **are** the incident; no other 5xx class observed |

**⚠️ Production remains unavailable at the close of this investigation (last verified 15:49:56Z).**


## 21. Causality assessment

**Temporal correlations found (NOT causal proof):**

| Correlation | Delta | Strength |
| --- | --- | --- |
| 8 uploads completed (15:30:50Z) → first 502 (15:31:22Z) | **32 seconds** | Tight temporal correlation; plausibility depends on the uploads having triggered automatic processing whose work coincided with a crash — **unverified** |
| Docs-only commit `1517588` (15:23:15Z) pushed → onset (~15:31Z) | ~7–8 minutes | Plausible only if (a) the release branch auto-deploys on push **and** (b) a build/restart began then and failed to become healthy — both **unverified** (`render.yaml` absent; auto-deploy/branch "NOT VERIFIED") |
| Commit `61e7ba2` (15:42:00Z) pushed during the outage | — | No correlating change in status after it (still 503) |

**Causality is NOT established.** Two hypotheses remain open and untested:

* **H1 — deploy/restart:** an auto-deploy triggered by a documentation-only push restarted the
  service, and the new instance did not reach healthy state.
* **H2 — processing workload:** automatic processing (incl. OCR of the scanned PDF) following the
  eight uploads exhausted instance resources (memory/CPU) or crashed the worker/process.

A third possibility — a **Render platform-level incident or instance recycling** — cannot be
excluded either. Crucially, **nothing observed indicates a Step 2 application defect**: no
application error response, no route-specific failure, and no traceback was ever obtained.

## 22. Incident classification

### `UNKNOWN — INSUFFICIENT INFRASTRUCTURE EVIDENCE`

Not classified as *application failure* (no app-generated error body/log), *infrastructure failure*
(no Render event/metric evidence), *resource/load failure* (no CPU/memory telemetry) or *dependency
failure* (no dependency telemetry). The **only** artefacts available — edge/proxy status codes,
headers and timing — are all consistent with *"Render had no healthy instance to route to"*, but they
cannot distinguish H1, H2 or a platform event.

## 23. Evidence gaps

1. **Render deployment history / events** (deploy ids, commits, start/finish, restart reasons) — no access.
2. **Render logs** for 15:20–15:46Z (`ERROR`, `Traceback`, `OOM`, `shutdown`, `startup`) — no access.
3. **Instance/worker identity & lifecycle** — `rndr-id` is per-request and cannot serve this purpose.
4. **Resource telemetry** (CPU, memory, restarts, OOM kills) — no access.
5. **Database/pool telemetry** — no credentials, and may not be discovered.
6. **Worker heartbeat / queue state** for the window — unreachable while the API was down.
7. **The eight documents' states** — unreachable; must be read on a healthy service.
8. **`render.yaml`/Procfile/Dockerfile** — absent from the repository, so build/start/health and
   auto-deploy settings cannot be verified from source at all.

## 24. Recommended next action (for the PO — not performed here)

1. **In the Render dashboard, inspect the service's events for 2026-09-17 15:20–15:46 UTC**:
   deploy events (was `1517588` deployed? by which branch?), instance restarts, OOM/exit codes,
   health-check failures, and whether the service is currently in a restart loop.
2. **Read the service logs** for that window (look for `OOM`, `Killed`, `MemoryError`, `asyncpg`
   pool timeouts, `Failed to start`, `Application startup failed`).
3. **Confirm whether auto-deploy is enabled and on which branch**, then **capture the dashboard's
   build/start/health configuration as `render.yaml`** (the documented highest operational risk).
4. Once the service is healthy, **re-read the eight document IDs** (§13) before any further
   acceptance — this costs nothing and recovers the lost read-back evidence.
5. If the incident proves workload- or process-related, a bounded remediation task should be raised;
   **no remediation is executed or authorised by this report.**

## 25. Acceptance-007 continuation criteria

Step 2 acceptance may resume only when **all** of the following hold:

1. Backend `/health` and `/api/v2/health` return **200** consistently (spaced checks, no CF challenge).
2. OpenAPI reachable and reporting the expected contract (**570 paths**).
3. Worker liveness visible again (`/api/v3/health/realtime`).
4. The cause of this incident is **understood at least to the level needed to know whether resumed
   acceptance could re-trigger it** (i.e. H2 explicitly excluded, or the workload path hardened
   enough that repeating 8 uploads is safe).
5. The eight already-uploaded documents are read back (not re-uploaded) for processing/extraction/
   OCR/EF/report evidence.
6. Acceptance traffic is paced to remain below bot-protection thresholds (avoid the CF challenge
   that produced misleading CORS errors).

Until then, Step 2 acceptance remains **paused**; CSV/PDF extraction, OCR, processing, EF, reports,
Consultant, P1 and isolation testing are **not** resumed by this task.

## 26. Final verdict

### `PRODUCTION STILL UNAVAILABLE — ACCEPTANCE BLOCKED`

Production is **still unavailable** (last verified 2026-09-17T15:49:56Z: frontend 200; backend
503/502 on every probed route, empty bodies, no Cloudflare challenge engaged). The cause is **not established** and
requires Render infrastructure evidence (`UNKNOWN — INSUFFICIENT INFRASTRUCTURE EVIDENCE`). Causality
with the eight uploads is **not established** (temporal correlation only). Step 2 is **not** closed
or re-verified by this report.

**Production data safety:** this investigation created **0** documents, **0** jobs, **0** reports,
**0** data mutations and **0** storage mutations; it issued only read-only HTTP probes. The eight
synthetic documents listed in §13 remain untouched. No credential was requested, discovered or used,
and the synthetic acceptance credentials do not appear anywhere in this report or its evidence.



