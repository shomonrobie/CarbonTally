# CT-PO-P14 --- Reconciliation + Investor Acceptance Contract

**Task ID:** `P14-RECON-01-20260924-INVESTOR-ACCEPTANCE-CONTRACT`\
**Date:** 2026-09-24\
**Repository:** `/home/shomonrobie/ct_93d5cdd`\
**Branch:** `p8-release-reconciled`\
**Purpose:** Reconcile the independent P14 audits and freeze a truthful,
evidence-based investor acceptance contract before further
implementation.

------------------------------------------------------------------------

## 1. Source audits

This contract is derived from two independent P14 audit passes:

1.  **Cline P14-AUDIT-01**
    -   `docs/architecture/CT-PO-P14-AUDIT-01-CARBON-ACCOUNTING-COMPETITIVE-SCOPE-COVERAGE-20260924.md`
    -   JSON matrix:
        `docs/architecture/artifacts/p14_audit_01_scope_competitive_matrix_20260924.json`
    -   Commit: `b1a313d5383fb30ee09d307be5800f5bfd2364ef`
2.  **CoStrict independent verification**
    -   Independently sampled the P14 artifact and queried the Demo Lab
        read-only.
    -   Reproduced the key numerical claims and independently confirmed
        the principal Scope 1 / Scope 2 / Scope 3 / review / supplier /
        reporting findings.

No production environment is authorized by this contract.

------------------------------------------------------------------------

# PART I --- RECONCILIATION

## 2. Reconciliation rule

For every capability, distinguish:

-   **DOCUMENTED**
-   **CODE EXISTS**
-   **ROUTE WIRED**
-   **FACTORS AVAILABLE**
-   **PERSISTED DATA**
-   **END-TO-END VERIFIED**

A capability must not be called investor-demo verified merely because
its schema, function, route, or factor library exists.

**END-TO-END VERIFIED** requires a real persisted chain demonstrating:

`source → extraction → mapping/review → factor → calculation → persistence → evidence → reporting`

------------------------------------------------------------------------

## 3. Reconciled live baseline

The two audits converge on the following Demo Lab state:

  Measure                             Reconciled finding
  --------------------------------- --------------------
  Emission factors                                 7,049
  Scope 1 factors                                  2,549
  Scope 2 factors                                    354
  Scope 3 factors                                  4,090
  Factor years populated                       2025 only
  Factor countries                             GB and IE
  Emissions logs                                       2
  Scope 1 persisted results                            2
  Scope 2 persisted results                            0
  Scope 3 persisted results                            0
  Evidence lines                                      23
  Suppliers                                            1
  Emissions rows with supplier_id                      0
  Activity clarifications                              0
  Manual review queue rows                             0
  Review audit rows                                    0
  Report versions                                      4
  Report artifacts                                     0
  Disclosure values                                    0
  Customer factors                                     0
  Scope 3 category taxonomy rows                       0

The audits therefore agree that the strongest currently demonstrated
path is the existing Scope 1 calculation/evidence chain.

------------------------------------------------------------------------

## 4. Scope 1 reconciliation

### Current status

**ACCEPTED AS END-TO-END VERIFIED, NARROWLY.**

Verified persisted results include:

-   12,181.4 kWh Net CV × 0.2027 = 2,469.169780 kg CO2e
-   8,420.0 kWh × 0.2027 = 1,706.734000 kg CO2e
-   reconciled item total = 4,175.903780 kg CO2e

The calculation snapshots preserve factor ID/source/set, quantity, unit,
methodology, algorithm version, content hash and source linkage.

### Limit

This does not establish all Scope 1 activity types.

Not yet E2E verified:

-   mobile combustion
-   fugitive emissions
-   process emissions

Process emissions are not implemented.

------------------------------------------------------------------------

## 5. Scope 2 reconciliation

### Current status

**NOT INVESTOR-DEMO VERIFIED.**

Available:

-   354 factors
-   346 electricity
-   8 heat
-   8 steam
-   0 cooling

Missing/unverified:

-   location-based calculation
-   market-based calculation
-   dual-method result storage
-   contractual instruments
-   REC/GO/REGO/PPA handling
-   residual mix
-   eight contractual-instrument quality criteria
-   grid-region resolution
-   real purchased-electricity E2E fixture
-   real Scope 2 persisted result

`LOCATION_BASED` / `MARKET_BASED` vocabulary exists, but this is not
evidence of implemented dual-method accounting.

### Contract consequence

Do not present Scope 2 as complete merely because electricity factors
exist.

------------------------------------------------------------------------

