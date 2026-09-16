# CT-P8-B1-PO-IMPLEMENTATION-AUTHORISATION-20260912-012

**Task ID:** `CT-P8-B1-PO-IMPLEMENTATION-AUTHORISATION-20260912-012`
**Title:** Phase 8 Batch B1 (Disclosure Model Foundation) — Final PO Implementation-Authorisation Gate
**Type:** READ-ONLY governance / architecture verification — **no implementation**
**Date:** 2026-09-12 (start `2026-09-12T21:31:09+06:00`)
**Final verdict:** `B1 IMPLEMENTATION AUTHORISED — READY FOR B1 IMPLEMENTATION`

> **Scope of this verdict:** this authorises **only** that a *separate B1 implementation task may now be
> issued*. It does **NOT** mean implementation has started, a migration has been created/applied, B1 is
> verified, B1 is complete, or production deployment is authorised.

---

## 1. Task ID
`CT-P8-B1-PO-IMPLEMENTATION-AUTHORISATION-20260912-012`.

## 2. Review objective
Independently determine whether B1 (the 11-table Disclosure Model Foundation) is **sufficiently specified,
bounded and governance-approved** that a separate B1 implementation task may be authorised. This is an
**authorisation** review, **not** an implementation review (B1 has not been implemented).

## 3. Documents inspected
1. `docs/architecture/CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md` (authoritative PQ-1…PQ-8 closure)
2. `docs/architecture/CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md` (B1 contract; §§1–29)
3. `docs/cline/reports/CT-P8-B1-PO-DECISION-RATIFICATION-20260912-011.md` (closure report)
4. `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` (20 Disclosure Model decisions)
5. `docs/cline/reports/CT-P8-G0-GOVERNANCE-CONSOLIDATION-20260912-008.md` (G0)
6. `docs/architecture/CARBONTALLY_PHASE8_P8X_COMPREHENSIVE_IMPLEMENTATION_READINESS_20260912.md` (roadmap; batch split)
7. `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md`; D1–D17 ratification
8. Repository schema/migrations (as needed)

## 4. Repository baseline inspected
`supabase/migrations/**` (55 files) — init schema (`organizations`, `report_generation_queue`,
`report_versions`, `manual_extraction_items`, `organization_files`), `20260807020000_add_calculation_snapshots.sql`,
`20260823010000_d33_evidence_traceability.sql`, `20260912000000_p7_audit_immutability_and_indexes.sql`,
`20260913000000_p8_report_lifecycle_status.sql`. Read-only; **no modification**.

## 5. Governance status
- **PQ-1…PQ-8 are explicitly CLOSED** in the ratified record (8 PQ sections; 8 `STATUS:` entries; 22 `CLOSED` mentions; verdict `B1 PO DECISION RATIFICATION COMPLETE — READY FOR IMPLEMENTATION`).
- The B1 contract's §28 PO-decision table is retitled **"[CLOSED — PO RATIFIED]"** and records each PQ with status + final PO decision.
- **No B1 PO decision remains open.** **Governance closure: SATISFIED.**

---

## 6. PQ-1 through PQ-8 verification

| PQ | Ratified decision | Verified in contract? | Consistent? |
|---|---|---|---|
| **PQ-1** | Intensity → **B3**; B1 creates no intensity table; 11 tables | §5/§6/§28 (intensity excluded; 11 tables confirmed) | **YES** |
| **PQ-2** | Explicit start/end on **both** applicability assessments and instance bindings; binding authoritative; agreement invariant | §9.8, §9.9 (+ **agreement invariant added**, §9.9), §27.B, §28 | **YES** (after the minimal §11 correction — see §19) |
| **PQ-3** | `effective_class` authoritative; `value_status` = `PENDING`/`RESOLVED`/`UNRESOLVED` only | §9.10, §10, §17, §27, §28 | **YES** |
| **PQ-4** | App-layer immutability + tests; no DB trigger for B1 | §9.10, §17, §25, §28 | **YES** |
| **PQ-5** | 34 outstanding migrations = deployment gate; dev/QA allowed; production gated | §3, §22, §28 | **YES** |
| **PQ-6** | Evidence/PO-controlled seeds; no invented version rows or E1 IDs; 2026 ESRS `ADOPTED_NOT_IN_FORCE` only where supported | §14, §28 | **YES** |
| **PQ-7** | E1 evidence does not block B1; `E1-COV` CONDITIONAL; no invented E1 IDs/mappings | §15, §28 | **YES** |
| **PQ-8** | Delivery sequence B1 → B2 → B3 → B4; no architecture removal | §6, §28 | **YES** |

