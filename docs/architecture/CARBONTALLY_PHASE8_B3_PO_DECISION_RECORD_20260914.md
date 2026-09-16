# CarbonTally — Phase 8 B3: PO DECISION RECORD (the 12 decisions of 2026-09-14)

**Task:** `CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260913-031` (contract / governance preparation only)
**Date:** 2026-09-14
**Authority:** PO blanket authorisation `CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260913-050`; PO ratification of the 12 recommendations, 2026-09-14
**Governs:** `docs/architecture/CARBONTALLY_PHASE8_B3_IMPLEMENTATION_CONTRACT_20260913.md` (Amendment 2)
**Type:** DECISION RECORD — **no implementation, no schema change, no migration, no test change, no deploy**

---

## 1. CONFLICT NOTICE (read first — nothing below is silently resolved)

This task was issued on the premise that B3 is *unimplemented* and that its contract is
*yet to be written*. **That premise does not match the verified repository state**, and
in accordance with the task's own instruction (*"if any existing artifact conflicts …
do not silently resolve the conflict. Report it"*) it is reported here rather than
reconciled by assumption.

| Premise in the task | Verified repository state (2026-09-14) |
|---|---|
| "Produce the authoritative B3 implementation contract" | **The B3 contract already exists**: `docs/architecture/CARBONTALLY_PHASE8_B3_IMPLEMENTATION_CONTRACT_20260913.md` (373 lines, §1–§22 incl. Amendment 1), produced by `…031` on 2026-09-13 |
| "Review B3 planning/decision artifacts" | `docs/cline/reports/CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260913-031.md` exists (99 lines) |
| **"B3 IMPLEMENTATION NOT STARTED"** | **B3 is IMPLEMENTED, INDEPENDENTLY VERIFIED and CLOSED**: migrations `20260917000000_p8_b3_intensity_catalogue.sql`, `20260917010000_p8_b3_intensity_ratios.sql`; modules `backend/domain/disclosure_projection.py`, `backend/api/v3_disclosure.py`, `backend/data/disclosure*.py`, `backend/services/disclosure_*.py`; gate **V3 PASS** (`…033`); closure `CT-P8-B3-CLOSURE-20260913-051.md` — *"B3 CLOSED — IMPLEMENTED, INDEPENDENTLY VERIFIED (V3 PASS), GOVERNANCE RECORDED"* |
| "next step … PO issues a separate B3 implementation authorization" | That step already occurred (`…032` implementation; `…033`/`…051` verification and closure) |

**Consequences, stated plainly:**

1. The statements the report was instructed to make — *"B3 IMPLEMENTATION NOT STARTED"*
   and *"NO B3 IMPLEMENTATION AUTHORIZATION GRANTED BY THIS TASK"* — cannot both be signed
   truthfully: the first is **factually false** in the current repository. §7.5 records the
   status reported instead. (The second statement **is** true and is signed without
   reservation.)
2. Creating a **second** B3 contract file would create two competing authoritative
   contracts for one batch, which AGENTS.md §4/§63 prohibit. The action taken is to record
   the 12 decisions as **Amendment 2 to the existing contract**, stating this deviation
   from the instruction openly so the PO can overrule it.
3. **No B3 artefact, migration, API, test or environment was modified by this task.**
   B3's closed status is untouched; this task neither re-opens, re-authorises nor re-closes B3.
4. This is a **documentation/governance conflict, not a product defect.** The 12 decisions
   are **consistent with** the as-built B3, with the single exception flagged in §4.

---

## 2. How to read the decisions

