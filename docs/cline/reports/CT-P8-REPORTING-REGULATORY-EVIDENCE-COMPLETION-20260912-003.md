# CT-P8-REPORTING-REGULATORY-EVIDENCE-COMPLETION-20260912-003

**Task reference:** `CT-P8-REPORTING-REGULATORY-EVIDENCE-COMPLETION-20260912-003`
**Date:** 2026-09-12
**Type:** BOUNDED REGULATORY EVIDENCE COMPLETION — **no implementation**
**Follows:** `CT-P8-REPORTING-REGULATORY-REQUIREMENT-VERIFICATION-20260912-001` (verdict: *DISCOVERY BLOCKED*), `CT-P8-REPORTING-REGULATORY-EVIDENCE-CLOSURE-20260912-002` (verdict: *EVIDENCE CLOSURE PARTIAL — PO REVIEW REQUIRED*)
**Governing decisions:** D1–D17 (treated as fixed)
**Final verdict:** `EVIDENCE CLOSURE PARTIAL — PO REVIEW REQUIRED`

---

## 1. Objective

Close the **five remaining authoritative-evidence gaps** identified by task `…-002`, using **primary/authoritative sources only**, and determine whether the regulatory evidence gate can be closed. **Evidence closure only** — no design, no schema, no code.

## 2. Previous blocking gaps (from `…-002` §23.7)

| # | Gap | Status entering this task |
|---|---|---|
| **G1** | ESRS **E1** exact disclosure identifiers/titles (Annex I to (EU) 2023/2772) | **[U]** — annex >5 MB in every EUR-Lex representation |
| **G2** | GHG Protocol Corporate Standard **Chapter 9** required/optional lists | **[U]** — PDF-only |
| **G3** | UK SECR numeric **"large"** thresholds | **[U]** — legislation.gov.uk JS-walled |
| **G4** | The **18 March 2026** CSRD amending act | **[U]** — consolidation date seen, act unidentified |
| **G5** | Irish **competent authority** | **[U]** — not captured |

## 3. Sources consulted (this task, all primary/authoritative)

| # | Source | Tier | Outcome |
|---|---|---|---|
| 1 | EUR-Lex consolidated CSRD — **`02022L2464 — EN — 18.03.2026 — 002.001`** (HTML representation) | 1 (legislation) | **Amending-act list obtained verbatim** → **G4 closed** |
| 2 | EUR-Lex — **`32026L0470`** (ELI `dir/2026/470/oj`) — Directive (EU) 2026/470 | 1 (legislation) | Title, adoption date, OJ ref, recitals obtained |
| 3 | EUR-Lex **search** (`/search.html`, quick + title queries) | 1 | Confirmed the adopted acts vs proposals (COM(2025)81 = proposal) |
| 4 | EUR-Lex **OJ-issue** HTML `OJ:L_202302772` | 1 | **Blocked** — exceeds 5 MB |
| 5 | Publications Office **cellar** `publications.europa.eu/resource/celex/32023R2772` | 1 | **Blocked** — exceeds 5 MB |
| 6 | EFRAG **Knowledge Hub** — *Historical Documents* | 1/2 | **Retrieved** — version/legal-effect statements obtained; E1 text is an interactive app only |
| 7 | EFRAG Knowledge Hub `2023 ESRS` / `interactive` paths; EFRAG Q&A platform | 1/2 | **Blocked** — HTTP 404 / no static text |
| 8 | gov.uk — **DESNZ**, *SECR regulations: evaluation* (pub. 29 Jan 2026, upd. 6 Aug 2026) — **content API** | 1/2 | **SECR in-scope categories obtained** |
| 9 | gov.uk — **DfE**, *SECR for academy trusts* (upd. 12 Aug 2026) — page + **content API** | 1/2 | **40,000 kWh de minimis + disclosure table obtained** |
| 10 | gov.uk — **HMRC** ESM10006 (upd. 22 Jul 2026) | 1/2 | **CA 2006 size test + two-year rule** |
| 11 | gov.uk — **HMRC** ESM10006A (upd. 22 Jul 2026) | 1/2 | **6 April 2025 threshold change obtained** |
| 12 | gov.uk — *Non-financial reporting review: simpler corporate reporting* (14 Oct 2024); *Modernising corporate reporting* (7 Sep 2026); gov.uk news (6 Sep 2026) | 1/2 | **UK thresholds in active reform** (watch item) |
| 13 | gov.uk — DESNZ **SECR 2018 post-implementation review** (26 May 2026) page + PDF | 1/2 | Page metadata + PDF confirmed; **PDF not text-extractable** |
| 14 | Irish Statute Book — **S.I. No. 336/2024** (re-read) | 1 (legislation) | Context re-confirmed; **no competent-authority designation in readable portion** |
| 15 | `iaasa.ie` — *Functions* | 1/2 (official regulator) | **IAASA's statutory roles obtained** → **G5 partially verified** |
| 16 | `enterprise.gov.ie` — *Company & Corporate Law* | 1/2 (official) | CRO/registry role; IAASA critical review context |
| 17 | `ghgprotocol.org` — *Corporate Standard* | 1 (standard owner) | **Seven Kyoto gases; Scope 2 Guidance 2015; supporting documents dated** |
| 18 | `ghgprotocol.org` — `corporate-standard-faq` | 1 | **Blocked** — HTTP 404 |

