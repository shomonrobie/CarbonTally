# CT-STEP2-FACTOR-SELECTION-POLICY-EVIDENCE-037

**Role:** Cline, forensic/evidence analyst. **READ-ONLY policy-evidence task** — no implementation, no code,
test, configuration, schema, migration or factor-data change, no deployment, no P1 activation, no matching
behaviour change. All database inspection was read-only (session forced
`SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`).

```text
BASELINE (D-A closure):  6174572d9c2d782493657670597e749a68717856
ACTUAL HEAD AT ANALYSIS: 6174572d9c2d782493657670597e749a68717856   (identical)
BRANCH:                  p8-release-reconciled
WORKING TREE AT START:   CLEAN (git status --porcelain → empty)
D-A STATUS:              PO-CLOSED — not reopened by this task.
```

---

## 1. EXECUTIVE SUMMARY

* D-A is closed and is **not** in scope here. The open question is **what CarbonTally should do when several
  authoritative factors are technically compatible with one extracted activity**.
* The evidence shows the problem is real, reproduced, and **data-rooted, not matcher-rooted**:
  * `Natural gas … [kWh (Net CV)]` alone offers **7 distinct concepts** (aggregates, gas components,
    blend variants, WTT) — see §6.
  * The **aggregate factor equals the sum of its gas components** — verified arithmetically for six
    independent families (`0.18259+0.00028+0.00009 = 0.18296`; `0.20229+0.00031+0.00010 = 0.20270`;
    `0.18457+0.00028+0.00009 = 0.18494`; `0.20448+0.00031+0.00010 = 0.20489`; diesel
    `2.62818+0.00029+0.03308 = 2.66155`; waste oils `2.70801+0.00302+0.03820 = 2.74924`).
    Selecting a component alone understates emissions by ~99 % for that activity.
  * **WTT is structurally separable in the data**: all **656** `WTT- …` factors are **Scope 3**; combustion
    fuel factors are Scope 1. Scope is populated, so it is usable as a *semantic* dimension.
  * **Treatment route is already encoded** for waste: `Waste disposal > …` = **134 activity names, all
    Scope 3**, route as name suffix (`- Landfill`, `- Closed-loop`, `- Open-loop`,
    `- Incineration with Energy Recovery`, `- Composting`). The `Fuels > Liquid fuels > Waste oils` family
    that currently absorbs a "Waste disposal" row is a **Scope 1 fuel**, not a disposal route.
* The factor model carries **no** category / methodology / gas / WTT / treatment / metric columns. Every
  semantic distinction lives in the **`activity_type` string** (taxonomy prefix + name markers), plus
  **`scope`**, **`unit`**, **`factor_set`/`factor_source`**, **`country`**, **`reporting_year`**.
* The existing `_prefer_aggregate_factor` mechanism is **partially sufficient**: it repairs
  *component → aggregate within the same name family* by a four-marker name test, but it cannot see scope,
  WTT, treatment route, jurisdiction or conflicting concepts, and it takes the *first* non-component
  candidate in repository order (§10).
* **Recommendation:** the smallest bounded policy is a deterministic, name-marker + `scope` **semantic
  guard** applied on the existing candidate list — no new engine, no new factor store, no new provenance
  system, no schema change (§13).

## 2. D-A FOLLOW-UP OBSERVATIONS (recorded, unchanged, not re-opened)

