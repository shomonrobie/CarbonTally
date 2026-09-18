# Phase 8 — Production Worker Remediation & Stability Verification

**Task ID:** `CT-STEP2-PRODUCTION-WORKER-VERIFY-014` · **Type:** READ-ONLY PRODUCTION VERIFICATION
**Date:** 2026-09-18 · **Release tip (repo):** `22f2ee194b3619fff28aa51fac7abc6398172d5e`
**Verdict:** `PRODUCTION WORKER VERIFICATION PARTIAL — ACCEPTANCE REMAINS PAUSED`
**Deployment identity:** **`DEPLOYMENT IDENTITY UNVERIFIED`** (backend commit cannot be established — §3)

---

## 1. Task identity

Determine whether the production environment is stable enough to resume `CT-STEP2-ACCEPT-007` after
the worker remediation in `CT-STEP2-WORKER-TIMEOUT-013`, and whether the deployed production worker
behaves consistently with the new bounded-extraction / fair-claiming implementation. Read-only: no
upload, re-upload, requeue, retry, unlock, delete, job creation, config change, restart or redeploy.
Credentials were used only from the process environment and never printed.

## 2. Git baseline

```
branch : p8-release-reconciled
HEAD   : 22f2ee194b3619fff28aa51fac7abc6398172d5e
origin : 22f2ee194b3619fff28aa51fac7abc6398172d5e   (identical)
status : clean
expected SHA per task: 22f2ee1 — matches
```

## 3. Deployed-SHA evidence — `DEPLOYMENT IDENTITY UNVERIFIED`

| Evidence source | What it provides | Result |
| --- | --- | --- |
| `GET /` | `{"message":"CarbonTally API","version":"3.0.0","status":"healthy","api_version":"v3","routes_count":49}` | **No commit/build identifier** |
| `GET /health` | `version: 3.0.0`, `supabase_connected`, `pool_connected`, component statuses | **No commit/build identifier** |
| `GET /api/v2/health` | `version: 1.0` | No commit identifier |
| `rndr-id` | per-request identifier only (established in `CT-STEP2-ACCEPT-010`) | **Not** a deployment identifier — deliberately not used |
| Render dashboard/API/CLI | not available in this environment | unavailable |

**No read-only evidence exposes the deployed backend commit**, so the production backend **cannot be
confirmed to be running `22f2ee1`**. Per the task's rule I report `DEPLOYMENT IDENTITY UNVERIFIED` and
do **not** mark the remediation as deployed. (Frontend deployment identity was not re-checked in this
task; it does not evidence the backend commit in any case.)

**Behavioural cross-check (material, §8):** the observed production behaviour is **inconsistent with
the F1 timeout fix being live** — see §8. This corroborates that the deployed backend most likely
predates the remediation, but is not proof of an exact SHA.

## 4. API stability probes (spaced, low frequency, no bursts)

| UTC | Endpoint | Status | Time | Notes |
| --- | --- | --- | --- | --- |
| 05:06:32 | `/` | **200** | 0.40 s | valid JSON |
| 05:06:40 | `/health` | **200** | 2.58 s | `supabase_connected: true`, `pool_connected: true` |
| 05:06:46 | `/api/v2/health` | **200** | 0.32 s | `status: ok` |
| 05:07:43 | `/health` | **200** | 0.43 s | |
| **05:10:14** | `/health` | **503** | 0.28 s | **origin 503** (no Cloudflare challenge) |
| 05:12:45 | `/health` | **200** | 2.16 s | slow |
| 05:16:17 | `/health` | **200** | **7.88 s** | very slow |
| 05:16:50 | `/health` | **200** | 0.88 s | |
| 05:17:16 | `/health` | **200** | 0.46 s | |
| 05:17:41 | `/health` | **200** | 0.47 s | |
| 05:18:07 | `/health` | **200** | 0.98 s | |

* **9 of 10 final-window probes returned 200**, and later probes were consistently healthy — the
  service is **predominantly serving again** (a clear improvement on the incident window).
* **`/openapi.json`** was reachable via the same origin in this window (contract intact); an anonymous
  protected endpoint (`GET /api/v3/documents` without a session) was previously observed to return
  **401** — the authorisation boundary is unchanged.
* **One intermittent 503** at 05:10:14Z and two slow responses (2.2 s, 7.9 s) mean the service is
  **not yet demonstrably *consistently* stable** — a single success was explicitly not accepted as
  proof (§19 of the task).
* 5xx count in this task's probes: **1**.

## 5. Worker heartbeat / liveness

* No RLS-readable heartbeat table exists for this principal (`worker_heartbeats`, `worker_heartbeat`,
  `processing_worker_heartbeats`, `worker_liveness` → **404**, PostgREST hints point to unrelated
  tables). `processing_logs` was empty in the earlier read-back.
