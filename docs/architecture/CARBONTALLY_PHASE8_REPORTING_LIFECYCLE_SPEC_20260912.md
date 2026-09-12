# CarbonTally — Phase 8 Report Versioning & Approval Lifecycle Specification

**Prompt ID:** `CT-P8-REPORTING-LIFECYCLE-SPEC-20260912-009`
**Date:** 2026-09-12
**Repository HEAD at specification:** `06989d5fe3aaf0203670e68aba6fd1b9f8da56e6` (branch `main`)
**Supersedes nothing.** Extends `CARBONTALLY_PHASE8_DISCOVERY_AND_CAPABILITY_GAP_ANALYSIS_20260912.md`.

---

## 1. Document Status and Authority

| Field | Value |
|---|---|
| Status | **DESIGN / SPECIFICATION ONLY — NO IMPLEMENTATION AUTHORISED** |
| Authority | Product Owner (PO) |
| Type | Architecture / product specification / existing-system design archaeology |
| Implementation authority conferred | **NONE** |
| Code/schema/production changes made | **NONE** |
| LLM installed / provider connected / key added | **NO / NO / NO** |

**Governance rule applied throughout:** *discovery does not equal authorization*. This document
establishes facts, identifies gaps, classifies existing components, proposes design options,
recommends where the repository supports a recommendation, and marks **PO DECISION REQUIRED**
where it does not. It does not silently choose business policy.

**Evidence standard:** the specification reuses CarbonTally's **existing** evidence and
provenance architecture (`emissions_logs`, `calculation_snapshots`, factor provenance,
`domain/evidence.py`, Phase 7 `audit_trail`). It **does not** introduce a competing evidence
score, confidence score, provenance model, audit model or calculation model, and it explicitly
prohibits resurrecting `emissions_logs.confidence_score` as a report/evidence quality metric.

---

## 2. Executive Summary

CarbonTally already has a **working report generation foundation** and a **partially-prepared
schema** for a lifecycle, but **no lifecycle**. Generation works; **editing, review, approval,
finalization and freezing do not exist in any form.**

**What exists (verified):**

* `ReportGenerationEngine` builds a **12-section** structured annual report from persisted
  `emissions_logs` + `calculation_snapshots` + `emission_factors`, with mandatory CO2/CO2e
  provenance labelling and honest `insufficient_data` states.
* `report_generation_queue` persists the report and its lifecycle
  (`pending → generating → completed | failed`), and **already contains dormant columns** for
  customer edits (`user_edits`) and a final artefact (`final_report_url`,
  `final_report_file_name`, `final_report_size_bytes`).
* `report_versions` records a generation snapshot per successful generation
  (`version_number`, `content`, `is_current`, `notes`, `change_summary`).
* `report_comments` exists with a section-level comment/resolution shape — **dormant**.
* `render_branded_pdf` renders a server-branded PDF from persisted content.
* Phase 7 `audit_trail` provides an append-only, taxonomy-classified audit substrate that
  already includes a **`report` category**.

**What does not exist (verified):**

* No report **state** beyond queue status; no `draft`/`reviewed`/`approved`/`final`.
* No approver, no approval timestamp, no approval decision record for reports.
* No customer narrative editing path (the `user_edits` column is not written by any API).
* No review workflow, no comment API/UI.
* No frozen final PDF (the PDF is rendered on demand and never stored).
* **No audit events for any report lifecycle action** (`v3_reports.py` makes no audit calls).
* **No RLS on any report table** — authorization for reports is API-layer only (§22).

**Recommended lifecycle (this specification):**

```text
GENERATE → DRAFT → EDIT (narrative overlay) → REVIEW → APPROVE → FINAL → FROZEN PDF
```

with the governing rule:

> **Approval freezes the meaning of the report version; finalization freezes the deliverable.
> Any post-approval content change invalidates the approval and requires a new version.**

**Structural recommendation:** **EXTEND** `report_generation_queue` + `report_versions` +
`report_comments` + `audit_trail`. Do **not** build a parallel report system, and do **not**
repurpose the Processing-Entity `approval_requests` / `approval_decisions` tables (§7.4).

---

## 3. Discovery Evidence

All findings below are grounded in named artefacts in the current tree.

| # | Artefact | Line / detail | Finding |
|---|---|---|---|
| E1 | `backend/api/v3_reports.py` | `SUPPORTED_REPORT_TYPES` (:63) | Exactly one supported type: `annual` |
| E2 | `backend/api/v3_reports.py` | routes (:163, :176, :214, :286, :309, :331, :348, :396) | 8 routes: types, list, create, detail, content, versions, download, pdf — **no edit/approve/finalize** |
| E3 | `backend/api/v3_reports.py` | `REPORT_STATUSES` (:66) | `("pending", "generating", "completed", "failed")` — queue vocabulary only |
| E4 | `backend/api/v3_reports.py` | version write (:268-281) | On success: `report_versions.create(..., is_current=True)` |
| E5 | `backend/api/v3_reports.py` | no audit import / no `record()` | **Report lifecycle produces no audit events** |
| E6 | `backend/engines/report_generation.py` | `_SECTION_ORDER` (:65) | 12 sections, fixed order |
| E7 | `backend/engines/report_generation.py` | `_generation_section` (:665-681) | Embeds `datetime.now(timezone.utc).isoformat()` → **content is non-deterministic** |
| E8 | `backend/engines/report_generation.py` | strict validation | Blocking validation errors raise `ValidationFailedError`; no report persisted |
| E9 | `backend/data/reports.py` | `_REPORT_FULL_COLUMNS` (:25) | Includes `user_edits`, `data_sources`, AI columns |
| E10 | `backend/data/reports.py` | `_row_to_report_full` (:65-107) | **Does not expose `user_edits`** (dormant column) |
| E11 | `backend/data/report_versions.py` | module docstring (:1-11) | "the RC2 dump carries no `reports` parent table" |
| E12 | `backend/data/report_versions.py` | `create(..., is_current=True)` (:56-90) | Never clears prior `is_current` → **multiple current rows possible** |
| E13 | `backend/data/report_versions.py` | `get_current` (:104) | Mitigates by `ORDER BY version_number DESC LIMIT 1` |
| E14 | `supabase/migrations/00000000000000_init_schema.sql` | `report_generation_queue` (:970) | `user_edits JSONB`; `final_report_url`/`_file_name`/`_size_bytes`; `ai_model_used`/`ai_tokens_used`/`ai_cost`/`ai_processing_time_ms` |
| E15 | same | `report_versions` (:1003) | `report_id`, `version_number`, `content`, `file_url`, `file_name`, `created_by`, `notes`, `change_summary`, `is_current`, `UNIQUE(report_id, version_number)` — **no status/approver** |
| E16 | same | `report_comments` (:1020) | `report_id`, `user_id`, `section_id`, `comment`, `comment_type`, `is_resolved`, `resolved_at`, `resolved_by`, `resolution_notes` — **no version_id, no visibility flag, no org_id** |
| E17 | same | `report_templates` (:947) | `template_structure JSONB`, `ai_prompts JSONB`, branding; `is_default`, `is_system`; org-nullable (global rows) |
| E18 | same | `approval_requests` (:1374) / `approval_decisions` (:1390) | FK to **`processing_assignments`** — PE/processing workflow, **not reports** |
| E19 | `database/rc1/002_rc1_constraints.sql` | (:495-496) | "`report_versions.report_id` is intentionally omitted: the dump contains no `reports` parent table" |
| E20 | `supabase/migrations/*` | RLS scan | **No `ENABLE ROW LEVEL SECURITY` and no policy on any report table** (21 RLS enablements exist elsewhere, incl. `calculation_snapshots`) |
| E21 | `backend/engines/pdf_render.py` | `render_branded_pdf` (:245-247) | Returns bytes; **never stored**; `SimpleDocTemplate` default metadata |
| E22 | `backend/engines/pdf_render.py` | `_draw_footer` (:219-226) | Footer embeds `date.today()`; reportlab adds `/CreationDate` + `/ID` → **not byte-reproducible** |
| E23 | `backend/engines/pdf_render.py` | `render(report, content)` | PDF identifies `report_type` + `reporting_year` but **not the version number** |
| E24 | `backend/api/consultant_branding.py` | `resolve_report_branding` (:54) | Brand derived from **server-verified** relationship, never client input (D21.7) |
| E25 | `backend/domain/audit.py` | `CAT_REPORT = "report"` (:59); `ACTOR_*`, `ORIGINS`, `OUTCOMES` (:23-47) | Phase 7 taxonomy already has a report category and actor/origin/outcome vocabulary, stored in `audit_trail.metadata` |
| E26 | `supabase/.../p7_audit_immutability_and_indexes.sql` | trigger + 5 indexes | `audit_trail` is append-only (immutability trigger) |
| E27 | `frontend/src/v3/reports/ReportsPage.jsx` | :242-246 | "Version" column reads `r.current_version?.version_number`, but the **list** endpoint omits `current_version` → always falls back to `v1`/`—` |
| E28 | `frontend/src/v3/reports/ReportDetailPage.jsx` | imports (:22-30) | No edit/approve/comment calls exist |
| E29 | `frontend/src/v3/api.js` | :1179 | `downloadReportPdf` exists and is unit-tested, but is **not wired into any reports component** |
| E30 | `backend/api/v3_reports.py` | `download_report` docstring (:347-352) | Claims "no PDF rendering exists in V3" while the `/pdf` route exists → **documentation drift** |
| E31 | `backend/services/billing.py` | :201 | `usage_tracking.reports_generated` is only **read**; never incremented by the reports surface |
| E32 | `backend/tests/unit/api/test_v3_reports.py` | ~35 tests | Existing coverage incl. org isolation, version roundtrip, branded PDF, not-ready paths |

### 3.1 Legacy report surface (independently re-verified)

| Legacy artefact | Content | Status |
|---|---|---|
| `backend/routes/reports.py` (2,097 lines) | `/report_status` advertising `["SECR","CSRD","ISSB","AUDITOR_EXCEL"]`; six generic types (`summary`, `documents`, `emissions`, `staff`, `organization`, `custom`); 10 metrics; template CRUD; scheduling; sharing; DEFRA import | **NOT mounted** by `backend/api/router.py` |
| `backend/report_generator.py` (1,071 lines) | `EnhancedSustainabilityReportPDF` (FPDF), SECR-oriented narrative, YoY comparison, methodology notes, intensity ratios | Legacy path; reads via a legacy client, not the authoritative chain |

**Confirmed:** the legacy surface is a **behavioural ancestor**, not an authoritative catalogue.
Its labels describe report *kinds* and *dashboards*, not 80–90 audit-ready report artefacts.

### 3.2 Prior-discovery consistency check

The prompt's Stop Condition 7 was checked: **the report engine described in the Phase 8
discovery document corresponds to the current implementation.** `v3_reports.py`,
`report_generation.py`, `data/reports.py`, `data/report_versions.py`, `pdf_render.py` and the
`report_*` tables all match the described architecture. No conflict found. No stop condition
was triggered by this task.

---

## 4. Current Authoritative Report Catalogue

### 4.1 Verified catalogue

```python
# backend/api/v3_reports.py:63  (V3, mounted, authoritative)
SUPPORTED_REPORT_TYPES: dict[str, str] = {
    "annual": "Annual emissions report (structured 12-section V3 report)",
}
```

**The authoritative V3 catalogue contains exactly ONE report type: `annual`.**

`validate_report_type()` raises **HTTP 422** for any other value, and
`GET /api/v3/reports/types` returns that single entry. `test_supported_report_types_are_real_engine_types()`
asserts the catalogue against the engine.

### 4.2 Verified engine sections

`ReportGenerationEngine._SECTION_ORDER` (`report_generation.py:65`) — twelve ordered sections:

| # | section_id | Title |
|---|---|---|
| 1 | `metadata` | Report metadata |
| 2 | `organization` | Organization |
| 3 | `period` | Reporting period |
| 4 | `totals` | Emissions totals |
| 5 | `scopes` | Scope summaries |
| 6 | `activities` | Category / activity summaries |
| 7 | `validation` | Validation |
| 8 | `benchmarking` | Benchmarking |
| 9 | `provenance` | Factor provenance |
| 10 | `calculation` | Calculation information |
| 11 | `lineage` | Source lineage |
| 12 | `generation` | Generation metadata |

`pdf_render.py` renders exactly these twelve section ids in this order.

### 4.3 Legacy labels — NOT part of the catalogue

`SECR`, `CSRD`, `ISSB`, `AUDITOR_EXCEL`, `summary`, `documents`, `emissions`, `staff`,
`organization`, `custom` exist **only** in the unmounted legacy monolith.
**They must not be treated as authoritative V3 report types.**

### 4.4 Mandatory distinction — type vs instance vs version vs artefact

This distinction is **mandatory** for all Phase 8 reporting work:

