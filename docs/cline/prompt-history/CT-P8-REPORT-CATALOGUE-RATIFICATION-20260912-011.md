# CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-011

**Prompt ID:** `CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-011`
**Date:** 2026-09-12
**Task purpose:** Phase 8 Open-Decision Closure & Implementation Authorisation Package — classify
every open decision, run the required special reviews, and establish whether S1 can be authorised.
**Type:** DOCUMENTATION / DECISION PACKAGE ONLY. No implementation authorised.
**Task status:** `COMPLETED — DECISION PACKAGE ONLY`

## Repository State at Start

| Item | Value |
|---|---|
| Branch | `main` |
| Starting HEAD | `10d43f65b3354c00a50f4fa584e05ad8baf934e0` |
| Relation to origin | 7 commits ahead of `origin/main` (`9e13236…`), **not pushed** |
| Pre-existing modified | 208 |
| Pre-existing untracked | 52 |
| Staged | 0 |

## Authoritative Inputs Reviewed

`CARBONTALLY_PHASE8_DISCOVERY_AND_CAPABILITY_GAP_ANALYSIS_20260912.md` ·
`CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` ·
`CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md` ·
`CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` (§5 actors, §13 authorization, §14 RLS, §16
ops/admin) · `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` (§0, §10, §11, §13, §14, §18) ·
`CARBONTALLY_PHASE7_CLOSURE_AND_RELEASE_BOUNDARY_20260912.md` (§5 non-claims) ·
`CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` · prompt histories `-008`, `-009`, `-010` ·
current backend/frontend/database/RLS/audit/billing implementation.

## MATERIAL CORRECTION DISCOVERED

