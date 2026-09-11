# CarbonTally — Original Processing Model Reconciliation

**Prompt Ref:** `CT-P6-2D-MODEL-RA-20260910-001`
**Response Ref:** `CT-P6-2D-MODEL-RA-20260910-001-R`
**Date/time:** 10 September 2026, approx. 17:05–17:36 local (Asia/Dhaka +0600)
**Task type:** READ-ONLY architectural / domain-model reconciliation
**Implementation:** NONE · **Schema changes:** NONE · **Migration:** NONE · **PO decisions made:** NONE

---

## 1. Executive Summary

The Product Owner's foundational model — *Organizations, Consultants, CarbonTally
and Manual Processing Entities can all participate in processing PDF and
CSV/Excel data, using automatic or manual processing where authorised, with
automatic/manual being a dimension separate from who performs it* — **is already
represented in the repository**, but it is expressed through **four different
mechanisms under different names**, and one element of the pending P6-2D
terminology (`D7b` — adding a `CONSULTANT` value to `processing_origin`)
**contradicts what `processing_origin` actually means**.

Evidence-backed findings:

1. **Actor dimension** — the four actors exist and are enforced by distinct
   surfaces: `/api/v3/processing/*` (organisation members, active-grant
   consultants, internal staff), `/api/v3/ops/*` (internal staff),
   `/api/v3/pe/*` (Processing Entity staff, assigned work only) and
   `/api/v3/qc/*` (CarbonTally QC).
2. **Processing mode** — automatic vs manual **already exists as an independent,
   explicitly actor-agnostic predicate**: `api/processing_mode.py`
   (`item_is_automatic`, the "P1 containment" classification), fail-closed, plus
   the durable job `stage`/`status` vocabulary. Its docstring states it is
   derived and temporary and that the **final provenance architecture is the D7
   workstream** — i.e. D7 is already designated as the home of mode provenance.
3. **Input type** — `services/automatic_extraction.py` classifies and extracts
   **PDF** (text → Tesseract OCR → ONNX fallback), **CSV**, **XLSX/XLS** and
   images; `file_type` is carried on the durable job. Input type is independent
   of actor, mode and state.
4. **Automatic → manual fallback is implemented**: extraction completeness below
   0.5 and mapping confidence below 0.6 route the job to `blocked`
   (`blocked → manual_review`), the item stays MANUAL under the P1 predicate, a
   human corrects it in the item workbench, and `POST /jobs/{id}/confirm`
   re-enters the pipeline. The organisation UI (`customer/ProcessingPage.jsx`)
   shows exactly this loop ("Document uploaded - automatic processing has been
   enqueued", retry, confirm).
5. **`processing_origin` does NOT mean "who processed" and does NOT mean
   "automatic vs manual".** It is documented as the immutable
   **internal-vs-PE manual-processing capacity / control-path selector**
   (`CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` §4: *"Internal or PE?"*),
   derived from the batch assignment carrier, that drives stage routing
   (`calculated → review` vs `calculated → pe_review`) and which upstream QC
   controls apply. **D7b as framed would conflate actor domain with processing
   channel and would require changing the origin CHECK constraint, the
   origin→stage routing and the origin's QC-control meaning.**
6. **Provenance** records the *human actor* (`extracted_by`, `qc_by`,
   `customer_reviewed_by`), the factor (`emission_factor_used`, `factor_kind`,
   `customer_factor_id`) and the snapshot/log (`calculated_by`, `performed_by`,
   `source_item_id`) — **but not the acting consultant's firm** (D7's real gap)
   and not the processing mode (only derivable via the P1 predicate).
7. **Entitlement** is organisation-owned and is checked at consultant submission
   (D6, non-charging) and charged at customer approval — unchanged by the model
   clarification.

**Verdict: `CLARIFICATION REQUIRED — PO RATIFICATION BLOCKED`** — scoped to the
`D7b` item only. `D6` is safe as-is; `D7` is safe once worded as *firm
provenance* rather than anything touching `processing_origin`; `D7b` must be
withdrawn or re-defined by the PO before ratification of the D7 family.

## 2. Scope and Read-Only Constraints

- Read-only: no code, schema, migration, RLS, permission, billing, workflow or
  configuration change was made.
- No new `processing_origin` value was introduced (explicitly prohibited).
- No product decision was made; clarifications are proposed as questions.
- Authoritative architecture/roadmap/register documents were **not** modified.
- Two deliverable documents were created (this report + the mandatory
  prompt-history record). No other file was touched.

## 3. Sources Inspected

**Authority:** `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` (manual
processing capacity, lines 497 and 1349); `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`
(§9 Phase 6, §12 dependencies, §14 authority map);
`CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` (§3 paths, §4 processing-origin
model, origin→stage routing, queues, backfill);
`CARBONTALLY_PHASE6_CONSULTANT_WORKFLOW_READINESS_REPORT.md` (§12 capabilities,
§13 provenance, §27 workstreams); `CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md`
(§7 billing, §8 provenance, §13 sequence); `CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`
(§15 entitlement, §16 provenance, §19 invariants); `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`
(D1–D11 + P6-2C ratified entries);
`docs/cline/CARBONTALLY_PHASE6_REMAINDER_UNIFIED_READINESS_ANALYSIS.md`;
`docs/cline/CARBONTALLY_P6_2C_INDEPENDENT_VERIFICATION_REPORT.md`.

