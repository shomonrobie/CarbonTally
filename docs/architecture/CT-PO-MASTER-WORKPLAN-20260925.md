# CarbonTally — Master Workplan & Execution Reference

**Reference:** `CT-PO-MASTER-WORKPLAN-20260925`  
**Date:** 2026-09-25  
**Status:** ACTIVE PO WORKPLAN / GOVERNANCE REFERENCE  
**Production deployment:** NOT AUTHORIZED  
**Production database mutation:** NOT AUTHORIZED

## 1. Purpose

This is the current working reference for Cline, independent verifiers, and the Product Owner from 2026-09-25 onward.

It consolidates the earlier investor-demo workplan, P16 closure, P17 architecture, the reconciled organization/CAMS decisions, UI/UX standard, P17-0 discovery gate, later P17 implementation, investor-demo/customer-experience work, future governance/reporting, and final assurance.

This document is a **workplan and authorization framework**, not implementation authorization.

No task may infer authorization merely because a phase appears below.

---

## 2. Current Ground Truth

### P16 — CLOSED

P16 final independent verification is **`P16_PASS`**.

Verified controls include:

- deterministic server-side calculation;
- factor precedence and factor safety;
- factor year/scope guards;
- supplier attribution;
- reportability lifecycle;
- invalidation and supersession;
- deterministic calculation idempotency;
- tenant isolation / cross-organization authorization;
- auditability;
- P16 regression protection.

Final full unit suite:

- 3,342 tests
- 3,322 passed
- 9 failed
- 11 skipped
- 0 errors
- 0 new Class-A failures

The remaining failures were classified as pre-existing/non-P16 Class B/E issues.

**Reference:** `docs/architecture/CT-PO-P16-FINAL-VERIFICATION-20250925.md`

### P17 ARCH-01

P17 ARCH-01 established the original Scope 2 + full 15-category Scope 3 accounting architecture.

It remains preserved as the architectural source.

It does **not** independently authorize implementation.

### P17 ARCH-02

ARCH-02 reconciled the architecture against later approved PO decisions.

Current status:

`P17_ARCH_RECONCILED_READY_FOR_VERIFICATION`

Current reconciled commit:

`906e66c4e2fa8ca02b006c71437bb988c4f53a48`

No P17 implementation has started.

**Reference:** `docs/architecture/CT-PO-P17-ARCH-02-RECONCILIATION-20250925.md`

---

# 3. Immediate Gate — P17 ARCH-03

Current task:

`P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE`

This is an independent/adversarial architecture verification, not another Cline self-review.

It must challenge:

- ARCH-01 and ARCH-02;
- Scope 2 model;
- contractual instruments;
- all 15 Scope 3 categories;
- unified CAMS;
- consultant/client organization model;
- acting-for context;
- customer contribution;
- capabilities vs permissions;
- lifecycle/reportability;
- UI/UX standard;
- existing UI baseline;
- authorization/RLS/tenant isolation;
- schema delta;
- idempotency;
- factor governance;
- reporting;
- evidence/provenance;
- double-counting controls;
- P16 regression;
- deferred scope.

Possible verdicts:

- `P17_ARCH_FREEZE_PASS`
- `P17_ARCH_FREEZE_PARTIAL`
- `P17_ARCH_FREEZE_BLOCKED`
- `P17_ARCH_FREEZE_FAIL`

### Authorization rule

**Do not authorize P17-0 or P17-A until ARCH-03 has a final independent verdict.**

If ARCH-03 passes, the next PO authorization decision is **P17-0 only**. P17-A remains separately gated.

---

# 4. Governing Product Architecture

## 4.1 Unified CAMS

CarbonTally uses **one shared carbon-accounting management system and accounting engine** for:

- CarbonTally Staff/Admin;
- direct customer organizations;
- consultant organizations;
- consultant client organizations;
- delegated users.

No separate consultant/customer/client accounting engines.

No duplicate calculation, evidence, reportability, lifecycle, or audit systems.

## 4.2 Organization / tenant model

Consultant clients are independent organizations/tenants.

Use an explicit relationship such as:

```text
Green Advisory (consultant)
        |
        +-- CONSULTANT_CLIENT --> ABC Manufacturing (independent org)
```

The client owns its:

- data;
- evidence;
- calculations;
- reports;
- history.

Consultant access is delegated, client-specific, revocable, and auditable.

## 4.3 Acting-for

Consultant context must be persisted where accounting/audit requires it.

The UI must make it obvious:

```text
CURRENT ORGANIZATION: Green Advisory
ACTING FOR: ABC Manufacturing
```