Each decision is recorded in substance (the PO's ratification is the authority), followed
by three things kept strictly separate:

* **As-built conformance** — the *evidence* in the current repository (factual reconciliation, not a decision).
* **Implementation constraint** — what the decision *means* for implementation (derived, not invented).
* **Flag** — raised only where the decision set is **not** sufficient to determine a
  behaviour that materially affects auditability, data semantics, security or
  user-visible behaviour. Nothing else is escalated as a PO decision.

---

## 3. The 12 ratified decisions

### `D-B3-1` — Authoritative calculation data

> **Decision.** CarbonTally's calculation layer treats **persisted structured data as the
> authoritative calculation input**. Extraction output remains evidence/input and must not
> silently become a competing calculation source of truth.

* **As-built:** B3 projections read persisted snapshots/values only; the projection engine
  **never recomputes emissions** (contract §7.2; `backend/domain/disclosure_projection.py`;
  closure `…051` §2 deliverable B: *"no emission recomputed"*). Extraction output feeds
  evidence (`evidence_line_items`, B2) and does not overwrite calculated values.
* **Implementation constraint:** no B3 path may derive a reported figure from raw
  extraction text when a persisted structured value exists.

### `D-B3-2` — Framework and version

> **Decision.** CarbonTally explicitly identifies the **applicable carbon-accounting
> framework and its version**. Historical calculations must be able to identify which
> framework/version was used.

* **As-built:** `disclosure_frameworks` + `disclosure_framework_versions` seeded (3
  frameworks, 26 versions); `disclosure_requirement_versions` are version-bound;
  `disclosure_values` carries `requirement_version_id` with
  `UNIQUE (report_version_id, requirement_version_id)` and indexes on both columns
  (B1 migration `20260914000000_p8_b1_disclosure_model_foundation.sql`).
* **Implementation note (NOT a PO decision):** the framework version is bound
  **transitively** — `disclosure_values.requirement_version_id` → requirement version →
  framework version. There is **no denormalised `framework_version_id` column on
  `disclosure_values`**. Identification of the framework/version used is therefore possible
  and reproducible, which is what the contract §15 claims. A direct column for query
  convenience would be an implementation preference for a future batch, not a decision.

### `D-B3-3` — Requirement sets

> **Decision.** Requirement sets are represented **explicitly and in a versionable /
> auditable manner**, not hidden solely inside application code.

* **As-built:** requirement sets exist as persisted, versioned rows
  (`disclosure_requirements`, `disclosure_requirement_versions`,
  `disclosure_purpose_requirements`, plus B3's mapping mechanism) — contract §4 deliverable
  C; closure `…051` §2 C. Requirement **identity is placeholder-level** (`B1RT_*`,
  `B2RT_*`) and mapping **content** is evidence-gated (`PQ-6`, `D17`, `B3-D7`, `B3-D8`).
* **Implementation constraint:** no requirement may be introduced as code-only logic.

### `D-B3-4` — Applicability

> **Decision.** Applicability is **deterministic and based on persisted, auditable
> inputs**, not hidden application assumptions. The contract must document the required
> applicability inputs and their lifecycle semantics. Do not invent fields the sources do
> not support; flag unresolved detail.

* **As-built:** assessments are **persisted rows** (`disclosure_applicability_assessments`)
  written and read through the data layer (`backend/data/disclosure.py`) and consumed by
  the projection engine (`backend/domain/disclosure_projection.py:350`). The ratified
  four-value vocabulary is **`APPLIES` · `DOES_NOT_APPLY` · `UNDETERMINED` ·
  `CUSTOMER_INPUT_REQUIRED`**, with `UNDETERMINED` first-class and never converted
  (`APPL`/D13; contract §9 as corrected by Amendment 1 §22.3). Assessments are
  period-dated and version-bound.
* **Implementation constraint:** applicability may never be inferred from request context,
  UI state, or a hard-coded rule table; it is read from persisted assessments.
* **Flag → §5.1 (`C-B3-1`)** — assessment *lifecycle* semantics are only partly specified.


### `D-B3-5` — Purpose codes

> **Decision.** Use **controlled, persisted, auditable purpose codes** where the model
> requires calculation/requirement purpose identification. Do not invent an uncontrolled
> vocabulary.

* **As-built:** `disclosure_purposes` seeded (4 purposes, 24 purpose versions);
  `purpose_code` is a **projection**, and `report_type` semantics are unchanged (`DM-2`;
  contract §10; closure `…051` §2 deliverable E).
* **Implementation constraint:** purposes are referenced by catalogue code; no new code may
  be minted at runtime.

### `D-B3-6` — Intensity denominators

> **Decision.** Intensity calculations must retain an **explicit denominator value, unit,
> and context/meaning**, rather than storing only a final intensity number.

* **As-built:** B3 ships **two** tables — `disclosure_intensity_denominator_types`
  (generic capability, `support_class` CHECK-restricted to `CARBONTALLY_SUPPORTED`) and
  `disclosure_intensity_ratios` (org-scoped selection persisting the denominator value,
  unit and basis) plus `disclosure_intensity_denominator_framework_links` for framework
  claims (migrations `20260917000000`, `20260917010000`; contract §6/Amendment 1 §22.2).
  Verified live in QA: all three tables exist with RLS **enabled** and policies (1 / 1 / 2).
* **Implementation constraint:** a stored intensity may never stand alone without its
  persisted denominator value + unit + context, and a customer-authored denominator is not
  silently accepted as a framework requirement (`B3-D1` PO direction, 2026-09-13).

### `D-B3-7` — Value status

> **Decision.** Use an **explicit controlled value-status model** so the system can
> distinguish how a value is represented/obtained, rather than relying on nulls or informal
> flags. Do not invent additional statuses without evidence.

* **As-built:** `disclosure_values.value_status` with the ratified controlled set
  (`PENDING` / `RESOLVED` / `UNRESOLVED`, contract §11, `PQ-3`/`DM-5`), with
  `effective_class` authoritative and `NOT_SUPPORTED` ≠ `CUSTOMER_INPUT_REQUIRED`
  (`B3-D5`, `B3-D6`; vocabulary confirmed present in `backend/domain/disclosure.py`).
  Live `disclosure_values` columns: `effective_class, value_status, value_kind,
  numeric_value, value_unit, text_value, source_kind, reason, computed_at, …`.
* **Implementation constraint:** no new status value may be added without evidence; a
  missing value must be represented by an explicit status, never by `NULL` semantics.

### `D-B3-8` — Calculation drill-down

> **Decision.** Provide an **auditable drill-down from reported/calculated results to the
> persisted calculation inputs and supporting evidence**, while avoiding unnecessary
> exposure of internal implementation details. The contract must define the boundary.

* **As-built:** the read model is the B2 `COALESCE` join exposed by
  `GET /api/v3/reports/{report_id}/disclosure/{value_id}/lines`
  (`backend/api/v3_disclosure.py`; contract §12.1/§12.2, deliverable G; V3 §7.6 verified on
  real line-linked fixtures). `B3-D12` ratified that drill-down is a **B3 read model** and
  that its **UI belongs to B4**.
* **Implementation constraint / boundary:** the API returns the persisted inputs and their
  evidence linkage — not internal tables, internal identifiers beyond those needed for
  traceability, or engine internals.

### `D-B3-9` — Evidence gaps

> **Decision.** Missing or insufficient evidence must be **explicitly represented**.
> CarbonTally must never silently fabricate, assume, or conceal missing evidence. The B3
> contract must define how the evidence-gap state affects calculation/reporting status,
> using only decisions already supported by the authoritative artifacts. Flag anything
> requiring another PO decision.

* **As-built (representation):** gaps are first-class, not nulls — `value_status =
  UNRESOLVED`, `effective_class = NOT_SUPPORTED` (distinct from
  `CUSTOMER_INPUT_REQUIRED`), applicability `UNDETERMINED` preserved (0 auto-resolved), a
  persisted `reason`, and *"no fabricated zeros"* (closure `…051` §3). E1 evidence remains
  **evidence-gated and conditional** (`E1-COV` CONDITIONAL, `G0-A`, task `…048`) with **no
  content invented**.
* **⚠ FLAG → §4 (`D-B3-13`):** the decisions **do not** determine how an open evidence gap
  affects *reporting/finalisation status*. Today a gap is **represented** but does **not
  block** approval/finalisation (B4 ratified Owner/Admin approval and `FINAL` immutability,
  `B4-D1`; no gap gate exists). Whether a gap must block finalisation, or merely surface,
  is **not resolved** by the 12 decisions or existing artefacts → **new PO decision required**.


### `D-B3-10` — Persistent non-production environment

> **Decision.** The controlled B1+B2 baseline is intended for a **dedicated persistent
> QA/test environment**, not production. This is an environment-baseline decision; it does
> **not** authorise deployment. Deployment/application remains a separate controlled task
> and PO authorisation.

* **As-built:** exactly one dedicated persistent QA environment exists and holds the
  baseline: **`carbontally_qa_phase8`** — S3 + B1×2 + B2×2 + B3×2 applied, RLS policies
  present, runtime suites executing (`…051` §7; verified read-only this task: the three
  intensity tables report `rls=true`, policies 1/1/2).
* **Effect on the older environment decision:** this **substantially satisfies**
  **`D-02`/`…029`** (*"PO must name a non-production target"*) for the B baseline, and
  removes the *"no persistent environment holds B1/B2"* blocker (`F-049-3`) in substance —
  see **§5.2 (`C-B3-2`)** for the one-line confirmation requested.
* **Implementation constraint:** no production migration, deployment, backfill or
  production credential use. Deployment remains a separate PO authorisation.

### `D-B3-11` — API surface

> **Decision.** B3 exposes only the **minimum API surface required by the approved B3
> requirements/workflows**. No speculative endpoints.

* **As-built:** the contract §12.2 surface is **seven** B3 endpoints:
  `GET /reports/{id}/disclosure`, `GET /reports/{id}/disclosure/{value_id}/lines`,
  `POST /reports/{id}/disclosure/project`, `GET|POST /reports/{id}/intensity`,
  `GET|POST /organizations/{org_id}/applicability` (closure `…051` §2 deliverable H/I).
* **Implementation note (NOT a conflict):** the same router file
  (`backend/api/v3_disclosure.py`) also hosts **six B4** endpoints (narrative,
  finalisation-check, approve, finalise, frozen-artefact GET/signed-url). Those belong to
  the separately contracted and closed B4 batch (`…034`/`…035`/`…052`), not to B3, and are
  **not** speculative B3 endpoints.
* **Implementation constraint:** any new B3 endpoint requires a contract amendment before
  implementation.

### `D-B3-12` — Historical behaviour

> **Decision.** Historical/finalised results must remain **tied to their historical
> calculation state/version**. Later framework, requirement, calculation-rule or factor
> changes must not silently alter an already-finalised historical result.

* **As-built:** values are bound to `report_version_id` **and** `requirement_version_id`
  (`UNIQUE (report_version_id, requirement_version_id)`; B1 migration `20260914000000`),
  with the framework version reachable transitively (`D-B3-2`). Contract §15 forbids
  retro-projection and backfill; the B2 Class-1 backfill remains unauthorised and
  unexecuted (`…051` §6). `APPROVED`/`FINAL` version content is immutable
  (`IMMUTABLE_STATUSES`; B4 ratified immutability), and a post-final change creates a new
  version.
* **Implementation constraint:** no retroactive rewrite of persisted values or of an
  approved/final version; corrections occur by creating a new version.

---

## 4. NEW PO DECISION REQUIRED

### `D-B3-13` — Effect of an open evidence gap on reporting / finalisation status

**Why it cannot be decided from the existing material.** `D-B3-9` requires the contract to
define how the evidence-gap state **affects calculation/reporting status**, but neither the
12 decisions nor the authoritative artefacts determine that effect. The as-built system
**represents** gaps faithfully (statuses, reasons, `UNDETERMINED`, no fabricated zeros) yet
B4's ratified behaviour lets an Owner/Admin approve and finalise regardless (`B4-D1`,
`FINAL` immutability, no gap gate). Two materially different behaviours are therefore both
consistent with today's repository, and the choice changes auditability, user-visible
behaviour and report semantics.

**Decision required (exactly one of):**

* **(a)** An open evidence gap is **advisory only** — it is surfaced on the report and in
  the drill-down, and finalisation remains permitted (status quo); or
* **(b)** An open evidence gap is a **blocking precondition** — approval/finalisation is
  refused while unresolved blocking gaps exist, with an explicit definition of which gap
  states are blocking; or
* **(c)** A **mixed** rule — some gap states block, others warn (with the mapping stated).

**Scope/impact if (b) or (c):** affects B4's finalisation path (already implemented and
closed) and would require a **new bounded batch**, not a silent change; it also interacts
with the `…048` E1 evidence dependency. **Out of scope of this task — flagged, not decided.**