**Backend/domain/data:** `api/processing_mode.py`, `domain/processing_origin.py`,
`domain/automatic_processing.py`, `domain/workflow.py`, `domain/partners.py`,
`data/manual_extraction.py`, `data/document_processing.py`, `data/emissions_logs.py`,
`data/audit.py`, `services/automatic_processing.py`, `services/automatic_extraction.py`,
`services/work_items.py`, `services/billing.py`, `api/v3_processing_workflow.py`,
`api/v3_automatic_processing.py`, `api/v3_documents.py`, `api/v3_operations.py`,
`api/v3_pe.py`, `api/operations_auth.py`, `api/consultant_auth.py`.

**Frontend:** `frontend/src/v3/customer/ProcessingPage.jsx`,
`…/customer/ProcessingItemWorkspace.jsx`, `…/consultant/ConsultantItemPage.jsx`,
`…/ops/ExtractionPanel.jsx`, `…/ops/PEEntityItemPage.jsx`,
`…/ops/OperatorItemPage.jsx`, `…/v3/api.js`.

## 4. Original Processing Model — Evidence

The Blueprint states the foundational capacity model explicitly:

> "CarbonTally may maintain its own internal Data Processing / Extraction
> department and may perform the same manual extraction and processing work that
> is assigned to external PEs. **PEs are additional controlled processing
> capacity, not the exclusive source of manual processing.**"
> — Blueprint V1.3, l.497 (repeated l.1349)

and the pipeline is documented as:

```
UPLOAD → INGEST → EXTRACTION → MAPPING → VALIDATION → CALCULATION
      → EVIDENCE → REVIEW/APPROVAL → REPORTING
```

Implementation confirms the model end-to-end:

| Model element | Implementation evidence |
|---|---|
| Any authorised actor can start processing | `POST /api/v3/processing/documents/{file_id}/enqueue` — `require_auth` + `ensure_processing_org_access` ("Org-scoped; internal staff and active-consultant grants pass") |
| Automatic processing exists for PDF **and** CSV/Excel | `services/automatic_extraction.extract_document(content, filename, mime)` with `_classify` → pdf / csv / xlsx / xls / image, and dedicated `_extract_pdf`, `_extract_csv`, `_extract_xlsx` |
| Manual processing exists for the **organisation** | `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` ("uses the /api/v3/processing/* surface (never the staff /api/v3/ops/* endpoints)") with Extract / Map / Validate / Calculate tabs and status gates; backend `…/items/{id}/extract|map|validate|calculate` |
| Manual processing exists for **consultants** | `frontend/src/v3/consultant/ConsultantItemPage.jsx` reusing `ExtractionPanel`; same `/processing/*` routes via active grant + capability |
| Manual processing exists for **CarbonTally internal** | `/api/v3/ops/items/{id}/start|extract|map|validate|calculate`, `/ops/queues/operator`, `/ops/next-item`; `OperatorItemPage.jsx`, `ExtractionPanel.jsx` |
| Manual processing exists for **Processing Entities** | `/api/v3/pe/items/{id}/start|extract|map|validate|calculate|pe-review|pe-qc` (`require_pe_member`, assigned-work scoped); `PEEntityItemPage.jsx` |
| Fallback when automatic cannot resolve | confidence gates + `mark_blocked` + `/jobs/{id}/confirm` (see §10) |
| Durable state, not a spinner | `document_processing_queue` job with `stage`/`status`/`attempt_count`; `domain/automatic_processing.py` |

**Conclusion:** the PO's clarification is a statement of what the repository
already implements; it is **not** new scope.

## 5. Actor Model (Q1)

| Actor | Category | Authorization / role mechanism | Surface |
|---|---|---|---|
| **Organisation** (customer) | data owner + processor | membership in the organisation; owner/admin vs member vs viewer; `ensure_processing_org_access`; approval requires `require_org_admin()`. Member manual processing is **deliberately admitted** (register D10) | `/api/v3/processing/*`, `/api/v3/uploads`, customer UI |
| **Consultant** | first-class operator acting for a client org | `consultant_profiles` (firm) → `consultant_firm_members` (active member) → `consultant_clients` **active grant** → capability flag (six-flag model) → resource scope → D38 conflict; canonical resolver `ensure_consultant_processing_authorized` | same `/api/v3/processing/*` + `/api/v3/consultants/*` |
| **CarbonTally internal** | platform operator/QA | `staff_profiles` + `staff_roles.permissions` (`can_review`, `can_process`, `can_view_all`, CT-QC authority); ops = `require_staff` | `/api/v3/ops/*`, `/api/v3/qc/*` |
| **Processing Entity** | external manual processing capacity | `require_pe_member` + entity context; **assigned work only** (`_ensure_assigned_item`/`_ensure_assigned_batch`); entity-scoped review queue | `/api/v3/pe/*` |

Additional actors present in the platform but **not processing actors**:
platform/system admin control plane, and the **automatic worker** (system actor
`00000000-…-000000000000`, not a human). Legacy/audit identities exist in the
demo manifest but add no new processing actor.