| ID | Observation | Evidence status in this task |
|---|---|---|
| `F-DA-1` | Row 1 selected the **CH4 component** `0.00031` instead of the aggregate `0.20270` | **Confirmed**; aggregate = component sum, so the component understates by ~99 % (§6) |
| `F-DA-2` | Explicit Net-CV prose reached the **WTT** factor `0.03347` | **Confirmed**; WTT is Scope 3 upstream — a materially different concept, not a combustion substitute (§6) |
| `F-DA-3` | **Scope 1 and Scope 3** can share activity/unit/basis | **Confirmed**; 4 distinct scope values exist; WTT = 100 % Scope 3 (§5) |
| `F-DA-4` | Other materially different concepts can share activity/unit/basis | **Confirmed and extended**; diesel has ≥5 concept families, waste ≥2 (§7, §8) |
| `F-DA-5` | Factor count 7,029 (earlier) vs 7,049 (verification env) | **RESOLVED — not stale, not duplicates:** `DEFRA-2025 = 7,029` + `SEAI-2025 = 20` = **7,049**; all rows `reporting_year = 2025`; **zero duplicate natural keys** `(year, activity, country, unit, scope)`. The earlier figure was a DEFRA-only query scope (§11) |

## 3. INDUSTRY / AUTHORITATIVE EVIDENCE — AND ITS LIMITS (honest status)

**Retrieved (authoritative, DESNZ publication page for the 2025 factors):** the release contains three sets
— *"condensed set: this abridged version of the full set is easiest to navigate and most frequently
requested. **Recommended for most, and new, users of conversion factors**"*, *"full set: contains all
available factors for the selected year. Recommended for advanced users only"*, *"flat file … designed for
use in automated processes"* — with the instruction *"Regular users: read the 'what's new' sheet … this will
ensure **consistent and comparable reporting year-on-year**"*, and *"**The methodology paper explains how
the conversion factors are derived.**"*

```text
AUTHORITATIVE REQUIREMENT (quoted above):
  · factors are published per year; the correct year's set must be used for year-on-year comparability;
  · the condensed set is the recommended default for ordinary users; the full set is for advanced users;
  · a published methodology paper exists and explains derivation.

NOT RETRIEVED — SPECIFIC EVIDENCE GAP (see verdict):
  · the substantive rule text on "aggregate kg CO2e vs individual gas components", on combustion-vs-WTT
    additivity/scope, and on SEAI factor selection lives in Excel workbooks / a 157-page methodology PDF;
  · the live GHG Protocol and SEAI pages returned HTTP 403 to this environment.
  ⇒ No claim in this report asserts that an external standard MANDATES a CarbonTally rule.
```

**Labelling used throughout:**

```text
AUTHORITATIVE REQUIREMENT  — stated in a source actually retrieved, quoted
AUTHORITATIVE DATA         — the published factor set itself, as loaded in the dataset
AUTHORITATIVE METHODOLOGY  — source exists; its text was NOT read in this window
RECOMMENDED PRACTICE       — inference from the structure of the published data
CARBONTALLY PRODUCT POLICY — a CarbonTally product choice; NOT an external mandate
```

## 4. CARBONTALLY CURRENT MATCHING ARCHITECTURE (traced, unchanged)

```text
MatchRequest (domain/matching.py) : id · activity · country · reporting_year · unit · scope ·
                                    organization_id · preferred_provider · max_stages
Stage order (default config)      : exact_match → natural_key → alias_match → keyword_search → fuzzy_match
                                    (semantic_match exists but is not in the default stage tuple)
Short-circuit                     : the FIRST stage reporting matched=True wins (factor_matching.py);
                                    D-A adds a post-stage `calorific_basis` step after the loop, before
                                    no_match — an ADDITIONAL path, not a reordering of the staged flow
Candidate generation              : index.keyword_search(activity, *, unit, country, provider, limit)
                                    → list[(EmissionFactor, score)] — the ONLY rank signal is `score`;
                                    no scope/category/method rank metadata exists
Filtering                         : unit is STRICT (verified: unit="kWh" → [] for the same activity);
                                    country strict; provider optional
Ranking / ties                    : per-stage confidence; a stage reporting score>=1.0 without matched
                                    yields status="ambiguous" + suggestions; otherwise the first matched
                                    stage decides — STAGE ORDER is the de-facto priority
SCOPE                             : available on MatchRequest and on every factor, but NO stage filters or
                                    ranks on it; the matched factor's scope flows through as data only
SOURCE / FACTOR SET / YEAR        : country + provider are query filters; factor_set and reporting_year are
                                    carried on the factor; natural key shape is
                                    (year, activity, country, unit, scope)
Aggregate vs component            : NOT modelled; encoded only as a NAME marker
                                    ("… of CH4 per unit", "of CO2 per unit", "of N2O per unit")
Combustion vs WTT / treatment     : NOT modelled; encoded only in the activity_type prefix/suffix
                                    ("WTT- …", "Waste disposal > … - Landfill")
Definitive vs non-definitive      : StageResult.is_definitive exists; exact/natural-key are deterministic
```

