# CT-P8-DISCLOSURE-MODEL-DESIGN-20260912-004

**Task reference:** `CT-P8-DISCLOSURE-MODEL-DESIGN-20260912-004`
**Date:** 2026-09-12
**Type:** PHASE 8 DISCLOSURE MODEL — **ARCHITECTURE / DESIGN ONLY. NO IMPLEMENTATION.**
**Governing decisions:** D1–D17 (treated as fixed; **no PO decision changed or made**)
**Final verdict:** `DESIGN COMPLETE — READY FOR PO REVIEW`

---

## 1. Objective

Produce the reviewed design for the Phase 8 **Disclosure Model** layer — the layer that sits between CarbonTally's authoritative carbon calculation/provenance/evidence foundation and its report presentation — such that (a) one calculation foundation feeds the four ratified report purposes, (b) **row-level/line-item evidence traceability works in both directions**, (c) **regulatory applicability is distinguished from CarbonTally capability**, and (d) framework/requirement/mapping versions are explicit so historical reports remain reproducible. **Design only.**

## 2. Documents read

| # | Document | What was taken from it |
|---|---|---|
| 1 | `…REPORTING_ARCHITECTURE_PO_RATIFICATION_D1-D17_20260912.md` | The full D1–D17 register (§§2–3, lines 1–1087) |
| 2 | `…REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md` | §§5–24 incl. the §24 evidence-completion section and §24.11 verdict |
| 3 | `CT-P8-REPORTING-REGULATORY-EVIDENCE-CLOSURE-20260912-002.md` | Prior closure status and source register |
| 4 | `CT-P8-REPORTING-REGULATORY-EVIDENCE-COMPLETION-20260912-003.md` | Five-gap outcome: G4 closed; G2/G3/G5 partial; **G1 unresolved** |
| 5 | `…REPORTING_LIFECYCLE_SPEC_20260912.md` | **§4 authoritative catalogue (exactly one type: `annual`), §4.2 the 12 engine sections, §4.4 type/instance/version/artefact, §5 normative definitions, §12–§16** |
| 6 | `…PRODUCT_AND_REPORT_RATIFICATION_20260912.md` | Report catalogue, assurance positioning, RBAC/report-scope model |
| 7 | `…OPEN_DECISION_CLOSURE_AND_IMPLEMENTATION_AUTHORISATION_20260912.md` | §7.1–7.5 S1 boundary + latent `is_current` defect; legacy disposition boundary |
| 8 | `…ASK_CARBONTALLY…AI_AUDITABILITY_DISCOVERY_20260912.md` | Audit-ledger architecture, taxonomy, append-only enforcement, overlapping log tables warning |
| 9 | `…CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` | Boundary between insight/AI and the disclosure layer (AI output is not authority) |
| 10 | `CARBONTALLY_PHASE7_CLOSURE_AND_RELEASE_BOUNDARY_20260912.md` | `not_assurance` markers; auditability purpose boundary (no surveillance) |
| — | `CT-P8-REPORTING-S4-NARRATIVE-OVERLAY-20260912-001.md` | S4 **HARD STOP** — confirmed not implemented and not authorised |
| — | `…PHASE8_DISCOVERY_AND_CAPABILITY_GAP_ANALYSIS_20260912.md` | §5 reporting archaeology; §6 authoritative calculation/evidence source |

## 3. Repository areas inspected

**Migrations (56 files, `supabase/migrations/`)** — full `CREATE TABLE` and `ALTER TABLE … ADD COLUMN` inventory extracted programmatically; specific migrations read in full: `20260823010000_d33_evidence_traceability.sql`, `20260913000000_p8_report_lifecycle_status.sql`, `20260912000000_p7_audit_immutability_and_indexes.sql`, `20260807020000_add_calculation_snapshots.sql`, `20260807040000_add_domain_events.sql`, `20260807050000_add_factor_aliases.sql`, `20260807000000_add_import_batches.sql`, `20260810020000_v3m3_customer_factors.sql`.

