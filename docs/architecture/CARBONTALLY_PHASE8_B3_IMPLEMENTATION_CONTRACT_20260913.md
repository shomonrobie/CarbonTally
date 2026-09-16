# CarbonTally — Phase 8 Reporting / Disclosure

## Batch B3 — Disclosure Model Integration — IMPLEMENTATION CONTRACT

**Task identity:** `CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260913-031`
**Task type:** ARCHITECTURE + IMPLEMENTATION CONTRACT (this task authorises no implementation by itself; implementation proceeds under the PO blanket authorization `…050` once the open decision below is answered)
**Date:** 2026-09-13
**Repository baseline:** branch `main` · HEAD `37b19d13723b0b1eabceeade86ce1615a98ab400` · staged 0 · 218 pre-existing tracked modifications
**Environment baseline:** `carbontally_qa_phase8` (dedicated non-production QA; B1 + B2 applied and runtime-verified under `-029`)
**Predecessors (authoritative):** B1 contract + PQ-1…PQ-8 ratification · B2 contract (corrected `-021`) · B2 closure (`-028`) · B1/B2 QA application (`-029`) · Disclosure Model Design (§§6–§23) · Disclosure Model Decision Record (20 decisions) · P8X readiness (§20 B3 row, §29) · Phase 8-X ownership ruling (`-040`: **no Phase 9**)
**Evidence tags:** **[R]** repository/live fact · **[D]** ratified decision · **[V]** verified · **[U]** unresolved · **[I]** interpretation · **[REC]** recommendation

---

## 1. The single sentence that defines B3

> **B3 makes the ratified disclosure architecture *computed*: it projects CarbonTally's already-authoritative calculation and evidence data into disclosure values bound to framework requirements, purpose projections and a controlled intensity model — without recalculating, without inventing regulatory content, and without writing to any authoritative carbon figure.**

## 2. Root boundary (binding)

| Concern | Owner | B3's position |
|---|---|---|
| Calculation / emissions numbers | Calculation engine + `calculation_snapshots` | **Consume only.** B3 never recomputes an emission. |
| Evidence / line addressability | **B2** (closed) | **Consume** the B2 links (`disclosure_value_evidence.source_line_item_id`, `calculation_snapshots.source_line_item_id`). B3 must not alter B2 objects. |
| Extraction fidelity (8→1) | **P1** (separate, unauthorised) | Not B3. |
| Factor matching (EF-E) | **P2** (separate, unauthorised) | Not B3. |
| Narrative / finalisation / frozen artefact | **B4** | Not B3. B3 supplies the requirement/value spine B4 narrates against. |
| Report lifecycle states | **S1/S3** (verified under `-030`) | **Consume.** No new lifecycle states in B3. |
| Production RLS remediation | Separate security workstream (held) | Not B3. |
| Operational intelligence | **Phase 8-X** (in-programme; `-040`) | Not B3. |

## 3. Verified current state (live, `carbontally_qa_phase8`)

| Item | Value |
|---|---|
| B1 tables present | **11** (`disclosure_frameworks`, `_framework_versions`, `_requirement_versions`, `_requirement_mappings`, `_report_purposes`, `_report_purpose_versions`, `_purpose_requirements`, `_report_instance_binding`, `_applicability_assessments`, `_values`, `_value_evidence`) **[R]** |
| B2 objects present | `evidence_line_items`; `disclosure_value_evidence.source_line_item_id`; `calculation_snapshots.source_line_item_id` **[R]** |
| Seeded reference data | frameworks **3** (GHG_PROTOCOL primary, UK_SECR, ESRS_E1) · framework versions **26** · purposes **4** (ANNUAL_CARBON, MANAGEMENT, UK_SECR, ESRS_E1_QUANT) · purpose versions **24** · requirement versions **26** **[R]** |
| Seeded requirement identifiers | requirement codes are **placeholder identities** (`B1RT_*`, `B2RT_*`); `official_identifier` is **absent** for all (per `PQ-6` / `D17`: no invented identifiers) **[R]/[D]** |
| `disclosure_requirement_mappings` rows | **0** **[R]** |
| `disclosure_purpose_requirements` rows | **0** **[R]** |
| `disclosure_applicability_assessments` rows | **0** **[R]** |
| `disclosure_values` rows | **0** **[R]** |
| Intensity tables | **absent** (`disclosure_intensity_denominator_types`, `disclosure_intensity_ratios`) — design §22 lists 14 MVP tables; B1 delivered 11 + B2 delivered `evidence_line_items`; **intensity is B3's** per `PQ-1` ("Intensity → B3; B1 keeps 11 tables; `INTENSITY_RATIO` reserved") **[R]/[D]** |
| B1 helpers | `p8_disclosure_is_org_member`, `p8_disclosure_is_org_admin` **[R]** |

