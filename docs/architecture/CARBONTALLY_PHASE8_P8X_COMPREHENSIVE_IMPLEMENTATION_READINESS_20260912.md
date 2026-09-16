# CarbonTally — Phase 8 + Phase 8-X Comprehensive Implementation-Readiness, Dependency, Parallelisation and Batch-Minimisation Assessment

**Document:** `CARBONTALLY_PHASE8_P8X_COMPREHENSIVE_IMPLEMENTATION_READINESS_20260912.md`
**Task reference:** `CT-P8-P8X-COMPREHENSIVE-IMPLEMENTATION-READINESS-20260912-007`
**Status:** READ-ONLY ASSESSMENT — **NO IMPLEMENTATION PERFORMED, NONE AUTHORISED**
**Date:** 2026-09-12
**Type:** Governance / discovery / planning. No code, schema, migration, API, frontend, extraction, OCR/LLM, calculation, factor, report, template, narrative, RLS, auth, billing, legacy or Phase 8-X change.
**Companion report:** `docs/cline/reports/CT-P8-P8X-COMPREHENSIVE-IMPLEMENTATION-READINESS-20260912-007.md`
**Governing decisions treated as fixed:** D1–D17 (`CARBONTALLY_PHASE8_REPORTING_ARCHITECTURE_PO_RATIFICATION_D1-D17_20260912.md`) and all 20 Disclosure Model decisions (`CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md`)
**Repository baseline:** branch `main`, HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c`
**Evidence tags:** **[R]** repository fact · **[D]** PO decision · **[V]** verified · **[U]** unresolved · **[I]** interpretation · **[REC]** recommendation

---

## 1. Executive Summary

**Headline:** the remaining Phase 8 scope is **one genuinely new layer** (the Disclosure Model) plus
**one upstream correctness dependency** (PDF/IMAGE line-item extraction), while **Phase 8-X is
overwhelmingly consolidation, not greenfield**. The platform already persists and computes almost
everything both workstreams need. The minimum practical plan is **8 implementation batches** and
**7 independent verification gates** (preceded by one prerequisite evidence/PO gate), with the
extraction fix, the EF-E picker fix, the E1 evidence closure and Phase 8-X Stage X1–X3 all safely
parallelisable.

**What already works (do not rebuild):** authoritative calculation + immutable snapshots + D33
provenance; multi-line calculation at the operations layer; CSV/XLSX line-items and the optional AI
line-item path; the FactorMatchingEngine; the report-version lifecycle (S1/S3, six states,
immutable-on-approval, new-version supersede); the 12-section report engine; the operations API
(49 endpoints) and operations console (26 files); auth/capability/scope machinery; audit, retention,
notification and billing substrates. **[R]**

**What is genuinely missing:** the entire Disclosure Model (framework/version → requirement → mapping
→ applicability → value → purpose → narrative) — **no `disclosure_*` table exists anywhere [R]**;
`evidence_line_items` / `calculation_snapshots.source_line_item_id` (addressable line identity); the
narrative overlay (S4); a structured SECR intensity denominator; per-gas, base-year and
consolidation-approach attributes; the Phase 8-X aggregation layer, worker heartbeat, health-path
correctness and runtime introspection. **[R]**

**What blocks production:** (a) **97 of 104 production tables have RLS disabled with `anon` holding
`GRANT ALL`** and **34 migrations outstanding** (including the Phase 8 report-lifecycle migration
`20260913000000_p8_report_lifecycle_status`) — the verified RLS baseline **[R]**; (b) the ESRS E1
identifier evidence gap (`E1-COV` = CONDITIONAL); (c) the **Phase 8 naming/scope discrepancy** (the
ratified Master Roadmap says "Phase 8 — Advanced Analytics, scope NOT defined", while this programme's
Phase 8 is the reporting/disclosure architecture) **[R]**.

**Verdict:** `DECISION READINESS COMPLETE — READY FOR PO REVIEW` — a reliable roadmap can be produced;
the blockers are *identified and sequenced*, not *unknown*. The blocking items (E1 evidence,
PX-1…PX-12, the 34-migration backlog, RLS) are recorded as gates, not as reasons the roadmap cannot
exist.

---

## 2. Assessment Objective

Answer: *"What is the minimum practical number of safe implementation batches and independent-verification
gates required to complete the remaining Phase 8 and Phase 8-X scope, given the capabilities that already
exist?"* — optimising for minimum safe batches, maximum reuse, maximum safe parallelisation, minimal
duplicated investigation, clear dependency ordering, independently verifiable boundaries, minimal
regression risk and preserved governance (§§9, 20–21).

---

## 3. Evidence Reviewed

| # | Artefact / area | Kind |
|---|---|---|
| 1 | `CARBONTALLY_PHASE8_REPORTING_ARCHITECTURE_PO_RATIFICATION_D1-D17_20260912.md` (the actual D1–D17 record; the prompt's `…REPORTING_ARCHITECTURE_DECISIONS…` filename does not exist) | [D] |
| 2 | `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md` | [D] design |
| 3 | `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` (20 decisions) | [D] |
| 4 | `CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md` (§24.11) + `CT-P8-REPORTING-REGULATORY-REQUIREMENT-VERIFICATION-20260912-001.md` + closure/completion `-002`/`-003` | [V]/[U] |
| 5 | `CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` (1751 lines) | [D] spec |
| 6 | `CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md` | [D] |
| 7 | `CARBONTALLY_PHASE8_OPEN_DECISION_CLOSURE_AND_IMPLEMENTATION_AUTHORISATION_20260912.md` (A1–A15, A-PE, A-AUD, A-RLS…) | [D] |
| 8 | `CARBONTALLY_PHASE8_DISCOVERY_AND_CAPABILITY_GAP_ANALYSIS_20260912.md` | discovery |
| 9 | `CT-P8-REPORTING-S4-NARRATIVE-OVERLAY-20260912-001.md` (S4 blocked) | [R] |
| 10 | Formalized Gate 0 forensics: `docs/cline/reports/CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md` and `docs/cline/reports/CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912.md`; original investigation retained in `docs/ChatGPT/chat_history/phase 8 implementaion chat history 01.md` §§16–22 | [R]/[V] |
| 11 | `CARBONTALLY_PHASE8X_OPERATIONAL_INTELLIGENCE_DISCOVERY_AND_IMPLEMENTATION_BOUNDARY_20260912.md` (926 lines) + `docs/ohd/reports/CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md` | [D] discovery |
| 12 | `CARBONTALLY_RLS_PRODUCTION_BASELINE_AND_REMEDIATION_SPEC_20260912.md` + `CARBONTALLY_PRODUCTION_RLS_SECURITY_HOLD_AND_REMEDIATION_REGISTER_20260912.md` | [V] |
| 13 | `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` (Phase 8 naming) | [D] |
| 14 | Source: `backend/api/v3_reports.py`, `backend/domain/report_lifecycle.py`, `backend/engines/report_generation.py`, `backend/engines/calculation.py`, `backend/services/automatic_extraction.py`, `backend/services/ai_document_extraction.py`, `backend/services/extraction_suggestions.py`, `backend/domain/evidence.py`, `backend/api/v3_operations.py`, `frontend/src/v3/ops/**` | [R] |
| 15 | `supabase/migrations/**` (55 files) | [R] |

**Referenced-but-absent evidence — now RESOLVED (Gate 0):** `docs/cline/reports/CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md`
and `docs/cline/reports/CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912.md` have been **formalized** as
durable repository files (consolidating the established chat-history evidence + repository code
inspection). See `docs/cline/reports/CT-P8-G0-GOVERNANCE-CONSOLIDATION-20260912-008.md`.

**Evidence-conflict — now RESOLVED (Gate 0):** the Decision Record's `DM-7` now carries the explicit
historical PDF/IMAGE re-parsing boundary (§6 refinement), so the earlier wording gap is closed.
`CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` §1.1 also records the **Phase 8
terminology disposition** (G0-B).

---

## 4. Current-State Inventory

**Disclosure Model [R] — COMPLETELY ABSENT.** A repo-wide search of `supabase/migrations/**` and
`backend/**` for `disclosure_framework`, `disclosure_requirement`, `disclosure_value`,
`disclosure_applicability`, `evidence_line_items`, `source_line_item_id` returns **zero** matches. There
are **no** framework/version, requirement, mapping, applicability, value, purpose, or narrative tables.

**Report lifecycle [R] — IMPLEMENTED + LOCALLY VERIFIED.** `report_versions.status` (six states) added
by `20260913000000_p8_report_lifecycle_status.sql`; state machine in `backend/domain/report_lifecycle.py`
(193 lines); version-scoped endpoints in `backend/api/v3_reports.py` (submit / request-changes / reject /
approve / finalize / new-version). `FINAL` terminal; `APPROVED`/`FINAL` immutable; supersede = new
`DRAFT`. **Production caveat:** that migration is one of the **34 outstanding** — **not applied in
production [R]**.

**Report catalogue [R] — ONE TYPE.** `SUPPORTED_REPORT_TYPES = {"annual": …}` (`v3_reports.py:96`).
`REPORT_STATUSES = ("pending","generating","completed","failed")` is the *generation* state machine,
deliberately distinct from the lifecycle state.

**Report engine [R].** `backend/engines/report_generation.py` composes exactly **12** ordered sections
(`metadata, organization, period, totals, scopes, activities, validation, benchmarking, provenance,
calculation, lineage, generation`), with `template_order` support.

**Calculation [R].** `backend/engines/calculation.py` — `CalculationRequest` (single factor per request),
`CalculationEngine.calculate()`, immutable SHA-256-hashed snapshots, and provenance fields
`source_file`, `source_page`, `source_item_id`. **Multi-line** calculation is **orchestrated by the
operations layer** (`v3_operations.py` stores per-line results into `mapped_data.line_items`).

**Extraction [R].** PDF → `_pdf_text` (pdfplumber → Tesseract → pypdfium2+ONNX) → `extraction_suggestions.suggest`
→ **flat single record** (`_extract_pdf`). IMAGE → OCR → same. CSV/XLSX → `_rows_to_line_items` →
**`line_items[]`**. Optional AI (`ai_document_extraction.py`) can emit `line_items[]`, but runs **only**
when `confidence < AUTO_EXTRACT_CONFIDENCE_MIN` or job metadata requests it (`prefer_ai`/`force_ai`/
`ai_required`) — so a "complete" flat deterministic record **suppresses** the multi-line AI path.

**Evidence [R].** `backend/domain/evidence.py` (356 lines); the D33 chain `source_item_id`/`source_file`/
`source_page` = **document-level + page**, not line-level. Line items exist only **inside JSONB**
(`extracted.line_items`, `mapped_data.line_items`), not as addressable rows.

**Factor matching [R].** `backend/engines/factor_matching.py` + `matching_stages.py` (the full engine);
`backend/data/emission_factors.py` `find_by_activity` (direct SQL) is what the **mapping pickers** use.

**Narrative [R].** **No** version-scoped narrative store, no overlay column, no endpoint. Legacy
`backend/report_generator.py` has presentation-only narrative strings (legacy path; D16).

**Phase 8-X [R].** **No** `services/operational_intelligence.py`, **no** `/api/v3/ops/runtime/*`, **no**
heartbeat. Ops API `v3_operations.py` = **49 endpoints**; ops console `frontend/src/v3/ops/**` = **27**
files. `report_generation_queue` has dormant `user_edits JSONB` and `final_report_url TEXT`.

**Legacy route [R].** `POST /api/reports/generate-enhanced-report` is live (`backend/routes/reports.py:1287`,
`backend/report_generator.py:1040`) — D16, untouched.

**Migration/deployment state [R].** Repo has **55** migrations; production has **21 applied / 34
outstanding**; **1** migration is `p8`-prefixed.

---

## 5. Phase 8 Completion Matrix

| Component (task §7.A) | State | Evidence |
|---|---|---|
| Framework/version model | **E — Missing** | no `disclosure_*` tables [R] |
| Requirement model | **E — Missing** | [R] |
| Requirement mappings | **E — Missing** | [R] |
| Report purpose model (`purpose_code`) | **E — Missing** | `purpose_code` 0 hits [R] |
| `report_type` vs `purpose_code` | **C — Designed** (`DM-2` ratified) | Decision Record |
| Applicability model | **E — Missing** | [R] |
| Disclosure values | **E — Missing** | [R] |
| Customer-input requirements | **E — Missing**; `CUSTOMER_INPUT_REQUIRED` semantics `[D]` | [R] |
| Customer-editable narrative boundary | **B/C** — policy ratified (`P3`), no store | S4 report [R] |
| Calculation/provenance linkage | **D — Partial** (document-level `source_item_id`; no disclosure link) | `calculation.py` [R] |
| Evidence linkage | **D — Partial** (D33 exists; no disclosure-evidence link) | `evidence.py` [R] |
| Intensity definitions/values | **E — Missing** | [R] |
| SECR denominator handling | **E — Missing**; `D11-CAT` ratified | [R] |
| ESRS E1 coverage | **F — Blocked** (`E1-COV` CONDITIONAL) | Decision Record |
| Finalisation rules (`DM-5`) | **C — Designed**; current lifecycle has only version-level `FINAL` | `report_lifecycle.py` |
| Historical reproducibility | **D — Partial** (`report_versions` + immutable snapshots exist; no framework binding) | [R] |
| Report versioning | **A — Implemented + verified** | `report_lifecycle.py`, migration [R] |
| Template/configuration architecture | **C — Designed** (D4); engine has `template_order` only | [R] |
| Export/frozen artefact architecture | **D — Partial** (`final_report_url` column dormant) | [R] |

---

## 6. Phase 8-X Current-State / Scope Assessment

**Authoritative scope EXISTS [D].** `CARBONTALLY_PHASE8X_OPERATIONAL_INTELLIGENCE_DISCOVERY_AND_IMPLEMENTATION_BOUNDARY_20260912.md`
(discovery complete) plus its OHD companion. It defines Phase 8-X as a **bounded extension/workstream of
Phase 8** (not a new Phase 9), overwhelmingly **consolidation/exposure/correctness**, with a **MUST set
M1–M6**, SHOULD S1–S6, LATER L1–L7, OUT-OF-SCOPE list, stages X1–X8, blockers BL-1/BL-2 and **12 open PO
decisions PX-1…PX-12**. Verdict: `PHASE 8-X DISCOVERY COMPLETE — IMPLEMENTATION BOUNDARY READY FOR PO REVIEW`.

**Scope is sufficient to plan but not to implement without PO decisions.** What exists (signal) [R]:
`document_processing_queue` (79 cols), `domain_events` + `correlation_id`, `audit_trail`, `usage_tracking`/
`billing_*`, AI cost across 3 tables, `report_generation_queue`, `import_batches`, `notification_delivery`,
`email_logs`, `login_history`, `sla_definitions`/`sla_compliance`, `staff_*`, `system_settings` + retention
service, 49 ops endpoints, 27-file ops console.

What is MISSING [R]: aggregation read model; worker liveness/heartbeat; health-path correctness
(`/health` does not test the pool path); threshold **evaluation**/alert dispatch (config keys inert);
deployment/runtime introspection (no version/build endpoint); any external observability tooling (none
in `requirements.txt`/`package.json`).

