# CarbonTally V3 Processing Entity
# Open Questions Classification

**Status:** READ-ONLY DECISION VALIDATION — CLASSIFICATION ONLY. NO IMPLEMENTATION.
**Date:** 2026-08-10 · Branch: `main`
**Mode:** Read-only. No code, database, migration, RLS, Storage, API, frontend or test
changes were made. The Architectural Decisions Register was **not** modified. Factor baseline
unchanged (DEFRA 7,029 · SEAI 20 · TOTAL 7,049).

**Source analysed:**
`docs/audit/CarbonTally_V3_Processing_Entity_Architecture_Decision_Analysis.md` — §24
Remaining Open Questions (10 questions), cross-checked against §22 Recommended Architecture,
§23 ADR-V3-001 Proposed Decision, the ADR Register (ADR-V3-001 OPEN; ADR-V3-003/004/005/006/
007/010 PROVISIONALLY DECIDED; ADR-V3-009 DECIDED), and the V3 IA §27 human-decision list.

**Purpose:** For each of the 10 open questions, classify it as exactly one of:
- **A. ARCHITECTURE-BLOCKING** — must be resolved before ADR-V3-001 can be considered DECIDED.
- **B. IMPLEMENTATION DETAIL** — does not prevent DECIDED; resolvable during V3 DB/backend design.
- **C. DEPENDENT DECISION** — belongs to another ADR; should not be resolved under ADR-V3-001.
- **D. DEFERRED** — can be intentionally postponed without affecting the core entity model.
- **PROVISIONALLY DECIDED** — an architectural clarification by the product/architecture
  owner establishes the direction (architecture principles settled); exact fields, states,
  transitions and RBAC detail are finalized during V3 architecture/schema/RBAC design. No
  database fields or enums are invented.

**Revision note:** per the product/architecture owner's architectural clarification,
Q1 (entity contract metadata) and Q6 (entity onboarding/offboarding workflow + authority)
are reclassified from **D — DEFERRED** to **PROVISIONALLY DECIDED**. ADR-V3-001's status is
**unchanged**.

---

## Classification

| # | Open Question | Classification | Why | Related ADR | Must Resolve Before H1? |
|---|---|---|---|---|---|
| 1 | Entity contract metadata scope (minimal vs contractual fields) | **PROVISIONALLY DECIDED** | Architectural clarification: Processing Entities have a contractual/commercial relationship with CarbonTally; the V3 architecture recognizes contract metadata as part of the Processing Entity domain. Exact commercial fields, pricing structures and detailed contract schema are deferred to the architecture/schema design phase. No database fields or enums invented. | ADR-V3-001 | **No** — direction settled; exact schema deferred |
| 2 | `entity_id` on other work tables (dpq, manual_extraction, report_generation_queue) | **C — DEPENDENT DECISION** | Whether the *technical state machines* (`document_processing_queue`, `report_generation_queue`) and dormant extraction structures carry entity scope is owned by ADR-V3-004 (dpq producer/consumer) and ADR-V3-016 (queue consolidation). ADR-V3-001 decides only the canonical Work Item surface (`manual_review_queue`) + batch. Resolving this here would pre-empt ADR-V3-004. | ADR-V3-004, ADR-V3-016 | **No** |
| 3 | Entity-level SLA definitions (per-entity `sla_definitions` vs entity-scoped keys in `queue_settings`) | **C — DEPENDENT DECISION** | The SLA configuration shape is owned by ADR-V3-006 (SLA/Priority/Escalation/Capacity, PROVISIONALLY DECIDED, "DB CONDITIONAL; API EXTEND"). The entity dimension only scopes the existing SLA surface; it does not change ADR-V3-001's entity model. | ADR-V3-006 | **No** |
| 4 | Entity capacity model (aggregate of `staff_workload` vs explicit entity capacity row) | **C — DEPENDENT DECISION** | Capacity is an input to ADR-V3-007 (AutoAssignmentEngine) and part of ADR-V3-006's capacity surface. Whether capacity is a derived aggregate or an explicit entity-scoped row is resolved under those ADRs, not under the entity model decision. | ADR-V3-007, ADR-V3-006 | **No** |
| 5 | CarbonTally internal representation: `entity_id IS NULL` vs a reserved "CarbonTally" entity row | **A — ARCHITECTURE-BLOCKING** | This is intrinsic to the entity model itself: it fixes the semantics of the entity dimension, the logical "CarbonTally queue", and the RLS convention (`is_entity_member` never matches internal work). The analysis §22 and the proposed decision text §23 already resolve it — **`staff_profiles.entity_id IS NULL` for CarbonTally internal** — so the owner must confirm that convention as part of the decision (not defer it). | ADR-V3-001 (itself) | **Yes** — but already answered in the proposed decision text; confirm NULL convention when recording the decision |
| 6 | Entity onboarding/offboarding workflow + authority | **PROVISIONALLY DECIDED** | Architectural clarification establishes these principles: (1) Entity onboarding is controlled by authorized CarbonTally personnel; (2) Processing Entities cannot self-activate; (3) lifecycle supports operational states including active, remediation/suspended and terminated; (4) suspension/termination must NOT delete historical work, audit, performance or issue history; (5) active/assigned work must have a defined reassignment/disposition process when an entity is suspended or terminated; (6) entity users' operational access must respect entity lifecycle. Exact lifecycle states, transition authority and the RBAC matrix are finalized during V3 architecture/RBAC design. No database fields or enums invented. | ADR-V3-001 (informs H12) | **No** — principles settled; exact states/authority/RBAC matrix deferred |
| 7 | Whether `is_entity_member` also covers entity admins for user management of their entity | **C — DEPENDENT DECISION** | The exact RLS predicate scope (who may manage entity users) belongs to ADR-V3-010 (RLS/Security/Tenant Isolation, PROVISIONALLY DECIDED), which owns the entity-RLS surface conditional on ADR-V3-001. ADR-V3-001 fixes only the existence of the deny-by-default entity boundary, not its admin-coverage detail. | ADR-V3-010 | **No** |
| 8 | Issue entity context: entity-scoped issue surface vs issues owned by CarbonTally with entity reference | **C — DEPENDENT DECISION** | ADR-V3-009 (Issue Management) is **DECIDED** (Option B). Whether issues are entity-scoped surfaces or CarbonTally-owned with an entity reference is an ADR-V3-009 implementation question; ADR-V3-001 only establishes that entity context *exists* on work surfaces. | ADR-V3-009 | **No** |
| 9 | Storage policy shape for per-assignment document access (signed URLs vs entity bucket) | **C — DEPENDENT DECISION** | Storage security for entity/worker-scoped document access is the V3-016 requirement and part of the RLS/security surface owned by ADR-V3-010. ADR-V3-001 requires "entity sees only assigned documents" conceptually; the Storage policy mechanism (signed URLs vs buckets) is resolved under the security work. | ADR-V3-010 (V3-016 Storage) | **No** |
| 10 | Migration sequencing (V3M-1 vs other V3 conditional migrations) | **B — IMPLEMENTATION DETAIL** | V3 IA §29 states no migration is created until the human decision is taken; V3M-1's design and sequencing against V3M-2/V3M-3/V3M-5 is a DB-design task that follows the decision. It cannot block the decision itself — it is the *output* of it. | ADR-V3-001 (implementation) | **No** |