## 5. FACTOR METADATA INVENTORY (what actually exists)

```text
DATABASE TABLE public.emission_factors — 13 columns, complete list:
  id (uuid) · reporting_year (int) · activity_type (varchar) · co2e_multiplier (numeric) ·
  created_at · updated_at · unit (text) · scope (text) · factor_source (text) · factor_set (text) ·
  country (varchar) · region_deprecated (varchar) · import_batch_id (uuid)

DOMAIN OBJECT the matcher sees — 12 dataclass fields, complete list:
  id · reporting_year · activity_type · co2e_multiplier · unit · scope · factor_source · factor_set ·
  country · provider_key (DERIVED — not a DB column) · natural_key · import_batch_id

ABSENT (verified against the column list — not inferred): category · methodology · gas/component flag ·
  aggregate flag · WTT/combustion flag · treatment route · metric (CO2 vs CO2e) · supplier-specific flag ·
  supersedes/version link · ranking weight

Consequences:
  · a distinction is only available to the matcher if it appears in the activity_type STRING, in `unit`,
    in `scope`, in `factor_set`/`factor_source`, or in `country`/`reporting_year`;
  · `provider_key` is derived from factor_source, so "supplier-specific vs generic" is not a stored
    dimension (customer-specific factors live in the separate `customer_factors` table and take
    precedence ahead of the pipeline — D-cf-5);
  · reporting_year is 2025 for ALL 7,049 rows — no cross-year ambiguity exists today, but the
    dimension is real for future imports (the DESNZ requirement in §3 is about exactly this).

Scope distribution (whole dataset): Scope 3 = 4,090 · Scope 1 = 2,549 · Scope 2 = 354 ·
  Outside of Scopes = 56      → the `scope` field is populated and 4-valued; usable as a semantic filter.
Factor sets: DEFRA-2025 = 7,029 (GB) · SEAI-2025 = 20 (IE).
Duplicate natural keys (year, activity, country, unit, scope): NONE.
```

## 6. NATURAL GAS CASE STUDY (real DEFRA-2025 data, GB, Scope 1 unless stated)

