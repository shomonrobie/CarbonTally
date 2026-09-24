# CT-PO-P12-STEP1-DOCUMENTATION-RECONCILIATION-20260924

**Reference:** `CT-PO-P12-STEP1-DOCUMENTATION-RECONCILIATION-20260924`
**Date:** 2026-09-24
**Governing workplan:** `CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924` — **STEP 1 — Foundation & Forensics**, workstream **1.1**
**Status:** STEP-1 DELIVERABLE — reconciliation record (no implementation, no mutation)
**Scope:** Investor-demo readiness only. Production readiness is **not implied**.
**Production deployment:** **NOT AUTHORIZED**

---

## 0. Authorization boundary (restated)

This document was produced under the Step-1 boundary. Authorized: read-only
inspection, forensic analysis, documentation reconciliation, independent
verification, creation of reports/decision records. **Not** authorized and **not**
performed: Demo Lab reset, destructive database operations, production database
access or mutation, evidence backfill, new accounting methodology, mapping
fallback, billing implementation, L7/L8 implementation, production deployment.

No implementation was changed in order to make documentation agree. Where
documentation and code/data disagree, the **discrepancy is recorded** and the
authoritative evidence is identified.

---

## 1. Method and evidence labels

| Label | Meaning |
| --- | --- |
| `FACT` | Directly observed in the repository, database or command output; reproducible |
| `OBSERVATION` | Observed read-only; a state, not an interpretation |
| `VERIFIED` | Independently reproduced in this Step-1 session |
| `UNVERIFIED` | Asserted by a document; not reproduced in this session |
| `INFERENCE` | Reasoned conclusion from observations; never presented as fact |
| `RECOMMENDATION` | Proposed action (not performed) |
| `AUTHORIZATION REQUIRED` | Action outside the Step-1 boundary; PO decision needed |

**Anti-convenience rule applied:** where two records conflicted, neither was
silently chosen. Both are listed in §5 with the evidence that discriminates them
(or an explicit statement that the discrimination is unresolved).

---

## 2. Repository and environment ground truth

### 2.1 Git (`FACT`, `VERIFIED`)

| Item | Value |
| --- | --- |
| Expected repository | `/home/shomonrobie/ct_93d5cdd` |
| Actual repository inspected | `/home/shomonrobie/ct_93d5cdd` — **matches** |
| Branch | `p8-release-reconciled` — **matches the handoff expectation** |
| HEAD | `3c38cbc59c95c04ea434ae128f86c94fd4b69190` |
| HEAD subject | `docs(p12): product capability / investor-demo forensic study (planning artifact only)` |
| `github` remote | `https://github.com/shomonrobie/CarbonTally.git` |
| `origin` remote | `/tmp/ct_step2` (a **local filesystem path**, not GitHub) |
| `@{upstream}` | `93d5cddd56bb683a5bb97ccf3419c191ddc617f5` |
| `github/p8-release-reconciled` | `3c38cbc59c95c04ea434ae128f86c94fd4b69190` (**equals HEAD**) |
| Ahead / behind vs `@{upstream}` | **ahead 106, behind 0** |
| Working tree | 1 modified tracked file (`.gitignore`), 14 untracked paths |

**Difference from the handoff (`FACT`).** The handoff/planning baseline names
release `93d5cddd` on `p8-release-reconciled`. The working tree is **106 commits
beyond** that baseline. Those local-only commits are not stray edits: they carry
the entire `tools/demo_lab/` harness (P12 tooling), the six Insight migrations
(`20261001000000`–`20261007000000`), P2/P3 remediation and verification records,
and the recent P12 planning documents — 113 files / 27,437 insertions against
`@{upstream}`. The `github` remote-tracking ref equals HEAD, so the release branch
on GitHub is aligned with the inspected HEAD; the stale reference is the
local-path `origin`.

### 2.2 Pre-existing untracked PO / ChatGPT artifacts (`OBSERVATION`)

Untracked and **left untouched** by this task:

- `.costrict/`
- `costrict-p3-ov-01-independent-re-verification.txt`
- `docs/ChatGPT/CarbonTally_Incremental_ChatGPT_PO_History_2026-09-22.md`
- `docs/ChatGPT/CarbonTally_Incremental_Chat_History_2026-09-22.md`
- `docs/ChatGPT/CarbonTally_Incremental_Chat_History_2026-09-22-Insight-Strategy-v2.md`
- `docs/ChatGPT/carbontally_handoff.md`
- `docs/architecture/CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924.md` (the governing workplan — **untracked**)
- `docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22.md` and `…-v2.md`
- `docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md`
- `docs/architecture/CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md`
- `docs/architecture/CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md`
- two zero-byte stray files named `8` and `=`

