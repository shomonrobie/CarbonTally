# Phase 8 — Bounded Non-Blocking Extraction & Fair Claiming (F1–F4 remediation)

**Task ID:** `CT-STEP2-WORKER-TIMEOUT-013` · **Type:** IMPLEMENTATION (worker/extraction remediation)
**Date:** 2026-09-18 · **Branch:** `p8-release-reconciled`
**Verdict:** `IMPLEMENTED AND VERIFIED — READY FOR PRODUCTION DEPLOYMENT`
**Production deployment:** **not performed from this environment** (no Render deploy path available);
production remains separately affected by the still-unresolved incident — §19–§20.

---

## 1. Task identity

Implement a bounded remediation for the four application defects confirmed by
`CT-STEP2-WORKER-STALL-012` (commit `7d45b17`): F1 (no extraction upper bound), F2 (synchronous
CPU-bound extraction on the event loop), F3 (oldest-first cap-3 claim starvation), F4 (hangs never
escalate / no attempt accounting). Scope was held to the worker/extraction path; no wider
architecture redesign was attempted or required.

## 2. Starting Git baseline

```
branch : p8-release-reconciled
HEAD   : 7d45b171e6bf3c2d4e282f265a2dabba54549ab4  == origin/p8-release-reconciled
worktree at start: clean (no pre-existing modifications)
protected ~/carbon_tally: NOT touched
```
No reset, clean, stash, rebase, merge or overwrite of unrelated work was performed.

## 3. Forensic findings being remediated

| ID | Forensic finding (012) | Remediation |
| --- | --- | --- |
| F1 | `_extract` called the synchronous `extract_document` with no timeout; only AI fan-out was bounded (60 s) | Single authoritative budget `EXTRACTION_TIMEOUT_S` awaited via `asyncio.wait_for` |
| F2 | pypdfium2/RapidOCR/CSV parsing executed directly on the event loop (`async def` calling sync code); 3-way `asyncio.gather` | Engine dispatched with `asyncio.to_thread` |
| F3 | `claim_next` selected `ORDER BY created_at, id` `LIMIT 3` with stuck `extracting` rows still claimable ⇒ 4th job starved | Candidate predicate now requires `locked_at IS NULL` after the stale release |
| F4 | `attempt_count` incremented only on failure paths ⇒ a hang never escalated and looped forever | Timeout raises `TimeoutError` into the **existing** failure pathway (attempt accounting + dead-letter disposition) |

## 4. Implementation design

```
claim_next(limit, stale_after_seconds=300)
  1. release stale claims  (locked_at < now-300s -> locked_at = NULL)          [unchanged]
  2. candidates WHERE locked_at IS NULL ... ORDER BY created_at, id
                    FOR UPDATE SKIP LOCKED LIMIT batch_size                     [F3 fix]

worker tick (batch 3, asyncio.gather)
  per job -> _run_stage('extracting') -> _extract -> _run_bounded_extraction:
      await asyncio.wait_for(                                                  [F1]
          asyncio.to_thread(extract_document, content, name, mime,             [F2]
                            organization_id=job.organization_id),
          timeout=EXTRACTION_TIMEOUT_S)
      on expiry: raise TimeoutError("extraction exceeded the Ns execution budget")
  -> _run_stage except-block (EXISTING PATHWAY):
        mark_failed(last_error="TimeoutError: ...", attempt_count=job.attempt_count + 1)  [F4]
        => stage='failed', status='failed', locked_at=NULL   (leaves executing state, I5)
```

Design answers (task §5):

1. **Authoritative timeout** — `EXTRACTION_TIMEOUT_S` in `services/automatic_processing.py`: one
   location, units **seconds**, default **240**, override `CT_EXTRACTION_TIMEOUT_S`.
