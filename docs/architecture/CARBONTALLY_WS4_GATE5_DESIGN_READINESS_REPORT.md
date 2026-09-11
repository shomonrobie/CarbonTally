# CarbonTally WS4 — Gate 5 Design & Implementation-Readiness Report
**Automated-Extraction Machine Provenance — bounded architecture/design review**

- **Date:** 4 September 2026
- **Nature:** Design/readiness only — **no code, SQL, migration, RLS, API, UI,
  D38/D39/D40, workflow, architecture or commit/push changes were made.**
- **Git HEAD (verified):** `1639121`
- **Predecessors:** `CARBONTALLY_WS4_GATE5_READINESS_REPORT.md` (definition-blocked,
  superseded for the *definition* by PO ratification below), `CARBONTALLY_WS4_GATE4_FINAL_ACCEPTANCE_REPORT.md`
  (Gate 4 PASSED), `CARBONTALLY_WS4_GATE4_REMEDIATION_F1_F2_REPORT.md` (accepted).

---

## 1. PO-ratified Gate 5 definition

The PO has now ratified the remaining per-gate itemization of the authoritative
WS4 final-acceptance scheme (which previously grouped this work only as the
*"Fixture-level human/automated provenance matrix (Gates 4-6)"*):

| Gate | Ratified meaning | State |
|---|---|---|
| Gate 4 | **Human provenance matrix** — complete human-actor attribution matrix over a continuous fixture run | **PASSED / ACCEPTED** (unchanged; not reopened) |
| Gate 5 | **Automated-extraction machine provenance** — durable provenance for automated extraction/processing | **This design** |
| Gate 6 | **Human-after-automation attribution** — later human saves/approvals reference, but never overwrite, the automated actor | Not implemented; Gate 5 must be Gate-6 compatible |

**Gate 5 therefore requires the system to durably answer:**

> What automated execution produced this extracted/processed result?

preserving, where applicable and only where truthfully known: automated
execution/job identity, provider, model, model/version, execution/version
context, source work item/document, the resulting extraction/action,
audit/evidence linkage, and timestamp/execution context.

### Scope boundary (from the ratified task)

- Use existing CarbonTally provenance/audit mechanisms wherever possible. Do **not**
  invent a parallel provenance architecture.
- Automated provenance is **evidence of an automated execution**, never a human
  identity, and must **not** be added to any human assignment vocabulary (D38).
- **Human actor provenance ≠ automated execution provenance** (Gate 4 unchanged).
- Gate 6 is **not** implemented here; Gate 5 only establishes a mechanism that lets
  a later human action reference prior automated provenance without overwriting it.

---

## 2. Current automated provenance architecture (verified)

The automatic-processing pipeline is the Phase A / CL-56 durable pipeline:

```
upload (v3_documents) -> document_processing_queue job (durable, server-side)
  -> worker claim (FOR UPDATE SKIP LOCKED) -> ingest -> extract -> map -> validate
  -> calculate (immutable snapshot) -> review (customer/owner, D5) -> completed
  blocked = manual-review gate (human rework -> re-enqueue -> resume)
```

### 2.1 Durable job record — `public.document_processing_queue`

The job row **is** the durable execution + work record. Verified columns/state it
already persists:

| Provenance aspect | Where it lives today | Notes |
|---|---|---|
| Job identity | `id` (UUID, PK) | Canonical durable record id |
| Organisation | `organization_id NOT NULL` | Org-scoped |
| Source document / work item | `source_item_id` → `manual_extraction_items`; `metadata.document_id` → `organization_files`; `file_name` / `file_url` | Evidence-chain root link (also used by `calculation_snapshots.source_item_id`) |
| Resulting extraction | `extracted_data` (JSONB) + mirror on the manual-extraction item (`save_extracted_data(..., _SYSTEM_ACTOR)`) | Resume marker; idempotent skip when present |
| Resulting mapping | `mapped_data`, `emission_factor_used`, `ai_mapping_confidence` | Matching decisions incl. factor/factor_kind per line |
| Resulting calculation | `calculation_snapshot_id` → immutable snapshot | No-duplicate guard via deterministic request ids (`uuid5(job.id::calc::idx)`) |
| Execution/version context | `pipeline_version` (`"v3-auto-1.0"`); `attempt_count` / `max_attempts`; `reprocess_count`; per-stage `*_at` timestamps | Coarse pipeline version only |
| AI extraction metadata | `metadata->'ai_extraction'` (status/method/model/confidence/merged_confidence/processing_time_ms/unresolved); `ai_extraction_result` JSONB; `ai_extraction_method` (method stamp, **also used for pure-deterministic runs**); `ai_confidence_score`; `ai_extracted_at`; `ai_processing_time_ms` | Populated only when the optional AI engine ran; **no provider, no model/version** |
| Human uploader / re-worker | `created_by` (uploader), `updated_by` (human confirm/retry) | Distinct human attribution |
| Worker claim | `lock_token` / `locked_at` | Transient; cleared on release — not an execution id |

