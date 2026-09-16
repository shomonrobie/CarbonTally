# PHASE 8 GIT BOUNDARY AUDIT

**Report ID:** `CT-P8-GIT-BOUNDARY-AUDIT-20260915` · **Prompt:** `CT-P8-GIT-BOUNDARY-01`
**Type:** READ-ONLY audit (this report is the only file created) · **Date:** 2026-09-15
**Baseline:** branch `main` · HEAD `20d27c0` · `origin/main` `9e13236` · staged 0

---

## A. Phase 8 workstream inventory

| Workstream | Implemented | Independently verified | PO-closed | Evidence |
|---|---|---|---|---|
| **B1** — disclosure model foundation + correction | Yes | Yes (V1 `…014`, V1R `…016`) | Yes (`…010`, `…011`, `…012`) | 9 × `CT-P8-B1-*`, `CARBONTALLY_PHASE8_B1_*`, `…_DISCLOSURE_MODEL_*` |
| **B2** — evidence line items + provenance | Yes | Yes (`…025`) | Yes (`CT-P8-B2-PO-CLOSURE-20260913-028.md`) | 7 × `CT-P8-B2-*`, `…_B2_IMPLEMENTATION_CONTRACT_…` |
| **B3** — intensity catalogue + ratios | Yes | Yes (`…033`) | Yes (`…051`, decisions `…031`/`…058`) | `CT-P8-B3-*`, `…_B3_*` |
| **B4** — narrative overlay + frozen artefact | Yes | Yes (gate V4 + fresh-clone replay `…055`) | Yes (`…052`) | `CT-P8-B4-*`, `…_B4_IMPLEMENTATION_CONTRACT_…` |
| **S1/S3** — lifecycle/state invariants | Yes | Yes (`…030`, `…056`) | Yes | `CT-P8-S1S3-INDEPENDENT-VERIFICATION-*` |
| **S2** — `is_current` single-valued | Yes | Yes | Yes (`…046`) | report + migration `…_p8_s2_is_current_single_valued.sql` |
| **S6** — report lifecycle visibility-first | Yes | Yes | Yes (`…063` §12) | `CT-P8-S6-IMPLEMENTATION-AND-IV-…-063.md` |
| **RLS-4A-1 / RLS-4A-2** hardening | Yes | Yes (`…060`, `…059`) | Yes | 3 untracked RLS migrations |
| **P1** — PDF/image extraction remediation | Yes | Yes | Yes (`…053`) | `CARBONTALLY_PHASE8_P1_*` (3) |
| **P2** — EF-E selection + catalogue census | Yes (EF-E closed) | Yes (`…054`) | Yes | `CT-P8-P2-EFE-CLOSURE-…-054.md` |
| **G0 gate register** | Yes (register) | n/a | Yes (`…042`) | `CARBONTALLY_PHASE8_G0_GATE_RECONCILIATION_REGISTER_20260914.md` |
| **Phase 8-X (X1/X2/X4/X5/X7)** | Yes | Yes | Yes | **already banked** — `20d27c0`, `a71a46a`, `137765f`, `3a34ae3` |

**Deferred (NOT part of this boundary; preserved):** RLS steps 3–5 · G0-D · S8 · I1 · D16 (`D-19`) · S6 `new_version` · `F-X1-2` · `F-B3-7` · `F-4A1B-1` · B4-D12 · N3 · external ESRS/P1-evidence/P2-catalogue · M5/G-23/`PX-4` · Phase 9 · OHD.

---

## B. Exact product implementation boundary (untracked, never committed)

**Verified never in history** (`git log --all -- <path>` → **0** for every sampled module) and all `??` untracked. **17 product modules:**

```
backend/api/v3_disclosure.py
backend/data/disclosure.py             backend/data/disclosure_narrative.py
backend/data/disclosure_projection.py  backend/data/evidence_line_items.py
backend/data/report_artefacts.py
backend/domain/disclosure.py           backend/domain/disclosure_exposure.py
backend/domain/disclosure_narrative.py backend/domain/disclosure_projection.py
backend/domain/line_items.py           backend/domain/report_artefact.py
backend/services/disclosure_finalisation.py  backend/services/disclosure_narrative.py
backend/services/disclosure_projection.py    backend/services/extraction_fidelity.py
backend/services/report_artefact_storage.py
```