**Phase 8-X dependencies [R]:** DEP-1 (`report_generation_queue` visibility needs Phase 8 report
migrations applied); DEP-2 (RLS gate — **must remain separate**); DEP-3/DEP-4 (existing repos/queue).

**Phase 8-X blockers [R]:** **BL-1** no Render/platform access; **BL-2** no read-only production DB role.
These block *verification* of runtime/deployment surfaces, not the in-app work.

**Not-invented:** this assessment does **not** define any Phase 8-X scope beyond the authoritative
document, and adds no API/schema.

---

## 7. Existing Capability Reuse Matrix

| Capability | Verdict | Why |
|---|---|---|
| Multi-line calculation (operations-layer orchestration) | **REUSE AS-IS** | Per-line factors/emissions already produced into `mapped_data.line_items`; the disclosure layer must **project**, not recompute |
| `CalculationEngine` + immutable snapshots | **REUSE AS-IS** | SHA-256 snapshots are the authoritative calculation record (D2/D8) |
| FactorMatchingEngine (`factor_matching.py`, `matching_stages.py`) | **REUSE AS-IS** (for engine paths) | Full matcher already used elsewhere; pickers are the separate concern (§10) |
| Emission-factor catalogue + import batches | **REUSE AS-IS** | Version/status/activation already modelled |
| D33 evidence chain (`source_item_id`, `source_file`, `source_page`) | **REUSE WITH EXTENSION** | Extend to reach the **line**; do not duplicate |
| CSV/XLSX `line_items[]` extraction | **REUSE AS-IS** | Already line-aware |
| Optional AI extraction (line-item capable) | **REUSE WITH ADAPTER** | Reuse the capability; adjust **triggering/gating**, not the engine |
| Report-version lifecycle (S1/S3) | **REUSE AS-IS** | Six states, immutability, new-version supersede |
| Report engine (12-section composition + `template_order`) | **REUSE WITH EXTENSION** | Template/purpose projections extend composition; no new engine |
| `report_versions` / `report_generation_queue` spine | **REUSE AS-IS** | Bind to it; introduce no competing report table (D2/D15) |
| Ops API (`v3_operations.py`) + ops console | **REUSE WITH EXTENSION** | Phase 8-X extends the namespace/tabs; no second dashboard |
| Authorization/capability/scope machinery (`require_*`, `ensure_org_access`) | **REUSE AS-IS** | Every new surface reuses the guard pattern |
| `audit_trail` + `AuditLogger` | **REUSE AS-IS** | Append-only; **audit ≠ telemetry** |
| `usage_tracking` / `billing_*` | **REUSE AS-IS** | Allowance substrate exists |
| `notifications`/`notification_delivery` + Resend path | **REUSE AS-IS** | Alert dispatch reuse (Phase 8-X S1) |
| `services/retention.py` + `system_settings` | **REUSE WITH EXTENSION** | Retention config exists; operational domains undefined (PX-7) |
| `core/units.normalize_unit` | **REUSE AS-IS** | Single normaliser (D23); do not add a second |
| `activity_categories` (`esrs_e1_category`, `ghg_protocol_*`) | **REUSE AS-IS** | Activity taxonomy; **not** a requirement model |
| Legacy `report_generator.py` narrative / enhanced-report route | **DO NOT REUSE** | D16 legacy/deprecated; separate disposition |
| `template_structure` JSONB on `report_templates` | **REQUIRES CHANGE (careful)** | Must stay presentation-only; must never become a requirement store (D2/D3) |