**Answer to Q1:** the repository supports the four-actor model exactly, plus the
system/automatic actor and the admin control plane.

## 6. Processing Mode Model (Q2) — the critical dimension

**Automatic vs manual is already modeled, and it is explicitly independent of
actor identity.**

Evidence: `api/processing_mode.py` (76 lines, module docstring l.1–21):

> "The PO rule: work whose extraction OR mapping was performed manually by an
> authorized human actor must pass the mandatory CarbonTally CT-QC gate… This
> module implements the agreed **P1 containment** classification — it is a
> DELIBERATELY DERIVED, temporary predicate, NOT the final provenance
> architecture (deferred to the P2/D7 provenance workstream). P1 classifies an
> item as AUTOMATIC only when a durable automatic-processing job exists for it
> AND the machine actually produced output… **Everything else is MANUAL.**"

`item_is_automatic(repos, item)` therefore:
- consults the durable job (`automation_extracted_data`) or the machine
  `extracted_by` zero-UUID marker;
- has **no actor input parameter at all** → it cannot depend on who the actor is;
- is fail-closed (unknown ⇒ MANUAL ⇒ CT-QC required).

Corroborating vocabulary: `domain/automatic_processing.py` owns the job stage
machine (`enqueued … blocked`), `STAGE_TO_STATUS["blocked"] = "manual_review"`,
and `AUTO_EXTRACT_CONFIDENCE_MIN = 0.5` / `AUTO_MAPPING_CONFIDENCE_MIN = 0.6` as
the mode-boundary gates.

**Explicit answers required by the prompt:**

| Proposition | Evidence-backed answer |
|---|---|
| `CONSULTANT ≠ MANUAL` | **SUPPORTED.** Consultants operate the automatic path (they may enqueue: `ensure_processing_org_access` admits active consultant grants) *and* the manual path (extract/map/validate/calculate via capabilities). A consultant-authored manual edit makes the item MANUAL; a consultant merely enqueuing an automatically resolved document leaves it AUTOMATIC. |
| `PROCESSING_ENTITY ≠ MANUAL` | **NOT SUPPORTED — a PE is by construction a *manual* capacity.** PE routes expose manual stage actions only; PE users are denied on the organisation processing surface and have no enqueue/upload route, so a PE cannot cause automatic processing. Evidence: `require_pe_member` + assigned-work scoping; register D10 evidence "Processing Entity staff are denied on the org surface (Gap G9)". |
| `ORGANIZATION ≠ AUTOMATIC` | **SUPPORTED.** Organisations operate both modes: `customer/ProcessingPage.jsx` ("Upload & process" → automatic) and `customer/ProcessingItemWorkspace.jsx` (Extract/Map/Validate/Calculate manual correction). |
| `CARBONTALLY_INTERNAL ≠ AUTOMATIC` | **SUPPORTED.** Internal staff both operate the automatic pipeline (job ops) and perform the manual operator workbench (`/ops/items/{id}/extract|map|validate|calculate`). |

**Conclusion (Q2):** automatic/manual is a genuine independent dimension
(machine-produced output vs human intervention), not an actor category. The PO's
clarification is already satisfied by `processing_mode.py` — and D7 is the
already-designated home for making that dimension *explicit provenance* rather
than a derived predicate.

## 7. Input-Type Model (Q3 part, Q5)

`services/automatic_extraction.py`:

- `_classify(filename, mime)` → `"pdf"` (ext or mime), `("csv","xlsx","xls")` →
  spreadsheet, images → image, otherwise `unsupported`;
- `extract_document(content, filename, mime)` dispatches to `_extract_pdf`
  (pdfplumber → Tesseract OCR → pypdfium2 render + ONNX OCR),
  `_extract_csv` (stdlib `csv`), `_extract_xlsx` (openpyxl), `_extract_image`;
- the durable job carries `file_type` and `processing_type` (default `"utility"`)
  (`data/document_processing.py`, `domain/automatic_processing.AutomaticProcessingJob`);
- `api/v3_documents.py` maps extensions to MIME (`pdf`, `csv`,
  `…spreadsheetml.sheet`, images) at upload.

**Independence verified:** `file_type` lives on the job and `document_type` on
the item; neither the actor nor the mode nor the workflow state selects the
input type. **Q5 answer: input type is independent of actor, processing mode and
workflow state.**

## 8. Automatic Processing

- **Engine:** `services/automatic_processing.AutomaticProcessingService` —
  `process_job` / `_run_stage` with stages `_ingest → _extract → _map →
  _validate → _calculate` and `_notify`.
- **Durability:** job rows in `document_processing_queue`
  (`data/document_processing.py`), claimed by `workers/automatic_processing.py`
  via `claim_next` / stale-lock release; `attempt_count`, `max_attempts`,
  `reenqueue`, `mark_failed`, `mark_blocked`.
- **Trigger:** `POST /api/v3/processing/documents/{file_id}/enqueue`
  (org-scoped; internal staff and active consultant grants pass) — i.e. **the
  organisation, a consultant, or internal staff can start automatic
  processing**. Customer UI: `customer/ProcessingPage.jsx` "Upload & process".
