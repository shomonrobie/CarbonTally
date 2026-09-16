---
Document Type: Task Report (DISCOVERY — no implementation)
Project: CarbonTally
Task Reference: CT-P8-REPORTING-COMPLIANCE-ARCHITECTURE-DISCOVERY-20260912-001
Status: COMPLETE
Created: 2026-09-12
---

# Task Report — CT-P8-REPORTING-COMPLIANCE-ARCHITECTURE-DISCOVERY-20260912-001

## 1. Task Reference

`CT-P8-REPORTING-COMPLIANCE-ARCHITECTURE-DISCOVERY-20260912-001`

## 2. Scope

Establish, on evidence, CarbonTally's reporting/disclosure architecture:

1. applicable authoritative carbon-accounting/reporting requirements;
2. relevant regulatory requirements;
3. relevant voluntary frameworks;
4. the actual current implementation and report architecture;
5. provisions for change as regulations/frameworks evolve.

Mandated separation of **(A)** legal/regulatory, **(B)** voluntary standards,
**(C)** guidance, **(D)** CarbonTally product/management enhancements — with C and
D never represented as compliance requirements.

**Explicitly out of scope / prohibited (all respected):** any implementation;
schema or migration changes; API changes; frontend changes; RLS or authorization
changes; report lifecycle changes; Phase 8 S4 Narrative Overlay implementation;
PDF freezing; AI implementation; billing; production/deployment changes; fixing
unrelated defects.

## 3. Sources Inspected

### 3.1 Authoritative external sources (retrieved, not recalled)

| # | Source | Retrieval |
|---|---|---|
| 1 | UK Government — *Environmental reporting guidelines: including Streamlined Energy and Carbon Reporting requirements* (DESNZ/Defra) | HTTP 200, 76 KB HTML |
| 2 | UK Government — *Environmental reporting guidance (SECR), March 2019* (152 pp PDF) | HTTP 200, 1.54 MB PDF, extracted via `pdftotext -layout` (6,488 lines) |
| 3 | GHG Protocol — *Corporate Standard* (revised edition) PDF | HTTP 200, 3.68 MB PDF → 7,278 lines |
| 4 | IFRS Foundation — *IFRS S2 Climate-related Disclosures* | HTTP 200, 114 KB HTML |
| 5 | EUR-Lex — *Directive (EU) 2022/2464* (CSRD) | HTTP 200, 894 KB HTML |
| 6 | EUR-Lex — *Commission Delegated Regulation (EU) 2023/2772* (ESRS) | HTTP 200, 5.65 MB HTML |
| 7 | GRI — GRI 305 standard publication | **NOT RETRIEVED** (HTTP 404 on PDF; no 305 content captured) |

### 3.2 CarbonTally documents inspected

* `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` (existence verified)
* `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` (existence verified)
* `CARBONTALLY_PHASE8_DISCOVERY_AND_CAPABILITY_GAP_ANALYSIS_20260912.md`
* `CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` (§9, §10, §15, §16, stage table)
* `CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md` (§4.2, §4.3, D-01)
* `CARBONTALLY_PHASE8_OPEN_DECISION_CLOSURE_AND_IMPLEMENTATION_AUTHORISATION_20260912.md` (A1/A3, S1–S4 matrix, authorisation status)
* `CARBONTALLY_PHASE8_ASK_CARBONTALLY_PERSISTENT_CONVERSATION_AND_AI_AUDITABILITY_DISCOVERY_20260912.md` (existence verified)
* `CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` (existence verified)
* `AGENTS.md` (governance: RLS policy, database change policy, §79 legacy code)

All eight task-named documents were **confirmed to exist** before use.

### 3.3 Repository (implementation) inspected

* `backend/engines/report_generation.py` — `_SECTION_ORDER` (line 65), module
  docstring, `ReportContent`, `ENGINE_VERSION`
* `backend/api/v3_reports.py` — `SUPPORTED_REPORT_TYPES` (line 63), all 14 routes,
  S3 lifecycle authorization
* `backend/report_generator.py` — legacy `EnhancedSustainabilityReportGenerator`,
  compliance strings (lines 328, 1008), CSRD/ISSB placeholders (1058-1060),
  router (line 19, endpoint line 1040)
* `backend/routes/reports.py` — router prefix `/api/reports`, legacy router inclusion
* `backend/main.py` — router mounting (line 213 mounts `reports`; 212 mounts `upload`)
* `backend/utils/emissions.py` — `get_activity_category` CSRD/ISSB/GHG mapping
* `backend/routes/upload.py` — mapping consumer
* `backend/utils/email.py` — compliance-report claim (line 239)
* `supabase/migrations/20260913000000_p8_report_lifecycle_status.sql` — status CHECK
* `frontend/src/v3/reports/{ReportsPage,ReportDetailPage}.jsx`,
  `frontend/src/v3/__tests__/reports-page.test.jsx`
