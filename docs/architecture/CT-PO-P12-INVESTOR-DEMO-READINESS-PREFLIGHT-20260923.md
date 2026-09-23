# CT-PO-P12-INVESTOR-DEMO-READINESS-PREFLIGHT-20260923

**Task:** Read-only P12 Investor-Demo Readiness Preflight — establish the exact current state and a bounded implementation backlog for the future **P12 Investor Demo Readiness Gate**.
**Kind:** FORENSICS / PLANNING ONLY. **This document authorizes nothing.** No implementation, no fix, no test/migration/frontend/demo-data change, no deployment, no PO closure.
**Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **Authoritative remote:** `github`

**Evidence labels used below (never interchangeable):**
`OBSERVED` (executed and quoted) · `DATABASE-OBSERVED` (read-only query against the Demo Lab database) · `CODE-TRACED` (read from source with file reference) · `TEST-VERIFIED` (an automated suite asserts it and was run) · `DOCUMENTED CLAIM` (asserted by a repository document, not re-executed here) · `INFERENCE` (reasoned from verified facts) · `UNKNOWN` (not determinable read-only).

---

## 1. Executive summary

1. **All ten named source documents exist and were read.** No file in §3 is missing. `tools/seed_investor_demo/DEMO_IDENTITIES.md` — referenced by `AGENTS.md` §54 — **does not exist** (see §15).
2. **The repository's actual demo infrastructure is the "Demo Lab"** (`tools/demo_lab/`, workstreams DEMO-T1 → T2-C → T3), not the ~1,185-identity "investor demo dataset" described in `AGENTS.md` §54. The real identity manifest is `tools/demo_lab/manifest.json` (13 actors). `OBSERVED`.
3. **The synthetic-document generator pin matches exactly:** `8ade2bf778d518d59924905849ab114ab2d082a0` appears in `tools/demo_lab/t3_scenarios.py:50` and `tools/demo_lab/t3_manifest.json` (`_generator.commit`). The generator stays offline; only generated documents are copied. No discrepancy. `CODE-TRACED`.
4. **The Demo Lab database is stale relative to the release and cannot run Insight at all.** `carbontally_demo_local` holds **136** public tables and **zero** tables matching `%insight%` — the I1/I2/I4/analytics/P2/P3 migrations (six files, `20261001000000`…`20261007000000`) have never been applied to it. `DATABASE-OBSERVED`.
5. **The demo population is thin and mostly blocked:** 4 organisations · 14 documents · processing queue **13 `manual_review` / 1 `customer_review`** · **1** calculation snapshot · **1** emissions log · **0** evidence line items · 7,049 factors · 2 report versions · 113 audit rows. `DATABASE-OBSERVED`.
6. **The curated 11-scenario corpus contract records only 2 scenarios as `EXPECTED_MATCHED`** (uk-gas, uk-water); 6 are `EXPECTED_AMBIGUOUS`, 1 `EXPECTED_NO_MATCH`, 1 `UNSUPPORTED_PDF`, 1 has no factor expectation. A general "upload → calculation" success path across the corpus **cannot be demonstrated truthfully today**. `CODE-TRACED` + `DOCUMENTED CLAIM`.
7. **The T3 harness's only independent verification verdict is FAIL** (`docs/verification/OHD_TASK_079_DEMO_T3_INDEPENDENT_VERIFICATION_20260920.md` → B-1 corpus unparseable, B-2 reset non-functional). The remediation (REM-001) fixed B-1/B-2/O-A/O-B but its own report ends **"IMPLEMENTATION BLOCKED — PO REVIEW REQUIRED"**, with downstream sections **NOT EXECUTED**; the manifest was subsequently reconciled to *record actual product behaviour*. **No independent verification of the remediated harness exists.** `DOCUMENTED CLAIM` + `CODE-TRACED`.
8. **P2 is PO-closed; P3 is not.** P3 is implemented and passed independent verification with non-blocking observations, and its P3-IV-01 defect was remediated and independently re-verified (`2be9033`, "PASS WITH NON-BLOCKING OBSERVATIONS"), but **P3 remains un-closed**. P12 must not assume P3 closure. `DOCUMENTED CLAIM`.
9. **The core customer journey is demonstrable today** (browser-verified across DR-001…DR-007: login, workspace, documents, exception workspace with machine-readable blocking reasons, one real calculation `2469.169780 kg CO₂e`, reports with artefacts, exports, consultant client scoping, billing *surfaces*), **but the evidence-destination link has no live data**: the Source Evidence Viewer route requires an evidence line item and the lab DB holds **0** such rows. `DOCUMENTED CLAIM` + `DATABASE-OBSERVED`.
10. **There is no P12-specific permanent record anywhere in the repository.** P12 exists only as: the master preflight package row (§11) and demo gate proposal (§17.1), the P1 matrix §11 investor-demo capability map and §10.1 sequencing, and P3/P2 references. `CODE-TRACED`.
11. **P12 can be scoped immediately, but it cannot be *executed* truthfully until the Demo Lab is re-provisioned to the current release schema** (P12-01) and a demonstrable calculation/evidence population is restored (P12-02), both lab-local and needing no production authority. See §17–§18.

**Headline:** the demo capability is real but currently *under-provisioned*; the main risks are **stale lab schema**, **near-empty calculation/evidence population**, **a corpus harness whose remediation is unverified**, and **documentation that still describes a demo dataset that is not in this checkout**.

---

## 2. Git / repository baseline

| Item | Value | Evidence |
| --- | --- | --- |
| Repository | `/home/shomonrobie/ct_93d5cdd` | `OBSERVED` |
| Branch | `p8-release-reconciled` (unchanged throughout this preflight) | `OBSERVED` |
| HEAD at preflight start | `b39caadc8dbfb3065cf23b8ee4ad6930c0f6b693` | `OBSERVED` |
| HEAD during/at end | `2be9033` — `docs(p8): independent re-verification of the P3-IV-01 remediation (PASS WITH NON-BLOCKING OBSERVATIONS)` | `OBSERVED` |
| Why HEAD moved | committed **and pushed by the concurrent independent P3-IV-01 re-verification**, not by this pass; `HEAD...github` was `0 0` before and after | `OBSERVED` |
| Remotes | `github` = `https://github.com/shomonrobie/CarbonTally.git` (authoritative); `origin` = `/tmp/ct_step2` (not contacted) | `OBSERVED` |
| Working tree (start and end) | ` M .gitignore` (pre-existing PO change) + untracked pre-existing artefacts: `.costrict/`, `8`, `=`, `costrict-p3-ov-01-independent-re-verification.txt`, and 8 untracked `docs/` PO/ChatGPT reference documents | `OBSERVED` |
| Actions taken by this pass | read-only inspection (including read-only `SELECT`s against the **Demo Lab** database only); one new report file; one documentation-only commit; push to `github/p8-release-reconciled`. No edit to any existing file, no branch switch, no reset/stash/clean, no history rewrite | Appendix A |

**Roadmap position used as given:** P1 (closed) → P2 (closed) → P3 (**not closed**; independent re-verification of the P3-IV-01 remediation completed with "PASS WITH NON-BLOCKING OBSERVATIONS" at `2be9033`, PO closure outstanding) → **P12 (this preflight)**. This preflight neither closes P3 nor depends on P3 closure for its *analysis*; §9 keeps "implemented", "independently verified" and "PO-closed" strictly separate.

---

## 3. Source documents inspected

All ten named documents exist; none was missing. Sizes are line counts; "used for" states what this preflight took from each.

| Document | Lines | Exists | Used for |
| --- | --- | --- | --- |
| `docs/architecture/CarbonTally_PO_Insight_Capability_Coverage_Matrix_2026-09-22.md` | 1245 | ✔ | 19-family coverage table with statuses; conflict register (X-5); §10 package sequence; **§11 investor-demo capability map** |
| `docs/architecture/CT-PO-INSIGHT-CAPABILITY-COVERAGE-MATRIX-IMPLEMENTATION-20260922.md` | 216 | ✔ | P1 scope, verified constants, carry-forward list (X2/X7, `AGENTS.md` §54 path, pre-existing failures) |
| `docs/architecture/CarbonTally_PO_P2_Temporal_Comparison_Closure_2026-09-23.md` | 183 | ✔ | P2 **CLOSED — IMPLEMENTED & INDEPENDENTLY VERIFIED**; closed scope; accepted limitation (no live-DB execution); explicit non-closure of P3 |
| `docs/architecture/CT-P8-INSIGHT-DATA-QUALITY-AUDIT-REPRODUCIBILITY-IMPLEMENTATION-20260923.md` | 291 | ✔ | P3 scope, answer-state table, "not-checked never reads as checked" contract |
| `docs/architecture/CT-P8-INSIGHT-P3-INDEPENDENT-VERIFICATION-20260923.md` | 740 | ✔ | P3 independent verification; P3-IV-01…P3-IV-05 findings |
| `docs/architecture/CT-P8-INSIGHT-P3-IV01-REMEDIATION-20260923.md` | 391 | ✔ | the authorized remediation; `no_checkable_records`; partial-coverage boundary |
| `docs/architecture/CT-P8-INSIGHT-P3-IV01-REVERIFICATION-20260923.md` | 549 | ✔ | **NEW since the last session**, committed at `2be9033`: verdict **PASS WITH NON-BLOCKING OBSERVATIONS**; §8 partial-coverage observation; P3 not PO-closed |
| `docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md` | 741 | ✔ | family model, answer-quality model, **E0–E4 evidence depth (§11)**, **NL architecture (§12)**, security/rate-limit/viewer sections |
| `docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md` | 971 | ✔ | 19 question classes (§2) and **Modes A–F** (§§682–760): authoritative numeric, calculation explanation, evidence navigation, comparative, conceptual, audit challenge |
| `docs/architecture/CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md` | 572 | ✔ | package definition **P12** (§11), demo-critical/truthful/limitation inventory (§9.1–§9.5), **demo gate proposal (§17.1)**, D-01…D-29 register |
| `docs/architecture/CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md` | 534 | ✔ | capability-status reconciliation (§6), viewer confirmation (§7), accepted carry-forwards (§8.1–§8.8), pre-existing failure boundary (§9) |

Additional records inspected (not listed in the authorization, but load-bearing for the demo assessment): `docs/architecture/CARBONTALLY_DEMO_T3_IMPLEMENTATION_20260920.md` (260), `…T3_REM_001_IMPLEMENTATION_20260920.md` (157), `…T3_REMEDIATION_20260920.md` (112), `docs/verification/OHD_TASK_079_DEMO_T3_INDEPENDENT_VERIFICATION_20260920.md` (562), `docs/demo-investor/DR-001…DR-007` (7 records, 146–289 lines each), `docs/architecture/CARBONTALLY_PHASE8_DEMO_T2C_FACTOR_DATASET_LOADING_PO_CLOSURE_DECISION_20260920.md`, `tools/demo_lab/README.md`, `tools/demo_lab/manifest.json`, `tools/demo_lab/t3_manifest.json`.

**P12-specific permanent record: none.** `grep -rl 'P12'` over all `*.md` returns 12 documents, none of which is a P12 plan, gate, closure or verification record; the only *definitions* of P12 are the master preflight §11/§17.1 and the P1 matrix §10.1/§11. `OBSERVED`.

---

## 4. Current demo infrastructure