---

## 8. Remaining Gap Matrix

Class A–G per task §1. "Blocks" = which batch.

| # | Gap | Class | Blocks | Notes |
|---|---|---|---|---|
| G-1 | Disclosure Model framework/version → requirement → mapping spine | C (designed) | B1 | Design §6–§9 |
| G-2 | Applicability model (period-dated, `UNDETERMINED`) | C (designed) | B1/B3 | `APPL` |
| G-3 | Disclosure values + purpose (`purpose_code`) projection | C (designed) | B1/B3 | `DM-2` |
| G-4 | Requirement semantics (`requirement_class`, capability) | C (designed) | B1 | D12 |
| G-5 | `evidence_line_items` + `calculation_snapshots.source_line_item_id` | E (missing) | B2 | §9 |
| G-6 | `disclosure_value_evidence` linkage | E (missing) | B1/B2 | §9 |
| G-7 | Deterministic idempotent historical backfill | E (missing) | B2 | `DM-7` |
| G-8 | PDF/IMAGE line-item extraction fidelity (8→1) | D/E | P1 | §9 |
| G-9 | EF-E picker exact-unit defect | Confirmed defect | P2 | §10 |
| G-10 | Narrative overlay store + endpoints (S4) | C (designed+policy) | B4 | `A1/A3/P3` ratified |
| G-11 | Frozen/export artefact (hash, metadata) | D (partial) | B4 | `final_report_url` dormant |
| G-12 | Finalisation gate (`DM-5` `CUSTOMER_INPUT_REQUIRED` vs `NOT_SUPPORTED`) | C | B4 | Decision Record §8 |
| G-13 | SECR intensity denominator (structured) | C (designed) | B3 | `D11-CAT`; catalogue content gated |
| G-14 | Per-gas / GWP | G (deferred) | — | `GP-GAS` |
| G-15 | Base year / recalculation | G (deferred) | — | `GP-BY` |
| G-16 | Consolidation-approach attribute | C | B1 | `GP-CONS` |
| G-17 | ESRS E1 identifiers/coverage | F (evidence-blocked) | G0 | `E1-COV` |
| G-18 | GHG Protocol Ch.9 required/optional lists | F (evidence-blocked) | G0 | [U] |
| G-19 | Residual SECR numeric detail | F (partially evidence-blocked) | B3 | [U] |
| G-20 | Phase 8-X aggregation read model | E (missing) | X1 | M3/X4 |
| G-21 | Phase 8-X worker/queue visibility | E (missing) | X1 | M1/X2 |
| G-22 | Phase 8-X health-path correctness + heartbeat | E (missing) | X1 | M2/X3; PX-5 |
| G-23 | Phase 8-X runtime/deployment introspection | E (missing) | X1 | M5; BL-1 |
| G-24 | Phase 8-X alerting evaluation/dispatch | E (missing) | X2 | S1; PX-6 |
| G-25 | Phase 8-X console extension | E (missing) | X2 | M4/X5 |
| G-26 | 34 outstanding production migrations (incl. P8 lifecycle) | Deployment | **Gate 0 / production** | [R] |
| G-27 | RLS baseline (97/104 disabled; `anon` GRANT ALL) | G (separate) | separate workstream | [V] |
| G-28 | Legacy route disposition | G (separate, D16) | — | `LEG` |

