# CarbonTally WS4 — Gate 5 Final Acceptance Report
**Automated-Extraction Machine Provenance — REAL-STACK VERIFICATION-ONLY ACCEPTANCE RUN**

- **Date:** 4 September 2026
- **Git HEAD (verified):** `1639121` — no product code was changed and nothing
  was committed or pushed during this run.
- **Authorisation:** PO accepted the Gate-5 design/readiness report and tasks
  T1–T8 (all COMPLETE/ACCEPTED), then authorised this separate final acceptance
  run. Gate 4 remains PASSED/ACCEPTED and was not rerun.

---

## 1. Scope and authorization

**Gate 5 = Automated-Extraction Machine Provenance.** Verification-only run over
the nine acceptance scenarios plus security, Gate-4 regression, cleanup and exact
baseline restoration. The accepted Gate-5 implementation under test:
`document_processing_queue` (canonical automated-execution record) with
`automation_provider` / `automation_model` / `automation_model_version` (T1/T3),
T2 host-derived runtime attribution facts, T3 worker capture (contributing AI vs
deterministic vs failed attempt truthfulness), T4
`automatic_processing:extracted` audit event with machine actor
`automatic_pipeline`, T5 typed API `automation` block, T6 DB write-once guard,
T7 regression, T8 readiness. **Gate 6 was not executed.**

**No product code, migration, RLS, D38/D39/D40, or Gate-4 changes were made.**

## 2. Environment

| Item | Value |
|---|---|
| Backend | Real FastAPI/V3 on `127.0.0.1:8050` (restarted this run via `uvicorn main:app` from `backend/`, loading the accepted build incl. T1–T6; lifespan starts the real automatic-processing worker) |
| Database | Real local Supabase/PostgreSQL (`DATABASE_URL` → `postgres`); `carbontally_test` mirror present |
| Auth | Real Supabase Auth (GoTrue `/auth/v1/token?grant_type=password`); personas created/removed via GoTrue admin (service role) |
| API | Real `https`-free HTTP API on `127.0.0.1:8050` (upload, processing jobs, review, retry) |
| AI runtime (Scenario 1/2/4) | The worker's real `infra/ai_runtime`/`LLMClient` path was enabled with `CARBONTALLY_AI_BASE_URL=http://127.0.0.1:9123/v1`, model `gpt-acceptance-2026-09-05`. **Note (disclosed):** the model-inference endpoint was a disposable local OpenAI-compatible responder (`/tmp/g5_ai_stub.py`) — the app-side code under acceptance (real HTTP LLM call, JSON parsing, unit normalisation, deterministic-wins merge, gates, DPQ persistence, audit) is the real unmodified application code; only the external inference response is stubbed. The stub returns a candidate JSON normally and HTTP 500 when the document text contains `ACCEPTANCE_FAILURE`. The stub was stopped after the run. |
| No mocks inside the app | The backend code under acceptance was never patched; unit-test fakes were not used for acceptance claims. |
| Worker | Real claim/process loop observed executing every fixture job (DPQ state transitions, automation capture, audit rows). |

## 3. Baseline (recorded before the run)

| Metric | Baseline |
|---|---|
| emission_factors | 7,049 |
| organizations | 975 |
| manual_extraction_items | 260 |
| manual_extraction_batches | 56 |
| work_item_assignments | 0 |
| conversations / messages / participants | 34 / 52 / 62 |
| notifications | 0 |
| E2E users/profiles | 0 / 0 |
| document_processing_queue (main) | 36 rows, all automation columns NULL |
| calculation_snapshots | 100 |
| migration files on disk | 49 |
| `supabase_migrations.schema_migrations` (main) | 46 |
| DPQ RLS / policy count | enabled / 4 |
---

## 4. Scenario 1 — Contributing AI (real pipeline)

Fixture org `a9242b81-ef62-5a96-afa1-f7f7f4aeb6ff` + disposable owner
`ws4gate5.owner@e2e.carbontally.local`. Uploaded a real PDF via the real API
(`POST /api/v3/uploads` → storage + organization_file + work item + durable DPQ
job). The deterministic text pass resolved only `activity` (completeness 0.33 →
below the auto gate), so the real worker invoked the AI engine; the stub returned
a full candidate (`Natural gas`, 1000, kWh, date, supplier) which was merged.

Durable DPQ record (job `e04ea683-048c-4e1b-9af5-29dc5fac5dc3`):

