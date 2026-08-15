---
Document Type: Implementation Verification Audit
Project: CarbonTally
Architecture Decision: ADR-V3-004
Version: 1.0
Status: FINAL
Audit Mode: READ-ONLY
Created: 2026-08-14
Author: Cline
Related ADR: ADR-V3-004
---

# CARBONTALLY V3 — ADR-V3-004 IMPLEMENTATION VERIFICATION AUDIT

**READ-ONLY AUDIT — no files modified, nothing committed.**

## 1. Search Results (entire repository)

Searched: `backend/`, `tests/`, `docs/`, `scripts/`, `supabase/`, `frontend/`, `admin/`, `src/`, `tools/`, `database/`, `demodatagen/`, all config files, git history. Terms: `document_processing_queue`, `dpq`, `ADR-V3-004`, `/process/`, `/jobs/`, `job_id`, `producer`, `consumer`, `enqueue`, `claim`, `worker`, `background task`, `async processing`, `upload processing`, `workflow producer`, `Celery`, `RQ`, `huey`, `asyncio.create_task`, `BackgroundTasks`.

| What | Found |
|---|---|
| `document_processing_queue` in application code (Python/JS/TS) | **ZERO references** — no `INSERT`, `SELECT`, `UPDATE`, `DELETE`, `from_(`, `.table(`, `.insert(`, or raw SQL anywhere in `backend/`, `frontend/`, `admin/`, `src/`, `tools/`, `scripts/` |
| `document_processing_queue` references | Only in: SQL schema/migrations (`CarbonTally_DB_Schema_V3M2.sql`, `database/rc1|rc2/*`, `supabase/migrations/*`), pgdelta catalogs (`supabase/.temp/`), and **docs** |
| `dpq` | Only in: SQL schema (indexes `dpq_claim_idx`, FKs), docs, RC1/RC2 verification SQL |
| `/process/*` endpoints | **NONE** |
| `/jobs/*` endpoints | **NONE** — no `job_id` anywhere in code |
| Worker infrastructure | **NONE** — no `apps/` directory, no `supabase/functions/` (edge functions), no Docker worker services, no CI worker jobs, no Celery/RQ/huey/background-task code |
| `apps/workers` (Node 20) | Exists **only in `docs/Final_Kimi/...`** — an aspirational design for a different (Next.js monorepo) architecture; **no such directory exists in this repo** |
| `supabase/config.toml` | Only Supabase CLI defaults (`[edge_runtime] enabled = true` is the stock local-runtime toggle; **zero edge functions defined**) |

## 2. Producer Analysis — DOES A PRODUCER EXIST?

**NO.** No active or legacy code creates rows in `document_processing_queue`.

The only queue-row producers in the repository are for **other** tables:

| Producer | File | Table written | Active? |
|---|---|---|---|
| Upload/status routes | `backend/routes/upload.py`, `routes/customer_documents.py`, `routes/documents_main.py` | `organization_files`, `customer_documents`, **`manual_review_queue`** | Yes (legacy routes, imported by `main.py`) |
| Legacy monolithic copies | `backend/main copy.py`, `backend/main copy 2.py` | `manual_review_queue` (e.g. copy 2 line 1328, 2493; copy line 996, 2103) | **No** — orphaned files, **not imported** by `main.py` |
| v2.1 reports | `backend/data/reports.py` | `report_generation_queue` | Yes |
| v2.1 factor imports | `src/commands/*` | `emission_factors`, `import_batches` | Yes (CLI) |
| `processing_queue` | — | — | **Nobody** (dormant; Queue Audit §3.2) |

**Exact-insertion verification:** searches for `from_('document_processing_queue'`, `table('document_processing_queue')`, `insert('document_processing_queue')`, `INSERT INTO public.document_processing_queue`, `rpc('...process...'`, and the string in `.py`/`.jsx`/`.js` all returned **zero results**.