**Plus the wiring files that are TRACKED-BUT-MODIFIED (mixed — see §F):**
`backend/api/router.py`, `backend/api/dependencies.py`, `backend/api/v3_reports.py`,
`backend/api/v3_emissions.py`, `backend/api/v3_processing_workflow.py`, `backend/core/units.py`,
`backend/data/emission_factors.py`, `backend/data/emissions_logs.py`, `backend/data/manual_extraction.py`,
`backend/domain/calculation.py`, `backend/domain/automatic_processing.py`, `backend/engines/calculation.py`,
`backend/services/automatic_extraction.py`, `backend/services/automatic_processing.py`,
`backend/tests/integration/conftest.py`, `backend/tests/unit/api/fakes.py`,
`backend/tests/integration/test_reports.py`, `backend/tests/integration/test_report_versions.py`,
`backend/tests/unit/api/test_v3_report_lifecycle.py`, and the S6 frontend files
(`frontend/src/App.js`, `frontend/src/v3/api.js`, `frontend/src/v3/reports/ReportDetailPage.jsx`,
`frontend/src/v3/reports/reports.css`).

**2 tooling scripts:** `backend/tools/backfill_evidence_line_items.py` (B2 backfill — likely durable),
`backend/tools/b2_clone_schema_harness.py` (verification-time clone harness).

---

## C. Migration boundary (12 untracked — all required, none temporary)

| Migration | Workstream | Approved | Verified | Commit? |
|---|---|---|---|---|
| `20260914000000_p8_b1_disclosure_model_foundation.sql` | B1 | Yes | Yes | **Yes** |
| `20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` | B1 | Yes | Yes | **Yes** |
| `20260916000000_p8_b2_evidence_line_items.sql` | B2 | Yes | Yes | **Yes** |
| `20260916010000_p8_b2_provenance_line_links.sql` | B2 | Yes | Yes | **Yes** |
| `20260917000000_p8_b3_intensity_catalogue.sql` | B3 | Yes | Yes | **Yes** |
| `20260917010000_p8_b3_intensity_ratios.sql` | B3 | Yes | Yes | **Yes** |
| `20260918000000_p8_b4_narrative_overlay.sql` | B4 | Yes | Yes | **Yes** |
| `20260919000000_p8_b4_frozen_artefact.sql` | B4 | Yes | Yes | **Yes** |
| `20260920000000_p8_rls_anon_grant_containment.sql` | RLS-4A-1 | Yes | Yes | **Yes** |
| `20260921000000_p8_s2_is_current_single_valued.sql` | S2 | Yes | Yes | **Yes** |
| `20260922000000_p8_rls_4a2_authenticated_grant_hardening.sql` | RLS-4A-2 | Yes | Yes | **Yes** |
| `20260923000000_p8_rls_4a1b_anon_default_privilege_hardening.sql` | RLS-4A-1b | Yes | Yes | **Yes** |

All 12 are additive/idempotent, already applied to QA (**never** to production), and **not applied by this audit**.

---

## D. Test boundary (24 untracked test files) + tools