## 4. Exact evidence obtained

### 4.1 G4 — the 18 March 2026 CSRD amendment **[V] — CLOSED**

From the EUR-Lex **consolidated CSRD**, header verbatim:

```
Consolidated TEXT: 32022L2464 — EN — 18.03.2026   02022L2464 — EN — 18.03.2026 — 002.001
►B  DIRECTIVE (EU) 2022/2464 … of 14 December 2022 … (OJ L 322 16.12.2022, p. 15)
Amended by:
►M1  DIRECTIVE (EU) 2025/794 … of 14 April 2025        L 794    1    16.4.2025
►M2  DIRECTIVE (EU) 2026/470 … of 24 February 2026     L 470    1    26.2.2026
```

* **Instrument:** **Directive (EU) 2026/470 of the European Parliament and of the Council of 24 February 2026** *amending Directives 2006/43/EC, 2013/34/EU, (EU) 2022/2464 and (EU) 2024/1760 as regards certain corporate sustainability reporting requirements and certain corporate sustainability due diligence requirements* (Text with EEA relevance).
* **CELEX:** `32026L0470` · **ELI:** `http://data.europa.eu/eli/dir/2026/470/oj` · **OJ:** **L 470, p. 1, 26.2.2026** · **Adopted:** 24 February 2026.
* **Interaction with (EU) 2025/794:** **cumulative and sequential** (M1 = application-date postponement; M2 = substantive scope/simplification). The 18/03/2026 consolidation = CSRD as amended by **both**.
* **Character (recitals):** adjusts the **scope** of the CSRD ("the Commission should assess the appropriateness of the **new scope** of Directive (EU) 2022/2464 **as amended by this Directive**"); review clause incl. a possible simplified reporting regime; narrows/clarifies CSDDD (2024/1760). The act commonly described as the CSRD/CSDDD "Omnibus".
* **Residual [U]:** the 2026 act's own **entry into force / transposition deadline** and the **exact amended Article 5(2) application dates** (document body 140,673 chars; readable window truncated). **Date detail, not identity.**

### 4.2 G3 — UK SECR thresholds **[V] in scope/de minimis/2025 change; two numerics remain [U]**

| Item | Exact evidence (verbatim where quoted) | Source |
|---|---|---|
| **In-scope categories** | SECR "applies to **UK-registered quoted companies, as well as large unquoted companies and LLPs that exceed the statutory thresholds for employees, turnover and balance sheet totals**" | DESNZ, *SECR regulations: evaluation*, pub. 29 Jan 2026, upd. 6 Aug 2026 |
| **De minimis** | "The 2018 Regulations require **large unquoted companies that have consumed (in the UK), more than 40,000 kilowatt-hours (kWh) of energy in the reporting period** to include energy and carbon information within their directors' (trustees') report, for any period beginning on or after **1 April 2019**"; "**the prior year equivalent figures must also be disclosed**" | DfE, *SECR for academy trusts*, upd. 12 Aug 2026, §§4.2–4.3 |
| **Size test** | a corporate entity "will be medium or large-sized if it meets **at least two of the following criteria for two consecutive financial years**"; "Qualifying criteria for the Small Companies Regime can be found from **section 382 Companies Act 2006 onwards**" | HMRC ESM10006, upd. 22 Jul 2026 |
| **2025 threshold change** | "**From 6 April 2025, two of these three thresholds in the Companies Act increased. The changes apply to financial years beginning on or after 6 April 2025.**" For those years the medium/large thresholds are "**Turnover of more than £15 million; and Balance sheet total of more than £7.5 million. The 50-employee limit remains unchanged.**" | HMRC ESM10006A, upd. 22 Jul 2026 |
| **Disclosure content** | energy consumption (kWh); optional breakdown (gas / electricity / transport fuel); Scope 1 / Scope 2 / Scope 3 (tCO2e); total gross emissions (tCO2e); intensity ratio; quantification & reporting methodology (2019 HM Government Environmental Reporting Guidelines + **GHG Reporting Protocol – Corporate Standard** + UK conversion factors); intensity rationale; energy-efficiency measures; prior-year comparison | DfE guidance (§24.4) |
| **[U] remaining** | the **2018 Regulations' own "large company"/"large LLP" definition and exemptions**; the **exact CA 2006 s.465 medium/large numerics** at/after 6 Apr 2025; **LLP qualification conditions** | legislation.gov.uk JS-walled; official PDFs non-extractable |
| **[V] watch item** | *Non-financial reporting review: simpler corporate reporting* (14 Oct 2024) proposed **raising the medium-sized employee threshold to 500 employees**; *Modernising corporate reporting* (7 Sep 2026) + gov.uk news (6 Sep 2026) announce a further corporate-reporting overhaul | gov.uk |