Audit context must distinguish actor, actor organization, organization acted for, data owner, role/delegation, timestamp, reason, source/evidence, and downstream effect.

## 4.4 Customer contribution

Customer organizations may contribute data when enabled.

Contribution may include:

- activity entry;
- evidence upload;
- supplier data;
- correction proposals;
- submission for review.

Contribution does **not** grant authority to:

- change governed methodology/factors;
- bypass validation;
- bypass review;
- make invalid calculations reportable;
- mutate historical results;
- access another organization;
- alter platform accounting governance.

## 4.5 Capabilities

Capabilities are:

- organization-scoped;
- CarbonTally-controlled;
- server-enforced;
- distinct from ordinary permissions.

Effective consultant authority is:

```text
client capability
∩ delegated client capability
∩ user/consultant role
```

The exact storage representation is a **P17-0 decision**. Reuse an existing ratified governance primitive where possible; do not create a duplicate capability system.

Disabled capabilities require both a meaningful UI state and backend denial.

---

# 5. Governed Lifecycle

Customer-contributed data is not automatically reportable.

The architecture maps onto existing state machines rather than creating a duplicate lifecycle:

```text
DRAFT
  ↓
SUBMITTED
  ↓
VALIDATED
  ↓
CALCULATED
  ↓
REVIEW
  ↓
APPROVED
  ↓
REPORTABLE
```

Rejection, correction, invalidation and supersession must exist where applicable.

Historical results must not silently mutate.

Customer changes preserve actor, timestamp, original/new values, reason, evidence, calculation effect and reportability effect.

---

# 6. UI/UX Is In-Phase Scope

Authoritative standard:

`CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md`

UI/UX is not deferred to a later generic Step 3 for affected P17 work.

Acceptance follows:

```text
UI
→ API
→ authorization
→ domain/service
→ database
→ audit/provenance
→ calculation/reportability
→ UI reflects final state
```

A backend-only implementation is not a complete PASS where UI/UX is required.

This applies to:

- organization context;
- ACTING FOR;
- capabilities;
- permission/disabled states;
- lifecycle;
- review/exception;
- Scope 1/2/3;
- evidence;
- suppliers;
- calculation detail;
- reportability;
- reporting;
- audit/history.

---

# 7. Accounting Scope

## Scope 1

Preserve P16. Do not silently redesign or upgrade unverified Scope 1 coverage.

P17 Scope 2/3 paths reuse the same deterministic calculation architecture.

## Scope 2

P17 covers:

- location-based;
- market-based;
- required method identity;
- energy type;
- facility context;
- factor governance;
- contractual instruments;
- allocations/validation;
- reportability;
- evidence/provenance;
- auditability.

`scope2_method` is persisted and must be part of idempotency/reporting/history.

Valid values:

`LOCATION_BASED | MARKET_BASED`

Method cannot be inferred solely from factor metadata.

Instrument existence does not itself make a contractual claim valid.

Jurisdiction-specific residual-mix and REGO/REC/GO rules remain framework-specific/deferred unless separately authorized.

## Scope 3

The architecture covers all 15 GHG Protocol categories.

Category identity must not be inferred from factor family alone.

Known semantic overlaps must remain distinct, including:

- Category 4 vs 9;
- Category 5 vs 12;
- Category 8 vs 13.

Current planning status:

| Category | Status |
|---|---|
| 1 | PARTIAL |
| 2 | NOT IMPLEMENTED / methodology decision preserved |
| 3 | SUPPORTED |
| 4 | SUPPORTED |
| 5 | SUPPORTED |
| 6 | SUPPORTED |
| 7 | PARTIAL |
| 8 | PARTIAL |
| 9 | PARTIAL |
| 10 | NOT IMPLEMENTED / methodology decision preserved |
| 11 | DEFERRED / methodology preserved |
| 12 | PARTIAL |
| 13 | PARTIAL |
| 14 | DEFERRED / operating-model decision preserved |
| 15 | DEFERRED / current approved scope preserved |

These are architecture/planning statuses, not claims of final E2E product support.

---

# 8. Factor Governance

P17 extends the P16 safety model:

- factor year;
- scope;
- geography;
- factor source/set/version;
- method compatibility;
- activity compatibility;
- energy type where applicable;
- category compatibility;
- data quality;
- no silent year fallback;
- no silent cross-scope fallback;
- no component factor used as a total.

Known cross-year factor candidate call sites remain a P17 implementation concern.

A factor count is not proof of E2E coverage.