**The prior statement "no RLS on any report table" was INACCURATE** (it appeared in `-008` §8.4,
`-009` §22.3 and `-010` §8.4 / D-12 / defect #1 / T2).

**Corrected finding:**

* `supabase/migrations/00000000000000_init_schema.sql:2315-2324` contains a **schema-wide RLS
  enablement loop** (`FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='public' … ALTER
  TABLE … ENABLE ROW LEVEL SECURITY`) that runs *after* the report tables are created in that same
  file → **RLS is enabled on all four report tables**.
* `rc2_rls.sql` §3 (lines 130-178) dynamically creates tenant policies for **every table with an
  `organization_id` column** → `report_generation_queue` and `report_templates` (both have it)
  receive tenant policies; **`report_versions` and `report_comments` have no `organization_id` and
  therefore no policy** → deny-all to `authenticated` under RLS.
* Backend access works because the connection role **bypasses RLS** (owner/service-role; Blueprint
  §14 records FORCE RLS as an open hardening item).
* **Effective report authorization today rests on the API-layer guards** (`require_org_member` +
  `ensure_org_access`), backed by negative org-isolation tests.

**Three unknowns marked `[UNVERIFIED]`** (require live DB inspection, which was **not** performed):
the live policy list per report table; the effective backend DB role; whether FORCE RLS is set.

**The correction does not change the ratified direction** and **does not block S1** (S1 changes no
RLS artefact). It **does** affect S2 planning.

## Deliverables

* `docs/architecture/CARBONTALLY_PHASE8_OPEN_DECISION_CLOSURE_AND_IMPLEMENTATION_AUTHORISATION_20260912.md`
  (17 sections)
* `docs/cline/prompt-history/CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-011.md` (this record)

## Files Created

* `docs/architecture/CARBONTALLY_PHASE8_OPEN_DECISION_CLOSURE_AND_IMPLEMENTATION_AUTHORISATION_20260912.md`
* `docs/cline/prompt-history/CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-011.md`

## Files Modified

* **None.**

## Findings Summary

### Special security reviews

1. **Report-table RLS** — RLS **enabled** on all four report tables; **policy coverage incomplete**
   (`report_versions` / `report_comments` unpolicied); **API-layer authorization is the effective
   control**. **Not an S1 blocker; an S2 prerequisite.** A documented app-layer-only approach is
   defensible **only if made explicit**; the current posture is *accidental*, not deliberate.
2. **Auditor access** — **no auditor role, table, workspace, invitation model or API exists**
   (Phase 7 created none). The **consultant active-grant pattern** (`consultant_clients` +
   `ensure_consultant_org_access`) is the recommended future analogue. `FUTURE`.
3. **PE access** — `backend/api/v3_pe.py` (662 lines, 21 routes) has **zero `report` references**;
   PE has no report route/scope/UI. **Recommendation: keep PE report-document access = No**; PE
   Admin portfolio reporting (`ops/entities/{id}/performance`) is a separate, entity-scoped surface
   consistent with Blueprint §5.3/§7/§8.

### Report-integrity review

All three issues **reconfirmed** and judged **S1-appropriate**, with a refinement:

* `report_versions.is_current` can be multiply-true (`create()` never demotes prior rows; only
  `UNIQUE(report_id, version_number)` exists; `get_current()` masks it). **Fix in S1 via the
  repository-level shape (S1-A, no migration)**; the structural partial-unique-index shape (S1-B) is
  deferred to S2 because it would fail if duplicate rows already exist (live state `[UNVERIFIED]`).
* The report **list omits `current_version`**, so the ReportsPage "Version" column always shows
  `v1`/`—`. **Fix in S1** with a single-query (no N+1) lookup.
* The `download_report` docstring wrongly claims no V3 PDF rendering exists. **Fix in S1** (docs
  only; no auditing introduced).

**S1 boundary: CONFIRMED** (with additions: no-N+1 constraint; regression test for the invariant).

### Legacy disposition

V3 report/reporting/export surfaces are **LIVE**; `backend/routes/reports.py` (2,097 lines),
`backend/report_generator.py` (1,071 lines) and legacy CRA analytics are **NOT mounted** (dead code).
**Recommendation: preserve untouched; no revival; labels stay out of the live product.** The **V3**
live-render `/pdf` route (not the legacy generator) is the one that interacts with the future
frozen-PDF model → **A15**.

### Roadmap consistency

Six stale statements identified (§0/§11/§13/§14/§18) — **all documentation-only**, **none
implementation-impacting**; `A-ROAD` records the recommended bounded updates. **Roadmap not edited.**

### Assurance-readiness scoring / staff capability / comment model

* **Scoring**: no numeric score exists (only an "AUDIT EVIDENCE READINESS" indicator with
  `not_assurance: true`); **`DEFER`** with five prerequisite definitions.
* **Staff capability**: capability flags exist (`can_approve` = *processing* approval today);
  **`DEFER`** — customer-only for the current lifecycle.
* **Comment model**: `report_comments` is a suitable foundation (section anchoring + resolution),
  missing `organization_id`, version binding and `visibility`; it can serve customer/consultant/
  reviewer comments, findings and evidence requests initially; **no separate finding table now**.

## Decision Classification Result

**24 decisions classified + 1 correction.** **DECIDE NOW: none. S1 blockers: none.**

| Classification | Items |
|---|---|
| `DECIDE NOW` | **none** |
| `DEFER` | A1, A3, A7, A11, A12, A13, A-AUD2, A-LEG (disposition), A-ASSUR, A-STAFF, A-COMMENT |
| `FUTURE` | A2, A4, A5, A6, A8, A9, A10, A14, A15, A-PE, A-AUD, A-RLS, A-ROAD, A-LEG (framework types) |
| `IMPLEMENTATION BLOCKER` | **A-RLS — for S2 only** (not S1) |

## S1 Authorisation Status

### READY FOR PO AUTHORISATION

No unresolved blocker remains for S1; S1 scope is defined (S1-A: repository-level `is_current` fix,
`current_version` exposure, docstring correction); S1 introduces no schema/RLS/lifecycle surface; and
no implementation has been started. **This package does not authorise S1** — the PO must.

## Change Statements

```text
Code changes:            NONE
Database changes:        NONE
Migrations:              NONE
RLS changes:             NONE
API changes:             NONE
Frontend changes:        NONE
Report-engine changes:   NONE
PDF changes:             NONE
AI / LLM changes:        NONE
Billing changes:         NONE
Messaging changes:       NONE
Production changes:      NONE
Roadmap edits:           NONE
Legacy code changes:     NONE
Authorization changes:   NONE
Push:                    NONE
```

## Verification Performed

Both documents exist; classifications are internally consistent across §13/§14/§15/§16; every open
decision is classified; the S1 boundary is explicit; no implementation, database, schema, RLS, API,
frontend or production change was made; no unrelated dirty/untracked work was removed or modified
(208 modified / 52 untracked preserved); nothing pushed.

**Stop-condition compliance:** no stop condition triggered. Live RLS inspection was **not** performed
(prompt §17) — the three resulting unknowns are marked `[UNVERIFIED]` and the recommendation does not
depend on them.

## Final Git State

* Ending HEAD: recorded in the completion report.
* Commit: one documentation-only commit (`docs: close Phase 8 open decisions and gate S1`), 2 files.
* Push status: **NOT PUSHED**.
* Unrelated modified/untracked work: **PRESERVED** (208 modified / 52 untracked restored; selective
  staging only; no reset / clean / stash / checkout).

## Unresolved PO Decisions

**Decide before S1:** none. **Acknowledge:** the §4 RLS correction; the S1-A scope choice.
**Before S2:** A-RLS. **Before S3:** A2, A4, A5, A6, A9, A7. **Before S4:** A1, A3.
**Before S5:** A10, A15. **Before S6:** A12, A13, A-PE. **Separate:** A-AUD, A-AUD2, A-ASSUR,
A-STAFF, A-LEG, A-ROAD, A14, A-COMMENT.

## Recommended Next Task

**Exactly one:** `CT-P8-S1-REPORT-CORRECTNESS-IMPLEMENTATION-20260912-012` — **S1 implementation
(report correctness foundation)**, **only if the Product Owner explicitly authorises S1**. Scope:
repository-level `is_current` fix (no migration), `current_version` exposure in the report list (one
query), and the stale `download_report` docstring correction, plus the invariant regression test.
Deliverables would be code + tests + an implementation report, followed by **independent
verification**. **Not begun; not authorised.**

*End of record.*
