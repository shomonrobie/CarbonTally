# Phase 8 — Production Recovery Verification + Existing Synthetic Upload Read-Back

**Task ID:** `CT-STEP2-ACCEPT-011` · **Type:** RECOVERY VERIFICATION + CONTROLLED READ-BACK (read-only)
**Date:** 2026-09-17 · **Release:** `p8-release-reconciled` @ `9ac6560`
**Final verdict:** `ACCEPTANCE MUST REMAIN PAUSED`
**API:** **DOWN** at close (last verified 16:01Z, real-browser confirmed)

---

## 1. Task identity

Verify whether production recovered after the `CT-STEP2-ACCEPT-010` incident, read back the **eight
existing** synthetic uploads in `Faria Green Company UK LTD`, recover acceptance evidence **without**
re-uploading anything, and decide whether `CT-STEP2-ACCEPT-007` may resume. Everything performed was
read-only; the synthetic credentials were used only at runtime via process environment and appear
nowhere in this report.

## 2. Incident context

`CT-STEP2-ACCEPT-010` recorded: Render 502/503 across all endpoints from ~15:31Z, frontend healthy,
cause unknown, Cloudflare challenge a **separate** condition, and the eight documents' post-upload
state unreadable. **This task's premise — "Production has now recovered" — is NOT confirmed.**

## 3. Git baseline

```
branch : p8-release-reconciled       HEAD : 9ac656063c25e8b5a04b241a7664bf228f2cb396
origin : 9ac656063c25e8b5a04b241a7664bf228f2cb396   (identical)
status : clean
lineage: 13cf6e5 → 1517588 → 61e7ba2 → 9ac6560
```
No code, test, migration, RLS or configuration change. No worktree modification.

## 4. Current API health — **DOWN (still)**

**Spaced curl probes** (browser User-Agent, 20–30 s apart, no burst):

| UTC | `/health` | `/api/v2/health` |
| --- | --- | --- |
| 15:58:20 | **502** (0 B) | **502** (0 B) |
| 15:58:46 | **503** (0 B) | 429 (CF challenge) |
| 15:59:07 | 429 (CF challenge) | 429 (CF challenge) |
| 15:59:28 | **502** (0 B) | **503** (0 B) |
| 16:00:00 | 429 (CF challenge) | 429 (CF challenge) |
| 16:00:20 | 429 (CF challenge) | 429 (CF challenge) |
| 16:01 (browser) | **502 then 503** (empty) | **503 then 503** (empty) |

* `/openapi.json` → **503** (empty body, i.e. not a CF page).
* **Zero HTTP 200 responses** from any backend endpoint in any probe.
* The **real-browser** probe (Chromium, which executes Cloudflare challenges) is decisive: for the
  two endpoints Cloudflare *passed through*, the origin returned **502/503 with an empty body** —
  therefore the failure is **at Render/origin, not an artefact of the curl path**.
* The outage now spans **~15:31Z → 16:01Z+ (~30 minutes)** with no recovery observed at any point.

## 5. Frontend health — **HEALTHY**

`https://carbontally.co.uk` → **200** throughout (curl probes and browser). Bundle unchanged:
`/static/js/main.9febc8f0.js`, `/static/css/main.8f1cfa49.css`.

## 6. Authentication — **PASS**

Supabase password grant (the authorised synthetic account) → **HTTP 200**; the identity service is
unaffected by the Render outage. Session-scoped reads below were performed with that session's JWT.

## 7. Synthetic organization — **VERIFIED**

| Item | Value |
| --- | --- |
| Organization | **Faria Green Company UK LTD** — `8ae45e55-afa9-42f1-b4f9-f0225f9b98cd` |
| Role | **owner**, `is_active: true` |
| Organisation created | `2026-09-17T15:24:27Z` |
| Read model used | the app's own RLS-scoped tables (org-scoped, read-only) |

## 8. Eight-document manifest (existing — NOT re-uploaded)

Because the HTTP API was unavailable, the read-back used the app's **own RLS-scoped persisted
state** (`organization_files` + `document_processing_queue`), which is tenant-scoped, read-only and
authorised by the synthetic Owner's session. **No document was re-uploaded, re-queued, retried,
modified or deleted.**