---

## 9. Line-Item / Extraction Dependency Assessment

**Verified present [R]:** CSV/XLSX `line_items[]`; AI path can emit `line_items[]`; per-line
mapping/calculation results in `mapped_data.line_items`; the calculation layer already supports multiple
lines and per-line factors; `pdf_engine._parse_fuel_invoice()` is line-item-aware.

**Verified gap [R]:** PDF/IMAGE deterministic extraction produces a **flat single record** via
`extraction_suggestions.suggest`; the mapper reads flat `activity`/`unit` (`v3_operations.py:959–960`);
the AI multi-line path is **suppressed** when the flat record's completeness clears the threshold.

**The 8→1 finding (existing evidence, not reopened) [R/V]:** an 8-line PDF invoice can yield **1**
extracted object; the suggestion logic can combine an activity label from one line with a
quantity/unit from another (observed `Waste` + `38.4 m³`); the retained item may be semantically wrong.

**Smallest safe implementation boundary [REC]:**
1. Make **line identity addressable** without re-architecting extraction: `evidence_line_items`
   (extracted *from* the JSONB the platform already stores) + one additive
   `calculation_snapshots.source_line_item_id` (FK `ON DELETE SET NULL`, mirroring D33).
2. Fix the **PDF/IMAGE flat-record defect** in the extraction layer so multiple source lines are
   preserved (reuse `line_items[]`; do **not** replace the calculation path).
3. Reuse the existing **gating** mechanism to allow the multi-line path (do not rewrite the AI engine).
4. **No manufactured granularity:** where only document-level provenance exists, the line row is
   synthetic with `row_reference = NULL` and the evidence classification stays `PARTIAL`.

**Do NOT [REC]:** bundle this with the picker defect (§10); auto re-extract historical documents (§15);
add a competing calculation engine; make `evidence_line_items` a parallel extraction.

---

## 10. Emission-Factor / EF-E Assessment

**Separate concerns (must not be bundled) [REC]:**

| # | Concern | Evidence | Batch |
|---|---|---|---|
| 1 | **Extraction defect** (8→1; cross-line activity/unit mixture) | chat history §§20–21 [R/V] | **P1** |
| 2 | **Picker defect (EF-E)** — exact unit equality on the processing mapping surface can exclude compatible factors (e.g. `kWh` vs `kWh (Gross CV)`) | chat history `EF-E: CONFIRMED (independent defect)`; `v3_processing_workflow.py:1113` exact equality vs substring elsewhere [R] | **P2** |
| 3 | **Factor-catalogue evidence gap** (whether a factor exists for a given pair) | `EF-A`/`EF-D` UNVERIFIED without live catalogue [U] | not a batch (evidence) |
| 4 | **Calculation-layer behaviour** | `EmissionFactor.calculate_emissions` raises `UnitMismatchError` → 422 (correct) | no change |

**Finding [V]:** the 8→1 invoice problem is **not** caused by the FactorMatchingEngine. The matcher
"was not wrong" for the observed item — `(activity="Waste", unit="cubic metres")` has no valid factor;
the *input* was defective. EF-E is a **separate, independent** defect that would also affect a
correctly-extracted single-line electricity item.

**Is EF-E safely a small independent batch? [REC] YES.** It is a bounded, localised correctness change
on one surface (exact-unit equality → the already-existing substring/normalised comparison used
elsewhere). It has a clear contract, a tiny blast radius, and independent verification (unit-compatibility
positive/negative tests). **It must not be bundled with P1.** It is a strong **parallel** work item.

**Do not [REC]:** merge P1/P2; change emission-factor data; replace the matcher; treat a missing-factor
state as a defect without live-catalogue evidence.

---

## 11. Disclosure Model Readiness

**Ready to implement** against ratified decisions: the design is complete (29 sections), the 20 decisions
are ratified (`E1-COV` CONDITIONAL), and the design is **reuse-first** (~23 existing tables reused
unchanged + one additive column). **Nothing is implemented [R].**

**Batched readiness:**

| Design area | Ready? | Gate |
|---|---|---|
| Framework/version → requirement → mapping spine | Yes | B1 |
| Requirement classification vocabulary | Yes (D12) | B1 |
| Applicability (period-dated) | Yes (`APPL`) | B1/B3 |
| Values + purpose projection | Yes (`DM-2`) | B1/B3 |
| Evidence/line-item linkage | Yes (`DM-7`) | B2 |
| Framework mappings (GHG/SECR/E1) | **Partially** — E1 gated | B3 |
| SECR intensity denominator | **Partially** — catalogue content gated | B3 |
| Narrative (`A1/A3`) | Yes (policy) | B4 |
| Finalisation (`DM-5`) | Yes | B4 |

**Key structural rule (preserve) [D]:** `requirement_class` (what the standard says) is a property of the
**requirement version**; the **effective** class is **derived** from applicability. `CUSTOMER_INPUT_REQUIRED`
≠ `NOT_SUPPORTED` (Decision Record §8). Do not collapse.

---

## 12. Regulatory / E1 Evidence Status

| Item | Status | Effect |
|---|---|---|
| GHG Protocol Corporate Standard | **[V]** identified as foundation (D8) | Ch.9 required/optional lists **[U]** (PDF-only) |
| UK SECR applicability | **[V] partial** — in-scope populations, `>40,000 kWh`, 2-of-3 over 2 FYs, 6 Apr 2025 change | residual SI "large" numerics **[U]** |
| ESRS E1 **exact identifiers/titles** (Annex I to (EU) 2023/2772) | **[U]** — representation limitation | **E1-COV = CONDITIONAL** |
| ESRS E1 version | **[V/D]** 2023 set as amended by (EU) 2025/1416; 2026 revision **NOT in force** | `E1-VER` RATIFIED |
| Irish competent authority | **[U]** context | no product requirement |

**`E1-COV` effect [D]:** only authoritatively verified E1 requirements may be production-supported.
**Can any implementation proceed without resolving it?** **YES [I/REC]** — the framework/version,
requirement, applicability, value, evidence and narrative **infrastructure** (B1–B4 minus the E1 seed
rows) can be built against the verified GHG Protocol + SECR concept set while E1 seeding waits. The E1
**requirement seed** is the only part gated. **Evidence-blocked ≠ code-blocked**: G-17/G-18 are
evidence-blocked (Gate 0); the surrounding infrastructure is not. **Do not invent** ESRS identifiers,
thresholds, deadlines or denominator sets.