## 4. B3 deliverables

| # | Deliverable | Kind |
|---|---|---|
| **A** | `disclosure_intensity_denominator_types` + `disclosure_intensity_ratios` (new, additive) | migration |
| **B** | Projection engine: deterministic derivation of `disclosure_values` from the ratified `source_kind` producer set | domain/service |
| **C** | Requirement-mapping loader/validator (mechanism + identity-level seeds only) | domain/data |
| **D** | Applicability engine (period-dated, version-bound, `UNDETERMINED` first-class) | domain/service |
| **E** | Purpose projections (`purpose_code` on the instance binding; purpose→requirement subset/order) | domain/data |
| **F** | Value-status semantics (`effective_class`, `value_status`, `NOT_SUPPORTED` vs `CUSTOMER_INPUT_REQUIRED`) | domain |
| **G** | Value→line enumeration read model (the B2 join) | read model |
| **H** | Intensity selection service (controlled catalogue; customer selection recorded; no arbitrary denominator) | domain/API |
| **I** | Read/limited-write API surface for the above | API |
| **J** | RLS on the new tables + server-side authorization | security |
| **K** | Audit events on every B3 write | audit |
| **L** | Tests: static, pure, runtime (QA), ALLOW/DENY, idempotency | tests |

## 5. Explicit non-scope

1. Any change to the **calculation engine**, factor data, evidence classification or `emissions_logs`.
2. Any **E1 official identifier** or framework content that the authoritative evidence does not support (`E1-COV` **CONDITIONAL**; `D17`).
3. Per-gas/GWP (`GP-GAS` deferred) and base-year/recalculation (`GP-BY` deferred).
4. Narrative, finalisation, frozen artefact (B4); report lifecycle states (S1/S3 closed).
5. P1 extraction remediation; P2 EF-E; RLS remediation; Phase 8-X; Insight; D16 legacy route.
5a. **Inventing intensity catalogue contents** — see §19 decision **B3-D1** (evidence/PO gated).
6. Historical re-extraction or any backfill of `disclosure_values`.


---

## 6. Schema additions (normative, additive-only)

### 6.1 `public.disclosure_intensity_denominator_types` (global controlled catalogue)

| Column | Type | Rule |
|---|---|---|
| `id` | `uuid` | PK, default `gen_random_uuid()` |
| `code` | `varchar` | **UNIQUE**, NOT NULL — the controlled denominator code |
| `name` | `varchar` | NOT NULL — human label |
| `unit_hint` | `varchar` | NULL — e.g. `GBP`, `tCO2e/FTE` |
| `denominator_kind` | `varchar` | NOT NULL — enumerated: `FINANCIAL` · `PHYSICAL` · `HEADCOUNT` · `AREA` |
| `evidence_basis` | `text` | NULL — the authoritative basis (required for any row asserted as statutory) |
| `source_tier` | `smallint` | NULL — same tier vocabulary as B1 reference data |
| `is_active` | `boolean` | NOT NULL DEFAULT `true` |
| `created_at` / `updated_at` / `created_by` / `updated_by` | (B1 reference-data conventions) | |

**Rule:** a customer-authored denominator must be **rejected** (D11-CAT acceptance criterion). The catalogue is application-owned and closed (D4).

### 6.2 `public.disclosure_intensity_ratios` (organisation-scoped selection)