If a valid factor cannot be established:

> fail closed → manual review / clarification.

Never invent a factor.

---

# 9. Manual Review / Honest Uncertainty

Manual review is a controlled success path.

Examples:

- ambiguous supplier;
- ambiguous waste semantics;
- insufficient extraction;
- unsupported category;
- missing/ambiguous factor;
- conflicting evidence;
- invalid contractual instrument;
- unclear Scope 2 method;
- unsupported geography.

Preserve original value, corrected value, actor, timestamp, reason, evidence, and downstream impact.

---

# 10. Security / Tenant Isolation

Security is evaluated using:

```text
actor
+
organization context
+
role
+
capability
+
delegation
```

Frontend controls are not security boundaries.

Sensitive workflows require both:

- positive ALLOW evidence;
- negative DENY evidence.

Consultants do not automatically become client administrators.

Cross-client and cross-tenant access must fail closed unless explicitly delegated.

---

# 11. Idempotency

P16 deterministic idempotency is preserved.

P17 accounting-defining dimensions must participate in the idempotency model.

Changing Scope 2 method, Scope 3 category, or another accounting-defining dimension must not silently reuse an incompatible result.

---

# 12. Reporting / Reportability

A route existing is not proof of a working reporting workflow.

Where reporting is claimed, verify:

```text
source
→ calculation
→ snapshot
→ validation/review
→ approval
→ reportability
→ report
→ evidence/provenance
→ UI
```

P17-I must produce a real verified reporting artifact where required.

---

# 13. P17 Phase Sequence

```text
P17-ARCH-03
      |
      v
P17-0  Discovery + Mapping + UI/UX Audit
      |
      v
P17-0 Independent Review / PO Gate
      |
      v
P17-A  Scope 2 Canonical Model + Factor Governance
      |
      v
P17-B / P17-C
      |
      v
P17-D
      |
      v
P17-E / P17-F / P17-G
      |
      v
P17-H  Lifecycle / Review / Reportability
      |
      v
P17-I  Reporting / Artefacts / Evidence
      |
      v
P17-J  Independent P17 Acceptance
```

The reconciled dependency remains:

`A → B/C → D → E/F/G → H → I → J`

P17-0 blocks P17-A and all later implementation.

---

# 14. P17-0 — Mandatory Discovery Gate

**Status: not yet authorized.**

P17-0 is read-only discovery/mapping.

It must not implement product code, migrations, schema, seed data, production changes, or new features.

### Required discovery

P17-0 must inventory:

1. actual repository/UI baseline;
2. UIUX-01 existing-vs-missing matrix;
3. reusable UI components;
4. staff/customer/consultant/client UX;
5. lifecycle UX;
6. ACTING FOR;
7. capability/permission/disabled states;
8. Scope 1/2/3 navigation;
9. all 15 Scope 3 category UX;
10. evidence/supplier/review/exception UX;
11. calculation/reportability/reporting/audit UX;
12. organization/consultant/client model;
13. capability/governance primitive;
14. lifecycle/state-machine sources;
15. role/authorization canonical source;
16. API/service/database ownership;
17. factor candidate call sites;
18. report/disclosure/artifact path;
19. schema implementation gaps;
20. reuse-vs-extend-vs-new decisions.

### Required P17-0 outputs

- permanent Markdown report;
- JSON discovery/mapping artifact;
- existing-vs-missing matrix;
- UI/UX mapping;
- capability representation recommendation;
- lifecycle mapping;
- authorization/role-source decision;
- dependency/blocker list;
- truthful verdict.

P17-0 should also produce explicit UI/UX recommendations before implementation begins.

---

# 15. Implementation Task Rules

Every Cline task must have:

- unique task ID;
- explicit authorization boundary;
- repository/branch;
- starting SHA;
- prerequisites;
- inspect-before-implement;
- existing-first reuse;
- no duplicate models;
- UI/UX requirements;
- backend authorization;
- RLS/tenant isolation;
- audit/provenance;
- idempotency;
- relevant tests;
- regression tests;
- permanent Markdown report;
- truthful verdict.

Cline must stop at the authorized boundary and must not declare PO closure.

---

# 16. Acceptance Model

Only **END-TO-END VERIFIED** counts as implementation acceptance.

Required chain:

```text
UI
→ API
→ authorization
→ domain/service
→ database
→ audit/provenance
→ calculation/reportability
→ UI final state
```

For security:

```text
ALLOW + DENY
```

For consultant/client:

```text
consultant
→ select client
→ ACTING FOR
→ delegated action
→ client-owned record
→ audit context
→ client isolation
```

