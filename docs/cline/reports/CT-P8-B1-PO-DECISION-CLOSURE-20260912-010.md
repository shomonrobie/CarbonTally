# CT-P8-B1-PO-DECISION-CLOSURE-20260912-010

**Task ID:** `CT-P8-B1-PO-DECISION-CLOSURE-20260912-010`
**Title:** Phase 8 Reporting — B1 Disclosure Model Foundation — PO Decision Closure
**Type:** READ-ONLY governance / decision-closure — **no implementation**
**Date:** 2026-09-12 (start `2026-09-12T21:08:36+06:00`)
**Final verdict (at analysis time):** `B1 PO DECISION CLOSURE BLOCKED — ADDITIONAL PO DECISION/EVIDENCE REQUIRED` — **SUPERSEDED** (see the status update above; PQ-1…PQ-8 are now CLOSED/RATIFIED)

**Evidence labels:** **[CONFIRMED]** repository/authoritative fact · **[PROPOSED]** B1-contract proposal · **[INFERRED]** derived · **[UNRESOLVED]** gated.

> **STATUS UPDATE — SUPERSEDED BY `CT-P8-B1-PO-DECISION-RATIFICATION-20260912-011`.** All eight decisions
> **PQ-1…PQ-8 are now CLOSED / RATIFIED**; the authoritative record is
> `CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md`. The **BLOCKED** verdict below records the
> state **at the time of this analysis** (before the PO decided PQ-3). The analytical findings and
> recommendations in §§10–18 remain valid; **§19 and the final verdict are superseded by the ratification
> record.**

---

## 1. Task ID
`CT-P8-B1-PO-DECISION-CLOSURE-20260912-010`.

## 2. Date
2026-09-12.

## 3. Repository / branch
`carbon_tally` · branch **`main`** · pre-existing working-tree changes preserved.

## 4. Starting HEAD
`19e4f01c176eee5870f3c15038b6e7c68b23281c` — `19e4f01 feat: implement Phase 8 report lifecycle foundation`.

## 5. Ending HEAD
`19e4f01c176eee5870f3c15038b6e7c68b23281c` — **unchanged** (no commit).

## 6. Initial Git status
| Item | Value |
|---|---|
| Branch | `main` (ahead 14) |
| Staged | 0 |
| Modified (tracked) | 208 |
| Untracked (porcelain) | 65 |

## 7. Final Git status
| Item | Value |
|---|---|
| Branch | `main` (ahead 14) |
| Staged | **0** |
| Modified (tracked) | **208 (unchanged)** |
| Untracked (porcelain) | **65 (unchanged** — the new report sits inside the already-untracked, collapsed `docs/cline/reports/` directory; `-uall` shows it as an individual untracked file) |

**208 pre-existing modifications preserved unchanged. No reset/checkout/clean/stash/restore/rebase/amend. No unrelated file altered. No commit, no push.**

## 8. Documents inspected
D1–D17 ratification; Disclosure Model Design (§§6–9, 11, 13, 18, 19, 20, 22); Decision Record (20 decisions + `DM-7` refinement); Comprehensive Readiness Assessment (§20 batch split, §23 blockers); G0 Governance Consolidation; Line-item forensic; Emission-factor forensic; **B1 Implementation Contract** (`CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md`, esp. §§4–6, 9, 14–27, 28); prior Cline report `…-009`; RLS production baseline.

## 9. Repository areas inspected
`supabase/migrations/**` (55 files) — incl. `20260912000000_p7_audit_immutability_and_indexes.sql` (DB-trigger append-only enforcement, all roles), `20260905020000_gate5_t6_automation_write_once_guard.sql` (BEFORE UPDATE write-once trigger), `20260807020000_add_calculation_snapshots.sql` + `20260912000000_p7_…` (calc-snapshot immutability = **app-layer/append-only by design**, no trigger), `20260831020000_audit_activity_immutability.sql`; `20260807070000_add_new_table_rls.sql` (grants/RLS); `20260831030000_tenant_org_id_not_null.sql`; `20260913000000_p8_report_lifecycle_status.sql`; key tables `report_generation_queue` (`reporting_year`), `report_versions`, `calculation_snapshots`, `organizations`, `audit_trail`.