**Consequence (`OBSERVATION`):** the governing workplan, the Insight architecture
reference, the Question Library, the INS-01 post-closure reconciliation and the
PO Insight Capability Decision Matrix are **not committed**. Only committed
reports are durable project record. This is the durability risk already flagged
as `D-27` / `X-5` in the P12 preflight §15 and is carried forward unchanged
(`AUTHORIZATION REQUIRED` — committing untracked PO artifacts is a PO decision,
not an agent decision).

### 2.3 Database environment (`OBSERVATION`, read-only)

Local Supabase Postgres instance: `127.0.0.1:54426` (container
`supabase_db_carbon_ledger`). Candidate demo environments:

| Database | Public tables | Role |
| --- | --- | --- |
| `carbontally_demo_local` | 136 | **Current Demo Lab** (DEMO-T1 / T2-C / T3 provision) |
| `postgres` | 116 | Historical flagship / investor-reference dataset |
| `carbontally_qa_phase8` | 133 | Persistent QA |
| `carbontally_test` | 117 | Dedicated integration-test database |

### 2.4 Service state (`OBSERVATION`)

| Endpoint | State |
| --- | --- |
| `127.0.0.1:54430` (Demo Lab gateway: `/auth/v1`, `/rest/v1`) | **listening** (`/auth/v1/health` → HTTP 200) |
| `127.0.0.1:8070` (release backend) | **NOT listening** (connection refused) |
| Demo Lab containers `carbontally_demo_lab_{gateway,storage,postgrest}` | present |

**Consequence (`INFERENCE`, high confidence):** the Demo Lab's own verification
harness (`tools/demo_lab/verify.py`, which performs password grants plus
**read-only** GET probes against the release API) **cannot be executed** in this
session because the release backend is not running. This is classified in the
Independent Workflow Verification report as an environment limitation, not a
product result.

---

## 3. Status vocabulary used (never interchangeably)

| Status | Meaning in this document |
| --- | --- |
| **IMPLEMENTED** | Code exists, is wired into the running composition root, and has tests |
| **INDEPENDENTLY VERIFIED** | A verifier other than the implementer reproduced the behaviour and recorded evidence |
| **PO CLOSED** | An explicit Product Owner closure record exists |
| **DEMO READY** | Demonstrable end-to-end from **live data in the selected demo environment today** |
| **PARTIAL** | Some real part works; a named part does not |
| **BLOCKED** | Cannot proceed without an external decision/authorization or without a missing environment capability |
| **NOT AUTHORIZED** | Explicitly outside current authorization |
| **UNKNOWN / NOT VERIFIED** | Not established by evidence in this session |

---

## 4. Capability reconciliation

Column meanings: **Doc claim** = what the record set asserts · **Code evidence** =
what the inspected release source actually contains · **Data/runtime evidence** =
what the databases actually contain (read-only) · **Reconciled** = Step-1 status.

### 4.1 Calculation, provenance and evidence