**Backend** — `engines/report_generation.py`, `engines/pdf_render.py` (referenced), `report_generator.py` (legacy), `api/v3_reports.py`, `api/v3_reporting.py`, `routes/reports.py`, `data/reports.py`, `data/reporting.py`, `data/report_versions.py`, `data/organizations.py`, `domain/evidence.py`, `domain/audit.py`, `domain/report_lifecycle.py` (referenced), `auth.py`, `api/dependencies.py`, `api/v3_operations.py`, `api/v3_processing_workflow.py`, `pdf_engine.py`, `utils/document_classifier.py`, `routes/admin/document-types.py`.

**Schema searches** — framework/disclosure/requirement/applicability/narrative table search (**none found**); per-gas/GWP/energy/base-year/uncertainty column search (**none except `organization_metadata.renewable_energy_percentage`, `energy_intensity`**); `report_generation_queue` RLS policy search; `template_structure` usage search.

**Tests referenced (not executed)** — `test_v3_report_lifecycle.py`, `test_v3_reports.py`, `test_report_generation.py`, `test_pdf_render.py`.

## 4. Design findings

1. **[I] The disclosure layer is the only genuinely missing layer.** The ratified chain (D2) is half-built already: authoritative data, calculation/provenance, evidence, presentation and lifecycle all exist and are verified. What does not exist is **framework → version → requirement → applicability → value → narrative binding**. The design is therefore an **addition of a small layer**, not a re-architecture.
2. **[REC] Two classification axes, not one.** `requirement_class` (what the law says: REQUIRED/CONDITIONAL/OPTIONAL/NOT_APPLICABLE/CUSTOMER_INPUT_REQUIRED/UNDETERMINED/NOT_SUPPORTED/FUTURE) belongs to the **requirement version**; the *effective* class is **derived** from the applicability assessment. This satisfies D9/D12/D13 and is why a boolean cannot work.
3. **[REC] Applicability must be period-dated.** Verified evidence shows UK SECR thresholds changed for financial years beginning on/after **6 Apr 2025** and are in active reform, and the CSRD is a **three-act chain** (2022/2464 + 2025/794 + **2026/470**). A global "current framework" or hard-coded threshold is factually wrong.
4. **[REC] One value, many purposes.** `disclosure_values` (one row per requirement version per report version) is the shared intermediate; purpose projections reorder/subset it — preventing four independent report engines (D6-R).
5. **[D] No new report spine.** The existing instance (`report_generation_queue.id`) + version (`report_versions`) + lifecycle (`status`) spine is bound to, never replaced.
6. **[D] No generic engine.** All variation is enumerated vocabulary + versioned configuration.
7. **[I] Compliance-claim risk remains concentrated in the legacy surface.** The legacy PDF generator emits a **"6. Compliance Statement"** section; that is D16 work, untouched.

## 5. Existing-schema findings

| Finding | Evidence |
|---|---|
| **No framework/requirement/disclosure/applicability/narrative/mapping table exists** | Exhaustive `CREATE TABLE` scan across all 56 migrations returned **zero** matches |
| **No per-gas or GWP columns anywhere** | `emission_factors.co2e_multiplier`, `calculation_snapshots.co2e_kg` only |
| **No Scope 2 location/market distinction** | single `scope` text on `emissions_logs` / `calculation_snapshots` |
| **No base year / recalculation model** | no matching columns |
| **No energy-mix model** | only `organization_metadata.energy_intensity` / `renewable_energy_percentage` (org profile metrics) |
| **Report/version/lifecycle spine exists and is sufficient for binding** | `report_generation_queue` (instance) + `report_versions` (`UNIQUE (report_id, version_number)`, `is_current`, `status`) |
| **Lifecycle vocabulary already ratified** | `status ∈ {DRAFT, REVIEWED, CHANGES_REQUESTED, REJECTED, APPROVED, FINAL}` (`20260913000000`) |
| **Audit ledger is append-only at the DB level** | trigger `p7_audit_trail_immutable` raises for every role incl. service role |
| **`calculation_snapshots` is an immutable forensic record** | SHA-256 `content_hash`, `algorithm_version`, `methodology`, exactly-one-factor XOR check, deterministic `request_id` |
| **`customer_factors` already models versioning** | `version`, `effective_from/to`, `status`, `source_reference` — a strong reuse precedent |
| **`units` is the central normalisation registry** | `conversion_factor` column |
| **`activity_categories` already carries framework taxonomy** | `esrs_e1_category`, `issb_category`, `ghg_protocol_scope`, `ghg_protocol_category` |
| **`report_templates.template_structure` is unused by the backend** | no Python reference found — must stay presentation-only |
| **Org framework booleans exist** | `organizations.secr_enabled` / `esrs_enabled` / `issb_enabled` (`api/v3_organizations.py`) |
| **No RLS policy found referencing `report_generation_queue`** | policy search returned none (recorded as an observation, **not** a remediation) |