| Concept | Definition | Current representation |
|---|---|---|
| **Report type** | What kind of report the engine can produce | `SUPPORTED_REPORT_TYPES` → `annual` |
| **Report instance** | One generated report for one organisation + reporting year (a "report" the user sees) | `report_generation_queue.id` |
| **Report version** | An immutable snapshot of that instance's content at a point in time | `report_versions` row (`report_id` + `version_number`) |
| **Final report artefact** | The frozen deliverable PDF tied to one approved version | **Does not exist yet** (columns `final_report_url`/`_file_name`/`_size_bytes` exist but are unpopulated by the PDF path) |

---

## 5. Report / Instance / Version / Artefact Definitions (normative)

**Report Type** — a value in `SUPPORTED_REPORT_TYPES` that the engine can genuinely produce.
Today: `annual`. A type is not a report.

**Report Instance** — a single generated report for one `organization_id` + `reporting_year` +
`report_type`. Identified by `report_generation_queue.id`. This is the "report" a user opens.
There is **no separate `reports` parent table** and none is required (§25).

**Report Version** — an append-only snapshot of a report instance's content at a point in time.
Identified by (`report_id`, `version_number`) — already enforced `UNIQUE`.
A version is the unit that is edited, reviewed, approved and finalised.

**System Content** — the deterministic portion of version content derived from CarbonTally's
persisted carbon data by `ReportGenerationEngine`. **Not editable by any customer.**

**Narrative Overlay** — the customer-authored portion of a version's content (commentary,
context, initiatives, future plans). Stored **separately** from system content (§15).

**Report Version Content** — the effective content of a version = System Content ⊕ Narrative
Overlay (the overlay wins only within its own editable keys; it can never override system keys).

**Final Report Artefact** — the frozen PDF produced from one **approved** version, stored once,
with a recorded content hash and an immutable association to that version.

**Approval** — a recorded decision by an authorised actor that a specific version is the
organisation's authorised representation for its reporting period. Approval binds **by version
identity**, never to "the report" generically.

**Finalization** — the act of producing and freezing the Final Report Artefact from an approved
version. After finalization the deliverable is immutable.

---

## 6. Existing Report Architecture

```text
POST /api/v3/reports
   │  (require_org_member + ensure_org_access + validate_report_type)
   ▼
ReportsRepository.create_generation_request()  → report_generation_queue row, status='pending'
   ▼
ReportsRepository.mark_generating()            → status='generating', started_at=NOW()
   ▼
ReportGenerationEngine.generate(ReportRequest)
   ├── OrganizationsRepository  (org + metadata)
   ├── EmissionsLogsRepository  (period logs + aggregate)
   ├── EmissionFactorsRepository (factor resolution + provenance)
   ├── ValidationEngine         (strict blocking → ValidationFailedError)
   ├── BenchmarkingEngine       (metric availability states)
   ├── CalculationEngine.verify (tamper / match verification per snapshot)
   └── EventBus(ReportGenerated) + AuditLogger
   ▼
ReportsRepository.complete_generation(url, size, page_count, content)
   → status='completed', generated_content={"page_count":n,"content":{12 sections}}
   ▼
ReportVersionsRepository.create(version_number=N, content, is_current=True)
   ▼
Response: { report: shape_report_out(...), content }
```

**Read paths:** `GET /api/v3/reports` (list, filters, `count_by_status`, server-resolved
branding), `/{id}` (detail + `current_version` + branding), `/{id}/content`, `/{id}/versions`,
`/{id}/download` (JSON attachment of persisted content), `/{id}/pdf` (branded PDF bytes).

**Failure path:** any exception → `mark_failed(status='failed', error_log=str(exc))`, then the
real error is mapped to an HTTP status. **Nothing is presented as ready unless the persisted row
is `completed` with content** (`shape_report_status.ready`).

**Key architectural properties**

| Property | Status |
|---|---|
| Server-authoritative (frontend never calculates) | ✅ |
| Content persisted (`generated_content` JSONB) | ✅ |
| Provenance labelled (CO2 vs CO2e; never relabelled) | ✅ |
| Honest insufficiency (`insufficient_data`, no fabricated zeros) | ✅ |
| Synchronous generation in-request | ✅ (documented: "no worker infrastructure") |
| Server-authorized branding (D21.7) | ✅ |
| Version snapshot per generation | ✅ |
| Lifecycle states beyond queue status | ❌ |
| Audit events | ❌ |
| Edit / review / approval / finalization | ❌ |
| PDF persisted | ❌ |

---

## 7. Existing Report Lifecycle

### 7.1 Persisted status vocabulary (verified)

```python
# backend/api/v3_reports.py:66
REPORT_STATUSES = ("pending", "generating", "completed", "failed")
STATUS_LABELS = {"pending": "Queued", "generating": "Generating",
                 "completed": "Ready", "failed": "Failed"}
```

This is a **generation queue state machine**, not a document lifecycle. It describes whether the
engine produced content — not whether that content is reviewed, approved or released.

### 7.2 Verified current flow

```text
[create]  pending
   ↓ mark_generating
generating
   ├── engine OK  → complete_generation → completed (+ version row, is_current=TRUE)
   └── engine err → mark_failed         → failed (+ error_log)
```

Terminal states: `completed`, `failed`. **No transition exists out of either state** in the
current implementation, and there is no re-generation path in the V3 surface.

### 7.3 `is_current` semantics (verified — and problematic)

`ReportVersionsRepository.create()` defaults `is_current=True` and **does not demote the previous
current row**. Consequence: if a report were ever generated twice, **two versions would both
carry `is_current=TRUE`**. `get_current()` masks this by ordering
`WHERE is_current = TRUE ORDER BY version_number DESC LIMIT 1` (E12/E13).

**Specification position:** `is_current` must become a **derived, single-valued invariant**
(exactly one current version per report instance), enforced transactionally. This is a
correctness requirement, not a preference.

### 7.4 `approval_requests` / `approval_decisions` — explicitly excluded

Verified: `approval_requests.assignment_id` is
`NOT NULL REFERENCES public.processing_assignments(id)` (E18). These tables belong to the
**Processing Entity / processing workflow**, not to reports.

**They must NOT be repurposed for report approval** — not even though their names suggest
otherwise. Report approval is a distinct domain with different actors, different scope and
different audit semantics. (See §25 Option B, evaluated and **not recommended**.)

### 7.5 Audit status (verified)

`v3_reports.py` contains **no audit calls** (E5). Therefore today:

* report generation is **not** audited;
* version creation is **not** audited;
* downloads are **not** audited.

The capability to audit exists (`AuditRepository` is present in the repository bundle; Phase 7
taxonomy includes `CAT_REPORT = "report"`), but the report surface does not use it.

---

## 8. Gap Analysis

| # | Requirement | Existing | Partial | Missing | Evidence |
|---|---|:-:|:-:|:-:|---|
| G1 | Authoritative 12-section report generation | ✅ | | | E1, E6 |
| G2 | Persisted report content | ✅ | | | E9, E14 |
| G3 | Generation lifecycle (queue states) | ✅ | | | E3, E14 |
| G4 | Version snapshot per generation | ✅ | | | E4, E15 |
| G5 | Unique/derived "current version" invariant | | ⚠ | | E12, E13 |
| G6 | Version **status** (draft/reviewed/approved/final) | | | ❌ | E15 |
| G7 | Customer narrative editing path | | ⚠ (column only) | | E9, E10, E14 |
| G8 | System vs editable field separation | | | ❌ | §9–§11 |
| G9 | Review workflow + comments API/UI | | ⚠ (dormant table) | | E16 |
| G10 | Approval record (actor, timestamp, decision) | | | ❌ | E15, E18 |
| G11 | Post-approval change policy | | | ❌ | — |
| G12 | Frozen final PDF artefact | | ⚠ (columns only) | | E14, E21, E22 |
| G13 | PDF **version association** | | | ❌ | E23 |
| G14 | Deterministic hash basis | | | ❌ | E7, E22 |
| G15 | Report lifecycle audit events | | ⚠ (substrate exists) | | E5, E25, E26 |
| G16 | Report-table RLS | | | ❌ | E20 |
| G17 | Concurrency / stale-version protection | | | ❌ | §26 |
| G18 | Frontend edit/review/approve UI | | | ❌ | E27, E28 |
| G19 | Report usage metering (`reports_generated`) | | ⚠ (read only) | | E31 |
| G20 | Legacy surface disposition decision | | | ❌ (policy) | §4.3 |

**Legend:** ✅ existing and sufficient · ⚠ partial/foundation · ❌ missing.
**Gaps G5, G6, G8, G10, G12, G15, G17 are the ones that make a lifecycle impossible today.**

---

## 9. System-Controlled Content (field-level classification)

Derived from the actual engine output (`report_generation.py` section builders). **None of these
fields may ever be customer-editable.** Any attempt to change them is a **carbon-data correction
request**, which must be resolved in the underlying CarbonTally workflow (§22) — never in a report.

| Section | Actual fields produced | Classification |
|---|---|---|
| `metadata` | report id, report type, reporting year, engine + version, generated-at, template id, provenance labels | **System-controlled (all)** |
| `organization` | organisation id, organisation name, organisation-metadata values | **System-controlled (all)** (profile edits belong to Organisation admin) |
| `period` | `start_date`, `end_date`, `reporting_year` | **System-controlled (all)** |
| `totals` | `status` (`available`/`insufficient_data`), `total_co2e_kg`, `unit` (`kg CO2`/`kg CO2e`/`kg CO2/CO2e mixed`), `source`, `total_rows`, `note` | **System-controlled (all)** |
| `scopes` | `status`, `scopes.{label}.co2e_kg`, `.unit`, `unit`, `source` | **System-controlled (all)** |
| `activities` | `status`, `activities[].{activity_type, co2e_kg, quantity, unit, row_count}`, `total_activities`, `top_activities` cut-off | **System-controlled (all)** |
| `validation` | `status`, `ok`, `counts`, issue `{code, severity, message, entity_type, entity_id, field, context}` | **System-controlled (all)** |
| `benchmarking` | `status`, `metrics[].{key,label,unit,status,value,numerator,denominator,baseline_value,delta,delta_pct,comparison,source,scope,facility_id,activity_type,note}`, `by_scope` | **System-controlled (all)** |
| `provenance` | `gas_coverage`, `factor_sources`, `factor_sets`, `countries`, `note` | **System-controlled (all)** |
| `calculation` | `status`, `methodology`, `algorithm_version`, `figures_from`, `snapshot_verification[].{snapshot_id,match,tampered,discrepancy}`, `unit` | **System-controlled (all)** |
| `lineage` | `emissions_logs.{count,reporting_year}`, `emission_factors.{resolved,factor_ids}`, `aggregate.{total_rows,by_scope_count}`, `source` | **System-controlled (all)** |
| `generation` | `generated_at`, `engine`, `engine_version`, `template_id` | **System-controlled (all)** — and the source of non-determinism (§19.4) |

### 9.13 System-controlled summary rule

> **System-controlled = every key produced by `ReportGenerationEngine` inside the twelve
> sections.** The narrative overlay is stored in a **separate namespace** (§15) precisely so that
> system keys and editable keys can never collide.

---

## 10. Customer-Editable Content

**The engine produces no editable content today.** There is no editable field anywhere in the
12-section output. The editable set is therefore a **new, deliberately bounded namespace** — not a
relaxation of existing fields.

### 10.1 Recommended editable set (bounded, narrative-only)

| Key (proposed namespace) | Type | Constraint |
|---|---|---|
| `management_commentary` | text | Plain text; max length; no HTML |
| `organisational_context` | text | Plain text; max length; no HTML |
| `operational_changes_explanation` | text | Explains variation against the system figures |
| `initiatives` | structured list (title + text) | Bounded item count |
| `reduction_actions` | structured list (title + text + optional target year) | Bounded item count |
| `future_plans` | text | Plain text |
| `section_notes.{section_id}` | text | Optional per-section caveat, explicitly labelled as customer commentary |

**Every editable field must render as clearly attributed customer narrative**, visually and
semantically distinct from system figures.

### 10.2 Explicitly NOT editable

Any key present in the system sections (§9). The overlay must be **rejected server-side** if it
contains a system key, a nested path into a system section, or a reserved name.
**Validation is by allowlist, never by blocklist.**

### 10.3 Formatting and injection constraints (specification)

* **Plain text only.** No HTML, no raw Markdown rendering, no embedded script.
* Output is escaped by the renderer (`pdf_render._escape` already escapes `& < >`).
* **No links** in the first implementation (avoids phishing/attribution risk in a deliverable).
* **Maximum lengths** per field and per version (numeric limits are a PO decision — §34-A3).
* **No file attachments, images or arbitrary JSON editing.**
* Narrative text is **untrusted input** and must never be placed in any AI system prompt (§29).

---

## 11. Approval-Controlled Content