| Column | Type | Rule |
|---|---|---|
| `id` | `uuid` | PK |
| `organization_id` | `uuid` | NOT NULL, FK → `organizations(id)` |
| `report_version_id` | `uuid` | NOT NULL, FK → `report_versions(id)` |
| `denominator_type_id` | `uuid` | NOT NULL, FK → `disclosure_intensity_denominator_types(id)` **`ON DELETE RESTRICT`** |
| `numerator_disclosure_value_id` | `uuid` | NULL, FK → `disclosure_values(id)` **`ON DELETE SET NULL`** |
| `denominator_value` | `numeric` | NULL — the customer-confirmed denominator quantity |
| `denominator_unit` | `varchar` | NULL |
| `ratio_value` | `numeric` | NULL — **computed**, persisted; never hand-edited |
| `selection_basis` | `text` | NOT NULL — why this denominator (D11 rationale requirement) |
| `confirmed_by` | `uuid` | NULL — the Customer Owner/Admin who confirmed (D11) |
| `confirmed_at` | `timestamptz` | NULL |
| `created_at` / `updated_at` / `created_by` / `updated_by` | | |

**Uniqueness:** `UNIQUE (organization_id, report_version_id, denominator_type_id)`.
**Rule (ratified):** CarbonTally may **recommend** a denominator but must **never silently select** one; the selection and its basis are persisted (D11-CAT).

### 6.3 Migration shape

Two additive migrations, ordered strictly after B2's `20260916…`:

1. `20260917000000_p8_b3_intensity_catalogue.sql` — create `disclosure_intensity_denominator_types`; enable RLS; grant posture mirroring B1 reference tables; **seed rows only if `B3-D1` supplies evidence-backed content — otherwise the table is created empty and seeding is a separate authorised step**.
2. `20260917010000_p8_b3_intensity_ratios.sql` — create `disclosure_intensity_ratios`; guarded FKs + indexes; RLS enabled with org-member policies (**Customer Owner/Admin write; Member read; Viewer read; PE no access**), mirroring the ratified B1 policy posture; **no trigger; no retention artefact** (the B2-D11 analogue).

**Idempotency:** `CREATE TABLE IF NOT EXISTS`, guarded constraint/policy blocks keyed on `pg_constraint.conname`/`pg_policies.policyname`; re-apply must be `rc=0` with zero schema delta (the V1R/V2 standard proven again in `-029`).

---

## 7. Projection engine (deliverable B)

### 7.1 The producer registry (closed set — no DSL)

The ratified `disclosure_values.source_kind` enumeration is the **only** set of producers **[D]** (design §…: `CALCULATION_AGGREGATE` · `EMISSIONS_LOG_AGGREGATE` · `FACTOR_PROVENANCE` · `EVIDENCE_COMPLETENESS` · `ENERGY_ACTIVITY` · `INTENSITY_RATIO` · `PRIOR_PERIOD_VALUE` · `ORG_PROFILE_FACT` · `CUSTOMER_INPUT`).

B3 implements a **registry** of registered producers. Adding a producer is a code change plus a contract amendment — **never** a data-driven rule (D4: no generic rules engine).

### 7.2 Projection rules (normative)

| `source_kind` | Derivation | Must never |
|---|---|---|
| `CALCULATION_AGGREGATE` | Aggregate persisted `calculation_snapshots` rows for the reporting period, grouped by the requirement's scope/category hints | recompute an emission; use `mapped_data` as a numeric source |
| `EMISSIONS_LOG_AGGREGATE` | Aggregate `emissions_logs` for the period (the same authoritative rows the engine wrote) | bypass `snapshot_id` lineage |
| `FACTOR_PROVENANCE` | Read `factor_kind`/`factor_id`/`customer_factor_id` from the snapshots used | invent factor data |
| `EVIDENCE_COMPLETENESS` | Compute coverage from `disclosure_value_evidence` + B2 line links | treat a missing line row as zero evidence without stating the reason |
| `ENERGY_ACTIVITY` | Aggregate activity quantities/units from snapshots | convert units outside the central normaliser |
| `INTENSITY_RATIO` | Read the persisted `disclosure_intensity_ratios` row | compute a ratio not selected/confirmed by the customer |
| `PRIOR_PERIOD_VALUE` | Read a prior `disclosure_values` row for the same requirement/period semantics | rewrite the prior row |
| `ORG_PROFILE_FACT` | Read the organisation profile/facility facts | fabricate a characteristic |
| `CUSTOMER_INPUT` | Read customer-supplied input for the requirement | treat absence as zero |

### 7.3 Determinism, idempotency and immutability