## 6. Evidence / provenance findings

* **[R] The document→calculation evidence chain already exists** (`20260823010000_d33_evidence_traceability.sql`): `organization_files ←(file_id)— manual_extraction_items ←(source_item_id)— calculation_snapshots ←(snapshot_id)— emissions_logs`, with `source_file`, `source_page`, `ON DELETE SET NULL` FKs and two indexes.
* **[R] Human-readable evidence presentation already exists** (`backend/domain/evidence.py`, D33.1): chain "source document → extracted line → mapping → emission factor → calculation → emission result", stable identifiers for auditors, and honest **COMPLETE / PARTIAL / UNAVAILABLE** classification.
* **[R] Evidence-readiness metrics already exist** (`backend/data/reporting.py`): `calculations_with_source`, `evidence_complete/partial/unavailable`, `open_issues`, plus the explicit non-assurance notice.
* **[I] Therefore the Disclosure Model adds only two links**: `disclosure_values → disclosure_value_evidence → calculation_snapshots`, plus the line-item hop (§7).

## 7. Row-level traceability findings

* **[R] Line items DO exist — but only inside JSONB.** `extracted.line_items` and `mapped_data.line_items` are read/written in `api/v3_operations.py` (explicit comment: *"the per-line results are stored back into `mapped_data.line_items`"*) and `api/v3_processing_workflow.py`; invoice-class document types exist (`invoice_electricity/gas/water/fuel/services`); `pdf_engine._parse_fuel_invoice()` is already line-item aware.
* **[I] The genuine gap:** line items are **not addressable rows**, so a value cannot point at *INV-123 line 3*. `calculation_snapshots.source_item_id` reaches only the **document-level** item plus a page.
* **[REC] Closure design:** `evidence_line_items` (addressable row extracted from the existing JSONB, parented to `manual_extraction_items`) + one additive nullable `calculation_snapshots.source_line_item_id` FK + `disclosure_value_evidence` for aggregates. **Nothing is re-extracted and no source data is copied.**
* **[D] Honesty rule:** where no finer granularity exists (manual single figure), the row is synthetic with `row_reference = NULL` and the classification stays `PARTIAL`. **No artificial granularity is fabricated.**
* **[REC] Format-agnostic:** the same concept covers utility bills, fuel, travel, purchase records, meter readings, CSV/XLSX source rows and manual entries.

## 8. Framework / version findings

* **[V] All three frameworks are live-version-changing** — CSRD three-act chain (2022/2464 + 2025/794 + **2026/470**, OJ L 470, 26.2.2026); ESRS 2023 set in force vs **2026 Simplified ESRS adopted but NOT in force**; SECR thresholds changed 6 Apr 2025.
* **[REC] Model:** `disclosure_frameworks` → `disclosure_framework_versions` (`status ∈ IN_FORCE / ADOPTED_NOT_IN_FORCE / SUPERSEDED / WITHDRAWN`, `source_tier` per D17, `legal_reference`) → `disclosure_requirement_versions` → `disclosure_requirement_mappings` (versioned).
* **[D] The 2026 ESRS revision is represented as `ADOPTED_NOT_IN_FORCE` with no application date — never as the implementation basis.**
* **[REC] Immutability:** versions referenced by a finalised report are never mutated; corrections create a new version and supersede the old one.

## 9. Applicability findings

* **[V] Rules are now evidenced** for UK SECR (in-scope populations; **>40,000 kWh**; 2-of-3 over two consecutive FYs; 6 Apr 2025 threshold change) and CSRD/ESRS (date-dependent phases; 2026 scope amendment; Ireland via S.I. 336/2024).
* **[REC] Design:** `disclosure_applicability_assessments` stores the **characteristic snapshot** (reusing existing `organizations` fields), the **status** (`APPLIES` / `DOES_NOT_APPLY` / `UNDETERMINED` / `CUSTOMER_INPUT_REQUIRED`), the **basis**, the actor and the date.
* **[D] CarbonTally never makes a legal determination** (D13); unknowns default to `UNDETERMINED`/`CUSTOMER_INPUT_REQUIRED`, never `DOES_NOT_APPLY`; voluntary use of a non-applicable capability is not blocked.
* **[U] Residual:** the SECR SI's own "large" definition and the CA 2006 s.465 numerics remain unread — recorded, not guessed.

