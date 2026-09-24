# CT-PO-P12-STEP1-IMPLEMENTATION-REPORT-20260924

**Reference:** `CT-PO-P12-STEP1-IMPLEMENTATION-REPORT-20260924`
**Date:** 2026-09-24
**Governing workplan:** `CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924` — **STEP 1 — Foundation & Forensics**
**Repository:** `/home/shomonrobie/ct_93d5cdd` @ `3c38cbc59c95c04ea434ae128f86c94fd4b69190`, branch `p8-release-reconciled`
**Scope:** Step 1 only. Step 2/3/4 **NOT** entered.
**Production deployment:** **NOT AUTHORIZED**

---

## 1. Executive Summary

Step 1 executed four workstreams — documentation reconciliation, independent
workflow verification, the EV-01 evidence-line forensic study, and freezing the
investor-demo scope — **entirely read-only**. No application, backend, frontend,
database, migration, RLS, seed data, test or evidence record was modified.

**The headline: CarbonTally's implemented capability is real, but almost none of it
is demonstrable from the current environments' data.**

What Step 1 established, with converging code and data evidence:

1. The known symptom (zero `evidence_line_items`) is **explained**. It is
   **contract-compliant behaviour**, not a defect. Evidence lines derive
   *exclusively* from `extracted_data.line_items[]`; every Demo Lab document was a
   PDF processed under the default P1 **`shadow`** extraction-shape mode, so the
   multi-line classifier's finding (`multi_line_suspect`, 2 candidate lines) was
   recorded but the shaped output deliberately withheld. Persisted payloads are
   **all flat**, so both the forward hook and the Class-1 backfill insert zero rows.
   No CSV/XLSX document was ever seeded, so the only unconditional `line_items[]`
   producers were never exercised.
2. The **canonical demo environment does not yet exist**. The Demo Lab is a
   pre-Insight provision (**0** Insight tables); **no** non-disposable local database
   has them; and the flagship `postgres` dataset has **no `evidence_line_items`
   table at all**.
3. The **only fully real end-to-end chain today** is one calculation:
   `12181.4 kWh × 0.2027 = 2469.169780 kg CO₂e` (DEFRA-DESNZ, `direct_multiply`,
   `v1.0`) with a snapshot, an emissions log and document-level provenance.
4. **Honest failure is genuinely demonstrable**: 13 blocked documents carry real,
   specific, human-readable reasons across four distinct failure classes.
5. The documentation record contains **at least 15 confirmed divergences** (9
   re-verified from the P12 preflight, 6 newly discovered), **none** resolved by
   editing either side.
6. The verifier **fixed nothing** and **did not exercise any workflow live**,
   because the release backend is not running and the available integration harness
   is destructive by construction. Every untested plane is reported `UNVERIFIED`.

**Status: `STEP 1 COMPLETE`.** No investor-demo readiness is claimed.

---

## 2. Repository Ground Truth (`FACT`)

| Item | Value |
| --- | --- |
| Repository | `/home/shomonrobie/ct_93d5cdd` (as expected) |
| Branch | `p8-release-reconciled` (as expected) |
| HEAD | `3c38cbc59c95c04ea434ae128f86c94fd4b69190` |
| HEAD subject | `docs(p12): product capability / investor-demo forensic study (planning artifact only)` |
| Upstream (`@{upstream}`) | `93d5cddd56bb683a5bb97ccf3419c191ddc617f5` |
| `github/p8-release-reconciled` | `3c38cbc…` — **equals HEAD** |
| Divergence | **ahead 106 / behind 0** of `@{upstream}` |
| Remotes | `github` = GitHub (aligned); `origin` = local path `/tmp/ct_step2` (stale at `93d5cddd`) |
| Working tree | 1 modified tracked file (`.gitignore`); 14 untracked paths |
| Untracked PO artifacts | workplan, handoff, Insight architecture refs, Question Library, INS-01 reconciliation, PO Insight matrix, `.costrict/`, `costrict-*.txt`, stray `8` and `=` (all left untouched) |
| Local DB instance | `127.0.0.1:54426` (PostgreSQL 17.6, container `supabase_db_carbon_ledger`) |
| Listening services | `54430` (Demo Lab gateway, `/auth/v1/health` → 200); `54426` (stack DB). **`8070` (release backend) DOWN** |
| Databases present | `carbontally_demo_local` (136 tables), `postgres` (116), `carbontally_qa_phase8` (133), `carbontally_test` (117) + 56 disposable `ct_*` clones |