* A projection run for `(report_version_id, requirement_version_id)` is **deterministic** given the same inputs.
* Re-running must be **idempotent**: upsert on the natural key, no duplicate rows, no history rewrite.
* `computed_at` records the run; a later run updates the *current* value only for non-finalised versions and **never** mutates a finalised version's values (D15, `DM-5`).
* Every projection writes a canonical append-only audit event (`audit_trail`; `CAT_REPORT`-class, action `disclosure.value.projected`).

---

## 8. Framework / requirement mapping (deliverable C)

**Mechanism in B3; content is evidence-gated.** B3 implements the loader/validator for `disclosure_requirement_mappings` (requirement → CarbonTally producer/activity linkage) and the `disclosure_purpose_requirements` subset/order loader.

**Ratified constraints:**
* `DM-1` — requirement codes are **version-bound**; no internal key is presented as an official identifier (D17).
* `PQ-6` — identities are seedable with evidence/PO confirmation; **no invented version rows and no invented E1 identifiers**.
* `E1-COV` remains **CONDITIONAL** — E1 content may be represented as `NOT_SUPPORTED` / `CUSTOMER_INPUT_REQUIRED` (`DM-5`), never estimated.

**Therefore:** B3 ships the mechanism and the identity-level seeds already present; it does **not** author mapping content. Any mapping row beyond identity level requires the same evidence/PO confirmation as E1 identifiers.

---

## 9. Applicability engine (deliverable D)

**Ratified (`APPL`, D13) — implemented literally:**

1. Inputs: organisation characteristics captured in `disclosure_applicability_assessments.characteristic_snapshot` (jsonb) drawn **only** from real org/profile/facility facts; the assessment is **period-dated** (`reporting_period_start/end`, `reporting_year`) and **framework-version-bound** (`framework_version_id`).
2. Outputs: `assessed_status` ∈ {`APPLICABLE`, `NOT_APPLICABLE`, `UNDETERMINED`} with a mandatory human-readable `basis`.
3. **`UNDETERMINED` is first-class** — insufficient information must produce `UNDETERMINED`, never a default to `NOT_APPLICABLE` (ALLOW/DENY test required).
4. **Never a legal determination** — no output text may assert legal advice or a legal conclusion; the product surface must state the basis is CarbonTally's recorded assessment.
5. Changing an assessment does **not** silently rewrite historical values: a re-assessment creates a new version (`version` column) bound to the period.

---

## 10. Purpose projections (deliverable E)

**Ratified (`DM-2`):** `purpose_code` and `report_type` remain separate; the single-entry `SUPPORTED_REPORT_TYPES` (`annual`) is **not** redefined or expanded; purpose is carried as a **projection on the instance binding** (`disclosure_report_instance_binding.purpose_version_id`).

Implementation: the four seeded purposes (ANNUAL_CARBON, MANAGEMENT, UK_SECR, ESRS_E1_QUANT) are represented as purpose versions; a purpose projection is an **ordered subset** of requirement versions (`disclosure_purpose_requirements.display_order`, `required_for_finalisation`) — it is **not** a second report engine (ratification §2.1/§2.3; D6-R). Templates remain **presentation only** (D3; `template_structure` is not a disclosure model).

---

## 11. Value status semantics (deliverable F)

| Element | Ratified rule |
|---|---|
| `effective_class` | Authoritative classification of the requirement for this instance (`PQ-3`) |
| `value_status` | Only `PENDING` · `RESOLVED` · `UNRESOLVED` (`PQ-3`) |
| Requirement classes | Required · Conditional · Optional · Not Applicable · Unavailable · **Customer Input Required** · Not Supported/Future (D12) |
| `NOT_SUPPORTED` vs `CUSTOMER_INPUT_REQUIRED` | **Never conflated** (`DM-5`, §8 of the Decision Record). `NOT_SUPPORTED` = CarbonTally cannot produce it; `CUSTOMER_INPUT_REQUIRED` = the customer must supply it |
| `reason` | Mandatory free-text explanation whenever the status is not `RESOLVED` |

---

## 12. Value→line enumeration read model and API (deliverables G, H, I)

### 12.1 Read model (the B2 join)