2. **Enforced in** `_run_bounded_extraction` (the single extraction call site).
3. **Covered:** the whole `extract_document` call — text-layer PDF, pypdfium2 render, Tesseract and
   `onnx_ocr` (RapidOCR) OCR, CSV/XLSX parsing. **Not** re-wrapped: the AI fan-out, which is already
   genuinely asynchronous and bounded by `AI_FANOUT_TIMEOUT_S = 60 s`.
4. **Off-loop:** `asyncio.to_thread` — a thread, not a new process pool/worker architecture.
5. **Recorded:** `last_error` = `TimeoutError: extraction exceeded the 240s execution budget` plus
   `attempt_count + 1`; bounded, no traces, no secrets.
6. **`attempt_count`** increments exactly where it already did for every other stage failure
   (`_run_stage` → `mark_failed`) — not on claim, not on stale release.
7. **Retry/dead-letter:** identical pathway to every other stage failure (§9).
8. **Stale recovery vs a timed-out worker:** the row is failed and unlocked before its lock can go
   stale, so it is never re-claimed as a stale claim.
9. **Claim skips busy jobs:** `locked_at IS NULL` after the stale release.
10. **Later jobs reached:** stuck rows leave the candidate set, so FIFO advances to them.
11. **Duplicate prevention:** the fresh-lock predicate + unchanged `FOR UPDATE SKIP LOCKED`; the
    240 s budget < the 300 s stale threshold means a live extraction is never deemed stale.
12. **Final failure:** dead-lettered (`stage='failed'`, not claimable) — it cannot loop.
13. **Evidence preserved:** the timeout path calls no writer with placeholder data; existing partial
    extraction / `last_error` / `manual_review_reason` values are untouched.

## 5. Changed files

| File | Change |
| --- | --- |
| `backend/services/automatic_processing.py` | `import os`; new documented `EXTRACTION_TIMEOUT_S`; new `_run_bounded_extraction` (`to_thread` + `wait_for` + truthful `TimeoutError`); `_extract` calls it (+75/−12) |
| `backend/data/document_processing.py` | `claim_next` candidate predicate requires `locked_at IS NULL`; docstring documents F3/I7/I8 (+22/−?) |
| `backend/tests/unit/services/test_worker_extraction_bound.py` | **NEW** focused regression tests (5) (+219) |

## 6. Timeout semantics

A timeout produces an explicit, truthful failure — never a success, factor mismatch, evidence gap,
manual review or calculation. Persisted state: `stage='failed'`, `status='failed'`,
`last_error='TimeoutError: extraction exceeded the 240s execution budget'`, `attempt_count` + 1,
`locked_at = NULL`. The reason text is bounded and contains no internals. The budget is deliberately
conservative and **not** tuned to any assumed Render resource size (task §6).

## 7. Event-loop safety (I2)

`extract_document` now runs in a worker thread. Verified by
`test_F2_blocking_extraction_does_not_block_the_event_loop`: while an 0.8 s blocking extractor runs,
an independent coroutine keeps being scheduled (≥5 heartbeats), i.e. HTTP-like responsiveness is
preserved. The task's warning is honoured explicitly — the fix does **not** merely wrap a synchronous,
event-loop-blocking call in an async timeout.

**Documented limitation (required by task §6):** cancelling the awaitable does **not** terminate
arbitrary synchronous work already executing in that thread. This is safe and leaks no ownership
because `extract_document` is a **pure** function — it returns a dict and writes nothing to the
database or storage; persistence happens only in the awaiting coroutine, which is no longer running
for that attempt. A timed-out job therefore cannot remain logically owned, and the orphan thread's
result is discarded rather than persisted.

## 8. PDF/OCR execution model

Behaviourally unchanged, positionally changed: text layer → Tesseract → pypdfium2 + RapidOCR
(`onnx_ocr`) now all execute inside the off-loop thread, with extraction results, page/line
provenance, P1 coverage and existing error handling preserved. The only change at the call site is
`to_thread` + `wait_for`; the `organization_id` argument that drives the tenant-scoped P1
allowlist/shadow decision is passed identically. The extraction engine itself was **not** modified,
and AI fan-out was **not** moved into a thread.