| Capability | Doc claim | Code evidence | Data / runtime evidence | Reconciled |
| --- | --- | --- | --- | --- |
| **Deterministic emissions calculation** | Implemented; server-authoritative; `Decimal` maths; immutable snapshots (WP §2; handoff §2.1) | `backend/services/automatic_processing.py::_calculate` / `_calculate_line`; `CalculationRequest`; engine returns `result.snapshot.id`, `result.snapshot.co2e_kg` (`CODE-TRACED`) | Demo Lab: `calculation_snapshots=1`, `emissions_logs=1` — `Natural gas`, `12181.4 kWh (Net CV)`, multiplier `0.2027`, **`2469.169780` kg CO₂e**, `direct_multiply`, `algorithm_version=v1.0`, `factor_source=DEFRA-DESNZ` (`DATABASE-OBSERVED`) | **IMPLEMENTED**, **INDEPENDENTLY VERIFIED** (P12 preflight DR-004 / prior verification), **DEMO READY (narrow: exactly one real record)** |
| **Calculation snapshots + provenance columns** | Snapshots carry `source_item_id`; factor provenance preserved (WP §2; AGENTS.md §17) | `calculation_snapshots` carries `factor_id, factor_source, factor_set, import_batch_id, reporting_year, factor_kind, customer_factor_id, request_id, content_hash, source_item_id, source_file, source_page, source_line_item_id` (`DATABASE-OBSERVED` — 28 columns) | Demo Lab snapshot: `source_item_id` **present**; `source_line_item_id` **NULL**; `source_page=3` | **PARTIAL** — `source_item_id` real; the **line-level** link (`source_line_item_id`) is NULL because no evidence line exists (see EV-01) |
| **`source_page` integrity** | `evidence.py` must never present an unverified page as an exact location (F-B2-7) | `domain/evidence.py::resolve_source_page` returns `PAGE_STATE_UNVERIFIED` for a snapshot-only page; the correction forbidding `page_count` landed in `999e4fb` (2026-09-22) (`CODE-TRACED`, `git blame`) | The Demo Lab snapshot was written **2026-09-20 17:32**, i.e. **before** the correction, with `source_page=3` = the document `page_count` (`3`, from queue metadata) (`DATABASE-OBSERVED`) | **IMPLEMENTED (code honest)**; the **stored value is a pre-correction page count** and is correctly classified unverified |
| **Source Evidence Viewer (backend)** | "Implemented / independently verified" (WP §10); route resolves an evidence line item | `backend/api/v3_evidence.py` — `GET /api/v3/evidence/line-items/{line_item_id}`; DM-6 exposure gate; audit-on-read; signed URL at FULL depth only (`CODE-TRACED`) | `evidence_line_items = **0**` in the Demo Lab; `disclosure_value_evidence = 0`; the Viewer therefore has **nothing to resolve** (`DATABASE-OBSERVED`) | **IMPLEMENTED**, **NOT DEMO READY** in the current environment |
| **Evidence-line materialisation** | B2 model exists; forward + backfill paths | Only two write paths exist: forward hook `ManualExtractionRepository._materialise_evidence_lines` → `EvidenceLineItemsRepository.materialise_for_item`; and the Class-1 backfill CLI `backend/tools/backfill_evidence_line_items.py`. Both derive lines **exclusively** from `extracted_data.line_items[]` (`domain/line_items.py::derive_line_candidates`); the module forbids fabricating a line for a flat document (`CODE-TRACED`) | **0 rows.** All 12 populated Demo Lab extraction items are **flat** (`activity, date, gross_amount, invoice_number, net_amount, quantity, supplier, unit`) with **no `line_items` key at all**; `jsonb_typeof(extracted_data->'line_items')` is NULL for every row (`DATABASE-OBSERVED`) | **IMPLEMENTED — INERT IN THIS ENVIRONMENT.** Forward hook yields 0 candidates; backfill has **0 eligible** items. Root cause: EV-01 report |
| **Insight evidence handoff** | Source Evidence Viewer ↔ Insight handoff implemented (`999e4fb`) | `services/insight_tools.py` exposes `report_evidence_lookup`, `calculation_snapshot_lookup`, discovery/aggregation/provenance with `reference_kinds` including `evidence_line_item` (`CODE-TRACED`) | Insight is **not runnable** in either candidate environment (no Insight tables — §4.4) | **IMPLEMENTED**, **BLOCKED** by schema (§4.4) |

### 4.2 Operational workflow planes