---

## 10. PQ-1 analysis — intensity catalogue placement

**Exact question:** Should `disclosure_intensity_denominator_types` + `disclosure_intensity_ratios` belong to **B1** or **B3**?

**Governing decisions:** D10 (SECR intensity ratio), D11 (controlled structured denominator model), **D11-CAT** (controlled catalogue; customer selects/confirms; CarbonTally may recommend; **no unrestricted custom denominator**; exact catalogue content verified before implementation), D12, D13; roadmap §20 batch split; design §11.3, §22.1.

**B1-contract sections:** §5 (non-scope lists intensity tables), §6 (records the design-MVP vs roadmap conflict), §28 PQ-1.

**Repository/evidence verification:**
- **[CONFIRMED]** No intensity table exists; `disclosure_*` tables = 0.
- **[CONFIRMED]** D11 explicitly states the *exact denominator catalogue and statutory treatment must be verified before implementation* (design §11.3). D11-CAT ratifies a **controlled catalogue** but does **not** supply its contents.
- **[CONFIRMED]** The design §22.1 places intensity in its MVP table set; the roadmap §20 places "SECR intensity model" in **B3**. → the recorded sequencing conflict.

**Structure vs content:** The **structure** (a controlled denominator-type catalogue + a per-period selected ratio with numerator/denominator/rationale) is **authorised by D11/D11-CAT**. The **content** (which denominator types exist) is **evidence-gated** and **not** authorised. Neither requires B1: the intensity concept depends on the **requirement vocabulary** (`INTENSITY_RATIO` source kind, `E1_GHG_INTENSITY`) and on disclosure values, both of which are B3-ish concerns.

**Determination:** **CONFIRMED WITH CONDITION.** B1 does **not** require intensity tables; placing them in B3 removes an evidence-gated, content-dependent surface from the foundation batch and keeps B1 at 11 tables.

**Consequence for B1:** B1 remains 11 tables; B1's requirement-mapping `source_kind` enum **reserves** `INTENSITY_RATIO` (already in the contract §9.4), so no B3 dependency leaks into B1. **No catalogued denominator is invented.**

**Recommended PO decision:** **Intensity belongs to B3.** Condition: neither intensity structure nor content is seeded in B1; the eventual architecture **retains** both tables (this is a delivery-sequence decision, **not** a removal).

---

## 11. PQ-2 analysis — reporting-period placement

**Exact question:** Where should explicit `reporting_period_start` / `reporting_period_end` live?

**Governing decisions:** **DM-3** (period start/end explicit; do not permanently assume calendar-year), **APPL** (applicability is period-dated), D15 (historical reproducibility). Design §8.1/§10.1 (period on the reporting context; calendar-year flagged).

**B1-contract sections:** §9.8 (`disclosure_applicability_assessments`), §9.9 (`disclosure_report_instance_binding`), §16 (applicability semantics).

**Repository verification:**
- **[CONFIRMED]** `report_generation_queue.reporting_year INTEGER NOT NULL` exists; the engine derives `YYYY-01-01 → YYYY-12-31` (calendar-year assumption) — design §10.1. `report_versions` carries no period.

**Is duplication justified?** **YES — it is justified denormalised context, not unsafe duplication**, because the two records answer **different questions**:
- the **applicability assessment** answers "does framework X apply to this organisation **for this period**?" (per `APPL`); it must be period-dated **independently** of any report instance;
- the **instance binding** records the period the **report** covers (per `DM-3`), which must be explicit and non-calendar.

**Required invariant (must agree):** when an applicability assessment is **referenced by** an instance binding, the binding's `(reporting_period_start, reporting_period_end)` **MUST equal** the assessment's. The **authoritative period for a report is the instance binding**; the assessment's period is the period it was assessed for. This is an app-layer + verification invariant (it cannot be expressed as a simple FK because the two periods are on different rows).