**Result:** all eight ratified decisions are reflected in the contract; **no contradiction** between the ratification record and the B1 contract.

## 7. B1 11-table scope verification
Contract §8 lists **exactly 11** tables, matching the authorised scope (1 `disclosure_frameworks` … 11
`disclosure_value_evidence`); §9 contains exactly **11** column-definition subsections (§9.1–§9.11). No
twelfth table. **PASS.**

## 8. B1/B2/B3/B4 boundary verification
- **B2** (`evidence_line_items`, `calculation_snapshots.source_line_item_id`, row/line addressability) — **excluded** from B1 (§5, §6, §9.11 "No `evidence_line_items` FK in B1"; §9.11 records the B2 additive extension explicitly as *not* B1).
- **B3** (intensity definitions/values, SECR denominator catalogue) — **excluded** (§5, §6, §28 PQ-1); `INTENSITY_RATIO` reserved only as a `source_kind` value.
- **B4** (narrative overlay, finalisation enhancements, frozen artefacts) — **excluded** (§5, §28 PQ-3/PQ-8); `disclosure_values` carries `reason` but no narrative table exists.
- **PASS** — B1 is the 11-table foundation only; B2/B3/B4 are named but not absorbed.

## 9. Schema / contract completeness assessment
The contract specifies, for all 11 tables: **exact columns** (name, PostgreSQL type, nullability, default),
**PKs**, **FKs with `ON DELETE` semantics**, **unique constraints**, **CHECK constraints/enumeration
vocabularies**, **indexes**, **cardinalities/relationships**, **ownership/tenant/entity scope**,
**lifecycle/version semantics**, **period semantics**, **immutability semantics**, **reference-seeding
semantics**, **historical-backfill rules**, **migration strategy**, **RLS intent**, **API/domain boundary**,
**idempotency**, **audit requirements**, and a **verification contract** (§§9–27). JSONB is used only for
`source_selector` (closed-key, app-validated) and `characteristic_snapshot` (facts + source) — both
justified. **PASS** — an implementer can proceed without inventing tables, fields, keys, constraints,
relationships or semantics.

## 10. Value-status / `effective_class` verification
Contract §9.10: `effective_class` is marked the **authoritative** home for the derived
requirement/applicability outcome; `value_status` is `CK IN ('PENDING','RESOLVED','UNRESOLVED')` and
"must NOT duplicate or reinterpret `requirement_class`, applicability, `carbontally_capability` or
`effective_class`". **No** reintroduction of `CUSTOMER_INPUT_REQUIRED`/`NOT_SUPPORTED`/`NOT_APPLICABLE`/
`UNDETERMINED` into `value_status` (grep-verified: 0 old four-value occurrences). §17 and §27 restate the
separation. **`effective_class` ≠ `value_status`. PASS.**

## 11. Period / invariant verification
Both `disclosure_applicability_assessments` (§9.8) and `disclosure_report_instance_binding` (§9.9) carry
explicit NN `reporting_period_start`/`reporting_period_end` with `CK (reporting_period_end >= reporting_period_start)`.
The contract **now explicitly states** the **period agreement invariant** in §9.9 (binding authoritative;
where an assessment is referenced, the two period pairs MUST equal) and the corresponding §27.B verification
bullet. No permanent calendar-year assumption (§10.1, §9.8 note; `report_generation_queue.reporting_year`
untouched). **PASS** (after the minimal correction — §19).

---

