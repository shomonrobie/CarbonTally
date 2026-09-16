# CT-P8-REPORTING-REGULATORY-REQUIREMENT-VERIFICATION-20260912-001

**Task reference:** `CT-P8-REPORTING-REGULATORY-REQUIREMENT-VERIFICATION-20260912-001`
**Date:** 2026-09-12
**Type:** DISCOVERY / regulatory-source verification — **no implementation**
**Governing decision record:** `CARBONTALLY_PHASE8_REPORTING_ARCHITECTURE_PO_RATIFICATION_D1-D17_20260912.md`
**Final verdict:** `DISCOVERY BLOCKED — ADDITIONAL AUTHORITATIVE EVIDENCE REQUIRED`

---

## 1. Objective

Produce an authoritative, requirement-by-requirement regulatory verification matrix for
CarbonTally's initial reporting architecture (GHG Protocol / UK SECR / ESRS E1 + Ireland/EU
applicability) so the Disclosure Model can subsequently be designed — using **primary/authoritative
sources** per D17, and **without implementation**.

## 2. Exact scope

**In scope:** authoritative verification; requirement matrix; cross-framework mapping; CarbonTally
capability mapping; 12-section assessment; narrative analysis; structural gap analysis; versioning
analysis; legacy compliance-claim findings; security/RLS implications (assessment only).

**Explicitly excluded / not performed:** application code; report generation; calculation engines;
database schema; migrations; API routes; frontend; S4; narrative implementation; RLS/permissions;
production; deleting/disabling the legacy route; changing compliance claims; XBRL/iXBRL; rules
engine; templates; disclosure tables; commit; push; reset; stash; unrelated fixes.

## 3. Sources consulted (authoritative)

| # | Source | What was obtained | Access status |
|---|---|---|---|
| S1 | GHG Protocol — Corporate Standard & Standards & Guidance (`ghgprotocol.org`) | Title, 2004 edition, seven Kyoto gases, Scope 2 Guidance 2015, Scope 3 Standard, Feb-2013 gases/GWP amendment, Base Year Adjustments appendix | **Read** |
| S2 | `ghg-protocol-revised.pdf` (3.68 MB) | — | **Not text-extractable** (binary via tooling) |
| S3 | gov.uk — *Environmental reporting guidelines: including SECR* (**PB13944**) | Title, publishers, published 12 Jun 2013 / updated 29 Mar 2019, scope + entities + methodology note | **Read (page)**; PDF body not read |
| S4 | `legislation.gov.uk/uksi/2018/1155/*` | — | **Blocked** (JS anti-bot wall) |
| S5 | EC — *Implementing and delegated acts — CSRD* | (EU) 2023/2772 (31 Jul 2023; OJ 22 Dec 2023); (EU) 2025/1416 (11 Jul 2025; OJ 10 Nov 2025); **3 Jul 2026 Revised-ESRS delegated act (not in force)**; 3 Jul 2026 voluntary standard | **Read** |
| S6/S7 | as above | revision/simplification references + not-in-force status | **Read** |
| S8 | EUR-Lex — Directive (EU) 2022/2464 (CSRD) | OJ **L 322, 16.12.2022, pp. 15–80**; consolidated versions **17/04/2025**, **18/03/2026** | **Read** |
| S9 | EUR-Lex — Directive (EU) 2025/794 | **14 April 2025**; amends (EU) 2022/2464 + 2024/1760 re application dates ("stop-the-clock") | **Read** |
| S10 | EUR-Lex — National transposition for 32022L2464 | Transposition deadline **06/07/2024**; several Member-State measures (Malta, Austria, Poland) | **Partial** — Ireland not captured |
| S11 | EFRAG — Sustainability reporting / ESRS workstreams / **ESRS Knowledge Hub** | 12 draft ESRS (22 Nov 2022); EC adoption 31 Jul 2023; OJ Dec 2023; **2026 Revised ESRS adopted 3 Jul 2026, effective only after OJ**; Simplified ESRS advice 30 Nov 2025; ESRS-40a ED | **Read** |
| S12 | Annex I, ESRS E1, (EU) 2023/2772 | — | **Not extractable** (>5 MB / interactive app) |

## 4. Repository files inspected

