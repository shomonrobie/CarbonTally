# Phase 8 — Worker Stall / Claim-Expiry Forensic Investigation

**Task ID:** `CT-STEP2-WORKER-STALL-012` · **Type:** READ-ONLY FORENSIC INVESTIGATION
**Date:** 2026-09-17/18 · **Release:** `p8-release-reconciled` @ `f87a129`
**Verdict:** `FORENSIC COMPLETE — APPLICATION DEFECT CONFIRMED`
(application failure modes confirmed **by source**; attribution of *this* incident to them is
**not** established and still requires Render telemetry — §21)

---

## 1. Task identity

Determine whether the `CT-STEP2-ACCEPT-011` production evidence (3 jobs in
`processing/extracting`, lock re-acquired 16:02:17Z, `attempt_count` 0, `last_error` null, one job
never claimed, API 502/503) represents an application worker/extraction defect, a missing
timeout/claim-expiry mechanism, an infrastructure failure, or an unexplained state.

## 2. Scope

Read-only: no code, tests, migrations, RLS, configuration, production data, queue state, documents or
storage were modified. No job was retried, requeued or unlocked. No Render restart/redeploy. No
credentials are reproduced here.

## 3. Baseline Git state

```
branch : p8-release-reconciled      HEAD : f87a129070d2ece90b8c288fe5d8b021a7697636
origin : f87a129070d2ece90b8c288fe5d8b021a7697636   (HEAD == origin)
worktree: clean at task start; no reset/clean/stash/rebase/merge performed
```

## 4. Previous incident context

* `P8-STEP2-PRODUCTION-API-INCIDENT-010.md` — API 502/503 from ~15:31Z; frontend 200; Cloudflare
  challenge a **separate** condition; cause unknown.
* `P8-STEP2-PRODUCTION-RECOVERY-READBACK-011.md` — API had **not** recovered; 8 documents intact;
  3 CSVs extracted + blocked truthfully; 3 jobs stuck `extracting`; 1 job never claimed.