## 10. Narrative findings

* **[R] Narrative is NOT implemented**; S4 is an explicit HARD STOP (minimum decisions unavailable). The only narrative-adjacent storage is the legacy, V3-unused `report_generation_queue.user_edits` JSONB and the dormant `report_comments` table.
* **[REC] Binding design:** `disclosure_narratives` keyed by `requirement_version_id` + `report_version_id`, with `narrative_kind`, `provenance (CUSTOMER|SYSTEM|MIXED)`, `system_facts_ref`, `evidence_refs`, version-bound status. `disclosure_management_commentary` is a **separate namespace with no requirement reference** (D5).
* **[D] No character limits and no field counts are invented** (D5 rejects the "7 fields × 4,000 characters" model); A1/A3/P3 remain PO decisions.
* **[D] Narrative binds to the requirement, not the report section** — binding to a section would re-introduce template-as-requirement, which D2 forbids.

## 11. Security findings

* **[R] The guard pattern already exists and is reusable:** `require_org_member()` / `require_org_admin()` (`backend/auth.py:445/470`) and `ensure_org_access()` (`backend/api/dependencies.py:149`); `POST /api/v3/reports` already applies `require_org_member + ensure_org_access + validate_report_type`.
* **[REC] Every new disclosure surface must reuse these guards** and the existing `audit_trail` taxonomy — **no new authorization or audit mechanism**.
* **[D] Highest-risk new path: the evidence drill-down** (value → line item → document). It must preserve organisation scoping, the **processing-entity document boundary** and the private-document storage rules (`20260823000000_d32_private_documents_storage.sql`). Signed URLs must never appear in disclosure payloads or logs.
* **[REC] Global catalogues (framework/requirement/GWP/denominator) are read-only to customers** — this is what keeps D4's "no generic rules engine" true.
* **[D] No RLS policy, grant, role or permission was modified.**

## 12. Migration implications

* **Reused unchanged:** ~23 tables (calculation, evidence, documents, report/version, audit, master data) — **no extension required for the MVP**.
* **Extension:** `calculation_snapshots.source_line_item_id` — **one additive nullable column** + FK `ON DELETE SET NULL` + index (mirrors the D33 pattern; no existing column or row rewritten).
* **New tables (MVP): 14** — frameworks, framework versions, requirement versions, requirement mappings, purposes, purpose requirements, purpose versions, instance binding, applicability assessments, values, value evidence, evidence line items, intensity denominator types, intensity ratios.
* **New tables (later): 10** — narratives, management commentary, gases, GWP sets/values, base-year records, targets, actions, policies, transition-plan elements.
* **Backfill:** `evidence_line_items` populated under the D33-only rule and, later, where a deterministic match exists (**prefer manual entry with empty history** otherwise); `source_line_item_id` backfilled only where deterministic. **No historical row is rewritten to manufacture provenance.**
* **Compatibility:** fully additive; no existing API shape, report content key, lifecycle status or RLS policy needs to change for the MVP.
* **[REC] Not created.** No migration file was authored in this task.

## 13. API implications

* **Existing surfaces identified for later change** (none modified): `GET /api/v3/reports/types` (single `annual` entry); `POST /api/v3/reports`; `GET /{id}/content`; `GET /{id}/versions`; the five lifecycle POSTs (`submit`/`request-changes`/`reject`/`approve`/`finalize`); `GET /{id}/pdf`; `GET /api/v3/reporting/audit-readiness` and `audit-activity`; and the **legacy** `POST /api/reports/generate-enhanced-report` (D16 only).
* **New concepts needed (design-level):** framework/version retrieval; requirement retrieval by purpose version; applicability management; disclosure retrieval by report version; **evidence drill-down (forward)**; **reverse evidence navigation**; intensity-ratio management; narrative binding (S4, not authorised).
* **[REC] Every new endpoint reuses the existing guard pattern and audit taxonomy**; no new authorization or audit mechanism.
* **[D] XBRL/iXBRL, statutory filing integration and external assurance interfaces are out of scope.**
* **[REC] Not implemented.** No route, schema or contract was changed.