`backend/engines/report_generation.py` (12-section `_DEFAULT_SECTIONS`, section builders, SEAI CO2-only
note) · `backend/report_generator.py` (legacy `EnhancedSustainabilityReportPDF`, compliance claims at
:328/:499) · `backend/routes/reports.py` (`POST /generate-enhanced-report` at :1287, auth + type map)
· `backend/main.py` (router mounting) · `backend/data/reports.py` (`_REPORT_FULL_COLUMNS`,
`_row_to_report_full`, `get_full`) · `backend/data/report_versions.py`, `backend/domain/report_lifecycle.py`
(S1/S3) · `supabase/migrations/00000000000000_init_schema.sql` (`report_versions`, `report_templates`,
`emissions_logs`, `organization_metadata`, `facilities`, `assets`, `emission_factors`) · D1–D17
ratification, lifecycle spec, product/report ratification, open-decision closure, Ask CarbonTally
discovery, Insight D2 ratification, S4 blocked report.

## 5. Findings

1. **[V] ESRS is mid-version-change (the single most important finding).** The **legally applicable**
   ESRS text is **Delegated Regulation (EU) 2023/2772** (OJ 22 Dec 2023) **as amended by (EU)
   2025/1416**; a **Revised ("simplified") ESRS was adopted on 3 July 2026 and is NOT in force**
   (pending OJ publication + scrutiny), with EFRAG's **Simplified ESRS advice of 30 Nov 2025** as the
   bridge. CarbonTally must **bind to 2023 ESRS numbering now** and model the transition (D14/D15).
2. **[V] UK SECR applicability** verified from official guidance (PB13944): from **1 April 2019** all
   UK quoted companies report **global energy use** *and* GHG emissions; **large unquoted companies**
   and **large LLPs** disclose annual energy use, GHG emissions and related information; location-based
   encouraged where not dual-reporting.
3. **[R] No framework/requirement/disclosure/template-version model exists**; `report_templates` is a
   template container without a version dimension; `organization_metadata` holds several useful
   metrics (size, floor area, renewable %, contact) that partly support SECR intensity denominators.
4. **[R] The legacy compliance route is live and claims compliance** ("Compliant with SECR/CSRD/ISSB";
   "complies with {report_type} requirements"), routes **CSRD/ISSB to the SECR generator**, and (visible
   code) **lacks an org-scope check** → recorded for D16.
5. **[U] Material evidence gaps remain** (see §8) → verdict is BLOCKED.

## 6. Requirements verified / produced

| Output | Location | Confidence |
|---|---|---|
| Framework inventory (bindable versions) | Report A §9.0 | **[V]** |
| GHG requirement matrix (19 rows) | Report A §9.2 | Concept-level; identifiers/lists **[U]** |
| SECR requirement matrix (15 rows) | Report A §9.3 | Scope **[V]**; contents/thresholds **[U]** |
| ESRS E1 requirement matrix (15 concept rows) | Report A §9.4 | **Concept-level only; identifiers [U]** |
| Cross-framework mapping | Report A §10 | **[I]** |
| Capability mapping (27 concepts) | Report A §11 | **[R]** |
| 12-section assessment | Report A §12 | **[R]/[I]** |
| Narrative classification (SYS/CUST/MIX/OPT) | Report A §13 | **[I]** |
| Structural gap analysis (16 concepts) | Report A §14 | **[I]/[REC]** |
| Versioning analysis | Report A §15 | **[I]** |

## 7. Discrepancies found (recorded, not reconciled silently)

| # | Discrepancy | Resolution |
|---|---|---|
| 1 | **[V] Documentation vs reality:** the S3-era reporting docs describe the legacy route as legacy/unmounted; the repository shows `POST /api/reports/generate-enhanced-report` **mounted and live** via `routes/reports.py` | Recorded; **D16** disposition required |
| 2 | **[R] The 12-section report was previously described as "the report"**; D3 now classifies it as a **presentation template**, and §12 shows 6 of 12 sections are technical evidence | Consistent with D3; recorded |
| 3 | **[V] Earlier CarbonTally lifecycle/ratification docs treat ESRS as if a single numbering applies**; a **2023 vs 2026** split now exists | Recorded; `E1-VER` PO decision raised (§19) |
| 4 | **[R] The legacy route's stated support list** ("SECR, CSRD, ISSB") **exceeds** the ratified D1 scope (GHG/SECR/ESRS E1; ISSB explicitly deferred) | Recorded for D16 |

## 8. Limitations

* **[U] GHG Protocol Chapter 9** required/optional lists **not read** (PDF not text-extractable) → the
  required/conditional/optional classification of D9's content is unverified.
* **[U] ESRS E1 exact disclosure identifiers/titles not extracted** (EUR-Lex annex >5 MB; EFRAG
  Knowledge Hub is interactive) → E1 rows are concept-level and must be re-keyed.
