# Phase 8 — Live Production Verification of the Worker Remediation

**Task ID:** `CT-STEP2-PRODUCTION-DEPLOY-VERIFY-015` · **Type:** READ-ONLY PRODUCTION RUNTIME VERIFICATION
**Date:** 2026-09-18 · **Release:** `p8-release-reconciled` @ `77084d4`
**Verdict:** `PRODUCTION DEPLOYMENT VERIFIED — WORKER REMEDIATION NOT YET VERIFIED — ACCEPTANCE REMAINS PAUSED`

---

## 1. Task identity

Verify the **runtime behaviour** (not the identity) of the deployed worker remediation (`0d14367`
containing F1–F4 fixes, in the ancestry of `77084d4`) using only the existing eight synthetic
acceptance documents. No code, config, data, jobs or deployments were modified; nothing was uploaded,
requeued, retried, unlocked or deleted; no restart or redeploy was performed.

## 2. Git baseline

```
branch : p8-release-reconciled
HEAD   : 77084d47621d3aa60300b7ee0c0caba8b47cbc10
origin : 77084d47621d3aa60300b7ee0c0caba8b47cbc10   (identical)
status : clean ; no history alteration ; ~/carbon_tally untouched
```

## 3. Render deployment identity (supplied, recorded — not inferred)

| Item | Value |
| --- | --- |
| Provider / service | Render — production backend |
| Status | **Deploy succeeded / Live** |
| Branch | `p8-release-reconciled` |
| Commit | **`77084d4`** |
| Trigger | manual deploy via Render Dashboard (operator action) |
| Ancestry contained | `0d14367` (fix), `8a336a9` (tests), `22f2ee1` (report), `77084d4` (report) |

Deployment identity is **not** inferred from `rndr-id` (which remains a per-request identifier and was
not used as one). The API still exposes no commit/build field of its own — noted as a limitation (§19).

## 4. Vercel deployment identity (supplied, recorded)

Frontend production (`carbontally.co.uk`): branch `p8-release-reconciled`, commit **`77084d4`**, live.
Frontend bundle identity was not otherwise re-derived in this task (it does not evidence backend
runtime behaviour).

## 5. API stability

**Spaced probes (3 s apart within a round, 22 s between rounds; no bursts):**

| UTC | Endpoints probed | Result |
| --- | --- | --- |
| 05:26:53, 05:27:16, 05:27:39, 05:28:01, 05:28:24, 05:28:46 | `/`, `/health`, `/api/v2/health` | **18 / 18 → 200**, `cf-mitigated` absent, bodies valid (168 B / 373 B / 78 B), response times **0.35–1.95 s** |
| 05:29 | `/openapi.json` | **200**, **570 paths** |
| 05:29 | `GET /api/v3/documents` (anonymous) | **401** — authorisation boundary intact |
| 05:30:07 / 05:31:47 / 05:33:30 / 05:35:11 | `/health` | **503** → 200 (1.97 s) → 200 (0.66 s) → **429 Cloudflare challenge** |
| 05:29 | `GET /api/v3/processing/status` (authenticated) | **503** |
| 05:40:34 | `/health` | **503** |

**Interpretation:** the backend is **substantially recovered and serving well for sustained windows**
(18 consecutive 200s), but it **flaps**: three separate 503s were observed (05:30, ~05:29, 05:40) and
`/processing/status` was 503 once. **5xx count in this task: 3.** Stability is *improved* but **not
consistent**, so "consistently serving" is **not** established. The 429 at 05:35:11 was a **Cloudflare
challenge** on my probing volume (see §17) and is not counted as an origin failure.

## 6. Worker liveness

* No RLS-readable worker heartbeat table exists for this principal (probed in `014`: four candidate
  tables → 404; PostgREST hints point to unrelated tables). **Stated plainly: heartbeat telemetry is
  inaccessible through RLS**, so liveness is evidenced from queue behaviour.
* **Worker: ALIVE** — queue transitions and fresh claims were observed:
  * `scan_light_gas.pdf` claimed at **05:04:17**, **05:14:18**, **05:29:20** and **05:39:22** (four
    distinct lock timestamps).
  * `layout_standard_elec.pdf` and `multi_fuel.pdf` advanced `extracting → blocked` at 04:59:20Z.
  * `diff_edge_fuel.pdf` advanced to `blocked` at 05:00:37Z with `method=pdf_text`, `attempt_count=1`.
* **Locks behave as designed for the *stale* path** (each claim appears after the ~300 s stale
  window), but **no job reaches a completed or failed terminal state** in this tenant.

## 7. Eight-document inventory (unchanged, read-only)

