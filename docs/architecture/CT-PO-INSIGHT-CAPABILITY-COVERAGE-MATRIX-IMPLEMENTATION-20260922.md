# CT-PO-INSIGHT-CAPABILITY-COVERAGE-MATRIX — IMPLEMENTATION REPORT

**Document ID:** `CT-PO-INSIGHT-CAPABILITY-COVERAGE-MATRIX-IMPLEMENTATION-20260922`
**Task:** P1 — CarbonTally Insight Capability Coverage Matrix
**Type:** DOCUMENTATION / GOVERNANCE ARTIFACT ONLY — no application capability implemented
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Remote:** `github`
**Baseline HEAD at task start:** `8916f82bb71dd8e3ef3050b4b1185507dd5b14cb`
**Date:** 2026-09-22

---

# 1. Purpose of this report

To record exactly what the P1 task inspected, created, verified and did **not** change, so that the artifact's provenance is auditable independently of the matrix itself.

---

# 2. What was inspected

## 2.1 Repository state (verified before any work)

| Check | Result |
| --- | --- |
| Branch | `p8-release-reconciled` |
| `git rev-parse HEAD` | `8916f82bb71dd8e3ef3050b4b1185507dd5b14cb` |
| `git ls-remote github refs/heads/p8-release-reconciled` | `8916f82bb71dd8e3ef3050b4b1185507dd5b14cb` |
| `git rev-list --left-right --count HEAD...github/p8-release-reconciled` | **`0 0`** (aligned) |
| `git status --short` | clean except the pre-existing untracked PO/ChatGPT documents (listed in §4) |
| INS-01 evidence present in history | `c7cd9cc` (preflight), `e4ea325` (implementation), `cbc529d` (implementation + report), `f1a7cce` (OHD verification) — all confirmed as commit objects |

## 2.2 Documents read

| Document | Use |
| --- | --- |
| `docs/architecture/CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md` | package IDs, D-ID register, family inventory, conflict seeds |
| `docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md` | family definitions, answer-quality model, E0–E4 evidence depth, NL/security/rate-limit/viewer sections, roadmap, status |
| `docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md` | 43 sections, 426 numbered questions, question classes, evidence modes A–F, clarification/no-data rules, ASK→VERIFY→EXPLAIN→TRACE, governance reminder |
| `docs/architecture/CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md` | C-nn capability decisions, §3.1–§3.11 detail, dependency order, evidence/security requirements, explicit boundary |
| `docs/architecture/CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md` | closure status, capability-status reconciliation, accepted observations, pre-existing defect boundary, technical-vs-commercial separation |
| `docs/architecture/CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-IMPLEMENTATION-20260922.md` and `…-OHD-VERIFICATION-20260922.md` | INS-01 scope and independent verification evidence |

## 2.3 Code and history verified during this task

| Claim asserted in the matrix | Verification performed | Result |
| --- | --- | --- |
| 15 answer states incl. `multiple_matches` | read `AnswerStatus` in `backend/domain/insight_interaction.py` | confirmed 15 values |
| 6-value `ToolStatus`, 4 reference kinds | read `backend/domain/insight_tool.py` | confirmed |
| 7-tool catalogue, no eighth tool | `TOOL_INSIGHT_DISCOVERY` / `_AGGREGATION` / `_AGGREGATE_PROVENANCE` (`backend/domain/insight_query.py:42-44`) plus the four ratified tools | confirmed |
| Bounds 25 / 50 / 100 / 3,660 / 3 / 128 and tolerance ceilings | read constants in `backend/domain/insight_query.py` | confirmed |
| `AGGREGATION_DIMENSIONS` = 7 incl. `supplier` | read the tuple (`backend/domain/insight_query.py:85-93`) | confirmed |
| Discovery / aggregation / provenance engines | `search_snapshots` (677), `count_matching_snapshots` (696), `aggregate_groups` (711), `list_group_snapshots` (774), `count_group_snapshots` (815) in `backend/data/emissions_logs.py` | confirmed |
| Snapshot factor-provenance fields | `factor_id, factor_source, factor_set, co2e_multiplier, methodology, algorithm_version, factor_kind, customer_factor_id` | confirmed |
| `SCOPE2_METHODS` is disclosure vocabulary only | `backend/domain/disclosure.py:145,253` | confirmed |
| Supplier captured upstream, not on the emission write path | `manual_extraction_items.mapped_supplier_id` (`data/manual_extraction.py:36,114,531`), `ai_mapped_supplier_id` (`data/document_processing.py:42`) | confirmed |
| Retention: 2 of 5 configured domains enforced | `services/retention.py:35` `_ELIGIBLE_DOMAINS`; `:52` `telemetry_excluded_tables` | confirmed |
| Insight ledgers have no delete surface | `NotImplementedError` at `data/insight.py:179`; `data/insight_interactions.py:184,192,199` | confirmed |
| Exports include `audit-package.json` | `api/v3_exports.py` routes | confirmed |
| Retention settings API | `api/v3_settings.py:72` GET, `:82` PUT `/retention` | confirmed |
| L8-A mechanisms exist | `services/operational_alerting.py`, `services/api_metrics.py`, `data/api_metrics.py`, `domain/api_metrics.py` | confirmed |
| Billing = data model + repositories + API, no PSP | `domain/billing.py`, `data/billing.py`, `api/v3_billing.py`; no Stripe/PayPal/Adyen/Gocardless/Paddle SDK in `backend/` or `frontend/src/` | confirmed |
| No first-class Scope 3 dimension | only legacy `backend/utils/emissions.py:132,141,171` and `scope_hint` | confirmed |
| Demo infrastructure is `tools/demo_lab/` | listing incl. `manifest.json`, `run_demo_lab.sh`, `reset_demo_lab.sh`, `t3_scenarios.py`, `verify.py` | confirmed |
| Question Library size | last numbered question is **426** (line 674) | confirmed |