| # | File | Document ID | `organization_files.status` | Uploaded (UTC) |
| --- | --- | --- | --- | --- |
| 1 | `mock_uk_fuel_card_messy.csv` | `5178640c-39dc-48f5-a1c4-cbb704e2e9ee` | uploaded | 15:30:33 |
| 2 | `mock_uk_utility_bill.csv` | `a9b07e05-37ca-4a83-aad3-beb5cf7eaeb6` | uploaded | 15:30:36 |
| 3 | `mock_scope3.csv` | `31b61ab8-b311-4948-8508-420260368454` | uploaded | 15:30:36 |
| 4 | `layout_standard_fuel.pdf` | `cbfc3072-5699-4749-98c7-661bca064052` | uploaded | 15:30:37 |
| 5 | `layout_standard_elec.pdf` | `585e4345-5919-41cc-a8ef-319d02f41c71` | uploaded | 15:30:41 |
| 6 | `scan_light_gas.pdf` | `91acc68d-baa9-4cd2-9558-251cec01379e` | uploaded | 15:30:43 |
| 7 | `diff_edge_fuel.pdf` | `3e6dd5d9-0fac-472b-b38b-1b8ecc99fada` | uploaded | 15:30:49 |
| 8 | `multi_fuel.pdf` | `30f761c6-899d-450a-b744-87c389d6f972` | uploaded | 15:30:41 |

**All 8 documents are intact and still present in the tenant** — the outage did not lose data.

## 9. Document read-back — per-job persisted state

| File | Queue status | Stage | Attempts | `ai_extraction_method` | Confidence | Blocking reason / note |
| --- | --- | --- | --- | --- | --- | --- |
| `mock_uk_fuel_card_messy.csv` | **manual_review** | blocked | 1 | **`csv`** | **1** | no confident factor for `AdBlue` lines (per-line, `no_match`, confidence 0.00) |
| `mock_uk_utility_bill.csv` | **manual_review** | blocked | 1 | **`csv`** | **1** | no confident factor for `Natural gas` kWh / `nan` kWh rows |
| `mock_scope3.csv` | **manual_review** | blocked | 1 | **`csv`** | **1** | no confident factor for `Client meeting in Dhaka` GBP etc. |
| `layout_standard_fuel.pdf` | **manual_review** | blocked | **0** | *(none)* | — | **completeness 0.33 below 0.50 threshold — unresolved: quantity, unit** |
| `layout_standard_elec.pdf` | **processing** | **extracting** | 0 | *(none)* | — | locked `16:02:17.280227Z`; **stuck ≥ 30 min** |
| `multi_fuel.pdf` | **processing** | **extracting** | 0 | *(none)* | — | locked `16:02:17.280227Z`; **stuck ≥ 30 min** |
| `scan_light_gas.pdf` | **processing** | **extracting** | 0 | *(none)* | — | locked `16:02:17.280227Z`; **stuck ≥ 30 min** |
| `diff_edge_fuel.pdf` | **pending** | enqueued | 0 | *(none)* | — | enqueued 15:30:49, **never claimed** |

## 10. CSV results (all three) — extraction PASS; mapping blocked truthfully

**Pipeline state reached:** upload → persist → enqueue → claimed → extracted (`method=csv`,
`confidence=1`) → mapped (attempted) → **blocked at mapping** → `manual_review`.
No calculation snapshot was produced because mapping did not resolve — **the system did not fabricate
factors or emissions**, which is the correct behaviour, not a defect.

**`mock_uk_fuel_card_messy.csv` — expected F-02 regression values: FOUND.** The persisted extraction
contains, for `source_row: 1`:

```json
{"date":"01/10/2023","unit":"litres","amount":85.21,"activity":"Diesel",
 "quantity":53.8,"supplier":"Esso","source_row":1}
```

| Expected (per manifest) | Persisted production value | Match |
| --- | --- | --- |
| activity = Diesel | `Diesel` | ✅ |
| quantity = 53.8 | `53.8` | ✅ |
| unit = litres | `litres` | ✅ |
| amount = 85.21 | `85.21` | ✅ |
| supplier = Esso | `Esso` | ✅ |
| source_row = 1 | `1` | ✅ |
| extraction method | `csv`, confidence **1** | ✅ |

All five expected values (plus `source_row` and full extraction confidence) are recovered **from real
production data** — the F-02 regression is **PASS** on the production release.

