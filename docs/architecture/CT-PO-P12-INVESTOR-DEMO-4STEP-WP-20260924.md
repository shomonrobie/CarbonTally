# CarbonTally Investor Demo — Formal 4-Step Workplan

**Reference:** `CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924`  
**Date:** 2026-09-24  
**Status:** PO WORKPLAN — PLANNING / AUTHORIZATION FRAMEWORK  
**Scope:** Investor-ready demonstration readiness only  
**Production readiness:** NOT IMPLIED  
**Production deployment:** NOT AUTHORIZED

---

## 1. Purpose

This workplan defines a controlled four-step path from the current CarbonTally product state to a truthful, repeatable, independently verified investor-ready demonstration.

The objective is **not** to complete the entire CarbonTally product roadmap.

The objective is to demonstrate a small number of coherent, real product journeys using the existing CarbonTally architecture and deterministic calculation/evidence capabilities, with only bounded implementation work where a genuine demo blocker is confirmed.

The four-step sequence is:

1. **Foundation & Forensics**
2. **Canonical Demo Environment**
3. **Investor Demo Experience**
4. **Independent Acceptance & Rehearsal**

No step automatically authorizes the next step.

---

# 2. Current Baseline

The September 24, 2026 product-capability / investor-demo forensic study established that CarbonTally's implemented capability surface is substantially broader than its current demonstration surface.

The principal problem is currently a combination of:

- demo-environment/schema divergence;
- insufficient populated demo data;
- absent live evidence-line materialisation in the available demo environments;
- unexercised operational workflows;
- incomplete demo tooling;
- unverified repeatability;
- several documented product/code gaps;
- stale or divergent documentation;
- absence of a safe read-only production inspection path.

The study also established that the current product already contains substantial capabilities including:

- customer/consultant/processing-entity/internal-staff persona and authorization structures;
- deterministic emissions calculation;
- calculation snapshots and provenance;
- Source Evidence Viewer;
- processing-entity assignment/reassignment infrastructure;
- two messaging planes;
- report lifecycle;
- document processing and honest failure states;
- Insight foundation with deterministic tools;
- P2 temporal comparison;
- P3 data-quality/reproducibility capability, with P3 overall still requiring final PO closure.

These existing capabilities must be demonstrated truthfully rather than replaced with artificial demo-only behavior.

---

# 3. Target Definition — “Investor Demo Ready”

CarbonTally is **INVESTOR DEMO READY** only when all of the following are true:

1. A canonical demo environment has been explicitly selected and documented.
2. The environment uses the current authorized release schema/code.
3. The approved synthetic generator/version is pinned and reproducible.
4. Demo identities, organisations, relationships and workflow states are intentionally seeded.
5. The principal demonstration journeys execute end-to-end.
6. Demonstrated emissions numbers are backed by real deterministic calculation records.
7. Demonstrated explanations can trace through calculation/provenance/factor/source/evidence where the journey claims such traceability.
8. Processing-entity workflows shown in the presentation have actually been exercised.
9. Reporting lifecycle states shown in the presentation have actually been exercised.
10. Insight interactions shown in the presentation use actual authorized capabilities and real demo data.
11. Unsupported capabilities are explicitly excluded from the presentation.
12. Security and tenant-isolation checks required by the demo are independently verified.
13. Known failure scenarios behave honestly and are demonstrable.
14. Reset/reprovision/reseed/reverify is repeatable.
15. An independent verifier completes the final acceptance gate without modifying the product.
16. The final investor presentation/script is aligned with what was actually verified.

**Investor Demo Ready does not mean:**

- production ready;
- audit/certification ready;
- fully feature complete;
- all Insight questions supported;
- all Scope 3 Categories 1–15 implemented;
- market-based Scope 2 implemented;
- Scope 1 decomposition complete;
- supplier intelligence complete;
- variance/reduction intelligence complete;
- billing complete;
- L7 complete;
- L8 complete.

---

# 4. Four-Step Overview