---

## 5. Confirmation items (not new business rules)

### 5.1 `C-B3-1` — Applicability assessment lifecycle completeness (`D-B3-4`)

Confirm that the **as-built** applicability lifecycle is sufficient and ratified as-is:
assessments are period-dated and version-bound; a re-assessment of an `UNDETERMINED` row
and supersession of an overlapping period are handled by **creating new persisted rows**
(history preserved), with no automatic resolution of `UNDETERMINED`.
*If* the intended semantics differ (e.g. an explicit supersession link or a
one-active-assessment-per-period constraint), that is a **data-semantics change** and should
be raised as a bounded decision before any implementation. No rule has been invented here.

### 5.2 `C-B3-2` — Environment name for `D-B3-10` / `D-02` (`…029`)

Confirm that **`carbontally_qa_phase8`** is the PO-named dedicated persistent QA/test
environment for the B baseline (it is the only such environment and already holds S3, B1,
B2 and B3). This confirmation converts `…029` from *"environment not named"* to *"named"*;
it does **not** authorise deployment, and it does not authorise B1/B2 application to any
other environment.


---

## 6. Consistency review

| Check | Result |
|---|---|
| **Internal consistency of the 12** | **Consistent.** `D-B3-1` (persisted data authoritative) underpins `D-B3-2`/`D-B3-3` (versioned framework/requirement identities) and `D-B3-12` (historical binding). `D-B3-6` (persisted denominator) and `D-B3-7` (controlled value status) are the mechanisms that make `D-B3-9` (honest evidence gaps) representable rather than assumed. `D-B3-4`/`D-B3-5` keep semantics out of code. `D-B3-11` constrains surface; `D-B3-8` constrains exposure. No decision contradicts another. |
| **Consistency with B1** | Consistent. B1 supplied the persisted spine (`disclosure_frameworks`, `disclosure_framework_versions`, `disclosure_requirements`/`_versions`, `disclosure_purposes`/`_versions`, `disclosure_values`, `disclosure_applicability_assessments`) — exactly the objects `D-B3-1…D-B3-5` and `D-B3-12` presuppose. `D-B3-4` uses B1's ratified CHECK vocabulary (Amendment 1 §22.3). |
| **Consistency with B2** | Consistent. B2's `evidence_line_items` + `source_line_item_id` linkage is the evidence substrate `D-B3-8` (drill-down) and `D-B3-9` (gap representation) rely on; B3 authors no evidence classification of its own (`…051` §6). |
| **Consistency with the B3 contract** | Consistent, and now **explicitly governed**: §7 projection (D-B3-1), §8 framework/requirement mapping (D-B3-2/3), §9 applicability (D-B3-4), §10 purposes (D-B3-5), §6 intensity (D-B3-6), §11 value status (D-B3-7), §12 read model/API (D-B3-8/11), §14 audit, §15 historical (D-B3-12), §18 environment (D-B3-10). |
| **Conflicts with ratified artefacts** | **One substantive gap, no direct contradiction:** `D-B3-9`'s "effect on reporting status" is undetermined (`D-B3-13`). Everything else conforms. The `D-B3-2` transitive-binding nuance and the `D-B3-11` B4-endpoint co-location are documented as implementation notes, not conflicts. |
| **Conflicts with the task premise** | **Yes — reported in §1** (B3 is implemented/closed, not unstarted; the contract already exists). Not silently resolved. |