```sql
SELECT dv.id AS disclosure_value_id, cs.id AS calculation_snapshot_id,
       eli.id AS evidence_line_item_id, eli.line_number, eli.source_page,
       eli.raw_description, eli.raw_quantity, eli.raw_unit, eli.materialisation_kind
  FROM public.disclosure_values dv
  JOIN public.disclosure_value_evidence dve ON dve.disclosure_value_id = dv.id
  LEFT JOIN public.calculation_snapshots cs ON cs.id = dve.calculation_snapshot_id
  LEFT JOIN public.evidence_line_items eli
         ON eli.id = COALESCE(dve.source_line_item_id, cs.source_line_item_id)
 WHERE dv.report_version_id = $1;
```

(The `COALESCE` is the B2 contract §14.2 shape: the snapshot link is the primary fact; the `dve` column covers snapshot-less evidence.)

### 12.2 API boundary

| Endpoint (proposed, minimal) | Method | Who | Purpose |
|---|---|---|---|
| `/api/v3/reports/{report_id}/disclosure` | GET | org member (RLS + server-side check) | The projected disclosure set for a report version |
| `/api/v3/reports/{report_id}/disclosure/{value_id}/lines` | GET | org member | Value→line drill-down (`DM-6` read model only; UI is B4) |
| `/api/v3/reports/{report_id}/disclosure/project` | POST | Customer Owner/Admin (+ consultant per ratified consultant model) | Run/refresh projections for a non-finalised version |
| `/api/v3/reports/{report_id}/intensity` | GET/POST | Owner/Admin write; Member/Viewer read | Select/confirm a denominator from the controlled catalogue |
| `/api/v3/organizations/{org_id}/applicability` | GET/POST | Owner/Admin write | Record an applicability assessment |

**Rules:** no endpoint may write a calculated value; authorization is enforced **server-side** (UI is never the boundary); unknown/absent catalogue rows must return a meaningful 4xx with an explanation, never a raw database error.


---

## 13. Authorization / tenancy / security (deliverable J)

1. **RLS enabled** on both new tables (no table is created with RLS off).
2. Policies follow the **ratified B1/B2 posture**: org-member read; Customer Owner/Admin write for ratio selection; **no PE access**; no cross-tenant visibility; the catalogue is **global read-only** reference data for authenticated users.
3. **Server-side authorization** for every write; the UI is never the boundary (AGENTS.md §44).
4. **No `FORCE RLS`** (the ratified deferred posture; B3 makes no new security claim).
5. **No production RLS remediation** — B3 touches no pre-existing policy, grant or RLS flag; the V2 parity standard must be re-proved on a clone.
6. `A-RLS` (report-table RLS posture) remains a **separate open decision** and must not be widened into B3.

## 14. Audit (deliverable K)

Reuse the canonical append-only `audit_trail` substrate (no new audit mechanism):

| Event | When |
|---|---|
| `disclosure.value.projected` | each projection run (per value) |
| `disclosure.value.status_changed` | status transitions |
| `disclosure.applicability.assessed` | each new applicability assessment version |
| `disclosure.intensity.selected` | denominator selection/confirmation |
| `disclosure.mapping.loaded` | mapping / purpose-subset load (run-level summary) |

No secret, token or signed URL may appear in any audit payload.

## 15. Historical reproducibility (D15, `DM-7`)

* Values are bound to **`report_version_id` + `requirement_version_id` + framework version**, so a historical report remains reproducible.
* B3 must **not** rewrite historical rows: no retro-projection of past versions, no backfill of `disclosure_values`, no history repair.
* Records that cannot be derived honestly remain `UNRESOLVED` / `NOT_SUPPORTED` with a reason — never a manufactured value.

## 16. Test / verification contract (deliverable L)

### 16.1 Layers

| Layer | Content |
|---|---|
| Static | migration-text guards (RLS enabled, additive-only, guarded constraints, no destructive statement); contract-clause mapping |
| Pure/unit | projection-registry determinism; aggregation semantics; status semantics; applicability `UNDETERMINED` preservation; ratio validation (arbitrary denominator rejected) |
| Runtime (QA) | apply + re-apply migrations (`rc=0`, zero schema delta); projection run over real snapshots; idempotent re-run; value→line join returns real B2 lines; RLS ALLOW/DENY via `SET ROLE` + claims emulation |
| Security | cross-tenant DENY; PE→disclosure DENY; Viewer→write DENY; Member→admin-only-op DENY |
| Regression | B1/B2 runtime (36) + B1/B2 unit (75) + S1/S3 (89) suites must remain green |

### 16.2 Rules

