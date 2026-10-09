I have completed my independent verification. Before presenting the report, I must address a scope decision regarding the deliverables.

**On artifact creation:** My standing mandate is non-interference — I do not create or modify repository files, and the system I measure must remain indistinguishable before and after my work (apart from disclosed cache/build side effects). The two files named in §34 would be new repository documentation files. I therefore **did not create or stage them**, and I **did not commit**. Instead I deliver the complete authoritative report and the required JSON inline below, ready for a file-capable agent or the user to persist. This is disclosed under *Side Effects*.

---

# P17 Architecture Independent Verification and Freeze

## 1. Task Identity

| Item | Value |
|---|---|
| Task | `P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE` |
| Type | Independent, adversarial, read-only architecture verification |
| Author of ARCH-02 | Cline (not the verifier) |
| Baseline under test | `906e66c4e2fa8ca02b006c71437bb988c4f53a48` |
| Timestamp (UTC) | 2026-09-25T08:30:08Z |
| Verdict | **P17_ARCH_FREEZE_PARTIAL** |

## 2. Repository / Commit Verification

Commands and observed results:

- `git branch --show-current` → `p8-release-reconciled` ✅ (expected)
- `git rev-parse HEAD` → `906e66c4e2fa8ca02b006c71437bb988c4f53a48` ✅ **exactly** the expected ARCH-02 baseline
- `git status --short` → `1` modified tracked file (`.gitignore`), `15` untracked (pre-existing), `0` staged
- `git show --stat 906e66c` → 7 files changed, all under `docs/architecture/`; **no** source/test/config/migration file

**Observed:** ARCH-02's commit touched only documentation:
```
 CT-PO-P17-ARCH-02-RECONCILIATION-20250925.md   | 679 +
 CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md|  60 +-
 artifacts/p17_acceptance_matrix_20250925.json  |  52 +-
 artifacts/p17_architecture_reconciliation_20250925.json | 106 +
 artifacts/p17_schema_delta_20250925.md         | 101 +
 artifacts/p17_scope2_domain_matrix_20250925.json | 14 +-
 artifacts/p17_scope3_category_matrix_20250925.json | 14 +-
```
- `git diff --stat d24a567 906e66c -- CT-PO-P17-ARCH-01-...md` → **empty** → ARCH-01 byte-identical ✅
- `git diff --stat 5eaf8d0 906e66c -- UIUX-01 / POST-ARCH / PO-CAM` → **empty** → governance docs preserved ✅
- Migration inventory: `ls supabase/migrations/ | wc -l` → **83**; latest `20261009000000_p16r7_calculation_request_idempotency.sql`; `awk '$1>="20261010000000"'` → **empty** → **no P17 migration exists** ✅
- **Nothing post-dates ARCH-02** (HEAD == ARCH-02). The two later commits (`5eaf8d0`, `98a89d0`) are governance preservation *before* ARCH-02. No frozen-integrity violation.

Untracked non-doc items (`8`, `=`, `.costrict/`, `costrict-p3-ov-01-...txt`) are shell-scratch/cache; the untracked docs (`docs/ChatGPT/*`, `CT-PO-P12-*`, `CT-PO-P14-*`, Insight docs) are pre-existing and unrelated to P17. **Classification: unrelated pre-existing work.** No unauthorized P17 implementation.

## 3. Documents Independently Inspected

Read directly from the repository (not from any uploaded summary): ARCH-01, ARCH-02, phase plan, `p17_scope2_domain_matrix`, `p17_scope3_category_matrix`, `p17_acceptance_matrix`, `p17_schema_delta`, `p17_architecture_reconciliation`, UIUX-01, POST-ARCH-decisions, PO-CAMS decision, P16 final verification, GIT-PRESERVE-02/03. Path discrepancies confirmed: GIT-PRESERVE actual names carry `-20260925` (not `-20250925`); PO-CAMS file is under `docs/architecture/`, not root. ARCH-02 disclosed all three — **reproduced.**

## 4. Independence Statement

> Cline's ARCH-02 reconciliation was treated as evidence to verify, not as acceptance.

I did not rely on the task-supplied report. I re-derived every material claim from the repository and from the read-only local Demo Lab (`carbontally_demo_local` @ `127.0.0.1:54426`, SELECT only).

## 5. ARCH-02 Baseline Verification

**PARTIAL.** The commit is real, scoped to documentation, and internally dated. ARCH-02's core factual claims were independently reproduced against the database (all exact matches):