### 4.3 G2 — GHG Protocol **[V] foundation; Chapter 9 [U]**

* **Seven Kyoto gases [V]:** "carbon dioxide (CO2), methane (CH4), nitrous oxide (N2O), hydrofluorocarbons (HFCs), perfluorocarbons (PFCs), sulphur hexafluoride (SF6) and nitrogen trifluoride (NF3)" — `ghgprotocol.org` *Corporate Standard*.
* The Corporate Standard "provides **requirements and guidance**" for corporate-level GHG inventories; it "focuses only on the accounting and reporting of emissions" [V].
* **Scope 2 Guidance [V]:** the standard "was updated in **2015** with the Scope 2 Guidance, which allows companies to credibly measure and report emissions from **purchased or acquired electricity, steam, heat, and cooling**".
* **Supporting documents dated [V]:** *Required gases and GWP values* — **February 2013** (252.51 KB); *Base Year Adjustments* — March 2004; *Categorizing GHG Emissions from Leased Assets* — March 2004; the published Corporate Standard PDF = **3.51 MB**; *GHG Protocol Reporting Template* — February 2017.
* **[U] still open:** the **Chapter 9 required/optional reporting lists**. Confirmed that the retrieval tooling returns **raw PDF byte-streams** (re-tested against a 562 KB gov.uk PDF), so PDF-only sources are unreadable regardless of publisher.

### 4.4 G5 — Ireland **[V] roles; formal designation [U]**

* `iaasa.ie` *Functions*, verbatim: "**The Companies Act 2014 sets out IAASA's legal responsibilities**"; "**IAASA sets the standards that govern statutory audits and sustainability assurance in Ireland**"; "**Under the EU Transparency Directive (enacted through Ireland's Transparency Regulations 2007), IAASA acts as Ireland's corporate reporting supervisor**"; "IAASA inspects the quality of the audit **and sustainability assurance** work performed by the auditors and **sustainability assurance service providers** of **Public Interest Entities (PIEs)**"; "IAASA conducts enquiries and investigations under **sections 933 and 934 of the Companies Act**".
* **S.I. 336/2024** (re-read): reg. 1 citation + **in operation 6 July 2024**; reg. 2 "Principal Act" = Companies Act 2014; regs 3–5 amend ss. 299/300/325 CA 2014; the inserted reporting content (incl. group reporting and the first-three-financial-years value-chain relief) was re-confirmed. **No competent-authority designation appeared in the readable portion.**
* `enterprise.gov.ie`: the **CRO** is "the central repository of public statutory information on Irish companies"; the page records a *Periodic Critical Review of the Irish Auditing and Accounting Supervisory Authority* (Nov 2025).
* **[U]:** the formal provision designating the CSRD/Accounting-Directive competent authority in Ireland.

### 4.5 G1 — ESRS E1 **[U] — not closed (representation blocker)**

Routes attempted and failed this task: EUR-Lex `CELEX:32023R2772` (TXT/HTML/ELI); EUR-Lex **OJ-issue HTML**; Publications Office **cellar**; EFRAG Knowledge Hub static paths (`/library/2023-esrs`, `/interactive/2023-esrs`); EFRAG Q&A platform. The EFRAG **Knowledge Hub** page *itself* was retrievable and confirms the Hub hosts the **2023 ESRS** and **2026 Revised ESRS** libraries — but the standard text is rendered only by an **interactive JS application**, with no static text or document endpoint. **No authoritative machine-readable E1 text is obtainable with the available tooling.**

## 5. Five-gap closure table

