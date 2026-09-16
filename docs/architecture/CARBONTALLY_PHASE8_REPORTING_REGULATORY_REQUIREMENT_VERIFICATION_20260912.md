# CarbonTally — Phase 8 Reporting: Regulatory Requirement Verification

**Document:** `CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md`
**Task reference:** `CT-P8-REPORTING-REGULATORY-REQUIREMENT-VERIFICATION-20260912-001`
**Status:** DISCOVERY OUTPUT (evidence gate following D1–D17 ratification)
**Date:** 2026-09-12
**Type:** Discovery / regulatory-source verification. **No implementation.**

---

## 1. Document control

| Item | Value |
|---|---|
| Governing decision record | `CARBONTALLY_PHASE8_REPORTING_ARCHITECTURE_PO_RATIFICATION_D1-D17_20260912.md` (PO-RATIFIED) |
| Source-governance rule applied | D17 (authoritative-source-first; Tier 1 > Tier 2 > Tier 3) |
| Repository baseline | branch `main`, HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| Evidence types | **[V]** verified from an authoritative source · **[R]** CarbonTally repository fact · **[I]** interpretation · **[REC]** recommendation · **[U]** unresolved |
| Final verdict | **`EVIDENCE CLOSURE PARTIAL — PO REVIEW REQUIRED`** (§24.11 — current). Earlier verdicts retained: §22 `DISCOVERY BLOCKED — ADDITIONAL AUTHORITATIVE EVIDENCE REQUIRED`; §23.7 `EVIDENCE CLOSURE PARTIAL — PO REVIEW REQUIRED` |

## 2. Executive summary

1. **[V]** The three D1 frameworks exist and their **current authoritative/legal versions were identified** (§5–§8). The most important discovery: **ESRS E1 is mid-version-change** — the legally applicable text is **Delegated Regulation (EU) 2023/2772** (as amended by **(EU) 2025/1416**), while a **Revised ("simplified") ESRS was adopted by the Commission on 3 July 2026 and is NOT yet legally effective** (pending OJ publication + scrutiny). CarbonTally must bind to the 2023 ESRS numbering now and model the revision as a first-class framework-version change (D14/D15).
2. **[V]** UK SECR applicability and the content basis of the energy-and-carbon report were verified from official UK government guidance (PB13944, last updated 29 March 2019).
3. **[U]** The **verbatim requirement identifiers/lists** for two of the three frameworks could **not** be extracted from a primary source in this session: ESRS E1's disclosure identifiers (Annex I to (EU) 2023/2772) and the GHG Protocol Corporate Standard **Chapter 9** required/optional lists. This is the primary reason for the BLOCKED verdict.
4. **[R]** CarbonTally has **no framework/requirement/disclosure/template-version model**; the 12-section report is a presentation artefact (consistent with D3), and several D9/SECR concepts (per-gas, base year, recalculation, intensity-denominator model, energy mix, targets/actions, uncertainty) have **no structured support**.
5. **[R]** The legacy route `POST /api/reports/generate-enhanced-report` **is live**, requires `require_org_member()`, and **emits explicit compliance claims** ("Compliant with SECR/CSRD/ISSB reporting standards"; "This report complies with {report_type} requirements") while mapping `CSRD`/`ISSB` to the same SECR generator → recorded for the separate **D16** disposition task (not modified).
6. **[R]** The disclosure model **can be designed** from the existing foundations, but its **requirement catalogue cannot be finalised** until the missing authoritative evidence (S2/S4/S12) is obtained.

## 3. Scope and exclusions

**In scope:** authoritative verification of GHG Protocol / UK SECR / ESRS E1 (+ EU/Ireland applicability); requirement matrix; cross-framework mapping; capability mapping; 12-section assessment; narrative analysis; structural gap analysis; versioning analysis; legacy-claim findings; security/RLS implications.

**Out of scope (not performed):** any implementation; schema/migration; RLS/grant/policy change; code/route/template/disclosure-table/rules-engine change; disabling the legacy route; S4; AI/Insight; XBRL; competitor claims as authority; legal determination for any customer.

**Evidence discipline:** every matrix row carries an explicit source; rows without a primary source are marked **[U]** and are **not** presented as verified requirements.

## 4. Authoritative source register

