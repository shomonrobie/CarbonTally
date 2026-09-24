# CT-PO-P12-STEP1-DECISION-20260924

**Reference:** `CT-PO-P12-STEP1-DECISION-20260924`
**Date:** 2026-09-24
**Governing workplan:** `CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924` — **STEP 1 — Foundation & Forensics**
**Repository:** `/home/shomonrobie/ct_93d5cdd` @ `3c38cbc59c95c04ea434ae128f86c94fd4b69190`, branch `p8-release-reconciled`
**Status:** STEP-1 EXIT / DECISION RECORD — **awaiting PO decision**
**Production deployment:** **NOT AUTHORIZED**
**Investor-demo readiness claimed:** **NO** (Step 1 is not the investor-readiness gate)

---

## 0. Purpose and companions

This record closes Step 1 by answering the 20 required questions with
evidence-backed answers and by stating the exact PO decision now required. It
deliberately does **not** declare investor-demo readiness and does **not** authorize
Step 2.

Companion Step-1 artifacts:

- `CT-PO-P12-STEP1-DOCUMENTATION-RECONCILIATION-20260924.md`
- `CT-PO-P12-STEP1-WORKFLOW-INDEPENDENT-VERIFICATION-20260924.md`
- `CT-PO-P12-STEP1-EV01-EVIDENCE-LINE-FORENSIC-DESIGN-20260924.md`
- `CT-PO-P12-STEP1-FROZEN-INVESTOR-DEMO-SCOPE-20260924.md`
- `CT-PO-P12-STEP1-IMPLEMENTATION-REPORT-20260924.md`

---

## 1. What is actually implemented?

**Answer.** Substantially more than is demonstrable. Code-verified as implemented
and wired: deterministic emissions calculation; immutable calculation snapshots with
factor provenance; the B2 evidence-line model (forward hook + Class-1 backfill) and
the shared Source Evidence Viewer backend; PE workspace, assignment/reassignment/
lease/release, review and QC routes; two messaging planes (organisation and
PE-operational) with server-side participant resolution; the reporting lifecycle
state machine (`DRAFT → REVIEWED → APPROVED → FINAL`); consultant/client grants;
master-data CRUD; the Insight foundation with a **10-tool** closed catalogue and
**15** answer states; the P2 temporal-comparison tool; the P3
data-quality/reproducibility tool; X2 alerting and X7 runtime metrics (implemented
and wired although their contracts say "BLOCKED"); and the `tools/demo_lab/` harness.

## 2. What is independently verified?

**Answer.** Verified **in this Step-1 session**: route surfaces, authorization and
guard wiring, persistence models, the reporting state machine and its integration
test coverage, the B2 derivation rule, the Insight tool/answer-state counts, the
generator pin, and the persisted state of all four candidate databases. Unit suite:
**3220 tests, 4 failed (pre-existing stale fixtures), 8 skipped, 0 errors**.

**Historical, not re-verified this session:** the last Demo Lab harness run
(2026-09-20 21:29Z) reported 13/13 actor contexts, 30/30 authorization probes and
18/18 isolation rules with **0 failures** — an `OBSERVATION`, not a re-verification.

**Not verified:** every end-to-end workflow (see Q14).

## 3. What is PO-closed?

**Answer.** P2 (temporal comparison) — closed, with a permanent closure record.
INS-01 (Insight foundation) — closed ("implemented & independently verified", with
accepted non-blocking observations). P3-**IV-01** — closed and independently
re-verified. **P3 overall is NOT PO-closed.**

## 4. What is investor-demo-ready?

**Answer.** **Only Story A, and only partially, and only at document-level
provenance.** Concretely: one real end-to-end calculation
(`12181.4 kWh × 0.2027 = 2469.169780 kg CO₂e`, `DEFRA-DESNZ`, `direct_multiply`,
`v1.0`) with a real snapshot, a real emissions log and document-level provenance;
plus document-level honest failures with real persisted reasons (four distinct
classes). Everything else is implemented but **not** demonstrable from the current
environment's data.

## 5. What remains partial?

**Answer.**

- **Provenance** — real at document level (`source_item_id`), absent at line level
  (`source_line_item_id = NULL`).
- **Source Evidence Viewer** — implemented; zero rows to resolve.
- **P3** — implemented and partly verified; P3 overall not PO-closed; no UI renderer.
- **Evidence-line materialisation** — implemented but inert in this environment.
- **Consultant/client** — model and topology verified; behaviour not exercised.
- **Authorization/isolation** — last recorded run clean; not re-run; F-T1-001 status
  unknown.
- **Reporting lifecycle** — state machine and its tests exist; only `DRAFT` versions
  exist anywhere.
- **Story A** — 1 real record where ≥ 2 are wanted.

## 6. What is blocked?

