# CT-STEP2-EF-POLICY-EVIDENCE-032 — Emission-Factor Policy Evidence Pack

**READ-ONLY forensic/evidence task.** No code, test, schema, EF data, configuration or production change.
The only artifact is this report. P1 untouched.

## 1–3. Task, baseline, scope
Task `CT-STEP2-EF-POLICY-EVIDENCE-032`; baseline `7a1294ce67c10ba269443dd41c2a473b93b86544`
(`p8-release-reconciled`, verified clean). Scope: evidence for Decisions A–F (natural-gas CV basis; power
taxonomy + scope; diesel selection; waste selection; factor-set UX/precedence; invoice-reference field),
separating *existing CarbonTally rule* / *dataset fact* / *external methodology* / *product decision*.
No recommendation or ranking is offered anywhere in this report.

## 4. Factor-set inventory (local authoritative DB, read-only)
```text
country | factor_source | factor_set | factors | distinct units | distinct scopes
GB      | DEFRA-DESNZ   | DEFRA-2025 |   7 029 | 15             | 4        ← default
IE      | SEAI          | SEAI-2025  |      20 |  4             | 2        ← alternative
providers ['DEFRA-DESNZ','SEAI'] · countries ['GB','IE'] · sets ['DEFRA-2025','SEAI-2025']
```
Both sets are present as **data**; the matching pipeline selects by `(country, preferred_provider)`
context (031), so a further set is an import, not a code change.

## 5. DEFRA evidence (dataset facts)
Natural gas (100% mineral blend) exists with four units and **two CV bases**, in both component and
aggregate form, all `Scope 1`:
```text
component  CH4 (kg CO2e of CH4 per unit)  kWh (Gross CV) 0.00028  ·  kWh (Net CV) 0.00031
component  CO2 (kg CO2e of CO2 per unit)  kWh (Gross CV) 0.18457  ·  kWh (Net CV) 0.20448
component  N2O (kg CO2e of N2O per unit)  kWh (Gross CV) 0.00009  ·  kWh (Net CV) 0.00010
AGGREGATE  (kg CO2e)                      kWh (Gross CV) 0.18494  ·  kWh (Net CV) 0.20489
also: cubic metres  2.08504 (CO2) / 2.08906 (CO2) · tonnes 2598.26 / 3.8528 · … ids e.g.
  69c9aeda-d10a-4db5-96d6-716cd359c781 (Gross aggregate), b8b759c5-… (Gross CO2 component)
```
The `kWh (Gross CV)` / `kWh (Net CV)` distinction is carried **in the factor unit spelling**, i.e. it is a
property of the factor-set data.

## 6. SEAI evidence (dataset facts)
```text
IE | Fuels > Gaseous fuels > Natural gas (NCV) (kg CO2) [cubic metres] 2.005357  Scope 1
IE | Fuels > Liquid fuels  > Diesel / gasoil (100% petroleum) (kg CO2) [litres] 2.682327  Scope 1
IE | Fuels > Liquid fuels  > Gasoline / petrol (100% petroleum) (kg CO2) [litres] 2.310723  Scope 1
```
SEAI encodes the measurement basis **in the activity name** (`Natural gas (NCV)`) and uses `cubic metres`;
it does **not** use DEFRA's `kWh (Gross CV)/(Net CV)` unit-qualifier convention. ⇒ the CV/measurement basis
is expressed **differently per factor set**, which is evidence that basis selection belongs to the
factor-set data/taxonomy rather than to a global matcher rule.

## 7–8. Natural gas — Gross vs Net (Decision A)
```text
EXISTING CARBONTALLY RULE for Gross/Net preference?      NO EXISTING CARBONTALLY RULE FOUND
  searched: 'Gross CV', 'Net CV', 'calorific', 'gross cv', 'net cv' across code/docs/SQL
  what DOES exist: the qualifier mechanics only —
    core/units.py UNIT_ALIASES maps "kwh (gross cv)"/"kwh (net cv)" to canonical spellings;
    core/units.py unit_matches_with_qualifier treats kWh ↔ kWh (Gross CV) as compatible;
    data/emission_factors.py:128-133 documents that find_by_activity(unit_qualifier_tolerant=True)
      exists so "a human operator typing 'kWh' also finds 'kWh (Gross CV)'";
    engines/calculation.py:228 and api/v3_processing_workflow.py:912 reference the same tolerance.
  No code, config, doc, migration or test prefers one basis over the other, and no rule derives the
  basis from the document, the supplier, or the factor set.
AMBIGUITY: for a source row stating only `kWh`, the DEFRA set offers two aggregate candidates whose
  values differ (0.18494 vs 0.20489) and whose basis is not stated by the source row.
PRODUCT DECISION REQUIRED: which CV basis is authoritative when the source document is unqualified.
TECHNICAL NOTE (defect, not a policy): the reason neither candidate is even reached today is the
  verbatim-unit natural-key/keyword filtering described in 030 (NaturalKeyStage key
  `(year, activity, country, request.unit or "", scope)`; keyword stage passes `request.unit`).
  Fixing that alone would make the matcher pick whichever qualified candidate the index enumerates
  first — i.e. fix and decision are coupled; the fix must not be shipped before the basis rule exists.
```

