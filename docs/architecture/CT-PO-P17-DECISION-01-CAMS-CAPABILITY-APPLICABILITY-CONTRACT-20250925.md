# CT-PO-P17-DECISION-01 — Freeze CarbonTally CAMS Organization Capability and Applicability Contract

**Document ID:** `CT-PO-P17-DECISION-01-CAMS-CAPABILITY-APPLICABILITY-CONTRACT-20250925`
**Task ID:** `P17-DECISION-01-20260925-CAMS-CAPABILITY-APPLICABILITY-CONTRACT`
**Task type:** PRODUCT / ARCHITECTURE DECISION AND RECONCILIATION — **documentation only**
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Date:** 2025-09-25
**Production authorization:** NOT AUTHORIZED
**Production contacted:** NO

---

## 1. Task identity, baseline and scope

### 1.1 Baseline verification (performed before any document was read)

| Check | Required | Observed | Result |
|---|---|---|---|
| Branch | `p8-release-reconciled` | `p8-release-reconciled` | **MATCH** |
| `git rev-parse HEAD` | `de4b0cac8cc18f8a60436052783b86f53c06c8f9` | `de4b0cac8cc18f8a60436052783b86f53c06c8f9` | **MATCH** |
| P17-IMPLEMENT-10 report present | `docs/architecture/CT-PO-P17-IMPLEMENT-10-PRODUCT-CONTRACT-APPLICABILITY-REPORTING-SUPPLIER-20250925.md` | present, 907 lines, 52,733 bytes | **PRESENT** |

The baseline SHA **matches exactly**. This task therefore proceeds and does **not** STOP.

### 1.2 What this task is, and is not

This is a **decision-support and reconciliation artifact**. It establishes what the
authoritative CarbonTally sources *actually* say about:

* organization capabilities,
* carbon-accounting operating models,
* Scope 3 category applicability,
* category capability/status semantics,
* the relationship between applicability and the accounting lifecycle, and
* the relationship between organization capability and category methodology maturity.

It **does not** implement anything. Per task §17 the following are explicitly excluded
and were **not** performed:

| Excluded action | Performed? |
|---|---|
| migrations created / altered | **NO** |
| schema/policy/RLS changed | **NO** |
| API routes created or altered | **NO** |
| services / calculation logic / repositories changed | **NO** |
| data modified, seeded or demo data touched | **NO** |
| UI created | **NO** |
| any database written (incl. `carbontally_test`, `carbontally_demo_local`) | **NO** |
| production contacted | **NO** |
| `.gitignore` modified | **NO** |
| pre-existing untracked files touched | **NO** |

### 1.3 The central question this task had to answer

P17-IMPLEMENT-09 and P17-IMPLEMENT-10 both discovered that the proposed organization-facing
applicability vocabulary —

```
CALCULATED · ESTIMATED · UNDER_REVIEW · NO_DATA_YET · NOT_APPLICABLE · EXCLUDED_WITH_REASON
```

— is **not present in the authoritative P17 Product Specification**. P17-IMPLEMENT-10
recorded that as `STOPPED — PO DECISION REQUIRED` and refused to invent it.

This task had to determine what the authoritative sources *do* establish. The answer,
established from source evidence in §4 and §7, is materially more useful than "nothing
exists": **CarbonTally already has a ratified, independently verified, implemented
applicability-and-capability model — but it lives in the Phase 8 *disclosure* layer, and
P17 has never been reconciled with it.** That is the finding this artifact freezes.

---

## 2. Working-tree state and scope guarantee

| Item | State |
|---|---|
| Branch | `p8-release-reconciled` |
| Baseline HEAD | `de4b0cac8cc18f8a60436052783b86f53c06c8f9` |
| Ending HEAD | recorded in §20.3 and in the companion SHA record |
| Tracked modifications at start | `.gitignore` **only** (pre-existing, deliberately not committed — same convention as P17-IMPLEMENT-09 and -10) |
| Pre-existing untracked files | 18 — **untouched** |
| Files this task creates | **1** (this document) |
| Files this task modifies | **0** existing files (except the appended SHA record commit) |

**Scope guarantee.** `git diff --name-only <baseline>..HEAD` at the end of this task must
show **documentation-only** changes. That verification is recorded in §19.

---

## 3. Documents reviewed

### 3.1 Primary authoritative (PO-authored) sources

| # | Document | Role |
|---|---|---|
| A | `docs/architecture/P17-PRODUCT-01 — Complete Scope 2 + Scope 3 Processing & Evidence Product Specification.md` (1,374 lines) | The P17 product specification. **Contains no applicability model** (§4.2). |
| B | `docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` (854 lines) — **D1** | APPROVED — PRODUCT BASELINE. §4 capability policy, §7 lifecycle, §11 operating models, §12 role/capability, §14–§16 scope contracts, **§19 organization capability management UX**. |
| C | `docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` (1,481 lines) — **D2** | APPROVED PRODUCT-OWNER DECISIONS. §5–§8 ownership/capability, §11 operating models, §12–§20 consultant model, §21 organization types, §22–§25 actor/report/evidence ownership, **§34 capability matrix**, §35 authorization principle, §36 tenant isolation, §37 no parallel engines, **§42 capability management UX**. |

`D1`/`D2` are the identifiers ARCH-01 itself uses (`ARCH-01:263` cites
"post-contract PO decisions **D1 §2/§21, D2 §2/§37**"), so the mapping is
source-corroborated, not inferred by this task.

### 3.2 P17 architecture freeze / reconciliation chain

| # | Document |
|---|---|
| D | `docs/architecture/CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md` (1,673 lines) — AD-P17-01…13, §4 capability inventory, §9–§40 category contracts, §42 disclosure/framework separation |
| E | `CT-PO-P17-ARCH-02-RECONCILIATION-20250925.md` |
| F | `CO-STRING-P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE.md` |
| G | `CT-PO-P17-ARCH-04-RECONCILIATION-20250925.md` |
| H | `CT-PO-P17-ARCH-05-INDEPENDENT-REVERIFICATION-FREEZE-20250925.md` |
| I | `CT-PO-P17-ARCH-06-RECONCILIATION-20250925.md` (481 lines) |
| J | `CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md` |
| K | `CT-PO-MASTER-WORKPLAN-20260925.md` |
| L | `CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md` |

(all under `docs/architecture/`)

### 3.3 P17 implementation reports (historical; AGENTS.md §80)

`CT-PO-P17-IMPLEMENT-04` … `-10` and `CT-PO-P17-IMPLEMENT-MASTER-01`, all under
`docs/architecture/`: `-04-CANONICAL-ACCOUNTING-WRITE-PIPELINE`,
`-05-SCOPE2-CALCULATION`, `-06-CONTRACTUAL-INSTRUMENT-REPOSITORY`,
`-07-SCOPE3-ALL-15-CATEGORIES`, `-08-SCOPE3-API-PERSISTENCE-COMPLETION`,
`-09-COMPLETE-SCOPE2-SCOPE3-ALL15`,
`-10-PRODUCT-CONTRACT-APPLICABILITY-REPORTING-SUPPLIER` (907 lines), `-MASTER-01`.

### 3.4 Machine-readable P17 artifacts (`docs/architecture/artifacts/`)

| # | Artifact |
|---|---|
| U | `p17_scope3_category_matrix_20250925.json` — 15-category matrix, `architecture_status_legend`, `status_rollup`, `structural_finding`, `status_semantics_authority` |
| V | `p17_acceptance_matrix_20250925.json` — phase gates, `T-INV-01…12`, `DC-01…11`, `status_conditional_acceptance_rule`, `post_contract_po_decisions` |
| W | `p17_schema_delta_20250925.md` |
| X | `p17_scope2_domain_matrix_20250925.json` |
| Y | `p17_architecture_reconciliation_20250925.json` |

### 3.5 Phase 8 disclosure-model authority (the decisive discovery)

| # | Document |
|---|---|
| Z1 | `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md` |
| Z2 | `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` (`DM-1`…`DM-7`, `D1`…`D17`) |
| Z3 | `CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md` |
| Z4 | `CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md` (`PQ-1`…`PQ-8`) |
| Z5 | `docs/cline/reports/CT-P8-B1-PO-DECISION-CLOSURE-20260912-010.md` |
| Z6 | `CARBONTALLY_PHASE8_B3_IMPLEMENTATION_CONTRACT_20260913.md` (`B3-D1`…`B3-D8`) |
| Z7 | `CARBONTALLY_PHASE8_B4_IMPLEMENTATION_CONTRACT_20260913.md` (`DM-5` finalisation gate) |
| Z8 | `docs/cline/reports/CT-P8-B3-CLOSURE-20260913-051.md`, `CT-P8-B3-INDEPENDENT-VERIFICATION-20260913-033.md` |

(Z1–Z4, Z6, Z7 under `docs/architecture/`)

### 3.6 Implementation and schema inspected (read-only)

| # | Path |
|---|---|
| AA | `backend/domain/disclosure.py` — ratified vocabularies and validators |
| AB | `backend/domain/disclosure_projection.py` — `derive_effective_class`, `decide_projection`, `UNSUPPORTED_CAPABILITIES` |
| AC | `backend/domain/disclosure_narrative.py`, `backend/domain/disclosure_exposure.py` |
| AD | `backend/domain/data_quality.py` — `DataQuality` (9 values), `reporting_bucket`, `quality_mix` |
| AE | `supabase/migrations/20260914000000_p8_b1_disclosure_model_foundation.sql` — `disclosure_applicability_assessments` |
| AF | `supabase/migrations/20260927000000_p8_fin06_manual_processing_governance.sql` — `manual_processing_grants` |
| AG | `supabase/migrations/20261008000000_p16r5_result_reportability_lifecycle.sql` |
| AH | `supabase/migrations/20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` |
| AI | `supabase/migrations/20261011000000_p17c_contractual_instruments_and_allocations.sql` |
| AJ | `supabase/migrations/20261012000000_p17d_scope3_category_taxonomy.sql` |
| AK | `supabase/migrations/20261013000000_p17h_estimation_and_assumption_records.sql` |
| AL | `supabase/migrations/20261014000000_p17_10_product_contract_reporting_dimensions.sql` |

### 3.7 Governance

`AGENTS.md`, in particular §2 (source-of-truth hierarchy), §15–§18 (factor precedence,
provenance, pipeline), §44–§45 (security), §62 (PO decision rule / do not invent business
policy), §66–§67 (schema and RLS), §73 (acceptance language), §80 (historical findings),
§84 (reporting standard).

---

## 4. Source-authority classification

### 4.1 Classification vocabulary used (task §4)

Every proposition in this document is classified as **exactly one** of:

| Class | Meaning |
|---|---|
| **AUTHORITATIVE** | Stated by a ratified PO/architecture source. Must be implemented as written. |
| **EXPLICITLY DEFERRED** | The authoritative source itself says the item is unresolved / to be reconciled / a later work package. |
| **IMPLEMENTED BUT NOT AUTHORITATIVE** | Code/schema exists and behaves, but no ratified product source mandates it. Cannot be relied on as product contract without a PO decision. |
| **INFERRED** | A sound architectural deduction from authoritative sources that those sources do not themselves state. Expressly *not* a requirement. |
| **MISSING / PO DECISION REQUIRED** | No authoritative source establishes it. Must not be invented (AGENTS.md §62). |

### 4.2 Objective finding 1 — `P17-PRODUCT-01` definitely contains no applicability model

Independently reproduced by this task (not accepted from P17-IMPLEMENT-10 on trust):

| Search | Scope | Result |
|---|---|---|
| `grep -c -i 'applicab'` | `P17-PRODUCT-01` (all 1,374 lines) | **`0`** — the token `applicab*` never appears |
| `grep -n -i 'capab'` | `P17-PRODUCT-01` | **no lines** — "capability" is not a P17-PRODUCT-01 concept either |
| `grep -o -i 'applicab[a-z]*'` | `artifacts/p17_scope3_category_matrix_20250925.json` | **4 matches, all the ordinary English adjective** ("applicable"), never a state name |
| `grep -rn 'NOT_APPLICABLE\|NO_DATA_YET\|EXCLUDED_WITH_REASON'` | `docs/**/*.md` | hits only in Phase 8 *disclosure* documents and P17-09/10 report prose |
| `grep -rn 'NOT_APPLICABLE'` | `backend/**/*.py` | **zero** in P17 accounting code; only in `domain/disclosure*.py` |

**Conclusion (AUTHORITATIVE).** The six-value applicability vocabulary is **absent from the
authoritative P17 product contract**. It exists only in the P17-IMPLEMENT-09 report, which
sits near the bottom of the AGENTS.md §2 hierarchy and is historical unless reverified.
P17-IMPLEMENT-10 was therefore correct to STOP. This artifact does not resurrect it.

### 4.3 Objective finding 2 — the decisive discovery: a ratified applicability/capability model already exists

`P17-PRODUCT-01` is not the only authoritative source. The repository already contains a
**ratified, PO-decided, independently verified and implemented** applicability-and-capability
model in the **Phase 8 disclosure layer**:

