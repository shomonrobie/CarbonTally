# PO Closure Record — P2 Temporal Comparison

Date: 2026-09-23
Document type: **Permanent PO closure record** (not an implementation or verification report)
Repository: `/home/shomonrobie/ct_93d5cdd` · Branch: `p8-release-reconciled` · Remote: `github`

## 1. PO Closure Decision

```text
P2 — CLOSED — IMPLEMENTED & INDEPENDENTLY VERIFIED
```

P2 (Insight capability family 11 — Temporal Comparison) is closed on the basis of
the implementation record, the independent verification verdict `PASS`, and the
test-inventory reconciliation. Closure covers exactly the scope in §2 and nothing
beyond it (§8).

## 2. Scope Closed

P2 provides one bounded, read-only Insight capability,
`insight_temporal_comparison`, answering "how did emissions differ between these
two periods?" — and nothing else.

| Closed scope element | Closed definition |
| --- | --- |
| Bounded two-period comparison | exactly two explicit, inclusive calendar periods (`period_a_start/end`, `period_b_start/end`); both required |
| Absolute change | `absolute_change = period_B − period_A` (kg CO₂e), always available |
| Percentage change | `((period_B − period_A) / period_A) × 100`, reported only when the baseline is non-zero |
| Zero-baseline percentage | `percentage_change = null` with `percentage_change_available = false` and `percentage_basis = "zero_baseline"` — no division by zero, no fabricated figure |
| Empty period vs zero emissions | an empty population takes the dedicated `no_data` path; it is never presented as a comparison against zero |
| Approved grouping dimensions | `scope`, `activity`, `facility`, `asset` only. `month`/`year` are excluded (they bucket the comparison axis) and `supplier` is excluded (no write path populates `supplier_id`; D-09 gates it); an unsupported dimension is **rejected**, never silently ignored |
| Deterministic kg CO₂e basis | one deterministic basis; values computed in Python (`Decimal`), never by the provider |
| Bounded result size / date scope | bounded period inputs and bounded/grouped output with an explicit truncation flag |
| Provenance / evidence pathway | no second evidence system: the result names `insight_aggregate_provenance` with its exact period bounds and remains traceable through the existing Shared Source Evidence Viewer |

Explicitly **outside** the closed scope (unchanged and not authorized by this
record): causal explanation ("why did it change"), variance/attribution,
restatement history, Scope 3 taxonomy, market-based Scope 2, Scope 1
decomposition, supplier persistence, factor-history implementation, RAG.

## 3. Authorization Basis

* **PO P2 implementation authorization (2026-09-22)** — recorded verbatim in the P2
  implementation report: *"Authorization: PO P2 implementation authorization
  (2026-09-22), bounded by the P1 capability coverage matrix
  (`CarbonTally_PO_Insight_Capability_Coverage_Matrix_2026-09-22.md`, family 11 /
  package P2)."*
* **The authorization fixes the comparison semantics itself** (two periods,
  `absolute = period_B − period_A`, `percentage = ((B − A) / A) × 100`, explicit
  zero-baseline behaviour, bounded grouping, deterministic ordering) and requires
  that the unresolved parts of **D-11** are **not** invented.