| Gap | Status | Primary source | Exact evidence | Version/date | CarbonTally impact |
|---|---|---|---|---|---|
| **G1 ESRS E1 identifiers** | **UNRESOLVED** | attempted EUR-Lex (TXT/HTML/ELI/cellar/OJ), EFRAG Hub, EFRAG Q&A | no machine-readable authoritative representation obtainable | ESRS Set 1 (EU) 2023/2772 + (EU) 2025/1416 | E1 rows stay concept-level; **E1-COV** still gated |
| **G2 GHG Ch.9** | **PARTIALLY VERIFIED** | `ghgprotocol.org` Corporate Standard | seven gases; Scope 2 Guidance 2015; Feb-2013 GWP annex; base-year appendix; Reporting Template; **Ch.9 lists PDF-only** | 2004 revised + 2015 + Feb-2013 | improves GP-GAS / GP-S2M / GP-BY; Ch.9 classification [U] |
| **G3 UK SECR thresholds** | **PARTIALLY VERIFIED** | DESNZ evaluation; DfE guidance; HMRC ESM10006/10006A | scope = quoted + large unquoted + LLPs; **>40,000 kWh**; 2-of-3 test over 2 consecutive FYs; **from 6 Apr 2025 > £15m / > £7.5m, 50 employees unchanged** | regime from 1 Apr 2019; change FY from 6 Apr 2025 | **APPL** must be date-aware |
| **G4 18 Mar 2026 CSRD amendment** | **VERIFIED** | EUR-Lex consolidated `02022L2464-20260318`; `32026L0470` | **►M2 Directive (EU) 2026/470 of 24 Feb 2026 — OJ L 470, 1, 26.2.2026** | act 24 Feb 2026; OJ 26 Feb 2026; consolidation 18 Mar 2026 | CSRD = **three-act chain**; amended scope governs |
| **G5 Irish competent authority** | **PARTIALLY VERIFIED** | `iaasa.ie`; S.I. 336/2024; `enterprise.gov.ie` | IAASA = Ireland's corporate reporting supervisor + sustainability-assurance oversight (CA 2014; ss.933/934) | functions 2026; SI in force 6 Jul 2024 | **regulatory context only** |

## 6. ESRS E1 findings

**Status: UNRESOLVED.** No E1 disclosure identifier or official title could be transcribed from an authoritative source in this task.

* **What is certain [V]:** the applicable ESRS are **Set 1 = Commission Delegated Regulation (EU) 2023/2772** (OJ L, 22.12.2023), **as amended by (EU) 2025/1416** (OJ 10.11.2025); the standards are organised into **ESRS 2 (general disclosures)** and topical standards **E1–E5 / S1–S4 / G1**, each comprising numbered **disclosure requirements** with **datapoints**.
* **What is NOT established [U]:** the exact identifiers/titles (e.g. `E1-1`…`E1-9`) and each one's requirement summary, applicability, quantitative/qualitative classification and datapoint content, along with the **ESRS 2** items E1 relies on.
* **Consequence for the D7-R scope:** the conceptual set named in the task (transition plan; policies; actions/resources; energy consumption and mix; gross Scope 1; gross Scope 2 location-based; gross Scope 2 market-based; gross Scope 3; significant Scope 3 categories; total GHG emissions; GHG intensity; targets; methodology) remains the **operative concept-level scope in §9.4**, but it **cannot yet be re-keyed to official identifiers**.
* **Explicitly outside CarbonTally's initial domain / requiring external or customer inputs (concept level, unchanged):** financial-effects/monetary datapoints, anticipated financial effects, and any datapoint requiring the customer to supply its own policy text, targets, transition-plan narrative, internal carbon price, or assured third-party data. None of these may be generated by CarbonTally.
* **Closing action:** transcribe **Annex I, ESRS E1** directly from the OJ PDF/printed OJ or from EFRAG's published ESRS E1 document using a reader or a PDF/text-rendering tool, then re-key the §9.4 rows and record required/conditional status.

## 7. ESRS 2026 revision — legal status (adoption ≠ applicability)

| # | Determination | Finding |
|---|---|---|
| 1 | Adoption date | **3 July 2026** (Commission adopted the Revised/Simplified ESRS delegated act) |
| 2 | OJ publication | **Not established** in the sources read |
| 3 | Scrutiny | Delegated-act due process pending; EFRAG: the EC "will provide a delegated act on simplified ESRS following its due process" |
| 4 | Entry into force | **Not in force** as of the task date |
| 5 | Application date | **None in effect** |
| 6 | Legally applicable now? | **No** — the 2023 set (as amended by (EU) 2025/1416) governs |
| 7 | Must CarbonTally implement it now? | **No** — EFRAG states "**Only the delegated act applies directly to companies in the scope of the amended CSRD**" |
| 8 | D14/D15 implication | A **first-class framework-version transition**: bind outputs to the version in force at the reporting date; a future version is a **new version**, never an in-place edit |