- **Machine provenance:** the worker stamps `extracted_by = MACHINE_EXTRACTOR`
  (`00000000-0000-0000-0000-000000000000`) and writes the write-once
  `automation_extracted_data` / `automation_provider` / `automation_model` block
  on the job — the evidence `item_is_automatic` consumes.
- **Coverage:** PDF (text → OCR → ONNX), CSV, XLSX/XLS, images.

## 9. Manual Processing

- **Org members:** `/api/v3/processing/items/{id}/start|extract|map|validate|calculate`
  (`_get_checked_item` → `ensure_processing_org_access`); UI
  `customer/ProcessingItemWorkspace.jsx` (Extract/Map/Validate/Calculate with
  gates `EXTRACT_EDITABLE`, `MAP_EDITABLE`, `VALIDATE_RUNNABLE`, …).
- **Consultants:** the same routes, additionally gated by the canonical resolver
  (active grant → capability `extract|map|validate|calculate|submit`) and by
  `_STAGE_PERMISSION`; UI `consultant/ConsultantItemPage.jsx`.
- **Internal staff:** `/api/v3/ops/items/{id}/start|extract|map|validate|calculate`,
  `/ops/queues/operator`, `/ops/next-item`; UI `ops/OperatorItemPage.jsx`,
  `ops/ExtractionPanel.jsx`.
- **Processing Entities:** `/api/v3/pe/items/{id}/start|extract|map|validate|calculate`
  plus `pe-review` / `pe-qc` / `clarify` / `issues`, on **assigned** batches only;
  UI `ops/PEEntityItemPage.jsx`.
- **Persisted provenance of a manual action:** `save_extracted_data(item_id,
  data, extracted_by)` writes `extracted_data`, `extracted_by` (the **human user
  id**), `extracted_at`, `status='extracted'`; mapping writes `mapped_data` +
  facility/asset/supplier + `emission_factor_used`.
- **Firm is NOT recorded** (see §14/§17).

## 10. Automatic → Manual Fallback (Q3)

**Already implemented, with explicit gates.** Traced directly from code:

```
upload (+ /documents/{id}/enqueue)          → job stage "enqueued"
  ↓ ingest (storage read)                   → "ingesting"
  ↓ extract (PDF/OCR/CSV/XLSX)              → "extracting"
      completeness < AUTO_EXTRACT_CONFIDENCE_MIN (0.5)      → mark_blocked(...)
  ↓ map (factor match, customer-factor precedence)
      unmatched OR confidence < AUTO_MAPPING_CONFIDENCE_MIN (0.6) → mark_blocked(...)
  ↓ validate (findings persisted)
  ↓ calculate (authoritative CO2e + snapshot + emissions log + evidence)
      validation/calc failures                              → mark_blocked(...)
  ↓ review (customer/owner verification)
```

- `mark_blocked` sets `status='manual_review'`
  (`STAGE_TO_STATUS["blocked"] = "manual_review"`) with `manual_review_reason`.
- A human corrects the item in the **item workbench** (the §9 surfaces) and calls
  `POST /api/v3/processing/jobs/{job_id}/confirm` (`require_auth` + org-scoped
  `_checked_job`; consultants additionally need `can_confirm_automation` per
  P6-2A-R1/B1), which applies any supplied corrections and re-enters the pipeline
  at `enqueued|extracting|mapping|validating`.
- Mode consequence: `processing_mode.item_is_automatic` docstring — *"a failed
  automatic run that a human completed manually stays MANUAL"* — so such work
  must pass CT-QC before customer review.

**Q3 answers:**

| Flow | Already supported? |
|---|---|
| CSV/Excel upload → automatic mapping → unresolved → manual map/correct | **YES** — `_extract_csv`/`_extract_xlsx` + `_map` with confidence gate → `blocked`/`manual_review` → `/jobs/{id}/confirm` + manual map routes |
| PDF upload → automatic extraction → automatic mapping → failure/uncertainty → manual correction/extraction/mapping | **YES** — `_extract_pdf` (text/OCR/ONNX) + `_map` with the same gates → block → human correction in the workbench → confirm |

Neither flow is a new feature; both are existing behaviour, already surfaced in
the customer UI (`ProcessingPage.jsx`: automatic job list with stages
`enqueued…calculating`, retry, confirm).

## 11. Actor × Processing-Mode Matrix (Q4)

Verified from route surfaces and authorization code (not assumed):

| Actor | Automatic | Manual | Constraint / evidence |
|---|---|---|---|
| **Organisation** (owner/admin/member) | **YES** | **YES** | upload/enqueue (auto) + `/processing/items/{id}/extract|map|validate|calculate` (manual); customer UI (`ProcessingPage`, `ProcessingItemWorkspace`). Viewer: read-only |
| **Consultant** | **YES** | **YES** | enqueue via active grant; manual via active grant + capability (`can_extract|map|validate|calculate|submit|confirm_automation`); D38 conflict deny-rule; no CT-QC, no customer approval |
| **CarbonTally internal** | **YES** | **YES** | job operations + `/ops/items/...` manual stages; CT-QC authority is internal-only |
| **Processing Entity** | **NO (not supported)** | **YES** | `/pe/*` is manual-only and assigned-work-scoped; PE users are denied on the org processing surface and have no enqueue/upload route. PEs are *additional controlled manual capacity* (Blueprint l.497) |
| **System/automatic worker** | **YES** (executes) | n/a | not a human actor; stamps machine provenance |