| Item | Meaning | Immutability |
|---|---|---|
| Approved version identity | `report_id` + `version_number` (+ version id) | Frozen at approval |
| Approver identity | actor id, actor type (`org_user` / `consultant` / `internal_staff`) | Frozen |
| Approval timestamp | UTC | Frozen |
| Approval decision | `approved` / `changes_requested` / `rejected` | Frozen, append-only |
| Approval comments | optional rationale | Frozen |
| Approval invalidation | who / when / why an approval was revoked | Append-only |
| Finalization timestamp | UTC | Frozen |
| Final PDF artefact | storage object identity | Immutable once written |
| Final PDF hash | content hash of the stored artefact | Immutable |
| Final version identifier | the version the artefact was produced from | Immutable |

**Rule:** once a version is `approved`, its **identity and decision record** are immutable. Once
finalised, the **artefact** is immutable. Only new versions may carry new approvals.

---

## 12. Proposed Lifecycle State Machine

### 12.1 Design analysis of the naive five-state model

The prompt's candidate chain was `DRAFT → EDITED → REVIEWED → APPROVED → FINAL`. Each element
was evaluated against what the repository can actually support:

| Candidate state | Evaluation | Decision |
|---|---|---|
| `DRAFT` | Necessary: a version exists but is not yet put forward. | **Keep as a state.** |
| `EDITED` | **Not a state.** Any edit produces a *new* version or mutates the overlay of an *existing draft*; "edited" is a **property/event** of a draft, not a lifecycle stage. Two states would double the transition surface for no gain. | **Demote to an event** (`narrative_edited`). |
| `REVIEWED` | `REVIEWED` is a **true state** because review completion is a distinct gate that approval depends on. | **Keep as a state.** |
| `APPROVED` | Necessary and distinct: approval is the legal/assurance act. | **Keep as a state.** |
| `FINAL` | Distinct from approved: approval authorises the *content*; finalization produces and freezes the *deliverable*. A report can be approved and not yet finalised (e.g. PDF generation pending). | **Keep as a state.** |
| `REJECTED` | Required: a reviewer or approver must be able to decline. | **Add.** |
| `CHANGES_REQUESTED` | Required: the most common real outcome of review — "edit and re-submit". | **Add.** |
| `SUPERSEDED` | Useful to mark an approved version replaced by a newer approved version. Can be **derived** from "an approved version exists with a higher `version_number`". | **Derive, do not store.** |

### 12.2 Recommended states

```text
                 ┌──────────────── CHANGES_REQUESTED ─────────────┐
                 │                      │ (new version created)   │
                 ▼                      ▼                          │
   ┌────────┐  submit   ┌──────────┐  approve  ┌──────────┐ finalize ┌───────┐
   │ DRAFT  │ ────────► │ REVIEWED │ ────────► │ APPROVED │ ───────► │ FINAL │
   └────────┘           └──────────┘           └──────────┘          └───────┘
       │                     │                       │
       │ reject              │ reject                │ revoke approval
       ▼                     ▼                       ▼
   ┌──────────┐          ┌──────────┐        (approval revoked →
   │ REJECTED │          │ REJECTED │         version returns to DRAFT
   └──────────┘          └──────────┘         on a NEW version)
       │
       └── (a rejected version is retained; a new version is created to continue)
```

**Stored states:** `DRAFT`, `REVIEWED`, `CHANGES_REQUESTED`, `REJECTED`, `APPROVED`, `FINAL`.

These are **version states**. They are **distinct from** the existing generation queue statuses
(`pending`/`generating`/`completed`/`failed`), which remain unchanged and continue to describe
generation, not document lifecycle. **The two vocabularies must not be conflated** — the queue
answers "did the engine produce content?", the version state answers "what has been agreed?".

### 12.3 Generation-status → version-state relationship

| Queue status | Version state available |
|---|---|
| `pending` | (no version exists yet) |
| `generating` | (no version exists yet) |
| `failed` | (no version exists; `error_log` recorded) |
| `completed` | A version exists, in state **`DRAFT`** |

**Recommended:** version state defaults to `DRAFT` when the first version is created.

---

## 13. State Transition Matrix

Every transition carries: actor, authorization requirement, timestamp, audit event and immutable
history. **No transition may be performed without an audit event.**

| # | From | Action | To | Actor | Conditions | Audit event |
|---|---|---|---|---|---|---|
| T1 | *(none)* | `generate` | `DRAFT` | Org Owner/Admin/Member; consultant (active grant); staff (permitted) | Generation succeeded; version created | `report.generated` |
| T2 | `DRAFT` | `edit_narrative` | `DRAFT` (unchanged) | Org Owner/Admin/Member (per policy); consultant (if permitted) | Actor may edit; overlay validates; version not `FINAL` | `report.narrative_edited` |
| T3 | `DRAFT` | `submit_review` | `REVIEWED` (pending review) → **`REVIEWED`** | Org Owner/Admin/Member | Version is `DRAFT`; no open blocking comments (per policy) | `report.review_submitted` |
| T4 | `DRAFT` | `add_comment` | `DRAFT` (unchanged) | Reviewer/Approver/Consultant/Staff (per visibility) | Comment permitted on this version | `report.comment_added` |
| T5 | `REVIEWED` | `add_comment` | `REVIEWED` (unchanged) | Reviewer/Approver | — | `report.comment_added` |
| T6 | `REVIEWED` | `resolve_comment` | `REVIEWED` (unchanged) | Comment author or approver | Comment exists | `report.comment_resolved` |
| T7 | `REVIEWED` | `request_changes` | `CHANGES_REQUESTED` | Reviewer/Approver (incl. consultant/staff per policy) | Version is `REVIEWED` | `report.changes_requested` |
| T8 | `REVIEWED` | `reject` | `REJECTED` | Reviewer/Approver | Version is `REVIEWED` | `report.rejected` |
| T9 | `CHANGES_REQUESTED` | `new_version` | `DRAFT` (new `version_number`) | Org Owner/Admin/Member; consultant (if permitted) | New version created | `report.version_created` |
| T10 | `REJECTED` | `new_version` | `DRAFT` (new `version_number`) | Org Owner/Admin/Member | New version created | `report.version_created` |
| T11 | `REVIEWED` | `approve` | `APPROVED` | **PO DECISION (§17)** — recommended Org Owner (and Admin per P4) | Version is `REVIEWED`; actor authorised; **stale check passes** (§26) | `report.approved` |
| T12 | `APPROVED` | `finalize` | `FINAL` | Approved actor or a system/authorised finaliser | Version is `APPROVED`; PDF rendered + stored + hashed successfully | `report.finalized` |
| T13 | `APPROVED` | `revoke_approval` | `DRAFT` (on a **new** version) | Actor with approval authority (PO DECISION §34-A6) | Reason recorded | `report.approval_revoked` |
| T14 | `APPROVED` | `edit_narrative` | **REJECTED transition** | — | **Prohibited**: an approved version is immutable. Actor must create a new version (T9) instead. | `report.edit_denied_approved` |
| T15 | `FINAL` | `edit_narrative` | **REJECTED transition** | — | **Prohibited**: final deliverable is immutable. | `report.edit_denied_final` |
| T16 | `FINAL` | `download` | `FINAL` (unchanged) | Any actor with view rights | Version is `FINAL` | `report.downloaded` *(policy — §34-A11)* |
| T17 | `FINAL` | `new_version` | `DRAFT` (new `version_number`) | Org Owner/Admin/Member | Explicitly permitted: a new reporting cycle or correction creates a new version; the prior `FINAL` remains unchanged and becomes **superseded (derived)** | `report.version_created` |
| T18 | any | `view` | unchanged | Any actor with view rights | Org/grant scope holds | *(optional — §34-A11)* |

### 13.1 Transition invariants

1. **No transition skips a gate.** `DRAFT → APPROVED` is invalid; `APPROVED → FINAL` requires
   approval first.
2. **`FINAL` is terminal** for a version. It can never leave `FINAL`, only be superseded by a
   *new* version.
3. **Approval is version-bound.** Transition T11 records the exact `version_id`; a later version
   does not inherit it.
4. **Every transition is audited** with actor, timestamp, from-state, to-state and version id.
5. **Every transition is authorised server-side.** The UI is never the boundary.
6. **Rejection is retained, never deleted** — a rejected version remains readable in history.

---

## 14. Versioning Semantics

Each question from the prompt, answered against repository evidence:

| Question | Answer | Basis |
|---|---|---|
| Is every generation a version? | **Yes.** T1 creates version N on every successful generation. | E4 |
| Is every customer edit a new version? | **Recommended: no — within `DRAFT`, narrative edits mutate the draft's overlay and emit an edit event. A new version is created when a `DRAFT` is superseded (T9/T10/T17).** This keeps version count meaningful rather than per-keystroke. | §12.1 |
| Is editing performed against a draft version? | **Yes — enforced.** Editing an `APPROVED`/`FINAL` version is rejected (T14/T15). | §13 |
| Is approval attached to a version? | **Yes — must be.** Approval records `version_id`, approver and timestamp. | §11 |
| Is finalization attached to a version? | **Yes.** The artefact records the `version_id` it was produced from. | §19 |
| Can two versions coexist? | **Yes.** All versions are retained; exactly one may be `is_current`. | E15, §7.3 |
| What should `is_current` mean? | **Exactly one version per report is "current"** = the highest `version_number`. Must be a derived, transactionally enforced invariant (fixes G5). | E12/E13 |
| Can an old version be viewed? | **Yes** — `GET /{id}/versions` + a version-scoped detail/content read. | E2 |
| Can an approved version be superseded? | **Yes** — by a newer approved version. "Superseded" is **derived**, not stored. | §12.1 |
| Does a new version invalidate the previous approval? | **No — it does not retroactively invalidate it; it supersedes it as the organisation's current authorised version.** The prior approval remains in history attached to its own version. | §18 |
| Can a final version ever be edited? | **No. Never.** Superseded only by a new version (T17). | §13 |

### 14.1 Recommended semantic model

```text
report instance (report_generation_queue.id)
 └── version 1  (report_versions, version_number=1)  status=DRAFT → REVIEWED → APPROVED → FINAL
 └── version 2  (report_versions, version_number=2)  status=DRAFT → ...  (is_current derived)
 └── version 3  ...
```

**Version content is composed of two persisted layers:**

```text
report_versions.content          =  SYSTEM CONTENT  (engine output; immutable once written)
report_versions.narrative_overlay =  NARRATIVE OVERLAY (customer-authored; editable pre-approval)
                                       ↓ (read-time composition)
                            EFFECTIVE VERSION CONTENT
```

**Recommendation: EXTEND `report_versions`** with a `status`, `narrative_overlay` and the
approval/finalization columns (§25 Option A) rather than adding a parallel versioning structure.
`content` keeps its current meaning (engine output) so existing readers and tests are unaffected.

### 14.2 Why not per-edit versions

Creating a version on every keystroke would: inflate version numbers meaninglessly, make
`is_current` semantics noisy, and make "what changed" unreadable. A version should correspond to
**a submitted state of the report**, not to an editing session.

---

## 15. Customer Narrative Overlay

### 15.1 Placement

**Recommended:** store the overlay **inside the version row** as a dedicated JSONB column
(proposed `narrative_overlay` on `report_versions`), **not** merged into `content`.

Rationale:

* Keeps system content provably untouched — the overlay physically cannot overwrite it.
* Makes the "system vs customer" distinction auditable and diffable.
* Composes at read time, so a report can be rendered with or without narrative.

**Alternative considered and rejected for v1:** storing the overlay in
`report_generation_queue.user_edits`. That column is report-scoped (not version-scoped), so it
cannot survive multiple versions and would break the version-bound edit rule (§13 T14/T15).
It may remain a legacy/unused column; **do not build the lifecycle on it.**

### 15.2 Editing rules

| Rule | Requirement |
|---|---|
| Section-level editing | **Permitted only** for the bounded narrative keys (§10.1). System sections are read-only. |
| Arbitrary JSON editing | **Prohibited.** Allowlisted keys and types only. |
| Validation | Server-side, on every write: key allowlist, type checks, length limits, plain-text only. |
| Who may edit | Per §22 matrix + PO decision P3 (recommended: Owner + Admin + Member; Viewer never). |
| Consultants editing on behalf of clients | **PO DECISION (§34-A1).** Precedent exists that consultants are first-class operators with active-grant scope, but narrative authorship on a *client's* deliverable is a policy choice. |
| Owners vs Admins | **PO DECISION (P3/P4).** Existing precedent: Customer Owner may self-approve a custom factor; Members may not. |
| Overlay on non-`DRAFT` versions | **Prohibited** (T14/T15). |

### 15.3 Explicit integrity statement

> A narrative edit is **not** a carbon-data correction. The overlay may never alter
> `emissions_logs`, `calculation_snapshots`, factor records, evidence, provenance, validation
> results, benchmark calculations, lineage or audit records. If any of those are wrong, the
> underlying CarbonTally workflow must correct them and the report must be **regenerated as a new
> version**.

---

## 16. Review and Comments

### 16.1 The dormant `report_comments` table (verified schema, E16)