| Existing sanctioned vocabulary | Where ratified | Where implemented |
|---|---|---|
| `APPLICABILITY_STATUSES` = `APPLIES`, `DOES_NOT_APPLY`, `UNDETERMINED`, `CUSTOMER_INPUT_REQUIRED` | `D13`/`APPL`; `B3 §22.3`; `B3-D4` **RATIFIED** | `backend/domain/disclosure.py:123-128` |
| `CARBONTALLY_CAPABILITIES` = `SUPPORTED`, `PARTIALLY_SUPPORTED`, `STRUCTURED_INPUT_REQUIRED`, `EXTERNAL_INPUT_REQUIRED`, `MISSING_CAPABILITY`, `FUTURE`, `NOT_APPLICABLE_TO_PRODUCT` | `D12`; `B3 §9` | `backend/domain/disclosure.py:60-68` |
| `REQUIREMENT_CLASSES` = `REQUIRED`, `CONDITIONAL`, `OPTIONAL`, `NOT_APPLICABLE`, `CUSTOMER_INPUT_REQUIRED`, `UNDETERMINED`, `NOT_SUPPORTED`, `FUTURE` | `B1 §9` | `backend/domain/disclosure.py:47-56` |
| `VALUE_STATUSES` = `PENDING`, `RESOLVED`, `UNRESOLVED` — "the ONLY materialisation lifecycle states … Deliberately NOT the requirement/applicability/capability vocabulary" (`PQ-3`) | `PQ-3` **RATIFIED** | `backend/domain/disclosure.py:135-137` |
| `effective_class` — the single **derived** outcome | `PQ-3` — "the **authoritative** home of the derived requirement/applicability/capability outcome" | `disclosure.py:11-12`; `disclosure_projection.py:246-269` |
| `NOT_SUPPORTED` ≠ `CUSTOMER_INPUT_REQUIRED` — never conflated | `DM-5`; `B3-D6` **RATIFIED** | `disclosure_projection.py:14-19, 272-280` |

This is the key architectural finding, and it has four consequences that shape this whole
decision:

1. **Applicability is already modelled as an axis orthogonal to the lifecycle.** `PQ-3`
   explicitly forbids `value_status` from duplicating or reinterpreting
   requirement/applicability/capability. Applicability is an *input* to a derived outcome,
   not a stage in a lifecycle.
2. **"Product capability" and "customer applicability" are already two separate inputs** to
   `derive_effective_class` — precisely the distinction task §14 asks whether CarbonTally
   needs. It needs it, and it already has it (in the disclosure layer).
3. **`NOT_APPLICABLE` vs `NOT_SUPPORTED` are already distinct ratified outcomes** — exactly
   the §8 distinction. See §8.
4. **`UNDETERMINED` is first-class and may never be coerced** to `DOES_NOT_APPLY`
   (`APPL`/`D13`; `disclosure_projection.py:261-262, 300`).

### 4.4 Objective finding 3 — P17 and the disclosure layer were never reconciled

`ARCH-01 §42` draws an explicit boundary and files applicability on the **other** side of it:

> **ACCOUNTING DATA** (P17 core): scope, method, category, activity, quantity, unit, factor,
> factor provenance, snapshot, emissions, evidence, reportability, data quality.
>
> **DISCLOSURE / FRAMEWORK PRESENTATION** (later phase): frameworks, purpose versions,
> requirement versions, mappings, **applicability assessments**, narrative, intensity ratios,
> official identifiers.

and then:

> 4. Framework content (requirement sets, official identifiers, **applicability**) is a
>    **separate later work package**.

`ARCH-01` further records the boundary is already materially present:
`disclosure_applicability_assessments`, `disclosure_values`, `domain/disclosure.py`, etc.

**Therefore (AUTHORITATIVE):** the authoritative architecture places applicability in the
**disclosure layer**, scoped to *reporting requirements*, and declares that work a *later
work package*. Nothing in the authoritative corpus requires a **Scope 3 category**
applicability model. Whether one is required at all is a PO decision (§7.4, §16).

### 4.5 Classification table — every proposition this artifact relies on

| # | Proposition | Class |
|---|---|---|
| P-01 | One Unified CAMS; Staff/Customer/Consultant/Client distinguished by actor + org context + role + capability + delegation, never by separate engines | **AUTHORITATIVE** (D2 §2/§35/§37; D1 §2; AD-P17-01/13) |
| P-02 | Consultant orgs are first-class customers and may hold their own Scope 1/2/3 accounting | **AUTHORITATIVE** (D2 §12/§19) |
| P-03 | Consultant clients are independent organizations, not sub-user-spaces | **AUTHORITATIVE — "HARD PRODUCT DECISION"** (D2 §13) |
| P-04 | Consultant access is delegated, explicit and auditable; it does not transfer ownership | **AUTHORITATIVE** (D2 §14) |
| P-05 | Organization-level accounting capabilities exist, are CarbonTally-controlled, and are not a global flag | **AUTHORITATIVE** (D1 §4/§29; D2 §7/§50; ARCH-01 §38/§39, amendment 4) |
| P-06 | The **exact capability control list** | **EXPLICITLY DEFERRED** — "must be reconciled with the actual P17 architecture and existing authorization system" (D1 §19; D2 §42) |
| P-07 | The **database representation** of capabilities | **EXPLICITLY DEFERRED** — "The exact database representation must be determined during P17 architecture work after inspection of the existing repository/schema" (D1 §4); P17-0 gate item 9; risks R1/R4 (ARCH-02 §656; ARCH-06 §233, §389) |
| P-08 | A **product-level** capability matrix (who may exercise what) | **AUTHORITATIVE**, explicitly "a product-level capability model, not a final database schema" (D2 §34) |
| P-09 | A reusable three-scope governance primitive (`organization`/`consultant_firm`/`consultant_client`) exists | **IMPLEMENTED BUT NOT AUTHORITATIVE** *for capabilities* — `manual_processing_grants`, migration `20260927000000`; independently confirmed ARCH-03 §"A" |
| P-10 | Regulatory *requirement* applicability is a ratified 4-value axis (`APPLIES`/`DOES_NOT_APPLY`/`UNDETERMINED`/`CUSTOMER_INPUT_REQUIRED`) | **AUTHORITATIVE** (D13/APPL; B3 §22.3; B3-D4 RATIFIED) — implemented and independently verified |
| P-11 | CarbonTally product capability for a requirement is a ratified 7-value axis, separate from regulatory applicability | **AUTHORITATIVE** (D12) |
| P-12 | `NOT_SUPPORTED` and `CUSTOMER_INPUT_REQUIRED` must never be conflated | **AUTHORITATIVE — RATIFIED** (DM-5; B3-D6) |
| P-13 | Applicability must not be duplicated into, or reinterpreted by, a lifecycle field | **AUTHORITATIVE — RATIFIED** (`PQ-3`) |
| P-14 | A **Scope 3 category** applicability model (per organization) | **MISSING / PO DECISION REQUIRED** (§4.2–§4.4, §7) |
| P-15 | An organization-facing "category data status" surface (`NO_DATA_YET` etc.) | **MISSING / PO DECISION REQUIRED** (§9, §16) |
| P-16 | Scope 3 category is a property of the activity/result, never of the factor | **AUTHORITATIVE** (AD-P17-02) |
| P-17 | The 15-category taxonomy is controlled reference data **and** "does NOT imply that a category has a supported methodology" | **AUTHORITATIVE** — `20261012000000_p17d_scope3_category_taxonomy.sql:34` (table `COMMENT`) |
| P-18 | Category architecture status ∈ {SUPPORTED, PARTIAL, DEFERRED, NOT_IMPLEMENTED} is the governance vocabulary for maturity, with one definition site | **AUTHORITATIVE** (`p17_scope3_category_matrix...json` → `status_semantics_authority`; ARCH-06 addition) |
| P-19 | Accounting lifecycle `DRAFT→SUBMITTED→VALIDATED→CALCULATED→REVIEW→APPROVED→REPORTABLE` | **AUTHORITATIVE** (D1 §7; D2 §9) |
| P-20 | Estimated vs calculated is a first-class, persisted distinction; an estimated value must carry an estimation record | **AUTHORITATIVE** (P17-PRODUCT-01 §6/§7; `T-INV-12`) — implemented in `20261013000000` |
| P-21 | No silent estimation; no fabricated zero; unresolved must be reported as a percentage | **AUTHORITATIVE** (P17-PRODUCT-01 §29; B3 §17 "never a fabricated zero") |
| P-22 | The 9-value data-quality vocabulary and the §29/§30 reporting buckets | **IMPLEMENTED BUT NOT AUTHORITATIVE as an enumeration** — §7 lists 8 "For example"; the bucket set is the PO's §29/§30 reporting list |
| P-23 | `D1 §19`'s ten controls are illustrative, not the frozen list | **INFERRED** — D1 §19 says "Examples" and then defers the list |

---

## 5. Organization operating model (FROZEN)

### 5.1 The five operating contexts

Per D2 §2/§12/§13 and D1 §2, CarbonTally's organization model has exactly five operating
contexts, and **one** accounting engine serves all of them:

| | Context | Definition | Authority |
|---|---|---|---|
| **A** | CarbonTally Staff/Admin | Internal CarbonTally actor operating the CAMS management plane | D1 §3A/§17; D2 §30 |
| **B** | Direct Customer Organization | A customer organization operating its **own** emissions accounting | D1 §3B/§18; D2 §31 |
| **C** | Consultant Organization | A CarbonTally customer that is *also* a consulting firm with its **own** accounting *and* a client portfolio | D2 §12/§19 |
| **D** | Consultant Client Organization | An **independent** organization whose accounting a consultant is authorized to operate | D2 §13/§33 |
| **E** | Delegated Consultant/User Access | Explicit, per-client, auditable delegated capability set | D2 §14/§18 |

```
                    CARBONTALLY PLATFORM
                             |
               UNIFIED CARBON ACCOUNTING
                  MANAGEMENT SYSTEM
                             |
      +----------------------+----------------------+
      |                      |                      |
CarbonTally            Direct Customer         Consultant
Admin/Staff            Organization            Organization
                                                      |
                                               Client Portfolio
                                                      |
                                        +-------------+-------------+
                                        |             |             |
                                     Client A      Client B      Client C
```
*(structure per D2 §2)*

### 5.2 Confirmation of the task's required PO decisions

Every item required by task §5 is confirmed against source. **No discrepancy was found.**

| # | Required confirmation | Verdict | Source (verbatim where quoted) |
|---|---|---|---|
| 1 | A CarbonTally customer may itself be a consultant organization | **CONFIRMED** | D2 §12 "**APPROVED** A CarbonTally customer may be a consulting organization." |
| 2 | A consultant can have its own carbon accounting | **CONFIRMED** | D2 §19 "**APPROVED** A consultant is also an organization. Therefore it can have its own Scope 1/2/3, evidence, suppliers, calculations, reviews, reports." + "Its own emissions must remain completely separate from client emissions." |
| 3 | A consultant client is an independent organization/tenant | **CONFIRMED** | D2 §13 "**HARD PRODUCT DECISION** A consultant's client must remain an independent organization. Do not model a consultant's client merely as a sub-user-space inside the consultant organization." |
| 4 | Consultant → client is an explicit relationship/delegation | **CONFIRMED** | D2 §13 `consultant_client_relationship(consultant_org_id, client_org_id, status)`; D2 §14 "The consultant receives explicit, auditable delegated access"; "Consultant access to a client organization must be explicitly authorized and auditable." |
| 5 | A consultant does not become the client's organization administrator merely by acting for that client | **CONFIRMED — explicitly prohibited** | D2 §18 "Do not model: `Consultant = Client Admin` as the general rule." + "Consultant access must be configurable per client." |
| 6 | The same CAMS/accounting engine is used by all organizations | **CONFIRMED** | D2 §2/§37 "There is one accounting engine."; D1 §21 "No Parallel Accounting Engines"; AD-P17-01/13; acceptance `AC-CAMS-01` |
| 7 | Consultant switches client context | **CONFIRMED** | D2 §16 "The consultant UX should support selecting a client organization." |
| 8 | Client context must visibly indicate ACTING FOR | **CONFIRMED** | D2 §44 "Acting for: ABC Manufacturing / Operator: Green Advisory / Jane Smith"; D2 §43 "A consultant must never be allowed to unknowingly perform an action against the wrong client." |
| 9 | Data ownership remains with the client organization | **CONFIRMED** | D2 §6 (ownership vs governance); D2 §13 "This preserves: tenant isolation, data ownership, auditability, reporting boundaries, client independence…" |
| 10 | Operator/actor identity remains distinct from data ownership | **CONFIRMED** | D2 §22 "the system must distinguish the organization that owns the data from the person/organization that entered it." |
| 11 | Reports, evidence and calculations belong to the owning organization even when prepared by a consultant | **CONFIRMED** | D2 §24 "The report belongs to ABC's accounting context, not the consultant's organization." (explicitly extended to calculations, evidence, activity data, reporting versions, reportability, audit history); D2 §25 evidence ownership |
| 12 | Audit records who acted, for which organization, and the relevant downstream effect | **CONFIRMED** | D2 §23 "who performed the action / which organization they were acting for / which organization owns the data / what changed / when / why / what accounting result was affected" |
| 13 | Tenant isolation remains mandatory | **CONFIRMED** | D2 §36 "A consultant's ability to operate Client A must not imply access to Client B."; `T-INV-08` four-cell RLS matrix; D2 §39 |