```text
unit 'kWh (Gross CV)' — combustion, Scope 1
  Fuels > Gaseous fuels > Natural gas (kg CO2e)                      0.18296  AGGREGATE (taxonomy: plain)
  Fuels > Gaseous fuels > Natural gas (kg CO2e of CO2 per unit)      0.18259  component
  Fuels > Gaseous fuels > Natural gas (kg CO2e of CH4 per unit)      0.00028  component
  Fuels > Gaseous fuels > Natural gas (kg CO2e of N2O per unit)      0.00009  component
  100% mineral blend variants (aggregate 0.18494, CO2 0.18457, CH4 0.00028, N2O 0.00009)
  WTT- fuels > Gaseous fuels > Natural gas (kg CO2e)                 0.03021  ← Scope 3, upstream
  WTT- fuels > … (100% mineral blend) (kg CO2e)                      0.03021  ← Scope 3, upstream

unit 'kWh (Net CV)' — combustion, Scope 1
  Fuels > Gaseous fuels > Natural gas (kg CO2e)                      0.20270  AGGREGATE
  Fuels > Gaseous fuels > Natural gas (kg CO2e of CO2 per unit)      0.20229  component
  Fuels > Gaseous fuels > Natural gas (kg CO2e of CH4 per unit)      0.00031  component  ← selected by D-A row 1
  Fuels > Gaseous fuels > Natural gas (kg CO2e of N2O per unit)      0.00010  component
  100% mineral blend variants (aggregate 0.20489, CO2 0.20448, CH4 0.00031, N2O 0.00010)
  WTT- fuels > Gaseous fuels > Natural gas (kg CO2e)                 0.03347  ← Scope 3, upstream
  WTT- fuels > … (100% mineral blend) (kg CO2e)                      0.03347  ← Scope 3, upstream

other unit (same concept set): 'cubic metres' — 100% mineral blend CO2 2.08504 · CH4 0.00307 ·
  N2O 0.00095 · aggregate ≈ 2.08906 ; and the SEAI variant: 'Natural gas (NCV) (kg CO2) [cubic metres]'
  2.005357, Scope 1, SEAI-2025/IE — note the metric is CO2, not CO2e.

ARITHMETIC PROOF THAT AGGREGATE = Σ COMPONENTS (all four Gas-CV cases):
  0.18259 + 0.00028 + 0.00009 = 0.18296 ✓   0.18457 + 0.00028 + 0.00009 = 0.18494 ✓
  0.20229 + 0.00031 + 0.00010 = 0.20270 ✓   0.20448 + 0.00031 + 0.00010 = 0.20489 ✓
⇒ A component factor is a PARTIAL emissions total. Selecting one (D-A row 1 behaviour) omits ~99 % of the
  activity's emissions for that unit (0.00031 vs 0.20270).

WHAT DISTINGUISHES THE CONCEPTS (all available, no new metadata needed):
  aggregate vs component → the "… of CH4/CO2/N2O per unit" name marker (and: aggregate == component sum)
  combustion vs WTT      → the 'WTT- fuels >' name prefix AND scope (WTT is Scope 3, combustion Scope 1)
  blend variants         → the '(100% mineral blend)' name fragment
  basis                  → the unit qualifier '(Gross CV)' / '(Net CV)' — resolved by D-A
  country/metric         → `country` (GB/IE) and `factor_source` (DEFRA-DESNZ / SEAI), plus 'kg CO2e'
                           vs 'kg CO2' in the name
```

## 7. DIESEL CASE STUDY (real DEFRA/SEAI data)

```text
'%diesel%' in GB = 2,405 rows (the term spans fuels, vehicles and business travel).
Distinct concept families relevant to a fuel-purchase line:
  Fuels > Liquid fuels > Diesel (100% mineral diesel)  [litres]  aggregate 2.66155 (CO2 2.62818 + CH4
        0.00029 + N2O 0.03308)  Scope 1  ← the mineral-diesel combustion concept
  Fuels > Liquid fuels > Diesel (average biofuel blend) [litres] Scope 1  ← blend variant
  Bioenergy > Biofuel > Development diesel (kg CO2e) [litres] 0.03705 Scope 1  ← BIOFUEL/development fuel
  Bioenergy > Biofuel > Biodiesel HVO / Biodiesel ME / Off road biodiesel [litres, kg, GJ] Scope 1
  Business travel- land > Cars (by market segment) > … - Diesel [km, miles] Scope 3  ← travel activity,
        per-distance, not a fuel quantity
  WTT variants exist for the fuel families (Scope 3), e.g. waste-oils WTT (§8)
SEAI-2025 (IE): Fuels > Liquid fuels > Diesel / gasoil (100% petroleum) (kg CO2) [litres] 2.682327
        and Road diesel (avg. biofuel content) (kg CO2) [litres] 2.410411 — same concept split, different
        jurisdiction (country='IE'), different metric (CO2).
OBSERVED (row 2 of the D-A five-row oracle): 'Diesel supply 4,434.4000 L' matched
        'Bioenergy > Biofuel > Development diesel (kg CO2e) [litres]' 0.03705 — i.e. a BIOFUEL
        development fuel, ~60× smaller than mineral diesel (2.66155). Keyword score alone cannot
        distinguish these; the taxonomy prefix ('Fuels > Liquid fuels >' vs 'Bioenergy > Biofuel >')
        and the concept words ('mineral'/'average biofuel blend') can.
```