* **Future-version identifiers:** deliberately **not recorded** — none were obtainable (§6), and none are invented.
* The 2026 revision is **not** substituted for the applicable ESRS model anywhere in the regulatory report.
* EFRAG Hub wording "companies in the scope of the **amended CSRD**" is an **independent corroboration** of the G4 finding.

## 8. GHG Protocol findings

* **[V]** The Corporate Standard "provides **requirements and guidance**"; it is the authoritative corporate-level inventory standard and "focuses only on the accounting and reporting of emissions".
* **[V]** Seven Kyoto gases: CO2, CH4, N2O, HFCs, PFCs, SF6, NF3.
* **[V]** Companion guidance: **Scope 2 Guidance (2015)** (purchased/acquired electricity, steam, heat, cooling); **Scope 3 Standard** and **Scope 3 Calculation Guidance** are the value-chain companions.
* **[V]** Dated supporting materials: **Required gases and GWP values — February 2013**; **Base Year Adjustments — March 2004**; **Categorizing GHG Emissions from Leased Assets — March 2004**; Corporate Standard PDF 3.51 MB; Reporting Template February 2017.
* **[U]** The **Chapter 9 "Reporting GHG Emissions" required vs optional corporate-report information** (organisational/operational boundaries, reporting period, Scope 1/2/3, gases, CO2e, base year, recalculation, exclusions, changes and their causes, inventory quality, uncertainty, sequestration/biogenic information, methodologies, facilities/organisational coverage, comparative information) could **not** be read, because Chapter 9 exists only as a binary PDF.
* **Rule preserved:** **no optional GHG Protocol content is converted into mandatory functionality** without the Chapter 9 text.

## 9. UK SECR threshold findings

* **Three in-scope populations [V]:** UK-registered **quoted** companies; **large unquoted** companies; **LLPs** — the latter two "that exceed the statutory thresholds for employees, turnover and balance sheet totals" (DESNZ).
* **De minimis [V]:** **more than 40,000 kWh** of UK energy consumption in the reporting period, for **large unquoted companies**; applies to periods **beginning on or after 1 April 2019**; prior-year figures required.
* **Size test [V]:** the CA 2006 test is **2 of 3** (turnover; balance-sheet total; average employees) satisfied **for two consecutive financial years**; small-companies criteria are at **CA 2006 s.382 onwards**.
* **Threshold change [V]:** **from 6 April 2025**, for financial years **beginning on or after that date**, the medium/large thresholds are **turnover > £15,000,000** and **balance sheet total > £7,500,000**, with the **50-employee limit unchanged** (the pre-change values cited by HMRC are turnover > £10.2m and balance sheet > £5.1m).
* **[U] not verified:** the 2018 Regulations' own "large company"/"large LLP" definition, their exemptions, and the **exact CA 2006 s.465 medium/large numerics** at/after 6 Apr 2025 (only the "not small" boundary is stated by HMRC).
* **Reform context [V]:** the medium-sized employee threshold may itself change (consultation proposed **500 employees**, 14 Oct 2024), and a broader corporate-reporting overhaul is in progress (Sep 2026). **Thresholds must be treated as versioned, date-aware data — never constants.**

## 10. EU CSRD amendment findings

* **The 18 March 2026 change is Directive (EU) 2026/470 of 24 February 2026** (OJ **L 470**, p. 1, **26.2.2026**; CELEX **32026L0470**), amending **2006/43/EC, 2013/34/EU, 2022/2464 and 2024/1760** as regards certain corporate sustainability reporting and due diligence requirements.
* **Chain [V]:** CSRD = **Directive (EU) 2022/2464** (OJ L 322, 16.12.2022, p. 15) **+ Directive (EU) 2025/794** (OJ L 794, 1, 16.4.2025 — ►M1) **+ Directive (EU) 2026/470** (OJ L 470, 1, 26.2.2026 — ►M2). The consolidation state **18.03.2026** incorporates both amendments.
* **Effect [V, from recitals]:** the 2026 act **adjusts the scope** of the CSRD (with a Commission review of "the **new scope** … as amended by this Directive", incl. consideration of a simplified reporting regime) and narrows/clarifies CSDDD scope. Commonly described as the CSRD/CSDDD "Omnibus".
* **[U] detail:** the 2026 act's own entry into force/transposition deadline and the amended **Article 5(2)** application dates were not transcribed.
* **Mandatory distinction preserved:** this is the **EU legal requirement**. CarbonTally's **product applicability logic** records the framework version and presents the amended scope; it does **not** assert any customer's legal status (D13).

