# CarbonTally Handoff

**Handoff reference:** `CT-HANDOFF-20260924-01`  
**Prepared:** 2026-09-24  
**Purpose:** Preserve the current CarbonTally PO/project state before clearing this session.  
**Authority:** Project conversation state, supplied project reports, and the formal 4-step investor-demo workplan.  
**Important:** Facts and unknowns are explicitly separated below. No unverified repository state is presented as current fact.

---

# 1. Goal

## Fact — current task

The immediate project goal is to take CarbonTally from its current implemented-but-not-yet-investor-demo-ready state to a **truthful, repeatable, independently verified investor-ready demonstration**.

The formal workplan reference is:

`CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924`

The workplan defines exactly four controlled steps:

1. **Foundation & Forensics**
2. **Canonical Demo Environment**
3. **Investor Demo Experience**
4. **Independent Acceptance & Rehearsal**

## Exact result required

The final result is:

> **INVESTOR DEMO READY**

or, if appropriate:

> **INVESTOR DEMO READY WITH DISCLOSED NON-BLOCKING LIMITATIONS**

The final status must be based on independent verification and a PO decision.

It must **not** be interpreted as:

- production readiness;
- audit/certification readiness;
- full product completion;
- completion of all Insight questions;
- completion of all Scope 3 Categories 1–15;
- completion of market-based Scope 2;
- completion of Scope 1 decomposition;
- completion of supplier/variance/reduction intelligence;
- billing completion;
- L7/L8 completion;
- production deployment authorization.

## Four intended investor stories

The demonstration should be bounded around:

### A — Normal calculation

Upload → extraction → mapping → validation → calculation → emissions result.

### B — Operational workflow

Work item → processing entity → assignment/reassignment → review/approval.

### C — Explainability

Emissions number → calculation snapshot → factor → source document → evidence → Insight explanation.

### D — Honest failure

Unsupported/ambiguous document → explicit reason → appropriate human action.

These stories are the demonstration target; they are not permission to implement unrelated roadmap capabilities.

---

# 2. Current State

## 2.1 Confirmed working / implemented capabilities

The project records establish the following capabilities as implemented, with varying verification/closure status:

- deterministic emissions calculation;
- calculation snapshots and provenance;
- Source Evidence Viewer;
- customer/consultant/processing-entity/internal-staff authorization structures;
- processing-entity assignment/reassignment infrastructure;
- two messaging planes;
- report lifecycle;
- document processing and honest failure handling;
- Insight deterministic foundation;
- bounded Insight discovery;
- bounded Insight aggregation;
- aggregate provenance;
- bounded temporal comparison;
- bounded data-quality intelligence;
- bounded calculation reproducibility;
- technical Insight rate limiting;
- P2 temporal comparison, **PO CLOSED**;
- P3-IV-01 targeted remediation, **independently re-verified and PO CLOSED**.

## 2.2 Confirmed status of major Phase 8 areas

### INS-01 Insight foundation

**Status: CLOSED.**

It was independently verified with PASS WITH NON-BLOCKING OBSERVATIONS and subsequently PO-closed.

The current Insight foundation contains 10 registered tools and 15 answer states according to the latest forensic/preflight records.

### P2 Temporal Comparison

**Status: CLOSED.**

The historical test-count discrepancy was reconciled.

Actual dedicated P2 test inventory:

- 43 tests;
- 43/43 passing in final independent verification.

The earlier “79” figure was corrected in the documentation; the retained evidence indicates it was likely a pytest progress percentage misread, although the exact keystroke/history origin is not independently provable.

### P3 Data Quality + Audit/Reproducibility

**Status: IMPLEMENTED and independently verified, but P3 overall is NOT YET PO-CLOSED.**

P3 had 48 dedicated tests and passed its dedicated suite.

P3-IV-01 was independently re-verified and PO-closed.

P3-IV-01's remaining accepted observation is important:

- a partially-uncheckable period can still return `success/all_checks_passed` when at least one record is checkable and no finding exists;
- `uncheckable_records` remains available as a truthful carrier;
- this was not reopened after verification.

Other P3 follow-ups/decisions remain open according to the current project records.

### Source Evidence Viewer

**Status: IMPLEMENTED / INDEPENDENTLY VERIFIED.**

