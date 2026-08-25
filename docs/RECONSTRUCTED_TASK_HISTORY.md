---
Document Type: Reconstructed Task History
Project: CarbonTally
Version: 1.0
Status: RECONSTRUCTED — copy of prior session history (no source of truth file existed)
Reconstructed: 2026-08-20
Author: Cline
Sources: git history (69 commits, HEAD a909cbe), docs/audit/cline/*, docs/cline/*, docs/Todos.md, docs/architecture/*
---

# CarbonTally — Reconstructed Task History

This document reconstructs the sequence of engineering tasks performed on the
CarbonTally codebase. No single authoritative "task history" existed, so the
history below is triangulated from three ground-truth sources:

1. **Git history** — 69 commits on `main`, HEAD `a909cbe` (2026-08-15).
2. **V3 audit & phase reports** — `docs/audit/cline/` (migration records,
   Phase 4–8 reports, resumption report, conformity gate).
3. **Planning/architecture docs** — `docs/architecture/`, `docs/cline/`,
   `docs/Todos.md`.

> **Important convention:** the codebase carries **two independent "Phase"
> numbering systems**. The **git commit phases** (Phase 0–8, committed
> 2026-08-07/08) describe the *V2.1 backend build*. The **V3 consolidation
> phases** (Phase 1–8, dated 2026-08-14…16) are the *V2.1 → V3 migration* and are
> documented in `docs/audit/cline/`. They do not map 1:1 (e.g. git "Phase 5:
> Emissions Calculation" ≠ V3 "Phase 5: Reporting"). This document separates them.

---

## 1. Timeline at a glance

| Era | Window | Theme | Evidence |
|---|---|---|---|
| 0 | **pre-2026-07-17** | Earliest product work — not in current repo history (clean-slate superseded it) | git log starts 07-17 |
| 1 | **2026-07-17 → 07-18** | Monorepo restructure; Render deployment prep | commits `7ca9533`…`d70db74` |
| 2 | **2026-07-21 → 07-24** | Backend folder move; admin dashboard; Google OAuth; mobile responsive; **v3.0 feature-complete** | `8b59378`…`a34b2f0` |
| 3 | **2026-07-23 → 07-27** | Staff/review/assignment; beta management; admin & log viewer | `987500a`, `9c68ab1` |
| 4 | **2026-08-04 → 08-06** | Database baselines RC1 → RC2 → RC2-final; schema/foundation | `9f87229`, `a054991`, `2d23fb8` |
| 5 | **2026-08-07 → 08-08** | **V2.1 backend architecture build** (git Phases 0–8) | `97e0f69`…`8bcd490` |
| 6 | **2026-08-14** | V2.1 + V3 DB foundation verified; V3 backend consolidation began | `dbe72aa`; docs 08-14 |
| 7 | **2026-08-14 → 08-16** | **V3 consolidation Phases 1–8** (inventory, core, doc/processing, factor-matching, emissions, reporting, customer-admin, consultant, ops/QC) | `docs/audit/cline/CarbonTally_V3_*_Phase_*` |
| 8 | **2026-08-16** | Power-loss resumption; Phase 5 runtime verification; Phase 8 finished; **full unit suite green (~900)** | `CARBONTALLY_V3_RESUMPTION_AFTER_POWER_LOSS.md` |
| 9 | **2026-08-15 → 08-17** | V3 checkpoints + Render-ready backend; pre-Phase-9 conformity/architecture gates | `cfabe26`, `a909cbe`; gates 08-17 |
---

## 2. Reconstructed task sequence (detailed)

### Era 1 — Monorepo restructure & Render deployment (2026-07-17 → 07-18)

- 07-17 `7ca9533` — **Clean slate**: CarbonTally restructured into one monorepo.
- 07-17 → 07-18 `35dbcd6`, `6344456`, `308c7a5` — Prepare backend for **Render**
  deployment: added `requirements.txt`, updated CORS, pinned Python 3.11.9 and
  stable pandas/numpy to stop build errors.
- 07-18 `8d5f021` etc. — Fixes: CSV header **smart column mapping**; replace the
  Review Queue; catch backend errors and surface detail to frontend; correct the
  live `carbontally.co.uk` CORS; add `react-hot-toast`; landing page.

### Era 2 — Backend restructure, admin, auth, mobile (2026-07-21 → 07-24)

- 07-21 `8b59378` — Move backend files into `/backend/`.
- 07-21 → 07-24 — Admin dashboard; `requirements.txt`; fix supabase package name;
  Google OAuth sign-in + organization support; complete mobile responsiveness;
  report-generation updates.
- **07-24 `a34b2f0` — "v3.0 feature-complete"**: the full monolith v3.0 — e-mail +
  Google OAuth auth, beta invite management, CSV/PDF/image upload + AI extraction,
  bulk upload + manual review queue, review/correction, emissions dashboard +
  charts, SECR/CSRD/ISSB report generation, team/roles, asset & facility
  management, onboarding wizard, glossary, DB-driven DEFRA factors.
- 07-24 — a flush-run of **deployment bug-fixes** (~20 commits): beta signup,
  beta login (1→6), admin dashboard (×5), supabase client (×2), backend
  requirements, secure admin routing refactor, wildcard admin-subpath fallback
  (404s), pydantic e-mail validation + resend config.

### Era 3 — Staff / review / beta-admin / log (2026-07-23 → 07-27)

- 07-23 `987500a` — Staff dashboard, review assignment, beta management.
- 07-27 `9c68ab1` — **Major update**: Manual Entry, Staff Review Queue, Admin
  Assignment, Document Status, Log Viewer.

### Era 4 — RC1 → RC2 database baselines (2026-08-04 → 08-06)

- 08-04 `9f87229` — **RC1** database full (schema baseline).
- 08-04 → 08-06 — `rc2` database full; RC2 **Final** database baseline
  (`2d23fb8`, tag `rc2-final`).
- 08-04 — device/branding polish: stop tracking SQL backups, update sidebar
  styles, fix case-sensitive sidebar import, restore missing `RealtimeContext.jsx`.

### Era 5 — V2.1 backend architecture build (backend commit phases, 2026-08-07 → 08-08)

> These are the **commit-level** phases — the original layered V2.1 backend.

- 08-07 `97e0f69` — **Phase 0–2**: CarbonTally architecture foundation.
- 08-07 `a57c224` — **Phase 3**: Infrastructure layer (tag `v2.1.1-phase3`).
- 08-07 `a13fd10` — **Phase 4**: Factor-matching engine (tag `v2.1-phase4`).
- 08-07 `0a5a603` — **Phase 5**: Emissions calculation engine.
- 08-07 `c5eadec` — **Phase 7**: Document processing + AI Extraction.
- 08-08 `e57543d` — **Phase 8**: Workflow Orchestrator.
- 08-08 `8bcd490` — Fix integration-test database isolation.

### Era 5b — V2.1 + V3 database foundation verified (2026-08-14)

- `dbe72aa` — "checkpoint: verified V2.1 and V3 database foundation" against the
  V3M2 (RC2) schema.

### Era 6 — V3 backend consolidation (2026-08-14 → 08-16)

> The V3 layered architecture (`api → engines → domain → data → infra → core`)
> was built from the V2.1 monolith; each phase carried an audit report in
> `docs/audit/cline/`.

| V3 Phase | Focus | Report(s) |
|---|---|---|
| **Inventory** | Full V2.1 component KEEP/EXTEND/REPOINT/REFACTOR/NEW/DEPRECATE classification | `CarbonTally_V3_Backend_V2.1_to_V3_Migration_Inventory_v1.0.md` |
| **1** | Backend consolidation (architecture re-plan + inventory) | `..._Phase1_Backend_Consolidation_Report_v1.0.md` |
| **2** | Composition / core services: `domain/{entity,customer_factor,issue}`, repositories, auth, dependencies, 3 routers | `..._Migration_Phase_Records_v1.0.md` §2 |
| **3** | Document / processing backend: preserve extraction engines, factor-matching boundary | `Migration_Phase_Records_v1.0.md` §3 |
| **4** | Factor matching + emissions intelligence: `engines/factor_matching.py`, `api/v3_emissions.py`, authoritative calc | `CARBONTALLY_V3_PHASE_4_REPORT.md` |
| **5** | Reporting: `api/v3_reports.py`, report lifecycle/versions/download, frontend | `CARBONTALLY_V3_PHASE_5_REPORT.md` |
| **6** | Customer administration: org profile/settings/members/invitations/roles/suppliers/facilities/assets | `CARBONTALLY_V3_PHASE_6_REPORT.md` |
| **7** | Consultant / multi-client: consultant profiles, firm members, client access | `CARBONTALLY_V3_PHASE_7_REPORT.md` |
| **8** | Internal ops / processing / QC: ops dashboard, staff roster, operator/reviewer/QC queues, assignments, SLA, frontend + tests | `CARBONTALLY_V3_PHASE_8_REPORT.md` |

Adjacent audit docs record: repository-integration diagnosis + fix-verification,
a full-integration failure diagnosis, legacy re-implementation, the
new-capabilities inventory, the processing-workflow report, and the ADR-V3.004
audit (confirms NO `/process`/`/jobs` worker infra — deferred by design).
### Era 7 — Power loss → resumption & Phase-5 verification (2026-08-16)

- A **PC power loss** stranded the session. V3 Phases 1–7 were complete; **Phase 8
  was IN PROGRESS**.
- `CARBONTALLY_V3_RESUMPTION_AFTER_POWER_LOSS.md` established the resumption point
  at Phase 8 and recorded the completed **Phase-5 runtime verification**: the V3
  Phase-5 unit suite ran **40/40 PASS** after repairing two pre-existing
  non-Phase-5 syntax defects and fixing 4 Phase-5 test bugs.
- Full-suite failure classification: ~205 environment (`pytest-asyncio` missing),
  ~9 FastAPI 0.141 route-harness, 6 native assertions — none in Phase-5's own
  files.

### Era 8 — V3 baseline + Render-ready checkpoint (2026-08-15)

- `cfabe26` — **checkpoint: CarbonTally V3 baseline**.
- `a909cbe` (tip/HEAD) — **checkpoint: CarbonTally V3 Render-ready backend**.

### Era 9 — Final architecture gates (2026-08-17)

- **Architecture Conformity Gate** (`CARBONTALLY_V3_ARCHITECTURE_CONFORMITY_GATE.md`):
  V3 Phases 3–8 complete; unit suite ≈900 RC=0; verdict **READY WITH CONDITIONS** —
  two competing entry points (`main.py` legacy + `main_v2.py`) not yet
  consolidated; **Phase 9 not started**.
- **ADR-V3.004 Implementation Verification Audit**: confirms no
  `document_processing_queue` consumer/worker exists (producer/consumer deferred).

---

## 3. Current state

- **HEAD:** `a909cbe` "checkpoint: CarbonTally V3 Render-ready backend"
  (2026-08-15). `main` == `origin/main`.
- **Backend:** V3 layered architecture (api → engines → domain → data → infra),
  V3 Phases 4–8 implemented, **unit suite green (≈900, RC=0)**; two competing
  entry points remain (`main.py` legacy + `main_v2.py`).
- **Frontend:** V3 report(s)/report-detail, ops-dashboard, staff-roster,
  operator/reviewer/QC queue screens present.
- **Databases:** RC1 → RC2 (final) baseline verified against the V3M2 (RC2)
  schema.

## 4. Likely next steps (from gate reports, not yet executed)

- **Phase 9** (per `docs/cline/CarbonTally-Phase9*` + the V3 consolidation plan):
  analyst surface, benchmarking, report generation. The conformity gate states
  "Phase 9 NOT started".
- Consolidate the two competing backend entry points; retire the legacy
  `backend/routes/**` surface.
- Adopt documented NOT-IMPLEMENTED follow-ons from Phase 5/6: report comments,
  export-history, MFA/TOTP, PDF/HTML report rendering.

## 5. Provenance & known gaps

- **No single task-history store existed** — this reconstruction triangulates
  the 69-commit `git log`, phase/audit reports, and planning docs. Within a day,
  ordering is by commit; commit wording is retained.
- **Earliest origin** (pre-2026-07-17) is not recoverable from `git` (a clean
  slate superseded it); earlier feature context appears in `docs/Todos.md`.
- Phase numbering differs between the V2.1 build (git) and the V3 consolidation
  (reports); this document keeps them distinct (see note at top).
- Some early V3 phase reports note "RUNTIME VERIFICATION PENDING (shell
  unavailable)" — later audits confirm the shell executed when output was
  redirected, and the conformity gate cites ≈900 unit tests green (RC=0).