**Difference from the handoff:** the inspected tree is **106 commits beyond** the
`93d5cddd` baseline named in the handoff. Those commits are substantive (the whole
`tools/demo_lab/` harness, the six Insight migrations, P2/P3 remediation and
verification records; 113 files / 27,437 insertions). The `github` remote matches
HEAD; only the local-path `origin` is stale. Recorded as divergence **D-14**.

---

## 3. Documents Inspected

**Governing / primary**

- `docs/architecture/CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924.md` (workplan; untracked)
- `docs/ChatGPT/carbontally_handoff.md` (handoff; untracked)

**Status / reconciliation sources**

- `CT-PO-P12-INVESTOR-DEMO-READINESS-PREFLIGHT-20260923.md`
- `CT-PO-PRODUCT-CAPABILITY-INVESTOR-DEMO-STUDY-20260924.md`
- `CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md`
- `CT-PO-INSIGHT-CAPABILITY-COVERAGE-MATRIX-IMPLEMENTATION-20260922.md`
- `CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md` (untracked)
- `CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md` (untracked)
- `CarbonTally_Insight_Architecture_Reference_2026-09-22.md` / `…-v2.md` (untracked)
- `CarbonTally_Insight_Question_Library_2026-09-22.md` (untracked)
- `CARBONTALLY_PHASE8X_X2_ALERTING_CONTRACT_20260914.md`
- `CARBONTALLY_PHASE8X_X7_API_RUNTIME_METRICS_CONTRACT_20260915.md`
- `CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md` (referenced for the §11/§12/§17 rules)
- P2 closure, P3 implementation / verification / re-verification records (`CT-P8-INSIGHT-P2-*`, `CT-P8-INSIGHT-P3-*`)
- T3 records: `CARBONTALLY_DEMO_T3_IMPLEMENTATION_20260920.md`, `…T3_REMEDIATION…`, `…T3_REM_001_IMPLEMENTATION…`
- `tools/demo_lab/README.md`, `tools/demo_lab/t3_manifest.json`
- Repository-level: `AGENTS.md`, `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`

**Source code inspected** (representative, not exhaustive): `backend/api/v3_pe.py`,
`v3_messaging.py`, `v3_reports.py`, `v3_reporting.py`, `v3_evidence.py`,
`v3_operations.py`, `v3_emissions.py`, `v3_documents.py`, `router.py`,
`consultant_auth.py`, `dependencies.py`; `backend/services/automatic_processing.py`,
`automatic_extraction.py`, `extraction_fidelity.py`, `insight_tools.py`; `backend/domain/evidence.py`,
`line_items.py`, `insight_interaction.py`; `backend/data/manual_extraction.py`,
`evidence_line_items.py`, `messaging.py`; `backend/tools/backfill_evidence_line_items.py`;
`supabase/migrations/20260916000000_p8_b2_evidence_line_items.sql` (and the B1/Insight migrations);
`tools/demo_lab/*`; `backend/tests/integration/conftest.py` and the relevant test suites.

---

## 4. Documentation Reconciliation

**Result: PARTIAL** (complete for the frozen Step-1 scope; two items are PO decisions
and one is a missing verification record).

- 15 capability rows reconciled against code + data.
- 9 preflight divergences re-verified; **11 new/consolidated divergences**
  registered as D-01…D-15 (full register in the Documentation Reconciliation report §5).
- Two documentation claims **verified as accurate** (the 15 `AnswerStatus` values and
  the generator pin `8ade2bf778d518d59924905849ab114ab2d0820a`).
- Nothing was reconciled by changing code or documentation.