---

## Recommendation

### ADR-V3-001 can safely become **DECIDED — OPTION B**.

**Reasoning:**

1. **Only one of the ten questions is ARCHITECTURE-BLOCKING (Q5).** The CarbonTally-internal
   representation convention (`staff_profiles.entity_id IS NULL` = CarbonTally internal,
   logical "CarbonTally queue") is intrinsic to the entity model. However, **the analysis
   already answers it in §22 and the proposed decision text in §23 states it explicitly**.
   Resolving it is therefore a *confirmation*, not an open investigation: the owner records
   the NULL convention as part of the ADR-V3-001 decision.

2. **Six questions are DEPENDENT DECISIONS (Q2, Q3, Q4, Q7, Q8, Q9)** that belong to other
   ADRs (ADR-V3-004/016, ADR-V3-006, ADR-V3-007, ADR-V3-010, ADR-V3-009). They must **not**
   be resolved under ADR-V3-001; their ADRs are PROVISIONALLY DECIDED (or DECIDED for V3-009)
   and become implementable once ADR-V3-001 unblocks them — the correct direction of dependency.

3. **Two questions are now PROVISIONALLY DECIDED (Q1, Q6)** by the product/architecture
   owner's architectural clarification. Their architectural direction is settled:
   - Q1 — contract metadata is part of the Processing Entity domain (exact commercial
     fields/pricing/contract schema deferred to schema design).
   - Q6 — onboarding is CarbonTally-controlled, entities cannot self-activate, lifecycle
     supports active/remediation-suspended/terminated, suspension/termination never deletes
     history, active work has a defined reassignment/disposition process, and entity user
     access respects lifecycle (exact states, authority and RBAC matrix deferred).
   Neither blocks ADR-V3-001 from being DECIDED.

4. **One question is an IMPLEMENTATION DETAIL (Q10)** — migration sequencing follows the
   decision by definition (V3 IA §29).

5. **No question remains classified DEFERRED (D).** Q1 and Q6 moved from D to
   PROVISIONALLY DECIDED; the earlier DEFERRED classification for them is superseded by the
   owner's clarification.

**Constraint honoured:** classifying Q2–Q9 as C/D means ADR-V3-001 is not overloaded with
decisions owned elsewhere — matching ADR principle 1/2 (no duplication, one owner per
decision) and the register's existing PROVISIONALLY DECIDED dependencies.

**Recommended action when recording the decision** (in a later, separate task — NOT this one):
confirm the NULL-convention answer to Q5 inside the ADR-V3-001 decision text (as the proposed
§23 text already does), then mark ADR-V3-001 DECIDED — OPTION B. The remaining nine questions
are then resolved under their owning ADRs or during V3 DB/backend design.

---

## Verification

1. File exists at `docs/audit/CarbonTally_V3_Processing_Entity_Open_Questions_Classification.md` — **yes**.
2. All 10 questions from the source analysis §24 classified exactly once — **yes** (A=1, B=1, C=6, PROVISIONALLY DECIDED=2, D=0).
3. Classification rationale given for each; related ADR identified — **yes**.
4. Q1 and Q6 reclassified from D — DEFERRED to PROVISIONALLY DECIDED per the owner's architectural clarification — **yes**.
5. ADR-V3-001's status is **unchanged** in the Architectural Decisions Register (still OPEN; not promoted to DECIDED) — **yes**.
6. No database fields, enums, lifecycle states or RBAC matrix invented — **yes** (deferred to V3 architecture/RBAC design).
7. The Architectural Decisions Register was updated **only where necessary** (ADR-V3-001 provisional-clarification notes) and ADR-V3-001's status was **not changed** — **yes**.
8. No code, database, migration, RLS, API, frontend or test files modified — **yes**.
9. Factor baseline unchanged (DEFRA 7,029 · SEAI 20 · TOTAL 7,049) — **yes**.

*End of classification. READ-ONLY — no implementation performed.*