## 11. Ireland — competent-authority findings

* **[V]** IAASA is, per its own official statement, the body whose "legal responsibilities" are set by the **Companies Act 2014**, and it: sets the standards governing **statutory audits and sustainability assurance**; acts as **Ireland's corporate reporting supervisor** (EU Transparency Directive via the Transparency Regulations 2007); inspects audit **and sustainability-assurance** quality of auditors and **sustainability assurance service providers of PIEs**; and enforces under **ss.933/934 CA 2014**.
* **[V]** The **CRO** is the central statutory repository; the **Corporate Enforcement Authority** exists as the company-law enforcement body (DETE).
* **[U]** The **formal CSRD competent-authority designation provision** was not located (the readable portion of S.I. 336/2024 contains none; the source was truncated).
* **Impact:** **regulatory context only** — no CarbonTally product requirement, and **no legal determination for any individual customer**.

## 12. Changes to the regulatory matrix

| Matrix item | Previous position | Change in this task |
|---|---|---|
| **CSRD framework chain** (§9.0) | 2022/2464 + 2025/794 (two acts) | **Now three acts** — **+ Directive (EU) 2026/470** (amended scope) → **[V]** |
| **CSRD applicability inputs** | "phase-in dates" only | **Scope and timing are version/date dependent**; the amended (narrower) scope governs → **[V]** |
| **SECR scope** | "large unquoted companies" / definition by reference | **Three populations [V]**, **de minimis 40,000 kWh [V]**, **2-of-3 two-consecutive-FY test [V]** |
| **SECR thresholds** | unverified numerics | **£10.2m / £5.1m pre-change → > £15m / > £7.5m, 50 employees unchanged, from FY beginning on/after 6 Apr 2025 [V]**; s.465 "large" numerics remain **[U]** |
| **SECR reform exposure** | not recorded | **New watch item [V]** (possible 500-employee medium threshold; Sep-2026 overhaul) |
| **GHG gases / companions** | [V] framework only | **Seven-gas list [V]**, **Scope 2 Guidance 2015 [V]**, **Feb-2013 GWP annex + 2004 base-year appendix identified [V]** |
| **GHG Chapter 9** | [U] | **[U] unchanged** (PDF-only) |
| **ESRS legal version** | [V] | **[V] confirmed**, with the delegated-act-only-applies rule stated by EFRAG |
| **ESRS E1 identifiers** | [U] | **[U] unchanged** (representation blocker) |
| **Ireland** | transposition [V]; authority [U] | **IAASA roles [V]**; formal designation **[U]** |

**No row was upgraded without a cited authoritative source; no row was upgraded on the basis of memory or a secondary summary.**

## 13. D1–D17 impact

**No D1–D17 contradiction identified.**

* **Strengthened:** D1; D8/D9 (GHG foundation); D10/D11 (SECR scope, de minimis, date-aware thresholds, disclosure elements); D12/D13 (ESRS + applicability, no customer legal determination); D14/D15 (the live 2023→2026 ESRS transition and the CSRD three-act chain); D16 (untouched); D17 (source hierarchy applied throughout).
* **Increased urgency, no change of decision:** **D14/D15** (version binding is now concretely necessary) and **D10/D11** (UK thresholds are date-dependent and in active reform).
* **No PO decision is contradicted**, and **no implementation was performed** as a result of this task.

## 14. 13 PO-decision status

| # | Decision | Evidence now permits PO decision? | Further evidence needed? | Nature |
|---|---|---|---|---|
| **A1** | Narrative field allowlist | Yes | No | Product/UX policy |
| **A3** | Narrative numeric limits | Yes | No | Product policy |
| **P3** | Customer-editable sections/fields | Yes | No | Product/UX policy |
| **D11-CAT** | SECR intensity denominator catalogue | Yes | No (not prescribed by the Regulations) | Product policy |
| **E1-COV** | Initial ESRS E1 coverage | **Not at identifier level** | **Yes — G1 must close first** (or PO accepts §9.4 concept set) | Regulatory fact + product policy |
| **E1-VER** | ESRS version to launch with | Yes (law is settled) | No | Product policy |
| **APPL** | Applicability-capture model | Yes (model) | No for the model; residual [U] items affect presentation precision only | Product policy |
| **GP-CONS** | Consolidation approach | Yes | No | Product policy |
| **GP-GAS** | CO2e-only vs per-gas | Yes (seven-gas list [V]) | No | Product policy |
| **GP-S2M** | Market-based Scope 2 | Yes (2015 Scope 2 Guidance [V]) | No for the decision | Product policy |
| **GP-S3** | Scope 3 in initial build | Yes | No | Product policy |
| **GP-BY** | Base year + recalculation | Yes (2004 appendix [V]) | No for the decision | Product policy |
| **LEG** | D16 legacy-route disposition | Yes | No | Product/architecture policy |

