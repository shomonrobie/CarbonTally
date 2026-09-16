# CT-P8-REPORTING-S4-NARRATIVE-OVERLAY-20260912-001

**Prompt ID:** `CT-P8-REPORTING-S4-NARRATIVE-OVERLAY-20260912-001`
**Date:** 2026-09-12
**Task:** Phase 8 Reporting — **S4 Narrative Overlay** (bounded narrative/presentation layer).
**Task type:** IMPLEMENTATION (bounded) — **not performed: HARD STOP invoked.**
**Outcome:** `S4 IMPLEMENTATION BLOCKED — PO/ARCHITECTURE REVIEW REQUIRED`
**Change footprint:** **No code, test, migration, RLS, schema, production or unrelated change was
made.** This report is the only artifact created.

---

## 1. Objective

Implement the ratified bounded **narrative overlay** for CarbonTally reports while preserving
strict separation between system-controlled carbon/report facts and user-editable
narrative/presentation content.

## 2. Pre-implementation code trace (performed before any change)

| # | Item | Result |
|---|---|---|
| 1 | `report_versions` schema | `id, report_id, version_number, content, file_url, file_name, created_by, created_at, notes, change_summary, is_current` (`supabase/migrations/00000000000000_init_schema.sql:1003-1016`) + `status` added by S3. Live `carbontally_test`/`postgres` columns confirm the same. **No `narrative_overlay` column exists.** |
| 2 | S1 changes | `is_current` single-current invariant (transactional demote), `current_by_reports` batch read, `current_version` in the listing, docstring correction. Intact (commit `c86b83c`). |
| 3 | S3 lifecycle | `backend/domain/report_lifecycle.py` (6 states, guarded transitions, audit-event names, declared authority), `ReportVersionsRepository.get_by_number()/set_status()` (atomic expected-state guard), version-scoped endpoints, append-only audit events. Intact (commit `19e4f01`). |
| 4 | Report generation/read APIs | `backend/api/v3_reports.py` (`/api/v3/reports`): `GET ""`, `POST ""`, `GET /{id}`, `GET /{id}/content`, `GET /{id}/versions`, `GET /{id}/download`, `GET /{id}/pdf`, plus S3 lifecycle endpoints. `backend/data/reports.py` maps `report_generation_queue` rows. |
| 5 | Authorization helpers | `api/dependencies.ensure_org_access`, `auth.require_org_member`, `require_org_admin`; the S3 customer-only guard rejects PE / internal staff / non-org-members. |
| 6 | Audit conventions | Canonical append-only `public.audit_trail` via `AuditRepository.record()` (INSERT-only); taxonomy in `domain/audit.py` (`ACTOR_*`, `CAT_REPORT`, `ORIGIN_*`, `OUTCOME_*`); `report*` actions classify to `report`. |
| 7 | `narrative_overlay` references | **NONE** anywhere in the repository (backend, frontend, SQL) except an S3 migration comment stating it is deliberately absent. |
| 8 | Frontend/API consumers | No frontend or API consumer reads or writes a narrative overlay; the dormant `report_generation_queue.user_edits` column is selected in SQL but **not returned by `_row_to_report_full`** (genuinely unexposed) — matching the ratification's "dormant and unexposed". |

## 3. Authoritative documents reviewed

1. `docs/architecture/CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` (§9, §10, §10.1–§10.3, §11, §12–§15, §21.2, §25, §34, §35).
2. `docs/architecture/CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md` (§8.3.1, §9.1–§9.3, §10, D-18/D-19, A1).
3. `docs/architecture/CARBONTALLY_PHASE8_OPEN_DECISION_CLOSURE_AND_IMPLEMENTATION_AUTHORISATION_20260912.md` (A1, A3, §14 matrix, §16).
4. S1 and S3 implementation/verification reports.
5. Current report-generation code and schema.

## 4. Existing implementation discovered

* **No narrative layer exists.** No version-scoped narrative store, no overlay column, no editing
  endpoint, no validation, no render-time composition.
* The ratified **principle** and **namespace boundary** are fixed; the **exact field allowlist and
  limits are explicitly undecided** (see §5).
* The lifecycle and audit foundations S4 depends on already exist (S1/S3), so the *mechanism* is
  buildable — but the *policy inputs* S4 must encode are not yet decided.

## 5. Why this is a HARD STOP (the block)

The S4 instruction states: *"If the specification does not contain enough information to implement a
safe allowlist, STOP and report the gap rather than inventing one."* and lists **"the existing
narrative allowlist is missing/ambiguous"** and **"required authorization rules cannot be
determined"** as hard-stop conditions. The authoritative documents are unambiguous:

**A. The exact allowlist is explicitly `PO DECISION REQUIRED` (not decided).**

* Ratification §9.1.2 (verbatim): *"The exact field allowlist is **`PO DECISION REQUIRED`** (§24 A1)
  — this ratification fixes the **principle and the namespace boundary**, not the final key list."*
  (`CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md:466-467`)