---

## 7. Readiness review (the eight required determinations)

| # | Question | Determination |
|---|---|---|
| **1** | Are all 12 PO decisions recorded? | **YES** — `D-B3-1`…`D-B3-12`, each with as-built conformance evidence and its implementation constraint. |
| **2** | Are they internally consistent? | **YES** — §6; mutually reinforcing, no contradiction. |
| **3** | Are they consistent with B1/B2? | **YES** — §6; they presuppose exactly the persisted objects B1/B2 delivered and add no competing source of truth. |
| **4** | Are all B3 dependencies explicitly identified? | **YES** — B1 (11 disclosure tables, seeds, applicability vocabulary), B2 (`evidence_line_items` + `source_line_item_id`), the ratified decision set (`D11-CAT`, `DM-1…DM-7`, `APPL`, `PQ-1`/`PQ-3`/`PQ-4`/`PQ-6`/`PQ-7`, `D15`, `D17`, `E1-COV` CONDITIONAL), the B3 contract, and the environment (`carbontally_qa_phase8`). |
| **5** | Any unresolved PO decisions? | **YES — one**: `D-B3-13` (effect of an open evidence gap on reporting/finalisation status). Plus two **confirmation** items (`C-B3-1`, `C-B3-2`) that are not new business rules. |
| **6** | Implementation ambiguities that must be resolved before authorisation? | **Yes, for any *future* B3-scoped change:** `D-B3-13` (behavioural) and `C-B3-1` (data semantics, only if the intended lifecycle differs). No *existing* implementation is blocked: as-built B3 conforms to `D-B3-1…D-B3-12` apart from the (status-quo) `D-B3-9` effect. |
| **7** | Is B1+B2 availability in the persistent QA/test environment still a prerequisite? | **YES** — B3 runtime suites execute only where the B1+B2 schema and seeds exist. **Satisfied today**: `carbontally_qa_phase8` holds S3 + B1×2 + B2×2 + B3×2 with RLS policies (verified read-only this task); a *skipped* suite would still not be a PASS. |
| **8** | Is a separate B3 implementation authorization still required? | **YES — unchanged.** Nothing in this task is, or may be read as, an implementation authorisation. |