| Step | Name | Primary outcome | Mutation | Independent verification |
|---|---|---|---|---|
| **1** | Foundation & Forensics | Freeze the demo scope and remove uncertainty before mutation | Primarily read-only | Required for selected workflow findings |
| **2** | Canonical Demo Environment | Produce a controlled, reproducible demo dataset/environment | Yes, bounded | Required |
| **3** | Investor Demo Experience | Make the approved journeys demonstrable end-to-end | Yes, bounded | Required |
| **4** | Independent Acceptance & Rehearsal | Prove the actual investor demo is truthful, secure and repeatable | No product fixes by verifier | Required |

---

# STEP 1 — FOUNDATION & FORENSICS

## Objective

Resolve the known uncertainties before changing the canonical demo environment.

This step is intentionally non-mutating wherever possible.

## Workstreams

### 1.1 Documentation reconciliation

Reconcile current documentation against the actual `p8-release-reconciled` repository state.

At minimum review:

- P12 preflight;
- Product Capability / Investor-Demo Forensic Study;
- Insight Capability Coverage Matrix;
- P2 closure;
- P3 implementation and verification records;
- INS-01 closure;
- Source Evidence Viewer records;
- demo-lab documentation;
- stale capability/tool-count references;
- X2/X7 and related documentation divergences.

The output must distinguish:

- implemented;
- independently verified;
- PO closed;
- demo-ready;
- partial;
- blocked;
- not authorized.

### 1.2 Independent workflow verification

Independently verify the workflows that may be used in the investor demonstration, including where applicable:

- processing-entity assignment;
- reassignment;
- partial release/completion;
- processing-entity workspace;
- PE messaging;
- consultant/client relationship;
- report lifecycle;
- relevant master-data CRUD;
- authorization boundaries;
- tenant isolation;
- current Demo Lab verification harness.

The verifier must not fix defects.

### 1.3 Evidence-line forensic/design study

Determine exactly why the current environments contain zero `evidence_line_items`.

Establish whether the cause is:

- offline-only materialisation;
- missing online materialisation;
- missing linkage;
- demo-seeding omission;
- another concrete implementation/data-path issue.

Determine the smallest safe implementation required for the approved investor journey.

No evidence implementation is authorized by this workplan merely because the study identifies a gap.

### 1.4 Freeze the demonstration scope

Freeze the initial investor demonstration around four stories:

**A. Normal calculation**

Upload → extraction → mapping → validation → calculation → emissions result.

**B. Operational workflow**

Work item → processing entity → assignment/reassignment → review/approval.

**C. Explainability**

Emissions number → calculation snapshot → factor → source document → evidence → Insight explanation.

**D. Honest failure**

Unsupported/ambiguous document → explicit reason → appropriate human action.

The final script may use fewer or more individual screens within these four stories, but it must remain bounded.

## Step 1 deliverables

1. Documentation reconciliation record.
2. Independent workflow verification report.
3. Evidence-line forensic/design report.
4. Frozen investor-demo capability scope.
5. Step-1 decision record identifying all remaining blockers and the exact implementation work required for Step 2/3.

## Step 1 exit criteria

Step 1 is complete only when:

- the canonical demo environment direction is confirmed;
- the four demonstration stories are frozen;
- required data entities and workflow states are known;
- evidence requirements are understood;
- genuine code/data blockers are distinguished from demo-environment problems;
- no unresolved critical uncertainty would make the Step-2 reset unsafe.

## Step 1 authorization boundary

**Authorized in principle:**

- read-only inspection;
- forensic analysis;
- documentation reconciliation;
- independent verification;
- creation of reports/decision records.

**Not authorized by Step 1:**

- Demo Lab reset;
- destructive database operations;
- production database access;
- production mutation;
- evidence backfill;
- new accounting methodology;
- mapping fallback;
- billing implementation;
- L7/L8 implementation;
- production deployment.

---

# STEP 2 — CANONICAL DEMO ENVIRONMENT

## Objective

Create one controlled and reproducible environment that represents the investor demonstration.

## Canonical environment direction

The current recommended direction is:

> **Current Demo Lab + current `p8-release-reconciled` schema + pinned synthetic generator.**

The historical `postgres` investor/UAT dataset remains a historical reference and must not silently become the canonical demo environment.

The pinned synthetic generator identified by the forensic study is:

`8ade2bf778d518d59924905849ab114ab2d082a0`

The exact checkout and invocation must be confirmed during Step 1 before mutation.

## Workstreams

### 2.1 Environment safety

Before reset/reprovision:

- prove the target database is the intended Demo Lab;
- prove it is not production;
- record target identity;
- record current state;
- establish reset scope;
- establish recovery/rollback procedure.

### 2.2 Schema alignment

Bring the Demo Lab to the current authorized release migration state.

This includes the current Insight migrations required by the investor demonstration.

No unrelated migration repair is authorized merely because the chain contains unrelated historical defects.

### 2.3 Controlled synthetic seed

Seed only the approved demonstration topology.

The working target identified by the forensic study is approximately:

- 2 direct customer organisations with meaningful role coverage;
- 1 consultant firm;
- 2 client organisations;
- 2 processing entities;
- processing-entity manager/staff identities;
- required internal operational roles;
- approximately 3 batches;
- approximately 12–15 work items across meaningful states;
- assignment/reassignment examples;
- conversations covering the authorized messaging planes;
- 2 reports with different lifecycle states;
- at least 2 evidence line items once the evidence path is authorized and available;
- 2 Insight interactions plus one honest no-data case;
- meaningful Scope 1 data across two periods;
- scripted authorization DENY cases.

These are **planning targets, not fixed counts**. Final counts must be frozen in Step 1.

### 2.4 Verification seed

After provisioning, verify:

- identity topology;
- organisation relationships;
- role boundaries;
- document corpus;
- processing states;
- assignment states;
- messaging;
- report lifecycle;
- calculation records;
- evidence records;
- Insight records;
- security controls.

## Step 2 deliverables

1. Canonical Demo Lab environment.
2. Frozen seed manifest.
3. Pinned generator reference.
4. Reset/reprovision script or controlled procedure.
5. Expected-count verification report.
6. Environment provenance record.
7. Repeatability/recovery evidence.

## Step 2 exit criteria

- current authorized schema is present;
- approved data topology exists;
- deterministic calculation records exist;
- required evidence exists or an explicitly accepted blocker remains;
- required workflow states exist;
- Insight is operational against the seeded environment;
- security checks pass;
- reset/reprovision procedure has been successfully exercised;
- independent verification passes.

---

# STEP 3 — INVESTOR DEMO EXPERIENCE

## Objective

Turn the verified canonical environment into a coherent investor demonstration.

This is not a general product-development phase.

Only work required to demonstrate the frozen Step-1 journeys is in scope.

## Workstreams

### 3.1 Calculation journey

Demonstrate:

- real document;
- extraction;
- mapping;
- validation;
- deterministic calculation;
- emissions result;
- underlying calculation/provenance.

### 3.2 Operational journey

Demonstrate:

- work item;
- processing entity;
- assignment;
- reassignment or partial completion where appropriate;
- review/approval state;
- relevant operational visibility.

### 3.3 Explainability journey

Demonstrate a real path:

**number → calculation → factor → source → evidence → Insight**

Every displayed link must resolve to real records.

No fabricated evidence.

No simulated audit trail.

### 3.4 Insight journey

Demonstrate only the authorized Insight capabilities actually populated in the canonical environment.

Possible presentation examples include:

- identified calculation explanation;
- bounded discovery;
- aggregation;
- temporal comparison;
- data-quality explanation;
- reproducibility explanation;
- provenance/evidence navigation.

The exact questions must be frozen after Step 2 verification.

### 3.5 Honest failure journey

Demonstrate at least one meaningful failure such as:

- unsupported document;
- ambiguous mapping;
- no matching factor;
- no-data Insight question.

The system must explain what happened and what human action is required.

### 3.6 Presentation polish

Only after the functional journeys work:

- remove misleading/stale navigation;
- ensure meaningful empty/error states;
- make presenter navigation coherent;
- align terminology;
- prepare a concise presenter script;
- ensure every investor claim maps to a verified capability.

## Step 3 deliverables

1. Investor demo navigation/presentation flow.
2. Presenter script.
3. Four demonstrated journeys.
4. Evidence/Insight demonstration path.
5. Honest failure demonstration.
6. Demo verification script.
7. Known-limitations statement.
8. Updated demo documentation.

## Step 3 exit criteria

- all four approved stories execute;
- demonstrated data is truthful;
- evidence claims are traceable;
- Insight claims match actual capabilities;
- no unsupported product claims remain in the presentation;
- security boundaries remain intact;
- demo can be reset and reproduced;
- implementation changes are committed and independently verified.

---

# STEP 4 — INDEPENDENT ACCEPTANCE & REHEARSAL

## Objective

Establish that the investor demo can actually be delivered reliably by someone other than the implementer.

## Independent verification areas

### Product flow

- authentication;
- organisation selection;
- upload;
- extraction;
- mapping;
- validation;
- calculation;
- operational workflow;
- reporting;
- evidence;
- Insight;
- messaging where demonstrated.

### Security

Verify:

- cross-tenant access denial;
- role-based restrictions;
- processing-entity boundaries;
- customer/consultant boundaries;
- Insight authorization;
- evidence/raw-content restrictions.

### Data truthfulness

Verify:

- demonstrated emissions originate from actual deterministic records;
- factors are genuine records;
- calculation snapshots are genuine;
- evidence references resolve;
- reports correspond to actual data;
- no demo-only fabricated values exist.

### Failure honesty

Verify that the selected failure scenarios:

- fail for the documented reason;
- do not silently fabricate results;
- expose appropriate next actions.

### Repeatability

Perform:

**reset → provision → seed → verify → run demo**

at least once as a controlled rehearsal.

Where appropriate, repeat the critical subset to establish deterministic behaviour.

### Presenter rehearsal

The final rehearsal must use the actual investor script.

The verifier should record:

- broken links;
- missing states;
- confusing navigation;
- unexpected latency/blockers;
- claims that cannot be reproduced;
- evidence that does not resolve;
- security or tenant-boundary surprises.

## Step 4 deliverables

1. Independent demo acceptance report.
2. Final demo script.
3. Final known-limitations statement.
4. Reprovision/recovery procedure.
5. Final demo environment identity/provenance record.
6. PO Investor Demo Readiness closure record.

## Step 4 final gate

The final PO decision may be:

### `INVESTOR DEMO READY`

or:

### `INVESTOR DEMO READY WITH DISCLOSED NON-BLOCKING LIMITATIONS`

or:

### `NOT YET INVESTOR DEMO READY`

No “READY” status may be inferred solely from Cline implementation completion.

---

# 5. Explicit Out-of-Scope Roadmap Items

Unless separately authorized, the following remain outside this four-step investor-demo workplan:

- full Scope 3 Categories 1–15 implementation;
- market-based Scope 2 methodology;
- Scope 1 decomposition;
- supplier persistence/analytics;
- variance/attribution methodology;
- reduction/decision intelligence;
- unrestricted natural-language database querying;
- RAG/knowledge-base implementation;
- consultant/auditor persona expansion;
- billing/payment-provider implementation;
- L7 retention/deletion implementation;
- L8 commercial implementation;
- production deployment;
- production database mutation;
- certification/audit claims.

---

# 6. Governance and Authorization Rules

## Cline

Cline may implement only the explicitly authorized step/task.

Cline must:

- inspect before modifying;
- preserve scope boundaries;
- run relevant tests;
- create a permanent implementation report;
- commit and push;
- leave the release branch aligned;
- stop at the authorized boundary;
- not declare PO closure.

## Independent verifier

The independent verifier must:

- work from the committed release state;
- independently reproduce the acceptance criteria;
- not repair defects;
- not modify product/source/test/config/schema/migration files;
- create only the explicitly authorized verification report;
- report PASS, PASS WITH NON-BLOCKING OBSERVATIONS, FAIL, or BLOCKED/INCONCLUSIVE as applicable.