### 4.1 What exists (code-traced inventory of `tools/demo_lab/` and related tooling)

| Asset | Lines | Purpose | Evidence |
| --- | --- | --- | --- |
| `tools/demo_lab/lab.py` | 335 | lab constants (`LAB_DB="carbontally_demo_local"`, gateway `54430`, backend `8070`, `STATE_DIR=$HOME/ct_local_env/demo_lab`), identity resolution, deterministic UUIDs, psql/HTTP helpers, container list | `CODE-TRACED` |
| `tools/demo_lab/manifest.json` | 148 | **identity manifest**: 4 organisations (org A, org B, client A, client B), 1 processing entity, 1 consultant firm, **13 actors** (platform admin, operator, pe_manager, 4 org-A roles, 2 org-B roles, consultant owner + member, 2 client owners) each with `expect` (actor_type, destination, role). **No credentials** in the file | `CODE-TRACED` |
| `tools/demo_lab/provision.py` | 405 | idempotent provisioning of identities/relationships; mirrors the 13 lab auth user ids into the lab DB `auth.users` for FK integrity | `DOCUMENTED CLAIM` |
| `tools/demo_lab/stack.py` | 306 | creates `carbontally_demo_local` and builds the release schema from `supabase/migrations/*.sql` (authoritative source), plus the storage substrate before migrations | `CODE-TRACED` |
| `tools/demo_lab/storage.py` | 362 | lab-owned storage substrate: `storage` schema cloned structurally, D32 policies, two private buckets, lab storage container + `/storage/v1` route | `DOCUMENTED CLAIM` |
| `tools/demo_lab/seed_factors.py` | 708 | DEMO-T2-C factor loading (DEFRA 2025 + SEAI 2025, serial, idempotent, SHA-256 verified, `--dry-run`, `--reset`, hard DB-name guard) | `DOCUMENTED CLAIM` |
| `tools/demo_lab/t3_scenarios.py` | 748 | corpus sync from the pinned external generator, real-API seeding, ground-truth verification, lab-scoped reset (B-2 fixed via the Storage API), hard `assert_lab_database()` guard | `CODE-TRACED` |
| `tools/demo_lab/t3_manifest.json` | 452 | **scenario contract**: 11 scenarios with actor/target/corpus glob/expected activity-unit/factor family/`b3_expectation`/findings; `_rem001_reconciliation` block | `CODE-TRACED` |
| `tools/demo_lab/t3_extract_probe.py` | 111 | candidate probe: "does the release extractor really parse this?" | `CODE-TRACED` |
| `tools/demo_lab/verify.py` | 309 | server-side verification: actor contexts + **20+ authorization/isolation probes** against real endpoints; records F-T1-001 as a known product defect rather than a false pass | `CODE-TRACED` |
| `tools/demo_lab/run_demo_lab.sh` | 89 | stack → provision → env file → (`--backend`) release backend → verify → (`--factors`) factor load | `CODE-TRACED` |
| `tools/demo_lab/reset_demo_lab.sh` | 62 | **reset**: lab auth users (by lab e-mail domain) → lab containers → `DROP DATABASE carbontally_demo_local WITH (FORCE)`; `--purge-state` also deletes credentials/evidence. Never touches stack DBs, the investor dataset, production or Render | `CODE-TRACED` |
| `tools/demo_lab/README.md` | 161 | topology, commands, actor table, honest limitations (incl. F-T1-001) | `DOCUMENTED CLAIM` |
| `tools/generate_synthetic_documents.py` | — | CarbonTally's own pre-existing document generator helper (unrelated to the pinned external generator) | `CODE-TRACED` |
| `tools/provision_tesseract_local.sh` | — | local OCR provisioning | `CODE-TRACED` |
| `tools/carbon_data_factory/` | — | separate TS/JSON dataset tooling (factors/config/schemas/verifiers); not the demo lab | `CODE-TRACED` |
| `tools/backup_recovery_drill.py` | — | backup/restore drill tool (L8-A artefact) | `CODE-TRACED` |
| `qa_harness/` (`scripts/{preflight,run_api,run_db,run_browser,run_agents,run_all,…}.py`, `browser/playwright`, `playwright.config.ts`) | — | independent QA harness; README marks it **BUILD-ONLY** (must not be run against the application until a checkpoint is authorized) | `DOCUMENTED CLAIM` |
| `docs/demo-investor/DR-001…DR-007` | 146–289 each | seven investor-facing verification/triage records (customer journey, frontend runtime, CORS/browser, deep R-A browser, remaining workflows, report refresh, defect triage) | `DOCUMENTED CLAIM` |

**Provisioning, reset, verification, identities, synthetic documents, deterministic seed data, manifest, scenario execution, end-to-end checks, tenant isolation, cleanup, report generation and evidence verification all exist as tooling.** An **Insight verification** step does **not** exist anywhere in `tools/` (`grep -rn 'insight' tools/` → **0 hits**). `OBSERVED`.

### 4.2 Live state of the running Demo Lab (read-only)

| Check | Result | Evidence |
| --- | --- | --- |
| Containers | `carbontally_demo_lab_gateway`, `…_storage`, `…_postgrest` up (2–3 days); stack containers (`supabase_*_carbon_ledger`) up | `OBSERVED` |
| Listening ports | `54430` (gateway), `54426` (stack DB) listening; **`8070` (release backend) NOT listening** | `OBSERVED` |
| Lab state dir | `$HOME/ct_local_env/demo_lab` exists: `credentials.local.json` (mode 600), `backend.env`, `backend.log`, `corpus/t3-uk-curated-v1/` (49 files incl. `corpus_provenance.json`), `evidence/` (`t2c_*`, `t3_scenarios_latest.json`, `t3_ground_truth_latest.json` — 21 Sep 00:57) | `OBSERVED` |
| Lab DB tables | **136** in `public`; **0** match `%insight%`; `insight_rate_limit_buckets`, `insight_concurrency_leases`, `carbontally_insight_conversations/interactions/messages/tool_calls` **absent** | `DATABASE-OBSERVED` |
| Lab DB data | `organizations=4`, `organization_files=14`, `document_processing_queue=14` (13 `manual_review`, 1 `customer_review`), `calculation_snapshots=1`, `emissions_logs=1`, `evidence_line_items=0`, `emission_factors=7049`, `report_versions=2`, `audit_trail=113` | `DATABASE-OBSERVED` |
| The one calculation | snapshot `af640887…`: `Natural gas`, `12181.4`, unit `kWh (Net CV)`, `2469.169780` kg CO₂e, `Scope 1`, `factor_source=DEFRA-DESNZ`, `factor_set=DEFRA-2025`, `source_item_id` present; emissions log `eb88e764…` references the snapshot | `DATABASE-OBSERVED` |
| Report tables | no table named `reports`/`report_instances`; present: `report_versions`, `report_comments`, `report_generation_queue`, `report_version_artifacts`, `report_templates`, `disclosure_report_*` | `DATABASE-OBSERVED` |

**Consequence (`INFERENCE`, high confidence):** the lab DB was provisioned **before** the Insight migrations existed (lab stack built 19–20 Sep; the Insight migrations are the `20261001…20261007` files). Therefore **every Insight route** (`/api/v3/insight/*`) would fail against this lab, and **P2 and P3 cannot be demonstrated at all** until the lab is re-provisioned. Re-provisioning is documented and lab-local (`stack.py` builds the schema from `supabase/migrations/*`), but whether `stack.py` applies *missing* migrations to an **existing** lab DB (rather than only on creation) is **UNKNOWN** and must be established as part of P12-01 — it decides between "re-run the stack" and "reset + rebuild the lab".

### 4.3 External synthetic-document generator reference (pin check)

| Item | Value | Evidence |
| --- | --- | --- |
| Repository | `https://github.com/shomonrobie/carbon_tally_synthetic_documents_generator` | `CODE-TRACED` |
| **Pinned commit** | `8ade2bf778d518d59924905849ab114ab2d082a0` — **matches the required pin exactly** | `OBSERVED` (grep across the working tree) |
| Where the pin is recorded | `tools/demo_lab/t3_scenarios.py:50` (`GENERATOR_COMMIT`), `tools/demo_lab/t3_manifest.json` (`_generator.commit`), plus historical records (`CARBONTALLY_DEMO_T3_IMPLEMENTATION_20260920.md`, `…T3_REMEDIATION…`, `OHD_TASK_079…`) | `CODE-TRACED` |
| Runtime coupling | none: the generator is an offline read-only checkout whose **documents** only are copied into `<state>/corpus/t3-uk-curated-v1`; no import, no execution, no vendored source; explicitly verified by OHD-079 ("no production module executes it") | `DOCUMENTED CLAIM` |
| Generator state in this checkout | `/tmp/extgen` was the verification checkout; it is **not present now** (`--source` defaults to `/tmp/extgen`), so `sync-corpus` cannot be re-run until a checkout at the pinned commit exists | `OBSERVED` |
| Discrepancy | **none** — no difference between the referenced pin and the actual repository state | `OBSERVED` |

---

## 5. Current executable demo scenarios

Two distinct things are called "scenario" in this repository; they must not be conflated.

### 5.1 Corpus/pipeline scenarios — `tools/demo_lab/t3_manifest.json` (11 declared)

`CODE-TRACED` (manifest) + `DOCUMENTED CLAIM` (findings established by REM-001-CONT round 2 and recorded in the manifest).

| # | Scenario | Actor → target | Factor expectation (`b3_expectation`) | Recorded finding | Demo consequence |
| --- | --- | --- | --- | --- | --- |
| 1 | `uk-electricity` | org_a_owner → Org A | `EXPECTED_AMBIGUOUS` (confidence 0.0) | no viable candidate in the examined 2025 subset (40/40) | pipeline blocks honestly; **no calculation** |
| 2 | `uk-gas` | org_a_owner → Org A | **`EXPECTED_MATCHED`** — factor `b9d1ed06-…` Net-CV natural gas, confidence 1.0 | extraction verified (activity Natural gas, 12181.4 kWh) | **the one scenario that completes** (matches the single snapshot in the lab DB) |
| 3 | `uk-diesel` | org_a_owner → Org A | `EXPECTED_AMBIGUOUS` | no viable candidate | blocks honestly |
| 4 | `uk-waste` | org_a_owner → Org A | **`EXPECTED_NO_MATCH`** (16/16 examined) — generic "Waste + tonnes" can reach the wrong `Waste oils` family | — | blocks honestly |
| 5 | `uk-water` | org_a_owner → Org A | **`EXPECTED_MATCHED`** — factor `fb9d28bf-…` water supply, confidence 1.0 | — | may complete (not among the current lab snapshots) |
| 6 | `uk-spend` | org_a_owner → Org A | **`UNSUPPORTED_PDF`** (`select=false`) | no PDF spend path exists (PO decision R-1) | explicitly **not** demoable by design |
| 7 | `uk-ambiguity` (intentional) | org_a_owner → Org A | `EXPECTED_AMBIGUOUS` | re-pointed to the octopus pool (skip_index 1) after `shell_energy`/`scottish_power` proved unsuitable (R-2) | demonstrates the *ambiguity* honesty state |
| 8 | `uk-missing-evidence` (intentional) | org_b_owner → Org B | none (selection uses `expect_unparseable`) | selection implemented; end-to-end exercise outstanding in REM-001 | demonstrates extraction/missing-evidence honesty |
| 9 | `consultant-client-a` | consultant_owner → Client A | `EXPECTED_AMBIGUOUS`; corpus substitution `ORG_029_edf_energy_202510.pdf` authorized | consultant upload path verified (201) | consultant journey upload works; mapping ambiguous |
| 10 | `consultant-client-b` | consultant_owner → Client B | `EXPECTED_AMBIGUOUS` | — | as above |
| 11 | `direct-org-b-isolation` | org_b_owner → Org B | `EXPECTED_AMBIGUOUS` (44/44 examined) | isolation control scenario | tenancy control |