## 12. E1 evidence boundary verification
B1 needs **no** official ESRS identifier: `requirement_code` is a controlled internal string,
`official_identifier` is nullable, and the CHECK `identifier_status='RESOLVED' OR official_identifier IS
NULL` structurally forbids an identifier while unresolved (§9.3). E1 **content** (requirement/mapping rows)
is deferred to B3. `E1-COV` remains **CONDITIONAL** (§28 PQ-7). **No invented E1 identifiers or mappings.**
**PASS.**

## 13. Regulatory-claim boundary verification
The contract makes **no** assurance, certification, auditor-status, statutory-filing or full-ESRS/CSRD
claim (grep: 0 occurrences of assurance/certification/auditor/legal-advice/statutory-filing/compliance).
It explicitly disclaims legal determination (§16.5: *"No legal-advice semantics"*, per `APPL`). No
compliance claim is introduced. **PASS.**

## 14. Migration / deployment boundary verification
The contract distinguishes:
- **dev/QA implementation** — B1 is purely additive, `IF NOT EXISTS` idempotent, depends only on objects present at the 21-migration level → **B1 may be implemented and verified in dev/QA** (§22 items 2–7);
- **production migration** — the **34 outstanding migrations** are an explicit **reconciliation gate**; a production migration strategy must be **independently verified** (§22 item 8, §28 PQ-5);
- **production deployment** — **NOT authorised** until reconciliation (§22 item 7, §28 PQ-5).
The 34-migration gate is preserved. **PASS.**

## 15. Existing architecture compatibility assessment
Read-only inspection confirms **no conflict**:
- **0** `disclosure_*` tables/columns exist in `supabase/migrations/**` or `backend/**` → the 11 new tables are genuinely new and collide with nothing.
- B1's FK targets exist: `organizations`, `report_generation_queue`, `report_versions`, `calculation_snapshots`, `emissions_logs`, `manual_extraction_items`, `organization_files` (verified present).
- B1 reuses the repository conventions (PK `id UUID DEFAULT extensions.uuid_generate_v4()`, `organization_id … ON DELETE CASCADE`, `TIMESTAMPTZ DEFAULT NOW()`, `CHECK` enums), the D33 `SET NULL` evidence pattern, and the existing guard/audit patterns; it **modifies no existing object**. **PASS.**

## 16. Verification-readiness assessment
§27 specifies: **(A)** implementation tests (schema/constraint/idempotency), **(B)** semantic
verification (framework/version, requirement, applicability, purpose, period, value), **(C)** security
verification (tenant isolation, actor scope, global-catalogue protection, cross-tenant references,
cross-framework-version contamination — ALLOW **and** DENY), **(D)** idempotency, **(E)** historical
reproducibility, **(F)** regression (S1/S3 lifecycle, calculation/snapshot behaviour), **(G)** migration
verification — with an explicit separation of implementation tests from the **independent** verification
required after B1 (roadmap gate V1). **PASS** — verification criteria are explicit enough for an
independent verification gate.

## 17. Findings
| # | Finding | Assessment |
|---|---|---|
| F-1 | PQ-1…PQ-8 are explicitly CLOSED; no open B1 PO decision | **PASS** |
| F-2 | Contract specifies exactly 11 tables; no B2/B3/B4 absorption | **PASS** |
| F-3 | `value_status` = `PENDING`/`RESOLVED`/`UNRESOLVED`; `effective_class` authoritative; no reintroduced values | **PASS** |
| F-4 | Explicit periods on both tables | **PASS** |
| F-5 | Period agreement invariant was *referenced* (§28) but not *stated* in the contract body | **CORRECTED (minimal documentation fix — §19)** |
| F-6 | No historical re-extraction / unsupported backfill (§20–§21; CLASS 1/2/3) | **PASS** |
| F-7 | E1 boundary safe; `E1-COV` CONDITIONAL; no invented identifiers | **PASS** |
| F-8 | No regulatory/assurance/certification claim; legal-advice explicitly disclaimed | **PASS** |
| F-9 | dev/QA vs production-migration vs production-deployment boundaries preserved; 34-migration gate intact | **PASS** |
| F-10 | No conflict with existing architecture (0 `disclosure_*`; FK targets exist; no existing object modified) | **PASS** |
| F-11 | Verification criteria explicit (A–G) incl. independent-verification separation | **PASS** |