Files inspected (HEAD `1639121`):

- `backend/data/document_processing.py` — job repository; `create`, `claim_next`,
  `advance_stage`, `reenqueue`, `sync_item_data`, `complete_review`, `release_stale_locks`.
- `backend/domain/automatic_processing.py` — stage machine, `PIPELINE_VERSION`,
  `AUTOMATIC_PIPELINE`, confidence gates.
- `backend/workers/automatic_processing.py` — claim loop; builds the optional AI
  engine via `infra/ai_runtime.configured_ai_extraction_engine()`.
- `backend/services/automatic_processing.py` — stage execution; `_extract` /
  `_run_ai_candidate` build the `ai_meta`/method stamps and persist them on the
  extraction→mapping `advance_stage` call; `_SYSTEM_ACTOR` used only for the
  manual-extraction-item mirror sync.
- `backend/api/v3_automatic_processing.py` — `_job_payload` exposes `ai_extraction`
  from `metadata` (comment: *"Phase 2 — AI-extraction provenance (candidate step)"*);
  confirm/retry/review gates.
- `backend/api/v3_documents.py` — `create_document_and_enqueue` auto-enqueues the
  durable job on every upload.

### 2.2 AI extraction runtime (optional, env-gated)

- `backend/infra/ai_runtime.py` — engine is built only when
  `CARBONTALLY_AI_BASE_URL` + `CARBONTALLY_AI_API_KEY` + `CARBONTALLY_AI_MODEL` are
  set; otherwise `None` and the pipeline is purely deterministic. Credentials are
  never persisted.
- `backend/infra/llm_client.py` — exposes `.model` and `.base_url` (OpenAI/
  Anthropic-compatible chat-completions root); provider identity is derivable from
  `base_url`, but is **not** recorded today.
- `backend/services/ai_document_extraction.py` — returns candidate envelope with
  `method` (`ai:<text-layer method>`), `model`, confidence, unresolved fields; all
  failure paths return `error` envelopes (durable, never false success).
- Deterministic extractor `backend/services/automatic_extraction.py` returns
  `method` stamps (e.g. `pdf_text`, OCR/image path, tabular CSV/XLSX path) —
  the deterministic method is persisted in the (legacy-named)
  `ai_extraction_method` column even for pure-deterministic runs.

### 2.3 Audit trail and engine-level attribution

- `public.audit_trail` (V3 forensic) is **deny-by-default / append-only**,
  service-role-written; actor is carried as a **string** (`metadata->>'actor'`),
  not a user FK — see `backend/data/audit.py`, `backend/infra/audit_logger.py`,
  migration `20260831020000_audit_activity_immutability.sql`.
- The automatic pipeline itself writes **no audit rows** for stage transitions or
  extraction. Audit rows exist only from the engines it calls:
  - `FactorMatchingEngine._audit` → `factor_match:<status>`, actor
    `"matching_engine"`, correlation = deterministic match request id
    (`uuid5(job.id::map::idx)`).
  - `CalculationEngine._audit` → `calculation:completed`, actor =
    `performed_by` (human, Gate 4) **or `"calculation_engine"`** for automatic
    runs; correlation = deterministic calc request id (`uuid5(job.id::calc::idx)`).
- Both engine correlation ids are **derived from the job id**, so an audit entry
  can be joined back to its job today — but there is no direct job-id reference and
  **no extraction/job-level audit event**.

### 2.4 Calculation provenance (Gate 4, accepted)

- `calculation_snapshots.performed_by` (nullable `uuid -> auth.users(id)`) records
  the actual human actor for human-performed calculations; **NULL** for automatic
  runs. `calculated_by` remains the organisation context. `source_item_id` links
  the snapshot to the originating work item (F2 verified). Migration
  `20260905000000_gate4_actor_provenance.sql`.