**Constraints:** consultant cells are bounded by the active grant, resource
scope, D38 conflict and the capability flag; the PE manual cell is bounded by
assignment (`_ensure_assigned_item`); every manual cell is bounded by workflow
state (`_require_transition`) and, for customer-facing hand-off, by the CT-QC
prerequisite for manual work.

## 12. Workflow-State Model (Q6)

Two consistent state vocabularies exist:

**A. Item lifecycle** (`domain/partners.ITEM_STATUS_FLOW`): `pending →
extracting → extracted → mapping → mapped → validating → validated →
calculating → calculated → (review|consultant_review|…) → reviewed/ct_qc →
ct_qc_approved → customer_review → approved|rejected`, with rework edges back to
`mapping`/`extracting` and PE stages (`pe_review`, `pe_qc`, `pe_qc_approved`)
for PE-origin work. `WORKFLOW_STAGES` = source, extraction, mapping, validation,
calculation, review, qc, pe_review, pe_qc, carbon_tally_qc, approval.

**B. Durable job pipeline** (`domain/automatic_processing`): `enqueued`,
`ingesting`, `extracting`, `mapping`, `validating`, `calculating`, `review`,
`completed`, `failed`, **`blocked`** (= `manual_review`), with `STAGE_TO_STATUS`
mapping onto the RC2 vocabulary.

**"Needs manual intervention" semantics (Q6 second part):** the state means *a
human must correct or confirm*, **not** *a consultant/PE must act*. Evidence:

- the automatic job blocks the same way regardless of who enqueued it, and
  `/jobs/{id}/confirm` is open to the org-scoped actor set (`require_auth` +
  `_checked_job`; consultants need `can_confirm_automation`);
- the organisation has its own manual correction workspace
  (`customer/ProcessingItemWorkspace.jsx`), which explicitly uses the
  `/api/v3/processing/*` surface and not the staff endpoints;
- the operator/PE **review queue** (`/ops/queues/review`, `require_staff` +
  `can_review`, entity-scoped) is a separate mechanism for the assigned manual
  capacity — not the only route to resolving manual intervention.

So "needs manual intervention" ⇒ **the relevant authorised processor** performs
it: the customer organisation (or its consultant) for org-owned work; internal
staff or the assigned PE for work routed through the manual-processing capacity.

## 13. Existing `processing_origin` Semantics (critical reconciliation)

Authoritative definition — `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` §4
"Processing-origin model":

> "**Processing origin** (immutable, historical):
> `manual_extraction_items.processing_origin VARCHAR CHECK (processing_origin IN ('CARBONTALLY_INTERNAL','PROCESSING_ENTITY'))`"
>
> "| Internal or PE? | `processing_origin` (new, immutable) |"
>
> line 125–126: "`calculated` → `review` **if** origin = CARBONTALLY_INTERNAL
> (skip PE stages); `calculated` → `pe_review` **if** origin = PROCESSING_ENTITY"

and `domain/processing_origin.py`:

> "…preserved as auditable provenance so CarbonTally QC can verify processed data
> regardless of origin (CT-QC-002) and so CarbonTally can tell **which upstream
> controls apply** (internal path has no PE Review/PE QC; the PE path does)."

| # | Question | Answer (evidence) |
|---|---|---|
| 1 | Authoritative definition | The **manual-processing capacity / control path**: CarbonTally's own processing department vs an assigned external PE |
| 2 | Where stored | `manual_extraction_items.processing_origin` (+ `processing_entity_id`), immutable |
| 3 | Values | Exactly two: `CARBONTALLY_INTERNAL`, `PROCESSING_ENTITY` (CHECK constraint) |
| 4 | Who sets it | CarbonTally-controlled assignment: `mark_pe_origin_if_unset` is called only from `api/v3_operations.py` (`/ops/entities/{entity_id}/extraction/…`, l.1059/1082) when Ops places the item in the PE extraction channel. Batch `entity_id` remains the mutable assignment carrier |
| 5 | When | Once, entering the PE channel (`UPDATE … WHERE processing_entity_id IS NULL AND processing_origin = 'CARBONTALLY_INTERNAL'`) |
| 6 | Can it change | **No** — write-once ("reassignment, retries and reprocessing cannot change it") |
| 7 | Immutable | **Yes** |
| 8 | Actor identity | **No** — human identity lives in `extracted_by` / `qc_by` / `customer_reviewed_by` |
| 9 | Processing channel | **Yes** — its primary meaning (internal department vs external PE) |
| 10 | Provenance | **Yes, derived** — preserved *as* auditable provenance so QC can see which controls applied |
| 11 | Workflow routing | **Yes** — selects `review` vs `pe_review`, hence which QC stages apply |
| 12 | Something else | Also a **queue/label** dimension (origin badge on queue/workbench rows; origin-aware CT-QC queue) |

**Summary: `processing_origin` = "which manual-processing capacity/control path
produced this work (CarbonTally internal department or external PE)" — a
workflow-routing + QC-control provenance label derived from CarbonTally's
assignment decision. It is NOT the human actor, NOT the actor domain, and NOT
the automatic/manual dimension.**