It is treated as a core CarbonTally capability and intended reusable evidence destination.

However, the current investor-demo environments have an evidence-population problem: the forensic study found zero `evidence_line_items`.

### Product capability / investor-demo forensic study

**Status: CLOSED as a planning/forensic artifact.**

Its main conclusion is that CarbonTally's implemented capability surface is substantially broader than its current demonstration surface.

The principal investor-demo problem is therefore not simply “build more product”; it is primarily:

- environment/schema divergence;
- thin demo data;
- missing/empty evidence materialisation in the demo environments;
- unexercised workflows;
- incomplete demo tooling;
- unverified repeatability;
- documentation divergence;
- several genuine smaller product/code gaps.

## 2.3 Current demo blockers

Confirmed from the latest forensic study/preflight:

1. Canonical demo environment has not yet been formally mutated/reprovisioned.
2. Existing Demo Lab was stale relative to the current release schema at the time of the study.
3. Insight migrations were absent from the then-observed Demo Lab.
4. Evidence line items were zero in the examined environments.
5. Processing-entity workflow is implemented but insufficiently populated/exercised for demonstration.
6. Messaging is implemented but insufficiently populated/exercised for demonstration.
7. Reporting lifecycle exists but the investor demonstration has not yet exercised the required approval/final states.
8. Demo reset/reprovision/reseed/reverify has not yet been established as a verified repeatable rehearsal.
9. Only a small subset of the synthetic mapping corpus currently produces matched/calculated scenarios.
10. Spend-based factor coverage remains a known gap.
11. Some historical/demo harness verification remains unresolved.
12. Some stale documentation/contracts remain to be reconciled.
13. No safe read-only production inspection path was available in the forensic study.

## 2.4 What is untested / not yet independently established

The following should not be described as demo-verified until Step 1/Step 4 evidence exists:

- complete PE investor workflow;
- PE assignment/reassignment/release demonstration;
- PE workspace end-to-end demonstration;
- PE messaging demonstration;
- consultant/client workflow demonstration;
- reporting lifecycle demonstration in the intended investor dataset;
- master-data CRUD demonstration in the intended demo environment;
- current Demo Lab reset → provision → seed → verify repeatability;
- live RLS behaviour in the canonical demo environment;
- complete evidence-line materialisation path in the canonical demo environment;
- final Insight investor demonstration against the canonical seeded dataset;
- final four-story investor rehearsal.

## 2.5 Known pre-existing issues

These are not to be silently folded into the investor-demo work:

- Review/SLA related test failures;
- stale migration-count pin(s) where already documented;
- `reporting/audit-activity` HTTP 500 / F-T1-001;
- cross-tenant factor metadata issue;
- DR-007 / historical demo verification issues where still applicable.

Each must be classified during the relevant verification rather than silently repaired.

---

# 3. Active Files

The paths below are the important project artifacts identified by the current project records.

## Authoritative repository / release location

`/home/shomonrobie/ct_93d5cdd`

**Why it matters:** authoritative release checkout used for Phase 8 work.

**Expected release branch:** `p8-release-reconciled`.

**Remote:** `github`.

## Current formal 4-step workplan

`CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924.md`

**Why it matters:** formal PO workplan defining the four investor-demo steps, gates, scope boundaries, deliverables, and final readiness criteria.

## Latest product capability / investor-demo forensic study

`docs/architecture/CT-PO-PRODUCT-CAPABILITY-INVESTOR-DEMO-STUDY-20260924.md`

**Why it matters:** principal forensic source for current product capability, personas, workflows, demo topology, blockers, environment recommendation, and PO decision candidates.

## P12 investor-demo readiness preflight

`docs/architecture/CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md`

**Why it matters:** broad earlier P12/L7/L8/demo preflight; documents demo infrastructure, blockers, proposed packages and governance dependencies.

## P12 readiness preflight

`docs/architecture/CT-PO-P12-INVESTOR-DEMO-READINESS-PREFLIGHT-20260923.md`

**Why it matters:** detailed P12 gate/backlog and current Demo Lab evidence before the later forensic study.

## Insight architecture reference v2

`docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md`

**Why it matters:** active product/architecture reference for the intended Insight capability families and answer-to-evidence design. It is not blanket implementation authorization.

