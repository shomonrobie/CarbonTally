# CarbonTally — Phase 7 Closure & Release Boundary

**Prompt Ref:** `CT-P7-CLOSURE-20260912-006`
**Date:** 2026-09-12
**Document type:** Durable closure & release-boundary governance record (subordinate to the Blueprint V1.3 and Master Roadmap V1.0).
**Authority:** Product Owner (closure decision recorded here).

---

## 1. Phase and Final Status

| Field | Value |
|---|---|
| Phase | **Phase 7 — Auditor / Assurance** |
| Final status | **CLOSED — INDEPENDENTLY VERIFIED WITH ACCEPTED RESIDUALS** |
| Closure decision | **Product Owner** |
| Implementation | COMPLETE (`CT-P7-AUDITABILITY-IMPLEMENTATION-20260912-004`) |
| Independent verification | COMPLETE (`CT-P7-INDEPENDENT-VERIFICATION-20260912-005`) — verdict *"PHASE 7 INDEPENDENTLY VERIFIED WITH ACCEPTED RESIDUALS — READY FOR CLOSURE"* |

Phase 7 delivered an **auditability + audit-trail + evidence-traceability + assurance-support** capability. It does **not** make CarbonTally an auditor, verifier or certification body (see §7).

## 2. Closure Basis (existing artifacts — not rewritten here)

| Artifact | Path | Git state at closure |
|---|---|---|
| Phase 7 implementation report | `docs/cline/prompt-history/CT-P7-AUDITABILITY-IMPLEMENTATION-20260912-004.md` | committed in `4368157` |
| Phase 7 independent verification report | `docs/cline/prompt-history/CT-P7-INDEPENDENT-VERIFICATION-20260912-005.md` | included in the Phase 7 closure commit (`docs: close Phase 7…`) |
| Implementation commit | `436815721aa2ec4b1d8ccd4f23d80c196fdbb109` | — |
| Docs commit | `3c8158604ae538bd7ac6656afac9b1acf7476ce1` | — |
| Phase 7 migration | `supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql` | present; **NOT applied to any database** |
| Predecessor closure | `docs/architecture/CARBONTALLY_PHASE6_CLOSURE_AND_RELEASE_BOUNDARY_20260911.md` | — |
| Historical archaeology | `docs/cline/prompt-history/CT-P7P8-HISTORICAL-DECISION-ARCHAEOLOGY-20260911-001.md` | — |
| Role/report catalogue | `docs/cline/prompt-history/CT-P7P8-ROLE-REPORT-CATALOGUE-20260912-002.md` | — |

## 3. What Phase 7 Delivered (as independently verified)

* **Canonical audit taxonomy** (`category`, `origin` human/system, `outcome`, `actor_type`, `organization_id`) stored in the existing `audit_trail.metadata` (no new audit table).
* **Investigation filters** on `GET /api/v3/ops/reporting/audit` (category/origin/outcome/entity/organisation/date).
* **Scoped auditability endpoints**: org `audit-activity` + `audit-readiness` (owner/admin), consultant client `audit-activity` (active grant), entity `audit-activity` (own entity).
* **Evidence package** `GET /api/v3/exports/audit-package.json` with factor provenance, workflow history, readiness, package **SHA-256**, and an explicit `not_assurance: true` notice.
* **AUDIT EVIDENCE READINESS** indicator (evidence-based; never "assured/verified/certified").
* **Audit integrity**: append-only trigger on `public.audit_trail` (all roles) + investigation indexes.
* **Frontend**: ops audit-console taxonomy filters/columns; customer "Audit & evidence" tab (owner/admin).
* Independent verification confirmed: live trigger behaviour, RLS deny-by-default, authorization allow/deny, package-hash reproducibility + tamper detection, route mounting, backend unit suite EXIT=0 (~1,674), frontend Jest 5/5, production build compiles.

## 4. Accepted Residuals (backlog — NOT silently fixed)

These are **accepted for closure** and recorded as backlog items. They are **not** claims that functionality is broken.

### P2 — Medium

| ID | Residual | Source |
|---|---|---|
| **F2-1** | Sensitive audit access is **not itself audited** (reading the audit trail / activity / readiness or downloading a package writes no audit event) | IV report §26 |
| **F2-2** | **Access-denied / security-failure events are not comprehensively audited** (cross-tenant, PE-foreign, unauthorised-consultant, member-denied) | IV report §26 |
| **F2-3** | **All-actor authentication/session audit** and reconstructable **session duration** are not complete | IV report §26 |
| **F2-4** | **Audit-failure semantics are inconsistent**: `record_item_extraction_edit` can swallow/log an audit-write failure (potential silent gap) while other callers fail-closed | IV report §26 |

