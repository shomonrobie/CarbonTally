# CT-PO-P17-DECISION-03 — PO Freeze: Product Capability Status, Category Applicability Boundary, and Investor Truth Surface

**Document ID:** `CT-PO-P17-DECISION-03-PO-FREEZE-CAPABILITY-STATUS-INVESTOR-SURFACE-20250926`
**Task ID:** `P17-DECISION-03-20260926-PO-FREEZE-CAPABILITY-STATUS-INVESTOR-SURFACE`
**Task type:** PRODUCT OWNER DECISION / FINAL PRODUCT-CONTRACT FREEZE — **documentation only**
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Date:** 2025-09-26
**Authority:** issued as the PO product-contract freeze requested by the task brief (§1, §4–§12, §15)
**Production authorization:** NOT AUTHORIZED
**Production contacted:** NO
**Database contacted:** NO (no query, no write, no migration, no seeding)

---

## 1. Task identity

### 1.1 What this document is

This is the **final PO product-contract decision** that closes the three decisions which were
blocking the next meaningful CarbonTally implementation phase:

| ID | Question |
|---|---|
| **PO-3** | Does CarbonTally require a **customer-facing Scope 3 category applicability** concept? |
| **PO-7** | How does **P17 product capability maturity** map to the **governed Disclosure vocabulary**, especially `NOT_SUPPORTED`? |
| **PO-9** | What exactly must the **investor-facing CarbonTally product surface** show? |

It is a **decision and freeze** artifact. It does not implement, and it does not re-open the
architecture. Specifically, per task §13 it does **not** create:

* another **applicability model** (PO-3 rules it out),
* another **capability model** (PO-7 rules it out),
* another **public status vocabulary** (PO-7 and §12 below rule it out).

### 1.2 What this document is NOT

* It is **not** an implementation authorization. §18 lists the consequences; each remains
  gated on a separately authorized task.
* It is **not** a re-audit of P17. It builds directly on `P17-DECISION-01` and
  `P17-DECISION-02` and re-verifies only the facts those two documents could not settle.
* It is **not** a UI specification. It is the contract a UI must satisfy; the UI itself is a
  future, separately authorized delivery.

### 1.3 The three facts this document had to settle

`P17-DECISION-02` ended `PARTIAL` with **zero** PO decisions fully resolved and three material
contradictions open (its §19.2): **C-2** (`NOT_IMPLEMENTED` ↔ `NOT_SUPPORTED` unmapped),
**C-5** (no Scope 3 category seam), **C-8** (unenforced applicability semantics with a live API).
Those three contradictions are the residue this document must close or escalate, and it may not
close them by inventing vocabulary.

---

## 2. Baseline and method

### 2.1 Baseline verification (performed before any source was read)

| Check | Required | Observed | Result |
|---|---|---|---|
| Branch | `p8-release-reconciled` | `p8-release-reconciled` | **MATCH** |
| `git rev-parse HEAD` | `28999af0926d6ce1032b3903c2737aabe6b350d9` | `28999af0926d6ce1032b3903c2737aabe6b350d9` | **MATCH** |
| Last commit on branch | `28999af` *"docs(p17): P17-DECISION-02 reconcile CAMS with Phase 8 disclosure applicability"* | identical | **MATCH** |

The baseline **matches exactly**. This task therefore proceeds and does **not** STOP.

### 2.2 Working-tree state at task start (preserved, not touched)

| Item | State | Action taken |
|---|---|---|
| `.gitignore` | **modified** (pre-existing) | **NOT committed, NOT reverted, NOT touched** |
| Pre-existing untracked files (`.costrict/`, `8`, `=`, `costrict-p3-ov-01-independent-re-verification.txt`, `docs/ChatGPT/*`, `docs/architecture/CO-STRING-…`, `CT-PO-MASTER-WORKPLAN…`, `CT-PO-P12-…`, `CT-PO-P14-…`, `CarbonTally_Insight_*`, `CarbonTally_PO_INS-01_*`, `CarbonTally_PO_Insight_*`, `P17-PRODUCT-01 …`) | **untracked at start** | **NOT added, NOT modified** |

`P17-PRODUCT-01` remains **untracked and unmodified** and is treated as an authoritative
*read-only product source* (task §3.3), exactly as `P17-DECISION-01` and `-02` treated it.

### 2.3 Method

1. Read the task brief and `AGENTS.md` (esp. §2 source-of-truth hierarchy, §62 PO-decision rule,
   §73/§74 acceptance language, §80 historical-findings rule).
2. Read the two prior P17 decision artifacts and the P17 architecture/implementation chain.
3. **Re-verified by direct code/grep inspection** every load-bearing factual claim inherited
   from `P17-DECISION-02` — because `AGENTS.md §80` forbids reporting a historical finding as a
   current fact, and because `P17-DECISION-02` contained at least one claim that does not
   survive re-verification (§5.4 below).
4. Classified each of PO-3 / PO-7 / PO-9 as **DECIDED / DEFERRED / PO DECISION STILL REQUIRED**
   on the evidence, and separated *architectural* findings from *commercial* choices
   (`AGENTS.md §4`, `§62`).

### 2.4 Scope guarantee

| Excluded action | Performed? |
|---|---|
| migrations created / altered | **NO** |
| schema / RLS / policy changed | **NO** |
| API routes or services created / altered | **NO** |
| Python / TypeScript / SQL modified | **NO** |
| tests created / modified | **NO** |
| seed or demo data touched | **NO** |
| any database read or write (incl. `carbontally_test`, `carbontally_demo_local`) | **NO** |
| UI created | **NO** |
| production contacted | **NO** |
| `.gitignore` modified | **NO** |
| pre-existing untracked files touched | **NO** |

---

## 3. Sources reviewed

### 3.1 Prior decision artifacts (the immediate parents of this decision)

| Source | Lines | Role here |
|---|---|---|
| `CT-PO-P17-DECISION-01-CAMS-CAPABILITY-APPLICABILITY-CONTRACT-20250925.md` | 1,412 | Raised PO-1…PO-9 (§16.1); froze the four-layer model L1–L4 (§14) |
| `CT-PO-P17-DECISION-02-RECONCILE-CAMS-DISCLOSURE-APPLICABILITY-20250925.md` | 1,205 | Established disclosure ownership of applicability; findings §7.4, §11.4, §14.5–14.6, §16 |

### 3.2 Product / PO authority

* `P17-PRODUCT-01 — Complete Scope 2 + Scope 3 Processing & Evidence Product Specification.md` (1,374 lines, untracked, read-only)
* `CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` (854 lines) — PO-CAMS
* `CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` (1,481 lines) — POST-ARCH, incl. §27 Scope 2, §28 Scope 3, §34 capability matrix

### 3.3 P17 architecture chain

`ARCH-01` (1,673 lines; esp. §42 Disclosure and framework separation, lines 1200–1220), `ARCH-02`,
`ARCH-04`, `ARCH-05`, `ARCH-06`, `UIUX-01`, `IMPLEMENTATION-PHASE-PLAN` (incl. §16 ARCH-02
amendments A1–A12, §17 ARCH-04 corrections, §18 ARCH-06 corrections).

### 3.4 Phase 8 Disclosure authority (the governed vocabulary)

| Source | What was read |
|---|---|
| `backend/domain/disclosure.py` (356 lines) | `REQUIREMENT_CLASSES` (L47), `CARBONTALLY_CAPABILITIES` (L60), `APPLICABILITY_STATUSES` (L124), `CONSOLIDATION_APPROACHES` (L131), `VALUE_STATUSES` (L139), `SCOPE2_METHODS` (L145), `FRAMEWORK_SEEDS` (L153) |
| `backend/domain/disclosure_projection.py` (449 lines) | `derive_effective_class` (L246), `decide_projection` (L283), `validate_applicability_basis` (L393), `unmapped_decision` (L406) |
| `backend/api/v3_disclosure.py` (686 lines) | the disclosure API surface |
| `CARBONTALLY_PHASE8_B3_PO_DECISION_RECORD_20260914.md`, `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md`, `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` | D12, D13, APPL, B3-D4, B3-D6, PQ-3, DM-5 |

### 3.5 P17 implementation reports (historical; `AGENTS.md §80`)

`P17-IMPLEMENT-09` (674 lines) and `P17-IMPLEMENT-10` (907 lines), plus the machine-readable
matrices `p17_scope3_category_matrix_20250925.json` (460 lines) and
`p17_scope2_domain_matrix_20250925.json` (350 lines).

### 3.6 Investor-surface authority

`CT-PO-P12-STEP1-FROZEN-INVESTOR-DEMO-SCOPE-20260924.md` (345 lines — Stories A–D),
`CT-PO-P14-RECON-01-INVESTOR-ACCEPTANCE-CONTRACT-20260924.md` (760 lines — per-scope
reconciliation and contract consequences), `CT-PO-PRODUCT-CAPABILITY-INVESTOR-DEMO-STUDY-20260924.md`,
`CT-PO-COMPREHENSIVE-INVESTOR-READY-PLATFORM-STUDY-20260924.md`.

### 3.7 Live code re-verified for this decision (read-only)

`backend/domain/scope3.py`, `backend/domain/scope3_contracts.py`, `backend/domain/cams.py`,
`backend/core/exceptions.py`, `backend/api/v3_scope3.py`, `backend/api/v3_accounting_context.py`,
`backend/services/scope2_calculation.py`, `backend/services/scope3_calculation.py`,
`supabase/migrations/20261012000000_p17d_scope3_category_taxonomy.sql`,
`backend/tests/unit/data/test_p17_migrations.py`,
`backend/tests/integration/test_p17_09_scope2_scope3_persistence_runtime.py`.

### 3.8 Current verified implementation state (re-verified at this baseline)

Because §4–§6 depend on what is *actually* implemented, the following was established by direct
inspection at `28999af`, not inherited from a report:

| Fact | Verified observation | Method |
|---|---|---|
| P17 migrations present in the repo | `20261010000000_p17a_accounting_dimensions_and_factor_governance`, `20261011000000_p17c_contractual_instruments_and_allocations`, `20261012000000_p17d_scope3_category_taxonomy`, `20261013000000_p17h_estimation_and_assumption_records`, `20261014000000_p17_10_product_contract_reporting_dimensions` | `ls supabase/migrations \| grep -iE 'p17'` |
| **No** `p17b` / `p17e` / `p17f` / `p17g` migration | confirmed absent | same |
| Scope 2 / Scope 3 routers are registered | `api/router.py:52-53` imports `v3_scope2`, `v3_scope3`; `:228-229` includes both | `grep -n 'scope' api/router.py` |
| Scope 2 / Scope 3 calculation services exist | `backend/services/scope2_calculation.py`, `backend/services/scope3_calculation.py` | `ls backend/services` |
| All 15 categories carry an explicit, code-resident architecture status | `backend/domain/scope3.py:65-71` — `class Scope3Status(StrEnum)` with `SUPPORTED`, `PARTIAL`, `DEFERRED`, `NOT_IMPLEMENTED`; `NOT_IMPLEMENTED_CATEGORIES = (2, 10)` | read + grep |
| **`architecture_status` is returned by the authenticated API** | `backend/api/v3_scope3.py:230` `"architecture_status": contract.architecture_status`; `backend/api/v3_accounting_context.py:354` | grep |
| The taxonomy row is **deliberately** not allowed to imply a methodology | migration L14-18: *"Category support status (SUPPORTED / PARTIAL / NOT_IMPLEMENTED / DEFERRED) is an ARCHITECTURE status … and is deliberately NOT stored here — a status is not reference data and putting it in a lookup table would invite treating 'the row exists' as 'the category is implemented'"*; enforced by a test asserting the four status tokens are **absent** from the migration (`backend/tests/unit/data/test_p17_migrations.py:460-463`) | read |
| The refusal path exists and is named for the governed concept | `backend/core/exceptions.py:171-181` — `Scope3CategoryNotSupportedError`, `code = "SCOPE3_CATEGORY_NOT_SUPPORTED"` | read |
| An explicit guard prevents inventing a methodology | `backend/domain/scope3.py:305-323` `assert_calculable` raises for `NOT_IMPLEMENTED`/`DEFERRED`; default-enforced at `backend/domain/cams.py:167,203` (`require_calculable_category: bool = True`) | read + grep |
| An honest bounded pathway exists for categories with no automated methodology | `backend/domain/scope3_contracts.py:17-30` — `ACTIVITY_FACTOR` / `ESTIMATION` / `MANUAL_REVIEW`; *"No number is invented"*; status *"reported verbatim, never upgraded"* | read |
| The non-test call sites of `assert_calculable` / `is_calculable` | `domain/scope3.py`, `domain/cams.py`, `domain/__init__.py` (exports), `api/v3_accounting_context.py` — **and nowhere else** | grep |
| Frontend consumers of applicability | **none** — the only `applicab*` matches in `frontend/src` are English prose ("if applicable", "applicable law") | grep |

**Consequence for this decision.** Two of `P17-DECISION-02`'s premises need restating (see §5.4):
the internal capability vocabulary is no longer confined to a governance JSON artifact — it is
**code-resident and crosses the authenticated API boundary**. That raises, not lowers, the
urgency of PO-7.

### 3.9 Live database verified for this decision (read-only)

The scope of this decision is documentation-only, but PO-7 and PO-9 both turn on whether the
governed vocabulary and the P17 result dimensions exist **at runtime** and not merely in source
(`AGENTS.md §2` — runtime truth outranks source). The following was therefore verified directly.
**Every statement issued was `SELECT`-only** (against `information_schema`, `pg_constraint`, and
the tables themselves); **no row, column, table, index, policy or migration was created, altered
or deleted**, and the demo dataset was not touched (`AGENTS.md §55`).

Target: the local investor-demo database **`carbontally_demo_local`** on `supabase_db_carbon_ledger`
(`127.0.0.1:54426`). It is the database the demo-lab PostgREST container is configured against
(`carbontally_demo_lab_postgrest` → `PGRST_DB_URI=…/carbontally_demo_local`), so it — not the
co-resident `postgres` database — is the demo runtime baseline. (Migration state is not tracked
there: `supabase_migrations.schema_migrations` does not exist in that database.)