- `CalculationRequest.performed_by` docstring (engine) states: *"None for
  automatic-pipeline runs (machine provenance is out of scope)"* — Gate 4 scope.
  `algorithm_version` (`DEFAULT_ALGORITHM_VERSION`) is stamped on every snapshot.
- The automatic service builds `CalculationRequest` **without** `performed_by`
  (correct — machine runs must not claim a human actor).

### 2.5 Existing provenance regression tests

- `backend/tests/unit/services/test_automatic_processing.py` —
  `TestPhase2AIDurableExtraction` already asserts that AI metadata
  (`status/model/method/merged_confidence`), `ai_processing_time_ms`,
  `ai_extraction_result`, and the `ai_extraction_method` stamp survive to the
  durable job; AI-failure paths are asserted durable/blocking.

---

## 3. Current gaps (what Gate 5 must close)

| # | Gap | Verified evidence |
|---|---|---|
| G1 | **Provider identity is never recorded.** Only the model identifier string is stored (JSONB) and only when an AI engine ran. The configured endpoint host (`LLMClient.base_url`) is available at runtime but discarded. | `ai_meta` in `_run_ai_candidate` carries `model` only; no provider field anywhere in DPQ/audit. |
| G2 | **Model/version is not a typed, durable, queryable field.** `model` lives inside two JSONB blobs (`metadata->'ai_extraction'`, `ai_extraction_result`); there is no explicit `model`/`model_version` column and no version concept beyond the model-id string and the static `pipeline_version`. | `_JOB_COLUMNS`, `advance_stage` parameters, API payload. |
| G3 | **No automated-execution audit event.** Stage transitions and extraction complete without any `audit_trail` row; only the downstream engines audit (indirect, deterministic-request-id correlation). The extraction execution that produced `extracted_data` is invisible in the audit trail. | No `log_action` call exists in `services/automatic_processing.py` or `workers/automatic_processing.py`; engines audit only. |
| G4 | **Deterministic/non-AI automation has no explicit machine attribution.** Deterministic runs record a method stamp (in the legacy-named `ai_extraction_method` column) and the static pipeline version, but there is no machine-actor audit label and no explicit "this result is deterministic-only, no model contributed" signal at the extraction boundary. | `_extract`: `method_stamp = method`, `metadata`/`ai_*` left NULL when `ai_meta is None`. |
| G5 | **Failed-AI-attempt attribution is incomplete/not fully truthful.** When an AI attempt is made and fails, the persisted error envelope records `"model": None` even though the model identifier actually attempted is known (`self._llm_client.model`), so the durable record cannot answer *"which model was attempted?"*. | Error envelopes in `_run_ai_candidate` / `ai_document_extraction.py` set `model: None`. |
| G6 | **No write-once enforcement for automated provenance.** Nothing in the schema or SQL prevents a future re-run (or an over-broad update) from overwriting the attribution of the extraction that produced the persisted `extracted_data`. Today the human gates happen not to touch `ai_*`, but the invariant is implicit only. | `advance_stage`/`reenqueue`/`sync_item_data` SQL; no guard exists. |
| G7 | **No provider/model/version surface in the API/evidence payload.** `_job_payload` exposes `ai_extraction` (from metadata) but no typed provider/model/version block that evidence/UI consumers can rely on. | `_job_payload` in `v3_automatic_processing.py`. |

---

## 4. Root cause of missing provenance

1. **Design intent deferred.** The Phase-2 AI-extraction scaffolding was deliberately
   introduced as a *"candidate step"* (see API comment and `_extract` Phase-2 block):
   provenance capture stopped at "persist whatever the AI engine reported", with no
   ratified requirement (until now) for a durable provider/model/version contract.
2. **Gate 4 deliberately scoped machine provenance out.** The accepted Gate-4
   remediation restricted itself to the human actor column
   (`calculation_snapshots.performed_by`, NULL for automatic runs) and explicitly
   documented that *"machine provenance remains out of scope."*
3. **The execution record conflates the job and the run.** `document_processing_queue`
   is both the durable work item and the only record of the automated execution; its
   provenance fields were treated as mutable stage outputs rather than write-once
   evidence, so no separate immutable execution-attribution block was ever created.
4. **Runtime configuration is not reflected into evidence.** The AI provider/model
   exist only in environment variables consumed to construct the engine
   (`infra/ai_runtime.py`); nothing maps that configured runtime identity into the
   durable job or audit contract at execution time.
5. **Auditing was added at the engine layer only.** Audit hooks were placed where a
   business outcome (match, calculation) exists; the extraction stage — the first
   automated value-producing step — was never given an audit boundary.