## 9. Power consumption — taxonomy (Decision B)
```text
EXISTING TAXONOMY: services/automatic_extraction.py:50 defines the canonical keyword family
    ("Electricity", re.compile(r"electricity|electrical|mpan", re.IGNORECASE))
  ⇒ a canonical activity "Electricity" EXISTS in CarbonTally's own taxonomy, but its keyword set does not
    contain "power", "power consumption" or "supply".
FACTORS: the phrase does not resolve; authoritative electricity factors do exist, e.g.
    Fuels > Electricity > Electricity consumption (kg CO2) [kWh]     (unit kWh)
    Fuels > Electricity > Gross electricity supply  (kg CO2) [kWh]   (unit kWh)
  and the activity_type prefix `Fuels > Electricity >` is the family the validation rule keys on (§10).
AMBIGUITY: two authoritative electricity targets exist with different meanings (consumption vs gross
  supply); the existing taxonomy does not establish which one the phrase denotes.
PRODUCT DECISION REQUIRED: whether to extend the existing Electricity keyword taxonomy with the phrase
  (and which canonical target), i.e. a taxonomy/vocabulary decision, not a code-architecture decision.
```

## 10. Power — scope (Decision B, second part)
```text
EXISTING CARBONTALLY RULE: YES — engines/validation.py:96-102 derives scope from the activity family:
    "``Fuels > Electricity > …`` implies Scope 2; the fuel families …" → returns "Scope 2"
  supported vocabulary (engines/validation.py:55): ("Scope 1","Scope 2","Scope 3","Outside of Scopes")
IMPLICATION: scope is a property of the SELECTED FACTOR's family, not of the invoice wording. Whichever
  electricity factor the PO designates, its own `scope` field will drive the scope used for the row.
AMBIGUITY: none beyond §9's choice of target factor; no separate scope decision appears necessary.
```

## 11–12. Diesel — candidates and selection mechanics (Decision C)
```text
CANDIDATES (DEFRA/GB, dataset facts)
  Fuels > Liquid fuels > Diesel (100% mineral diesel) (kg CO2e) [tonnes] 3203.91143   Scope 1
  Fuels > Liquid fuels > Diesel (100% mineral diesel) (kg CO2e of CO2 per unit)[tonnes] 3164.33  Scope 1
  Fuels > Liquid fuels > Diesel (average biofuel blend) (kg CO2e) [tonnes] 3087.94462 Scope 1
  WTT- fuels > … Diesel (100% mineral diesel) (kg CO2e) [tonnes]  752.0276            Scope 3
  Outside of scopes > Forecourt fuels containing biofuel > Diesel … [tonnes] 163.17   Outside of Scopes
  Outside of scopes > Biofuel > Development diesel (kg CO2e of CO2 per unit) [GJ] 73.54 Outside of Scopes
  (the factor actually selected for storage 'Diesel' in 029/031 was
   Bioenergy > Biofuel > Development diesel (kg CO2e) [litres] 0.03705, id c3afa542-1daf-419c-88ea-94252d4dba18)
MECHANICS (existing, unchanged): staged pipeline exact_match → natural_key → alias_match →
  keyword_search → fuzzy_match, then _prefer_aggregate_factor (aggregate over component). For 'Diesel'
  the keyword stage matched a Bioenergy/Biofuel factor at confidence 1.000; the aggregate step changed
  nothing because the pick is already whole-gas (non-component).
EXISTING CARBONTALLY RULE that excludes biofuel/development factors, or that prefers
  'Diesel (100% mineral diesel)' / 'average biofuel blend' for a generic diesel line?   NO RULE FOUND
  (the dataset DOES distinguish the classes via the activity hierarchy and the explicit
   'Outside of Scopes' category, but no CarbonTally code or configuration reads that distinction for
   preference, and no documentation states a preference.)
AMBIGUITY: "Diesel" matches several materially different factors (mineral diesel, average biofuel blend,
  biofuel/development, WTT Scope 3, out-of-scope forecourt fuel) with very different multipliers.
PRODUCT DECISION REQUIRED: FACTOR-SELECTION POLICY REQUIRED — which factor class satisfies a generic
  diesel source row. No ranking was invented and the current selection was left untouched.
```