| Check | Result | Meaning for this decision |
|---|---|---|
| `public` table count | **141** | matches the "existing 141-table inventory" cited by `20261011000000_p17c…` — this is the pre-P17 demo baseline |
| `disclosure_*` tables | **15 present** | the Phase 8 disclosure model **is applied** at runtime |
| `disclosure_requirement_versions.carbontally_capability` exists | **yes** | `M-1`'s target has a real, persisted runtime home — PO-7 introduces no schema |
| CHECK on `carbontally_capability` | **7 values**: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `STRUCTURED_INPUT_REQUIRED`, `EXTERNAL_INPUT_REQUIRED`, `MISSING_CAPABILITY`, `FUTURE`, `NOT_APPLICABLE_TO_PRODUCT` | DB-enforced, and **identical** to `backend/domain/disclosure.py` L60-68 and to `20260914000000_p8_b1…` L128-130 — **no source↔runtime drift** |
| CHECK on `requirement_class` | **8 values**: `REQUIRED`, `CONDITIONAL`, `OPTIONAL`, `NOT_APPLICABLE`, `CUSTOMER_INPUT_REQUIRED`, `UNDETERMINED`, `NOT_SUPPORTED`, `FUTURE` | idem — the `REQUIREMENT_CLASSES` tuple at `backend/domain/disclosure.py:47-56`, and `20260914000000_p8_b1…` L122-124 |
| `disclosure_requirement_versions.scope2_method_hint` (with its own CHECK) | **present** | the §5.4 correction to `P17-DECISION-02 §M-7` is confirmed **at runtime**, not only in source |
| `disclosure_values.scope2_method_hint` | **absent** | confirms the seam is catalogue-level, not value-level |
| `disclosure_requirement_versions` rows | **0** | the governed catalogue is **empty** — no requirement and therefore no capability value is currently persisted |
| `disclosure_applicability_assessments` rows | **0** | the applicability seam exists and is unused (directly relevant to PO-3 / PO-9) |
| `calculation_snapshots.scope2_method` | **absent** | P17-A (`20261010000000`) **not applied** to the demo database |
| `calculation_snapshots.scope3_category` | **absent** | P17-D (`20261012000000`) **not applied** |
| `contractual_instruments`, `instrument_allocations` | **absent** | P17-C (`20261011000000`) **not applied** |
| `estimation_records` | **absent** | P17-H (`20261013000000`) **not applied** |
| any column named `architecture_status`, anywhere in `public` | **absent** | confirms at runtime the deliberate non-persistence of the internal status (§5.4) |

**Three consequences, binding on §18:**

1. **PO-7's governed vocabulary is real at runtime but unpopulated.** The column and its CHECK
   exist; the catalogue has zero rows. A capability claim made on any surface **today** therefore
   has a governed *shape* but no governed *backing*. Authoring the requirement catalogue is a
   separate, out-of-scope task — it is **not** a reason to change the mapping.
2. **The P17 result dimensions do not exist at runtime.** `scope2_method`, `scope3_category`,
   `contractual_instruments` and `estimation_records` are **source-only**. Consequently PO-9
   items 3–6 (methodology, `scope2_method` / `scope3_category`, factor provenance, estimation
   basis) **cannot be satisfied against the current demo database** until the P17 schema deltas
   are applied. This is an implementation prerequisite (§18) — **not** grounds to weaken the
   frozen contract.
3. **Absence of a column is an engineering state and may never be shown.** Per PO-9, absence
   renders as absence — never as `0`, never as "not applicable", and never as a capability claim
   inferred from a missing column.

---

## 4. PO-3 analysis — should CarbonTally have a customer-facing Scope 3 category applicability concept?

### 4.1 The question, stated precisely

> Does CarbonTally require a **customer-facing Scope 3 category applicability** concept — i.e. a
> statement of the form *"Scope 3 category N applies / does not apply to this organisation and
> period"*?

### 4.2 The evidence

**(a) Applicability already has an owner, at the wrong granularity for this question.**
`P17-DECISION-02 §7.4` (independently-derived) found that the Phase 8 Disclosure applicability
axis is assessed at **framework-version × organisation × reporting period** — it has *no*
requirement-level and *no* category-level discriminator. Its persisted statuses are
`APPLIES` / `DOES_NOT_APPLY` / `UNDETERMINED` / `CUSTOMER_INPUT_REQUIRED`
(`backend/domain/disclosure.py:124-129`).

**(b) The question actually decomposes into two different propositions** (`P17-DECISION-02 §11.3`):

| Sub-question | Meaning | Outcome |
|---|---|---|
| **Q-11a** | *"Does a framework requirement about Scope 3 category N apply to this organisation/period?"* | Outcome **B** (granularity), compounded by **C** (zero `disclosure_requirement_versions` seeded) |
| **Q-11b** | *"Is Scope 3 category N material/relevant to this organisation's inventory?"* | Outcome **B** — **no owner exists**, because GRG/ESRS materiality is an organisation-specific **judgement** |

**(c) The 15-category matrix is not an applicability model and never was.** Its descriptor is
`architecture_status ∈ {SUPPORTED, PARTIAL, DEFERRED, NOT_IMPLEMENTED}` and every one of the four
legends is a statement about **CarbonTally**, not about the customer (matrix
`architecture_status_legend`, lines 11–16).

**(d) Building a P17 applicability model is already prohibited by ratified reasoning.**
`P17-DECISION-02 §10.4/§12.3` ruled that P17 must not author disclosure vocabulary; `ARCH-01 §42`
lists *applicability assessments* as disclosure-layer; `PQ-3` forbids collapsing the
applicability and materialisation lifecycles.

**(e) The correct future expression, if ever needed, requires zero new model.**
`P17-DECISION-02 §13.3` — author a **requirement** into `disclosure_requirement_versions` that is
genuinely about category N, let `disclosure_applicability_assessments` assess it, let
`derive_effective_class` resolve it, surface it through `disclosure_values` under the existing
`value_status` lifecycle. **Zero new tables, zero new enums, zero new states.**

**(f) The real commercial risk — "zero-emission misrepresentation" — is not solved by
applicability.** `P17-PRODUCT-01 §6/§7` and `POST-ARCH §9` require that *missing data is never
represented as zero*, and `B3 §17` requires *"never a fabricated zero"*. The platform already
answers this with **absence rendered as absence**, a distinct **`UNRESOLVED`** bucket and
`Unresolved %` (`P17-PRODUCT-01` §29 buckets), and the P16 reportability lifecycle that keeps
non-reportable results out of aggregates. A per-category *applicability* claim is **not** what
prevents a fabricated zero; it is a **different, stronger and legally-loaded** claim.

**(g) Category-level transparency is a product requirement; category-level applicability is
not.** `P17-PRODUCT-01 §29` requires category-level transparency and that partial Scope 3
coverage **identify the underlying categories** (citing the UK 2025–26 Sustainability Reporting
Guidance materiality-based approach). Notably, the authoritative product specification contains
**zero** occurrences of "applicab*" (`P17-IMPLEMENT-10 §6.1`).

### 4.3 The three candidate positions, assessed

| Option | Position | Assessment |
|---|---|---|
| **A** | No explicit category applicability model — not even as a future concept | **Rejected as the stated position.** It is too strong: the guidance pattern in (g) shows a **real** future disclosure need for identifying categories in partial coverage. Declaring the concept permanently non-existent would pre-empt a genuine product/reporting decision and would contradict §42's disclosure-layer roadmap |
| **B** | Category applicability is a **future product concept**, but **not required for the current accounting product** | **ADOPTED.** It solves a real future problem at the correct layer (a disclosure *requirement*), while making **no** claim the current product cannot support. It keeps the honest today-behaviour (absence as absence) as the operative risk control |
| **C** | Category applicability **is required now**, as an explicit customer-facing concept | **Rejected for now.** It would (i) require inventing a vocabulary (`AGENTS.md §62`), (ii) make CarbonTally assert an organisation-specific **materiality judgement** it is not positioned to own, and (iii) create a *"does not apply"* claim whose misuse is exactly the zero-emission misrepresentation the platform is built to prevent |

### 4.4 PO-3 decision

> **PO-3 — DECIDED (Option B).** CarbonTally does **not** require a customer-facing Scope 3
> category applicability concept for the current accounting product. Category applicability is a
> **future product concept**, to be expressed — when and if ratified — as a **requirement** in the
> existing Phase 8 Disclosure catalogue, never as a new P17 model.
>
> **Therefore, current product obligations are:**
> 1. P17 must **not** create any applicability table, column, enum or claim. *(Confirms and closes
>    `P17-DECISION-02 §10.4/§12.3` and contradiction **C-5**.)*
> 2. Category truth is expressed **only** through (i) **product capability** (PO-7) and (ii)
>    **result presence / reportability / data-quality** (L4) — never as *"applies / does not
>    apply to you"*.
> 3. Absence of data must continue to render as **absence**, with `UNRESOLVED` and
>    `Unresolved %` visible. A category with no result is **never** `0` and **never**
>    "not applicable".
> 4. The term **"applicability"** is reserved for the Phase 8 disclosure sense
>    (requirement × organisation × period). It must not be re-used for categories.

### 4.5 What PO-3 explicitly does NOT decide (still open — see §17)

* **PO-3-R1** — whether CarbonTally should ever **own** an organisation-specific
  **materiality/relevance** determination (Q-11b). This is a separate future PO decision with
  methodology, liability and consultancy-scope implications. It is **not** decided here.
* **PO-5** — the **L3 data-availability vocabulary** ("measured zero" vs "not measured"). PO-3
  does not supply it; PO-3 only forbids solving it with an applicability claim.

### 4.6 Contradiction closed

| Contradiction | Prior status | Status after PO-3 |
|---|---|---|
| **C-5** — `scope2_method` crosses to disclosure via `scope2_method_hint`, but `scope3_category` has no disclosure counterpart | OPEN (`P17-DECISION-02 §19.1`) | **CLOSED — deliberately not required.** The absence of a Scope 3 category seam is now a *design outcome*, not a gap: no per-category disclosure requirement exists, and none may be invented by P17. If a category disclosure requirement is ever ratified, it is authored in the disclosure catalogue, not wired as a P17→disclosure column. **See §5.4.1** — the seam was additionally mislocated by `P17-DECISION-02 §M-7` at `disclosure_values`; the verified column is `disclosure_requirement_versions.scope2_method_hint` |

---

## 5. PO-7 analysis — how does product capability maturity map to the governed Disclosure vocabulary?

### 5.1 The two vocabularies, verbatim

**P17 internal architecture status** — the 4-value descriptor of the 15-category matrix
(`p17_scope3_category_matrix_20250925.json` → `architecture_status_legend`; mirrored in code as
`backend/domain/scope3.py:65-71`):

| Value | Legend (verbatim, abridged) |
|---|---|
| `SUPPORTED` | *"factor families and an existing calculation path are sufficient to build the category…"* |
| `PARTIAL` | *"factor-supported or structurally derivable but has a boundary, data or deduplication prerequisite…"* |
| `DEFERRED` | *"a ratified decision or external reference data is required before the category can be bounded"* |
| `NOT_IMPLEMENTED` | *"no factor family, no methodology and no data contract exist; the category needs a new input contract and/or new factor set"* |

**Phase 8 / Disclosure governed vocabularies** (`backend/domain/disclosure.py`):

```python
REQUIREMENT_CLASSES = ("REQUIRED", "CONDITIONAL", "OPTIONAL", "NOT_APPLICABLE",
                       "CUSTOMER_INPUT_REQUIRED", "UNDETERMINED", "NOT_SUPPORTED", "FUTURE")   # L47-56

CARBONTALLY_CAPABILITIES = ("SUPPORTED", "PARTIALLY_SUPPORTED", "STRUCTURED_INPUT_REQUIRED",
                            "EXTERNAL_INPUT_REQUIRED", "MISSING_CAPABILITY", "FUTURE",
                            "NOT_APPLICABLE_TO_PRODUCT")                                      # L60-68

APPLICABILITY_STATUSES = ("APPLIES", "DOES_NOT_APPLY", "UNDETERMINED",
                          "CUSTOMER_INPUT_REQUIRED")                                          # L124-129

VALUE_STATUSES = ("PENDING", "RESOLVED", "UNRESOLVED")                                        # L139
```

`CARBONTALLY_CAPABILITIES` is a property of the **requirement version**, described in the module
comment as *"distinct from regulatory applicability and from value materialisation (D12)"*.

### 5.2 The relationship the PO must fix

The two vocabularies describe **different subjects**, and both are authoritative:

| | P17 `architecture_status` | Disclosure `CARBONTALLY_CAPABILITIES` |
|---|---|---|
| Subject | a **Scope 3 accounting category** | a **reporting requirement version** |
| Granularity | category (1–15) | requirement version |
| Owner | P17 architecture / category matrix | Phase 8 Disclosure (`D12`) |
| Persisted? | **No** (deliberately — see §5.4) | yes, on `disclosure_requirement_versions` |
| Customer-facing today? | **No consumer** | **No** (no requirement content seeded; no consumer) |

`P17-DECISION-02 §14.6` established arithmetically that `NOT_IMPLEMENTED` expresses a **product
limitation**, and that the governed expression of a product limitation is `NOT_SUPPORTED` (a
`REQUIREMENT_CLASS`) / `MISSING_CAPABILITY` (a `CARBONTALLY_CAPABILITY`) — never an
`applicability_status`, and never a customer's "not applicable".

### 5.3 The mapping (frozen by this decision)

> **M-1 — internal → governed capability.** A P17 `architecture_status` value is mapped, at the
> boundary, onto the already-governed `CARBONTALLY_CAPABILITIES` vocabulary:

| P17 internal `architecture_status` | Governed capability (`CARBONTALLY_CAPABILITIES`) | Governed requirement class (when a requirement is in play) | Never |
|---|---|---|---|
| `SUPPORTED` | `SUPPORTED` | never a class — a capability statement | never an `effective_class` |
| `PARTIAL` | `PARTIALLY_SUPPORTED` | `UNRESOLVED` with a bounded reason, or `RESOLVED` for the in-scope part | never `REQUIRED` |
| `DEFERRED` | `FUTURE` (if genuinely scheduled / pending a named decision) — otherwise `MISSING_CAPABILITY` | `FUTURE` | never `NOT_APPLICABLE` |
| `NOT_IMPLEMENTED` | `MISSING_CAPABILITY` | `NOT_SUPPORTED` | never `NOT_APPLICABLE`; never `DOES_NOT_APPLY` |

> **M-2 — no new public vocabulary.** The customer/investor-facing status vocabulary is **exactly**
> `CARBONTALLY_CAPABILITIES` (7 values) plus the requirement-class semantics that already resolve
> through `derive_effective_class`. No new token, enum, column or table is introduced.
> `PARTIALLY_SUPPORTED`, `MISSING_CAPABILITY` and `FUTURE` already exist and already carry the
> required meanings.

> **M-3 — no rename of architecture history.** `architecture_status` and its four values stay
> exactly as authored. The P17 matrix is **not** rewritten; its statuses are *mapped at the
> boundary*, never edited in place (`AGENTS.md §4`, `§71`).

> **M-4 — `NOT_IMPLEMENTED` is internal-only.** It is an **architecture/engineering** status and
> must never be (a) surfaced to a customer as a product status, (b) rendered as a requirement
> class, (c) rendered as an applicability outcome, or (d) presented beside a category name
> without its capability mapping.

> **M-5 — `NOT_SUPPORTED` is a requirement class, not a lifecycle.** It is not a
> `value_status`, not a reportability state, and not an applicability status (`PQ-3`; the four
> separate lifecycles must never be merged).