## Insight Question Library

`docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md`

**Why it matters:** coverage/acceptance catalogue for candidate Insight questions; not 400+ separately authorized features.

## Insight Capability Coverage Matrix

`docs/architecture/CarbonTally_PO_Insight_Capability_Coverage_Matrix_2026-09-22.md`

**Why it matters:** PO capability-family status, dependencies, acceptance depth and authorization boundaries.

## INS-01 closure reconciliation

`docs/architecture/CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md`

**Why it matters:** permanent PO record for the closed Insight foundation.

## P2 implementation report

`docs/architecture/CT-P8-INSIGHT-TEMPORAL-COMPARISON-IMPLEMENTATION-20260922.md`

**Why it matters:** implementation evidence for P2.

## P2 independent verification

`docs/architecture/CT-P8-INSIGHT-P2-INDEPENDENT-VERIFICATION-20260923.md`

**Why it matters:** independent P2 verification evidence, if present under this exact path in the current checkout. The exact current repository path must be rechecked before relying on it.

## P2 PO closure

`docs/architecture/CarbonTally_PO_P2_Temporal_Comparison_Closure_2026-09-23.md`

**Why it matters:** permanent PO closure record for P2.

## P3 implementation report

`docs/architecture/CT-P8-INSIGHT-DATA-QUALITY-AUDIT-REPRODUCIBILITY-IMPLEMENTATION-20260923.md`

**Why it matters:** implementation evidence for P3.

## P3 independent verification

`docs/architecture/CT-P8-INSIGHT-P3-INDEPENDENT-VERIFICATION-20260923.md`

**Why it matters:** independent P3 verification evidence.

## P3-IV-01 remediation

`docs/architecture/CT-P8-INSIGHT-P3-IV01-REMEDIATION-20260923.md`

**Why it matters:** exact targeted remediation record.

## P3-IV-01 re-verification

`docs/architecture/CT-P8-INSIGHT-P3-IV01-REVERIFICATION-20260923.md`

**Why it matters:** independent verification evidence for the closed P3-IV-01 defect.

## Source Evidence Viewer implementation

`docs/architecture/CT-P8-SOURCE-EVIDENCE-VIEWER-IMPLEMENTATION-20260922.md`

**Why it matters:** implementation record for the reusable evidence destination.

## Source Evidence Viewer independent verification

`docs/architecture/CT-P8-SOURCE-EVIDENCE-VIEWER-OHD-VERIFICATION-20260922.md`

**Why it matters:** independent verification record for the Source Evidence Viewer.

## Demo Lab

`tools/demo_lab/`

**Why it matters:** current intended infrastructure for controlled investor-demo provisioning, reset and verification.

## Synthetic document generator

`/home/shomonrobie/carbon_tally_synthetic_documents`

**Why it matters:** external/offline synthetic corpus generator identified by the forensic study. Required pinned commit:

`8ade2bf778d518d59924905849ab114ab2d082a0`

It must remain external, pinned, and unmodified unless separately authorized.

## Historical investor demo data report

`CARBONTALLY_V3_INVESTOR_DEMO_DATA_REPORT.md`

**Why it matters:** historical demo dataset evidence. It must not silently be treated as the current canonical demo environment.

## Historical investor-scale UAT audit

`CARBONTALLY_V3_INVESTOR_SCALE_ACCEPTANCE_AUDIT.md`

**Why it matters:** historical investor/UAT findings, including prior evidence, workflow and demo defects.

---

# 4. Changes Made

## 4.1 Phase 8 / Insight foundation

Fact:

- I1, I2 and I4/I5/I6 foundations were implemented and independently verified in earlier Phase 8 work.
- INS-01 discovery/aggregation/provenance/rate-limiting foundation was implemented and independently verified.
- INS-01 was subsequently PO-closed.

Result:

- Insight has a bounded deterministic tool architecture.
- Source Evidence Viewer is available as the intended reusable evidence destination.
- Technical rate limiting is implemented.
- Commercial/I8 authorization remains separate.

## 4.2 P1 Capability Coverage Matrix

Fact:

P1 created the capability-family matrix covering 19 Insight capability families.

Result:

- 19/19 families recorded;
- implementation/partial/missing distinctions documented;
- dependencies and authorization boundaries documented;
- P1 was PO-closed as a documentation/governance artifact.

## 4.3 P2 Temporal Comparison

Fact:

P2 implemented bounded two-period comparison.

Result:

- explicit two periods;
- deterministic absolute and percentage change;
- zero baseline percentage is unavailable/null;
- bounded grouping;
- provenance reuse;
- P2 dedicated test inventory reconciled to 43 tests;
- independent verification passed;
- PO closure completed.

## 4.4 P3 Data Quality + Reproducibility

Fact:

P3 implemented two bounded tools:

- `insight_data_quality`;
- `insight_calculation_reproducibility`.

Result:

- dedicated P3 suite: 48 tests;
- independent verification passed with a non-blocking observation;
- P3-IV-01 was identified as a genuine defect;
- targeted remediation was implemented;
- P3-IV-01 was independently re-verified;
- P3-IV-01 is PO-closed;
- P3 as a whole remains open pending remaining PO decisions/closure.

## 4.5 P3-IV-01 remediation

Fact:

The defect where a period contained rows but zero checkable records was corrected.

Expected corrected result:

`success / no_checkable_records`

instead of:

`success / all_checks_passed`

when `checked == 0` and `uncheckable > 0`.

Verification:

- original defect reproduced;
- corrected behaviour reproduced;
- P3 48/48 passed;
- P2 43/43 passed;
- Insight regression 398 passed;
- full unit suite still had four pre-existing failures;
- no migration/catalogue/P2/frontend changes were introduced.

## 4.6 Product Capability / Investor-Demo Forensic Study

Fact:

A read-only forensic study was completed and committed.

Reported commit:

`3c38cbc59c95c04ea434ae128f86c94fd4b69190`

The report was approximately 983 lines / 113 KB and report-only.

Result:

- no production mutation;
- no backend/frontend/schema/demo-data mutation;
- canonical Demo Lab direction recommended;
- investor-demo blockers identified;
- approximate identity/data topology proposed;
- PO decision candidates D-P1 through D-P10 identified.

## 4.7 Formal four-step workplan

Fact:

The formal workplan was created:

`CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924`

It establishes:

- Step 1: Foundation & Forensics;
- Step 2: Canonical Demo Environment;
- Step 3: Investor Demo Experience;
- Step 4: Independent Acceptance & Rehearsal.

The workplan does **not** itself authorize Demo Lab reset/reprovision or production mutation.

---

# 5. Current Branch and Uncommitted Work

## Last verified repository state

**Fact from the latest project records:**

- repository: `/home/shomonrobie/ct_93d5cdd`;
- branch: `p8-release-reconciled`;
- remote: `github`;
- latest specifically recorded forensic-study commit: `3c38cbc59c95c04ea434ae128f86c94fd4b69190`;
- at that point the branch and remote were aligned `0/0`;
- the working tree contained known pre-existing/untracked PO/ChatGPT artifacts.

## Current exact repository state

**UNKNOWN / NOT VERIFIED in this handoff generation.**

The current execution environment does not expose `/home/shomonrobie/ct_93d5cdd`, so a fresh `git status`, branch check, and current HEAD check could not be performed.

Therefore this handoff deliberately does **not** claim that the above commit/branch/cleanliness is the live state at the moment this file is written.

Before any implementation begins after session handoff, run:

```bash
cd /home/shomonrobie/ct_93d5cdd
git branch --show-current
git status --short --branch
git log -1 --oneline
git remote -v
```

Expected branch, based on the last verified project record:

```text
p8-release-reconciled
```

Known pre-existing untracked PO/ChatGPT artifacts must not be mistaken for implementation changes.

---

# 6. Facts vs Guesses / Unresolved Items

## Facts

- The investor-demo objective is governed by `CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924`.
- Four controlled steps are defined.
- The current product capability surface is broader than the current demo surface.
- Demo Lab was stale relative to the current release schema in the latest forensic observation.
- Evidence-line population was zero in the examined environments.
- PE/messaging/reporting capabilities exist in code but were not sufficiently exercised in the intended investor demo.
- P2 is PO-closed.
- P3-IV-01 is PO-closed.
- P3 overall is not PO-closed.
- Demo Lab mutation/reprovision has not been authorized.
- Production deployment is not authorized.
- The pinned synthetic generator SHA is `8ade2bf778d518d59924905849ab114ab2d082a0`.

