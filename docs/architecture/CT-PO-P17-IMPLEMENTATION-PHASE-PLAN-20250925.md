# CT-PO-P17 — Implementation Phase Plan

**Document:** `CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md`
**Task ID:** `P17-ARCH-01-20250925-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT`
**Date:** 2025-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` — branch `p8-release-reconciled`
**Baseline commit:** `9c96cbf11204b1dcebd15d1598653b0e9ba3e5be`
**Main contract:** `docs/architecture/CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md`

> **No phase below is authorised by this document.** This plan sequences work so that a subsequent, separately
> authorised implementation task can be pointed at exactly one phase. Production is not authorised at any point.

---

## 1. Principles

1. **Smallest correct change first.** P17 begins with the two canonical dimensions and the factor-governance gap; it does not begin with new category tables.
2. **Reuse, do not parallelise.** Every phase extends `calculation_snapshots`, `emissions_logs`, the calculation engine, the matching/selection policy, the evidence machinery, the adjudication lifecycle and the reportability lifecycle that P16 already verified.
3. **One phase, one gate.** A phase is not closed until its gate is demonstrated with persisted evidence.
4. **No fabricated data.** No factor, category, instrument, method or estimate is invented to make a journey work.
5. **Fail closed.** Ambiguity produces a review state, never a guessed value.
6. **No production.** Demo Lab or a disposable clone only (invariant F-046-1).

---

## 2. Dependency graph

```
P17-A  (dimensions + factor governance)
  |
  +--> P17-B  (Scope 2 LOCATION_BASED E2E)
  |       \
  |        +--> P17-C  (MARKET_BASED + instruments)   [shares the Scope 2 activity + method dimension]
  |
  +--> P17-D  (Scope 3 canonical category model)
          |
          +--> P17-E  (categories 1-5)
          +--> P17-F  (categories 6-10)
          +--> P17-G  (categories 11-15)
                  |
   P17-E/F/G -----+--> P17-H  (cross-category integrity, controls, provenance)
                          |
                          +--> P17-I  (reporting / disclosure integration)
                                  |
                                  +--> P17-J  (independent P17 acceptance)