**Answer.**

| Blocker | Nature |
| --- | --- |
| Demo Lab schema is a pre-Insight provision (**0** `%insight%` tables) | environment / engineering |
| **No** candidate environment has the Insight tables (not even the flagship dataset) | environment |
| Flagship `postgres` dataset has **no** `evidence_line_items` table | environment / schema divergence |
| Near-empty demonstrable population (1 snapshot, 1 emissions log, 0 evidence lines, 13/14 documents blocked, 0 assignments, 0 conversations, 0 master data, all report versions `DRAFT`) | environment / data |
| Evidence lines cannot be derived from any existing payload (all flat; P1 `shadow`) | configuration + corpus selection |
| Corpus cannot be re-synced (`/tmp/extgen` pinned checkout absent) | tooling |
| Harness usability against the current HEAD not proven | environment verification |
| Release-identity ambiguity (local branch 106 commits ahead of the referenced baseline) | reference hygiene |
| No single authoritative T3 status record; harness re-verification record missing | verification governance |

## 7. What is not authorized?

**Answer.** Unchanged from the workplan: Demo Lab reset; reseed mutation; destructive
database operations; production database access or mutation; evidence backfill; new
accounting methodology; mapping fallback; billing implementation; L7/L8
implementation; production deployment; unrelated roadmap work; full Scope 3;
market-based Scope 2; supplier intelligence; reduction/decision intelligence;
unrestricted natural-language querying; RAG; general UI/product expansion.
Additionally not authorized by Step 1: committing the untracked PO artifacts
(D-27), resolving the X-3/X-5-style business conflicts, fixing the D-09 messaging
docstring, and enabling the P1 `enabled` extraction shape.

## 8. What genuine product defects were discovered?

**Answer.** **None.** No Step-1 finding is attributable to incorrect application
behaviour:

- Zero `evidence_line_items` is **contract-compliant behaviour** (the derivation rule
  must not fabricate a line for a flat document).
- The stale `source_page = 3` is correctly classified `unverified` by current code.
- The 4 unit-test failures are stale test fixtures, not product behaviour.
- **F-T1-001** (`/api/v3/reporting/audit-activity` → HTTP 500 for an authorised
  owner) remains **pre-existing and un-re-verified**; it is recorded as `UNKNOWN`
  (the API could not be called; no fix was inspected).

## 9. What are merely demo-environment/data problems?

**Answer.** The majority: the pre-Insight Demo Lab schema (D-02); the empty
population (assignments, conversations, master data); the flat payloads caused by
P1 `shadow` (D-01); the absent pinned generator checkout; the `DRAFT`-only report
versions (D-07); and the missing `evidence_line_items` in the flagship dataset
(D-03). Also documentation/test-record staleness: D-05, D-06, D-08, D-10, D-11,
D-12, D-15, and the release-identity ambiguity D-14.

## 10. What is the root cause of the evidence-line problem?

**Answer (EV-01, `COMPLETE`).** Evidence lines are derived **exclusively** from
`manual_extraction_items.extracted_data.line_items[]`. Every document processed in
the Demo Lab was a **PDF** processed under the default **`shadow`** extraction-shape
mode, so the P1 classifier's finding *(multi-line suspect, 2 candidate lines)* was
recorded in metadata but the shaped output was **deliberately withheld**. The
persisted payload was therefore flat (keys: `activity, date, gross_amount,
invoice_number, net_amount, quantity, supplier, unit` — **no** `line_items`), the
derivation rule correctly produced **zero candidates**, and both the forward hook and
the Class-1 backfill inserted nothing. Contributing causes: (a) the seeded corpus
contains **no CSV/XLSX** document, so the only unconditional `line_items[]`
producers were never exercised; (b) the flagship `postgres` dataset has no
`evidence_line_items` table at all. **Not** caused by a missing hook, a missing
linkage, or a Demo Lab schema mismatch.

## 11. What exact evidence chain can currently be demonstrated?

**Answer.**

```text
Source document (uk-gas PDF, Org 3fd0f325…)
  → extracted flat activity data (Natural gas, 12181.4, kWh (Net CV))
  → mapped factor (b9d1ed06…, DEFRA-DESNZ / DEFRA-2025)
  → validation (passed)
  → deterministic calculation (direct_multiply, v1.0, content_hash, request_id)
  → calculation snapshot (af640887…)
  → emissions result (2469.169780 kg CO₂e, Scope 1, 2025-05-05)
  → document-level provenance (source_item_id, source_file, factor_id)
```

**This chain is real and fully traceable at document level. It has no per-line and
no Insight link.** The demo script must state exactly that (frozen wording in the
Frozen Scope §3.2).

## 12. What evidence chain still requires implementation?

**Answer.** Steps 3→4→11→13 of the EV-01 path trace, plus link 14:

| # | Missing link | Minimum safe remediation (RECOMMENDATION, not authorized) |
| --- | --- | --- |
| 3 | `extracted_data.line_items[]` | Seed ≥ 1 genuinely **tabular** (CSV/XLSX) document through the real pipeline (EV-01 Option A) — no code change |
| 4 | `evidence_line_items` rows | follows automatically from the forward hook once link 3 exists |
| 11 | `calculation_snapshots.source_line_item_id` | follows automatically from the calculation-time ordinal lookup |
| 13 | Source Evidence Viewer | becomes resolvable once links 3–11 exist |
| 14 | Insight explanation | apply the six `2026100*` Insight migrations to the demo environment |

**Rejected:** deriving lines from flat payloads; direct SQL inserts; running the
backfill (0 eligible items). See EV-01 §E.4.

## 13. What exact workflows can be demonstrated?

**Answer.** From real records, today:

1. **Document → calculation → emissions** (one document: the `uk-gas` PDF, fully
   processed to `customer_review`). **YES.**
2. **Document → honest block with a specific reason → human action route**
   (four classes, each with a real persisted `manual_review_reason` value). **YES.**
3. **Document-level provenance inspection** (factor, factor set, methodology,
   algorithm version, content hash, request id, source item/file). **YES.**

Frozen for Step 2 (not yet demonstrable): assignment/reassignment/partial release;
PE workspace; messaging (either plane); report approval/finalisation; master-data
CRUD; per-line evidence; the Source Evidence Viewer; Insight; P2; P3.

## 14. What workflows failed or remain unverified?

**Answer.** **Failed:** none (no workflow produced an incorrect or unexpected
result; none was exercised). **Unverified — 11:** PE assignment; reassignment;
partial release; PE workspace visibility; messaging (both planes, including live
delivery); report review/approval/finalisation; consultant operating a client
workspace; master-data CRUD; Insight (all questions); P2; P3; Source Evidence
Viewer; and the cross-tenant DENY matrix (code-verified only; last recorded harness
run clean but not re-run). Verification was limited by the release backend being
down and by the Step-1 read-only boundary — **not** by evidence of a defect.

## 15. What exact four investor stories are frozen?

**Answer.**

| Story | Frozen as | Today |
| --- | --- | --- |
| **A — Normal calculation** | Upload → extraction → mapping → validation → calculation → emissions result, anchored on the real `uk-gas` record; ≥ 2 matched calculations after Step 2 | **Mostly demonstrable** |
| **B — Operational workflow** | Work item → processing entity → assignment/reassignment → review/approval, explicitly bounded as **internal Operations ↔ PE** (no customer assignment, no customer↔PE messaging) | **Requires Step 2** |
| **C — Explainability** | Emissions number → snapshot → factor → source document (**real**), then evidence → Insight (**requires Step 2**), with mandatory disclosure of the missing last mile | **Document-level only** |
| **D — Honest failure** | Ambiguous mapping (primary) + insufficient-data completeness gate (second beat); unsupported/no-text as fallback; Insight no-data requires Step 2 | **Demonstrable** |

## 16. What data/entities/states are required for Step 2?

**Answer (full detail in Frozen Scope §7).** Canonical environment = the Demo Lab on
the current release migration set **including all six `2026100*` migrations**, with a
persisted schema-revision record; **2** direct orgs, **1** consultant firm,
**2** client orgs, **2** processing entities, PE manager + PE staff, internal
operator/reviewer/QC/staff-admin; relationships (org, consultant↔client,
PE↔work); `~3` batches and `~12–15` work items across meaningful states;
**≥ 2** matched calculations; **≥ 2** blocked documents with real reasons;
**≥ 1 tabular document** producing `line_items[]`; **≥ 2** `evidence_line_items`
linked to snapshots; **≥ 4** assignments incl. reassignment and partial release;
**2** report versions in **different** lifecycle states; conversations covering both
messaging planes; **2** Insight interactions + **1** honest no-data case;
**≥ 1** facility, asset and supplier; two-period Scope-1 data if P2 is shown.
Counts are planning targets, not fixed counts.

## 17. What security DENY cases are required?

**Answer.** S-1…S-13 as frozen in the Frozen Scope §6: Org A→Org B; Client A→Client
B; consultant→ungranted org; PE Alpha→PE Beta; PE→customer document/evidence;
customer→PE plane; customer→internal ops; viewer→write; member→owner/admin surface;
customer→admin control plane; tenant→another tenant's Insight; evidence read below
FULL depth → restricted (withheld, not nulled). **S-4 is a required ALLOW positive
control.** Every unexpected ALLOW is a serious security finding and must be recorded
as such by the Step-4 verifier.

## 18. What must be implemented before Step 3?