* Runtime suites **must execute** against `carbontally_qa_phase8`; **a skipped suite is not a PASS**.
* Existing tests are **amended, never deleted**.
* Every acceptance criterion in §20 must be executed, not asserted.


---

## 17. Migration strategy

| # | Migration | Shape |
|---|---|---|
| B3-1 | `20260917000000_p8_b3_intensity_catalogue.sql` | new global catalogue table + RLS + policy; **seeding only if `B3-D1` content exists** |
| B3-2 | `20260917010000_p8_b3_intensity_ratios.sql` | new org-scoped table + guarded FKs/indexes + RLS policies |

* Strictly after `20260916010000` (B2).
* Additive-only; no existing object altered; no row of any pre-existing table written.
* Apply to **QA only**; production remains prohibited (G0-D).
* Documented rollback: `DROP TABLE disclosure_intensity_ratios`, then `DROP TABLE disclosure_intensity_denominator_types` (nothing pre-existing is rewritten).

## 18. Environment and rollout

* Implementation and runtime verification occur on **`carbontally_qa_phase8`** (non-production, dedicated, persistent) — established in `-029`.
* Independent verification (gate **V3**) re-uses the disposable privileges-inclusive clone method (V1R/V2 precedent).
* **Backfill: not authorised.** Production: not authorised.

## 19. Decision register (`B3-Dn`)

| ID | Decision | Status | Basis |
|---|---|---|---|
| **B3-D1** | **Intensity denominator catalogue contents** (which denominator types exist, with their statutory/authoritative basis) | **OPEN — PO DECISION REQUIRED** | `D11-CAT` is RATIFIED as a *controlled-catalogue mechanism*, but its boundary states the **exact catalogue contents and statutory treatment must be verified before implementation**; playbook `B3-PO-5`; `E1-COV` CONDITIONAL |
| **B3-D2** | Implementation proceeds with the catalogue table **empty** while `B3-D1` is pending | **DECIDED (this contract)** | The mechanism is ratified; only the content is gated. Avoids inventing denominators while unblocking schema + mechanism work |
| **B3-D3** | `purpose_code` is a projection; `report_type` semantics unchanged | **RATIFIED** | `DM-2` |
| **B3-D4** | Applicability period-dated, version-bound, `UNDETERMINED` first-class, never legal advice | **RATIFIED** | `APPL` / D13 |
| **B3-D5** | `value_status` limited to `PENDING`/`RESOLVED`/`UNRESOLVED`; `effective_class` authoritative | **RATIFIED** | `PQ-3` |
| **B3-D6** | `NOT_SUPPORTED` ≠ `CUSTOMER_INPUT_REQUIRED` | **RATIFIED** | `DM-5`, Decision Record §8 |
| **B3-D7** | E1 official identifiers may remain absent; E1 content expressed honestly as unsupported/conditional | **RATIFIED + evidence-gated** | `E1-COV` CONDITIONAL, `PQ-6`, `PQ-7`, `D17` |
| **B3-D8** | B3 authors no mapping content beyond identity level | **DECIDED (this contract)** | `PQ-6`; mechanism-only scope |
| **B3-D9** | Intensity placement in B3 (2 new tables) | **RATIFIED** | `PQ-1` |
| **B3-D10** | No triggers; app-layer validation; no retention artefact on the new tables | **DECIDED (this contract)** | mirrors `B2-D11`, `PQ-4` |
| **B3-D11** | Per-gas and base-year remain out of B3 | **RATIFIED** | `GP-GAS`, `GP-BY` deferred |
| **B3-D12** | Drill-down is a **read model in B3**; UI belongs to B4 | **DECIDED (this contract)** | playbook `B3-PO-7`; roadmap §20 B4 row |

**Only `B3-D1` is a genuine open PO decision.** It blocks only catalogue *seeding* and denominator-offering features — not deliverables A (schema), B–G, J–L.

---

## 20. Acceptance criteria (gate **V3**)

