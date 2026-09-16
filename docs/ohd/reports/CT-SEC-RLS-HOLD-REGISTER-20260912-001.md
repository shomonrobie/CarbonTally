---
Document Type: OHD Task Report
Project: CarbonTally
Prompt ID: CT-SEC-RLS-HOLD-REGISTER-20260912-001
Status: COMPLETE
Created: 2026-09-12
---

# OHD Task Report — CT-SEC-RLS-HOLD-REGISTER-20260912-001

## 1. Prompt ID

`CT-SEC-RLS-HOLD-REGISTER-20260912-001`

## 2. Objective

Create a permanent, PO-controlled **RLS Security Hold & Remediation Register** for
CarbonTally, based strictly on the already-completed OHD production RLS baseline
and remediation specification, so that the verified production security findings
and the agreed remediation direction are preserved while Phase 8 and the
subsequently defined Phase 8-X operational-intelligence work are completed.

Documentation and project-control only. No implementation of any kind.

## 3. Source Documents Reviewed

| Document | Use |
|---|---|
| `docs/architecture/CARBONTALLY_RLS_PRODUCTION_BASELINE_AND_REMEDIATION_SPEC_20260912.md` | **Authoritative source.** Verified production findings, evidence classification, F-1…F-9 dispositions, remediation groups (RLS-4A…RLS-6), prerequisites, migration drift analysis, PO decision questions. Re-read directly (not from memory) at §2 baseline, §5.2 prerequisites, §8 RLS-4A group, §14 PO decisions. |
| `docs/architecture/CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md` | Predecessor reconciliation; first `emission_factors` exposure record. |
| `docs/architecture/CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md` | Migration-by-migration production status; batching prohibition evidence. |
| `docs/architecture/CARBONTALLY_PRODUCTION_READINESS_AUDIT_20260911.md` | Production readiness position. |
| `docs/architecture/CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md` | Authentication/access model. |
| `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` | Architecture source of truth. |
| `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` | PO-ratified roadmap (terminates at Phase 8). |
| `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` | Actor/workspace/access model; historical recursion-fix lineage (§39, §39.1). |
| `docs/architecture/CARBONTALLY_PHASE9_SYSTEM_RUNTIME_AND_OPERATIONAL_INTELLIGENCE_BASELINE_20260912.md` | Historical operational-intelligence baseline (unratified "Phase 9" filename; referenced only to prevent identifier confusion). |
| `database/rc1/004_rc1_rls.sql`, `database/rc2/004_rc2_rls.sql` | RC RLS storeys; tenancy-hole warning; "never DISABLE RLS" guidance. |
| `supabase/migrations/00000000000000_init_schema.sql` | Bulk RLS-enablement loop (lines 2319–2324) — drift root cause. |
| `supabase/migrations/20260822000000_p9_rls_recursion_fix.sql` | Hard prerequisite. |
| `supabase/migrations/20260831030000_tenant_org_id_not_null.sql` | Hard prerequisite. |
| `backend/infra/supabase.py` | Backend privileged (`BYPASSRLS`) access path. |
| `frontend/src/lib/realtime/manager.js` | Realtime subscription inventory. |
| `AGENTS.md` | Governance: RLS policy, database change policy, tenant isolation, security boundary. |

All 16 paths were confirmed to exist before citation (existence check performed).

## 4. Document Created

| Path | Status |
|---|---|
| `docs/architecture/CARBONTALLY_PRODUCTION_RLS_SECURITY_HOLD_AND_REMEDIATION_REGISTER_20260912.md` | **CREATED** — contains all 12 required sections |
| `docs/ohd/reports/CT-SEC-RLS-HOLD-REGISTER-20260912-001.md` | **CREATED** — this report (`docs/ohd/reports/` did not exist and was created as the task-specified destination) |

### 4.1 Required sections present in the register

1. Purpose · 2. Current Status · 3. Why the Work Is Deferred · 4. Verified
Production Baseline (incl. evidence limitations) · 5. Security Findings (incl.
"what is not claimed") · 6. Proposed Remediation Sequence (incl. RLS-4A-1 /
RLS-4A-2 split) · 7. Known Prerequisites (incl. batching prohibition) ·
8. PO Decisions Still Required · 9. Explicit Non-Actions · 10. Reopening
Condition · 11. Relationship to Phase 8 and Phase 8-X · 12. Source and Lineage ·
13. Project-Control Status Summary.