**Determination:** **CONFIRMED WITH CONDITION.**

**Consequence for B1:** B1 retains explicit periods on **both** records; `report_generation_queue.reporting_year` is untouched; the consistency invariant is added to the B1 verification contract (§27.B of the contract).

**Recommended PO decision:** **Keep explicit periods on both B1 records, with the stated agreement invariant.** (Consolidating to one record is the alternative; it would weaken either applicability or report-period explicitness.)

---

## 12. PQ-3 analysis — `disclosure_values.value_status`

**Exact question:** Is the proposed `value_status` vocabulary
`PENDING · RESOLVED · CUSTOMER_INPUT_REQUIRED · NOT_SUPPORTED · NOT_APPLICABLE · UNDETERMINED`
semantically clean?

**Governing decisions:** D12 (requirement semantics are richer than a boolean), **DM-5** (`CUSTOMER_INPUT_REQUIRED` ≠ `NOT_SUPPORTED`; finalisation rules), **APPL** (applicability states incl. `UNDETERMINED`), D13; the four-way invariant **REQUIREMENT ≠ APPLICABILITY ≠ CAPABILITY ≠ CUSTOMER INPUT** (Decision Record §9).

**B1-contract section:** §9.10 — `disclosure_values` carries **`effective_class`** (CHECK ∈ the `requirement_class` set) **and** `value_status` (the proposed set), both drawn from the design's "class/status" language (design §18.1 D).

**Verification of semantic cleanliness — the exact problem:**

The contract defines **two** columns on the same row whose value domains **overlap**:

- `effective_class` ∈ { REQUIRED, CONDITIONAL, OPTIONAL, **NOT_APPLICABLE**, **CUSTOMER_INPUT_REQUIRED**, **UNDETERMINED**, **NOT_SUPPORTED**, FUTURE } — *the derived requirement/applicability state*;
- `value_status` ∈ { **PENDING**, **RESOLVED**, **CUSTOMER_INPUT_REQUIRED**, **NOT_SUPPORTED**, **NOT_APPLICABLE**, **UNDETERMINED** } — *the proposed value state*.

**Four values are shared** (`CUSTOMER_INPUT_REQUIRED`, `NOT_SUPPORTED`, `NOT_APPLICABLE`, `UNDETERMINED`). The same fact — e.g. "this disclosure cannot be produced because the capability is absent" — can therefore be recorded as `effective_class='NOT_SUPPORTED'`, as `value_status='NOT_SUPPORTED'`, or as both. That is **two sources of truth for one derived outcome**.

Worse, `value_status` **mixes two distinct dimensions**:
1. a **materialisation lifecycle** (`PENDING` → `RESOLVED`); and
2. **derived regulatory/applicability outcomes** (`CUSTOMER_INPUT_REQUIRED`, `NOT_SUPPORTED`, `NOT_APPLICABLE`, `UNDETERMINED`) that already belong to the `requirement_class`/applicability dimension.

This is precisely the conflation the four-way invariant forbids: **VALUE MATERIALISATION STATUS** must not absorb **REQUIREMENT SEMANTICS**, **APPLICABILITY** or **PRODUCT CAPABILITY**. It also creates a downstream ambiguity for **`DM-5` finalisation** (B4 reads the value state to decide whether to block on `CUSTOMER_INPUT_REQUIRED` vs surface `NOT_SUPPORTED`) — if the outcome can live in either column, finalisation must arbitrate between them.

**Determination:** **REQUIRES PO DECISION.** The proposed `value_status` is **not** semantically clean; a change is necessary, and the change defines the B1 value-layer schema, so it is a **material PO architecture decision** (not a wording fix).

**Consequence for B1:** B1's `disclosure_values` column set is **not final** until this is decided. This is the item that gates the closure.

**Recommended resolution (for PO ratification — not applied):** keep the two dimensions **non-overlapping**:
- **`effective_class`** = the **single** home for the derived requirement/applicability outcome (the `requirement_class` vocabulary), derived from `requirement_class` + applicability;
- **`value_status`** = a **pure materialisation lifecycle** only — e.g. `PENDING` | `RESOLVED` | `UNRESOLVED` (optionally a terminal materialisation state) — with **no** value duplicating a derived outcome.