### 5.3 The authorization equation (FROZEN)

D2 §16/§35 fix the authorization model for **every** accounting action, for **every**
organization type:

```
   ACTOR
 + ORGANIZATION CONTEXT
 + ROLE
 + CAPABILITY
 + DELEGATED RELATIONSHIP
 = PERMITTED ACTION
```

with D2 §16 stating "The UI must reflect this, but the backend/API/database must enforce it.
Frontend hiding is not authorization."

**This is the frozen organization operating model for this decision.** No element of it
requires a new entity, and no element of it conflicts with any other authoritative source.

### 5.4 The three operating models are configurations, not products (FROZEN)

D1 §11/D2 §11 define Managed, Collaborative and Self-Service/Advanced operating models and
state: *"These are configurations of one product, not separate systems."* The organization
capability flags (§6) are the mechanism that realises the difference between them.

---

## 6. Capability model

### 6.1 What is authoritative — capability *existence* and the product matrix

**Product decision (AUTHORITATIVE).** Customer carbon accounting is a **per-organization
capability**, never a global hard-coded behaviour:

> **D1 §4** "Customer carbon accounting is a **per-organization capability**. It must NOT be
> a global hard-coded behavior."
>
> **D2 §7** "Customer carbon accounting is configurable **per organization**… The architecture
> must support organization-level accounting capabilities/policies… Do not create a duplicate
> policy system if equivalent capability infrastructure already exists."

D1 §29 restates it as the final PO decision: *"Customer capabilities are organization-level
and configurable."*

**The product-level capability matrix (AUTHORITATIVE).** D2 §34 gives the approved conceptual
model of *who may exercise what*. It is explicitly "a product-level capability model, not a
final database schema":

| Capability | Direct Customer | Consultant's Client | Consultant | CarbonTally Staff |
|---|---|---|---|---|
| Own Scope 1 | Yes, configurable | Yes, configurable | Yes | Yes, authorized |
| Own Scope 2 | Yes, configurable | Yes, configurable | Yes | Yes, authorized |
| Own Scope 3 | Yes, configurable | Yes, configurable | Yes | Yes, authorized |
| Upload evidence | Yes | Yes | Yes | Yes |
| Manage accounting data | Configurable | Configurable | Configurable per client | Yes, authorized |
| Supplier data | Yes | Yes | Yes | Yes |
| Review | Configurable | Configurable | Delegated | Yes |
| Reporting | Yes | Yes | On behalf of client | Yes |
| Client portfolio | No | No | Yes | Yes |
| Organization capability management | No | No | Limited/delegated | Yes |
| Global factor governance | No | No | No | Yes |
| Platform-wide governance | No | No | No | Yes |

Two rows are directly load-bearing and are **FROZEN**:

* **"Organization capability management: Direct Customer = No; Consultant's Client = No;
  Consultant = Limited/delegated; CarbonTally Staff = Yes."** — capability *administration* is
  not a customer capability.
* **"Global factor governance: … CarbonTally Staff = Yes" only** — consistent with AGENTS.md
  §15 and D1 §9 (customer permission ≠ accounting authority).

### 6.2 What is explicitly deferred — the control list and the representation

| Deferred item | The exact deferral language | Source |
|---|---|---|
| The **enumeration** of capability controls | "**Examples:** … The final control list must be reconciled with the actual P17 architecture and existing authorization system." | D1 §19 |
| The same enumeration, restated with one addition | "…`Consultant Features ON/OFF` … The exact controls must be reconciled with existing architecture. Do not implement unnecessary duplicated switches." | D2 §42 |
| The **database representation** | "The exact database representation must be determined during P17 architecture work after inspection of the existing repository/schema." | D1 §4 |
| Representation choice | P17-0 gate item 9: "Customer capability/enablement representation decided (extend the existing scope-based governance primitive vs a new policy table) with a written rationale" | ARCH-06 §233 |
| Status of that gate item | ARCH-06 risk **R4** "Capability representation still undecided" (Medium); ARCH-02 R1 "Blocks P17-A if unresolved; a wrong choice creates a duplicate policy system." | ARCH-06 §389; ARCH-02 §656 |

### 6.3 The candidate controls, recorded but NOT frozen

D1 §19 (ten, introduced by "Examples") and D2 §42 (eleven, adding `Consultant Features`):

```
Customer Carbon Accounting        ON/OFF
Scope 1 Customer Entry            ON/OFF
Scope 2 Customer Entry            ON/OFF
Scope 3 Customer Entry            ON/OFF
Customer Evidence Upload          ON/OFF
Customer Supplier Data            ON/OFF
Customer Editing                  ON/OFF
Customer Review                   ON/OFF
Staff Review Required             ON/OFF
Staff Approval Required           ON/OFF
Consultant Features               ON/OFF        <- D2 §42 only
```

**Classification: EXPLICITLY DEFERRED.** These ten/eleven are the PO's illustrative set. This
artifact does **not** freeze them as the contract, because the PO explicitly reserved that
decision. The two lists **differ**, which is itself evidence that the set was never frozen.

### 6.4 The existing primitive (code exists; not authoritative for capabilities)

ARCH-02 §541 recommended, and ARCH-03 independently confirmed, that a reusable three-scope
governance primitive exists:

```sql
manual_processing_grants (
    scope_type CHECK (scope_type IN ('organization','consultant_firm','consultant_client')),
    scope_id, enabled, reason, set_by,
    CONSTRAINT manual_processing_grants_scope_key UNIQUE (scope_type, scope_id)
)
```
`supabase/migrations/20260927000000_p8_fin06_manual_processing_governance.sql:54-67`

ARCH-03 additionally established the constraint that makes the representation a real decision:

* **(A)** the primitive exists and its comment states "no duplicate tenancy concept is invented";
* **(B)** the three-scope pattern *can* carry multi-key capabilities, but only as a **sibling**
  table with `(scope_type, scope_id, capability_key)`, because `manual_processing_grants` is
  single-key with `UNIQUE(scope_type, scope_id)`;
* **(C)** extending `manual_processing_grants` directly would change a **P8-verified** governance
  table's unique key — a semantic change.

**Classification: IMPLEMENTED BUT NOT AUTHORITATIVE for capabilities.** The table is real and
independently verified; using it to carry accounting capabilities is ARCH-02's *recommendation*,
not a ratified decision. **PO DECISION REQUIRED** (§16, PO-2).

### 6.5 Enablement capability vs product capability — two axes, never merged

The task asks whether CarbonTally requires explicit capabilities for carbon accounting, Scope
1/2/3, supplier management, evidence management, manual review, reporting, consultant/client
management, acting-for/delegation, staff administration and factor management. The authoritative
answer has **two layers**:

| Layer | Vocabulary | Status |
|---|---|---|
| **Organization enablement** (what a tenant may *do*) | the D1 §19 / D2 §42 control names + the D2 §34 matrix | Existence **AUTHORITATIVE**; enumeration **EXPLICITLY DEFERRED** |
| **CarbonTally product capability** (whether CarbonTally can *produce* a governed output) | `CARBONTALLY_CAPABILITIES` — 7 ratified values (D12) | **AUTHORITATIVE** and already implemented |

These are **different axes** and must not be merged. The D1 §19 names (`scope3_customer_entry`,
`customer_review`, …) are **enablement** controls; `carbontally_capability` describes whether
CarbonTally *supports producing* a value. Conflating them would reproduce exactly the defect
`PQ-3` forbids. This is the same collapse that §8 and §14 of this artifact forbid one level down.

### 6.6 Capability table (mandated by task §6)

| Capability | Definition | Applicable org type | Who may exercise it | Delegation possible? | Authoritative source | Current implementation status | Implementation required? |
|---|---|---|---|---|---|---|---|
| Carbon accounting (tenant enablement) | May this organization operate emissions accounting at all? | B, C, D | Customer owner/admin; CarbonTally staff | via consultant delegation to D | D1 §4/§29; D2 §7/§34 | **NOT IMPLEMENTED** (no per-org capability surface) | **YES — blocked on PO-2** |
| Scope 1 / 2 / 3 customer entry | May customers contribute their own scope data? | B, C, D | configured per organization | delegated per client (D2 §18) | D1 §19; D2 §42/§34 | **NOT IMPLEMENTED** | **YES — blocked on PO-2** |
| Evidence upload (customer) | May the customer attach its own evidence? | B, C, D | configured | yes | D1 §19; D2 §34 | Feature exists; enablement control **NOT IMPLEMENTED** | **Partial — blocked on PO-2** |
| Supplier data (customer) | May the customer supply supplier information? | B, C, D | configured | yes | D1 §16/§19; D2 §29/§34 | Domain exists (P16/P17); control **NOT IMPLEMENTED** | **Partial — blocked on PO-2** |
| Manual review participation | May the customer participate in review? | B, C, D | configured | per client | D1 §19; D2 §34 | Review workflow exists; control **NOT IMPLEMENTED** | **Partial — blocked on PO-2** |
| Approval | May the customer approve? | B, C, D | configured; D2 §18 "Client retains final approval" | per client | D1 §19; D2 §18/§34 | Lifecycle exists (P16-R5); control **NOT IMPLEMENTED** | **Partial — blocked on PO-2** |
| Reporting | May the organization report? | B, C, D | owner; consultant "on behalf of client" | yes | D2 §24/§34 | Reporting layer partially implemented | **Partial** |
| Consultant / client management | Portfolio, invitation, delegated capabilities, termination | C | consultant org admins | n/a (this *is* delegation) | D2 §17/§43 | §17/§43 typed "Where applicable"; not verified here | **PO-2 dependent** |
| Acting-for / delegation | Explicit per-client delegated capability + attribution | C, D, E | consultant org admins; clients | yes | D2 §14/§16/§18/§23 | Acting-for persistence partially implemented (P17-IMPLEMENT-02/03); P17-0 gate item 11 remains decision-only | **Partially** |
| Staff administration of capabilities | Turn tenant capabilities on/off | A | CarbonTally staff only | no | D1 §19; D2 §34/§42 | **NOT IMPLEMENTED** | **YES — blocked on PO-2** |
| Factor / customer-factor management | Govern factors and customer factors | A (global); customers may create their own | CarbonTally staff (global); customer owner may create/approve own customer factor | customer factors are org-scoped | D2 §34; D1 §9; AGENTS.md §15/§16 | Customer-factor precedence implemented | **No — EXISTS** |

**No capability name above was invented by this task.** Each is either quoted from D1 §19 /
D2 §42 / D2 §34, or is a ratified disclosure axis (`CARBONTALLY_CAPABILITIES`), and the table
states which.

---

## 7. Applicability model

### 7.1 The authoritative applicability model that already exists

Task §7 requires determining whether CarbonTally has an authoritative requirement for an
organization/category applicability model, and demands that seven concepts not be collapsed into
one status. The authoritative corpus answers both — but **not in the layer P17-09/10 looked at**.

**The authoritative applicability model is the Phase 8 disclosure model.** It is ratified
(D13/`APPL`; `B3-D4`), implemented, and independently verified:

| Axis | Ratified vocabulary | Semantics | Authority |
|---|---|---|---|
| **Regulatory applicability** | `APPLIES`, `DOES_NOT_APPLY`, `UNDETERMINED`, `CUSTOMER_INPUT_REQUIRED` | Whether a reporting requirement applies to this organization for this period | D13/`APPL`; `B3 §22.3`; `B3-D4` **RATIFIED** |
| **CarbonTally product capability** | `SUPPORTED`, `PARTIALLY_SUPPORTED`, `STRUCTURED_INPUT_REQUIRED`, `EXTERNAL_INPUT_REQUIRED`, `MISSING_CAPABILITY`, `FUTURE`, `NOT_APPLICABLE_TO_PRODUCT` | Whether CarbonTally can produce the governed value | `D12`; `B3 §9` |
| **Requirement class** | `REQUIRED`, `CONDITIONAL`, `OPTIONAL`, `NOT_APPLICABLE`, `CUSTOMER_INPUT_REQUIRED`, `UNDETERMINED`, `NOT_SUPPORTED`, `FUTURE` | What the source framework says | `B1 §9` |
| **Effective class** (derived, single home) | the derived outcome of the three axes above | `PQ-3`: the "**authoritative** home of the derived requirement/applicability/capability outcome" | `PQ-3` |
| **Value status** (materialisation only) | `PENDING`, `RESOLVED`, `UNRESOLVED` | Deliberately **not** the applicability vocabulary | `PQ-3` |

**Two ratified invariants are decisive and are FROZEN by this decision:**

1. **`PQ-3`** — "`value_status` is a **narrow materialisation lifecycle only** … and MUST NOT
   duplicate or reinterpret `requirement_class` / applicability / `carbontally_capability` /
   `effective_class`."
2. **`APPL`/`D13`** — applicability is **period-dated, version-bound**, and `UNDETERMINED` is
   **first-class**; it "can never be coerced to a value or to not-applicable", and CarbonTally
   "never makes a legal determination" (design §9.4).