**Result: 12 of 13 are permission-ready and are policy, not regulatory-fact, matters. Only `E1-COV` still depends on a regulatory fact (`G1`).** No decision was made here.

## 15. Remaining unresolved questions

| # | Question | Kind | Closing action |
|---|---|---|---|
| 1 | **ESRS E1 exact disclosure identifiers/titles + required/conditional status (and the ESRS 2 items E1 uses)** | Regulatory fact | Transcribe Annex I, ESRS E1 from the OJ PDF/printed OJ or EFRAG's ESRS E1 document with a PDF/text reader |
| 2 | **GHG Protocol Chapter 9 required vs optional report information** | Regulatory fact | Read the Corporate Standard PDF Ch. 9 (+ its annexes) with a PDF reader |
| 3 | **The 2018 Regulations' own "large company"/"large LLP" definition, exemptions and the CA 2006 s.465 numerics** | Regulatory fact | Read SI 2018/1155 / CA 2006 s.465 directly (legislation.gov.uk in a browser, or the published SI) |
| 4 | **Directive (EU) 2026/470's own entry into force/transposition deadline and amended Article 5(2) dates** | Regulatory fact (detail) | Read the 2026 act's Articles in a browser |
| 5 | **Ireland's formal CSRD competent-authority designation** | Regulatory fact (context) | Read S.I. 336/2024 (and CA 2014 provisions) in full |
| 6 | **Whether the 2026 Simplified ESRS has been published in the OJ / entered into force** | Regulatory fact (forward-looking) | Monitor EUR-Lex/OJ; do not implement ahead of legal effect |

## 16. Implementation-readiness assessment

* **Gate 1 — Regulatory evidence:** **PARTIAL — NOT CLOSED.** G4 closed; G2/G3/G5 partially verified; **G1 open**.
* **Gate 2 — Requirement matrix:** **produced and improved**; E1 rows still concept-level.
* **Gate 3 — PO review:** **PENDING** (12 of 13 decisions now permission-ready).
* **Gate 4 — Disclosure-model design:** **NOT AUTHORIZED** (may be requested; conditions in §16 Q3 below).
* **Gate 5 — Implementation:** **NOT AUTHORIZED.**

**Q1 — Sufficient basis for Disclosure Model design?** Substantially yes, **except ESRS E1 identifier-level coverage**. All framework identities/versions/statuses are [V]; SECR scope/de minimis/2025 thresholds [V]; SECR content [V]; CSRD chain [V].
**Q2 — Are remaining gaps regulatory facts or PO/product decisions?** **Both, cleanly separable** — five regulatory-fact residuals (§15) and 12 policy decisions (§14).
**Q3 — Can the next task be a Disclosure Model design task?** **Yes, for PO review + concept/architectural design**, subject to (a) closing `G1` **or** the PO ratifying coverage against the §9.4 concept-level E1 set, and (b) including a **framework-version model** (D14/D15).
**Q4 — Remaining primary-source blockers?** **Yes — five (§15 items 1–5), all representation/tooling blockers**, solvable by a human reader or a PDF/text-rendering tool, **not** by further searching.

**No implementation readiness is claimed.**

## 17. Files changed / created, database, code, security

**Files changed (1):**

* `docs/architecture/CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md`
  * added **§24** (evidence completion: §24.1 five-gap table, §24.2–24.6 per-gap findings, §24.7 ESRS 2026 status, §24.8 D1–D17, §24.9 PO inventory, §24.10 readiness test, §24.11 verdict);
  * added a **navigation pointer** to §24 in §22's supersession note and updated the §1 document-control verdict row to point to §24.11 while retaining the earlier verdicts;
  * **§§5–23 retained unchanged** — no earlier finding was deleted or silently rewritten.

**Files created (1):**

* `docs/cline/reports/CT-P8-REPORTING-REGULATORY-EVIDENCE-COMPLETION-20260912-003.md` (this report).

**Database status:** **NO CHANGE.** No migration, no DDL/DML, no schema/table/column/index/policy change, no data touched.