### 7.5 Implementation / authorisation status (stated truthfully)

| Instructed wording | Truthful status |
|---|---|
| *"B3 IMPLEMENTATION NOT STARTED"* | **CANNOT BE SIGNED — factually false.** `B3 IMPLEMENTATION IS COMPLETE AND CLOSED` (`…032` implementation · `…033` gate **V3 PASS** · `…051` closure · migrations `20260917000000`, `20260917010000`). The correct statement is: **NO NEW B3 IMPLEMENTATION WAS PERFORMED BY THIS TASK** (see §8). |
| *"NO B3 IMPLEMENTATION AUTHORIZATION GRANTED BY THIS TASK"* | **SIGNED — TRUE.** This task grants no authorisation, re-opens nothing and closes nothing. |
| *"B3 CONTRACT COMPLETE — READY FOR PO IMPLEMENTATION AUTHORISATION"* | **NOT APPLICABLE AS WRITTEN** — the contract was already complete on 2026-09-13 (plus Amendment 1), and B3 implementation authorisation has already been given and discharged. The accurate equivalent is:<br>**B3 DECISION RECORD COMPLETE — 12 DECISIONS RECORDED; ONE NEW PO DECISION REQUIRED (`D-B3-13`); NO NEW B3 IMPLEMENTATION AUTHORISATION REQUESTED OR GRANTED.** |