## 9. Retry / attempt / dead-letter semantics

```
claim → bounded extraction → (timeout | success | other failure)
      → failure accounting (attempt_count + 1) → stage='failed' (dead-letter, not claimable)
      → explicit re-enqueue to retry
```

The timeout participates in the **existing** model (no second retry counter, I6). Consistent with the
pre-existing design, `mark_failed` sets `stage='failed'`, so the row leaves the claimable set and a
hanging/failing job can never loop (I5). `max_attempts` is **not consulted** on this path — that is
the pre-existing contract for every stage failure (not introduced here); automatic retry-on-timeout
would be a **product decision**, recorded as a follow-up (§22), not improvised.

## 10. Claim fairness (F3 / I7)

`claim_next` now selects only rows that are **unlocked after the stale release**:

```sql
UPDATE ... SET locked_at = NULL, lock_token = NULL
  WHERE locked_at IS NOT NULL AND locked_at < $1;      -- stale recovery first (I9, unchanged)

WITH claimed AS (
  SELECT id FROM public.document_processing_queue
   WHERE (stage IN ('enqueued','ingesting','extracting','mapping','validating','calculating')
          OR (stage IS NULL AND status = 'pending'))
     AND locked_at IS NULL                             -- NEW: busy jobs are not fresh work
   ORDER BY created_at, id                             -- FIFO preserved
   FOR UPDATE SKIP LOCKED                              -- atomicity preserved
   LIMIT :batch_size
) UPDATE ... SET locked_at = $1, lock_token = $2, updated_at = $1 ...
```

A long/stuck job is claimed **once** and then leaves the candidate set, so FIFO order reaches the jobs
queued behind it — **three stuck jobs can no longer starve a fourth pending job**. Intentionally stale
jobs are still recovered (step 1); caller-applied tenant/status scoping is unchanged;
`FOR UPDATE SKIP LOCKED` was **not** removed; the worker does **not** skip old jobs blindly.

Evidence: `test_F3_claim_skips_freshly_locked_jobs_and_releases_stale_first` asserts the ordering
(release before select), `locked_at IS NULL`, `FOR UPDATE SKIP LOCKED`, `ORDER BY created_at, id`,
`LIMIT 3` and token binding. *The database-level assertion “3 locked rows + 1 pending ⇒ the pending
row is claimed” requires the local integration stack and is listed as a follow-up verification (§22);
the SQL contract above is the deterministic unit-level proof available here.*

## 11. Stale-lock semantics (I8)

The stale threshold (**300 s**) was **not** changed. The new extraction budget (**240 s**) sits
deliberately **below** it, so in the normal case a legitimately executing extraction can never be
treated as stale by another worker (no duplicate extraction). The relationship is documented **in
code** at the constant's definition, coupling any future change to either value. A future need for a
budget above 300 s would require per-job lock renewal — recorded as a follow-up (§22), not
implemented speculatively.

## 12. Restart recovery (I9)

Unchanged by design: a worker/process disappearance leaves `locked_at` in place, the next claim
releases it once older than 300 s, and the job is re-claimed. The only behavioural difference is that
a job being executed by a **live** worker is no longer re-claimed while it runs (F3 fix). No
production worker was killed or restarted; destructive restart simulation was not performed (no
disposable local stack available) and is listed as a follow-up verification (§22).

## 13. Partial-evidence preservation (I4)

The timeout path only calls `mark_failed`. It never calls `mark_blocked` or `advance_stage` with
placeholder data, so already-persisted partial extraction metadata, `manual_review_reason` and
`last_error` values are not overwritten.
`test_I4_timeout_does_not_overwrite_persisted_partial_evidence` asserts that no stage-writer call
carries extraction data on this path, and the stage's existing idempotent resume
(`if job.extracted_data: → mapping`) is unaffected.

## 14. P1 interaction (I12)