## Product Owner

PO controls:

- step authorization;
- scope changes;
- acceptance of observations;
- closure;
- investor-readiness declaration;
- any transition to production-readiness planning.

---

# 7. Required Evidence Chain for the Investor Narrative

The strongest investor demonstration should make the following chain visible:

**Source document**

↓

**Extracted activity/data**

↓

**Mapped emission factor**

↓

**Validation**

↓

**Deterministic calculation**

↓

**Calculation snapshot**

↓

**Emissions result**

↓

**Provenance**

↓

**Source Evidence Viewer / evidence**

↓

**CarbonTally Insight explanation**

This chain is a central demonstration objective.

Where any link is unavailable, the presentation must say so rather than implying that the link exists.

---

# 8. Demo Narrative

The preferred narrative structure is:

### Act 1 — “CarbonTally calculates.”

Show a real document becoming a deterministic emissions result.

### Act 2 — “CarbonTally operates.”

Show human processing workflow, assignment/reassignment and controlled review.

### Act 3 — “CarbonTally explains.”

Show an emissions number traced back through calculation, factor, source and evidence, followed by an Insight explanation.

### Act 4 — “CarbonTally is honest about uncertainty.”

Show an unsupported or ambiguous case and demonstrate the system refusing to invent an answer.

This narrative is intentionally more important than demonstrating a large volume of synthetic records.

---

# 9. Workplan Sequence

```text
STEP 1
Foundation & Forensics
        |
        v
PO confirms scope / blockers
        |
        v
STEP 2
Canonical Demo Environment
        |
        v
Independent environment verification
        |
        v
STEP 3
Investor Demo Experience
        |
        v
Independent feature/demo verification
        |
        v
STEP 4
Independent Acceptance & Rehearsal
        |
        v
PO FINAL GATE
        |
        +----> INVESTOR DEMO READY
        |
        +----> READY WITH DISCLOSED LIMITATIONS
        |
        +----> NOT YET READY
```

---

# 10. Current PO Status

| Area | Status |
|---|---|
| Product capability / investor-demo forensic study | **CLOSED — PLANNING ARTIFACT** |
| P2 temporal comparison | **CLOSED** |
| INS-01 Insight foundation | **CLOSED** |
| Source Evidence Viewer | **Implemented / independently verified** |
| P3-IV-01 | **CLOSED / independently verified** |
| P3 overall | **NOT YET PO-CLOSED** |
| Canonical demo environment | **NOT YET AUTHORIZED FOR MUTATION** |
| Demo reset/reprovision | **NOT YET AUTHORIZED** |
| Evidence-line materialisation | **REQUIRES EV-01 DECISION** |
| PE workflow investor demonstration | **REQUIRES INDEPENDENT WORKFLOW VERIFICATION** |
| Reporting approval demonstration | **REQUIRES WORKFLOW VERIFICATION/EXERCISE** |
| Investor demo experience implementation | **NOT YET AUTHORIZED** |
| Final investor-demo acceptance | **NOT YET AUTHORIZED** |
| Production readiness | **SEPARATE / NOT IMPLIED** |
| Production deployment | **NOT AUTHORIZED** |

---

# 11. Immediate Next PO Action

The next authorized planning/forensic work should be **Step 1**, beginning with:

1. documentation reconciliation;
2. independent workflow verification;
3. evidence-line forensic/design study;
4. freezing the exact investor-demo scope.

Only after Step 1 produces sufficient evidence should the PO authorize the canonical Demo Lab reset/reprovision.

---

# 12. Final Principle

The investor demonstration must prove **what CarbonTally actually does**, not what the roadmap says it will eventually do.

The standard is:

> **Real data → deterministic calculation → traceable provenance → evidence → explainable Insight → honest failure handling → independently verified demonstration.**

The four-step workplan is therefore a controlled path to demonstrating existing CarbonTally capability credibly, while preventing investor-demo work from silently becoming unrestricted product development or production deployment.