**Code status:** **NO CHANGE.** No backend, frontend, route, service, template, report-generation, calculation, extraction, narrative or rules-engine change.

**Security / RLS status:** **NO CHANGE.** No RLS policy, grant, role, permission, auth or storage change; no secrets, credentials, tokens or signed URLs were accessed, produced or recorded.

## 18. Tests / checks performed

* Document-structure verification of the edited architecture report (section headings and new §24 subsections present; §§5–23 intact).
* Consistency check that every new **VERIFIED** classification is backed by an explicitly cited authoritative source and that nothing was upgraded without one.
* Confirmation that G1 is reported **UNRESOLVED** (not silently omitted or assumed).
* Re-confirmation of the PDF non-extractability limitation against a second, independent official PDF.
* No application tests were run **because no application code was changed**.

## 19. Git status / worktree status / commit status / push status

**Recorded before starting:**

| Item | Value |
|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| Branch | `main` |
| Staged files | **0** |
| Modified files | **208** (all pre-existing) |
| Untracked entries | **60** (collapsed; **759** with `--untracked-files=all`) |

**Recorded after completion:**

| Item | Value |
|---|---|
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` — **unchanged** |
| Branch | `main` — **unchanged** |
| Staged files | **0** — unchanged |
| Modified files | **208** — unchanged (no new modified entry created) |
| Untracked entries | **60** collapsed (our new report lands inside the already-untracked `docs/cline/reports/` directory) |
| Branch position | `main…origin/main` — **ahead 14** (unchanged) |

**Only the two permitted documentation artefacts were touched:**

| Path | Git state | Change |
|---|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md` | **untracked** (`??`) | **additive**: 696 → **866** lines (+170); `##` section count **24** (§1–§24); **§22 (line 542) and §23 (line 556) preserved verbatim**; only §24, the §22 pointer and the §1 verdict row were added/updated |
| `docs/cline/reports/CT-P8-REPORTING-REGULATORY-EVIDENCE-COMPLETION-20260912-003.md` | **untracked** (`??`, new file) | created (this report) |

**Pre-existing work integrity:**

* Neither document appears in `git diff --name-only` (they are untracked, so no tracked file was modified by this task).
* No pre-existing working-tree change was overwritten, stashed, reverted or staged.
* No code, schema, migration, RLS, route, template or production file was touched.

**Commit status:** **NO COMMIT.** **Push status:** **NO PUSH.** No `reset`, `stash`, `clean`, `rebase`, `amend` or force-push was performed. No `.env`, credential, key, token, JWT, demo credential or signed URL was read, created or recorded.

## 20. Final verdict

### `EVIDENCE CLOSURE PARTIAL — PO REVIEW REQUIRED`

**Conclusively closed:** **G4 — the 18 March 2026 CSRD amendment**, identified and verified as **Directive (EU) 2026/470 of 24 February 2026** (OJ **L 470**, p. 1, **26.2.2026**; CELEX **32026L0470**), consolidating with **Directive (EU) 2025/794** into the CSRD text of **18/03/2026** — plus a separately verified statement of the **ESRS 2026-revision legal status** (adopted 3 July 2026; **not in force**; only an adopted delegated act applies).

**Materially advanced:** **G3 UK SECR** (three in-scope populations; **>40,000 kWh** de minimis; CA 2006 2-of-3 test over two consecutive financial years; **from 6 April 2025 turnover > £15m / balance sheet > £7.5m with the 50-employee limit unchanged**); **G2 GHG Protocol** (seven Kyoto gases; Scope 2 Guidance 2015; Feb-2013 GWP annex; 2004 base-year appendix; Reporting Template); **G5 Ireland** (IAASA's statutory corporate-reporting-supervision and sustainability-assurance roles).

**Not closed:** **G1 — ESRS E1 exact disclosure identifiers/titles** (a representation/tooling blocker, not a source-availability blocker), which is the single item still gating the **`E1-COV`** PO decision; plus four **detail** residuals that do not gate design.

**Why not "COMPLETE":** the task's own rule is that the COMPLETE verdict applies only if **all five** gaps are conclusively resolved. **G1 is UNRESOLVED** and G2/G3/G5 retain unread detail, so the honest verdict remains **PARTIAL**. **No implementation readiness is claimed**, and no "ready for implementation" language is used.

**Mandatory stop condition observed:** this task stopped after updating the two documentation reports. It did **not** proceed to Disclosure Model design/implementation, database or schema work, S4, legacy-route disposition, RLS remediation, or Phase 8-X. **PO review and explicit authorization are required before any further work.**