| # | File | Queue status | Stage | Attempts | `locked_at` | Method | Emissions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `mock_uk_fuel_card_messy.csv` | manual_review | blocked | 1 | null | `csv` | null |
| 2 | `mock_uk_utility_bill.csv` | manual_review | blocked | 1 | null | `csv` | null |
| 3 | `mock_scope3.csv` | manual_review | blocked | 1 | null | `csv` | null |
| 4 | `layout_standard_fuel.pdf` | manual_review | blocked | 0 | null | — | null |
| 5 | `layout_standard_elec.pdf` | manual_review | blocked | 0 | null | — | null |
| 6 | `multi_fuel.pdf` | manual_review | blocked | 0 | null | — | null |
| 7 | `scan_light_gas.pdf` | **processing** | **extracting** | **0** | **05:39:22.139937Z** | — | null |
| 8 | `diff_edge_fuel.pdf` | manual_review | blocked | 1 | null | `pdf_text` | null |

All eight remain intact (`organization_files` = 8 rows). Document IDs unchanged from
`docs/cline/evidence/P8-STEP2-ACCEPT-011/`.

## 8. Five PDF jobs — state progression vs `ACCEPT-011` and `014`

| File | 011 (Sep 17) | 014 (Sep 18 early) | Now (05:40Z) | Change |
| --- | --- | --- | --- | --- |
| `layout_standard_elec.pdf` | `extracting`, lock 16:02:17Z | `blocked` 04:59:20Z | unchanged | left executing (earlier) |
| `multi_fuel.pdf` | `extracting`, lock 16:02:17Z | `blocked` 04:59:20Z | unchanged | left executing (earlier) |
| `scan_light_gas.pdf` | `extracting` | claimed 05:04:17Z, 05:14:18Z | **claimed 05:29:20Z and 05:39:22Z**, still `extracting`, attempts 0, no error | **still cycling** |
| `diff_edge_fuel.pdf` | `enqueued`, never claimed | `blocked` 05:00:37Z, `pdf_text`, attempts 1 | unchanged | processed |
| `layout_standard_fuel.pdf` | `blocked` 15:30:55Z | unchanged | unchanged | — |

No transition was caused by this task.

## 9. F1 runtime evidence — **NOT VERIFIED; inconsistent with the deployed timeout path**

Deployed code (in the ancestry of `77084d4`): each attempt is awaited under
`asyncio.wait_for(..., timeout=EXTRACTION_TIMEOUT_S)` with `EXTRACTION_TIMEOUT_S = 240`; expiry raises
`TimeoutError` → existing failure pathway → `mark_failed(last_error="TimeoutError: extraction exceeded
the 240s execution budget", attempt_count + 1)` → `stage='failed'`.

Observed for the one naturally executing extraction (`scan_light_gas.pdf`):

| Claim (`locked_at`) | Expected under deployed code | Observed |
| --- | --- | --- |
| 05:04:17Z | complete or fail by ~05:08:17Z | neither; re-claimed as stale |
| 05:14:18Z | complete or fail by ~05:18:18Z | neither; re-claimed as stale |
| 05:29:20Z | complete or fail by ~05:33:20Z | neither; re-claimed as stale |
| 05:39:22Z | complete or fail by ~05:43:22Z | still `processing`/`extracting` at 05:40:34Z |

Across **four claims**: `attempt_count` remains **0**, `last_error` is **null**,
`ai_extraction_method` is **null**, and no `failed` state ever appears.

⇒ the timeout → truthful-failure → attempt-accounting path is **not observable in production**:
**`F1 RUNTIME EXECUTION UNVERIFIED`**. This is *not* asserted as a new defect (§19) — the same
signature would result from any condition that ends the attempt outside the awaited coroutine before
240 s elapses, most plausibly **repeated worker/process restarts** (each boot claims, then dies before
the budget), which is also consistent with the observed API flapping (§5). What is established is that
F1 **cannot be verified in the current runtime**. No timeout, hang or requeue was manufactured.

## 10. F2 runtime evidence — **PARTIAL (weak positive, not attributable)**

* With the scan job nominally in `extracting`, five consecutive `/health` probes returned **200**
  (0.46–7.88 s) during 05:16–05:18Z (`014`), and this task recorded **18 consecutive 200s** across
  ~2 minutes (0.35–1.95 s).
* Counter-evidence: 503s in the same window (05:30:07Z, 05:40:34Z) and slow responses (1.97 s, 7.88 s).
* Sampling cannot demonstrate the **absence** of event-loop blocking, and the extraction's true
  runtime state between claims is unknown (the job may not be executing at all).

**Strength: weak positive; no attribution to the remediation; no mathematical proof claimed.**

## 11. F3 runtime evidence — **symptom absent; mechanism NOT attributably verified**