Alternative (also PO-selectable): **drop `effective_class`** and let the value carry the derived outcome; but this loses the explicit requirement-vs-effective distinction.

**Do NOT silently redesign:** this report only records the recommended resolution; the B1 contract is unmodified.

---

## 13. PQ-4 analysis — immutability enforcement

**Exact question:** For values belonging to `APPROVED`/`FINAL` report versions, should immutability be enforced by the **application layer** or by a **database trigger**?

**Governing decisions:** D15 (historical reproducibility), the lifecycle ratification (approved/final content immutable), `DM-5`.

**B1-contract section:** §9.10 (immutability note; mechanism left open = PQ-4), §25.

**Repository evidence — two existing precedents:**
- **[CONFIRMED]** **DB-trigger enforcement** exists: `p7_audit_trail_immutable` (BEFORE UPDATE OR DELETE on `audit_trail`) raises for **every role including the service role**; `gate5_t6_automation_write_once_guard` is a BEFORE UPDATE write-once trigger; `20260831020000_audit_activity_immutability.sql` made legacy activity tables immutable.
- **[CONFIRMED]** **App-layer enforcement** is used for `calculation_snapshots` — the p7 migration itself describes it as *"immutable forensic calculation records (existing; append-only **by design** + SHA-256 `content_hash`)"* with **no** immutability trigger; protection is app-layer + `ON DELETE RESTRICT` factor FKs.

**Assessment of the options for `disclosure_values`:**

| Option | Pros | Cons / risk for B1 |
|---|---|---|
| **App-layer** | Matches the `calculation_snapshots` precedent; no cross-table trigger; the writer is CarbonTally's own service layer (no customer write path to values, `P3`); independent of the outstanding lifecycle migration | Weaker than DB enforcement; a future code defect could mutate a finalised value |
| **DB trigger** | Strongest guarantee; matches the `p7` ledger precedent | The condition is **cross-table** (`report_versions.status ∈ {APPROVED, FINAL}`); it would couple `disclosure_values` to a column added by the **outstanding** migration `20260913000000`; a BEFORE UPDATE/DELETE trigger must resolve the parent status per row; complicates a future authorised retention/purge |
| **Both** | Strongest + pragmatic | Must be carefully ordered; over-engineered for B1 |

**Determination:** **CONFIRMED WITH CONDITION — app-layer enforcement for B1**, with **specified future DB hardening** deferred.

**Recommended PO decision:** For B1, enforce immutability at the **application layer** (the B1 service layer refuses to mutate values whose parent `report_versions.status ∈ {APPROVED, FINAL}`), proven by an **independent verification test** (attempt to mutate a finalised value → DENY). Rationale: the writer is the CarbonTally service layer; the comparable `calculation_snapshots` is app-layer-protected; and a cross-table trigger would depend on a lifecycle column that is presently **outstanding** in production. **Defer** DB hardening to a later security/retention task.

**If a future DB trigger is authorised, it must protect (specified, not written):** `BEFORE UPDATE OR DELETE` on `public.disclosure_values` (and `public.disclosure_value_evidence`) that resolves `report_versions.status` via `report_version_id` and **raises** when the status ∈ `{APPROVED, FINAL}`; it must **allow INSERT** of new rows for a new version, must fire for **all roles including the service role** (the `p7` semantic), and must be droppable by an explicitly authorised retention/purge process. **Not implemented here.**

---

## 14. PQ-5 analysis — the 34 outstanding migrations

**Exact question:** Does the migration backlog block B1, or gate only production deployment?

**B1-contract sections:** §3 (baseline), §22 (migration strategy), §28 PQ-5.

