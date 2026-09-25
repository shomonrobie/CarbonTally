# CT-PO-P17-DECISION-02 — Reconciliation of CAMS with the Phase 8 Disclosure
# Capability / Applicability Model

**Task ID:** `P17-DECISION-02`
**Title:** Reconcile CAMS (Carbon Accounting Management System) capability/applicability with the
already-ratified Phase 8 Disclosure capability/applicability model
**Date:** 2026-09-25
**Type:** Documentation-only decision / reconciliation artifact
**Verdict:** `P17_DECISION_PARTIAL` (see §20)
**Production contacted:** **NO**
**Pushed:** **NO**

---

## 1. Task identity and authority

### 1.1 What this document is

This is the **single cross-layer reconciliation artifact** for the question:

> *Does P17 (CAMS) need its own capability/applicability model, or does the Phase 8 Disclosure
> model already own that concept — and if it owns it, what exactly does each vocabulary mean?*

It resolves a **cross-layer architectural contradiction** that had stopped two successive
implementation attempts: `ARCH-01 §42` files applicability as *"a separate later work package"*,
while the Phase 8 B1/B3 migrations describe applicability as **already implemented**.

### 1.2 What this document is NOT

| Not | Why |
|---|---|
| A second applicability model | Prohibited. The Phase 8 model is authoritative (§13) |
| A new capability vocabulary | Prohibited. `CARBONTALLY_CAPABILITIES` (D12) is unchanged (§6) |
| A new status vocabulary | Prohibited. No new state names are introduced anywhere in this document |
| An implementation task | No code, schema, RLS, migration, API or UI change is made (§18) |
| A PO policy decision | Business choices are **not** silently decided; they are escalated (§16) |
| A database probe | No database connection was made. Persistent-state claims are cited to the repository record and marked as such (§4.3) |

### 1.3 Authority under which this artifact is issued

- `AGENTS.md §2` — source-of-truth hierarchy (runtime > API contract > Git source > migrations > tests)
- `AGENTS.md §80` — historical findings are regression targets, **not** current defects, until reverified
- `AGENTS.md §62` — PO decision rule: do not silently change business policy
- `CT-PO-P17-DECISION-01` §14.1 — the four-layer capability/applicability decomposition
- `ARCH-01 §42` — the statement this document reconciles

---

## 2. Scope and non-goals

### 2.1 In scope

1. Read the authoritative Phase 8 Disclosure implementation and design.
2. Read the P17/CAMS authored requirement and accounting-layer implementation.
3. Establish **verbatim** semantics for: `REQUIREMENT_CLASSES`, `CARBONTALLY_CAPABILITIES`,
   `APPLICABILITY_STATUSES`, `VALUE_STATUSES`, derived `effective_class`.
4. Answer the **Scope 3 category applicability** question and classify it into one evidence
   outcome.
5. Produce a P17↔Disclosure concept mapping.
6. Revisit PO-1 … PO-9 and record exactly what is now **resolved by evidence** versus what
   **remains open**.
7. Record the layer each concept is **owned** by.
8. Record the truthful investor-demo posture.

### 2.2 Non-goals (explicitly excluded)

- No `backend/` source change.
- No `supabase/migrations/` change.
- No RLS change.
- No API route or schema change.
- No frontend change.
- No data seeding, no requirement-version content.
- No amendment to any pre-existing artifact — recommendations only (§17).

> **Rule applied throughout:** where this document would otherwise have to *invent* a state,
> a boundary or an applicability outcome, it says **PO DECISION REQUIRED** instead (§16).

---

## 3. Baseline and method

### 3.1 Baseline