| Column | Type | Note |
|---|---|---|
| `id` | UUID PK | — |
| `report_id` | UUID NOT NULL | attaches a comment to a report |
| `user_id` | UUID NOT NULL | author |
| `section_id` | VARCHAR | **matches the 12 engine `section_id` values exactly** |
| `comment` | TEXT NOT NULL | body |
| `comment_type` | VARCHAR | **no vocabulary defined anywhere** |
| `is_resolved` / `resolved_at` / `resolved_by` / `resolution_notes` | — | resolution lifecycle |
| `created_at` / `updated_at` | TIMESTAMPTZ | — |

**Assessment: suitable for report review — a good foundation.**

| Aspect | Verdict |
|---|---|
| Attaches to a report | ✅ |
| Attaches to a section | ✅ |
| Resolution lifecycle | ✅ |
| Author identity | ✅ |
| **Version binding** | ❌ **missing** — a comment cannot be pinned to `version_number` |
| **Tenant scope** | ❌ **missing** — no `organization_id` (must be derived via the report) |
| **Internal/external visibility** | ❌ **missing** — no visibility flag |
| Comment typing | ⚠ `comment_type` exists but carries no vocabulary |

### 16.2 Recommended approach

**REUSE + EXTEND `report_comments`.** Do **not** create a new comment table, and do **not** reuse
`user_feedback`, `issues`, messaging or PE approval structures for report review.

Recommended bounded additions (specification only — no migration in this task):

| Addition | Purpose |
|---|---|
| `version_number` (or `version_id`) | Bind a comment to the version it reviews (a comment on v1 is not a comment on v2) |
| `organization_id` | Direct tenant scoping (supports RLS and efficient scoped reads) |
| `visibility` (`internal` / `shared`) | Distinguish CarbonTally/consultant-internal notes from customer-visible review comments |
| `comment_type` vocabulary | Recommended values: `review_note`, `change_request`, `approval_note` |

### 16.3 Comment policy rules (recommended)

| Rule | Recommendation |
|---|---|
| Do comments become part of the final report? | **No.** Comments remain **separate** from report content. The deliverable contains no internal commentary. |
| Who can comment | Reviewers/approvers, consultants (active grant), internal staff (per permission). Customers on their own report if permitted. |
| Can customers see internal comments | **No** — internal comments are staff/consultant-only (§34-A7). |
| Can consultants see customer comments | **Yes** — within an active grant. |
| Can staff see all comments | **Yes** — within their permission scope. |
| Deletion | Comments are **never hard-deleted**; resolution is recorded. |
| Blocking semantics | An unresolved `change_request` comment should **block approval** (§34-A9). |

---

## 17. Approval Model

### 17.1 Who may approve — evidence and evaluation

**Repository precedent found (cited as precedent, not as automatic policy):**

* AGENTS.md §16 records a **ratified PO decision**: a **Customer Owner MAY self-approve** a custom
  factor; a Customer Member may not unless separately authorized; a Customer Viewer may not.
* Report generation currently requires only `require_org_member()` — *generation* is open to any
  org member, and there is **no approval gate at all** (E2).

**Candidate approvers evaluated:**

| Candidate | Evaluation | Recommendation |
|---|---|---|
| **Customer Owner** | Strongest precedent: the Owner is the organisation's authority and may already self-approve factors. The report is the organisation's own assertion. | **Recommended primary approver.** |
| **Customer Admin** | Admins hold org-wide administrative rights; allowing Admin to approve is low-risk and operationally useful. | **Recommended co-approver (P4).** |
| **Customer Member** | Members author data but are not organisational authorities. | **Not recommended.** |
| **Customer Viewer** | Read-only by definition. | **Not recommended.** |
| **Consultant** | Consultants are first-class operators with active-grant scope, but approving a **client's** assertion creates an assurance-like implication the client did not make. | **PO DECISION (§34-A2).** Recommended: **no** — review and request changes only. |
| **Internal staff** | Staff approval would imply CarbonTally asserts the report's correctness — conflicting with the Phase 7 positioning that CarbonTally is **not** an auditor/verifier and provides QC, not assurance. | **PO DECISION (§34-A2).** Recommended: **no** — review and comment only. |

### 17.2 Explicitly addressed: may a Customer Owner self-approve a report?

**Recommended answer: YES — with conditions.**

1. The report is an **authoritative presentation of the organisation's own persisted data**. The
   organisation is the party making the assertion; no external party's approval is implied.
2. There is a **direct, ratified precedent**: the Owner may self-approve a customer factor
   (AGENTS.md §16).
3. CarbonTally's Phase 7 positioning is **support, not assurance**. Requiring a CarbonTally staff
   approval would contradict that positioning by implying CarbonTally validates the content.

**Conditions (recommended):**

* Approval is bound to a **specific version** (`version_id`).
* Approval is **audited** with actor + timestamp.
* Self-approval is **not** permitted while unresolved blocking `change_request` comments exist.
* Self-approval **never** implies or displays any assurance, certification or audit claim.

> This is a **recommendation**. The final rule is **PO DECISION (P4 / §34-A2)**.

### 17.3 Approval record contents

Approval must capture, at minimum: `version_id`, `report_id`, `version_number`, approving
`user_id`, `actor_type`, `approved_at` (UTC), decision, optional rationale, and the
`content_hash` of the approved effective content (§19.4).

### 17.4 Approval vocabulary

Recommended decision values: `approved`, `changes_requested`, `rejected`.
Recommended actor types reuse the **existing Phase 7 vocabulary** (`ACTOR_ORG_USER`,
`ACTOR_CONSULTANT`, `ACTOR_INTERNAL_STAFF`) — do not invent a parallel actor model.

---

## 18. Post-Approval Change Policy

### 18.1 Options evaluated

**Option A — Approved version is immutable; any change creates a new draft version and approval
must happen again.**

* ✅ Strongest integrity: the approved artefact can never silently drift from what was approved.
* ✅ Simplest to reason about and to audit ("what was approved is what exists").
* ✅ Matches the append-only posture of `calculation_snapshots` and `audit_trail`.
* ⚠ Requires re-approval after any narrative tweak (acceptable: finalisation should follow
  approval promptly).

**Option B — Approved version can be edited and approval is automatically revoked.**

* ✅ Allows late corrections without a new version.
* ❌ **Mutates an approved record** — an approved version's content would change after approval,
  destroying the meaning of the approval and any artefact already rendered from it.
* ❌ Audit reconstruction becomes ambiguous (what did the approver actually approve?).
* ❌ Conflicts with the evidence/append-only architecture.

**Option C — Some post-approval narrative edits are permitted without reapproval.**

* ✅ Operationally convenient.
* ❌ Requires a policy distinguishing "safe" from "unsafe" edits — reintroducing the integrity
  ambiguity Option A eliminates.
* ❌ Two versions could differ while both claim the same approval.

### 18.2 Recommendation

> **Option A. Any post-approval content change invalidates approval and requires a new version
> with a new approval.**

Stated as a hard rule:

```text
APPROVED or FINAL version content  ⇢  IMMUTABLE
Any content change                 ⇢  NEW VERSION (version_number + 1), status = DRAFT
New version                        ⇢  requires its own REVIEW + APPROVAL (+ FINALIZE)
Prior version                      ⇢  retained unchanged; becomes SUPERSEDED (derived)
```

**Rationale specific to CarbonTally:** the report is an evidence-backed presentation of
provenance-preserved carbon data. The platform's credibility rests on *"the number you can see
today is the number that was approved."* Options B/C break that property.

**Clarification of "invalidates approval":** the *prior* approval record is **not deleted or
rewritten** — it remains true of the *prior* version. It is **superseded** as the organisation's
current authorised version. "Invalidate" means "no longer the current approval", not "erased".

### 18.3 Consequence — the golden rule

> **Approval freezes the meaning of the report version; finalization freezes the deliverable.**

---

## 19. Final / Frozen PDF Model

### 19.1 Current state (verified)

* `render_branded_pdf(report, content, brand) -> bytes` (E21) — **pure bytes out, never stored**.
* The PDF is generated on demand at `GET /{id}/pdf`.
* `report_generation_queue` **already has** `final_report_url`, `final_report_file_name`,
  `final_report_size_bytes` (E14) — but the PDF path **does not populate them**.
* The PDF identifies `report_type` and `reporting_year`, **not the version** (E23).
* The footer embeds `date.today()`; reportlab also writes `/CreationDate` and a document `/ID`
  (E22) → **two renders of identical content produce different bytes**.

### 19.2 Is a frozen final PDF required?

**Recommended: YES.** A report that can be re-rendered to different bytes cannot be a traceable
deliverable, and an approval cannot be shown to correspond to a specific file.

### 19.3 Recommended model

```text
APPROVED version (version_id, version_number, content_hash of effective content)
        ↓ finalize
Render PDF from: approved version content + server-authorized brand
        ↓
Store object ONCE (private storage; no public URL)
        ↓
Record: artefact identity, storage path, byte size, SHA-256 of the stored bytes,
        renderer metadata, brand context, version_id it was produced from
        ↓
FINAL — never re-rendered, never overwritten
```

**Association:** the artefact is bound to **exactly one** `version_id`. Downloads of the final
report serve the **stored artefact**, never a fresh render.

### 19.4 The hashing question — a material finding

Because both the **engine content** (E7: `generated_at` timestamp) and the **PDF bytes**
(E22: `CreationDate`, `/ID`, footer date) are **non-deterministic**, the specification must
distinguish two hashes:

| Hash | Over what | Purpose | Reproducible? |
|---|---|---|---|
| **Content hash** | A **canonical, normalised** serialisation of the *effective version content*, with volatile keys excluded (`generation.generated_at`) | Ties approval and the artefact to the exact content | **Yes** (must be) |
| **Artefact hash** (`pdf_sha256`) | The **exact stored PDF bytes** | Tamper detection for the specific stored file | Not required to be reproducible — it identifies *this* file |

**Specification position:** approval records the **content hash**; the artefact record stores the
**byte hash** of the stored file. Conflating them would either make approval unverifiable or make
the artefact hash meaningless.

**Implementation note (not implemented):** achieving a reproducible PDF would additionally require
rendering with fixed document metadata (no wall-clock date, fixed `/ID`) — a change to
`pdf_render`. The two-hash model removes the need to require this.

### 19.5 Can `report_versions` hold this, or is a separate artefact record needed?

**Recommended: `report_versions` holds the approval + finalization metadata** (`status`,
`approved_by`, `approved_at`, `finalized_at`, `content_hash`, `final_report_url`, `pdf_sha256`),
which is sufficient for a **one-artefact-per-version** model — the model this specification
recommends. A separate artefact table is justified only if multiple artefacts per version must be
retained (re-renders, alternate brands, multiple locales) — see §25 Option C.

### 19.6 Storage and security requirements for the frozen artefact

* Stored in **private** storage; **no public URL**; access only via an authorised API call.
* Never log or expose the storage path or any signed URL (AGENTS.md §68).
* The download authorisation is re-checked **server-side** on every request.
* Storage-object deletion must **not** be able to silently orphan or destroy a final artefact
  (§28).

### 19.7 PDF metadata requirements

The final PDF should carry, in its own metadata and/or cover: report instance id, report type,
reporting year, **version number**, approval timestamp, and the branding actually applied.
*(Adding version/approval metadata to the PDF is a change to `pdf_render` — out of scope here.)*

### 19.8 Known gap to record

`download_report`'s docstring states *"no PDF rendering exists in V3 — documented backend gap"*
while `GET /{id}/pdf` exists (E30). This is **documentation drift** that must be corrected when
the lifecycle is implemented; it is not a functional defect.

---

## 20. Provenance Requirements

The report lifecycle **reuses** existing provenance and adds **no competing model**.

### 20.1 What a version must preserve

| Preserved reference | Source of truth | Required? |
|---|---|---|
| Report instance identity | `report_generation_queue.id` | ✅ |
| Version identity + number | `report_versions.id`, `.version_number` | ✅ |
| Engine output (system content) | `report_versions.content` | ✅ |
| Engine identity + version | `content.generation.engine`, `.engine_version` | ✅ (already emitted) |
| Reporting period | `content.period` | ✅ (already emitted) |
| Calculation references | `content.calculation.snapshot_verification[].snapshot_id` | ✅ (already emitted) |
| Factor provenance | `content.provenance.{gas_coverage, factor_sources, factor_sets, countries}` | ✅ (already emitted) |
| Source lineage | `content.lineage` (`emissions_logs.count`, `emission_factors.factor_ids`) | ✅ (already emitted) |
| Validation status | `content.validation.status`, `.ok`, `.counts` | ✅ (already emitted) |
| **Underlying snapshot integrity** | `calculation_snapshots.factor_id`, `.co2e_multiplier`, `.content_hash`, `.algorithm_version` | ✅ via reference — **never copied or recomputed** |
| Evidence chain | `domain/evidence.py` per `log_id` | ✅ via reference — not embedded in the report |
| Brand applied | server-resolved `BrandContext` (D21.7) | ✅ recorded on the artefact |
| Approval identity/time | approval record | ✅ |
| Content hash | canonical effective content | ✅ (§19.4) |

### 20.2 Provenance rules