## 13–14. Waste — candidates and aggregate mechanics (Decision D)
```text
CANDIDATES (DEFRA/GB, dataset facts)
  Fuels > Liquid fuels > Waste oils (kg CO2e of CO2 per unit) [tonnes] 3171.09  Scope 1   ← component
  Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit)  [tonnes]    3.5504  Scope 1 ← component
  Fuels > Liquid fuels > Waste oils (kg CO2e of N2O per unit)  [tonnes]   44.73876 Scope 1 ← component
  (aggregate Waste oils (kg CO2e) [tonnes] 3219.37916 was selected by the existing aggregate preference)
  Bioenergy > Biogas > Landfill gas (kg CO2e) [tonnes] 0.69696 · [kWh] 0.0002     Scope 1
MECHANICS (existing, verified in 029/031): the component CH4 pick is re-selected to the aggregate
  'Waste oils (kg CO2e)' by _prefer_aggregate_factor — the rule itself works.
EXISTING CARBONTALLY RULE establishing "Waste disposal" → "Waste oils"?   NO RULE FOUND.
  Evidence against the equivalence being established by the data: the matched activity lives under
  'Fuels > Liquid fuels' (a fuel), not under any waste-treatment/disposal family, and a search of the
  dataset for waste/landfill terms surfaced no waste-disposal/landfill activity for a mass of general
  waste; the only other waste-related family found is Landfill gas (a fuel gas), not waste disposal.
AMBIGUITY: the source phrase describes a disposal service; the available factors describe a waste-derived
  fuel. These are materially different activities.
PRODUCT DECISION REQUIRED: whether "Waste disposal" should map to the waste-oils family at all, and if not,
  which activity/factor class represents it (with the consequence that the current value may change).
```

## 15–16. Factor-selection architecture and fact-set precedence
```text
GENERIC MATCHING RULES (mechanism): stage order, natural key (year, activity, country, unit, scope),
  alias resolution, keyword/fuzzy scoring, unit compatibility (027 + qualifier rule), aggregate-over-
  component preference, confidence threshold AUTO_MAPPING_CONFIDENCE_MIN.
METHODOLOGY/PRODUCT POLICY (currently NOT defined anywhere): CV basis (Gross/Net), which electricity
  target the phrase "power consumption" denotes, which diesel class a generic diesel row may use, whether
  "Waste disposal" denotes waste oils, and the factor-set default/override surface.
FACTOR-SET PRECEDENCE (031 implementation, verified): factor_set_context(metadata) =
  document override (metadata factor_country / factor_provider) → PO default (GB / DEFRA-DESNZ); the
  effective value is passed into MatchRequest(country=…, preferred_provider=…) so the search is
  CONSTRAINED to one set. All rows of one document inherit one effective set; per-row mixing is not
  introduced. Tests: tests/unit/services/test_factor_set_context.py (6, passing).
```

## 17. Factor-set UX findings (Decision E)
```text
EXISTING ARCHITECTURE: the pipeline already accepts effective context from job metadata keys
  factor_country / factor_provider (document level) over the PO default, so org default + document
  override are representable TODAY without per-row mixing (§16).
OPTIONS OBSERVED IN THE EXISTING ARCHITECTURE (no choice made):
  (a) organisation/account settings — the repository bundle already exposes settings / queue_settings
      repositories, the natural home for an org-level default;
  (b) document-level override — per-document queue/document metadata already carries document keys;
  (c) the PO-declared future Emission Factor module will own set management (not built here).
AMBIGUITY: which surface is authoritative, and whether an upload-time control is required.
PRODUCT DECISION REQUIRED: where the org default and the document override are exposed.
```