---

## 13. Narrative Readiness

**Current state [R]:** no version-scoped narrative store, no overlay column, no endpoint, no validation,
no render-time composition. S4 was **blocked** (`S4 IMPLEMENTATION BLOCKED — PO/ARCHITECTURE REVIEW
REQUIRED`) because `A1`/`A3` were undecided.

**Change since [D]:** the Decision Record now ratifies `A1`, `A3`, `P3`:
- **`A1`** — bounded, requirement-specific narrative; no report-wide editing; Owner/Admin may author.
- **`A3`** — no arbitrary character/field limits; typed fields; limits only where evidence supports them.
- **`P3`** — customers may edit customer-owned inputs / permitted narrative; may **not** edit calculated
  emissions, provenance, factors or system-derived values.

**Smallest safe implementation [REC]:** disclosure-specific narrative bound to requirement versions
(plus a bounded optional management-commentary namespace); version-scoped, **DRAFT-only** editing;
server-side allowlist/plain-text validation; Owner/Admin role enforcement; append-only
`report.narrative_edited` audit events; finalisation integration. **Additive migration** on the
report-version spine. **No** unrestricted report-wide editing; **no** generic rules engine; **no** AI
in the customer-editable path (spec §29).

**Dependency:** narrative *binding keys* are derived from the **Disclosure Model requirement layer**
(B1/B3) — so S4 lands **after** B1/B3 (it is B4).

---

## 14. Report Purpose / Template Readiness

**Current state [R]:** one engine type (`annual`); 12 sections; `template_order` support. Four purposes
(D6-R: Annual Carbon, Management, UK SECR, ESRS E1 Quantitative) do **not** exist as first-class models.

**Shared vs purpose-specific [REC]:**

| Layer | Shared | Purpose-specific |
|---|---|---|
| Authoritative data/calculation/evidence | **Shared** (D2/D8) | — |
| Disclosure values (`requirement → value`) | **Shared** | which requirements each purpose **selects/orders** |
| Applicability | **Shared** mechanism | per-framework applicability facts |
| Narrative | **Shared** mechanism | requirement bindings differ |
| Template / presentation | **Shared** engine (`template_order`) | per-purpose section ordering + labels |
| `purpose_code` | **Separate concept** from `report_type` (`DM-2`) | — |

**Rule [D]:** the four purposes must **not** become four report engines (D6-R); `report_type` must not be
silently redefined (`DM-2`).

---

## 15. Historical Data Strategy

| # | Record class | Deterministic backfill? | Treatment |
|---|---|---|---|
| 1 | Records **already containing `line_items[]`** (CSV/XLSX; any AI-line documents) | **YES** — deterministic, idempotent | Populate `evidence_line_items` from existing JSONB (B2) |
| 2 | **Flat PDF/IMAGE** records (no persisted line structure) | **NO** | **Cannot** be populated deterministically; `row_reference = NULL`, `PARTIAL`, or **excluded** |
| 3 | Records with **OCR/text available** but no persisted lines | **NO (without re-parsing)** | Requires a **separately authorised** re-parsing task; not part of B2 |
| 4 | Records **without sufficient source representation** | **NO** | No line-level claim; document-level only |

**Preserved invariant [D]:** historical documents must **NOT** be automatically re-extracted solely for
Disclosure Model population without an explicitly authorised migration/extraction task (`DM-7`). Backfill
is **additive, idempotent, non-destructive**; no row is rewritten to manufacture provenance; unmatched
stays unmatched. **Silent historical reprocessing is prohibited.**

---

## 16. Dependency Graph

**Critical path (MUST PRECEDE):**
```text
G0 (evidence/PO closure)
  → B1 (Disclosure Model foundation: schema + reference seed)
     → B2 (evidence/line-item addressability + idempotent backfill)
        → B3 (integration: calculation projections + mappings + applicability + purpose/template + SECR intensity)
           → B4 (narrative overlay + frozen export artefact + finalisation)
              → Phase 8 acceptance
```

**Cross-graph edges:**
- **P1 (extraction 8→1)** → **B2's line population** (line identity is only real if extraction preserves lines); independent of B1.
- **P2 (EF-E)** → independent of everything (mapping UX correctness). **[CAN RUN IN PARALLEL]**
- **X1 (Phase 8-X X1–X3)** → depends on **DEP-1** (Phase 8 report migrations applied) for the report-queue slice only; otherwise independent. **[CAN RUN IN PARALLEL]**
- **X2 (Phase 8-X X4–X7)** → depends on X1 (+ PX-6/PX-7). **[SEQUENTIAL within 8-X]**
- **G0 (E1 evidence)** → gates only the **E1 seed rows** in B3, not B1/B2/B4. **[PARALLEL-capable]**

**Classification:**
| Edge | Class |
|---|---|
| B1 → B2 → B3 → B4 | MUST PRECEDE (within Phase 8 core) |
| P1 ↔ B1/B3 | CAN RUN IN PARALLEL (P1 lands before/with B2) |
| P2 ↔ everything | CAN RUN IN PARALLEL |
| X1 ↔ Phase 8 core | CAN RUN IN PARALLEL (separate workstream, different namespace) |
| P1 ↔ P2 | **MUST REMAIN SEPARATE** (different root causes) |
| Phase 8-X ↔ RLS remediation | **MUST REMAIN SEPARATE** |
| Phase 8 ↔ D16 legacy | **MUST REMAIN SEPARATE** |
| B3 E1 rows ↔ E1 evidence | BLOCKED BY EVIDENCE |
| X-runtime introspection ↔ platform access | BLOCKED BY TECHNICAL CAPABILITY (BL-1) |
| B4 narrative ↔ requirement bindings | MUST PRECEDE (narrative binds to requirements) |

**No artificial dependencies created** merely because components are conceptually related (e.g. Phase 8-X
does **not** require the Disclosure Model to exist; P2 does **not** require P1).

---

## 17. Parallelisation Opportunities

| Candidate | Why safe to parallelise | Land by |
|---|---|---|
| **E1 evidence closure** (doc/evidence) | Pure discovery; touches no code; gates only the E1 seed rows | G0 |
| **P1 — extraction line-item fidelity** | Self-contained extraction-layer change; contract = `line_items[]` (already exists for CSV/XLSX); independent of Disclosure Model | with/before B2 |
| **P2 — EF-E picker correctness** | Tiny localised fix on one surface; no shared contract with P1 | any time |
| **X1 — Phase 8-X X1–X3** | Separate namespace (`/api/v3/ops/*`) + existing ops console; reuses existing repos; does not touch Phase 8 product code | parallel with B1–B4 |
| **B1 seed-data prep / B4 narrative shell** | Once contracts frozen, reference-seed data prep + narrative scaffolding can proceed while B2/B3 land | staggered |
| **Report-template scaffolding** | `template_order` already exists; purpose→section mapping is data/config | with B3 |