> **Correction to the ADR register's justification:** the ADR (line 378) says "only legacy monolithic copies wrote it." The legacy copies actually write **`manual_review_queue`**, not `document_processing_queue`. **No code in repository history has ever written dpq.** This is a minor inaccuracy in the ADR's *justification*, not a contradiction of its *decision*.

## 3. Consumer Analysis — DOES A CONSUMER EXIST?

**NO.** No worker/service/route claims, reads, or transitions dpq rows.

- No `FOR UPDATE SKIP LOCKED`, no claim loop, no `dpq_claim_idx`-matching query in any code.
- `dpq_claim_idx` (RC1/RC2 partial index) exists **in the schema** for a hypothetical worker that was never built.
- The only "*worker*" strings in the repo are `pdfjs.GlobalWorkerOptions.workerSrc` (browser PDF rendering) and `jest-worker` (node_modules) — not application workers.
- The v2.1 `WorkflowOrchestrator` (`engines/workflow.py`) is the closest concept, but it drives `customer_documents.status` + `domain_events` through `DocumentsRepository`/`EventsRepository` — **it does not read or write dpq**, and it is **not wired into `api/dependencies.py`** (the composition root) or any HTTP route.

## 4. `/process/*` and `/jobs/*` APIs

**NONE exist.** The only matching routes are admin **read-only log viewers** in `backend/routes/admin/logs.py`:

- `GET /processing` → `get_processing_logs` — reads `processing_logs` (no writes)
- `GET /processing/{log_id}` → `get_processing_log_detail` — reads `processing_logs`
- `GET /processing/file/{file_id}` → `get_processing_logs_by_file` — reads `processing_logs`
- `GET /processing/stats` → `get_processing_stats` — aggregates `processing_logs`

These are log-query endpoints, not job/ingestion endpoints. No request contract, no job creation, no pipeline invocation. The Traceability Matrix confirms: "`/process/pdf`, `/process/excel`, `/process/csv` upload endpoints (CT-ARCH-012 examples) — **not implemented**; document processing is engine-level only."

## 5. Complete Flow Trace

| Step | Status | Source |
|---|---|---|
| HTTP/API ingestion | **MISSING** | no `/process/*` / `/jobs/*` endpoint |
| Job creation | **MISSING** | no job table/code (`job_id` absent) |
| dpq producer | **MISSING** | zero dpq writes in code |
| dpq state | **LEGACY/INACTIVE** | table exists (init schema + RC1/RC2 hardening), never written |
| Worker/consumer | **MISSING** | no worker code anywhere |
| AI stage | **PARTIALLY IMPLEMENTED** | `engines/ai_extraction.py` (engine-level, not dpq-wired, not HTTP-wired) |
| Manual/QC/customer stages | **PARTIALLY IMPLEMENTED (legacy)** | `manual_review_queue` + legacy admin routes (`reviews.py`, `assignments.py`) + `customer_verifications` — active legacy human-queue surfaces, **not dpq** |
| Work Item interaction | **MISSING** (for dpq) / **LEGACY** (manual_review_queue) | no dpq↔WorkItem link |
| workflow/calculation | **PARTIALLY IMPLEMENTED** | `WorkflowOrchestrator` → extraction/AI/matching/calculation engines at **engine level only**; not exposed via HTTP; does not use dpq |
| completion/failure | **ENGINE-LEVEL ONLY** | `customer_documents.status` + `domain_events`, not dpq |

## 6. Test Analysis

| Test | Type | Proves dpq producer/consumer? |
|---|---|---|
| `tests/unit/engines/test_workflow.py` | UNIT | No — tests the orchestrator state machine over fakes |
| `tests/integration/test_workflow.py` | INTEGRATION | No — tests orchestrator against `customer_documents`/`domain_events` via repos; **no dpq** |
| `tests/integration/test_extraction.py`, `test_ai_extraction.py` | INTEGRATION (engine-level) | No — engine over document repo/events |
| Any dpq/producer/consumer/jobs test | — | **NONE FOUND** — zero matches for `dpq`, `document_processing_queue`, `enqueue`, `claim`, `job` in `tests/` |
| `20260807060000_add_dpq_workflow_columns.sql` (M7) | SCHEMA-ONLY | No — adds `workflow_error_count`/`workflow_next_retry_at` columns; schema, not implementation |