**No change.** The P1 classifier, coverage fan-out, shadow/controlled-rollout semantics and the
`organization_id` authorisation argument are untouched; the call site passes the same arguments.
P1 was not activated for any tenant and its fail-safe `shadow` default is unchanged.

## 15. Tests added / changed

New file `backend/tests/unit/services/test_worker_extraction_bound.py` (disposable fixtures only — no
database, storage or production resource):

| Test | Guards |
| --- | --- |
| `test_F1_a_never_returning_extraction_is_bounded` | F1/I1 — a never-returning extractor is bounded (0.2 s budget; elapsed < 3 s) and the reason names the budget |
| `test_F2_blocking_extraction_does_not_block_the_event_loop` | F2/I2 — ≥5 independent heartbeats during a blocking extraction; success result unchanged (I11) |
| `test_F4_timeout_reaches_the_existing_failure_pathway` | F4/I5/I6 — `mark_failed` with `attempt_count + 1` and a `TimeoutError` reason; **no** `mark_blocked`, **no** stage writer (I3) |
| `test_I4_timeout_does_not_overwrite_persisted_partial_evidence` | I4 — pre-existing partial extraction survives; no placeholder writes |
| `test_F3_claim_skips_freshly_locked_jobs_and_releases_stale_first` | F3/I7/I8/I9 — stale release precedes selection; `locked_at IS NULL`; `SKIP LOCKED`/FIFO/`LIMIT`/token preserved |

**No existing test was modified, weakened or deleted.**

## 16. Test results

| Run | Command | Result |
| --- | --- | --- |
| Focused (new) | `pytest tests/unit/services/test_worker_extraction_bound.py -v` | **5 passed, 0 failed** (6.5 s) |
| Targeted Step 2 / worker subset | `pytest tests/unit -q -k 'csv or xlsx or ocr or p1 or multi_line or enqueue or lifecycle or preview or extract or worker or claim'` | **exit 0**, 0 failures (~398 tests) |
| Full backend unit suite | `pytest tests/unit -q` | **exit 1 — exactly 5 failures, all pre-existing** (§17) |

## 17. Regression results

**The 5 full-suite failures are pre-existing and unrelated to this change — proven, not assumed.**
`test_p6_1b_membership_workspace_authorization.py` (2) and `test_review_sla_surfaces.py` (3) fail on
route-registration assertions (“expected a GET commercial (staff) route”, canonical ops SLA /
review-assign surfaces) — domains this task never touched. Proof of pre-existence: a **pristine clone
of `7d45b17`** (no working-tree changes) created via `git clone --shared` in `/tmp/ct_pristine`
produces the **identical 5 failures**; they are also deterministic (they fail in isolation, so this is
not an order-dependent artefact). No test was altered to obtain green results.

Frontend tests were **not** run: the change alters no API contract, response shape or frontend-visible
state (backend-internal worker behaviour only), per task §14.

## 18. Security / tenant-isolation verification

* No change to authentication, authorisation, RLS, policies, storage access or JWT handling.
* Org scoping around the claim is unchanged — the only added predicate is a **lock** check.
* No new endpoint, no new credential, no secret logging; the timeout reason contains only the budget.
* `organization_id` is still forwarded unchanged to the extraction engine (tenant-scoped P1 allowlist
  decision intact).
* No production data, storage object, queue row or configuration was modified by this task.

## 19. Deployment status

**Not deployed from this environment.** No Render deploy path is available here (no dashboard/API/CLI
session), and fabricated deployment status is forbidden. The code is committed and pushed to
`origin/p8-release-reconciled`, the normal release lineage for the controlled deployment path.
Production **remains unable to serve** (`/health` 502/503 during this task) — a separate, unresolved
infrastructure condition.

## 20. Production verification status

**NOT PERFORMED.** The live backend cannot serve requests, so the remediation could not be verified in
production: no live extraction, no live claim/fairness observation, no live timeout behaviour, and no
assessment of the historical incident. Verification is limited to §16–§17 and the design in §4–§14.