**Summary:** 2 `EXPECTED_MATCHED` · 6 `EXPECTED_AMBIGUOUS` · 1 `EXPECTED_NO_MATCH` · 1 `UNSUPPORTED_PDF` · 1 selection-only. Every expectation here describes **actual product behaviour** (verified via `POST /api/v2/factor-match` on the running lab); **no factor was forced and no threshold was weakened**. Docker note: the deliberately ambiguous/no-match outcomes are *honest failures*, not harness defects — but they mean the corpus cannot be presented as "11 successful calculations".

### 5.2 Investor-facing verification scenarios — `docs/demo-investor/DR-001…DR-007`

These are **verification records of real browser/server journeys**, not executable scenario scripts. All seven explicitly end with *"CarbonTally is not declared investor-ready"*. `DOCUMENTED CLAIM`.

| Record | Journey verified | Status |
| --- | --- | --- |
| DR-001 | frontend / customer-journey forensics (no browser evidence; states so) | `DOCUMENTED CLAIM` |
| DR-002 | frontend runtime + CRA startup; found a **Demo Lab gateway CORS gap** | `DOCUMENTED CLAIM` |
| DR-003 | with the CORS correction: **real browser login** with a lab identity, session, org context, dashboard counts, document list, exception reasons, the R-A calculation, reports, billing surfaces | `DOCUMENTED CLAIM` |
| DR-004 | deep browser verification of the R-A item: extracted fields, matched factor, arithmetic `12181.4 kWh (Net CV) × 0.2027 = 2469.169780 kg CO₂e`, snapshot id, evidence chain labelled COMPLETE, item awaiting customer review | `DOCUMENTED CLAIM` |
| DR-005 | exception workspace (machine-readable block reason), reports, report artefact download, exports (CSV contains the R-A row), review/approval wiring (never executed), consultant + client scoping, billing, Realtime gap | `DOCUMENTED CLAIM` |
| DR-006 | report regeneration produced a report with the real scope-1 total; `ghg_inventory` refresh unsupported (422) | `DOCUMENTED CLAIM` |
| DR-007 | 9 issues triaged → 3 genuine display defects **fixed and browser-verified**; 3 non-defects; 3 PO decisions outstanding | `DOCUMENTED CLAIM` |

### 5.3 Scenario-level verdicts

| Property | Finding | Evidence |
| --- | --- | --- |
| Scenario *contract* exists and is deterministic | yes (11 scenarios, fixed commit/seed/globs, per-document SHA-256 + `generation_seed`, stable file prefixes) | `CODE-TRACED` |
| Scenario *execution* is currently reproducible | **PARTIAL** — seeding is idempotent (second run skipped 11/11) and was OHD-observed; the post-remediation re-sync/re-seed/reset proof was never executed | `DOCUMENTED CLAIM` |
| A scripted investor demo flow exists | **NO** — no demo script artefact exists in `docs/demo-investor/` or elsewhere; the master preflight lists "a scripted, repeatable demo flow" as *should be polished* (§16.2/§17.1) | `OBSERVED` |
| Scenarios depending on **P3 closure** | **none** (no scenario invokes Insight at all) | `OBSERVED` |
| Scenarios depending on **unauthorized future capability** | `uk-spend` (PDF spend — recorded unsupported), plus anything requiring Scope 3 / market-based Scope 2 / Scope 1 decomposition / variance / supplier persistence | `DOCUMENTED CLAIM` |
| Evidence path produced by scenarios | `<state>/evidence/t3_scenarios_latest.json` and `t3_ground_truth_latest.json` (21 Sep 00:57) | `OBSERVED` |

---

## 6. Core workflow capability inventory

Classification vocabulary as required: `WORKING` · `PARTIAL` · `BROKEN` · `NOT IMPLEMENTED` · `NOT DEMO-READY` · `UNKNOWN`. "Demo-ready" means **truthfully demonstrable in the current lab, live, in front of an audience** — not merely that code exists.

| Capability | Classification | Evidence | Demo consequence |
| --- | --- | --- | --- |
| Authentication (email/password, persona roles) | **WORKING** | lab GoTrue + 13 identities; `verify.py` login/context probes; DR-003 browser login verified; TOTP MFA architected | all personas can be logged in — **requires the release backend to be started** (`run_demo_lab.sh --backend`; port 8070 is currently not listening) |
| Customer workspace (dashboard, documents, emissions, reports, issues, messaging, insight) | **WORKING** | `frontend/src/v3/customer/*`; routes in `frontend/src/App.js`; DR-003/DR-004 browser-verified | customer-facing shell is demonstrable |
| Document upload | **WORKING** | `POST /api/v3/uploads` (direct) and `POST /api/v3/consultants/clients/{id}/documents` (consultant) both returned 201 in T3; 14 `organization_files` rows exist | upload is demonstrable; the consultant-client path is also proven |
| Extraction | **PARTIAL** | real pipeline ran; `document_processing_queue` shows 13 `manual_review` / 1 `customer_review`; clean text-native UK PDFs only; OCR deferred (T3 §21) | extraction works but **most curated documents do not reach mapping**; scanned/OCR documents unsupported |
| Mapping | **PARTIAL** | only 2 of 11 factor families resolve deterministically (`uk-gas`, `uk-water`); 6 ambiguous; 1 `no_match`; spend unsupported | mapping must be presented with its honest block reasons, not as a general success |
| Validation | **PARTIAL** | `ValidationEngine` A1/A2/A5 reused by extraction/workspace and by P3; blocking reasons surface in the exception workspace (DR-005) | validation is demonstrable via the exception workspace |
| Calculation | **WORKING** | `engines/calculation.py`, immutable `calculation_snapshots`; **1** live snapshot (`2469.169780` kg CO₂e) | the deterministic calculation is demonstrable — but with a **single** record |
| Deterministic result (arithmetic visible) | **WORKING** | DR-004 read `12181.4 kWh (Net CV) × 0.2027 = 2469.169780 kg CO₂e` from the live UI with factor/methodology/algorithm version | strongest single demo asset today |
| Evidence | **NOT DEMO-READY** (as the Viewer route) | `evidence_line_items = 0`; `/evidence/line-items/{lineItemId}` + `SourceEvidenceViewer.jsx` exist; DR-004/DR-005 saw the *lineage/evidence-trail panels*, and DR-005 explicitly recorded "No evidence record exists for this item" | the promised evidence **destination** cannot be shown from live data; whether the pipeline *should* have created a line item for the calculated record is itself an open question (see P12-06) |
| Report generation | **WORKING** | `report_versions=2`; DR-006 regenerated a report whose UI/API/artefact all state `2469.169780 kg CO2e`, no `insufficient_data` | demonstrable; the **duplicate + stale** annual/`ghg_inventory` artefacts remain investor-visible (PO decision, DR-007) |
| Exports | **WORKING** | DR-005: org-scoped CSV/JSON GETs; CSV contains the R-A row with factor/snapshot/emissions ids | demonstrable (read-only) |
| Review / approval workflow | **PARTIAL** | wired with owner/admin gating, confirmation, mandatory rejection reason, server authority — **never executed** (DR-005 §17) | can be shown as a window, **cannot** be demonstrated as a completed approval |
| Billing / commercial surfaces | **PARTIAL** | plan/credit/order surfaces render provider-neutrally; **no PSP, no entitlements, no invoicing** (master preflight §8) | must be presented as configuration/surfaces only; **any payment or plan-fulfilment implication would be false** |
| Messaging | **PARTIAL** | messaging surfaces + Realtime code exist; the lab gateway has **no `/realtime/v1` route**, so live delivery/notification is blocked (DR-005 §18) | inbox rendering/send may be demonstrable; live push is not |
| Processing workspace (D19) / exception workspace | **WORKING** | `/processing/{itemId}` workspace; DR-005 browser-verified with exact machine reason and next step | demonstrable and investor-legible |
| PE workspace (`/pe`) and internal ops (`/ops`) | **UNKNOWN** (demo) | routes + `verify.py` PE/admin probes exist; no browser verification recorded | independent verification depth **not established** (DR-005 §20 item 6) |
| OCR / scanned documents | **NOT IMPLEMENTED** (demo path) | T3 §21: clean text-native only; OCR capacity is production-critical and excluded | must be stated as unsupported in a demo |
| Multi-tenant isolation (as a demonstrable control) | **WORKING** | `verify.py` 20+ ALLOW/DENY probes (org A↔B, client A↔B, consultant→unrelated org, viewer/member denials); DR-005 client scoping verified | demonstrable and one of the platform's strongest differentiators |
| Live RLS enforcement verification | **UNKNOWN** | `tests/unit/data/test_i2_insight_rls_live.py` needs a live DB (skipped in unit runs); F-046-1 forbids pointing the destructive harness at persistent DBs | may be shown only via a disposable clone; not part of a customer demo |

**Notable pre-existing defect affecting the demo:** **F-T1-001** — `GET /api/v3/reporting/audit-activity` returns **HTTP 500** (`asyncpg: operator does not exist: uuid = text`) for a correctly authorised owner. `verify.py` reports it as a known product defect rather than a pass. It must be either avoided or narrated (it is a genuine product defect, not a demo artefact). `CODE-TRACED` + `DOCUMENTED CLAIM`.

---

## 7. Insight capability inventory

### 7.1 What the Insight capability surface consists of

| Component | Verified state | Evidence |
| --- | --- | --- |
| I3 tool catalogue | **10 tools** currently registered: the four ratified (`report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup`) + INS-01's three (`insight_discovery`, `insight_aggregation`, `insight_aggregate_provenance`) + **P2** `insight_temporal_comparison` + **P3** `insight_data_quality`, `insight_calculation_reproducibility` | `CODE-TRACED`; pinned by `test_p8_insight_temporal_comparison.py` `assert len(TOOL_REGISTRY) == 10` (`TEST-VERIFIED`) |
| Status vocabulary | 6 ratified `ToolStatus` values; `reason` is a free-form machine-readable contract string (no registry) | `CODE-TRACED` |
| Answer states | 15 I4 `AnswerStatus` values incl. `no_data`, `zero`, `multiple_matches`, `rate_limited`, `provider_unavailable` | `CODE-TRACED` + `TEST-VERIFIED` |
| Bounded contract constants | 25 discovery / 50 groups / 100 provenance snapshots / 3,660-day period / tolerance ceilings / 4 tool calls per interaction / provider attempts 2 | `DOCUMENTED CLAIM` (matrix §3.3) |
| Rate limiting (technical) | PostgreSQL-backed buckets + concurrency leases; enforced on both execution routes; **CLOSED under INS-01** | `DOCUMENTED CLAIM` + `TEST-VERIFIED` (unit) |
| Source Evidence Viewer | single evidence destination; route `/evidence/line-items/{lineItemId}`; re-authorises on every read (DM-6) | `CODE-TRACED` |
| Frontend Insight workspace | `/insight` (customer only, `RoleRoute requireOrg`), `InsightPage.jsx`, `InsightInteraction.jsx`, `InsightAnswerState.jsx`, `InsightReferences.jsx`, **`InsightComparison.jsx` (P2 only)** | `CODE-TRACED` |
| Frontend Insight tests | 5 suites: `insight-answer-states.test.js`, `insight-api.test.js`, `insight-comparison.test.jsx`, `insight-page.test.jsx`, `insight-references.test.jsx` | `OBSERVED` |
| Backend Insight API | `/api/v3/insight/conversations…`, `/interactions…`, `/tools`, `/invoke`, `/intent` | `CODE-TRACED` |
| Insight DB tables | `carbontally_insight_conversations / interactions / messages / tool_calls`, `insight_rate_limit_buckets`, `insight_concurrency_leases` — **absent from the Demo Lab DB** | `DATABASE-OBSERVED` |