---

# 3. What was created

| File | Lines | Nature |
| --- | --- | --- |
| `docs/architecture/CarbonTally_PO_Insight_Capability_Coverage_Matrix_2026-09-22.md` | 1,245 | the permanent coverage/planning matrix (the P1 deliverable) |
| `docs/architecture/CT-PO-INSIGHT-CAPABILITY-COVERAGE-MATRIX-IMPLEMENTATION-20260922.md` | this file | the P1 implementation report |

## 3.1 Structure of the matrix

All 17 required sections are present:

§1 purpose and status · §2 source hierarchy **and conflict register** · §3 INS-01 verified baseline · §4 nineteen-family coverage matrix (summary table plus per-family detail for **families 1–19**, each recording business purpose, representative Question-Library questions, deterministic engine, authoritative data, current Insight tool/API exposure, current answer states, evidence depth, Source Evidence Viewer path, status, what is implemented, exact missing capability, schema-change requirement, accounting-policy requirement, PO decision IDs, dependencies, proposed package, security/tenant-isolation considerations, verification requirements, investor-demo relevance, production relevance, and current authorization status) · §5 Question Library coverage (section→family map, representative answerability, ASK→VERIFY→EXPLAIN→TRACE preservation) · §6 evidence-depth matrix · §7 answer-state matrix · §8 security/tenant-isolation matrix · §9 PO decision dependencies · §10 package dependency map · §11 investor-demo capability map · §12 L7/L8 dependency map · §13 current gaps · §14 recommended sequencing · §15 explicit non-authorizations · §16 verification requirements · §17 PO approval boundary · Final status block.

## 3.2 Status vocabulary used (exactly, never interchangeably)

EXISTS · PARTIAL · MISSING · PO DECISION REQUIRED · NOT AUTHORIZED · DEFERRED · ANSWERABLE · UNSUPPORTED · NO DATA · INFERENCE.

**Resulting split:** EXISTS **4** · PARTIAL **6** (one of which is data-empty) · MISSING **9**; eight families are accounting-decision-blocked (6, 7, 8, 9, 12, 15, 17, 19).

---

# 4. What was **not** changed

| Area | Status |
| --- | --- |
| Application / backend code | **not modified** |
| Frontend code | **not modified** |
| Migrations | **none created, none modified** |
| Database schema | **not modified** |
| Tests | **not modified and not run** — a documentation-only package requires no application test, and this is stated explicitly so it is not mistaken for a passed suite |
| Configuration / environment | **not modified** |
| Billing · retention · legal hold · deletion · storage deletion | **not implemented or modified** |
| Insight features (temporal comparison, data quality, audit/reproducibility, Scope 3, market-based Scope 2, Scope 1 decomposition, supplier persistence, variance/attribution, knowledge/RAG, reduction intelligence, billing/PSP) | **not implemented** |
| INS-01 | **not modified, not reopened**; no observation remediated; no eighth tool added |
| X2/X7 contract records | **not reconciled** |
| Pre-existing review-SLA failures and the stale migration pin | **not remediated** |
| Demo infrastructure · investor data · external synthetic generator | **not touched** |
| Deployment / production configuration | **not changed** |
| Untracked PO/ChatGPT documents | **not staged, not modified, not committed** |
| Secrets | **none introduced** — no credential, token, signed URL or key appears in either document |

---

