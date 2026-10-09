# CT-FEATURE-02 — FALSE-`IMPLEMENTED_AND_WIRED` REGISTER (FIEW)

**Task ID:** `CT-FEATURE-02-20260927-INDEPENDENT-VERIFICATION-…`
**Type:** READ-ONLY verification output. No source/migration/DB/production change.
**Companion documents:** `CT-PO-CARBONTALLY-FEATURE-CATALOGUE-INDEPENDENT-VERIFICATION-20260927.md` (primary), `CT-PO-CARBONTALLY-FEATURE-VERIFICATION-MATRIX-20260927.md` (matrix).
**Authority:** `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` (branch `p8-release-reconciled`).

---

## 0. Definition and rule

A row is registered here when Cline classified a feature `IMPLEMENTED_AND_WIRED`
but independent evidence shows the claimed **executable chain** depends on a
condition **absent from the authoritative durable environment** (flagship local
`postgres`, or any durable environment), per the task's §7 critical false-positive
rule.

**Downgrade rule applied:**
```
CLINE = IMPLEMENTED_AND_WIRED
AND ( feature persistence is created ONLY by an UNAPPLIED migration
      OR persistence exists ONLY in a disposable clone )
→ INDEPENDENT = BLOCKED_BY_SCHEMA | DISPOSABLE_ENVIRONMENT_ONLY
```

**Independently reproduced durability boundary** (read-only, flagship `postgres`, 2026-09-27):
ledger = 46 rows (max `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql`);
89 migration files on disk; **43 unapplied** (`20260905000000` → `20261020000000`);
`evidence_line_items`, `disclosure_requirement_versions`, `accounting_dimensions`,
`contractual_instruments`, `scope3_categories`, `carbontally_insight_conversations`,
`report_version_artifacts`, `activity_clarifications`, `estimation_records`,
`manual_processing_grants`, `locations` = **ABSENT**; `system_settings.operational_telemetry_retention_days` = **ABSENT**.