**Repository verification:**
- **[CONFIRMED]** 55 migrations in repo; **21 applied / 34 outstanding** in production (RLS baseline §5.1).
- **[CONFIRMED]** The outstanding set includes `20260913000000_p8_report_lifecycle_status` (the lifecycle `status` column) and `20260831030000_tenant_org_id_not_null`.
- **[CONFIRMED]** B1's proposed migration is purely **additive** and references only objects present at the **21-migration** level (`organizations`, `report_generation_queue`, `report_versions`, `calculation_snapshots`, `emissions_logs`, `manual_extraction_items`, `organization_files`).

**Determination:** **CONFIRMED.** B1 has **no dependency on any outstanding migration** for the creation of its tables; `report_versions(id)` exists since the init schema, so the `disclosure_values.report_version_id` FK resolves at the 21-migration level. B1 can be designed and applied in **dev/QA** independently. **This is a DEPLOYMENT GATE, not a B1 architecture blocker.**

**Caveat (recorded):** B1's **runtime immutability semantics** (PQ-4) reference `report_versions.status`, which the outstanding `20260913000000` adds. In a partially-migrated production schema that column may be absent, so B1 must **not** be deployed to production ahead of the lifecycle migration. This reinforces the gate but does **not** change B1's DDL.

**Recommended PO decision:** **Production deployment of B1 remains blocked until the 34-migration backlog is independently reconciled and verified.** B1 may be designed and applied in **dev/QA** on its own. **No migration is reconciled or applied here.**

---

## 15. PQ-6 analysis — reference-seed scope

**Exact question:** What reference data should B1 seed?

**Governing decisions:** D1 (three frameworks), D6-R (four purposes), **D17** (authoritative-source-first), **E1-COV** (CONDITIONAL). Design §§6.1, 6.2, 6.5.

**B1-contract section:** §28 PQ-6 (recommends seeding only framework identities, initial framework versions, purpose identities; defer requirement/mapping content).

**Repository/evidence verification — the critical sub-question (do framework VERSION rows require authoritative evidence?):**
- **[CONFIRMED]** **Yes.** D17 and design §6.3 make `source_tier` + `authoritative_source_date` part of the model; a version row asserts a legal fact (in-force status), so it **requires** authoritative evidence.
- **[CONFIRMED]** The verified evidence supports **framework identities** and **most version facts**: GHG Protocol Corporate Standard; UK SECR (PB13944, 2019; thresholds changed for FYs beginning on/after **6 Apr 2025**); ESRS **2023 set** (as amended by **(EU) 2025/1416**) **in force**; the **2026 Simplified ESRS** **adopted but NOT in force**.
- **[UNRESOLVED]** The regulatory **evidence closure is PARTIAL** (§24.11): the ESRS E1 identifier/title transcription, the GHG Protocol Ch.9 lists, and the **residual SECR numeric "large" detail** are unresolved. This concerns **requirement content**, not framework identity.

**Determination:** **CONFIRMED WITH CONDITION.**
- **Framework identities** (3 rows: `GHG_PROTOCOL`, `UK_SECR`, `ESRS_E1`) — **safely seedable** (D1 facts).
- **Purpose identities** (4 rows, D6-R) — **safely seedable**.
- **Framework version rows** — seedable **only** where the in-force status is **[V]-verified**, and **the exact seed list must be PO-confirmed**, because the precise version **segmentation/labels** (e.g. whether the 6 Apr 2025 SECR threshold change is a separate version row or an applicability boundary; the exact ESRS amendment labelling) is a **judgement**, not a transcribed fact. The **2026 ESRS** revision must be seeded as `ADOPTED_NOT_IN_FORCE` with **no** `applicable_from` (design §6.5).
- **Requirement / requirement-mapping content** — **NOT** seeded in B1 (B3); E1 content stays gated (PQ-7).

**Recommended PO decision:** B1 seeds **framework identities + purpose identities** (uncontested D1/D6-R facts). B1 seeds **framework version rows only as PO-confirmed, [V]-verified rows** (incl. the 2026 ESRS as `ADOPTED_NOT_IN_FORCE`); if the PO prefers maximum conservatism, defer **all** version rows to B3. **Requirement and mapping content are deferred to B3.** **No legal/reference data is invented.**