* **Liveness is therefore evidenced indirectly, from queue state** (legitimate natural evidence):

| Observation | Value | Meaning |
| --- | --- | --- |
| `scan_light_gas.pdf` `locked_at` | **05:04:17.406304Z** then **05:14:18.324043Z** | a worker **claimed** this job twice within the window — the worker is alive and ticking |
| `layout_standard_elec.pdf`, `multi_fuel.pdf` | advanced `extracting → blocked` at **04:59:20Z** (0.5 s apart) | worker performed a single multi-job claim/progress event |
| `diff_edge_fuel.pdf` | advanced to `blocked` at **05:00:37Z** with `method=pdf_text`, attempts **1** | worker processed a job through extraction → mapping → validation |

**Worker: ALIVE.** Sustained health is *not* established: the same job has now been claimed at least
twice without completing (§8), and no completed job exists in this tenant.

## 6. Existing eight-document state (read-only, RLS-scoped, unchanged IDs)

| # | File | Queue status | Stage | Attempts | `locked_at` | Method | Emissions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `mock_uk_fuel_card_messy.csv` | manual_review | blocked | 1 | null | `csv` | null |
| 2 | `mock_uk_utility_bill.csv` | manual_review | blocked | 1 | null | `csv` | null |
| 3 | `mock_scope3.csv` | manual_review | blocked | 1 | null | `csv` | null |
| 4 | `layout_standard_fuel.pdf` | manual_review | blocked | 0 | null | — | null |
| 5 | `layout_standard_elec.pdf` | manual_review | blocked | 0 | null | — | null |
| 6 | `multi_fuel.pdf` | manual_review | blocked | 0 | null | — | null |
| 7 | `scan_light_gas.pdf` | **processing** | **extracting** | 0 | **05:14:18.324Z** | — | null |
| 8 | `diff_edge_fuel.pdf` | manual_review | blocked | 1 | null | **`pdf_text`** | null |

All eight documents remain **intact** (`organization_files` = 8 rows, `status=uploaded`), and the API
read model works again: `GET /api/v3/documents` **200**, `GET /api/v3/processing/status` **200**
(`pipeline: {source: 1, extraction: 6, mapping: 1, …}`, `total_items: 8`, `pct_complete: 0.0`).

## 7. Five incident-affected PDF jobs

| File | Incident state (Sep 17) | Current state (Sep 18) | Assessment |
| --- | --- | --- | --- |
| `layout_standard_elec.pdf` | `extracting`, locked 16:02:17Z, attempts 0 | **manual_review/blocked**, attempts 0, `locked_at` null, updated **04:59:20Z** | left the executing state; blocked on completeness 0.33 < 0.50 (truthful) |
| `multi_fuel.pdf` | `extracting`, locked 16:02:17Z, attempts 0 | **manual_review/blocked**, attempts 0, updated **04:59:20Z** | same |
| `scan_light_gas.pdf` | `extracting`, locked 16:02:17Z, attempts 0 | **still `extracting`**, re-claimed **05:04:17Z** then **05:14:18Z** | **still not completing; no timeout failure** |
| `diff_edge_fuel.pdf` | `enqueued`, **never claimed** | **manual_review/blocked**, attempts **1**, `method=pdf_text`, reason `validation found blocking findings: EXTRACTION_MISSING_FIELD (supplier)`, updated **05:00:37Z** | **claimed, extracted, validated** — starvation symptom gone |
| `layout_standard_fuel.pdf` | `manual_review`, attempts 0 | unchanged (`blocked`, updated 15:30:55Z Sep 17) | unchanged / truthful |

No transition was caused by this task.

## 8. F1 verification — **`PRODUCTION EXECUTION UNVERIFIED` / behaviour inconsistent**

`scan_light_gas.pdf` was claimed **twice** — `locked_at` **05:04:17Z**, then **05:14:18Z** — and
remained `processing`/`extracting` with **`attempt_count = 0`**, **`last_error` null** and no
`failed` state.

Under the remediation as built, the 05:04:17Z claim must have been resolved within
`EXTRACTION_TIMEOUT_S` (240 s) — by ~05:08:17Z — by completing **or** by failing truthfully
(`TimeoutError: extraction exceeded the 240s execution budget`, `attempt_count` + 1, `stage='failed'`).
**Neither occurred**; instead the row became claimable again after the 300 s stale window and was
re-claimed — the *pre-fix* behaviour.

⇒ a timed-out extraction **cannot** be shown to be bounded in production; the evidence is
**inconsistent with the F1 remediation being live**. No timeout was manufactured and no job requeued.

## 9. F2 verification — **PARTIAL, not attributable**