| # | Source | Tier | Status |
|---|---|---|---|
| S1 | GHG Protocol — Corporate Standard (`ghgprotocol.org/corporate-standard`; `/standards-guidance`) | 1 | **Partial** — publication facts verified; Chapter 9 text not extractable |
| S2 | GHG Protocol — Corporate Standard full PDF (`ghg-protocol-revised.pdf`, 3.68 MB) | 1 | **Not extractable** (binary PDF via available tooling) |
| S3 | UK gov.uk — *Environmental reporting guidelines: including SECR requirements* (PB13944) | 1/2 | **Verified (metadata + scope)**; PDF body not read |
| S4 | UK SI 2018/1155 (*Companies (Directors' Report) and LLPs (Energy and Carbon Report) Regulations 2018*) | 1 (legislation) | **Blocked** — `legislation.gov.uk` serves a JS "verify you are not a robot" wall |
| S5 | Commission Delegated Regulation **(EU) 2023/2772** (ESRS) | 1 | **Verified** (reference, adoption/OJ dates, status) |
| S6 | Commission Delegated Regulation **(EU) 2025/1416** | 1 | **Verified** (reference, dates) |
| S7 | Commission Delegated Regulation of **3 July 2026** (Revised/Simplified ESRS) | 1 | **Verified** (adopted; **not in force**) |
| S8 | Directive **(EU) 2022/2464** (CSRD) | 1 | **Verified** (OJ L 322, 16.12.2022, pp. 15–80; consolidated versions 17/04/2025, 18/03/2026) |
| S9 | Directive **(EU) 2025/794** ("stop-the-clock") | 1 | **Verified** (14 April 2025; amends 2022/2464 + 2024/1760 re application dates) |
| S10 | EUR-Lex **National transposition** for 32022L2464 | 1 | **Partial** — transposition deadline 06/07/2024 + several Member-State measures seen; **Ireland not captured** |
| S11 | EFRAG (official ESRS technical adviser) — Sustainability reporting / ESRS workstreams / ESRS Knowledge Hub | 1/2 | **Verified** (process, adoption dates, version status) |
| S12 | ESRS E1 detailed text (Annex I to (EU) 2023/2772) | 1 | **Not extractable in-session** (>5 MB / interactive app) |

**[U] Access limitation to record:** EUR-Lex serves the ESRS annex as a single `>5 MB` document and the EFRAG Knowledge Hub is an interactive application; `legislation.gov.uk` blocks non-JS clients. These are **tooling limits, not source-availability limits** — all sources exist and are obtainable by direct reading.

## 5. GHG Protocol findings

### 5.1 Verified facts [V]

| Item | Finding | Source |
|---|---|---|
| Publication | **"The GHG Protocol Corporate Accounting and Reporting Standard"** (the *Corporate Standard*); published by WRI & WBCSD; site offers *"Corporate Standard Revised (English)"* (3.51 MB) | S1 |
| Edition | **2004 revised edition** (the site's partner/contributor list is titled "Corporate Standard (**2004 edition**)") | S1 |
| Gases | Covers the **seven Kyoto Protocol gases**: CO2, CH4, N2O, HFCs, PFCs, SF6, NF3 | S1 |
| Scope 2 | Updated in **2015** with the **Scope 2 Guidance** (purchased/acquired electricity, steam, heat and cooling) | S1 |
| Companions | **Corporate Value Chain (Scope 3) Standard**; **Scope 3 Calculation Guidance**; Land Sector & Removals Standard/Guidance | S1 |
| Supporting amendments | **"Amendments and Corrections — Required gases and GWP values" (February 2013)**; **"Appendices — Base Year Adjustments" (March 2004)**; "Categorizing GHG Emissions from Leased Assets" (March 2004) | S1 |
| Standards family | Corporate Standard; Scope 2 Guidance; Scope 3 Standard; Scope 3 Calculation Guidance; (in development) **Actions and Market Instruments (AMI) Standard** proposing a **multi-statement reporting structure** | S1 |
| Boundary of the standard | It provides **requirements and guidance** for preparing a corporate GHG inventory and is "designed to develop a verifiable inventory", but it **does not** standardise how verification is conducted | S1 |

### 5.2 Unresolved [U]

* **Chapter 9 ("Reporting GHG Emissions") — the standard's required/optional information lists — could not be extracted** (S2 not text-extractable; no HTML mirror found). Consequently the **required vs conditional vs optional classification** of the D9 content list (and of additional items such as uncertainty/inventory quality, comparative information, contact information) is **not independently verified** in this session.
* The **"Required gases and GWP values" amendment (Feb 2013)** was identified but not read → the exact **GWP set/treatment** is unverified.

### 5.3 Interpretation [I] and recommendation [REC]

* **[I]** The D9 list of 21 items is **conceptually consistent** with the Corporate Standard's reporting chapter (organizational boundary; consolidation approach; entities/facilities; operational boundary; activities/scopes; reporting period; Scope 1 & 2; by-scope; gases/CO2e; base year; recalculation; biologically sequestered CO2; methodologies; exclusions; changes & causes; comparatives; inventory quality/uncertainty; sequestration; coverage; contact).
* **[REC]** Gate 1 for GHG is **not closed**: obtain the Corporate Standard (2004 revised) **Chapter 9** text and the Feb-2013 gases/GWP amendment, then classify every D9 item as **required / conditional / optional** per D12 before the requirement catalogue is frozen.

## 6. UK SECR findings

### 6.1 Verified facts [V] — source S3

| Item | Finding |
|---|---|
| Guidance | **"Environmental reporting guidelines: including Streamlined Energy and Carbon Reporting requirements"** (Ref **PB13944**; PDF 1.47 MB; 152 pages) |
| Publishers | Department for Energy Security and Net Zero (DESNZ), DEFRA, and (at publication) BEIS |
| Published / updated | Published **12 June 2013**; **last updated 29 March 2019**; the guidance "includes changes which take effect **from 1 April 2019**" |
| Core requirement | From **1 April 2019** **all UK quoted companies** must report their **global energy use** *in addition to* **GHG emissions** in the annual **Directors' Report** |
| Extended scope | Requirements also exist for **large unquoted companies** and **large LLPs** to disclose their **annual energy use and GHG emissions** and related information |
| Entities affected | (a) all UK-incorporated companies listed on the **London Stock Exchange main market**, an **EEA market**, or dealing on **NYSE or NASDAQ**; (b) **unquoted large companies** incorporated in the UK required to prepare a **Directors' Report under Part 15 of the Companies Act 2006**; (c) **large LLPs** ("large" per the existing framework for annual accounts and reports, based on **sections 465 and 466 of the Companies Act**) |
| Voluntary extension | Government "encourages all other companies to report similarly, although this remains **voluntary**" |
| Methodology | Where organisations do not dual-report, government "encourage[s] use of the **location-based reporting method**"; **dual reporting remains preferred but is not mandatory** |

### 6.2 Unresolved [U]

* **Exact statutory content list** of the energy-and-carbon report (energy use in **kWh**; relevant **energy sources**; **transport energy** for large unquoted companies/LLPs; **Scope 1** and **Scope 2** emissions; at least one **intensity ratio** and its **denominator rules**; **prior-year** figures; **methodology**; **energy-efficiency actions** narrative) — these come from the **SI 2018/1155 / guidance PDF body**, which **could not be fetched** (S4 JS wall; S3 PDF body not read).
* **Exact "large" qualification thresholds** (turnover / balance-sheet total / employees) — referenced to CA 2006 **ss. 465–466** but **not read verbatim** in-session.
* **[I]** The commonly cited instrument for the 1 April 2019 changes is the **Companies (Directors' Report) and Limited Liability Partnerships (Energy and Carbon Report) Regulations 2018 (SI 2018/1155)**; this is **consistent** with the guidance changelog but is **not verbatim-verified** here.
* **[REC]** Gate 1 for SECR is **not closed**: read **PB13944 (29 March 2019)** and **SI 2018/1155** (required contents + qualification conditions) before freezing the SECR requirement set and the **D11 intensity-denominator catalogue**.

## 7. ESRS E1 findings

### 7.1 Authoritative version resolution — the key finding [V] (sources S5–S7, S11)

```text
2022-11-22  EFRAG delivered 12 draft ESRS to the European Commission
2023-07-31  Commission adopted Delegated Act = ESRS Set 1
2023-12-22  Published in OJ  ->  Commission Delegated Regulation (EU) 2023/2772
2025-07-11  Commission Delegated Regulation (EU) 2025/1416 adopted
2025-11-10  (EU) 2025/1416 published in OJ
            -> amends 2023/2772 (postponement of the date of application of
               disclosure requirements for certain undertakings)
2025-11-30  EFRAG "Simplified ESRS" Technical Advice delivered to the EC
2026-07-03  Commission adopted a Delegated Regulation SIMPLIFYING certain ESRS
            ("Revised ESRS") + a voluntary standard for undertakings protected
            by the value chain cap
            -> NOT IN FORCE (awaiting OJ publication + scrutiny completion)
```

| Item | Finding |
|---|---|
| **Currently legally applicable ESRS text** | **Commission Delegated Regulation (EU) 2023/2772 of 31 July 2023, OJ 22 December 2023** (ESRS Set 1), **as amended by (EU) 2025/1416** |
| Legal basis | Directive 2013/34/EU as amended by **Directive (EU) 2022/2464 (CSRD)** |
| Set 1 structure | 12 sector-agnostic ESRS (2 cross-cutting — ESRS 1, ESRS 2; 5 environmental incl. **E1 Climate change**; 4 social; 1 governance) — **[I]** structure; EFRAG confirms "**twelve draft standards**" |
| **Revised ("simplified") ESRS** | Adopted as a Commission delegated act on **3 July 2026**; EFRAG published the adopted text on its Knowledge Hub; it **"will become legally effective only after its publication in the Official Journal … following the completion of the scrutiny period later this year"** |
| Transition mechanics | The EFRAG Knowledge Hub maps each Revised-ESRS paragraph back to the **2023 ESRS** paragraph; EFRAG's **Simplified ESRS Technical Advice (30 Nov 2025)** is the bridge document |
| Also adopted 3 July 2026 | A delegated regulation establishing **sustainability reporting standards for voluntary use by undertakings protected by the value chain cap** (not in force) |
| Sector-specific ESRS | In development (multi-year); **out of initial scope** |
| Other official activity | LSME standard; voluntary standard for non-CSRD SMEs; ESRS digital (XBRL) taxonomy; implementation guidance; Q&A platform; **ESRS-40a** exposure draft for certain non-EU undertakings (comments by 31 Oct 2026) |

### 7.2 Unresolved [U]

* **The exact ESRS E1 disclosure requirement identifiers and titles** (the `E1-*` series plus the ESRS 2 cross-cutting disclosures it relies on) **could not be extracted** from a primary source in-session (S12: EUR-Lex annex `>5 MB`; EFRAG Knowledge Hub is an interactive app). The E1 rows in §9 are therefore **concept-level only** and their **identifiers/titles are unverified**.
* **Which E1 datapoints require external/customer input vs CarbonTally calculation** cannot be enumerated until the E1 text is read.
* The **Revised ESRS renumbering** (and therefore the future framework-version binding under D14/D15) is unverified.

### 7.3 Interpretation [I] and recommendation [REC]

* **[I]** D7-R's Layer 1/2/3 split is **consistent** with the *categories* of ESRS E1 coverage, but the mapping from D7-R layers to actual `E1-*` requirements is **not yet authoritatively established**.
* **[REC]** Bind CarbonTally to the **2023 ESRS (2023/2772 as amended by 2025/1416)** numbering **now**; register the **2026 Revised ESRS** as the next framework version (D14); read **Annex I (E1)** before freezing E1 coverage.

## 8. Ireland / EU applicability findings

### 8.1 EU level [V] (sources S8–S10)

| Item | Finding |
|---|---|
| CSRD | **Directive (EU) 2022/2464 of 14 December 2022**; **OJ L 322, 16.12.2022, pp. 15–80**; CELEX 32022L2464; consolidated versions dated **16/12/2022, 17/04/2025, 18/03/2026** |
| "Stop-the-clock" | **Directive (EU) 2025/794 of 14 April 2025** amending Directives (EU) 2022/2464 and (EU) 2024/1760 **as regards the dates from which Member States are to apply certain corporate sustainability reporting and due diligence requirements**; in force the day after OJ publication |
| Transposition deadline | **06/07/2024** (EUR-Lex national-transposition record for 32022L2464) |
| National measures (examples seen) | Malta — *Corporate Sustainability Reporting Regulations, 2026* (gazette 2026-02-13) and *Various Laws relating to CSR (Amendment) Act, 2026*; **Austria — Nachhaltigkeitsberichtsgesetz (NaBeG), BGBl. I Nr. 6/2026** (2026-02-18); Poland (4 measures) |
| Further CSRD amendment | A consolidated CSRD version dated **18/03/2026** exists ⇒ a further amending act beyond Directive (EU) 2025/794 applies; **the amending instrument was not identified in-session** [U] |

### 8.2 Ireland — unresolved [U]

* **Ireland's CSRD transposition measure was not captured** — the EUR-Lex national-transposition page truncated before the Irish entry.
* **[U]** Obtain: EUR-Lex *National transposition* for CELEX 32022L2464 (**Ireland** section); the Irish implementing instrument (candidate official sources: **Irish Statute Book**, **Department of Enterprise, Tourism and Employment**, **IAASA / CRO** as competent authority).
* **[I]** Because the CSRD is an **EU Directive**, its effect in Ireland is via a **national transposition measure**; CarbonTally must treat Irish applicability as **customer-specific** (D13) and must **not** make a legal determination.

### 8.3 The three levels CarbonTally must keep distinct [REC]

| Level | Meaning | CarbonTally responsibility |
|---|---|---|
| 1 — EU requirement | CSRD/ESRS as adopted at EU level (S5–S9) | Model framework + version + requirement set |
| 2 — National implementation | Member-State transposition/application (Irish SI; Austrian NaBeG; Maltese regulations) | Record jurisdiction context; never assert legal status |
| 3 — Customer applicability | Whether **this** customer must report (size/listing/consolidation/timing) | Capture or request confirmation; **no legal determination** (D13) |

**[U]** The **CSRD phase-in dates** (Art. 5(2) CSRD, as amended) were **not verbatim-verified** in-session and must be confirmed from the consolidated CSRD text before being encoded.

## 9. Detailed requirement matrix

### 9.0 Framework inventory (verified versions)

| Framework | Authoritative version to bind | Source |
|---|---|---|
| GHG Protocol | **Corporate Accounting and Reporting Standard, 2004 revised edition** (+ Scope 2 Guidance 2015; Scope 3 Standard; Feb-2013 gases/GWP amendment) | S1 |
| UK SECR | **SECR regime in force from 1 April 2019** (guidance **PB13944**, last updated **29 Mar 2019**; instrument **SI 2018/1155**) | S3 (S4 unread) |
| ESRS E1 | **ESRS Set 1 = Delegated Regulation (EU) 2023/2772** (OJ 22 Dec 2023) **as amended by (EU) 2025/1416**; **2026 Revised ESRS adopted 3 Jul 2026, not yet in force** | S5–S7, S11 |

### 9.1 Abbreviations

**Class:** R required · C conditional · O optional · F future/unsupported
**Purpose:** A Annual Carbon · M Management · S UK SECR · E ESRS E1
**Narrative:** — none · SYS system-derived · CUST customer-authored · MIX mixed · OPT optional commentary
**Capability status:** SUPP supported · PART partial · SI structured-input exists · EI external-input needed · MISS missing · FUT future · N/A not applicable
**Initial decision:** I initial · D deferred · F future · X excluded
**Source:** GP = GHG Protocol Corporate Standard (2004 rev.) · **GP-C9p** = its Chapter 9 *(not read → [U])* · UK-G = PB13944 · **UK-SI** = SI 2018/1155 *(not read → [U])* · **E1p** = Annex I, ESRS E1, (EU) 2023/2772 *(not read → [U])* · REG = (EU) 2023/2772 · CSRD = (EU) 2022/2464

> **Evidence caveat (applies to all three sections):** rows sourced **GP-C9p / UK-SI / E1p** are built from the **concept set named in D9/D10/D7-R** and the frameworks' verified structure; the **exact identifiers, wording and required/conditional status** of those rows remain **[U]** until the primary texts listed in §4 are read.

### 9.2 GHG Protocol — Corporate Standard (2004 revised) [+ Scope 2 Guidance 2015]

| ID | Requirement | Class | Purpose | Structured data | Calculation | Evidence | Narrative | CT capability | Status | Gap | Decision | Ver. | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GP-ORG | Organizational boundary: entities/facilities included | R | A/M/S/E | org units, facilities, control basis | n/a | boundary definition | CUST | `organizations`, `facilities`, `assets` | PART | No boundary record; no consolidation basis | I | Y | GP / GP-C9p [U] |
| GP-CONS | Consolidation approach (equity share / financial / operational control) | R | A/M/E | chosen approach + application | affects which sources aggregate | boundary rationale | CUST | none | MISS | No consolidation-approach concept | I | Y | GP / GP-C9p [U] |
| GP-OPS | Operational boundary — scopes/activities included | R | A/M/S/E | scope per source, activity types | Scope 1/2/3 classification | factor + source provenance | — | `emissions_logs.scope` (free text) | PART | Scope is unconstrained text; no governed scope-3 categories | I | Y | GP / GP-C9p [U] |
| GP-PERIOD | Reporting period | R | A/M/S/E | period start/end, year | period filter | ledger dates | — | `report_generation_queue.reporting_year`, `content.period` | SUPP | Year-granular only | I | Y | GP / UK-G |
| GP-S1 | Scope 1 emissions | R | A/M/S/E | activity + factor per source | yes (engine) | factor + snapshot | — | `emissions_logs`, `calculation_snapshots`, engine | SUPP | No per-gas split | I | Y | GP / UK-G |
| GP-S2 | Scope 2 emissions (location-based **and** market-based) | R | A/M/S/E | kWh + grid factor (L) / contractual instruments (M) | yes (L); M needs instruments | factor + contract evidence | MIX | engine (one scope-2 basis) | PART | **No dual-report (location vs market) model**; no instruments | I | Y | GP + Scope 2 Guidance 2015 |
| GP-S3 | Scope 3 (Corporate Value Chain Standard) | C | E (initial), M | categories 1–15 | category methods | supplier/estimate provenance | MIX | none in ledger | MISS | No Scope-3 category/value-chain model | D/F | Y | GP Scope 3 Std |
| GP-BY | Base year + base-year emissions | R (where set) | A/M/E | base year + totals | recalculation base | base-year dataset | CUST | none | MISS | No base-year concept | I | Y | GP / Base Year Adjustments (Mar 2004) |
| GP-RECALC | Base-year recalculation policy, triggers, significance threshold | R (where base year) | A/M/E | policy + threshold + recalc log | recalculation | recalculation log | CUST | none | MISS | No recalculation policy/engine | I | Y | GP / Base Year Adjustments (Mar 2004) |
| GP-GAS | Individual GHGs + CO2e (7 Kyoto gases; GWP set) | R (CO2e min.) | A/M/S/E | per-gas masses | GWP conversion | GWP source | — | CO2e only (SEAI CO2-only) | PART | **No per-gas ledger** | I | Y | GP / Required gases & GWP (Feb 2013) |
| GP-EXCL | Exclusions and reasons | R | A/M/S/E | excluded sources + reason | n/a | rationale | CUST | none | MISS | No exclusion model | I | Y | GP / GP-C9p [U] |
| GP-CHG | Significant changes & causes vs prior period | R | A/M/E | change list + cause | variance analysis | supporting data | MIX | engine YoY (partial) | PART | No governed changes/causes model | I | Y | GP / GP-C9p [U] |
| GP-CMP | Historical/comparative information | R | A/M/S/E | prior-year figures | recompute/retain | prior snapshots | — | `report_versions`; ledger history | PART | No framework-bound comparative disclosure | I | Y | GP / UK-G |
| GP-QUAL | Inventory quality / uncertainty | R (qual.) / O (quant.) | A/M/E | quality indicators | uncertainty calc (O) | methodology | CUST/MIX | `issues`, validation | PART | No uncertainty/quality model | I | Y | GP / GP-C9p [U] |
| GP-BIO | Biologically sequestered CO2 (not offsets) | C | A/M/E | sequestration activity | separate accounting | evidence | — | none | MISS | No sequestration/removal concept | D | Y | GP / GP-C9p [U] |
| GP-METH | Methodologies / calculation approach | R | A/M/S/E | method per source | documented | factor sources, algorithm version | SYS | `calculation_snapshots`, `provenance` | SUPP | Needs framework-level methodology statement | I | Y | GP / UK-G |
| GP-COV | Facilities / organizational coverage of the inventory | R | A/M/S/E | coverage list/% | n/a | boundary docs | CUST | `facilities`, `assets` | PART | No coverage statement | I | Y | GP / GP-C9p [U] |
| GP-CONTACT | Responsible / contact information | R | A/M/E | contact | n/a | n/a | CUST | `organization_metadata.primary_contact_name` | SI | Not surfaced in reports | I | Y | GP / GP-C9p [U] |
| GP-OFFSET | Offsets presented separately from the inventory | O | A/M | offset data | n/a | certificates | CUST | `organization_metadata.carbon_offset_percentage` | PART | Presentation only | O/D | Y | GP-C9p [U] |

### 9.3 UK SECR — regime in force from 1 April 2019

| ID | Requirement | Class | Purpose | Structured data | Calculation | Evidence | Narrative | CT capability | Status | Gap | Decision | Ver. | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SECR-APP | Applicability determination (quoted company / large unquoted company / large LLP; qualification conditions) | R | S | listing status, size metrics (turnover, balance sheet, employees), jurisdiction | n/a | filings/confirmations | CUST | none | MISS | No applicability engine or captured reporting context (D13 model needed) | I | Y | **UK-G [V]**; UK-SI [U] |
| SECR-GLOBAL | Global energy use (quoted companies) | R | S | energy by source, worldwide | kWh aggregation | energy invoices/meters | — | `emissions_logs` raw_quantity + unit | PART | No energy-focused reporting model; no invoice/meter evidence binding | I | Y | UK-G [V] |
| SECR-ENERGY | UK energy use in **kWh** (gas, electricity, other) | R | S | kWh per source per site | kWh aggregation | meter/invoice evidence | — | usage quantity + `units` (`kWh`) | PART | Energy is inferred from activity data, not a first-class energy model | I | Y | UK-G [V]; UK-SI [U] |
| SECR-SRC | Relevant UK energy sources breakdown | R | S | source list (gas, electricity, transport fuels, other) | n/a | n/a | — | activity/unit data | PART | No governed energy-source taxonomy | I | Y | UK-G; UK-SI [U] |
| SECR-TRANSPORT | Transport energy (large unquoted companies & LLPs) | C | S | fuel/energy by transport mode | kWh aggregation | fuel records | — | `assets`, activity data | MISS | No transport-energy model | I | Y | UK-G; UK-SI [U] |
| SECR-S1 | Scope 1 emissions (UK) | R | S | activity + factor | yes (engine) | factor + snapshot | — | engine + `calculation_snapshots` | SUPP | No SECR-specific Scope-1 presentation | I | Y | UK-G [V] |
| SECR-S2 | Scope 2 emissions (UK) | R | S | kWh + factor | yes (engine) | factor + snapshot | — | engine | SUPP | Requires **location-based** basis (no dual model) | I | Y | UK-G [V] |
| SECR-CO2E | Report in CO2e | R | S | CO2e | conversion | factor GWP | — | engine (kg CO2e) | SUPP | Unit presentation (tCO2e) to confirm | I | Y | UK-G [V] |
| SECR-PERIOD | Reporting period aligned to the financial year | R | S | FY start/end | period filter | filings | — | `organization_metadata.fiscal_year_start/end`; `reporting_year` | PART | FY dates exist but are not bound to the report | I | Y | UK-G; UK-SI [U] |
| SECR-PRIOR | Prior-year comparative | R | S | prior-year energy + emissions | recompute/retain | prior data | — | ledger history | PART | No framework-bound comparative | I | Y | UK-G [V] |
| SECR-INTENSITY | At least one GHG **intensity ratio** | R | S | numerator + denominator + unit | ratio | denominator evidence | CUST/MIX | `organization_metadata.energy_intensity`, `annual_revenue`, `total_assets`, `total_floor_area_sqft`, `occupied_floor_area_sqft` | SI | No controlled **denominator catalogue / ratio definition** model (D11) | I | Y | UK-G [V]; UK-SI [U] |
| SECR-DENOM | Denominator rules/definitions | R | S | denominator type + value + unit + source | n/a | denominator evidence | CUST | `organization_metadata` metrics (partly) | SI | **D11 catalogue undefined** (PO decision) | I | Y | UK-G; UK-SI [U] |
| SECR-METH | Methodology statement | R | S | method used | documented | factor sources | SYS | `calculation_snapshots.methodology`, provenance | PART | Needs SECR-level statement | I | Y | UK-G [V] |
| SECR-EE | **Energy-efficiency actions** narrative | R | S | actions taken + (indicative) savings | n/a | supporting notes | **CUST** | none | MISS | No SECR narrative field; blocked by S4 (see §13) | I | Y | UK-G; UK-SI [U] |
| SECR-EXEMPT | Exemptions / alternative provisions (e.g. low-energy-use exemption, offshore/overseas operations, aggregation for unquoted subsidiaries) | C | S | exemption basis | n/a | confirmation | CUST | none | MISS | No exemption model | I | Y | UK-SI [U] |

### 9.4 ESRS E1 (Climate change) — ESRS Set 1, (EU) 2023/2772 as amended by (EU) 2025/1416

> **[U] Critical caveat:** the **official `E1-*` identifiers and titles are unverified** (S12). The rows below use **conceptual identifiers** derived from D7-R's Layer 1/2/3 and the ESRS structure; they must be **re-keyed to the authoritative identifiers** once Annex I is read. Layer: **L1** = production-grade carbon/energy; **L2** = structured related-climate support; **L3** = explicit external-input/future boundary (D7-R).

| ID (concept) | Requirement (concept) | Layer | Class | Structured data | Calculation | Evidence | Narrative | CT capability | Status | Gap | Decision | Ver. | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1-GOV | Governance: board/management oversight, responsibilities, expertise, incentive schemes | L2 | R (ESRS 2) | roles, schemes | n/a | governance docs | CUST | none | MISS | No governance disclosure model | D | Y | REG; E1p [U] |
| E1-STRAT | Strategy: business model, value chain, material IROs, transition plan **(incl. transition plan for climate mitigation)** | L2/L3 | R (ESRS 2/E1) | strategy + plan | n/a | board approval, plan doc | CUST/MIX | none | MISS | No strategy/transition-plan model; scenario/resilience is L3 | D | Y | REG; E1p [U] |
| E1-POL | Policies related to climate change mitigation/adaptation | L2 | R | policy text + status | n/a | policy docs | CUST | none | MISS | No policy model | D | Y | REG; E1p [U] |
| E1-ACT | Actions and resources related to climate policy (incl. expected GHG reductions, energy-efficiency & renewable actions) | L2 | R | action list + resources + expected reduction | reduction estimates | plans, procurement | CUST/MIX | none (report narrative only) | MISS | No actions/reduction model; overlaps D7-R Layer 2 | I/D | Y | REG; E1p [U] |
| E1-TGT | GHG reduction targets (base year, scope coverage, milestones, progress) | L2 | R | target model | progress vs base year | target documentation | CUST | none | MISS | No targets model; depends on GP-BY baseline | D | Y | REG; E1p [U] |
| E1-ENERGY | Energy consumption (total, by source) **and energy mix** (fossil/renewable/nuclear shares) | L1 | R | MWh/kWh by source; mix % | consumption + share calc | meter/invoice; contracts | — | activity data + `units`; `organization_metadata.renewable_energy_percentage` | PART | **No energy model or renewable-mix datum model** | D | Y | REG; E1p [U] |
| E1-S123 | **Gross Scope 1, Scope 2 (location- and market-based), Scope 3** and **total GHG emissions** | L1 | R | per-scope totals; scope-3 categories | engine (S1/S2-L); S2-M and S3 missing | factor + snapshots | — | engine (S1, S2 single-basis) | PART | No **market-based Scope 2**, no **Scope 3 categories**, no per-gas | I/D | Y | REG; E1p [U] |
| E1-SIG3 | **Significant Scope 3 categories** identification/disclosure | L1 | R (if significant) | category list + data | category methods | value-chain evidence | CUST | none | MISS | No value-chain/supplier model | D | Y | REG; E1p [U] |
| E1-INTENSITY | GHG **intensity** metrics (e.g. per net revenue) | L1 | R | numerator/denominator/unit | ratio | denominator evidence | MIX | `organization_metadata.annual_revenue`; engine totals | SI | No intensity model (same D11 gap as SECR) | D | Y | REG; E1p [U] |
| E1-REMOVAL | GHG **removals** and **carbon credits** (kept separate) | L1 | R | removals + credits | n/a | certificates | CUST | `carbon_offset_percentage` (partial) | PART | No removal/credit model | D | Y | REG; E1p [U] |
| E1-ICP | **Internal carbon pricing** schemes | L2 | C | scheme details | n/a | policy | CUST | none | MISS | No ICP model | D/F | Y | REG; E1p [U] |
| E1-ANTICIPATED | **Anticipated financial effects** (and physical/transition risks, scenario analysis) | L3 | R (ESRS E1) | scenario/risk/financial data | n/a | modelling | CUST | none | MISS | **Explicitly outside CarbonTally's domain (D7-R Layer 3)** | X/F | Y | REG; E1p [U] |
| E1-METH | Methodologies and inputs for E1 metrics | L1 | R | method per metric | documented | factor provenance | SYS/MIX | `calculation_snapshots`, `provenance` | PART | Needs E1-level methodology statement | D | Y | REG; E1p [U] |
| E1-COMP | Comparative information / definition of reporting period | L1 | R | prior-period data | recompute | prior snapshots | — | `report_versions` history | PART | No framework-bound comparative | D | Y | REG; E1p [U] |
| E1-DMAT | Double-materiality assessment (ESRS 2 IRO-1/IRO-2) | L2/L3 | R (gate) | materiality assessment | n/a | assessment docs | CUST | none | MISS | **Customer / professional-adviser input; outside CarbonTally domain** | X/F | Y | REG; E1p [U] |

## 10. Cross-framework mapping

```text
Scope 1 / Scope 2 emissions
   +--> Annual Carbon Report            (GP-S1, GP-S2)
   +--> Management Report
   +--> UK SECR                         (SECR-S1, SECR-S2)
   +--> ESRS E1                         (E1-S123)

Energy consumption in kWh
   +--> Management
   +--> UK SECR                         (SECR-ENERGY, SECR-GLOBAL)
   +--> ESRS E1                         (E1-ENERGY)

Intensity ratio
   +--> Management
   +--> UK SECR                         (SECR-INTENSITY — at least one)
   +--> ESRS E1                         (E1-INTENSITY, where applicable)

Organizational + operational boundary, methodology, provenance, evidence
   +--> all four purposes              (GP-ORG/OPS/METH, SECR-METH, E1-METH)

Base year, targets, actions
   +--> Management
   +--> ESRS E1                         (E1-TGT, E1-ACT)

Per-gas / market-based Scope 2 / Scope 3
   +--> ESRS E1                         (E1-S123, E1-SIG3)  [GP-S3 conditional]
```

| Class of data | Frameworks | Notes |
|---|---|---|
| **Shared authoritative data** | All four purposes | Scope 1/2 totals, activity data, factors, provenance, period, methodology, evidence, lifecycle |
| **Framework-specific presentation** | Each purpose | Report structure, disclosure ordering, statutory statements |
| **Additional structured data needed** | SECR, ESRS E1 (+ GP) | Energy in kWh by source; energy mix; intensity numerator/denominator; prior-period figures |
| **Not derivable from the existing ledger** | ESRS E1 (L2/L3), SECR narrative | Targets, actions/expected reductions, policies, transition plan, uncertainty, scenario/risk, removals/credits |
| **Requires customer input** | SECR, ESRS E1, GP | Consolidation approach, base year, exclusions, energy-efficiency actions narrative, materiality, governance, targets |

## 11. CarbonTally capability mapping (repository facts [R])

| Concept | Current support | Evidence | Status |
|---|---|---|---|
| Organizational boundary | `organizations`, `organization_metadata`; presentation section `organization` | schema; engine §9 | **PART** |
| Consolidation approach | **none** | no schema field/engine concept | **MISS** |
| Operational boundary | `emissions_logs.scope` (free text); engine `scopes`/`activities` | schema; engine | **PART** |
| Facilities | `facilities`, `assets`, `vehicles` | schema | **SUPP** (not bound to a disclosure) |
| Individual gases | **none** (CO2e only) | engine note: "SEAI factors are CO2-only" | **MISS** |
| CO2e | engine totals (`total_co2e_kg`), `calculation_snapshots.co2e_kg` | engine; schema | **SUPP** |
| Base year | **none** | no schema field | **MISS** |
| Recalculation | **none** | no schema field/engine | **MISS** |
| Historical comparatives | prior-year ledger + `report_versions` history; engine YoY in benchmarking | schema; engine | **PART** |
| Energy in kWh | activity `raw_quantity` + `unit` (FK `units`); no energy-first-class model | schema | **PART** |
| Energy mix | `organization_metadata.renewable_energy_percentage` (single %) | schema | **PART/MISS** |
| Intensity ratios | `organization_metadata.energy_intensity` + size metrics | schema | **SI** (no ratio-definition model, D11) |
| Denominator definitions | size/financial metrics only | `annual_revenue`, `total_assets`, floor areas | **SI** |
| Methodology | `calculation_snapshots.methodology`/`algorithm_version`; provenance section | schema; engine | **SUPP** |
| Exclusions | **none** | — | **MISS** |
| Causes of emissions changes | engine YoY (partial); no governed model | engine | **PART** |
| Inventory quality / uncertainty | `issues` + validation results (data-quality, not inventory-uncertainty) | schema; engine | **PART** |
| Sequestration / biogenic CO2 | **none** | — | **MISS** |
| Evidence / provenance | `calculation_snapshots`, factor provenance, document/evidence links, `audit_trail` | schema; engine | **SUPP** |
| Targets | **none** | — | **MISS** |
| Reduction actions | **none** | — | **MISS** |
| Energy-efficiency actions | **none** | — | **MISS** |
| Transition-plan information | **none** | — | **MISS** |
| Customer-authored narrative | **blocked** — S4 deliberately not implemented (A1/A3 undecided) | `docs/cline/reports/CT-P8-REPORTING-S4-…md` | **MISS** |
| Framework / requirement / disclosure model | **none**; `report_templates` exists (template container only) | schema `report_templates` | **MISS** |
| Template versioning | `report_templates` has no version dimension | schema | **MISS** |
| Report lifecycle / versioning | `report_versions` (+`status`), S1/S3 | schema; S3 | **SUPP** |

## 12. Current 12-section report assessment

The V3 report's 12 sections (`backend/engines/report_generation.py`, `_DEFAULT_SECTIONS`): `metadata, organization, period, totals, scopes, activities, validation, benchmarking, provenance, calculation, lineage, generation`.

| Section | Nature | Requirements it can serve | Assessment |
|---|---|---|---|
| `metadata` | Technical / evidence | GP-PERIOD (partial), report identity for D15 binding | **Retain as technical metadata**; must gain framework/version binding |
| `organization` | Disclosure-ish | GP-ORG (partial), GP-COV (partial) | Partial; **no consolidation approach** |
| `period` | Disclosure | GP-PERIOD, SECR-PERIOD, E1-COMP | Retain; **bind to financial year** where required |
| `totals` | Disclosure | GP-S1/S2 (aggregate), SECR-S1/S2, E1-S123 (partial) | Retain; **no per-gas, no dual Scope 2, no Scope 3** |
| `scopes` | Disclosure | GP-OPS, SECR-S1/S2, E1-S123 | Retain; needs governed scope/scope-3 categories |
| `activities` | Disclosure | GP-OPS, GP-S1/S2 detail | Retain; **not an energy-kWh disclosure** |
| `validation` | Technical / evidence | GP-QUAL (partial) | Retain as **evidence**, not a statutory disclosure |
| `benchmarking` | Management (optional) | GP-CMP (partial), E1-INTENSITY (partial) | **Management/optional** — not a SECR/E1 disclosure as-is |
| `provenance` | Technical / evidence | GP-METH, GP-GAS (GWP source), E1-METH | Retain as **evidence**; feeds methodology narrative |
| `calculation` | Technical / evidence | GP-METH, GP-S1/S2 | Retain as **evidence** |
| `lineage` | Technical / evidence | GP-COV (partial), evidence traceability | Retain as **evidence** |
| `generation` | Technical | engine/version stamping for D15 | Retain; feeds reproducibility binding |

**Findings**
* **[I]** Six of twelve sections are **technical-evidence** sections (`metadata`, `validation`, `provenance`, `calculation`, `lineage`, `generation`), not regulatory disclosures. They are valuable for **evidence/provenance** (an asset) but must **not** be counted as disclosure coverage.
* **[R/I]** The four candidate disclosure sections (`organization`, `period`, `totals`, `scopes`, `activities`) cover **part** of the GHG/SECR/E1 carbon core and **none** of the L2/L3 or narrative requirements.
* **[REC]** The template **can evolve** into a presentation of the Disclosure Model (D3 permits evolution/supersession) — but **only after** the requirement catalogue is authoritatively frozen (§22). **Do not redesign the report now.**

## 13. Narrative analysis

Using the verified requirement set (and D5's hybrid model):

### 13.1 System-derived narrative (SYS) — CarbonTally can compose safely

| Requirement | Purpose | Facts required | Ownership | Evidence linkage | S4 binding |
|---|---|---|---|---|---|
| GP-METH / SECR-METH / E1-METH — methodology statement | A/M/S/E | methodology, algorithm version, factor sources | CarbonTally | `calculation_snapshots`, provenance | **Bind to disclosure** |
| GP-PERIOD / SECR-PERIOD — period statement | A/M/S/E | reporting period | CarbonTally | report metadata | Bound |
| Boundary statement (organizational/operational) | A/M/S/E | boundary + consolidation | CarbonTally + customer choice | boundary record | Mixed |

### 13.2 Customer-authored narrative (CUST) — CarbonTally cannot derive

| Requirement | Purpose | Facts required | Ownership | Evidence | S4 binding |
|---|---|---|---|---|---|
| **SECR-EE — energy-efficiency actions** | S | actions taken (+ indicative savings) | **Customer** (ratified required) | supporting notes | **Bind to disclosure** |
| GP-EXCL — exclusions & reasons | A/M/S/E | exclusions + rationale | Customer | rationale | Bind |
| GP-BY / GP-RECALC — base year & recalculation policy | A/M/E | base year, policy, threshold | Customer | policy doc | Bind |
| E1-POL / E1-TGT / E1-ACT — policies, targets, actions | E | policy/target/action data | Customer | policy/plan docs | Bind (L2) |
| GP-ORG / GP-CONS — boundary & consolidation choices | A/M/S/E | chosen approach | Customer | boundary doc | Bind |
| GP-QUAL — inventory quality/uncertainty statement | A/M/E | quality assessment | Mixed | methodology | Bind |

### 13.3 Mixed narrative (MIX)

| Requirement | Purpose | Facts | Ownership |
|---|---|---|---|
| GP-CHG — significant changes & causes | A/M/E | computed variance + customer explanation | **Mixed** |
| GP-S2 — market-based Scope 2 | A/M/S/E | contractual instruments + customer confirms | Mixed |
| SECR-INTENSITY / E1-INTENSITY — ratio narrative | S/E | computed ratio + customer-selected denominator | Mixed |

### 13.4 Optional management commentary (OPT)

* D5-B permits a **separate namespace for optional human-authored commentary that is not itself a regulatory disclosure** (e.g. management commentary in the **Management Report**). It has **no statutory source** and must never be presented as a disclosure.

### 13.5 S4 implications (no implementation)

* **[I]** A **requirement-bound narrative** model (D5-A) is needed: narrative must be **bound to a specific requirement**, not to an arbitrary field list.
* **[REC]** The **previously proposed 7-fields × 4,000-characters model is rejected by D5**, and **no character limits or field counts may be invented** here. The allowlist/limits remain **PO decisions (A1/A3)** — S4 stays blocked until the requirement map in §9 is frozen and A1/A3 are decided.

## 14. Structural data-model gap analysis (design concepts only — **no schema created**)

| Concept | Why required | Requirement driving it | Existing schema | Normalize or reference? | Needed now? |
|---|---|---|---|---|---|
| **Framework** | Frameworks are versioned and bound to reports (D14/D15) | All | **none** | Controlled reference table | **Design now** |
| **Framework version** | ESRS is mid-revision (2023 vs 2026); SECR/GHG amendments | D14/D15 | **none** | Controlled, immutable version key | **Design now** |
| **Requirement / disclosure** | The disclosure model is requirement-driven (D2) | All | **none** | Controlled catalogue keyed to framework version | **Design now** |
| **Requirement applicability** | D12/D13 need richer semantics than a boolean | GP-C*, SECR-APP, E1-* | **none** | Enum/flag set (required/conditional/optional/N-A/unavailable/customer-input/future) | **Design now** |
| **Requirement → data mapping** | Templates must not define requirements (D4) | All | **none** | Versioned mapping (requirement → data/calculation/evidence/narrative) | **Design now** |
| **Report purpose** | Four purposes share one foundation (D6-R) | All | `report_generation_queue.report_type` (free string) | Controlled enum + purpose definition | **Design now** |
| **Template version** | Reproducibility (D15) | All | `report_templates` (**no version dimension**) | Version key + immutable published templates | **Design now** |
| **Narrative binding** | D5 requirement-bound narrative | SECR-EE, GP-EXCL, E1-* | **none** (S4 blocked) | Bind narrative to requirement | **Design now; implement later (S4)** |
| **Organizational + consolidation boundary** | GP required content | GP-ORG, GP-CONS, GP-COV | partial (`organizations`, `facilities`) | Boundary record with consolidation approach | **Design now** |
| **Operational boundary** | GP required content | GP-OPS | partial (`emissions_logs.scope` free text) | Governed scope/activity taxonomy | **Design now** |
| **Per-gas emissions** | GP-GAS, E1-S123 | GP-GAS | **none** (CO2e only) | Per-gas ledger columns/rows | **Deferred** (needs factor support) |
| **Base year + recalculation** | GP required | GP-BY, GP-RECALC | **none** | Base-year record + recalculation log | **Design now** |
| **Comparative period** | GP/SECR/E1 | GP-CMP, SECR-PRIOR | partial | Prior-period reference (not duplication) | **Design now** |
| **Intensity-ratio definition** | D11 requires a controlled catalogue | SECR-INTENSITY, E1-INTENSITY | **none** | Controlled denominator/ratio catalogue | **Design now** |
| **Energy data / energy mix** | SECR + E1 Layer 1 | SECR-ENERGY, E1-ENERGY | partial (activity `raw_quantity`+`unit`) | Energy-source model + mix | **Design now** |
| **Targets / actions** | E1 Layer 2, SECR-EE | E1-TGT, E1-ACT, SECR-EE | **none** | Structured target/action model | **Design now; implement later** |

**[REC] Minimum necessary now:** framework, framework version, requirement, applicability, mapping, report purpose, template version. The rest are needed for **coverage** but can be phased. **[Warn]** Do **not** generalise into an unrestricted rules engine (D4).

## 15. Versioning analysis (D14/D15)

### 15.1 The required binding chain

```text
Framework                    (GHG Protocol | UK SECR | ESRS E1)
   -> Framework Version      (e.g. ESRS 2023/2772+2025/1416  vs  2026 Revised; SECR post-2019)
      -> Requirement Version (requirement catalogue revision)
         -> Mapping Version  (requirement -> data/calculation/evidence/narrative)
            -> Report Purpose (Annual | Management | SECR | ESRS E1)
               -> Template Version
                  -> Calculation/Data Context (engine + algorithm + factor set + period)
                     -> Evidence (snapshots, documents, provenance)
                        -> Narrative (requirement-bound + optional commentary)
                           -> Final Artefact (frozen, hashable)
```

### 15.2 What the current lifecycle already provides [R]

| Link | Current support |
|---|---|
| Report instance + version | `report_generation_queue` + `report_versions` (with `status`) — **SUPP** |
| Calculation/data context | `calculation_snapshots` (`methodology`, `algorithm_version`, `content_hash`), `emission_factors` — **SUPP** |
| Evidence / provenance | snapshots, factor provenance, documents, `audit_trail` (append-only) — **SUPP** |
| Lifecycle/approval | DRAFT→REVIEWED→APPROVED→FINAL (S3) — **SUPP** |
| Final artefact | `report_versions.file_url` + `final_report_url` (no frozen-PDF stage yet, S5) — **PART** |

### 15.3 What is missing for D14/D15 [U]

1. **Framework + framework-version binding** on the report/version record.
2. **Requirement-catalogue version** + **mapping version** referenced by the finalised report.
3. **Template version** (the `report_templates` table has no version dimension).
4. **Narrative binding** to requirements (S4-blocked).
5. **Frozen-artefact hash/immutability** (S5).
6. **[V]** A **live example of the exact need**: the **2026 Revised ESRS** replacing the 2023 ESRS means any ESRS report produced today must remain bound to the **2023** requirement version after the revision enters into force.

**[REC]** D15 requires that a finalised report record **which framework version, requirement version and mapping version** produced it — the report must remain reproducible without duplicating all source data.

## 16. Legacy compliance-claim findings (for the separate D16 disposition — **not modified**)

**[R] Facts found in the repository:**

| # | Finding | Evidence |
|---|---|---|
| 1 | The legacy route **`POST /api/reports/generate-enhanced-report` is mounted and live** | `backend/routes/reports.py:1287`; `reports.router` included in `backend/main.py:213` |
| 2 | The same endpoint is **also defined** in the unused `backend/report_generator.py:1040` | duplicate definition |
| 3 | Its generator emits an **explicit compliance claim**: footer *"Compliant with SECR/CSRD/ISSB reporting standards"* | `backend/report_generator.py:328` |
| 4 | A compliance statement *"This report complies with {report_type} requirements."* is written into the report body | `backend/report_generator.py:499` |
| 5 | `CSRD` and `ISSB` requests are **silently served by the SECR generator** (`generate_enhanced_secr_report()`) — a mislabelled path | `backend/routes/reports.py:1289-1296` |
| 6 | It reads data via the **legacy Supabase client**, not the authoritative engine/calculation chain | `backend/report_generator.py` |
| 7 | **Authorization observation:** the route requires `require_org_member()` but the visible code passes `request.organization_id` to the generator **without an `ensure_org_access` org-scope check** | `backend/routes/reports.py:1288-1307` |
| 8 | **[V] The claims exceed the ratified boundary**: D1 explicitly states the initial scope "does not constitute compliance certification or assurance"; D16 states no legacy compliance claim should remain exposed without separate authorization and supporting evidence | D1, D16 |

**[REC]** These findings **strongly support D16** (legacy/deprecated pending formal disposition). **No deletion, disabling, rewrite, migration or API change was made** — D16 requires a separate bounded disposition task. The claim text and the missing org-scope check should be recorded as evidence for that task.

## 17. Security / RLS implications (assessment only — **no change made**)

* **[R]** Report tables have **RLS enabled with zero policies** (a deny-all posture under non-owner roles; the backend's owner/service path bypasses it). The disclosure model must therefore keep **authorization at the API layer** (the existing `ensure_org_access` / role guards) and must not assume client-side (RLS) enforcement. *(Verified in the S3 verification gate.)*
* **[I] New scope dimensions the disclosure model introduces** (assessment, not implementation):
  1. **framework/requirement/mapping/template** records — are they system-controlled global reference data, or tenant-scoped? ([REC] system-controlled + versioned, read-only to tenants);
  2. **requirement applicability** (D13) — who may record it (customer Owner/Admin? consultant? staff?) and with what scope;
  3. **narrative** (D5) — authoring is restricted to **Customer Owner/Admin** (D5), consistent with the S4 analysis; **Members/Viewers** are excluded;
  4. **SECR/ESRS reporting context** — tenant-scoped, must be isolated across organisations;
  5. **legacy enhanced route** — the missing org-scope check (item 7 above) is a **pre-existing** tenant-isolation observation.
* **[REC]** **No RLS/grant/policy change is authorized or proposed here.** The separate production RLS security hold remains in force and untouched.

## 18. Competitor / product context (bounded — **not authority**)

* **[I]/[REC] Bounded observation only:** established carbon/reporting platforms generally separate **inventory management** from **disclosure/report production**, maintain **framework/requirement libraries**, map one dataset to multiple frameworks, and (for ESRS/EU) support **digital tagging (XBRL/iXBRL)**. This is consistent with the ratified D2 architecture. **Competitor behaviour is product-awareness only and is not evidence of any regulatory requirement**; the ESRS digital taxonomy is the relevant official consideration ([V] EFRAG is developing the ESRS XBRL taxonomy — S11).

## 19. PO decisions still required

| # | Decision | Why it is needed | Status |
|---|---|---|---|
| **A1** | Narrative field allowlist (keys, types, formatting, **who may edit**) | S4 blocked; D5 requirement-bound narrative | **OPEN** |
| **A3** | Narrative numeric limits (per field/version, item counts) | S4 blocked | **OPEN** |
| **P3** | Exactly which sections/fields are customer-editable | D5/S4 | **OPEN** |
| **D11-CAT** | SECR **intensity denominator catalogue** + recommended ratios | §6/§9 SECR-INTENSITY | **OPEN** |
| **E1-COV** | Exact **initial ESRS E1 disclosure coverage** (which `E1-*` + ESRS 2 items are Layer 1 / Layer 2 / excluded) | §7/§9 E1 table | **OPEN** |
| **E1-VER** | Which **ESRS version** to launch with (2023 ESRS only, or dual 2023/2026) | 2026 Revised ESRS pending OJ | **OPEN** |
| **APPL** | Applicability-capture model (UK "large" thresholds; ESRS D13; jurisdiction context) | SECR-APP, E1-DMAT | **OPEN** |
| **GP-CONS** | Whether to support **consolidation approach** (equity/financial/operational control) | GP-CONS required | **OPEN** |
| **GP-GAS** | Whether **CO2e-only** is acceptable initially (vs per-gas) | GP-GAS / E1-S123 | **OPEN** |
| **GP-S2M** | Whether to support **market-based Scope 2** (dual reporting) | GP-S2 / E1-S123 | **OPEN** |
| **GP-S3** | Whether **Scope 3 / value chain** is in the initial build | GP-S3, E1-SIG3 | **OPEN** |
| **GP-BY** | Whether **base year + recalculation** is in the initial build | GP-BY/RECALC | **OPEN** |
| **LEG** | D16 legacy-route disposition (reg. compliance claims + org-scope check) | §16 | **OPEN (D16 task)** |

## 20. Implementation readiness assessment

### 20.1 Gate status

| Gate | Requirement | Status |
|---|---|---|
| **Gate 1 — Regulatory evidence** | Complete authoritative verification of GHG / SECR / ESRS E1 / Ireland-EU | **PARTIAL — NOT CLOSED** (frameworks, versions and legal refs verified; **E1 identifiers, GHG Ch.9 lists, SECR SI content, Irish transposition missing**) |
| **Gate 2 — Requirement matrix** | Requirement-by-requirement matrix | **PRODUCED, NOT EVIDENTIALLY COMPLETE** (§9; E1 rows concept-level only) |
| **Gate 3 — PO review** | PO ratifies coverage, E1 coverage, SECR denominators, applicability, gaps, narrative bindings | **PENDING** |
| **Gate 4 — Architecture design** | Design the disclosure model + structural concepts | **NOT STARTED (not authorized)** |
| **Gate 5 — Implementation authorization** | Implementation prompt | **NOT AUTHORIZED** |

### 20.2 Direct answers to the required verdict questions

1. **Is the initial reporting architecture sufficiently specified to design the Disclosure Model?** — **Yes at the architectural level** (the D2/D4/D5/D6-R/D14/D15 chain is coherent and the repository can host it). **But the requirement catalogue it must encode is not yet evidentially complete**, so design may begin only as **concept design**, not as final content mapping.
2. **What exact regulatory requirements are verified?** — **[V]** Framework identities/versions and legal references: GHG Corporate Standard **2004 rev.** (+ Scope 2 Guidance 2015); SECR **in force from 1 Apr 2019** (PB13944); ESRS = **(EU) 2023/2772 as amended by 2025/1416**, with the **2026 Revised ESRS adopted but not in force**; CSRD = **(EU) 2022/2464**, OJ L 322, amended by **(EU) 2025/794**; transposition deadline **06/07/2024** — plus the **concept-level** requirement sets in §9.
3. **What requirements remain unresolved?** — ESRS E1 **exact identifiers/titles** and required/conditional status; the GHG Protocol **Chapter 9 required/optional lists**; the **SECR statutory content list and "large" thresholds** (SI 2018/1155); **Ireland's transposition measure**; CSRD **phase-in dates**; the CSRD amending instrument evidenced by the 18/03/2026 consolidation.
4. **What exact CarbonTally structural gaps exist?** — §14: no framework / framework-version / requirement / applicability / mapping / report-purpose / template-version model; no consolidation approach; no base year or recalculation; no exclusion model; no per-gas ledger; no dual Scope 2; no Scope 3; no energy/mix model; no intensity-ratio definition catalogue; no targets/actions; no narrative (S4 blocked).
5. **What must be added before S4?** — The **frozen requirement catalogue** (from §9 once the missing evidence is read) **plus the PO decisions A1/A3/P3** (§19). Only then can narrative be **bound to requirements** (D5) with a non-arbitrary allowlist.
6. **Is the current 12-section report still safe to retain as a presentation template?** — **Yes.** D3 permits retention for continuity/regression safety; §12 confirms it is a **presentation/evidence** artefact, not a disclosure model. **Retain; do not redesign now.**
7. **What must happen to the legacy compliance route?** — A **bounded D16 disposition task** must decide (remove / disable / retain behind a non-authoritative internal boundary / migrate). Its **compliance claims** and the **missing org-scope check** are evidence for that task. **Nothing was changed.**
8. **What PO decisions remain?** — §19 (A1, A3, P3, D11-CAT, E1-COV, E1-VER, APPL, GP-CONS, GP-GAS, GP-S2M, GP-S3, GP-BY, LEG).
9. **Is the project ready for Disclosure Model implementation?** — **No.** The Disclosure Model *design* may be authorised (Gate 4), but **implementation** must wait for Gate 1 closure and Gate 3 (PO) ratification.

## 21. Recommended next steps

1. **Close Gate 1** by reading the four missing primary sources (**no code changes**):
   (a) GHG Protocol Corporate Standard (2004 rev.) **Chapter 9** + the Feb-2013 **"Required gases and GWP values"** amendment;
   (b) UK **PB13944** (29 Mar 2019) and **SI 2018/1155**;
   (c) **Annex I, ESRS E1** of (EU) 2023/2772 (direct OJ read, or the EFRAG Knowledge Hub **"2023 ESRS"** interactive text);
   (d) **Ireland's** CSRD transposition measure + the consolidated CSRD **phase-in dates**.
2. **Re-issue this requirement matrix** with `GP-*` / `SECR-*` / `E1-*` rows **re-keyed to official identifiers** and required/conditional status.
3. **PO ratifies** coverage and the decisions in §19 (Gate 3).
4. **Then authorise Gate 4** (disclosure-model design — concepts only), including the **framework-version model** needed for the **ESRS 2023 → 2026 transition**.
5. Run the **D16 legacy-route disposition** as its own bounded task.
6. **Keep S4 blocked** until the requirement catalogue + A1/A3 are frozen.

## 22. Final verdict

### `DISCOVERY BLOCKED — ADDITIONAL AUTHORITATIVE EVIDENCE REQUIRED`

**Rationale.** The discovery established the frameworks, their **current authoritative versions** (including the decisive ESRS version-change finding) and a complete **concept-level** requirement matrix with repository capability mapping. However, **two of the three frameworks' requirement-level detail** (ESRS E1 identifiers; GHG Protocol Chapter 9 required/optional lists) and **two applicability inputs** (SECR statutory content/thresholds; Ireland's transposition) could **not be verified from primary sources within this session**. Under **D17** and this task's own discipline ("Do not claim a requirement is verified unless you can identify the authoritative source"), **Gate 1 is not closed** and the requirement matrix is **not evidentially complete**. Declaring "ready" would overstate verification.

**What is nonetheless ready:** the D2/D4/D5/D6-R/D14/D15 architecture is coherent; the repository **can** host the Disclosure Model; the **concept-level** gap analysis and the **capability mapping** are complete; and the **ESRS version transition** is now known and must shape the versioning model.

**What remains:** closure of the four evidence gaps in §21.1 and the PO decisions in §19.

> **⚠ SUPERSEDED (partial) BY §23** — the evidence-closure task `CT-P8-REPORTING-REGULATORY-EVIDENCE-CLOSURE-20260912-002` resolved part of the gaps above. **Read §23 for the closure record**; the findings in §§5–21 are retained unchanged as the historical record.
>
> **⚠ FURTHER SUPERSEDED (partial) BY §24** — the evidence-completion task `CT-P8-REPORTING-REGULATORY-EVIDENCE-COMPLETION-20260912-003` closed the CSRD 2026-amendment gap and advanced the SECR, GHG Protocol and Ireland gaps. **Read §24 (verdict §24.11) for the current status.**

## 23. Evidence closure update — 2026-09-12 (task `…-EVIDENCE-CLOSURE-20260912-002`)

This section **adds** the closure evidence; it does not rewrite §§5–22.

### 23.1 Closure status summary

| Gap (from §8 / Report B §14) | Previous | **Now** | Closing source |
|---|---|---|---|
| GHG Protocol Chapter 9 required/optional lists | [U] | **[U] still unresolved** | Corporate Standard PDF is the only source; not text-extractable (S1/S2) |
| GHG gases / Scope 2 Guidance / companions | [V] | **[V] confirmed** | S1 (ghgprotocol.org) |
| UK SECR statutory instrument identified | [I] | **[V] confirmed** — *Companies (Directors' Report) and LLPs (Energy and Carbon Report) Regulations 2018* | UK-SECR-G2 |
| UK SECR disclosure content | [U] | **[V] VERIFIED** | UK-SECR-G2 |
| UK SECR "large" numeric thresholds | [U] | **[U] partially verified** (definition by reference to CA 2006 ss.465–466) | S3 |
| ESRS legal version/status | [V] | **[V] confirmed** | S5–S7, S11 |
| ESRS E1 exact identifiers/titles | [U] | **[U] still unresolved** (annex >5 MB in every EUR-Lex representation) | S12 |
| CSRD phase-in/application timing | [U] | **[V] VERIFIED (recital + amending act)** | EU-2025/794-HTML |
| CSRD 2025 amendment | [V] | **[V] confirmed** | S9 / EU-2025/794-HTML |
| CSRD 18/03/2026 consolidation amending act | [U] | **[U] still unresolved** | S8 (versions list) |
| Ireland transposition | [U] | **[V] VERIFIED** — S.I. 336/2024 (+ S.I. 498/2024) | IE-336/IE-498 |
| Irish competent authority | [U] | **[U] unresolved** | — |

**New source register entries (added to §4):**

| # | Source | Tier | What it establishes |
|---|---|---|---|
| **UK-SECR-G2** | gov.uk — *Streamlined Energy and Carbon Reporting (SECR) for academy trusts* (DfE, published 9 Oct 2024, **updated 12 Aug 2026**) | 1/2 (official guidance) | The 2018 Regulations implement SECR; the **SECR minimum disclosure elements** incl. a worked example |
| **EU-2025/794-HTML** | EUR-Lex HTML of **Directive (EU) 2025/794** (OJ L series **2025/794, 16.4.2025**) | 1 (legislation) | CSRD phase-in dates + the **two-year postponement**; transposition deadline **31 Dec 2025** |
| **UK-PIR-2026** | gov.uk/DESNZ — *2026 post-implementation review of the SECR regulations 2018* (published **26 May 2026**) | 1/2 | SECR framework introduced **2019**, replaced the CRC Energy Efficiency Scheme; official review of SECR |
| **IE-336** | Irish Statute Book — **S.I. No. 336/2024**, *European Union (Corporate Sustainability Reporting) Regulations 2024* | 1 (legislation) | Ireland's principal CSRD transposition (in operation **6 July 2024**) |
| **IE-498** | Irish Statute Book — **S.I. No. 498/2024**, *…(No. 2) Regulations 2024* | 1 (legislation) | Further Irish amendments (made **1 Oct 2024**) |

### 23.2 GHG Protocol — closure status: **PARTIALLY VERIFIED** (unchanged core gap)

* **[V] Confirmed** (S1): the Corporate Standard remains the authoritative framework; it covers the **seven Kyoto gases**; categorises emissions into **Scope 1/2/3** (WRI/GHG-Protocol page); the **Scope 2 Guidance (2015)** and **Scope 3 Standard** are the relevant companions.
* **[U] Still unresolved:** the **Chapter 9 "Reporting GHG Emissions" required/optional information lists** and the **Feb-2013 "Required gases and GWP values"** content. Every available representation is a **binary PDF** (the only formats published by GHG Protocol); EUR-Lex/HTML alternatives do not exist for this document.
* **Closing action (unchanged, now confirmed necessary):** open the Corporate Standard PDF **Ch. 9 (and its Annexes)** directly in a PDF reader, or obtain the printed/OJ equivalent; then classify each D9 item.

### 23.3 UK SECR — closure status: **CONTENT VERIFIED**, thresholds partially verified

**[V] Instrument (authoritative):** the official UK government guidance states: *"The **Companies (Directors' Report) and Limited Liability Partnerships (Energy and Carbon Report) Regulations 2018** (the 2018 Regulations) implement the requirements for Streamlined Energy and Carbon Reporting (SECR)"* (UK-SECR-G2, updated 12 Aug 2026). DESNZ's official review confirms the SECR framework was **introduced in 2019 and replaced the CRC Energy Efficiency Scheme** (UK-PIR-2026, 26 May 2026).

**[V] Required disclosure elements** (official worked example in UK-SECR-G2; "the previous year's data must also be reported for comparison purposes"):

| # | Element | Notes |
|---|---|---|
| 1 | **Energy consumption used to calculate emissions (kWh)** | Headline kWh figure |
| 2 | Energy consumption **breakdown (kWh)** — gas / electricity / transport fuel | Marked **optional** in the example; fuel in **litres** converts to kWh via "fuel properties" (preferred) |
| 3 | **Scope 1 emissions (tCO2e)** | e.g. gas, owned transport |
| 4 | **Scope 2 emissions (tCO2e)** | purchased electricity |
| 5 | **Scope 3 emissions (tCO2e)** | e.g. business travel in employee-owned vehicles |
| 6 | **Total gross emissions (tCO2e)** | |
| 7 | **Intensity ratio** | Chosen ratio + rationale ("the recommended ratio for the sector") |
| 8 | **Quantification and reporting methodology** | Names the **2019 HM Government Environmental Reporting Guidelines**, the **GHG Reporting Protocol – Corporate Standard** and the **UK Government Conversion Factors for Company Reporting** |
| 9 | **Measures taken to improve energy efficiency** | Narrative |
| 10 | **Prior-year comparison** | Required alongside the current year |

**[V] Scope (from PB13944, S3):** from **1 April 2019** all **UK quoted companies** report **global energy use** *and* GHG emissions; **large unquoted companies** and **large LLPs** disclose annual energy use, GHG emissions and related information; **location-based** method encouraged where not dual-reporting.

**[U] Remaining SECR gap — numeric "large" thresholds.** The guidance defines "large" **by reference to the Companies Act 2006 (ss. 465–466)** rather than restating numbers; the **exact turnover/balance-sheet/employee thresholds were not captured** (legislation.gov.uk is JS-walled and PB13944 is a PDF). **Closing action:** read **PB13944** §"Who needs to comply" and/or **SI 2018/1155** (reg. 3 + Schedule) and **CA 2006 s.465** directly.

**Net effect on §9.3:** the rows `SECR-ENERGY`, `SECR-SRC`, `SECR-TRANSPORT`, `SECR-S1`, `SECR-S2`, `SECR-INTENSITY`, `SECR-METH`, `SECR-EE`, `SECR-PRIOR` now have **verified official content backing**; `SECR-APP` remains partially verified pending the numeric thresholds; `SECR-EXEMPT` remains **[U]** (exemptions/alternative provisions not captured).

### 23.4 ESRS E1 — closure status: **PARTIALLY VERIFIED** (identifiers still unresolved)

**[V] Legal position (confirmed, unchanged):**

| Version | Status | Dates |
|---|---|---|
| **Delegated Regulation (EU) 2023/2772** (ESRS Set 1) | **Legally applicable** | Adopted 31 Jul 2023; **OJ 22 Dec 2023** |
| **(EU) 2025/1416** | Amendment in force | Adopted 11 Jul 2025; **OJ 10 Nov 2025** — postponement of the date of application of disclosure requirements for certain undertakings |
| **Revised/Simplified ESRS** | **Adopted, NOT in force** | Delegated act adopted **3 Jul 2026**; effective only **after OJ publication + scrutiny**; EFRAG's **Simplified ESRS Technical Advice 30 Nov 2025** is the bridge |

**[U] The exact ESRS E1 disclosure identifiers/titles remain unresolved.** Closure was attempted through **every** representation available to this tooling:

| Attempt | Result |
|---|---|
| EUR-Lex **ELI** `reg_del/2023/2772/oj` and `/oj/eng` | **>5 MB — fetch refused** |
| EUR-Lex **`legal-content/EN/TXT`** | **>5 MB — refused** |
| EUR-Lex **`legal-content/EN/TXT/HTML`** | **>5 MB — refused** |
| EUR-Lex **legal-content summary (LSU)** | redirects to the >5 MB annex |
| **EFRAG** sustainability-reporting / ESRS-workstream / publications pages | 404 or no E1 index |
| **EFRAG ESRS Knowledge Hub** (`knowledgehub.efrag.org`) | **interactive application**; confirms the version map but does not serve the E1 identifier list as text |
| European Commission press-corner Q&A | JavaScript shell (no content) |

**Closing action (precise):** read **Annex I, ESRS E1 ("Climate change")** of Delegated Regulation (EU) 2023/2772 **directly** — either from the OJ PDF (OJ L, 22.12.2023) / the printed OJ, or from the EFRAG Knowledge Hub **"2023 ESRS"** interactive text, or from EFRAG's published ESRS E1 standard document. Then re-key §9.4's concept rows to the official `E1-*` identifiers and titles, and (once the 2026 Revised ESRS is in force) map 2023 → 2026 identifiers.

### 23.5 Ireland / EU — closure status: **VERIFIED** (with one minor gap)

**(1) EU law [V]**

| Item | Verified fact | Source |
|---|---|---|
| CSRD | **Directive (EU) 2022/2464 of 14 December 2022**, **OJ L 322, 16.12.2022, p. 15** | S8 |
| 2025 amendment | **Directive (EU) 2025/794 of 14 April 2025**, **OJ L series 2025/794, 16.4.2025** — amends (EU) 2022/2464 and 2024/1760 as regards the **dates from which Member States are to apply** certain reporting/due-diligence requirements; **Member States must transpose by 31 December 2025** | EU-2025/794-HTML |
| **Phase-in timing (as amended)** | **Large PIEs >500 employees** (and PIE parents of large groups >500 employees): report **in 2025 for FY beginning on/after 1 Jan 2024** (*unchanged*). **Other large undertakings / other large-group parents: FY beginning on/after 1 Jan 2025 → postponed by two years to FY beginning on/after 1 Jan 2027.** **SMEs (except micro), small non-complex institutions, captive insurers: FY on/after 1 Jan 2026 → postponed by two years to FY on/after 1 Jan 2028.** | EU-2025/794-HTML (recital 3 + "postponed by two years") |
| CSDDD (2024/1760) dates | Amended by the same directive (Article 2): phases from **26 July 2027 / 2028 / 2029** | EU-2025/794-HTML |
| Consolidated CSRD versions | 16/12/2022 · 17/04/2025 · **18/03/2026** | S8 |
| **[U] minor gap** | the **amending instrument behind the 18/03/2026 consolidation** was **not identified** (the consolidation list does not name it) | S8 |

**(2) Irish national implementation [V]**

| Item | Verified fact | Source |
|---|---|---|
| Principal transposition | **S.I. No. 336/2024 — European Union (Corporate Sustainability Reporting) Regulations 2024**; made by the Minister for Enterprise, Trade and Employment (notice in **Iris Oifigiúil, 9 July 2024**); **comes into operation 6 July 2024**; gives effect to Directive (EU) 2022/2464; amends the **Companies Act 2014** | IE-336 |
| Content evidence | The Irish SI inserts the CSRD-style sustainability-reporting content into the Companies Act 2014 (directors'/group reporting): business model & strategy (incl. resilience), **time-bound targets including, where appropriate, absolute GHG emission reduction targets at least for 2030 and 2050**, role/expertise of administrative, management and supervisory bodies, **policies**, **incentive schemes**, **due diligence**, principal actual/potential adverse impacts, principal risks & dependencies, and **indicators**; plus a **first-three-financial-years value-chain relief** | IE-336 |
| Further amendment | **S.I. No. 498/2024 — European Union (Corporate Sustainability Reporting) (No. 2) Regulations 2024**; made **1 October 2024** (Iris Oifigiúil, 4 October 2024); amends Companies Act 2014 **ss. 1587, 1594, 1598**; its explanatory note states it amends *"further to"* S.I. 336/2024 | IE-498 |
| **[U] minor gap** | the Irish **competent authority** was not captured | — |

**(3) Customer-specific applicability — NOT determined (per D13) [REC]**
CarbonTally must not determine a customer's legal position. The facts required to enable a *customer* (or its adviser) to determine Irish/EU applicability are: **legal form and member state of establishment**; **listing status** (regulated market / EEA / NYSE / NASDAQ); **size** (average employees, net turnover, balance-sheet total); **public-interest-entity status**; **role in a group** (parent/subsidiary, consolidated accounts); and the **financial-year commencement date** (which determines the applicable phase).

### 23.6 D1–D17 impact assessment

**No D1–D17 contradiction identified.**

* The closure evidence **strengthens** D1 (frameworks confirmed), D8/D9 (GHG foundation), D10/D11 (SECR), D13 (ESRS applicability model), D14/D15 (versioning — reinforced by the **2026 Revised ESRS** and the **2025/794 postponement**) and D17 (source hierarchy).
* **No PO decision is contradicted.** Two matters **increase** (but do not change) the weight of existing decisions:
  1. **[I] D14/D15 are now demonstrably urgent**: the ESRS revision (adopted, not in force) and the CSRD phase-in postponement are **live versioning events** within the initial planning horizon.
  2. **[I] D13 is reinforced**: Irish applicability arises from a **national SI (336/2024)** layered on the EU directive, confirming that CarbonTally must record **jurisdiction + reporting context** rather than assert legal status.

### 23.7 Revised closure verdict (supersedes §22 for status purposes)

### `EVIDENCE CLOSURE PARTIAL — PO REVIEW REQUIRED`

**Closed in this task:** UK SECR instrument + disclosure content; CSRD phase-in timing (as amended) and the 2025 amendment; **Ireland's transposition (S.I. 336/2024 + S.I. 498/2024)**; ESRS legal version/status (re-confirmed).

**Still open:** (a) **ESRS E1 exact identifiers/titles** (highest priority — annex not machine-readable); (b) **GHG Protocol Chapter 9** required/optional lists; (c) UK **numeric "large" thresholds**; (d) the **18/03/2026 CSRD amending instrument**; (e) Irish **competent authority**. All five require **direct reading of a specific primary document** (§§23.2–23.5) — not further discovery.

















---

## 24. Evidence completion update — 2026-09-12 (task `CT-P8-REPORTING-REGULATORY-EVIDENCE-COMPLETION-20260912-003`)

This section **adds** the second closure pass over the five gaps left open by §23. It **does not** rewrite §§5–23. Every earlier unresolved finding is preserved; where a finding is now resolved it is **explicitly superseded** with the new primary evidence and its source/version/date.

### 24.1 Five-gap closure table

| Gap | Status | Primary source | Exact evidence | Version / date | CarbonTally impact |
|---|---|---|---|---|---|
| **G1 — ESRS E1 exact identifiers/titles** | **UNRESOLVED** | Attempted, all blocked: EUR-Lex `CELEX:32023R2772` (TXT/HTML/ELI); EUR-Lex OJ-issue HTML `OJ:L_202302772`; Publications Office cellar `publications.europa.eu/resource/celex/32023R2772`; EFRAG Knowledge Hub; EFRAG Q&A platform | No authoritative **machine-readable** representation of Annex I, ESRS E1 could be obtained: TXT/HTML/ELI/cellar representations each exceed the retrieval size limit; the OJ-issue representation exceeds it too; the EFRAG Knowledge Hub renders ESRS through an interactive JS application and exposes no static text | ESRS Set 1 = **(EU) 2023/2772**, OJ L, 22.12.2023, as amended by **(EU) 2025/1416** (OJ 10.11.2025) | §9.4 E1 rows remain **concept-level**; **E1-COV** cannot yet be keyed to official identifiers |
| **G2 — GHG Protocol Chapter 9 required/optional lists** | **PARTIALLY VERIFIED** | `ghgprotocol.org` — Corporate Standard page (**S1**) | The Corporate Standard "provides **requirements and guidance**" for corporate GHG inventories; covers the **seven Kyoto Protocol gases — CO2, CH4, N2O, HFCs, PFCs, SF6, NF3**; updated in **2015** by the **Scope 2 Guidance** ("purchased or acquired electricity, steam, heat, and cooling"); published PDF is *GHG Protocol Corporate Standard Revised (English)*, **3.51 MB**; listed supporting documents include **"Required gases and GWP values" (February 2013, 252.51 KB)**, **"Base Year Adjustments" (March 2004)** and **"Categorizing GHG Emissions from Leased Assets" (March 2004)**; listed resource **"GHG Protocol Reporting Template" (February 2017)**. The Chapter 9 required/optional lists remain **non-extractable** (all GHG Protocol publications are binary PDFs — re-confirmed on a DESNZ PDF this task) | Corporate Standard (**2004 revised**) + Scope 2 Guidance (**2015**) + Feb-**2013** GWP annex; page read **2026-09-12** | Improves evidence for **GP-GAS** (seven-gas list; Feb-2013 GWP source identified), **GP-S2M** (2015 Scope 2 Guidance exists as a companion) and **GP-BY** (2004 base-year-adjustment appendix); **Chapter 9 classification remains [U]** |
| **G3 — UK SECR numeric "large" thresholds** | **PARTIALLY VERIFIED** | DESNZ — *SECR regulations: evaluation* (gov.uk, pub. **29 Jan 2026**, upd. **6 Aug 2026**); DfE — *SECR for academy trusts* (upd. **12 Aug 2026**) §4.2–4.3; HMRC **ESM10006** + **ESM10006A** (both upd. **22 Jul 2026**) | Scope: SECR "applies to **UK-registered quoted companies, as well as large unquoted companies and LLPs that exceed the statutory thresholds for employees, turnover and balance sheet totals**". De minimis: "**large unquoted companies that have consumed (in the UK) more than 40,000 kilowatt-hours (kWh) of energy** in the reporting period" must include energy and carbon information in the directors' report, "for any period beginning on or after **1 April 2019**"; prior-year equivalents also disclosed. CA 2006 size test: corporate entity is "medium or large-sized if it meets **at least two of** turnover, balance sheet total and employees **for two consecutive financial years**" — small-companies criteria at **CA 2006 s.382 onwards**. **Threshold change: "From 6 April 2025, two of these three thresholds in the Companies Act increased. The changes apply to financial years beginning on or after 6 April 2025"** — medium/large = turnover **> £15 million** and balance sheet total **> £7.5 million**, **"the 50-employee limit remains unchanged"** | Regime in force from **1 Apr 2019**; threshold change effective for FY **beginning on or after 6 Apr 2025** | **APPL** / SECR applicability must be **date-aware** and must not hard-code one threshold set; a 2025 threshold change is a live applicability variable |

| **G4 — 18 March 2026 CSRD amendment** | **VERIFIED** | EUR-Lex consolidated text **`02022L2464 — EN — 18.03.2026 — 002.001`**; EUR-Lex **`32026L0470`** (ELI `dir/2026/470/oj`) | The consolidated CSRD's amending-act list states verbatim: **►M1 DIRECTIVE (EU) 2025/794 … of 14 April 2025 — OJ L 794, 1, 16.4.2025**; **►M2 DIRECTIVE (EU) 2026/470 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL of 24 February 2026 — OJ L 470, 1, 26.2.2026**. Full title: *"Directive (EU) 2026/470 … of 24 February 2026 amending Directives 2006/43/EC, 2013/34/EU, (EU) 2022/2464 and (EU) 2024/1760 as regards certain corporate sustainability reporting requirements and certain corporate sustainability due diligence requirements (Text with EEA relevance)"* | Adopted **24 Feb 2026**; OJ **26 Feb 2026**; consolidated CSRD state **18 Mar 2026** | The CSRD **scope and timing are now governed by three acts** (2022/2464 + 2025/794 + 2026/470). Applicability logic must reflect the **amended (narrower) scope stated in the 2026 act**, not the original 2022 scope |
| **G5 — Irish competent authority** | **PARTIALLY VERIFIED** | `iaasa.ie` — *Functions* page; Irish Statute Book **S.I. 336/2024**; `enterprise.gov.ie` — *Company & Corporate Law* | "**The Companies Act 2014 sets out IAASA's legal responsibilities**"; IAASA **"sets the standards that govern statutory audits and sustainability assurance in Ireland"**; **"Under the EU Transparency Directive (enacted through Ireland's Transparency Regulations 2007), IAASA acts as Ireland's corporate reporting supervisor"**; IAASA "inspects the quality of the audit **and sustainability assurance** work performed by the auditors and **sustainability assurance service providers** of **Public Interest Entities (PIEs)**"; IAASA "conducts enquiries and investigations under **sections 933 and 934 of the Companies Act**". The read portion of S.I. 336/2024 (regs 1–5 and the inserted reporting content) contains **no competent-authority designation**; DETE lists the **CRO** as the central statutory repository and records a *Periodic Critical Review of IAASA* (Nov 2025) | IAASA functions as published 2026; S.I. 336/2024 in operation **6 Jul 2024** | **Regulatory context only.** No CarbonTally product requirement arises; no customer legal determination is made |

### 24.2 Gap 1 — ESRS E1 identifiers: **UNRESOLVED** (new routes attempted, no closure)

* **Preserved finding (§7.2, §23.4):** the exact ESRS E1 disclosure identifiers/titles had not been read from a primary source.
* **New routes attempted in this task — all blocked:**
  1. EUR-Lex **Publications Office cellar** (`publications.europa.eu/resource/celex/32023R2772`) — response exceeded the 5 MB retrieval limit.
  2. EUR-Lex **Official Journal issue HTML** (`legal-content/EN/TXT/HTML/?uri=OJ:L_202302772`) — response exceeded the 5 MB retrieval limit.
  3. **EFRAG Knowledge Hub** — the *Historical Documents* page was retrievable and **confirms the Hub hosts the "2023 ESRS" and "2026 Revised ESRS" libraries**, but the standard text is rendered by an **interactive JS application** with no static fallback (`/library/2023-esrs`, `/interactive/2023-esrs` → HTTP 404; the Hub advertises a "Starter plan" app, not a document).
  4. **EFRAG Q&A platform** (`efrag.org/en/sustainability-reporting/esrs-q-a-platform`) → HTTP 404.
* **Conclusion:** the authoritative text exists and its legal identity is certain (**Annex I to (EU) 2023/2772**, as amended by **(EU) 2025/1416**), but **the identifier-level transcription is not obtainable with the tooling available to this session**. This is a **tooling/representation blocker, not a source-availability blocker**.
* **Closing action (precise):** transcribe Annex I, ESRS E1 directly from the OJ PDF/printed OJ, or from EFRAG's published ESRS E1 document, using a reader or a tool that renders PDF/text. Then re-key §9.4 rows to official identifiers and record required/conditional status.
* **No change** to the previous classification: E1 rows stay **[U] at identifier level, [V] at framework/version level**.

### 24.3 Gap 2 — GHG Protocol: **PARTIALLY VERIFIED** (foundation improved; Chapter 9 still [U])

* **New verified facts [V]** (S1, `ghgprotocol.org` Corporate Standard page, read 2026-09-12):
  * the standard "provides **requirements and guidance** for companies and other organizations preparing a corporate-level GHG emissions inventory";
  * it covers the **seven Kyoto Protocol gases: CO2, CH4, N2O, HFCs, PFCs, SF6, NF3**;
  * it was "**updated in 2015 with the Scope 2 Guidance**, which allows companies to credibly measure and report emissions from **purchased or acquired electricity, steam, heat, and cooling**";
  * the published document is *GHG Protocol Corporate Standard Revised (English)*, **3.51 MB**;
  * listed **supporting documents**: **"Required gases and GWP values" — Date: February 2013 (252.51 KB)**; **"Appendices / Base Year Adjustments" — March 2004**; **"Categorizing GHG Emissions from Leased Assets" — March 2004**;
  * listed **additional resource**: **"GHG Protocol Reporting Template" — Date: February 2017 (33.63 KB)**;
  * the standard "focuses only on the accounting and reporting of emissions".
* **Still [U]:** the **Chapter 9 "Reporting GHG Emissions" required / optional information lists**. Confirmed again this task that the retrieval tooling returns **raw PDF byte-streams**, so PDF-only sources are not text-readable regardless of publisher.
* **Requirement-classification position (unchanged):** no GHG Protocol **optional** item may be promoted to mandatory functionality without the Chapter 9 text (§9.2 rule).

### 24.4 Gap 3 — UK SECR thresholds: **PARTIALLY VERIFIED** (scope, de minimis and the 2025 threshold change now verified)

* **New verified facts [V]:**
  * **In-scope categories** (DESNZ evaluation, pub. 29 Jan 2026 / upd. 6 Aug 2026): "**UK-registered quoted companies, as well as large unquoted companies and LLPs that exceed the statutory thresholds for employees, turnover and balance sheet totals**".
  * **De minimis threshold** (DfE guidance §4.2, upd. 12 Aug 2026): **more than 40,000 kWh** of UK energy consumption for **large unquoted companies**; applies "for any period beginning on or after **1 April 2019**"; **prior-year equivalent figures must also be disclosed** (§4.3).
  * **Companies Act 2006 size test** (HMRC ESM10006, upd. 22 Jul 2026): a corporate entity "will be medium or large-sized if it meets **at least two of** the following criteria **for two consecutive financial years**"; qualifying criteria for the small-companies regime are at **section 382 Companies Act 2006 onwards**.
  * **Threshold change effective for financial years beginning on or after 6 April 2025** (HMRC ESM10006A, upd. 22 Jul 2026): "**From 6 April 2025, two of these three thresholds in the Companies Act increased. The changes apply to financial years beginning on or after 6 April 2025.**" For those years "the thresholds for when a corporate entity is medium or large-sized are: **Turnover of more than £15 million; and Balance sheet total of more than £7.5 million. The 50-employee limit remains unchanged.**"
  * **Disclosure elements** (§23.3, re-confirmed): energy consumption (kWh); optional energy breakdown (gas / electricity / transport fuel); **Scope 1**, **Scope 2** and **Scope 3** emissions in tCO2e; **total gross emissions** in tCO2e; **intensity ratio**; quantification & reporting methodology (2019 HM Government Environmental Reporting Guidelines, **GHG Reporting Protocol – Corporate Standard**, UK Government conversion factors); intensity-measurement rationale; measures taken to improve energy efficiency; prior-year comparison.
* **Supersedes the previous classification** of the SECR applicability inputs from **[U]** to **[V] for scope, the 40,000 kWh condition and the 2025 threshold change**; the "SECR content verified" finding of §23.3 stands.
* **Still [U]:** (i) the **2018 Regulations' own definition of "large company" / "large LLP"** and their exemptions; (ii) the **exact numeric CA 2006 s.465 medium/large limits** at and after 6 April 2025 (HMRC states only the "not small" boundary, not the large boundary); (iii) LLP-specific qualification conditions. Blockers: `legislation.gov.uk` is JavaScript-walled; the identified official PDFs are not text-extractable.
* **New watch item [V] — UK thresholds are in active reform:** gov.uk consultation *Non-financial reporting review: simpler corporate reporting* (14 Oct 2024) sought views on **raising the employee threshold for medium-sized companies to 500 employees** and exempting medium-sized companies from producing a Strategic Report; a further consultation, *Modernising corporate reporting* (7 Sep 2026), and the accompanying gov.uk news item (6 Sep 2026) describe a corporate-reporting overhaul. **CarbonTally must not hard-code a single SECR applicability threshold set** — thresholds are a versioned, date-aware input (**APPL**, D10/D11).

### 24.5 Gap 4 — the 18 March 2026 CSRD amendment: **VERIFIED (closed)**

* **Preserved finding (§23.1, §23.5):** the consolidation point **18/03/2026** had been observed in EUR-Lex's consolidated-versions list but the **amending act was not identified**.
* **New authoritative evidence [V]** — EUR-Lex consolidated text **`02022L2464 — EN — 18.03.2026 — 002.001`** states, verbatim:

  > Amended by: … **►M1 DIRECTIVE (EU) 2025/794** OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL of 14 April 2025 — **L 794, 1, 16.4.2025**;
  > **►M2 DIRECTIVE (EU) 2026/470** OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL of 24 February 2026 — **L 470, 1, 26.2.2026**

* **Instrument identified [V]:** **Directive (EU) 2026/470 of 24 February 2026**, CELEX **32026L0470**, ELI `http://data.europa.eu/eli/dir/2026/470/oj`, OJ **L 470, p. 1, 26.2.2026** — *amending Directives 2006/43/EC, 2013/34/EU, (EU) 2022/2464 and (EU) 2024/1760 as regards certain corporate sustainability reporting requirements and certain corporate sustainability due diligence requirements*.
* **Interaction with Directive (EU) 2025/794 [V]:** they are **sequential and cumulative** — 2025/794 is designated **►M1** (the "stop-the-clock" postponement of application dates) and 2026/470 is designated **►M2** (the substantive scope/simplification amendment). The 18/03/2026 consolidation therefore = CSRD as amended by **both**.
* **Character of the 2026 act [V] (from its recitals):** it adjusts the **scope** of the CSRD ("the Commission should assess the appropriateness of the **new scope of Directive (EU) 2022/2464 as amended by this Directive**"), includes a review clause referencing proportionality and a possible simplified reporting regime, and narrows/clarifies the scope of CSDDD (2024/1760). It is the act commonly described as the CSRD/CSDDD "Omnibus".
* **Residual [U] (detail, not identity):** the 2026 act's **own entry into force / transposition deadline** and the **exact amended Article 5(2) application dates** were not transcribed — the document body (140,673 characters) is longer than the readable window. This is a **date-detail** gap, not an identification gap.
* **Mandatory distinction:** the *EU legal requirement* is the amended CSRD (2022/2464 + 2025/794 + 2026/470). CarbonTally's *product applicability logic* must (a) record the **framework version/date** and (b) present the **amended scope** — it must not assert that any particular customer is in or out of scope (D13).
* **Changed requirement classification:** the §8.1/§9.0 framing of the CSRD as a two-act chain is **superseded** — it is now a **three-act chain**, and applicability depends on the **financial year commencement date**, which determines which phase (and which amended scope) applies.

### 24.6 Gap 5 — Irish competent authority: **PARTIALLY VERIFIED**

* **New authoritative evidence [V] (`iaasa.ie`, Functions):**
  * "**The Companies Act 2014 sets out IAASA's legal responsibilities**", across five areas: Standards and Policy; Professional Body Supervision; Corporate Reporting Supervision; Assurance Quality Supervision; Enforcement.
  * Standards and Policy — IAASA "**sets the standards that govern statutory audits and sustainability assurance in Ireland**".
  * Corporate Reporting Supervision — "Under the EU Transparency Directive (enacted through Ireland's **Transparency Regulations 2007**), **IAASA acts as Ireland's corporate reporting supervisor**".
  * Assurance Quality Supervision — IAASA "inspects the quality of the audit **and sustainability assurance** work performed by the auditors and **sustainability assurance service providers** of **Public Interest Entities (PIEs)**".
  * Enforcement — IAASA "conducts enquiries and investigations under **sections 933 and 934 of the Companies Act**".
* **Supporting evidence [V]:** the readable portion of **S.I. 336/2024** (reg. 1 citation/commencement — in operation **6 July 2024**; reg. 2 "Principal Act" = Companies Act 2014; regs 3–5 and the inserted reporting content) contains **no express "competent authority" designation**; `enterprise.gov.ie` describes the **CRO** as "the central repository of public statutory information on Irish companies" and records a *Periodic Critical Review of the Irish Auditing and Accounting Supervisory Authority* (Nov 2025).
* **Still [U]:** the **formal designation provision** naming the CSRD/Accounting-Directive competent authority (or authorities) in Ireland. Not established by the sources read.
* **Conclusion:** the Irish supervisory landscape is **IAASA (corporate reporting supervision + sustainability-assurance oversight)**, the **CRO (filing/registry)** and the **Corporate Enforcement Authority (company-law enforcement)**; whether and how the SI designates these expressly remains open. **Impact: regulatory context only — no CarbonTally product requirement, and no legal determination for any customer** (D13).

### 24.7 ESRS 2026 revision — legal status verified separately from adoption

The eight required determinations, each kept distinct:

| # | Determination | Finding | Basis |
|---|---|---|---|
| 1 | **Adoption date** | The Commission **adopted** the Revised/Simplified ESRS delegated act on **3 July 2026** | Commission (recorded §7.1; EFRAG Hub corroborates the sequence) |
| 2 | **Publication in the Official Journal** | **Not established** in the sources read; the EFRAG Knowledge Hub states the 2023 ESRS "**should be replaced in 2026 by simplified ESRS once adopted as delegated act by the EC**" | EFRAG Knowledge Hub (*Historical Documents*, read 2026-09-12) |
| 3 | **Scrutiny / status** | Pending delegated-act scrutiny; EFRAG states the EC "**will provide a delegated act on simplified ESRS following its due process**" | EFRAG Knowledge Hub |
| 4 | **Entry into force** | **Not in force** as of the task date | EFRAG Hub + prior finding (§7.1, §23.4) |
| 5 | **Application date** | **Not applicable yet** — no application date is in effect | EFRAG Hub + prior finding |
| 6 | **Legally applicable as of the task date?** | **No.** The applicable ESRS remain **(EU) 2023/2772** (OJ 22.12.2023) as amended by **(EU) 2025/1416** (OJ 10.11.2025) | §23.4 + §24.7 |
| 7 | **Must CarbonTally implement it now?** | **No.** EFRAG states plainly: "**Only the delegated act applies directly to companies in the scope of the amended CSRD**" — until the delegated act is in force, the 2023 set governs | EFRAG Knowledge Hub |
| 8 | **Transition / version-binding implication (D14/D15)** | The 2023 set → 2026 revision is a **first-class framework-version transition**: CarbonTally must bind outputs to the **ESRS version in force at the reporting date**, model a future version as a **new version** (never an in-place edit), and preserve the **exact** version identifier on every disclosure/calculation snapshot | Derived from the Hub statement + D14/D15 |

* **Future-version disclosure identifiers:** none are recorded, because no authoritative identifiers for the 2026 revision were obtainable (§24.2). **This is deliberately left blank rather than guessed.**
* **Rule applied:** "adopted" ≠ "currently applicable". The currently applicable ESRS model is **not** replaced by the future revision in this report, and CarbonTally must not implement the future revision ahead of its legal effect.
* **Corroboration of Gap 4:** the EFRAG Hub's own wording — "companies in the scope of the **amended CSRD**" — independently indicates that the CSRD has been amended, consistent with §24.5.
* **E1-VER (PO decision) is now materially better informed:** the question is no longer "which version is law?" (the 2023 set, as amended) but "does CarbonTally launch with the 2023 set only, or build dual-version support now?" — a **product-policy** question.

### 24.8 D1–D17 impact assessment

**No D1–D17 contradiction identified.**

* **Strengthened:** D1 (frameworks and their legal versions confirmed), D8/D9 (GHG foundation — seven gases, Scope 2 Guidance 2015, Feb-2013 GWP annex, base-year appendix), D10/D11 (SECR — scope, 40,000 kWh de minimis, 2025 threshold change, disclosure elements), D12/D13 (ESRS + applicability — date/version-dependent, no customer legal determination), D14/D15 (versioning — 2023→2026 ESRS transition and the CSRD's three-act chain), D16 (legacy claims — untouched), D17 (source hierarchy — applied throughout).
* **Two matters increase, but do not change, existing decisions:**
  1. **[I] D14/D15 are now demonstrably urgent and concrete**: there is a **live ESRS version transition** (2023 set in force; 2026 revision adopted, not in force) **and** a **three-act CSRD chain** with date-dependent application. Version binding is not a future concern.
  2. **[I] D10/D11 applicability must be date-aware**: UK SECR thresholds changed for financial years beginning on or after **6 April 2025**, and UK size/scope rules are **in active reform**. A single hard-coded threshold set would be wrong for part of the population.
* **Nothing in the new evidence contradicts any ratified decision**, and no new PO decision is *forced* by law — the open items are **product-policy choices** (§24.9).

### 24.9 PO decision inventory — evidence status (no decisions made here)

| # | Decision | Does authoritative evidence now permit the PO to decide? | Additional evidence required? | Nature of the decision |
|---|---|---|---|---|
| **A1** | Narrative field allowlist | **Yes** — framework scope is established; the allowlist is a design choice | No | **Product/UX policy** |
| **A3** | Narrative numeric limits | **Yes** | No | **Product policy** |
| **P3** | Which sections/fields are customer-editable | **Yes** — the §13.1–13.4 SYS/CUST/MIX/OPT classification stands | No | **Product/UX policy** |
| **D11-CAT** | SECR intensity denominator catalogue | **Yes** — SECR requires an intensity ratio **and a rationale**; the catalogue itself is a choice | No (the Regulations do not prescribe denominators) | **Product policy** |
| **E1-COV** | Exact initial ESRS E1 disclosure coverage | **Not yet at identifier level** — the E1 identifier list is **[U]** (§24.2) | **Yes — G1 must close first**, or the PO must accept the concept-level E1 set enumerated in §9.4 | **Regulatory fact + product policy (hybrid)** |
| **E1-VER** | Which ESRS version to launch with | **Yes** — the law is settled (2023 set, as amended); launch-2023-only vs dual-version is a choice | No | **Product policy** |
| **APPL** | Applicability-capture model | **Yes** — SECR scope/de minimis/2025 change and the CSRD chain are **[V]**; the *capture model* is a design choice | No for the model; the residual [U] items (§§24.4, 24.6) affect only presentation precision | **Product policy** (minor regulatory detail outstanding) |
| **GP-CONS** | Consolidation approach support | **Yes** — the standard offers the approaches; the support level is a choice | No | **Product policy** |
| **GP-GAS** | CO2e-only initially vs per-gas | **Yes** — the **seven-gas list is [V]** (§24.3) | No | **Product policy** |
| **GP-S2M** | Market-based Scope 2 (dual reporting) | **Yes** — the **2015 Scope 2 Guidance** is **[V]** evidence that dual reporting exists | No for the decision; the guidance's precise wording sits behind the PDF blocker | **Product policy** |
| **GP-S3** | Scope 3 in the initial build | **Yes** | No | **Product policy** |
| **GP-BY** | Base year + recalculation | **Yes** — a **Base Year Adjustments** appendix (March 2004) is **[V]**; its mandatory/optional status stays [U] | No for the decision | **Product policy** |
| **LEG** | D16 legacy-route disposition | **Yes** | No | **Product/architecture policy** (separate D16 task) |

**Summary:** **12 of 13** decisions are now **permission-ready** on the available evidence and are **architectural/product-policy matters, not regulatory facts**. Only **E1-COV** still depends on a remaining regulatory fact (**G1**).

### 24.10 Readiness test — direct answers

* **Q1 — Are the initial regulatory requirements now sufficiently evidenced to serve as the authoritative basis for Disclosure Model design?**
  **Substantially yes, with one exception.** Framework identity, legal version and status are **[V]** for all three frameworks. **UK SECR** scope, de minimis (**40,000 kWh**) and the **2025 threshold change** are **[V]**, and the SECR disclosure elements are **[V]**. The **CSRD** is now correctly modelled as a **three-act chain** with an identified 2026 amendment. **ESRS** legal status is **[V]**. The single exception is the **ESRS E1 identifier-level disclosure list (G1, [U])**, plus three minor detail residuals (GHG Chapter 9 lists; the SECR SI's own "large" definition; the Irish designation). The requirements are therefore sufficient as the basis for **design**, and sufficient for the PO to decide **12 of 13** open decisions.

* **Q2 — Are the remaining gaps regulatory facts, or are they now PO/product decisions?**
  **Both, cleanly separable.** The remaining **regulatory facts** are: (i) **ESRS E1 identifiers** (G1); (ii) **GHG Protocol Chapter 9 required/optional lists** (G2 detail); (iii) the **SECR SI's own "large"/exemption wording and the CA 2006 s.465 numerics** (G3 detail); (iv) the **2026 act's own application dates** (G4 detail); (v) the **Irish competent-authority designation** (G5 detail). Everything else now confronting the project — **A1, A3, P3, D11-CAT, E1-VER, APPL (model), GP-CONS, GP-GAS, GP-S2M, GP-S3, GP-BY, LEG** — is a **PO/product-policy decision**, not a legal question.

* **Q3 — Can the next task be a Disclosure Model design task?**
  **Yes — for PO review and concept-level/architectural design, subject to two conditions:** (a) **E1-COV must either be preceded by closing G1**, or the PO must ratify coverage against the **concept-level E1 set in §9.4**; and (b) the **framework-version model** must be part of the design (D14/D15), because the **ESRS 2023→2026 transition** and the **CSRD three-act chain** are live. This is **not** authorization to implement.

* **Q4 — Are there any remaining primary-source blockers?**
  **Yes — five, all of the same kind (representation of the source, not availability of the source):**
  1. **EUR-Lex / Publications Office** — the ESRS annex exceeds the retrieval size limit in every text representation (TXT, HTML, ELI, cellar, OJ-issue).
  2. **EFRAG Knowledge Hub** — ESRS text is exposed only through an interactive application; no static text or document endpoint.
  3. **GHG Protocol** — Chapter 9 exists only as a binary PDF, and the retrieval tool does not extract PDF text (re-confirmed this task).
  4. **legislation.gov.uk** — JavaScript-walled; the 2018 Regulations could not be read directly.
  5. **Irish Statute Book** — the SI is retrievable, but the readable window did not reach any competent-authority designation.
  **Each is a tooling/representation blocker solvable by a human reader or a PDF/text-rendering tool — not by further searching.**

### 24.11 Evidence-completion verdict (supersedes §23.7 for status purposes)

### `EVIDENCE CLOSURE PARTIAL — PO REVIEW REQUIRED`

* **Closed in this task:** **G4 — the 18 March 2026 CSRD amendment is identified and verified** as **Directive (EU) 2026/470 of 24 February 2026** (OJ **L 470**, p. 1, **26.2.2026**; CELEX **32026L0470**), consolidating with **Directive (EU) 2025/794** into the CSRD text of **18/03/2026**. **The ESRS 2026-revision status is also verified separately from its adoption** (§24.7), including the decisive point that **only an adopted delegated act applies**.
* **Materially advanced in this task:** **G3 — UK SECR** (in-scope categories, the **40,000 kWh** de minimis, the CA 2006 two-consecutive-financial-year size test, and the **6 April 2025 threshold increase to turnover > £15m / balance sheet > £7.5m with the 50-employee limit unchanged**); **G2 — GHG Protocol** (seven Kyoto gases, Scope 2 Guidance 2015, Feb-2013 GWP annex, base-year appendix, Reporting Template); **G5 — Ireland** (IAASA's statutory corporate-reporting-supervision and sustainability-assurance roles).
* **Not closed:** **G1 — ESRS E1 exact identifiers/titles** (tooling blocker) — the one item that still gates **E1-COV**; plus four **detail** residuals that do **not** gate design.
* **The verdict is NOT "implementation ready".** Gate 1 remains **partially closed**; Gate 3 (PO ratification) is **pending**; Gate 4 (design) may be authorised; Gate 5 (implementation) is **not authorised**. No code, schema, RLS, route or production change was made in this task.

> **⚠ §23.7 is SUPPLEMENTED BY §24.11** for current status. §§5–23 are retained unchanged as the historical record; §24 supersedes §23 **only** on the five gaps it addresses.