**Disclosure split (independently computed from the catalogue's own Truth cell):**
57 downgraded rows → **20 carry an explicit schema caveat** in the Truth cell (too-strong
token, disclosed) and **37 carry a plain `IMPLEMENTED_AND_WIRED` token** with no
schema caveat (undisclosed at row level).

**Column key (all 22 required columns):**
`ID` register id · `FTR` feature id · `FEATURE` · `DOMAIN` · `CLINE` Cline truth ·
`IND` independent status · `EVID_FOR` evidence for Cline · `EVID_AGAINST` evidence against ·
`BE` backend path · `API` api path · `FE/AD` frontend/admin path · `DB_DEP` database dependency ·
`MIG_DEP` migration dependency (unapplied unless stated) · `AUTH` authorization dependency ·
`CFG` runtime-configuration dependency · `TEST` test evidence · `DUR` durable-environment evidence ·
`DISP` disposable-only evidence · `HIST` historical-only evidence · `FINAL` · `CONF` confidence · `REASON`.

---

## 1. Cluster A — P17-A dimension columns (`20261010000000_p17a_…`, unapplied; verified ABSENT)

| ID | FTR | FEATURE | DOMAIN | CLINE | IND | EVID_FOR | EVID_AGAINST | BE | API | FE/AD | DB_DEP | MIG_DEP | AUTH | CFG | TEST | DUR | DISP | HIST | FINAL | CONF | REASON |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIEW-001 | FTR-044 | Organisation type & consolidation approach | D04 | I&W (repository) | BLOCKED_BY_SCHEMA | row "verified present only in ct_p17k_20260926" | `organizations` has no such columns in flagship | — | — | admin org forms | `organizations` | p17a (unapplied) | org admin | none | none | colonnes ABSENT | clone | none | BLOCKED_BY_SCHEMA | High | persistence created only by unapplied migration |
| FIEW-002 | FTR-076 | Acting-for attribution on results/logs | D09 | I&W (repository) | BLOCKED_BY_SCHEMA | cites p17a + reporting endpoints | acting_for columns ABSENT in flagship | `backend/domain/acting_for.py` | `/api/v3/reporting/audit-activity` | consultant UI | calc/snapshots cols | p17a (unapplied) | consultant auth | none | none | ABSENT | clone | none | BLOCKED_BY_SCHEMA | High | attribution columns only exist in clone |
| FIEW-003 | FTR-085 | Facility as accounting dimension | D11 | I&W (repository) | BLOCKED_BY_SCHEMA | p17a adds `facility_id` | `facility_id` ABSENT in flagship | `engines/calculation.py` | — | — | calc/emissions cols | p17a (unapplied) | — | — | none | ABSENT | clone | none | BLOCKED_BY_SCHEMA | High | column clone-only |
| FIEW-004 | FTR-135 | Data-quality dimension on results | D19 | I&W (repository) | BLOCKED_BY_SCHEMA | p17a adds `data_quality` | column ABSENT in flagship | `domain/insight_quality.py` | — | — | calc/emissions cols | p17a (unapplied) | — | — | none | ABSENT | clone | none | BLOCKED_BY_SCHEMA | High | column clone-only |
| FIEW-005 | FTR-144 | Factor governance attributes | D21 | I&W (repository) | BLOCKED_BY_SCHEMA | p17a §3 adds 4 cols | cols ABSENT in flagship | `domain/provider.py` | `/api/v2/admin/providers` | — | `emission_factors` | p17a (unapplied) | staff admin | — | none | ABSENT | clone | none | BLOCKED_BY_SCHEMA | High | governance attrs clone-only |
| FIEW-006 | FTR-149 | Scope 1 energy-type dimension | D22 | I&W (repository) | BLOCKED_BY_SCHEMA | p17a adds `energy_type` + CHECK | ABSENT in flagship | `engines/calculation.py` | — | — | calc/emissions cols | p17a (unapplied) | — | — | none | ABSENT | clone | none | BLOCKED_BY_SCHEMA | High | dimension clone-only |
| FIEW-007 | FTR-153 | Location-based method constraint enforcement | D23 | I&W (repository) | BLOCKED_BY_SCHEMA | p17a CHECKs on `scope2_method` | ABSENT in flagship | `services/scope2_calculation.py` | `/api/v3/scope2` | — | calc cols | p17a (unapplied) | — | — | none | ABSENT | clone | none | BLOCKED_BY_SCHEMA | High | constraint clone-only |
| FIEW-008 | FTR-167 | Scope 3 category-specific dimensions | D27 | I&W (repository) | BLOCKED_BY_SCHEMA | p17a + p17-10 cols | ABSENT in flagship | `services/scope3_calculation.py` | — | — | calc/emissions cols | p17a, p17_10 (unapplied) | — | — | none | ABSENT | clone | none | BLOCKED_BY_SCHEMA | High | dimensions clone-only |
| FIEW-009 | FTR-170 | Accounting-dimension columns on results | D28 | I&W (repository) | BLOCKED_BY_SCHEMA | p17a adds 10 cols | `accounting_dimensions` is not a table; cols ABSENT | `data/accounting_context.py` | `/api/v3/accounting` | — | calc/emissions cols | p17a (unapplied) | accounting auth | — | none | ABSENT | clone | none | BLOCKED_BY_SCHEMA | High | 10 columns absent; naming drift |
| FIEW-010 | FTR-173 | Consolidation approach & org type context | D28 | I&W (repository) | BLOCKED_BY_SCHEMA | p17a §5 adds cols | ABSENT in flagship | `domain/cams.py` | — | admin | `organizations` | p17a (unapplied) | org admin | — | none | ABSENT | clone | none | BLOCKED_BY_SCHEMA | High | columns clone-only |
| FIEW-011 | FTR-174 | Product-contract reporting dimensions | D28 | I&W (repository) | BLOCKED_BY_SCHEMA | p17-10 alters snapshots+logs | ABSENT in flagship | — | — | — | calc/emissions cols | p17_10 (unapplied) | — | — | none | ABSENT | clone | none | BLOCKED_BY_SCHEMA | High | columns clone-only |

## 2. Cluster A2 — P17-C/D/H clone-only objects

| ID | FTR | FEATURE | DOMAIN | CLINE | IND | EVID_FOR | EVID_AGAINST | MIG_DEP | DUR | DISP | FINAL | CONF | REASON |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIEW-012 | FTR-157 | Contractual instrument repository | D25 | I&W (repository) | DISPOSABLE_ENVIRONMENT_ONLY | p17c creates tables | `contractual_instruments` ABSENT in flagship | p17c (unapplied) | ABSENT | clone | DISPOSABLE_ENVIRONMENT_ONLY | High | table only in clone |
| FIEW-013 | FTR-158 | Instrument allocations | D25 | I&W (repository) | DISPOSABLE_ENVIRONMENT_ONLY | p17c | `instrument_allocations` ABSENT | p17c (unapplied) | ABSENT | clone | DISPOSABLE_ENVIRONMENT_ONLY | High | table only in clone |
| FIEW-014 | FTR-161 | Instrument allocation to consumption | D26 | I&W (repository) | DISPOSABLE_ENVIRONMENT_ONLY | p17c | ABSENT | p17c (unapplied) | ABSENT | clone | DISPOSABLE_ENVIRONMENT_ONLY | High | table only in clone |
| FIEW-015 | FTR-164 | Scope 3 category taxonomy (15) | D27 | I&W (repository) | DISPOSABLE_ENVIRONMENT_ONLY | p17d creates `scope3_categories` | ABSENT in flagship | p17d (unapplied) | ABSENT | clone (15 rows) | DISPOSABLE_ENVIRONMENT_ONLY | High | taxonomy only in clone |
| FIEW-016 | FTR-169 | Scope 3 estimation & assumptions | D27 | I&W (repository) | DISPOSABLE_ENVIRONMENT_ONLY | p17h creates `estimation_records` | ABSENT in flagship | p17h (unapplied) | ABSENT | clone | DISPOSABLE_ENVIRONMENT_ONLY | High | table only in clone |
| FIEW-017 | FTR-175 | Estimation records (P17-H) | D29 | I&W (repository) | DISPOSABLE_ENVIRONMENT_ONLY | p17h | ABSENT | p17h (unapplied) | ABSENT | clone | DISPOSABLE_ENVIRONMENT_ONLY | High | table only in clone |

## 3. Cluster A3 — P16-R (unapplied)

| ID | FTR | FEATURE | DOMAIN | CLINE | IND | EVID_FOR | EVID_AGAINST | MIG_DEP | DUR | DISP | FINAL | CONF | REASON |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIEW-018 | FTR-181 | Calculation idempotency (request id) | D30 | I&W (repository) — unique index clone-only | BLOCKED_BY_SCHEMA | p16r7 creates unique index | index/column ABSENT in flagship | p16r7 (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | idempotency key not durable |
| FIEW-019 | FTR-182 | Result reportability lifecycle | D30 | I&W (repository) — column absent in 4/5 DBs | BLOCKED_BY_SCHEMA | p16r5 alters snapshots/logs | `reportability_status` ABSENT in flagship | p16r5 (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | lifecycle column not durable |

## 4. Cluster A4 — Gate 4/5/6 automation provenance (unapplied)

| ID | FTR | FEATURE | DOMAIN | CLINE | IND | EVID_FOR | EVID_AGAINST | MIG_DEP | DUR | DISP | FINAL | CONF | REASON |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIEW-020 | FTR-184 | Calculation actor attribution (Gate 4) | D30 | I&W | BLOCKED_BY_SCHEMA | MIG present | `20260905000000` UNAPPLIED; attribution cols absent | gate4 (unapplied) | ABSENT | none | BLOCKED_BY_SCHEMA | High | migration only; not applied |
| FIEW-021 | FTR-185 | Machine/automation provenance gates (Gate 5) | D30 | I&W | BLOCKED_BY_SCHEMA | MIG present | `20260905010000`,`20260905020000` UNAPPLIED | gate5 (unapplied) | ABSENT | none | BLOCKED_BY_SCHEMA | High | migration only; not applied |
| FIEW-022 | FTR-186 | Human-after-automation attribution (Gate 6) | D30 | I&W | BLOCKED_BY_SCHEMA | MIG present | `20260906010000` UNAPPLIED | gate6 (unapplied) | ABSENT | none | BLOCKED_BY_SCHEMA | High | migration only; not applied |

## 5. Cluster B — Evidence

| ID | FTR | FEATURE | DOMAIN | CLINE | IND | EVID_FOR | EVID_AGAINST | BE | API | MIG_DEP | DUR | DISP | FINAL | CONF | REASON |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIEW-023 | FTR-111 | Activity clarifications & adjudication lifecycle | D15 | I&W | BLOCKED_BY_SCHEMA | MIGs + API `/api/v3/activity-clarifications`(5) | `activity_clarifications` ABSENT in flagship (verified) | `domain/activity_clarification.py` | `/api/v3/activity-clarifications` | p8_fs_* (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | persistence absent durably |
| FIEW-024 | FTR-127 | Evidence line items (P8-B2) | D18 | I&W | BLOCKED_BY_SCHEMA | MIG + API + route | `evidence_line_items` **ABSENT** in flagship (verified) | `data/evidence_line_items.py` | `/api/v3/evidence` | p8_b2 (unapplied) | ABSENT | clone(0) | BLOCKED_BY_SCHEMA | High | no durable evidence store |
| FIEW-025 | FTR-128 | Provenance line links | D18 | I&W | BLOCKED_BY_SCHEMA | MIG + BE | table ABSENT (unapplied p8_b2 links) | `data/evidence_line_items.py` | `/api/v3/evidence` | p8_b2_line_links (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | link table not durable |
| FIEW-026 | FTR-130 | Evidence idempotency & correction privileges | D18 | I&W | BLOCKED_BY_SCHEMA | MIG present | `disclosure_value_evidence` ABSENT (unapplied) | `services/disclosure_*` | `/api/v3/disclosure` | p8_b1 (20260915, unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | Med-High | dependency not durable |

## 6. Cluster C — Reporting artefacts & disclosure model

| ID | FTR | FEATURE | DOMAIN | CLINE | IND | EVID_FOR | EVID_AGAINST | BE/API | MIG_DEP | DUR | DISP | FINAL | CONF | REASON |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIEW-027 | FTR-178 | Estimation disclosure narrative integration | D29 | I&W | BLOCKED_BY_SCHEMA | MIG 20260918 + BE | `disclosure_narrative_entries` ABSENT (unapplied) | `services/disclosure_narrative.py` | p8_b4 (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | table not durable |
| FIEW-028 | FTR-211 | Report lifecycle & catalogue (status machine) | D34 | I&W | PARTIALLY_IMPLEMENTED/BLOCKED | report tables exist | lifecycle-status MIG 20260913 UNAPPLIED → status column absent | `/api/v3/reports`(14) | p8_report_lifecycle (unapplied) | table present; status absent | — | BLOCKED_BY_SCHEMA (partial) | High | lifecycle column not durable |
| FIEW-029 | FTR-219 | Intensity catalogue & ratios (B3) | D34 | I&W | DISPOSABLE_ENVIRONMENT_ONLY | MIGs exist | `disclosure_intensity_*` ABSENT in flagship | — | p8_b3 (unapplied) | ABSENT | qa133 yes | DISPOSABLE_ENVIRONMENT_ONLY | High | qa/clone-only |
| FIEW-030 | FTR-220 | Report finalisation & frozen artefact (B4) | D34 | I&W | DISPOSABLE_ENVIRONMENT_ONLY | MIG exists | `report_version_artifacts` **ABSENT** in flagship (verified) | `services/report_artefact_storage.py` | p8_b4_frozen (unapplied) | ABSENT | qa133 yes | DISPOSABLE_ENVIRONMENT_ONLY | High | qa/clone-only |
| FIEW-031 | FTR-223 | Report versions `is_current` integrity (S2) | D35 | I&W | BLOCKED_BY_SCHEMA | `report_versions` present | single-valued MIG 20260921 UNAPPLIED | — | p8_s2 (unapplied) | table present; rule absent | — | BLOCKED_BY_SCHEMA | High | integrity rule not durable |
| FIEW-032 | FTR-224 | Version artefacts (rendered files) | D35 | I&W | DISPOSABLE_ENVIRONMENT_ONLY | MIG + BE | `report_version_artifacts` ABSENT | `data/report_artefacts.py` | p8_b4 (unapplied) | ABSENT | qa133 yes | DISPOSABLE_ENVIRONMENT_ONLY | High | qa/clone-only |
| FIEW-033 | FTR-226 | Disclosure model foundation | D36 | I&W | BLOCKED_BY_SCHEMA | 11 tables in MIG 20260914 | all `disclosure_*` ABSENT in flagship | `services/disclosure_*` | p8_b1 (unapplied) | ABSENT | clone/qa133 | BLOCKED_BY_SCHEMA | High | foundation not durable |
| FIEW-034 | FTR-227 | Governed requirement-version rows (P17-K) | D36 | I&W | BLOCKED_BY_SCHEMA | 55 rows in clone | `disclosure_requirement_versions` **ABSENT** (verified) | `domain/capability_catalogue.py` | p8_b1 + p17k (unapplied) | ABSENT | clone (55) | BLOCKED_BY_SCHEMA | High | reference rows not durable |
| FIEW-035 | FTR-228 | Disclosure values & value-evidence | D36 | I&W | BLOCKED_BY_SCHEMA | MIG 20260915 | `disclosure_values`/`_value_evidence` ABSENT | `data/disclosure_*` | p8_b1 (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | tables not durable |
| FIEW-036 | FTR-229 | Disclosure narrative overlay (B4) | D36 | I&W | BLOCKED_BY_SCHEMA | MIG 20260918 | `disclosure_narrative_entries` ABSENT | `services/disclosure_narrative.py` | p8_b4 (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | table not durable |
| FIEW-037 | FTR-230 | Disclosure projection engine | D36 | I&W | BLOCKED_BY_SCHEMA | BE modules present | depends on disclosure tables ABSENT | `services/disclosure_projection.py` | p8_b1 (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | projection has no durable input |
| FIEW-038 | FTR-231 | Disclosure purposes & instance binding | D36 | I&W | BLOCKED_BY_SCHEMA | MIG 20260914 | `disclosure_report_purposes` etc ABSENT | — | p8_b1 (unapplied) | ABSENT | qa133 | BLOCKED_BY_SCHEMA | High | tables not durable |
| FIEW-039 | FTR-232 | Disclosure applicability assessments | D36 | I&W | BLOCKED_BY_SCHEMA | MIG 20260914 | table ABSENT | — | p8_b1 (unapplied) | ABSENT | qa133 | BLOCKED_BY_SCHEMA | High | table not durable |
| FIEW-040 | FTR-233 | Disclosure finalisation service | D36 | I&W | BLOCKED_BY_SCHEMA | `api/v3_disclosure.py`(15) exists | depends on disclosure tables ABSENT | `services/disclosure_finalisation.py` | p8_b1 (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | no durable finalisation store |

## 7. Cluster D — Insight (schema absent in every durable environment)

| ID | FTR | FEATURE | DOMAIN | CLINE | IND | EVID_FOR | EVID_AGAINST | BE/API/UI | MIG_DEP | DUR | DISP | FINAL | CONF | REASON |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIEW-041 | FTR-234 | Insight Layer-1 persistence (I1) | D37 | I&W (repository) — schema absent in every durable DB | BLOCKED_BY_SCHEMA | MIG 20261001 | `carbontally_insight_*` **ABSENT** (verified) | `data/insight.py` | p8_i1 (unapplied) | ABSENT | clone/test | BLOCKED_BY_SCHEMA | High | persistence not durable |
| FIEW-042 | FTR-235 | Insight L1 authorization boundary (I2) | D37 | I&W | BLOCKED_BY_SCHEMA | MIG 20261002 + BE | authz over absent tables | `api/insight_authz.py` | p8_i2 (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | boundary over absent schema |
| FIEW-043 | FTR-236 | Insight tool catalogue (I3) | D37 | I&W | BLOCKED_BY_SCHEMA | BE + API 3 | tools read absent persistence | `services/insight_tools.py` `/api/v3/insight/tools` | p8_i1 (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | Med-High | tools have no durable data |
| FIEW-044 | FTR-237 | Insight L2 interaction orchestration (I4) | D37 | I&W | BLOCKED_BY_SCHEMA | MIG 20261003 | `carbontally_insight_interactions` ABSENT | `/api/v3/insight/interactions` | p8_i4 (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | table not durable |
| FIEW-045 | FTR-238 | Insight planner/context/rate-limit/leases | D37 | I&W | BLOCKED_BY_SCHEMA | MIG 20261005 | `insight_rate_limit_buckets` ABSENT | `services/insight_rate_limit.py` | p8_insight… (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | tables not durable |
| FIEW-046 | FTR-239 | Insight temporal comparison (P2) | D37 | I&W | BLOCKED_BY_SCHEMA | MIG 20261006 + UI | tables ABSENT | `insight/InsightComparison.jsx` | p8_insight (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | backend absent |
| FIEW-047 | FTR-240 | Insight data-quality + reproducibility (P3) | D37 | I&W | BLOCKED_BY_SCHEMA | MIG 20261007 | tables ABSENT | `domain/insight_quality.py` | p8_insight (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | backend absent |
| FIEW-048 | FTR-241 | Insight customer UI | D37 | I&W | BLOCKED_BY_SCHEMA | UI files `InsightPage.jsx` exist | UI renders over ABSENT backend | `insight/InsightPage.jsx` route `/insight` | p8_i1 (unapplied) | ABSENT | clone | BLOCKED_BY_SCHEMA | High | UI exists, backend not durable |

## 8. Cluster E — Governance / RLS / capability

| ID | FTR | FEATURE | DOMAIN | CLINE | IND | EVID_FOR | EVID_AGAINST | BE/API | MIG_DEP | DUR | FINAL | CONF | REASON |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIEW-049 | FTR-036 | Anonymised/public grant containment | D03 | I&W | BLOCKED_BY_SCHEMA | 3 MIGs named | `20260920/22/23` UNAPPLIED; only baseline RLS present (174 policies) | — | p8_rls_* (unapplied) | baseline only | BLOCKED_BY_SCHEMA (partial) | High | hardening migrations not applied |
| FIEW-050 | FTR-142 | `emission_factors` internal containment | D20 | I&W | BLOCKED_BY_SCHEMA | MIG 20260926 | UNAPPLIED | — | p8_d4 (unapplied) | absent | BLOCKED_BY_SCHEMA | High | containment not applied |
| FIEW-051 | FTR-146 | Provider ownership & provider-driven updates | D21 | I&W | PARTIALLY/BLOCKED | `/api/v2/admin/providers`(2) present | containment MIG 20260926 UNAPPLIED | `domain/provider.py` | p8_d4 (unapplied) | base present | BLOCKED_BY_SCHEMA (partial) | Med | base works; hardening blocked |
| FIEW-052 | FTR-147 | Governed capability statement of factor support | D21 | I&W | BLOCKED_BY_SCHEMA | MIG 20261020 (reference data only) | `disclosure_requirement_versions` **ABSENT** (verified) | `domain/capability_catalogue.py` | p8_b1+p17k (unapplied) | ABSENT | BLOCKED_BY_SCHEMA | High | reference data has no durable table |
| FIEW-053 | FTR-193 | Manual-processing governance grants (FIN-06) | D31 | I&W | BLOCKED_BY_SCHEMA | MIG 20260927 + API admin/manual-processing(4) | `manual_processing_grants` **ABSENT** (verified) | `api/manual_processing_auth.py` | p8_fin06 (unapplied) | ABSENT | BLOCKED_BY_SCHEMA | High | grant table not durable |
| FIEW-054 | FTR-306 | RLS policy layer & tenant containment (hardening) | D46 | I&W | BLOCKED_BY_SCHEMA | 9 MIGs named | `20260920-20260926` UNAPPLIED; 174 baseline policies only | `qa_harness/db/rls.py` | p8_rls_* (unapplied) | baseline only | BLOCKED_BY_SCHEMA (partial) | High | hardening not applied |
| FIEW-055 | FTR-327 | Entitlement resolution per organisation (RLS gating) | D49 | I&W | BLOCKED_BY_SCHEMA | API present | `HAS_ENTITLEMENT` gating MIG 20260925 UNAPPLIED | `/api/v3/commercial/entitlement/…` | p8_rls_4b (unapplied) | absent | BLOCKED_BY_SCHEMA (partial) | Med | RLS gating not applied |
| FIEW-056 | FTR-331 | Governed capability catalogue reference data (P17-K) | D50 | I&W | DOCUMENTED_ONLY/REFERENCE_DATA | MIG 20261020 | creates **no object**; UNAPPLIED; target tables absent | `domain/capability_catalogue.py` | p17k (unapplied) | ABSENT | DOCUMENTED_ONLY | High | no executable effect |
| FIEW-057 | FTR-334 | Plan → capability entitlement mapping | D50 | I&W | BLOCKED_BY_SCHEMA | API present | entitlement RLS gating MIG 20260925 UNAPPLIED | `/api/v3/commercial/plans` | p8_rls_4b (unapplied) | absent | BLOCKED_BY_SCHEMA (partial) | Med | gating not applied |

---

## 9. Secondary (lower-confidence) observations — not counted in the 57

| FTR | FEATURE | CLINE | OBSERVATION | SUGGESTED STATUS | CONF |
|---|---|---|---|---|---|
| FTR-124 | Quality chain PE QC → CT QC → customer approval | I&W | evidence is MIG(20260902, applied)+DOC only; no wired path located | SCHEMA_ONLY / UNEXERCISED | Med |
| FTR-129 | Evidence traceability columns (D33) | I&W | MIG(20260823)+DOC only; migration applied but no distinct wired surface located | SCHEMA-supported, surface unproven | Med |
| FTR-191 | Dual-origin workflow (V1.2) | I&W | MIG(applied)+DOC only | SCHEMA_ONLY / DOCUMENTED | Med |
| FTR-200 | QC approval boundary enforcement | I&W | DOC+MIG(applied) only | schema-supported, unexercised | Med |
| FTR-204 | Audit/activity immutability (WS1/P7) | I&W | `audit_activity_immutability` applied; `p7_audit_immutability_and_indexes` (20260912) UNAPPLIED | PARTIALLY_IMPLEMENTED | Med |
| FTR-251 | Notification event-key production (WS3/D40) | I&W | MIG(applied) only | schema-supported | Low |
| FTR-323 | Billing security & configurable subscription foundation | I&W | MIG(applied) only; all billing transactional tables 0 rows | schema-supported, unexercised | Low |
| FTR-056/067/194 | Consultant processing-mode provenance (D7) | I&W | base rows exist; provenance MIGs (`20260906100000`,`20260910120000`) UNAPPLIED | PARTIALLY_IMPLEMENTED | Med |

## 10. Corrective action for every registered row

1. Change the **Truth token** from `IMPLEMENTED_AND_WIRED` to
   `IMPLEMENTED_IN_CODE_BUT_BLOCKED_BY_SCHEMA` (clusters A, B, C-status, E) or
   `DISPOSABLE_ENVIRONMENT_ONLY` (clusters A2, D-aria) or `DOCUMENTED_ONLY`
   (FIEW-056), keeping the existing Evidence cell.
2. Recompute the headline count: **`313 IMPLEMENTED_AND_WIRED` → `256` durable-and-wired**
   (313 − 57), pending the W1 migration application.
3. Re-test after `GA-01` (apply the 43 migrations) is executed on a declared durable
   environment; any row whose object then exists may be restored to `IMPLEMENTED_AND_WIRED`.

## 11. Cross-register checks (2026-09-28)

* **The CT-IMPLEMENT-04 factor-read repoint (CT-SCHEMA-03 F-05/F-09) touches no row
  of this register.** The 57 registered rows are schema-blocked *features*; none of
  them is the retired factor read path. The three rows that mention factors —
  `FIEW-005` (factor governance attributes), `FIEW-050` (`emission_factors`
  internal containment) and `FIEW-052` (capability statement of factor support) —
  concern unapplied migrations (`p17a`, `p8_d4`, `p17k`) that this remediation
  neither applies nor depends on, so their status is unchanged.

<!--CTEOF-->