| Item | Value |
|---|---|
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` (`git rev-parse --abbrev-ref HEAD`) |
| Baseline commit | `55af3a64c0e473d0a6b43601e407bd09e6609418` |
| Baseline verification | `git rev-parse HEAD` matched the task-declared baseline exactly |
| Production contacted | NO |
| Database contacted | NO |
| Migrations applied | NO |
| Files created | 1 (this document) |
| Files modified | 0 |
| Files deleted | 0 |

### 3.2 Method

1. **Recall** — Hindsight context for P17 and Phase 8 (§3.3).
2. **Read the authority first, then the code.** The Phase 8 design and decision records were
   read *before* the implementation, so the implementation was tested against a stated
   contract rather than being used to define one.
3. **Verbatim extraction.** Every vocabulary in this document is transcribed from source with
   its line-level origin recorded. No value is paraphrased.
4. **Coverage check by grep, not by impression.** Claims of the form *"no X exists"* are backed by
   a repository-wide count (§4.3).
5. **Classification, not convenience.** The Scope 3 question was classified into an
   evidence outcome (§11) *before* deciding what should be done about it.

### 3.3 Hindsight recall outcome

Recall returned the Phase 8 B-series ratification history (B1 foundation, B2, B3, B4) and the
P17 A→I accounting series. It did **not** contain a ruling on P17/CAMS applicability ownership.
This document is therefore the first durable statement of that ruling and should be retained
(§20.4).

---

## 4. Source evidence inventory

### 4.1 Authoritative sources actually read for this decision

| # | Source | Layer | Role in this decision | Tracking |
|---|---|---|---|---|
| S1 | `backend/domain/disclosure.py` | Disclosure domain | **PRIMARY authority** for every vocabulary | tracked |
| S2 | `backend/domain/disclosure_projection.py` | Disclosure domain | **PRIMARY authority** for `effective_class` derivation | tracked |
| S3 | `supabase/migrations/20260914000000_p8_b1_disclosure_model_foundation.sql` | Disclosure schema | Persisted contract, CHECK constraints, table comments | tracked |
| S4 | `supabase/migrations/20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` | Disclosure schema | Grants on the applicability table | tracked |
| S5 | `backend/api/v3_disclosure.py` | Disclosure API | Exposure + authorization of applicability | tracked |
| S6 | `backend/data/disclosure.py`, `backend/data/disclosure_projection.py` | Disclosure data | Only consumers of `disclosure_applicability_assessments` | tracked |
| S7 | `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md` | Design | D12/D13/APPL/PQ-3 authored semantics | tracked |
| S8 | `docs/architecture/CARBONTALLY_PHASE8_B3_PO_DECISION_RECORD_20260914.md` | Decision | B3-D4 applicability ratification | tracked |
| S9 | `docs/architecture/CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md` | P17 architecture | §42 — the contradictory statement | tracked |
| S10 | `docs/architecture/CT-PO-P17-DECISION-01-CAMS-CAPABILITY-APPLICABILITY-CONTRACT-20250925.md` | P17 decision | The 4-layer decomposition + PO-1…PO-9 | tracked |
| S11 | `docs/architecture/CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` | P17 decision | §7 / §34 / §42 enablement authority | tracked |
| S12 | `docs/architecture/CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` | PO decision | §4 / §7 / §19 enablement + lifecycle authority | tracked |
| S13 | `docs/architecture/CT-PO-P17-ARCH-06-RECONCILIATION-20250925.md` | P17 reconciliation | R4/R10 runtime-state record | tracked |
| S14 | `backend/domain/data_quality.py` | Accounting domain | Reporting buckets + estimation predicate | tracked |
| S15 | `supabase/migrations/20261008000000_p16r5_result_reportability_lifecycle.sql` | Accounting schema | The **accounting** reportability lifecycle | tracked |
| S16 | `supabase/migrations/20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` | Accounting schema | P17-A dimensions; only P17 migration naming disclosure | tracked |
| S17 | `docs/architecture/artifacts/p17_scope3_category_matrix_20250925.json` | P17 artifact | 15-category matrix + `structural_finding` | tracked |
| S18 | `docs/architecture/P17-PRODUCT-01 — Complete Scope 2 + Scope 3 Processing & Evidence Product Specification.md` | PO product spec | §6/§7/§24/§29/§30/§33 | **untracked** (§4.3) |

### 4.2 Precedence applied

Where a design/decision document and the implementation disagreed, the **implementation and
migration CHECK constraints** won (`AGENTS.md §2`: runtime truth outranks design prose). No such
disagreement was found — the implementation matches the D12/D13/APPL/PQ-3 contract.

### 4.3 Coverage checks (grep-based, reproducible)

These counts make the *"does not exist"* claims in this document falsifiable.

| Claim | Check | Result |
|---|---|---|
| The disclosure applicability model is implemented | `grep -rn 'applicab' supabase/migrations/` | Positive in the two `p8_b1_*` migrations only |
| **P17 carries no applicability concept** | `grep -rn 'applicab' supabase/migrations/` | **Zero** occurrences in any P17 migration |
| P17 accounting migrations are decoupled from disclosure | `grep -c 'disclosure' supabase/migrations/*p17*` | Only `20261010000000_p17a_*` = **2**, both *comments* citing disclosure **vocabulary** |
| **No frontend consumes applicability** | `grep -rn 'applicability' frontend/src/` | **Zero** matches |
| Applicability is consumed only by the disclosure layer | `grep -rln 'disclosure_applicability_assessments'` over `frontend/src backend/services backend/data` | `backend/data/disclosure.py`, `backend/data/disclosure_projection.py` only |

**Consequence of the last two rows:** the disclosure applicability model currently has **no user
surface at all**. It is a server-side contract with an API and no consumer. Recorded as finding
C-8 (§19), not as a defect to be fixed here.

> **Evidence-limitation disclosure (`AGENTS.md §80`).** Two facts used in §15 come from the
> repository's **own** prior reconciliation record (`ARCH-06 R10`) rather than an independent live
> query by this task, because §2.2 forbids database access:
> `disclosure_values` = **0 rows**, `report_version_artifacts` = **0 rows**.
> They are cited as **documented-historical**, not as re-verified live state.

---

## 5. `REQUIREMENT_CLASSES` — semantics and authority

### 5.1 Verbatim definition

`backend/domain/disclosure.py:47-56`:

```python
REQUIREMENT_CLASSES: tuple[str, ...] = (
    "REQUIRED",
    "CONDITIONAL",
    "OPTIONAL",
    "NOT_APPLICABLE",
    "CUSTOMER_INPUT_REQUIRED",
    "UNDETERMINED",
    "NOT_SUPPORTED",
    "FUTURE",
)
```

**Eight values. Unchanged by this decision.**

### 5.2 What the vocabulary *is*

`REQUIREMENT_CLASSES` is the classification of a **reporting requirement version**. It answers:

> *"What does the framework text say about this requirement?"*

It is a property of `disclosure_requirement_versions` — a row in a **global, non-organisation-scoped
catalogue**. There is no `organization_id` on that table.

### 5.3 What the vocabulary is *not*

| Mistaken reading | Correct reading | Discriminating evidence |
|---|---|---|
| "Does this apply to our customer?" | **No** — that is `APPLICABILITY_STATUSES` (§12) | Separate columns on separate tables; §9 derivation reads **both** |
| "Is this an accounting obligation?" | **No** — framework/disclosure scoped | Zero occurrences on any P17 table (§4.3) |
| "A customer obligation list" | **No** — global catalogue, no organisation column | `disclosure_requirement_versions` schema |
| "Six states" | **Eight** | §5.1 |

### 5.4 Why the same three tokens appear in two vocabularies

`NOT_APPLICABLE`, `CUSTOMER_INPUT_REQUIRED` and `UNDETERMINED` appear in **both**
`REQUIREMENT_CLASSES` and `APPLICABILITY_STATUSES`. This is **deliberate and ratified**, not a
naming accident:

- as a **requirement class**, the token says *"the framework text itself does not impose this /
  requires customer input / is undetermined"* — a statement about the **source document**;
- as an **applicability status**, the token says *"for this organisation and this period,
  whether it applies is not applicable / needs customer input / is undetermined"* — a statement
  about the **organisation**.

The two are then collapsed by `effective_class` (§9), whose job is precisely to resolve them into
one governed outcome. Recorded as residual-risk C-6 (§19) because the collision is a genuine
source of human and implementation error, but **no change is made** — the vocabulary is ratified.

---

## 6. `CARBONTALLY_CAPABILITIES` — semantics and authority

### 6.1 Verbatim definition

`backend/domain/disclosure.py:58-68`:

```python
#: CarbonTally capability — a property of the REQUIREMENT VERSION, distinct from
#: regulatory applicability and from value materialisation (D12).
CARBONTALLY_CAPABILITIES: tuple[str, ...] = (
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "STRUCTURED_INPUT_REQUIRED",
    "EXTERNAL_INPUT_REQUIRED",
    "MISSING_CAPABILITY",
    "FUTURE",
    "NOT_APPLICABLE_TO_PRODUCT",
)
```

**Seven values. Unchanged by this decision.** The docstring is explicit on the axis: *"a property of
the REQUIREMENT VERSION, distinct from regulatory applicability and from value materialisation"*.

### 6.2 The seven sub-questions of §6, answered

| # | Question | Answer | Evidence |
|---|---|---|---|
| 1 | Exact capability list | The **7** values above | §6.1 |
| 2 | Does D12 override PO-1? | **No — they are different axes.** D12 governs `carbontally_capability` (*can the product produce this requirement?*). PO-1 governs the **organisation-level enablement control list** (*is this customer allowed to use this feature?*) | `disclosure.py:58-59`; S10 §7.3; S11 §7/§34/§42 |
| 3 | Do D1 §19 (10 controls) and D2 §42 (11 controls) enumerate the same list? | **No — and neither is an authoritative *enumeration*.** D1 §19 presents them as *"Examples"*; D2 §42 presents a *reconciled* list that adds `Consultant Features`. A superset/example pair is not an enumeration | S12 §19; S11 §42 |
| 4 | Product-level or organisation-level? | `carbontally_capability` is **product-level** (global catalogue, no `organization_id`). Enablement is **organisation-level** | S3 schema; S11 §42 |
| 5 | Persisted? | `carbontally_capability`: **YES** — a persisted, constrained column on the requirement-version catalogue. Organisation enablement: **NO** — no table, no column | §4.3; S11 §42 |
| 6 | Delegated? | Organisation enablement is described as configurable/delegated (D2 §34 matrix). `carbontally_capability` carries **no** delegation concept | S11 §34/§42 |
| 7 | Does either affect **accounting execution**? | **NEITHER.** `carbontally_capability` affects only **disclosure projection** (via `derive_effective_class`). Organisation enablement, if implemented, would gate **who may act** — not whether the accounting engine runs | S2; S10 §14.1 |
| 8 | Disclosure-only? | `carbontally_capability`: **disclosure-only. Confirmed.** It is read by `derive_effective_class`, whose output is consumed only by disclosure projection and the B4 report gate | S2; S4.3 |

### 6.3 The naming collision this section resolves

Two different concepts are both called **"capability"** in the CarbonTally corpus:

| Concept | Scope | Vocabulary | Authority | Status |
|---|---|---|---|---|
| **`carbontally_capability`** | one **requirement version** (global) | 7 values (§6.1) | **D12** | **IMPLEMENTED** |
| **Customer/org enablement capability** | one **organisation** | *undefined list* (D1 §19 examples, D2 §42 reconciled) | D1 §4/§7/§19, D2 §7/§34/§42 | **NOT IMPLEMENTED — PO DECISION REQUIRED (PO-1)** |

**Ruling of this decision:** these must **not** be merged and **not** be renamed casually. They are
orthogonal: one is a *product truth about a requirement*, the other is a *commercial entitlement of
an organisation*. The customer-facing phrase "CarbonTally capability" must always be disambiguated
before use. This is recorded as contradiction C-3 (§19) and is an **implementation-clarity
recommendation** (§17.2), not a PO business decision.

---

## 7. The central question — what `APPLIES` does and does **not** mean

### 7.1 Verbatim definition

`backend/domain/disclosure.py:123-129`:

```python
#: Applicability states (D13/APPL). ``UNDETERMINED`` is first-class.
APPLICABILITY_STATUSES: tuple[str, ...] = (
    "APPLIES",
    "DOES_NOT_APPLY",
    "UNDETERMINED",
    "CUSTOMER_INPUT_REQUIRED",
)
```

### 7.2 The exact proposition `APPLIES` asserts

> **`APPLIES` asserts:** *"this **reporting requirement**, as expressed in this **framework
> version**, applies to **this organisation** for **this reporting period**."*

It is a **four-part proposition** — requirement × framework version × organisation × period. It is
**never** a statement about a Scope 3 category, an activity, a factor, or an emissions result.

### 7.3 The four limbs, with structural evidence

| Limb of `APPLIES` | Structural evidence |
|---|---|
| **A requirement version** | `disclosure_applicability_assessments` is keyed to a `framework_version_id`; the assessed object is the framework version's requirement set |
| **A framework version** | The FK is to `disclosure_framework_versions` (status vocabulary `IN_FORCE` / `ADOPTED_NOT_IN_FORCE` / `SUPERSEDED` / `WITHDRAWN`) — the version is the unit of assessment, not an individual requirement |
| **An organisation** | `organization_id` is on the table; `assert_same_organization` enforces the cross-tenant invariant |
| **A reporting period** | `reporting_period_start` / `reporting_period_end` are persisted, with a period-order CHECK, and a uniqueness constraint over the (org, framework version, period, version) tuple |

### 7.4 The granularity finding — the most consequential result of this task

> **Applicability is assessed at FRAMEWORK-VERSION granularity, not at requirement granularity, and
> therefore certainly not at Scope 3 category granularity.**

This is a **new, implementation-derived** finding. `DECISION-01` established that no *P17*
category-applicability model existed; this task establishes the stronger, more useful fact:
**even the Phase 8 disclosure applicability axis cannot express per-category applicability**, because
its unit of assessment is a whole framework version.

Two mechanisms combine to make this true:

1. **Unit of assessment.** The persisted assessment binds
   `(organization_id, framework_version_id, reporting_period_start, reporting_period_end, version)`.
   There is **no** requirement-level, and no category-level, discriminator.
2. **No populated requirements at all.** `grep` for seeded `disclosure_requirement_versions` rows
   returns **zero**. The applicability model is **schema- and contract-complete but content-empty**.

### 7.5 Consequences

| Consequence | Status |
|---|---|
| `APPLIES` must never be surfaced to a customer as *"Scope 3 Category N applies"* | **PROHIBITED** (see §15) |
| The disclosure applicability axis cannot be reused as a Scope 3 relevance screen | **CONFIRMED** (§11 outcome) |
| A per-category applicability concept, if wanted, requires a **new PO decision** | **PO-3, narrowed — still open** (§16) |
| P17 must **not** build its own applicability model to fill this gap | **PROHIBITED** (§13) |

### 7.6 Latent coupling risk

`backend/api/v3_disclosure.py` also exposes `GET/POST
/api/v3/organizations/{organization_id}/applicability`, guarded by `require_org_member()` plus
`_authorize_read` / `_authorize_write`. Because **no frontend consumes it** (§4.3), no UI currently
misstates a framework-version applicability as a category applicability. That safety is
*incidental*, not enforced — recorded as C-8 (§19).

---

## 8. `VALUE_STATUSES` — semantics and authority

### 8.1 Verbatim definition

`backend/domain/disclosure.py:137-139`:

```python
#: PQ-3 — the ONLY materialisation lifecycle states. Deliberately NOT the
#: requirement/applicability/capability vocabulary.
VALUE_STATUSES: tuple[str, ...] = ("PENDING", "RESOLVED", "UNRESOLVED")
```

**Three values.** Note the docstring's explicit prohibition: *"Deliberately NOT the
requirement/applicability/capability vocabulary."* PQ-3 forbids reusing those tokens here.

### 8.2 What the vocabulary *is*

`VALUE_STATUSES` is the **materialisation lifecycle of a disclosure value** — a `disclosure_values`
row bound to a report version. It answers:

> *"Has this report slot been filled yet, and if so, did it resolve?"*

`disclosure_values` is documented as a *"Projection of persisted calculations; never
recomputed."* Note `UNRESOLVED` — like `UNDETERMINED` in applicability, the failure-to-resolve state
is **first-class**, never an omission.

### 8.3 What the vocabulary is *not* — three neighbouring lifecycles

This is the second-most consequential disambiguation in this document. CarbonTally has **four**
distinct lifecycle vocabularies that are routinely conflated:

| # | Lifecycle | Where persisted | Vocabulary | Answers |
|---|---|---|---|---|
| L-A | **Disclosure materialisation** | `disclosure_values.value_status` | `PENDING` / `RESOLVED` / `UNRESOLVED` (PQ-3) | Has the report slot been filled? |
| L-B | **Accounting result reportability** | `calculation_snapshots.reportability_status` **and** `emissions_logs.reportability_status` (P16R5) | `reportable` / `not_for_reporting` / `superseded` | May this *emissions result* enter an aggregate? |
| L-C | **Report version** | report version status (`IMMUTABLE_REPORT_VERSION_STATUSES` = `APPROVED`, `FINAL`) | report-version statuses | Has the report been approved/frozen? |
| L-D | **Purpose version** | `disclosure_purpose_versions.status` | `DRAFT` / `ACTIVE` / `SUPERSEDED` (CHECK-constrained) | Is this purpose definition in use? |

**Ruling of this decision:** L-A and L-B must **never** be merged. They answer different questions at
different layers. `AGENTS.md §75`/`§18` require the platform to report *business state*; conflating
"the emissions result is superseded" with "the disclosure slot is unresolved" would misstate both.

### 8.4 Decisive evidence for the separation

- **PQ-3 is a written prohibition** (§8.1 docstring) — the separation is *intentional*, not
  incidental.
- **The projection function cannot emit an accounting state.** `decide_projection` returns only
  `PENDING` / `RESOLVED` / `UNRESOLVED`. It has no code path producing `reportable` or `superseded`.
- **The accounting lifecycle has its own migration and its own reason.** P16R5 was created because
  *"exclusion from reporting was a convention, not a rule"* — a **reportability** problem. It
  deliberately left *"every historical accounting value untouched"* and added additive columns only.
- **`emissions_logs` is the shared consumption boundary.** The P16R5 migration comment states
  `emissions_logs` is *"the row consumed by reporting/**disclosure**"*, and
  `disclosure_value_evidence` links `emissions_log_id`. This is the **one legitimate seam** between
  L-B and L-A: disclosure **reads** reportability-filtered aggregates; it does not restate them.
- **Two structurally independent state machines** — no FK, no shared enum, no shared trigger.

### 8.5 Why this matters for CAMS (the answer to the CAMS question)

The accounting side therefore **already has** an explicit, machine-enforceable life
*and* a machine-enforceable reportability verdict. There is **no gap** for P17 to fill with a
second status vocabulary. Any CAMS "result state" must be expressed as
`reportability_status` (L-B) — and any report-facing state as `value_status` (L-A). This is the
first of the two rulings that make a duplicate CAMS model unnecessary.

---

## 9. `effective_class` — inputs, derivation, output, consumer

### 9.1 Verbatim definition

`backend/domain/disclosure_projection.py:246-269`:

```python
def derive_effective_class(
    *,
    requirement_class: str,
    applicability_status: str,
    carbontally_capability: str,
) -> str:
    """Derive the authoritative ``effective_class`` (PQ-3 home of the outcome).

    Precedence (documented and test-locked): applicability -> capability ->
    requirement class. ``UNDETERMINED`` is never coerced to not-applicable.
    """
    if applicability_status not in APPLICABILITY_STATUSES:
        raise DisclosureViolation(f"B3: unknown applicability status {applicability_status!r}")
    if applicability_status == "DOES_NOT_APPLY":
        return "NOT_APPLICABLE"
    if applicability_status == "UNDETERMINED":
        return "UNDETERMINED"
    if applicability_status == "CUSTOMER_INPUT_REQUIRED":
        return "CUSTOMER_INPUT_REQUIRED"
    if carbontally_capability in UNSUPPORTED_CAPABILITIES:
        return "FUTURE" if carbontally_capability == "FUTURE" else "NOT_SUPPORTED"
    if requirement_class in UNSUPPORTED_REQUIREMENT_CLASSES:
        return requirement_class
    return requirement_class
```

### 9.2 The four required answers

| Question | Answer |
|---|---|
| **Inputs** | Exactly three: `requirement_class` (requirement version, global), `applicability_status` (organisation × framework version × period), `carbontally_capability` (requirement version, global) |
| **Derivation** | A **fixed, documented and test-locked precedence**: *applicability → capability → requirement class*. Applicability is **exhaustive**: when it returns `DOES_NOT_APPLY` / `UNDETERMINED` / `CUSTOMER_INPUT_REQUIRED`, capability and requirement class are **never consulted** |
| **Output** | One string drawn from the `REQUIREMENT_CLASSES` value space, persisted as `disclosure_values.effective_class` (`NOT NULL`) |
| **Consumer** | `decide_projection` → `value_status`; `_reason_for_effective_class` → the human reason; `unmapped_decision` → the no-mapping path; and the B4 frozen-artefact report gate |

### 9.3 The precedence table (derived, complete)

| `applicability_status` | in `UNSUPPORTED_CAPABILITIES`? (`MISSING_CAPABILITY` / `NOT_APPLICABLE_TO_PRODUCT` / `FUTURE`) | `effective_class` |
|---|---|---|
| `DOES_NOT_APPLY` | *not consulted* | `NOT_APPLICABLE` |
| `UNDETERMINED` | *not consulted* | `UNDETERMINED` |
| `CUSTOMER_INPUT_REQUIRED` | *not consulted* | `CUSTOMER_INPUT_REQUIRED` |
| `APPLIES` | yes, `FUTURE` | `FUTURE` |
| `APPLIES` | yes, any other | `NOT_SUPPORTED` |
| `APPLIES` | no | `requirement_class` (verbatim) |

`UNSUPPORTED_CAPABILITIES = ("MISSING_CAPABILITY", "NOT_APPLICABLE_TO_PRODUCT", "FUTURE")`
(`disclosure_projection.py:92-96`);
`UNSUPPORTED_REQUIREMENT_CLASSES = ("NOT_SUPPORTED", "FUTURE")` (`:99`).

### 9.4 Why `effective_class` is the correct — and only — home for the outcome

`effective_class` is the **single point** at which three orthogonal facts resolve into one governed
outcome. It is:

- **disclosure-owned** — defined in `backend/domain/disclosure_projection.py`, persisted on a
  disclosure table;
- **cross-layer-consumed** — the accounting layer's facts (via `CALCULATION_AGGREGATE` /
  `EMISSIONS_LOG_AGGREGATE` source kinds, reportability-filtered per `T-INV-06`) enter through
  `source_kind`, not through a new vocabulary;
- **the reason P17 must not build a parallel mechanism** — a second "CAMS applicable?" flag would
  create a second, divergent resolution of the same three facts.

### 9.5 Implementation observations (recorded, not changed)

| # | Observation | Assessment |
|---|---|---|
| O-1 | Lines 267-269 contain a **redundant branch**: `if requirement_class in UNSUPPORTED_REQUIREMENT_CLASSES: return requirement_class` immediately followed by `return requirement_class`. `UNSUPPORTED_REQUIREMENT_CLASSES` is therefore currently inert | **Harmless.** Behaviour is identical. Likely retained for explicitness/future divergence. **No change made** — no defect, and `AGENTS.md §71` forbids non-required rewrites |
| O-2 | Applicability is **never** downgraded: `UNDETERMINED` is never coerced. The docstring states this and the code honours it | **Correct and important** — this is the mechanism behind §14 |
| O-3 | `validate_applicability_basis` **requires** a non-empty basis and calls `assert_no_legal_determination(basis)` | **Correct** — CarbonTally records facts, not legal advice; the API response also carries `"legal_determination": False` |
| O-4 | `unmapped_decision` returns `UNRESOLVED` with "never a guessed producer and never a zero" | **Correct** — no silent zero can be fabricated at the disclosure boundary |

---

## 10. CAMS ↔ Disclosure concept mapping

### 10.1 The mapping

Legend for **Owner**: `DISC` = disclosure layer · `ACCT` = accounting/P17 layer · `SEAM` = a
legitimate cross-layer read · `BOTH` = the concept exists on both sides.

| # | Concept | P17 / CAMS side (authority) | Disclosure side (authority) | Owner | Relationship |
|---|---|---|---|---|---|
| M-1 | **Reporting requirement** | *Does not exist* (P17 has no requirement catalogue) | `disclosure_requirements` / `_versions` (S3, S7 §7) | **DISC** | Disclosure-only. P17 must never author a requirement |
| M-2 | **Requirement class** | *Does not exist* | `disclosure_requirement_versions.requirement_class` = `REQUIREMENT_CLASSES` (8) (§5) | **DISC** | Disclosure-only |
| M-3 | **Applicability** | *Does not exist* — zero `applicab*` in any P17 migration (§4.3) | `disclosure_applicability_assessments.assessed_status` = `APPLICABILITY_STATUSES` (4) (§7) | **DISC** | **Disclosure-only. This is the reconciliation ruling** |
| M-4 | **Capability (product)** | **No** — P17 carries no capability flag | `disclosure_requirement_versions.carbontally_capability` = `CARBONTALLY_CAPABILITIES` (7) (§6) | **DISC** | Disclosure-only |
| M-5 | **Capability (organisation enablement)** | P17/D1/D2 **require** it, list examples, **do not implement** it | *Does not exist* | **PO DECISION REQUIRED (PO-1)** | Open. Not a disclosure concept |
| M-6 | **Category maturity** | `architecture_status` (4) in the 15-category matrix (S17): `SUPPORTED` / `PARTIAL` / `DEFERRED` / `NOT_IMPLEMENTED` | `carbontally_capability` (7) (§6) | **BOTH, unmapped** | **Two vocabularies for one intuition** → PO-7 (§16) |
| M-7 | **Methodology** | `calculation_snapshots.scope2_method` (`LOCATION_BASED`/`MARKET_BASED`); `scope3_category` / `accounting_method` (P17-A, S16) | `disclosure_values.scope2_method_hint`; `disclosure_requirements.source_selector` (JSONB) | **SEAM** | ARCH-01 §42 rule 3 names `scope2_method_hint` *"the seam"*. **Asymmetric:** Scope 2 method crosses; **Scope 3 category has no disclosure counterpart column** (C-5) |
| M-8 | **Calculation** | `calculation_snapshots` + `emissions_logs` (S15) | *Never calculates* — `disclosure_values` is "a projection of persisted calculations; never recomputed" | **ACCT** | Disclosure **reads**; it must never compute an emissions number |
| M-9 | **Data quality** | `calculation_snapshots.data_quality` via `DataQuality` (9 values) + `is_estimated` (S14) | *No data-quality vocabulary* | **ACCT** | Accounting-only. Disclosure surfaces it only via `FACTOR_PROVENANCE` / `EVIDENCE_COMPLETENESS` source kinds |
| M-10 | **Estimation** | `estimation_records`; `is_estimated` is the single predicate (T-INV-12) | *No estimation concept* | **ACCT** | Accounting-only. `CUSTOMER_INPUT` ≠ estimation and must not be read as such |
| M-11 | **Uncertainty (numeric)** | Deliberately **absent** — "a fabricated precision" (S14) | Deliberately **absent** | **NEITHER (by design)** | Both layers independently refuse to invent a band. **Consistent** |
| M-12 | **Evidence** | `evidence_line_items`; provenance chain `T-INV-07` | `disclosure_value_evidence` (links `calculation_snapshot_id` / `emissions_log_id` / `source_item_id` / `source_file_id`); `EVIDENCE_COMPLETENESS_STATES` = `COMPLETE`/`PARTIAL`/`UNAVAILABLE` | **SEAM** | The **second legitimate seam**: disclosure links to accounting evidence by FK and never re-derives it |
| M-13 | **Reportability** | `reportability_status` ∈ {`reportable`, `not_for_reporting`, `superseded`} on **both** `calculation_snapshots` and `emissions_logs` (P16R5, S15); `T-INV-06` | *No reportability vocabulary* | **ACCT** | Disclosure consumes **reportability-filtered** aggregates. **Disclosure must never restate or override reportability** |
| M-14 | **Lifecycle** | **Two**: result reportability (L-B, 3 values) and report version (L-C, `APPROVED`/`FINAL`) | **Two**: value materialisation (L-A, 3 values) and purpose version (L-D, 3 values) | **SPLIT** | **Four lifecycles, deliberately separate** (§8.3). Never merge L-A and L-B |
| M-15 | **Disclosure value** | *Does not exist* | `disclosure_values` (`value_status`, `effective_class`, `value_kind` ∈ `QUANTITATIVE`/`QUALITATIVE`/`NARRATIVE_BOUND`/`SELECTION`) | **DISC** | Disclosure-only. The **only** place a report figure is stated |
| M-16 | **Data availability / absence** | An activity with no result is simply **absent**; `data_quality = 'unresolved'` records *unknown, not zero* | `value_status = 'UNRESOLVED'` **plus** a distinct `effective_class` reason | **SEAM, unmapped** | **No shared vocabulary.** The nearest honest cross-layer mapping is *absence ↔ UNRESOLVED*, but it is **not ratified** → PO-5 (§16) |
| M-17 | **Consolidation approach** | `CONSOLIDATION_APPROACHES` (3) — P17-A cites the **disclosure** vocabulary (S16 comment) | `disclosure.py` `CONSOLIDATION_APPROACHES` | **DISC-owned, ACCT-consumed** | **A working precedent:** P17-A deliberately cites the frozen disclosure vocabulary instead of minting its own |
| M-18 | **Scope 2 method** | `scope2_method` — P17-A comment: *"frozen B1 disclosure vocabulary"* | `SCOPE2_METHODS` = `LOCATION_BASED`/`MARKET_BASED` | **DISC-owned, ACCT-consumed** | **Second working precedent** (§10.3) |

### 10.2 Gap directions

| Direction | Concepts |
|---|---|
| **Accounting-only** (disclosure has no counterpart) | M-8 Calculation · M-9 Data quality · M-10 Estimation · M-13 Reportability |
| **Disclosure-only** (accounting has no counterpart) | M-1 Requirement · M-2 Requirement class · M-3 Applicability · M-4 Product capability · M-15 Disclosure value |
| **Two vocabularies for one idea (unmapped)** | M-6 Category maturity · M-16 Data availability |
| **Legitimate cross-layer reads** | M-7 Methodology (`scope2_method_hint`) · M-12 Evidence (FK) · M-13 Reportability (filter) |
| **Already-correct reuse precedents** | M-17 Consolidation approach · M-18 Scope 2 method |

### 10.3 The precedent that settles the ARCH-01 §42 question

M-17 and M-18 are **decisive**. On two separate occasions the P17 accounting layer needed a
vocabulary the disclosure layer already owned, and **cited it rather than minting a second one**:

- P17-A, `consolidation_approach`: *"backend/domain/disclosure.py CONSOLIDATION_APPROACHES"*
- P17-A, `scope2_method`: *"frozen B1 disclosure vocabulary"*

Therefore the correct reading of `ARCH-01 §42` is **not** that P17 must build an applicability
model. It is that **the mechanism already exists and P17 must cite it exactly as it already cites
`CONSOLIDATION_APPROACHES`.** §17.1 states the recommended wording amendment.

### 10.4 The reconciliation ruling

> **P17/CAMS must NOT implement its own possibility/applicability model.**
>
> The Phase 8 Disclosure model is the **sole** owner of: reporting requirements, requirement
> classes, applicability, product capability and disclosure values. P17/CAMS owns: activities,
> factors, calculations, data quality, estimation, evidence, reportability and methodology.
> The two layers are joined by **exactly three** ratified seams — `scope2_method_hint` (methodology),
> `disclosure_value_evidence` (evidence FK) and reportability-filtered aggregates — and by the
> **reuse precedents** `CONSOLIDATION_APPROACHES` and `SCOPE2_METHODS`.
>
> Any future P17 requirement that *looks* like applicability must be satisfied by **citing**
> `APPLICABILITY_STATUSES`, never by minting a parallel column, table or enum.

---

## 11. The Scope 3 applicability question — outcome classification

### 11.1 The question as asked

> *"Is Scope 3 <category> applicable?"*

### 11.2 The five possible outcomes (defined before classification)

| Outcome | Meaning | Consequence if selected |
|---|---|---|
| **A** | Applicability ownership is **already fully satisfied** by the Phase 8 model at the granularity asked | No P17 action. Cite and move on |
| **B** | An owner exists, but it **cannot express** the question at the granularity asked — a **structural/granularity gap** | **PO DECISION REQUIRED** before any implementation |
| **C** | An owner exists and **can** express the question, but the content is **not populated** — a **data/enablement gap** | No model change; an enablement task |
| **D** | **No owner exists**; a new model would be required | Would authorise a second model — **rejected by §10.4** |
| **E** | **Cannot be determined** from available evidence | BLOCKED / UNVERIFIED |

### 11.3 The question decomposes — it is not one question

The single sentence *"is Scope 3 <category> applicable?"* conflates **two different propositions**.
They have **different outcomes**.

**Q-11a (the reporting-requirement reading):** *"Does a framework requirement about Scope 3
category N apply to this organisation and period?"*
→ Owned by `disclosure_applicability_assessments` at framework-version granularity.

**Q-11b (the accounting-relevance reading):** *"Is Scope 3 category N material/relevant to this
organisation's inventory?"*
→ **No owner.** GRG/ESRS materiality sits above and beside both the disclosure applicability axis
and the accounting layer.

### 11.4 Classification

| Sub-question | Outcome | Evidence |
|---|---|---|
| **Q-11a** — reporting-requirement applicability | **B, compounded by C** | Outcome **B**: the axis is scoped to a **framework version**, so it **cannot** answer a per-category question (§7.4). Outcome **C** compounds it: **zero** `disclosure_requirement_versions` rows are seeded, so even the framework-version-level answer is unpopulated |
| **Q-11b** — category materiality/relevance | **B** | No owner exists for materiality as a *category-level* determination. **However this is NOT outcome D** — see §11.5 |

### 11.5 Why this is **B**, and why it is **not D**

It is **B**, not **A**, because the framework-version unit of assessment provably cannot answer a
per-category question — this is a **structural** limit, not a missing row.

It is **B**, not **C**, because adding requirement rows would **not** fix it: no amount of seeded
content changes the fact that the discriminator is a framework version.

It is **B**, not **D**, because **a model does exist and must be used** — the correct future
answer is almost certainly to add a *requirement* (a framework requirement genuinely about Scope 3
category N) to the existing catalogue, and let the existing applicability axis assess it. That is
**authoring content into the existing model**, which is the opposite of outcome D. **No second
model is justified by this gap.**

It is **B**, not **E**, because the evidence is conclusive: the migration's keys, constraints and
the derivation function were read directly (§7.3, §9.1).

### 11.6 What the 15-category matrix actually establishes

`p17_scope3_category_matrix_20250925.json` is a **capability/maturity** artifact — is P17 *able* to
process this category, and to what degree? Its descriptor is `architecture_status` ∈
`SUPPORTED` / `PARTIAL` / `DEFERRED` / `NOT_IMPLEMENTED` (M-6). That is a statement about the
**product**, not about the **customer**.

> **Therefore: the 15-category matrix must never be presented as an applicability assessment.**
> It answers *"can CarbonTally do this?"*, never *"does this apply to you?"* This is the
> single most likely future mis-statement and is recorded as C-4 (§19) and PO-7 (§16).

### 11.7 Consequence for P17 implementation

P17 must **not** build a category applicability model to resolve Q-11b. Until PO-3 is decided:

- category applicability is **`UNDETERMINED`** by policy;
- the honest UI statement is *"Category N: CarbonTally processing status = <architecture_status>.
  Applicability to your organisation is not yet determined."*;
- `UNDETERMINED` must **never** be rendered as "not applicable" (§14).

---

## 12. Layer ownership

### 12.1 The ownership matrix

| Concept | Owner layer | Owning artifact | Who may **write** it | Who may **read** it |
|---|---|---|---|---|
| Framework + framework version | **Disclosure** | `disclosure_frameworks`, `disclosure_framework_versions` | Admin / governed seeding (`report:disclosure_framework_seeded`) | Internal + authorised org reads |
| Reporting requirement + version | **Disclosure** | `disclosure_requirements`, `disclosure_requirement_versions` | Governed seeding only (`PQ-6`: **identities only**, no regulatory content authored by CarbonTally) | Internal |
| Requirement class | **Disclosure** | same table | Governed seeding | Internal |
| Product capability | **Disclosure** | same table | Governed seeding | Internal |
| Applicability assessment | **Disclosure** | `disclosure_applicability_assessments` | Authorised org member via API; **audited** (`report:disclosure_applicability_assessed`); **basis required**; **no legal determination** | Org members (RLS-scoped) |
| Disclosure value | **Disclosure** | `disclosure_values` | Projection from persisted calculations; frozen at `APPROVED`/`FINAL` | Report consumers |
| Purpose + purpose version | **Disclosure** | `disclosure_purposes`, `disclosure_purpose_versions` | Governed seeding | Internal |
| Activity data + extraction | **P17 / accounting** | source documents, extraction items | Operators/consultants via workflow | Workflow-scoped |
| Factor + factor provenance | **P17 / accounting** | factor tables, `customer_factors` | Factor governance (P17-A) | Workflow-scoped |
| Calculation | **Accounting** | `calculation_snapshots` | Calculation engine (server-authoritative) | Workflow + disclosure aggregates |
| Emissions log | **Accounting** | `emissions_logs` | Calculation engine | **Disclosure (reportability-filtered)** |
| Data quality | **Accounting** | `calculation_snapshots.data_quality`, `DataQuality` | Calculation engine | Workflow + reporting buckets |
| Estimation | **Accounting** | `estimation_records`, `is_estimated` | Operator/consultant | Workflow |
| Evidence | **Accounting** | `evidence_line_items` | Operator/consultant | Workflow + **disclosure (by FK)** |
| Reportability | **Accounting** | `reportability_status` on snapshots + logs | Invalidation workflow (**reason + actor + timestamp mandatory**) | All reporting/disclosure consumers |
| Methodology (`scope2_method`, `scope3_category`, `accounting_method`) | **Accounting (columns) / Disclosure (vocabularies)** | P17-A columns citing disclosure vocabularies | Workflow / calculation | Workflow + disclosure (`scope2_method_hint`) |
| Category maturity | **P17 documentation artifact** | `p17_scope3_category_matrix_*.json` | P17 authors | Internal only — **never a customer applicability statement** |

### 12.2 The three ratified seams — and no others

| Seam | Direction | Contract |
|---|---|---|
| **S-1 Methodology** | accounting → disclosure | `calculation_snapshots.scope2_method` feeds `disclosure_values.scope2_method_hint`. ARCH-01 §42 rule 3 names this *"the seam"* |
| **S-2 Evidence** | disclosure → accounting | `disclosure_value_evidence` FKs to `calculation_snapshot_id` / `emissions_log_id` / `source_item_id` / `source_file_id`. Disclosure **links**, never re-derives |
| **S-3 Reportability filter** | accounting → disclosure | Disclosure aggregates read only `reportability_status = 'reportable'` rows (`T-INV-06`). Disclosure **never** writes or overrides reportability |

Plus two **vocabulary reuse** couplings (not data seams): `CONSOLIDATION_APPROACHES`, `SCOPE2_METHODS` (§10.3).

**Any new seam requires a PO decision.** Notably, a **Scope 3 category channel** from P17 to
disclosure is **conspicuously absent** — `scope3_category` exists only on the accounting side (C-5).

### 12.3 Ownership rules (normative for P17 implementation)

1. **P17 must not author disclosure vocabulary.** No new `applicability`-like enum, table or column.
2. **P17 must not author requirement content.** Requirement authoring is disclosure-governed.
3. **P17 must not compute a disclosure value.** Calculation is accounting; projection is disclosure.
4. **P17 must not override reportability from a disclosure context.** Reportability is accounting.
5. **Disclosure must not compute emissions.** It reads; it never recalculates.
6. **Category maturity is never applicability.** Three different propositions (M-6, §11.6).
7. **Applicability is organisation×framework-version×period** — never a category, activity or result.

---

## 13. Granularity — where applicability **is** and **is not** assessed

### 13.1 The granularity ladder

| Granularity | Can the Phase 8 applicability axis express it? | Evidence |
|---|---|---|
| **Framework version** | **YES** — this is precisely its unit of assessment | §7.3 |
| **Requirement (individual)** | **NO** — no requirement-level discriminator on the assessment row | §7.3 |
| **Organisation** | YES (one organisation per assessment, RLS-scoped) | §7.3 |
| **Reporting period** | YES (`reporting_period_start` / `_end`, period-order CHECK) | §7.3 |
| **Scope 3 category** | **NO** | §7.4 |
| **Activity / emission source** | **NO** | §7.4 |
| **Emissions result** | **NO** — reportability, not applicability, governs results | §8.3 L-B |
| **Disclosure value / report slot** | **NO** — materialisation, not applicability | §8.3 L-A |

### 13.2 Permissible vs impermissible statements

Before PO-3 is decided, only these phrasings are permitted:

| ✅ Permitted | ❌ Impermissible |
|---|---|
| *"For GHG Protocol Corporate Standard v\<x\>, the framework is assessed as APPLIES for this organisation and period."* | *"Scope 3 Category 1 applies to you."* |
| *"CarbonTally processing status for Category 1: `SUPPORTED`."* | *"Category 1 is applicable."* |
| *"Category 1 applicability to your organisation is **`UNDETERMINED`**."* | *"Category 1 is not applicable."* |
| *"This result is `not_for_reporting` because \<reason\>."* | *"This result is unresolved."* (wrong lifecycle — L-B ≠ L-A) |
| *"This disclosure slot is `UNRESOLVED`: `NOT_SUPPORTED` by CarbonTally."* | *"Not applicable."* (wrong `effective_class`) |

### 13.3 Where a future category question *should* live

If PO-3 is ratified in favour of a per-category applicability concept, the evidence in §11.5 points
to the **existing** mechanism, not a new one:

1. author a **requirement** in `disclosure_requirement_versions` that is genuinely about Scope 3
   category N (governed seeding, `PQ-6` identities/content discipline);
2. let `disclosure_applicability_assessments` assess it for the organisation and period;
3. let `derive_effective_class` resolve it through the **existing** precedence;
4. surface it through `disclosure_values` under the **existing** `value_status` lifecycle.

That path requires **zero new tables, zero new enums, zero new states** — which is the strongest
possible evidence that outcome D is not warranted.

### 13.4 Residual granularity gap (recorded, not resolved)

Even that path does **not** create category-level **materiality** (Q-11b). GRG/ESRS materiality is a
**methodological** determination with an organisation-specific judgement component. It has **no
owner** today. Whether CarbonTally should own it, and at what granularity, is **PO-3 (still open)**.
P17 must not assume it.

---

## 14. `NOT_IMPLEMENTED` vs `DOES_NOT_APPLY` — does the model prevent the ambiguity?

### 14.1 The question

If CarbonTally cannot process Scope 3 Category 2 (Capital Goods), does the platform tell the
customer *"Category 2 is not applicable"* — which would be **false**? Or does it correctly say
*"Category 2 applies, but CarbonTally cannot currently produce it"*?

### 14.2 Answer: **YES within the disclosure model; NO across the CAMS boundary — and the fix is already available**

### 14.3 The disclosure model does prevent it (evidence)

`derive_effective_class` (§9.1) keeps the **three sources of "no value"** strictly apart:

| Source of "no value" | `effective_class` | Ratified reason (`_reason_for_effective_class`) |
|---|---|---|
| **Regulatory** — it genuinely does not apply | `NOT_APPLICABLE` | *"not applicable for this reporting period and organisation"* |
| **Product** — CarbonTally can't produce it | `NOT_SUPPORTED` | *"not supported by CarbonTally"* |
| **Product, scheduled** | `FUTURE` | *"scheduled for a future CarbonTally capability"* |
| **Information** — unknown | `UNDETERMINED` | *"applicability undetermined - insufficient information"* |
| **Customer** — needs the customer | `CUSTOMER_INPUT_REQUIRED` | *"customer input required"* |

The model is **deliberately non-conflatable** (`DM-5`, Decision Record §8). Additionally:

- `UNDETERMINED` is **never coerced** to `NOT_APPLICABLE` (docstring + code, O-2);
- `validate_applicability_basis` **requires a basis** and refuses legal determinations (O-3);
- `unmapped_decision` returns `UNRESOLVED` — *"never a guessed producer and never a zero"* (O-4).

**So within the disclosure layer, the ambiguity is structurally prevented. This part needs no work.**

### 14.4 The CAMS side does **not** prevent it (evidence)

The P17 matrix's `architecture_status` legend (S17) is, verbatim, **entirely product-side**:

| Value | Legend (verbatim) | What it is a statement about |
|---|---|---|
| `SUPPORTED` | *"factor families and an existing calculation path are sufficient to build the category…"* | **CarbonTally** |
| `PARTIAL` | *"factor-supported or structurally derivable but has a boundary, data or deduplication prerequisite…"* | **CarbonTally** |
| `DEFERRED` | *"a ratified decision or external reference data is required before the category can be bounded"* | **CarbonTally** |
| `NOT_IMPLEMENTED` | *"no factor family, no methodology and no data contract exist; the category needs a new input contract and/or new factor set"* | **CarbonTally** |

**Not one of the four values carries a regulatory, organisational or materiality meaning.** Two
consequences follow:

1. ✅ **`architecture_status` cannot be *ambiguous* about applicability — it says nothing about it.**
2. ⚠️ **But that is precisely the danger:** a reader who sees `NOT_IMPLEMENTED` beside *"Capital
   Goods"* will read it as *"not applicable to me"*, which is **false**. Categories 2 and 10 are
   `NOT_IMPLEMENTED` because **CarbonTally has no factor set**, not because they do not apply.

### 14.5 The ambiguity is **not closed by vocabulary** — the tokens prove it

| Token | Where ratified | Registered in `disclosure.py`? |
|---|---|---|
| `NOT_SUPPORTED` | `REQUIREMENT_CLASSES` (disclosure) | **YES** — and mapped to *"not supported by CarbonTally"* |
| `NOT_APPLICABLE` | `REQUIREMENT_CLASSES` (disclosure) | **YES** — *"not applicable for this reporting period and organisation"* |
| `NOT_IMPLEMENTED` | **P17 matrix artifact only** | **NO.** Verified by grep: zero occurrences in `backend/` (excl. `.venv`), `supabase/` or any `docs/architecture/*.md` |

`NOT_IMPLEMENTED` is an **artifact-local, unratified** token. It is **not** a member of any governed
vocabulary, is **not persisted**, and has **no disclosure counterpart**. It therefore sits outside
the mechanism that prevents the ambiguity.

### 14.6 The already-available fix (recommendation, not implementation)

The correct mapping is **arithmetically determined** by the ratified vocabularies:

| P17 `architecture_status` | Correct disclosure expression | Rationale |
|---|---|---|
| `NOT_IMPLEMENTED` | `NOT_SUPPORTED` (*"not supported by CarbonTally"*) | No factor family/methodology/data contract — this is exactly a product limitation |
| `DEFERRED` | `NOT_SUPPORTED` for the current capability, or `FUTURE` if genuinely scheduled | Depends on whether a PO decision is pending or a delivery is planned → **PO-7** |
| `PARTIAL` | **Not a class at all** — processable within a bounded scope | Must surface as `UNRESOLVED` with a bounded reason, or `RESOLVED` for the in-scope part |
| `SUPPORTED` | **Not a class at all** — a capability statement | Never an `effective_class` |

> **Recommendation MD-1 (§17.2).** P17 must **never** express `architecture_status` as a
> requirement class. Where a customer-facing statement is needed, it must be routed through the
> existing `NOT_SUPPORTED` / `FUTURE` classes, which is a **citation** of ratified vocabulary, not
> a new model.

### 14.7 Residual risk recorded

Because `NOT_IMPLEMENTED` is unratified and unpersisted, nothing in code can currently **prevent**
its future misuse as an applicability statement. This is C-2 (§19) and drives PO-7 (§16).

---

## 15. Investor-demo truth

### 15.1 What is true today

| Fact | Value | Basis |
|---|---|---|
| Disclosure applicability model | **Schema-complete, contract-complete** | S3/S4 migrations + S1/S2 domain code |
| `disclosure_requirement_versions` rows seeded | **0** | `grep` over the repository (§7.4) |
| `disclosure_values` rows | **0** | Documented-historical (`ARCH-06 R10`) — **not** re-verified live (§4.3) |
| `report_version_artifacts` rows | **0** | Documented-historical (`ARCH-06 R10`) — **not** re-verified live (§4.3) |
| Any applicability assessment in the demo | **None possible** — no requirements exist to assess | §7.4 |
| Frontend surface for applicability | **None** | `grep` = zero matches (§4.3) |
| P17 Scope 3 category implementation | **None.** *"ARCHITECTURE ONLY - no category is implemented by this task"* (S17) | S17 |
| Category statuses re-verified at this baseline | **NO** — S17 was authored at `9c96cbf1…`, which is **not** the current baseline `55af3a64…` | S17 |

### 15.2 Per-category demo truth (all 15 categories)

The P17 matrix's 15 statuses, with the **applicability** column added by this decision:

| Cat | Name | `architecture_status` (product ability) | Applicability to any customer (this platform, today) | May be claimed as "applies"? |
|---|---|---|---|---|
| 1 | Purchased Goods and Services | `PARTIAL` | **`UNDETERMINED`** | **NO** |
| 2 | Capital Goods | `NOT_IMPLEMENTED` | **`UNDETERMINED`** | **NO** |
| 3 | Fuel- and Energy-Related Activities | `SUPPORTED` | **`UNDETERMINED`** | **NO** |
| 4 | Upstream Transportation and Distribution | `SUPPORTED` | **`UNDETERMINED`** | **NO** |
| 5 | Waste Generated in Operations | `SUPPORTED` | **`UNDETERMINED`** | **NO** |
| 6 | Business Travel | `SUPPORTED` | **`UNDETERMINED`** | **NO** |
| 7 | Employee Commuting | `PARTIAL` | **`UNDETERMINED`** | **NO** |
| 8 | Upstream Leased Assets | `PARTIAL` | **`UNDETERMINED`** | **NO** |
| 9 | Downstream Transportation and Distribution | `PARTIAL` | **`UNDETERMINED`** | **NO** |
| 10 | Processing of Sold Products | `NOT_IMPLEMENTED` | **`UNDETERMINED`** | **NO** |
| 11 | Use of Sold Products | `DEFERRED` | **`UNDETERMINED`** | **NO** |
| 12 | End-of-Life Treatment of Sold Products | `PARTIAL` | **`UNDETERMINED`** | **NO** |
| 13 | Downstream Leased Assets | `PARTIAL` | **`UNDETERMINED`** | **NO** |
| 14 | Franchises | `DEFERRED` | **`UNDETERMINED`** | **NO** |
| 15 | Investments | `DEFERRED` | **`UNDETERMINED`** | **NO** |

Rollup: `SUPPORTED` = 3, 4, 5, 6 (4) · `PARTIAL` = 1, 7, 8, 9, 12, 13 (6) · `DEFERRED` = 11, 14, 15 (3)
· `NOT_IMPLEMENTED` = 2, 10 (2). **Total = 15** — matches `category_count_check`.

> The **`UNDETERMINED`** column is **not** a defect, a placeholder or a gap in the matrix. It is the
> **honest, PO-correct** state: no mechanism to determine per-category applicability has been
> ratified (§11 outcome **B**), therefore the answer is not known, and `UNDETERMINED` is the
> vocabulary's first-class state for "not known" (§9.1).

### 15.3 What must NOT be claimed to an investor, customer or consultant

| ❌ Must not be claimed | Why |
|---|---|
| *"CarbonTally determines which Scope 3 categories apply to you."* | No such mechanism is ratified or populated (§11 B) |
| *"Category N is not applicable because it's `NOT_IMPLEMENTED`."* | **False inference** — `NOT_IMPLEMENTED` = "we have no factor set", not "it doesn't apply" (§14.4) |
| *"Applicability is live / already assessed for the demo organisations."* | **Zero requirements seeded** → zero assessments possible (§15.1) |
| *"Disclosure values are populated from the demo calculations."* | `disclosure_values` = 0 rows; no requirement content to project into |
| *"`SUPPORTED` means the category applies."* | `SUPPORTED` is a **product** statement only (§14.4) |
| *"The 15-category matrix is an applicability report."* | It is a capability/maturity artifact (§11.6) |

### 15.4 What MAY be claimed (accurate and defensible)

| ✅ May be claimed | Why it is true |
|---|---|
| *"The applicability model is implemented and enforced server-side, with an audit trail and a mandatory basis."* | S1/S2/S3/S4/S5; `validate_applicability_basis` |
| *"Regulatory non-applicability is structurally distinguished from product non-support."* | §14.3 — distinct classes, distinct reasons, non-coercion of `UNDETERMINED` |
| *"Where CarbonTally cannot produce a requirement, the platform says so explicitly rather than reporting zero."* | O-4 (`unmapped_decision`); `no_silent_estimation_rule` |
| *"Invalid results are machine-excluded from reporting."* | L-B reportability with mandatory reason/actor/timestamp (S15) |
| *"Scope 3 category 2 and 10 are recognised as requiring a new input contract and/or factor set."* | S17 `NOT_IMPLEMENTED` legend |
| *"Every Scope 3 category is separated from its neighbour by a boundary/origin property, not by factor family."* | S17 `structural_finding` |

### 15.5 The demo's most valuable truthful demonstrator

The single strongest honest demo claim available **today** is the **counter-factual discipline**
described in §14.3 and §11.7: the platform's *refusal* to say "not applicable" when it merely
cannot produce the number. That is the business value proposition (*"real provenance over
unexplained numbers"*, `AGENTS.md §85`) demonstrated with zero fabricated data.

---

## 16. PO decision register

### 16.1 Method

`DECISION-01 §16.1` raised **PO-1 … PO-9**. This task's job was **not** to decide them, but to
determine, from evidence, **which are now resolved, which are narrowed, and which are untouched**.
`AGENTS.md §62` forbids an implementer or a documentation artifact from resolving a business
question. Where this document resolves anything, it resolves only **factual/architectural**
questions (*"which layer owns this?"*), never **commercial or policy** ones.

### 16.2 The register — PO-1 … PO-5

| ID | Subject (gist from `DECISION-01 §16.1`) | Status after this task | What this task resolved by evidence | What **remains** a PO decision |
|---|---|---|---|---|
| **PO-1** | The organisation capability control list — D1 §19 lists 10 as *"Examples"*, D2 §42 lists 11 as *"reconciled"* | **STILL OPEN (unchanged)** | Only that neither document is an authoritative **enumeration** (§6.2 Q3) — a superset/example pair is not a definition | Which controls exist. **Unresolved and unresolvable from evidence** |
| **PO-2** | Capability storage representation (sibling multi-key table / extend `manual_processing_grants` / new policy table) | **STILL OPEN (unchanged)** | That organisation enablement is **not persisted at all** today (§4.3) — confirming there is no existing representation to adopt | The representation. **Not addressed by this task** |
| **PO-3** | Whether a Scope 3 category applicability model is required, and if so (a) which layer, (b) vocabulary, (c) dated/static, (d) subset vs enum | **PARTIALLY RESOLVED — narrowed** | **(a) RESOLVED: the disclosure layer** owns applicability, and **P17 must not build one** (§10.4, §12.3). **The ARCH-01 §42 contradiction is resolved** (§10.3, §17.1). Also resolved: even the disclosure axis is **framework-version granularity**, so it **cannot** express per-category applicability (§7.4, §13.1) | **(b)** vocabulary, **(c)** period-dated vs static, **(d)** subset membership vs per-category enum — **and the whole Q-11b materiality question**, which has **no owner** (§11.5, §13.4). **OPEN** |
| **PO-4** | How the CarbonTally product-capability gap is represented to (or hidden from) the customer, so *"CarbonTally has not built it"* is never shown as the customer's *"not applicable"* | **PARTIALLY RESOLVED — mechanism resolved** | **The mapping is arithmetically determined**: `NOT_IMPLEMENTED` → `NOT_SUPPORTED`; `DEFERRED` → `NOT_SUPPORTED`/`FUTURE`; `SUPPORTED`/`PARTIAL` are **never** requirement classes (§14.6). The *inward* rule was already ratified (`DM-5`/`B3-D6`) | The **outward wording**, and whether any customer surface exists before PO-3. **OPEN** |
| **PO-5** | The data-availability vocabulary — may an organisation distinguish *"we measured zero"* from *"we have not measured"*, and what are the permitted state names? (`NO_DATA_YET` / `EXCLUDED_WITH_REASON` are **not** ratified) | **NARROWED — still open** | That a ratified mechanism **already exists** on the disclosure side: `UNRESOLVED` + a distinct `effective_class` reason (§8.2, §9.5 O-4), and that the honest cross-layer mapping is *absence ↔ `UNRESOLVED`* (M-16). **No new state is needed** — only a decision about which existing state to surface | Whether to ratify a new name at all, or surface the existing `UNRESOLVED`/`effective_class` pair. **OPEN** |

### 16.3 The register — PO-6 … PO-9

| ID | Subject (gist from `DECISION-01 §16.1`) | Status after this task | What this task resolved by evidence | What **remains** a PO decision |
|---|---|---|---|---|
| **PO-6** | Scope 2 method-level applicability beyond the ARCH-01 §400 presence rule | **STILL OPEN (unchanged)** | Only that `SCOPE2_METHODS` is a **method** vocabulary, not an applicability vocabulary, and is already cited by P17-A (§10.3) — so method-level applicability still has **no owner** | Whether a per-method, per-period applicability state is required. **OPEN** |
| **PO-7** | Reconcile the two product-capability vocabularies: disclosure `CARBONTALLY_CAPABILITIES` (7, `D12`) vs P17 `architecture_status` (4, `status_semantics_authority`) | **STILL OPEN — now decision-ready** | The **complete evidence** for the decision: both legends verbatim (§14.4), the exact overlap (`MISSING_CAPABILITY` ↔ `NOT_IMPLEMENTED`), the **scope difference** (requirement-version vs category), and the decisive fact that **`NOT_IMPLEMENTED` is unratified and unpersisted** (grep = zero outside the artifact, §14.5) | **Unify, map, or keep separate with a documented mapping.** Only the PO may decide — both vocabularies are AUTHORITATIVE and neither may be silently changed. **OPEN** |
| **PO-8** | Does `modelled` report as its own data-quality bucket? | **STILL OPEN (unchanged)** | Nothing. Outside this task's scope; no disclosure-applicability evidence bears on it | The decision. **OPEN** |
| **PO-9** | May a per-organisation category-coverage surface exist in the investor demo before L2/L3 are decided, and under what truthful wording? | **NARROWED — decision-ready** | The **exact permitted and impermissible wordings** (§13.2) and the exhaustive *must-not-claim* / *may-claim* lists (§15.3, §15.4) | **Yes/no**, and adoption of the wording. **OPEN** |

### 16.4 Scorecard

| Status | Count | Decisions |
|---|---|---|
| **Fully resolved by evidence** | **0** | — |
| **Partially resolved** (mechanism resolved; substance open) | **2** | PO-3 (layer ownership + granularity), PO-4 (mapping) |
| **Narrowed / decision-ready** | **3** | PO-5, PO-7, PO-9 |
| **Unchanged / open** | **4** | PO-1, PO-2, PO-6, PO-8 |

> **Explicit statement for the record:** this artifact resolves **zero** PO business decisions. It
> resolves **architectural ownership** questions (which layer owns applicability; at what
> granularity it operates; how `NOT_IMPLEMENTED` must be expressed) and it **escalates** every
> remaining question. No PO decision was silently taken, and no existing ratified decision was
> altered.

### 16.5 The single highest-value next PO decision

**PO-3.** It gates PO-9, and it is the only open decision that determines whether *any* new P17
work is authorised. **PO-7 should be decided in the same sitting**, because its answer determines
whether the `NOT_IMPLEMENTED` ↔ `MISSING_CAPABILITY` reconciliation is a **mapping**
(documentation only) or a **change** (schema + migration + regression).

---

## 17. Required implementation changes, if any

### 17.1 Recommended amendment to `ARCH-01 §42` (documentation — **recommended, not applied**)

`ARCH-01 §42` currently files applicability as *"a separate later work package"*. That wording is
**the origin of the cross-layer contradiction** and is now **factually incorrect**: the work package
was delivered in Phase 8 B1/B3.

**Recommended replacement wording** (for PO approval — **not applied by this task**):

> **§42 (amended proposal).** Applicability is **not** a P17 work package. It is owned by the Phase 8
> Disclosure model, already implemented:
> `disclosure_applicability_assessments` with `APPLICABILITY_STATUSES`
> (`APPLIES` / `DOES_NOT_APPLY` / `UNDETERMINED` / `CUSTOMER_INPUT_REQUIRED`), resolved through
> `derive_effective_class` (applicability → capability → requirement class).
> Its unit of assessment is **framework version × organisation × reporting period** — it is
> therefore **not** a Scope 3 category applicability model, and P17 must not build one.
> Where P17 needs an existing vocabulary, it **cites** it, exactly as P17-A cites
> `CONSOLIDATION_APPROACHES` and `SCOPE2_METHODS`.
> Any per-category applicability requirement is **PO-3**, and its most likely correct resolution is
> to **author a requirement** into the existing catalogue — not to extend P17.

**Rationale:** leaving the current wording in place will cause a **third** implementation attempt to
build a second applicability model, duplicating governed vocabulary and creating two divergent
resolutions of the same three facts (`AGENTS.md §4`, `§71`).

### 17.2 Recommendations MD-1 … MD-4 (documentation only)

| ID | Recommendation | Layer | Requires PO? | Change type |
|---|---|---|---|---|
| **MD-1** | P17 must **never** express `architecture_status` as a requirement class. Route customer-facing statements through the existing `NOT_SUPPORTED` / `FUTURE` classes (§14.6) | P17 documentation + future UI | **No** — it is a citation of ratified vocabulary | Documentation/UI wording |
| **MD-2** | Wherever "capability" appears customer-facing, it must be disambiguated as **product capability** (`carbontally_capability`) or **organisation enablement** (§6.3) | Product/docs | **No** — clarity only | Documentation |
| **MD-3** | The 15-category matrix must carry an explicit header stating it is a **capability/maturity** artifact and **not** an applicability assessment (§11.6) | P17 artifact | **No** — restates the artifact's own `status_semantics_authority` | Documentation |
| **MD-4** | Adopt the §13.2 permitted/impermissible wording table as the standing language rule for any category surface | All layers | **Yes** — PO-9 covers adoption | Documentation |

### 17.3 Code / schema changes required

| # | Change | Required? | Why |
|---|---|---|---|
| 1 | New P17 applicability table/column/enum | **NO — PROHIBITED** | §10.4, §12.3. Would duplicate governed vocabulary |
| 2 | New disclosure state names | **NO — PROHIBITED** | §1.2. Existing vocabularies are sufficient (§13.3) |
| 3 | Seed `disclosure_requirement_versions` | **NO — NOT AUTHORISED HERE** | `PQ-6` governs content authoring; a distinct governed task. Also, seeding alone would **not** resolve PO-3 (§11.5) |
| 4 | Any frontend category-applicability surface | **NO — BLOCKED ON PO-3 / PO-9** | §15.3, §16.3 |
| 5 | Fix the redundant branch at `disclosure_projection.py:267-269` (O-1) | **NO** | Harmless; behaviour identical; `AGENTS.md §71` — smallest correct change |
| 6 | Amend `ARCH-01 §42` wording | **RECOMMENDED** (§17.1) | Removes the contradiction's source |
| 7 | Add a documentation cross-reference from the P17 matrix to §14.6 MD-1 | **RECOMMENDED** | Prevents the `NOT_IMPLEMENTED` → "not applicable" mis-inference |

### 17.4 What must happen **before** any implementation begins

1. **PO-3** decided (per-category applicability: model or not; if yes, `requirement`-based).
2. **PO-7** decided (capability vocabulary relationship: map or change).
3. `ARCH-01 §42` amended (§17.1).
4. Only then may a P17 implementation task be scoped — and it must be scoped as a
   **citation/consumption** task, never as a **model-authoring** task.

---

## 18. What this decision does **not** change

### 18.1 Prohibitions carried forward

| # | Prohibition | Authority |
|---|---|---|
| P-1 | **No second applicability model** in P17/CAMS | §10.4, §12.3 |
| P-2 | **No new state names** anywhere | §1.2; `AGENTS.md §62` |
| P-3 | **No amendment** to `REQUIREMENT_CLASSES`, `CARBONTALLY_CAPABILITIES`, `APPLICABILITY_STATUSES`, `VALUE_STATUSES` | §5, §6, §7, §8 |
| P-4 | **No merge** of L-A (disclosure materialisation) and L-B (accounting reportability) | §8.3, M-14 |
| P-5 | **No reuse** of `architecture_status` as an applicability or requirement class | §14.6 |
| P-6 | **No new cross-layer seam** without a PO decision | §12.2 |
| P-7 | **No silent resolution** of PO-1 … PO-9 | §16 |
| P-8 | **No change** to RLS, grants, API contracts or the OpenAPI surface | §2.2 |
| P-9 | **No `ARCH-01` file modification** — amendment is recommended, not applied | §17.1 |
| P-10 | **No database access**, no migration applied, no seeding | §3.1 |

### 18.2 Frozen artifacts this document treats as authoritative and untouched

- Phase 8 B1 disclosure foundation (migrations `20260914000000`, `20260915000000`)
- D12 (capability axis), D13/APPL (applicability), PQ-3 (materialisation), D15 (immutability), DM-5 (non-conflation)
- B3-D4 applicability ratification (`CARBONTALLY_PHASE8_B3_PO_DECISION_RECORD_20260914.md`)
- P16R5 result reportability lifecycle (migration `20261008000000`)
- P17-A accounting dimensions (migration `20261010000000`)
- The 15-category matrix and its `architecture_status` legend (S17)

### 18.3 Explicit statement regarding pre-existing untracked files

`docs/architecture/P17-PRODUCT-01 — Complete Scope 2 + Scope 3 Processing & Evidence Product
Specification.md` (S18) is **untracked** in this repository. It was **read** as evidence. It was
**not** modified, staged, committed or deleted. Its untracked status is recorded so a future
reader can reproduce this decision's evidence set exactly (`AGENTS.md §70`, `§81`).

---

## 19. Cross-layer contradictions and residual risks

### 19.1 Contradiction register

| # | Contradiction / risk | Layers | Severity | Status after this decision |
|---|---|---|---|---|
| **C-1** | `ARCH-01 §42` files applicability as *"a separate later work package"*, while Phase 8 B1/B3 **already implement** it | P17 architecture ↔ disclosure implementation | **HIGH** — it caused two failed implementation attempts | **RESOLVED in principle** (§10.3, §17.1). **Residual:** the artifact text is unchanged until the PO approves the amendment, so the misleading wording **still exists on disk** |
| **C-2** | `NOT_IMPLEMENTED` (P17 matrix) is **unratified and unpersisted**; `NOT_SUPPORTED` (disclosure) is ratified and persisted. The two express the same idea in different vocabularies | P17 artifact ↔ disclosure domain | **HIGH** — directly enables the *"not implemented ⇒ not applicable"* false statement | **OPEN** — correct mapping established (§14.6) but **the relationship is PO-7** |
| **C-3** | Two different concepts are both called **"capability"**: product capability (7 values, persisted) and organisation enablement (undefined list, unpersisted) | D12 ↔ D1 §19 / D2 §42 | **MEDIUM** — naming collision, not a data defect | **OPEN** — disambiguation recommended (MD-2); the list itself is PO-1 |
| **C-4** | The 15-category `architecture_status` matrix can be **read as** an applicability assessment by a reader who does not consult the legend | P17 artifact ↔ customer interpretation | **MEDIUM** | **MITIGATED only by documentation** (MD-3). Nothing structural prevents misuse |
| **C-5** | **Asymmetric seam:** `scope2_method` crosses P17→disclosure via `scope2_method_hint`, but **`scope3_category` has no disclosure counterpart**. Methodology is partially wired | P17-A ↔ disclosure | **MEDIUM** | **OPEN — recorded.** Not required today (no per-category disclosure requirement exists), but it is the seam that would be needed if PO-3 says yes |
| **C-6** | Three tokens (`NOT_APPLICABLE`, `CUSTOMER_INPUT_REQUIRED`, `UNDETERMINED`) exist in **both** `REQUIREMENT_CLASSES` and `APPLICABILITY_STATUSES` with **different meanings** | disclosure domain-internal | **LOW–MEDIUM** — a genuine implementation/human error trap | **RATIFIED BY DESIGN** — no change permitted (§5.4). Mitigated by `effective_class` resolving the pair |
| **C-7** | The applicability axis operates at **framework-version** granularity and **cannot** express requirement-level or category-level applicability | disclosure implementation ↔ P17 need | **HIGH** — it is the structural reason PO-3 cannot be answered by citing the existing model | **RESOLVED AS A FINDING** (§7.4, §13.1). The *decision* it forces is **PO-3** |
| **C-8** | The applicability model has a full API and **no consumer**. Its correct behaviour is therefore **incidental, not enforced** | disclosure API ↔ product surface | **MEDIUM** — latent; becomes active the moment a UI is built | **OPEN** — recorded. Mitigated only while zero consumers exist |

### 19.2 Material contradictions that **remain** open

Per the task's verdict rule, the following are **material cross-layer contradictions that this
document has NOT resolved** — they are **identified and escalated**, not fixed:

| Contradiction | Why it is material | Gate |
|---|---|---|
| **C-2** — `NOT_IMPLEMENTED` ↔ `NOT_SUPPORTED` unmapped | A customer-facing statement can currently be made that misrepresents a product limitation as a regulatory non-applicability | **PO-7** |
| **C-5** — no Scope 3 category seam | If PO-3 authorises per-category applicability, an unratified seam will be needed (or must be avoided) | **PO-3** |
| **C-8** — unenforced applicability semantics with a live API | The correct non-conflation behaviour is not enforced by any consumer contract; the first UI built could re-introduce the conflation | **PO-9 / a future UI task** |

**Therefore the verdict is `PARTIAL`, not `COMPLETE`** (§20).

### 19.3 Residual risk accepted by this task

| Risk | Why accepted |
|---|---|
| `disclosure_values` / `report_version_artifacts` row counts were not re-verified live | §2.2 forbids database access; the counts are attributed to their source and marked documented-historical (§4.3) |
| P17 category statuses were authored at an **earlier SHA** (`9c96cbf1…`) than this baseline | The authoring artifact records `implementation_state = "ARCHITECTURE ONLY"` and `category_statuses_unchanged`, so the statuses remain valid **as architecture statements**; they are not re-verified product state, and §15.1 says so |
| Human-readable category names in §15.2 were transcribed from the artifact | The artifact is the authority; the names are presentation only and carry no decision weight |

---

## 20. Verdict, deliverable summary and recommended next task

### 20.1 Verdict

> ## `P17_DECISION_PARTIAL`
>
> The **architectural** question this task was raised to answer is **fully resolved**:
> applicability is owned by the Phase 8 Disclosure model, P17/CAMS must not build a second one, and
> the `ARCH-01 §42` contradiction is explained and a correction is recommended.
>
> The verdict is **PARTIAL rather than COMPLETE** because **material cross-layer contradictions
> remain open and unresolvable without a PO decision** — specifically **C-2**
> (`NOT_IMPLEMENTED` ↔ `NOT_SUPPORTED` unmapped, PO-7), **C-5** (no Scope 3 category seam, PO-3) and
> **C-8** (unenforced applicability semantics behind a live API with no consumer, PO-9). Claiming
> COMPLETE would require either silently deciding PO-3/PO-7 — prohibited by `AGENTS.md §62` — or
> asserting a resolution the evidence does not support (`AGENTS.md §74`).

### 20.2 Required task-return fields

| Field | Value |
|---|---|
| **Task ID** | `P17-DECISION-02` |
| **Starting SHA** | `55af3a64c0e473d0a6b43601e407bd09e6609418` |
| **Ending SHA** | `55af3a64c0e473d0a6b43601e407bd09e6609418` **+ this document's commit** (see §20.5; no source file changed, so all other paths remain at the starting SHA) |
| **Branch** | `p8-release-reconciled` |
| **Report path** | `docs/architecture/CT-PO-P17-DECISION-02-RECONCILE-CAMS-DISCLOSURE-APPLICABILITY-20250925.md` |
| **Files changed** | **1 created** (this report). **0** source, schema, migration, API, RLS or frontend files modified. **0** files deleted |
| **Cross-layer findings** | C-1 … C-8 (§19.1), of which **C-1 and C-7 resolved as findings**, **C-2, C-5, C-8 remain material and open** (§19.2); **C-3, C-4, C-6 recorded** |
| **PO decisions resolved** | **0 fully resolved.** PO-3 and PO-4 **partially resolved** (architectural mechanism only); PO-5, PO-7, PO-9 **narrowed / decision-ready**; PO-1, PO-2, PO-6, PO-8 **unchanged/open** (§16.4) |
| **Production contacted** | **NO** |
| **Pushed** | **NO** |
| **Database contacted** | **NO** |
| **Migrations applied** | **NO** |
| **`.gitignore` modified** | **NO** |
| **Pre-existing untracked files touched** | **NO** (§18.3) |
| **Verdict** | **`P17_DECISION_PARTIAL`** |

### 20.3 The three findings that matter most

1. **Applicability is disclosure-owned and must stay there** (§10.4) — and the P17 layer already
   demonstrated the correct pattern twice by **citing** `CONSOLIDATION_APPROACHES` and
   `SCOPE2_METHODS` instead of minting its own vocabularies (§10.3). **This is the reconciliation.**
2. **Applicability is framework-version granularity, not category granularity** (§7.4) — a **new,
   implementation-derived** finding that **disposes of** the assumption that the existing model could
   answer *"is Scope 3 Category N applicable?"*. Outcome **B** (§11.4): a PO decision, not a build.
3. **`NOT_IMPLEMENTED` is an unratified, unpersisted token with no counterpart in any governed
   vocabulary** (§14.5) — and it is the exact token that will be misread as *"not applicable"*. The
   correct expression already exists: `NOT_SUPPORTED` (§14.6).

### 20.4 Recommended next implementation task

> ### `P17-DECISION-02-FOLLOWUP-01` — *Ratify the PO-3 / PO-7 decisions and amend `ARCH-01 §42`*
>
> **Scope (documentation only, no code):**
> 1. Place **PO-3** and **PO-7** before the PO with the decision-ready evidence in §11 and §14.
> 2. On approval, amend `ARCH-01 §42` using the proposed wording in §17.1.
> 3. Apply **MD-1 … MD-4** (§17.2) — including the capability/maturity disclaimer header on the
>    15-category matrix.
> 4. **Do not** create any P17 applicability model, table, column or enum.
>
> **Why this and not an implementation task:** every candidate implementation is **gated** on PO-3 or
> PO-7 (§17.4). An implementation task started now would either duplicate governed vocabulary or
> decide a business question by accident — both prohibited.
>
> **Deferred candidates (do NOT start):** a per-organisation category-coverage UI (blocked on PO-9);
> seeding disclosure requirement content (a `PQ-6`-governed content task, and insufficient alone);
> a Scope 3 category disclosure seam (blocked on PO-3).

### 20.5 Git discipline observed

| Rule | Compliance |
|---|---|
| `git status` / `git branch` / `git rev-parse HEAD` inspected before work | ✅ |
| No `git reset --hard`, `git clean -fd`, force-push, rebase or history rewrite | ✅ |
| No `.env`, credential, token, JWT or signed URL read, written or committed | ✅ |
| No unrelated working-tree change absorbed | ✅ |
| `.gitignore` untouched | ✅ |
| Pre-existing untracked files untouched | ✅ |
| **Not pushed** | ✅ |

### 20.6 Durable facts to retain in Hindsight

Per `AGENTS.md §3` and `§83`, the following durable project facts should be retained (no secrets,
no credentials, no temporary data):

1. **Applicability is owned by the Phase 8 Disclosure model** — `APPLICABILITY_STATUSES`
   (`APPLIES` / `DOES_NOT_APPLY` / `UNDETERMINED` / `CUSTOMER_INPUT_REQUIRED`) at
   framework-version × organisation × period granularity. **P17/CAMS must not build a second model.**
2. **Applicability is framework-version granularity, not Scope 3 category granularity.**
3. **P17-A already establishes the correct reuse pattern** — it cites
   `backend/domain/disclosure.py` `CONSOLIDATION_APPROACHES` and `SCOPE2_METHODS` rather than
   minting its own vocabularies.
4. **Four separate lifecycles must never be merged** — `value_status` (PQ-3), `reportability_status`
   (P16R5), report-version status, purpose-version status.
5. **`NOT_IMPLEMENTED` (P17 matrix) is unratified and unpersisted**; the governed expression of a
   product limitation is `NOT_SUPPORTED`.
6. **`ARCH-01 §42` is factually incorrect** and awaits a PO-approved amendment.

---

*End of `CT-PO-P17-DECISION-02`. Documentation-only artifact. No code, schema, RLS, API, UI,
database or seeding change was made. Production was not contacted. Nothing was pushed.*


