```

**Critical path:** P17-A → P17-B → P17-C → P17-H → P17-I → P17-J.
P17-D can be built in parallel with P17-B/C once P17-A is in place, because the Scope 2 and Scope 3 dimension work touches disjoint result sets.

**Systemic blocker risk:** every phase that adds a calculation path must also add the dimension to the deterministic request-id digest (DC-10). Omit it once and duplicate reportable results reappear — the exact defect P16-R7 closed.

---

## 3. P17-A — Scope 2 canonical model + factor governance

**Objective.** Make the two canonical dimensions (`scope2_method`, `scope3_category`) placeable and enforceable on results, and close the latent cross-year factor-candidate gap.

**Prerequisites.** None. This is the first phase.

**Schema delta.** §2.1–§2.5 of `p17_schema_delta_20250925.md` (migration `20261010000000`).

**Domain / engine work.**
* Extend `CalculationRequest` / `CalculationSnapshot` / `EmissionLog` with the new dimensions (nullable).
* Extend the deterministic request-id digest to include `scope2_method` and `scope3_category` (DC-10) — **one mechanism**, not a second one.
* Extend `_calc_payload_digest` accordingly; keep the existing manual/automatic key namespaces as they are.
* Add the year filter at the four candidate call sites (`v3_operations.py:1039`, `v3_operations.py:1650`, `v3_processing_workflow.py:1156`, `automatic_processing.py:1615`) so an operator is never silently shown a cross-year candidate. Where a cross-year candidate must remain visible (an explicit operator override), it must be labelled with its year and require an explicit decision.

**Explicit non-scope.** No Scope 2 calculation method yet. No category assignment logic. No new factors. No UI work.

**Gate `SCHEMA_AND_GOVERNANCE`.** All items in `p17_acceptance_matrix_20250925.json → phase_gates[P17-A].must_pass`.

**Exit criteria.** Migration applied to the Demo Lab only; 34 snapshots / 34 logs byte-identical in every pre-existing column; `NOT VALID` constraints reject a deliberately invalid insert and accept history; RLS/ACL unchanged in effect; cross-year candidates no longer present unlabelled; data + unit tests green; the two stale migration-count expectations updated to the new correct values and reported as such.

---

## 4. P17-B — Scope 2 location-based end-to-end

**Objective.** The first real, persisted Scope 2 result, by one explicit method.

**Prerequisites.** P17-A.

**Domain / service work.** A Scope 2 activity input contract (energy type, quantity, unit, facility or explicit national resolution, country, period); a location-factor selection path requiring an exact reporting year and matching country/geography; `scope2_method='LOCATION_BASED'` persisted on both the snapshot and the log.

**Explicit non-scope.** No market-based method. No instruments. No residual mix.

**Gate `SCOPE2_LOCATION_E2E`.** See the acceptance matrix.

**Exit criteria.** One electricity activity with a real location factor; a reproducible snapshot (`/calculations/{id}/verify` green); an intact evidence chain; a reportable result appearing in a method-filtered aggregate; a negative test proving a Scope 2 write without a method is rejected.

---

## 5. P17-C — Scope 2 market-based + contractual instruments

**Objective.** The second method, plus the instrument domain that makes a market claim auditable and non-duplicable.

**Prerequisites.** P17-A; P17-B recommended (shares the activity contract).

**Schema delta.** §3.1–§3.2 (migration `20261011000000`).

**Domain / service work.** Instrument registration with evidence; instrument validation (validity window, geography, vintage, quantity, retirement status, evidence presence); allocation to a specific activity/snapshot with quantity reconciliation; market-factor selection; `scope2_method='MARKET_BASED'` persisted alongside — never replacing — the location-based result.

**Explicit non-scope.** No residual-mix dataset. No framework-specific certificate rules (REGO/REC semantics are FRAMEWORK_SPECIFIC and deferred) unless separately ratified. No second instrument model.

**Gate `SCOPE2_MARKET_AND_INSTRUMENTS`.** See the acceptance matrix: including the two negative requirements (cross-organisation claim denied; over-allocation denied) and the invalid-instrument review requirement.

**Exit criteria.** Both methods persisted for one activity and independently readable; instrument claim uniqueness proven at the database and API layers; an invalid/expired/missing-evidence instrument produces a controlled review state rather than a result; reporting distinguishes the methods.

---

## 6. P17-D — Scope 3 canonical category model

**Objective.** Make category a required, explicit, non-inferred dimension of every new Scope 3 result.

**Prerequisites.** P17-A.

**Schema delta.** §3.3 (migration `20261012000000`) plus the `scope3_category` columns already added in P17-A.

**Domain / service work.** The 15-category controlled vocabulary; a resolution step that produces a category either from a deterministic rule with a recorded basis or from an operator decision; the boundary/origin properties that separate 4/9, 5/12 and 8/13.

**Explicit non-scope.** No category calculation path yet. No factor-hint population. No backfill.

**Gate `SCOPE3_CATEGORY_MODEL`.** See the acceptance matrix.

**Exit criteria.** 15 canonical categories seeded; a new Scope 3 write without a category is rejected; history untouched and explicitly documented as category-less; no free-text-only inference of a category exists anywhere.

---

## 7. P17-E / P17-F / P17-G — Scope 3 Categories 1–5 / 6–10 / 11–15

**Objective.** One END-TO-END VERIFIED journey per category the architecture marks deliverable.

**Prerequisites.** P17-D (and P17-H's estimation records before categories 7/11/12 are attempted).

**Per-category work.** The input contract, methodology, factor-eligibility rule, evidence requirement, review triggers and golden fixture defined in `p17_scope3_category_matrix_20250925.json`.

**Explicit non-scope.** Any category marked `DEFERRED` or `NOT_IMPLEMENTED` in the matrix must be **explicitly reported as blocked with its prerequisite named**, never silently skipped and never claimed.

**Gates `SCOPE3_CAT_1_5`, `SCOPE3_CAT_6_10`, `SCOPE3_CAT_11_15`.** See the acceptance matrix.

**Exit criteria.** A persisted, evidence-linked, correctly categorised, reportable result per delivered category, each with at least one deterministic golden calculation whose expected value is derived independently of the implementation.

---

## 8. P17-H — Cross-category validation, double-counting controls, provenance

**Objective.** Prove the new dimension set is internally consistent and that no category or method double counts.

**Prerequisites.** P17-B/C and P17-E/F/G (the controls need results to detect).

**Schema delta.** §3.4 and §2.5 consolidation approach (migrations `20261013000000`, `20261014000000`).

**Work.** Implement DC-01…DC-11 detection; the estimation-record contract; the data-quality dimension population; the provenance reader for the chain report value → snapshot → source activity → evidence → factor → operator decision.

**Gate `INTEGRITY`.** See the acceptance matrix.

**Exit criteria.** Every control has a deterministic mechanism and at least one negative test; the provenance chain resolves for every delivered journey; idempotency holds on every new calculation path.

---

## 9. P17-I — Reporting / disclosure integration

**Objective.** Turn real persisted results into a real report artefact that distinguishes scope, method, category and reportability.

**Prerequisites.** P17-H.

**Work.** Extend the existing disclosure projection (`backend/data/disclosure_projection.py`, which already filters `reportability_status = 'reportable'` and supports a `scope_hint`) so Scope 2 method and Scope 3 category are first-class report dimensions; generate a real artefact from real Demo Lab results.

**Explicit non-scope.** No framework-specific disclosure schema in the accounting core. No claim of GHG Protocol / CSRD / ESRS / SECR / IFRS S2 / CDP / PCAF compliance.

**Gate `REPORTING`.** See the acceptance matrix.

**Exit criteria.** A generated artefact in which location-based and market-based Scope 2 are separate lines, Scope 3 categories are distinguishable and never collapsed internally into an undifferentiated total, and superseded/not-for-reporting results are excluded but still inspectable.

---

## 10. P17-J — Independent P17 acceptance

**Objective.** Independent reproduction of the Scope 2 and Scope 3 journeys.

**Prerequisites.** P17-I.

**Gate `INDEPENDENT`.** An implementer's own report does not satisfy this gate (the P2 and P16 precedent: Cline's own verification is not independent verification).

**Exit criteria.** Independent report; tenant-isolation negative matrix green; full regression classified with zero Class-A failures; production never contacted; limitations stated truthfully.

---

## 11. What must remain frozen

| Frozen artefact | Why |
|---|---|
| `supabase/migrations/**` (all 83 historical files) | P16/P12 evidence integrity; migrations are append-only history |
| The six-PDF canonical corpus, ground truth, oracle, generator, manifest (`p12-canonical*`, `ground_truth`, `oracle`) | P16 acceptance evidence; byte-identical at P16 close |
| `docs/architecture/CT-PO-P16-*`, `CT-PO-P12-*`, `CT-PO-P14-*` reports | Historical acceptance records; never rewritten |
| The `reportable | not_for_reporting | superseded` lifecycle | Ratified at P16-RD-4; P17 reuses it |
| `uq_calc_snapshots_request_id` and the deterministic-id mechanism | The single idempotency mechanism (DC-10) |
| The `activity_clarifications` adjudication lifecycle | Ratified manual-review system; P17 extends, never replaces |
| The supplier resolver contract (org-scoped, fail-closed) | P12-IMPL-02 contract |
| The disclosure `SCOPE2_METHODS` vocabulary | Reused verbatim, never redefined |
| RLS policies, FORCE, default privileges | Security boundary; changes need separate authorisation |
| D17 / D19 / D21 frozen UX decisions | PO-frozen; P17 adds data and workflow, not a redesign |

---

## 12. Rollout sequencing and observability

1. Each phase ships its migration + service change + tests together, applied to the **Demo Lab only**.
2. Every new calculation path emits the same audit and event signals the existing paths emit (`audit_trail`, domain events), so the operations console and API metrics observe it without redesign.
3. New async or batch work (bulk Scope 3 ingestion, instrument validation sweeps) must be idempotent and retry-safe with persisted job state. A spinner is not processing.
4. Where a phase could alter existing reporting output, introduce it behind an explicit configuration switch so the P16-verified paths remain demonstrable unchanged.

---

## 13. Phase-level risks

| Risk | Impact | Mitigation |
|---|---|---|
| Request-id digest not updated when a dimension is added | duplicate reportable results (the P16-R7 defect) | DC-10 is a mandatory per-phase check |
| Category inferred from factor family | silent misclassification | AD-P17-02: category is an activity property; hints are proposals only |
| Market-based result silently replacing location-based | false dual-method claim | separate results, separate request ids, method in every report dimension |
| Instrument claimed twice | false low/zero market-based claim | claimant org on the instrument row + allocation reconciliation tests |
| Historical rows accidentally backfilled | fabricated accounting history | `NOT VALID` constraints only; backfill prohibited |
| A `DEFERRED` category claimed as delivered | false coverage claim | the matrix status must be carried into every report |
| Scope creep into frameworks | unratified compliance claims | main contract §39: alignment documented, compliance not claimed |
| Phase attempts to reuse the destructive integration harness against a data-bearing DB | data loss | invariant F-046-1: disposable clone only |

---

## 14. First implementation phase (recommended)

**P17-A — Scope 2 canonical model + factor governance.**

Rationale: it is the only phase that is (a) a prerequisite of every other phase, (b) fully specified at this point,
(c) non-fabricating (additive columns + `NOT VALID` constraints + a governance fix that touches no accounting
value), and (d) independently verifiable without any new factor, instrument or category data. It also closes the
one concrete, currently verifiable defect this contract found (unlabelled cross-year factor candidates at four
production call sites).

**Authorisation state:** recommended only, and **gated behind §15 below**. This task does not implement it.

---

## 15. Pre-implementation reconciliation prerequisite (P17-0) — **MANDATORY**

Two **APPROVED PRODUCT-OWNER** decision records post-date the P17 architecture contract and explicitly require it to be
reconciled before affected implementation (full register with sources and impacts: main contract §57):

* `docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` (D1)
* `docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` (D2 — its §51 lists the reconciliation items)

They are not created or committed by this task.

**Effect on this plan.**

| Item | Effect |
|---|---|
| Mandatory UI/UX inside affected phases (D1 §6/§23; D2 §41/§50) | **Each affected phase (P17-B … P17-I) must deliver the applicable UI/UX as part of the phase**, not as a later "Step 3" work package. Phase scope, effort and gates increase accordingly. |
| Governed submission → approval before reportability (D1 §7; D2 §9) | P17-H's reportability work is extended: the PO lifecycle must be mapped onto existing state machines, and customer-contributed data must not reach `reportable` without approval. |
| Customer-owned data contribution + source actor / acting-for context (D1 §2/§4; D2 §5/§22/§23) | A contributor entry point and actor/context provenance are added to the phase scope (primarily P17-B/C/E/F/G input contracts and P17-H provenance). |
| Organization capabilities; permission ≠ accounting authority; consultant delegated client access (D1 §9; D2 §7/§8/§12–§18) | Affects the API contract (§38), the RLS/security model (§39) and the UX of every affected phase. |
| Existing-vs-missing discovery + classification before coding (D1 §5/§26; D2 §39/§40) | **Every phase must begin with that classification** and must reuse existing functionality where appropriate. |
| PASS / PARTIAL / FAIL / BLOCKED / DEFERRED reporting vocabulary (D2 §47/§48) | Phase completion reports must use the five-way vocabulary. |

**Recommended vehicle:** a small, documentation-only reconciliation task (e.g. `P17-RECON-01`) that amends the main
contract and this plan, and produces the existing-vs-missing classification. **P17-A must not begin before that
reconciliation is complete**, because the reconciliation may add columns (source actor / acting context) to the same
P17-A migration, and one amendment is cheaper and safer than two migrations.

**Status of this prerequisite:** **NOT DONE** — registered by this task, not performed by it.