---

## 8. Scope and prohibited behaviour (this task)

**Performed:** repository/context review + this decision record + **Amendment 2** appended to
the existing B3 contract (documentation only).

**Not performed — and not to be read as authorised or performed:**

* No B3 implementation, re-implementation, re-open, re-verification or re-closure.
* No change to application behaviour, database schema, migrations, APIs, frontend, tests or
  production configuration; **no `git commit`**.
* No **B4**, **P1**, **P2**, **RLS remediation**, **Phase 8-X / Phase 9**, **Insight (I1–I8)**
  or **legacy-route** work.
* No production migration, deployment, backfill or production data access; no environment
  mutation of any kind (QA read **read-only** for evidence).
* No inferred PO decision: exactly **one** item (`D-B3-13`) is raised as **required**, and
  **two** (`C-B3-1`, `C-B3-2`) as **confirmations**.

**Governance rule acknowledged:** completion of this task is **not** B3 implementation
authorisation, does not self-authorise B3 and does not self-close B3. The next step is for
the PO to review this record and, if satisfied, either issue the one remaining decision
(`D-B3-13`) or record that the status quo under `D-B3-9` is accepted.

---

## 9. Provenance of this record

| Item | Value |
|---|---|
| Evidence base | contract `CARBONTALLY_PHASE8_B3_IMPLEMENTATION_CONTRACT_20260913.md` (§1–§22) · `CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260913-031.md` · `CT-P8-B3-IMPLEMENTATION-20260913-032.md` · `CT-P8-B3-INDEPENDENT-VERIFICATION-20260913-033.md` · `CT-P8-B3-CLOSURE-20260913-051.md` · B1/B2 contracts and closures · live read-only inspection of `carbontally_qa_phase8` |
| Migrations (authored by `…032`, **not** by this task) | `20260917000000_p8_b3_intensity_catalogue.sql`, `20260917010000_p8_b3_intensity_ratios.sql` |
| Modules (authored by `…032`, **not** by this task) | `backend/domain/disclosure_projection.py`, `backend/api/v3_disclosure.py`, `backend/data/disclosure*.py`, `backend/services/disclosure_*.py` |
| Environment touched | `carbontally_qa_phase8` — **reads only**; production untouched |