1. **Reference, never duplicate.** The report references `calculation_snapshots` and evidence by
   id; it must not copy or re-derive them.
2. **Never recompute at render time.** The PDF renders the stored version content; it does not
   re-run the engine.
3. **`gas_coverage` labels are immutable.** `kg CO2` / `kg CO2e` / `kg CO2/CO2e mixed` must never
   be normalised, relabelled or averaged for presentation convenience.
4. **The evidence drill-down must remain reachable** from a final report (report → calculation →
   evidence), subject to the viewer's authorization.
5. **A report is not evidence.** The report presents evidence; it does not replace
   `calculation_snapshots` or the evidence chain.

---

## 21. Audit Requirements

### 21.1 Substrate — REUSE `audit_trail`

Verified (E25/E26): `audit_trail` is append-only (Phase 7 immutability trigger), carries
`action_type`, `table_name`, `record_id`, `performed_by`, `performed_at`, `old_data`, `new_data`,
`changes`, `ip_address`, `user_agent`, `metadata`, and the Phase 7 taxonomy stores
`category` / `origin` / `outcome` / `actor_type` / `organization_id` inside `metadata`. It
already defines **`CAT_REPORT = "report"`**.

**Do NOT create a parallel report audit table.**

### 21.2 Required audit events

| Event | Trigger | Category | Origin | Entity |
|---|---|---|---|---|
| `report.generated` | T1 | `report` | `system` (engine) + human requester | report |
| `report.version_created` | T9/T10/T17 | `report` | `human` | version |
| `report.narrative_edited` | T2 | `report` | `human` | version |
| `report.review_submitted` | T3 | `workflow` | `human` | version |
| `report.comment_added` | T4/T5 | `report` | `human` | version |
| `report.comment_resolved` | T6 | `report` | `human` | version |
| `report.changes_requested` | T7 | `report` | `human` | version |
| `report.rejected` | T8 | `report` | `human` | version |
| `report.approved` | T11 | `report` | `human` | version |
| `report.approval_revoked` | T13 | `report` | `human` | version |
| `report.finalized` | T12 | `report` | `human`/`system` | version + artefact |
| `report.final_pdf_rendered` | within T12 | `report` | `system` | artefact |
| `report.final_pdf_frozen` | within T12 | `report` | `system` | artefact |
| `report.downloaded` | T16 | `report` | `human` | version + artefact *(policy — §34-A11)* |
| `report.edit_denied_approved` | T14 | `authorization` | `human` | version |
| `report.edit_denied_final` | T15 | `authorization` | `human` | version |

**Note on taxonomy:** the existing action-prefix map already routes any `report*` action to
`CAT_REPORT` (`"report": CAT_REPORT`, E25). **No taxonomy change is required** to record these
events under the `report` category. `report.approval_revoked` / `report.finalized` etc. all
classify correctly by prefix.

### 21.3 Reconstruction requirement

Every lifecycle action must be reconstructable as:

```text
who        → performed_by + actor_type
when       → performed_at (UTC)
what version → record_id (version id) + metadata.version_number
what action  → action_type
what changed → changes / changed_fields (+ narrative field names, never full payloads)
previous state → old_data / metadata.status_from
new state      → new_data / metadata.status_to
```

**Payload discipline:** audit entries record **field names and statuses**, not full narrative
bodies or document content (consistent with `audit_helpers.changed_extraction_keys` and AGENTS.md
§78 — never log secrets or raw document content).

---

## 22. Authorization Matrix

### 22.1 Existing mechanisms (verified — reuse, do not bypass)

| Requirement | Mechanism |
|---|---|
| Customer organisation scope | `ensure_org_access`, `require_org_member`, `require_org_admin` |
| Consultant firm | `require_consultant` (active firm membership) |
| Consultant-client grant | `ensure_consultant_org_access` (ACTIVE grant only; ended/suspended denied) |
| Processing Entity | `require_entity_scope` + active entity |
| Internal staff | `require_internal_staff`, `require_staff`, `ensure_staff_permission` |
| Org audit/evidence reads | `ensure_org_audit_access` (owner/admin only) |
| RLS | **Not present on report tables** (E20) — see §22.3 |

### 22.2 Action × actor matrix

`?` = PO DECISION REQUIRED. No cell is guessed.

| Action | Customer Owner | Customer Admin | Customer Member | Customer Viewer | Consultant (active grant) | Internal Staff | PE |
|---|---|---|---|---|---|---|---|
| View report (list/detail/content) | ✅ | ✅ | ✅ | ✅ (read-only) | ✅ (active grant) | ✅ (per permission) | **No** |
| View version history | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **No** |
| Download persisted content | ✅ | ✅ | ✅ | ✅ (policy `?`) | ✅ | ✅ | **No** |
| Edit narrative | ✅ | ✅ | **?** (§34-A1) | **No** | **?** (§34-A1) | **No** | **No** |
| Submit for review | ✅ | ✅ | **?** | No | **?** | No | No |
| Add review comment | ✅ | ✅ | **?** | No | ✅ | ✅ | **No** |
| Add **internal** comment | No | No | No | No | ✅ (own firm) | ✅ | No |
| Resolve comment | ✅ | ✅ | **?** | No | ✅ | ✅ | No |
| Request changes | ✅ | ✅ | No | No | ✅ | ✅ | No |
| **Approve** | ✅ (recommended, §17.2) | ✅ (recommended P4) | **No** | **No** | **?** (§34-A2) | **?** (§34-A2) | **No** |
| Revoke approval | **?** (§34-A6) | **?** | No | No | No | No | No |
| **Finalize** (produce frozen PDF) | ✅ (same authority as approve) | ✅ | No | No | **?** | **?** | No |
| Download final PDF | ✅ | ✅ | ✅ | ✅ | ✅ (active grant) | ✅ (per permission) | **No** |
| **Delete a draft version** | **?** (§34-A8) | **?** | No | No | No | No | No |
| Delete an approved/final version | **NEVER** | **NEVER** | Never | Never | Never | Never | Never |

**PE column is all "No":** Processing Entities are **not** report consumers. PE work is
assignment-scoped processing; PE users must not gain access to customer report data
(AGENTS.md §12). This must be enforced server-side and is a **negative security test target**.

### 22.3 The report-table RLS finding (security — recorded, not fixed)

**Verified (E20):** no report table has `ENABLE ROW LEVEL SECURITY`, and no policy references a
report table. 21 RLS enablements exist elsewhere in the schema (including
`calculation_snapshots`, `factor_aliases`, `domain_events`, `import_batches`).

**Current consequence:** report authorization is enforced **only** at the API layer
(`ensure_org_access` after `reports.get_full()`). This is not a UI-boundary violation — the API
does check — but it means there is **no defence-in-depth** for reports, unlike carbon data.

**Specification requirements (not implemented here):**

1. Report-lifecycle tables must gain **explicit RLS** (enabled + org-scoped policies) as part of
   implementation, **or** carry a documented, deliberate application-level authorization
   justification (AGENTS.md §67).
2. **No existing RLS may be weakened** to make the lifecycle work.
3. Any new lifecycle table (if one is added) must ship with RLS from the start.
4. The proposed lifecycle must **never** widen access: it only adds gates.

> **This is a pre-existing security observation.** It is recorded because the proposed lifecycle
> must not be built on an unaudited assumption, and because enabling RLS on report tables is a
> requirement of the implementation phase — not a change made by this specification task.

### 22.4 UI is never the boundary

Every row in §22.2 must be enforced **server-side**. Disabling a frontend button, hiding an
approval control, or omitting a route is **not** authorization (AGENTS.md §7, §44).

---

## 23. API Design (specification only)

### 23.1 Existing conventions to follow

* Router: `APIRouter(prefix="/api/v3/reports", tags=["V3 — Reports"])` (E2).
* Auth: `Depends(require_org_member())` + `ensure_org_access(current_user, report["organization_id"])`.
* Repository access via `RepositoryBundle = Depends(get_repositories)`.
* Errors: `404` not found; `409` wrong lifecycle state; `422` bad input.
* Branding: server-resolved `resolve_report_branding` (never client-supplied).
* Content responses return persisted data only; nothing is synthesised.

### 23.2 Proposed additions (smallest coherent set)

| Method | Path | Actor | Request | Response | Transition | Audit | Idempotency | Concurrency |
|---|---|---|---|---|---|---|---|---|
| `GET` | `/api/v3/reports/{id}/versions/{version_number}` | view rights | — | version detail + overlay + status | — | — | N/A | N/A |
| `PATCH` | `/api/v3/reports/{id}/versions/{version_number}/narrative` | edit rights | `{ narrative: {...}, expected_status: "draft" }` | updated version | T2 | `report.narrative_edited` | Repeating same payload is a no-op | `expected_status` + optimistic check |
| `POST` | `/api/v3/reports/{id}/versions/{version_number}/submit` | submit rights | `{ note? }` | version (`REVIEWED`) | T3 | `report.review_submitted` | Submitting an already-submitted version → `409` | state guard |
| `POST` | `/api/v3/reports/{id}/versions/{version_number}/comments` | comment rights | `{ section_id?, comment, comment_type, visibility }` | comment | T4/T5 | `report.comment_added` | Client-supplied idempotency key optional | — |
| `POST` | `/api/v3/reports/{id}/versions/{version_number}/comments/{comment_id}/resolve` | comment rights | `{ resolution_notes? }` | comment | T6 | `report.comment_resolved` | Resolving twice → no-op/`409` | — |
| `POST` | `/api/v3/reports/{id}/versions/{version_number}/request-changes` | review rights | `{ note? }` | version (`CHANGES_REQUESTED`) | T7 | `report.changes_requested` | `409` if not `REVIEWED` | state guard |
| `POST` | `/api/v3/reports/{id}/versions/{version_number}/reject` | review rights | `{ reason }` | version (`REJECTED`) | T8 | `report.rejected` | `409` if not `REVIEWED` | state guard |
| `POST` | `/api/v3/reports/{id}/versions/{version_number}/approve` | **approver (PO)** | `{ rationale?, expected_content_hash }` | version (`APPROVED`) | T11 | `report.approved` | Approving an approved version → `409` | **`expected_content_hash` must match** (§26) |
| `POST` | `/api/v3/reports/{id}/versions/{version_number}/revoke-approval` | **PO** | `{ reason }` | new version `DRAFT` | T13 | `report.approval_revoked` | `409` if not `APPROVED` | state guard |
| `POST` | `/api/v3/reports/{id}/versions/{version_number}/finalize` | approver/finaliser | `{ }` | version (`FINAL`) + artefact metadata | T12 | `report.finalized` + artifact events | **Idempotent**: re-finalising a `FINAL` version returns the existing artefact, does not re-render | state guard + `409` if not `APPROVED` |
| `GET` | `/api/v3/reports/{id}/versions/{version_number}/pdf` | view rights | — | final stored artefact (only when `FINAL`) | T16 | `report.downloaded` (policy) | N/A | N/A |
| `POST` | `/api/v3/reports/{id}/versions` | edit rights | `{ from_version_number, reason? }` | new `DRAFT` version | T9/T10/T17 | `report.version_created` | `409` if source not `CHANGES_REQUESTED`/`REJECTED`/`FINAL` | sequence via `next_version_number` |

**Unchanged (must not regress):** `GET /types`, `GET ""`, `POST ""`, `GET /{id}`, `GET /{id}/content`,
`GET /{id}/versions`, `GET /{id}/download`, `GET /{id}/pdf` (P2 — see §34 note on the legacy
`/{id}/pdf` live-render route vs the new stored-artefact route).

### 23.3 API design rules

1. **Version-scoped mutations.** Every lifecycle mutation addresses a specific
   `version_number` — never "the report".
2. **State guards are server-side.** Wrong-state calls return `409` with the actual state.
3. **No client-supplied actor.** Actor identity always comes from the authenticated session.
4. **No client-supplied brand.** Branding remains server-resolved (E24).
5. **Approval requires the expected content hash** so a stale approval cannot be forged (§26).
6. **`finalize` is idempotent** — duplicate finalisation must not create a second artefact.
7. **Final PDF downloads serve the stored artefact** — never a fresh render.
8. **No endpoint returns system content as "editable".** The response must clearly separate
   `content` (system) from `narrative_overlay` (editable).

---

## 24. Frontend Design (specification only)

### 24.1 Existing surface (verified)

* `frontend/src/v3/reports/ReportsPage.jsx` (369 lines) — list + generate modal + filters +
  status badge + a "Version" column (E27).
* `frontend/src/v3/reports/ReportDetailPage.jsx` (263 lines) — status, metadata, content preview,
  version list, downloads. No edit/approve/comment controls (E28).
* `frontend/src/v3/api.js` — `listReports`, `getReport`, `getReportContent`, `getReportVersions`,
  `getReportTypes`, `generateReport`, `downloadReport`, `downloadReportPdf`, `getClientReports`.
* D21 tokens (`v3/tokens.css`) and shared UI components (`v3/components/ui/*`) are the design system.

### 24.2 Proposed report experience