* `backend/tests/unit/api/test_v3_reports.py`, `test_v3_report_lifecycle.py`,
  `test_reporting.py`

### 3.4 Database / schema inspected (read-only)

* `activity_categories` — columns `esrs_e1_category`, `issb_category`,
  `ghg_protocol_scope`, `ghg_protocol_category` (verified via
  `information_schema.columns`), and **row count: 0**
* `report_versions` / lifecycle status vocabulary (via the S3 migration)

## 4. Commands / Checks Performed

| Check | Result |
|---|---|
| `git rev-parse HEAD` / `git branch --show-current` | `19e4f01c…` on `main` |
| `git status --short` | 208 modified, 57 untracked, **0 staged** |
| Existence check of 8 task-named documents | **all EXISTS** |
| `grep` of engine `_SECTION_ORDER` | **12 sections verified** |
| `grep` for `SUPPORTED_REPORT_TYPES` | `{"annual": …}` verified |
| `grep` of S3 migration for status vocabulary | DRAFT/REVIEWED/CHANGES_REQUESTED/REJECTED/APPROVED/FINAL verified |
| `grep` for report endpoints | 14 routes verified |
| `grep` for compliance framework mentions | legacy compliance claims + CSRD/ISSB/ESRS mapping found |
| `grep` for legacy mounting | `main.py:213` → `routes/reports.py:30` → **live route** |
| `information_schema` column query on `activity_categories` | 4 framework-mapping columns present |
| Row-count query on `activity_categories` | **0 rows** |
| **`pytest` read-only: `test_v3_reports.py`, `test_v3_report_lifecycle.py`, `test_reporting.py`** | **118 passed, 0 failed** (S1/S3 intact) |
| Authoritative source retrieval (7 URLs) | 6 retrieved, 1 not available (GRI 305) |

Temporary working files were written to `/tmp` only. **No temporary files were
created inside the repository**; nothing required cleanup in the worktree.

## 5. Findings

### 5.1 The central architectural finding
The V3 reporting architecture is **`DATA → FIXED 12-SECTION REPORT`**. The
evidence supports **`DATA → DISCLOSURE MODEL → PRESENTATION`**, because:

* **no framework investigated requires a 12-section structure** (GHG Protocol
  specifies required *information*; SECR specifies required *disclosures*; ESRS
  specifies *datapoints*);
* the GHG Protocol Corporate Standard **itself** separates **"Required
  information"** from **"Optional information"** and labels chapters **STANDARD**
  vs **GUIDANCE** — a two-tier distinction CarbonTally's model cannot express;
* of the 12 sections, ~4 carry (partial) required content, ~6 are CarbonTally
  evidence/technical metadata, and 2 map to *optional* framework content.

### 5.2 Required disclosures missing from the current structure
GHG Protocol required: organizational boundary + **consolidation approach**;
operational boundary (+ scope 3 list); **six GHGs separately**; **base year** +
recalculation policy + trend; recalculation context; **biologically sequestered
carbon**; **specific exclusions**; causes of non-recalculating changes;
**offsets**; facility list; inventory-quality/uncertainty; contact person.
SECR (legal): **intensity ratio**; **previous-year figures**; **energy use in
kWh**; **energy efficiency action taken** (narrative); methodology (partial).

### 5.3 Existing capability is structural, not real
`activity_categories` carries `esrs_e1_category`, `issb_category`,
`ghg_protocol_scope`, `ghg_protocol_category` — but holds **0 rows**. A column's
existence is not evidence of support.

### 5.4 Material documentation-vs-implementation discrepancy
The Phase 8 ratification states legacy reporting is **"unmounted and
unreferenced"**. Implementation shows the legacy generator **is mounted**:
`backend/main.py:213` → `backend/routes/reports.py:30` →
`backend/report_generator.py:1040` = **`POST /api/reports/generate-enhanced-report`**.
That route **emits PDF text asserting "Compliant with SECR/CSRD/ISSB reporting
standards"** (`report_generator.py:328`), states the report "has been prepared in
accordance with the … (SECR) regulations" (`:1008`), and returns the **SECR**
report for `report_type` values `CSRD` and `ISSB` with the comment
`# Placeholder` (`:1058-1060`). A separate product claim appears in
`backend/utils/email.py:239`. **Reported, not fixed** — fixing is prohibited by
this task.