**Answer.** (All `AUTHORIZATION REQUIRED`.)

1. Resolve the **release-identity ambiguity** (D-14) and freeze the exact release
   commit for Step 2.
2. Re-provision/align the Demo Lab to the **current release migration state**
   (including the six Insight migrations) and persist a schema-revision record.
3. Restore the **pinned generator checkout** (`8ade2bf…`) so the corpus can be
   re-synced.
4. Seed the frozen topology, including a **tabular document** (or a scoped P1
   rollout decision) to unlock `evidence_line_items`.
5. Create **assignment/reassignment/release** state for Story B.
6. Create **report versions in non-`DRAFT` states** for the reporting beat.
7. Create **conversations** in both messaging planes.
8. Create **master data** so CRUD and relationships are visible.
9. Apply the Insight schema and verify the Insight tools operate against the seeded
   data (including one honest no-data case).
10. Re-run the Demo Lab harness and the relevant integration suites against a
    **disposable clone** to obtain `RUNTIME-VERIFIED (EXERCISED)` evidence.
11. Obtain a **PO decision on the EV-01 options** and on the messaging-docstring,
    T3-record and X-2/X-3/X-5 documentation conflicts.

**No Step-3 (UI/experience) work may begin before Step 2 is independently verified.**

## 19. What remains outside scope?

**Answer.** Production readiness and deployment; audit/certification; full product
completion; all Scope 3 Categories 1–15; market-based Scope 2; Scope 1
decomposition; supplier intelligence; reduction/decision intelligence; variance
intelligence; billing completion; L7; L8; unrestricted natural-language querying;
RAG; any new evidence model or second viewer; and any general product/UI expansion.

## 20. Is Step 1 complete?

**Answer.**

```text
STEP 1 COMPLETE
```

Rationale: the five required deliverables exist; the four stories are frozen; the
required data entities and workflow states are known; the evidence requirements are
established and the root cause is proven; genuine code blockers are clearly
separated from demo-environment problems; and no unresolved critical uncertainty
would make a Step-2 reset unsafe — **provided** Q18 items 1 and 11 are decided
first.

**Not claimed:** `INVESTOR DEMO READY`. Step 1 is not the investor-readiness gate.

---

## 21. Exact recommended next PO decision

**DECISION REQUIRED — STEP 2 CANONICAL DEMO ENVIRONMENT.**

Questions the PO must answer, in order:

| # | Decision | Options |
| --- | --- | --- |
| **D-2-1** | Freeze the release commit for the demo | (a) `3c38cbc` (current HEAD, aligned with `github/p8-release-reconciled`); (b) a different commit/reference |
| **D-2-2** | Confirm the canonical environment | (a) Demo Lab `carbontally_demo_local` re-provisioned to current release schema **(recommended)**; (b) migrate the `postgres` flagship dataset instead (**not recommended** — it lacks the B2 table and would mutate a protected dataset); (c) create a fresh isolated environment |
| **D-2-3** | Accept the data-loss scope of the Demo Lab reset | The reset drops the lab DB and its current 4 orgs / 13 users / 14 documents / 1 calculation / 2 reports / 113 audit rows |
| **D-2-4** | Choose the EV-01 unlock | (a) **seed ≥ 1 genuinely tabular (CSV/XLSX) document** — no code change, no configuration change **(recommended)**; (b) enable the P1 controlled rollout (`CARBONTALLY_P1_EXTRACTION_SHAPE=enabled` + allowlist) for the demo organisation; (c) neither — then Story C must be presented as document-level only |
| **D-2-5** | Approve evidence-line materialisation via the real pipeline only | Must be explicit: no direct inserts, no backfill, no change to `derive_line_candidates` |
| **D-2-6** | Authorise re-provisioning the pinned generator checkout (`8ade2bf…`) | Needed for `sync-corpus` |
| **D-2-7** | Confirm the demo-scope counts (Frozen Scope §7) | Planning targets → frozen counts |
| **D-2-8** | Authorise the disposable-clone integration verification pass | Required for F-046-1 compliance and for `RUNTIME-VERIFIED (EXERCISED)` evidence |
| **D-2-9** | Decide the documentation conflicts | D-09 (messaging docstring), D-12 (T3 status), D-10 (X-2/X-3 contracts), D-11 (1,185-identity dataset) |
| **D-2-10** | Decide durability of the untracked PO artifacts (D-27) | Commit or explicitly leave untracked |

**Until the PO authorizes at least D-2-1…D-2-5, Step 2 must not begin.**

---

## 22. Final status

```text
STEP 1 COMPLETE
```

- No investor-demo readiness is claimed.
- No Step-2 action was taken.
- No Demo Lab mutation occurred.
- No implementation was performed.
- Production is unaffected and unauthorized.