* **D-11 in the permanent P1 record** — the coverage matrix records family 11
  Temporal Comparison as governed by PO decision ID **D-11** ("period basis,
  restatements, percentage basis") and marks D-11 as required for that family. P2
  implements the **comparison basis** only; **restatement semantics remain
  PO-owned and unresolved**, and P2 makes no restatement ("as reported at the
  time") claim — confirmed in the combined verification record §27.
* No further or additional authorization is asserted here. This document invents
  no decision and expands no scope.

## 4. Implementation Evidence

| Item | Record |
| --- | --- |
| Implementation commit | `f2e456817e78c4f88e55837129ceefb0e9e90659` — `feat(p8): bounded Insight temporal comparison (P2, capability family 11)` |
| Implementation report | `docs/architecture/CT-P8-INSIGHT-TEMPORAL-COMPARISON-IMPLEMENTATION-20260922.md` |
| Migration change (applicable) | **new** `supabase/migrations/20261006000000_p8_insight_temporal_comparison.sql` — widens `ci_tool_calls_tool_name_check` from seven to eight authorized tool names; additive, idempotent, no new table/column/index, no answer-state change, no RLS change, no destructive statement |
| Implementation surfaces | backend `domain/insight_query.py`, `services/insight_query_planner.py`, `services/insight_tools.py`, `services/insight_interactions.py`, `domain/insight_interaction.py`; frontend `InsightComparison.jsx`, `InsightInteraction.jsx`, `insight.css`, `insight-comparison.test.jsx`; tests including the dedicated P2 suite |
| Final verified Git state | HEAD `c24e080373611bfb1190e8332262b015c03a51aa` on `p8-release-reconciled`, identical to `github/p8-release-reconciled`, alignment `0 0` (OBSERVED while preparing this record) |
| P2 migration position | `20261006000000_p8_insight_temporal_comparison.sql` present at its correct position (OBSERVED). The later MIG-1 remediation renamed only the **P3** migration; P2's ordering is unchanged |
| P2 source changes after implementation | **none.** The only post-implementation change to any P2 file is the authorized MIG-1 catalogue pin in the P2 test file (`assert len(TOOL_REGISTRY) == 8` → `== 10` plus a docstring) — one hunk, verified with `git diff f2e4568` (OBSERVED) |

## 5. Independent Verification

| Element | Record |
| --- | --- |
| Verifier | **Restricted CoStrict read-only independent verifier** ("OHD/CoStrict — Final Independent P2 Re-Verification") — an independent verifier, not the implementing agent |
| Verdict | **`PASS`** |
| Conclusion | `P2 INDEPENDENTLY VERIFIED — READY FOR PO CLOSURE` |
| Independently verified HEAD | `c24e080373611bfb1190e8332262b015c03a51aa` |
| Test result | actual P2 inventory **43 tests**; suite **43/43 passing**; **no skips, no failures** |
| Principal checks confirmed | P2 arithmetic and period semantics; zero-baseline percentage behaviour; empty-period behaviour; approved grouping dimensions; bounds; tenant isolation; route rate limiting; provenance/evidence pathway; no unauthorized analytics expansion; no P2 test weakening or removal; no P2 source changes after implementation; Git state unchanged during independent verification |

**Source of the verdict.** The verifier's report is **not committed to this
repository** — `.costrict/` contains only `package.json` and `.gitignore`, and no
CoStrict/independent P2 report exists under `docs/architecture/` (OBSERVED). The
verdict and findings above are therefore recorded **as transmitted by the PO in the
P2 closure authorization**, and the repository-checkable details were re-confirmed
while preparing this record: the verified HEAD equals the current HEAD exactly; the
dedicated P2 suite passes **43/43** at that HEAD (OBSERVED: `43 passed, 1 warning in
0.13s`); the P2 test file holds **43** test functions with **no**
parametrisation/skip/xfail markers, identical at the implementation commit; and the
P2 migration is present at its correct position (all OBSERVED).

**Distinction from Cline's own verification.**
`CT-P8-INSIGHT-P2-P3-CLINE-VERIFICATION-20260923.md` was produced by the
**implementing agent** and is explicitly **not** independent verification;
`CT-P8-INSIGHT-P2-P3-MIG1-REMEDIATION-20260923.md` is likewise an
implementing-agent record. Those documents are context and evidence, not the source
of independence. Independence in this closure rests solely on the CoStrict
verifier's `PASS`.

## 6. Test Inventory Reconciliation

* The actual dedicated P2 suite contains **43 tests** (43 test functions, no
  parametrisation, no skips, no dynamically generated tests) and passes **43/43**.
  It has been **43 since the implementation commit** `f2e4568` — the file never
  contained a different number of tests (OBSERVED).
* The combined P2 + P3 count is **91** (43 + 48), not 127.
* **`79` and `127` were never P2 test counts.** No retained pytest output or
  session log contains either figure; both appear only inside two Cline reports,
  where they were presented as measurements. The reconciliation established that
  they were arrived at by arithmetic rather than measurement
  (`127 = 48 real P3 + 79 inferred P2`), while the genuine 13-file regression
  summary of **299** was a real pytest line and is unaffected.
* **Accepted explanation of the `79` origin:** the historical `79%` pytest
  **progress percentage** — printed by pytest for a run long enough to wrap its
  progress line — was misread as a test count. This is consistent with the
  tooling's observable behaviour (a single 43-test run prints no intermediate
  percentage, whereas a multi-file run does print percentages), and it is recorded
  here as the accepted interpretation. What is *directly provable* from retained
  evidence is that no pytest summary ever reported 79; the exact keystroke-level
  origin is not reconstructible and was labelled **UNVERIFIABLE** in the
  reconciliation, whose substantive findings are unchanged.
* **Permanent reconciliation record:**
  `docs/architecture/CT-P8-INSIGHT-P2-TEST-INVENTORY-RECONCILIATION-20260923.md`
  (verdict `RECONCILED — NO P2 DEFECT; DOCUMENTATION CORRECTED`), which also
  corrected the two affected Cline reports. No test was added, removed, renamed,
  disabled or weakened by the reconciliation, and no artificial test-count
  manipulation was performed.


## 7. Accepted Limitation / Observation

**Accepted limitation (not upgraded, not removed):** the independent verification
**did not execute the P2 comparison against a live PostgreSQL database**. The
verifier classified this as an **acknowledged limitation**, not a blocking defect,
because the comparison logic is deterministic and pure, its period/aggregation
inputs are already-verified organization-scoped repository paths, and the tool
contract is exercised through the automated suite.

Boundary of this limitation, stated so it is not misread as broader coverage:

* this closure does **not** claim that P2 was independently exercised end-to-end
  against live data;
* the P2 **migration** was separately applied to a **disposable** PostgreSQL
  container during the MIG-1 remediation, where its 7 → 8 tool-name constraint was
  verified (implementing-agent evidence, not independent verification);
* the limitation therefore concerns the independent verifier's *live-database
  comparison execution*, and it stands as an accepted limitation of this closure.

## 8. Explicit Non-Closure

This document closes **P2 only**. It does **not**:

* close **P3** — the Insight Data Quality + Audit/Reproducibility package remains
  implemented-and-self-verified only, awaiting its own independent verification and
  PO closure;
* close **MIG-1** — the migration-sequencing remediation is complete and verified
  by the implementing agent, but its independent verification and PO closure are
  separate and outstanding;
* authorize **L7** (retention / deletion / legal hold) or **L8** (billing,
  entitlements, commercial SLO/SLA);
* authorize **production deployment**;
* authorize **any additional Insight capability** (P12, Scope 3, market-based
  Scope 2, Scope 1 decomposition, variance/attribution, supplier persistence,
  factor history, RAG, or any other package).

## 9. Git / Publication Record

* Starting HEAD while preparing this record: `c24e0803…` (aligned `0 0`).
* Closure-document commit: recorded below with its SHA.
* Push target: `github/p8-release-reconciled` (no force).
* Alignment after push:
  `git rev-list --left-right --count HEAD...github/p8-release-reconciled` = `0 0`.
* This task changed **documentation only** — no application/source code, no test,
  no migration, no frontend and no configuration file. The working tree continues
  to carry only the **pre-existing** verifier/environment artifacts
  (` M .gitignore`, `.costrict/`, `8`, `=`), which this task did not create and did
  not stage.