**No test proves a producer or consumer exists, because neither exists.**

## 7. Git History

Branch `main`, **8 commits** (from `.git/logs/HEAD`):

| Hash (new) | Message |
|---|---|
| `97e0f69` | Phase 0-2: CarbonTally Architecture Foundation |
| `a57c224` | Phase 3: Infrastructure Layer |
| `a13fd10` | Phase 4: Factor Matching Engine |
| `0a5a603` | Phase 5: Emissions Calculation Engine |
| `c5eadec` | **Phase 7: Document Processing and AI Extraction** (→ `DocumentExtractionEngine`/`AIExtractionEngine`, engine-level) |
| `e57543d` | **Phase 8: Workflow Orchestrator** (→ `engines/workflow.py`, engine-level, no HTTP wiring) |
| `8bcd490` | Fix integration test database isolation |
| `dbe72aa` (HEAD) | checkpoint: verified V2.1 and V3 database foundation |

No commit message references ADR-V3-004, dpq, producer, consumer, `/process`, `/jobs`, or job infrastructure. The uncommitted working tree (`tmp_git.txt`) contains the V2.1 Phase 9/10 code and V3 migrations/tests — **no producer/consumer/jobs code among them**. Classification: **A. never implemented** (there is no evidence of implementation-then-revert; nothing to revert).

## 8. Comparison Against ADR-V3-004

| ADR-V3-004 Requirement | Repository Evidence | Status |
|---|---|---|
| dpq retained as technical state machine | Table + RC1/RC2 CHECKs/claim index preserved; never deleted | **IMPLEMENTED** |
| dpq producer | Zero writes anywhere in code | **MISSING** |
| dpq consumer | No worker/claim code | **MISSING** |
| document work type | No active document work-type wiring (schema `document_types`/`document_type_categories` only) | **MISSING** |
| ingestion → dpq | No ingestion endpoint writes dpq | **MISSING** |
| AI stage | `AIExtractionEngine` exists (engine-level, not dpq-wired) | **PARTIALLY IMPLEMENTED** |
| manual stage | Active legacy `manual_review_queue` surface (not dpq) | **PARTIALLY IMPLEMENTED** (legacy) |
| QC stage | No dpq QC; legacy review surfaces only | **LEGACY/INACTIVE** (for dpq) |
| customer review stage | Legacy `customer_verifications`/`customer_documents` surfaces (not dpq) | **PARTIALLY IMPLEMENTED** (legacy) |
| Work Item interaction | No dpq↔WorkItem link; `manual_review_queue` is the de-facto Work Item store | **MISSING** (dpq) |
| retry/reprocessing | M7 columns on dpq schema; orchestrator retry at engine level; no consumer | **PARTIALLY IMPLEMENTED** |
| failure handling | Engine-level orchestrator failures; no dpq consumer failure path | **PARTIALLY IMPLEMENTED** |
| /process API | No endpoint | **MISSING** |
| /jobs API | No endpoint | **MISSING** |
| integration tests | Orchestrator/extraction integration tests exist; no dpq/jobs tests | **PARTIALLY IMPLEMENTED** |

## 9. ADR / Implementation Discrepancy

**The ADR register is NOT stale on its central claim.** ADR-V3-004's decision — "no active backend route produces dpq rows today; the final producer/consumer architecture is OPEN/DEFERRED" — is **correct and confirmed** by this audit. The product owner's belief that a Phase 8/9/10 producer/job architecture exists is **not supported** by any repository evidence.

One minor discrepancy in the ADR's *justification* (not its decision): the ADR says "only legacy monolithic copies wrote it." The legacy copies write `manual_review_queue`, **not** `document_processing_queue`. No code has ever written dpq. Recommendation: correct that parenthetical in the register when next touched — a documentation edit, not an architecture change.

## 10. FINAL VERDICT