| # | Criterion | Evidence |
|---|---|---|
| A1 | B3 migrations apply and re-apply (`rc=0`) with zero schema delta on a production-shaped clone | migration logs + diff |
| A2 | B1+B2 objects and the 116 pre-existing tables are unchanged (parity) | clone harness |
| A3 | Projections deterministic and idempotent; no duplicate rows; no history rewrite | runtime probes |
| A4 | No emission recomputed; every number resolves to a persisted snapshot/log | provenance probes |
| A5 | Value→line enumeration returns real B2 `evidence_line_items` rows via the `COALESCE` join | runtime probe |
| A6 | `UNDETERMINED` applicability preserved, never coerced | ALLOW/DENY test |
| A7 | Arbitrary (customer-authored) denominator rejected; selection + basis persisted | negative test |
| A8 | `NOT_SUPPORTED` and `CUSTOMER_INPUT_REQUIRED` not conflated | status test |
| A9 | Cross-tenant, PE, Viewer-write and Member-admin denials hold server-side | security tests |
| A10 | Audit events emitted for every B3 write; no secret logged | audit queries |
| A11 | S1/S3/B1/B2 suites remain green (no regression) | regression run |

---

## 21. Verdict

### `B3 CONTRACT COMPLETE — ONE PO DECISION REQUIRED (B3-D1); IMPLEMENTATION OTHERWISE AUTHORISED AND UNBLOCKED`

B3 is fully specified against the ratified decisions (`DM-2`, `APPL`, `PQ-1`, `PQ-3`, `PQ-4`, `PQ-6`, `PQ-7`, `DM-1`, `DM-5`, `DM-6`, `DM-7`, `D11-CAT`, `D15`, `D17`, `E1-COV`) and the live QA state. Every deliverable except the intensity **catalogue content** can be implemented immediately; `B3-D1` is raised to the PO as a compact decision, and its absence is handled by shipping the catalogue table **empty** (no invented denominators) rather than by stalling the batch.

---

## 22. Amendment 1 — `B3-D1` ANSWERED by PO (2026-09-13) and schema corrections

### 22.1 The answered decision

> **PO direction:** CarbonTally must remain architecturally capable of supporting intensity metrics. The four candidates (net revenue/turnover, floor area, FTE headcount, physical output) **remain candidates for the controlled catalogue**. None may be labelled a statutory SECR/ESRS E1 requirement merely because it is plausible or commonly used. **Framework-specific statutory/evidence assertions must be kept separate from the generic denominator definition.** No official SECR/E1 requirement or identifier may be invented. `evidence_basis`, `source_tier`, framework applicability (or equivalent) must distinguish: generic CarbonTally-supported · framework-supported · statutory/mandatory · evidence-not-yet-verified. Nothing may be seeded as statutory without authoritative evidence.

**Governing distinction:** **CarbonTally denominator capability ≠ regulatory requirement.**

### 22.2 What this changed in the implementation

| Element | Original contract | As implemented (and why) |
|---|---|---|
| Catalogue table | one table carrying `unit_hint`/`source_tier`/`evidence_basis` | **split in two**: `disclosure_intensity_denominator_types` carries **only** the generic capability (`support_class` restricted to `CARBONTALLY_SUPPORTED` by CHECK); all framework claims live in `disclosure_intensity_denominator_framework_links` | separates capability from obligation (PO) |
| Statutory claims | prose rule | **structural CHECK**: `treatment = 'STATUTORY_REQUIRED'` requires `evidence_basis` + `source_tier` + `verified_at`; `official_reference` requires `verified_at` | makes an unverified statutory claim impossible |
| Seeds | candidates + framework content | **4 generic candidates only; framework-link table seeded EMPTY** | with no authoritative evidence, the honest record is the absence of a claim |
| `selection_source` | not specified | `CUSTOMER_SELECTED` / `CUSTOMER_CONFIRMED` / `CARBONTALLY_RECOMMENDED`, and a **RECOMMENDED row cannot carry a confirmation stamp** (CHECK) | implements "may recommend, never silently select" (`D11-CAT`) |

### 22.3 Correction to §9 (authoritative B1 vocabulary)

The applicable B1 CHECK vocabulary is **`APPLIES` · `DOES_NOT_APPLY` · `UNDETERMINED` · `CUSTOMER_INPUT_REQUIRED`** (verified live in `disclosure_applicability_assessments`). §9's illustrative wording (`APPLICABLE`/`NOT_APPLICABLE`) is superseded by this vocabulary; the ratified rule is unchanged.

### 22.4 Remaining B3 deliverables (not yet implemented)