The pipeline is **not** broken; the provenance simply stops at "what the model string
was (sometimes), embedded in JSONB", and is neither provider-complete, typed,
audited at the extraction boundary, nor immutably guarded.

---

## 5. Proposed minimal canonical mechanism

**Design rule:** the durable job row (`document_processing_queue.id`) **is** the
canonical automated-execution record, and the extraction stage pass that first
persists `extracted_data` is the canonical automated execution for that output.
We extend that row with a small **write-once machine-attribution block** rather than
introducing a new table, because:

- the job row already carries the execution <-> output <-> source links (see 2.1);
- the extraction executes (and persists output) **once per job** in practice —
  resume markers make re-runs skip stages whose outputs already exist, so a
  per-attempt history table would model a case the current pipeline cannot produce;
- the new block inherits the existing DPQ authorization posture unchanged.

### 5.1 Canonical mechanism (one additive block on the durable job)

Three nullable, write-once columns on `public.document_processing_queue`:

| Column | Type | Semantics (truthful) |
|---|---|---|
| `automation_provider` | `VARCHAR(120)` NULL | Provider identity of the model that **contributed** to the persisted extraction output. Derived from the configured endpoint host at runtime (e.g. `openai`, `anthropic`, `openrouter`) — never fabricated. **NULL** = deterministic-only result, or no AI contributed. |
| `automation_model` | `VARCHAR(240)` NULL | Model identifier actually sent to the provider for the contributing AI pass (the engine's `model`). **NULL** = deterministic-only result. |
| `automation_model_version` | `VARCHAR(120)` NULL | Explicit provider/model version qualifier **only when one is truthfully known**; otherwise **NULL** (never fabricated, never guessed from the model id). |

Supporting semantics:

- **Contributing vs attempted (truthfulness rule).** The typed block records the
  provenance of the **persisted output**:
  - AI pass **merged** into the persisted `extracted_data` (AI `status: ok`,
    deterministic-wins merge) -> provider/model/version set; the method stamp
    `deterministic_method + ai:...` already persists in `ai_extraction_method`.
  - AI **attempted but failed** and the deterministic result alone was persisted ->
    typed block stays **NULL** (deterministic-only output); the failed attempt is
    recorded **with the attempted model id** in the existing
    `metadata->'ai_extraction'` / `ai_extraction_result` failure envelope (closes
    G5 by storing the model that was actually attempted, `status: error`, detail).
  - No AI engine configured / not invoked -> typed block NULL; deterministic
    provenance = method stamp + `pipeline_version` + machine audit label (5.3).
- **Write-once.** The block is written only by the extraction-stage advance that
  first persists `extracted_data`, using SQL that never overwrites non-NULL values
  (e.g. `automation_provider = COALESCE($n, automation_provider)`) and is never
  referenced by any human-save path (`reenqueue`, `sync_item_data`,
  `complete_review`, item workbench saves all leave it untouched). A lightweight
  `BEFORE UPDATE` guard trigger is an optional hardening task (T6) that makes the
  invariant database-enforced.
- **Legacy/unknown rows.** Pre-Gate-5 rows and deterministic rows keep NULL with no
  backfill and no fabricated metadata (truthful provenance). A NULL
  `automation_provider` is documented as *"deterministic-only or legacy/unknown"*.
- **Deterministic/non-AI automation** (design question 7) is therefore answered by
  method stamp + `pipeline_version` + engine algorithm versions already stamped
  (calculation `algorithm_version`), surfaced under a machine audit label — no model
  provider columns are abused for non-model automation.

### 5.2 Answers to the nine design questions

1. **Canonical automated execution identifier** -> the durable job row
   `document_processing_queue.id`, referenced everywhere (`source_item_id` chain,
   deterministic engine correlation ids, new audit row). Stage-level attempt
   context = `attempt_count` + `*_at` timestamps + deterministic request ids.
2. **Where provider/model/version persist** -> typed write-once block on the job row
   (5.1), mirrored into the audit `after` metadata of the extraction audit event
   (5.3), and surfaced through the existing job detail payload.
3. **Execution -> source work item/document** -> already exists and is unchanged:
   `source_item_id` -> `manual_extraction_items`, `metadata.document_id` ->
   `organization_files`, `file_url`/`file_name`.
4. **Output -> execution** -> already exists and is unchanged: `extracted_data` /
   `mapped_data` / `calculation_snapshot_id` live on the same row as the execution;
   snapshots link back via `source_item_id`.
5. **Audit-trail reference** -> new additive extraction audit event (below); existing
   engine audit rows already correlate to the job via deterministic request ids —
   unchanged.
6. **Later human action references automated output without overwriting** -> the
   write-once block stays intact across human rework (`confirm` / `sync_item_data` /
   `reenqueue` write human corrections to `extracted_data`/`mapped_data` and stamp
   `updated_by` with the human id, never the automation columns). Gate 6 can then
   show: original automated attribution preserved **plus** human
   `performed_by`/`updated_by`/item-save actor alongside it.
7. **Deterministic/non-AI automation** -> no provider/model (NULL block); machine
   actor audit label + method stamp + `pipeline_version` + engine algorithm
   versions; no assumption that every automated process is an AI model.
8. **Provider/model metadata unavailable** -> NULL columns + truthful audit fields;
   error-attempt envelopes record the attempted model id and failure detail; no
   fabricated metadata ever.
9. **Legacy automated records** -> untouched, NULL block, no backfill; documented via
   column comments.

### 5.3 Extraction audit event (machine actor, append-only)

One additive `AuditLogger.log_action(...)` call at the end of the extraction stage
(after the job row persists `extracted_data`):

```
action          = "automatic_processing:extracted"
entity_type     = "document_processing_queue"
entity_id       = job.id
correlation_id  = job.id
actor           = "automatic_pipeline"      # machine label — NOT a user id,
                                            # never enters D38/human vocab
after           = { method, pipeline_version, provider, model, model_version,
                    confidence, attempt_count, source_item_id, ai_status }
```

`audit_trail` is append-only and deny-by-default; the entry is service-role-written,
best-effort (audit failure never breaks the job), exactly like the existing engine
audit calls. This gives the audit trail a direct, immutable job-id reference to the
automated extraction execution (closes G3/G7) without any audit schema change.

---

## 6. Exact tables / columns / services that would change

> Nothing below has been applied. This is the *design* of the smallest consistent
> change set, for later bounded implementation tasks (see 12).

**Database — one new additive migration (name suggested for the sequence after
`20260905000000_gate4_actor_provenance.sql`):**

- `public.document_processing_queue`
  - `ADD COLUMN IF NOT EXISTS automation_provider VARCHAR(120)`
  - `ADD COLUMN IF NOT EXISTS automation_model VARCHAR(240)`
  - `ADD COLUMN IF NOT EXISTS automation_model_version VARCHAR(120)`
  - `COMMENT ON COLUMN ...` (NULL = deterministic-only or legacy/unknown; write-once;
    never a human identity; no D38 interaction)
  - optional hardening (T6): `BEFORE UPDATE` guard function/trigger
    `dpq_guard_automation_write_once` that rejects changes to non-NULL
    `automation_*` values (applied to main + test DBs, idempotent).
- **No new table** (existing row carries the requirement; see 5).
- **No RLS change** (see 9).
- **No data migration / no backfill** (truthfulness for legacy rows).

**Backend services/domain:**

- `backend/infra/ai_runtime.py` (or a tiny helper beside it) — expose a truthful
  `provider_label(base_url)` (host-derived) and the engine's model/version facts;
  no secrets, no config additions.
- `backend/services/automatic_processing.py` — build the attribution block in
  `_extract`/`_run_ai_candidate`; pass `automation_provider/model/model_version`
  into the extraction->mapping `advance_stage` call; include the attempted model id
  in AI-failure envelopes (G5); fire the 5.3 audit event after the persisted
  advance.
- `backend/domain/automatic_processing.py` — add the machine-actor constant
  (`AUTOMATION_ACTOR = "automatic_pipeline"`) and document the provenance contract
  (no version bump to `PIPELINE_VERSION` is required by this change).
- `backend/data/document_processing.py` — extend `advance_stage` parameters/SQL for
  the three write-once columns (`_JOB_COLUMNS`, mapper fields); ensure no other
  method writes them.

**API (observability only, no new route):**

- `backend/api/v3_automatic_processing.py` — `_job_payload` adds a typed
  `automation` block (`provider`, `model`, `model_version`) beside the existing
  `ai_extraction`, so evidence/UI consumers can read the durable contract.

**Tests** — see 11.

---

## 7. Migration required?

**Yes — exactly one, additive and idempotent** (6). It adds three nullable columns
(plus comments and, optionally, the write-once guard trigger) to
`public.document_processing_queue`. It must be applied to **both** the main/local
Supabase schema and the dedicated integration-test database mirror (as the Gate-4
migration was), and verified with the existing migration-count/column checks before
any Gate-5 fixture run. No new table, no backfill, no destructive change; Gate-4
columns (`performed_by`, `source_item_id`) untouched.

---

## 8. Audit / evidence integration

- **Audit:** the new 5.3 extraction event lives in the existing append-only,
  deny-by-default `audit_trail`, written service-side through the existing
  `AuditLogger` (best-effort, never raises into the job). It joins the pipeline's
  two existing engine events (`factor_match:*`, `calculation:completed`) whose
  correlation ids already derive from the job id. The machine actor is a **string
  label**, exactly like today's `"matching_engine"` / `"calculation_engine"` /
  `"system"` labels — no user-identity semantics, no FK, no D38 vocabulary change.
- **Evidence chain (unchanged, now machine-annotated):** the existing chain
  Source Document -> `manual_extraction_items` (source_item_id) -> DPQ job ->
  snapshot -> emissions already resolves through the job row; adding the typed block
  to that row makes the automated provenance reachable wherever the job detail is
  visible, without touching the evidence-domain model.
- **Gate-4 compatibility:** the human-actor mechanism (`calculation_snapshots.performed_by`,
  engine `performed_by` fallback to `"calculation_engine"`) is **not modified**.
  Automatic runs still leave `performed_by` NULL; the machine attribution is a
  separate, additive evidence block — the required distinction
  **human actor provenance != automated execution provenance** stays explicit.

---

## 9. Security / RLS implications

- **No new authorization path.** Automated provenance rides on the existing DPQ
  table and job-detail API. All access continues to require
  `ensure_processing_org_access` (org member / internal staff / active-consultant
  grant); PE staff remain **denied** on this surface; cross-org reads remain
  impossible; no new endpoint is added.
- **No RLS policy change.** `document_processing_queue` access is governed by the
  existing server-side authorization model used by the whole Phase-A pipeline
  (backend service-role + per-request org checks); the new columns inherit it
  unchanged. No client can write the job row directly, and the optional guard
  trigger additionally prevents any future over-broad UPDATE from rewriting a
  non-NULL automation block.
- **Secrets stay out.** Only the provider host label, model id and optional version
  are persisted — never the API key, base URL, prompt text, or document content
  (consistent with `infra/ai_runtime.py`/`ai_document_extraction.py` rules).
- **No cross-tenant or cross-PE leakage.** The typed block is org-scoped by the row;
  no new relationship or FK exposes it to another organisation, consultant, or PE.
- **Machine actor is not an identity.** `"automatic_pipeline"` (audit string) is not
  a user id, is never inserted into `performed_by`, D38 assignee fields, or any
  human-assignment vocabulary.

---

## 10. Gate 6 compatibility

Gate 5 deliberately leaves the door open for Gate 6 (human-after-automation
attribution) without implementing it:

- The write-once automation block is **referenceable but not rewritable**: after a
  human reviews/corrects automated output and confirms
  (`confirm_job`/`sync_item_data`/item workbench saves), the machine block still
  answers *"what the automated execution originally produced"*, while the human
  action is recorded through the existing human mechanisms (`updated_by`,
  item-save actors, and — for recalculation — snapshot `performed_by`).
- The audit trail will contain both the extraction event (machine actor) and any
  later human action events, ordered by time — the raw material Gate 6 needs for
  the chain:
  `Source Document -> Automated Execution (machine block + audit) -> Extracted Value
  -> Human Review/Correction (human actor) -> Mapping/Validation -> Calculation ->
  Snapshot -> QC -> Approval`.
- No Gate-4 or D38/D39/D40 semantics are altered, so Gate 6 remains a verification
  gate (plus any *separately ratified* small additions) rather than a rework of the
  provenance model.

---

## 11. Regression-test strategy

| Layer | Tests |
|---|---|
| Unit — extraction provenance | Extend `backend/tests/unit/services/test_automatic_processing.py` (`TestPhase2AIDurableExtraction`): assert typed `automation_provider/model/model_version` on the durable job for a successful AI merge; assert **NULL** block for deterministic-only runs; assert method stamp + `pipeline_version` present; assert failed-AI attempt now records the attempted model id with `status: error` while the typed block stays NULL. |
| Unit — write-once | Assert re-advance/re-enqueue/`sync_item_data` never changes a non-NULL automation block (with and without the guard trigger); assert human confirm stamps `updated_by` only. |
| Unit — audit | Fake audit sink: extraction stage emits `automatic_processing:extracted` with `actor="automatic_pipeline"`, `entity_id=job.id`, `correlation_id=job.id`, and the attribution `after` block; audit failure does not break the job. |
| API — positive/negative | Job list/detail returns the typed `automation` block for the owning org; cross-org detail denied (403); PE user denied; confirm/retry/review authorization unchanged. |
| DB — migration | Columns exist in main + test DBs with comments; NULL for legacy rows; no backfill occurred; Gate-4 `performed_by`/`source_item_id` untouched; migration idempotent (re-run is a no-op); RLS posture unchanged. |
| Gate-5 fixture (later, verification-only) | A disposable automated-extraction fixture (deterministic and, if configured, AI) asserting job + audit + API provenance, following the Gates 1-4 matrix/evidence conventions, with exact baseline restoration. |

No change to the accepted Gate-4 regression matrix is required; the new assertions
are additive.

---

## 12. Implementation work breakdown (small bounded tasks)

Each task is independently testable; none touches D38/D39/D40, RLS, workflow
semantics, or the Gate-4 actor mechanism.

1. **T1 — Migration.** Additive `automation_provider/model/model_version` columns +
   comments (+ optional write-once guard trigger) on `document_processing_queue`;
   apply to main and test DBs; add DB regression checks.
2. **T2 — Runtime attribution facts.** `infra/ai_runtime.py` provider-label helper
   (host-derived) exposing provider/model (and optional version) without secrets;
   unit test.
3. **T3 — Capture in the worker path.** Extend
   `services/automatic_processing.py` (`_extract`/`_run_ai_candidate`) and
   `data/document_processing.advance_stage` to persist the write-once block on the
   extraction->mapping advance; include the attempted model id in AI-failure
   envelopes.
4. **T4 — Extraction audit event.** Add the 5.3 `AuditLogger` call after the
   persisted extraction advance (best-effort, machine actor).
5. **T5 — API surface.** Add the typed `automation` block to `_job_payload`; update
   module docstring/comments.
6. **T6 — Write-once hardening (optional but recommended).** DB guard trigger +
   tests proving automation columns are immutable once set.
7. **T7 — Regression suite.** Unit (extraction provenance, write-once, audit) + API
   positive/negative tests; run the full backend unit suite; confirm the
   pre-existing unrelated integration-suite failures are unaffected (documented,
   out of scope).
8. **T8 — Verification-only Gate-5 fixture run** (separate phase, after
   implementation is tested): disposable automated-extraction fixture + full
   evidence conventions (terminal/DB/API checks), exact baseline restoration, and
   a Gate-5 acceptance report — mirroring the Gate-4 re-run procedure.

---

## 13. Risks / open questions

| # | Risk / question | Handling |
|---|---|---|
| R1 | Provider identity from `base_url` host is an approximation (custom gateways/proxies). | Store the derived host label; never a fabricated canonical name. If PO later wants a configurable display label, that is a small config addition (implementation decision, not a Gate-5 blocker). |
| R2 | Model version is usually not separately exposed by providers; the model id may embed a version. | `automation_model_version` stays NULL unless truthfully known; the full model id is recorded in `automation_model`. No parsing heuristics that could fabricate a version. |
| R3 | Re-runs that genuinely re-execute extraction (failure before any output persisted) would overwrite the block unless guarded. | Write-once SQL + optional trigger (T6) make first-write-wins; attempt context is retained in `attempt_count` and the failure metadata. |
| R4 | The legacy-named `ai_extraction_method` column also carries deterministic method stamps. | Kept as-is (no rename — would churn consumers); documented. A rename would be out of scope. |
| R5 | Stage timestamp semantics are approximate (`extracted_at` is stamped on *entry* to extracting; `mapped_at` on the extraction->mapping advance). | Not part of Gate 5's acceptance; flagged as an observation. The AI execution window is already captured precisely by `ai_extracted_at`/`ai_processing_time_ms`. |
| R6 | Whether a **machine audit label** such as `automatic_pipeline` should also be attached to the existing `calculation:completed` entries for automatic runs. | Optional additive follow-up for Gate 6 clarity; **not** required for Gate 5 (would touch the Gate-4-adjacent audit call and is deliberately left out of the minimal change). |
| Q1 | Does the PO require provider/model provenance for the **OCR** and deterministic text-extraction engines too (beyond method stamps)? | Current design records method stamp + pipeline version for deterministic stages; per-engine version strings would be additive if later requested. |
| Q2 | Should the typed block be surfaced in a UI evidence panel now? | Not required by the ratified scope (API/job/audit contract). UI presentation is out of scope unless separately ratified. |

---

## 14. Explicit out-of-scope items

- Any code, SQL, migration, RLS, API, UI, D38/D39/D40, workflow or architecture
  change **in this task** (design only).
- Gate 6 (human-after-automation attribution) implementation and its verification
  fixture.
- Reopening or modifying the accepted Gate-4 human-actor mechanism
  (`calculation_snapshots.performed_by`, engine actor fallback).
- D38 assignment vocabulary/architecture changes; batch-vs-item semantics; PE
  security boundary; QC independence; customer-approval separation.
- D40 entity-assignment notifications (already recorded as not a Gate-5 blocker).
- New database tables, new API routes, new audit tables, new event types.
- Backfilling or fabricating provider/model/version for legacy automated records.
- Renaming existing columns (`ai_extraction_method`, etc.).
- AI provider accounts, keys, config, or any secret handling.
- Fixing the pre-existing unrelated integration-suite failures (documented, not
  part of this workstream).
- Any commit or push.

---

## 15. Readiness verdict

**GATE 5 IMPLEMENTATION READY**

- The PO-ratified definition (Gate 5 = automated-extraction machine provenance) is
  precise enough to implement without inference.
- The smallest architecture-consistent mechanism is an **additive write-once
  machine-attribution block on the existing durable job row**
  (`automation_provider` / `automation_model` / `automation_model_version`),
  a machine-actor **extraction audit event** in the existing append-only
  `audit_trail`, a typed API surface addition, and regression tests — one additive
  migration, no new table, no RLS change, no D38/D39/D40 change, no Gate-4 change.
- Truthfulness rules are defined for deterministic automation, unavailable
  metadata, failed AI attempts, and legacy rows (no fabrication, no backfill).
- Gate 6 compatibility is preserved: later human actions reference the automated
  block without overwriting it.
- No architecture decision beyond the PO ratification is required to proceed.
- **Nothing was implemented, changed, committed, or pushed in this task.**

### Status of the preceding definition blocker

`CARBONTALLY_WS4_GATE5_READINESS_REPORT.md` recorded **GATE 5 DEFINITION BLOCKED**
and explicitly noted machine/provider/model provenance as *out of scope for Gate 5
as currently specified*. The PO's ratification of Gate 5 = automated-extraction
machine provenance **resolves that definition blocker** and brings that theme into
scope; this report is the resulting implementation-ready design.

---

## Appendix — files inspected (HEAD `1639121`)

- `backend/workers/automatic_processing.py`
- `backend/services/automatic_processing.py`
- `backend/services/automatic_extraction.py`
- `backend/services/ai_document_extraction.py`
- `backend/domain/automatic_processing.py`
- `backend/data/document_processing.py`
- `backend/api/v3_automatic_processing.py`
- `backend/api/v3_documents.py`
- `backend/infra/ai_runtime.py`
- `backend/infra/llm_client.py`
- `backend/infra/audit_logger.py`
- `backend/data/audit.py`
- `backend/engines/calculation.py`
- `backend/engines/factor_matching.py`
- `backend/data/emissions_logs.py`
- `backend/tests/unit/services/test_automatic_processing.py`
- `supabase/migrations/00000000000000_init_schema.sql`
- `supabase/migrations/20260800000000_rc2_schema.sql`
- `supabase/migrations/20260807060000_add_dpq_workflow_columns.sql`
- `supabase/migrations/20260829000000_v3m9_durable_automatic_processing.sql`
- `supabase/migrations/20260831020000_audit_activity_immutability.sql`
- `supabase/migrations/20260905000000_gate4_actor_provenance.sql`
- `docs/architecture/CARBONTALLY_PHASE5_WS4_FINAL_ACCEPTANCE_REPORT.md`
- `docs/architecture/CARBONTALLY_WS4_GATE4_READINESS_REPORT.md`
- `docs/architecture/CARBONTALLY_WS4_GATE4_FINAL_ACCEPTANCE_REPORT.md`
- `docs/architecture/CARBONTALLY_WS4_GATE4_REMEDIATION_F1_F2_REPORT.md`
- `docs/architecture/CARBONTALLY_WS4_GATE5_READINESS_REPORT.md`