## 18. Invoice-reference trace (Decision F)
```text
EXISTING FIELD(S) — YES, they exist:
  domain/line_items.py:45 "invoice_number" is an established line-item field;
  engines/extraction.py:52 deterministic invoice_number regex;
  services/automatic_extraction.py:105-107,122-123 header aliases invoice_number|invoice_no|invoice_ref
    → invoice_number; :719-720 the CSV/XLSX path promotes line_items[0].invoice_number into extracted;
  services/extraction_suggestions.py:62,122,135-136 invoice_number suggestion + unresolved tracking;
  domain/evidence.py:188 "invoice_reference" in the evidence context;
  services/automatic_processing.py:269 "invoice_number" in the required-field vocabulary.
LOSS POINT (multi-line PDF path): the P1 candidate records built by
  services/extraction_fidelity.build_line_items() carry description/quantity/unit/page/line_number/
  source_line/extraction_method but NO invoice_number, and the PDF path does not copy a document-level
  invoice_number onto the extracted record — observed in 029/031 where the extracted store gained
  date/supplier but the reference did not reach the line set.
CLASSIFICATION: supported-but-not-propagated (technical defect), NOT a missing field.
SMALLEST FIX (not applied): carry the existing deterministic invoice_number onto the P1 line items and the
  extracted record so the existing provenance chain can surface it. No schema change required.
```

## 19–20. Provenance and report architecture
```text
ALREADY SUPPORTED: source document/file (organization_files; queue file_name/file_url) · source item
  (document_processing_queue.source_item_id) · source line item (evidence_line_items ordinal ↔ line id;
  CalculationRequest.source_item_id / source_line_item_id) · source ordinal, line_number, source_line
  (P1 records + mapping entries) · page with honest page_basis · mapped activity + factor identity
  (mapped_data entries; factor_id/factor_kind) · factor set/source/year (emission_factors.factor_set /
  factor_source / reporting_year, present in the dataset and on matched factors) · quantity/unit ·
  calculation snapshot (deterministic request id) · report lines (disclosure/report modules consume
  calculation records).
SUPPORTED BUT NOT PROPAGATED: factor_set / factor_source / reporting_year onto the persisted calculation
  snapshot and the report line (the matched factor carries them; the snapshot copy was not verified because
  the sink has not been exercised — see 030/031).
ABSENT / UNDECIDED: invoice reference on the multi-line PDF line set (§18). No new field proposed.
REPORT PATH (identified, not exercised): report lines take emissions from persisted calculation records via
  the existing disclosure/report modules; a future actual report must read factor identity and factor-set
  identity from the snapshot and source identity through source_item_id / source_line_item_id. No report
  code was modified and no report was generated in this task.
```

## 21–23. Decision matrix (no recommended-choice column; no ranking)
```text
Decision                  | Existing CT rule? | Data evidence? | Candidates | Ambiguity | Product decision? | Technical fix?
Natural gas Gross vs Net  | NO rule found     | YES — DEFRA has both bases; SEAI names the basis (NCV) | 0.18494 Gross / 0.20489 Net (aggregates) | which basis for an unqualified kWh row | YES | YES (T1)
Power canonical activity  | PARTIAL — "Electricity" keyword family exists (electricity|electrical|mpan) | YES — Electricity consumption; Gross electricity supply | two kWh factors | which target the phrase denotes | YES (taxonomy) | NO
Power scope               | YES — `Fuels > Electricity > …` implies Scope 2 (validation rule) | YES — scope on factors | n/a | none beyond target choice | NO | NO
Diesel selection          | NO rule found     | YES — mineral vs average blend vs biofuel/Development; WTT Scope 3; Outside of Scopes | 6+ classes | which class satisfies a generic diesel row | YES | NO
Waste activity selection  | NO rule found (aggregate step works) | YES — Waste oils under Fuels > Liquid fuels; Landfill gas; no disposal activity found | 3 components + aggregate + landfill gas | disposal service vs waste-derived fuel | YES | NO
Factor-set precedence     | YES — 031 context (document → default) | YES — two sets present | n/a | none | NO (surface only) | NO
Factor-set UI location    | NO — three options (§17) | PARTIAL | n/a | which surface | YES (UX) | NO
Invoice reference field   | YES — field + regex + aliases exist | YES | invoice_number (line items); invoice_reference (evidence) | none | NO | YES (T2)
```