`derive_effective_class` implements the precedence literally (applicability → capability →
requirement class), and `decide_projection` returns `UNRESOLVED` with a **distinct reason string**
for each unsupported outcome (`backend/domain/disclosure_projection.py:246-320`).

### 7.2 The seven concepts, and where each is authoritatively homed

Task §7 lists seven concepts that "must not be collapsed into one status merely for
implementation convenience". This artifact maps each to its **authoritative home**:

| | Concept | Authoritative home | Status | Must NOT be merged into |
|---|---|---|---|---|
| **A** | Applicability | `disclosure_applicability_assessments.applicability_status` (`APPLIES`/`DOES_NOT_APPLY`/`UNDETERMINED`/`CUSTOMER_INPUT_REQUIRED`) | **AUTHORITATIVE**, implemented | B, C, D, E, F, G |
| **B** | Data availability | the **absence of a result row**; `data_quality = 'unresolved'`; disclosure `value_status = 'UNRESOLVED'` | **AUTHORITATIVE as a rule** ("no fabricated zero"); **not** an enumeration | A, D |
| **C** | Calculation status | `scope2_method`, `scope3_category`, `calculation_snapshots`, `algorithm_version` + reportability lifecycle | **AUTHORITATIVE**, implemented (P17-A/D; P16-R5) | A, E, F |
| **D** | Estimation | `estimation_records` (method, inputs, assumptions, factor, source, actor, timestamp) + `data_quality.is_estimated` | **AUTHORITATIVE**, implemented (P17-H; `T-INV-12`) | A, E |
| **E** | Review status | the review / manual-review path + reportability lifecycle | **AUTHORITATIVE** (D1 §7; D2 §9; P17-PRODUCT-01 §26) | A, F |
| **F** | Reportability | reportability lifecycle (`20261008000000_p16r5_result_reportability_lifecycle.sql`); disclosure immutability `D15` | **AUTHORITATIVE** | A, C |
| **G** | Methodology maturity | category `architecture_status` for the **product**; `methodology`/`scope3_method` for a **result** | **AUTHORITATIVE**, two distinct homes (see §14) | A, B, C |

**FROZEN.** The seven concepts are seven axes. A single field cannot represent them. Any future
implementation that collapses them is prohibited by this decision and by `PQ-3`.

### 7.3 Per-category applicability decision table (Scope 3 categories 1–15)

Task §7 asks, for each category, whether the product contract explicitly requires a state such as
applicable / not applicable / no data / excluded / estimated / under review / calculated. The
answer is **no for all fifteen**, and the evidence is uniform.

| Cat | Category | Authoritative per-organization *applicability* state required? | Authoritative `no data` distinct state required? | Status that IS authoritative | Architecture status (maturity — **unchanged**) |
|---|---|---|---|---|---|
| 1 | Purchased Goods and Services | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | category + methodology + quality + estimation + reportability | `PARTIAL` |
| 2 | Capital Goods | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ `capitalisation_declared` gate) | `NOT_IMPLEMENTED` |
| 3 | Fuel- and Energy-Related Activities | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ DC-02 derivation) | `SUPPORTED` |
| 4 | Upstream Transportation & Distribution | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ `transport_boundary='upstream'`) | `SUPPORTED` |
| 5 | Waste Generated in Operations | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ `waste_origin='operations'`) | `SUPPORTED` |
| 6 | Business Travel | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ `trip_purpose`) | `SUPPORTED` |
| 7 | Employee Commuting | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ estimation basis) | `PARTIAL` |
| 8 | Upstream Leased Assets | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ `consolidation_approach`) | `PARTIAL` |
| 9 | Downstream Transportation & Distribution | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ `transport_boundary='downstream'`) | `PARTIAL` |
| 10 | Processing of Sold Products | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ estimation basis) | `NOT_IMPLEMENTED` |
| 11 | Use of Sold Products | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ `use_phase_assumption`) | `DEFERRED` |
| 12 | End-of-Life Treatment of Sold Products | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ `waste_origin='sold_product_eol'`) | `PARTIAL` |
| 13 | Downstream Leased Assets | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ `consolidation_approach`) | `PARTIAL` |
| 14 | Franchises | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ `allocation_basis`) | `DEFERRED` |
| 15 | Investments | **NO — PO DECISION REQUIRED** | **NO — PO DECISION REQUIRED** | as above (+ `attribution_basis`) | `DEFERRED` |

**Result: 15 × 2 = 30 cells, all `NO — PO DECISION REQUIRED`.** This is a *uniform* negative
result, not a partial one, and it is the strongest available evidence that no applicability model
was ever specified for Scope 3 categories. Reproducible:

* `grep -c -i 'applicab' P17-PRODUCT-01` → **`0`**
* `grep -o -i 'applicab[a-z]*' artifacts/p17_scope3_category_matrix_20250925.json` → 4 colloquial
* the category-matrix key set contains **no** applicability field (keys:
  `accepted_activity_types`, `architecture_status`, `business_meaning`, `category`,
  `e2e_acceptance_scenario`, `evidence_requirements`, `existing_factor_families`,
  `expected_output`, `factor_requirements`, `factor_year_requirements`, `geography_requirements`,
  `manual_review_triggers`, `methodologies`, `minimum_input_data`, `name`, `prerequisite_work`,
  `reporting_dimensions`, `slug`, `supplier_requirements`, `tenant_security_considerations`)

**Note on column 5.** The `architecture_status` values are **carried forward unchanged** from
`p17_scope3_category_matrix_20250925.json` and its `status_semantics_authority`, as task §13
requires. This artifact neither upgraded nor downgraded a single category.

### 7.4 The unresolved question (PO-3)

Because 30 of 30 cells are unestablished, the honest freeze here is a **decision boundary**, not a
vocabulary:

> **FROZEN:** CarbonTally's authoritative applicability model is the ratified, implemented Phase 8
> disclosure applicability axis (`APPLIES` / `DOES_NOT_APPLY` / `UNDETERMINED` /
> `CUSTOMER_INPUT_REQUIRED`), scoped to *reporting requirements*, and it is an axis orthogonal to
> the accounting lifecycle (`PQ-3`).
>
> **NOT FROZEN — PO DECISION REQUIRED (PO-3):** whether a **Scope 3 category** applicability
> concept is required at all, and if so (a) which layer owns it, (b) its vocabulary, (c) whether
> it is period-dated and version-bound like the disclosure axis, and (d) whether it is a
> *subset-selection* mechanism ("this organization's reporting boundary includes categories
> {3,4,5,6,…}") or a *per-category state enum*.

**Architectural seam that already exists (INFERRED — offered for the PO decision only).** The
disclosure layer already contains a ratified precedent for "an organization's ordered subset":
`disclosure_purpose_requirements` represents a purpose projection as an **ordered subset** with
`display_order` and `required_for_finalisation`, and is explicitly *not* a second report engine
(`B3 §10`). A category-applicability model expressed as **subset membership** would be consistent
with that precedent and would avoid introducing the six-value enum entirely. This is recorded as
an **option**, not a requirement.

---

## 8. `NOT_APPLICABLE` vs `NOT_IMPLEMENTED` (mandatory distinction)

Task §8 requires this distinction to be documented and treated as mandatory, and forbids treating
the two as equivalent.

### 8.1 Verdict: the distinction is AUTHORITATIVE — and already structurally encoded

**`NOT_APPLICABLE` and `NOT_IMPLEMENTED` are not two words for the same outcome. In CarbonTally's
ratified architecture they arise from two *different axes* and produce two *different*,
non-conflatable outcomes.** This is not this artifact's proposal; it is `DM-5`/`B3-D6`, which is
**RATIFIED**.

| Concept | Axis | Ratified value | Ratified reason string | Meaning |
|---|---|---|---|---|
| **`NOT_APPLICABLE`** | applicability | `applicability_status = 'DOES_NOT_APPLY'` → `effective_class = 'NOT_APPLICABLE'` | `"not applicable for this reporting period and organisation"` | The organization's boundary/business/activity **does not require** this item |
| **`NOT_IMPLEMENTED`** (CarbonTally side) | product capability | `carbontally_capability ∈ {MISSING_CAPABILITY, NOT_APPLICABLE_TO_PRODUCT}` → `effective_class = 'NOT_SUPPORTED'` | `"not supported by CarbonTally"` | CarbonTally **has not implemented** the capability/methodology |
| **`FUTURE`** | product capability | `carbontally_capability = 'FUTURE'` → `effective_class = 'FUTURE'` | `"scheduled for a future CarbonTally capability"` | Deliberately deferred product work |
| `CUSTOMER_INPUT_REQUIRED` | applicability | `applicability_status = 'CUSTOMER_INPUT_REQUIRED'` | `"customer input required"` | Needs the customer, not CarbonTally |
| `UNDETERMINED` | applicability | `applicability_status = 'UNDETERMINED'` | `"applicability undetermined - insufficient information"` | Honestly unknown |

The precedence is implemented literally in `derive_effective_class`
(`backend/domain/disclosure_projection.py:246-269`), and the distinct reason strings come from
`_reason_for_effective_class` (`:272-280`). `decide_projection` then returns
`value_status = 'UNRESOLVED'` with that reason — **never a fabricated zero** (`:300-307`).

**`DM-5`/`B3-D6` (RATIFIED) states the rule directly:** `NOT_SUPPORTED` (CarbonTally cannot produce
it) and `CUSTOMER_INPUT_REQUIRED` (the customer must supply it) "are **never conflated**" — they
produce different reasons.

### 8.2 The same distinction is separately ratified at the taxonomy level

The Scope 3 category taxonomy migration carries an authoritative statement of the identical
principle one level down — **category membership does not imply product capability**:

> `20261012000000_p17d_scope3_category_taxonomy.sql:34` —
> "the controlled 15-category GHG Protocol Scope 3 vocabulary behind
> `calculation_snapshots.scope3_category` and the DC-04/DC-05/DC-07 boundary rules.
> **Reference data only - it does NOT imply that a category has a supported methodology.**"

This is decisive for §15: a category existing in the taxonomy is **not** evidence that CarbonTally
supports it, nor that it applies to a given customer.

### 8.3 What is NOT established (PO DECISION REQUIRED)

| Question | Status |
|---|---|
| May an **organization-facing** surface ever display the CarbonTally-side state (`NOT_SUPPORTED`/`NOT_IMPLEMENTED`) as if it were the customer's own state? | **NO — prohibited.** `DM-5`/`B3-D6` forbid conflating the axes, and P17-IMPLEMENT-09 §24 item 7 records that "`NOT_IMPLEMENTED` never appears as an organization-facing state" is **not yet satisfied** |
| Is there an **accounting-layer** (not disclosure-layer) representation of `NOT_APPLICABLE` / `NOT_IMPLEMENTED` for a Scope 3 category? | **MISSING / PO DECISION REQUIRED** (PO-3, PO-4) |
| Does the product require an organization to be able to *declare* a category out of boundary? | **MISSING / PO DECISION REQUIRED** — the substance of PO-3 |

**FROZEN:** any future implementation must keep these two axes separate. An implementation that
renders "CarbonTally has not yet built Category 2" as "Category 2 is not applicable to you" is
prohibited by this decision. `P17-IMPLEMENT-09 §24.7` already identified exactly this hazard.

---

## 9. `NO DATA` vs `ZERO EMISSIONS`

### 9.1 Verdict: the *rule* is authoritative; the *vocabulary* is not

| Aspect | Status |
|---|---|
| **Never fabricate a zero when data is absent** | **AUTHORITATIVE** — `B3 §17` acceptance criterion "never a fabricated zero"; `decide_projection` returns `numeric_value=None` + `UNRESOLVED` (§8.1) |
| **Never silently convert missing activity data into invented activity data** | **AUTHORITATIVE** — P17-PRODUCT-01 §6 "Never silently convert missing activity data into invented activity data."; `T-INV-12` no-silent-estimation |
| **An unresolved outcome must be reported as a percentage** | **AUTHORITATIVE** — P17-PRODUCT-01 §29 requires reporting to expose "Estimated %", "Manual-review %", "Unresolved %" |
| **An explicit "no data yet" state distinct from zero** | **MISSING / PO DECISION REQUIRED** (PO-5) — `NO_DATA_YET` appears nowhere in any ratified source (§4.2) |
| **An explicit "excluded activity" state** | **MISSING / PO DECISION REQUIRED** (PO-5) |

### 9.2 What the implementation actually does today

| Layer | Behaviour | Evidence |
|---|---|---|
| Disclosure projection | absent data → `UNRESOLVED` + reason; **no numeric value is written** | `disclosure_projection.py:300-320` |
| Data quality | `DataQuality.UNRESOLVED` = "could not be determined and is carried as unknown" | `backend/domain/data_quality.py:20-46` |
| Reporting projection | `reporting_bucket` / `quality_mix` expose `UNRESOLVED` and `UNCLASSIFIED` as **separate buckets**, so an unresolved item cannot be silently absorbed into a total | `backend/domain/data_quality.py:151-191` |
| Accounting results | no row = no data; a stored `0` quantity is a measured zero | P17-A/D schema |

**Consequence for Scope 3 investor reporting (AUTHORITATIVE).** Because §29 requires
`Unresolved %` and because `quality_mix` keeps `UNRESOLVED` distinct, CarbonTally **can already
truthfully** distinguish "we have no data for this category" from "this category's emissions sum
to zero" **at the reporting-projection layer** — provided no surface renders an absent bucket as
`0`, and no surface renders an absent category as `0 tCO₂e`.

**What is missing (PO-5).** There is no ratified **vocabulary** for an organization-facing
"no data yet" or "excluded" statement, and no ratified rule deciding whether an organization may
*distinguish* "we measured zero" from "we have not measured". Until PO-5 is decided, the safe and
truthful behaviour is to render **absence as absence** (no value, with a reason), never as `0`.

---

## 10. `ESTIMATED` vs `CALCULATED`

### 10.1 Verdict: AUTHORITATIVE and already implemented — FROZEN, nothing to add

The product model **does** require an explicit distinction between a measured/calculated result and
an estimated one, and it requires the estimation to be *recorded*, not merely flagged:

| Required distinction | Authoritative source | Implementation |
|---|---|---|
| `estimated` is a data-quality classification | P17-PRODUCT-01 §7 lists `ESTIMATED` | `DataQuality.ESTIMATED` |
| A methodology hierarchy with estimation near the bottom, primary/supplier-specific at the top | P17-PRODUCT-01 §6 (7-step hierarchy) | `methodology` / `scope3_method` on the result |
| "Never silently convert missing activity data into invented activity data" | P17-PRODUCT-01 §6 | `T-INV-12` |
| Manual review is a **feature**, not an error | P17-PRODUCT-01 §26 | review path + `activity_clarifications` |
| Maturity runs from "Calculated" (Level 3) to "Primary data" (Level 7) | P17-PRODUCT-01 §33 (0–7 maturity model) | reporting `methodology` + `data_quality` |
| Estimation record: method, inputs, assumptions, factor, source, actor, timestamp | `T-INV-12` | `estimation_records` (`20261013000000_p17h_estimation_and_assumption_records.sql`) |
| At most one estimation record per calculation snapshot | `T-INV-12` | `uq_estimation_records_snapshot` on `(calculation_snapshot_id)` |

`backend/domain/data_quality.py` additionally encodes a subtle and ratified rule: of the nine
data-quality values, **exactly four are estimates** (`secondary_estimated`,
`spend_based_estimated`, `modelled`, `estimated`), while:

* `activity_based` is deliberately **NOT** an estimate — it is activity data, hierarchy step 4;
* `manual` describes *who* established the value, not that it is estimated;
* `unresolved` is "the explicit admission that no value was established at all".

`is_estimated` is documented as "the single predicate the rest of the system uses".

### 10.2 What this decision does to that implementation: nothing

**`FROZEN — DO NOT REPLACE`.** P17-IMPLEMENT-08/09/10's estimation persistence is **preserved
unchanged** by this decision, as task §10 requires. This task only establishes the contract around
it, and that contract is already satisfied. Two clarifications are frozen for future work:

1. **Estimation is not applicability.** An estimated value can exist only for a category that is
   applicable *and* has a supported methodology; estimation never *creates* applicability.
2. **Estimation is not a lifecycle stage.** `ESTIMATED` is a *quality* attribute of a result that
   has already passed through `CALCULATED`. §11 forbids promoting it into a lifecycle state.

---

## 11. Relationship to the accounting lifecycle

### 11.1 The lifecycle (FROZEN, unchanged)

```
DRAFT → SUBMITTED → VALIDATED → CALCULATED → REVIEW → APPROVED → REPORTABLE
```
D1 §7: *"Customer-entered data must use the controlled accounting lifecycle… Where applicable,
rejection, correction, invalidation, and supersession paths must exist. Customer submission must
never silently bypass required accounting controls."* D2 §9 restates it. The result-level
reportability lifecycle is implemented in
`supabase/migrations/20261008000000_p16r5_result_reportability_lifecycle.sql` and protected by
`T-INV-06` (a non-reportable or superseded result is absent from every reportable aggregate while
remaining readable by id).

### 11.2 Applicability must NOT become a replacement lifecycle (FROZEN)

Task §11 forbids inventing a lifecycle such as
`NO_DATA_YET → CALCULATED → ESTIMATED → REPORTABLE` unless the authoritative documents explicitly
require it. **They do not.** The ratified architecture instead supplies a *model* for how
applicability relates to a lifecycle — and it is the opposite of a replacement:

> **`PQ-3` (RATIFIED):** applicability/capability is one axis; the materialisation lifecycle
> (`PENDING`/`RESOLVED`/`UNRESOLVED`) is a *different*, deliberately narrow axis, and the latter
> "MUST NOT duplicate or reinterpret" the former.

So the authoritative relationship is **orthogonal axes + a gate**, not a merged state machine:

```
   ACCOUNTING LIFECYCLE (per activity)        APPLICABILITY / CAPABILITY AXES
   DRAFT → … → CALCULATED → REVIEW                        |
      → APPROVED → REPORTABLE                            |  applicability_status
                                                          |  carbontally_capability
                                                          |  requirement_class
                                                          v
                                            effective_class  (derived, PQ-3)
                                                          |
                                                          v
                                          FINALISATION GATE  (DM-5, ratified)
```

### 11.3 How applicability legitimately influences reportability (AUTHORITATIVE)

The ratified `DM-5` finalisation gate is the *only* sanctioned join between the two:

| `effective_class` | Gate behaviour (ratified) |
|---|---|
| unresolved `REQUIRED` | **BLOCKS** finalisation |
| unresolved `CUSTOMER_INPUT_REQUIRED` | **BLOCKS** finalisation |
| applicable `NOT_SUPPORTED` | **SURFACED** — never blocking-hidden, never presented as satisfied |
| `NOT_APPLICABLE` | **informational** |
| `UNDETERMINED` | **informational** (and can never be coerced, §7.1) |

Source: `docs/cline/reports/CT-P8-B4-IMPLEMENTATION-20260913-035.md:34`.

### 11.4 The maturity model is a description, not a state machine (FROZEN)

P17-PRODUCT-01 §33 defines Levels 0–7 (Document captured → Extracted → Classified → Calculated →
Provenanced → Reviewed → Reportable → Primary data) and states its purpose: *"This gives investors
and internal teams a truthful understanding of maturity."* It is a **descriptive explanatory
model**.

**FROZEN.** It must not be persisted as a lifecycle status column, and it must not be confused with
either the accounting lifecycle (§11.1) or the governance maturity vocabulary (§13.2). Three
different things; three different homes.

---

## 12. Scope 2 contract

### 12.1 Confirmation of the authoritative Scope 2 contract

| Scope 2 element | Verdict | Authority / evidence |
|---|---|---|
| Purchased **electricity** | **AUTHORITATIVE** | P17-PRODUCT-01 §8; D1 §14; D2 §27 |
| Purchased **heat** | **AUTHORITATIVE** | as above |
| Purchased **steam** | **AUTHORITATIVE** | as above |
| Purchased **cooling** | **AUTHORITATIVE**, with "where applicable" | D1 §14; D2 §27; ARCH-01 §9/§10 + amendment 9: *"cooling, when requested and unsupported by factors, is a **fail-closed review state**, not a fabricated result"* |
| **Location-based** accounting | **AUTHORITATIVE**, first-class | `domain/disclosure.py` `SCOPE2_METHODS = ("LOCATION_BASED","MARKET_BASED")`; ARCH-01 §9; `T-INV-01`, `T-INV-05` |
| **Market-based** accounting | **AUTHORITATIVE**, first-class | ARCH-01 §10; `T-INV-05` |
| **Contractual instruments** | **AUTHORITATIVE** — a **governed accounting entity**, never a text field | D1 §14 "Do not implement contractual instruments as a superficial text field if the P17 contract requires governed instrument records."; D2 §27; ARCH-01 §11; migration `20261011000000_p17c_contractual_instruments_and_allocations.sql`; acceptance `AC-S2INST-01`; `T-INV-09` |
| **Allocations** | **AUTHORITATIVE** | ARCH-01 §11; `T-INV-09` ("an instrument cannot be claimed by a second organisation and cannot be over-allocated") |
| **Factor governance** | **AUTHORITATIVE** | ARCH-01 §29.1/§29.2 (factor_id, source, year, version, scope, category, unit, geography, methodology); `T-INV-10` ("a factor-year mismatch never silently substitutes a factor from another year"); AGENTS.md §15 |
| **Evidence** | **AUTHORITATIVE** | P17-PRODUCT-01 §8 evidence examples (utility invoice, meter data, supplier statement, energy contract, EAC/REC/REGO-type evidence, contractual instrument, allocation evidence, supplier-specific factor) |
| **Data quality** | **AUTHORITATIVE** | P17-PRODUCT-01 §7; §29; `domain/data_quality.py` |
| **Reportability** | **AUTHORITATIVE** | ARCH-01 §12 (Scope 2 reporting contract); reportability lifecycle (`20261008000000_p16r5`) |

**Capability and applicability semantics for Scope 2:**

1. **Capability applies at scope granularity, not per method.** `scope2_customer_entry` is an
   organization capability (D1 §19; D2 §42). There is **no** authoritative `location_based_customer_entry`
   / `market_based_customer_entry` control. → **FROZEN:** Scope 2 capability is one control.
2. **The method is a reporting dimension, not an applicability axis.** `scope2_method` is persisted on
   the result (P17-A/B; migration `20261010000000`), is protected by `T-INV-01` (a Scope 2 result cannot
   be persisted without it), and `T-INV-05` requires that **both** method results for the same activity
   exist and neither is mutated. **FROZEN:** the two methods are not "applicable / not applicable".
3. **One presentation rule exists and is AUTHORITATIVE:** ARCH-01 §400 —
   *"A report may present either method alone only when the other is explicitly reported as not
   present/not applicable."* This is a **presentation-honesty rule about the presence of the other
   method's value**, and it is *not* the disclosure applicability model and *not* the six-value enum.
   **FROZEN as written; it must not be implemented as a three-state applicability enum.**

### 12.2 Scope-2-specific unresolved decision (PO-6)

| Question | Status |
|---|---|
| Must the product represent a per-organization, period-dated applicability for each Scope 2 **method** (e.g. "this organization has no market-based instruments in FY2026"), beyond the §12.1(3) presence rule? | **MISSING / PO DECISION REQUIRED (PO-6)** — no authoritative source requires it; the §12.1(3) rule covers the honest-presentation need |
| Does Scope 2 need an organization-level "no Scope 2 activity" state distinct from zero? | **MISSING / PO DECISION REQUIRED** — same question as §9 (PO-5), at Scope 2 granularity |

Otherwise, **Scope 2 requires no capability or applicability semantics different from Scope 3.**
Both are "accounting dimensions over the existing pipeline" (AD-P17-01).

---

## 13. Scope 3 contract — the 15-category matrix

### 13.1 Confirmation that the final product contract requires all 15 categories

**AUTHORITATIVE.** P17-PRODUCT-01 §9–§23 define an explicit contract for each of the 15 categories;
§34 lists "all 15 categories represented / at least one truthful calculation/estimation path per
category / category-specific methodology" as **must-have**; §35 requires "all 15 categories" in the
investor demo; D1 §15 and D2 §28 both state the requirement.
`docs/architecture/artifacts/p17_scope3_category_matrix_20250925.json` carries exactly **15**
entries and a `category_count_check`. No category is optional in the product contract.

### 13.2 Status preservation (task §13 — mandatory)

Task §13 requires that existing maturity classifications **not** be rewritten. They are therefore
reproduced **unchanged** from `p17_scope3_category_matrix_20250925.json`:

| Category | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `architecture_status` | PARTIAL | NOT_IMPL | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | PARTIAL | PARTIAL | PARTIAL | NOT_IMPL | DEFERRED | PARTIAL | PARTIAL | DEFERRED | DEFERRED |

**Roll-up (unchanged):** `SUPPORTED (4)` = 3, 4, 5, 6 · `PARTIAL (6)` = 1, 7, 8, 9, 12, 13 ·
`DEFERRED (3)` = 11, 14, 15 · `NOT_IMPLEMENTED (2)` = 2, 10.

`NOT_IMPL` in the roll-up denotes `NOT_IMPLEMENTED`; the full word is used below.

**The status vocabulary has exactly one definition site** — the matrix's
`status_semantics_authority`, added by ARCH-06 to fix a drift risk. Its own rule, quoted:

> "this matrix declares each category's authoritative STATUS in `status_rollup`; it does not declare
> the required acceptance LEVEL for that status … **SUPPORTED** → the full defined acceptance path
> must pass (END-TO-END VERIFIED); **PARTIAL** → only the explicitly bounded in-scope acceptance path
> must pass and what remains outside scope must be named (bounded acceptance, NOT a full E2E claim,
> and NOT upgraded to SUPPORTED); **NOT_IMPLEMENTED** → NO implementation E2E required, the category
> must be explicitly recorded as not implemented with a documented blocked record; **DEFERRED** → NO
> implementation E2E required, the deferral and its dependency must be explicit … **No category status
> was changed by this addition.** `category_statuses_unchanged: true`"

**Note on the passage of implementation work.** P17-IMPLEMENT-07/09/10 have since *implemented*
calculation pathways for all 15 (P17-IMPLEMENT-09 §9 records `Result identity persisted: VERIFIED`
for each). That is a change in **implementation** state, not in the **architecture status**
vocabulary, and P17-IMPLEMENT-09 itself states: *"no architecture status was changed to manufacture
a PASS."* This artifact preserves both records as they are, and flags the distinction in §14.3.

### 13.3 The mandated per-category matrix

Legend: **Cap** = required capability · **Meth** = supported methodologies · **Data** = minimum data ·
**Evid** = evidence requirement · **Est** = estimation requirement · **Bound** = boundary control ·
**Maturity** = `architecture_status` (**unchanged**) · **Deferred** = known deferred methodology work ·
**Appl** = authoritative per-organization applicability requirement.

| Cat | Name | Cap | Meth | Data | Evid | Est | Bound | Maturity | Deferred | Appl |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Purchased Goods and Services | category dim. + factor match | `supplier_specific`; `average_data`; `hybrid`; `spend_based` (**explicit only**) | period; product/service; supplier or class; quantity **or** spend; unit | purchase invoice/line (`evidence_line_items`); supplier identity | spend-based is an estimate → `estimation_records` | Cat 1 ↔ Cat 2 (**DC-03**); excludes 2/3/4/5 | **PARTIAL** | supplier PCF/EPD ingestion; hybrid method | **none — PO DECISION REQUIRED** |
| 2 | Capital Goods | category dim. + factor match + `capitalisation_declared` | `supplier_specific`; `average_data`; `spend_based` (explicit); `asset_embodied` (needs dataset) | period; capital good id; supplier; quantity or value; attributed asset/facility | invoice/asset acquisition + embodied disclosure where supplier-specific | none mandated | **DC-03**; never auto-classify an expensive purchase | **NOT_IMPLEMENTED** | fixed-asset-register ingestion; automatic capitalisation boundary | **none — PO DECISION REQUIRED** |
| 3 | Fuel- and Energy-Related Activities | category dim. + source link | `direct_multiply` on a WTT/T&D factor; `derive_from_source_activity` | reference to the Scope 1/2 activity/snapshot; quantity; unit; fuel/energy type; period | **the derivation link itself** (persisted) | not an estimate (derived) | **DC-02** single derivation per source (`uq_calc_snapshots_cat3_source`) | **SUPPORTED** | broader WTT families | **none — PO DECISION REQUIRED** |
| 4 | Upstream Transportation & Distribution | category dim. + boundary property | `distance_based`; `fuel_based`; `supplier_specific` | carrier/supplier; mode; distance or fuel; mass/volume; period; origin; destination | carrier invoice / consignment | none mandated | **DC-04** `transport_boundary='upstream'` | **SUPPORTED** | tonne-km modelling PARTIAL | **none — PO DECISION REQUIRED** |
| 5 | Waste Generated in Operations | category dim. + origin property | `direct_multiply` (material + treatment route) | material; quantity; unit; treatment route; period; provider | waste transfer/service doc; clarification record | none mandated | **DC-05** `waste_origin='operations'` | **SUPPORTED** | per-material route factor families PARTIAL | **none — PO DECISION REQUIRED** |
| 6 | Business Travel | category dim. + `trip_purpose` | `distance_based`; `passenger_km_based`; `spend_based` (**explicit only**) | travel mode; distance or spend; passenger count; period; geography | booking/expense evidence with mode, distance/class, dates | spend-based is an estimate | mode-specific; journey grouping deferred | **SUPPORTED** | journey/grouping layer; spend-based authorisation | **none — PO DECISION REQUIRED** |
| 7 | Employee Commuting | category dim. + estimation basis | `average_data`; `survey_based_estimate` (**explicit only**); `distance_based` | mode; distance; frequency; employee count; period; occupancy | **the estimation record IS the mandatory evidence** | **estimation is the normative path** | commuting scope boundary | **PARTIAL** | CSV/XLSX ingestion; aggregate extrapolation | **none — PO DECISION REQUIRED** |
| 8 | Upstream Leased Assets | category dim. + `consolidation_approach` | `direct_multiply` on asset activity; `asset_energy_based` | leased asset; asset type; lessee relationship; activity/energy; period; consolidation treatment | lease agreement + asset activity evidence | none mandated | **DC-06**/**DC-07** versus Cat 13 | **PARTIAL** | `consolidation_approach` persistence | **none — PO DECISION REQUIRED** |
| 9 | Downstream Transportation & Distribution | category dim. + boundary property | `distance_based`; `fuel_based`; `supplier_specific` | sold product/shipment; carrier; mode; mass/volume; distance; origin; destination; period | outbound consignment/invoice | none mandated | **DC-04** `transport_boundary='downstream'` | **PARTIAL** | tonne-km modelling PARTIAL | **none — PO DECISION REQUIRED** |
| 10 | Processing of Sold Products | category dim. + estimation basis | `supplier_specific` (processor-declared); `average_data` on processing type; `estimated_from_processing_energy` | sold intermediate product; processor; quantity; processing activity; period | processor declaration / processing activity evidence | **estimation is the adopted pathway** | downstream process boundary | **NOT_IMPLEMENTED** | processor-declaration input contract | **none — PO DECISION REQUIRED** |
| 11 | Use of Sold Products | category dim. + `use_phase_assumption` | `lifetime_use_based` (assumption-driven); `supplier_specific` (product-declared) | product type; units sold; expected use profile/lifetime; energy per unit; factor; explicit assumptions | product specification / lifetime assumption record + energy-per-use evidence | **explicit use-phase assumption required** | sold-product boundary | **DEFERRED** | bounded use-phase methodology needs PO authorisation | **none — PO DECISION REQUIRED** |
| 12 | End-of-Life Treatment of Sold Products | category dim. + origin property | `material_composition_based`; `average_data` by product/waste category | sold product; quantity; material composition; treatment route; geography; period | composition + assumed route, both recorded | average-data treatment mix | **DC-05** `waste_origin='sold_product_eol'`; invariant versus Cat 5 | **PARTIAL** | sold-product entity; treatment-mix data | **none — PO DECISION REQUIRED** |
| 13 | Downstream Leased Assets | category dim. + `consolidation_approach` | `direct_multiply` on asset activity; `asset_energy_based` | leased asset; lessee relationship; activity/energy; period; boundary treatment | lease agreement (lessor position) + asset activity | none mandated | **DC-06**/**DC-07** versus Cat 8 | **PARTIAL** | `consolidation_approach` persistence | **none — PO DECISION REQUIRED** |
| 14 | Franchises | category dim. + `allocation_basis` | `franchisee_reported`; `average_data` by franchise type; `estimated_from_floor_area_or_activity` | franchise relationship; location; activity/energy; period; allocation basis | franchise agreement + franchisee activity/energy | **controlled estimation required** | franchise operating boundary | **DEFERRED** | franchise operating model needs PO decision | **none — PO DECISION REQUIRED** |
| 15 | Investments | category dim. + `attribution_basis` | **BOUNDED: `attribution_equity_share` only** | investment entity; type; ownership/exposure share; period; financial and/or investee activity data; attribution method | investment record + investee emissions/activity, or an investee-reported figure with its source | equity-share attribution | investment attribution boundary | **DEFERRED** | PCAF scoring, asset-class treatment, sector attribution — all DEFERRED | **none — PO DECISION REQUIRED** |

**Every `Appl` cell reads "none — PO DECISION REQUIRED".** That is the uniform §7.3 finding, carried
into the matrix rather than hidden.

**Cross-category boundary controls (AUTHORITATIVE, P17-PRODUCT-01 §24).** The product requires a
boundary engine, not a UI warning:

```
Cat 4 ↔ Cat 9 · Cat 5 ↔ Cat 12 · Cat 8 ↔ Cat 13 · Scope 1/2 ↔ Cat 3
Scope 2 ↔ contractual instruments · Cat 1 ↔ Cat 2
```

with `Boundary Check → PASS | CLARIFICATION | BLOCK`. P17-PRODUCT-01 §24: *"This is absolutely
essential."* `DC-09` (instrument over-allocation) is additionally verified implemented
(`p17_instrument_over_allocated()`; `assert_allocation_within_quantity`) per P17-IMPLEMENT-09 §15.

**Structural finding (AUTHORITATIVE, carried forward).** From the category matrix's
`structural_finding`:

> "Every Scope 3 category is separated from its neighbour by a BOUNDARY or ORIGIN property, never by
> the factor family. Categories 4/9 …, 5/12 … and 8/13 … share factor families outright. Therefore
> the canonical category model MUST carry an explicit boundary/origin dimension on the activity, and
> the factor library must never be treated as evidence of category coverage."

This is the authoritative basis for `AD-P17-02` (category is a property of the activity/result, never
of the factor) and, together with `T-INV-11` (no silent reclassification), it is also the reason a
category-applicability model **cannot** be inferred from factor availability.

---

## 14. Product capability vs customer applicability — the four layers

### 14.1 The four layers and their authoritative status

Task §14 requires determining whether CarbonTally must represent four **separate** things, and
whether the authoritative documents define all four. They must be separate; only some are defined.

| Layer | Question it answers | Authoritative home | Status |
|---|---|---|---|
| **L1 — PRODUCT CAPABILITY** | "Does CarbonTally support Category X?" | **Two existing homes**: disclosure `CARBONTALLY_CAPABILITIES` (7 values, D12) for reporting requirements; P17 category `architecture_status` (4 values, `status_semantics_authority`) for accounting categories | **AUTHORITATIVE** — but the two vocabularies are unreconciled (PO-7) |
| **L2 — CUSTOMER APPLICABILITY** | "Does Category X apply to Organization Y?" | disclosure `applicability_status` (4 values) **for reporting requirements only** | **AUTHORITATIVE for disclosure requirements; MISSING for Scope 3 categories → PO-3** |
| **L3 — CUSTOMER DATA STATUS** | "Has Organization Y provided data for Category X?" | **no ratified state**; derivable from persisted facts (`evidence_coverage`, `estimation_records`, `data_quality` buckets, presence of result rows) | **MISSING as a state → PO-5** (the underlying facts are AUTHORITATIVE) |
| **L4 — ACCOUNTING STATUS** | "Is Organization Y's Category X result calculated / reviewed / reportable?" | reportability lifecycle (`T-INV-06`; `20261008000000_p16r5`); disclosure immutability `D15` | **AUTHORITATIVE** |

### 14.2 FROZEN: the four layers must not be collapsed

This is the central product finding of this decision, and it is FROZEN:

> **A category's presence in the taxonomy, CarbonTally's support for it, an organization's
> applicability for it, an organization's data availability for it, and the accounting status of a
> result for it are five different facts. No single field may represent more than one of them.**

Three of the five are already separately ratified (taxonomy ∉ capability per the P17-D `COMMENT`,
§8.2; capability ∉ applicability per `derive_effective_class`; applicability ∉ lifecycle per
`PQ-3`). This artifact extends the same rule to L3.

### 14.3 Three vocabularies that look similar and are not

A future implementer will be tempted to unify these. They are different:

| Vocabulary | Values | Describes | Home |
|---|---|---|---|
| `architecture_status` | SUPPORTED / PARTIAL / DEFERRED / NOT_IMPLEMENTED | **CarbonTally's engineering maturity** for a category | category matrix (governance artifact) |
| `CARBONTALLY_CAPABILITIES` | SUPPORTED / PARTIALLY_SUPPORTED / STRUCTURED_INPUT_REQUIRED / EXTERNAL_INPUT_REQUIRED / MISSING_CAPABILITY / FUTURE / NOT_APPLICABLE_TO_PRODUCT | **CarbonTally's capability to produce a governed output** for a requirement | disclosure layer (`D12`) |
| `applicability_status` | APPLIES / DOES_NOT_APPLY / UNDETERMINED / CUSTOMER_INPUT_REQUIRED | **Whether an item applies to this organization and period** | disclosure layer (`D13`/`APPL`) |

**FROZEN.** `architecture_status` is a *governance* vocabulary about CarbonTally's engineering state.
`applicability_status` is a *customer-and-period* vocabulary. They must never be merged into one
column, and `architecture_status` must never be presented to a customer as their applicability
(§8.3). Note also that `architecture_status` **includes** `NOT_IMPLEMENTED` while the disclosure
capability axis expresses the same idea as `MISSING_CAPABILITY`; this is precisely the vocabulary
drift risk the ARCH-06 `status_semantics_authority` single-definition-site rule was written to
prevent, and it is why PO-7 is raised rather than resolved here.

### 14.4 What this means for implementation sequencing

Because L1 is only partly frozen, L2/L3 are not, and L4 exists:

* **L4 work may proceed** — it is authoritative and implemented.
* **L3 work may proceed to the extent it *exposes* authoritative facts** (evidence coverage,
  estimation records, quality buckets, result presence) **without inventing a state name**.
* **L1/L2 work is blocked** on PO-3, PO-4 and PO-7.

---

## 15. Investor-truth implications

### 15.1 The six prohibited implications

Task §15 forbids the investor experience from implying any of the following. Each is prohibited,
and each prohibition has an authoritative basis:

| Prohibited implication | Authoritative basis for the prohibition |
|---|---|
| Every customer has activity in all 15 categories | P17-PRODUCT-01 §29 requires *category-level transparency* and the identification of partially-covered categories; the taxonomy `COMMENT` says the 15 rows are reference data only |
| `NOT_IMPLEMENTED` means `NOT_APPLICABLE` | `DM-5`/`B3-D6` (§8); P17-IMPLEMENT-09 §24.7 |
| Missing data means zero emissions | `B3 §17` "never a fabricated zero"; P17-PRODUCT-01 §6; `T-INV-12`; §9 |
| An estimated value is measured data | P17-PRODUCT-01 §7 + §6 hierarchy; `T-INV-12`; `data_quality.is_estimated`; §10 |
| A deferred methodology is fully supported | `status_semantics_authority`: `DEFERRED` → "the deferral and its dependency must be explicit" |
| A category is reportable merely because a calculation exists | `T-INV-06`: a non-reportable/superseded result is **absent from every reportable aggregate**; D1 §7 lifecycle |

### 15.2 Investor-truth matrix

| Concept | What can be shown truthfully **today** | What **cannot** yet be shown | Implementation required |
|---|---|---|---|
| Scope totals (1, 2-location, 2-market) | Persisted, reportability-filtered aggregates | — | none (EXISTS) |
| Scope 3 by all 15 categories | per-category totals where reportable results exist (P17-D dimension; §29 reporting model) | that all 15 have data for a given organization | §L2/L3 (PO-3/PO-5) before any per-category "covered / not covered" claim |
| Category methodology | `methodology` / `scope3_method` on the result | per-category *maturity* as a customer fact | L1 reconciliation (PO-7) |
| Data quality mix | §29/§30 buckets via `reporting_bucket` / `quality_mix` (primary / activity / average / spend / estimated / manual review / **unresolved** / unclassified) | — | none (IMPLEMENTED, P17-IMPLEMENT-10) |
| Primary vs secondary | derivable from the quality buckets | — | none (EXISTS) |
| Estimated % / Manual-review % / **Unresolved %** | all three derivable; `UNRESOLVED` is a distinct bucket | — | none (EXISTS) |
| Evidence coverage | `evidence_coverage` / `EVIDENCE_COMPLETENESS` (`COMPLETE`/`PARTIAL`/`UNAVAILABLE`) | — | none (EXISTS) |
| Per-result provenance | report value → snapshot → source activity → evidence → factor (`T-INV-07`) | — | none (EXISTS) |
| Reportability state | reportability lifecycle; non-reportable excluded from aggregates (`T-INV-06`) | — | none (EXISTS) |
| **Category applicability** ("Category X applies to this organization") | **nothing** — no authoritative model exists | the whole concept | **PO-3 decision, then implementation** |
| **"No data yet" vs "zero emissions"** | absence can be shown *as absence* (§9.2) | a named state | **PO-5 decision, then implementation** |
| **"Not applicable" vs "CarbonTally not implemented"** | the *distinction* is ratified and may be explained in narrative | an organization-facing state for the CarbonTally side | **PO-4 decision, then implementation** |
| Complete business-trip journey (Cat 6) | the 7 individually auditable legs | the journey as one grouped entity | journey/grouping layer (DEFERRED, P17-IMPLEMENT-09 §24) |
| Category maturity ("CarbonTally supports Category X") | **internally** (the 4-value `architecture_status`) | to a customer, as their applicability | PO-7 |

### 15.3 The one legitimate way to show maturity honestly today

`P17-PRODUCT-01 §33`'s 0–7 maturity model exists precisely so that *"investors and internal teams"*
can have *"a truthful understanding of maturity"*. Because it is derived from persisted facts
(`methodology`, `data_quality`, evidence presence, review and reportability state), an
**internally-facing** maturity statement per result is honest today. What is **not** honest today is
any **per-organization, per-category** statement of applicability or coverage, because the
organization-level axes (L2/L3) are undecided.

**Recommended truthful posture until PO-3/PO-4/PO-5 are decided:** show what exists, label
estimation as estimation, show `Unresolved %` explicitly, and state that a category with no result
is "no result recorded" rather than `0` or "not applicable".

---

## 16. Explicit unresolved PO decisions

### 16.1 Decisions raised by this artifact

Nine decisions remain. Each is stated as a question with its consequence, so the PO can decide
without further archaeology. **None of them may be resolved by an implementer** (AGENTS.md §62).

| ID | Decision required | Why it is a PO decision | Blocks |
|---|---|---|---|
| **PO-1** | **The organization capability control list.** Which controls exist? D1 §19 lists 10 and says "Examples"; D2 §42 lists 11 (adding `Consultant Features`) and says "reconciled". | The PO explicitly reserved the enumeration twice, and the two lists differ | The capability UI (D2 §42) and any capability-gated behaviour |
| **PO-2** | **The capability storage representation.** Extend the ratified three-scope primitive as a multi-key **sibling** table `(scope_type, scope_id, capability_key)`, or extend `manual_processing_grants` directly, or a new policy table? | D1 §4 defers it; ARCH-02 §656/ARCH-06 §233 make it P17-0 gate item 9; ARCH-03 §"C" notes that extending the existing table changes a **P8-verified** unique key | P17-0 gate item 9; all of PO-1's implementation |
| **PO-3** | **Whether a Scope 3 category applicability model is required at all**, and if so: (a) which layer owns it; (b) its vocabulary; (c) period-dated/version-bound or static; (d) **subset membership** versus a per-category state enum. | 30 of 30 matrix cells are unestablished (§7.3); ARCH-01 §42 files applicability in the disclosure layer as "a separate later work package" | L2 entirely; any per-category applicability surface |
| **PO-4** | **How the CarbonTally product-capability gap is represented to (or hidden from) a customer**, so that "CarbonTally has not built it" is never shown as the customer's "not applicable". | `DM-5`/`B3-D6` fix the *inward* rule; the *outward* representation is not specified, and P17-IMPLEMENT-09 §24.7 records the requirement as unsatisfied | Any customer-facing category listing |
| **PO-5** | **The data-availability vocabulary**: may an organization distinguish "we measured zero" from "we have not measured", and what are the permitted state names (`NO_DATA_YET` / `EXCLUDED_WITH_REASON` are **not** ratified)? | §29 requires an `Unresolved %` but no ratified per-category presence state exists | L3; Scope 3 investor reporting |
| **PO-6** | **Scope 2 method-level applicability** beyond the ARCH-01 §400 presence rule — is a per-method, per-period applicability state required? | No source requires it; inventing it would create a three-state enum from a one-sentence wording | Scope 2 view design |
| **PO-7** | **Reconcile the two product-capability vocabularies**: disclosure `CARBONTALLY_CAPABILITIES` (7 values, `D12`) vs P17 category `architecture_status` (4 values, `status_semantics_authority`), which express overlapping ideas differently (e.g. `MISSING_CAPABILITY` vs `NOT_IMPLEMENTED`). Unify, map, or keep separate with a documented mapping? | Both are AUTHORITATIVE, so neither may be silently changed; only the PO can decide the relationship | L1; §14.3 |
| **PO-8** | **Does `modelled` report as its own data-quality bucket?** (carried forward verbatim from P17-IMPLEMENT-10 §"PO DECISION REQUIRED") | The §29/§30 reporting list does not name `modelled`; P17-IMPLEMENT-10 mapped it into `ESTIMATED` and flagged the choice | Data-quality reporting presentation |
| **PO-9** | **May a per-organization category-coverage surface exist in the investor demo before L2/L3 are decided?** If yes, under what truthful wording? | It is the product-facing consequence of PO-3/PO-5 and is a commercial-presentation decision | Investor-demo scope |

### 16.2 Pre-existing open PO decisions this decision depends on (not raised here)

Recorded for completeness; these were raised by earlier authoritative records and remain open.
They are **not** re-opened by this artifact.

| ID | Open item | Source |
|---|---|---|
| P17-0 gate item 9 | capability/enablement representation | ARCH-06 §233 |
| P17-0 gate item 11 | delegated-user / acting-for **authorization** model (decision only) | ARCH-06 §233 |
| `DM-1`…`DM-7` | requirement naming, purpose↔report_type, reporting-period semantics, benchmarking, `NOT_SUPPORTED`/`CUSTOMER_INPUT_REQUIRED` finalisation policy, evidence drill-down depth, line-item timing | Phase 8 Decision Record |
| `B3-PO-4`, `B3-PO-5`, `B3-PO-7`, `B3-PO-8` | purpose projections; SECR intensity denominator catalogue; drill-down boundary; E1 emission policy while `E1-COV` is CONDITIONAL | `CT-P8-B3-CONTRACT-AND-PO-DECISIONS` / `CT-P8-REST-PLAN` |
| ARCH-01 §"H" | which Scope 2 capabilities are MUST-HAVE | ARCH-01 §1558 |
| R12 | ARCH-06 is self-reported and **not** independently verified — blocking for any authorisation | ARCH-06 §"R12" |

### 16.3 What is *not* an open decision (frozen here)

For absolute clarity, these are **settled by this artifact** and require no further PO input:

1. The organization operating model (§5) — all twelve confirmations hold.
2. The authorization equation (§5.3).
3. The 7-stage accounting lifecycle (§11.1).
4. The 4-axis applicability/capability/requirement/materialisation separation (`PQ-3`) (§7.1).
5. `NOT_APPLICABLE` ≠ `NOT_SUPPORTED` (`DM-5`/`B3-D6`) (§8).
6. Never fabricate a zero (§9).
7. Estimated vs calculated, and the no-silent-estimation rule (§10).
8. The full Scope 2 element contract (§12).
9. All 15 Scope 3 categories are required, with their statuses **unchanged** (§13).
10. The four-layer separation principle (§14.2).
11. The six investor-truth prohibitions (§15.1).

---

## 17. Proposed implementation sequence

Task §16 requires a proposed implementation sequence. The sequence below is ordered so that **no
step depends on an undecided PO item**, and so that each step is independently verifiable.

### 17.1 The critical ordering constraint

Two orderings are forbidden by this decision:

* **Do not implement PO-1's controls before PO-2 decides their representation** — doing so risks a
  duplicate policy system (ARCH-02 §656).
* **Do not implement any category-applicability surface before PO-3** — doing so would invent the
  six-value model that P17-IMPLEMENT-10 correctly refused to invent.

### 17.2 Sequence

| Step | Work | PO dependency | Prerequisite gate | Nature |
|---|---|---|---|---|
| **D0** | **PO resolves PO-1…PO-9.** This artifact is the decision input. | — | — | PO |
| **D1** | **Reconcile the P17 contract with the Phase 8 disclosure model** — write the applicability/capability boundary into `ARCH-01 §42` so applicability is no longer "a later work package" but an explicitly *named* boundary with an owner. Documentation only. | none | D0 or parallel | Docs |
| **D2** | **P17-0 gate item 9** — capability representation decision + written rationale (PO-2). | PO-2 | D0 | Docs |
| **D3** | **P17-0 gate item 11** — delegated-user / acting-for authorization model (decision only). | none | D0 | Docs |
| **D4** | **L4/L3 exposure work (no new vocabulary).** Surface what is already authoritative: per-category totals, `quality_mix` buckets incl. `Unresolved %`, evidence coverage, methodology, reportability state, per-result provenance. This extends the P17-IMPLEMENT-10 §29/§30 projection to a user-visible surface — **no new state names**. | none | none | Impl + UI |
| **D5** | **Capability implementation** (PO-1's controls on PO-2's representation), server-side enforced, with the capability-management UX of D2 §42. | PO-1, PO-2 | D2 | Impl + UI |
| **D6** | **Category applicability implementation** — only after PO-3, and only for the layer PO-3 names. If PO-3 selects subset membership, this is a membership projection, not a status enum. | PO-3 | D1, D0 | Impl + UI |
| **D7** | **Data-availability representation** (L3) per PO-5, with the §9 rule (absence renders as absence) enforced. | PO-5 | D0 | Impl + UI |
| **D8** | **Customer-facing representation of the product-capability gap** per PO-4, satisfying P17-IMPLEMENT-09 §24.7. | PO-4 | D0 | Impl + UI |
| **D9** | **Investor-demo coverage surface** per PO-9, built only from D4/D6/D7 facts. | PO-9 | D4 | UI |

### 17.3 Recommended next implementation task

**Recommended next task: `P17-IMPLEMENT-11 — L4/L3 truth-surface projection (no new vocabulary)`.**

Rationale:

* It is the **only** substantial implementation item with **no PO dependency**.
* It generalises the work P17-IMPLEMENT-10 already landed (`reporting_bucket` / `quality_mix` /
  §29/§30 projection) up to a user-visible surface, so it reuses rather than duplicates.
* It is the precondition for PO-9 (investor demo) and it makes `Unresolved %` and evidence coverage
  visible, which is exactly what §15.3 says can be shown truthfully today.
* It carries a hard constraint that makes it safe: **no new state name may be introduced**; the task
  must report BLOCKED if it needs one.

**Recommended immediately-parallel documentation task:** D1 (reconcile ARCH-01 §42 with the Phase 8
disclosure applicability model). It is pure documentation, but it removes a real contract ambiguity
that has now caused two STOPPED implementation attempts.

---

## 18. Security and tenant implications

### 18.1 What this decision changes about security: nothing

This task is documentation-only and changes **no** RLS policy, grant, route, service or schema.
Every existing security control remains exactly as it was. The content below is therefore a
**constraint on future implementation**, not a report of a change.

### 18.2 Constraints any future capability/applicability implementation must satisfy

| # | Constraint | Basis |
|---|---|---|
| 1 | Every capability check must be enforced **server-side**; "frontend hiding is not authorization" | D2 §16; AGENTS.md §7/§44 |
| 2 | Capability administration is a **staff** capability; Direct Customer = No and Consultant's Client = No | D2 §34 |
| 3 | A capability for organization A must never confer anything on organization B | D2 §36; `T-INV-08` |
| 4 | A consultant's delegated capability must be **per client**; `Consultant = Client Admin` is expressly not the general rule | D2 §18 |
| 5 | Capability/applicability rows must be **organization-scoped under RLS**, following the established convention (member read / org-admin write for org-scoped governance; staff-only on the staff plane) | AGENTS.md §67; existing patterns |
| 6 | If the three-scope governance primitive is extended, its existing **P8-verified** unique key must not be silently changed | ARCH-03 §"C" |
| 7 | Any new table must carry the standard privilege revocations consistent with the established convention | e.g. `20260914000000`, `20260915000000` |
| 8 | Applicability/capability changes are **accounting-governance** events and must be audited with actor + acting-for + owning organization | D2 §23; AGENTS.md §17 |
| 9 | An applicability state must never be used to bypass the accounting lifecycle or the `DM-5` gate | §11; `PQ-3` |
| 10 | Category applicability must never be **inferred** from factor availability, quantity presence or spend presence | `AD-P17-02`; `T-INV-11`; §13.3 `structural_finding` |
| 11 | An organization must never see another organization's applicability, capability or data status | D2 §36; AGENTS.md §45 |
| 12 | `UNDETERMINED` must never be coerced to `DOES_NOT_APPLY`, and CarbonTally must never assert a legal determination | `APPL`/`D13` |

### 18.3 Security negative tests a future implementation must add

Extending the AGENTS.md §45 list, these become mandatory when PO-1/PO-2/PO-3 are implemented:

* Customer A → Customer B capability read/write (**must DENY**)
* Consultant A → Consultant B's client capability read/write (**must DENY**)
* Consultant → a client they are not delegated for (**must DENY**)
* Client user → its own capability **administration** (**must DENY** — D2 §34 row)
* Customer → staff capability administration (**must DENY**)
* Organization member → another organization's applicability assessment (**must DENY**)
* A disabled capability → the corresponding write route (**must DENY server-side**, not merely hide the UI)
* Consultant with `read-only` delegated access on Client C → a write route for Client C (**must DENY** — D2 §18)

---

## 19. Verification performed

### 19.1 Method

Because this is documentation/decision work, task §19 requires four classes of verification: source
existence, requirement provenance, unresolved-decision marking, and non-mutation. Each was executed
and its evidence is recorded below.

### 19.2 Every cited source exists

**41 of 41 cited paths verified present** (`[ -f ]` over the full citation list in §3 plus the
artifacts and migrations cited inline). Result: **0 MISSING**. No citation in this document refers
to a non-existent path.

### 19.3 Every claimed authoritative requirement has a source

The provenance chain was established **before** any decision was written, and every table row in this
document carries an explicit source column or inline citation. The classification table in §4.5
covers every proposition the decision relies on, each tagged AUTHORITATIVE / EXPLICITLY DEFERRED /
IMPLEMENTED BUT NOT AUTHORITATIVE / INFERRED / MISSING.

Independently re-executed (not accepted from P17-IMPLEMENT-10 on trust):

| Check | Command | Result |
|---|---|---|
| P17-PRODUCT-01 contains no applicability model | `grep -c -i 'applicab' "docs/architecture/P17-PRODUCT-01 — …Product Specification.md"` | **`0`** |
| P17-PRODUCT-01 contains no capability model | `grep -c -i 'capab' <same file>` | **`0`** |
| Category matrix has no applicability field | `python3 -c "…list(c.keys())…"` per category | 20 keys, **no applicability key** |
| Category matrix has 15 categories + a count check | JSON `category_count_check` | **15**, unchanged |
| Category statuses unchanged | JSON `status_rollup` + `status_semantics_authority.category_statuses_unchanged` | **`true`** |
| The disclosure vocabularies exist as cited | `backend/domain/disclosure.py:47-56, 60-68, 123-128, 135-137` | present, exact |
| `derive_effective_class` precedence as cited | `backend/domain/disclosure_projection.py:246-269` | present, exact |
| Distinct reason strings as cited | `disclosure_projection.py:272-280` | present, exact |
| `manual_processing_grants` three-scope CHECK + UNIQUE as cited | `20260927000000_…:54-67` | present, exact |
| Category taxonomy `COMMENT` as quoted | `20261012000000_…:34` | present, exact |

### 19.4 Every unresolved decision is explicitly marked

The string `PO DECISION REQUIRED` appears throughout, and §16 lists **PO-1 … PO-9** with the
question, the reason it is a PO decision, and what it blocks. §7.3 marks **30 of 30**
category/applicability cells as unresolved rather than defaulting them. §16.3 separately lists what
*is* settled, so no reader can mistake a freeze for an omission or vice versa.

### 19.5 No proposed state is presented as existing functionality

Every proposed or illustrative element is labelled:

* the six-value applicability vocabulary — labelled **NOT part of the authoritative product
  contract** (§4.2) and **NOT FROZEN / PO DECISION REQUIRED** (§7.4);
* D1 §19 / D2 §42's control lists — labelled **EXPLICITLY DEFERRED** and "recorded but NOT frozen"
  (§6.2, §6.3);
* the subset-membership alternative — labelled **INFERRED … offered for the PO decision only**
  (§7.4);
* the three-scope primitive as a capability store — labelled **IMPLEMENTED BUT NOT AUTHORITATIVE for
  capabilities** and "ARCH-02's recommendation, not a ratified decision" (§6.4).

### 19.6 No implementation, schema or database was changed

| Assertion | Evidence |
|---|---|
| No implementation file changed | no file under `backend/`, `frontend/` or `supabase/` was opened for write; the only write performed was to this document |
| No schema changed | no migration file was created or edited |
| No database written | no database client, migration runner, psql or integration harness was invoked; the agent executed only `git`, `ls`, `grep`, `sed`, `awk`, `wc`, `python3 -c` (JSON **read** only) and file reads |
| `carbontally_test` not modified | not connected to |
| `carbontally_demo_local` not modified | not connected to |
| No integration harness run | the `backend/tests/integration/conftest.py` destructive-`pool` fixture (AGENTS.md §55.1, `F-046-1`) was **not** executed against any target |
| `.gitignore` not modified | pre-existing modification left exactly as found (§2) |
| pre-existing untracked files not touched | 18 → 19, the increment being this document |

### 19.7 Production was not contacted

No production host, URL, API, database or console was contacted. The document is a local repository
artifact only. `production_contacted = false`.

### 19.8 Git verification

```
git rev-parse HEAD                    -> de4b0cac8cc18f8a60436052783b86f53c06c8f9   (baseline, verified)
git status --porcelain | grep -v '^??' -> " M .gitignore" only (pre-existing)
```

**Documentation-only proof (executed after commit 1):**

```
$ git diff --name-only de4b0cac8cc18f8a60436052783b86f53c06c8f9..HEAD
docs/architecture/CT-PO-P17-DECISION-01-CAMS-CAPABILITY-APPLICABILITY-CONTRACT-20250925.md

$ git diff --name-only de4b0cac8cc18f8a60436052783b86f53c06c8f9..HEAD | grep -v '\.md$' | wc -l
0
```

**Result:** exactly **one** file changed across the task's commits, and it is a `.md`. **Zero**
non-documentation files changed. The guarantee in §2 holds.

---

## 20. Final PO decision status

### 20.1 What is now frozen

Eleven items are frozen because a ratified authoritative source supports them (§16.3):

1. The **organization operating model** — five contexts, one engine, all twelve PO confirmations
   verified against source, with no discrepancy found (§5).
2. The **authorization equation** — actor + organization context + role + capability + delegated
   relationship = permitted action (§5.3).
3. The **accounting lifecycle** — `DRAFT → … → REPORTABLE`, unchanged (§11.1).
4. The **four-axis separation** — requirement class, applicability, product capability and the narrow
   materialisation lifecycle are four axes; `value_status` must not reinterpret them (`PQ-3`) (§7.1).
5. **`NOT_APPLICABLE` ≠ `NOT_SUPPORTED`/`NOT_IMPLEMENTED`** — two axes, distinct reason strings, never
   conflated (`DM-5`/`B3-D6`) (§8).
6. **Never fabricate a zero**; absence renders as absence (§9).
7. **Estimated vs calculated** — the estimation-record contract is preserved unchanged and is not to
   be replaced (§10).
8. The **Scope 2 element contract** — electricity, heat, steam, cooling, both methods, governed
   instruments, allocations, factor governance, evidence, quality, reportability (§12).
9. **All 15 Scope 3 categories are required**, with their `architecture_status` values reproduced
   **unchanged** (§13).
10. The **four-layer separation principle** and the prohibition on merging the three similar-looking
    vocabularies (§14).
11. The **six investor-truth prohibitions** (§15.1).

### 20.2 What remains undecided

Nine PO decisions: **PO-1 … PO-9** (§16.1). The most consequential is **PO-3** — whether a Scope 3
category applicability model is required at all. Even this artifact's central positive finding (that
a ratified applicability/capability model already exists) does not dispose of PO-3, because that model
is scoped to **reporting requirements** in the **disclosure** layer, and no authoritative source
extends it to **Scope 3 accounting categories** (§4.4, §7.4).