## 8. WASTE CASE STUDY (real DEFRA data)

```text
'%waste%' in GB = 155 rows, two semantically opposite families sharing one token:
  (a) Fuels > Liquid fuels > Waste oils — a FUEL, Scope 1, 19 rows including WTT (Scope 3) variants:
        (kg CO2e) [litres] 2.74924 · [tonnes] 3219.37916 · [kWh (Gross CV)] 0.25641
        (kg CO2e of CH4 per unit) [tonnes] 3.5504   ← selected for the D-A row-3 'Waste disposal' line
        WTT- fuels > Liquid fuels > Waste oils (kg CO2e) [tonnes] 1116.83712   Scope 3
  (b) Waste disposal > … — a DISPOSAL family: 134 distinct activity names, ALL Scope 3, with the treatment
      route encoded as a NAME SUFFIX:
        Waste disposal > Construction > Aggregates - Landfill · - Closed-loop · - Open-loop
        Waste disposal > Construction > Wood - Composting
        Waste disposal > Construction > Average construction - Incineration with Energy Recovery
        Waste disposal > Construction > Soils - Landfill · Tyres - Closed-loop · Metals - Landfill …
      (further routes such as Recycling / Anaerobic digestion appear in the remaining 134 names)
  (c) Material use > Organic > Compost derived from … - Primary material production [tonnes] Scope 3
      — a third, adjacent concept (material production, not disposal)
WHY 'Waste disposal' CAN REACH 'Waste oils': keyword scoring shares the token "Waste", while the taxonomy
  prefix ('Waste disposal' vs 'Fuels > Liquid fuels') and `scope` (Scope 3 disposal vs Scope 1 fuel) are NOT
  used as filters. The dataset contains sufficient metadata to separate the families without keyword
  guessing:
    · taxonomy prefix 'Waste disposal >' vs 'Fuels > ' (string, already present)
    · scope: 134/134 Waste-disposal names are Scope 3; the Waste-oils fuel concept is Scope 1
    · treatment route as the '- …' suffix (Landfill / Closed-loop / Open-loop / Incineration with Energy
      Recovery / Composting) — present for the disposal family only
    · unit: disposal routes are per 'tonnes' at product level; the fuel is per litre/kWh/tonne of FUEL
  ⇒ D-FS-4 is answerable from existing data; no new field is strictly required (a treatment column would be
    cleaner — a PO trade-off, not a blocker).

## 9. ELECTRICITY CASE STUDY (real DEFRA + SEAI data)

```text
'%electricity%' in GB = 657 rows; the family is heterogeneous by SCOPE and by CONCEPT:
  Managed assets- electricity > Electricity generated > Electricity: UK (kg CO2e) [kWh]  Scope 3  0.17700
        (components CH4 0.0009 · CO2 0.17489 · N2O 0.00122)
  Outside of scopes > Electricity generated > Electricity: UK (kg CO2e of CO2 per unit) [kWh]
        scope='Outside of Scopes' 0.11507      ← a 4th scope value in live use
  SECR kWh UK electricity for EVs > Cars (by market segment) > … Battery Electric Vehicle / Plug-in Hybrid
        [km, miles] Scope 2   ← per-DISTANCE, not per-kWh: the unit is the discriminator
  Fuels > Solid fuels > Coal (electricity generation …)  Scope 1  ← a FUEL used to generate electricity
SEAI-2025 (IE, country='IE', factor_source='SEAI', metric kg CO2):
  Fuels > Electricity > Electricity consumption (kg CO2) [kWh]   Scope 2  0.19780338
  Fuels > Electricity > Gross electricity supply (kg CO2) [kWh]  Scope 2  0.17832767
        ← consumption vs supply is a NAME-level distinction only; both Scope 2, same unit
