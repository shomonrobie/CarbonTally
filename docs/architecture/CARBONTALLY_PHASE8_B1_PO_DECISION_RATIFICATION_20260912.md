# CarbonTally — Phase 8 B1 Disclosure Model Foundation — PO Decision Ratification

**Document:** `CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md`
**Task reference:** `CT-P8-B1-PO-DECISION-RATIFICATION-20260912-011`
**Status:** PO DECISION RATIFICATION RECORD — **B1 PO DECISIONS CLOSED; B1 IMPLEMENTATION NOT AUTHORISED**
**Date:** 2026-09-12
**Type:** Governance / architecture documentation only. No code, schema, migration, API, frontend, RLS or production change.
**Repository baseline:** branch `main`, HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c`
**Governing decisions:** D1–D17; the 20 Disclosure Model decisions (`CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md`)
**Contract reconciled:** `CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md`
**Analytical basis:** `docs/cline/reports/CT-P8-B1-PO-DECISION-CLOSURE-20260912-010.md`
**Closure report:** `docs/cline/reports/CT-P8-B1-PO-DECISION-RATIFICATION-20260912-011.md`

---

## 1. Purpose

Formally record the Product Owner's closure of the eight outstanding B1 PO decisions (**PQ-1…PQ-8**) raised
by the B1 implementation contract and analysed in the B1 decision-closure report. This document is the
**authoritative closure record**; it does not authorise implementation.

**Rule of construction:** this document records only the PO decisions supplied for this task. It creates no
new B1 architecture, invents no regulatory identifier/threshold/denominator, and does not change D1–D17 or
the 20 Disclosure Model decisions.

---

## 2. PQ-1 — Intensity catalogue placement

**DECISION:** **Ratified with condition.** Intensity remains a **B3** responsibility. **B1 SHALL NOT** create
intensity-specific tables or implementation. B1 may reserve the semantic concept `INTENSITY_RATIO` where the
contract already requires it, but actual intensity definitions/values belong to B3. B1 scope is **not**
expanded by this decision.

**RATIONALE:** D10/D11 require a controlled intensity model, but **D11 / D11-CAT** state the *exact
denominator catalogue and statutory treatment must be verified before implementation*, and the catalogue
content is not yet verified. The design §22.1 lists intensity in its MVP table set while the roadmap §20
places the "SECR intensity model" in **B3**; adopting the roadmap as the delivery sequence (PQ-8) resolves
the sequencing question without changing the architecture.

**GOVERNING EVIDENCE:** D10, D11, **D11-CAT**, D12, D13; design §§11.3, 22.1; roadmap §20; B1 contract §5/§6/§28.

**IMPLEMENTATION CONSEQUENCE:** B1 = **11 tables**; no intensity table created or seeded. `source_kind='INTENSITY_RATIO'` and the `E1_GHG_INTENSITY` concept remain reserved for B3. **No denominator is invented.**

**STATUS:** **RATIFIED WITH CONDITION** (CLOSED).

---

## 3. PQ-2 — Reporting-period placement

**DECISION:** **Ratified with condition.** Both `reporting_period_start` and `reporting_period_end` SHALL be
explicit on **both** `disclosure_applicability_assessments` **and** `disclosure_report_instance_binding`.
The **report-instance binding is authoritative** for the report instance. Where both records carry period
information, the implementation SHALL **enforce/document the agreement invariant** between them. Permanent
calendar-year reporting SHALL **not** be assumed.

**RATIONALE:** **DM-3** requires explicit period start/end and forbids a permanent calendar-year assumption;
**APPL** requires applicability to be **period-dated** independently of any report instance. The two records
therefore answer different questions, so duplicating the period is **justified denormalised context**.

**GOVERNING EVIDENCE:** **DM-3**, **APPL**, D15; design §§8.1, 10.1; B1 contract §9.8/§9.9/§16.

**IMPLEMENTATION CONSEQUENCE:** B1 keeps explicit periods on both records; `report_generation_queue.reporting_year` is untouched; the agreement invariant is added to the B1 verification contract. B1 remains 11 tables.

**STATUS:** **RATIFIED WITH CONDITION** (CLOSED).

---

## 4. PQ-3 — Disclosure value status

**DECISION:** **Ratified.** `effective_class` is **kept** as the **authoritative home** for the derived
requirement/applicability outcome and SHALL **NOT** be removed or replaced. `value_status` SHALL be a
**separate, narrow materialisation lifecycle** field whose initial vocabulary is exactly:

- `PENDING` — disclosure value materialisation has not yet completed;
- `RESOLVED` — the value has been successfully materialised/resolved;
- `UNRESOLVED` — the system currently cannot produce a resolved disclosure value.

`value_status` MUST **NOT** duplicate or reinterpret `requirement_class`, applicability,
`carbontally_capability` or `effective_class`. **`UNRESOLVED` MUST NOT be used as a substitute for**
`CUSTOMER_INPUT_REQUIRED`, `NOT_SUPPORTED`, `NOT_APPLICABLE`, `UNDETERMINED`, or any requirement /
applicability / capability classification — those remain in `effective_class` and the existing domain model.

**RATIONALE:** The earlier `value_status` proposal overlapped `effective_class` in four values and conflated
**value-materialisation** with **derived regulatory/applicability/capability outcomes**, breaking the
four-way invariant (REQUIREMENT ≠ APPLICABILITY ≠ CAPABILITY ≠ CUSTOMER INPUT) and leaving the `DM-5`
finalisation signal ambiguous. Keeping the two dimensions non-overlapping preserves both.

**GOVERNING EVIDENCE:** D12, **DM-5**, **APPL**, D13; Decision Record §8/§9; B1 contract §9.10; closure report `…-010` §12.

**IMPLEMENTATION CONSEQUENCE:** The B1 contract is reconciled (§9.10, §10, §17, §27): `value_status`
`CK IN ('PENDING','RESOLVED','UNRESOLVED')`; `effective_class` remains authoritative; the `reason` field
attaches to the derived outcome (`effective_class`), not to `value_status`. Valid examples:
`requirement_class=REQUIRED`, `carbontally_capability=SUPPORTED`, `applicability=APPLIES`,
`effective_class=CUSTOMER_INPUT_REQUIRED`, `value_status=PENDING`; and `effective_class=NOT_SUPPORTED`,
`value_status=UNRESOLVED`.

**STATUS:** **RATIFIED** (CLOSED).

---

## 5. PQ-4 — Immutability enforcement

**DECISION:** **Ratified with condition.** For B1, immutability SHALL initially be enforced at the
**application/service layer** and **verified by tests**. A **database trigger is NOT required for B1**.
Database-level hardening may be considered later as a **separate bounded task**. B1 implementation scope is
**not** expanded by this decision.

**RATIONALE:** The writer of `disclosure_values` is CarbonTally's own service layer (no customer write path
to system-derived values per `P3`); the existing `calculation_snapshots` immutability is **app-layer /
append-only by design** (no trigger); and a cross-table conditional trigger would depend on
`report_versions.status`, a column added by an **outstanding** migration. The `p7_audit_trail_immutable`
trigger remains the precedent **if** DB hardening is later authorised.

**GOVERNING EVIDENCE:** D15; the ratified lifecycle (approved/final immutable); repository:
`20260912000000_p7_audit_immutability_and_indexes.sql`, `20260807020000_add_calculation_snapshots.sql`; B1
contract §9.10/§25; closure report `…-010` §13.

**IMPLEMENTATION CONSEQUENCE:** B1 enforces immutability for values whose parent report version is `APPROVED`/`FINAL` in the service layer, with a DENY test. A future DB trigger (if authorised) must block UPDATE/DELETE on `disclosure_values`/`disclosure_value_evidence` when the parent status ∈ {APPROVED, FINAL}, fire for all roles including the service role, and remain droppable by an authorised retention/purge process.

**STATUS:** **RATIFIED WITH CONDITION** (CLOSED).

---

## 6. PQ-5 — 34 outstanding migrations

**DECISION:** **Ratified.** The existence of 34 outstanding repository migrations is a
**deployment/reconciliation gate**, **not** an architectural reason to redesign B1. B1 may be implemented
and verified in **development/QA** independently. **NO production deployment of B1 SHALL be authorised**
until the outstanding migration set has been reconciled and a production migration strategy has been
**independently verified**.

**RATIONALE:** B1 is purely additive and references only objects present at the 21-migration level
(`organizations`, `report_generation_queue`, `report_versions`, `calculation_snapshots`, `emissions_logs`,
`manual_extraction_items`, `organization_files`). No outstanding migration is a B1 DDL dependency.

**GOVERNING EVIDENCE:** RLS baseline (`21 applied / 34 outstanding`); B1 contract §3/§22; closure report `…-010` §14.

**IMPLEMENTATION CONSEQUENCE:** B1 may be designed/applied in dev/QA; production stays gated. **No migration is modified or reconciled by this task.**

**STATUS:** **RATIFIED** (CLOSED).

---

## 7. PQ-6 — Reference seeds

**DECISION:** **Ratified with condition.** The B1 architecture may seed/reference **framework identities**,
**framework-version identities** and **report-purpose identities** **ONLY** where the identity/version
information is supported by **authoritative evidence and/or explicit PO confirmation**. **Version rows MUST
NOT be invented.** In particular, **no unresolved ESRS E1 requirement identifiers** may be invented. The
**2026 ESRS** material SHALL be represented as `ADOPTED_NOT_IN_FORCE` **only** where that status is
supported by the existing authoritative-evidence record. Detailed requirement and requirement-mapping
content remains **outside** this task and is handled in the appropriate later batch.

**RATIONALE:** D17 makes source governance part of the model; a version row asserts a legal fact and
therefore requires authoritative evidence. Framework and purpose **identities** are D1/D6-R facts; the exact
version **segmentation/labels** involve judgement and require PO confirmation.

**GOVERNING EVIDENCE:** D1, D6-R, **D17**, **E1-COV**; design §§6.1, 6.2, 6.3, 6.5; closure report `…-010` §15.

**IMPLEMENTATION CONSEQUENCE:** B1 seeds framework identities + purpose identities; framework-version rows only as PO-confirmed, [V]-verified rows (2026 ESRS = `ADOPTED_NOT_IN_FORCE` where supported). Requirement/mapping content is deferred to B3.

**STATUS:** **RATIFIED WITH CONDITION** (CLOSED).

---

## 8. PQ-7 — E1 coverage

**DECISION:** **Ratified.** Unresolved ESRS E1 authoritative evidence does **NOT** block B1 architecture or
B1 implementation. **`E1-COV` remains CONDITIONAL.** Only authoritatively verified E1
requirements/identifiers may be treated as **production-supported**. **Do NOT invent E1 requirement IDs. Do
NOT create fabricated E1 mappings. Do NOT weaken the evidence requirement.**

**RATIONALE:** B1 needs **no** official ESRS identifier: `requirement_code` is a controlled internal string,
`official_identifier` is nullable, and a CHECK structurally forbids an official identifier while
`identifier_status='UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION'`. E1 **content** is B3, not B1.

**GOVERNING EVIDENCE:** **E1-COV** (CONDITIONAL), **E1-VER**, **DM-1**, **D17**; design §12.1; B1 contract §9.3/§15; closure report `…-010` §16.

**IMPLEMENTATION CONSEQUENCE:** B1 proceeds framework-agnostically; E1 seeding stays gated; the structure accepts E1 later via a data update (no re-architecture). The `identifier_status` CHECK is the structural guard.

**STATUS:** **RATIFIED** (CLOSED).

---

## 9. PQ-8 — Batch split

**DECISION:** **Ratified.** Use the previously agreed implementation sequence **B1 → B2 → B3 → B4** with the
previously identified supporting/remediation tracks and gates. This is a **delivery sequencing decision** and
does **not** remove any architecture element from the overall Phase 8 design. **B1 remains limited to the B1
contract.**

**RATIONALE:** The design §22.1 MVP table list and the roadmap §20 batch split describe the **same canonical
architecture**; they differ only in **delivery order**. The line-item forensic justifies isolating
evidence/line-item work in B2, and the intensity content is evidence-gated (PQ-1).

**GOVERNING EVIDENCE:** D2, D3, D6-R; design §22.1; roadmap §19–§20; G0 governance consolidation (recorded sequencing conflict); closure report `…-010` §17.

**IMPLEMENTATION CONSEQUENCE:** B1 = the foundation batch only; `evidence_line_items`/`source_line_item_id` = B2; intensity = B3; narrative/finalisation/frozen artefacts = B4.

**STATUS:** **RATIFIED** (CLOSED).

---

## 10. Decision summary

| PQ | Topic | Status | Outcome |
|---|---|---|---|
| **PQ-1** | Intensity catalogue placement | **CLOSED — RATIFIED WITH CONDITION** | Intensity → **B3**; B1 keeps 11 tables; `INTENSITY_RATIO` reserved |
| **PQ-2** | Reporting-period placement | **CLOSED — RATIFIED WITH CONDITION** | Explicit periods on **both** records; instance binding authoritative; agreement invariant |
| **PQ-3** | Disclosure value status | **CLOSED — RATIFIED** | `effective_class` authoritative; `value_status` = `PENDING`/`RESOLVED`/`UNRESOLVED` only |
| **PQ-4** | Immutability enforcement | **CLOSED — RATIFIED WITH CONDITION** | App-layer for B1 + tests; no DB trigger for B1 |
| **PQ-5** | 34 outstanding migrations | **CLOSED — RATIFIED** | Deployment gate; dev/QA allowed; production gated |
| **PQ-6** | Reference seeds | **CLOSED — RATIFIED WITH CONDITION** | Identities seedable with evidence/PO confirmation; no invented version rows or E1 IDs |
| **PQ-7** | E1 coverage | **CLOSED — RATIFIED** | E1 evidence does not block B1; `E1-COV` remains CONDITIONAL |
| **PQ-8** | Batch split | **CLOSED — RATIFIED** | B1 → B2 → B3 → B4 delivery sequence |

**All eight B1 PO decisions are CLOSED. No B1 PO decision remains open.**

---

## 11. B1 contract reconciliation (PQ-3 and the closed-decision references)

`CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md` was updated **only** to reflect the ratified
decisions and to remove the previously-open `value_status` proposal:

| Contract section | Change |
|---|---|
| Header | Status → "B1 PO DECISIONS CLOSED …"; added the PQ-1…PQ-8 CLOSED/ratified reference line |
| §6 (B1 vs B2) | PQ-1 note updated from "raises PO decision" to "ratified as PQ-1 (intensity → B3)" |
| §9.10 (`disclosure_values`) | `value_status` reconciled to `PENDING`/`RESOLVED`/`UNRESOLVED`; `effective_class` marked authoritative; `reason` re-attached to `effective_class`; PQ-3/PQ-4 closed notes |
| §10 (Keys & Constraints) | `disclosure_values` row updated to the new `value_status` set + `effective_class`-based `reason` |
| §17 (Value Semantics) | Added the explicit `value_status` lifecycle rule and the PQ-4/QP-3 closed notes; renumbered |
| §22 (Migration Strategy) | PQ-5 reference marked **CLOSED — RATIFIED** |
| §27 (Verification) | Value-semantics test updated to assert the new `value_status` set and non-duplication |
| §28 (PO Decisions) | Section retitled to the **CLOSED** table; all eight decisions recorded with status + final PO decision |
| §29 (Verdict) | Updated to "PO DECISIONS CLOSED — READY FOR A SEPARATE IMPLEMENTATION AUTHORISATION TASK" |

**No other redesign was made.** The 11-table B1 scope, the B1/B2 boundary, the migration strategy, the RLS
intent and the API/domain boundary are unchanged.

---

## 12. B1 implementation authorisation status

**B1 implementation is NOT authorised by this document.** Closing PQ-1…PQ-8 clears the B1 **decision
gate only**. B1 implementation requires a **separate, explicit PO implementation-authorisation task**
(roadmap Gate 5) that references this ratification record and the B1 contract. No implementation prompt is
created by this task.

**B1 IS READY FOR A SEPARATE IMPLEMENTATION AUTHORISATION TASK.**

---

## 13. Contradictions / unresolved issues

- **None requiring implementation or architectural redesign.** The single cross-cutting issue identified by
  the closure analysis (PQ-3) is now **resolved by a PO decision** and reconciled in the B1 contract.
- **Recorded, not resolved here (by design, and outside this task's scope):** the production migration
  backlog (PQ-5 gate) and the broader RLS remediation remain **separate workstreams**. They gate
  *production*, not the B1 decision set or dev/QA implementation.
- **No unresolved PO decision has been silently invented or assumed.** All eight decisions are recorded
  exactly as ratified; `E1-COV` remains **CONDITIONAL**.

---

## 14. Change control

1. This document is the **authoritative closure record** for PQ-1…PQ-8. Where any other document conflicts
   with it on these eight decisions, this record governs until the PO amends it.
2. Any change to a decision here requires **explicit PO ratification** and a new/updated record.
3. This record **does not** authorise implementation, migrations, schema, API, frontend, RLS or production
   changes.

---

## 15. Verdict

**`B1 PO DECISION RATIFICATION COMPLETE — READY FOR IMPLEMENTATION`**

*(Meaning: the B1 **decision gate** is closed and the B1 contract is reconciled. It is **not** a claim that
implementation is complete or already authorised — a separate PO implementation-authorisation task is
required.)*