| Capability | Doc claim | Code evidence | Data / runtime evidence | Reconciled |
| --- | --- | --- | --- | --- |
| **Processing-entity (PE) workspace** | PE assignment/reassignment infrastructure exists; PE must see work assigned to its entity (WP §2; AGENTS.md §12) | `backend/api/v3_pe.py` — `/api/v3/pe/me`, `/work`, `/batches/{id}/items`, `items/{id}/{start,extract,map,validate,calculate,status,pe-review,pe-qc,clarify}`, `items/{id}/workspace`, and a work-lease block `items/{id}/work/{claim,release,complete}` (`CODE-TRACED`) | Demo Lab: `processing_entities=1`, but `work_item_assignments=0`, `processing_assignments=0`, `reassignment_history=0` → **no assigned work exists to display** (`DATABASE-OBSERVED`) | **IMPLEMENTED**, **NOT DEMO READY** (no assigned work data) |
| **Assignment / reassignment / release** | Assignment, reassignment, partial release must be verifiable (WP §1.2) | `backend/api/v3_operations.py` — `/api/v3/ops/items/{id}/work/{claim,assign,reassign,recover,release,complete}`; batch assignment `/api/v3/ops/batches/{id}/assign`; storage table `public.work_item_assignments` maintained in `data/manual_extraction.py` (lease + reassignment + recovery) (`CODE-TRACED`) | Demo Lab `work_item_assignments = 0`; `postgres` = **2** rows. Assignment covers **internal Operations/PE staff**, not customer users (`DATABASE-OBSERVED`) | **IMPLEMENTED**, **UNVERIFIED END-TO-END**, **NOT DEMO READY** in the Demo Lab |
| **Review / QC workflow** | Review and approval are explicit stages (AGENTS.md §26) | `/api/v3/ops/items/{id}/{qc,submit-review}`, `/api/v3/ops/qc/ct-queue`, `/api/v3/ops/qc/items/{id}/decision`, `/api/v3/ops/queues/{operator,review,qc}`, `/api/v3/pe/items/{id}/{pe-review,pe-qc}` (`CODE-TRACED`) | Demo Lab extraction states are `pending (2)`, `extracted (11)`, `calculated (1)` — **no review/QC state is populated**. `postgres` shows a full spread: `pending 162, approved 30, extracted 29, calculated 14, mapped 12, validated 10, rejected 3, extracting 2, mapping 1, qc_approved 1` (`DATABASE-OBSERVED`) | **IMPLEMENTED**, **UNVERIFIED END-TO-END**, **NOT DEMO READY** in the Demo Lab |
| **Messaging (two planes)** | Two messaging planes: customer/consultant↔client and PE operational (WP §2; handoff §2.1) | `backend/api/v3_messaging.py`: (a) organisation conversations `/api/v3/messaging/conversations*` — org members + consultant firm members holding an **ACTIVE** grant (D15), optional server-resolved `support` counterparty (internal staff with `can_manage_staff`); (b) **PE operational** conversations `/api/v3/messaging/entity-conversations*` — PE members of their own **ACTIVE** entity ↔ authorised CarbonTally Operations. There is **no customer↔PE plane** (D18 boundary absolute) (`CODE-TRACED`) | Demo Lab: `conversations=0`, `messages=0`, `conversation_participants=0` → **no conversation can be displayed**. `postgres`: `conversations=36` (`org 35`, `entity 1`), `messages=54`, participants 65 (`DATABASE-OBSERVED`) | **IMPLEMENTED**, **NOT DEMO READY** in the Demo Lab; **no customer↔PE messaging exists by design** |
| **Messaging documentation internal conflict** | — | The module docstring states "General employees and **Processing Entity staff never get messaging access** … RLS has no entity messaging storey — the D18 boundary is absolute", yet the same module implements PE operational messaging for active PE members (`_resolve_entity_actor` returns `("pe", entity_id)`) and migration `20260902040000_phase5_pe_operational_messaging.sql` exists (`CODE-TRACED`) | — | **CONFIRMED DIVERGENCE (D-09)** — docstring vs implementation in the same file |
| **Reporting lifecycle** | Report lifecycle implemented; must be exercised for the demo (WP §10; handoff §2.1) | `backend/api/v3_reports.py` — `DRAFT → REVIEWED → APPROVED → FINAL`, with `CHANGES_REQUESTED` / `REJECTED`, server-side guards, and `submit / request-changes / reject / approve / finalize` routes; `backend/tests/integration/test_report_lifecycle.py` covers draft default, expected-state-only transition, per-report isolation, unratified-status rejection, and `FINAL` terminality (`CODE-TRACED`) | Demo Lab: `report_versions = 2`, **both `DRAFT`**; `report_generation_queue = 3` (`completed`). `postgres`: `report_versions = 17`, **all `DRAFT`**; queue `completed 11 / failed 2 / pending 1` → **no non-DRAFT lifecycle state exists anywhere** (`DATABASE-OBSERVED`) | **IMPLEMENTED**, **NOT DEMO READY** (no reviewed/approved/final version exists in any candidate environment) |
| **Consultant/client relationship** | Consultants are first-class operators; a consultant-client relationship is explicit; cross-consultant access denied (AGENTS.md §10/§11) | `backend/api/v3_consultants.py`; `api/consultant_auth.py::ensure_consultant_org_access`; `consultant_firm_members`, `consultant_clients`; grants carry an ACTIVE state (D15) (`CODE-TRACED`) | Demo Lab: `organizations=4` (Org A, Org B, Client A, Client B); `consultant_firm_members=2`; `organization_members=8` (`DATABASE-OBSERVED`) | **IMPLEMENTED**; last recorded harness run shows **0/18 isolation-rule failures** (see IWV report §7) — **INDEPENDENTLY VERIFIED at that time**, but **not re-verified in this session** |
| **Master-data CRUD (facilities / assets / suppliers / vehicles)** | D17 master-data architecture; CRUD with validation (AGENTS.md §34/§41) | `backend/api/v3_organizations.py`, `api/v3_suppliers.py`, `api/v3_vehicles.py` route families exist (`CODE-TRACED`) | Demo Lab: `facilities=0`, `assets=0`, `suppliers=0`. `postgres`: `facilities=157`, `assets=310`, `suppliers=156` (`DATABASE-OBSERVED`) | **IMPLEMENTED**, **UNVERIFIED END-TO-END**, **NOT DEMO READY** in the Demo Lab |