## Unknown / must not be guessed

- The exact current Git HEAD after the workplan file was created.
- The exact current `git status`.
- Whether the project root currently contains an already-existing `carbontally_handoff.md`.
- Whether the Demo Lab has been changed since the forensic study.
- Whether the Demo Lab migrations/data/evidence state has changed since the forensic study.
- Whether any new implementation occurred after the forensic study.
- Whether PE/reporting/messaging workflows have been independently verified since the forensic study.
- Whether the evidence-line materialisation issue has been implemented or resolved since the forensic study.
- Whether the production environment can now be safely inspected read-only.
- Whether the final investor demo can currently be executed end-to-end.

No assumption should be promoted to fact without a fresh repository/environment check.

---

# 7. Next Step — Ordered

## 1. Verify repository ground truth

Before any implementation:

```text
branch → HEAD → status → remote alignment
```

Confirm the actual current release state.

## 2. Begin Step 1 — Foundation & Forensics

The first active work should be:

### 2A. Documentation reconciliation

Reconcile stale documentation against the current repository.

### 2B. Independent workflow verification

Independently verify:

- PE assignment/reassignment/release;
- PE workspace;
- PE messaging;
- consultant/client relationship;
- reporting lifecycle;
- relevant master-data CRUD;
- authorization/tenant isolation;
- Demo Lab verification harness.

No verifier fixes.

### 2C. EV-01 evidence-line forensic/design study

Determine why `evidence_line_items` are empty and the minimum safe path to a demonstrable evidence chain.

Do not implement evidence materialisation until the PO explicitly authorizes it.

### 2D. Freeze exact investor-demo scope

Freeze the exact:

- identities;
- organisations;
- workflow states;
- document corpus;
- calculations;
- reports;
- evidence;
- Insight questions;
- failure scenario;
- security DENY scenarios.

## 3. PO decision after Step 1

Review Step-1 outputs.

Only then decide whether to authorize:

- canonical Demo Lab reset/reprovision;
- controlled synthetic seeding;
- evidence implementation/backfill, if justified;
- bounded demo UI/experience work.

## 4. Step 2 — Canonical Demo Environment

After explicit PO authorization:

```text
prove target is Demo Lab
→ reset/reprovision
→ current release migrations
→ pinned synthetic generator
→ controlled seed
→ verify counts/workflows/security
→ independent verification
```

## 5. Step 3 — Investor Demo Experience

Only implement what is necessary for the frozen four stories.

Do not expand into unrelated roadmap work.

## 6. Step 4 — Independent Acceptance & Rehearsal

Independent verifier reproduces:

```text
reset → provision → seed → verify → run demo
```

and checks:

- product flow;
- evidence;
- Insight;
- security;
- truthful data;
- honest failures;
- repeatability;
- final presenter script.

## 7. Final PO gate

Choose exactly one:

- `INVESTOR DEMO READY`;
- `INVESTOR DEMO READY WITH DISCLOSED NON-BLOCKING LIMITATIONS`;
- `NOT YET INVESTOR DEMO READY`.

---

# 8. Immediate Governance Rule

**Do not jump directly to Step 2.**

The next engineering/verification action is **Step 1 Foundation & Forensics**.

In particular:

> **Do not reset or reseed the Demo Lab until the target environment, reset scope, seed source, expected topology, safety guard, evidence requirement, rollback/recovery approach, and verification targets have been frozen and explicitly authorized by the PO.**

---

# 9. Handoff Summary

**Current strategic position:**

CarbonTally has substantial implemented capability, including deterministic calculation, provenance, evidence-viewer architecture, operational processing infrastructure, reporting lifecycle, and a bounded Insight foundation.

The current investor-demo gap is primarily the controlled connection of those capabilities into one verified, populated, repeatable demonstration environment.

**Next action:**

> **Step 1 — Foundation & Forensics**

with three immediate workstreams:

1. documentation reconciliation;
2. independent workflow verification;
3. EV-01 evidence-line forensic/design study.

Only after those are complete should canonical Demo Lab mutation be considered.

**Production remains outside this workplan.**