**Headline divergences:**

| ID | Summary |
| --- | --- |
| D-01 | Evidence-line root cause identified (was `UNKNOWN`) — payload-shape gate + P1 `shadow`, not a missing hook |
| D-02 / D-04 | Demo Lab (and every non-disposable DB) lacks the Insight tables |
| D-03 | The flagship `postgres` dataset has **no `evidence_line_items` table** |
| D-05 | Insight matrix says "seven tools"; the registry holds **10** |
| D-07 | **No** non-`DRAFT` report version exists in any candidate environment |
| D-09 | `v3_messaging.py` docstring contradicts its own PE-operational implementation |
| D-10 | X2/X7 contracts say "BLOCKED" while implementation, wiring and tests exist |
| D-11 | `AGENTS.md` §54's 1,185-identity dataset does not exist; the real manifest has 13 actors |
| D-13 | The Demo Lab snapshot's `source_page = 3` is a pre-correction page *count* |
| D-14 | Release-identity ambiguity (local branch 106 ahead of the referenced baseline) |
| D-15 | Two stale unit-test expectations (pre-existing) |

---

## 5. Workflow Verification

**Result: PASS WITH OBSERVATIONS** — at the boundary the Step-1 authorization
permits. Full detail in the Independent Workflow Verification report.

| Plane | Code-verified | Demonstrable from current data | Exercised live |
| --- | --- | --- | --- |
| Calculation → snapshot → emissions | **YES** | **YES (1 record)** | NO |
| Document-level provenance | **YES** | **YES** | NO |
| Honest failure (4 classes) | **YES** | **YES** | NO |
| PE workspace / assignment / reassignment / release | **YES** | **NO (0 rows)** | NO |
| Messaging (organisation plane) | **YES** | **NO (0 rows)** | NO |
| Messaging (PE-operational plane) | **YES** | **NO (0 rows here)** | NO |
| Customer ↔ PE messaging | **does not exist by design** | n/a | n/a |
| Consultant/client relationship | **YES** | PARTIAL (topology only) | NO |
| Reporting lifecycle | **YES** | **NO** (all `DRAFT`) | NO |
| Master-data CRUD | **YES** | **NO (0 rows)** | NO |
| Insight / P2 / P3 | **YES** | **NO — schema absent** | NO |
| Source Evidence Viewer | **YES** | **NO (0 evidence lines)** | NO |

**No workflow produced an unexpected result**; none was exercised. The limitation is
environmental (backend down) and procedural (read-only boundary), **not** evidence
of a defect.

---

## 6. Security / Tenant Verification

**Result: PARTIAL.**

- **Code-verified controls:** organisation isolation (`ensure_org_access`,
  `require_org_member`); consultant↔client ACTIVE-grant gate
  (`ensure_consultant_org_access`); PE entity scoping (`work_item_effective_entity`,
  `is_entity_member`) with `_resolve_entity_actor` forcing a PE caller to its **own**
  entity; internal staff permissions (`ensure_staff_permission`, e.g.
  `can_manage_staff`); evidence-line re-authorization on every read with the line id
  treated as a locator (not a grant) and signed URLs issued only at FULL DM-6 depth;
  Insight `authorize_insight_scope` + per-object organisation re-check.
- **Observed (historical, not re-run):** the Demo Lab harness's last recorded run
  (`verify_20260920T152922Z.json`, 2026-09-20) reported **13/13** actor contexts,
  **30/30** authorization probes and **18/18** isolation rules with **0 failures**
  against `carbontally_demo_local`.
- **Not verified in this session:** no DENY/ALLOW case was executed; no unexpected
  ALLOW was observed (none could be tested).
- **Required for Step 2/4:** the frozen DENY set S-1…S-13, including the `ALLOW`
  positive control S-4, re-run against the frozen environment.
- **Not fixed:** nothing.

---

## 7. Demo Lab Harness Assessment

**Result: PARTIAL — present and previously usable; usability against current HEAD
NOT PROVEN.**