### 4.3 Insight, P2, P3 and the Demo Lab

| Capability | Doc claim | Code evidence | Data / runtime evidence | Reconciled |
| --- | --- | --- | --- | --- |
| **Insight foundation (INS-01)** | "CLOSED — IMPLEMENTED & INDEPENDENTLY VERIFIED" (INS-01 post-closure reconciliation §13; WP §10) | `backend/api/v3_insight*.py`, `services/insight_tools.py`, `insight_query_planner.py`, `insight_interactions.py`, `insight_rate_limit.py`; **10** `ToolDefinition`s registered (`CODE-TRACED`) | **0** `%insight%` tables in the Demo Lab; **0** in `postgres`; Insight tables exist only in disposable `ct_*` clones and `carbontally_test` (`DATABASE-OBSERVED`) | Code **IMPLEMENTED**, **PO CLOSED**; **DEMO READY = NO** in any candidate environment |
| **P2 — temporal comparison** | PO CLOSED (WP §10; handoff §2.1) | `TOOL_INSIGHT_TEMPORAL_COMPARISON` in `insight_tools.py`; migration `20261006000000_p8_insight_temporal_comparison.sql` (`CODE-TRACED`) | Migration **not applied** to the Demo Lab (built 19–20 Sep, before the `2026100*` migrations) (`DATABASE-OBSERVED`, `INFERENCE`) | **PO CLOSED**, **NOT DEMO READY** (schema absent) |
| **P3 — data quality / reproducibility** | P3-IV-01 CLOSED / independently verified and re-verified; **P3 overall NOT YET PO-CLOSED** (WP §10; handoff §2.1) | Migration `20261007000000_p8_insight_data_quality_reproducibility.sql`; remediation `8554b78`; re-verification `2be9033` (`CODE-TRACED`) | Migration **not applied** to the Demo Lab (`DATABASE-OBSERVED`) | **P3-IV-01 PO CLOSED**; **P3 overall PARTIAL / NOT PO-CLOSED**; **NOT DEMO READY**; P3 has **no UI renderer** (preflight §17.1 P12-05) |
| **Insight tool catalogue count** | The Insight Capability Coverage Matrix states "**seven** authorized tools (closed catalogue — no eighth tool exists or is implied)" | `TOOL_DEFINITIONS` now holds **10** entries (`grep -c 'ToolDefinition('` = 10) after P2/P3 added tools 8–10 (`VERIFIED`) | — | **CONFIRMED STALE DOCUMENT** (D-05) — matrix not updated after P2/P3 |
| **Insight answer states** | Matrix §7 records "15 answer states incl. `multiple_matches`" | `backend/domain/insight_interaction.py::AnswerStatus` enumerates exactly **15** values (14 specification states + `multiple_matches`) (`VERIFIED`) | — | **CONFIRMED ACCURATE** — matrix claim matches code |
| **Aggregation dimensions** | Matrix §3.2 approved **six** aggregation dimensions | Seven implemented (supplier added under the INS-01 authorization) — recorded as conflict `X-3` in the matrix itself (`UNVERIFIED` beyond the matrix's own record) | — | **PARTIAL / recorded divergence** (D-06) |
| **Demo Lab schema revision** | No document records the lab's schema revision (preflight §15) | `tools/demo_lab/stack.py` builds the schema from `supabase/migrations/*.sql` and reports `migration_files` / `migrations_with_errors`, but **persists no schema-revision record** (`CODE-TRACED`) | The Demo Lab has **136** public tables and **0** Insight tables, i.e. a pre-`2026100*` provision (`DATABASE-OBSERVED`) | **CONFIRMED** — no lab schema-revision record exists (D-08) |
| **Demo Lab harness** | `tools/demo_lab/` is the P12 demo tooling; last independent verification of the T3 harness returned **FAIL**; post-remediation re-verification **has no record** (preflight §15 / §18.2 B5) | `lab.py`, `stack.py`, `provision.py`, `storage.py`, `seed_factors.py`, `t3_scenarios.py`, `t3_manifest.json`, `verify.py`, `run_demo_lab.sh`, `reset_demo_lab.sh` all present (`CODE-TRACED`) | State dir `$HOME/ct_local_env/demo_lab` present (`backend.env`, `credentials.local.json`, `corpus/t3-uk-curated-v1`, 14 `verify_*.json` runs); **last run 2026-09-20 21:29Z: `contexts 13/failed 0`, `probes 30/failed 0`, `isolation_rules 18/failed 0`, `known_product_defects []`, database `carbontally_demo_local`** (`OBSERVATION`) | Harness **PRESENT and previously usable**; **NOT RE-EXERCISED in this session** (release backend not running) — see IWV report §7 |
| **T3 corpus ground truth** | Corpus contract yields 2/11 successful mappings; `snapshot_present 0` | `tools/demo_lab/t3_manifest.json` declares **11** scenarios; generator pin `8ade2bf778d518d59924905849ab114ab2d0820a` — **matches the workplan §2 pin exactly** (`VERIFIED`) | `evidence/t3_ground_truth_latest.json`: `compared 10`, `activity_match 9`, `quantity_match 5`, `unit_match 5`, **`snapshot_present 0`**, `skipped 1` (`OBSERVATION`) | **PARTIAL** — the corpus does **not** produce calculations (consistent with 13/14 documents blocked in `manual_review`) |

### 4.4 Divergences carried in from the P12 preflight (re-checked read-only)

**None was resolved by changing either side.**

| Preflight ID | Divergence | Step-1 re-check | Status |
| --- | --- | --- | --- |
| **X-5 / D-27** | `AGENTS.md` §54 names `tools/seed_investor_demo/DEMO_IDENTITIES.md` (~50 orgs, 911 consultant-client owners, **1,185 identities**). That directory is absent; the real manifest is `tools/demo_lab/manifest.json` (**13 actors**) | `tools/` contains no `seed_investor_demo`; Demo Lab orgs = **4**, users = **13** (`VERIFIED`) | **CONFIRMED — PO DECISION REQUIRED** |
| **X-5 corollary** | Identity domains differ: `@demo-lab.carbontally.local` (lab) vs `@demo.carbontally.local` (documented 1,185-identity dataset) | README §3 states the lab domain; `carbontally_demo_local` users = 13 | **CONFIRMED — PO DECISION REQUIRED** (which dataset the demo uses) |
| **X-3 / D-28** | X2 alerting and X7 metrics **contract records** say "IMPLEMENTATION BLOCKED / PO DECISION REQUIRED" while implementation, tests and wiring exist | X2 contract line 6: *"CONTRACT PRODUCED — OPEN PO CHOICES — IMPLEMENTATION BLOCKED AT THE `PX-6` GATE"*; X7 contract line 5: *"CONTRACT PREPARED — IMPLEMENTATION BLOCKED: PO DECISION REQUIRED"*, line 101: *"X7 is BLOCKED at the contract stage. No X7 code was written…"* — **yet** `backend/services/operational_alerting.py` and `backend/services/api_metrics.py` both exist, `api_metrics` is imported and used by `api/router.py` middleware, and `tests/integration/test_operational_alerting_x2_runtime.py` + `test_api_metrics_x7_runtime.py` exist (`VERIFIED`) | **CONFIRMED — PO DECISION REQUIRED** (contract records are stale relative to code) |
| **Matrix family statuses** | Matrix §4 lists family 11 (Temporal Comparison) and family 14 (Data Quality) as **MISSING**; both are now implemented | P2 closed; P3 implemented + independently verified; migrations `20261006000000` / `20261007000000` exist (`VERIFIED`) | **CONFIRMED — point-in-time planning artifact** |
| **Preflight staleness** | Master preflight §9.4 lists temporal comparison among the truthful limitations; §17.1's demo gate omits temporal comparison and data quality | Both now implemented (above) | **CONFIRMED — the P12 gate must add them** |
| **T3 record inconsistency** | T3 REM-001 ends "IMPLEMENTATION BLOCKED — PO REVIEW REQUIRED" while `t3_manifest.json` encodes a later reconciliation | `t3_manifest.json` **does** contain `_rem001_reconciliation` (`authorization, generator_pin, authorized_substitutions, established_no_viable_candidate, unchanged_by_decision, boundaries`) (`VERIFIED`); no single authoritative T3 status record exists | **CONFIRMED — no single authoritative T3 status record** |
| **T3 verification status** | The only independent verification of the demo harness (OHD-079) returned FAIL; post-remediation re-verification has no record | No new verification record found (`UNVERIFIED` / absent) | **CONFIRMED — release-relevant, unresolved** |
| **`reports` table naming** | DR records speak of "report" rows; no table `reports` / `report_instances` exists | Present: `report_versions`, `report_comments`, `report_generation_queue`, `report_version_artifacts`, `report_templates`, `disclosure_report_*` (`VERIFIED`) | **Informational — no action** |
| **`evidence_line_items` absent in the flagship dataset** | *New in Step 1 — not previously recorded* | `postgres` (975 orgs, 100 snapshots) has **no `public.evidence_line_items` table at all** (`VERIFIED`) | **NEW CONFIRMED DIVERGENCE (D-03)** — the flagship dataset cannot satisfy the evidence chain under any workflow |

---

## 5. Divergence register (consolidated)

| ID | Divergence | Authoritative evidence | Class |
| --- | --- | --- | --- |
| **D-01** | `evidence_line_items = 0` is **not** a missing-hook problem: the forward hook exists and fires; the **payload never carries `line_items[]`**, so zero candidates are derivable and the backfill has zero eligible items | `domain/line_items.py::derive_line_candidates`; `data/manual_extraction.py::_materialise_evidence_lines`; `DATABASE-OBSERVED` (all 12 populated items flat; `jsonb_typeof(…->'line_items')` NULL) | **RESOLVED by EV-01** (was `UNKNOWN` in preflight §10) |
| **D-02** | The Demo Lab was provisioned **before** the six Insight migrations, so it has **0** `%insight%` tables and no Insight route can execute | `DATABASE-OBSERVED` (136 public tables, 0 matching `%insight%`); migrations `20261001000000`–`20261007000000` | CONFIRMED (preflight B1) |
| **D-03** | The historical flagship dataset `postgres` has **no `evidence_line_items` table** — the evidence chain is structurally impossible there | `DATABASE-OBSERVED` (relation absent; query error) | **NEW** |
| **D-04** | **No** non-disposable local database carries the Insight tables: `postgres` 0, `carbontally_demo_local` 0, `carbontally_qa_phase8` 0; only disposable `ct_*` clones + `carbontally_test` do | per-database scan of 60 databases (`VERIFIED`) | **NEW** |
| **D-05** | Insight Capability Coverage Matrix says "seven authorized tools"; the registry holds **10** | `grep -c 'ToolDefinition(' backend/services/insight_tools.py` = 10 | CONFIRMED (preflight) |
| **D-06** | Matrix §3.2 approved six aggregation dimensions; seven implemented | matrix's own conflict `X-3` | Recorded (preflight) |
| **D-07** | **No** candidate environment contains a non-`DRAFT` report version, so no reviewed/approved/final report state can be shown | `report_versions`: Demo Lab 2 × `DRAFT`; `postgres` 17 × `DRAFT` | **NEW** |
| **D-08** | No persisted Demo Lab schema-revision record exists | `tools/demo_lab/stack.py` writes counts but no revision record | CONFIRMED (preflight) |
| **D-09** | `backend/api/v3_messaging.py` docstring says PE staff "never get messaging access", while the same file implements PE operational messaging for active PE members | file §1–13 vs `/entity-conversations` routes and `_resolve_entity_actor` | **NEW** |
| **D-10** | X2/X7 contract records say "IMPLEMENTATION BLOCKED / PO DECISION REQUIRED" while implementation, wiring and integration tests exist | contract lines 6 / 5 / 101 vs `services/operational_alerting.py`, `services/api_metrics.py`, `api/router.py`, integration tests | CONFIRMED (preflight X-3/D-28) |
| **D-11** | `AGENTS.md` §54 documents a 1,185-identity investor-demo dataset (`tools/seed_investor_demo/DEMO_IDENTITIES.md`) that **does not exist** in this checkout; the real Demo Lab manifest has **13 actors / 4 organisations** | `ls tools/`; `organizations=4`, `users=13` | CONFIRMED (preflight X-5/D-27) |
| **D-12** | No single authoritative T3 status record; the only independent harness verification (OHD-079) was **FAIL** and the post-remediation re-verification record does not exist | T3 REM-001 §8/§22 vs `t3_manifest.json::_rem001_reconciliation`; no verification report found | CONFIRMED (preflight) |
| **D-13** | The Demo Lab's single snapshot carries `source_page = 3`, i.e. the document **page count**, written by the pre-`F-B2-7` code path; current code correctly classifies such a page as `unverified` and refuses to present it | `git blame` (`999e4fb`, 2026-09-22) vs snapshot `calculated_at` 2026-09-20 17:32; `domain/evidence.py::resolve_source_page` | **NEW** (data staleness, honestly handled by current code) |
| **D-14** | Release identity is ambiguous: the working tree is **106 commits ahead** of `origin/p8-release-reconciled` (`93d5cddd`, a local `/tmp/ct_step2` path) while `github/p8-release-reconciled` equals HEAD | `git rev-list --left-right --count`; `git rev-parse github/…` | **NEW** (reference hygiene) |
| **D-15** | Two unit-test expectations are stale relative to the current release (a route-registration test targets the pre-refactor composition root; a migration-count assertion expects 71 files where 81 exist) — **pre-existing, unrelated to the investor-demo workflows** | `tests/unit/api/test_review_sla_surfaces.py` (`_paths()` = `{'/api/v2/health'}`); `tests/unit/data/test_d17_provider_ownership_migration_revision.py:264` (`assert len(names) == 71`, actual 81) | **NEW** (test-record divergence) |

---

## 6. What Step 1 actually advanced

1. **`UNKNOWN` → root cause (`D-01`).** The preflight (§10) explicitly left "whether the
   pipeline *should* have produced an `evidence_line_items` row" as `UNKNOWN`
   read-only. Step 1 traced the complete code and data path and established the
   cause conclusively (see the EV-01 report). This is the largest single
   uncertainty removed by Step 1.
2. **Confirmed the Insight-layer environment blockers with fresh evidence**
   (`D-02`, `D-04`) — and additionally established that the **flagship dataset is
   not a viable Insight host either** and **cannot host the evidence chain at all**
   (`D-03`).
3. **Verified two documentation claims as accurate** — the 15 `AnswerStatus`
   values and the generator pin `8ade2bf…`. Reconciliation is not only about
   finding errors.
4. **Re-verified every preflight divergence read-only**, resolving none by editing
   code or documentation.

---

## 7. What was not changed

- No application, frontend, backend, database, migration, RLS or seed data was modified.
- No Demo Lab reset/reseed/provision was performed; no row was inserted, updated or deleted.
- No documentation was rewritten to match code, and no code was changed to match documentation.
- No test was modified to obtain a green result.
- No untracked pre-existing artifact was committed, moved or deleted.

---

## 8. Residual `UNKNOWN` after this workstream

| Item | Why still unknown | How it would be resolved |
| --- | --- | --- |
| Whether `tools/demo_lab/stack.py` applies **missing** migrations to an **existing** lab DB (or requires reset + rebuild) | Deciding this requires either reading the code path fully against a live lab (a mutation-adjacent action) or a PO-authorized lab operation | Step 2 (P12-01) |
| Whether `verify.py` still passes against the current release (the last green run was 2026-09-20, before later local-only commits) | The release backend is not running; starting it / running the harness is a live-environment action | Step 2 / separately authorized verification |
| Whether the T3 corpus can be **re-synced** (`/tmp/extgen` checkout at the pinned commit) | The pinned generator checkout is absent from this machine | Step 2 (P12-12) |
| Whether the Demo Lab's audited identity/authorization behaviour still matches the last recorded harness evidence | Re-running `verify.py` requires the release backend | Step 2 / separately authorized verification |
| Whether `postgres` (flagship) could be migrated in place to add the missing B2/Insight tables | Not investigated: mutating that dataset is explicitly protected | PO decision + separate authorization |

---

## 9. Verdict

**Documentation reconciliation: PARTIAL — complete for the capabilities required by
the frozen Step-1 scope; two records remain unresolved because they are PO
decisions, not technical reconciliations (D-10, D-11), and one is a missing
independent verification record (D-12).**

- 15 capability rows reconciled with code + data evidence (§4.1–§4.3).
- 9 preflight divergences re-verified (§4.4) + 11 new/consolidated divergences
  registered (§5, D-01…D-15).
- Net effect for the investor-demo plan: the **calculation** capability is real and
  demonstrable; **provenance** is real at document level but **not** at line level;
  **evidence**, **Insight**, **P2**, **P3**, **messaging**, **report lifecycle**,
  **PE workflow** and **master data** are all **implemented but not demonstrable in
  either candidate environment today** without the Step-2 environment work.