During 05:16–05:18Z `scan_light_gas.pdf` was continuously `extracting` (claimed 05:14:18Z) while
**five consecutive `/health` probes returned 200** (0.46–7.88 s) with the origin serving
(`rndr-id` present, no Cloudflare challenge) — the API serves while an extraction is in flight.

But (a) one **503** occurred earlier in the window (05:10:14Z) and two responses were slow (2.2 s,
7.9 s); (b) sampling cannot prove the absence of event-loop blocking, and the same sample would also
be consistent with the **old** code if the in-flight extraction periodically returned to the loop.
**No attribution to the remediation is claimed.**

## 10. F3 verification — **symptom absent, mechanism NOT VERIFIED**

The invariant "a currently locked/executing job is not selected again as fresh work merely because it
is old in FIFO order" **cannot be confirmed**: `scan_light_gas.pdf` is still selected repeatedly —
albeit legitimately, because its lock **expires** after 300 s rather than being held fresh.

The *starvation symptom* is gone (the previously never-claimed `diff_edge_fuel.pdf` was claimed and
processed, and the older stuck rows left the claimable set). **However**, that sequence is also
reachable under the **old** predicate once the older rows became `blocked`, so the improvement
**cannot be attributed to the F3 fix**. Deterministic evidence for F3 remains the unit SQL-contract
test from commit `0d14367`, not production.

## 11. F4 verification — **PARTIAL**

* `diff_edge_fuel.pdf` carries **`attempt_count = 1`** while `blocked` — an attempt/retry transition
  was recorded rather than frozen at 0, and the job is not left in `extracting` (blocked rows are not
  fresh claim candidates).
* **But** the *timeout* path produced no failure state anywhere in this window (§8), so the new
  timeout → `mark_failed(attempt_count + 1)` behaviour is **unobserved in production**.
* No failure was forced.

## 12. OCR verification — **UNVERIFIED**

`scan_light_gas.pdf` (content-verified earlier as having **no text layer**) is the document whose
extraction would exercise the OCR chain. Current state: `status=processing`, `stage=extracting`,
**`ai_extraction_method = null`**, `ai_extracted_at` unset, `attempt_count = 0`, `last_error` null;
claimed at 05:04:17Z and again at 05:14:18Z without reaching `manual_review`, `failed` or any method
record.

⇒ **`onnx_ocr` production execution remains UNVERIFIED.** The document was **not** re-uploaded,
reprocessed or requeued to force it, and it did not complete naturally in the observed window.

## 13. CSV preservation — **PASS (unchanged, truthful)**

| Evidence | Value |
| --- | --- |
| `mock_uk_fuel_card_messy.csv` | `manual_review`/`blocked`, **`method = csv`**, `attempt_count = 1`, `updated_at = 2026-09-17T15:30:52.345112Z` (**identical to the ACCEPT-011 read**), `calculated_emissions_kg_co2e = null`, reason unchanged (per-line `no_match`, `AdBlue` litres) |
| `mock_uk_utility_bill.csv` | `manual_review`/`blocked`, `method = csv`, attempts 1, `updated_at 15:30:58Z` (unchanged) |
| `mock_scope3.csv` | `manual_review`/`blocked`, `method = csv`, attempts 1, `updated_at 15:30:55Z` (unchanged) |

The persisted F-02 extraction values already recovered from production (`Diesel` / `53.8` / `litres` /
`85.21` / `Esso` / `source_row 1`, `method=csv`, confidence 1) were **not re-read**, because the row
is unchanged (same `updated_at`) and nothing in this task wrote to it; they remain as recorded in
`P8-STEP2-PRODUCTION-RECOVERY-READBACK-011.md` §10 and its evidence bundle. **No reprocessing, no
re-upload.**

## 14. No-fabrication verification — **PASS**

For all eight documents: `calculated_emissions_kg_co2e` is **null** for every row (no fabricated
calculation); `calculation_snapshot_id`/`calculated_at` unset (no fabricated snapshot); unresolved
factor matches remain **explicit** (`no_match`, `confidence=0.00`, per line — no fabricated factor);
manual-review reasons remain present and specific (per-line `no_match`; completeness
`0.33 < 0.50 — unresolved: quantity, unit`; `validation found blocking findings:
EXTRACTION_MISSING_FIELD (supplier)`); quantities/units appear only where the extractor returned them.
Nothing was modified during verification.

## 15. Cloudflare distinction

`cf-mitigated: challenge` was **absent** on every probe; the single non-200 (05:10:14Z **503**) came
from the **origin** (`rndr-id` present, no challenge page) — a genuine backend blip, **not** a
Cloudflare challenge. No 429/challenge was encountered because probes were spaced (≥15 s) with no
bursts, so Cloudflare behaviour played no part in this verdict and was never treated as worker-failure
evidence.