| Finding | Detail |
| --- | --- |
| Harness complete in the release | `lab.py`, `stack.py`, `provision.py`, `storage.py`, `seed_factors.py`, `t3_scenarios.py`, `t3_manifest.json`, `t3_extract_probe.py`, `verify.py`, `run_demo_lab.sh`, `reset_demo_lab.sh`, `README.md` |
| State material present | `$HOME/ct_local_env/demo_lab` with `backend.env` / `credentials.local.json` (mode 600), `corpus/t3-uk-curated-v1`, 14 `verify_*.json`, T2-C factor evidence |
| Lab infrastructure | gateway + PostgREST + storage containers present; **release backend (8070) not running** |
| Factor dataset | **loaded** — `emission_factors = 7,049` (DEFRA-2025 7,029 + SEAI-2025 20) |
| Last harness result | 2026-09-20 21:29Z — all contexts/probes/isolation rules passed |
| Cannot currently run | `verify.py` (needs the backend); `sync-corpus` (needs the `/tmp/extgen` pinned checkout, absent) |
| Safety design | `reset_demo_lab.sh` is lab-scoped; `t3_scenarios.py` has a hard `assert_lab_database()` guard limited to `carbontally_demo_local` |
| Independent verification of the harness | **missing** — the only prior verification (OHD-079) returned FAIL and the post-remediation record does not exist (D-12) |
| Destructive integration harness | `TRUNCATE … RESTART IDENTITY CASCADE`, refused for protected markers (F-046-1) — **not run in Step 1** |

---

## 8. EV-01 Evidence-Line Investigation

**Result: COMPLETE — root cause proven; remediation identified but NOT authorized.**

**Observed.** `evidence_line_items = 0` while `manual_extraction_items = 14` and
`calculation_snapshots = 1`. All 12 populated items carry a **flat** payload
(`activity, date, gross_amount, invoice_number, net_amount, quantity, supplier, unit`)
with `jsonb_typeof(extracted_data->'line_items') = NULL` for every row. The processed
document's queue metadata records `p1_coverage.mode = "shadow"`,
`multi_line_suspect = true`, `candidate_lines = 2`.

**Root cause.** `domain/line_items.py::derive_line_candidates` derives lines
*exclusively* from `extracted_data.line_items[]` and is contractually forbidden from
fabricating a line for a flat document. `line_items[]` is emitted unconditionally
only by the CSV/XLSX producers and conditionally by the PDF path (requiring effective
P1 mode `enabled`, which defaults to `shadow` and is downgraded to `shadow` unless
`CARBONTALLY_P1_ORGANIZATION_ALLOWLIST` is set). Every Demo Lab document was a PDF
processed in `shadow` mode; no tabular document was ever seeded. Therefore the
forward hook derived **0 candidates** and the Class-1 backfill had **0 eligible
items**.

**Excluded causes:** offline-only materialisation; missing online materialisation;
missing linkage; Demo Lab schema mismatch. **Confirmed secondary:** the flagship
`postgres` dataset has no `evidence_line_items` table at all.

**Minimum safe remediation (RECOMMENDED, not authorized):** seed ≥ 1 genuinely
tabular (CSV/XLSX) document through the real pipeline — no code change, no
configuration change — or, as a fallback, enable the P1 controlled rollout for the
demo organisation. **Rejected:** synthesising lines from flat payloads; direct SQL
inserts; running the backfill.

---

## 9. Frozen Four-Story Demo Scope

**Result: COMPLETE (proposed).**

| Story | Anchor | Demonstrable today |
| --- | --- | --- |
| **A — Normal calculation** | The real `uk-gas` document → `2469.169780 kg CO₂e` | **Mostly** (1 record) |
| **B — Operational workflow** | Work item → PE → assignment/reassignment → review/approval, bounded as **internal Operations ↔ PE** | **NO** — needs Step-2 seeding |
| **C — Explainability** | number → snapshot → factor → source document (**real**); evidence → Insight (**needs Step 2**), with mandatory disclosure | **Document-level only** |
| **D — Honest failure** | Ambiguous mapping (primary) + completeness gate (second), with real persisted reasons | **YES** |