### 7.2 Per-capability classification and demo reachability

| Insight capability | Code status | Verification status | **Demo status (current lab)** | Evidence |
| --- | --- | --- | --- | --- |
| Identified calculation lookup (family 1) | EXISTS | INS-01 closed + independently verified | **NOT DEMO-READY** (no Insight schema in lab) | matrix §4.1; lab DB |
| Discovery (family 2) | EXISTS | INS-01 closed + verified | **NOT DEMO-READY** | matrix §4.2 |
| Aggregation (family 3) | EXISTS | INS-01 closed + verified | **NOT DEMO-READY**; data near-empty (1 snapshot) | matrix §4.3 |
| Aggregate provenance (family 4) | EXISTS | INS-01 closed + verified | **NOT DEMO-READY** | matrix §4.4 |
| Temporal comparison (family 11 / **P2**) | EXISTS | independent verification PASS + **PO CLOSED** | **NOT DEMO-READY** (no schema); UI component exists | P2 closure record |
| Data quality (family 14 / **P3**) | EXISTS (`insight_data_quality`) | independent verification **PASS WITH NON-BLOCKING OBSERVATIONS**; P3-IV-01 remediated + re-verified; **NOT PO-closed** | **NOT DEMO-READY** (no schema; **no UI renderer**) | P3 records + re-verification |
| Calculation reproducibility (**P3**) | EXISTS (`insight_calculation_reproducibility`) | as above | **NOT DEMO-READY** (no schema; no UI renderer) | P3 records |
| Source Evidence Viewer | EXISTS | INS-01 closed; PO-confirmed core capability | **NOT DEMO-READY** as a live viewer (0 evidence line items) | INS-01 §7; lab DB |
| Evidence navigation (report→version→calculation→source) | EXISTS | DR-004/DR-005 browser-verified lineage panels | **PARTIAL** — lineage panels demonstrable; the standalone Viewer route is not | DR-004/DR-005 |
| Tenant isolation / Insight authorization (I2) | EXISTS | unit/API suites + `verify.py` probes across the app | **NOT DEMO-READY** (Insight endpoints cannot run) | `test_v3_insight_i2_authorization.py` |
| Rate limiting (technical) | EXISTS | closed under INS-01 + unit-verified | **NOT DEMO-READY** (its tables are in an unapplied migration) | lab DB |
| Meaningful failure states (`no_data` / `unsupported` / `multiple_matches` / `rate_limited`) | EXISTS (I4 states) | `TEST-VERIFIED` at contract level | **NOT DEMO-READY** via Insight; *partially* demonstrable through the processing exception workspace (honest, machine-readable) | DR-005 |
| Scope analysis (family 5) | PARTIAL (scope grouping only; no comparison) | — | not demoable as a comparison | matrix §4.5 |
| Supplier (9) / Scope 3 (6) / Scope 2 market-based (7) / Scope 1 decomposition (8) / variance (12) / methodology (15) / knowledge (17) / reporting frameworks (18) / reduction (19) | **MISSING** as capabilities | — | **must return unsupported / no-data**, never a guess | matrix §4.6–§4.19 |

### 7.3 Cross-cutting Insight findings for P12

1. **The Insight layer is entirely absent from the demo harness** — no `tools/` reference, no Insight table in the lab DB, no Insight step in `verify.py`. `OBSERVED` + `DATABASE-OBSERVED`.
2. **P3 has no UI surface at all**: `grep -rn 'insight_data_quality\|insight_calculation_reproducibility' frontend/src` → **0 hits**; only `insight_temporal_comparison` is invoked from the UI (`InsightComparison.jsx:64`). A P3 question reaches the planner and executes server-side, but is rendered only as a generic tool-call row plus narration. `OBSERVED`.
3. **The tool-catalogue count is documented inconsistently** (the P1 matrix says 7 and "no eighth tool exists"; reality is 10) — see §15.
4. **P3 remains un-closed**, and its open items that touch P12 presentation are the **partial-coverage non-blocking observation** (a period with ≥1 checkable record plus uncheckable records still answers `all_checks_passed`, carried by `uncheckable_records`) and P3-IV-02…P3-IV-05. None blocks the demo; each must be *narrated accurately* if P3 is demonstrated.

---

## 8. P2 integration (temporal comparison)

P2 is **PO-closed** (`CarbonTally_PO_P2_Temporal_Comparison_Closure_2026-09-23.md`: "CLOSED — IMPLEMENTED & INDEPENDENTLY VERIFIED") with an accepted limitation: the independent verification **did not execute the comparison against a live PostgreSQL database**. `DOCUMENTED CLAIM`.

| P2 element required by the task | Implemented in code | Independently verified | PO-closed | Exercised by the **demo infrastructure** |
| --- | --- | --- | --- | --- |
| two explicit periods (`period_a_*`, `period_b_*`) | ✔ | ✔ | ✔ | **no** |
| absolute change (`B − A`) | ✔ | ✔ | ✔ | **no** |
| percentage change (`((B−A)/A)×100`, only when baseline ≠ 0) | ✔ | ✔ | ✔ | **no** |
| zero-baseline behaviour (`null` + `percentage_change_available=false` + `percentage_basis="zero_baseline"`) | ✔ | ✔ | ✔ | **no** |
| empty-period behaviour (`no_data` / `no_rows_in_periods`, never "0 vs 0") | ✔ | ✔ | ✔ | **no** |
| permitted grouping dimensions (`scope`, `activity`, `facility`, `asset` only; unsupported → rejected) | ✔ | ✔ | ✔ | **no** |
| provenance pathway (names `insight_aggregate_provenance`; traceable via the shared viewer) | ✔ | ✔ | ✔ | **no** |

**Evidence:** contract and tests are `TEST-VERIFIED` (`tests/unit/api/test_p8_insight_temporal_comparison.py` → 43 tests, catalogue pin `== 10`); UI wiring is `CODE-TRACED` (`InsightComparison.jsx` → `insight_temporal_comparison`); the **demo harness does not exercise it** and the lab DB lacks the schema (`OBSERVED` / `DATABASE-OBSERVED`).

**P12 implication:** P2 is the most *presentable* Insight capability (closed, bounded, dedicated UI detail view), but it needs (a) the lab schema re-provisioned and (b) at least two periods with real data — the lab currently holds **one** snapshot in a single period, so a truthful two-period comparison would today surface `no_data`/zero-baseline behaviour rather than an interesting delta.

---

## 9. P3 integration and the status boundary

The task requires three statuses to be kept strictly separate. They are:

| Status | P2 | P3 | Evidence |
| --- | --- | --- | --- |
| **Implemented in code** | YES | YES | `CODE-TRACED` (tool registry: `insight_temporal_comparison`, `insight_data_quality`, `insight_calculation_reproducibility`; 10-tool registry pinned by test) |
| **Independently verified** | YES (`PASS`; accepted limitation: no live-DB execution) | YES — `PASS WITH NON-BLOCKING OBSERVATIONS`; the earlier P3-IV-01 finding was remediated (`8554b78`) and **independently re-verified** (`2be9033`) | `DOCUMENTED CLAIM` (P2 closure record; P3 independent verification §17; P3-IV-01 re-verification §15) |
| **PO-closed** | **YES** | **NO** | `DOCUMENTED CLAIM` (P2 closure record §1; the P3 re-verification §15 states P3 is not PO-closed) |
| **Exercised by the demo infrastructure** | NO | NO | `OBSERVED` (`grep 'insight' tools/` = 0 hits) + `DATABASE-OBSERVED` (no Insight tables in the lab) |

### 9.1 P3 element-by-element check against the demo

| P3 element | Implemented | Independently verified | PO-closed | Demo status |
| --- | --- | --- | --- | --- |
| Data-quality analysis (`insight_data_quality`) | ✔ | ✔ (PASS + observations) | ✘ | **NOT DEMO-READY** — no lab schema, **no UI renderer** |
| No-checkable-record handling (`records_checked == 0` ⇒ `no_checkable_records`, never `all_checks_passed`) | ✔ (remediated) | ✔ (re-verified, 3/3 deterministic runs) | ✘ | not demonstrable in the UI; provable only at the tool/API layer |
| Reproducibility (`insight_calculation_reproducibility`: 10 retained conditions, recomputation + hash match) | ✔ | ✔ | ✘ | **NOT DEMO-READY** — no lab schema, no UI renderer |
| Provenance / evidence chain of a P3 answer | ✔ (result names its snapshot/lineage; viewer remains the only destination) | ✔ | ✘ | cannot be shown live (0 evidence line items) |
| Truthful limitation states (`snapshot_not_checkable`, `reproducibility_limitation`) | ✔ | ✔ | ✘ | not rendered in the UI today |

### 9.2 P3 open items that a demo narrator must respect

* **Partial coverage (non-blocking observation):** a period with at least one checkable record **and** at least one uncheckable record still answers `reason="all_checks_passed"` with `uncheckable_records` as the truthful carrier. The independent re-verifier classified this as **NON-BLOCKING** and explicitly invited a PO ruling on the stricter reading. A demo must not present `all_checks_passed` as "every record was checked". `DOCUMENTED CLAIM`.
* **P3-IV-02** (foreign-id existence oracle, pre-existing), **P3-IV-03** (stale migration filename in the historical report), **P3-IV-04** ("13-file / 299" set not enumerated), **P3-IV-05** (pre-existing D17 pin `81 == 71`) — all still open governance items. `DOCUMENTED CLAIM`.
* **P3 does not add a new UI surface**; presenting P3 requires either a presenter-side API demonstration or an accepted "tool + narration" presentation.

**Explicit non-inference:** nothing above may be read as P3 closure, and P12 must not be scheduled on the assumption that P3 closes. Conversely, **no P12 item identified in this preflight strictly requires P3 closure** — only accurate narration (§17 classifies this per item).

---

## 10. Evidence-to-answer chain

The chain the product promises:

```text
Question
  ↓
Deterministic CarbonTally computation
  ↓
Structured answer
  ↓
Provenance
  ↓
Source Evidence Viewer
  ↓
Underlying source / evidence
```