* **New in this task:** the outage is now **~12.5 hours old** — spaced probes at **04:40Z (next day)**
  still return **502 / 503 / 503** for `/health` while the frontend returns **200** (DNS resolves to
  Render's origin via Cloudflare, `216.24.57.16/.18`).

## 5. Exact affected production jobs (from captured evidence)

| File | Document ID | Stage at capture | `locked_at` = `updated_at` | `attempt_count` | `last_error` |
| --- | --- | --- | --- | --- | --- |
| `layout_standard_elec.pdf` | `585e4345-5919-41cc-a8ef-319d02f41c71` | `extracting` | `2026-09-17T16:02:17.280227Z` | **0** | `null` |
| `multi_fuel.pdf` | `30f761c6-899d-450a-b744-87c389d6f972` | `extracting` | `2026-09-17T16:02:17.280227Z` | **0** | `null` |
| `scan_light_gas.pdf` | `91acc68d-baa9-4cd2-9558-251cec01379e` | `extracting` | `2026-09-17T16:02:17.280227Z` | **0** | `null` |
| `diff_edge_fuel.pdf` | `3e6dd5d9-0fac-472b-b38b-1b8ecc99fada` | `enqueued` (never claimed) | `null` | **0** | `null` |
| 3 CSVs + `layout_standard_fuel.pdf` | — | `blocked` (manual_review) | `null` | **1** | `null` |

The **material fact** is that the three stuck rows share one identical claim timestamp.

## 6. Production timeline

| UTC | Event | Source |
| --- | --- | --- |
| 15:30:33–15:30:49 | 8 documents uploaded (201) and enqueued | 011 evidence |
| 15:30:52–15:30:58 | **3 CSVs** extracted (`method=csv`, conf 1) → mapping → blocked (manual_review) | 011 evidence |
| ~15:30:41–15:30:49 | PDF jobs claimed and enter `extracting` | 011 evidence |
| **15:31:22** | first API failure (authenticated read → **502**) | 010/011 |
| 15:33–15:39 | 503s (Cloudflare challenge separate) | 010 |
| **16:02:17.280227Z** | **one claim event locks 3 rows simultaneously** (`locked_at=updated_at`) | 011 evidence |
| 16:0x → 04:41 next day | API still 502/503; jobs never completed | this task |

## 7. Queue state machine (source: `backend/data/document_processing.py`, `domain/automatic_processing.py`)

```
enqueued → ingesting → extracting → mapping → validating → calculating → completed
                            ↓            ↓           ↓
                        blocked      blocked      blocked    (manual_review; re-entry via human action)
   any stage → failed  (dead-letter after max_attempts=3; reachable only via failure paths)
```

**Claimable set** (`claim_next`, lines 236-255): `stage IN ('enqueued','ingesting','extracting',
'mapping','validating','calculating')` **or** `(stage IS NULL AND status='pending')`.
**`blocked` is NOT claimable** — confirmed by production data (the 4 blocked rows were never
re-claimed while the 3 `extracting` rows were).

## 8. Worker lifecycle (source: `backend/workers/automatic_processing.py`)

* `poll_interval_seconds = 1.0`, **`batch_size = 3`**, `stale_lock_seconds = 300` (lines 60-63).
* `start()` → `asyncio.create_task(_run_loop)`; `_run_loop` ticks every second and **never dies**
  (exceptions caught, lines 113-114).
* `_tick()`: writes a **heartbeat on every tick incl. idle** (line 129) → dispatches alerting as a
  background task (line 147) → `claim_next(token, limit=3, stale_after_seconds=300)` (line 153) →
  **`asyncio.gather(*(self._process_one(job, token) …))`** (line 160): **up to 3 jobs concurrently in
  one event loop**.
* Per-job crash → `mark_failed("worker exception: …")` (lines 164-172).
* `stop()` cancels the loop task; in-flight jobs are **not** failed or released explicitly — they are
  recovered later by stale-lock release (§9).

## 9. Lock / claim semantics (source)

`claim_next` (lines 216-256) performs, in order:

1. `UPDATE … SET locked_at=NULL, lock_token=NULL WHERE locked_at IS NOT NULL AND locked_at < now-300s`
   → **stale-lock release happens inside every claim call**;
2. `WITH claimed AS (SELECT id … WHERE stage IN (…) ORDER BY created_at, id FOR UPDATE SKIP LOCKED
   LIMIT 3)` → `UPDATE … SET locked_at=$1, lock_token=$2, updated_at=$1` — note **`updated_at` is set
   equal to `locked_at`**, which is precisely the fingerprint observed in production.

Also present: `release_lock(job_id, token)` (token-checked, 258-266) and `release_stale_locks(300)`
(268-281). **There is no per-job lock renewal** — only the *worker* has a heartbeat — so a long
extraction's lock goes stale after 300 s and the job becomes claimable **again while still running**.

**What produced the 16:02:17.280227Z observation?** An identical sub-second `locked_at == updated_at`
on three rows in the same instant is the signature of **one `claim_next(limit=3)` call re-claiming
three previously stale rows** (all three had been claimed ~15:30:41-43, i.e. >300 s earlier). It is
**not** evidence of a successful retry, and it does **not** record worker identity (the claim stores
only a per-tick `lock_token`). Whether the claimant was a **fresh** worker (restart) or the **same**
long-lived process ticking again **cannot be distinguished from the data** — recorded as an unknown
(§20.1).

## 10. Timeout analysis — **no extraction upper bound (CONFIRMED)**

* `_extract()` (`services/automatic_processing.py:449`) calls **`extract_document(...)` at line 466 with
  no timeout wrapper**; the only timeout in the chain is `AI_FANOUT_TIMEOUT_S = 60.0` (line 172),
  applied to **AI fan-out calls only** (line 818).
* There is **no `asyncio.wait_for`, no `asyncio.timeout`, no worker-level extraction deadline** anywhere
  in the worker or extraction services (grep over `workers/automatic_processing.py`,
  `services/automatic_processing.py`, `services/automatic_extraction.py`,
  `services/extraction_fidelity.py`, `services/ocr*.py`, `pdf_engine.py` returns **only** the AI-fanout
  timeout).

**Direct answer to the key question — “can a job remain indefinitely in `processing/extracting` if
extraction hangs or the worker disappears?” → YES for a hang; recovery exists for a disappearance.**

* **Worker disappears** (crash/OOM/kill): the lock goes stale after 300 s and the job is **re-claimed**
  by the next claim call — resumability works, but **nothing is recorded** (no `last_error`, no
  `attempt_count` increment) because the failure occurs outside the process.
* **Extraction hangs inside a live process**: the job is re-claimed every ≥300 s but **never completes
  and never escalates**, because `attempt_count`/`max_attempts` are only exercised on *failure* paths
  (§12). This is an **uncovered failure mode, not an intended design** — the module docstring claims
  bounded re-runs, but a hang produces no bound.

## 11. OCR / PDF execution analysis (CONFIRMED event-loop hazard)

* Fallback chain (`services/automatic_extraction.py`): text layer → **tesseract** (`"tesseract_ocr"`)
  → `_render_pdf_pages_pypdfium` (**pypdfium2**) + **`_onnx_ocr` → `rapidocr_onnxruntime.RapidOCR`**
  (`"onnx_ocr"`, lines 290-364); the same for images (lines 521-530).
* These are **plain synchronous functions** (`def _extract_pdf`, `def _onnx_ocr`, …) and there is **no
  `to_thread` / `run_in_executor`** anywhere in `workers/automatic_processing.py` or
  `services/automatic_processing.py` (grep returns only `create_task`/`gather`).
* `_extract` is `async def` but calls that synchronous work **directly on the event-loop thread**
  (line 466). `RapidOCR()` construction is cached in a module global (`_onnx_ocr_engine`) and is
  expensive on first use (model load: CPU + memory).
* The tick runs **up to 3 such jobs concurrently** via `asyncio.gather` (worker line 160); the loop is
  single-threaded, so three CPU-bound synchronous extractions **serialise and block the loop**.

**Consequence (mechanism, source-confirmed):** while a PDF/OCR extraction executes, the same process
cannot serve HTTP or run other coroutines; when several run back-to-back — or one runs very long — the
process is **alive but unresponsive**, which is exactly the observed signature (**worker claims at
16:02:17Z while `/health` returns 502/503**). `_onnx_ocr` also swallows all exceptions by design
(“OCR fallback must never raise”), so an OCR failure surfaces as *unresolved* rather than as an error.

## 12. `attempt_count` semantics (CONFIRMED)

`attempt_count` is written **only** on these paths in `services/automatic_processing.py`: `…+1` at
lines **398**, **644**, **1041**, and passed through unchanged at line 358 — i.e. **failure/retry and
specific stage transitions**, **never on claim** (`claim_next` does not touch it) and **never by
stale-lock release**.

Production `attempt_count = 0` therefore means **“this job has never taken a failure/retry
transition”** — *not* “never claimed”, *not* “never extracted”, *not* “no retry”. The three stuck jobs
and the never-claimed job both read 0 for entirely different reasons, so `attempt_count` alone cannot
distinguish “hung” from “never started”.

`max_attempts` defaults to **3** (`data/document_processing.py:82,141`;
`domain/automatic_processing.py` `DEFAULT_MAX_ATTEMPTS`) and is reachable only through failure paths.
**A hang can never exhaust `max_attempts`, so dead-lettering is unreachable for hangs** — the job can
loop forever through 300-s re-claims with `attempt_count` frozen at 0.

## 13. Unclaimed-job analysis (`diff_edge_fuel.pdf`) — **CONFIRMED STARVATION**

`claim_next` orders candidates `ORDER BY created_at, id` (oldest-first) with `LIMIT batch_size = 3`,
and `stage='extracting'` rows stay claimable. At the 16:02:17Z claim the claimable set was exactly
**4 rows**: the 3 stuck `extracting` PDFs (created 15:30:41-43) and `diff_edge_fuel.pdf`
(`enqueued`, created **15:30:49** — the youngest). Oldest-first + cap 3 ⇒ the three older rows are
re-claimed and `diff_edge_fuel.pdf` is **never reached**. The never-claimed job is therefore explained
by **head-of-line blocking in the claim query combined with jobs that never leave `extracting`** — it
is not invisible to the worker, not filtered by tenant/status, and not an outage artefact.

## 14. Restart / recovery safety analysis

| Question | Answer (source-based) |
| --- | --- |
| Does the lock become stale? | Yes — after `stale_lock_seconds = 300`; released by the next claim call |
| Can another worker reclaim it? | Yes (`FOR UPDATE SKIP LOCKED` + stale release) |
| Can duplicate/concurrent extraction occur? | **Yes, in principle** — a long extraction whose lock expires becomes claimable while still running (no per-job renewal; only a worker heartbeat) |
| Is partial data overwritten? | Stage outputs are the idempotency markers (`if job.extracted_data: → mapping`), so a re-run resumes rather than restarting; `advance_stage` is token-scoped |
| Is evidence preserved? | Yes for persisted stages; **no** evidence is written if the process dies mid-extraction (`last_error` stays null) |
| Does `attempt_count` change on restart? | **No** — restart-driven re-claims leave it at 0 |
| Can the job become permanently stuck? | **Yes** — via a hang (no timeout, no escalation) or via repeated crash-restart cycles that always die before persisting |

## 15. Render / infrastructure evidence availability

**INFRASTRUCTURE EVIDENCE UNAVAILABLE.** No Render dashboard, API token, CLI session, log drain,
metrics endpoint or instance identity is accessible from this environment, and none may be discovered.
Specifically unavailable: deployment events/SHA, restart/OOM/termination reasons, health-check
failures, CPU/memory telemetry, worker stdout/stderr, DB connection/pool errors.
`rndr-id` remains a **per-request** identifier and is **not** an instance id (it was not used as one).
No explanation is manufactured to replace the missing telemetry.

## 16. Local reproduction

**No runtime reproduction was performed.** A faithful reproduction requires the disposable local stack
(`e2e/environment` Supabase + worker), which was outside this read-only task's scope and budget, and a
production-side reproduction is forbidden (§1). The findings in §10–§14 rest on **direct source
reading plus evidence-fit** — the identical-timestamp claim signature and the batch-cap arithmetic are
verifiable without execution. A minimal local reproduction is proposed as an *acceptance test* for the
remediation task (§22), not as a forensic requirement.

## 17. Confirmed facts

1. **Claim SQL**: oldest-first, `LIMIT batch_size(3)`, stale release (>300 s) inside each claim,
   `locked_at = updated_at = now` on claim; `blocked` not claimable. *(source, lines 216-256)*
2. **Worker**: poll 1 s, batch 3, `asyncio.gather` concurrency, heartbeat per tick, loop never dies,
   per-job exception → `mark_failed`. *(source, lines 57-175)*
3. **No extraction timeout**; only AI fan-out is bounded (60 s). *(source §10)*
4. **Synchronous PDF/OCR extraction on the event loop**, no executor offload. *(source §11)*
5. **`attempt_count` incremented only on failure/transition paths**, never on claim or stale release.
   *(source §12)*
6. **Hang ⇒ no escalation**: `max_attempts` unreachable, dead-letter cannot trigger. *(source §12)*
7. **The 16:02:17.280227Z triple lock is a single claim event** on three stale rows (identical
   `locked_at == updated_at`; matches the claim UPDATE signature). *(evidence-fit)*
8. **`diff_edge_fuel.pdf` starvation** is explained by oldest-first + cap-3 with 3 older claimable rows.
   *(evidence-fit)*
9. **The API is still unavailable ~12.5 h after onset** (04:40Z probes: 502/503; frontend 200).
10. **No production mutation** was performed (§24).

## 18. Supported conclusions

* The pipeline has **three genuine application-level robustness defects** that are independent of this
  incident's cause: **no extraction upper bound** (F1), **blocking synchronous extraction on the event
  loop** (F2) and **claim starvation** (F3); plus **F4** — **hangs are never escalated** to
  failure/dead-letter.
* The production state captured in `CT-STEP2-ACCEPT-011` is **fully consistent** with F1/F2/F4 (jobs
  re-claimed at 300-s intervals, `attempt_count` frozen at 0, `last_error` null — exactly what a hang
  or a pre-persist crash produces) and with F3 for the unclaimed job.
* It is **equally consistent** with a crash-restart loop (infrastructure/resource) that kills the
  process mid-extraction before any failure is persisted.

## 19. Unconfirmed hypotheses

* **H2′ (event-loop blocking as the incident cause):** synchronous pdfium + RapidOCR work blocked HTTP
  serving long enough for health checks to fail and the proxy to return 502/503. *Supported by:* worker
  alive (claim at 16:02:17Z) while HTTP died; the CPU-bound OCR path; 3-way `gather`; first-time
  `RapidOCR()` model load. *Not confirmed:* no logs/metrics.
* **H1 (auto-deploy triggered by the 15:23Z docs-only push):** *no* supporting measurement;
  `render.yaml` is absent and auto-deploy/branch are documented as NOT VERIFIED.
* **H3 (OOM / crash-loop):** plausible; would leave **no** job record (matches `last_error` null and a
  frozen `attempt_count`), but memory telemetry is unavailable.
* **H4 (Render platform incident):** cannot be excluded; no events available.

## 20. Unknowns

1. Whether the 16:02:17Z claim came from a **new** worker (restart) or the **same** long-lived process
   (no worker identity is persisted on the row).
2. Why the API has remained unavailable for ~12.5 h (crash-loop? failed deploy? OOM? platform event?).
3. Whether any OCR execution ever started/completed for `scan_light_gas.pdf` (`ai_extraction_method`
   is null; no logs).
4. Whether `extract_document` was **executing** or the process was **dead** at 16:02:17Z.
5. Whether duplicate concurrent extraction actually occurred at any point (possible per §14).
6. `layout_standard_fuel.pdf` completeness **0.33** — fixture-expected, or an extraction-quality
   regression?
7. Whether the 8 uploads contributed to the outage at all (temporal correlation only).

## 21. Is an application defect confirmed?

**Yes — application-level failure modes F1–F4 are confirmed by source code and evidence-fit**, and they
are defects regardless of this incident's cause:

| ID | Defect | Location | Expected invariant | Observed reality |
| --- | --- | --- | --- | --- |
| **F1** | No upper bound on extraction | `services/automatic_processing.py:449-474` | Every job attempt must be time-bounded | No `wait_for`/deadline; only AI fan-out (60 s) is bounded |
| **F2** | Synchronous CPU-bound extraction on the event loop | `services/automatic_extraction.py` (`_extract_pdf`, `_onnx_ocr`, `RapidOCR`) called from `async def _extract`; no `to_thread`/executor | HTTP serving must not be blocked by extraction | 3-way `asyncio.gather` of sync extractions can block serving |
| **F3** | Claim starvation (head-of-line blocking) | `data/document_processing.py:236-255` | Newly enqueued work must eventually be claimed | oldest-first + `LIMIT 3` + hung rows claimable ⇒ newest job starved |
| **F4** | Hangs never escalate | `data/document_processing.py` + `domain/automatic_processing.py` (`max_attempts=3`) | Unprogressing jobs must reach `failed`/dead-letter | `attempt_count` only increments on failure paths ⇒ a hang loops forever at 0 |

**Incident attribution is NOT established** — the 15:31Z onset and the ~12.5 h duration still require
Render telemetry (§15, §19).

Answering the task's §11 framing directly: the evidence supports a **combination of A and C** —
**A** (confirmed indefinite-stall failure modes exist in the worker/extraction implementation) and
**C** (the missing timeout/claim-expiry escalation is real, but the production incident prevented
proving that *it* caused the observed stall). It does **not** support **B** (the recovery mechanism
alone explaining the state) because recovery re-claims without progress and without escalation, and it
does not reach **D/E** because the source-level defects are demonstrable.

## 22. Proposed follow-up tasks (NOT implemented)

**`CT-STEP2-WORKER-TIMEOUT-013` — Bounded, non-blocking extraction with fair claiming**

* **Root cause:** F1 + F2 + F3 + F4 (above).
* **Affected code:** `backend/workers/automatic_processing.py` (tick/claim loop),
  `backend/services/automatic_processing.py` (`_extract`),
  `backend/data/document_processing.py` (claim ordering + attempt/expiry bookkeeping),
  `backend/services/automatic_extraction.py` (OCR/PDF call sites).
* **Proposed bounded fix (design only — not authorised here):**
  (a) wrap `extract_document` in a bounded deadline and treat expiry as a **failure transition** so
  `attempt_count` increments and dead-lettering becomes reachable;
  (b) run extraction in a worker thread/process pool so the event loop stays free;
  (c) add per-job lock renewal (or claim-expiry-aware in-progress guard) to prevent concurrent
  duplicate extraction;
  (d) make claiming fair so a newer job cannot be starved indefinitely behind hung older rows.
* **Required tests:** expiry escalates to `failed` after `max_attempts`; a hung extractor cannot block
  health/HTTP; a 4th job is claimed while 3 older jobs hang; duplicate-extraction guard.
* **Production verification requirement:** requires a healthy backend (currently unavailable).

**Still required (unchanged):** Render/infrastructure investigation for the ~12.5 h outage (deploy
events, restarts, OOM, logs) — see `P8-STEP2-PRODUCTION-API-INCIDENT-010.md` §24.

**Supporting (already proposed):** `CT-STEP2-WORKER-OBS-009` — worker/queue observability (the absence
of worker identity on the row and of a processing log trail is why §20.1/§20.4 are unanswerable).

## 23. Impact on Step 2 acceptance

`CT-STEP2-ACCEPT-007` **remains paused**. Nothing here clears the blocking condition: the API is still
unavailable, the three PDF jobs remain uncompleted, and a genuine defect class (F1–F4) now needs a
bounded remediation plus a healthy environment to verify. **No acceptance, no remediation and no
production change is authorised by this task.**

## 24. Statement of no production mutation

```
new documents = 0 · new jobs = 0 · requeues/retries/unlocks = 0 · new reports = 0
data mutations = 0 · storage mutations = 0 · RLS/config/queue/OCR/P1 changes = 0
Render restart/redeploy = none · code/tests/migrations modified = none
credentials printed/committed = none
```

Read-only actions performed: repository reading and `git` state queries; spaced read-only production
probes (≤10 requests, ≥8 s apart, no burst); earlier RLS-scoped `GET`/`SELECT` reads of the synthetic
tenant's own rows via the authorised synthetic Owner session (carried forward from `ACC-011` evidence
and re-verified health only in this task).

## 25. Final verdict

### `FORENSIC COMPLETE — APPLICATION DEFECT CONFIRMED`

Worker-stall status: **confirmed failure modes** (F1–F4) — the queue can hold a job in
`processing/extracting` indefinitely when extraction does not return, with no escalation to
`failed`/dead-letter, and the claim query can starve newer jobs behind hung ones.
Unclaimed-job status: **explained** (F3 starvation, not an outage artefact).
Outage relationship: **not established** (temporal correlation only; H2′ plausible, H1/H3/H4 not
excluded). Infrastructure evidence: **UNAVAILABLE**.

**Next gate (in order):** (1) Render/infrastructure investigation + recovery of the backend, (2) then a
bounded worker remediation (`CT-STEP2-WORKER-TIMEOUT-013`) with its tests, (3) then production
stability verification, and only then (4) resumption of `CT-STEP2-ACCEPT-007`.