Full frozen wording, per-story records and the mandatory disclosure sentences are in
the Frozen Investor Demo Scope report.

---

## 10. Required Step-2 Topology (summary)

The Demo Lab, aligned to the current release migration set **including all six
`2026100*` Insight migrations**, with a persisted schema-revision record; 2 direct
orgs, 1 consultant firm, 2 client orgs, **2** processing entities, PE manager + PE
staff, internal operator/reviewer/QC/staff-admin; ~3 batches, ~12–15 work items,
**≥ 2** matched calculations, **≥ 2** blocked documents, **≥ 1 tabular document**,
**≥ 2** evidence line items, **≥ 4** assignments incl. reassignment and partial
release, 2 report versions in different lifecycle states, conversations on both
messaging planes, 2 Insight interactions + 1 honest no-data case, and ≥ 1 facility /
asset / supplier. Counts are **planning targets**, not fixed counts.

---

## 11. Remaining Blockers

| # | Blocker | Type | Blocks |
| --- | --- | --- | --- |
| B1 | Demo Lab schema is a pre-Insight provision (0 `%insight%` tables) | environment | all Insight, P2, P3 demonstration |
| B2 | Near-empty demonstrable population | environment/data | Stories A (partly), B, C, D (Insight no-data) |
| B3 | Evidence-line destination has zero data (EV-01: flat payloads + P1 `shadow`) | configuration + corpus | Story C last mile |
| B4 | Flagship `postgres` dataset has no `evidence_line_items` table | schema divergence | rules out that dataset as canonical |
| B5 | Harness re-verification record missing; harness usability against HEAD unproven | verification governance | Step 2/4 confidence |
| B6 | Pinned generator checkout absent (`/tmp/extgen`) | tooling | corpus re-sync |
| B7 | No non-`DRAFT` report version exists anywhere | data | reporting beat |
| B8 | Release-identity ambiguity (D-14) | reference hygiene | freezing the Step-2 release |
| B9 | P3 has no UI renderer | capability | P3 in a visual narrative |
| B10 | Documentation conflicts requiring PO decisions (D-09, D-10, D-11, D-12) | governance | claim language |

---

## 12. Pre-existing Issues (not caused by Step 1)

| Issue | Evidence | Status |
| --- | --- | --- |
| `F-T1-001` — `/api/v3/reporting/audit-activity` HTTP 500 for an authorised owner (`uuid = text` operator error) | recorded in earlier `verify_*.json` runs and the P12 preflight §18.2 B11 | **UNKNOWN** — the latest recorded harness run lists no known product defects, but the API could not be called this session and no fix commit was inspected |
| 4 stale unit-test expectations | `test_review_sla_surfaces.py` (asserts on the pre-refactor module router); `test_d17_provider_ownership_migration_revision.py:264` (`== 71`, actual 81) | **PRE-EXISTING**, unrelated to the demo workflows |
| Untracked PO/ChatGPT artifacts (workplan, handoff, Insight references, matrices) | `git status` | **PRE-EXISTING** (preflight `D-27`/X-5) |
| X2/X7 contract records say "BLOCKED" while implementation exists | contract lines vs code | **PRE-EXISTING** divergence |
| Stray zero-byte files `8` and `=` in the repository root | `ls -la` | **PRE-EXISTING** housekeeping (not cleaned — not authorized) |

---

## 13. Newly Discovered Issues

| Issue | Evidence | Class |
| --- | --- | --- |
| **Flagship `postgres` dataset has no `evidence_line_items` table** | `DATABASE-OBSERVED` | schema divergence |
| **No candidate environment has the Insight tables** (only disposable `ct_*` clones + `carbontally_test`) | 60-database scan | environment |
| **No non-`DRAFT` report version exists anywhere** | `report_versions` in both candidate DBs | data |
| **`v3_messaging.py` docstring contradicts its own PE messaging implementation** | file §1–13 vs `/entity-conversations` + `_resolve_entity_actor` | documentation |
| **The Demo Lab snapshot's `source_page` is a pre-correction page count** | `git blame` `999e4fb` (2026-09-22) vs snapshot `calculated_at` 2026-09-20 | data staleness (correctly classified by current code) |
| **Release-identity ambiguity** — 106 commits ahead of the referenced baseline while GitHub is aligned | `git rev-list`, `git rev-parse github/…` | reference hygiene |
| **EV-01 root cause** (payload-shape gate + P1 `shadow` + no tabular corpus) | code + data trace | forensic (resolves a prior `UNKNOWN`) |