---

## 10. Appendix — the 12 decisions as ratified (verbatim statements)

The decision statements in §3 record the ratified substance. For exactness, the **verbatim
ratified statements** are reproduced here, so no reader has to rely on a paraphrase. Each is
followed by its record id; **nothing beyond these 12 statements was ratified**, and nothing
was added to them.

1. *"CarbonTally's calculation layer will treat **persisted structured data as the authoritative calculation input**. Extraction output remains evidence/input and must not silently become a competing calculation source of truth."* — `D-B3-1`
2. *"CarbonTally will explicitly identify the **applicable carbon-accounting framework and its version**. Historical calculations must be able to identify which framework/version was used."* — `D-B3-2`
3. *"CarbonTally will represent **requirement sets explicitly and in a versionable/auditable manner** rather than hiding requirements solely inside application code."* — `D-B3-3`
4. *"Applicability will be **deterministic and based on persisted, auditable inputs** rather than hidden application assumptions. Document the required applicability inputs and their lifecycle semantics in the B3 contract. Do not invent specific fields if the repository/source material does not support them. Flag any unresolved implementation detail for PO review."* — `D-B3-4`
5. *"Use **controlled, persisted, auditable purpose codes** where the B3 model requires calculation/requirement purpose identification. Do not invent an uncontrolled vocabulary."* — `D-B3-5`
6. *"Intensity calculations must retain an **explicit denominator value, unit, and context/meaning**, rather than storing only a final intensity number."* — `D-B3-6`
7. *"Use an **explicit controlled value-status model** so the system can distinguish how a value is represented/obtained rather than relying on nulls or informal flags. Do not invent additional statuses without evidence."* — `D-B3-7`
8. *"Provide an **auditable drill-down from reported/calculated results to the persisted calculation inputs and supporting evidence**, while avoiding unnecessary exposure of internal implementation details. The contract must clearly define the intended boundary."* — `D-B3-8`
9. *"Missing or insufficient evidence must be **explicitly represented**. CarbonTally must never silently fabricate, assume, or conceal missing evidence. The B3 contract must define how this evidence-gap state affects calculation/reporting status, using only decisions already supported by the authoritative artifacts. Flag anything requiring another PO decision."* — `D-B3-9` *(→ `D-B3-13`, §4)*
10. *"The controlled B1+B2 baseline is intended for a **dedicated persistent QA/test environment**, not production. This decision is for the environment baseline; it does NOT authorize deployment yet. Deployment/application remains a separate controlled task and PO authorization."* — `D-B3-10` *(→ `C-B3-2`, §5.2)*
11. *"B3 should expose only the **minimum API surface required by the approved B3 requirements/workflows**. Do not create speculative endpoints."* — `D-B3-11`
12. *"Historical/finalized results must remain **tied to their historical calculation state/version**. Later framework, requirement, calculation-rule, or factor changes must not silently alter an already-finalized historical result."* — `D-B3-12`