### 20.3 Ending SHA and commit record

| Order | SHA | Subject |
|---|---|---|
| 1 | `de01cfb790e6604ead14e8c2b893697a9c6ebedc` | `docs(p17): freeze CAMS capability and applicability contract (DECISION-01)` — this document |
| 2 | *(this SHA-record commit — its own SHA cannot appear inside itself)* | `docs(p17): record DECISION-01 commit SHAs` |

* **Baseline:** `de4b0cac8cc18f8a60436052783b86f53c06c8f9`
* **Ending HEAD:** recorded in the companion SHA record (a commit's own SHA cannot appear inside
  itself; same convention as P17-IMPLEMENT-08/09/10)
* **`Pushed: NO`**
* **Documentation-only proof:** `git diff --name-only de4b0cac..HEAD` lists only `.md` files

### 20.4 Final verdict

**`P17_DECISION_PARTIAL`**

Justification, applying the task's own rule — *"Do not claim COMPLETE if authoritative sources remain
insufficient to determine the required product contract"*:

* The artifact **does** freeze a substantial, evidence-backed contract: eleven items, including the
  entire organization operating model, the lifecycle, the Scope 2 contract, the 15-category Scope 3
  contract with statuses preserved, the four-axis separation, and the `NOT_APPLICABLE` vs
  `NOT_IMPLEMENTED` rule. On those, it is **COMPLETE**.