## 14. Unresolved regulatory evidence

Carried forward unchanged and **not invented** (design §25): (1) **ESRS E1 exact identifier/title** — `UNRESOLVED — AUTHORITATIVE SOURCE REPRESENTATION LIMITATION`; (2) GHG Protocol Chapter 9 required/optional lists (PDF-only); (3) the SECR SI's own "large" definition and CA 2006 s.465 numerics (legislation.gov.uk JS-walled); (4) Directive (EU) 2026/470's own application dates; (5) Irish competent authority designation (**no product impact**); (6) whether the 2026 Simplified ESRS is in force (represented as `ADOPTED_NOT_IN_FORCE`).

**Design consequence:** each is a **data/verification** action, not a schema change — which is why requirement codes are controlled strings and framework versions carry an explicit legal-status enum.

## 15. PO decisions required

**13 carried-forward decisions** (A1, A3, P3, D11-CAT, E1-COV, E1-VER, APPL, GP-CONS, GP-GAS, GP-S2M, GP-S3, GP-BY, LEG) mapped to their design impact, **plus 7 new design decisions** raised by this work: **DM-1** requirement-code naming policy; **DM-2** purpose ↔ `report_type` relationship; **DM-3** reporting-period semantics; **DM-4** status of `benchmarking` content; **DM-5** finalisation policy for `NOT_SUPPORTED` / `CUSTOMER_INPUT_REQUIRED`; **DM-6** customer evidence drill-down depth; **DM-7** line-item population timing.

**[D] None of these was decided in this task.** Detail: design §§26.1–26.2.

## 16. Files created / files changed

| File | Action | Detail |
|---|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md` | **Created** (design Deliverable A) | 102,637 bytes; **29 `##` sections** (all mandated); untracked |
| `docs/cline/reports/CT-P8-DISCLOSURE-MODEL-DESIGN-20260912-004.md` | **Created** (Deliverable B, this report) | untracked |

**No other file was created, modified, moved or deleted.** No pre-existing document was edited — including the D1–D17 ratification record, the regulatory verification report, the lifecycle spec and every previous task report.

## 17. Database / code / RLS status

| Area | Status |
|---|---|
| **Database** | **NO CHANGE.** No migration created; no DDL/DML executed; no schema, table, column, index, constraint or policy touched |
| **Code** | **NO CHANGE.** No backend, frontend, engine, route, service, template, report-generation, calculation, narrative or rules change |
| **RLS / security** | **NO CHANGE.** No policy, grant, role, permission, auth or storage change; no secrets or signed URLs read, produced or recorded |
| **Production** | **NO CHANGE.** Nothing deployed, enabled or disabled |
| **Legacy route** | **UNTOUCHED** (`POST /api/reports/generate-enhanced-report`); no compliance claim altered |
| **S4 / Phase 8-X** | **NOT STARTED** |

## 18. Tests / checks performed

* **Schema inventory verification** — programmatic extraction of every `CREATE TABLE` and `ALTER TABLE … ADD COLUMN` across all **56** migrations, plus proof-by-absence searches for framework/disclosure/requirement/applicability/narrative tables and per-gas/GWP/energy/base-year/uncertainty columns.
* **Relationship tracing** — the D33 evidence chain read from the migration itself (`source_item_id`, `file_id`, `ON DELETE SET NULL` FKs, indexes) rather than inferred.
* **Line-item verification** — confirmed `extracted.line_items` / `mapped_data.line_items` usage in `v3_operations.py` and `v3_processing_workflow.py`, plus invoice document types and `_parse_fuel_invoice`.
* **Report catalogue / lifecycle verification** — `SUPPORTED_REPORT_TYPES` (one entry), `REPORT_STATUSES`, `report_versions.status` vocabulary and the 12 engine sections cross-checked against the lifecycle spec §4.
* **Guard-pattern verification** — `require_org_member`/`require_org_admin`/`ensure_org_access` existence and existing usage.
* **Deliverable structure verification** — design document contains all **29** mandated sections; this report contains all mandated sections.
* **No application tests were run** — **because no application code was changed.** Running them would prove nothing about a documentation-only task.