# 5. Source files used

## 5.1 Documents (read from the repository)

`CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md` · `CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md` · `CarbonTally_Insight_Question_Library_2026-09-22.md` · `CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md` · `CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md` · `CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-IMPLEMENTATION-20260922.md` · `CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-OHD-VERIFICATION-20260922.md` · `AGENTS.md`.

## 5.2 Code cited in the matrix (verified as listed in §2.3)

`backend/domain/insight_query.py` · `backend/domain/insight_tool.py` · `backend/domain/insight_interaction.py` · `backend/domain/disclosure.py` · `backend/data/emissions_logs.py` · `backend/data/insight.py` · `backend/data/insight_interactions.py` · `backend/data/evidence_line_items.py` · `backend/data/settings.py` · `backend/data/audit.py` · `backend/data/exports.py` · `backend/data/suppliers.py` · `backend/data/manual_extraction.py` · `backend/data/document_processing.py` · `backend/data/notifications.py` · `backend/data/reporting.py` · `backend/data/api_metrics.py` · `backend/data/billing.py` · `backend/services/retention.py` · `backend/services/operational_alerting.py` · `backend/services/api_metrics.py` · `backend/services/insight_tools.py` · `backend/services/insight_query_planner.py` · `backend/services/insight_context.py` · `backend/services/insight_interactions.py` · `backend/api/v3_exports.py` · `backend/api/v3_settings.py` · `backend/api/v3_billing.py` · `backend/api/v3_emissions.py` · `backend/api/admin_audit.py` · `backend/engines/*` · `backend/utils/emissions.py` · `frontend/src/v3/**` (route surface, insight, evidence, admin, customer billing) · `supabase/migrations/**` (including the D37 billing migrations and the INS-01 migration) · `tools/enforce_retention.py` · `tools/backup_recovery_drill.py` · `tools/demo_lab/**`.

---

# 6. Discrepancies found

## 6.1 Conflicts recorded in the matrix (not silently resolved)

| ID | Conflict | Resolution applied |
| --- | --- | --- |
| **X-1** | PO capability matrix rows C-01/C-02/C-04/C-05/C-14/C-18 read “NOT IMPLEMENTED”, while discovery, aggregation (7 dimensions), scope grouping and aggregate→evidence provenance are implemented and OHD-verified | **INS-01 closure §6 governs** (it states the earlier matrix predates INS-01). The untracked earlier matrix was **not edited** |
| **X-2** | C-14's required discovery states vs the two implemented vocabularies | A **mapping** is documented (matrix §7.2); no substantive conflict |
| **X-3** | PO matrix §3.2 approved six aggregation dimensions; seven are implemented (supplier added) | Recorded; the INS-01 authorization explicitly included supplier; the dimension is currently data-empty |
| **X-4** | X2 alerting and X7 metrics **contract records** say “IMPLEMENTATION BLOCKED”, while code, wiring and tests exist | **Code is authoritative for what exists**; `PO DECISION REQUIRED` (**D-28**) to reconcile the records |
| **X-5** | `AGENTS.md` §54 names `tools/seed_investor_demo/DEMO_IDENTITIES.md`, which does not exist in this checkout | Filesystem governs; recorded as a documentation gap (D-27-adjacent) |
| **X-6** | PO matrix lists rate limiting as **NOT AUTHORIZED** (SEC-01), while INS-01 closed technical rate limiting | **INS-01 closure §8.7 governs for technical rate limiting only**; commercial controls remain unauthorized |

## 6.2 Clarifications (not conflicts)

| Item | Note |
| --- | --- |
| `_ANSWER_ORDER` vs `AnswerStatus` | `_ANSWER_ORDER` is an internal 10-entry **ranking** tuple while the `AnswerStatus` enum holds **15** values. This is a design distinction, not an inconsistency, and it is preserved |
| `completeness_score` | Two unrelated notions (organisation-profile completeness vs extraction completeness). Recorded explicitly so a future data-quality package cannot conflate them (**D-14**) |
| `/carbon-reduction-plan` frontend route | A public page route exists but is **not** evidence of a reduction engine; the matrix does not treat it as family 19 capability |
| Question-Library count | Confirmed at **426** numbered questions; the matrix maps sections and representative questions rather than claiming a per-question percentage |
| INS-01 commit `f1a7cce` | Was local-only at the master preflight and is now published on the remote (an ancestor of the preflight report commit) |

---

# 7. Verification performed