| Link | Current state | Evidence |
| --- | --- | --- |
| Question → bounded intent | **WORKING** — deterministic planner maps a question to one closed tool schema; it never generates SQL, never authorises, never selects a tenant, never calculates (`Architecture Reference v2 §12`) | `CODE-TRACED` + `TEST-VERIFIED` (planner tests) |
| Deterministic computation | **WORKING** — server-authoritative engine, immutable snapshots, `Decimal` maths; the lab's one record proves the arithmetic | `DATABASE-OBSERVED` + DR-004 |
| Structured answer | **WORKING** — bounded, deterministic `ToolResult` + 15 answer states; narration is bounded to tool output | `CODE-TRACED` |
| Provenance | **PARTIAL** — aggregates name `insight_aggregate_provenance`; snapshots carry `source_item_id`; the lab's snapshot has one | `CODE-TRACED` + `DATABASE-OBSERVED` |
| **Source Evidence Viewer** | **BROKEN AS A LIVE DEMO** — the route `/evidence/line-items/{lineItemId}` requires an evidence line item and **`evidence_line_items = 0`** in the lab DB; the Viewer therefore has nothing to resolve | `DATABASE-OBSERVED` + `CODE-TRACED` |
| Underlying source/evidence | **PARTIAL** — documents + storage objects + extraction items exist (14 documents, `manual_extraction_items` populated for processed items); no evidence line items | `DATABASE-OBSERVED` |

**Which current scenario can demonstrate the full chain?** **None, today.** The closest is the **R-A natural-gas item** (DR-004/DR-005): question/"identified calculation" → deterministic result `2469.169780 kg CO₂e` → structured detail with factor, methodology, algorithm version and snapshot id → **lineage/evidence-trail panels inside the report and workspace** → source document. The missing link is specifically the **standalone Source Evidence Viewer over an evidence line item** (`evidence_line_items = 0`), i.e. the "last mile" of the E3 promise.

**Gap (not a defect judgement):** whether the pipeline *should* have produced an `evidence_line_items` row for the calculated item, or whether the Viewer is populated only in other workflows, is **UNKNOWN** read-only and must be established before P12 claims an end-to-end evidence demonstration (P12-06). This must **not** be fixed by inventing a new viewer or by inserting rows outside the workflow.

---

## 11. Security and tenant isolation

Distinguishing the required categories: **actually verified (executed)** · **covered by tests** · **only inspected** · **not tested**.

| Control | Category | Detail | Evidence |
| --- | --- | --- | --- |
| Customer tenant isolation (org A ↔ org B) | **covered by tests + demo-executable** | `verify.py` probes assert 200 for own org and 403/404 for the other, both directions; `test_scope_aware_authorization.py` | `CODE-TRACED` |
| Consultant ↔ unrelated organisation | **covered by tests + demo-executable** | `verify.py` consultant→Org B probe expected 403/404 | `CODE-TRACED` |
| Client A ↔ Client B | **actually verified (browser)** | DR-005: client identity restricted to its own two documents, no cross-tenant leakage | `DOCUMENTED CLAIM` |
| Viewer → write / owner-admin surfaces | **covered by tests + demo-executable** | `verify.py` viewer/member denial probes on `audit-activity` (403) | `CODE-TRACED` |
| Foreign identifiers (IDOR) | **covered by tests** | `test_legacy_upload_idor.py`; object re-check on every Insight read (I2 + DM-6) | `CODE-TRACED` |
| Authentication | **actually verified (browser)** | DR-003 browser login with a real lab identity, session and org context | `DOCUMENTED CLAIM` |
| Authorization planes (customer / consultant / client / PE / internal ops) | **covered by tests; PE + ops only inspected for the demo** | `verify.py` includes PE and admin-control-plane probes; **no browser verification recorded**; PE/internal demo depth is a PO question (DR-005 §20) | `CODE-TRACED` + `DOCUMENTED CLAIM` |
| Rate limiting (technical) | **covered by tests only** | bucket + concurrency lease enforced on both execution routes **cannot be demonstrated in the current lab** (tables absent — migration never applied) | `DOCUMENTED CLAIM` + `DATABASE-OBSERVED` |
| Evidence access / viewer re-authorization | **inspected; not exercised live** | `SourceEvidenceViewer` re-authorizes per read; **no evidence line items exist**, so no live ALLOW/DENY case | `CODE-TRACED` + `DATABASE-OBSERVED` |
| Signed URL / raw document exposure | **covered by tests + observed product control** | `test_storage_security.py`; DR-005 observed the workspace source pane showing "View only — download disabled for this role" | `CODE-TRACED` + `DOCUMENTED CLAIM` |
| Insight tool authorization (I2 boundary, org re-check, references-not-grants) | **covered by tests** | `test_v3_insight_i2_authorization.py`; I3/I4 wiring suites; structurally verified in the P3 verification | `TEST-VERIFIED` |
| Live RLS enforcement | **not tested in this environment** | live RLS specs require a database; `F-046-1` forbids pointing the destructive integration harness at persistent environments (the Demo Lab is **not** a disposable clone) | `CODE-TRACED` |
| Pre-existing security-adjacent defects | **inspected** | **F-T1-001** audit-activity 500 for an authorized owner (availability defect, not a disclosure); the pre-existing factor-metadata cross-tenant exposure (`GET /api/v3/emissions/factors/{id}`) remains tracked (INS-01 closure §8.6) — **not reopened, not worsened** | `DOCUMENTED CLAIM` |

**No security finding was fixed or probed destructively during this preflight.** All database access was read-only `SELECT`; nothing was written, deleted or reconfigured. `OBSERVED`.

**P12 relevance:** tenant isolation is already the most demonstrable security story (ALLOW **and** DENY pairs exist and run server-side). What is missing for P12 is a **scripted, repeatable presentation** of those probes and at least one *visibly denied* cross-tenant attempt (P12-09) — not new security work.

---

## 12. Failure honesty / no-fabrication assessment

| Risk | Current state | Assessment |
| --- | --- | --- |
| Fabricated emissions | **Not present.** The engine is server-authoritative; DR-004 read the real arithmetic from the UI; the lab snapshot carries factor + batch + hash provenance | `DOCUMENTED CLAIM` + `DATABASE-OBSERVED` — **no fabrication observed** |
| Fabricated evidence | **Not present, but the inverse risk exists:** the Viewer has no data, so nothing can be fabricated there; the risk is *implying* the viewer was exercised | `DATABASE-OBSERVED` |
| Hard-coded outputs presented as live calculations | **Not observed.** T3 explicitly records "no calculation result is hard-coded"; reports are generated from persisted rows | `DOCUMENTED CLAIM` |
| Unsupported Scope 3 classification | No Scope 3 dimension exists | risk only if a presenter invents it |
| Unsupported market-based Scope 2 | only a **disclosure vocabulary** (`SCOPE2_METHODS`, `scope2_method_hint`) exists — vocabulary ≠ methodology; the matrix forbids inferring policy from code | `DOCUMENTED CLAIM` |
| Unsupported Scope 1 decomposition | no classification exists | as above |
| Unsupported supplier analytics | `emissions_logs.supplier_id` is never written; the supplier dimension returns `no_data` by design | `DOCUMENTED CLAIM` |
| Unsupported variance / attribution | no attribution engine; **P2 provides comparison only, never causation** | `DOCUMENTED CLAIM` |
| Unsupported reduction recommendations | no target/scenario model exists | `DOCUMENTED CLAIM` |
| Certification / audit-assurance claims | **explicitly prohibited** — the report UI itself states *"The evidence trail shows how this result was produced. It is not an independent audit or certification."*; E4 does not exist; "do not claim E4 merely because E3 exists" | `CODE-TRACED` + `DOCUMENTED CLAIM` |
| Production-readiness claims | production deployment remains **NOT AUTHORIZED** in every record | `DOCUMENTED CLAIM` |
| Billing / payment implication | surfaces exist but there is **no PSP, no entitlement enforcement, no invoicing** | **material risk if the billing screen is shown without narration** |
| Retention / erasure implication | the retention surface lists five domains but **only two are enforced**; no legal hold, no erasure, no storage-object deletion | **material risk if settings are shown as compliance** |
| Demo-only behaviour presented as general capability | the lab is explicitly a lab; the "1,185 investor identity" dataset referenced by `AGENTS.md` §54 **is not in this checkout** | see §15 |
| Messaging implication | live delivery blocked in the lab (no `/realtime/v1`) | risk if messaging is shown as live |

**Where something is synthetic, it is labelled synthetic:** all documents come from the pinned external generator, are copied into a lab-local corpus outside the repository, and carry `corpus_provenance.json` plus per-document SHA-256 and `generation_seed`. **Where something is deterministic demo data, it is identifiable:** the artefact prefix `t3imp_<scenario>__`, the lab e-mail domain `@demo-lab.carbontally.local`, and organisations named "Demo Lab Organisation A/B", "Demo Lab Client A/B". `CODE-TRACED`.

**Verdict:** the repository already carries unusually strong truthfulness machinery (bounded narration, honest block reasons, `no_data` ≠ `zero`, an explicit "not a certification" disclaimer, recorded limitations). The residual risk is **presentation, not fabrication**: no demo script exists that encodes which limitations must be spoken, and two screens (billing, retention) can mislead if shown without their limitation sentences. `INFERENCE`.

---

## 13. Demo reset and repeatability

| Mechanism | Exists | Verified | Notes / gaps |
| --- | --- | --- | --- |
| Clean reset (full) | yes — `reset_demo_lab.sh` | `DOCUMENTED CLAIM` (code-traced; executed historically) | lab auth users (by e-mail domain) → lab containers → `DROP DATABASE carbontally_demo_local WITH (FORCE)`; `--purge-state` deletes credentials/evidence. **Never** touches the stack DBs, the investor dataset, production or Render — correct safety posture | `CODE-TRACED` |
| Deterministic re-provisioning | yes — `run_demo_lab.sh` (stack → provision → env → verify → optional factors) | `DOCUMENTED CLAIM` | README states every step is idempotent; **not re-executed here** (read-only preflight) |
| Lab-scoped artefact reset (T3) | yes — `t3_scenarios.py reset` | **implementer-only after remediation** | OHD-079 verified the original reset **BROKEN** (B-2: direct `storage.objects` deletion blocked by `protect_objects_delete`); REM-001 switched to the Storage API (`storage_delete_objects()` at `t3_scenarios.py:611`), but **the fix was never independently verified** and the reset/reseed proof was **"NOT EXECUTED"** | `DOCUMENTED CLAIM` + `CODE-TRACED` |
| Idempotent seeding | yes | **OHD-observed (pre-remediation)** | second identical seed: 11/11 skipped, 0 new uploads, no duplicate state | `DOCUMENTED CLAIM` |
| Isolation between runs | yes | `CODE-TRACED` | lab-prefixed containers, dedicated DB, deterministic UUIDs, `t3imp_` prefix, hard `assert_lab_database()` guard; `seed_factors.py` has its own DB-name guard |
| Restoration to a known state | **PARTIAL** | — | a full reset destroys the lab DB, so "known state" must be re-created by stack + provision + factors + corpus sync + seed; there is **no golden-state artefact or snapshot/restore**, and `/tmp/extgen` is gone, so the corpus cannot currently be re-synced |
| Repeated execution without duplicate data | **PARTIAL** | `DOCUMENTED CLAIM` | seeding skips already-seeded scenarios; report generation creates a **new** row per call (DR-006/DR-007: two annual reports + a stale `ghg_inventory` are the visible result) → repetition *accumulates* report artefacts |

**Exact gap (not fixed here):** there is **no verified end-to-end "reset → re-provision → re-seed → verify" rehearsal** for the *current* release, yet every successful demo depends on one. This is P12's central repeatability item (P12-08) and it interacts with P12-01 (stale lab schema).