# VERDICT A — ADR-V3-004 NOT IMPLEMENTED

### 1. Evidence
- Zero dpq INSERT/SELECT/UPDATE/DELETE references in any application code (backend, frontend, admin, src, tools, scripts).
- Zero `/process/*` and `/jobs/*` endpoints; the only `/processing` routes are read-only `processing_logs` viewers.
- Zero worker/consumer infrastructure: no `apps/`, no `supabase/functions`, no Docker/CI workers, no Celery/RQ/background-task code.
- `supabase/config.toml` contains only Supabase CLI defaults; no edge functions.
- Git history: 8 commits, none implementing ADR-V3-004; working tree adds only V2.1 Phase 9/10 + V3 DB work.
- The v2.1 `WorkflowOrchestrator` + extraction/AI engines exist at engine level but are **not HTTP-wired and do not use dpq** — they drive `customer_documents.status` + `domain_events`.
- Authoritative corroboration: `docs/audit/CarbonTally_V3_Queue_Architecture_Audit.md` §3.3 ("**no active backend route.** Legacy monolithic copies (E7) were the intended producers... no active v2.1 route found") and `docs/cline/CarbonTally-v2.1-Traceability-Matrix-v1.0.md` §9.3/§18.3 ("`/process/*` endpoints not implemented").

### 2. Files/functions
- Schema-only: `supabase/migrations/00000000000000_init_schema.sql` (dpq table), `20260807060000_add_dpq_workflow_columns.sql` (M7), `database/rc1/*`, `database/rc2/*` (`dpq_claim_idx`).
- Engine-level (not dpq, not HTTP): `backend/engines/workflow.py` (`WorkflowOrchestrator`), `backend/engines/extraction.py`, `backend/engines/ai_extraction.py`.
- Active human-queue producers (not dpq): `backend/routes/upload.py`, `routes/customer_documents.py`, `routes/documents_main.py`.
- Admin log viewers: `backend/routes/admin/logs.py` (`GET /processing*`).

### 3. Tests proving implementation
**None.** No test exercises a dpq producer, dpq consumer, `/process/*`, or `/jobs/*`. Existing workflow/extraction tests prove engine-level orchestration over `customer_documents`/`domain_events` only.

### 4. Git commits
`c5eadec` (Phase 7: document processing + AI extraction, engine-level) and `e57543d` (Phase 8: workflow orchestrator, engine-level) are the closest work — neither implements ADR-V3-004's producer/consumer or `/process`/`/jobs` surfaces.

### 5. ADR/implementation discrepancy
None material. The ADR's PROVISIONALLY DECIDED/OPEN-DEFERRED status is accurate. (Minor note: its "legacy monolithic copies wrote it" justification is imprecise — no code ever wrote dpq.)

### 6. Recommended NEXT ACTION
**Do not code.** The audit proves implementation is missing *and* the architecture is **not yet decided** — ADR-V3-004 explicitly retains the producer/consumer design as OPEN/DEFERRED behind the V3 document work type (which itself depends on ADR-V3-003). The correct next step is:

1. **Resolve the ADR-V3-004 design decision** (producer/consumer architecture for the V3 document work type) in the Architectural Decisions Register — i.e., decide whether the dpq producer is the FastAPI backend (`WorkflowOrchestrator` wired to an ingestion route), a separate worker process, or deferred again — before any implementation.
2. **Correct the register's minor justification inaccuracy** (the "legacy monolithic copies wrote it" parenthetical).
3. Only after the decision is recorded as DECIDED should implementation proceed (ingestion → dpq producer → dpq consumer → `/process/*` + `/jobs/*`), per the sequencing already documented in `docs/cline/CarbonTally_Backend_V3_Migration_Plan_v1.0.md` §15 Step 9.

---

**This was an audit only. No code, database, migration, RLS, Storage, API, contract, test, or data was modified. Nothing was committed or pushed. Factor baseline unchanged (DEFRA 7,029 · SEAI 20 · TOTAL 7,049).**