**Durable regression/unit/integration suites — COMMIT (24):**
`tests/integration/`: `test_disclosure_b1_runtime.py`, `test_disclosure_b3_projection_runtime.py`,
`test_disclosure_b3_v3_security.py`, `test_disclosure_b4_finalisation_runtime.py`,
`test_evidence_line_items_b2_runtime.py`, `test_s1s3_iv_invariants.py`, `test_s2_is_current_invariant.py`
`tests/unit/api/`: `test_s1s3_iv_supersession.py`, `test_v3_disclosure_api.py`,
`test_v3_disclosure_finalisation_api.py`, `test_v3_disclosure_narrative_api.py`
`tests/unit/data/`: `__init__.py`, `test_b2_migration.py`, `test_disclosure_migration.py`,
`test_disclosure_sql_typing.py`, `test_emission_factors_unit_selection.py`
`tests/unit/domain/`: `test_disclosure.py`, `test_disclosure_exposure.py`, `test_disclosure_narrative.py`,
`test_disclosure_projection.py`, `test_evidence_line_items.py`, `test_report_artefact.py`
`tests/unit/services/`: `test_efe_selection_sites.py`, `test_extraction_fidelity.py`
`tests/unit/`: `test_units_qualifier.py`

**Tools:** `backend/tools/backfill_evidence_line_items.py` → **commit** (durable data tool);
`backend/tools/b2_clone_schema_harness.py` → **PO decision** (verification-time harness).
**Excluded test artefact:** `backend/test_results.json` (generated).

---

## E. Documentation/evidence boundary

**Class A+B — durable evidence, RECOMMENDED FOR COMMIT (≈42 reports + 27 architecture docs):**
* `docs/cline/reports/`: all `CT-P8-B1-*`, `CT-P8-B1B2-ENV-APPLICATION-*`, `CT-P8-B2-*`, `CT-P8-B3-*`, `CT-P8-B4-*`, `CT-P8-S1S3-*`, `CT-P8-S2-CLOSURE-*`, `CT-P8-S6-*`, `CT-P8-RLS-4A-1-*`, `CT-P8-RLS-4A-2-*`, `CT-P8-FINAL-PROGRAMME-REPORT-*`, `CT-P8-MASTER-SEQUENTIAL-EXECUTION-*`, `CT-P8-G0-GATE-RECONCILIATION-*`, `CT-P8-P1-CLOSURE-*`, `CT-P8-P2-EFE-CLOSURE-*`
* `docs/architecture/` Phase 8/8-X set (27): disclosure model design + decision record, reporting architecture/lifecycle/catalogue ratifications, B1–B4 contracts, P1/P2 packages, G0 register, RLS remediation plan + hold register, 8-X discovery/readiness — the ratified decision record behind the banked code.

**Class C — temporary investigation (commit optional / PO decision):** `CT-P8-CURRENT-STATE-RECOVERY-023`, `CT-P8-REST-PLAN-027`, `CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC`, `CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC`, `CT-P8-P8X-PHASE9-PO-RECONCILIATION-040`, `CT-P8-P1-AUTHORISATION-PREPARATION-037`, `CT-P8-REPORTING-*` sets.

**Class D/E — generated or superseded (exclude):** `CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260913-031.md` (superseded by `…-058`), `backend/test_results.json`, root `test_results*.json`, `v1.9.txt`, `output/` captures.

**Class F — unrelated (exclude):** OHD reports (4, parked), Insight/Phase-9 docs, GA4/admin docs.


---

## F. Mixed-file analysis

| File group | Mixed with | Whole-file safe? | Required approach |
|---|---|---|---|
| 17 untracked Phase 8 modules + 24 untracked tests | nothing | **Yes** | `git add` per file (blob = worktree bytes) |
| 12 untracked migrations, 2 tools, Phase 8 reports/docs | nothing | **Yes** | `git add` |
| `backend/api/router.py` | **Phase 8 router registration** + X7 (committed) + other work | **No** | **blob-level**: HEAD + only the Phase 8 registration hunk |
| `backend/api/dependencies.py`, `v3_reports.py`, `v3_emissions.py`, `v3_processing_workflow.py` | Phase 8 endpoints/repositories + earlier-phase work | **No** | **blob-level** (per-hunk attribution required) |
| `backend/core/units.py`, `domain/calculation.py`, `engines/calculation.py`, `data/emission_factors.py`, `data/emissions_logs.py`, `data/manual_extraction.py`, `domain/automatic_processing.py`, `services/automatic_extraction.py`, `services/automatic_processing.py` | Phase 8 (units/EF-E selection, `source_line_item_id` provenance) + earlier work | **No** | **blob-level** (per-hunk attribution required) |
| `tests/integration/conftest.py`, `tests/unit/api/fakes.py`, `tests/integration/test_reports.py`, `test_report_versions.py`, `tests/unit/api/test_v3_report_lifecycle.py` | Phase 8 test additions + **B2 test-double drift (`F-X1-2`)** + earlier work | **No** | **blob-level**; must **not** absorb `F-X1-2` into Phase 8 |
| `frontend/src/App.js`, `frontend/src/v3/api.js`, `frontend/src/v3/reports/ReportDetailPage.jsx`, `reports.css` | **S6 frontend** (Phase 8, PO-closed) over X5-committed content | **No** | **blob-level** (S6 hunks only) |