**No new product defect** was discovered. Every newly discovered issue is an
environment, data, documentation or reference-hygiene issue.

---

## 14. Authorization Boundaries

**Remained inside the Step-1 boundary.** Performed: read-only inspection; forensic
analysis; documentation reconciliation; independent verification; creation of
reports/decision records; unit-test execution.

**Deliberately NOT performed (and still unauthorized):**

- Demo Lab reset, reseed, re-provision or any lab mutation;
- destructive database operations (the integration harness was **not** run);
- production database access or mutation;
- evidence backfill or evidence-line implementation;
- any application/frontend/backend/database/migration/RLS/seed/test modification;
- enabling `CARBONTALLY_P1_EXTRACTION_SHAPE=enabled`;
- committing the untracked PO artifacts;
- resolving the documentation/business conflicts (D-09…D-12);
- any Step 2/3/4 work.

**AUTHORIZATION REQUIRED** is recorded explicitly for every remediation proposed in
the EV-01, verification and frozen-scope reports, and for the ten Step-2 decisions in
the Decision Record §21.

---

## 15. Tests Executed

| Suite | Command | Result |
| --- | --- | --- |
| Unit | `backend/.venv/bin/python -m pytest tests/unit -q --tb=no -p no:cacheprovider --junit-xml=…` | **3220 tests — 4 failed, 8 skipped, 0 errors, 266.35 s** (~3208 passed) |
| Integration | *(not run — destructive by construction; F-046-1 + Step-1 read-only boundary)* | **NOT RUN** |
| Demo Lab harness `verify.py` | *(not run — release backend down)* | **NOT RUN** |

**Failure separation:** newly discovered **none**; pre-existing **4**; environment
**0**; test-harness fixture **4** (the same four); genuine product defects **0**
identified in this run. **No test was modified.**

---

## 16. Evidence / Artifacts Produced

**Step-1 documents (all new, in `docs/architecture/`):**

| # | Artifact | Path |
| --- | --- | --- |
| 1 | Documentation Reconciliation Report | `docs/architecture/CT-PO-P12-STEP1-DOCUMENTATION-RECONCILIATION-20260924.md` |
| 2 | Independent Workflow Verification Report | `docs/architecture/CT-PO-P12-STEP1-WORKFLOW-INDEPENDENT-VERIFICATION-20260924.md` |
| 3 | EV-01 Evidence-Line Forensic/Design Report | `docs/architecture/CT-PO-P12-STEP1-EV01-EVIDENCE-LINE-FORENSIC-DESIGN-20260924.md` |
| 4 | Frozen Investor Demo Scope | `docs/architecture/CT-PO-P12-STEP1-FROZEN-INVESTOR-DEMO-SCOPE-20260924.md` |
| 5 | Step-1 Decision / Exit Record | `docs/architecture/CT-PO-P12-STEP1-DECISION-20260924.md` |
| 6 | Step-1 Implementation / Forensics Report (this file) | `docs/architecture/CT-PO-P12-STEP1-IMPLEMENTATION-REPORT-20260924.md` |

**Raw evidence** (read-only captures, retained for audit; not committed):

- Git ground truth for both checkouts; working-tree inventory.
- Per-database count matrix for `carbontally_demo_local`, `postgres`,
  `carbontally_qa_phase8`, `carbontally_test` (organizations, users, members, PEs,
  assignments, batches, extraction items, evidence line items, snapshots, emissions,
  factors, report versions, queue states, conversations, messages, master data).