## 6. Scope 3 reconciliation

### Current status

**NOT INVESTOR-DEMO VERIFIED AS GHG Protocol Scope 3 ACCOUNTING.**

There are 4,090 Scope 3 factors, but there is currently no populated GHG
Protocol category dimension and no persisted Scope 3 calculation.

### Factor-supported / structurally partial categories

1.  Purchased goods and services
2.  Fuel- and energy-related
3.  Upstream transport and distribution
4.  Waste generated in operations
5.  Business travel
6.  Employee commuting
7.  Upstream leased assets

### Not implemented according to the audit

2.  Capital goods
3.  Downstream transport and distribution
4.  Processing of sold products
5.  Use of sold products
6.  End-of-life treatment of sold products
7.  Downstream leased assets
8.  Franchises
9.  Investments

### Contract consequence

The investor demo must not claim "all Scope 3" or imply that factor
count equals Scope 3 accounting coverage.

------------------------------------------------------------------------

## 7. Waste / Category 5 reconciliation

Waste is deliberately fail-closed.

The factor taxonomy requires material + treatment route. Bare "Waste" is
insufficient, and plausible treatment routes can materially change the
factor.

Therefore:

`ambiguous waste → clarification → operator selection → calculation`

is a **successful governed workflow**, not an extraction failure.

The audits agree that the machinery exists, but no live clarification
row has yet been exercised.

------------------------------------------------------------------------

## 8. Manual-review reconciliation

### Design status

**IMPLEMENTED / ROUTE-WIRED / AUDITABLE BY DESIGN.**

The model preserves:

-   original value/activity
-   reason for review
-   source evidence
-   eligible factor choices
-   selected factor
-   actor
-   actor scope
-   timestamp
-   version/supersession
-   recalculation requirement

### Operational status

**NOT YET VERIFIED.**

Current live counts:

-   clarification rows: 0
-   manual review queue: 0
-   review audit rows: 0

### Contract consequence

Investor acceptance requires at least one real ambiguous case to travel
through:

`uncertain → user review → correction/selection → audit record → recalculation → new persisted result`

------------------------------------------------------------------------

## 9. Supplier reconciliation

### Current status

**MODELLED + ENGINE PARTIALLY IMPLEMENTED, BUT NOT E2E VERIFIED.**

The supplier model and resolver exist. Supplier attribution is writable
and available to reporting/Insight.

But:

-   only 1 supplier exists in the demo state
-   0 emissions rows have `supplier_id`
-   real canonical PDFs have not demonstrated supplier reuse
-   automatic processing wiring remains incomplete

### Required investor proof

Document 1:

`Robinsons Recycling Services Ltd → supplier confirmation/creation → supplier_id`

Document 2:

`same supplier → same supplier_id → calculation`

The second document must not silently create a duplicate supplier.

------------------------------------------------------------------------

## 10. Reporting reconciliation

### Current status

**ARCHITECTURE EXISTS; REAL REPORT ARTEFACT NOT VERIFIED.**

Existing:

-   report versions
-   approval/finalization routes
-   disclosure architecture
-   frozen-artifact architecture

Missing live evidence:

-   generated report artifact
-   disclosure values
-   regulatory requirement content

### Contract consequence

Investor acceptance requires at least one report generated from real
persisted demo calculations, not merely a report route or empty report
version.

------------------------------------------------------------------------

## 11. Factor-year reconciliation

Current factors are 2025 only.

Canonical PDF corpus contains:

-   3 FY2025 documents
-   3 FY2026 documents

There is currently no verified policy for activity year ≠ factor year.

### Contract rule

**Never silently use a mismatched factor year.**

Before investor acceptance, the demo must either:

-   use only year-compatible documents, or
-   explicitly show a warning/review decision for FY2026, or
-   implement and verify a documented factor-year selection policy.

No silent substitution is acceptable.

------------------------------------------------------------------------

## 12. SEAI scope

**SEAI is explicitly deferred to Version 4.**

This contract does not require new SEAI implementation or expansion.

Existing SEAI support remains documented as existing capability; it is
not an investor acceptance blocker for this contract.

------------------------------------------------------------------------

# PART II --- INVESTOR ACCEPTANCE CONTRACT

## 13. Purpose

The investor demo is not intended to claim full production
carbon-accounting coverage.

It must demonstrate a **truthful, auditable carbon-data journey**
showing:

1.  realistic source document
2.  extraction
3.  uncertainty handling
4.  human review where required
5.  factor selection
6.  calculation
7.  supplier attribution
8.  evidence lineage
9.  reporting
10. audit trail