* Ratification D-18: *"`RATIFIED` (principle) / **`PO DECISION REQUIRED`** (allowlist)."* (line 1059)
* Spec §10.1 is titled **"Recommended editable set (bounded, narrative-only)"** — a recommendation,
  not a decision (lines 412-422).
* Spec §34 P3: *"Exactly which report sections/fields are customer-editable? — **RECOMMENDED**
  (§10.1 bounded narrative namespace) — **final PO DECISION REQUIRED**"* (line 1576).
* Spec §34 A1: *"May a consultant edit a client's narrative, and may a Customer Member edit? —
  **PO DECISION REQUIRED**"* (line 1602).

**B. The numeric limits (which make the layer "bounded") are explicitly `PO DECISION REQUIRED`.**

* Spec §10.3: *"**Maximum lengths** per field and per version (**numeric limits are a PO decision —
  §34-A3**)."*
* Spec §34 A3: *"Narrative field length limits, item counts, and formatting — … numeric values
  **PO DECISION REQUIRED**"* (line 1604).
* Ratification A1: *"…which keys, types, **length limits**, formatting, and **who may edit**
  (Owner/Admin/Member/consultant) … **numeric values are a PO call**"* (line 1160).

**C. Shipping the S4 editing endpoint before those decisions is explicitly prohibited.**

* Closure/Auth doc A1 (`DEFER`): *"**Risk if deferred:** none, **provided no editing endpoint ships
  before the allowlist exists.**"* (lines 727-736)
* Closure/Auth doc A3 (`DEFER`): *"**If deferred:** fine, **provided the S4 endpoint does not ship
  without caps.**"* (lines 750-759)
* Closure/Auth matrix: A1 — *"Decide before S4"*; A3 — *"Decide with A1"* (lines 1061, 1063);
  *"A1 / A3 narrative model | **S4** | **PO decision on the allowlist and limits**"* (line 1167);
  §16 lists *"narrative allowlist"* among outstanding PO decisions (line 1263).

**D. "Who may edit" is also undecided.**

* Ratification §8.3.1: Members' narrative editing is *"**per policy (§24)**"* and *"Members'
  editing/commenting rights are **per explicit permission** (§24 A1)."* (lines 349, 355-356).
  Consultant narrative authorship on a *client's* deliverable is explicitly *"**PO DECISION
  (§34-A1)**"* (spec §15.2, line 635).

**Conclusion.** The ratified design fixes the *principle*, the *namespace boundary*, the
*plain-text / no-HTML / no-links* rule and the *allowlist-not-blocklist* rule — all of which S4 must
honour — but the **exact key list, types, numeric caps and editor set are undecided PO policy**.
Adopting §10.1's *recommended* keys plus invented caps would be exactly the "invent one" action the
instruction forbids, and would contradict the closure document's explicit prohibition. No later
document resolves A1/A3: the newest docs (RLS security hold/register, Phase 8-X discovery, Phase 9
baseline) do not decide the narrative allowlist, and no S4/narrative decision exists in
`docs/cline/prompt-history/`.

## 6. Exact S4 scope implemented

**NONE.** No part of the narrative-overlay capability was implemented (no storage, no validation, no
allowlist, no endpoints, no audit events). Implementing the editing path was prohibited by the
authoritative documents until A1/A3 are decided (§5 C).

## 7. Files changed

**None.** No source, test, migration, documentation or configuration file was modified, added or
deleted by this task, other than this report:

* `docs/cline/reports/CT-P8-REPORTING-S4-NARRATIVE-OVERLAY-20260912-001.md` (new — this report)

## 8. Database / schema changes

**None.** No migration was created or applied. No `narrative_overlay` column was added. No RLS policy,
grant, function or table was touched. No production database was contacted or altered.

## 9. API changes

**None.** No endpoint was added, changed or removed; the `/api/v3/reports/...` surface is exactly as
S3 left it.

## 10. Authorization changes

**None.** No authorization helper, role, capability or guard was added, broadened or altered.

## 11. Audit changes

**None.** No audit event, taxonomy entry or audit path was added or modified; the append-only
`audit_trail` architecture is untouched.

## 12. Tests added

**None** (S4 tests cannot be written against an undecided allowlist without encoding invented policy).

## 13. Test commands and results

No implementation ⇒ no S4 tests. To demonstrate the reporting baseline is intact and unaffected, the
existing reporting suites were run (read-only; no source change):

| Command (from `backend/`) | Exit | Result |
|---|---|---|
| `.venv/bin/python -m pytest tests/unit/api/test_v3_report_lifecycle.py tests/unit/api/test_v3_reports.py tests/unit/api/test_reporting.py -q` | **0** | **118 passed** |

## 14. Pre-existing test failures