| Verification | Method | Outcome |
| --- | --- | --- |
| All 19 families present | heading audit of the matrix | 19 of 19, each with the full required field set |
| Required final sections present | heading audit | all 17 required sections (§1–§17) plus a final-status block |
| Implementation-status claims anchored in code/history | the targeted reads listed in §2.3 | every non-trivial status claim verified |
| No future package described as implemented | review of §4 statuses and §9 (`APPROVE` ≠ authorization) | PASS |
| Unresolved PO decisions remain unresolved | review of §9.1–§9.2 and family 15 | PASS — family 15 records a **missing** decision instead of inventing one |
| E4 not claimed | review of §6 (E4 column) and §4 family 16 | PASS — E4 is “PO-defined” / “PO decision” throughout |
| Single evidence destination preserved | review of §6, §8.2 and §11 | PASS — no second viewer proposed |
| INS-01 untouched | `git status` / `git diff` review | PASS — no code, migration or test change |
| Only the two authorized files changed | staged-diff review before commit | PASS |
| No secrets in the new documents | pattern scan for credential / token / JWT / signed-URL shapes | PASS — no matches |
| Application tests | not applicable to this package | **none run, none modified** — stated so it is not mistaken for a passed suite |

---

# 8. Git state

| Item | Value |
| --- | --- |
| Baseline HEAD (task start) | `8916f82bb71dd8e3ef3050b4b1185507dd5b14cb` |
| Remote at task start | `github/p8-release-reconciled` = `8916f82bb71dd8e3ef3050b4b1185507dd5b14cb` |
| Alignment at task start | `0 0` |
| Working tree at task start | clean except the pre-existing untracked PO/ChatGPT documents |
| Files staged by P1 | the two documents named in §3, and nothing else |
| Untracked PO/ChatGPT documents | left untracked, per the authorization |

**Post-commit and post-push values** (P1 commit SHA, remote SHA, alignment, final working-tree status) are recorded in §9.

---

# 9. Push results

| Item | Value |
| --- | --- |
| P1 artifact commit | `9a521b06aecc624e15c7687e6384ebb3c75fcf42` |
| Commit subject | `docs(p8): PO Insight capability coverage matrix (P1, planning artifact only)` |
| Commit content | **2 files, 1,454 insertions, 0 deletions** — no code, migration, test, frontend or configuration |
| Branch pushed | `p8-release-reconciled` |
| Push target | `github/p8-release-reconciled` |
| Push result | `8916f82..9a521b0  p8-release-reconciled -> p8-release-reconciled` (accepted) |
| Remote SHA after push | `9a521b06aecc624e15c7687e6384ebb3c75fcf42` |
| `git ls-remote github refs/heads/p8-release-reconciled` | `9a521b06aecc624e15c7687e6384ebb3c75fcf42` |
| `git rev-parse HEAD` | `9a521b06aecc624e15c7687e6384ebb3c75fcf42` |
| Alignment after push | **`0 0`** |
| Both P1 files tracked | confirmed (`git ls-files`) |
| Untracked PO/ChatGPT documents | **still untracked** (`git ls-files` count for those paths = 0) |
| Working tree after push | pre-existing untracked PO/ChatGPT documents only; no tracked modification outstanding |
| Documentation follow-up | this Git-state record was itself committed as `fbe0adc544f5e4b8493a607b7ee8fcbafcb302eb` (`docs(p8): record P1 commit SHA and push result in the coverage-matrix implementation report`); at the time of writing, the remote tip was `fbe0adc544f5e4b8493a607b7ee8fcbafcb302eb` with alignment **`0 0`** and no other tracked change present |

**Summary of the P1 Git outcome:** two documentation-only commits (`9a521b0` carrying the matrix and this report; `fbe0adc` carrying this Git-state record), zero application-code, migration, schema, test, frontend or configuration changes, and `0 0` alignment with `github/p8-release-reconciled`.

---

# 10. Remaining work and constraints

* **P1 is complete as a planning artifact.** It authorizes nothing.
* **No P2–P12 package was started**, and none may start without a separate bounded PO authorization.
* **Items requiring PO action:** the decisions listed in matrix §9.1–§9.2; confirmation of the conflict register (§2.3 here / §2.3 there); and a **new decision** for methodology/boundary (family 15).
* **Carry-forward items remain unchanged and unremediated:** INS-01 closure §8.1–§8.8, the pre-existing test failures, the pre-existing factor-metadata exposure, the X2/X7 record divergence, and the `AGENTS.md` §54 path.
* **No production-readiness, certification or competitive claim** is made by either document.
* **F-046-1 reminder carried forward:** the integration harness performs destructive setup and may only ever target a disposable database — never the investor demo, persistent QA, or production.

---

**Report status: P1 COMPLETE — documentation-only. No application capability implemented, no migration created, no test modified, no deployment performed.**