## 24–25. Ambiguities and technical defects (documented, NOT applied)
```text
T1 natural-key/keyword unit filtering uses request.unit verbatim → qualifier-compatible factors are
   unreachable. Where: engines/matching_stages.py (NaturalKeyStage key `(year, activity, country,
   request.unit or "", scope)`; keyword stage passes request.unit) and engines/factor_matching.py.
   Current: no_match for `Natural gas` + `kWh`. Expected: the existing rule
   unit_matches_with_qualifier('kWh','kWh (Gross CV)') == True applied in the search path, exactly as
   data/emission_factors.py:128-133 documents for find_by_activity(unit_qualifier_tolerant=True).
   Smallest fix: apply the qualifier rule in the index/search unit filter. COUPLED to Decision A.
T2 invoice_number not propagated onto the multi-line PDF line set (services/extraction_fidelity.py
   build_line_items + PDF record assembly). Field already exists → no schema change.
T3 _prefer_aggregate_factor early-returns on a non-matched result, so its aggregate/recovery lookup is
   unreachable when the staged pipeline returns no_match (services/automatic_processing.py); fixing it
   needs a confidence/status convention for a recovered candidate → coupled to Decisions A/C.
```

## 26. Product decisions required (exact list)
```text
D-A  CV basis (Gross CV vs Net CV) for a source row whose unit is unqualified `kWh`
D-B1 which canonical electricity activity "Power consumption" denotes (Electricity consumption vs Gross
     electricity supply) and whether the existing electricity keyword taxonomy is extended
D-B2 scope — NO decision needed: the existing rule derives it from the selected factor's family (§10)
D-C  which diesel factor class satisfies a generic diesel row (mineral / average blend / biofuel /
     Development / WTT Scope 3 / Outside of Scopes)
D-D  whether "Waste disposal" denotes the waste-oils family at all, and if not which activity represents it
D-E  factor-set UX: where the organisation default and the document override are surfaced
D-F  NO field decision needed (invoice_number exists); only the propagation fix T2
```

## 27. External official evidence
**NONE USED.** Every statement derives from the repository's own code, its own tests, or the local
authoritative EF dataset. No external DEFRA/SEAI documentation was consulted, so none is cited and no
external methodology is presented as a CarbonTally rule.

## 28–30. Production safety, P1 state, conclusion
No production mutation/upload/calculation/report/queue operation/EF modification/deployment/Render/Vercel/
configuration change; protected job `9ef61662-1c0a-497a-b5e9-c179e2134784` untouched; all database access
read-only against the **local** authoritative database; **P1 = `shadow`**.
```text
EXISTING CARBONTALLY RULES FOUND: scope-from-activity-family (Fuels > Electricity > → Scope 2);
  alias/qualifier unit tolerance (kWh ↔ kWh (Gross CV)); aggregate-over-component preference;
  invoice_number as an established line-item field; factor-set context precedence (031).
NO EXISTING RULE FOUND: Gross/Net preference; diesel factor-class preference; waste activity equivalence;
  which electricity target "power consumption" denotes; factor-set UX surface.
DATASET FACTS: two factor sets (DEFRA-2025 GB 7 029 · SEAI-2025 IE 20); DEFRA carries both CV bases as
  unit-qualified factors; SEAI expresses the basis in the activity name (NCV) on cubic metres; diesel and
  waste each expose several materially different factor classes.
TECHNICAL DEFECTS (evidence-complete, not applied): T1, T2; T3 requires a policy-coupled convention.
```

## 31. Exact next implementation gate
```text
GATE 1 — Decisions D-A, D-B1, D-C, D-D, D-E.
GATE 2 — On D-A only, T1 becomes implementable generically (qualifier-aware unit filtering) with
         regression tests; without D-A, T1 must not ship (it would silently select one CV basis).
GATE 3 — T2 (invoice-number propagation) is independent of every decision and can be implemented now,
         with tests, without schema change.
GATE 4 — After Gates 1–2, the calculation sink, a persisted snapshot and an actual report can be exercised
         locally to complete report → snapshot → source_line_item_id → source row provenance.
```

## FINAL VERDICT

**EVIDENCE COMPLETE — READY FOR PO DECISIONS**

Every question A–F is answered from repository/dataset evidence: the rules that exist are identified with
file references, dataset facts are enumerated with real factor IDs, genuine ambiguities are stated as
ambiguities, and three technical defects are recorded precisely — without choosing, ranking or
recommending any factor.