`mock_uk_utility_bill.csv`: `method=csv`, confidence 1; consumption extracted in `kwh` with
`Natural gas` and `Electricity` recognised; several rows carry `activity: "nan"` (blank/NaN values in
the source fixture) which surfaced as `no_match` — recorded truthfully rather than invented.
`mock_scope3.csv`: `method=csv`, confidence 1; 4 line items with dates, quantities and GBP amounts
extracted with `source_headers` preserved; mapping blocked per line (travel/hotel/waste descriptions
have no factors) — expected for a Scope-3 narrative file.

## 11. PDF results

| File | State | Extraction |
| --- | --- | --- |
| `layout_standard_fuel.pdf` | manual_review (blocked) | completeness **0.33 < 0.50** → unresolved `quantity`, `unit`; **no fabrication, no crash** |
| `layout_standard_elec.pdf` | **processing/extracting (stuck)** | not completed |
| `multi_fuel.pdf` | **processing/extracting (stuck)** | not completed |

The **completeness gate behaved correctly** (blocked and explained rather than inventing a number),
which is genuine acceptance evidence for the validation stage. Note as an observation: a text-layer
invoice reaching only 0.33 completeness is a **quality signal** worth monitoring (§27), not a defect
established here.

## 12. Multi-line results

`multi_fuel.pdf` is still `processing/extracting` (locked 16:02:17Z) — **no line-candidate output
exists yet**, so multi-line coverage/ordering/line-identity evidence is **UNVERIFIABLE**. P1 was not
touched; its effective mode remains `shadow` (fail-safe default) and **no P1 activation was
performed or observed**.

## 13. OCR results

`scan_light_gas.pdf` (verified earlier as **no text layer**) is one of the three jobs **stuck in
`extracting`** with `ai_extraction_method: null`. Therefore:

* **`onnx_ocr` execution could NOT be confirmed** — `UNVERIFIABLE`.
* Whether OCR is the cause of the stall is **not established** (no logs); it is one of three stuck
  jobs, two of which are text-layer PDFs.

## 14. Difficult-document result (`diff_edge_fuel.pdf`)

Queue row exists (`pending`, stage `enqueued`, created 15:30:49Z) and the document is intact in
`organization_files` — **nothing crashed, was lost or fabricated** — but it was **never claimed** by a
worker (attempt_count 0, no lock), so extraction never ran: **UNVERIFIABLE** for extraction
behaviour; **PASS** for ingest integrity.

## 15. Queue state — **read successfully (persisted)**

8 queue rows = 1 per uploaded document (no duplicates, no orphans):

| Status | Count | Files |
| --- | --- | --- |
| `processing` / `extracting` | **3** | `layout_standard_elec.pdf`, `multi_fuel.pdf`, `scan_light_gas.pdf` (locked `16:02:17.280227Z`) |
| `manual_review` / `blocked` | **4** | the 3 CSVs + `layout_standard_fuel.pdf` |
| `pending` / `enqueued` | **1** | `diff_edge_fuel.pdf` |
| `completed` / `failed` / dead-letter | **0** | — |

`attempt_count` is **0** on all three stuck rows and on the never-claimed row; the rows that reached
manual review show **1**. `last_error` is **null** everywhere — nothing was recorded as an error,
which is why no `failed` state exists. The processing-log table contains **0 rows** for this tenant,
so there is no in-product log trail for these jobs.

## 16. Worker state — **ALIVE, but no job has completed**

Evidence the worker is running: three rows carry **`locked_at = updated_at =
2026-09-17T16:02:17.280227Z`** — a worker (re)claimed/refreshed those locks at 16:02:17Z, ~32 minutes
after they were enqueued and ~31 minutes after the API first failed. Two of the three were already
seen `processing` earlier, and the identical sub-second timestamp across all three indicates a
**single claim event touching three rows at once** — consistent with a worker start-up
**re-claim / stale-lock recovery** pass.

**But no job in this tenant has reached `completed`**, and the three in-flight jobs have not progressed
beyond `extracting` in ~32 minutes while `attempt_count` stays at **0**. The fourth job has never been
claimed. Worker *liveness* is therefore evidenced; worker *progress/completion* is not.

## 17. Processing state

