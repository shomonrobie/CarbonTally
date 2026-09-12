# CT-P8-REPORTING-LIFECYCLE-SPEC-20260912-009

**Prompt ID:** `CT-P8-REPORTING-LIFECYCLE-SPEC-20260912-009`
**Date:** 2026-09-12
**Task purpose:** Phase 8 Report Versioning & Approval Lifecycle — architecture / product
specification and existing-system design archaeology.
**Type:** DESIGN / SPECIFICATION ONLY. No implementation authorised.
**Task status:** `COMPLETED — SPECIFICATION ONLY`

## Scope

Produce an implementable specification for the authoritative V3 report lifecycle
(`GENERATE → DRAFT → EDIT → REVIEW → APPROVE → FINAL → FROZEN PDF`) covering: report catalogue,
report/instance/version/artefact definitions, system vs customer-editable vs approval-controlled
content, version state machine and transition matrix, versioning semantics, narrative overlay,
review/comments, approval model, post-approval policy, frozen PDF model, provenance, audit,
authorization, API, frontend, schema options, concurrency, failure cases, retention, the AI
narrative boundary, and the Ask CarbonTally dependency.

**Non-implementation rule:** no code, frontend, SQL, migration, schema, RLS, authorization,
report-generation, PDF-rendering, LLM, provider, API-key, billing, messaging, production or
deployment change was made.

## Repository State at Start

| Item | Value |
|---|---|
| Branch | `main` |
| Starting HEAD | `06989d5fe3aaf0203670e68aba6fd1b9f8da56e6` |
| Relation to origin | 5 commits ahead of `origin/main` (`9e13236…`), **not pushed** |
| Pre-existing modified | 208 |
| Pre-existing untracked | 52 |
| Staged | 0 |

## Files Inspected

**Reporting API / engine / data**
`backend/api/v3_reports.py` · `backend/engines/report_generation.py` · `backend/engines/pdf_render.py`
· `backend/api/consultant_branding.py` · `backend/data/reports.py` · `backend/data/report_versions.py`
· `backend/domain/report.py` · `backend/domain/branding.py` · `backend/tests/unit/api/test_v3_reports.py`

**Audit / domain**
`backend/domain/audit.py` · `backend/api/audit_helpers.py` · `backend/data/audit.py`
· `backend/api/dependencies.py`

**Schema / migrations**
`supabase/migrations/00000000000000_init_schema.sql` (`report_templates`, `report_generation_queue`,
`report_versions`, `report_comments`, `approval_requests`, `approval_decisions`, `audit_trail`,
`usage_tracking`) · `supabase/migrations/20260807070000_add_new_table_rls.sql`
· `supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql` · RLS scans across all
54 migrations · `database/rc1/002_rc1_constraints.sql`

**Frontend**
`frontend/src/v3/reports/ReportsPage.jsx` · `frontend/src/v3/reports/ReportDetailPage.jsx`
· `frontend/src/v3/api.js`

**Legacy**
`backend/routes/reports.py` · `backend/report_generator.py`

## Findings (summary)

### Verified facts

1. **Catalogue = one type.** `SUPPORTED_REPORT_TYPES = {"annual": …}` (`v3_reports.py:63`);
   12 sections (`report_generation.py:65`); `validate_report_type` → 422 otherwise. The
   `SECR`/`CSRD`/`ISSB`/`AUDITOR_EXCEL`/generic labels live only in the **unmounted** legacy
   monolith and are **not** authoritative.
2. **No `public.reports` parent table.** Report identity = `report_generation_queue.id`
   (documented in `data/report_versions.py` and `database/rc1/002_rc1_constraints.sql:495`).
3. **`report_generation_queue` already carries dormant lifecycle columns:** `user_edits JSONB`,
   `final_report_url`, `final_report_file_name`, `final_report_size_bytes`, `ai_model_used`,
   `ai_tokens_used`, `ai_cost`, `ai_processing_time_ms`.
4. **`report_versions` has no status/approver.** Columns: `report_id`, `version_number`, `content`,
   `file_url`, `file_name`, `created_by`, `created_at`, `notes`, `change_summary`, `is_current`,
   `UNIQUE(report_id, version_number)`.
5. **`is_current` defect:** `create()` defaults `is_current=True` and never demotes prior rows →
   multiple `is_current=TRUE` rows are possible; `get_current()` masks it by ordering.
6. **`report_comments` is dormant** (no backend/frontend usage): `report_id`, `user_id`,
   `section_id`, `comment`, `comment_type` (no vocabulary), `is_resolved`, `resolved_at`,
   `resolved_by`, `resolution_notes`. Suitable foundation; missing version binding, org scope,
   visibility.
7. **`approval_requests`/`approval_decisions` are PE-scoped** — `assignment_id NOT NULL REFERENCES
   processing_assignments(id)`. **Not report-related; must not be repurposed.**