## 16. Incident relationship

* Production has **recovered substantially** since Sep 17 (predominantly 200s, API read model working,
  ingestion evidence intact) but showed **one intermittent origin 503** and two slow responses
  (2.2 s, 7.9 s) — not yet demonstrably consistently stable.
* **No claim is made that the worker remediation fixed the historical Render outage.** Correct
  assessment: production is largely serving again; the worker defects' production behaviour is only
  **partially** consistent with the new implementation (F1 inconsistent; F2/F3/F4 not attributable);
  the **historical causal relationship remains unknown** (no Render telemetry available).
* One prior symptom **has** disappeared: no job holds a stale Sep-17 lock, and the previously
  never-claimed job was processed.

## 17. Production limitations

1. **Deployed backend SHA is unobtainable** — no commit/build identifier on any read-only surface
   (`rndr-id` is per-request and was deliberately not used as one).
2. **No Render logs / metrics / deploy events** — restart history, OOM and deploy id unverifiable.
3. **No RLS-readable worker heartbeat or processing-log table** for this principal; liveness inferred
   from queue state.
4. The OCR document appears to be **cycling** (claim → stale → re-claim) without completing — the
   exact behaviour class the remediation targets — while the remediation's effect is not evidenced.
5. Sampling cannot prove the absence of event-loop blocking (F2) or starvation (F3).
6. One 503 and two slow responses mean stability is **improving but unproven**.

## 18. Step 2 acceptance gate — **NOT READY**

`CT-STEP2-ACCEPT-007` **remains paused**. Each reason is independently sufficient:

1. **Deployment identity unverified** — the production backend cannot be confirmed to be running
   `22f2ee1`, and the F1 evidence indicates that it is **not**.
2. **Worker remediation not demonstrated in production** — F1 behaviour is *inconsistent* with the new
   implementation; F2/F3/F4 are not attributable to the fix; OCR remains unverified.
3. **Stability not yet consistent** — one origin 503 plus two slow responses in the window, with a job
   still cycling in `extracting`.

**`CT-STEP2-ACCEPT-007 MAY RESUME` is therefore NOT stated.**

## 19. Exact next task

**`CT-STEP2-PRODUCTION-DEPLOY-VERIFY-015` — Establish deployed SHA and re-verify the worker
remediation in production** (proposed; not executed here):

1. Promote/redeploy the backend at `22f2ee1` through the normal controlled path (operator action; this
   environment has no Render access).
2. **Establish deployment identity** — expose and read a build/commit identifier (e.g. a
   `commit`/`build` field on `/` or `/health`) so deployment can be verified without inference.
3. Re-run this verification and observe the naturally pending jobs (e.g. `scan_light_gas.pdf`) across
   the 240 s budget, confirming that the timeout → truthful failure → attempt-accounting path
   **appears in production**.
4. Separately (unchanged): the Render infrastructure investigation per
   `P8-STEP2-PRODUCTION-API-INCIDENT-010.md` §24, for the historical incident and the lingering
   intermittent 503.

No *new* defect task is raised: the observed `extracting` cycling is consistent with the
**already-confirmed** defect class (`CT-STEP2-WORKER-STALL-012`, fix `0d14367`) whose **deployment is
unverified** — it is not evidence of a new defect, and nothing was patched or requeued here.

## 20. Mutation statement

```
new documents = 0 · re-uploads = 0 · requeues/retries/unlocks = 0 · new jobs = 0
deletions = 0 · data mutations = 0 · storage mutations = 0 · new reports = 0
config changes = 0 · Render restarts/redeploys = 0 · code/tests/migrations modified = none
credentials printed or committed = none
```

Read-only actions: `git` state queries; spaced read-only HTTP probes (≤16 requests, ≥15 s apart, no
bursts); one authenticated session for the authorised synthetic Owner; RLS-scoped `GET`/`SELECT`s of
that tenant's own rows (queue, files, processing status) plus four table-existence probes for
heartbeat telemetry (all 404). No `POST`/`PUT`/`PATCH`/`DELETE` was issued to the application or the
database.

## Final verdict

### `PRODUCTION WORKER VERIFICATION PARTIAL — ACCEPTANCE REMAINS PAUSED`

Production is largely serving again (9 of 10 probes 200) and the worker is alive, but the deployed
backend **cannot be identified**, the bounded-extraction behaviour is **not** evidenced in production
(and is inconsistent with the fix), OCR remains unverified, and one intermittent origin 503 plus a
still-cycling job mean stability is not yet demonstrably consistent. `CT-STEP2-ACCEPT-007` therefore
**remains paused**, pending `CT-STEP2-PRODUCTION-DEPLOY-VERIFY-015`.