---

## 16. PQ-7 analysis — does unresolved E1 evidence block B1?

**Exact question:** Does the unresolved ESRS E1 authoritative evidence block B1?

**Governing decisions:** **E1-COV** (CONDITIONAL — only authoritatively verified E1 requirements may be production-supported; unresolved identifiers gated; do not invent), **E1-VER** (bind to the 2023 set as amended and in force; represent later revisions as not-in-force), **DM-1** (controlled internal concept keys; never present internal keys as official identifiers), D17.

**B1-contract sections:** §9.3 (`requirement_code` free-form; `identifier_status`; CHECK `identifier_status='RESOLVED' OR official_identifier IS NULL`), §15, §28 PQ-7.

**Verification:**
- **[CONFIRMED]** B1's requirement table needs **no** official ESRS identifier: `requirement_code` is a **controlled internal string**, `official_identifier` is **nullable**, and the CHECK **structurally forbids** an official identifier while `identifier_status='UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION'`.
- **[CONFIRMED]** E1 **content** (requirement rows, mapping rows) is **B3**, not B1 — so B1's scope never touches E1 identifiers.

**Determination:** **CONFIRMED.** Unresolved E1 evidence does **not** block B1. B1 remains **framework-agnostic**; the structure accepts E1 later without re-architecture (a **data update** re-keys the concept to official identifiers once evidence closes — design §12.1). **`E1-COV` remains CONDITIONAL.**

**Recommended PO decision:** **Re-affirm that E1 seeding stays gated; B1 proceeds without E1 content.** No E1 identifier, threshold, date, materiality value, applicability rule or requirement text is invented.

---

## 17. PQ-8 analysis — roadmap batch split

**Exact question:** Should the roadmap be formally adopted as the implementation/delivery sequence without changing the canonical architecture?

**Governing decisions:** D2/D3 (canonical architecture; 12-section report is presentation only), D6-R, the G0 recorded sequencing conflict; roadmap §19–§20 (Option A/B/C; recommended Option B = B1–B4 + P1/P2 + X1/X2).

**B1-contract section:** §6 (records the design-MVP vs roadmap conflict), §28 PQ-8.

**Verification:**
- **[CONFIRMED]** The design §22.1 lists a 14-table MVP including `evidence_line_items` and the intensity tables; the roadmap §20 assigns evidence/line-item addressability to **B2** and the SECR intensity model to **B3**.
- **[CONFIRMED]** Both documents describe the **same canonical architecture** (framework → requirement → mapping → purpose → applicability → value → evidence; D2). The difference is **delivery sequence**, not architecture content.
- **[CONFIRMED]** The line-item forensic establishes that manufactured line granularity is forbidden and that flat PDF/IMAGE records are not deterministically backfillable → strong justification for isolating evidence/line-item work in B2.

**Determination:** **CONFIRMED.** Adopting the roadmap as the delivery sequence is safe and is **not** a removal of any architecture element.

**Recommended PO decision:** **YES — adopt the roadmap batch split (B1 foundation · B2 evidence/line-item addressability · B3 intensity/integration · B4 narrative/finalisation/frozen artefacts) as the implementation sequence.** This **must not** be read as removing `evidence_line_items` or the intensity model from the eventual Phase 8 architecture. The design §22.1 MVP remains the **content definition** of that architecture; the roadmap is the **delivery schedule**.

---

## 18. Cross-decision consistency check