WHAT DISTINGUISHES THEM: `scope` (2 vs 3 vs Outside of Scopes), `unit` (kWh vs km vs miles vs tonnes), the
  taxonomy prefix, `country`, and the name words 'generated'/'consumption'/'supply'. D-B (electricity
  policy) is NOT implemented or pre-judged here.
```

## 10. EXISTING `_prefer_aggregate_factor` — ANALYSIS

```text
LOCATION   services/automatic_processing.py:1414 (defined); called at :1256 (mapping stage, service layer)
SIGNATURE  async def _prefer_aggregate_factor(self, activity: str, unit: Optional[str], result)
WHAT IT CALLS "AGGREGATE"
  the four markers ("of CH4 per unit", "of N2O per unit", "of CO2 per unit", "of CO2e per unit") DEFINE the
  component class; "aggregate" = any candidate whose activity_type contains none of them.
WHEN IT RUNS
  only after a match and only on the automatic-processing mapping path — NOT inside
  FactorMatchingEngine. The 034/035 oracles drove the engine directly, so they did NOT exercise this
  mechanism; that scope caveat matters when reading the D-A row evidence.
WHEN IT RETURNS EARLY
  1) status != "matched" or factor is None → unchanged; 2) the CURRENT matched factor has no component
  marker → unchanged ("already aggregate"); 3) any exception → logged, unchanged (never break mapping).
WHAT CANDIDATE INFORMATION IT SEES
  a fresh find_by_activity(activity, unit=unit, limit=20, unit_qualifier_tolerant=True) then
  next((f for f in candidates if not any(marker in f.activity_type)), None).
WHAT IT CANNOT DISTINGUISH
  · scope (Scope 1 combustion vs Scope 3 WTT vs 'Outside of Scopes');
  · a component→aggregate swap that crosses CONCEPTS (Development diesel → mineral diesel);
  · treatment route (Waste disposal vs Waste oils);
  · jurisdiction/metric (DEFRA kg CO2e vs SEAI kg CO2);
  · basis (Gross vs Net) — it inherits whatever the tolerant unit query returned first;
  · which aggregate is "the" aggregate when several qualify (plain vs '100% mineral blend' vs WTT).
VERDICT: PARTIALLY SUFFICIENT — a correct, narrow repair for the one failure mode it targets, safely
  guarded, but structurally incapable of the other three F-DA modes; its "first candidate in repository
  order" resolution is an ordering-dependent tie-break, not a policy.
```

## 11. DATA DISCREPANCY — RESOLVED

```text
Claim A (earlier evidence): 7,029 factors.      Claim B (035 verification): 7,049 factors.
VERIFIED: SELECT factor_set, count(*) → DEFRA-2025 = 7,029 · SEAI-2025 = 20  ⇒ total 7,049.
All rows reporting_year = 2025 (single year). Duplicate natural keys (year, activity, country, unit,
scope): ZERO. No version/supersedes column exists, so a duplicate/version issue is not possible in the
current schema. CLASSIFICATION: QUERY-SCOPE DIFFERENCE (a DEFRA-only count vs all factor sets), NOT stale
evidence, NOT duplicates, NOT a data defect. No dataset change was made or is proposed. (The SEAI-2025
import also carries a different metric — kg CO2, not kg CO2e — and country='IE', both visible in the data.)

## 12. REQUIRED POLICY DIMENSIONS (evidence-supported; no order assumed from the brief)