```text
Report
 ├── Overview        status badge, period, organisation, brand, lifecycle timeline
 ├── Content         the 12 system sections (READ-ONLY, provenance-labelled)
 ├── Narrative       customer-editable fields (editable when DRAFT; read-only otherwise)
 ├── Evidence        drill-down: calculation → snapshot → evidence (existing EvidenceTrail)
 ├── Version history version list with state + approver + timestamps (existing + extended)
 ├── Review          comments by section, resolve / request changes
 ├── Approval        approve / request changes / reject (gated, audited)
 └── Final PDF       finalised artefact download (only when FINAL)
```

### 24.3 Per-actor view

| Element | Customer Owner/Admin | Customer Member | Customer Viewer | Consultant (active grant) | Staff | PE |
|---|---|---|---|---|---|---|
| Content (system sections) | read | read | read | read | read (perm) | — |
| Narrative editing | ✅ | per P3 | ❌ | per P3 | ❌ | ❌ |
| Review comments | ✅ | per P3 | ❌ | ✅ | ✅ | ❌ |
| Internal comments | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Approval controls | ✅ | ❌ | ❌ | per P4 | per P4 | ❌ |
| Final PDF | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

### 24.4 Required UI behaviours

1. **State badges** for version states (`Draft`, `In review`, `Changes requested`, `Rejected`,
   `Approved`, `Final`) — distinct from the existing generation badges (`Queued`, `Generating`,
   `Ready`, `Failed`). Both visible without ambiguity.
2. **System vs narrative must be visually unmistakable.** System figures render in the established
   data presentation; narrative renders as attributed commentary (e.g. "Customer narrative").
3. **Final lock:** when a version is `FINAL`, edit controls are absent/disabled **and** the server
   rejects any attempt (`409`).
4. **Approval confirmation** states what is being approved: version number, reporting period, and
   the consequence ("any further change requires a new version and a new approval").
5. **Approval must show the content hash** (or a short human-readable digest) so the approver
   approves a specific artefact identity.
6. **Version comparison:** show a **meaningful report-level change summary** using the existing
   `change_summary` / `notes` fields (E15) plus narrative field names — **never a raw JSON/database
   diff**.
7. **No fabricated statistics.** `ReportsPage` already documents this principle; extend it.
8. **Fix the Version column:** the list endpoint must include `current_version` (or the column must
   derive from the versions endpoint) so it does not always display `v1` (E27).
9. **Accessible and responsive** per AGENTS.md §49/§50 and D21.
10. **No client-side lifecycle logic.** The UI reflects server state and never decides transitions.

---

## 25. Schema Design Options (specification only — no migration created)

### Option A — EXTEND `report_versions` (**RECOMMENDED**)

Add to `report_versions`: `status`, `narrative_overlay JSONB`, `approved_by`, `approved_at`,
`approved_decision`, `approval_comment`, `finalized_at`, `content_hash`, `pdf_sha256`, plus a
derived/single-valued guarantee for `is_current`.

| Criterion | Assessment |
|---|---|
| Advantages | One place per version holds content + overlay + status + approval + artefact metadata; matches the existing `UNIQUE(report_id, version_number)` spine; minimal new surface; existing readers unaffected (`content` keeps its meaning) |
| Disadvantages | `report_versions` becomes a wider table; the `is_current` invariant must be explicitly fixed |
| Auditability | ✅ Excellent — one row per version, joined to `audit_trail` by `record_id` |
| RLS implications | Extend the new report-table policies to this table (§22.3) |
| Migration complexity | **Low** — additive columns; optional backfill of existing rows to `status='DRAFT'` |
| Concurrency | Direct — row-level state allows `WHERE status = <expected>` guards |
| Future AI compatibility | ✅ Good — narrative overlay and system content stay separable, exactly what an AI narrative layer needs (§29) |
| **Recommendation** | **✅ Recommended** |

### Option B — Reuse `approval_requests` / `approval_decisions` (**NOT RECOMMENDED**)

| Criterion | Assessment |
|---|---|
| Advantages | Tables exist; their names sound generic |
| Disadvantages | **`approval_requests.assignment_id` is `NOT NULL REFERENCES processing_assignments(id)`** — report approvals have no assignment; would require a destructive change to an active PE table and would conflate two authorization domains |
| Auditability | ❌ Would mix PE workflow approvals with customer report approvals in one ledger |
| RLS implications | ❌ PE-scoped policies would have to be loosened or dual-purposed — **risk of weakening a boundary** |
| Migration complexity | **High** and risky |
| Concurrency | N/A |
| Future AI compatibility | Poor |
| **Recommendation** | **❌ Rejected** (§7.4) |

### Option C — Extend `report_versions` + new `report_version_artifacts` table

Extend `report_versions` for status/approval; add a dedicated artefact table
(`version_id`, `storage_path`, `byte_size`, `pdf_sha256`, `renderer_version`, `brand_kind`,
`created_at`, `created_by`).

| Criterion | Assessment |
|---|---|
| Advantages | Supports multiple artefacts per version (re-renders, brands, locales); clean separation of content/approval from deliverable |
| Disadvantages | More surface; most benefit unrealised in a one-artefact-per-version model |
| Auditability | ✅ Good |
| RLS implications | One more table to secure |
| Migration complexity | Medium |
| Concurrency | Slightly more complex (artefact uniqueness per version) |
| Future AI compatibility | Good |
| **Recommendation** | **⚠ Defer** — adopt only if multi-artefact per version becomes a real requirement |

### Option D — New dedicated report-approval event table

| Criterion | Assessment |
|---|---|
| Advantages | Full approval-decision history (approve → revoke → re-approve) as first-class rows |
| Disadvantages | Duplicates what `audit_trail` already records append-only; risks a second audit ledger |
| Auditability | ✅ but **redundant** with `audit_trail` |
| **Recommendation** | **❌ Rejected** unless the PO requires approval decisions queryable independently of the audit trail |

### 25.1 Selected model

> **Option A for the lifecycle**, with **Option C available** if a second artefact per version is
> later required. **Option B is explicitly rejected** for security and domain reasons.

### 25.2 `is_current` remediation (required in implementation)

Whichever option is chosen, the `is_current` **multiple-true** defect (E12) must be fixed. Options:
(a) demote prior rows in the same transaction; (b) drop reliance on the flag and derive current =
`MAX(version_number)`; or (c) a partial unique index enforcing at most one `TRUE` per `report_id`.
Option (c) is the strongest because it makes the invariant **structurally impossible** to violate.

---

## 26. Concurrency and Idempotency

### 26.1 Required protections

| Hazard | Recommended protection |
|---|---|
| Two simultaneous narrative edits overwriting each other | **Optimistic concurrency**: client sends the version it read; server compares `content_hash`/`updated_at` and returns `409` on mismatch |
| Two simultaneous approvals | **State guard + row lock**: `UPDATE ... WHERE id = $1 AND status = 'REVIEWED'`; a second caller gets 0 rows → `409` |
| Two simultaneous finalizations | **Idempotent finalize**: if `status='FINAL'` and an artefact exists, return the existing artefact; never render twice |
| Approval of a stale version | **`expected_content_hash` required** on approve; mismatch → `409` with the current hash |
| Finalization after a change since review | Finalize requires `status='APPROVED'`; any change after approval forces a new version (T14), so a changed version cannot be `APPROVED` |
| Duplicate `version_number` allocation | Existing `UNIQUE(report_id, version_number)` (E15) + `next_version_number()`; retry on unique violation |
| Concurrent new-version creation | Same unique constraint; only one insert can win |

### 26.2 The stale-approval rule (critical)

> Approval is valid only against the **exact content the approver saw**. Therefore the approval
> request must carry the `content_hash` the approver reviewed, and the server must reject the
> approval if the current content hash differs.

This is the single most important concurrency control in the lifecycle: without it, an approver
could approve stale content and the system would record an approval for content they never saw.

### 26.3 Idempotency summary

| Operation | Idempotent? | Behaviour on repeat |
|---|---|---|
| `generate` (`POST /reports`) | ❌ (creates a new instance) | Each call creates a new report instance — acceptable and explicit |
| `edit_narrative` | ✅ (same payload = same state) | No-op if identical; otherwise hash/ETag guard |
| `submit` | ✅ | `409` if already submitted |
| `comment` | ⚠ | Optional client idempotency key to prevent duplicate comments |
| `approve` | ✅ | `409` if already `APPROVED`, or hash mismatch |
| `finalize` | ✅ | Returns the existing artefact; never re-renders |
| `new_version` | ⚠ | Guarded by the source-state condition (T9/T10/T17) |

---

## 27. Failure and Edge Cases

| # | Scenario | Required behaviour |
|---|---|---|
| 1 | **Report generation fails** | `mark_failed` persists the real `error_log`; status `failed`; no version created; API returns `5xx`/mapped status with a user-safe message; **no fabricated content**; audited as `report.generated` with `outcome=failure` |
| 2 | **Generation succeeds but version persistence fails** | The report row is `completed` but no version exists. **Must be detected**: reads that expect a version return an explicit "version unavailable" state, not `v1`. Implementation should make generation+version write atomic where possible; otherwise reconcile. **Recorded as a gap (G4/G5).** |
| 3 | **Two users edit simultaneously** | Optimistic concurrency (§26); the loser gets `409` + the current hash and must re-read |
| 4 | **Approval attempted on a stale version** | Rejected with `409` + current `content_hash` (§26.2) |
| 5 | **Approval attempted on a draft** | Rejected `409` ("version is not in review") |
| 6 | **Approved report edited** | **Rejected** `409` (T14); the client is told to create a new version |
| 7 | **Final report edit attempted** | **Rejected** `409` (T15); final is immutable |
| 8 | **PDF generation fails during finalize** | Version remains `APPROVED` (not `FINAL`); real error surfaced; retryable; audited with `outcome=failure`; **never** mark `FINAL` without a stored artefact |
| 9 | **Final PDF hash mismatch (tamper/corruption)** | Download must fail closed; incident recorded in audit; the artefact is reported as **integrity-failed**, never silently served |
| 10 | **Final PDF storage failure** | Finalization aborts; version stays `APPROVED`; no partial/`FINAL` state is persisted |
| 11 | **Source carbon data changes after generation** | The existing version is **unaffected** (content snapshot is immutable). A new version reflects the change. **Recommended: surface a "data has changed since this version" indicator** using snapshot recency (`content.lineage` / snapshot timestamps) — see §34-A12 |
| 12 | **Source carbon data changes after approval** | The approved version remains the approved representation of **that** data. Recommended: **flag staleness** (never auto-invalidate silently) — §34-A12 |
| 13 | **Report regenerated after approval** | A new version is created (T17); the prior `FINAL`/`APPROVED` version is retained unchanged and becomes superseded (derived) |
| 14 | **User loses authorization during the lifecycle** | Every request re-authorises from the session; a revoked user's next action fails `403`. In-flight operations re-check. **Never** cache authorization in the client |
| 15 | **Consultant grant expires** | `ensure_consultant_org_access` denies (ended/suspended grants carry no access, D15). The consultant can no longer view/edit/approve; content remains with the customer |
| 16 | **Organisation membership changes** | Revoked members lose access on their next request; their historical audit entries remain |
| 17 | **Duplicate approval request** | Second request returns `409` (already approved); no second approval row |
| 18 | **Duplicate finalization request** | Idempotent: returns the existing artefact; **no** second render, no second artefact |
| 19 | **Report instance with no version** | All version-scoped endpoints return an explicit "no version yet" state; the UI must not display a fabricated version number (E27) |
| 20 | **Comment on a version that has since been superseded** | Comment remains attached to its own version; it is **not** carried forward to the new version |

---

## 28. Data Retention and Immutability

### 28.1 Existing principles (verified context)

* `calculation_snapshots` is documented as *"Immutable forensic record… Append-only; never updated
  or deleted"*.
* `audit_trail` is append-only via the Phase 7 immutability trigger.
* N3 retention is a **configurable, server-side** capability managed through the admin control
  plane; retention must **not** weaken auditability, evidence or regulatory traceability
  (AGENTS.md §42).
* Retention tooling exists: `backend/services/retention.py`, `backend/tools/enforce_retention.py`.

### 28.2 Recommended retention rules

| Artefact | Retention | Deletable? |
|---|---|---|
| Report instance (`report_generation_queue`) | Retained; subject to org retention policy | Only per retention policy, and only when no `FINAL` version exists — **PO DECISION (§34-A10)** |
| Version (`report_versions`) — `DRAFT` | Retain while the instance exists | **PO DECISION** whether a draft may be deleted (§34-A8) |
| Version — `REJECTED` / `CHANGES_REQUESTED` | **Retain** — they are lifecycle history | No |
| Version — `APPROVED` | **Retained indefinitely** | **Never** |
| Version — `FINAL` | **Retained indefinitely** | **Never** |
| Final PDF artefact | **Retained indefinitely** | **Never** while the version exists |
| Comments | Retain with the version | Never hard-deleted; resolved instead |
| Audit records | Retain per audit policy | **Never** (append-only) |