### P3 — Low / hardening

| ID | Residual | Source |
|---|---|---|
| **F3-1** | A **privileged DB owner/superuser** can bypass the immutability trigger via `session_replication_role=replica` (trigger is not `ENABLE ALWAYS`); the application `service_role` cannot | IV report §24 |
| **F3-2** | **Historical pre-Phase-7 audit rows** do not contain the new taxonomy metadata (categorised on read, excluded from SQL category/origin filters) | IV report §26 |
| **F3-3** | Package **`counts`** are not included in the package hash | IV report §20 |
| **F3-4** | **Report-version lineage** has no dedicated snapshot column; it is derived through the existing lineage (`report content → emissions_logs → calculation_snapshots`) | IV report §14 |
| **F3-5** | **Deployed-process V3 import/reachability** was not independently verified | IV report §23 |

### Verification limitations (NOT defects)

* No representative live **multi-document / multi-actor batch** scenario was executed.
* No live **report ↔ source** lineage verification.
* No live **historical modification/recalculation** scenario.
* Deployed-process **V3 import** not verified.

## 5. Explicit Non-Claims (positioning preserved)

**CarbonTally does NOT claim that Phase 7 makes it:**

* an independent GHG auditor;
* an independent verifier;
* a certification body;
* a regulatory certification authority.

The system provides auditability, evidence traceability, provenance, investigation support and assurance-supporting evidence. It is **not** independent assurance.

**Prohibited wording** (must not be used): "CarbonTally is independently assured"; "CarbonTally is certified"; "CarbonTally is a certified verifier"; "CarbonTally is GDPR compliant". Technical controls may **support** GDPR/UK GDPR/Irish legal obligations, but **legal compliance requires appropriate legal/privacy review**.

Verified in implementation: every Phase 7 payload carries `not_assurance: true` + a notice; the readiness indicator is labelled **"AUDIT EVIDENCE READINESS"**; no auditor role/table was created.

## 6. Release Boundary Decisions

1. **Phase 7 implementation is complete.**
2. **Independent verification is complete.**
3. **Residuals are accepted for closure.**
4. **Residuals are backlog items and are not silently considered fixed** (see §4).
5. **No Phase 7 residual remediation is authorized by this task.**
6. **No Phase 7 production migration has been applied** — the repository contains no evidence of production application; verification confirmed the trigger/function/indexes are absent in the inspected environment (applied only inside a rolled-back transaction). Production migration remains **NOT AUTHORIZED**.
7. **Phase 7 commits remain unpublished until the Product Owner explicitly authorizes a push.** At closure, `main` is **2 commits ahead of `origin/main`** and **NOT PUSHED**.
8. **Phase 8 implementation must not begin as part of this task.**
9. **Phase 8 begins only after a separate specification/discovery and PO ratification step.**

## 7. Auditability Purpose Boundary (no surveillance)

Phase 7 auditability exists for **accountability, traceability, security, investigation, evidence and governance** — **not** employee productivity scoring or surveillance. Where session duration is ever recorded (F2-3, not yet implemented), it must **not** be framed as employee productivity measurement.

## 8. Documentation References

* Architecture authority: `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` (§11 Evidence & Provenance, §13 Authorization, §14 RLS).
* Roadmap: `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`.
* Phase 6 closure: `docs/architecture/CARBONTALLY_PHASE6_CLOSURE_AND_RELEASE_BOUNDARY_20260911.md`.
* Technical operations assessment produced alongside this closure: `docs/architecture/CARBONTALLY_TECHNICAL_OPERATIONS_DOCUMENTATION_ASSESSMENT_20260912.md`.

## 9. Status Summary

```
Phase 7 — Auditor / Assurance
Status:            CLOSED — INDEPENDENTLY VERIFIED WITH ACCEPTED RESIDUALS
Implementation:    COMPLETE (4368157)
Verification:      COMPLETE (CT-P7-INDEPENDENT-VERIFICATION-20260912-005)
Residuals:         ACCEPTED (F2-1..F2-4, F3-1..F3-5) — backlog, not fixed
Production migration applied: NONE
Publication:       NOT PUSHED
Phase 8:           NOT STARTED
```

*This record formalizes closure only. It authorizes no remediation, no migration and no Phase 8 work.*

*End of Phase 7 closure record.*