The four known pre-existing integration failures caused by the non-UUID literal `"user-1"` bound to
UUID columns are unchanged and were **not** touched:
`test_create_and_roundtrip_version`, `test_mark_generating`, `test_mark_failed_persists_error`,
`test_create_request_records_created_by_and_name`. They are unrelated to S4 (no S4 code exists).

## 15. No RLS / grant / security remediation performed

**Confirmed.** No RLS was enabled, disabled, or altered; no policy was created, dropped or modified;
no grant was added or revoked; no `SECURITY DEFINER` function was touched; RLS-4A-1/RLS-4A-2 and the
production RLS remediation sequence were **not** implemented or applied; the outstanding production
migration backlog was **not** batch-applied. The separate OHD production RLS security hold is
untouched. (This task made no schema or database change of any kind.)

## 16. No production changes

**Confirmed.** No production database, environment, deployment, Render configuration or migration
history was contacted or modified. Only local read-only inspection was performed (schema/column and
RLS posture of `carbontally_test`/`postgres`).

## 17. No unrelated worktree changes discarded

**Confirmed.** No `git reset`/`clean`/`stash`/`checkout`/`restore` was run; no pre-existing modified
or untracked file was overwritten, deleted or staged. The two RLS security documents, the Phase 8-X
discovery document, the Phase 9 baseline and its prompt-history, and every other pre-existing
change remain exactly as found.

## 18. Git / worktree status

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` (unchanged — S3, parent `b471286`) |
| Modified files | **208** (pre-existing set, unchanged) |
| Untracked files | **57** entries (pre-existing set; this report is inside the already-untracked `docs/cline/reports/`) |
| Staged files | **0** |
| Commit created during this task | **NO** |
| Pushed | **NO** (`main` ahead 14 of `origin/main`) |

Baseline at task start was 264 entries (208 modified / 56 untracked); the single-entry drift is
attributable to **other processes** creating docs (e.g. `docs/ohd/reports/…`, the RLS security
register) during the session — not to this task.

## 19. Deviations from the authorized S4 scope

**None.** The task was stopped at the documented hard-stop rather than deviating. No partial,
speculative or alternative narrative mechanism was introduced, and no S2/S5/S6/S8 or AI/Insight/RLS
work was performed.

## 20. Remaining limitations

* S4 is **not implemented**; the bounded narrative overlay does not exist.
* The S4 dependencies that **do** exist and are ready to build on: S1 `is_current` invariant,
  S3 lifecycle states/guards/endpoints, the version-scoped repository primitives
  (`get_by_number`, guarded `set_status`), and the canonical append-only audit trail with the
  `report` taxonomy.
* Until A1/A3 are decided, any narrative editing endpoint would ship unbounded/unallowlisted input,
  which the closure document explicitly prohibits.

## 21. Recommended next step

1. PO decides **A1** (the exact narrative field allowlist: keys, types, formatting, and **who may
   edit** — Owner/Admin/Member and whether a consultant may edit a client's narrative) and **A3**
   (numeric caps: per-field and per-version maximum lengths, and item counts) — and confirms
   **P3**. The natural baseline is the spec §10.1 recommendation, which must be explicitly adopted
   or amended.
2. Re-issue **S4** with the decided allowlist and caps. S4 can then be implemented as a minimal
   additive migration (`report_versions.narrative_overlay JSONB`), server-side allowlist/plain-text
   validation, version-scoped retrieval/replace/clear endpoints restricted to the ratified editor
   set with DRAFT-only edits (T14/T15), and append-only `report.narrative_edited` audit events —
   reusing the S1/S3 primitives and the existing authorization/audit architecture, with **no RLS
   change**.

---

## Appendix — minimum decisions required to unblock S4

| Decision | Content needed | Source |
|---|---|---|
| **A1** | Exact allowlist: which of the §10.1 recommended keys are adopted (management_commentary, organisational_context, operational_changes_explanation, initiatives, reduction_actions, future_plans, section_notes), their types, formatting, and **who may edit** (Owner/Admin/Member/consultant) | Spec §34-A1, §10.1, §15.2; Ratification §9.1.2, §8.3.1, A1 |
| **A3** | Numeric limits: max length per text field, max length per version, max items per structured list, allowed `section_notes` keys | Spec §34-A3, §10.3 |
| **P3** | Confirmation of which report sections/fields are customer-editable | Spec §34-P3 |

---

## Final verdict

`S4 IMPLEMENTATION BLOCKED — PO/ARCHITECTURE REVIEW REQUIRED`

**Reason:** the bounded narrative overlay's **exact field allowlist (A1)** and **numeric limits (A3)**
are, by the ratified Phase 8 documents, explicitly `PO DECISION REQUIRED` and undecided; the closure
authorisation document states the S4 editing endpoint must **not** ship before the allowlist and caps
exist. Implementing S4 now would require inventing the policy inputs the task instruction forbids
inventing. No code, test, migration, RLS or production change was made.