```text
DIMENSION                  EVIDENCE FROM THIS ANALYSIS                           REQUIRED?
1 jurisdiction/country     GB vs IE factors coexist; country is populated         YES — hard filter
2 factor set / source      DEFRA-2025 vs SEAI-2025; metric differs (CO2e/CO2)     YES — hard filter
3 reporting year           all rows 2025 today; DESNZ requires the correct       YES — hard filter
                           year's set for year-on-year comparability (§3)
4 unit compatibility       strict unit match already enforced by the index;       YES — already enforced
                           km vs kWh vs miles vs tonnes separates families
5 activity semantic        'Waste disposal' vs 'Waste oils'; 'Fuels > Liquid     YES — the core gap
   identity (taxonomy)     fuels >' vs 'Bioenergy > Biofuel >' prefixes
6 combustion vs WTT        656/656 WTT factors are Scope 3; combustion Scope 1    YES — F-DA-2
7 scope                    4 values in use incl. 'Outside of Scopes'; 134/134     YES — as a SEMANTIC
                           disposal names Scope 3, fuel families Scope 1           dimension, not decoration
8 aggregate vs component   aggregate == Σ components (6 proofs); a component       YES — F-DA-1
                           omits ~99 % of the activity total
9 basis (Gross/Net)        already resolved by D-A (closed); must not regress      YES — PRESERVED
10 treatment/methodology   disposal routes already in the name suffix             YES for waste
11 metric (CO2/CO2e)       SEAI = kg CO2, DEFRA = kg CO2e — NOT a stored field    PO CHOICE (name-only today)
12 supplier/custom factor  customer_factors already precedes the pipeline          ALREADY HANDLED (D-cf-5)
13 deterministic tie-break ties are resolved today by stage order / repository     YES — must be explicit
                           order; D-A already set an id-ordered/1.0 precedent
NOT a dimension: an AI ranking engine, a new factor store, or a new provenance system — nothing in the
evidence requires them; every distinction needed already exists in activity_type/unit/scope/country/set.
```

## 13. CANDIDATE POLICY OPTIONS AND THE EVIDENCE FOR/AGAINST

```text
OPTION A — status quo (+ keep _prefer_aggregate_factor)
  FOR : zero risk; component repair already works inside one name family.
  AGAINST: leaves F-DA-1 (row 1 component), F-DA-2 (WTT), F-DA-4 (diesel concept) live; the tie-break
          remains repository order. All three are reproduced in the evidence above.

OPTION B — smallest bounded deterministic semantic guard (RECOMMENDED)
  Apply, on the EXISTING candidate list only, a deterministic filter/priority using metadata already
  present: (i) jurisdiction + factor set + reporting year; (ii) unit compatibility (already enforced);
  (iii) taxonomy-prefix semantic identity for the activity family; (iv) exclude WTT-prefixed / Scope-3
  upstream candidates for Scope-1 combustion activity unless source evidence requests WTT; (v) require an
  aggregate (non-component) candidate when one exists for the chosen family; (vi) deterministic id-ordered
  tie-break with the D-A confidence precedent (1.0 for a deterministic policy selection).
  FOR  : every rule is grounded in the dataset above; no schema change, no new factor store, no engine
         redesign, no AI; narrows the candidate set only where a wrong concept is PROVEN reachable;
         reuses D-A's confidence/ordering precedent; blast radius containable by tests.
  AGAINST: prefix/marker semantics couple to the published naming convention (mitigation: keep the markers
         in one module with tests; a future metadata column can replace them).

OPTION C — add explicit factor metadata columns (category/methodology/gas/WTT/treatment/metric)
  FOR  : removes the string coupling; ranking becomes data-driven.
  AGAINST: schema change + migration + enrichment of 7,049 rows; larger than the problem; the importer has
         no source column for these today; needs separate PO authorisation.

OPTION D — AI/semantic ranking engine
  EXPLICITLY EXCLUDED by the task brief and unsupported by the evidence; rejected as over-engineering.
```

## 14. EXACT UNRESOLVED PO DECISIONS (evidence prepared, NOT answered)