------------------------------------------------------------------------

## 14. Investor acceptance principle

### Core invariant

> CarbonTally must never invent uncertain carbon-accounting data.

If data cannot be reliably extracted or resolved:

**show it to the user for manual review and correction, preserve the
original, record the correction and continue only from the auditable
corrected state.**

Automatic matching must not guess.

------------------------------------------------------------------------

## 15. Investor acceptance journeys

The acceptance suite shall contain the following journeys.

### IA-01 --- Scope 1 real calculation

Must demonstrate:

`CSV/source → extraction → mapping → DEFRA factor → calculation → evidence → emissions → report`

Acceptance:

-   persisted calculation exists
-   arithmetic reconciles
-   factor provenance is visible
-   evidence points back to source
-   result is explainable

Existing Scope 1 evidence may be used as the baseline regression.

------------------------------------------------------------------------

### IA-02 --- PDF extraction

Use the frozen canonical six-PDF corpus.

Must demonstrate:

-   supplier
-   customer
-   invoice reference
-   date
-   billing period
-   line items
-   quantity
-   unit
-   raw evidence

No corpus modification.

------------------------------------------------------------------------

### IA-03 --- Manual review / waste clarification

Use a canonical waste line where the treatment route is not printed.

Expected:

`Waste → ambiguous → clarification`

Operator must:

1.  see original extracted value
2.  see why automatic selection is unsafe
3.  see eligible choices
4.  select/correct the factor
5.  persist the action
6.  trigger recalculation
7.  preserve audit history

Acceptance requires a real persisted clarification record.

------------------------------------------------------------------------

### IA-04 --- Supplier creation and reuse

First canonical document:

`Robinsons Recycling Services Ltd`

Operator confirms or creates the supplier.

Second canonical document:

same supplier.

Acceptance:

-   same organization-scoped supplier identity
-   no duplicate
-   `mapped_supplier_id` populated
-   `emissions_logs.supplier_id` populated
-   downstream reporting can filter by supplier

------------------------------------------------------------------------

### IA-05 --- Scope 3 investor slice

The investor demo does not need all 15 categories.

For the current acceptance contract, demonstrate a bounded Scope 3 slice
using categories already supported by factor families:

-   Category 1 --- Purchased goods/services
-   Category 4 --- Upstream transport/distribution
-   Category 5 --- Waste
-   Category 6 --- Business travel
-   Category 7 --- Employee commuting

Category 3 may be included where its factor/data path can be
demonstrated without creating misleading claims.

### Critical rule

The UI/report must clearly identify the demonstrated subset.

It must **not** claim full Scope 3 coverage.

A category is accepted only when an actual persisted E2E result exists.

------------------------------------------------------------------------

### IA-06 --- Scope 2 investor slice

Scope 2 requires a separate implementation/decision contract before it
can be accepted.

At minimum, acceptance must define and demonstrate the intended
accounting method.

The investor contract must not call a single electricity multiplication
"full Scope 2" while dual-method requirements remain unresolved.

------------------------------------------------------------------------

### IA-07 --- Reporting

From real persisted demo data:

`calculations → emissions → report → approval → finalization → artifact`

Acceptance:

-   report artifact exists
-   totals reconcile to persisted emissions
-   reporting period is explicit
-   scope is explicit
-   source/calculation lineage remains traceable
-   finalized output cannot silently change

------------------------------------------------------------------------

### IA-08 --- Cross-tenant security regression

Existing tenant isolation must remain green.

No investor acceptance task may weaken:

-   RLS
-   organization boundaries
-   PE boundaries
-   support-role boundaries
-   supplier organization scoping

------------------------------------------------------------------------

# PART III --- INVESTOR ACCEPTANCE GATES

## 16. Mandatory gates

  --------------------------------------------------------------------------
  Gate                    Requirement             Acceptance
  ----------------------- ----------------------- --------------------------
  G1                      Scope 1                 Real persisted E2E
                                                  calculation

  G2                      PDF extraction          6/6 canonical documents

  G3                      Extraction fidelity     21/21 line structures, no
                                                  known false positives

  G4                      Manual review           ≥1 real
                                                  clarification/correction

  G5                      Supplier                Create/confirm + reuse
                                                  across ≥2 documents

  G6                      Supplier propagation    supplier_id reaches
                                                  emissions

  G7                      Scope 3                 At least one clearly
                                                  bounded category E2E

  G8                      Scope 2                 Explicit method + real E2E
                                                  result before claiming
                                                  Scope 2

  G9                      Evidence                Every accepted calculation
                                                  has source evidence

  G10                     Reporting               Real report artifact
                                                  generated from real data

  G11                     Auditability            Original → correction →
                                                  calculation → report
                                                  traceable

  G12                     Year handling           No silent FY2026/2025
                                                  mismatch

  G13                     Security                Required tenant-isolation
                                                  checks green

  G14                     Regression              EV-01 and relevant
                                                  existing regressions green

  G15                     Truthfulness            UI/docs state exactly what
                                                  is and is not covered
  --------------------------------------------------------------------------