| Stage | Reached | Evidence |
| --- | --- | --- |
| upload / persist | ✅ all 8 | `organization_files` (8 rows, `uploaded`) |
| enqueue | ✅ all 8 | `document_processing_queue` (8 rows) |
| claim | ✅ 7 of 8 (1 pending) | locks on 7 rows historically; 3 currently locked |
| extract | ✅ 3 CSVs (`method=csv`, conf 1); ❌ 5 PDFs | persisted `automation_extracted_data` |
| map | ✅ attempted (3 CSVs + 1 PDF), all `no_match` per line | `manual_review_reason` |
| validate | ✅ completeness gate fired (`0.33 < 0.50`) | `manual_review_reason` |
| calculate | ❌ 0 | no snapshots |
| complete | ❌ 0 | no `completed_at` |

## 18. Factor / calculation state — **no fabrication (correct behaviour)**

`calculated_emissions_kg_co2e`, `calculated_at` and `calculation_snapshot_id` are **null for all 8**
rows. Mapping produced **explicit line-level `no_match` reasons** (e.g. `AdBlue litres`,
`Client meeting in Dhaka GBP`) instead of silently choosing a wrong factor or inventing a number —
the intended precedence/refusal behaviour. No factor, mapping or formula was altered.

## 19. Manual-review state — **working and truthful**

4 of 8 jobs are `manual_review` / `blocked` with populated `manual_review_reason`: per-line factor
`no_match` reasons (3 files) and an explicit completeness-threshold reason
(`0.33 below 0.50 — unresolved: quantity, unit`). Per the task's own rule, a document that
legitimately requires manual review is **not** a defect: evidence is preserved, nothing is
fabricated, and the state is explained.

## 20. Report / lifecycle state — **UNVERIFIABLE**

No calculation snapshots exist, so no emissions/evidence/report rows can exist for these uploads;
and the HTTP API needed to read `/api/v3/reports` was unavailable. Report lifecycle remains
unexercised in production.

## 21. Outage impact on the eight uploads — **occurred DURING processing; partial impact**

| Phase | Time (UTC) | State |
| --- | --- | --- |
| Uploads + enqueue + CSV extraction/mapping | 15:30:33 – 15:30:58 | **all completed before the outage** |
| First API failure (502) | **15:31:22** | onset |
| PDF jobs in `extracting` | from ~15:30:41 | **still in `extracting` at ~16:03** |
| Worker (re)lock of 3 jobs | **16:02:17** | worker alive ~31 min after onset |

The outage began **after** the CSVs finished (their truthful manual-review outcomes were already
persisted) and **during/after** the PDF extractions. **No data was lost and nothing was fabricated.**
Causality (uploads → outage) is **not established** — only temporal correlation, now narrowed to the
**PDF extraction** jobs rather than "the 8 uploads" as a whole (§25).

## 22. Render evidence

**Render infrastructure evidence unavailable.** No dashboard, API token, CLI session or log stream
exists in this environment, and none may be discovered. Current deployment id, service state, restart
events, instance identity, CPU/memory/OOM metrics and the incident-window logs remain unobtainable.
The **product-side** evidence in §15–§17 (a live worker at 16:02Z, three stuck extractions, one
unclaimed job, empty processing logs) is new and material, but it is **not** a substitute for Render
telemetry. I do **not** claim the incident was infrastructure-caused merely because 503s were
returned.

## 23. Cloudflare separation — **CONFIRMED SEPARATE**

In one and the same real-browser session, `/health` and `/api/v2/health` returned **502/503 with an
empty body and no challenge**, while `/` and `/openapi.json` returned **429 "Just a moment…"**
challenge pages. Cloudflare decides per request, and the Render failures occur on requests Cloudflare
**passed through** — the two conditions are distinct, as recorded in `CT-STEP2-ACCEPT-010`. No burst
was issued; probe spacing was ≥20 s.

## 24. Data-safety verification

| Check | Result |
| --- | --- |
| New documents | **0** |
| New jobs / re-queues / retries | **0** |
| New reports | **0** |
| Data mutations | **0** (only `GET`/`SELECT`; no write verb was issued) |
| Storage mutations | **0** |
| The eight documents | **intact** (`organization_files`: 8 rows, `status=uploaded`) |
| Credentials | runtime env only; **absent** from this report, the evidence bundle and Git |
| Cloudflare / P1 / RLS / config / code / tests / migrations | untouched |