```text
D-FS-1 aggregate vs component: EVIDENCE = the aggregate is exactly Σ components (6 arithmetic proofs) and
  a component omits ~99 % of the activity total; the component class is identifiable by an existing name
  marker. → Recommendation offered: prefer the aggregate; the PO decides.
D-FS-2 combustion vs WTT: EVIDENCE = 656/656 WTT factors are Scope 3 while combustion fuel factors are
  Scope 1; values differ by an order of magnitude (0.03347 vs 0.20270). → Recommendation offered: exclude
  WTT for Scope-1 activity unless requested; PO decides whether WTT is ever auto-selected.
D-FS-3 scope as a mandatory semantic dimension: EVIDENCE = scope is populated and 4-valued and perfectly
  separates the WTT/combustion split (and the 134 disposal names from the Scope-1 waste-oils fuel), but
  does NOT alone identify an activity (electricity consumption and SECR EV factors are both Scope 2).
  → PO decides whether scope is a filter or only a preference.
D-FS-4 waste treatment vs unrelated 'Waste oils': EVIDENCE = the taxonomy prefix and the '- Landfill /
  - Closed-loop / - Open-loop / - Incineration with Energy Recovery / - Composting' suffixes already
  distinguish them; scope separates disposal (3) from the fuel (1). → PO decides the precedence.
D-FS-5 residual ambiguity after all semantic dimensions: EVIDENCE = the dataset has NO duplicate natural
  keys, so after (jurisdiction, set, year, unit, family) only genuinely equivalent variants remain
  ('100% mineral blend' vs plain; consumption vs supply). → PO decides deterministic selection vs
  surfacing `ambiguous` (the engine already supports ambiguous + suggestions).
D-FS-6 deterministic final tie-break: EVIDENCE = today it is stage order / repository order, which is not
  a stated policy; D-A already established a defensible precedent (order by factor id; deterministic
  confidence 1.0). → PO confirms id-ordering (or another stable rule) as the final tie-break.
```

## 15. WHAT THIS TASK DID NOT CHANGE (binding statement)

```text
NO application code change · NO test change · NO configuration change · NO schema/migration change ·
NO factor-data change (no row added, edited or deleted) · NO matching-behaviour change · NO ranking change ·
NO change to _prefer_aggregate_factor · NO deployment · NO P1 activation (P1 remains SHADOW) ·
NO D-B/D-C/D-D work started · D-A NOT reopened. No production access; all DB use read-only with the session
forced READ ONLY; no disposable records were created, so no cleanup was required. The ONLY artefact of this
task is this report. Scratch analysis harnesses live outside the repository (/tmp/v37_*.py) and are not
committed.
```

## FINAL VERDICT

**EVIDENCE PARTIAL — SPECIFIC EVIDENCE GAP**

The CarbonTally-internal evidence required for the PO decisions is **complete and verifiable**: the actual
matcher architecture; the actual metadata inventory (13 DB columns / 12 domain fields, with the absent
dimensions enumerated); four real case studies; six arithmetic proofs that the aggregate equals the sum of
its components; the 656/656 WTT-as-Scope-3 separation; the 134-name waste-treatment encoding; the full
trace and verdict on `_prefer_aggregate_factor`; and the resolved 7,029/7,049 discrepancy.

The **gap** is external only and is stated plainly: the substantive rule text of the GHG Protocol and SEAI
guidance could not be retrieved from this environment (**HTTP 403**), and the DESNZ rule detail lives in
Excel workbooks / a 157-page methodology PDF — so **no external standard is claimed to mandate any
CarbonTally rule**. Only one externally-quoted requirement survived retrieval (per-year factor sets, and the
condensed-set vs advanced-set distinction, §3). The options in §13 therefore rest on CarbonTally-internal
evidence plus AUTHORITATIVE DATA — sufficient to *prepare* D-FS-1…D-FS-6, insufficient to assert external
compliance wording.

**No implementation was performed. D-A remains PO-CLOSED and was not reopened. D-B/D-C/D-D were not
started. PO is not closed by this report.**