---

## 14. UI/UX readiness observations

Concrete, code/test/browser-traced observations only. **No redesign proposed and no fix made.**

| Observation | Kind | Evidence |
| --- | --- | --- |
| Three genuine investor-facing display defects were found and **fixed + browser-verified** (documents `Uploaded` bound to the wrong field; workspace `Scope` read from a non-existent payload path; review "Mapped activity" read the wrong key). Post-fix: real timestamps, `Scope 1`, `Mapped activity Natural gas` | resolved | DR-007 |
| Three triaged issues were **not defects** (factor `source` vs `set` are two real DB fields; the evidence "Technical details" control is a working native `<details>`; empty Currency/Amount are disabled editable inputs) | expected behaviour | DR-007 |
| **Three issues require PO decisions and were left untouched**: (1) no customer document-detail/preview route (`/documents` only — the document view is the processing workspace + inline emissions panel); (2) duplicate/stale annual report rows remain in the list; (3) legacy `ghg_inventory` cannot be refreshed (generation API supports `annual` only → 422) | open PO decisions | DR-007 |
| The regression tests written for the two rendering fixes **could not be executed** — the jest/jsdom environment cannot load `canvas` (pre-existing limitation) | pre-existing test-infrastructure gap | DR-007 |
| The exception/processing workspace communicates the machine reason and next step on one screen ("Manual review · attempt 0/3 · mapping could not auto-resolve: line 1: no confident factor for 'Water' litres (status=no_match, confidence=0.00)") — a genuinely strong, honest UX | strength | DR-005 |
| Reports render a 12-section artefact (organisation, period, lineage, provenance, validation, branding), but the 2025 annual report's emissions content was **stale** (generated before the R-A row); DR-006 regenerated it correctly — the stale artefact and the duplicate row remain visible | data/artefact coherence risk | DR-005 + DR-006 |
| Insight answer states carry an explicit frontend guard — "`no_data` is never shown as `zero`"; narration is labelled "CarbonTally summary" and can be suppressed; `0 data lookups` renders when no tool ran | strength (machine-checkable) | `InsightAnswerState.jsx` (`CODE-TRACED`) |
| Tool results without a dedicated renderer (**all P3 results**, and any other tool) appear only as `<tool name> + <status badge>` plus narration; there is no structured data-quality/reproducibility view | **gap** | `InsightInteraction.jsx` (`CODE-TRACED`) |
| Messaging live delivery/notification is blocked in the lab (no `/realtime/v1` gateway route); processing views refresh by 10-second HTTP polling | gap (PO decision) | DR-005 |
| Loading / empty / error states: the v3 shell provides `StateViews`, `DataTable`, `Alert` and D21 tokens (master preflight §9.5); no systematic empty-state audit exists for the demo journeys | not systematically verified | `DOCUMENTED CLAIM` |
| Responsive behaviour and accessibility of the demo journeys: **no evidence found** in the DR records or tests for the demo path | **UNKNOWN** | — |
| Dead-end flows: none recorded in DR-001…DR-007; the known dead-end risk is a *presentation* one — an unanswerable question must surface `unsupported`/`no_data` rather than an empty control (the matrix's own rule) | risk | `DOCUMENTED CLAIM` |

---

## 15. Documentation / code divergences

Recorded for PO decision. **None was silently reconciled; no side was modified.**

| ID | Divergence | Evidence | Status |
| --- | --- | --- | --- |
| **X-5 / D-27** | `AGENTS.md` §54 names `tools/seed_investor_demo/DEMO_IDENTITIES.md` (~50 orgs, 911 consultant-client owner identities, **1,185 identities**). **That directory does not exist in this checkout**; the real manifest is `tools/demo_lab/manifest.json` (**13 actors**). `.gitignore:49` still ignores the non-existent path | `ls tools/` → no `seed_investor_demo`; `git check-ignore -v` matches; `grep` finds only historical `docs/` references | **CONFIRMED — PO DECISION REQUIRED** |
| **X-5 corollary** | Because the dataset is absent, `AGENTS.md` §54/§55 investor-demo-safety rules currently protect nothing in this checkout, and the demo's identity domain differs (`@demo-lab.carbontally.local` vs the documented `@demo.carbontally.local`) | `CODE-TRACED` (README §3) | **PO DECISION REQUIRED** (which dataset the demo uses) |
| **X-3 / D-28** | X2 alerting and X7 metrics **contract records** say "IMPLEMENTATION BLOCKED / PO DECISION REQUIRED" while implementation, tests and wiring exist | matrix conflict register; master preflight §3.1 | **CONFIRMED — PO DECISION REQUIRED** |
| **New — matrix tool count** | The P1 matrix §3.2 states "**seven** authorized tools (closed catalogue — no eighth tool exists or is implied)"; the registry now holds **10** (P2 and P3 added tools 8–10 after the matrix) | `CODE-TRACED` (`assert len(TOOL_REGISTRY) == 10` passes) | **CONFIRMED — matrix not updated after P2/P3** |
| **New — matrix family statuses** | Matrix §4 lists family 11 Temporal Comparison **MISSING** and family 14 Data Quality Intelligence **MISSING**; both are now implemented (P2 closed; P3 implemented + independently verified) | matrix §4.11/§4.14 vs P2/P3 records | **CONFIRMED — point-in-time planning artifact** |
| **New — preflight staleness** | Master preflight §9.4 lists "temporal comparison" among the truthful limitations to narrate, and §17.1's demo gate does not mention temporal comparison or data quality at all — both predate P2/P3 | master preflight §9.4/§17.1 | **CONFIRMED — the P12 gate must add them** |
| **New — T3 record inconsistency** | The T3 REM-001 report ends **"IMPLEMENTATION BLOCKED — PO REVIEW REQUIRED"** (round-3 `uk-ambiguity` failure; many sections "NOT EXECUTED"), while `t3_manifest.json` encodes the *later* reconciliation (R-1/R-2 decisions, `EXPECTED_*`, `established_no_viable_candidate`) | T3 REM-001 §8/§22 vs `t3_manifest.json` `_rem001_reconciliation` | **CONFIRMED — no single authoritative T3 status record** |
| **New — T3 verification status** | The only independent verification of the demo harness (OHD-079) returned **FAIL** before remediation; after remediation there is **no** independent verification record | OHD-079 §20 vs `t3_scenarios.py`/REM-001 | **CONFIRMED — release-relevant** |
| **New — lab vs release schema** | The Demo Lab DB is a pre-Insight provision (no `%insight%` tables) while the release contains six Insight migrations; **no document records the lab's schema revision** | `DATABASE-OBSERVED` + `supabase/migrations` | **CONFIRMED — no lab schema-revision record exists** |
| **New — P3 documentation timeline** | The P3 implementation report still cites the pre-rename migration filename (P3-IV-03) and the P3-IV-04 "13-file / 299" set is still not enumerated; both remain open | P3 IV reports | **open governance items** |
| **Informational** | The lab DB has no table named `reports`/`report_instances` while DR records speak of "report" rows; report data lives in `report_versions` (+ `report_comments`, `report_generation_queue`, `report_version_artifacts`) | `DATABASE-OBSERVED` | recorded, no action implied |
| **D-27 (untracked records)** | The P1/P2/P3/Insight PO reference documents and the CoStrict verification artefacts are **untracked**; only committed reports are durable | `git status` | **PO DECISION REQUIRED** (durability) |

---

## 16. Proposed P12 acceptance gate (bounded)

Derived **only** from the master preflight §17.1 (the only existing demo-gate proposal), the P1 matrix §11 (investor-demo capability map) and the capabilities actually verified above. **No scoring, no ranking, no percentage complete.** Each clause is pass/fail with evidence.

**Gate mechanics (proposed, mirroring the existing per-package gate at master preflight §17.2/§17.3):** a pre-demo verification run recorded with Git SHA, database identity, the scenario list and raw output; DR-001…DR-007 findings re-checked; the truthful-limitation script reviewed before the demo; and an explicit statement that passing this gate is **not** production authorization.

### A. Functional demo — the core customer journey, end-to-end
1. A demo persona can authenticate and land in the correct workspace, all roles used in the script included.
2. A document can be uploaded through the customer UI and the consultant-client path, with the created rows visible server-side.
3. Upload → extraction → mapping → validation → calculation completes **for at least one ready scenario**, with the deterministic figure, factor, methodology and algorithm version all visible on screen.
4. A blocked document explains **why** in machine-readable terms and presents a next step.
5. A report can be generated/opened and its artefact downloaded; its emissions content matches the calculated data (no staleness).
6. Exports (CSV/JSON) return the same numbers as the UI.

### B. Insight — only the implemented and verified families, truthfully
7. Identified calculation lookup, discovery (incl. `multiple_matches`), aggregation and aggregate provenance work against real data.
8. **P2 temporal comparison** works for two explicit periods, including zero-baseline and empty-period behaviour.
9. **P3 data quality and reproducibility** work and are presented with their true status (implemented + independently verified; **not** PO-closed) and with the partial-coverage observation respected.
10. An unsupported capability (e.g. supplier analytics, Scope 3 question) returns `unsupported`/`no_data` **on screen**, not a guess.

### C. Evidence — the answer-to-evidence chain
11. The chain question → deterministic computation → structured answer → provenance → **Source Evidence Viewer** → source is demonstrated for at least one record end-to-end.
12. If the Viewer cannot be exercised from live data, the gate **fails clause 11** and the presenter must state the limitation explicitly rather than substituting a lineage panel *without saying so*.

### D. Security — isolation and authorization demonstrated
13. ALLOW **and** DENY are both shown for at least one cross-tenant pair (org A ↔ org B) and one plane boundary (customer ↔ consultant, or client A ↔ client B).
14. The denied attempt is visible as a real server-side denial (not a hidden button), and the evidence is recorded in the run's output.
15. No signed URL, credential or token appears in any demo artefact, log or slide.

### E. Failure honesty — no fabricated success
16. At least one `no_data`/`unsupported` and one ambiguous/no-match moment are shown **as part of the script**.
17. Billing is presented as configuration/surfaces only; retention settings are presented with their enforced/unenforced reality; no certification, audit-assurance or production-readiness claim is made anywhere.
18. Every number on screen traces to a persisted record the audience can see.

### F. Repeatability — reset and rerun
19. Reset → re-provision → re-seed → verify completes with recorded evidence on the current release, and a second immediate run produces no duplicate state (report accumulation handled or accepted in writing).
20. The pre-demo verification run (`verify.py`, plus the Insight checks) passes, or every failure is enumerated as a known, narrated limitation.

### G. Data truthfulness
21. Synthetic/demo data is identified as such in the script (generator pin recorded, corpus provenance available, lab e-mail domain, `t3imp_` prefixes).
22. The demo dataset's identity (Demo Lab vs the `AGENTS.md` §54 dataset) is decided and stated.

### H. Investor narrative
23. The demo never presents a future capability as existing: verified-limitations list is spoken, and the "implemented / independently verified / PO-closed" distinction is respected for each capability shown.
24. No production, certification, security or commercial commitment is implied and no presenter claim exceeds the screens shown.

---

## 17. P12 implementation backlog

Classes: `P12-REQUIRED` · `P12-OPTIONAL` · `NOT-P12` · `BLOCKED`. "P3 closure?" states whether the item depends on P3 becoming PO-closed. **Nothing below is implemented by this preflight.**

### 17.1 P12-REQUIRED

| ID | Gap | Evidence | Required change (bounded) | Depends on | P3 closure? | PO decision? | Suggested verification | P12 relevance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **P12-01** | The Demo Lab DB is a pre-Insight provision: 136 tables, **no** Insight tables, so no Insight route can run | `DATABASE-OBSERVED`; `supabase/migrations/2026100*` | Establish whether `stack.py` applies missing migrations to an existing lab DB; if not, reset + re-provision the lab to the current release schema and record the lab's schema revision in its evidence | none (lab-local) | no | no (tooling is documented) — but a reset **destroys current lab data**, so the PO must accept that | `stack.py` reports `migrations_with_errors: []`; a post-provision query returns the six Insight tables; `/api/v3/insight/tools` answers 200 | precondition for **all** Insight demonstration |
| **P12-02** | Only **1** calculation snapshot / **1** emissions log / **0** evidence line items exist, and 13 of 14 documents are blocked in `manual_review` | `DATABASE-OBSERVED` | Re-run the authorized pipeline (corpus sync + seed) against the re-provisioned lab so a scripted demo has a real population, keeping the honest blocks | P12-01; P12-12; PO authorisation for lab-data mutation | no | **yes** (mutation of demo data; report regeneration is already a PO question, DR-005 §20) | per-run T3 evidence JSON; queue/snapshot/emissions/evidence counts recorded with the run | without it every Insight demo is empty and the core journey has one record |
| **P12-03** | No scripted investor demo flow exists; the corpus contract records only 2 `EXPECTED_MATCHED` scenarios | `OBSERVED` (no script artefact); `t3_manifest.json` | Write a bounded demo script: personas, scenarios, screens and limitation sentences; explicitly mark ambiguous / no-match / spend-unsupported scenarios as *honest failures* | P12-02 | no | **yes** (which limitations the audience hears) | script reviewed against §16; rehearsal produces the expected states | converts raw capability into a repeatable narrative |
| **P12-04** | The demo harness's only independent verification is **FAIL** (OHD-079); the remediation is implementer-verified only with many sections "NOT EXECUTED" | OHD-079 §20; T3 REM-001 §8/§22 | Commission independent verification of the **remediated** `t3_scenarios.py` + manifest (selection, seeding, reset, ground-truth, idempotency) | P12-01 (a lab to run against) | no | **yes** (authorisation of an independent pass) | independent PASS/FAIL with raw evidence on a frozen commit | the demo's evidence producer must itself be trustworthy |
| **P12-05** | Insight (INS-01 + P2 + P3) is never exercised by any demo tooling; P3 has **no UI renderer** | `grep 'insight' tools/` = 0; P3 tool grep in `frontend/src` = 0 | Add an Insight step to the demo verification tooling; for P3 choose a presenter-side API/tool demonstration or an agreed minimal presenter view — **without** inventing a new evidence viewer or any NL/SQL surface | P12-01; PO decision on P3 presentation | **no** (P3 is already independently verified; closure affects only the claim language) | **yes** (presentation scope) | run the Insight step live; assert `no_data` / `no_checkable_records` / limitation states appear truthfully | the differentiator the roadmap has been building toward |
| **P12-06** | The Source Evidence Viewer cannot be demonstrated from live data (`evidence_line_items = 0`) | `DATABASE-OBSERVED` + `CODE-TRACED` | Establish **why** no evidence line item exists for a calculated record (product behaviour vs workflow gap) and, on that basis, either produce one through the normal workflow or record the limitation; **do not** create a second viewer | P12-01 / P12-02 | no | **yes** if it becomes a defect triage | `/evidence/line-items/{id}` renders an authorised line item; a foreign id is denied | clause C11 is otherwise unprovable |
| **P12-07** | No pre-demo verification record or runbook exists for the current release | `OBSERVED` (master preflight §17.1 lists it as *should be polished*) | Produce the runbook + a recorded pre-demo verification (Git SHA, lab DB identity, migration count, scenario list, raw pass/fail, known limitations) | P12-01 / P12-02 | no | no | the record itself is the artefact; a re-run reproduces it | gate mechanics (§16) |
| **P12-08** | No verified `reset → re-provision → re-seed → verify` rehearsal exists; the T3 reset fix is unverified | §13; OHD-079 B-2; REM-001 | Rehearse the full cycle on the current release and record it, including second-run idempotency and report-accumulation behaviour | P12-01 | no | **yes** (reset is destructive to lab data) | second run: 0 duplicate documents/scenarios; invariants asserted before/after | a demo that cannot be repeated is not a gate |
| **P12-09** | The isolation matrix exists in `verify.py` but is not a scripted presentation and has no visible in-UI denial | `CODE-TRACED` (`verify.py:99-210`); DR-005 | Script the ALLOW/DENY demonstration (org A↔B, client A↔B, consultant→unrelated, viewer/member) and record raw output; ensure no signed URL/token is shown | P12-01 | no | no | raw probe output with expected denial codes; screen evidence of at least one denial | clauses D13/D14 |
| **P12-10** | No scripted failure-honesty moments and no limitation list for presenters | §12; master preflight §9.3/§9.4 | Encode at least one `no_data`/`unsupported` and one ambiguous/no-match moment, plus the billing/retention/certification sentences | P12-02 / P12-03 | no | **yes** (wording of limitations) | scripted run shows the states on screen and the sentences are spoken | clauses E16–E18 |
| **P12-11** | Demo verification covers identities/authorization only — no Insight, data-quality or reproducibility checks | `CODE-TRACED` (`verify.py`) | Extend demo verification (or add a companion checker) to assert Insight tool availability, one deterministic aggregate, one data-quality answer and one reproducibility answer | P12-01 / P12-05 | no | no | new checks run green against the re-provisioned lab | clauses B7–B9 |
| **P12-12** | The corpus cannot currently be re-synced: `/tmp/extgen` (the pinned generator checkout) is absent, and `sync-corpus` defaults to it | `OBSERVED`; `t3_scenarios.py` (`--source` default) | Re-create a read-only checkout at the pinned commit `8ade2bf…` (or point `--source` at an existing one) so the corpus can be re-selected without network assumptions | none | no | no | `sync-corpus --dry-run` resolves 11/11 deterministically; SHA-256s match `corpus_provenance.json` | required for P12-02 / P12-08 |

### 17.2 P12-OPTIONAL

| ID | Gap | Evidence | Change | Notes |
| --- | --- | --- | --- | --- |
| **P12-13** | Duplicate/stale report artefacts are investor-visible (two annual reports; unrefreshable `ghg_inventory`) | DR-007 issues 8–9 | PO decision, then a bounded lab-data cleanup **or** an explicit narrative | demo-data only; PO decision required |
| **P12-14** | `rate_limited` cannot be demonstrated (limiter tables absent from the lab) | `DATABASE-OBSERVED` | After P12-01, script a rate-limit demonstration if the audience value justifies it | otherwise present as tested-not-demonstrated |
| **P12-15** | Messaging live delivery is blocked (no `/realtime/v1` on the lab gateway) | DR-005 §18 | Add the gateway route (lab capability) or keep messaging in the narrative as polled | PO decision (DR-005 §20 item 3) |
| **P12-16** | PE and internal-ops surfaces have no demo-verified depth | DR-005 §20 item 6 | Bounded verification of one PE journey and one ops journey | PO decision on depth |
| **P12-18** | The demo path has no browser automation; the QA harness is BUILD-ONLY | `qa_harness/README.md`; `playwright.config.ts` | Optionally automate the scripted path for regression | must never target non-disposable data without authorisation |
| **P12-21** | Responsive/accessibility of the demo journeys is unverified | §14 | Optional bounded audit at the documented viewports | AGENTS.md §49/§50 framing |
| **P12-22** | No "golden state" artefact for the demo | §13 | Optional reproducible snapshot/restore of the lab to a known demo state | depends on PO decisions about mutation |

### 17.3 NOT-P12

| ID | Item | Why not P12 |
| --- | --- | --- |
| **P12-17** | Reconciling X-5 (`AGENTS.md` §54 path), D-28 (X2/X7 records), the matrix's stale tool-count/family statuses, the T3 record inconsistency and D-27 durability | governance/documentation track; only the demo-relevant subset (which dataset, which statuses are narrated) feeds P12 |
| **P12-19** | OCR / scanned-document support | production-critical and explicitly deferred (T3 §21); not demo-critical |
| **P12-20** | F-T1-001 (`audit-activity` 500 for an authorised owner) | a genuine product defect for separate bounded triage; P12 only decides to avoid or narrate it |
| — | Scope 3 / market-based Scope 2 / Scope 1 decomposition / variance / supplier persistence / factor history / knowledge layer / reduction intelligence | not authorized and decision-blocked (D-09/D-10/D-12/D-13/D-15/D-17/D-19); the demo must return `unsupported` |
| — | L7 retention lifecycle, L8-A SLO/incident policy, L8-B billing/PSP | separate packages (P4/P5/P11); no demo dependency |
| — | Production deployment, environment promotion, certification | explicitly excluded (§19) |

### 17.4 BLOCKED

| Item | Blocked by |
| --- | --- |
| Any P12 item that mutates lab data, regenerates/deletes report artefacts or resets the lab (P12-02, P12-08, parts of P12-01/P12-13) | **PO authorisation** — they change demo data |
| Independent verification of the remediated harness (P12-04) | **PO authorisation** of an independent pass |
| Any capability claim based on the `AGENTS.md` §54 dataset (1,185 identities) | the dataset does not exist in this checkout (X-5) → **PO decision on which dataset the demo uses** |

---

## 18. Dependencies and blockers

**Can P12 begin implementation immediately after P3 PO closure?** It can **begin**, but P3 closure is **not the only precondition** — and several items must be decided or authorised first.

### 18.1 What P3 closure does and does not unblock

* P3 closure affects only the **claim language** for P3 in the demo (whether data quality / reproducibility may be described as "closed"). It is **not** an engineering precondition for any P12 item (see the "P3 closure?" column in §17).
* P3 closure does **not** fix: the stale lab schema, the near-empty population, the missing evidence line items, the unverified corpus harness, the missing demo script, or any documentation divergence.

### 18.2 Hard blockers found (ordered by severity for P12)

| # | Blocker | Evidence | Type |
| --- | --- | --- | --- |
| B1 | **Demo Lab schema is stale** — no Insight tables at all; the entire Insight layer (INS-01, P2, P3) cannot run in the demo | `DATABASE-OBSERVED` | engineering (lab-local) — P12-01 |
| B2 | **Near-empty demonstrable population** — 1 snapshot, 1 emissions log, 0 evidence line items, 13/14 documents blocked | `DATABASE-OBSERVED` | engineering + PO authorisation for data mutation — P12-02 |
| B3 | **Evidence-destination link has no data** — the Source Evidence Viewer cannot be shown from live data | `DATABASE-OBSERVED` | engineering/forensic — P12-06 |
| B4 | **The corpus contract yields 2/11 successful mappings** — a general "upload → calculation" narrative is not truthful; the demo must be scripted around honest failures | `t3_manifest.json` | narrative + PO decision — P12-03/P12-10 |
| B5 | **The demo harness's only independent verification is FAIL; the remediation is unverified and REM-001 ends BLOCKED** | OHD-079 §20; T3 REM-001 §22 | verification governance — P12-04 |
| B6 | **No demo script, runbook or pre-demo verification record exists** | `OBSERVED` | engineering + PO wording decisions — P12-03/P12-07 |
| B7 | **No verified reset → reseed rehearsal; the reset fix is unverified** | §13 | engineering + PO authorisation — P12-08 |
| B8 | **The corpus cannot be re-synced** (`/tmp/extgen` absent) | `OBSERVED` | engineering — P12-12 |
| B9 | **P3 has no UI renderer**, and Insight has no demo tooling at all | `grep` = 0 in both | engineering + PO decision — P12-05/P12-11 |
| B10 | **Documentation/code divergence X-5** (`AGENTS.md` §54 dataset absent; 13 vs 1,185 identities) | §15 | **PO decision** — which dataset the demo uses |
| B11 | **Pre-existing product defect F-T1-001** (audit-activity 500) that an investor could trigger | `verify.py`; `DOCUMENTED CLAIM` | separate triage; P12 must avoid/narrate |
| B12 | **Billing and retention screens can mislead without narration** | §12 | narrative — P12-10 |
| B13 | **Messaging live delivery is blocked in the lab** | DR-005 | optional lab capability — P12-15 |
| B14 | **No live-RLS verification path for the demo** (F-046-1 forbids pointing the destructive harness at persistent data; the lab is not a disposable clone) | `CODE-TRACED` | engineering/governance — optional |

### 18.3 Dependency edges (P12-internal)

```text
P12-01 (lab schema)  ─┬─► P12-05 (Insight demo path) ──► P12-11 (Insight checks)
                      ├─► P12-14 (rate-limit demo, optional)
                      ├─► P12-02 (population) ──► P12-03 (script) ──► P12-10 (honesty clauses)
                      ├─► P12-06 (evidence chain)
                      └─► P12-08 (reset/rehearsal)
P12-12 (corpus checkout) ──► P12-02 / P12-08
P12-04 (harness verification) ──► independent; needs P12-01
P12-07 (runbook + pre-demo record) ──► after P12-01 / P12-02
P3 PO closure ──► affects P12-05 / P12-03 *claim language only* (no engineering edge)
```

**Conclusion:** P12 is **not** gated on P3 closure, but it **is** gated on (i) a lab re-provision, (ii) a PO decision permitting demo-data restoration, and (iii) PO decisions on narrative scope. Without those, P12 could only produce a demo showing one calculation, no Insight and no evidence viewer.

---

## 19. Explicit P12 exclusions

P12 is an **investor/demo readiness gate**. It is **not**, and must never be read as:

| Excluded from P12 | Why | Where it belongs |
| --- | --- | --- |
| Production deployment / environment promotion / production configuration | no such authorization exists anywhere in the record set | separate production gate |
| Security certification, penetration-test sign-off, ISO/SOC-style assurance | P12 *demonstrates* isolation; it does not certify | separate assurance track |
| Legal / compliance certification, regulatory sign-off, tax/VAT posture | L7/L8 governance decisions (D-01…D-08, D-20…D-26) are unanswered | PO / legal |
| Audit or accounting-assurance certification | E4 does not exist; the product itself disclaims certification | D-16 |
| Commercial billing readiness: PSP integration, invoicing, dunning, entitlements, overage metering | no PSP and no entitlement enforcement exist (master preflight §8) | P11 |
| Full L7 retention readiness (all domains enforced, legal hold, erasure, storage-object deletion propagation) | three of five domains unenforced; no legal hold, no erasure path | P4 / D-01…D-08 |
| Full L8-A governance (SLO/SLA commitments, alert thresholds/recipients, incident runbook, secrets policy, RTO/RPO) | PO decisions outstanding | P5 / D-08, D-20…D-26 |
| Consultant/auditor **expanded** readiness (consultant Insight, auditor direct Insight) | **DEFERRED / NOT AUTHORIZED** | separate authorization |
| Enterprise readiness, scale assurance, hardening programme, external APM/monitoring stack | production-critical, deliberately outside demo readiness | production track |
| Scope 3 taxonomy, market-based Scope 2, Scope 1 decomposition, variance/attribution, supplier persistence, factor-history intelligence, knowledge/RAG layer, framework mapping, reduction intelligence | not implemented and decision-blocked | P6–P10 / D-09…D-19 |
| Creating a second evidence viewer or any new evidence capability | the shared Source Evidence Viewer remains the single destination | INS-01 §7 / AGENTS.md |
| Unrestricted natural-language → SQL/database access; RAG answering | the NL boundary forbids it ("must not generate SQL"; closed schema only) | Architecture Reference v2 §12 |
| New accounting methodology, score, grade, weighting or confidence metric | P12 adds no methodology anywhere | architecture boundary |
| Investor-dataset reseed / truncation / global modification | AGENTS.md §55 (and the dataset is absent from this checkout anyway) | governance |
| Fixing display defects (DR-007 class), review-SLA failures, the D17 pin, F-T1-001 | out of scope for a readiness gate | separate triage |
| Committing the untracked PO/CoStrict reference artefacts | a durability decision (D-27) | PO governance |

---

## 20. Recommended next PO decision

**A single bounded authorization is recommended, in two parts**, because parts of P12 mutate demo data and therefore cannot proceed on an engineer's judgement.

**Part 1 — authorise the non-mutating P12 workstream (can start immediately):**

1. **P12-01 (investigation half):** establish whether `stack.py` applies missing migrations to an existing lab DB, and record the lab's current schema revision — read-only diagnosis.
2. **P12-12:** restore a read-only checkout of the external synthetic-document generator at the pinned commit `8ade2bf778d518d59924905849ab114ab2d082a0` (no generator change; nothing new is brought into the release).
3. **P12-06 (forensic half):** determine why no `evidence_line_items` row exists for a calculated record and report it (a fix only if separately authorised).
4. **P12-03 / P12-10 (drafting half):** draft the demo script and the truthful-limitation sentences for PO review.
5. **P12-11 (design half):** specify the Insight demo/verification checks, including the P2 and P3 steps.

**Part 2 — PO decisions required before any mutating or claim-bearing step:**

| # | Decision needed | Consequence if deferred |
| --- | --- | --- |
| D-A | **Which dataset the demo uses** — the 13-actor Demo Lab (`tools/demo_lab/manifest.json`) or the `AGENTS.md` §54 dataset that is absent from this checkout (X-5) | the demo's identity/narrative foundation is unresolved |
| D-B | **Authorise lab re-provision** (reset + rebuild to the current release schema), accepting that current lab data is destroyed (B1 / P12-01) | no Insight capability can be demonstrated at all |
| D-C | **Authorise demo-data restoration** — re-run corpus sync + seed, and decide the report-artefact question (regenerate / clean duplicates / narrate) (P12-02, P12-13) | the demo shows one calculation and near-empty Insight |
| D-D | **Approve the demo narrative and its limitation list** — notably that most corpus scenarios are honest ambiguous/no-match/unsupported outcomes, that evidence depth is E3 (not E4), and that billing/retention/messaging limitations are spoken (P12-03, P12-10) | truthfulness risk: the demo could imply capabilities that do not exist |
| D-E | **Decide the P3 presentation status** — "implemented and independently verified, PO closure outstanding" (recommended; accurate today) or wait for closure | affects only the words used about P3 |
| D-F | **Authorise independent verification of the remediated T3 harness** (P12-04) | the demo's evidence producer remains FAIL-then-unverified |
| D-G | **Decide whether the documentation divergences (X-5, D-28, matrix staleness, T3 record inconsistency, D-27 durability) are reconciled inside P12 or in the separate governance track** (recommended: separate, with only the demo-relevant subset inside P12) | recurring ambiguity about which record is authoritative |

**Recommended sequencing:** Part 1 now → D-A…D-C → P12-01 (mutating half) + P12-02 → P12-05/P12-06/P12-07/P12-08 → D-D → P12-03/P12-09/P12-10/P12-11 → pre-demo verification → **then** the P12 gate. P3 PO closure may occur in parallel; it changes only the words used about P3.

---

## Appendix A — Verification of this preflight's own repository impact

| Check | Result |
| --- | --- |
| Files created by this task | `docs/architecture/CT-PO-P12-INVESTOR-DEMO-READINESS-PREFLIGHT-20260923.md` — **the only change** |
| Application code / tests / migrations / frontend / demo tooling / demo data / configuration modified | **none** |
| Database writes | **none** — only read-only `SELECT`s against `carbontally_demo_local` (the Demo Lab database); the investor/stack databases were never queried |
| Containers created / removed / configured | **none** (read-only `docker ps` and `docker exec … psql -tAc "SELECT …"`) |
| Secrets, tokens, signed URLs or credentials introduced | **none** — no credential file was read; only counts and non-sensitive identifiers/fields are quoted |
| Branch switched / history rewritten / reset / stash / clean | **none** |
| Commit content | this report only (documentation-only commit) |
| Push target | `github/p8-release-reconciled` |
| Pre-existing untracked artefacts (`.costrict/`, `8`, `=`, `costrict-p3-ov-01-independent-re-verification.txt`, 8 untracked PO documents) and the pre-existing `.gitignore` modification | **left exactly as found — not staged, not committed** |

---

## Final status

```text
P12 PREFLIGHT COMPLETE — READY FOR PO REVIEW
```

**Already demo-ready** (verified live or browser-verified): authentication with real personas · customer workspace and processing/exception workspace with honest machine-readable block reasons · document upload (direct and consultant-client) · the deterministic calculation `2469.169780 kg CO₂e` with factor, methodology and algorithm version visible · report generation with a downloadable artefact containing the real total · exports · consultant/client tenant scoping · billing/plan **surfaces** (configuration only) · the 7,049-factor dataset.

**Missing** (all lab-local; no production authority needed): the current release schema in the Demo Lab (**no Insight tables at all**) · a meaningful calculation/evidence population (1 snapshot, 1 emissions log, **0** evidence line items, 13/14 documents blocked) · any Insight demonstration path (P2 and P3 included) · a scripted demo flow with truthful-limitation sentences · a pre-demo verification record / runbook · a verified reset → reseed rehearsal · an independently verified corpus harness (its only verdict is FAIL, pre-remediation).

**Depends on P3 closure: nothing structurally.** P3 closure affects only the claim language for data quality / reproducibility (P12-05, P12-03). P3 is currently *implemented* + *independently verified* (P3-IV-01 remediated and re-verified at `2be9033`) but **not PO-closed**; this preflight neither closes it nor assumes closure.

**Requires a PO decision:** D-A dataset identity (X-5) · D-B lab re-provision · D-C demo-data restoration · D-D demo narrative/limitations · D-E P3 presentation wording · D-F independent verification of the remediated harness · D-G where the documentation divergences are reconciled.

**Must remain outside P12:** production deployment; security/legal/audit certification; full L7/L8 governance and commercial billing; consultant/auditor expanded readiness; Scope 3, market-based Scope 2, Scope 1 decomposition, variance, supplier persistence, factor history, knowledge/RAG, reduction intelligence; any new evidence viewer; any NL→SQL or RAG surface; any new accounting methodology, score or grade.

**Not claimed by this report:** P3 closure, P12 implementation, P12 acceptance, investor readiness, production readiness or any certification. This is a **read-only preflight**; implementation may begin only under a fresh bounded authorization.



