- `automation_provider = '127.0.0.1'` (T2 host-derived label, truthful)
- `automation_model = 'gpt-acceptance-2026-09-05'` (the configured/attempted model)
- `automation_model_version = NULL` (no version truthfully known)
- `pipeline_version = 'v3-auto-1.0'`, `attempt_count = 1`
- `source_item_id = '9694cade-0dd2-490f-b181-07171a4fbe2c'` (work item linkage)
- `metadata->ai_extraction`: `status=ok, method='ai:pdf_text', model=…, merged_confidence=1.0`
- `extracted_data` contains the AI-filled `line_items` (the deterministic pass
  supplied activity; AI contributed quantity/unit/date/supplier)

**Result: PASS** — the extraction result is associated with the correct automated
execution (job identity + source item) and the block is truthful. (Note: mapping
then blocked this specific fixture job because the local demo factor set has no
2025 `Natural gas` kWh match — this is unrelated to provenance; S1/S2 provenance
evidence was captured on the durable record and audit trail regardless, and the
full mapping→calculation chain was verified deterministically in Scenario 3.)

## 5. Scenario 2 — Automated-extraction audit event (real audit persistence)

DB evidence (`public.audit_trail`, append-only) for job `e04ea683-…`:

- `action_type = 'automatic_processing:extracted'`, `table_name =
  'document_processing_queue'`, `record_id = job id`
- `metadata->>'actor' = 'automatic_pipeline'` (machine label; no human/PE identity)
- `metadata->>'correlation_id' = job id`
- `new_data` (after) = `{method: 'pdf_text+ai:pdf_text', pipeline_version:
  'v3-auto-1.0', provider: '127.0.0.1', model: 'gpt-acceptance-2026-09-05',
  model_version: null, confidence: 1.0, attempt_count: 1,
  source_item_id: '9694cade-…', ai_status: 'ok'}`
- **No API key / secret present** in `new_data`, `metadata`, or the DPQ row
  (verified; the local key string appears nowhere in persisted metadata).
- No user/PE/role/principal was created for `automatic_pipeline` (see §13).

**Result: PASS.**

## 6. Scenario 3 — Deterministic automation (no false AI provenance)

Uploaded a fully-tabular electricity CSV (real API). Deterministic completeness
1.0 → the worker did **not** invoke AI. Job `c7239582-9b54-4ffe-b211-35b03e7e98f1`
reached `review`:

- `automation_provider = automation_model = automation_model_version = NULL`
- no `ai_extraction` metadata
- extraction audit event present with `method='csv'`, `ai_status=null`,
  `provider=null`, `model=null` — clearly distinguishing **automated processing**
  from **AI contribution**
- snapshot created (`fde1d6b8-727a-4054-84e9-c08d62b0315e`) with
  `source_item_id` = item and `performed_by` NULL (machine run; Gate-4 intact)
  and emissions-log row linked.

**Result: PASS.**

## 7. Scenario 4 — Failed AI attempt (not falsely contributing)

**4a – blocked durable failure:** uploaded a PDF whose text includes
`ACCEPTANCE_FAILURE`; deterministic completeness 0.33 → AI attempted, stub
returned HTTP 500 → job blocked (`manual_review`). Verified: `automation_*` all
NULL, `extracted_data` not persisted, no `automatic_processing:extracted` audit
row (no misleading evidence), `manual_review_reason` carries the durable AI
failure (`AI extraction failed: LLM API returned HTTP 500 …`).

**4b – deterministic proceed with attempted-model truthfulness:** uploaded a
deterministic-complete CSV carrying the failure marker with `prefer_ai`; the
worker invoked AI (real HTTP call), the attempt failed, and the job proceeded
deterministically to `review`. Verified: `automation_*` remain NULL (attempt ≠
contribution), the durable `metadata->ai_extraction` records `status='error'`
**with the attempted model id `gpt-acceptance-2026-09-05`**, and the audit event
carries `ai_status='error'`, `provider=null`.

**Result: PASS.**


---

## 8. Scenario 5 — Write-once integrity (real PostgreSQL)

Executed against the real main database on the Scenario-1 DPQ row (automation
populated) plus per-column semantics:

| Check | Result |
|---|---|
| Initial population (NULL→value) | PASS (observed in S1; also per-column version populate allowed) |
| Same-value update no-op | PASS |
| Overwrite provider rejected + unchanged | PASS (`check_violation`, write-once message) |
| Overwrite model rejected + unchanged | PASS |
| Clear to NULL rejected | PASS |
| Independent per-column semantics | PASS (NULL `model_version` populated while provider/model set; later overwrite of the now-populated version rejected) |
| T3 `COALESCE` compatibility | PASS (COALESCE over populated value keeps value, no error) |
| Unrelated DPQ update | PASS (`manual_review_reason` updated) |

**Result: PASS.**

## 9. Scenario 6 — Human-after-automation preparation (limited, Gate-6 NOT executed)

- Scenario-3 deterministic job: the **owner approved** the job via the real
  review API → `completed`; automation fields remained NULL/untouched.
- Scenario-1 AI job (blocked at mapping): the **owner retried** via the real API
  (human processing/save on the durable job) → `automation_provider` /
  `automation_model` remained **unchanged** (`127.0.0.1` /
  `gpt-acceptance-2026-09-05`), i.e. the automated provenance stayed
  independently recoverable and was not overwritten by a human action.
- DB-level write-once (Scenario 5) additionally guarantees any later write that
  would change a populated field is rejected.

**Result: PASS (Gate-5 invariant verified; Gate 6 not implemented or claimed).**

## 10. Scenario 7 — API provenance (real API)

On the real API for the Scenario-1 job:

| Caller | Result |
|---|---|
| Owning organisation owner | **200** — payload exposes typed `automation` = `{provider:'127.0.0.1', model:'gpt-acceptance-2026-09-05', model_version:'v1'}` (version populated by the S5 per-column test) |
| Unauthorised organisation (demo owner of another org, real sign-in) | **403** |
| Processing Entity staff (`pe-staff-1.demo@…`, real sign-in) | **403** |
| Unauthenticated | **401** |

No secret material is exposed in job payloads (only provider/model/version
identity). **Result: PASS.**

## 11. Scenario 8 — Source traceability

Verified chains on the real stack:

- **Source Document → Work Item → Automated Execution → Extracted Output →
  Audit Evidence**: uploaded document (`organization_files`) → work item
  (`manual_extraction_items`, id on the job as `source_item_id`) → DPQ job
  (canonical automated-execution record, `v3-auto-1.0`) → persisted
  `extracted_data` on the job → `automatic_processing:extracted` audit row
  (job-id entity/correlation).
- **Calculation compatibility (Gate-4 chain unchanged)**: Scenario-3 deterministic
  job produced `calculation_snapshot_id → calculation_snapshots` with
  `source_item_id` = the work item and `performed_by` NULL, plus an
  `emissions_logs` row linked to the snapshot. The accepted Gate-4 mechanism was
  not modified; its columns remain intact.

**Result: PASS.**

## 12. Scenario 9 — Legacy / truthfulness

- Pre-existing DPQ rows (all 36, non-fixture) remained untouched and all carry a
  NULL automation block — verified at the end of the run (no backfill, no
  fabricated historical provenance).
- Deterministic runs stayed NULL; failed AI attempts were never represented as
  contributing; only real contributing executions populated the block.

**Result: PASS.**

## 13. Security results

- `automatic_pipeline` is an audit **string label** only: no user, PE member,
  role, D38 assignee, or authorization principal was created (DB checks: no
  matching `staff_roles`, no `work_item_assignments` machine assignee, no auth
  user/principal).
- Machine provenance introduces no authorization path: cross-org and PE access
  denied (403) on the real API; unauthenticated 401.
- RLS posture unchanged: DPQ RLS enabled with the same 4 policies; no RLS or
  policy changes; no bypass.
- No secrets persisted: DPQ metadata and audit `after` blocks contain no API key
  or credential material (verified).

**Result: PASS.**

## 14. Gate-4 regression confirmation

Gate-4-critical provenance remained intact where touched by the Gate-5
scenarios: `calculation_snapshots.performed_by` and `source_item_id` columns
present and populated for human paths (unchanged); machine-run snapshots keep
`performed_by` NULL (correct — machine ≠ human actor); processing-origin and the
existing audit mechanism were not modified. The full Gate-4 matrix was not rerun
(as authorised).

**Result: PASS.**


---

## 15. Cleanup

All disposable fixtures were removed after evidence capture:

- Deleted 4 fixture DPQ jobs (S1 AI, S3 deterministic, S4a blocked, S4b
  proceed), 4 manual-extraction items, 1 auto-created "Uploads" batch for the
  fixture org.