## 18. Blockers
**None.** No unresolved PO decision, no ratification↔contract contradiction, no missing critical schema
semantics, no B1/B2/B3/B4 ambiguity, no unsupported regulatory claim, no unresolved E1 issue requiring
invented identifiers, no invalidating migration dependency, no material architecture incompatibility, and
no requirement that cannot be implemented deterministically from the contract. The single gap found
(F-5) was a **documentation under-specification**, corrected minimally (§19); it was not a material
blocker.

---

## 19. Files changed, if any

**One minimal documentation correction** was made, as permitted by the task ("the minimum necessary
documentation change"):

**Modified:** `docs/architecture/CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md`
- **§9.9 (`disclosure_report_instance_binding`)** — added the explicit **"Period agreement invariant
  (PQ-2 RATIFIED)"** statement (instance binding authoritative; where an assessment is referenced, the two
  period pairs **MUST equal**; app/service-layer enforced; no permanent calendar-year assumption).
- **§27.B (semantic verification)** — extended the period-semantics bullet to assert the same invariant.

**Why:** the ratified **PQ-2** condition requires the agreement invariant to be "enforced/documented"; the
contract §28 PQ-2 row already *claimed* it was enforced/documented and "added to verification", but the
contract **body** did not state it and §27 did not test it — an internal inconsistency. The fix makes the
contract self-contained for the implementer and consistent with its own §28 claim. It is **not** a
redesign: no table, column, key, constraint, index or boundary changed.

**Created:** `docs/cline/reports/CT-P8-B1-PO-IMPLEMENTATION-AUTHORISATION-20260912-012.md` (this report).

**No other file was created or modified.** No source code, migration, schema, API, frontend, RLS or
production change.

## 20. Confirmation that no implementation was performed
**Confirmed.** No code, schema, migration, API, frontend, RLS, legacy-report, Phase 8-X, extraction, factor
or billing change. **No migration created** (`supabase/migrations/` = **55**, unchanged); no database
operation; nothing applied to Supabase; no implementation prompt created. The change set is **one contract
clarification + one report**.

## 21. Git / worktree impact

| Item | Before (`21:31:09`) | After |
|---|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` | `19e4f01c176eee5870f3c15038b6e7c68b23281c` (unchanged) |
| Branch | `main` (ahead 14) | `main` (ahead 14) |
| Staged | 0 | **0** |
| Modified (tracked, ` M`) | 208 | **208 (unchanged)** |
| Untracked (porcelain entries) | 66 | **66 (unchanged** — the new report sits inside the already-collapsed untracked `docs/cline/reports/`; the B1 contract was already untracked) |
| Migrations | 55 | **55 (unchanged)** |

- **No tracked file was modified.** The two touched documents (`…B1_IMPLEMENTATION_CONTRACT_20260912.md`,
  `…CT-P8-B1-PO-IMPLEMENTATION-AUTHORISATION-20260912-012.md`) are untracked-only.
- **208 pre-existing modifications preserved unchanged.** No reset/checkout/clean/stash/restore/rebase/amend.
  **No commit. No push.**

## 22. Final verdict

### `B1 IMPLEMENTATION AUTHORISED — READY FOR B1 IMPLEMENTATION`

**Distinction (as required):**
- **AUTHORISATION** — **GRANTED** (this task): a separate B1 implementation task **may now be issued**, limited to the 11-table B1 Disclosure Model Foundation.
- **IMPLEMENTATION** — **NOT started** (no code, no migration, no schema change).
- **VERIFICATION** — **NOT performed** (independent verification is required after implementation; roadmap gate V1).
- **PRODUCTION DEPLOYMENT** — **NOT authorised** (gated by the 34-migration reconciliation and an independently verified production migration strategy).

**Governance basis:** `CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md` (PQ-1…PQ-8 all CLOSED),
the reconciled `CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md`, and
`CT-P8-B1-PO-DECISION-RATIFICATION-20260912-011.md`. No blocker remains.

*STOP — authorisation review complete. B1 implementation is NOT begun; no migration created; nothing
committed or pushed.*