**Looks parallelisable but should NOT be [REC]:**
- **P1 + P2** — superficially "both mapping UX", but different root causes; bundling would blur the
  extraction fix's verification (task §5, §10).
- **Phase 8-X + RLS remediation** — combining operational visibility with a security remediation makes
  both unverifiable (Phase 8-X §18).
- **B3 E1 rows + E1 evidence** — must not "parallelise" by inventing E1 identifiers to keep moving.
- **B2 backfill + P1** — B2 backfill must **not** re-extract (only reads persisted data); running P1's
  live extraction "to help backfill" would violate `DM-7`.
- **Report generation rewrite + lifecycle** — the lifecycle is verified; a rewrite would regress it.

---

## 18. Work That Must Remain Separate

| Workstream | Why separate |
|---|---|
| **P1 extraction fidelity** vs **P2 EF-E** | Different root causes (task §5) |
| **RLS remediation** | Verified security gate; must not be combined with feature work (AGENTS.md §67; Phase 8-X §18) |
| **D16 legacy disposition** | `LEG`; separate bounded task |
| **Phase 8-X** vs **Phase 8 product capabilities** | Different namespaces/audiences; separately traceable (Phase 8-X §16) |
| **Per-gas / base-year** | Deferred until calculation support (`GP-GAS`/`GP-BY`) |
| **The 34-migration production backlog** | Deployment/remediation concern; not silently bundled into a feature batch |
| **`DATABASE_URL` config/deployment issue** | Phase 8-X PX-9 — explicitly separate |
| **2026 ESRS revision** | Represented as future/not-in-force (`E1-VER`); not implemented |
| **Historical re-extraction** | Prohibited (`DM-7`) unless separately authorised |

---

## 19. Batch Consolidation Options A/B/C

### OPTION A — maximum consolidation (3 batches, 2 gates)
1. **Disclosure Model + evidence + narrative + export** (everything Phase 8).
2. **Extraction + EF-E** (both mapping-related).
3. **Phase 8-X** (all stages).
- *Pros:* fewest steps. *Cons:* enormous blast radius; a schema+migration+projection+narrative+export
  change verified as one unit cannot localise a failure; violates "manageable blast radius"; **bundles
  P1+P2 (explicitly forbidden)**; risks regressing the verified lifecycle. **NOT RECOMMENDED.**

### OPTION C — maximum isolation (13 batches, 13 gates)
B1a framework/version; B1b requirement; B1c applicability; B1d values/purpose; B2a `evidence_line_items`;
B2b backfill; B3a projections; B3b mappings; B3c SECR intensity; B4a narrative; B4b frozen artefact;
P1; P2; (X1–X8 separately).
- *Pros:* finest rollback. *Cons:* excessive gate overhead; many batches too small to be meaningful;
  duplicated setup/verification; slower.

### OPTION B — balanced (RECOMMENDED)
**8 implementation batches, 7 verification gates** (see §20). Each batch is a **cohesive** unit with a
clear contract, bounded blast radius and an independent rollback/debug boundary. It keeps P1 and P2
separate, keeps Phase 8-X in its own namespace, and verifies each cohesive unit before the next.

**Why Option B wins [I]:** it minimises *elapsed* time (4 parallel tracks) without ever asking a reviewer
to validate more than one cohesive concern at once. Option A saves ~5 steps but makes failures
unlocalisable; Option C adds ~5 gates for no material safety gain.

---

## 20. Recommended Minimum Practical Batch Plan

| ID | Title | Scope | Prereq | Combined-safely rationale | Must NOT include | Verify | Parallel? | Risk |
|---|---|---|---|---|---|---|---|---|
| **B1** | Disclosure Model foundation | New tables: framework, framework_version, requirement_version, requirement_mapping, applicability, disclosure_value, disclosure_value_evidence, purpose; RLS + indexes; reference seed (frameworks/version/purpose) | G0 decisions | One cohesive schema; additive; isolates the new layer | Projections, narrative, extraction, E1 **seed rows**, RLS remediation, legacy | V1 | No (critical path) | Med |
| **B2** | Evidence / line-item addressability | `evidence_line_items`; `calculation_snapshots.source_line_item_id` (additive FK `SET NULL`); evidence-link population; deterministic idempotent backfill (class-1 only) | B1 | One cohesive provenance unit; mirrors D33; non-destructive | Re-extraction, P1 extraction fix, P2, narrative | V2 | Partially (after B1) | Med-High |
| **B3** | Disclosure Model integration | Read-only calculation projections; framework mappings (GHG Protocol + SECR + E1 **concept set**); applicability engine; purpose/template projections; SECR intensity model | B1,B2 | One cohesive "compute the disclosure" unit; read-only consumption | Calculation-engine change; E1 **identifiers** (until G0); per-gas; base-year | V3 | No | Med-High |
| **B4** | Narrative + frozen artefact + finalisation | Narrative overlay (S4) bound to requirements; DRAFT-only; validation; role enforcement; frozen export artefact (hash/metadata); `DM-5` finalisation gate | B1,B3 | Report-lifecycle extension unit; reuses S1/S3 + audit | New report engine; report-wide editing; comments table; generic rules | V4 | No | Med |
| **P1** | Extraction line-item fidelity (8→1) | Preserve multiple source lines for PDF/IMAGE; reuse `line_items[]`; adjust gating so the multi-line path is not suppressed | none (contract = existing `line_items[]`) | Single extraction-layer correctness unit | Calculation change; EF-E; factor data; historical re-extraction | VP | **Yes** | Med-High |
| **P2** | EF-E picker correctness | Exact-unit equality → normalised/substring comparison on the processing mapping surface | none | Tiny localised fix; clear contract | P1; matcher replacement; factor data | VP | **Yes** | Low |
| **X1** | Phase 8-X Stage X1–X3 | Operational-visibility matrix (docs); worker/queue visibility (X2); health-path correctness + heartbeat + runtime introspection (X3) | PX-2/PX-4/PX-5 | One cohesive "observe the platform" unit; read-only; existing namespace | RLS; DATABASE_URL remediation; alerting; incident model | VX1 | **Yes** (own workstream) | Med |
| **X2** | Phase 8-X Stage X4–X7 | Aggregation service (`operational_intelligence.py`); unified failures/SLA/usage/imports/delivery/AI; console extension; alerting; API metrics | X1 + PX-6/PX-7 | One cohesive "breadth" unit after correctness | New dashboards; new metrics store; mutations of job state | VX2 | Conditional (after X1) | Med |

**Totals: 8 implementation batches · 7 independent verification gates (V1–V4, VP, VX1, VX2[conditional])**,
preceded by **Gate 0** (evidence/PO closure).

---

## 21. Recommended Verification Gates

Smallest set providing meaningful independent verification (one gate per cohesive unit; no gate verifies
more than one concern).