The projection engine (§7), mapping loader (§8), applicability engine (§9), purpose projections (§10), value-status semantics (§11), value→line read model and API (§12), plus the service layer and the full test contract (§16). Gate **V3** therefore remains **open** (partially evidenced).

---

## 23. Amendment 2 — the 12 PO decisions of 2026-09-14 recorded; B3 status reconciled

**Date:** 2026-09-14 · **Task:** `CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260913-031`
**Full record:** `docs/architecture/CARBONTALLY_PHASE8_B3_PO_DECISION_RECORD_20260914.md`

### 23.1 Purpose and standing

The PO ratified **12 further decisions** on 2026-09-14 governing B3's calculation,
framework/requirement, applicability, purpose, intensity, value-status, drill-down,
evidence-gap, environment, API and historical behaviour. They are recorded as
**`D-B3-1`…`D-B3-12`** and are **consistent with this contract**; they are therefore
recorded here as *governing* rather than as a replacement for any clause.

**No other B3 contract was created.** This batch already has exactly one authoritative
contract (this document). Producing a second would create competing governance artefacts
(AGENTS.md §4/§63), so the decisions were recorded as this amendment. The task instruction
that asked for a newly created contract is **explicitly deviated from, and flagged for PO
overrule** if a different form was intended.

### 23.2 Decision → contract clause map

| Decision | Governs | Contract clause(s) | As-built conformance |
|---|---|---|---|
| `D-B3-1` authoritative calculation data | projections read persisted data only; extraction is evidence | §2, §7.2 | conforms (`…051` §2 B: no emission recomputed) |
| `D-B3-2` framework + version identified | framework/version binding | §8, §15 | conforms — bound via `requirement_version_id` → framework version (transitive; no direct column) |
| `D-B3-3` requirement sets explicit/versionable | requirement + mapping mechanism | §8 | conforms (identity-level only; content evidence-gated per `B3-D7`/`B3-D8`) |
| `D-B3-4` applicability deterministic from persisted inputs | applicability engine | §9 (+ Amendment 1 §22.3 vocabulary) | conforms (`disclosure_applicability_assessments` persisted, read by projection; `UNDETERMINED` preserved) |
| `D-B3-5` controlled purpose codes | purpose projections | §10 | conforms (`DM-2`, catalogue-seeded) |
| `D-B3-6` explicit denominator value/unit/context | intensity model | §6 (+ Amendment 1 §22.2) | conforms (3 tables; framework claims separated and evidence-gated) |
| `D-B3-7` controlled value-status model | value status semantics | §11 | conforms (`PENDING`/`RESOLVED`/`UNRESOLVED`; `effective_class` authoritative) |
| `D-B3-8` auditable drill-down | value→line read model + boundary | §12.1, §12.2 (`B3-D12`) | conforms (7 endpoints; UI deferred to B4) |
| `D-B3-9` evidence gaps explicit | gap representation + effect on status | §11, §15 | **representation conforms**; **effect on reporting/finalisation status UNDETERMINED** → new decision `D-B3-13` |
| `D-B3-10` persistent non-production environment | environment baseline | §18 | conforms in substance — `carbontally_qa_phase8` holds S3+B1+B2+B3; deployment still **not** authorised (`C-B3-2` confirmation) |
| `D-B3-11` minimum API surface | API boundary | §4, §12.2 | conforms (7 B3 endpoints; the 6 co-located endpoints belong to the separately closed B4 batch) |
| `D-B3-12` historical/finalised binding | reproducibility + immutability | §15 | conforms (`UNIQUE (report_version_id, requirement_version_id)`; no retro-projection/backfill; `APPROVED`/`FINAL` immutable) |

### 23.3 The one item requiring a further PO decision

`D-B3-9` requires the contract to define how an evidence-gap state **affects
calculation/reporting status**. The 12 decisions and the existing artefacts do **not**
determine this (today gaps are represented but do not block approval/finalisation).
It is raised as **`D-B3-13`** — see the decision record §4. **No rule has been invented
here**, and no implementation change is proposed by this amendment.

### 23.4 Status

* **B3 remains CLOSED** (`…051`). This amendment does **not** re-open B3, does not
  re-verify it, does not re-close it, and does not authorise any new B3 implementation.
* No clause of this contract is superseded except where Amendment 1 already corrected §9.
* The as-built implementation is unchanged by this amendment (documentation only).