---

## 11. Post-record PO clarifications (2026-09-14, recorded; no decision invented)

Two open items from §4/§5 were settled by PO instruction in the master execution
clarification of 2026-09-14. Recorded here for ledger hygiene so later cycles do not
re-raise them. **No new decision is created by this section** — it records the PO's
instruction and its effect on the two open items.

| Item | Was | Now | Authority / basis |
|---|---|---|---|
| **`C-B3-1`** applicability lifecycle completeness | confirmation requested (§5.1) | **CONFIRMED — CLOSED** | PO instruction §5 of the 2026-09-14 master clarification states the intended baseline (explicitly recorded; dated and framework-version-bound; facts persisted; written basis required; `UNDETERMINED` preserved; not auto-inferred from documents; report explicitly linked to the assessment used; re-assessment creates a new version; an existing report does not silently switch to a newer assessment) and directs *"If this is already implemented and verified, do not reopen B3."* Evidence that the as-built system matches that baseline: `docs/cline/reports/CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260914-058.md` and the code-level trace in the applicability explanation (`services/disclosure_projection.py:45 _applicability_status`, `domain/disclosure_projection.py:246 derive_effective_class`, contract §9, `…051` §2/§3). **B3 is not reopened.** |
| **`D-B3-13`** effect of an open evidence gap on reporting/finalisation | new PO decision required (§4) | **RESOLVED — option (a) advisory only; no blocking rule** | PO instruction §4 of the same clarification: *"Do not introduce a rule that CarbonTally itself blocks the customer's reporting/approval process solely because evidence is missing unless an explicit PO decision authorizes that behavior."* No such authorising decision exists, so the ratified position is the as-built one: gaps are **flagged and preserved**, never blocking, never fabricated. Should the PO later want a blocking rule, that requires a new explicit decision and a bounded change to the finalisation path — it must not be inferred. |
| Draft-report retention / replacement / deletion | implied by the applicability review | **NOT a B3 matter** | PO instruction §5: *"Any question concerning draft-report retention, replacement or deletion belongs to the appropriate report lifecycle/B4 decision rather than reopening B3."* Routed to the report-lifecycle/B4 decision set. |

**Unchanged:** B3 remains **CLOSED** (`…051`); the B3 contract is unchanged by this section
(it is recorded in this decision record only); no implementation, migration, API or test change.