## 14. Existing Provenance Semantics

| Dimension | Recorded today? | Where |
|---|---|---|
| Authenticated human actor | **YES** | `manual_extraction_items.extracted_by`, `qc_by`, `customer_reviewed_by` (+ `_at`); audit `performed_by`; emissions log `calculated_by` |
| Machine/automatic actor | **YES** | `extracted_by = MACHINE_EXTRACTOR` (zero UUID); job `automation_extracted_data`, `automation_provider`, `automation_model` (write-once) |
| Organisation | **YES** | batch/item `organization_id`; `emissions_logs`; job `organization_id` |
| Consultant (human) | **YES** (as a user id) | the same `extracted_by`/audit columns — a consultant action is recorded as the human user |
| **Consultant firm** | **NO** | no firm column on items/jobs/snapshots/audit → **D7's real gap** |
| Processing Entity | **YES** | `processing_entity_id` (item, immutable) + `work_item_assignments` (`assignee_kind`, `actor_domain`, `processing_entity_id`) |
| Processing **mode** (auto vs manual) | **Derived only** | `processing_mode.item_is_automatic` (P1 predicate; explicitly "NOT the final provenance architecture … deferred to the P2/D7 provenance workstream") |
| Calculation provenance | **YES** | snapshots + `data/emissions_logs`: `factor_kind`, `customer_factor_id`, `source_item_id`, `source_file`, `source_page`, `request_id`, `performed_by` |
| Machine vs human-after-automation | **Partially** | write-once automation block + human `extracted_by`; the mixed case is documented as *not distinguishable* by P1 |

**Assessment:** provenance is strong for *who (user), what factor, which source,
which organisation*; it is **absent for firm** and **implicit for mode** — both
absences sit exactly inside D7's designated scope.

## 15. Entitlement Relationship

- **Owner:** the **client organisation** (P6-0 D-7 ratified; register D6 records
  client-org ownership as canonical). Billing keys every operation by the
  *server-loaded* `batch.organization_id` — never by the consultant firm or the
  acting user.
- **Check points:** non-charging availability check at consultant submission
  (`ensure_processing_entitlement`, D6, fail-closed 403, no mutation) and the
  authoritative charge at **customer approval** (`charge_processing`,
  `idempotency_key = charge:item:{id}`, the single call site).
- **Relationship to actor/mode:** entitlement is **independent of the processing
  actor and of the processing mode**. Whoever performs automatic or manual
  processing (organisation, consultant, internal staff, PE), the entitlement
  consumed is the client organisation's.
- **Not modified by this task.**

## 16. D6 Reconciliation

**UNCHANGED — the D6 proposal faithfully preserves the original model.**

D6 says: entitlement is organisation-owned; the approval-time charge is
canonical; an optional **non-charging** availability check at consultant
submission. The repository implements exactly this, actor- and mode-agnostically.
Nothing in the original processing model requires entitlement to move to a firm,
an actor, or a mode; nor does it require a check at "processing start" for any
actor class. D6 only makes an existing, already-coded behaviour ratifiable
policy.

## 17. D7 Reconciliation

**NEEDS CLARIFICATION (wording/scope only) — the concept is valid, but it must
not touch `processing_origin`.**

- D7's substance — *record the acting consultant firm at action time,
  additively, server-derived* — addresses a **real** gap (§14: no firm recorded
  anywhere in item/job/snapshot/audit provenance) and does not conflict with the
  actor/mode/origin dimensions.
- Two clarifications are required:
  1. D7 must be stated as **provenance of the acting consultant firm** (and, if
     the PO wishes, the explicit **processing-mode provenance**), explicitly
     *not* as a change to any origin value, CHECK constraint or origin→stage
     routing.
  2. D7 should acknowledge that `api/processing_mode.item_is_automatic` already
     designates D7 as the home of the *mode* provenance, so D7 may need to cover
     **two** additive dimensions (firm + mode) rather than firm alone.
- D7 remains additive, non-destructive and compatible with write-once origin.

## 18. D7b Reconciliation

**PROPOSED MODEL CONFLICT — do NOT implement as framed.**