* The previously starved **`diff_edge_fuel.pdf` (never claimed under the old predicate) has been
  claimed, extracted (`pdf_text`), validated and blocked** — the *starvation symptom* is gone.
* But the deployed predicate cannot be confirmed as the cause: the three older rows had already left
  the claimable set (`blocked`) before the 4th was processed, so the same sequence is reachable under
  the old predicate.
* `scan_light_gas.pdf` is re-claimed repeatedly — **legitimately** under the new predicate (its lock
  expires after 300 s rather than being held fresh) — consistent with, but not diagnostic of, the fix.

**Verdict: symptom absent, mechanism unverified in production** (deterministic proof remains the unit
SQL-contract test in `8a336a9`).

## 12. F4 runtime evidence — **`F4 PRODUCTION EXECUTION UNVERIFIED`**

No naturally occurring failure/timeout exists to inspect: no row carries `last_error`, none is
`stage='failed'`, and `attempt_count` is 0 on every non-CSV row. `diff_edge_fuel.pdf` does carry
`attempt_count = 1` while `blocked`, and no job holds a stale Sep-17 lock — both consistent,
neither diagnostic. **No failure was forced.**

## 13. Stale-lock analysis

* Source (unchanged): stale threshold **300 s**, extraction budget **240 s** ⇒ **240 s < 300 s still
  holds**, so under the deployed code an extraction should always resolve before its claim goes stale.
* Production is **inconsistent with that relationship being active**: four consecutive claims of the
  same job appear *after* the stale window (05:04 → 05:14 → 05:29 → 05:39, ~10–15 min apart) with **no
  resolution between them**, whereas the deployed budget should have produced an outcome within 4 min.
* **Natural stale recovery IS observed** (the row becomes claimable again after ~300 s) while the
  **240 s budget's effect is NOT observed at all** — the core runtime discrepancy of this task.
* Neither value was changed; no restart was simulated.

## 14. OCR status — **UNVERIFIED IN PRODUCTION**

`scan_light_gas.pdf` at 05:40:34Z: `status=processing`, `stage=extracting`,
**`ai_extraction_method = null`** (neither `tesseract_ocr` nor `onnx_ocr` ever recorded),
`ai_extracted_at`/`confidence` unset, `attempt_count = 0`, no block reason. It neither completed nor
failed in the window, so the **pypdfium2 + RapidOCR/ONNX path remains UNVERIFIED IN PRODUCTION**.
It was **not** requeued or re-uploaded.

## 15. CSV preservation — **PASS (re-verified in this task)**

| Item | Value |
| --- | --- |
| `mock_uk_fuel_card_messy.csv` | `manual_review`/`blocked`, **`method = csv`**, **`confidence = 1`**, `updated_at = 2026-09-17T15:30:52.345112Z` (**unchanged since ACCEPT-011**), `calculated_emissions_kg_co2e = null`, reason unchanged (per-line `no_match`, `AdBlue` litres) |
| Persisted first line item (re-read now) | `{"date":"01/10/2023","unit":"litres","amount":85.21,"activity":"Diesel","quantity":53.8,"supplier":"Esso","source_row":1}` → **Diesel / 53.8 / litres / 85.21 / Esso / source_row 1 confirmed** |
| Persisted line count | **50** |
| `mock_uk_utility_bill.csv` / `mock_scope3.csv` | `method = csv`, attempts 1, `updated_at` unchanged (15:30:58Z / 15:30:55Z), reasons intact |

Nothing was rewritten; the evidence was only read.

## 16. No-fabrication verification — **PASS**

For all eight documents: `calculated_emissions_kg_co2e` is **null everywhere** (no fabricated
calculation); no `calculation_snapshot_id`; unresolved factor matches remain **explicit**
(`no_match`, `confidence=0.00`, per line); manual-review reasons remain present and specific
(per-line `no_match`; `completeness 0.33 below 0.50 — unresolved: quantity, unit`;
`validation found blocking findings: EXTRACTION_MISSING_FIELD (supplier)`); no placeholder
quantity/unit was introduced by resumed processing.

## 17. Cloudflare distinction

| Condition | Evidence | Classification |
| --- | --- | --- |
| Successful origin response | 200s with valid bodies, `cf-mitigated` absent | normal service |
| **Origin failure** | **503** at 05:30:07Z, ~05:29Z (`/api/v3/processing/status`), 05:40:34Z — `rndr-id` present, `cf-mitigated` **absent** | backend unavailability, **not** Cloudflare |
| **Cloudflare challenge** | **429** at 05:35:11Z (91 ms, challenge page) during the densest probe round | bot protection triggered by **my probe volume**; explicitly **not** worker failure |

No burst traffic was generated; probes were spaced (3 s within a round, ~22 s between rounds).