- Extraction-payload shape analysis (`jsonb_object_keys`, `jsonb_typeof`).
- The single snapshot's full column set and the emissions log row.
- The 13 persisted `manual_review_reason` values.
- The per-database Insight-table scan across 60 databases.
- The `t3_manifest.json` scenario/b3-expectation extraction.
- The last Demo Lab `verify_*.json` summary and `t3_ground_truth_latest.json`.
- Unit-test JUnit XML summary.
- Route-decorator inventories for the PE, messaging, reporting, evidence, operations,
  documents, consultant, supplier and vehicle routers.

**No secret, credential, JWT or signed URL was captured, printed or committed.** The
Demo Lab credential file was never read.

### 16.1 Git record for this Step-1 delivery

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| Step-1 artifacts commit | `7962162eafa0046d7b7fffa9d3d296035555c553` — `docs: complete P12 investor demo step 1 forensics` |
| Parent (pre-Step-1 HEAD) | `3c38cbc59c95c04ea434ae128f86c94fd4b69190` |
| Files in the commit | exactly **6** (the six artifacts above) — `6 files changed, 2201 insertions(+)` |
| Push target | `github` → `https://github.com/shomonrobie/CarbonTally.git` (`3c38cbc..7962162  p8-release-reconciled -> p8-release-reconciled`) |
| Post-push alignment | `github/p8-release-reconciled == HEAD` — **ALIGNED** |
| Unrelated work absorbed | **none** — the pre-existing `.gitignore` modification and all 13 pre-existing untracked PO/ChatGPT artifacts remain uncommitted and untouched |
| Production / Demo Lab mutation | **none** |
| `git diff --check` | **CLEAN** |


---

## 17. Step-1 Exit Assessment

**Exit criteria (workplan §1, Step-1 exit criteria) — assessed:**

| Criterion | Met? | Basis |
| --- | --- | --- |
| The canonical demo environment direction is confirmed | **YES** | Demo Lab `carbontally_demo_local` re-provisioned to the current release schema (recommended); the flagship dataset is explicitly ruled out (D-03) |
| The four demonstration stories are frozen | **YES** | Frozen Scope report |
| Required data entities and workflow states are known | **YES** | Frozen Scope §5/§7 + Decision Record Q16 |
| Evidence requirements are understood | **YES** | EV-01 report §B/§D/§E |
| Genuine code/data blockers are distinguished from demo-environment problems | **YES** | Decision Record Q8/Q9; no product defect found |
| No unresolved critical uncertainty would make the Step-2 reset unsafe | **YES, conditional** | Conditional on PO resolving the **release commit** (D-2-1) and the **reset data-loss scope** (D-2-3) before mutation |

**No unresolved critical uncertainty remains about *what* Step 2 must do.** The two
open items are *decisions*, not unknowns.

---

## 18. Exact Recommended Next PO Decision

**DECISION REQUIRED — authorise (or refuse) STEP 2 — Canonical Demo Environment.**

The PO should confirm, in one decision:

1. the **release commit** to freeze (`3c38cbc` recommended);
2. the **canonical environment** (Demo Lab re-provisioned — recommended);
3. acceptance of the **Demo Lab reset data-loss scope**;
4. the **EV-01 unlock** (seed ≥ 1 genuinely tabular document — recommended; or enable
   the P1 controlled rollout; or accept Story C as document-level only);
5. that **evidence-line materialisation must occur only via the real pipeline** (no
   direct inserts, no backfill, no derivation change);
6. re-provisioning of the **pinned generator checkout**;
7. the **frozen demo counts**;
8. the **disposable-clone integration verification** pass (F-046-1 compliant);
9. disposition of the **documentation conflicts** (D-09, D-10, D-11, D-12);
10. durability of the **untracked PO artifacts** (D-27).

**Until at least items 1–5 are authorized, Step 2 must not begin.**

```text
STEP 1 COMPLETE
INVESTOR DEMO READY: NOT CLAIMED
STEP 2: NOT STARTED — AWAITING PO AUTHORIZATION
```