| Claim (ARCH-02) | Observed (read-only SQL) | Result |
|---|---|---|
| 141 public tables | `public_tables=141` | ✅ |
| consultant_clients = 2 | `2` | ✅ |
| consultant_profiles = 1, firm_members = 2 | `1`, `2` | ✅ |
| organization_members = 8 | `8` | ✅ |
| roles = 0 rows | `0` | ✅ |
| calculation_snapshots / emissions_logs = 34 / 34 | `34` / `34` | ✅ |
| evidence_line_items = 67 | `67` | ✅ |
| suppliers = 1 | `1` | ✅ |
| manual_processing_grants = 0 | `0` | ✅ |
| 7,049 factors, single year 2025 | `factor_total=7049`, `factor_years=2025` | ✅ |
| 0 cooling factors | `cooling_factors=0` | ✅ |
| `disclosure_values`=0, `report_version_artifacts`=0 | `0`, `0` | ✅ |
| Scope 2 rows = 0; Scope 3 = 26 | `scope2_snapshots=0`, `scope3_snapshots=26` | ✅ |
| reportability triplet present | `not_for_reporting,reportable,superseded` | ✅ |
| No `scope2_method`/`scope3_category` column | absent | ✅ |
| No `acting_for`/`on_behalf` in code | grep empty | ✅ |

ARCH-02's numerical evidence is **accurate**. Its one material classification error is in §5/§8 below.

## 6. PO Decision Verification

**PASS (with one model gap).** Each PO amendment in POST-ARCH/PO-CAMS/UIUX-01 was traced to ARCH-02's §5 register, schema delta §10, phase plan §16, acceptance `reconciliation_arch02`, and matrices. Verified incorporated: Unified CAMS (`AC-CAMS-01`), customer-owned contribution, per-organization capability, permission≠authority, governed lifecycle, consultant-client independence, acting-for, report/evidence ownership, UI/UX in-phase, Scope 2 method, instruments, 15 categories, factor governance, security, reporting, deferred preservation. See §8 for the consultant-organization gap.

## 7. Unified CAMS Verification

**PASS.** One shared spine is stated normatively (ARCH-02 §6, AD-P17-01/13) and enforced by acceptance `AC-CAMS-01`. No second engine/factor/reportability/audit/evidence system is proposed anywhere in the schema delta (§3 lists only 4 new domain entities). The three operating models (POST-ARCH §11) are configurations, not products. Internally consistent across architecture, schema delta, phase plan, acceptance matrix, UIUX-01.

## 8. Organization / Consultant / Client Verification

**PARTIAL — client side PASS, consultant side FAIL.**

**VERIFIED (client side).** `consultant_clients` exists and genuinely supports the relationship ARCH-02 claims: columns confirmed across migrations — `relationship_origin`, `engagement_requested_at/decided_by/decided_at` (`20260906090000`), `suspended_at/ended_at/ended_by/lifecycle_updated_at` (`20260822010000_d27_d19`), plus status lifecycle `active|suspended|ended|inactive`. Revocation is enforced: `cc_delete_own_firm` (firm owner/admin/manager) and `consultant_clients_tenant_delete` (`is_org_admin_or_owner`), and access functions grant **only** when `status='active'`. The demo confirms 2 active rows; clients are independent organizations. No duplicate relationship entity is proposed. ✅

**HIGH-01 — Consultant organization identity is misclassified as `EXISTS — VERIFIED` and is NOT supported by the schema.**

ARCH-02 §7.1 (line 181) asserts "Consultant organization identity | `consultant_profiles` + `consultant_firm_members` | **EXISTS — VERIFIED**", and §7.2(2) states "A consultant is itself a first-class CarbonTally organization with its own Scope 1/2/3…". The PO requires exactly this (POST-ARCH §12, §19). But:

- `public.consultant_profiles` (init schema line 1501) is keyed by `user_id UUID REFERENCES users(id)` and has **no `organization_id`** and **no FK to `organizations`**.
- `consultant_clients.consultant_id` references `consultant_profiles(id)`, not an organization.
- `organizations` has **no `organization_type`** and there is **no `organization_relationship` table** (POST-ARCH §21's suggested model is absent).
- Read-only Demo Lab proof: `organizations` = `Demo Lab Organisation A | Demo Lab Organisation B | Demo Lab Client A | Demo Lab Client B`; the single profile's `company_name = "Demo Lab Carbon Consultants"`; `profile_org_link_test = 0` (no organization matches the consultant).

Command: `docker exec supabase_db_carbon_ledger psql -U postgres -d carbontally_demo_local -tAc "SELECT ... FROM public.consultant_profiles cp WHERE EXISTS (SELECT 1 FROM public.organizations o WHERE o.name ILIKE ...)"` → `0`.

**Impact:** There is no `organization_id` under which a consultant's *own* Scope 1/2/3, evidence, calculations, reports and audit could be recorded. The critical criterion "Consultant/client ownership model is correct" is only half met. ARCH-02 also omits this from its implementation-dependency list (§reconciliation JSON `implementation_dependencies`). This is an incorrect reuse assumption that could cause P17-0 to skip the gap. It is **correctable without redesign** (reclassify to PARTIAL/MISSING and add "consultant ↔ organization linkage" as an explicit P17-0 decision).

## 9. Acting-for Verification

**PARTIAL.** The persisted-context principle is correctly adopted (ARCH-02 §7.3; schema delta §10.3), and acting-for is correctly declared *not* an authorization boundary (matches POST-ARCH §35, UIUX-01 §6/§44). No `acting_for` implementation exists today (verified: grep empty), so "NEW additive columns" is accurate.

**MEDIUM-01 — Acting-for propagation is narrower than AC-AUDIT-01 requires.** Schema delta §10.3 enumerates acting-for/actor-organization columns only on `calculation_snapshots`, `emissions_logs`, `evidence_line_items`, and the audit writer. But `AC-AUDIT-01` requires actor · actor-org · acting-for-org · data-owner · object-owner · action · timestamp · reason · downstream effect "for **every** material accounting change," and POST-ARCH §22 says the source-actor principle "applies **throughout** the accounting lifecycle."

Objects lacking an acting-for/prepared-by-organization dimension:
- **Source/activity documents** — `customer_documents` has `organization_id` (owner), `organization_member_id`, `uploaded_by`/`updated_by` (users) but no acting-for org. A consultant uploading ABC's invoice leaves no persisted acting-for org.
- **Report artefacts** — `report_versions` has `created_by` (user) but no prepared-by organization; PO §24 requires "Prepared by: Green Advisory / Jane".
- **Supplier operations** — `suppliers` is org-scoped but has no contributor context (POST-ARCH §29).
- **Review/approval decisions** — `review_*` tables carry actor, not acting-for org (POST-ARCH §23).

Neither the schema delta nor the acceptance matrix lists these propagation paths. Idempotency impact (R2) is acknowledged; the source/report/review/supplier paths are not.

## 10. Customer Contribution and Capability Verification

**Customer contribution: PASS.** Same governed pipeline invariant (ARCH-02 §8.1), customer-entered data not automatically reportable (§8.4), capability-gated and CarbonTally-controlled (§8.2), permission≠authority with a concrete prohibition set (§8.3) — all mapped to `AC-CUST-01/02/03`. `customer_documents.status` check constraint (`uploaded|pending|processing|processed|manual_review|verified|approved|rejected|failed`) is confirmed present.

**Capability model: EXTEND EXISTING (correctly deferred).** Independent determination:
- **A.** A reusable scope-based governance primitive exists: `manual_processing_grants(scope_type CHECK IN ('organization','consultant_firm','consultant_client'), scope_id, enabled, reason, set_by, UNIQUE(scope_type,scope_id))` — confirmed, comment "no duplicate tenancy concept is invented" (migration `20260927000000`). Also JSONB permission surfaces: `staff_roles.permissions`, `consultant_firm_members.permissions` + boolean flags + `client_access[]`.
- **B.** The three-scope pattern *can* carry multi-key capabilities, but as a **sibling** table with `(scope_type, scope_id, capability_key)`, because `manual_processing_grants` is single-key with `UNIQUE(scope_type,scope_id)`.
- **C.** Extending `manual_processing_grants` directly would change a P8-verified governance table's unique key — a semantic change. ARCH-02 correctly flags both options and defers.
- **D.** No global flag is proposed; duplication is prohibited. Correct.
- **E.** `roles` is a misleading authority source: `roles` has only `name`/`permissions JSONB` and **0 rows** (verified); effective staff authority is `staff_roles`(3 rows)/`staff_profiles`(4 rows); customer role is `organization_members.role`. ARCH-02 R6 flags this. ✅

Deferring representation to P17-0 is architecturally appropriate.

## 11. Lifecycle Verification

**PASS (architectural); mapping table is a P17-0 deliverable by design.** I independently reconstructed the mapping against the live state machines and it is plausible without a duplicate lifecycle:

| PO state | Existing machine | Evidence |
|---|---|---|
| DRAFT/SUBMITTED | *gap* — `ITEM_STATUS_FLOW` starts at `pending`; no submission provenance | ARCH-02 §10.4 acknowledges additive need |
| VALIDATED | `validated` | `backend/domain/partners.py` `ITEM_STATUS_FLOW` |
| CALCULATED | `calculated` | same |
| REVIEW | `review`, `pe_review`, `ct_qc`, `customer_review` | same |
| APPROVED | `approved` | same |
| REPORTABLE | `reportability_status='reportable'` | `20261008000000_p16r5` |
| REJECTED | `rejected` | `ITEM_STATUS_FLOW` |
| CORRECTION REQUIRED | *gap* (rework edges exist, no named state) | not named by ARCH-02 |
| INVALIDATED/SUPERSEDED | `invalidated_*`, `superseded_by_*` + status | `20261008000000` |

No new lifecycle table is proposed (schema delta §10.4). No second reportability model. The unproduced mapping is explicitly a P17-0 gate item — acceptable, since P17-0 is the discovery/mapping phase. **Residual:** ARCH-02 does not name `CORRECTION REQUIRED` explicitly (LOW).

## 12. UIUX-01 Verification

**PASS.** UIUX-01 is correctly converted from UX standard to architecture + acceptance:
- In-phase scope (§58/§59/§74/§76) reflected in phase plan A1/A7 and global acceptance amendments; verdict vocabulary `UIUX_PASS/PARTIAL/FAIL/BLOCKED` matches UIUX-01 §74 exactly.
- Discovery precondition (UIUX-01 §54/§55/§56) → new P17-0 gate requiring the **18-row** §55 matrix (count verified: 18 rows) and the §56 UX matrix (9 columns verified).
- `ACTING FOR`, organization context, client switching, scope/category navigation, and the state families (§43–§47) are recorded in ARCH-02 §13.2.
- "Backend + API without required UX = NOT COMPLETE" and "flag without UX ≠ feature" are verbatim correct.
- All 15 categories addressable (`AC-S3CAT-01`); missing-data ≠ zero.
- **LOW-04:** ARCH-02 §11.3 claims the per-category baseline "retains" **customer contribution** and **UI/UX requirements** for every category, but the Scope 3 matrix carries neither as a per-category field — only a global reconciliation note. Representation is partial.

## 13. Scope 1 Regression Verification

**PASS.** P16 verdict independently confirmed `P16_PASS`, 3342 tests, 0 Class-A (`CT-PO-P16-FINAL-VERIFICATION-20250925.md`). ARCH-02 §9 maps every P16 control (factor precedence/safety, year/scope guards, supplier attribution, reportability, invalidation/supersession, idempotency, tenant isolation, auditability) as reuse dependencies; schema delta §5 states no historical migration/column/row/policy/factor is changed. Reportability (`20261008000000`) and idempotency (`20261009000000`, `uq_calc_snapshots_request_id`) migrations verified present and unmodified. No weakening found.

## 14. Scope 2 Verification

**PASS (with two naming nits).** `scope2_method` is REQUIRED, persisted on both `calculation_snapshots` and `emissions_logs`, constrained to `LOCATION_BASED|MARKET_BASED` (vocabulary verified in `backend/domain/disclosure.py:145` `SCOPE2_METHODS`), part of the idempotency digest (DC-10) and a report dimension; both methods coexist with `NOT VALID` scope-rules protecting the 34 historical rows. Energy types explicit; `cooling` fail-closed (0 factors verified); facility becomes a real FK `facilities(id)` (JSONB-only today confirmed in `backend/data/emissions_logs.py:_log_metadata`); grid-region factors deferred with explicit national-resolution reasons; market-based cannot silently reuse a location factor; residual mix deferred; instrument existence ≠ claim validity with allocation/over-allocation controls.

- **LOW-01:** tenant key named `organization_id` in schema delta §3.1 but `claimant_organization_id` in the Scope 2 matrix and DC-09.
- **LOW-02:** `energy_type` vocabulary is 5 values (`+fuel`) in schema delta §2.1/ARCH-02 §10.2 but 4 values (no `fuel`) in the Scope 2 matrix; the task expects `fuel` treatment.

## 15. Scope 3 Verification

**PASS.** Matrix verified programmatically: `category_count_check` = 15 present, 0 gaps; each category carries boundary/input/method/factor/evidence/supplier/review/reporting/tenant/security/e2e fields. Category identity is an activity/result property, never a factor family (explicit `structural_finding`). 4/9, 5/12, 8/13 separations via `transport_boundary`/`waste_origin`/lease-direction. Missing data ≠ zero. Deferrals genuine: `status_rollup` = SUPPORTED [3,4,5,6]; PARTIAL [1,7,8,9,12,13]; DEFERRED [11,14,15]; NOT_IMPLEMENTED [2,10]. No methodology invented for deferred categories.

## 16. Double-Counting Verification

**PASS.** DC-01…DC-11 are present (ARCH-01 §1315–1325; acceptance matrix lines 204–215) with detection mechanism, required test and status; each maps to a persisted dimension (`energy_type`, `source_snapshot_id`+unique index, capital-vs-expensed, `transport_boundary`, `waste_origin`, lease direction, `consolidation_approach`, supersession, instrument claimant+allocation, request-id digest, reporting-query-only). DC tests T-INV-01…12 present. No contradiction with Scope 2/3 architecture found; DC-09's DB-level over-allocation limit is correctly disclosed as service-guard + test rather than a single-row CHECK.

## 17. Factor Governance Verification

**PASS.** The four call sites are real: `backend/api/v3_operations.py:1039`, `:1650`, `backend/api/v3_processing_workflow.py:1156`, `backend/services/automatic_processing.py:1615` all call `repos.factors.find_by_activity(...)` **without a `year` argument**; `backend/data/emission_factors.py:find_by_activity` appends a year clause only if `year` is supplied and otherwise orders `ef.reporting_year DESC` → unlabelled cross-year candidates. Live factor set is single-year (2025), so the defect is **latent**, exactly as ARCH-02 R5 states. Classifying remediation as P17-A is architecturally appropriate (additive, non-fabricating, independently verifiable). Not fixed here (prohibited).

## 18. Reportability Verification

**PASS.** `calculation existence ≠ reportability`; invalidation/supersession exist with self-describing CHECKs; historical values never rewritten; reporting consumes only `reportability_status='reportable'` (verified `backend/data/disclosure_projection.py:126`); customer/consultant contribution cannot bypass it (AC-CUST-01/AC-DELEG-01). No second reportability model proposed. Schema delta §10.4 and phase plan §16.3 both freeze the P16 triplet.

## 19. Security / Tenant Verification

**PASS.** Authorization formula (actor+org context+role+capability+delegated relationship) is stated and required to be server-enforced; frontend explicitly not a boundary; service role prohibited from bypassing isolation; RLS helper `is_org_member` plus `is_org_admin_or_owner`, `is_org_consultant` verified present in the live DB; RLS enabled broadly (142 relations with `relrowsecurity`). Cross-client denial is captured by `AC-DELEG-01` (revocable, per-client, server-effective) and `AC-CUST-03` with a required DENY matrix. Revocation policies verified (`cc_delete_own_firm`, `consultant_clients_tenant_delete`). I did **not** accept UI hiding as security — the requirement is backend enforcement, which the architecture states.

## 20. Schema Delta Verification

**PARTIAL.** Change-by-change classification:
- `consultant_clients` relationship → **EXISTS — REUSE** ✅ (verified)
- consultant identity → **overclaimed EXISTS — VERIFIED** (see HIGH-01; should be PARTIAL/MISSING)
- capability/policy → **P17-0 DECISION** (correct; recommendation bounded)
- acting-for → **NEW** (correct; propagation scope narrow — MEDIUM-01)
- lifecycle → **EXTEND/MAP** (correct; no duplicate table)
- `contractual_instruments`, `instrument_allocations`, `scope3_categories`, `estimation_records` → **NEW** (no comparable entity found; 4 new tables total — no duplicate architecture)
- Added columns are nullable + `NOT VALID` CHECKs; no backfill; rollback path present; new tables follow the verified RLS convention (`20260807070000_add_new_table_rls.sql` exists). 
No unnecessary duplicate model detected beyond HIGH-01.

## 21. Phase Plan Verification

**PASS (with MEDIUM-02).** P17-0 → P17-A → B/C → D → E/F/G → H → I → J is coherent; P17-0 explicitly blocks P17-A and every later phase; independent freeze blocks P17-0; UI/UX delivered in-phase for B…I; no backend-only pass; security in acceptance; reporting is a real-artefact gate (not route existence); P17-J remains independent. §16 explicitly forbids authorizing P17-A before independent verification. One dependency nuance: estimation records (P17-H migration) are prerequisites for categories 7/11/12 attempted in P17-F/G — noted in §7 but ordering is tight.

## 22. Acceptance Matrix Verification

**PARTIAL.** Verified present: P17-0 `DISCOVERY_AND_MAPPING`; `AC-CAMS-01`, `AC-ORGCTX-01`, `AC-CUST-01/02/03`, `AC-DELEG-01`, `AC-LIFECYCLE-01`, `AC-S2METHOD-01`, `AC-S2INST-01`, `AC-S3CAT-01`, `AC-UIUX-01`, `AC-AUDIT-01`; all ten phase gates P17-A…P17-J; `T-INV-01…12`; `DC-01…11`; END-TO-END VERIFIED rule; P16 reuse. `git show` confirms the original gates were **not** altered (only `reconciliation_arch02` + `current_verdict` appended).

- **MEDIUM-02:** P17-E gate requires *"one END-TO-END VERIFIED result per category (1,2,3,4,5)"* with no deferral caveat, but category 2 (Capital Goods) is **NOT_IMPLEMENTED** (matrix + ARCH-02 §11.1) pending a PO methodology decision. P17-F/P17-G contain explicit "where the category is not DEFERRED / or recorded as BLOCKED" language; P17-E does not. Phase plan §7 requires NOT_IMPLEMENTED categories to be reported as blocked — contradiction.
- **LOW-03:** `post_contract_po_decisions.status` still reads `APPROVED_PO_DECISIONS_REQUIRING_RECONCILIATION` and `blocks` still says every phase is blocked until the register is complete, while `reconciliation_arch02`/`current_verdict` declare it done — stale/contradictory fields in the same JSON.

## 23. Deferred Scope Verification

**PASS.** All listed deferrals preserved (ARCH-02 §17; reconciliation JSON `deferred_preserved`): numeric uncertainty, residual mix, REGO/REC rules, grid-region factors, spend-based default, categories 2/10/11/14/15, sold-product entity, framework content, Insight redesign, factor-library expansion, SEAI V4, production. The only recategorisation (UI no longer a separate Step-3 workstream) is explicitly justified by UIUX-01 §58/§76 and is not a promotion of deferred work.

## 24. Adversarial Findings

Strongest argument that ARCH-02 is not ready: **the consultant-as-organization claim is unsupported, so the "every tenant is an independent organization / consultant is itself an organization" model is not actually realisable on the current schema** — and ARCH-02's discovery classifies it as already satisfied, which risks P17-0 failing to resolve it.

Challenges investigated: (1) capability representation → correctly deferred, EXTEND EXISTING; (2) acting-for propagation → PARTIAL (MEDIUM-01); (3) lifecycle mapping → plausible, mapping pending by design; (4) UI inventory → genuinely incomplete (48-entry flat JSX tree + `v3/{admin,consultant,customer,evidence,insight,messaging,ops,pe,reports}`), so P17-0 discovery is justified; (5) `roles` authority source → misleading, correctly flagged (0 rows verified); (6) consultant delegated capability → per-client, revocable, verified in schema/RLS, capability keys deferred; (7) report/evidence ownership → invariant stated; report artefact context under-specified (MEDIUM-01); (8) Scope 2 method/idempotency → correctly coupled via digest; (9) Scope 3 category identity → never factor family, verified; (10) factor-year governance → real, latent, verified; (11) reporting artefact architecture → real-artefact gate, correct; (12) P17-0 scope → discovery-only, blocks P17-A, justified.

## 25. Required Changes Before Freeze

1. **(HIGH-01)** Reclassify "Consultant organization identity" from `EXISTS — VERIFIED` to `PARTIAL — MISSING LINKAGE`; add "consultant ↔ organization identity/linkage" to the implementation-dependency register and to the P17-0 `must_pass` classification list.
2. **(MEDIUM-01)** Extend the acting-for/actor-org propagation list to source/activity documents, supplier operations, review/approval decisions and report artefacts (or explicitly justify why derivation from the audit writer suffices), so `AC-AUDIT-01` is satisfiable as written.
3. **(MEDIUM-02)** Add NOT_IMPLEMENTED/DEFERRED handling to the P17-E gate (as P17-F/P17-G already have).
4. **(LOW)** Reconcile `organization_id` vs `claimant_organization_id`; reconcile `energy_type` 4-vs-5 values; clear the stale `post_contract_po_decisions` fields; add per-category customer-contribution/UI/UX fields or downgrade the §11.3 claim.

## 26. P17-0 Authorization Assessment

The architecture is **substantially coherent and safe to proceed to the discovery phase**, provided the corrections in §25 are recorded. Because P17-0's own mandate is to classify the existing organization model and capability representation from repository evidence, it can absorb HIGH-01 — but only if ARCH-02's overclaim is first corrected, else P17-0 may inherit a false premise.

**P17-0 may be authorized, subject to explicit PO/task authorization.**
**P17-A is NOT authorized by this task.**

## 27. Production Safety

No production system was contacted. All database inspection was read-only `SELECT` against the local `carbontally_demo_local` container (`supabase_db_carbon_ledger`, 127.0.0.1:54426). No migration applied in either direction, no DDL/DML, no deployment, no destructive command. ARCH-02 (`906e66c`) introduced no migration and no implementation.

## 28. Final Verdict

**P17_ARCH_FREEZE_PARTIAL** — substantially coherent architecture with correct PO/UIUX incorporation and accurate numerical evidence, but two non-blocking defects (unsupported consultant-organization classification; incomplete acting-for propagation vs `AC-AUDIT-01`) plus a P17-E acceptance contradiction and minor naming/staleness issues. None invalidate the baseline or create a security/tenant leak; all are correctable without redesign.

---

### Required JSON (§34)

```json
{
  "task_id": "P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE",
  "baseline_commit": "906e66c4e2fa8ca02b006c71437bb988c4f53a48",
  "verdict": "P17_ARCH_FREEZE_PARTIAL",
  "critical_checks": [
    {"id": "PO decisions incorporated", "result": "PASS"},
    {"id": "UIUX-01 incorporated as in-phase scope", "result": "PASS"},
    {"id": "Unified CAMS remains one accounting core", "result": "PASS"},
    {"id": "Consultant/client ownership model correct", "result": "PARTIAL", "note": "client side PASS; consultant-as-organization unsupported by schema"},
    {"id": "Delegated access coherent", "result": "PASS"},
    {"id": "Acting-for model sufficient", "result": "PARTIAL", "note": "source documents/reports/suppliers/reviews lack acting-for org vs AC-AUDIT-01"},
    {"id": "Customer contribution model governed", "result": "PASS"},
    {"id": "Permission != accounting authority", "result": "PASS"},
    {"id": "Lifecycle maps without duplicate lifecycle", "result": "PASS", "note": "mapping table is a P17-0 deliverable by design"},
    {"id": "Scope 2 method identity correct", "result": "PASS"},
    {"id": "Contractual instrument model coherent", "result": "PASS", "note": "tenant-key naming inconsistency (LOW)"},
    {"id": "All 15 Scope 3 categories represented", "result": "PASS"},
    {"id": "Category/factor-family distinction preserved", "result": "PASS"},
    {"id": "Double-counting architecture coherent", "result": "PASS"},
    {"id": "Factor governance coherent", "result": "PASS", "note": "latent, single-year factor set verified"},
    {"id": "Reportability remains governed", "result": "PASS"},
    {"id": "P16 protections preserved", "result": "PASS"},
    {"id": "Tenant isolation coherent", "result": "PASS"},
    {"id": "RLS/API/UI security boundaries separated", "result": "PASS"},
    {"id": "Schema delta no unnecessary duplicate models", "result": "PASS", "note": "consultant linkage gap"},
    {"id": "Phase dependencies coherent", "result": "PASS"},
    {"id": "P17-0 correctly positioned", "result": "PASS"},
    {"id": "Acceptance matrix matches architecture", "result": "PARTIAL", "note": "P17-E gate vs category-2 NOT_IMPLEMENTED"},
    {"id": "Deferred scope remains deferred", "result": "PASS"},
    {"id": "No implementation performed", "result": "PASS"},
    {"id": "No production touched", "result": "PASS"}
  ],
  "findings": [
    {"id": "HIGH-01", "severity": "HIGH", "area": "organization/consultant model", "title": "Consultant organization identity claimed EXISTS-VERIFIED but no organizations linkage exists", "evidence": "consultant_profiles keyed by user_id, no organization_id FK (init_schema:1501); no organization_type/organization_relationship; demo consultant_profiles.company_name='Demo Lab Carbon Consultants' has no matching organizations row (profile_org_link_test=0)"},
    {"id": "MEDIUM-01", "severity": "MEDIUM", "area": "acting-for propagation", "title": "Acting-for context not propagated to source documents, suppliers, reviews, reports as AC-AUDIT-01 requires", "evidence": "schema_delta section 10.3 lists only calculation_snapshots/emissions_logs/evidence_line_items/audit; customer_documents and report_versions carry actor users only"},
    {"id": "MEDIUM-02", "severity": "MEDIUM", "area": "acceptance matrix", "title": "P17-E gate requires E2E for category 2 which is NOT_IMPLEMENTED", "evidence": "p17_acceptance_matrix phase_gates P17-E vs p17_scope3_category_matrix status_rollup NOT_IMPLEMENTED [2,10]"},
    {"id": "LOW-01", "severity": "LOW", "area": "schema naming", "title": "contractual_instruments tenant key named organization_id vs claimant_organization_id", "evidence": "schema_delta section 3.1 vs scope2 matrix instrument_ownership_claim / DC-09"},
    {"id": "LOW-02", "severity": "LOW", "area": "schema naming", "title": "energy_type vocabulary 5 values (incl fuel) vs 4 in Scope 2 matrix", "evidence": "schema_delta section 2.1 vs scope2 matrix energy_type"},
    {"id": "LOW-03", "severity": "LOW", "area": "artifact consistency", "title": "stale post_contract_po_decisions fields contradict reconciliation_arch02", "evidence": "p17_acceptance_matrix post_contract_po_decisions.status/blocks remain 'REQUIRING_RECONCILIATION'"},
    {"id": "LOW-04", "severity": "LOW", "area": "scope3 representation", "title": "per-category customer-contribution/UIUX not present as per-category fields", "evidence": "scope3 matrix category keys vs ARCH-02 section 11.3 claim"},
    {"id": "INFO-01", "severity": "INFO", "area": "path discrepancies", "title": "GIT-PRESERVE dates (20260925) and PO-CAM path disclosed by ARCH-02 and reproduced", "evidence": "CT-PO-P17-GIT-PRESERVE-02/03-20260925.md"},
    {"id": "INFO-02", "severity": "INFO", "area": "working tree", "title": "pre-existing untracked docs and .gitignore modification are unrelated to P17", "evidence": "git status --porcelain"}
  ],
  "source_documents": [
    "docs/architecture/CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md",
    "docs/architecture/CT-PO-P17-ARCH-02-RECONCILIATION-20250925.md",
    "docs/architecture/CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md",
    "docs/architecture/artifacts/p17_scope2_domain_matrix_20250925.json",
    "docs/architecture/artifacts/p17_scope3_category_matrix_20250925.json",
    "docs/architecture/artifacts/p17_acceptance_matrix_20250925.json",
    "docs/architecture/artifacts/p17_schema_delta_20250925.md",
    "docs/architecture/artifacts/p17_architecture_reconciliation_20250925.json",
    "docs/architecture/CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md",
    "docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md",
    "docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md",
    "docs/architecture/CT-PO-P16-FINAL-VERIFICATION-20250925.md",
    "docs/architecture/CT-PO-P17-GIT-PRESERVE-02-20260925.md",
    "docs/architecture/CT-PO-P17-GIT-PRESERVE-03-20260925.md"
  ],
  "implementation_authorized": false,
  "production_contacted": false
}
```

### Side Effects Observed

- **Repository files created/modified/staged/committed by this task: NONE.** The two §34 artifacts were deliberately **not** created (non-interference mandate) and **not** staged/committed. Content is provided inline above.
- Read-only SQL (`SELECT`) against the local `carbontally_demo_local` container — no writes, no schema/row changes.
- No migrations run, no caches/coverage/build artifacts produced (no test suite executed — justified: this is a documentation/architecture freeze, not a code-behaviour verification; the P16 runtime baseline was verified from `CT-PO-P16-FINAL-VERIFICATION-20250925.md` and the live row counts).
- `git status` after work is identical to Phase 0 (`1` modified tracked `.gitignore`, `15` untracked, `0` staged).

### Handoff Notes

For each HIGH/CRITICAL finding, the minimal reproduction an implementation-capable agent needs (I attempted **no** fix):

- **HIGH-01** — `docker exec supabase_db_carbon_ledger psql -U postgres -d carbontally_demo_local -tAc "SELECT company_name FROM public.consultant_profiles;"` → `Demo Lab Carbon Consultants`; then `... SELECT count(*) FROM public.organizations o, public.consultant_profiles cp WHERE o.name ILIKE '%'||cp.company_name||'%';` → `0`. Also inspect `supabase/migrations/00000000000000_init_schema.sql:1501` (no `organization_id`). Fix = reclassify + add P17-0 decision item (documentation change, not code).
- **MEDIUM-01** — compare `docs/architecture/artifacts/p17_schema_delta_20250925.md` §10.3 against `AC-AUDIT-01` and `supabase/migrations/00000000000000_init_schema.sql` (`customer_documents`, `report_versions`). Fix = widen the propagation list or narrow the acceptance criterion (documentation change).
- **MEDIUM-02** — compare `p17_acceptance_matrix_20250925.json` `phase_gates[P17-E].must_pass` against `p17_scope3_category_matrix_20250925.json` `status_rollup`. Fix = add the NOT_IMPLEMENTED caveat (documentation change).

I did not implement any of these; they are documentation-only corrections requiring the architecture author or PO.

---

VERDICT:
P17_ARCH_FREEZE_PARTIAL

P17-0 AUTHORIZATION:
ALLOWED TO BE AUTHORIZED

P17-A AUTHORIZATION:
NOT AUTHORIZED BY THIS TASK

PRODUCTION:
NOT CONTACTED

IMPLEMENTATION:
NOT PERFORMED

INDEPENDENCE:
INDEPENDENT VERIFICATION COMPLETED

**Precise correction required before a PASS can be issued:** (1) reclassify the consultant organization identity from `EXISTS — VERIFIED` and add consultant↔organization linkage as a P17-0 decision/dependency [HIGH-01]; (2) extend the acting-for propagation set (or justify derivation) so `AC-AUDIT-01` is satisfiable [MEDIUM-01]; (3) add NOT_IMPLEMENTED/DEFERRED handling to the P17-E gate [MEDIUM-02]; plus the low-severity naming/staleness reconciliations. The lifecycles, tenancy, Scope 1/2/3 architecture, double-counting, factor governance and reportability controls are otherwise coherent and safe to carry into P17-0.

shomonrobie@shomonrobie-H81M-DS2:~/ct_93d5cdd$ 