------------------------------------------------------------------------

# PART IV --- WHAT IS OUT OF SCOPE

## 17. Explicitly deferred

The following are not required for this investor acceptance contract:

-   full 15-category Scope 3 implementation
-   financed emissions / PCAF
-   product carbon footprints
-   supplier portal
-   supplier questionnaires
-   spend-based estimation
-   anomaly detection
-   peer benchmarking
-   target modelling
-   full multi-entity consolidation
-   full framework/regulatory requirement content
-   production assurance programme
-   external assurance workflow
-   full GWP/gas disclosure
-   uncertainty modelling
-   factor library expansion
-   2026 factor-library expansion unless required by the selected
    acceptance journey
-   SEAI expansion --- **Version 4**
-   P1 promotion
-   canonical corpus v2
-   reporting architecture redesign
-   supplier architecture redesign
-   parallel manual-review system
-   numeric confidence-score redesign

------------------------------------------------------------------------

# PART V --- IMPLEMENTATION RULES

## 18. No broad implementation

Each implementation task must have:

-   unique task ID
-   explicit scope
-   mandatory Markdown report
-   production prohibition
-   Demo Lab only
-   no unrelated refactor
-   no corpus/oracle modification unless separately approved
-   no silent schema changes
-   executable acceptance evidence
-   exact files changed
-   test results
-   known limitations

------------------------------------------------------------------------

## 19. Existing architecture should be reused

Do not create parallel systems for:

-   manual review
-   supplier management
-   evidence
-   calculation snapshots
-   audit trail
-   reporting

The goal is to exercise and complete the existing paths where they are
already architecturally sufficient.

------------------------------------------------------------------------

## 20. Fail-closed rule

For all extraction, mapping and factor resolution:

`uncertain → review`

not:

`uncertain → guessed value`

This applies especially to:

-   waste treatment
-   supplier identity
-   factor selection
-   factor-year mismatch
-   incompatible units
-   missing required fields

------------------------------------------------------------------------

## 21. Evidence rule

Every accepted calculation must be traceable to:

`source document → source line/item → extracted value → normalized value → factor → calculation snapshot → emissions row → report`

If a link is unavailable, the journey is not accepted as fully
auditable.

------------------------------------------------------------------------

# PART VI --- REQUIRED NEXT WORK

## 22. Next task is decision/design, not broad implementation

Before further implementation, create:

`P15-DECISION-01-20260924-INVESTOR-JOURNEY-IMPLEMENTATION-CONTRACT`

That task should translate this contract into bounded implementation
packages.

Recommended sequence:

1.  **P15-A --- Scope 2 decision**
2.  **P15-B --- bounded Scope 3 demo slice**
3.  **P15-C --- exercise P12 supplier/review implementation**
4.  **P15-D --- real-data reporting artifact**
5.  **P15-E --- full investor acceptance run**
6.  Independent verification
7.  Only then Step 3 UI work

------------------------------------------------------------------------

## 23. Definition of investor-demo acceptance

CarbonTally may be described as having a **verified investor
demonstration journey** only when all mandatory gates G1--G15 pass.

Until then, the truthful status is:

> **Foundation substantially implemented; investor journey still
> undergoing end-to-end acceptance.**

This wording deliberately avoids claiming complete Scope 1/2/3 coverage.

------------------------------------------------------------------------

## 24. Final reconciliation statement

The two independent audits materially agree.

The principal issue is not that CarbonTally lacks a carbon-accounting
data model. It has substantial infrastructure for factors, calculation
provenance, evidence, ambiguity handling, supplier data and reporting.

The principal issue is that several important capabilities have not yet
produced **real persisted end-to-end evidence**.

The investor acceptance program therefore prioritizes:

**exercise → verify → preserve evidence → demonstrate**

over:

**add more architecture → assume it works.**

------------------------------------------------------------------------

## 25. STOP CONDITION

No implementation begins from this document alone.

A subsequent implementation task must explicitly reference this contract
and define the exact gate(s) it is authorized to satisfy.

**Production remains unauthorized.**