> **M-6 — claim strength is a function of architecture status.** The *strength of product claim*
> CarbonTally may make about a category is derived from its architecture status, and is
> **non-upgradeable**. This rule is **not invented here** — it is the already-ratified
> `status_conditional_acceptance_rule` (`p17_acceptance_matrix_20250925.json`, authority
> `P17-ARCH-06`, findings `ARCH05-01/02/03`), re-expressed for the product/investor surface:

| `architecture_status` | Claim CarbonTally **may** make | Claim **forbidden** | Required evidence (`ARCH-06`) |
|---|---|---|---|
| `SUPPORTED` | *"CarbonTally supports category N"* | a claim beyond the defined acceptance path | full END-TO-END VERIFIED result |
| `PARTIAL` | *"CarbonTally supports category N **within a bounded scope**"* — plus an explicit statement of what is outside scope | any implication of full support; **`PARTIAL` is never presented as `SUPPORTED`** | bounded in-scope result **+** explicit out-of-scope statement |
| `DEFERRED` | *"CarbonTally has **deferred** category N, pending <named decision/prerequisite>"* | presenting deferral as delivery **or** as failure | explicit deferral record naming the blocking decision |
| `NOT_IMPLEMENTED` | *"CarbonTally does **not currently support** category N — it requires <named prerequisite>"* | presenting a not-implemented category as delivered, as "not applicable", or as `0` | explicit not-implemented record naming the missing prerequisite |

### 5.4 A required correction to `P17-DECISION-02 §14.5` (recorded, with evidence)

`P17-DECISION-02 §14.5` asserted that `NOT_IMPLEMENTED` has **"zero occurrences in `backend/`
(excl. `.venv`), `supabase/` or any `docs/architecture/*.md`"**, characterising it as
*"artifact-local, unratified"*. **Re-verification at this baseline does not support that
statement as written.** The verified position is more nuanced, and the nuance is what makes PO-7
a *live* integration concern rather than a documentation-tidiness concern:

| Claim | Verified status at `28999af` | Evidence |
|---|---|---|
| `NOT_IMPLEMENTED` occurs in `backend/` | **FALSE as worded — it occurs 33×** (incl. `backend/domain/scope3.py` 10×, `scope3_contracts.py` 4×, `cams.py` 1×, `core/exceptions.py` 1×, plus tests) | `grep -rn 'NOT_IMPLEMENTED' backend/ --include=*.py` |
| `NOT_IMPLEMENTED` is a **code-resident** token | **TRUE** | `backend/domain/scope3.py:65-71` `class Scope3Status(StrEnum)`; `:251-252` `NOT_IMPLEMENTED_CATEGORIES` |
| `NOT_IMPLEMENTED` is **exposed by the authenticated API** | **TRUE** | `backend/api/v3_scope3.py:230` `"architecture_status": contract.architecture_status`; `backend/api/v3_accounting_context.py:354` |
| `NOT_IMPLEMENTED` is **persisted as a database vocabulary value** | **FALSE — deliberately** | migration `20261012000000_p17d…` L14-18 rationale; `backend/tests/unit/data/test_p17_migrations.py:460-463` asserts all four tokens are absent from the migration |
| `NOT_IMPLEMENTED` is a member of a **governed disclosure vocabulary** | **FALSE** | it is not in `REQUIREMENT_CLASSES`, `CARBONTALLY_CAPABILITIES` or `APPLICABILITY_STATUSES` |

**Corrected statement, adopted as the standing fact:**