## 19. Deviations

| # | Item | Description |
|---|---|---|
| **D-1** | **"12-section report" clarification** | The task's phrase is accurate for the **authoritative V3 structured engine** (12 `section_id`s) but not for the legacy PDF generator, which emits **6 numbered sections + TOC**. Recorded as a **discrepancy** (design §16.1) rather than silently resolved. No artefact was changed. |
| **D-2** | **Two documents, two scopes** | The design is one document of **29 sections**; the report is separate. No third artefact was produced (no implementation prompt, as instructed). |
| **D-3** | **No PO decision taken** | The design deliberately records options + recommendations instead of selecting values for A1/A3/P3/D11-CAT/E1-COV/E1-VER/APPL/GP-*/LEG or the new DM-* decisions. |
| **D-4** | **Deferred concepts explicitly deferred** | Narrative, per-gas/GWP and base-year/recalculation are designed **conceptually** but placed in §23 (deferred) rather than MVP, to keep the initial schema honest and bounded. |
| **D-5** | **Live DB not inspected** | Consistent with prior Phase 8 tasks: no live database connection was used, so statements about *persisted* data (e.g. whether duplicate `is_current` rows exist) remain **[UNVERIFIED]** and are marked as such. |
| **D-6** | **No ESRS identifier invented** | Where identifiers are unknown, the verified **concept** name is used with the explicit marker. This is a deliberate adherence to instruction, not an omission. |

## 20. Git status / worktree status / commit status / push status

**Recorded before starting**

| Item | Value |
|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| Branch | `main` |
| Staged | **0** |
| Modified | **208** (all pre-existing) |
| Untracked entries | **60** (collapsed; **759** with `--untracked-files=all`) |
| Branch position | `main…origin/main` — ahead 14 |

**Recorded after completion**

| Item | Value |
|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` — **unchanged** |
| Branch | `main` — **unchanged** |
| Staged | **0** — unchanged |
| Modified | **208** — unchanged (**no tracked file modified by this task**) |
| Untracked entries | **61** (collapsed; **761** with `-uall`) — **+1** = the new design document in `docs/architecture/`; this report lands inside the already-untracked `docs/cline/reports/` directory |
| Branch position | `main…origin/main` — ahead 14 (unchanged) |

**Only the two permitted documentation artefacts were touched:**

| Path | Git state | Note |
|---|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md` | **untracked** (`??`, new) | 102,637 bytes; 29 sections |
| `docs/cline/reports/CT-P8-DISCLOSURE-MODEL-DESIGN-20260912-004.md` | **untracked** (`??`, new) | this report |

**Worktree integrity:** neither deliverable appears in `git diff --name-only` (they are untracked; **no tracked file was modified**). No pre-existing working-tree change was overwritten, staged, stashed, reverted or cleaned.

**Commit status:** **NO COMMIT.** **Push status:** **NO PUSH.** No `reset`, `stash`, `clean`, `rebase`, `amend` or force-push. No `.env`, credential, key, token, JWT, demo credential or signed URL was read, created or recorded.

## 21. Final verdict

### `DESIGN COMPLETE — READY FOR PO REVIEW`

**Closed:** the design covers all 29 mandated sections; the two structural gaps the task prioritised — **row-level/line-item traceability** and **separation of regulatory applicability from CarbonTally capability** — are designed concretely and minimally; the reuse posture is proven against verified repository facts (≈23 tables reused unchanged, **one** additive column, no new report spine, no new calculation engine, no new audit or authorization mechanism).

**Explicitly not claimed:** *implementation ready*. Gate 5 remains **NOT AUTHORIZED**; Gate 3 (PO ratification of the design and of the decisions in §15) is **pending**; unresolved regulatory evidence is carried forward, not resolved (§14).

**Mandatory stop condition observed:** this task stopped after producing the two documentation deliverables. It did **not** design-or-create migrations, implement any Disclosure Model table, mapping, applicability, narrative/S4, template or drill-down, and did **not** modify the calculation engine, report generation, APIs, RLS, permissions, production surface or the legacy compliance route. **PO review and explicit authorization are required before any implementation.**