## 21. Known limitations

1. **Thread cancellation is not termination** — a timed-out extraction thread may still run to
   completion in the background (its result is discarded). Rare, non-persisting, but it consumes CPU
   until it finishes; bounding that would require process isolation (explicitly out of scope here).
2. **`max_attempts` is not consulted** on the timeout path (pre-existing behaviour for all stage
   failures): a timeout dead-letters rather than auto-retrying; re-enqueue remains the retry.
3. **Database-level fairness proof** (`3 locked + 1 pending ⇒ pending claimed`) needs the local
   integration stack; only the SQL contract is asserted in the unit suite.
4. **Restart/disappearance simulation** was not executed locally (no disposable stack available).
5. The **240 s** budget is a conservative default and is **not** validated against the largest real
   OCR document on production hosting — that cannot be tested while production is unavailable.
6. The **five pre-existing** unrelated full-suite failures remain (documented above, not fixed here).

## 22. Follow-up requirements

1. **PO/infra: resolve the Render incident**, then deploy this remediation through the normal
   controlled path and verify `/health`, worker heartbeat, a CSV and a scanned-PDF extraction.
2. Re-inspect the five jobs left by the incident (document IDs in
   `docs/cline/evidence/P8-STEP2-ACCEPT-007/` and the 011 evidence): with this fix deployed, unlocked
   rows are claimable again and any orphaned lock clears after 300 s.
3. Optional bounded task: **integration-level fairness test** in the disposable local stack.
4. Optional bounded task: **per-job lock renewal**, only if a budget above 300 s is ever required.
5. Product decision if desired: **automatic retry-on-timeout** bounded by `max_attempts`.
6. Unchanged proposals: `CT-STEP2-WORKER-OBS-009` (persist worker identity + a processing-log trail so
   stall attribution is answerable from product data) and the paused `CT-STEP2-ACCEPT-007`.

## 23. Final Git

| Item | Value |
| --- | --- |
| Implementation commit | **`0d14367`** — `fix(p8): bound extraction execution and stop claim starvation (F1–F4)` |
| Test commit | **`8a336a9`** — `test(p8): cover bounded extraction, timeout accounting and claim fairness` |
| Report commit | recorded in the task summary (report banked after the two code commits) |
| Push | `7d45b17..8a336a9 → origin/p8-release-reconciled` (verified) |
| HEAD vs origin | identical after each push |
| Worktree | clean; no unrelated files staged |

## 24. What was NOT changed

* P1 fidelity contract, classifier, coverage and shadow/controlled rollout — untouched (no activation).
* Factor matching, emission factors, calculation engine and formulas — untouched.
* Reporting lifecycle, disclosure, evidence/provenance contracts — untouched.
* RLS, policies, authentication, authorisation, tenant/consultant/client isolation — untouched.
* Billing, subscriptions, credits — untouched. Retention — untouched.
* Consultant functionality — untouched. Deferred Batch Upload — untouched.
* Extraction-engine internals (`services/automatic_extraction.py`) — not modified.
* Stale-lock threshold (300 s), worker batch size (3) and poll interval (1 s) — not modified.
* AI fan-out — not modified and not moved into a thread.
* No new queue architecture, process pool or external worker was introduced.

## Final verdict

### `IMPLEMENTED AND VERIFIED — READY FOR PRODUCTION DEPLOYMENT`

Code implemented and banked; focused regression tests green (**5/5**); targeted Step 2/worker subset
green (**0 failures**); full-suite failures limited to the **5 proven pre-existing, unrelated** ones;
Git banked and pushed with **HEAD == origin** and a clean tree. **Production deployment and production
verification were not possible from this environment** and remain gated on the separately unresolved
Render incident. This remediation addresses the **confirmed application-level worker/extraction
defects** identified by `CT-STEP2-WORKER-STALL-012`; the causal relationship between those defects and
the historical Render outage **remains unproven**.