### 28.3 Hard rules

1. **Approved and final versions are never deleted.** This is non-negotiable for an
   evidence-backed platform.
2. **Audit records are never deleted** (Phase 7 immutability).
3. **Final artefacts are never deleted while their version exists.**
4. **Storage deletion must not orphan a `FINAL` version.** Any storage-object deletion path must
   check for a referenced `FINAL` artefact first and refuse.
5. **Retention may remove drafts/instances only**, and only through the approved admin retention
   mechanism — never by an ad-hoc delete.

### 28.4 Legal position

**No legal or compliance claim is made in this document.** Whether a specific retention period is
required (and for how long) is **PO DECISION (§34-A10)** with legal review where applicable.
If retention policy is not established, no implementation may invent one.

---

## 29. AI-Assisted Narrative Boundary

### 29.1 Required boundary (normative)

```text
Authoritative CarbonTally data  (emissions_logs / calculation_snapshots / evidence)
          ↓
Deterministic report structure  (ReportGenerationEngine — 12 sections, fixed)
          ↓
Approved system-controlled facts  (immutable, provenance-preserved)
          ↓
Narrative generation  (deterministic template  OR  AI-assisted)   ← PO DECISION (P8)
          ↓
Customer review / edit  (narrative overlay only)
          ↓
Approval  (version-bound)
          ↓
Frozen final report  (+ artefact hash)
```

### 29.2 Hard prohibitions (the LLM must NEVER)

* calculate emissions;
* choose authoritative emission factors;
* invent evidence, source documents or provenance;
* alter calculation results or validation outcomes;
* alter the system-controlled sections;
* bypass authorization or read outside the caller's scope;
* directly write database state.

### 29.3 Required mechanism if AI is used

* Must use the **existing provider abstraction**: `backend/infra/llm_client.py` and
  `backend/infra/ai_runtime.py` (env-configured; OpenAI/Anthropic-compatible; truthful
  `provider_label()`; attribution that never reads the API key).
* **No new LLM client, no direct HTTP calls, no provider SDK in this codebase.**
* AI output is **candidate text only** — inserted into the *narrative overlay* as a draft that a
  human must review and approve. It can never write to `content` (system sections).
* Prompt-injection defence applies: system content is trusted; **any** document-derived or
  customer-derived text is untrusted and must never be placed in a system prompt.
* Attribution: if AI assisted, record the provider/model/version facts in the version metadata
  (the existing `ai_model_used` / `ai_tokens_used` / `ai_cost` columns already exist on
  `report_generation_queue`, E14 — a **REUSE** opportunity).

### 29.4 Deterministic vs AI-assisted

**PO DECISION REQUIRED (P8).** The repository does not determine it. What the repository does
establish is that a **deterministic/template-first** path is available today with **zero** new
risk, and that an AI-assisted path is architecturally prepared (§29.3). Recommended sequencing:
**deterministic template first**; AI-assisted later, behind the abstraction, once §22 of the
Phase 8 discovery (AI safety requirements) is satisfied.

### 29.5 What must not happen

* The narrative layer must not become the place where "the numbers are explained away". It may
  **explain** system figures; it may not **replace** them.
* AI must never be required for a report to be valid. A report must be producible and approvable
  with deterministic narrative only.

---

## 30. Ask CarbonTally Dependency

### 30.1 Why the report lifecycle constrains Ask CarbonTally

Ask CarbonTally will answer questions about emissions and reporting. If it cannot distinguish
*generated* from *approved* from *final*, it will present drafts as if they were agreed — a
truthfulness failure of exactly the kind the AI safety requirements prohibit.

### 30.2 Required report-state exposure to future controlled tools

The lifecycle must be exposed to future AI tools as **explicit, machine-readable state on the
version**, not as prose and not as a boolean "ready":

| Exposed field | Purpose |
|---|---|
| `report_id`, `report_type`, `reporting_year` | Identify the instance |
| `version_number`, `version_id` | Identify the version |
| `status` (`DRAFT`/`REVIEWED`/`CHANGES_REQUESTED`/`REJECTED`/`APPROVED`/`FINAL`) | The authoritative agreement state |
| derived "current version" | Whether this is the current version |
| `approved_at`, `approved_by` | Who authorised it, and when |
| `finalized_at`, artefact presence | Whether a frozen deliverable exists |
| `content_hash` | Identity of the approved content |

### 30.3 Assistant rules (normative for the future implementation)

1. The assistant **must not** present a `DRAFT`, `REVIEWED`, `CHANGES_REQUESTED` or `REJECTED`
   version as approved or final.
2. The assistant **must not** say "your final report says…" unless the underlying version is
   `FINAL` (or explicitly and accurately `APPROVED`).
3. The assistant must **state the version and its state** when quoting report content.
4. The assistant must **not** summarise an unreviewed draft as an organisational position.
5. The assistant must respect the same authorization scope (a Viewer cannot see internal comments;
   a PE user has no report access at all).
6. Every report-reading tool call must be **audited**.

### 30.4 Recommended tool contract additions

Extend the tool concept from the Phase 8 discovery with report-state awareness:

| Tool | Output must include |
|---|---|
| `report_lookup` | instance, **all versions with status**, derived current version, approval metadata |
| `report_version_lookup` | the specific version's state, system content, narrative overlay (if visible to the caller), approval metadata |
| `report_evidence_lookup` | evidence for a specific system figure, for a given version |

**Do not implement.** This section constrains a future implementation.

---

## 31. Reuse / Extend / Refactor / New Build Matrix

| Component | Classification | Reason | Proposed action |
|---|---|---|---|
| `ReportGenerationEngine` (`engines/report_generation.py`) | **REUSE** | The only authoritative report engine; 12 sections; honest provenance; already correct | Use as-is. Compose narrative **outside** it, never inside |
| `report_generation_queue` | **EXTEND** | Carries instance + status + `generated_content` + artefact + AI columns | Reuse. Populate `final_report_*` on finalize. Do **not** repurpose `user_edits` as the overlay |
| `report_versions` | **EXTEND** | Correct spine (`report_id` + `version_number` + `UNIQUE`); missing status/approval/overlay/hash | Add `status`, `narrative_overlay`, approval + finalization columns, `content_hash`, `pdf_sha256`; fix `is_current` |
| `data/report_versions.py` | **EXTEND** | Correct CRUD; `create()` leaves multiple `is_current` rows | Add state-transition methods; demote prior current rows; add optimistic-concurrency guards |
| `data/reports.py` | **EXTEND** | Solid lifecycle primitives | Add finalize/artefact persistence; expose `current_version` in the list payload (E27) |
| `report_comments` | **REUSE + EXTEND** | Good section-level shape; dormant | Add `version_number`, `organization_id`, `visibility`, `comment_type` vocabulary; wire API + UI |
| `v3_reports.py` | **EXTEND** | Correct guards, shaping, branding; no lifecycle routes | Add the version-scoped lifecycle endpoints (§23); add audit calls; fix the `download_report` docstring drift (E30) |
| `pdf_render` (`render_branded_pdf`) | **REUSE + EXTEND** | Correct server-branded rendering; returns bytes | Reuse. Add finalization-time storage + hashing in the service layer; optionally add version/approval metadata to the PDF |
| `audit_trail` + Phase 7 taxonomy + trigger | **REUSE** | Append-only substrate; `CAT_REPORT` exists; `report*` already routes to it | Reuse. **Emit the events** (§21). No new audit table, no taxonomy change required |
| Authorization guards (`ensure_org_access`, `require_org_member`, `require_consultant`, `ensure_consultant_org_access`, `require_entity_scope`, `ensure_staff_permission`) | **REUSE** | The correct, proven authorization contract | Reuse unchanged. Add approval checks **on top** — never replace them |
| RLS on report tables | **NEW BUILD** (policy) | **No RLS exists on report tables** (E20) | Add enablement + org-scoped policies, or document deliberate application-level authorization (AGENTS.md §67). **Never weaken existing RLS** |
| Frontend `ReportsPage` / `ReportDetailPage` | **EXTEND** | Correct real-data surfaces; no lifecycle UI | Add narrative editing, review, approval, final lock, version comparison; fix the Version column (E27) |
| `frontend/src/v3/api.js` | **EXTEND** | Correct client surface; `downloadReportPdf` unwired | Add lifecycle calls; wire the PDF download |
| `approval_requests` / `approval_decisions` | **DO NOT TOUCH** | FK-bound to `processing_assignments`; a different domain | **Explicitly excluded** (§7.4, §25 Option B) |
| Legacy `routes/reports.py` + `report_generator.py` | **LEAVE (Class D)** | Unmounted legacy monolith; behavioural ancestor | No action pending PO decision P2 |
| `report_templates` | **REUSE (latent)** | Exists with `template_structure`, `ai_prompts`, branding; V3 passes `template_id` through only | Do not build template CRUD now; recognise it as the future home for per-tenant structure |

### 31.1 Summary

> **No component requires a parallel replacement.** The lifecycle is an **EXTEND** of
> `report_versions` + `v3_reports.py` + `data/*` + `report_comments`, layered on the **REUSE** of
> the engine, PDF renderer, audit trail and authorization guards. The only genuinely **NEW** work
> is (a) report-table RLS policy, (b) the artefact storage/hash step, and (c) the narrative
> overlay column and its validation.

---

## 32. Future Implementation Acceptance Criteria

Criteria for the **eventual** implementation. None are met today; none are claimed here.

### 32.1 Authorization

- [ ] Unauthorized users cannot view reports (`403`, not a hidden button).
- [ ] A customer cannot read or edit another organisation's report (org isolation).
- [ ] A consultant cannot act outside an ACTIVE grant; ended/suspended grants are denied.
- [ ] **PE users cannot access customer report data at all** (negative test).
- [ ] A Viewer cannot edit, comment, or approve.
- [ ] A Member cannot approve.
- [ ] Every UI restriction is **also** enforced server-side (test both ALLOW and DENY).
- [ ] Report-table RLS exists and enforces org scope (§22.3).

### 32.2 Integrity

- [ ] A customer cannot modify system-controlled sections (`content`) by any route.
- [ ] A customer cannot modify `calculation_snapshots`.
- [ ] A customer cannot modify evidence or provenance.
- [ ] A customer cannot modify validation results.
- [ ] A customer cannot modify lineage or benchmark calculations.
- [ ] A customer cannot modify or delete audit records.
- [ ] An overlay payload containing a system key is **rejected** server-side.

### 32.3 Lifecycle

- [ ] Invalid transitions are rejected (`409`) — e.g. `DRAFT → APPROVED`, `APPROVED → FINAL` without approval.
- [ ] Approval requires `REVIEWED` state.
- [ ] Finalization requires `APPROVED` state.
- [ ] A `FINAL` version cannot be edited or re-finalised into different content.
- [ ] A post-approval change creates a new version (§18 Option A) and requires new approval.
- [ ] Exactly one version per report satisfies the "current version" invariant.
- [ ] Generation failure never yields a version.

### 32.4 Audit

- [ ] Every transition in §13 emits an audit event (§21.2).
- [ ] Actor identity is captured (never client-supplied).
- [ ] UTC timestamps are captured.
- [ ] Version identity is captured.
- [ ] Old and new state are reconstructable.
- [ ] Audit entries contain no full narrative bodies, document content or secrets.

### 32.5 PDF / artefact

- [ ] The final PDF corresponds to exactly one approved version.
- [ ] The final PDF cannot silently change (stored once; hash recorded).
- [ ] The artefact hash mismatch fails closed.
- [ ] The artefact remains associated with its version after supersession.
- [ ] No public URL or signed URL is exposed or logged.

### 32.6 Concurrency

- [ ] Stale approval is rejected (content-hash mismatch).
- [ ] Concurrent edits cannot silently overwrite (optimistic concurrency).
- [ ] Duplicate finalization is idempotent (no second artefact).

### 32.7 AI boundary

- [ ] AI cannot modify report state.
- [ ] AI cannot modify carbon calculations, factors or evidence.
- [ ] AI cannot fabricate report facts.
- [ ] AI may only explain authoritative structured data.
- [ ] `DRAFT`/`APPROVED`/`FINAL` status is respected by any assistant surface.

### 32.8 Regression

- [ ] All existing `test_v3_reports.py` tests continue to pass.
- [ ] Existing report endpoints keep their contracts.
- [ ] No existing RLS policy is weakened.

---

## 33. PO Decisions P1–P8