8. **No RLS on any report table** — no `ENABLE ROW LEVEL SECURITY`, no policy (21 RLS enablements
   exist elsewhere, incl. `calculation_snapshots`). Authorization is API-layer only — **no
   defence-in-depth for reports**.
9. **Report lifecycle is unaudited** — `v3_reports.py` makes no audit calls.
10. **PDF is never stored**; not byte-reproducible (reportlab `/CreationDate` + `/ID`; footer
    `date.today()`); identifies report type/year but **not the version**.
11. **Engine content is non-deterministic** — `_generation_section.generated_at =
    datetime.now(timezone.utc).isoformat()`.
12. **Frontend has no lifecycle UI**; the "Version" column always falls back to `v1`/`—` because
    the list endpoint omits `current_version`; `downloadReportPdf` exists but is unwired.
13. **Documentation drift:** `download_report`'s docstring says "no PDF rendering exists in V3"
    while `/pdf` exists.
14. **`usage_tracking.reports_generated` is only read**, never incremented by the reports surface.

### Design conclusions

* **EXTEND** `report_versions` (Option A) — add `status`, `narrative_overlay`, approval and
  finalization columns, `content_hash`, `pdf_sha256`; fix `is_current`.
* **REJECT** reusing the PE approval tables (Option B) — different domain; would risk weakening a
  boundary.
* **Six stored version states**: `DRAFT`, `REVIEWED`, `CHANGES_REQUESTED`, `REJECTED`, `APPROVED`,
  `FINAL`; `SUPERSEDED` and "current version" are **derived** (`EDITED` demoted to an event).
* **Post-approval change = Option A**: any change creates a new version and requires new approval.
* **Two-hash model**: canonical content hash for approval; byte hash for the stored artefact.
* **Reuse `audit_trail`** (Phase 7 `CAT_REPORT` already exists; `report*` already routes to it) —
  no parallel audit table, no taxonomy change needed.
* **Narrative overlay** lives in a separate, bounded, allowlisted namespace — never merged into
  system `content`.
* **Ask CarbonTally** must see explicit version state and must never present a draft as approved
  or final.

## Files Created

* `docs/architecture/CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` (38 sections)
* `docs/cline/prompt-history/CT-P8-REPORTING-LIFECYCLE-SPEC-20260912-009.md` (this record)

## Files Modified

* **None.**

## Change Statements

```
Code changes:        NONE
Database changes:    NONE
Migrations:          NONE
RLS changes:         NONE
Production changes:  NONE
Deployment:          NONE
LLM changes:         NONE
Provider changes:    NONE
API keys added:      NONE
Billing changes:     NONE
Messaging changes:   NONE
Push:                NONE
```

## Tests / Checks Performed

Read-only only:

* Confirmed both created files exist and are non-empty.
* Verified every material claim against source (line-referenced in the specification's evidence
  table).
* Confirmed no application/database/production file was modified by this task.
* Confirmed no migration was created or modified.
* Confirmed no secrets were added (scanned both documents).
* Confirmed no LLM provider is configured (no `CARBONTALLY_AI_*` / `OPENAI_*` / `ANTHROPIC_*` /
  `OPENROUTER_*` env vars; no LLM SDK in either `requirements.txt`).
* Verified the prior Phase 8 discovery's report-engine description still matches the current
  implementation (prompt Stop Condition 7 — no conflict).
* Inspected `git status` / `git diff` scoped to task files.

## Final Git State

* Ending HEAD: recorded in the completion report.
* Commit: one focused documentation commit (`docs: specify Phase 8 report lifecycle`), 2 files.
* Push status: **NOT PUSHED**.
* Unrelated dirty/untracked work: **PRESERVED** (208 modified / 52 untracked restored; selective
  staging only; no reset / clean / stash / checkout).

## Unresolved PO Decisions

**P1–P8**: catalogue correction acknowledgement; legacy disposition; editable field set; approver
set; post-approval policy; mandatory frozen PDF; report-approval distinctness from PE approvals;
deterministic vs AI-assisted narrative.

**A1–A15**: consultant/Member editing; consultant/staff approval; narrative length/format limits;
review as a mandatory gate; one-step vs two-step approval; approval revocation; comment
visibility; draft deletion; change-request blocking; retention and final-report deletability;
download auditing; staleness flagging and "data as of" timestamp; evidence drill-down exposure;
billing/entitlement gating; legacy live-render PDF route disposition.

## Recommended Next Task

**Exactly one:** `CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-010` — Phase 8 Report Catalogue &
PO Decision Ratification (P1–P8, A1–A15), producing a short ratified decision register that
authorises (or defers) each lifecycle rule **before** any implementation step S1. It directly
unblocks the specification's implementation sequence, requires no code or schema change, and
prevents implementation from pre-empting product policy. **Not begun.**

*End of record.*