For customer contribution:

```text
customer entry/upload
→ submission
→ validation
→ calculation
→ review
→ approval
→ reportability
```

---

# 17. Preserved P17 Acceptance Controls

The reconciled architecture preserves:

- 12 invariant tests;
- 11 double-counting controls;
- P16 non-regression;
- deterministic idempotency;
- tenant isolation;
- reportability lifecycle;
- factor safety;
- category identity;
- Scope 2 method identity;
- contractual instrument validation;
- customer governance boundaries;
- acting-for provenance.

These cannot be weakened to make tests pass.

---

# 18. Deferred Scope

Do not silently promote:

- numeric uncertainty/confidence;
- residual mix methodology;
- jurisdiction-specific REGO/REC/GO rules;
- grid-region-level factors;
- default spend-based methodology;
- detailed Category 2 methodology;
- detailed Category 10 methodology;
- detailed Category 11 methodology;
- Category 14 operating model;
- Category 15 expansion beyond approved scope;
- sold-product entity model;
- framework-specific disclosure content;
- Insight redesign;
- factor-library expansion;
- SEAI V4;
- production deployment;
- production database mutation;
- certification/audit claims.

---

# 19. Investor-Demo Workstream

The original investor-demo workplan remains the governing **demo objective**:

1. Foundation & Forensics
2. Canonical Demo Environment
3. Investor Demo Experience
4. Independent Acceptance & Rehearsal

Step 1's earlier forensic work is complete for the prior baseline. Later demo steps must now consume the frozen/reconciled P17 architecture where the customer experience depends on it.

Investor-demo readiness means:

- canonical environment;
- authorized release/schema;
- reproducible synthetic data;
- intentional identities/orgs/relationships;
- real E2E journeys;
- real deterministic calculations;
- traceable provenance/evidence where claimed;
- exercised workflows;
- honest failure states;
- repeatable reset/reseed/reverify;
- independent acceptance;
- presentation aligned to verified capability.

It does **not** mean production readiness, full roadmap completion, certification, or audit readiness.

---

# 20. Investor Stories

### A — CarbonTally calculates

`upload → extraction → mapping → validation → calculation → emissions result`

### B — CarbonTally operates

`work item → processing entity → assignment/reassignment → review/approval`

### C — CarbonTally explains

`emissions → snapshot → factor → source → evidence → Insight`

### D — CarbonTally is honest

`unsupported/ambiguous case → explicit reason → human action`

No fabricated chain. If a link does not exist, the presentation says so.

---

# 21. Canonical Demo Environment

Do not seed a large investor dataset before the required accounting architecture, lifecycle and UI are frozen.

After relevant P17 acceptance:

1. select canonical environment;
2. pin authorized release/schema;
3. validate/pin synthetic generator;
4. create canonical organizations;
5. create consultant/client relationships;
6. create users/delegated users;
7. seed realistic FY2025/FY2026 records;
8. include deliberate review/exception cases;
9. establish evidence/provenance;
10. exercise calculations;
11. exercise lifecycle;
12. exercise reporting;
13. exercise Insight;
14. verify tenant isolation;
15. verify reset/reseed repeatability.

Earlier pinned generator SHA:

`8ade2bf778d518d59924905849ab114ab2d082a0`

This must be revalidated before treating it as the active canonical generator.

---

# 22. Customer / Consultant Investor Experience

The final demonstration should present one coherent product:

```text
CarbonTally Staff
      |
      +--------------------------+
      |                          |
Direct Customer             Consultant
                                |
                                +-- Client A
                                +-- Client B
```

Consultants should be able to:

- manage their own accounting when enabled;
- manage client organizations through explicit relationships;
- switch client context;
- see ACTING FOR;
- act only within delegated authority;
- access client-owned records;
- preserve audit context.

Direct customers use the same CAMS.

---

# 23. P18 and P19

### P18

The old governance/reporting/framework prompt is **requirements source material only**.

Create a new P18 prompt after P17 acceptance, reconciled with:

- unified CAMS;
- customer contribution;
- consultant/client;
- acting-for;
- organization capabilities;
- lifecycle;
- UIUX-01;
- implemented Scope 2/3;
- factor governance;
- reporting artifacts.

Do not execute the old P18 prompt unchanged.

### P19

The old assurance/production-readiness prompt is also **requirements source material only**.

Create a new final acceptance prompt after the product state matures.

It should independently verify accounting, Scope 1/2/3, manual review, suppliers, factors, data quality, tenant isolation, delegation, lifecycle, reporting, evidence, provenance, assurance readiness, migration repeatability, disposable integration and production safety.