**Consequence:** the **untracked** Phase 8 content is whole-file safe; the **tracked-modified** wiring is **not** — it needs the same blob-level technique already proven for X4/X5/X7/X1+X2, applied to **≈24 files**, several of which must be split across more than one banking commit (Phase 8 vs S6 vs B2).

---

## G. QA / assurance / agent / screenshot classification

| Directory | Purpose | Referenced by production code | Historically tracked | Verdict |
|---|---|---|---|---|
| `qa_harness/` | Independent QA harness (`qa_harness/scripts/run_all.py`) — an **intended** project artefact (`AGENTS.md` §52) | No | **Yes — 135 files already tracked**, 3 history commits; 201 untracked | **Partially repository material.** The untracked remainder includes a local **`.venv/`** (playwright, pygments…) that **must never be committed**. Harness code/tests scope: **PO decision** |
| `saas-assurance/` | Assurance / security-profile material | No | No (0 tracked, 0 history) | **PO decision** — new and unreferenced; likely belongs outside the product repo |
| `agent_swarm/` + `agent_swarm_v2_artifacts/` | AI review artefacts (generated) | No | No | **Exclude** — generated |
| `screenshots/` | Evidence captures | No | No | **Exclude / PO decision** — generated evidence, not source |
| Secrets | — | — | — | Scan matched **only `qa_harness/.venv/**` vendored files** (false positives); **no application secrets, tokens or credentials found**. Nothing was printed or modified |

---

## H. Phase 7 commit assessment

`4368157 feat(phase7): auditor/assurance auditability, taxonomy, evidence package` — **15 files, +2068/−24**, coherently Phase 7: backend (`api/dependencies.py`, `api/v3_exports.py`, `api/v3_reporting.py`, `data/audit.py`, `data/reporting.py`, `domain/audit.py`), tests (`test_p7_auditability.py`, `test_audit_p7.py`, `fakes.py`), frontend (`admin/AdminPage.jsx`, `admin/AuditTab.jsx`, `v3/api.js`, `ops/AuditConsoleTab.jsx`), migration `…_p7_audit_immutability_and_indexes.sql`, and the P7 implementation report.

* **Complete approved Phase 7 implementation?** Consistent with the Phase 7 record (`3c81586` records the commit; `bffe7e4` closes Phase 7) → **yes, as far as the records show**.
* **Reachable from `origin/main`?** **No** — local-only (one of the 19 unpushed commits).
* **Safe to preserve as-is?** **Yes** — self-contained; no unrelated work identified; **must not be amended**.


---

## I. Explicit exclusions (must NOT be committed by any Phase 8 banking)

**Deferred/held work:** RLS steps 3–5 · G0-D/production · S8 · I1 · D16 · S6 `new_version` · `F-X1-2` · `F-B3-7` · `F-4A1B-1` · B4-D12 · N3 · P1 customer-visible enablement · P2 EF-A/EF-D catalogue · M5/G-23/`PX-4` · Phase 9 · **OHD**.

**Generated / temporary / environment:** `qa_harness/.venv/**` (and any other `.venv`) · `backend/test_results.json` · root `test_results*.json` · `v1.9.txt` · `output/**` · `screenshots/**` · `agent_swarm/**` · `agent_swarm_v2_artifacts/**` · `.claude/**` · `.clinerules/**` · `.openhands/**` · `.windsurf/**` · `supabase/snippets/**`.

