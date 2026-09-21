# CARBONTALLY P8 I4 — Q1 PO CLOSURE DECISION (2026-09-21)

**Subject:** `public.ai_content_history`
**Decision:** `Q1 CLOSED — OPTION C SELECTED`
**Selected disposition:** `OPTION C — RETAIN UNCHANGED / OUTSIDE I4 / FUTURE DISPOSITION DEFERRED`
**Decision date:** 2026-09-21

**Provenance (Cline):** this document records the Product Owner's Q1 decision of 2026-09-21 exactly as transmitted to Cline. Sections 1–6 are the PO's decision text, reproduced **verbatim and unaltered**. Section 7 is Cline's recording note. Recording this decision authorizes no implementation of any kind.

**Evidence chain relied upon by the decision:**

| Artefact | Commit |
| --- | --- |
| Historical forensic analysis — `docs/implementation/phase8/CT-P8-I4-AI-CONTENT-HISTORY-ORIGIN-FORENSIC-20260921.md` | `2c67a31` |
| Schema-fit analysis — `docs/implementation/phase8/CT-P8-I4-AI-CONTENT-HISTORY-INSIGHT-SCHEMA-FIT-20260921.md` | `123cc3a` |
| Independent OHD verification — `docs/implementation/phase8/CT-P8-I4-AI-CONTENT-HISTORY-OHD-VERIFICATION-20260921.md` | `067ce73` |
| Q1 disposition preparation — `docs/implementation/phase8/CT-P8-I4-Q1-AI-CONTENT-HISTORY-DISPOSITION-PREPARATION-20260921.md` | `02419ca` |
| I4 pre-authorization readiness audit — `docs/implementation/phase8/CT-P8-I4-PREAUTHORIZATION-READINESS-AUDIT-20260921.md` | `fca5469` |

---

## 1. Decision

The Product Owner formally selects **D2 §22.3 Option C**:

> **Retain `public.ai_content_history` unchanged and defer its future disposition.**

The existing `public.ai_content_history` table is **not part of the authorized I4 Insight implementation** and must not be reused as the canonical I4 conversation store, interaction store, or canonical Insight audit ledger.

No migration, rename, deletion, restructuring, RLS modification, Prisma modification, or application-code integration of this table is authorized as a consequence of this decision.

## 2. Rationale

The decision is based on the completed evidence chain:

* historical forensic analysis;
* schema-fit analysis;
* independent OHD verification;
* Q1 disposition-preparation reconciliation.

The evidence establishes that `ai_content_history` is a legacy/inherited AI-generation-history structure originating before Phase 8.

The repository currently has no verified application reader/writer for the table.

The table contains potentially useful AI-generation metadata, including generated-content, model, usage, latency, cost, feedback, and acceptance concepts, but its existing structure does not satisfy the requirements for the I4 conversation/interaction architecture.

In particular, it does not constitute the canonical I4 conversation/message model, does not provide the required I4 interaction lifecycle and correlation structure, and its existing authorization posture is not the I2 creator-private Insight authorization model.

The OHD verification also established that the table has four existing RLS policies and a tracked Prisma model. Therefore the prior characterization of the table as having no policies or no ORM/model is withdrawn. This decision relies on the corrected evidence.

Production row presence and external/legacy writers remain unverified. Consequently, deletion, migration, restructuring, or retirement would be premature.

## 3. I4 boundary

For I4, `public.ai_content_history` is explicitly classified as:

**LEGACY / OUTSIDE I4**

It is not an I4 dependency.

I4 must not:

* read from it;
* write to it;
* migrate data from it;
* make it the I4 AI-generation store;
* make it the I4 interaction store;
* make it the I4 conversation/message store;
* use it as the canonical audit ledger;
* modify its RLS policies;
* modify its Prisma model;
* modify its schema.
## 4. Future disposition

Future consideration of the table remains possible if CarbonTally later requires a dedicated AI-generation/evaluation history capability.

Such consideration must be handled as a separate PO architectural decision and must not be inferred from this Q1 closure.

Potential future questions include whether its concepts should eventually be:

* retained as a legacy structure;
* replaced by a canonical Insight AI-generation structure;
* migrated into another bounded structure;
* or otherwise retired after production/external-writer analysis.

None of those future actions is authorized by this decision.

## 5. Scope of closure

This decision closes **Q1 only**.

It does not resolve:

* Q2 canonical audit ledger;
* Q3 answer-status vocabulary;
* Q4 raw question/context persistence;
* Q5 Layer-2 mutability;
* Q6 tool argument/result persistence;
* Q7 Layer-1 lifecycle;
* Q8 shared visibility;
* Q9 interaction/audit linkage;
* Q10 idempotency/retry/atomicity;
* Q11 provider-unavailable behavior;
* Q12 retention/deletion/export;
* Q13 billing/credits;
* Q14 provider/evaluation/SLO decisions.

I4 therefore remains **NOT AUTHORIZED** until the remaining blocking pre-authorization decisions are resolved.

## 6. PO verdict

**Q1 — CLOSED**

**Selected disposition:** `OPTION C — RETAIN UNCHANGED / OUTSIDE I4 / FUTURE DISPOSITION DEFERRED`

**Implementation authorization resulting from Q1:** `NONE`

**I4 authorization resulting from Q1:** `NONE`

**Database changes authorized:** `NONE`

**Application changes authorized:** `NONE`

---

## 7. Cline recording note (provenance only — not part of the PO decision text)

`DIRECT` — **No implementation, and no repository change beyond this document, was made as a consequence of this decision.** Recorded state at the time of recording:

* authoritative checkout `/home/shomonrobie/ct_93d5cdd`, branch `p8-release-reconciled`, recording base HEAD `02419caaf162d81e16e2bb81c12bff2b5f764293`, remote `github/p8-release-reconciled` aligned, working tree clean;
* `public.ai_content_history` — **unchanged** (no migration, no DDL, no column, no index, no constraint);
* its **four RLS policies** (`ai_content_history_tenant_select/insert/update/delete`) and their grants — **unchanged**;
* `prisma/schema.prisma` — **unchanged** (the Prisma model and its declared relations/indexes remain as found, and the Prisma-vs-SQL schema-authority divergence remains an open governance item);
* I1/I2/I3, the Master Specification v1.1, application code, tests and configuration — **unchanged**;
* the Q1 disposition-preparation record (`02419ca`) recorded Q1 as open **at that point in time**; it is deliberately **not rewritten**, and this closure document supersedes its status statement;
* `PRODUCTION ROW PRESENCE NOT VERIFIED` and external/legacy writers `UNKNOWN` remain true after this decision, which is precisely why no migration, restructuring, retirement or deletion is authorized.

`DIRECT` — **Q1 is closed; Q2–Q14 remain unresolved; I4 remains NOT AUTHORIZED.** This document records a PO decision and authorizes no work. Any future action on `ai_content_history` requires a separate, explicit PO decision.