### 4.2 Documentation-quality controls applied

* **Verified facts vs proposed remediation vs future decisions** are separated by
  section (facts in §4–§5; proposal in §6–§7; open decisions in §8).
* **Implemented / verified / deferred / not authorized** are distinguished
  explicitly in §2, §6 and §9.
* **No unsupported compliance claims.** The register states in §5.2 that it makes
  **no** GDPR / UK GDPR / Irish data-protection statement and asserts **no**
  certification, audit or assurance status.
* **No Phase 9 created or implied** — stated in §3, §11 and §12.5.
* Ratified terminology preserved (RLS group identifiers; "DEFERRED / NOT YET
  AUTHORIZED"; the two hard prerequisites by exact migration filename).
* The register duplicates **no** technical specification; the authoritative
  detail remains the source report (§12.1).

## 5. Exact Scope Performed

1. Recorded the git/worktree baseline (HEAD, branch, modified/untracked counts).
2. Verified existence of all 16 cross-referenced documents/artefacts.
3. Re-read the authoritative source report directly — its §2 (production
   baseline), §5.2 (hard prerequisites), §8 (RLS-4A group definition) and §14
   (PO decisions) — rather than relying on recalled content.
4. Confirmed there are **no** pre-existing "Phase 8-X" references in the
   repository (0 matches), so the register records it as the PO's designation and
   cross-references the historical operational-intelligence baseline to prevent
   identifier confusion.
5. Created `docs/ohd/reports/` (did not previously exist) as the task-specified
   location for the mandatory report.
6. Authored the register with all 12 required sections plus a project-control
   status summary.
7. Authored this task report.
8. Performed final verification of git/worktree state.

**Not performed:** any RLS remediation, any grant/policy/function change, any
migration creation or application, any production or configuration change, any
code or schema change, any commit or push.

**Read-only database or production access during this task: NONE.** No database
or production command was run in this task. The register's §4 baseline is
transcribed from the authoritative source report, which is clearly stated as a
point-in-time snapshot requiring re-verification on reopening (register §9.2,
§10).

## 6. Confirmation — No Code / Schema / RLS / Grant / Function / Production Changes

Confirmed: **no** changes were made to:

* application code — **NO**
* database schema — **NO**
* migrations (created, modified, or applied) — **NO**
* RLS enabled or disabled — **NO**
* RLS policies (created, altered, dropped) — **NO**
* grants (GRANT or REVOKE) — **NO**
* `SECURITY DEFINER` functions — **NO**
* Supabase configuration — **NO**
* production configuration — **NO**
* production data (read or written) — **NO**
* tests — **NO**
* any documentation other than the two files in §4 — **NO**

## 7. Confirmation — No RLS Remediation Implemented

Confirmed: **no** remediation group from the proposed sequence was implemented.

| Group | Implemented? |
|---|---|
| RLS-4A-1 — Anonymous Access Containment | **NO** |
| RLS-4A-2 — Authenticated Grant Hardening | **NO** |
| RLS-4 → Function / `SECURITY DEFINER` hardening | **NO** |
| RLS-5 — Policy correctness | **NO** |
| RLS-3 — Reference / static tables | **NO** |
| RLS-2 — Operational / control-plane tables | **NO** |
| RLS-1 — Critical tenant / customer tables | **NO** |
| Group verification | **NO** |

No outstanding migration was applied. No migration batch was applied.

## 8. Confirmation — RLS-4A-1 Status

> **RLS-4A-1 (Anonymous Access Containment) remains NOT AUTHORIZED / DEFERRED.**

This is stated in the register at §2 (status table), §6 (group status), §9
(explicit non-actions), §10 (reopening condition) and §13 (project-control
summary). The register explicitly states that RLS-4A-1 is **not** automatically
authorized by this register, by the passage of time, by completion of Phase 8 or
Phase 8-X, or by any other event — only an explicit PO authorization opens the
gate.

## 9. Discrepancies and Ambiguities Discovered

| # | Item | Disposition |
|---|---|---|
| **A-1** | **RLS-4A split.** The source report defines a single group **RLS-4A** ("Anonymous grant reduction"). The task instruction defines it as two sub-steps: **RLS-4A-1 (Anonymous Access Containment)** and **RLS-4A-2 (Authenticated Grant Hardening)**. | Recorded as the PO's refinement. The mapping is faithful to RLS-4A's own "desired state" clause (anon → no privileges; authenticated → DML only), so no finding is altered. Flagged in the register §6 for transparency. |
| **A-2** | **RLS-4 is absent from the task-stated sequence.** The task states the sequence as `RLS-4A → RLS-5 → RLS-3 → RLS-2 → RLS-1 → verification`. The source report's sequence additionally contains **RLS-4 (Function / `SECURITY DEFINER` / privilege hardening)**, to which findings **F-5 (TRUNCATE)** and **F-6 (`anon` `EXECUTE`)** are assigned. | **NOT RESOLVED — flagged for PO confirmation** (register §6.1, decision **D-13**). The register records the PO-stated sequence as its sequence and warns that if RLS-4 is genuinely dropped, F-5 and F-6 must be explicitly reassigned to RLS-4A-1 / RLS-4A-2 or they will be lost. Recorded rather than silently resolved, per the instruction not to reinterpret the source. |
| **A-3** | **"Phase 8-X" is a new designation.** A repository-wide search found **0** pre-existing references to "Phase 8-X". The operational-intelligence workstream's only existing baseline carries a historical filename using "Phase 9" (`CARBONTALLY_PHASE9_SYSTEM_RUNTIME_AND_OPERATIONAL_INTELLIGENCE_BASELINE_20260912.md`), whose identifier was never PO-ratified. | Recorded faithfully: the register uses **Phase 8-X — Operational Intelligence** as the PO's designation, and §11 explicitly states that the historical document does **not** create a Phase 9 and must not be read as doing so. **No Phase 9 was created, assigned or implied by this task.** |
| **A-4** | **Q2 / D-2 wording.** The source report's decision is labelled "Accept the **unaudited** status of 12 tables missing from production". | The register preserves the decision and its blocking effect while phrasing it as "the status of the 12 production-missing tables", avoiding any implication of an audit determination. No finding is weakened: the 12 missing tables are still recorded in §4.3 with their exact names. |
| **A-5** | **Worktree delta not attributable to this task.** Untracked count moved from **53** at the end of the previous task to **54** at the start of this task, due to an unrelated directory created at 16:54:25 (`docs/cline/reports/`). Separately, `supabase/snippets/Untitled query 673.sql` is an untracked Supabase Studio scratch file. | **Not touched, not modified, not removed.** Reported for accuracy. Neither is attributable to this task. |
| **A-6** | **Baseline staleness.** The register's §4 production baseline is a 2026-09-12 point-in-time snapshot. | Explicitly documented as requiring re-verification before remediation is authored (register §3, §9.2, §10). No claim is made that the baseline is current. |

No discrepancy required stopping the task; none required a code, schema, RLS,
grant, function, or production change.

## 10. Git / Worktree Status

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD (start of task) | `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| HEAD (end of task) | `19e4f01c176eee5870f3c15038b6e7c68b23281c` — **unchanged** |
| HEAD commit | `feat: implement Phase 8 report lifecycle foundation` |
| Modified (tracked) files | **208** — unchanged; no tracked file was modified by this task |
| Untracked files | **54** at task start → **56** at task end (**+2**: this register and this report) |
| Staged files | **0** |
| Commits created | **0** |
| Pushed | **NO** |
| Reset / clean / stash | **NONE performed** |
| Unrelated work | **Preserved exactly** |

Pre-existing modified and untracked work was preserved without exception. No file
outside the two created by this task was written, staged, reverted or removed.

## 11. Final Verdict

**`RLS SECURITY HOLD REGISTER CREATED — REMEDIATION DEFERRED`**

---

## Appendix — Register Status Line (as published)

```text
RLS PRODUCTION SECURITY REMEDIATION — DEFERRED / NOT YET AUTHORIZED

Discovery : COMPLETE (read-only, independently performed)
Baseline  : VERIFIED 2026-09-12 (point-in-time; re-verify on reopening)
Remediation implemented : NO
RLS-4A-1  : NOT AUTHORIZED / NOT IMPLEMENTED
RLS-4A-2  : NOT AUTHORIZED / NOT IMPLEMENTED
Reopening : explicit Product Owner authorization only
```