## 18. Historical incident boundary

* **A — Worker remediation deployed?** Yes: Render Dashboard establishes `77084d4` (branch
  `p8-release-reconciled`), whose ancestry contains `0d14367`.
* **B — Worker remediation behaves correctly?** **Not established** (§9–§14): the deployed timeout path
  is not observable, F2/F3/F4 are not attributably verified, and OCR remains unverified.
* **C — Historical Render outage cause?** **Still unknown** — no infrastructure telemetry available in
  this environment. **No claim is made that the worker remediation caused or definitively resolved the
  September 17 outage**; current stability is reported as *current* stability only.

## 19. Limitations

1. The API exposes **no commit/build identifier**, so deployment identity rests on the supplied Render
   Dashboard evidence (recorded, not independently derivable here).
2. **No Render logs, metrics, deploy events or restart history** — the leading explanation for the F1
   discrepancy (restarts ending attempts before 240 s) **cannot be confirmed or excluded**.
3. **No RLS-readable worker heartbeat table** for this principal (404 in `014`); liveness is inferred
   from queue transitions rather than telemetry.
4. Only **one** job (`scan_light_gas.pdf`) is naturally exercising extraction, so F1/F4 evidence rests
   on a single document and four claim cycles.
5. Sampling cannot prove the absence of event-loop blocking (F2) or starvation (F3).
6. The API flapped during this task (3 origin 503s), so "consistently serving" is **not** established.
7. Harness note: an earlier read filtered the queue by the **document** id, whereas
   `document_processing_queue.id` is the **job** id — those reads returned empty rows and are **not**
   evidence of data loss. All conclusions here use correct org-scoped reads.

## 20. Step 2 acceptance gate — **NOT READY**

Deployment identity is confirmed, but **the worker remediation is not verified in production**
(F1 unobservable/inconsistent, F2/F3/F4 not attributably verified, OCR unverified) and the API is **not
consistently stable** (3 origin 503s in the window). Therefore **`CT-STEP2-ACCEPT-007 MAY RESUME` is
NOT declared.**

## 21. Next task

**`CT-STEP2-WORKER-RUNTIME-DISCREPANCY-016` — Resolve the deployed-vs-observed worker timeout
discrepancy** (proposed; not executed here). Required evidence/actions (PO/infra):

1. Retrieve **Render runtime logs** around **05:04–05:44Z on 2026-09-18**: process starts/stops,
   OOM/exit codes, the worker startup line
   (`automatic-processing worker started (poll 1.0s, batch 3)`), and any
   `automatic-processing tick failed` / `job … crashed during processing` entries.
2. Confirm **which Render service** runs the worker and that it was rebuilt from `77084d4` — a separate
   service or instance would explain a pre-fix claim cycle.
3. Confirm whether the process is **restarting repeatedly** (each boot claiming, then dying before the
   240 s budget) — this would explain both the cycling job and the intermittent 503s.
4. Then re-run `CT-STEP2-PRODUCTION-DEPLOY-VERIFY-015` to observe the timeout path appear naturally.

No new defect is asserted: the cycling job is consistent with the **already-confirmed** defect class
whose *runtime behaviour* awaits the evidence above, and nothing was patched or requeued.

## 22. Mutation statement

```
new documents = 0 · re-uploads = 0 · requeues/retries/unlocks = 0 · new jobs = 0 · deletions = 0
data mutations = 0 · storage mutations = 0 · new reports = 0 · config changes = 0
Render/Vercel restarts or redeploys = 0 · code/tests/migrations modified = none
credentials printed or committed = none
```

Read-only actions: `git` state queries; spaced read-only HTTP probes (~40 requests total, ≥3 s apart,
no bursts); one authenticated session for the authorised synthetic Owner; RLS-scoped `GET`/`SELECT`s of
that tenant's own rows (queue, files, processing status). No `POST`/`PUT`/`PATCH`/`DELETE` was issued to
the application or the database.

## Final verdict

### `PRODUCTION DEPLOYMENT VERIFIED — WORKER REMEDIATION NOT YET VERIFIED — ACCEPTANCE REMAINS PAUSED`

Deployment at `77084d4` is confirmed and the backend is substantially serving again (18 consecutive
200s; OpenAPI **570 paths**; auth boundary intact with a 401 for anonymous access; CSV evidence
re-verified unchanged with **no fabrication**). However the **deployed timeout path is not observable**
(four claims, `attempt_count` frozen at **0**, no `failed` state, `ai_extraction_method` null),
F2/F3/F4 are not attributably verified, OCR remains unverified, and **three origin 503s** were
observed — so the remediation's runtime behaviour is **not yet verified** and `CT-STEP2-ACCEPT-007`
**remains paused**.