* **[U] UK SI 2018/1155** not read (legislation.gov.uk JS wall) → SECR content list and "large"
  thresholds unverified.
* **[U] Ireland's CSRD transposition measure not captured**; **[U]** CSRD phase-in dates not
  verbatim-verified; **[U]** the CSRD amending instrument behind the 18/03/2026 consolidation not
  identified.
* **[U]** The Apr-2013/Feb-2013 GWP set ("Required gases and GWP values") not read.
* **[I]** All interpretation/recommendation markers are flagged as such in Report A.

## 9. Tests / checks performed

**No automated test suite was run** — this task changed **no code, schema or configuration**, so no
test outcome could be affected. The checks actually performed were evidence checks:

* repository inspection (report engine sections; legacy generator/route; schema of `report_versions`,
  `report_templates`, `emissions_logs`, `organization_metadata`, `emission_factors`; S1/S3 modules);
* route-mounting verification (`main.py` → `routes/reports.py`);
* **20 authoritative web retrievals** (see §3) across `ghgprotocol.org`, `gov.uk`,
  `legislation.gov.uk` (blocked), `eur-lex.europa.eu`, `finance.ec.europa.eu`, `efrag.org`,
  `knowledgehub.efrag.org`;
* evidence typing of every matrix row (**[V]/[R]/[I]/[REC]/[U]**).

## 10. Files created / changed

| File | Action |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md` | **Created** (Report A — 22 sections) |
| `docs/cline/reports/CT-P8-REPORTING-REGULATORY-REQUIREMENT-VERIFICATION-20260912-001.md` | **Created** (Report B — this file) |
| **All other files** | **Unchanged** |

## 11. Database status

**No database change.** No migration created or applied; no table/column/constraint/index altered; no
data written; **no database connection was opened by this task**. (The ESRS/SECR facts were obtained
from official publications, not from any database.)

## 12. Security status

**No security change.** No RLS enabled/disabled/modified; no policy or grant created/revoked; no
`SECURITY DEFINER` function touched; no production change; the separate production RLS security hold is
untouched. Assessment-only observations (new scope dimensions; the legacy route's org-scope gap) are
recorded in Report A §§16–17 for their respective bounded tasks.

## 13. Deviations

**None.** All prohibited activities were avoided; nothing was committed, pushed, reset or stashed.

## 14. Unresolved questions

1. ESRS E1 **exact disclosure identifiers/titles** and their required/conditional status.
2. GHG Protocol **Chapter 9** required/optional lists; the **GWP set** (Feb-2013 amendment).
3. UK SECR **statutory content list**, **transport-energy** scope and **"large" thresholds**.
4. **Ireland's** CSRD transposition measure; the CSRD **phase-in dates**; the amending instrument
   evidenced by the **18/03/2026** consolidation.
5. Whether the **2026 Revised ESRS** will be effective for FY2026/FY2027 reporting and how
   (binding decision needed for `E1-VER`).

## 15. PO decisions required

A1 · A3 · P3 (narrative allowlist/limits/editable set) · **D11-CAT** (SECR denominator catalogue) ·
**E1-COV** (initial E1 coverage) · **E1-VER** (ESRS version strategy) · **APPL** (applicability capture)
· **GP-CONS** (consolidation approach) · **GP-GAS** (CO2e-only vs per-gas) · **GP-S2M** (market-based
Scope 2) · **GP-S3** (Scope 3/value chain) · **GP-BY** (base year/recalculation) · **LEG** (D16 legacy
disposition). Detail in Report A §19.

## 16. Final verdict

### `DISCOVERY BLOCKED — ADDITIONAL AUTHORITATIVE EVIDENCE REQUIRED`

Gate 1 is **not closed** and the requirement matrix is **not evidentially complete**: ESRS E1
identifiers, GHG Protocol Chapter 9 content, the UK SECR statutory content/thresholds and Ireland's
transposition remain unverified from primary sources. The architecture is coherent and the repository
can host the Disclosure Model, but **no implementation readiness is claimed**.

## 17. Git / worktree / commit / push status

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` (**unchanged**) |
| Modified files | **208** (pre-existing set — unchanged) |
| Untracked | **60** entries (task-start 59 → **+1** = Report A; Report B sits inside the already-untracked `docs/cline/reports/`) |
| Staged | **0** |
| Commit created | **NO** |
| Push | **NO** (`main` ahead 14 of `origin/main`) |
| Pre-existing work overwritten/deleted | **NONE** |
| Unrelated files modified | **NONE** (only the two reports above) |