## 25. Incident assessment update

Building on `CT-STEP2-ACCEPT-010` (probe-level evidence only):

| Question | Updated assessment |
| --- | --- |
| API recovered? | **No** — 502/503 from 15:31Z through 16:01Z; real-browser confirmed |
| Was the failure edge-only (CF)? | **No** — failures occur on CF-passed requests (§23) |
| Was the process dead? | **No** — the worker (re)locked 3 jobs at **16:02:17Z**, ~31 min after onset, so a backend process is alive and doing queue work |
| What is failing? | The **HTTP serving path** at Render (502/503, empty bodies) while background queue work continues |
| Did processing complete? | **Partially** — 3 CSVs fully extracted + mapped (before onset); 5 PDFs never completed; 3 stuck `extracting`; 1 never claimed |
| Cause of the API failure | **STILL UNKNOWN** — no Render logs/events/metrics. Neither **H1** (auto-deploy restart) nor **H2** (workload/OCR resource pressure) can be confirmed; H2 now has more circumstantial support because the jobs that never finished are precisely the PDF/OCR extractions while the trivial CSV parses completed in seconds |
| Causality with the uploads | **NOT ESTABLISHED** (temporal correlation only) |
| New candidate defect (**not** a confirmed defect) | **Three jobs stuck in `extracting` ≥30 min with `attempt_count` still 0, lock re-acquired at 16:02:17Z, one job never claimed, `last_error` null and no processing-log rows.** If this recurs on a healthy service it indicates a **worker stall / missing extraction-timeout & claim-expiry escalation** (`attempt_count` not incrementing ⇒ no retry/dead-letter progression). Proposed investigation: **`CT-STEP2-WORKER-STALL-012`**. Root cause **unproven** — it may equally be a symptom of the platform condition. No remediation performed. |

## 26. Acceptance continuation decision

### `ACCEPTANCE MUST REMAIN PAUSED`

Each of the following is independently sufficient per this task's criteria:

1. **API remains unavailable** — 502/503 on every probe, real-browser confirmed (not a curl artefact).
2. **Existing data only partially readable** — persisted queue/extraction state was readable via the
   app's RLS model, but the HTTP read model, processing workspaces, previews, emissions and reports
   were not.
3. **An active production condition persists** — three jobs stalled in `extracting`, one unclaimed,
   API down, plus a candidate worker-stall condition to investigate.

Step 2 is **not** declared complete and `CT-STEP2-ACCEPT-007` is **not** resumed.

## 27. Remaining gaps

1. API availability at Render (blocks every remaining HTTP-based acceptance step).
2. Cause of the HTTP-serving failure (Render telemetry required).
3. Completion of the 5 PDF extractions, including whether `onnx_ocr` executes (§13) — unverified.
4. Multi-line line-candidate evidence (`multi_fuel.pdf`).
5. `layout_standard_fuel.pdf` completeness **0.33** — quality signal to monitor (expected for that
   fixture, or a text-layer extraction regression? **unproven**; needs fixture comparison).
6. Mapping `no_match` rates for `AdBlue`, Scope-3 narratives and `nan` activity rows — expected
   behaviour, but useful factor-coverage input for the product backlog.
7. Reports/lifecycle, organisation isolation (needs a second tenant), Consultant parity and P1 active
   multi-line remain unexercised.

## 28. Final verdict

### `ACCEPTANCE MUST REMAIN PAUSED`

Production has **not** recovered (**API DOWN**; frontend healthy). The eight synthetic documents are
**intact and partially readable**, and the read-back recovered genuinely valuable acceptance
evidence — above all the **F-02 fuel-card regression reproduced exactly in production**
(Diesel / 53.8 / litres / 85.21 / Esso / `source_row` 1, `method=csv`, confidence 1), correct
**completion-gate** behaviour (0.33 < 0.50 blocked rather than fabricated), truthful **per-line mapping
`no_match`** reasons, and **no fabricated emissions**. Against that: the **HTTP API is down**, the five
PDF extractions never completed, and a **candidate worker-stall condition** is recorded for
investigation (`CT-STEP2-WORKER-STALL-012`) with an unproven root cause.

No re-upload, retry, requeue, mutation, restart, redeploy or configuration change was performed.