| ID | Decision | Status |
|---|---|---|
| **P1** | Accept the correction that the authoritative V3 report catalogue contains **one** report type (`annual`) rather than ~80–90 audit-ready reports? | **PO DECISION REQUIRED** (evidence is unambiguous: E1) |
| **P2** | What happens to the legacy report surfaces — behavioural ancestor only, progressive retirement, or formal V3 revival? | **PO DECISION REQUIRED** |
| **P3** | Exactly which report sections/fields are customer-editable? | **RECOMMENDED** (§10.1 bounded narrative namespace) — **final PO DECISION REQUIRED** |
| **P4** | Who may approve — Customer Owner only, Owner + Admin, or another model? | **RECOMMENDED** Owner + Admin (§17.1) — **final PO DECISION REQUIRED** |
| **P5** | Does any post-approval edit invalidate approval and require re-approval? | **RECOMMENDED: YES — Option A** (§18.2) — **final PO DECISION REQUIRED** |
| **P6** | Is a frozen final PDF mandatory? | **RECOMMENDED: YES** (§19.2) — **final PO DECISION REQUIRED** |
| **P7** | Should report approval be distinct from the PE `approval_requests`/`approval_decisions` model? | **RECOMMENDED: DISTINCT** — rejection on evidence (§7.4, §25 Option B). **PO DECISION REQUIRED to ratify** |
| **P8** | Should narrative generation be deterministic/template-first, AI-assisted, or hybrid? | **PO DECISION REQUIRED** (§29.4). No LLM is built or configured by this task |

### 33.1 Evidence-based status summary

* **Resolved by repository evidence (no PO decision needed to *know the fact*):** the current
  catalogue is one type; `approval_requests` is PE-scoped; report tables have no RLS; report
  lifecycle is unaudited; `is_current` can be multiply-true; the PDF is not stored and not
  byte-reproducible.
* **Recommended and justified, but still a PO call:** P3–P8.
* **Genuine policy decisions with no repository answer:** P1 acknowledgement, P2 legacy
  disposition, P4 approver set, P8 narrative strategy.

---

## 34. Additional PO Decisions

Additional decisions revealed by the archaeology. Each is material to the lifecycle and none can
be resolved from the repository.

| ID | Question | Recommended (if any) | Status |
|---|---|---|---|
| **A1** | May a consultant edit a client's narrative, and may a Customer Member edit? | Owner + Admin + Member; consultant editing is advisory — **PO DECISION REQUIRED** | PO DECISION REQUIRED |
| **A2** | May a consultant **approve** a client's report? May internal staff approve? | **No** to both (§17.1) — staff approval would imply assurance CarbonTally does not provide | PO DECISION REQUIRED |
| **A3** | Narrative field length limits, item counts, and formatting | Plain text; bounded lengths; no HTML/links (§10.3) — numeric values **PO DECISION REQUIRED** | PO DECISION REQUIRED |
| **A4** | Is review a required gate, or may approval follow directly from `DRAFT`? | Keep review as a required state; allow an org policy to auto-review | PO DECISION REQUIRED |
| **A5** | One-step approval or review + approval (two roles)? | Two-step where the org has >1 authorised actor; single-step acceptable for small orgs | PO DECISION REQUIRED |
| **A6** | May a Customer Owner **revoke** an approval, and under what conditions? | Permit revocation before finalization, with a recorded reason; **never** after finalization | PO DECISION REQUIRED |
| **A7** | Are review comments internal-only, or customer-visible? | **Split by `visibility`**: internal (staff/consultant) and shared (customer-visible) | PO DECISION REQUIRED |
| **A8** | May a customer delete a **draft** version? | Permit deletion of `DRAFT` only, never `APPROVED`/`FINAL`; preferably "discard draft" (soft) | PO DECISION REQUIRED |
| **A9** | Do unresolved `change_request` comments **block** approval? | **Yes** — recommended | PO DECISION REQUIRED |
| **A10** | Retention period for report instances, versions and artefacts; may a `FINAL` report ever be deleted? | `APPROVED`/`FINAL` never deleted; retention periods require legal review (§28.4) | PO DECISION REQUIRED |
| **A11** | Is **download** of a report or final PDF an audited event? | **Yes** — audit `report.downloaded` | PO DECISION REQUIRED |
| **A12** | If underlying carbon data changes after approval, should the report be **flagged stale** (never auto-invalidated), and should the report display a "data as of" timestamp? | **Yes to flagging and to a "data snapshot as of" timestamp**; never silently change an approved report (§27 cases 11–12) | PO DECISION REQUIRED |
| **A13** | Should the **final report expose calculation/evidence drill-down** to the reader? | Yes, subject to the viewer's authorization (§20.2 rule 4) | PO DECISION REQUIRED |
| **A14** | Is report finalization **billable / entitlement-gated**? | Out of scope here; note that `report_generation_queue` already has AI cost columns and `usage_tracking.reports_generated` exists but is never incremented (E31) | PO DECISION REQUIRED |
| **A15** | Should the legacy live-render `GET /{id}/pdf` route be replaced by the frozen-artefact route, or both kept? | Keep the legacy route for drafts; the frozen route for `FINAL` | PO DECISION REQUIRED |

---

## 35. Recommended Implementation Sequence

**Not started. Each step requires its own PO authorisation.**

| Step | Scope | Depends on | Risk |
|---|---|---|---|
| **S0** | **PO ratifies P1–P8 and A1–A15** (or the subsets needed for S1) | — | — |
| **S1** | **Correctness fixes only**: fix `is_current` multi-true (E12) via partial unique index; surface `current_version` in the list payload (E27); correct the `download_report` docstring drift (E30) | S0 (P1 acknowledgement) | **Low** — no new features |
| **S2** | **Schema**: EXTEND `report_versions` (Option A) + `report_comments` additions + **RLS enablement and org-scoped policies on report tables** (§22.3) | S1 | **Medium** — migration; RLS touches security |
| **S3** | **Lifecycle service + API**: version-scoped endpoints (§23), state machine (§13), audit events (§21) | S2 | **Medium** |
| **S4** | **Narrative overlay**: bounded, validated, allowlisted; separate from `content` (§10, §15) | S3 | **Medium** |
| **S5** | **Frozen final PDF**: finalize step, private storage, content hash + artefact hash, immutable association (§19) | S3 | **Medium-High** — storage + hashing + idempotency |
| **S6** | **Frontend lifecycle UI**: version history with state, narrative editor, review/comments, approval controls, final lock, version comparison (§24) | S4, S5 | **Medium** |
| **S7** | **Regression + negative security tests**: org isolation, PE denial, Viewer denial, stale approval, final immutability, RLS coverage (§32) | S3–S6 | **Low-Medium** |
| **S8** | **(Separate, later)** AI-assisted narrative — only after the Phase 8 AI safety preconditions and behind `infra/` (§29) | S0 (P8), AI preconditions | **High** — not in this lifecycle scope |

**Sequencing principle:** **S1 before S2** — do not extend a table whose existing invariant is
provably violable.

---

## 36. Explicit Non-Goals

This specification does **not**:

1. Implement anything — no code, no schema, no migration, no API, no UI.
2. Configure, install or connect any LLM, provider or API key.
3. Create a second report system, report engine, export surface, audit table, evidence model or
   authorization model.
4. Revive the legacy report surface (`SECR`, `CSRD`, `ISSB`, `AUDITOR_EXCEL`, generic types).
5. Repurpose `approval_requests` / `approval_decisions` (PE-scoped) for report approval.
6. Resurrect `emissions_logs.confidence_score` as a report or evidence quality metric.
7. Weaken any RLS policy, authorization guard, or tenant boundary.
8. Change messaging, billing/subscription, or the carbon calculation engine.
9. Define net-zero targets, baselines or scenarios (Phase 8 P8-5, separate discovery).
10. Define disclosure-framework support (Phase 8 P8-7, separate discovery).
11. Implement Ask CarbonTally — it only constrains it (§30).
12. Set retention periods, approval policy or narrative-editing policy (PO decisions).
13. Claim assurance, certification, audit or compliance status — for CarbonTally or its reports.
14. Delete, rewrite or restructure any historical artefact.

---

## 37. Risks and Dependencies

### 37.1 Risks

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | **Lifecycle built on the unscoped report tables** (no RLS, E20) | High — defence-in-depth gap | Address RLS in S2 before adding lifecycle writes (§22.3) |
| R2 | **`is_current` multi-true defect** propagates into "current version" semantics | High — wrong version approved/served | Fix in S1 with a partial unique index (§25.2) |
| R3 | **Non-deterministic content/PDF** mis-used as a reproducibility guarantee | Medium-High — false integrity claim | Two-hash model (§19.4); never claim PDF reproducibility |
| R4 | **Customer narrative mutating system facts** | Critical — integrity breach | Separate `narrative_overlay` column; allowlist validation; §15.3 |
| R5 | **Stale approval** (approving content the approver never saw) | High — invalid approval | `expected_content_hash` requirement (§26.2) |
| R6 | **Approval implying assurance** | High — positioning/regulatory risk | §17 exclusion of consultant/staff approval; no assurance language in the UI |
| R7 | **Conflation of generation status and version state** | Medium — user confusion, wrong UI gating | Keep both vocabularies explicit and separately labelled (§12.3, §24.4) |
| R8 | **`user_edits` repurposed by a future implementer** | Medium — breaks version-bound editing | Explicit warning (§15.1) |
| R9 | **Audit events omitted** (as today, E5) | High — lifecycle not reconstructable | Every transition must emit an event (§21); acceptance criterion (§32.4) |
| R10 | **Frozen artefact orphaned or overwritten** | High — deliverable integrity | Store once; immutable association; refuse deletion (§28.3) |
| R11 | **PE access to reports creeping in** | High — boundary erosion | PE column all "No" (§22.2); negative test (§32.1) |
| R12 | **Legacy surface accidentally revived as "the 80–90 reports"** | Medium-High — scope/credibility | P1/P2 decisions; §4.3 |
| R13 | **Production data depth unverified** — approved reports over thin history | Medium | Verify population before promising report depth |
| R14 | **Scope creep into AI narrative** | High — unproven safety surface | S8 is explicitly separate and gated (§35) |

### 37.2 Dependencies

| Dependency | Needed for | Status |
|---|---|---|
| PO decisions P1–P8, A1–A15 | Everything from S1 onward | **OUTSTANDING** |
| Legal review of retention (§28.4, A10) | S2/S5 | **OUTSTANDING** |
| Production data-population verification | Any claim of usable approved reporting | **UNVERIFIED** |
| A decision on report-table RLS approach (§22.3) | S2 | **REQUIRED** |
| Storage plan for the frozen artefact (private bucket, naming, lifecycle) | S5 | **NOT DEFINED** |
| Phase 8 AI safety preconditions | S8 only | **NOT MET** |

### 37.3 What this specification did NOT verify

* Production database population, applied-migration state, and whether any report rows exist.
* Live runtime behaviour of the report endpoints (no production access attempted).
* Whether `report_comments` has any historical rows.
* Whether `report_templates` is populated.
* Any Render/Vercel/Supabase production configuration.

---

## 38. Final Recommendation

1. **Adopt the lifecycle**: `GENERATE → DRAFT → EDIT → REVIEW → APPROVE → FINAL → FROZEN PDF`,
   with six stored version states (`DRAFT`, `REVIEWED`, `CHANGES_REQUESTED`, `REJECTED`,
   `APPROVED`, `FINAL`) plus **derived** "superseded" and "current version".
2. **Adopt Option A** (extend `report_versions`) and **reject Option B** (PE approval tables) on
   security and domain grounds.
3. **Adopt the narrative-overlay model**: system `content` is immutable; the customer edits a
   separate, bounded, allowlisted `narrative_overlay`.
4. **Adopt Option A for post-approval change**: any change creates a new version and requires new
   approval. **Approval freezes meaning; finalization freezes the deliverable.**
5. **Adopt the two-hash model** for the frozen PDF (canonical content hash for approval; byte hash
   for the stored artefact).
6. **Reuse `audit_trail`** and emit the lifecycle events — no parallel audit log.
7. **Reuse existing authorization guards unchanged**, add approval checks on top, and **add RLS to
   the report tables** without weakening anything.
8. **Acknowledge the one-type report catalogue** (P1) and decide the legacy disposition (P2)
   **before** any catalogue expansion.
9. **Sequence S1 (correctness) before S2 (schema)** so the lifecycle is not built on a provably
   violable invariant.
10. **Keep AI narrative entirely out of this lifecycle until separately authorised** and until the
    Phase 8 AI safety preconditions are met.

### Preserved principle

> **CarbonTally reports are authoritative presentations of CarbonTally's persisted,
> provenance-preserved carbon data. Customer narrative may explain that data, but customer
> narrative must never become the source of the data. Approval freezes the meaning of the report
> version; finalization freezes the deliverable.**

> **The report lifecycle must extend CarbonTally's existing architecture, not create a parallel
> reporting system.**

```text
PHASE 8 REPORT LIFECYCLE SPECIFICATION COMPLETE
STATUS:                    DESIGN / SPECIFICATION ONLY
IMPLEMENTATION AUTHORISED: NO
CURRENT CATALOGUE:         annual (1 type, 12 sections) — VERIFIED
RECOMMENDED MODEL:         EXTEND report_versions + report_comments + audit_trail
REJECTED:                  reuse of PE approval_requests / approval_decisions
PO DECISIONS OPEN:         P1-P8 + A1-A15
CODE / DB / PROD CHANGES:  NONE
MIGRATIONS:                NONE
LLM / PROVIDER / KEY:      NONE
```

*End of specification.*