**Unrelated workstreams:** `.agents/skills/**` (69 mods) · `admin/**` (69 mods, non-GA4) · `tools/**` + `demodatagen/**` (42 mods) · `openhands/*` branches · `saas-assurance/**` pending PO decision.

**Superseded evidence:** `CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260913-031.md` (superseded by `…-058`).

---

## J. Proposed banking sequence (for PO authorisation — NOT executed)

1. **Commit 1 — Phase 8 B1 + B2:** the B1/B2 untracked modules, their tests, `backend/tools/backfill_evidence_line_items.py`, the 4 `p8_b1_*/p8_b2_*` migrations, the B1/B2 reports/contracts — **plus the B1/B2 hunks of the mixed API/data/domain files via blob-level staging**.
2. **Commit 2 — Phase 8 B3 + B4:** B3/B4 modules + tests + 4 migrations + B3/B4 evidence + narrative-overlay docs.
3. **Commit 3 — Phase 8 S-series:** `is_current` migration + S1S3/S2 tests + S1S3/S2/S6 closure evidence + **S6 frontend hunks via blob-level staging**.
4. **Commit 4 — Phase 8 RLS-4A hardening:** 3 RLS migrations + `…059`/`…060` reports + RLS plan/hold-register docs.
5. **Commit 5 — Phase 8 programme evidence:** final programme report, master sequential execution, G0 register, P1/P2 closure, readiness/discovery docs, and (optionally) the architecture decision set.
6. **Separate PO decisions:** (a) the `qa_harness` untracked remainder + a `.gitignore` entry for `.venv`; (b) `saas-assurance/`; (c) confirmation that `screenshots/` and `agent_swarm*/` stay excluded; (d) `b2_clone_schema_harness.py`; (e) that Phase 7 + the already-committed Phase 8 docs remain local-only until the push decision (previous audit recommendation stands).

---

## K. Final recommendation

### `PHASE 8 BOUNDARY UNCLEAR — PO REVIEW REQUIRED`

**What is already clear and ready (no decision needed):** the **43 untracked Phase 8 backend files** (17 product modules + 24 durable tests + 2 tooling scripts) and the **12 untracked Phase 8 migrations** are unambiguously the already-approved, independently verified, PO-closed Phase 8 implementation; each is whole-file safe to stage, none exists in history, and none is temporary. A large body of durable evidence (B1–B4/S-series/RLS closure + IV reports and 27 architecture decision records) is likewise ready.

**Why the boundary is nonetheless UNCLEAR — three genuine PO decisions:**

1. **≈24 tracked-modified wiring files are mixed** (Phase 8 hunks + earlier-phase work + B2 test-double drift `F-X1-2` + S6 frontend). Their Phase 8 portions require **blob-level per-hunk attribution** before staging; the boundary for those files cannot be certified from filenames or file-level status alone, and one of them must not absorb `F-X1-2`.
2. **Development-artefact scope is undecided:** `qa_harness` is *partly tracked already* (135 files) with an untracked remainder that includes a **local `.venv` that must never be committed**; `saas-assurance/` (217 files) is new and unreferenced; `screenshots/` (96) and `agent_swarm*/` (136) are generated. Whether any of this belongs in the product repository is a PO decision, not an implementation detail.
3. **Banking is not yet decidable in isolation:** the previous audit's **push decision is still open**, and Phase 8 banking plus the already-local Phase 7/Phase 8 documentation commits form one coherent publishing question. Banking Phase 8 now is safe *for the repository*, but the grouping/ordering should be confirmed so the eventual push is coherent.

**Nothing was staged, committed, pushed, reset, cleaned or modified.**
*Audit performed read-only by `CT-P8-GIT-BOUNDARY-01`; the only file created is this report. HEAD remains `20d27c0`, `origin/main` remains `9e13236`, staged area empty.*