- Deleted fixture `organization_files` rows and their storage objects (via the
  Storage API, after the DB-level storage guard required it).
- Deleted fixture calculation snapshots and linked emissions-log rows (the two
  machine-run snapshots created by S3/S4b).
- Deleted fixture audit rows (extraction audits + engine match/calculation
  events) by record/correlation identity, including all deterministic
  match/calculation correlation ids derived from the fixture job ids.
- Deleted notifications created for the disposable owner, the owner's
  organisation membership, the auth user (GoTrue) and its public-users mirror
  row, and the fixture organisation row.
- Stopped the disposable AI responder. The backend remains running (environment
  state unchanged otherwise).

## 16. Final baseline

Verified exactly (18/18 checks PASS):

emission_factors 7,049 · organizations 975 · manual_extraction_items 260 ·
manual_extraction_batches 56 · work_item_assignments 0 · conversations 34 ·
messages 52 · conversation_participants 62 · notifications 0 ·
DPQ 36 rows with all automation columns NULL · E2E users/profiles 0/0 ·
calculation_snapshots 100 · migration files 49 · schema_migrations 46 ·
no fixture DPQ/storage residue · no `automatic_processing:extracted` or
`automatic_pipeline` audit residue.

The accepted Gate-5 schema remains applied: the three `automation_*` columns and
the T6 `dpq_guard_automation_write_once` function/trigger are retained; DPQ RLS
(enabled, 4 policies) and Gate-4 columns (`performed_by`, `source_item_id`) are
intact.

## 17. PASS / PARTIAL / FAIL matrix

| # | Mandatory criterion | Result |
|---|---|---|
| S1 | Contributing-AI durable provenance (provider/model/version/job/source) | **PASS** |
| S2 | `automatic_processing:extracted` audit (actor, ids, after-block, no secrets) | **PASS** |
| S3 | Deterministic automation: NULL block, no false AI provenance, distinguishing audit | **PASS** |
| S4 | Failed AI attempt: durable failure + attempted-model truthfulness, never contributing | **PASS** |
| S5 | Write-once integrity (population, no-op, overwrite/clear rejection, per-column, COALESCE, unrelated update) | **PASS** |
| S6 | Gate-6 preparation: human save/approval never overwrites automation | **PASS** (Gate 6 not executed) |
| S7 | Real-API provenance: owner 200, cross-org 403, PE 403, unauth 401, no secrets | **PASS** |
| S8 | Traceability chain + Gate-4 calculation compatibility | **PASS** |
| S9 | Legacy/truthfulness: no backfill/fabrication | **PASS** |
| SEC | Security: no machine user/PE/role/D38/principal, RLS intact, no secrets | **PASS** |
| G4 | Gate-4 regression (performed_by/source_item_id/origin/audit intact) | **PASS** |
| CLEAN | Baseline restored exactly | **PASS** |
| NOCODE | No product code changed; nothing committed/pushed | **PASS** |

**Matrix total: 13/13 PASS · 0 PARTIAL · 0 FAIL.**

## 18. Findings

1. **Environment note (non-blocking):** the AI inference endpoint for S1/S2/S4
   was a disposable local OpenAI-compatible responder (disclosed in §2). All
   application code under acceptance (LLM HTTP client, JSON parsing, merge,
   gates, persistence, audit) is the real, unmodified implementation; no
   in-app mocks were used.
2. **Observation (non-blocking):** the Scenario-1 AI job could not be factor
   mapped on the local demo factor set (`Natural gas` kWh, 2025 → no match), so
   the job durably blocked at the mapping stage. This is unrelated to machine
   provenance (S1/S2 evidence is on the durable record + audit trail) and the
   full mapping→calculation chain was proven on the real stack via the
   deterministic electricity fixture (S3/S8). No product defect was identified.
3. No other findings.

## 19. Confirmation: no product code was changed

Confirmed. This acceptance run was verification-only. No product code,
migration, RLS policy, API, UI, D38/D39/D40, Gate-4, or workflow file was
modified. Git HEAD remains `1639121`; nothing was committed or pushed. (The only
artifacts created are disposable `/tmp` scripts and this report.)

## 20. Final verdict

All mandatory Gate-5 acceptance criteria PASS on the real stack, and the
database baseline was restored exactly. The accepted Gate-5 schema (three
`automation_*` columns + the T6 write-once guard) remains in place.

**GATE 5 — PASSED**