### 5.5 GRI 305 — evidence gap
**Not established from authoritative source.** The GRI 305 publication could not
be retrieved; no GRI 305 content informed this report.

### 5.6 Applicability uncertainties
* **CSRD/ESRS phased application dates** — **UNVERIFIED** in this pass.
* **IFRS S2 jurisdiction adoption** — **UNVERIFIED**; the standard is effective
  1 Jan 2024, but legal force depends on adoption.
* **GRI 305 content** — not established.

## 6. Decisions Required from PO

PO-1 initial framework scope · PO-2 disclosure model vs fixed sections ·
PO-3 role of the 12-section report · PO-4 template/configuration strategy ·
PO-5 narrative architecture boundary · PO-6 supported purposes ·
PO-7 Ireland/EU scope · PO-8 additional discovery before S4 ·
**PO-9 disposition of the live legacy compliance-claim route and claims** ·
PO-10 offsets/sequestration/facility-list product scope ·
PO-11 XBRL/iXBRL tagging need · PO-12 IFRS S2 adoption position ·
PO-13 CSRD/ESRS phased dates currently in force.

Recommended options and consequences are given in §23 of the discovery report.
**No PO decision was made in this task.**

## 7. Unresolved Questions

1. Which frameworks are in the **initial** catalogue (PO-1)?
2. Does CarbonTally adopt a **disclosure model** (PO-2)?
3. What is the **12-section** report's status (PO-3)?
4. Is the 7-key narrative allowlist and its limits retained, replaced or
   requirement-bound (PO-5)?
5. Are the current **CSRD/ESRS** phased dates in force (PO-13)?
6. Is **IFRS S2** adopted in any target jurisdiction (PO-12)?
7. What is **GRI 305**'s authoritative content, and is GRI in scope at all?
8. What is the **disposition of the live legacy route** and its compliance
   claims (PO-9)?
9. Are **offsets / sequestration / facility lists** in product scope (PO-10)?
10. Is **digital tagging** required for any customer (PO-11)?

## 8. Implementation Blockers

| # | Blocker | Type |
|---|---|---|
| B1 | Framework scope not PO-ratified (PO-1) | **Blocks the disclosure model's content** |
| B2 | Disclosure-model adoption not ratified (PO-2) | **Blocks S4 and template work** |
| B3 | 12-section status unresolved (PO-3) | Blocks template/presentation decisions |
| B4 | Narrative boundary unresolved (PO-5) | **Blocks S4** |
| B5 | CSRD/ESRS phased dates unverified (PO-13) | Blocks EU scope definition |
| B6 | IFRS S2 adoption unverified (PO-12) | Blocks IFRS S2 in/out decision |
| B7 | GRI 305 not established | Blocks GRI inclusion |
| B8 | Legacy compliance-claim route needs a PO disposition (PO-9) | **Compliance-claim risk; requires separate authorisation to change** |
| B9 | Structural concepts (boundary/consolidation, per-gas, base year, comparatives, intensity ratio) require **schema change** to implement | Not authorized here |

## 9. Recommended Next Action

1. PO ratifies **PO-1, PO-2, PO-3, PO-4, PO-5, PO-6, PO-7**.
2. Obtain legal/regulatory confirmation for **PO-12** and **PO-13**.
3. Obtain **GRI 305** authoritative content **only if** GRI is to be considered.
4. Authorize a **separate bounded task** for **PO-9** (legacy compliance claims).
5. Then author a bounded implementation contract for the **disclosure model**
   (framework/version/requirement/tier/mapping/purpose/template/narrative-binding)
   plus the **structural** concepts in §16 — no general framework engine.
6. Then re-scope **S4** against the ratified model. **Do not implement S4 now.**

## 10. RLS Boundary

* **No RLS change was made.** No policy, grant, `SECURITY DEFINER` function,
  authorization rule or RLS setting was touched.
* No RLS remediation was begun (no RLS-4A-1, no RLS-4A-2, no RLS-5/3/2/1).
* Security/scope implications recorded only as **requirements the reporting
  architecture must respect**: tenant isolation, entity scope, role/capability
  authorization, **version-bound access**, evidence access controls, and the
  customer/consultant/staff/auditor boundaries.
* Noted dependency: `report_versions` is RLS-enabled with **0 policies**
  (service-only) in the repository migration set — consistent with the separate
  RLS hold register. **Not remediated here.**

## 11. Files Created