| Dimension | PQ-1 | PQ-2 | PQ-3 | PQ-4 | PQ-5 | PQ-6 | PQ-7 | PQ-8 | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| B1 table count (11) | keeps 11 | n/a | n/a | n/a | n/a | n/a | n/a | keeps 11 | **consistent** |
| B1/B2 boundary | no leak | no leak | no leak | no leak | no leak | no leak | no leak | confirms | **consistent** |
| B3 intensity | confirms | — | — | — | — | — | — | confirms | **consistent** |
| E1 evidence gating | — | — | — | — | — | defers E1 seed | confirms no blocker | — | **consistent** |
| Report period | — | both records + invariant | — | — | — | — | — | — | **consistent** (with condition) |
| value_status | — | — | **OPEN** | — | — | — | — | — | **INCONSISTENT — gating item** |
| Immutability | — | — | — | app-layer | — | — | — | — | **consistent** (weaker than D15's ideal → condition) |
| Migration deployment | — | — | — | caveat | gate | — | — | — | **consistent** |
| Historical reproducibility | — | — | — | — | — | — | — | — | **consistent** |
| RLS security | — | — | — | — | — | — | — | — | **consistent** (remediation separate) |
| Finalisation (DM-5) | — | — | **affects** | — | — | — | — | — | **INCONSISTENT — depends on PQ-3** |

**Contradiction identified (not silently resolved):**

- **C-1 — PQ-3 is a cross-cutting open item.** The `value_status` conflation is not merely local to `disclosure_values`: because **`DM-5` finalisation (B4)** reads the value state to distinguish `CUSTOMER_INPUT_REQUIRED` (block) from `NOT_SUPPORTED` (surface honestly), an unresolved value-status model leaves the **finalisation signal ambiguous**. Resolving PQ-3 is therefore required both for the B1 schema **and** for a coherent B4 finalisation contract.
- **C-2 — PQ-4 is a mild tension, not a contradiction.** D15 requires finalised reports to remain reproducible; app-layer immutability is weaker than the `p7` DB-trigger guarantee. This is **acceptable for B1** (the writer is CarbonTally's service layer; `calculation_snapshots` uses the same pattern) but is recorded as a **condition** with a specified future DB hardening.
- No other contradictions. PQ-1/PQ-2/PQ-5/PQ-6/PQ-7/PQ-8 are mutually consistent and consistent with the B1 table count and the B1/B2/B3/B4 boundaries.

---

## 19. Final PO recommendation

> **SUPERSEDED (see the status update at the top).** The table below records the analysis-time status. The
> PO has since decided **all eight** items: **PQ-1, PQ-2, PQ-4, PQ-6 = RATIFIED WITH CONDITION; PQ-3, PQ-5,
> PQ-7, PQ-8 = RATIFIED** — recorded in `CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md`.

**Seven of the eight decisions are closable now** (CONFIRMED or CONFIRMED WITH CONDITION). **One (PQ-3) requires a PO decision** because the proposed `value_status` vocabulary is **not semantically clean** and its resolution defines the B1 value-layer schema.

| PQ | Analysis-time status | Post-ratification status | Recommended decision |
|---|---|---|---|
| **PQ-1** | **CONFIRMED WITH CONDITION** | **CLOSED — RATIFIED WITH CONDITION** | Intensity belongs to **B3** (delivery); architecture retains both intensity tables; B1 keeps 11 tables; `INTENSITY_RATIO` reserved |
| **PQ-2** | **CONFIRMED WITH CONDITION** | **CLOSED — RATIFIED WITH CONDITION** | Keep explicit periods on **both** B1 records, with the **agreement invariant** (instance binding is authoritative) |
| **PQ-3** | **REQUIRES PO DECISION** | **CLOSED — RATIFIED** | `effective_class` = authoritative derived-outcome home; `value_status` = pure materialisation lifecycle `PENDING`/`RESOLVED`/`UNRESOLVED` |
| **PQ-4** | **CONFIRMED WITH CONDITION** | **CLOSED — RATIFIED WITH CONDITION** | **App-layer** immutability for B1 + verification test; **defer** DB trigger (specified semantics recorded) |
| **PQ-5** | **CONFIRMED** | **CLOSED — RATIFIED** | Production deployment **gated** by migration reconciliation; B1 dev/QA-applicable independently |
| **PQ-6** | **CONFIRMED WITH CONDITION** | **CLOSED — RATIFIED WITH CONDITION** | Seed **framework identities + purpose identities**; framework **version rows only PO-confirmed & [V]-verified** (2026 ESRS = `ADOPTED_NOT_IN_FORCE`); requirement/mapping content → B3 |
| **PQ-7** | **CONFIRMED** | **CLOSED — RATIFIED** | E1 evidence does **not** block B1; E1 seeding stays gated; `E1-COV` remains CONDITIONAL |
| **PQ-8** | **CONFIRMED** | **CLOSED — RATIFIED** | Adopt the roadmap batch split as the **delivery sequence** (no architecture removal) |

**At analysis time**, because PQ-3 remained open and materially defines the B1 schema, the architecture
decision-closure document was deliberately NOT created (per the task's "if and only if the eight decisions
can be cleanly closed" rule). **Subsequently**, the PO decided PQ-3 (and ratified the other items), so the
**architecture closure record was created** as `CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md`
and the B1 contract was reconciled to the ratified `value_status` semantics.

**All eight decisions are now CLOSED.** B1 is eligible for a **separate** implementation authorisation task
(it is **not** auto-authorised).

---

## 20. B1 implementation authorisation status

**"Is B1 implementation authorised after this task?" — NO.**

This task only closes/recommends PO decisions. Even if all eight decisions were confirmed, a **separate
PO action must explicitly authorise** a bounded B1 implementation task. **No implementation prompt is
created.** B1 implementation remains **NOT AUTHORISED**.

## 21. Files created / modified
**Created (1):** `docs/cline/reports/CT-P8-B1-PO-DECISION-CLOSURE-20260912-010.md` (this report).
**Deliberately NOT created:** `docs/architecture/CARBONTALLY_PHASE8_B1_PO_DECISION_CLOSURE_20260912.md` — withheld because **PQ-3 requires a further material PO decision** (task §17 gate).
**Modified: none.** No other file was created, modified, moved or deleted.

## 22. Confirmation that no implementation occurred
**Confirmed.** No source code, database schema, migration, RLS policy, grant, API route, frontend,
configuration or production change. **No migration created, modified or run.** Nothing applied to
Supabase. The B1 contract, Disclosure Model design, Decision Record, roadmap, G0 report and forensic
reports were **not modified**. No implementation prompt created. Change set = **one Markdown report**.

## 23. Confirmation that no commit / push occurred
**Confirmed.** HEAD unchanged at `19e4f01c176eee5870f3c15038b6e7c68b23281c`; branch `main` (ahead 14);
staged 0; **208** pre-existing modifications preserved unchanged; untracked **65 (unchanged** — the report
is inside the already-untracked, collapsed `docs/cline/reports/`; the closure **architecture** document was
deliberately **not** created). No reset/checkout/clean/stash/restore/rebase/amend. **No commit. No push.**

---

## Final verdict

> **SUPERSEDED — PQ-1…PQ-8 are now CLOSED / RATIFIED** by task `CT-P8-B1-PO-DECISION-RATIFICATION-20260912-011`
> (authoritative record: `CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md`). The verdict below was
> correct **at the time of this analysis**, before the PO decided PQ-3.

### `B1 PO DECISION CLOSURE BLOCKED — ADDITIONAL PO DECISION/EVIDENCE REQUIRED` *(at analysis time — superseded)*

**Blocking item (at analysis time):** **PQ-3** — the proposed `disclosure_values.value_status` vocabulary was
**not semantically clean** (it overlapped `effective_class` in four values and conflated
value-materialisation with derived regulatory/applicability outcomes). A PO decision was required before the
B1 value-layer schema was final. **Seven of eight decisions (PQ-1, PQ-2, PQ-4, PQ-5, PQ-6, PQ-7, PQ-8) were
closable in the same PO action.**

**Post-ratification state:** all eight decisions are **CLOSED**; PQ-3 was decided (`effective_class`
authoritative; `value_status` = `PENDING`/`RESOLVED`/`UNRESOLVED`); the B1 contract was reconciled; the
architecture closure record was created. **B1 is ready for a separate implementation authorisation task.**

*STOP — read-only decision-closure complete. No implementation begun; B1/B2/P1/P2/Phase 8-X not started;
no implementation prompt created; nothing committed or pushed.*