| Gate | After | Must be proven before the next batch |
|---|---|---|
| **G0** | (prerequisite — not implementation) | E1 evidence gap closed or explicitly scoped; PX-1 resolved; batch plan approved; production migration strategy for the 34-outstanding backlog agreed |
| **V1** | B1 | Schema is **additive** and idempotent; RLS state on the new tables is **designed and tested** (ALLOW + DENY); reference seed matches the verified framework/version/purpose set; no existing table mutated |
| **V2** | B2 | `evidence_line_items` rows are addressable; `source_line_item_id` links snapshot→line; backfill is **idempotent** (re-run = no dupes) and **non-destructive**; unmatchable rows stay `NULL`/`PARTIAL`; **no** re-extraction occurred |
| **V3** | B3 | Every disclosed value resolves to a persisted calculation/snapshot (provenance intact); applicability is period-dated and `UNDETERMINED` is preserved; **no** fabricated E1 identifiers; `report_type` unchanged |
| **V4** | B4 | Only permitted roles persist narrative; DRAFT-only edit; no write path to calculation/provenance/factor; `DM-5` blocks `CUSTOMER_INPUT_REQUIRED` and surfaces `NOT_SUPPORTED`; frozen artefact is immutable/hashed; lifecycle invariants (S1/S3) unregressed |
| **VP** | P1 + P2 | Multi-line PDF/IMAGE yields **multiple** extracted items (not 1); the cross-line activity/unit mixture is gone; EF-E unit-compatibility ALLOW/DENY; **no** regression on single-line electricity; P1 and P2 verified **separately** |
| **VX1** | X1 | Health reports **degraded** (not healthy) with the pool path unavailable; worker heartbeat/liveness accurate; queue counts reconcile to direct SQL; **no** secret exposure; non-staff denied, PE staff entity-scoped |
| **VX2** | X2 (conditional) | Failure/aggregate views reconcile to source tables; redaction review passed; alerts are rate-limited/idempotent (no storms); console is responsive/accessible (D21) |

**Gates G0 + V1–V4 + VP + VX1 + VX2.** VX2 is **conditional** (only if X2 proceeds). No stage claims
acceptance merely because it ran (AGENTS.md §52/§74).

---

## 22. Schema / API / Backend / Frontend Impact Matrix

| Batch | DB/schema | Backend | API | Frontend | Tests | Docs |
|---|---|---|---|---|---|---|
| **B1** | **New capability** (additive tables + RLS + indexes) | Extension (repos/services) | Extension | No change | New | Yes |
| **B2** | **Extension** (1 additive col) + **New capability** (`evidence_line_items`) | Extension | Extension | Optional (drill-down later) | New | Yes |
| **B3** | No change (uses B1) | Extension (read-only projections + mappings seed) | Extension | Extension (purpose views) | New | Yes |
| **B4** | **Extension** (narrative/artefact on report spine) | Extension | Extension | Extension | New | Yes |
| **P1** | No change (JSONB already exists) | **Requires change** (extraction only) | No change | No change | New regression | Yes |
| **P2** | No change | **Requires change** (picker query) | No change | No change | New | Yes |
| **X1** | Extension (heartbeat — PX-5) or no change if reuse-only | Extension | Extension (`/api/v3/ops/*`) | Extension (ops tabs) | New | Yes |
| **X2** | No change (views optional) | Extension | Extension | Extension | New | Yes |

**No change recommended merely for elegance.** B3 consumes calculation **read-only**; no engine change.
P1/P2 are the only batches touching existing shared code, and both are localised.

---

## 23. Production Blocker Matrix

Classified **without promoting accepted residuals** unless evidence shows impact.

| # | Blocker | Class | Evidence | Owner |
|---|---|---|---|---|
| BL-A | **RLS baseline: 97/104 tables RLS disabled + `anon` `GRANT ALL`** | **P0** | RLS baseline spec [V] | Separate RLS workstream |
| BL-B | **34 outstanding production migrations** (incl. P8 lifecycle `20260913000000`) | **P0** | RLS baseline §5.1 [V] | Deployment remediation |
| BL-C | **ESRS E1 identifier/coverage evidence gap** (`E1-COV` CONDITIONAL) | **P1** | verification report §6/§24.11 [U] | PO/evidence |
| BL-D | **Phase 8 naming/scope discrepancy** (roadmap vs this programme) — **disposition now recorded** (Decision Record §1.1, G0-B); master-roadmap wording preserved | **P2** | roadmap V1.0:26 [R] | PO / roadmap governance (PX-1) |
| BL-E | **PDF/IMAGE line-item extraction (8→1)** | **P1** | chat history [R/V] | P1 |
| BL-F | **Row-level evidence/provenance capability** | **P1** | design §14 [R] | B2 |
| BL-G | **EF-E picker exact-unit defect** | **P2** | chat history EF-E [V] | P2 |
| BL-H | **Legacy report disposition (D16)** | **P2** | open-decision closure §8 [R] | Separate |
| BL-I | **Phase 8-X runtime/deployment verification (BL-1/BL-2)** | **P2** | Phase 8-X §14 [R] | PO (PX-4) |
| BL-J | **Customer-shaped end-to-end calculation evidence** (residual) | **P2** | prior reports [U] | verify, don't assume |
| BL-K | **Subscription/allowance provisioning operability** (residual) | **P2** | Phase 8-X §17 [R] | verify |
| BL-L | **Worker shutdown cause / `DATABASE_URL` config** | **P2** | Phase 8-X §11 [R] | separate (PX-9) |

**Note:** BL-J/BL-K are recorded as **verify-before-claim** residuals, **not** auto-promoted, consistent
with the task instruction.

---

## 24. Phase 8-X Acceleration Plan

**Can Phase 8-X start partially in parallel with Phase 8? [REC] YES — the documentation, worker/queue
visibility and health-correctness slice (Stage X1–X3) can start immediately after PX-2/PX-4/PX-5, without
waiting for the Disclosure Model.**

| 8-X component | Can start in parallel? | Stable interface / dependency | Must wait for |
|---|---|---|---|
| X1 documentation (operational-visibility matrix) | **YES** | none | nothing (docs only) |
| X2 worker/queue visibility | **YES** | `document_processing_queue` repo + `/api/v3/ops/*` guard | nothing (superficial DEP-1 for the report-queue slice) |
| X3 health correctness + heartbeat + runtime introspection | **YES** (heartbeat subject to **PX-5**) | existing health surface + worker status | PLATFORM ACCESS for full verification (BL-1) |
| X4 aggregation (failures/SLA/usage/imports/delivery/AI) | **Partially** | read-only over existing repos | X2; DEP-1 for report slice |
| X5 console extension | Yes, after X2–X4 | existing ops console (27 files) | X2–X4 |
| X6 alerting | **NO** | `notifications`/`notification_delivery` | **PX-6** (recipients/channels/thresholds) |
| X7 API metrics | **NO** | needs an approved storage/retention decision | **PX-7**; no new metrics store without approval |

**Contracts to freeze before parallel work:**
1. The `/api/v3/ops/*` **namespace + guard contract** (`require_internal_staff()`; PE = entity-scoped).
2. The **read-only** design rule (no mutation of job state in the initial release).
3. The **redaction rule** (metadata over contents; no payloads/tokens/secrets).
4. The **heartbeat** decision (PX-5: schema row vs reuse-only).

**If No:** the reason would be BL-1/BL-2 (platform access) — but those block **verification**, not the
in-app slice. **No speculative APIs/schemas are created** by this assessment.