| Path | Status |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_REPORTING_COMPLIANCE_AND_DISCLOSURE_ARCHITECTURE_DISCOVERY_20260912.md` | **CREATED** — 26 required sections + Appendices A–C |
| `docs/cline/reports/CT-P8-REPORTING-COMPLIANCE-ARCHITECTURE-DISCOVERY-20260912-001.md` | **CREATED** — this report |

## 12. Files Modified

**NONE.** No existing file was modified, renamed, moved or deleted.

## 13. Files Intentionally Untouched

Deliberately **not** modified, despite findings:

* `backend/report_generator.py` — legacy compliance claims (PO-9; fixing is out of scope)
* `backend/routes/reports.py`, `backend/main.py` — live legacy mounting (PO-9)
* `backend/utils/email.py` — compliance-report product claim (PO-9)
* `backend/engines/report_generation.py` — 12-section engine (PO-2/PO-3)
* `backend/api/v3_reports.py` — report endpoints / lifecycle (S3 intact)
* `backend/utils/emissions.py`, `backend/routes/upload.py` — empty mapping consumer
* `supabase/migrations/**` — no migration created or modified
* `activity_categories` and all other tables — no schema or data change
* `frontend/src/v3/reports/**` — no frontend change
* All pre-existing modified/untracked work in the worktree

## 14. Confirmation — No Implementation / Schema / RLS / Production Changes

Confirmed **NO** changes to: source code; database schema; migrations (none
created or applied); APIs; frontend; report lifecycle; RLS; authorization;
narrative overlay; PDF freezing; AI; billing; deployment; production
configuration; production data.

Database interaction was **strictly read-only**
(`SET default_transaction_read_only=on`; `information_schema` and `COUNT` queries
only). No production system was accessed. No commit. No push. No reset, clean or
stash. No temporary files left in the repository.

## 15. Git / Worktree Status

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD (start) | `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| HEAD (end) | `19e4f01c176eee5870f3c15038b6e7c68b23281c` — **unchanged** |
| Modified (tracked) | **208** — unchanged |
| Untracked | **57 → 58** entries in `git status --short`. **Two files were created**, but only one new entry appears: the new architecture document adds an entry, while this report lands inside the already-untracked `docs/cline/` directory, which `git status --short` reports as a single collapsed directory entry |
| Staged | **0** |
| Commits / pushes | **0 / none** |
| Unrelated work | **Preserved exactly** |

## 16. Tests / Checks Performed, and Pre-existing Failures

* **Run:** `backend/.venv/bin/python -m pytest tests/unit/api/test_v3_reports.py tests/unit/api/test_v3_report_lifecycle.py tests/unit/api/test_reporting.py -q`
* **Result:** **118 passed, 0 failed** → confirms **S1 (`is_current` fix) and S3
  (version lifecycle) remain intact**.
* **Pre-existing failures:** **none encountered** in the suites run.
* No test was altered to make anything pass. The worktree was not modified to
  influence any test.
* Not run: full backend suite, frontend suite, e2e acceptance (not required for
  this discovery; recorded here for transparency).

## 17. Ambiguities / Evidence Gaps

| # | Gap | Impact |
|---|---|---|
| AG-1 | **GRI 305 not established** from authoritative source | GRI must not drive requirements; PO decision needed |
| AG-2 | **CSRD/ESRS phased application dates unverified** | EU scope date-boundary uncertain |
| AG-3 | **IFRS S2 jurisdiction adoption unverified** | IFRS S2 in/out undetermined |
| AG-4 | `legislation.gov.uk` returned HTTP 202/empty for SI 2018/1155 | The SI text was not machine-verified; the **gov.uk guidance PDF** was used as the authoritative substitute |
| AG-5 | Documentation vs implementation conflict on legacy mounting (§5.4) | Requires PO interpretation (PO-9) |
| AG-6 | `activity_categories` mapping rows = 0 **locally**; production row count **not verified** | Mapping capability treated as latent, not real |
| AG-7 | Competitor capability survey is **category-level** only, deliberately not verified feature claims | Used for product awareness only |
| AG-8 | No authoritative **narrative length limits** found | Limits must be technical bounds set post-ratification, not compliance-derived |

## 18. Final Verdict

**DISCOVERY COMPLETE — PO DECISIONS REQUIRED BEFORE ARCHITECTURE RATIFICATION**

The architectural direction is evidenced and recommended
(`DATA → DISCLOSURE MODEL → PRESENTATION`; the 12-section structure reclassified
as a presentation template), but ratification is blocked on PO decisions PO-1 to
PO-8 (plus PO-9 to PO-13 surfaced by evidence) and on the unresolved applicability
gaps AG-1 to AG-3. **S4 cannot proceed on its current basis.** No implementation
is authorized or performed.