P19 does not itself authorize production.

---

# 24. Required Verification Pattern

```text
Cline implementation
        ↓
Cline report
        ↓
Independent verification
        ↓
Independent report
        ↓
PO decision
```

Architecture work follows the same principle.

Cline completion is never equivalent to independent acceptance.

---

# 25. Required Report Standard

Every Cline report must contain:

- task ID;
- date;
- repository;
- branch;
- starting SHA;
- ending SHA;
- scope;
- prerequisites;
- files inspected;
- files changed;
- migrations;
- tests;
- test results;
- security evidence;
- data/corpus impact;
- production safety;
- limitations;
- unresolved issues;
- exact verdict.

No fabricated PASS.

---

# 26. Production Safety

Unless a future explicit PO authorization says otherwise:

- no production DB connection;
- no production migration;
- no production seed;
- no production mutation;
- no production deployment;
- no production credentials;
- no production-data copying into demo.

---

# 27. Master Sequence From This Point

```text
CURRENT
  |
  v
P17-ARCH-03 — Independent Architecture Verification
  |
  +-- PASS --> PO authorization for P17-0
  |
  +-- PARTIAL/BLOCKED/FAIL --> PO review/reconciliation
                         |
                         v
                       P17-0
                         |
                         v
                P17-0 review / PO gate
                         |
                         v
                  P17-A through P17-I
                         |
                         v
                P17-J independent acceptance
                         |
                         v
                Canonical demo environment
                         |
                         v
                  Canonical seed/data
                         |
                         v
             Customer/consultant E2E UX
                         |
                         v
                  Investor rehearsal
                         |
                         v
              Independent demo acceptance
                         |
                         v
                 INVESTOR DEMO READY
                         |
                         v
                P18 governance/reporting
                         |
                         v
                 P19 final assurance
                         |
                         v
              Separate PO production decision
```

---

# 28. Old Prompt Status

| Prompt | Status |
|---|---|
| P17-IMPLEMENT-01 | Requirements library; **do not execute unchanged** |
| P18-IMPLEMENT-01 | Requirements library; rewrite after P17 |
| P19-ACCEPT-01 | Requirements library; rewrite after implementation state matures |

They remain useful because they contain detailed requirements, but they do not override the reconciled architecture.

---

# 29. Truthfulness Standard

Always distinguish:

```text
DOCUMENTED
≠ CODE EXISTS
≠ ROUTE WIRED
≠ AVAILABLE
≠ PERSISTED
≠ E2E VERIFIED
≠ INDEPENDENTLY VERIFIED
≠ PRODUCTION READY
```

A factor count is not proof of accounting.

A route is not proof of a workflow.

A database row is not proof of a user journey.

A unit test is not proof of E2E behavior.

A Cline PASS is not independent acceptance.

An investor demo is not production readiness.

---

# 30. Current Authorization Snapshot

| Workstream | Status |
|---|---|
| P16 | **PASS / CLOSED** |
| P17 ARCH-01 | **Architecture established / preserved** |
| P17 ARCH-02 | **RECONCILED / READY FOR INDEPENDENT VERIFICATION** |
| P17 ARCH-03 | **CURRENT INDEPENDENT VERIFICATION GATE** |
| P17-0 | **NOT YET AUTHORIZED** |
| P17-A | **NOT AUTHORIZED** |
| P17-B…P17-J | **NOT AUTHORIZED** |
| Canonical demo mutation | **NOT AUTHORIZED** |
| Investor-demo seeding | **NOT AUTHORIZED** |
| P18 | **NOT AUTHORIZED** |
| P19 | **NOT AUTHORIZED** |
| Production readiness | **NOT AUTHORIZED** |
| Production deployment | **NOT AUTHORIZED** |

---

# 31. Authoritative References

- `docs/architecture/CT-PO-P16-FINAL-VERIFICATION-20250925.md`
- `docs/architecture/CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md`
- `docs/architecture/CT-PO-P17-ARCH-02-RECONCILIATION-20250925.md`
- `docs/architecture/CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md`
- `docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md`
- `docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md`
- `CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924.md`
- `carbontally_handoff.md`

---

# 32. Final Rule

The immediate sequence is:

> **P17-ARCH-03 independent verification → PO decision → P17-0 discovery/mapping → independent/PO gate → P17-A.**

No implementation should jump ahead of this sequence.

This document is the current master planning/reference baseline. It does not replace authoritative phase reports and does not authorize production.