The readiness analysis proposed adding a `CONSULTANT` value to
`processing_origin` (rationale: "consultant firm/origin provenance + queue
labelling", roadmap §9 deferral row). The evidence shows this conflates distinct
dimensions:

1. **`processing_origin` answers "Internal or PE?"** — a *manual-processing
   capacity / control-path* distinction (§13; V1.2 §4, line 192). A consultant
   is a **client-side actor**, not a processing capacity.
2. **It is workflow routing.** Origin selects `calculated → review` vs
   `calculated → pe_review` (V1.2 §4). A `CONSULTANT` value has no defined
   routing and would leave stage selection undefined for consultant-worked items.
3. **It is a CHECK-constrained, write-once vocabulary set by Ops assignment.**
   Adding a value is a schema + routing + queue-semantics change — the opposite
   of the additive, behaviour-preserving work D7 was meant to be.
4. **It mixes modes.** Consultants process both automatically and manually
   (§11). An origin value keyed to an actor cannot express mode; conversely a
   consultant-worked item may legitimately keep `CARBONTALLY_INTERNAL` origin.
5. **It duplicates existing mechanisms.** "Which firm acted" belongs in
   provenance (D7); "which capacity processed this" is already internal-vs-PE;
   "who was the human" is already `extracted_by`. No question remains for a
   fourth origin value to answer.

**Consequence:** D7b should be **withdrawn** (recommended) or re-defined by the
PO as an explicit *redefinition* of the origin concept — a different, larger
decision involving schema, routing, queues and the CT-QC control model. It must
not be bundled into P6-2D as originally worded.

## 19. D7c Reconciliation

**UNCHANGED.** The no-backfill recommendation is compatible with the model. For
*firm* provenance there is no historical source of truth (the firm was never
recorded), so backfill is impossible as well as undesirable: new actions only.
The existing `processing_origin` historical backfill (V1.2 §4) is a different
case and is unaffected.

## 20. D8 / D11 Impact

- **D8 (conversation kind):** unaffected by the processing model. Consultants
  already participate in org-scoped conversations via the active grant
  (`v3_messaging.py`, role `consultant`) — consistent with a consultant being a
  client-side actor on the client org's data. The kind question remains a PO
  vocabulary choice (recommended: reuse, no new kind).
- **D11 (notification vocabulary):** unaffected conceptually, but payloads should
  carry the **actor's firm** (D7) and must **not** attempt to express a
  "consultant origin". The events describe workflow transitions (submitted to
  CT-QC, QC outcome, customer decision, rework), which exist independently of
  origin.

## 21. Impact on Pending PO Decisions

| Decision | Impact | Exact question for the PO (where clarification is required) |
|---|---|---|
| **D6** | **UNCHANGED** | — (implemented; ratify as policy) |
| **D7** | **NEEDS CLARIFICATION (scope/wording)** | "Should D7 record *only* the acting consultant firm at action time, or *also* make the processing-mode provenance (automatic vs manual) explicit in the same additive change — given that `processing_mode.py` already names D7 as the destination for the mode predicate?" |
| **D7b** | **PROPOSED MODEL CONFLICT** | "Do you wish to **withdraw** the proposed `CONSULTANT` `processing_origin` value (recommended, because origin means internal-vs-PE manual capacity and drives PE-vs-internal stage routing), or do you wish to **redefine** `processing_origin` as an actor-domain vocabulary — a larger decision requiring a CHECK-constraint change, stage-routing rules and queue-semantics changes?" |
| **D7c** | **UNCHANGED** | — (no backfill; new actions only) |
| **D8** | **UNCHANGED** | — (recommend reuse of org conversations; a distinct kind only if reporting requires it) |
| **D11** | **DOCUMENTATION GAP** (payload semantics) | "Confirm that consultant-processing notification payloads identify the **acting firm** (per D7) and never an origin-style consultant label." |

Additional decision surfaced by this reconciliation (not previously listed):

| Ref (proposed) | Impact | Question |
|---|---|---|
| `PO-P6-2-MODEL-20260910` | **DOCUMENTATION GAP** | "Should the foundational four-actor × automatic/manual processing model be ratified as documentation in the Blueprint (§22/§23), including that **PEs are a manual-processing capacity only** (no automatic channel) and that automatic/manual is independent of actor?" |

**No decision is made here.** Clarifications are questions only.

## 22. Documentation Gaps

The foundational model is **partially** documented, in fragments:

| Concept | Documented? | Where / gap |
|---|---|---|
| Four processing actors | **Partial** | Blueprint names the internal department + PEs (l.497, l.1349); Phase-6 docs cover consultants. **No single authoritative statement** that Organizations, Consultants, CarbonTally and PEs are the four processing participants |
| Automatic vs manual as a dimension | **Partial** | Documented in code docstrings (`domain/automatic_processing.py`, `api/processing_mode.py`) — **not** in architecture text |
| Automatic processing for CSV/Excel **and** PDF | **Not documented** | Only in `services/automatic_extraction.py` (code) |
| Automatic → manual fallback (confidence gates + human confirm) | **Not documented** | Only in code (`AUTO_*_CONFIDENCE_MIN`, `mark_blocked`, `/jobs/{id}/confirm`) |
| `processing_origin` = internal-vs-PE manual capacity | **Yes** | `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` §4 — clearest statement in the repository |
| PE = manual capacity only (no automatic) | **Implicit only** | Blueprint l.497; never stated as an explicit rule |
| Entitlement owned by the client org regardless of processor | **Yes** | P6-0 D-7 / register D6; `services/billing.py` |
| Firm provenance | **Gap (known)** | Not recorded; deferred to D7 |
| Mode provenance (explicit, not derived) | **Known gap, acknowledged in code** | `processing_mode.py` defers it to D7 |

**Primary documentation gap:** no authoritative architecture section states the
complete processing model (actors × modes × input types × fallback). The closest
single statement is V1.2 §4, which covers only the origin dimension.

## 23. Required Documentation Updates

Reported, **not made** (silent modification of authoritative architecture
documents is forbidden, and none of these is "unquestionably required and safe"
because each states product policy).

| # | Document | Section | Clarification required | Why it matters | Before PO ratification? |
|---|---|---|---|---|---|
| 1 | `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` | Processing model (near l.497 / pipeline) | Add: the four processing actors; that processing **mode** (automatic/manual) is independent of actor; that PEs are a **manual capacity only**; the automatic→manual fallback with confidence gates | Prevents future mis-modelling such as D7b | **Yes** |
| 2 | `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` §4 (or the Blueprint) | Processing-origin model | Add one sentence: "`processing_origin` identifies the **manual-processing capacity/control path** (CarbonTally internal vs external PE); it is not actor identity and not processing mode" | Prevents re-proposing `CONSULTANT` as an origin value | **Yes** |
| 3 | `CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md` | §8/§13 | Cross-reference the mode dimension and D7's designated role in making mode explicit | Keeps P6-2 docs coherent with `processing_mode.py` | Optional |

## 24. Risks / Ambiguities

| # | Risk / ambiguity | Assessment |
|---|---|---|
| R1 | A future agent implements D7b as written, adding a `CONSULTANT` origin value | Schema/constraint/routing change; breaks PE-vs-internal stage selection and misrepresents the model. **Mitigation:** PO clarification + documentation update (§23) |
| R2 | The P1 mode predicate is described as "temporary", so mode provenance may drift | Already acknowledged in `processing_mode.py`; D7 is the designated fix |
| R3 | Mixed/corrected automatic work is not distinguishable (a human edits an automatic value) | Documented P1 limitation. Relevant because the PO's model includes "automatic … then manual correction": the *state* is right (item becomes MANUAL) but the *history* is not yet explicit |
| R4 | "Needs manual intervention" could be mis-read as "consultant/PE must act" | Disproved by §12; the customer manual workspace exists. Risk is documentation-only |
| R5 | PE × automatic not supported could be mistaken for a defect | It is consistent with the Blueprint (PEs = additional manual capacity). Document explicitly to prevent "fixing" a non-defect |
| R6 | D7 (firm) implemented without also addressing mode, leaving the predicate permanent | Addressed by the §17/§21 wording clarification |
| R7 | Terminology drift between "origin", "mode", "channel", "capacity" | Recommend the Blueprint/glossary adopt the four distinct terms (actor, mode, input type, origin) |

## 25. Evidence Limitations

1. **No runtime execution.** Static inspection only (code, data-layer SQL,
   frontend) — no server started, no job run, no browser session. Behavioural
   claims rest on code paths plus existing verified suites (P6-2A/2B/2C).
2. **No live database query.** Column names/constraints come from the data-layer
   SQL and the V1.2 design document, not from `information_schema`; the V1.2
   CHECK-constraint text is documentation evidence and was not re-verified
   against the live schema.
3. **The PE × automatic conclusion is by surface analysis** (no PE enqueue route;
   PE denied on the org surface per register D10 evidence). Strong, but not
   exercised at runtime here.
4. **The fallback trace is code-based**; end-to-end behaviour is asserted by
   existing suites (`test_v3_automatic_processing_jobs.py`,
   `test_automatic_processing.py`, `test_p6_2b_4_ct_qc_prerequisite.py`) rather
   than re-run in this task.
5. **No PO decision is treated as ratified** beyond the P6-0 package and
   `PO-P6-2C-D1/D2/D3`.
6. **The documentation-gap assessment is a judgement** based on searching the
   architecture corpus for these concepts; another document may mention them in
   passing.

## 26. Final Verdict

### `CLARIFICATION REQUIRED — PO RATIFICATION BLOCKED`

(scoped to the `D7b` item; `D6`, `D7` and `D7c` are otherwise ready)

**A. Does the current implementation/documentation faithfully represent the
original CarbonTally processing model?**
**The *implementation* — yes.** All four actors process; automatic and manual
modes exist for the organisation, consultant and internal actors; PDF, CSV and
Excel are all handled automatically with an implemented automatic→manual
fallback; entitlement is organisation-owned. The *documentation* represents it
only in fragments (§22) — a real documentation gap, not an implementation gap.

**B. Does the proposed P6-2D D7/D7b model preserve that architecture?**
**D7: yes** (additive firm provenance; must be worded so it does not touch
origin, and ideally also carries the mode provenance `processing_mode.py` already
assigns to D7). **D7b: no** — as framed it introduces an actor-domain value into
a constrained, routing-driving, manual-capacity vocabulary.

**C. Is `processing_origin` currently used for the same conceptual purpose that
D7/D7b assume?**
**No.** It is the internal-vs-PE **manual-processing capacity / control-path**
selector (immutable, write-once, Ops-set, driving `review` vs `pe_review` and the
QC-control path). D7b assumes an actor/provenance vocabulary — a different
concept.

**D. Does automatic/manual processing remain an independent dimension?**
**Yes.** `api/processing_mode.py` classifies mode from machine-production
evidence with **no actor parameter**, is fail-closed, and is explicitly
documented as derived; the same actors operate both modes (except PEs, which are
manual-only by construction and cannot enqueue automatic processing).

**E. Can the PO safely proceed to ratify D6/D7/D7b after this report?**
**D6 — yes. D7 — yes, with the scope/wording clarification. D7b — no, not as
framed:** the PO must first answer the §21 question (withdraw vs redefine
`processing_origin`). Once that is answered and the §23 documentation updates are
agreed, the P6-2D decision set can be ratified.