---

## 25. Implementation Order

```text
G0  Evidence / PO closure  (E1 evidence; PX-1; approve batch plan; migration strategy)
       │
       ├─────────────────────────── PARALLEL TRACK A (extraction) ───────────────
       │     P1  Extraction line-item fidelity (8→1)     → VP
       │     P2  EF-E picker correctness                 → VP
       │
       ├─────────────────────────── PARALLEL TRACK B (Phase 8-X) ────────────────
       │     X1  Stage X1–X3 (docs, worker/queue, health/runtime)  → VX1
       │     X2  Stage X4–X7 (aggregation, console, alerting, metrics) → VX2 (conditional)
       │
       └─────────────────────────── PHASE 8 CORE (critical path) ────────────────
             B1  Disclosure Model foundation            → V1
             B2  Evidence / line-item addressability    → V2
             B3  Disclosure Model integration           → V3
             B4  Narrative + frozen artefact + finalisation → V4
```

**Minimum practical counts:** **8 implementation batches** (B1–B4, P1, P2, X1, X2) · **7 independent
verification gates** (V1–V4, VP, VX1, VX2[conditional]) · **1 prerequisite gate** (G0). Three of the
batches (P1, P2, X1) are **fully parallelisable** from day one, so wall-clock time is materially shorter
than the batch count suggests.

---

## 26. Acceptance Principles

For every batch, acceptance must include (as applicable): **functional**, **regression**,
**provenance/evidence**, **authorization/security (ALLOW *and* DENY)**, **data-integrity**,
**migration/backfill** (idempotent, non-destructive), and **frontend/API**. Additionally:
- No claim of acceptance merely because a stage ran, a page loaded, or a unit test passed (AGENTS.md §74).
- Provenance: every disclosed figure resolves to a persisted snapshot; no manufactured granularity.
- `CUSTOMER_INPUT_REQUIRED` ≠ `NOT_SUPPORTED`; `UNDETERMINED` ≠ `NOT_APPLICABLE`.
- `report_type` unchanged; `purpose_code` separate; no assurance/certification/legal claims.
- Historical rows never rewritten; backfill re-runnable with zero duplicates.

---

## 27. Risks / Unknowns

| # | Risk / unknown | Severity | Note |
|---|---|---|---|
| R1 | **Phase 8 naming/scope** (roadmap "Advanced Analytics" vs reporting programme vs 8-capability prompt list) | **Resolved (Gate 0) for this programme** | Disposition recorded in `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` §1.1 (G0-B): governing terminology = Phase 8 Reporting/Disclosure programme; master-roadmap wording preserved; no third definition adopted. Any master-roadmap change remains a PO/roadmap-governance action |
| R2 | Referenced forensic reports **absent** | **Resolved (Gate 0)** | Formalized as `CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md` and `CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912.md` |
| R3 | `DM-7` Decision Record wording **lacked** the re-parsing refinement | **Resolved (Gate 0)** | `DM-7` now carries the explicit historical PDF/IMAGE re-parsing boundary (§6 refinement) |
| R4 | Production **migration backlog (34)** + RLS baseline | **High** | Deploy/remediation gate (BL-A/BL-B) |
| R5 | E1 concept-set seeding without identifiers | Med | Use internal concept keys + unresolved marker (`DM-1`) |
| R6 | Scope creep into a generic rules engine | High | D4; enumerated vocabularies |
| R7 | Phase 8-X **verification** blocked by platform access | Med | BL-1/BL-2 |
| R8 | Backfill correctness on mixed historical data | Med | Class-1 only; unmatched stays NULL |
| R9 | Regression of verified S1/S3 lifecycle | Med | B4 extends, never rewrites |
| R10 | Live DB not inspected in this task | — | All persisted-state claims are [R]/[U], not [V] at the live-DB level |

---

## 28. Deferred / Separate Work

Items not in any recommended batch: comments/`report_comments` (dormant); per-gas/GWP (`GP-GAS`);
base-year/recalculation (`GP-BY`); GRI; IFRS S2; 2026 ESRS revision; consolidation multi-approach;
Phase 8-X L1–L7 (incident model, SLOs, backup visibility, external APM, anomaly detection, composite
score, `/admin` control plane); RLS remediation; D16 legacy disposition; `DATABASE_URL` remediation;
backup/restore implementation; unrestricted AI/DB access. **None is implemented here.**

---

## 29. Final PO Decisions Required

| # | Decision | Why |
|---|---|---|
| **G0-A** | Close/scope the **ESRS E1 identifier** evidence gap (`E1-COV`) | Unblocks E1 seed rows in B3 |
| **G0-B** | Resolve **PX-1** (Phase 8 naming/scope) — **RESOLVED for this programme** in Decision Record §1.1; master-roadmap wording deliberately preserved | Remaining: PO/roadmap-governance update of the Master Roadmap, if desired |
| **G0-C** | Approve the **batch plan (B1–B4, P1, P2, X1–X2)** and the Option-B split | Authorises bounded prompts |
| **G0-D** | Agree the **production migration strategy** for the 34-outstanding backlog | Deploy readiness |
| **G0-E** | Confirm **B2 scope**: `evidence_line_items` + `source_line_item_id` + `disclosure_value_evidence` as MVP | Provenance boundary |
| **G0-F** | Confirm **P1 treatment** of historical PDF/IMAGE records (no auto re-extraction; re-parsing as separate authorised task) — **recorded** in `DM-7` §6 refinement | `DM-7` boundary |
| **G0-G** | Phase 8-X **PX-2/PX-4/PX-5/PX-6/PX-7** (MUST set; platform access; heartbeat; alerting; retention) | Unblocks X1/X2 |
| **G0-H** | Confirm **RLS remediation** stays a separate workstream | Security sequencing |
| **G0-I** | Refresh the **`DM-7`** wording to include the re-parsing refinement — **DONE** (Decision Record §6) | Conflict removed |

---

## 30. Recommended Next Action

1. **PO reviews this assessment** and resolves G0-A…G0-I.
2. On approval: issue a **bounded prompt for B1 only**, and **in parallel** a bounded prompt for
   **P2 (EF-E)** and the **Phase 8-X documentation stage (X1 docs)** — all three have no dependency on
   each other and none touches a verified subsystem.
3. **Do not** issue a prompt that bundles B1–B4, or P1+P2, or Phase 8-X with RLS.
4. **Do not** begin implementation until Gate 0 is closed.

---

## 31. Conclusion

The remaining scope is **large but not unknown**. Phase 8's genuinely new work is one cohesive layer
(Disclosure Model) plus one upstream correctness dependency (extraction) plus two small independent
fixes; Phase 8-X is mostly consolidation over data that already exists. **8 implementation batches** and
**7 verification gates** are sufficient and safe, with three tracks parallelisable from day one. The
hard blockers are **production governance** (RLS + 34 outstanding migrations) and **two evidence/scope
decisions** (E1 identifiers; the Phase 8 naming discrepancy) — all identified, none requiring invention.

**Final verdict:** `DECISION READINESS COMPLETE — READY FOR PO REVIEW`