> `NOT_IMPLEMENTED` is an **unratified-as-governed, deliberately unpersisted, but
> code-resident and API-exposed** internal architecture status. It is not a database vocabulary
> value (`M-3` and the migration's own rationale keep it out of the schema) and it is not a
> disclosure vocabulary member — **but it is returned to API consumers today as
> `architecture_status`**, which means the conflation risk (`NOT_IMPLEMENTED` read as
> *"not applicable"*) sits on a **live integration boundary**, not merely in a governance file.

**Effect on `P17-DECISION-02`:** its §14.5 token table is superseded by this table; its §14.6
recommendation (`MD-1`) is **strengthened, not weakened**, and is now frozen as `M-1`/`M-4`. Its
verdict was `PARTIAL` for exactly this kind of residual; this correction is recorded rather than
silently absorbed (`AGENTS.md §80`).

### 5.4.1 Verified schema anchor — `carbontally_capability` is **already** a persisted, CHECK-enforced column

The `M-1`/`M-2` mapping is not merely a Python-tuple convention. Re-verification of the B1
disclosure migration shows the governed capability vocabulary is **already a first-class,
database-enforced property of a requirement version**:

| Fact | Evidence |
|---|---|
| `disclosure_requirement_versions.carbontally_capability` is **`NOT NULL`** | `supabase/migrations/20260914000000_p8_b1_disclosure_model_foundation.sql:93-115` |
| It is **CHECK-constrained to exactly the 7 `CARBONTALLY_CAPABILITIES` values** (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `STRUCTURED_INPUT_REQUIRED`, `EXTERNAL_INPUT_REQUIRED`, `MISSING_CAPABILITY`, `FUTURE`, `NOT_APPLICABLE_TO_PRODUCT`) | idem, `CONSTRAINT disclosure_requirement_versions_capability_check` |
| `requirement_class` is likewise CHECK-constrained to exactly the 8 `REQUIREMENT_CLASSES` values | idem, `…_class_check` |
| `scope2_method_hint` is on **`disclosure_requirement_versions`**, not on `disclosure_values` | idem, line 107 + `…_scope2_method_check` |

**Two consequences:**

1. **PO-7 introduces no schema.** The governed capability vocabulary already has a persisted,
   CHECK-enforced home. `M-2` is therefore a *reuse* instruction, not a creation instruction —
   which is exactly why PO-7 can be ratified as a **documentation-only** decision with no
   migration.
2. **A required correction to `P17-DECISION-02` §M-7 (row 1, "Methodology").** That row located the
   disclosure seam at **`disclosure_values.scope2_method_hint`**. Verified: the column is
   **`disclosure_requirement_versions.scope2_method_hint`** — a **requirement-level hint about
   which method a requirement is about**, not a value-level answer. `disclosure_values` does not
   carry a `scope2_method_hint` column. The seam is therefore **catalogue-level, not
   value-level**, and contradiction **C-5** (§4.6) is closed on that corrected basis: P17 supplies
   the method *dimension* on the calculation; the disclosure catalogue's `scope2_method_hint`
   *selects which requirement* is being answered. No P17→value wiring is intended or required.

### 5.5 PO-7 decision

> **PO-7 — DECIDED.** CarbonTally recognises **two distinct, permanently separate status axes**,
> with an explicit, frozen, boundary-only mapping between them:
>
> 1. **Internal architecture status** — P17 `architecture_status`
>    (`SUPPORTED` / `PARTIAL` / `DEFERRED` / `NOT_IMPLEMENTED`). It describes **CarbonTally's
>    engineering maturity for a category**. It is internal. It is not persisted, not a governed
>    vocabulary, and must never be shown to a customer or an investor as a product status.
> 2. **Governed product capability status** — the Phase 8 `CARBONTALLY_CAPABILITIES` vocabulary
>    (`D12`), reached through the `M-1` mapping, and expressed to a requirement as
>    `REQUIREMENT_CLASSES` (`NOT_SUPPORTED` / `FUTURE`) via the existing `derive_effective_class`.
>
> **The customer-facing capability surface may expose exactly the governed
> `CARBONTALLY_CAPABILITIES` vocabulary — all seven values** — and, where a requirement is
> genuinely in play, the `REQUIREMENT_CLASSES` values reached through `derive_effective_class`.
> **No other vocabulary is permitted.** The seven governed capability values, and the question
> each answers, are:
>
> | Governed value | Question it answers | Produced by `M-1` from |
> |---|---|---|
> | `SUPPORTED` | *CarbonTally supports this* | `SUPPORTED` |
> | `PARTIALLY_SUPPORTED` | *CarbonTally supports this within a bounded scope* | `PARTIAL` |
> | `STRUCTURED_INPUT_REQUIRED` | *CarbonTally can do this, but it needs structured input first* | `PARTIAL` (input-prerequisite case) |
> | `EXTERNAL_INPUT_REQUIRED` | *CarbonTally can do this, but it needs an external reference/source first* | `PARTIAL` (external-data case) |
> | `MISSING_CAPABILITY` | *CarbonTally does not currently have this capability* | `NOT_IMPLEMENTED` (and `DEFERRED` where nothing is scheduled) |
> | `FUTURE` | *CarbonTally intends this, but it is not present yet* | `DEFERRED` (genuinely scheduled / pending a named decision) |
> | `NOT_APPLICABLE_TO_PRODUCT` | *This is not a thing the product is the answering party for* | never produced by `M-1` from a category status — it is a **catalogue-authored** statement |
>
> Three points are decisive and must not be lost:
>
> * **`STRUCTURED_INPUT_REQUIRED` and `EXTERNAL_INPUT_REQUIRED` are exactly how PO-9's "what
>   depends on customer data" (§9.3 item 8) is expressed honestly.** Without them, an
>   input-blocked category would be forced into either `MISSING_CAPABILITY` (overstating the
>   product limitation) or `SUPPORTED` (overstating the product). Both would be untruthful.
> * **`NOT_APPLICABLE_TO_PRODUCT` is a *product-capability* statement and is NOT applicability.**
>   It says *"the product is not the party that answers this requirement"* — a statement about
>   CarbonTally. It is **not** a statement about a customer's obligation, and it may never be
>   derived from, or rendered as, `NOT_APPLICABLE` (the `requirement_class`) or a per-tenant
>   applicability outcome. This is the precise vocabulary distinction PO-3 turns on (§4.6, **C-5**).
> * **`NOT_APPLICABLE` as a `requirement_class` is catalogue-level, never tenant-level.** A
>   framework version may classify a *requirement* as `NOT_APPLICABLE` because the framework itself
>   says so; the tenant-level judgement lives only in `disclosure_applicability_assessments`
>   (verified present and empty at runtime — §3.9). PO-7 neither authorises nor forbids a
>   tenant-level class; that remains the disclosure layer's own governance (`D12`).
>
> In particular:
> * `NOT_IMPLEMENTED` is **never** a customer-facing value (`M-4`);
> * `NOT_SUPPORTED` **is** the customer-facing expression of a product limitation for a
>   requirement, and it is **already governed** — it is not introduced here;
> * `PARTIAL` is **not** a customer-facing value — it maps to `PARTIALLY_SUPPORTED`;
> * **no** status may be presented as applicability, and `NOT_APPLICABLE` may never be produced
>   from `MISSING_CAPABILITY` / `NOT_SUPPORTED`.

### 5.6 Contradiction closed

| Contradiction | Prior status | Status after PO-7 |
|---|---|---|
| **C-2** — `NOT_IMPLEMENTED` ↔ `NOT_SUPPORTED` unmapped, so a product limitation could be presented as a regulatory non-applicability | OPEN, **material** (`P17-DECISION-02 §19.2`) | **CLOSED.** The mapping is now frozen (`M-1`…`M-5`), the direction is fixed (internal → governed, never the reverse), the internal token is prohibited from customer surfaces, and the honest refusal path is already implemented (`Scope3CategoryNotSupportedError`, `code = "SCOPE3_CATEGORY_NOT_SUPPORTED"`). No code change is required to *establish* the mapping; an implementation change **is** required to *apply* it at the API boundary (§18) |

---

## 6. PO-9 analysis — what must the investor-facing surface show?

### 6.1 What the investor must be able to understand (task §6)

| # | Required understanding | Is it derivable from authoritative state today? |
|---|---|---|
| 1 | What CarbonTally **supports** | **YES** — mapped capability (`M-1`) + code-resident status |
| 2 | What CarbonTally **calculates** | **YES** — persisted `calculation_snapshots` / `emissions_logs` with `methodology`, `algorithm_version`, `content_hash` |
| 3 | What is **estimated** | **YES** — `data_quality.is_estimated` + persisted `estimation_records` |
| 4 | What is **under review** | **YES** — `reportability_status` lifecycle (`P16R5`) + processing/workflow state |
| 5 | What has **evidence** | **YES** — `evidence_coverage` / `EVIDENCE_COMPLETENESS_STATES` (`COMPLETE`/`PARTIAL`/`UNAVAILABLE`) |
| 6 | What **methodology/factor** was used | **YES** — `methodology`, `scope2_method`, `scope3_category`, `factor_id`, `factor_source`, `factor_kind` |
| 7 | What remains **unsupported** | **YES** — mapped capability (`MISSING_CAPABILITY` / `NOT_SUPPORTED`) |
| 8 | What depends on **customer data** | **YES** — `CUSTOMER_INPUT_REQUIRED` / `STRUCTURED_INPUT_REQUIRED` / `EXTERNAL_INPUT_REQUIRED` semantics, and the contract's required-input lists |
| 9 | What belongs to **disclosure/reporting requirements** | **YES** — the disclosure layer's own vocabulary, kept separate (`M-5`) |

**Conclusion:** every one of the nine investor requirements is satisfiable from **already-governed
or already-persisted** state. **No new vocabulary is needed for the investor surface** — which is
the decisive finding for PO-9.

### 6.2 The decisive constraint

`P17-DECISION-01 §14.4` and `-02 §15.3` established that a **per-organisation, per-category**
*coverage/applicability* claim is prohibited while L2/L3 are undecided. PO-3 has now decided L2's
answer (no applicability concept) and PO-7 has decided L1's expression. Therefore the investor
surface may legitimately present:

* **capability** (per category, mapped), and
* **result presence and quality** (per category, from persisted state),

and may **not** present applicability, materiality, or a "covered / not covered" claim that
implies either.

### 6.3 PO-9 decision

> **PO-9 — DECIDED.** The investor-facing CarbonTally product surface **may** exist and is
> **frozen as a *capability + result-presence* surface**, subject to the following contract.
>
> **It MUST show**, for the scope under demonstration:
> 1. **Capability** per Scope 3 category — expressed **only** through the `M-1` mapping into the
>    governed `CARBONTALLY_CAPABILITIES` vocabulary (all seven values; see §5.5 for what each one
>    asserts), explicitly labelled as **"CarbonTally capability"**, never as applicability.
>    Where a category's limitation is an **input** limitation, the governed value is
>    `STRUCTURED_INPUT_REQUIRED` / `EXTERNAL_INPUT_REQUIRED` — not `MISSING_CAPABILITY` and not
>    `SUPPORTED`.
> 2. **Calculation availability** — derived from persisted results, not from the architecture status.
> 3. **Methodology** — the persisted `methodology`, `scope2_method` / `scope3_category`, and factor
>    provenance (`factor_id`, `factor_source`, `factor_kind`) for any result shown.
> 4. **Estimation transparency** — an estimate is labelled an estimate, with its persisted basis.
> 5. **Review state** — what is under review / not reportable, using the **existing** reportability
>    lifecycle.
> 6. **Evidence** — the evidence-coverage state, and the provenance chain where it exists.
> 7. **Unsupported capability** — stated plainly, per category, in governed vocabulary.
> 8. **Data dependency** — where a category is blocked on customer/external input, say so.
> 9. **Disclosure separation** — disclosure/reporting requirements are presented as a **separate**
>    concern; a missing disclosure value is never rendered as an emissions fact, and vice versa.
>
> **It MUST NOT:**
> * display `NOT_IMPLEMENTED`, `PARTIAL`, `DEFERRED` or `SUPPORTED` (internal architecture values)
>   as a product or investor status (`M-4`);
> * claim that CarbonTally **determines applicability**, marks a category **not applicable**, or
>   assesses **materiality** (PO-3);
> * claim *"all 15 Scope 3 categories"* or imply that factor count equals Scope 3 coverage
>   (`P14-RECON-01 §6` contract consequence);
> * present a category with no result as `0`, or as "not applicable" — absence renders as absence;
> * present an estimate as measured data;
> * show a fabricated or manually-authored number that has no `calculation_snapshot`;
> * show a report that was not generated from real persisted calculations (`P14-RECON-01 §10`);
> * show Scope 2 as complete merely because electricity factors exist (`P14-RECON-01 §5`).

### 6.4 Contradiction closed

| Contradiction | Prior status | Status after PO-9 |
|---|---|---|
| **C-8** — the applicability model has a full API and no consumer, so its correct (non-conflating) behaviour is incidental rather than enforced; the first UI built could re-introduce the conflation | OPEN, **medium** (`P17-DECISION-02 §19.1`) | **CLOSED AS A CONTRACT.** The permitted and prohibited claims are now frozen above and in §8/§9/§12, and the internal→governed boundary is fixed by `M-1`…`M-5`. **Residual implementation risk remains** and is listed in §18: the API currently emits `architecture_status` verbatim (`v3_scope3.py:230`), so the boundary mapping must be applied by whichever surface is built first. That is an *implementation* obligation now, not an undecided contract |

---

## 7. Product capability model

### 7.1 The frozen model (five facts, never merged)

`P17-DECISION-01 §14.2` froze that five facts must never be collapsed. This decision supplies the
missing **expression** for the first of them and confirms the rest:

| # | Fact | Question | Expression (frozen) | Status |
|---|---|---|---|---|
| 1 | **Taxonomy** | Does category N exist in the GHG Protocol vocabulary? | `scope3_categories` (15 reference rows) | exists; reference data only |
| 2 | **Product capability** | Does CarbonTally support category N? | P17 `architecture_status` (internal) → **mapped** to `CARBONTALLY_CAPABILITIES` (governed) | **frozen by PO-7** |
| 3 | **Customer applicability** | Does category N apply to this organisation? | **no expression — deliberately** (Phase 8 disclosure applicability covers *requirements*, at framework-version granularity) | **frozen by PO-3** |
| 4 | **Customer data status** | Has the organisation provided data? | derivation from persisted facts; **no ratified state name** | **PO-5 — still open** |
| 5 | **Accounting status** | Is the result calculated / reviewed / reportable? | `reportability_status` lifecycle (`P16R5`) | authoritative; exists |

### 7.2 The capability expression rule

* **Internally**, engineering maturity may be described with the 4-value `architecture_status`
  (API field `architecture_status`, governance matrix).
* **Externally** (customer, consultant, investor), capability is expressed with
  `CARBONTALLY_CAPABILITIES` reached through `M-1`.
* The mapping is **one-directional**: internal → governed. No governed vocabulary value may be
  written back into P17 `architecture_status`, and `architecture_status` may never be *persisted*
  as a product state (`M-3`, migration rationale).

### 7.3 The refusal principle (already implemented — confirm, do not rebuild)

An architecture-limited category must **refuse loudly** rather than invent a number:
`assert_calculable` (`domain/scope3.py:305-323`) and `Scope3CategoryNotSupportedError`
(`code = "SCOPE3_CATEGORY_NOT_SUPPORTED"`). Where a **bounded, honest** route exists it is one of
the contract pathways — `ACTIVITY_FACTOR`, `ESTIMATION` (mandatory persisted `EstimationRecord`),
or `MANUAL_REVIEW` (a controlled clarification naming the missing inputs) — and
`scope3_contracts.py` states explicitly that *"No number is invented"*. PO-7 does **not** change
this behaviour; it fixes the **vocabulary** used when the behaviour is reported. The governed
capability value for a `NOT_IMPLEMENTED` category is `MISSING_CAPABILITY` with requirement-class
expression `NOT_SUPPORTED`; for a `DEFERRED` category it is `FUTURE` (class `FUTURE`) — the two are
**never** conflated (`M-1`, §11.2).

---

## 8. Customer truth model

### 8.1 The six questions a customer / consultant must be able to answer

Per `AGENTS.md §76` and `P17-DECISION-01 §14`, the customer-facing truth surface must let a
customer, and their consultant operating their workspace, answer:

| # | Question | Frozen expression | Notes |
|---|---|---|---|
| 1 | **What can CarbonTally do for me?** | governed capability per category (`M-1`/`M-6`) | never applicability; never `NOT_IMPLEMENTED` |
| 2 | **What have I got results for?** | persisted results only (`calculation_snapshots` / `emissions_logs`) | derived from data, not from capability |
| 3 | **How was each number derived?** | `methodology`, `scope2_method` / `scope3_category`, factor provenance (`factor_id`, `factor_source`, `factor_kind`), `content_hash` | the provenance chain is mandatory |
| 4 | **Is this measured, estimated, or missing?** | `is_estimated` + persisted `EstimationRecord`; **missing = `UNRESOLVED`** | `PO-5` still owns the *name* of the "no data supplied" state |
| 5 | **What has evidence?** | evidence-coverage state (`COMPLETE` / `PARTIAL` / `UNAVAILABLE`) | never infer coverage from uploads |
| 6 | **What is outstanding / who acts next?** | validation issues + workflow/reportability state | the blocking-issue lifecycle is authoritative |

### 8.2 The zero-misrepresentation rules (frozen)

> **C-1.** A category with **no result** renders as **absence** — it is never `0`, never
> `0.00 kg CO₂e`, and never "not applicable". `UNRESOLVED` and `Unresolved %` must remain visible
> whenever part of an inventory is unresolved (`P17-PRODUCT-01 §29`; `B3 §17`; `POST-ARCH §9`).

> **C-2.** An **estimate** is labelled an estimate at the point of display, and carries its
> persisted basis. It is never presented as measured data (`no_silent_estimation_rule`).

> **C-3.** A category's **capability** and its **result presence** are displayed as **two separate
> facts**. A supported category with no data must not look like an unsupported category, and an
> unsupported category must not look like a category with no emissions.

> **C-4.** **No customer-facing claim of applicability, materiality, or "not relevant to you"**
> may be produced (PO-3). The term *applicability* does not appear on a customer emissions surface
> in the category sense.

> **C-5.** A **refused** calculation is surfaced as a refusal with its governed code
> (`SCOPE3_CATEGORY_NOT_SUPPORTED`) and the missing prerequisite — never as a silent zero and never
> as a generic error.

### 8.3 Scope 2 truth for customers (frozen)

| Fact | Customer expression |
|---|---|
| Method is **mandatory** on every Scope 2 result | a Scope 2 number is always attributable to `LOCATION_BASED` or `MARKET_BASED`; a Scope 2 result without a method is **refused at persistence** (`accounting_dimensions.py:215-221`; `domain/scope2.py:138-144` — *"the method is never inferred"*) |
| Method is **never inferred** | the UI may not default, guess, or carry forward a method |
| Market-based is **not** implemented as an engine | only the **disclosure vocabulary** (`SCOPE2_METHODS`) and the requirement-level `scope2_method_hint` exist. A market-based Scope 2 total must **not** be claimed (contract consequence of `P14-RECON-01 §5`; `D-10`) |
| Factor presence ≠ Scope 2 coverage | electricity factors existing in the library is **not** evidence that Scope 2 is complete |

### 8.4 What the customer surface must never show

* the internal tokens `NOT_IMPLEMENTED`, `PARTIAL`, `DEFERRED`, `architecture_status`;
* an emissions figure without a `calculation_snapshot`;
* a report not generated from persisted calculations;
* a "coverage %" that silently treats missing data as zero;
* any derived claim about what the customer is *required* to report (that is the disclosure
  layer's job and is separately governed).

---

## 9. Investor truth model

### 9.1 The investor acceptance principle (frozen)

> **The investor demo must not overstate the product.** Every claim on an investor-facing surface
> must be **materially true of the current product**, and the surface must be capable of stating
> what is **real, verified, partial, deferred, not implemented, and dependent on customer data**.
> An investor must never be left with a claim the product cannot support, and CarbonTally must never
> present a *blocked* or *deferred* outcome as *delivery*.

This re-states, for the investor surface, the already-ratified non-upgrade clause of
`ARCH-06` (`non_upgrade_clause`): *"A PARTIAL category is never required to produce a full E2E
claim"* — and, symmetrically, is **never allowed to be presented as though it had**.

### 9.2 The four truth levels the investor surface must keep distinct

`P17-DECISION-01 §14.3` separated four levels. The investor surface must keep them distinct,
because each has a different evidence standard:

| Level | Question | Authority | What the investor may be shown | What is forbidden |
|---|---|---|---|---|
| **L1 — Capability** | *Can the product do it?* | architecture status → `M-1` mapping → `CARBONTALLY_CAPABILITIES` | the **mapped** governed value, plus the bounded scope statement for `PARTIAL` | raw `architecture_status`; `NOT_IMPLEMENTED` presented as a product status; capability read as applicability |
| **L2 — Applicability** | *Does this requirement apply to this organisation?* | Phase 8 disclosure applicability (requirement × org × period) | nothing, per-organisation, in a demo of product capability | any per-category applicability claim (PO-3); any materiality claim |
| **L3 — Data availability** | *Has the org supplied data?* | derivation from persisted facts | **presence of persisted results**, i.e. "results exist / do not exist yet" | naming a "no data" state with an unratified token (`PO-5` open); implying absence = zero |
| **L4 — Result state** | *What is the result's quality/reportability?* | `reportability_status` + `is_estimated` + evidence coverage | review state, estimate labelling, evidence coverage | showing a non-reportable result as final; showing an estimate as measured |

### 9.3 Required investor claims (frozen)

The investor surface, when it speaks about Scope 2 / Scope 3 capability and results, **must** be
able to state all nine of §6.1 — and must make the following statements explicitly available:

1. **What is supported** — per category, in governed vocabulary, with bounded-scope wording for
   `PARTIAL` and a named prerequisite for anything not supported.
2. **What is actually calculated and persisted** — Scope 1 and Scope 2 location-based calculation
   with persisted snapshots; Scope 3 **only** on the pathways that really exist.
3. **What is estimated** — explicitly labelled, with its persisted basis.
4. **What is under review / not reportable** — using the existing lifecycle.
5. **What has evidence** and what does not.
6. **Which methodology and factor were used** for any result shown.
7. **What is unsupported** — stated plainly.
8. **What depends on customer data** — stated plainly.
9. **That disclosure/regulatory requirements are a separately-governed concern** — never conflated
   with emissions arithmetic.

### 9.4 Prohibited investor claims (frozen)

> **Forbidden, without exception, on any investor-facing surface:**
>
> 1. *"All 15 Scope 3 categories are supported."* — Verified status rollup is
>    `SUPPORTED` **[3, 4, 5, 6]** (`4` of 15), `PARTIAL` **[1, 7, 8, 9, 12, 13]**,
>    `DEFERRED` **[11, 14, 15]**, `NOT_IMPLEMENTED` **[2, 10]**.
> 2. *"4,090 Scope 3 factors means Scope 3 coverage."* Factor count is **not** category coverage
>    (`structural_finding`: categories 4/9, 5/12 and 8/13 *share factor families outright*).
> 3. *"CarbonTally determines which reporting requirements apply to you"* — PO-3; that is the
>    disclosure layer and is not activated.
> 4. *"Market-based Scope 2 is supported"* — no engine exists (`D-10`).
> 5. *"Scope 2 is complete"* because electricity factors exist.
> 6. Any report, total or dashboard produced from non-persisted or manually-authored numbers.
> 7. Any category shown as `0` when it is merely unmeasured.
> 8. Any `NOT_IMPLEMENTED`/`DEFERRED` category presented as delivered.
> 9. Any treated-as-`SUPPORTED` presentation of a `PARTIAL` category (non-upgrade clause).
> 10. Any statement that a demo dataset's investor-demo organisation is a real customer.

### 9.5 The investor acceptance test (frozen, deterministic)

For every category 1–15, the investor surface **passes** only if all of the following hold:

| Test | Condition |
|---|---|
| **IT-1** | the capability shown for category N equals the `M-1` mapping of its authoritative `architecture_status` |
| **IT-2** | no raw `architecture_status` token is displayed |
| **IT-3** | the claim strength matches `M-6` (full / bounded / deferred / not-implemented wording) |
| **IT-4** | if a result is shown, it resolves to a real persisted calculation snapshot with provenance |
| **IT-5** | if the category is `NOT_IMPLEMENTED` or `DEFERRED`, **no** result is shown and the prerequisite is named |
| **IT-6** | no applicability, materiality or "not applicable" wording appears (PO-3) |
| **IT-7** | missing data is not rendered as `0` |
| **IT-8** | estimates are labelled and carry their persisted basis |
| **IT-9** | the disclosure/reporting layer is visually and semantically **separate** from emissions results |

A surface that fails **IT-2**, **IT-4**, **IT-5**, **IT-6** or **IT-7** is **not acceptable for
investor use**, irrespective of how it looks.

---

## 10. Scope 2 truth matrix

### 10.1 The Scope 2 authority set

Scope 2 is governed by `p17_acceptance_matrix_20250925.json → scope2_minimum_acceptance`
(items **S2-01 … S2-15**), read together with `P17-DECISION-02 §14.4` (method is mandatory, never
inferred) and `P14-RECON-01 §5` (market-based must not be claimed on the strength of disclosure
vocabulary alone). This decision adds and removes **no** Scope 2 requirement; it fixes the
**truth** attached to each.

### 10.2 What the matrix recorded versus what is verified now

The S2 rows were authored at the P17 architecture baseline. Two of them have **moved since**, by
implementation now present in source — and neither move may be reported as more than it is
(`AGENTS.md §73`, `§74`):

| # | Requirement | Matrix `architecture_status` | Verified at `28999af` — source | Verified at runtime (§3.9) |
|---|---|---|---|---|
| **S2-01** | location-based calculation | `READY_TO_BUILD` (*"NOT IMPLEMENTED"* at that baseline) | **implemented as a service**: `backend/services/scope2_calculation.py` (IMPLEMENT-05) — an orchestrator over the canonical `CalculationEngine.calculate()` path composing `domain.scope2` + Phase 4 `MatchResult`. **No second engine, no second persistence system** | **not runnable against the demo DB** — `calculation_snapshots.scope2_method` absent |
| **S2-02** | market-based calculation | `READY_TO_BUILD` (*"NOT IMPLEMENTED"*) | **implemented as a path**: `domain.scope2` instrument-eligibility rules + `domain.contractual_instruments` (DC-09 over-allocation guard); a market-based request is **never silently downgraded** to location-based (`scope2_calculation.py:22-27`) | **not runnable** — `contractual_instruments` absent |
| **S2-03** | both methods persisted independently | `REQUIRES_SCHEMA_DELTA_P17A` | **authored**: `20261010000000_p17a…` adds `scope2_method` to `calculation_snapshots` **and** `emissions_logs`, with `…_scope2_method_check` **and** `…_scope2_method_required` (`scope <> 'Scope 2' OR scope2_method IS NOT NULL`), plus per-method indexes | **not applied** |
| **S2-04** | factor-year enforcement | `PARTIAL_GAP_IDENTIFIED` | unchanged by this decision; matrix records enforcement **on the natural-key/pipeline path** with **4 call sites** still able to cross a year | not independently re-verified here |
| **S2-05** | contractual instrument registration | `REQUIRES_NEW_ENTITY` | **entity now exists in source**: `public.contractual_instruments` (`20261011000000_p17c…`) — tenant key `organization_id`, instrument type/identifier/issuer/geography, generation period, vintage year, quantity+unit, validity window, retirement status, `evidence_item_id` | **absent** |
| **S2-06** | contractual instrument validation | `REQUIRES_NEW_ENTITY` | **present in source**: `domain/contractual_instruments` + `instrument_allocations` carrying a **composite FK** `(instrument_id, organization_id)` → `contractual_instruments(id, organization_id)`, making a cross-tenant allocation **structurally impossible** rather than merely policy-denied | **absent** |
| **S2-07** | evidence / provenance | `REUSE_EXISTING` | machinery exists (`evidence_line_items`, snapshots, `content_hash`); *"UNEXERCISED FOR SCOPE 2"* still holds | no Scope 2 evidence rows to observe |
| **S2-08** | manual review path | `REUSE_EXISTING` | implemented (activity clarifications + adjudication lifecycle); P17-A adds `resolved_scope2_method` to `activity_clarifications` so a **reviewer** can resolve the method explicitly | **not applied** → `resolved_scope2_method` absent |
| **S2-09** | supplier / provider attribution | `REUSE_AND_EXTEND` | implemented (`supplier_id` propagated on the live waste path) | unchanged |
| **S2-10** | reportability lifecycle | `REUSE_EXISTING` | implemented (P16-RD-4 classification) | unchanged |
| **S2-11** | idempotent calculation | `REUSE_EXISTING` | implemented (deterministic request id + `uq_calc_snapshots_request_id`) | unchanged |
| **S2-12** | tenant isolation | `REUSE_EXISTING` | implemented (RLS + `ensure_org_access` + route guards) | unchanged |
| **S2-13** | reporting distinction between methods | `REQUIRES_SCHEMA_DELTA_P17A` | the disclosure **vocabulary** exists (`SCOPE2_METHODS`; `disclosure_requirement_versions.scope2_method_hint` — verified at runtime) and the accounting dimension is now **authored** in P17-A across four tables | requirement-version catalogue **empty** (0 rows); `scope2_method` columns **absent** |
| **S2-14** | no silent fallback | `PARTIAL_GAP_IDENTIFIED` | unchanged: year gap at 4 call sites; **no residual-mix data** in the factor library | not independently re-verified |
| **S2-15** | independent verification | `PROCESS_REQUIRED` | **P17-J gate — still outstanding.** No Scope 2 end-to-end result has been independently verified, and this documentation decision verifies none | — |

### 10.3 The Scope 2 claim boundary (frozen)

> **SC-1. Method is part of a Scope 2 result's identity, not its metadata.** A Scope 2 figure is
> shown *as* `LOCATION_BASED` or *as* `MARKET_BASED`, never bare. A Scope 2 result without a method
> is **refused at persistence**; a surface may therefore never render a method-less Scope 2 total.

> **SC-2. The method is never inferred, defaulted or carried forward** — not by the engine, not by a
> surface, not by a reviewer's convenience. A surface that guesses a method has made an accounting
> claim that is not CarbonTally's to make.

> **SC-3. Location-based and market-based are never summed, netted or reconciled into one figure.**
> They are different accounting claims, not two views of one number
> (`scope2_calculation.py:22-24`).

> **SC-4. Market-based may be described as "supported" only where the contractual-instrument
> pathway is actually available.** As verified in §3.9, on the demo database it is **not** — P17-C
> is unapplied. Until it is applied *and* exercised, the honest governed expression for a
> market-based requirement is `EXTERNAL_INPUT_REQUIRED` or `MISSING_CAPABILITY`, **never**
> `SUPPORTED`.

> **SC-5. Factor presence is not Scope 2 coverage.** Electricity factors existing in the library is
> not evidence that Scope 2 is complete (`S2-07`, `S2-14` remain open).

> **SC-6. Routing is part of the claim.** A well-to-tank / fuel-and-energy line misrouted into
> Scope 2 instead of category 3 is a **claim defect** (DC-02). A Scope 2 total must not be presented
> as WTT-inclusive unless that routing rule is in force.

---

## 11. Scope 3 category truth matrix (1–15)

### 11.1 The authority and the rollup

Statuses are the **verified rollup** of
`p17_scope3_category_matrix_20250925.json` (`status_rollup`; mirrored in code at
`backend/domain/scope3.py:65-71`). The rollup is **not** uniform and must never be presented as such:

```text
SUPPORTED        [3, 4, 5, 6]              →  4 of 15
PARTIAL          [1, 7, 8, 9, 12, 13]      →  6 of 15
DEFERRED         [11, 14, 15]              →  3 of 15
NOT_IMPLEMENTED  [2, 10]                   →  2 of 15
```

**Structural finding, preserved verbatim as a claim constraint:** factor families are **shared**
across 4/9, 5/12 and 8/13. Therefore **factor count is not category coverage**, and a category may
never be presented as supported because a sibling category's factors exist.

### 11.2 The matrix (frozen)

For each category: the internal status, its `M-1` governed expression, the **strongest** claim
`M-6` permits, what is forbidden, and what actually blocks it.

| # | Category | `architecture_status` | Governed capability | Strongest permitted claim (`M-6`) | Forbidden | Blocking prerequisite (`prerequisite_work`) |
|---|---|---|---|---|---|---|
| **1** | Purchased Goods and Services | `PARTIAL` | `PARTIALLY_SUPPORTED` / `STRUCTURED_INPUT_REQUIRED` | *"supported within a bounded scope"* — with the scope stated explicitly | any spend-based coverage claim **before** the spend-based authorisation decision; implying all category-1 activity is covered | canonical category dimension (P17-D); **PO decision on spend-based authorisation**; explicit methodology recording for spend-based lines |
| **2** | Capital Goods | `NOT_IMPLEMENTED` | `MISSING_CAPABILITY` (class `NOT_SUPPORTED`) | *"not currently supported — requires &lt;named prerequisite&gt;"* | any coverage claim; any "not applicable" wording; any `0` | capital-goods methodology decision (supplier figure vs spend-based vs new factor set); category 1↔2 exclusion control; asset-level attribution dimension |
| **3** | Fuel- and Energy-Related Activities Not Included in Scope 1 or 2 | `SUPPORTED` | `SUPPORTED` | *"CarbonTally supports category 3"* | a claim beyond the defined acceptance path | category 3 → source snapshot derivation link with a uniqueness constraint (DC-02) |
| **4** | Upstream Transportation and Distribution | `SUPPORTED` | `SUPPORTED` | *"CarbonTally supports category 4"* | conflating upstream with downstream (4 and 9 **share factor families**) | explicit upstream/downstream boundary property on the activity (DC-04); mode controlled vocabulary |
| **5** | Waste Generated in Operations | `SUPPORTED` | `SUPPORTED` | *"CarbonTally supports category 5"* | claiming disclosure/reporting end-to-end for the waste slice | category dimension on the waste path (P17-D); reporting/disclosure E2E for the waste slice |
| **6** | Business Travel | `SUPPORTED` | `SUPPORTED` | *"CarbonTally supports category 6"* | letting WTT variants sit in category 6 instead of category 3 (DC-02) | WTT-vs-direct routing rule so WTT variants land in category 3 (DC-02) |
| **7** | Employee Commuting | `PARTIAL` | `PARTIALLY_SUPPORTED` / `STRUCTURED_INPUT_REQUIRED` | *"supported within a bounded scope"*; estimated lines labelled as estimates | presenting average-data estimates as measured; **estimating at all before the authorisation decision** | estimation-record entity/contract (P17-H); **PO decision on whether average-data commuting estimates are authorised at all** |
| **8** | Upstream Leased Assets | `PARTIAL` | `PARTIALLY_SUPPORTED` | *"supported within a bounded scope"* | double-counting leased assets against Scope 1/2 without the consolidation dimension; conflating with category 13 (8 and 13 **share factor families**) | organisation-level consolidation approach dimension (P17-H boundary work); DC-07 duplication detector |
| **9** | Downstream Transportation and Distribution | `PARTIAL` | `PARTIALLY_SUPPORTED` | *"supported within a bounded scope"* | conflating downstream with upstream (4 and 9 **share factor families**); claiming the whole outbound boundary | boundary property + DC-04 detector; **PO decision: which element of outbound logistics is in scope for the first delivery** |
| **10** | Processing of Sold Products | `NOT_IMPLEMENTED` | `MISSING_CAPABILITY` (class `NOT_SUPPORTED`) | *"not currently supported — requires &lt;named prerequisite&gt;"* | any coverage claim; any `0`; any "not applicable" wording | processing factor/methodology decision; processor-declaration input contract; sold-product entity; DC-03 (1 vs 2 vs 10) exclusion |
| **11** | Use of Sold Products | `DEFERRED` | `FUTURE` | *"deferred, pending &lt;named decision/prerequisite&gt;"* | presenting the deferral as delivery **or** as failure; estimating use-phase without an authorised methodology | **PO decision to authorise a bounded use-phase methodology and which product types are in scope**; assumption-set entity; sold-product entity |
| **12** | End-of-Life Treatment of Sold Products | `PARTIAL` | `PARTIALLY_SUPPORTED` / `STRUCTURED_INPUT_REQUIRED` | *"supported within a bounded scope"*; treatment-mix assumptions labelled | presenting a treatment-mix assumption as measured data; double-counting against category 5 (5 and 12 **share factor families**) | waste-origin property + DC-05 detector; sold-product entity; treatment-mix assumption record |
| **13** | Downstream Leased Assets | `PARTIAL` | `PARTIALLY_SUPPORTED` | *"supported within a bounded scope"* | conflating with category 8 (8 and 13 **share factor families**); claiming a lease direction that has not been established | lease-direction property + DC-07 detector; consolidation approach dimension |
| **14** | Franchises | `DEFERRED` | `FUTURE` | *"deferred, pending &lt;named decision/prerequisite&gt;"* | presenting the deferral as delivery **or** as failure; assuming franchisees are tenants | **PO decision on the franchise operating model and whether franchisees are tenants or external parties**; franchise entity; allocation-basis contract |
| **15** | Investments | `DEFERRED` | `FUTURE` | *"deferred, pending &lt;named decision/prerequisite&gt;"* | claiming a PCAF-aligned result; claiming equity-share attribution before ratification | **PO decision ratifying the bounded `attribution_equity_share` methodology and explicitly deferring PCAF**; investment entity; investee data-sharing authorisation model; lag-handling decision |

### 11.3 Scope 3 claim rules (frozen)

> **S3-1. The rollup is shown in full and never aggregated into optimism.** The product surface may
> never say *"all 15 categories supported"* or *"15 categories"* unqualified. The four-way split
> (4 / 6 / 3 / 2) is the honest expression.

> **S3-2. Non-upgrade is absolute.** A `PARTIAL` category is never presented as `SUPPORTED`
> (`ARCH-06 non_upgrade_clause`, `M-6`). This applies to wording, colour, ordering, iconography and
> any implied completeness.

> **S3-3. `NOT_IMPLEMENTED` and `DEFERRED` categories show no result.** They show the governed
> capability value **and** the named prerequisite. A category with no result never renders `0`.

> **S3-4. No applicability, materiality or "not applicable" wording, ever (PO-3).** Where the honest
> statement is *"the product is not the answering party"*, the governed value is
> `NOT_APPLICABLE_TO_PRODUCT` — a **capability** statement. It must never be rendered as, or
> derived from, a tenant applicability outcome.

> **S3-5. Absence renders as absence.** Unmeasured ≠ zero ≠ not applicable. (The customer-visible
> *name* of the absence state is **PO-5, still open** — §17 — so no surface may invent one.)

> **S3-6. Factor count is never coverage.** Because factor families are shared across 4/9, 5/12 and
> 8/13, no claim may link a factor count to category support (`P14-RECON-01 §6`).

> **S3-7. A status may only be *raised* by a ratified architecture decision, never by a UI
> decision.** No frontend, report or demo configuration may promote a category. The mapping is
> internal → governed, one-directional (`M-3`).

> **S3-8. Where a category is blocked on a PO decision, it is unavailable until that decision
> exists.** Seven such decisions are open (§17.2) covering categories 1, 2, 7, 9, 11, 14 and 15.
> Presenting any of those capabilities as available before the decision is a misrepresentation.

---

## 12. `NOT_SUPPORTED` semantics and the four independent lifecycles

### 12.1 The four lifecycles that must never be merged

`PQ-3` (ratified, `CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md`) separated four
concepts that are frequently, and wrongly, collapsed into one "status". Verified at runtime
(§3.9) and in source, each is a **distinct field with a distinct vocabulary and a distinct owner**:

| Lifecycle | Field | Vocabulary | Answers | Owned by |
|---|---|---|---|---|
| **Applicability** | `disclosure_applicability_assessments.applicability_status` | `APPLIES`, `DOES_NOT_APPLY`, `UNDETERMINED`, `CUSTOMER_INPUT_REQUIRED` | *is this requirement in play for this tenant / period?* | the **tenant's** disclosure assessment (`D12`, `APPL`) |
| **Requirement class** | `disclosure_requirement_versions.requirement_class` (and `…_effective_class`) | the 8-value set (§3.9) | *what kind of requirement is this, per the framework / catalogue?* | the **catalogue** |
| **Product capability** | `disclosure_requirement_versions.carbontally_capability` | the 7-value set (§3.9, §5.5) | *can CarbonTally produce it?* | **CarbonTally** |
| **Materialisation** | `disclosure_values.value_status` | `PENDING`, `RESOLVED`, `UNRESOLVED` | *has a value actually been materialised?* | the **pipeline** |

> **PQ-3 is explicit:** `value_status` *"must NOT duplicate or reinterpret `requirement_class`,
> applicability, `carbontally_capability` or `UNDETERMINED`"*. The four previously-overlapping
> values are **runtime-rejected** by CHECK on `value_status` (23514). **`effective_class` ≠
> `value_status`.**

### 12.2 The derived outcome, verified

`backend/domain/disclosure_projection.py:246-269` — precedence is
**applicability → capability → requirement class**, and it is **test-locked**:

```python
if applicability_status == "DOES_NOT_APPLY":        return "NOT_APPLICABLE"
if applicability_status == "UNDETERMINED":          return "UNDETERMINED"
if applicability_status == "CUSTOMER_INPUT_REQUIRED": return "CUSTOMER_INPUT_REQUIRED"
if carbontally_capability in UNSUPPORTED_CAPABILITIES:
    return "FUTURE" if carbontally_capability == "FUTURE" else "NOT_SUPPORTED"
return requirement_class
```

with (`disclosure_projection.py:91-99`):

* `UNSUPPORTED_CAPABILITIES = ("MISSING_CAPABILITY", "NOT_APPLICABLE_TO_PRODUCT", "FUTURE")`
* `UNSUPPORTED_REQUIREMENT_CLASSES = ("NOT_SUPPORTED", "FUTURE")`

**Two consequences of the exact code — both decisive for PO-3 and PO-7:**

1. **A product-capability statement can never become a tenant applicability outcome.** Because
   `NOT_APPLICABLE_TO_PRODUCT` is *not* an applicability status and *does* derive to
   `NOT_SUPPORTED` (never to `NOT_APPLICABLE`), the engine **structurally cannot** render *"the
   product is not the answering party"* as *"this does not apply to you"*. This is the
   code-level proof of the §5.5 vocabulary distinction and of **C-5**'s closure.
2. **`STRUCTURED_INPUT_REQUIRED` and `EXTERNAL_INPUT_REQUIRED` are deliberately absent from
   `UNSUPPORTED_CAPABILITIES`.** They therefore fall through to `requirement_class` — i.e. the
   requirement remains **expected**, and the value's availability depends on inputs. That is
   precisely how PO-9's *"what depends on customer data"* (§9.3 item 8) is expressed without
   either under-claiming (calling it `MISSING_CAPABILITY`) or over-claiming (calling it
   `SUPPORTED`).

### 12.3 `NOT_SUPPORTED` — the six semantics (frozen)

> **NS-1. `NOT_SUPPORTED` is a statement about the product, never about the customer's
> obligation.** *"Not supported by CarbonTally"* (`_reason_for_effective_class`) means *CarbonTally
> cannot produce this*. It is **never** *"you are not required to report this"*. A surface that
> shows `NOT_SUPPORTED` in a context where a customer could read it as a compliance conclusion has
> made a legal-adjacent claim the product is not entitled to make (`APPL`, `D13` — *never legal
> advice*).

> **NS-2. `NOT_SUPPORTED` ≠ `CUSTOMER_INPUT_REQUIRED`, and the two are never conflated.**
> A ratified decision (`B3-D6`, `DM-5`): they produce **distinct, non-conflatable reasons** —
> *"not supported by CarbonTally"* vs *"customer input required"*. Merging them destroys the only
> distinction that tells a customer *why* a number is absent and *who* can fix it.

> **NS-3. `NOT_SUPPORTED` ≠ `NOT_APPLICABLE`.** See §12.2 consequence 1: the derivation cannot
> produce the latter from the former, and no surface may simulate it.

> **NS-4. `NOT_SUPPORTED` / `FUTURE` / `NOT_APPLICABLE` / `UNDETERMINED` materialise no value —
> and never `0`.** `decide_projection` treats all four as non-producible; empty authoritative rows
> yield `UNRESOLVED`, **never zero** (`B3 honesty rules`). Showing `0 tCO₂e` for any of these is a
> **fabricated measurement**.

> **NS-5. `NOT_SUPPORTED` is surfaced, never silently satisfied.** Finalisation gates on unresolved
> `REQUIRED`; a `NOT_SUPPORTED` item is **displayed as unsupported, not presented as complete**
> (`DM-5`). The same applies to the investor surface: it appears in the honest capability list, not
> in a "done" column.

> **NS-6. Both the requirement-class and the product-capability statement are shown where they
> differ.** For a `NOT_IMPLEMENTED` category the governed pair is
> (`carbontally_capability = MISSING_CAPABILITY`, `effective_class = NOT_SUPPORTED`). Showing only
> one of the two is an incomplete claim; showing `NOT_SUPPORTED` alone invites NS-1's
> misreading.

> **NS-7. The vocabularies are closed and CHECK-enforced.** No surface may introduce a synonym —
> not "N/A", not "—", not "coming soon", not "0 tCO₂e", not "not measured", not "excluded". Any
> value outside the governed sets (§3.9) is a **vocabulary escape** and therefore a claim defect.
> The customer-visible *name* of the absence state remains **PO-5, open** (§17.1).

---

## 13. Internal status vs external vocabulary

### 13.1 The two axes, precisely characterised

| | **Axis A — internal engineering status** | **Axis B — governed product vocabulary** |
|---|---|---|
| **Values** | `SUPPORTED`, `PARTIAL`, `DEFERRED`, `NOT_IMPLEMENTED` | 7 × `CARBONTALLY_CAPABILITIES` + 8 × `REQUIREMENT_CLASSES` (CHECK-enforced) |
| **Resident at** | `backend/domain/scope3.py:65-71` (code constant only) | `backend/domain/disclosure.py:60-68` (`CARBONTALLY_CAPABILITIES`) and `:47-56` (`REQUIREMENT_CLASSES`); DB CHECK on `disclosure_requirement_versions` |
| **Persisted?** | **No** — verified by full-`public`-schema scan: no column of this name exists (§3.9). Non-persistence is **deliberate and enforced by a test** (`test_p17_migrations.py:460-463`) | **Yes** — `NOT NULL` columns on a real, migrated table |
| **Crosses the API?** | **Yes** — `v3_scope3.py:230` exposes it as `architecture_status`; `v3_accounting_context.py:354` likewise. This corrects `P17-DECISION-02 §14.5`'s *"grep = 0"* claim, which is **stale** | **Yes** — and it is the axis that carries governed meaning |
| **Authority** | engineering truth about **our** code | governed truth about **the product**, safe to show a customer |
| **Consumer** | internal engineering / QA / roadmap | customer, consultant, investor-facing surfaces |

### 13.2 Blast radius — where each axis may appear

| Surface | Axis A (`architecture_status`) | Axis B (governed vocabulary) |
|---|---|---|
| Internal architecture docs, backlog, QA evidence, engineering reports | **permitted, expected** | permitted |
| Internal API responses consumed by CarbonTally-internal tooling | **permitted** (its current state) | permitted |
| Internal operations UI | **permitted with explicit internal labelling** | permitted |
| **Customer workspace** | **FORBIDDEN** | **REQUIRED** |
| **Consultant workspace (client-facing view)** | **FORBIDDEN** | **REQUIRED** |
| **PE workspace** | **FORBIDDEN** | **REQUIRED** (where a capability statement is in scope) |
| **Investor / due-diligence surface** | **FORBIDDEN** | **REQUIRED** — and additionally constrained by §9/§15 |
| Reports, exports, disclosure artefacts | **FORBIDDEN** | **REQUIRED** |

> Axis A may cross an API — it already does — but **crossing an API is not authorisation to render
> it**. An internal field reaching a browser that renders it to a customer is the same defect as a
> leaked column, and is governed by the same rule (`AGENTS.md §44`: the frontend is never the
> security boundary; equally, internal vocabulary is never customer vocabulary).

### 13.3 The boundary, as one law

`M-1` … `M-6` (§5.2) reduce to a single **one-directional law**:

> **Internal status → governed vocabulary is permitted and required. Governed vocabulary →
> internal status is forbidden.** Nothing in a customer-, consultant-, PE- or investor-facing
> surface may be back-derived into an `architecture_status`, into a roadmap position, or into a
> delivery commitment. The mapping is a *presentation of truth*, not a *source of truth*.

### 13.4 Vocabulary rules (frozen)

> **IV-1. Axis A is never rendered outside internal surfaces.** No customer/investor artefact may
> contain the strings `PARTIAL`, `DEFERRED` or `NOT_IMPLEMENTED` as a *status*. (`SUPPORTED` is
> shared by both axes and is safe **only** in its Axis-B sense.)

> **IV-2. Axis B values are quoted verbatim, never paraphrased.** The governed value is the claim.
> Human-readable explanation may accompany it; it may not replace it.

> **IV-3. The mapping is applied per statement, not per surface.** A surface may not adopt one
> mapping and then drift for individual rows.

> **IV-4. Where Axis B cannot express something honestly, the surface says less — never more.** If
> no governed value fits, the correct output is a **narrower** statement or **no statement**, never
> a bespoke one (IV-2, NS-7).

> **IV-5. `M-1`'s mapping is not a licence to upgrade.** `PARTIAL` → `PARTIALLY_SUPPORTED` is not an
> upgrade; `MISSING_CAPABILITY`/`FUTURE` are truthful *limitations* and must be rendered as
> plainly as a strength (`M-6`).

> **IV-6. Adding a governed value requires a decision at the disclosure layer, not the P17 layer.**
> The vocabularies are `D12`'s; PO-7 reuses them unchanged and does **not** own them.

---

## 14. Customer surface vs investor surface

Both surfaces speak **Axis B** (§13). They differ in **audience, scope and obligation** — never in
the truth of an individual value.

### 14.1 What each surface is for

| | **Customer surface** | **Investor surface** |
|---|---|---|
| **Audience** | a customer organisation's Owner/Admin/Member/Viewer; consultants acting for a client | investor / due-diligence reader |
| **Scope** | **one tenant** (`organization_id`), one reporting period | **product-level** capability, plus result *presence* |
| **Purpose** | *"what does my data support, what is missing, why, and what do I do?"* (§8's six questions) | *"what can this product actually do, and is there real output behind the claim?"* |
| **Carries tenant emissions data?** | **yes** — scoped to the caller's authorised tenant(s) | **no** — see CS-1 |
| **Carries applicability/materiality conclusions?** | **no** (PO-3) — applicability is Phase 8 | **no** (PO-3, PO-9) |
| **Carries roadmap/commitments?** | only as governed `FUTURE` text with a named decision | only as governed `FUTURE` text with a named decision |
| **Fails closed on?** | tenant isolation (CS-4) | unsupported claims (CS-3) |

### 14.2 Customer-surface obligations

> **CT-1. Every absent number is explained.** A missing category, a missing method or a missing
> Scope 2/3 slice is accompanied by the governed capability value **and** the reason class
> (`MISSING_CAPABILITY` + `NOT_SUPPORTED`; `STRUCTURED_INPUT_REQUIRED`; `CUSTOMER_INPUT_REQUIRED`;
> `FUTURE`). A bare gap is not acceptable (§8 C-3).

> **CT-2. The customer is never shown a compliance conclusion.** No "you are not required", no
> "exempt", no "not material". Applicability is Phase 8 (`PO-3`), and *never legal advice*
> (`APPL`/`D13`).

> **CT-3. The customer's actions are distinguished from CarbonTally's limitations.** Where the
> blocker is the customer's own data, the surface says so (`CUSTOMER_INPUT_REQUIRED` /
> `STRUCTURED_INPUT_REQUIRED` / `EXTERNAL_INPUT_REQUIRED`); where it is the product's, it says that
> (`MISSING_CAPABILITY`, `NOT_SUPPORTED`). Conflating them is `NS-2`'s defect.

> **CT-4. The customer sees their own truth at full fidelity** — their factor provenance, their
> snapshots, their evidence. `M-6`'s limitations govern what CarbonTally *claims*; they do not
> censor what the customer's own data says.

### 14.3 Investor-surface obligations

> **IN-1. Capability and result-presence only.** All nine §9.3 items are either **capability**
> statements or **presence** statements — *"this exists / does not exist / is deferred"* — never
> quantity, coverage, applicability or materiality claims.

> **IN-2. Real, reproducible, sourced examples only.** Any illustrated result comes from persisted
> data with provenance; a mocked or hand-typed figure is forbidden (§9.5, IT-4).

> **IN-3. The limitation column is as prominent as the capability column.** A governing
> presentational rule, not a preference (§9.5, IT-5).

> **IN-4. No roadmap commitment beyond `FUTURE` with a named decision.** No dates, no "next
> quarter", no implied delivery (§7.4).

### 14.4 The single-truth rules (frozen)

> **CS-1. No tenant data on the investor surface.** No organisation name, no facility, no
> per-tenant figure, no tenant-identifying aggregate, absent explicit documented consent. Investor
> content is **product-level**.

> **CS-2. The same governed value is shown to both surfaces.** A capability value **may not differ**
> between the customer surface and the investor surface. Composition, ordering and emphasis may
> differ; **the value may not**. Two surfaces asserting different capability values is a truth
> defect, not a presentation choice.

> **CS-3. The investor surface fails closed.** Where a §9.3 item cannot be truthfully satisfied,
> the surface shows *less*, and the gap is recorded — never filled with a stronger claim.

> **CS-4. The customer surface fails closed on tenancy.** Any doubt about authorisation yields
> denial, per `AGENTS.md §44`/`§67`. Capability vocabulary never travels across a tenant boundary
> as data.

> **CS-5. Neither surface may be the other's input.** The investor surface is not generated from
> tenant data, and customer-facing behaviour is not configured by investor-facing content. They
> share **vocabulary and mapping**, not state.

---

## 15. Commercial consequences

This section records what the frozen contract **enables and forbids commercially**. It makes **no
pricing, packaging or contractual commitment** — those are PO decisions (`§62`).

### 15.1 The commercial asset this decision protects

CarbonTally's differentiator is not the *number* — competitors produce numbers. It is the
**traceable chain** that lets a customer, an auditor and an investor each check the claim:
source → extraction → factor → validation → snapshot → evidence → approval → report
(`AGENTS.md §17`, `§27`). A capability claim that overstates is not a marketing win — it is an
asset being spent. Therefore:

* **`MISSING_CAPABILITY` and `FUTURE` are commercially safe to state.** They are proofs of
  measurement discipline. A prospect who sees 4/6/3/2 and a named prerequisite learns that
  CarbonTally's `SUPPORTED` means something.
* **A single overstated category is disproportionately corrosive**, because it invites the reader
  to doubt the chain everywhere. The mapping therefore has **no discretionary tier** (`M-2`,
  `M-3`).

### 15.2 What may be sold *today*, as stated

| Product statement | Permitted today? | Basis |
|---|---|---|
| *"CarbonTally processes and calculates Scope 1, Scope 2 and Scope 3 categories 3–6"* | **Yes** | `SUPPORTED` = categories 3, 4, 5, 6 (`§11.2`); Scope 1/2 via the canonical engine; **Scope 2 method must be stated with any Scope 2 figure** (`SC-1`) |
| *"Supports Scope 2 location-based and market-based"* | **Not as stated** | market-based is `EXTERNAL_INPUT_REQUIRED`/`MISSING_CAPABILITY` on the demo runtime until P17-C is applied and exercised (`SC-4`) |
| *"Scope 3 categories 1, 7, 8, 9, 12, 13 — supported within a bounded scope"* | **Yes, with the boundary stated** | `PARTIALLY_SUPPORTED` (`§11.2`) |
| *"Categories 2 and 10 — not supported, prerequisite: X"* | **Yes** | `MISSING_CAPABILITY` + `NOT_SUPPORTED` is the honest and *stronger* statement (`IN-3`) |
| *"Categories 11, 14, 15 — deferred, pending <named decision>"* | **Yes** | `FUTURE` + named decision (`IN-4`) |
| *"15 categories supported"* | **No** | `S3-1` |
| *"Customers can determine which categories apply to them"* | **No** | PO-3: no applicability concept customer-facing |
| Any of the seven PO-blocked categories (1, 2, 7, 9, 11, 14, 15) presented as *available* | **No** | `S3-8` |

### 15.3 Commercial reads (not commitments)

1. **The two-axis model (§13) is itself sellable.** A competitor cannot copy a governed mapping
   quickly, because the mapping is only credible if the underlying chain is real. The separation of
   *"what we can do"* from *"what your framework requires"* is a genuine product position in a
   market full of over-claims.
2. **`STRUCTURED_INPUT_REQUIRED` / `EXTERNAL_INPUT_REQUIRED` are onboarding conversations, not
   losses.** They name exactly what the customer must supply — turning a vague "not available"
   into a scoped, billable data-onboarding step.
3. **The investor surface, honestly built, is a due-diligence accelerator** — it answers
   *"is there real output?"* with reproducible evidence (`IN-2`) rather than assertion.
4. **The deferral of applicability (PO-3) removes a liability.** The product currently makes **no**
   applicability statement; that is defensible and it is reversible later at catalogue level (§4.6).

### 15.4 Commercial constraints that follow (frozen)

> **CM-1. No sales artefact may use an `architecture_status`** (`IV-1`). The internal/external
> split applies to pitch decks, proposals and marketing pages exactly as it applies to product UI.

> **CM-2. No sales artefact may present a capability value differently from the product.** `CS-2`
> binds the deck as much as the screen.

> **CM-3. No roadmap date may be implied from `FUTURE`.** (`IN-4`)

> **CM-4. Nothing in this decision authorises a commercial claim about price, packaging, SLAs,
> guarantees, assurance or verification.** Those remain PO decisions and are explicitly **not**
> decided here.

---

## 16. Decisions frozen by this artifact

### 16.1 PO-3 — Scope 3 category applicability

| | |
|---|---|
| **Status** | **DECIDED — Option B** |
| **Decision** | **No customer-facing Scope 3 category applicability model is introduced now.** The product holds **no** per-category applicability concept, no applicability vocabulary, and no applicability surface. *"Applicability"* is **reserved** for the disclosure layer (`L2`), to be expressed — if and when Phase 8 requires it — as a **requirement** in `disclosure_requirement_versions`, i.e. **zero new model** (§4.6). |
| **Why Option B** | The governed seam already exists (`disclosure_requirement_versions` + `disclosure_applicability_assessments`, 15 tables, applied and empty — §3.9). A parallel category-level applicability model would be a **duplicate tenant abstraction** (`AGENTS.md §4`, `§66`) for a question no source currently requires answering. |
| **Absence semantics (frozen)** | A category with no result renders as **absence**. Absence is never `0`, never "0 tCO₂e", never "not applicable", never "excluded", never a blank. (`S3-5`, `NS-4`, `NS-7`) |
| **Contradiction closed** | **C-5** — the contradiction between a category-status enum and a customer-facing applicability reading is removed by refusing to create the latter. |
| **Reversibility** | Fully reversible at **catalogue** level (a requirement row), with **no** schema change, no new table and no new UI contract. |
| **Explicitly NOT decided** | The customer-visible *name* of the absence state (**PO-5, open**); any per-method applicability (**PO-6** → resolved in substance, §17.1). |

### 16.2 PO-7 — Product capability status ↔ governed disclosure vocabulary

| | |
|---|---|
| **Status** | **DECIDED** |
| **Decision** | The two vocabularies are **permanently separate**, joined by a **boundary-only, one-directional, non-upgrading** mapping `M-1`…`M-6` (§5.2): internal `architecture_status` (`SUPPORTED`/`PARTIAL`/`DEFERRED`/`NOT_IMPLEMENTED`) → governed `carbontally_capability` (7 CHECK-enforced values) + `requirement_class` (8 values), reached through `derive_effective_class`. |
| **Zero new vocabulary, zero new schema** | The governed column is `NOT NULL` with a CHECK on a **migrated** table (§3.9). No new table, column, migration, API or enum is introduced. |
| **Solved by reuse, not by unification** | Unification was rejected: both vocabularies are separately authoritative (`AGENTS.md §62`), and one is *engineering* truth while the other is *governed product* truth (§13.1). |
| **Non-upgrade is absolute** | `M-6` + `S3-2` + `IV-5`: a limitation is rendered as plainly as a strength; no surface, report or deck may promote a value. |
| **Contradiction closed** | **C-2** — the `MISSING_CAPABILITY` vs `NOT_IMPLEMENTED` conflict is resolved by making one map into the other, documented and test-anchored, instead of each silently shadowing the other. |
| **Corrections delivered** | `P17-DECISION-02 §14.5` (*"grep = 0"*) is **stale**: `NOT_IMPLEMENTED` **is** code-resident (`scope3.py:65-71`) and **does** cross the authenticated API (`v3_scope3.py:230`; `v3_accounting_context.py:354`), while being **deliberately non-persisted** (verified: no such column anywhere — §3.9; test-locked by `test_p17_migrations.py:460-463`). |

### 16.3 PO-9 — Investor truth surface

| | |
|---|---|
| **Status** | **DECIDED** |
| **Decision** | The investor surface is frozen as a **capability + result-presence** surface: the nine MUST-show items (§9.3) and the ten-item MUST-NOT list (§9.4), from a **reproducible, provenance-carrying** data path (§9.5 `IT-4`). It makes **no** applicability, materiality, coverage, completeness or assurance claim, and shows **no** tenant data (`CS-1`). |
| **Vocabulary** | **Axis B only** (`IV-1`); the same values as the customer surface (`CS-2`). |
| **Contradiction closed** | **C-8** — closed **as a contract**. Residual *implementation* risk (that the contract is met in practice) is recorded in §18 and is **not** claimed as verified here. |
| **Fails closed** | `CS-3`: an unsatisfiable item yields *less* content plus a recorded gap — never a stronger claim. |
| **Explicitly NOT decided** | Any commercial commitment (`CM-4`); the investor-demo *scope* remains gated by the §18 prerequisites. |

### 16.4 Net effect on the PO register

| | Before this artifact | After |
|---|---|---|
| Open | PO-1 … PO-9 (nine) | **PO-1, PO-2, PO-5, PO-8 confirmed open; PO-3, PO-7, PO-9 decided; PO-4, PO-6 resolved in substance** (§17.1) |

**No decision in this artifact changes an existing ratified decision** — `PQ-3`, `DM-5`, `B3-D6`,
`D12`, `D13`, `APPL`, the `L1`–`L4` separation, or the four-axis model. Two corrections to
`P17-DECISION-02` (§5.4) repair a *descriptive* claim; they do not alter `DECISION-02`'s decisions.

---

## 17. Decisions still open

### 17.1 The PO-1 … PO-9 register after this artifact

| ID | Question | Status after this artifact | Blocked work |
|---|---|---|---|
| **PO-1** | The organization capability **control list** (which named controls exist) | **OPEN — untouched** | capability UI; capability-gated behaviour |
| **PO-2** | The capability **storage representation** (sibling table vs extend `manual_processing_grants` vs new policy table) | **OPEN — untouched** (P17-0 gate item 9) | all of PO-1's implementation |
| **PO-3** | Scope 3 category applicability model | **DECIDED — Option B (§16.1)** | closed |
| **PO-4** | How the product-capability gap is represented to (or hidden from) a customer | **RESOLVED IN SUBSTANCE by PO-7** — the outward rule is now fully specified: the governed capability value **and** the requirement class are shown, explicitly labelled as a **CarbonTally capability**, never as applicability (`§13.2`, `§14.2 CT-1/CT-3`, `NS-1`/`NS-6`); the internal `architecture_status` is **forbidden** outside internal surfaces (`IV-1`). PO **confirmation is requested only for formal closure** | customer-facing category listing |
| **PO-5** | The **data-availability vocabulary** — may an organisation distinguish *"we measured zero"* from *"we have not measured"*, and under what ratified state names? (`NO_DATA_YET` / `EXCLUDED_WITH_REASON` are **not** ratified) | **OPEN — and deliberately left open.** This artifact constrains the *behaviour* (absence ≠ zero ≠ not-applicable, `S3-5`/`NS-4`/`NS-7`) without inventing the *name* | `L3`; Scope 3 investor reporting; any "no data" state label |
| **PO-6** | Scope 2 **method-level applicability** beyond the presence rule | **RESOLVED IN SUBSTANCE by PO-3** — no per-method applicability state is introduced: the method is a **result dimension** (`SC-1`), not an applicability concept, and PO-3 introduces no customer-facing applicability at all. PO confirmation requested only for formal closure | Scope 2 view design |
| **PO-7** | Reconciliation of the two product-capability vocabularies | **DECIDED (§16.2)** | closed |
| **PO-8** | Does `modelled` report as its own data-quality bucket? | **OPEN — untouched** | data-quality reporting presentation |
| **PO-9** | Whether a per-organization category-coverage surface may exist in the investor demo, and under what truthful wording | **DECIDED (§16.3)** — the *wording* is frozen; the *scope* remains gated by §18 | closed on contract; implementation gated |

**Six remain open: PO-1, PO-2, PO-5, PO-8** (four genuinely open) plus **PO-4 and PO-6** awaiting
**formal PO closure only** (their substance is now determined). None of these was decided by an
implementer (`AGENTS.md §62`).

### 17.2 The seven category-level PO decisions this artifact surfaces

The verified `prerequisite_work` of the category matrix records **seven further PO decisions**,
each of which gates a specific category. They are **not** raised by this artifact and **not**
resolved by it, but they must be visible, because `S3-8` forbids presenting any of these
categories as available before the decision exists:

| Category | Decision required | Category's status today |
|---|---|---|
| **1** Purchased Goods and Services | whether **spend-based** authorisation is granted | `PARTIAL` — spend-based path unavailable |
| **2** Capital Goods | the capital-goods **methodology** (supplier figure vs spend-based vs a new factor set) | `NOT_IMPLEMENTED` |
| **7** Employee Commuting | whether **average-data commuting estimates** are authorised at all | `PARTIAL` — estimation unavailable |
| **9** Downstream Transportation and Distribution | **which element of outbound logistics** is in scope for the first delivery | `PARTIAL` |
| **11** Use of Sold Products | whether a **bounded use-phase methodology** is authorised, and which product types | `DEFERRED` |
| **14** Franchises | the **franchise operating model** — are franchisees tenants or external parties? | `DEFERRED` |
| **15** Investments | ratifying the bounded **`attribution_equity_share`** methodology and **explicitly deferring PCAF** | `DEFERRED` |

### 17.3 Non-PO prerequisites (implementation, not policy)

These are **not** PO decisions and are not resolved here; they are the concrete engineering state
this artifact's §18 depends on. All four are **verified**, not assumed:

| # | Prerequisite | Verified state |
|---|---|---|
| **PR-1** | **The P17 schema deltas are applied to the environment that will host the customer/investor surfaces.** `20261010000000_p17a…`, `20261011000000_p17c…`, `20261012000000_p17d…`, `20261013000000_p17h…` and `20261014000000_p17_10…` are the **only** P17 migration files present in `supabase/migrations` (there is no `p17b`/`p17e`/`p17f`/`p17g` file; the lettering is sparse by design, and the gap implies **no** outstanding work item) | **NOT APPLIED to the demo database.** Verified absent: `calculation_snapshots.scope2_method`, `.scope3_category`, `.scope3_method`, `.transaction_provider`; `contractual_instruments`; `instrument_allocations`; `estimation_records` (§3.9) |
| **PR-2** | **The governed requirement catalogue is authored** — at least one `disclosure_requirement_versions` row per capability claim the product wishes to make | **EMPTY — 0 rows** (§3.9). The governed *shape* exists; the governed *content* does not |
| **PR-3** | **`P17-J` independent verification of the Scope 2 end-to-end path** (`S2-15`, matrix `PROCESS_REQUIRED`) | **OUTSTANDING.** This documentation decision verifies no runtime result and must not be read as doing so |
| **PR-4** | **An environment whose migration state is tracked** for any claim about *which* P17 deltas are present (`supabase_migrations.schema_migrations` does not exist in the demo database — §3.9) | Outstanding; the §3.9 evidence was therefore established by **direct schema inspection**, which is the stronger check |

---

## 18. Implementation consequences

This artifact changes **no** code, schema, migration, API, RLS policy or UI. The consequences below
are the obligations it creates for work that follows.

### 18.1 Tiered consequences

**Tier 0 — no new code, enforceable immediately (documentation/behavioural):**

1. Any surface that already renders a category or capability status must use **Axis B** only
   (`IV-1`, `§13.2`). The internal `architecture_status` that already crosses the API
   (`v3_scope3.py:230`, `v3_accounting_context.py:354`) must not be rendered outside internal
   surfaces.
2. **Absence is rendered as absence** — never `0`, never "0 tCO₂e", never "not applicable", never
   a bare blank (`S3-5`, `NS-4`, `NS-7`).
3. The full four-way rollup (**4 / 6 / 3 / 2**) is used wherever the category set is summarised
   (`S3-1`).
4. Sales and marketing artefacts are bound by `CM-1`…`CM-4` exactly as product UI is.

**Tier 1 — prerequisite for any governed claim with runtime backing (PR-1):**

5. Apply `p17a`, `p17c`, `p17d`, `p17h`, `p17_10` to the environment hosting the surfaces, under
   the existing deployment gate (outstanding migrations are a **deployment** gate, not a
   development one). Re-run the §3.9 checks afterwards and record the result.
6. Do **not** invent a parallel column, table or enum to satisfy a P17 dimension that P17-A/C/D/H
   already author (`AGENTS.md §66`).

**Tier 2 — prerequisite for a *backed* capability claim (PR-2):**

7. Author `disclosure_requirement_versions` rows so the 15 categories (and any Scope 1/2
   requirement) have a persisted governed capability value. This is a **disclosure-layer /
   catalogue** task and is **out of scope** here. Until it is done, a capability value shown on a
   surface is a governed-*shaped* statement whose catalogue home is empty.

**Tier 3 — the surfaces themselves (gated):**

8. **Customer capability surface** — per §8 and §14.2. Gated by PO-5 (the absence-state *name*)
   for any UI that needs to label a "no data" state; not gated on anything else in this artifact.
9. **Investor surface** — per §9, §11.3, §14.3–§14.4. Gated by `PR-1`, `PR-2` and `IN-2`
   (a reproducible, provenance-carrying data path). Must not be built on mocked figures.
10. **Scope 2 work** — any Scope 2 figure must carry its method (`SC-1`); market-based may not be
    claimed `SUPPORTED` until P17-C is applied **and** exercised (`SC-4`).

### 18.2 Forbidden implementations (each one a re-opened decision)

| # | Forbidden | Re-opens |
|---|---|---|
| **F-1** | A customer-facing Scope 3 category **applicability** model, vocabulary, per-category state enum, or subset-membership flag | **PO-3** (§16.1) |
| **F-2** | A **new** capability vocabulary, enum, status column or "coverage" field to express product capability | **PO-7** (§16.2) |
| **F-3** | Rendering an `architecture_status` (`PARTIAL`/`DEFERRED`/`NOT_IMPLEMENTED`) on a customer, consultant, PE, investor, report or export surface | **PO-7**, `IV-1` |
| **F-4** | Deriving an `architecture_status` **from** a governed value (reverse mapping) | `§13.3` |
| **F-5** | Presenting a capability value on a surface differently from the governed value, or differently between surfaces | `CS-2`, `CM-2` |
| **F-6** | Rendering `0`/`0 tCO₂e`/`N/A`/`—`/a blank for an absent, unsupported, deferred or undetermined item | **PO-3**, `S3-3`, `NS-4`, `NS-7` |
| **F-7** | Any tenant-identifying data, figure or aggregate on the investor surface | `CS-1` |
| **F-8** | A coverage, completeness, materiality, applicability or assurance **claim** on the investor surface | **PO-9** (§16.3) |
| **F-9** | Promoting, ordering or colouring a category so that a limitation reads as a strength | `M-6`, `S3-2`, `IV-5` |
| **F-10** | Adding a second calculation/persistence path for Scope 2 or Scope 3 to satisfy a surface | `AGENTS.md §6`, `§25`; `S2-01` |

### 18.3 Acceptance gates for any future capability surface

Deterministic and checkable — not a review opinion:

| # | Gate | Check |
|---|---|---|
| **AG-1** | Every capability value rendered is a member of the governed CSV — the **7 × `M-1`** or the **`REQUIREMENT_CLASSES`** reached via `derive_effective_class` | value-set assertion against `disclosure.py` constants |
| **AG-2** | Every absent, unsupported, deferred or undetermined item carries a reason class / governed value — including `NOT_SUPPORTED` and `CUSTOMER_INPUT_REQUIRED` as **distinct** outcomes | per-state test, both branches (`NS-2`) |
| **AG-3** | No Axis-A token is rendered on any non-internal surface | string scan for `PARTIAL`, `DEFERRED`, `NOT_IMPLEMENTED` used as a status |
| **AG-4** | No `0`, `0 tCO₂e`, `N/A`, `—`, `not applicable`, `excluded`, `coming soon` appears for a non-produced item | negative tests, one per state (both surfaces) |
| **AG-5** | The investor surface contains **no** tenant identifier and issues **no** tenant-table query | route/query audit + identifier scan |
| **AG-6** | The same requirement shows the **same** value on both surfaces | cross-surface equality test (`CS-2`) |
| **AG-7** | The four-way rollup is shown, not a total | summary assertion (`S3-1`) |
| **AG-8** | Any illustrated result on the investor surface resolves to persisted data with provenance | provenance-chain check (`IN-2`) |

Failure of `AG-2`, `AG-3`, `AG-4`, `AG-5` or `AG-6` is a **claim or security defect**, not a
polish item.

### 18.4 Explicit non-changes

This artifact does **not** change, and must not be cited as changing:

* any **schema**, table, column, constraint, index or **migration** (none added, altered or removed);
* any **RLS policy** or **authorization** rule;
* any **API** route, response shape or OpenAPI contract;
* any **UI** component, route or vocabulary;
* any **emissions factor**, calculation rule, snapshot semantics or provenance field;
* any **demo data** — the §3.9 verification was `SELECT`-only and touched nothing;
* any **decision** in `P17-DECISION-01` or `P17-DECISION-02` (the two §5.4 corrections repair a
  *descriptive* claim — `§14.5`'s `grep = 0` and `§M-7`'s seam location — and leave every decision
  intact);
* any **`P14-RECON-*`** finding or any `ARCH-*` decision.

---

## 19. Security and tenancy consequences

### 19.1 No new surface and no new authorization is created

This artifact authorises **no** endpoint, route, policy or grant. It adds no principal, no role, no
capability and no RLS change. Any surface built under it must therefore obtain its authorization
from the **existing** model — authenticated identity, organisation membership,
consultant/client relationship, PE assignment, and RLS — with server-side enforcement in every
case (`AGENTS.md §7`, `§44`).

### 19.2 The investor surface may not become a tenant-data path

> **SEC-1. The investor surface is product-level and tenant-free.** It must not read tenant tables,
> must not aggregate tenant data, and must not receive tenant identifiers. If it is ever served by
> an API, that endpoint must be safe to serve **without** any tenant context — i.e. it must be
> derived from governed **catalogue** and product-level facts only.

> **SEC-2. No service-role shortcut.** A service-role or RLS-bypassing path must not be introduced
> to make the investor surface convenient. `AGENTS.md §67` permits elevated access only where
> explicitly authorised and documented; this artifact authorises none.

> **SEC-3. Absence of a tenant identifier is a weaker guarantee than absence of a tenant query.**
> `AG-5` therefore checks the *query path*, not only the rendered output.

### 19.3 The customer surface inherits isolation unchanged

The governed capability vocabulary is **product-level metadata**; the **values** it describes are
per-tenant and remain RLS-protected. The `M-1` mapping is a **presentation** mapping and creates
**no** new data path: it changes how a status is *rendered*, never what a caller may *read*.

> **SEC-4. Capability vocabulary must not become a cross-tenant channel.** Because a requirement
> version row is shared catalogue data, a surface must never attach tenant-specific state to a
> shared row in a way that is visible to another tenant. Tenant state belongs on tenant-scoped
> rows (`disclosure_applicability_assessments`, `disclosure_values`) — which is exactly why PO-3
> refused to create a per-category applicability field (§16.1).

### 19.4 The isolation tests this decision makes relevant

The standing negative matrix (`AGENTS.md §45`) applies unchanged, **plus two new ones** created by
this decision:

| # | Boundary | Expected | Rule |
|---|---|---|---|
| 1 | Customer A → Customer B | **DENY** | §45 |
| 2 | Consultant A → Consultant B | **DENY** | §45 |
| 3 | Consultant A → Consultant B's client | **DENY** | §45 |
| 4 | PE A → PE B | **DENY** | §45 |
| 5 | PE → prohibited customer document | **DENY** | §45 |
| 6 | Viewer → prohibited write | **DENY** | §45 |
| 7 | Customer/PE → internal operations | **DENY** | §45 |
| **8** | **Investor surface → any tenant data** | **DENY / IMPOSSIBLE** | **`SEC-1`, `SEC-3`, `CS-1`, `F-7`** |
| **9** | **Any non-internal surface → Axis A vocabulary** | **ABSENT** | **`IV-1`, `F-3`, `AG-3`** |

Every unexpected **ALLOW** on rows 8–9 is a **serious finding** in the same sense as rows 1–7.

### 19.5 Verification integrity and handling rules

* The §3.9 database verification was **`SELECT`-only**. No row, column, table, index, policy or
  migration was created, altered or deleted; the demo dataset was not modified (`AGENTS.md §55`).
* **No secrets are recorded in this artifact**: no credentials, JWTs, API keys, signed URLs,
  connection strings, or demo passwords. The database and container names appear only as
  environment identification.
* **No signed URL, storage path or token** is quoted anywhere in this document.
* Nothing in this artifact weakens authentication. MFA remains optional in development and a
  separate production policy decision (`AGENTS.md §69`).

> **SEC-5. Fail closed.** Where a surface cannot establish authorisation, or cannot establish that
> a value is governed, it shows **less** — or nothing — and records the gap. It never shows a
> fallback value, a default, an inferred method or an invented state.

---

## 20. Final verdict

### 20.1 Decision verdicts

| Decision | Verdict | Frozen in |
|---|---|---|
| **PO-3** — Scope 3 category applicability | **DECIDED — Option B**: no customer-facing applicability concept now; future expression is a requirement in `disclosure_requirement_versions` (zero new model); absence is never `0` and never "not applicable" | §16.1 |
| **PO-7** — Product capability status ↔ governed disclosure vocabulary | **DECIDED**: two permanently separate axes, joined by the boundary-only, one-directional, non-upgrading mapping `M-1`…`M-6`; **zero new vocabulary, zero new schema** | §16.2 |
| **PO-9** — Investor truth surface | **DECIDED**: capability + result-presence surface with nine MUST-show items and an explicit MUST-NOT list; no applicability/materiality/coverage claim; no tenant data | §16.3 |
| PO-4 | **RESOLVED IN SUBSTANCE** by PO-7 — PO confirmation requested for formal closure only | §17.1 |
| PO-6 | **RESOLVED IN SUBSTANCE** by PO-3 — PO confirmation requested for formal closure only | §17.1 |
| PO-1, PO-2, PO-5, PO-8 | **OPEN — untouched** (PO-5 deliberately: the absence-state *name* is not invented here) | §17.1 |
| Seven category-level PO decisions (cat. 1, 2, 7, 9, 11, 14, 15) | **OPEN — surfaced, not decided** | §17.2 |

> ## **FINAL VERDICT: `P17_DECISION_COMPLETE`**
>
> All three decisions in scope — **PO-3, PO-7 and PO-9** — are **materially and fully decided**.
> No sub-part of any of the three is left undecided by an implementer, and no question has been
> deferred to code. The remaining open items (**PO-1, PO-2, PO-5, PO-8**, and the seven
> category-level decisions) are **out of scope for this artifact**, were already open before it,
> and do not leave PO-3, PO-7 or PO-9 partially resolved.

### 20.2 Evidence discipline — what is and is not claimed

| Claim | Status |
|---|---|
| Documentation authored and internally consistent | **DONE** (this artifact) |
| Baseline `p8-release-reconciled` @ `28999af0926d6ce1032b3903c2737aabe6b350d9` verified MATCH | **VERIFIED** |
| Runtime vocabulary + schema state verified by direct `SELECT`-only inspection (§3.9) | **VERIFIED** |
| Two corrections to `P17-DECISION-02` (`§14.5`, `§M-7`) established in source **and** at runtime | **VERIFIED** |
| PO-3, PO-7, PO-9 resolved | **DECIDED (contract frozen)** |
| Any customer or investor surface actually conforming to this contract | **NOT VERIFIED — no surface exists yet** |
| The P17 result dimensions available at runtime | **NOT APPLIED (PR-1)** |
| The governed requirement catalogue populated | **NOT DONE — 0 rows (PR-2)** |
| Scope 2 end-to-end runtime acceptance | **NOT VERIFIED (PR-3 / `P17-J`)** |

**This artifact is `IMPLEMENTED` and `TESTED` as documentation. It is not `ACCEPTED`.** Its
contract is not satisfied on any surface until `PR-1`, `PR-2` and the §18.3 gates are met. No
investor-surface or customer-capability acceptance may be reported on the strength of this
document (`AGENTS.md §73`, `§74`).

### 20.3 NEXT IMPLEMENTATION TASK

> **`P17-K` — "Governed capability catalogue + P17 runtime dimensions"**
>
> **Goal:** make the frozen contract *backed at runtime* for the 15 categories (and the Scope 1/2
> requirements), without inventing any model.
>
> 1. Apply `20261010000000_p17a…`, `20261011000000_p17c…`, `20261012000000_p17d…`,
>    `20261013000000_p17h…`, `20261014000000_p17_10…` **into a disposable clone first**, verify,
>    then promote under the existing deployment gate (`AGENTS.md §55.1`).
> 2. Re-run the §3.9 read-only check set and record the before/after result as evidence.
> 3. Author the governed `disclosure_requirement_versions` catalogue rows so every category and
>    Scope 1/2 requirement carries a `carbontally_capability` value **exactly** as `M-1` maps it
>    (`S3-2` non-upgrade is a test, not a convention).
> 4. Add the §18.3 gates `AG-1` … `AG-8` as automated tests, including the two new isolation tests
>    (§19.4 rows 8–9).
> 5. Produce an implementation report stating what is `IMPLEMENTED` vs `VERIFIED`.
>
> **Explicitly not part of `P17-K`:** any applicability model (F-1), any new capability vocabulary
> (F-2), any surface UI, any commercial claim (`CM-4`).

### 20.4 NEXT 3 COMMERCIAL PRIORITIES

1. **Close the P17-K catalogue + runtime gating so a capability claim is *backed*.** Until then the
   honest capability statement has a governed shape and no governed content (`PR-1`, `PR-2`).
2. **Align every existing sales, proposal and marketing artefact with the frozen mapping before it
   is next used** — no `architecture_status` (`CM-1`), the same values as the product (`CM-2`), no
   implied dates (`CM-3`). This is zero-cost and prevents a claim being made in a deck that the
   product would not make on a screen.
3. **Earn the seven category-level PO decisions with evidence, not optimism.** Categories 1, 2, 7,
   9, 11, 14 and 15 are gated on named PO decisions (§17.2); each decision needs its
   methodology/prerequisite laid out, so the outcome is a *documented* capability change rather
   than a marketing one.

### 20.5 Freeze marker

This decision and the rules it contains — `M-1`…`M-6`, `SC-1`…`SC-6`, `S3-1`…`S3-8`,
`NS-1`…`NS-7`, `IV-1`…`IV-6`, `CT-1`…`CT-4`, `IN-1`…`IN-4`, `CS-1`…`CS-5`, `CM-1`…`CM-4`,
`F-1`…`F-10`, `AG-1`…`AG-8`, `SEC-1`…`SEC-5` — are **frozen**. A change to any of them requires a
new recorded decision, not an implementation choice (`AGENTS.md §62`, `§63`).

---

*End of `CT-PO-P17-DECISION-03`. Documentation only: no code, schema, migration, API, RLS policy,
UI or demo data was created, altered or removed by this artifact.*