* The artifact **cannot** freeze the objective that gave rise to this task — the organization/category
  applicability model — because the authoritative corpus genuinely does not determine it. All 30
  category/applicability cells are unestablished, and the authoritative architecture files
  applicability in a *different layer*, scoped to *reporting requirements*, as a *later work package*.
* Three further material items (the capability control list, its representation, and the reconciliation
  of two product-capability vocabularies) are **explicitly deferred by the PO himself** in D1 §4/§19
  and D2 §42, and by the P17-0 gate.

`P17_DECISION_COMPLETE` would therefore be a false claim. `P17_DECISION_BLOCKED` would also be wrong:
the task was not blocked — it completed its analysis, produced the frozen artifact, and produced a
precise, implementable decision list. **`PARTIAL` is the accurate verdict:** the authoritative portions
are frozen; the remaining portions are correctly identified as PO decisions and are enumerated with
enough precision to be decided without further archaeology.

### 20.5 What acceptance of this artifact means, and does not mean

Accepting this document means: the frozen items in §20.1 are the product contract, and PO-1…PO-9 are
the outstanding decisions. It does **not** mean that any capability or applicability behaviour exists
— no code, schema, API or UI was changed by this task (§19.6), and no applicability or capability model
is implemented. It also does not clear ARCH-06 risk **R12** (ARCH-06 remains self-reported and not
independently verified), which stays blocking for any authorisation.

---

## Document control

**Task type:** product/architecture decision — documentation only
**Implementation status:** NOT IMPLEMENTED (by design — nothing in this task was to be implemented)
**Schema status:** UNCHANGED
**Database status:** UNTOUCHED
**Production status:** NOT AUTHORIZED / NOT CONTACTED
**Baseline SHA:** `de4b0cac8cc18f8a60436052783b86f53c06c8f9`
**Final verdict:** `P17_DECISION_PARTIAL`
**Recommended next implementation task:** `P17-IMPLEMENT-11 — L4/L3 truth-surface projection (no new vocabulary)`
**Recommended parallel documentation task:** D1 — reconcile `ARCH-01 §42` with the Phase 8 disclosure applicability model
**Pushed:** NO
