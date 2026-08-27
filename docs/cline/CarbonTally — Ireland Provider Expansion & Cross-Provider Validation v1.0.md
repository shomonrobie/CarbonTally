# CarbonTally — Ireland Provider Expansion & Cross-Provider Validation v1.0

## OBJECTIVE

Extend CarbonTally's provider architecture to support Ireland emission factors alongside the existing DEFRA/UK dataset.

This is NOT Phase 9 yet.

This is a controlled provider-expansion and architecture-validation phase that must prove that the existing CarbonTally mapping and calculation architecture works correctly across multiple national factor sources.

Current authoritative UK dataset:

* DEFRA-DESNZ
* DEFRA-2025
* GB
* reporting year 2025
* 7,029 persisted emission factors

Ireland must become an additional provider/factor source without duplicating the mapping engine, calculation engine, workflow engine, or core domain logic.

---

# NON-NEGOTIABLE RULES

1. READ-ONLY discovery first.
2. Do not modify production code during discovery.
3. Do not guess or invent Irish emission-factor data.
4. Do not invent Irish factor sources.
5. Do not silently substitute UK/DEFRA factors for Irish factors.
6. Preserve the existing provider/plugin architecture.
7. Reuse the existing Mapping/Factor Matching Engine.
8. Reuse the existing Calculation Engine.
9. Do not create a separate Ireland-specific mapping engine.
10. Do not create a separate Ireland-specific calculation engine.
11. Do not modify existing DEFRA factor values.
12. Do not truncate or reset the authoritative database.
13. Do not run integration tests against the authoritative database if the test fixture can truncate it.
14. Use a dedicated integration/test database where required.
15. Do not commit or push.
16. Do not modify unrelated working-tree changes.
17. Do not repeatedly read the same temporary file.
18. Do not get stuck in polling loops. One command → wait for completion → inspect result once.

---

# PHASE A — DISCOVERY ONLY

Before changing anything, inspect:

* Architecture v2.1
* Implementation Preparation Pack
* existing provider base/registry
* DEFRA provider implementation
* ImportMappingEngine
* FactorMatchingEngine
* CalculationEngine
* FactorSearch index
* emission_factors schema/model
* import_batches schema/model
* existing provider tests
* existing integration-test database configuration
* current Ireland-related provider placeholders/specifications, if any

Do not reread files repeatedly.

Produce:

## Ireland Provider Architecture Assessment

Include:

1. Existing provider interface
2. Existing DEFRA provider implementation
3. What an Ireland provider must implement
4. Existing country/source/version fields that can represent Ireland
5. Existing import/version/batch mechanisms
6. Existing mapping pipeline
7. Existing matching pipeline
8. Existing calculation pipeline
9. Existing database constraints relevant to Irish factors
10. Exact files that would need modification/addition
11. Any architecture gaps

STOP after discovery if the required Irish source/data cannot be established from the repository/specification.

---

# PHASE B — IDENTIFY AUTHORITATIVE IRISH FACTOR SOURCE

Determine which Irish emission-factor dataset CarbonTally is supposed to support.

Use the project's existing provider specifications/prep-pack if one exists.

If an authoritative source is not specified in the repository, DO NOT invent one.

Instead report:

* source required
* source format required
* reporting year/version required
* whether the source is downloadable
* whether licensing/usage restrictions need confirmation
* what information is missing

If the authoritative source is already specified and available, continue.

Document:

* provider name
* source organization
* country
* reporting year
* factor-set identifier
* source URL/reference if already documented
* source file
* number of source records
* number of usable factors
* skipped records and reasons

---

# PHASE C — IMPLEMENT IRELAND PROVIDER

Implement the Ireland provider using the SAME provider architecture used by DEFRA.

Expected conceptual structure:

providers/
base.py
registry.py
defra/
ireland/

Do not assume the directory name if the existing architecture uses another convention.

The provider must support:

* source metadata
* version/reporting year
* source country
* parser
* mapper
* validator
* exporter/import integration where required
* deterministic factor identity/natural-key behavior
* import batch tracking
* idempotent import

Do not duplicate generic import logic that already exists.

Provider-specific logic belongs inside the Ireland provider.

Generic mapping/matching/calculation logic remains shared.

---

# PHASE D — IMPORT SAFELY

Before importing:

1. Verify the target database.
2. Verify it is NOT the integration-test database.
3. Verify DEFRA count remains 7,029.
4. Verify no test fixture will truncate the database.
5. Verify the Irish import is idempotent.

Then import the Irish dataset.

Record:

* source rows
* accepted factors
* skipped rows
* validation failures
* duplicates
* warnings
* import batch ID
* factor source
* factor set
* reporting year
* country

Do not alter existing DEFRA rows.

---

# PHASE E — DATABASE VERIFICATION

After import verify independently:

### DEFRA

Expected:

7,029 existing DEFRA factors.

### Ireland

Report:

* total Irish factors
* factor source
* factor set
* reporting year
* country
* active/inactive counts
* natural-key uniqueness
* duplicate count
* import batch
* skipped/invalid rows

### Cross-provider

Verify:

* DEFRA rows remain intact
* Irish rows are distinguishable by provider/source/country/version
* no natural-key collisions incorrectly overwrite factors from another provider
* provider/source metadata is preserved
* search index contains both datasets

Do NOT assume the exact Irish factor count before importing.

---

# PHASE F — MAPPING ENGINE VALIDATION

This is the most important part.

Use the EXISTING CarbonTally Mapping/Matching Engine.

Do NOT create Ireland-specific matching logic.

Create a representative Irish test corpus containing real activities/categories/units from the imported Irish dataset.

Test:

## 1. Exact matches

Irish activity → Irish factor

Expected:

* correct factor
* correct provider
* correct country
* confidence = 1.0 where applicable

## 2. Natural-key matches

Test:

activity + unit + country/scope combinations.

## 3. Alias matches

Where aliases exist, verify they resolve to the correct Irish factor.

## 4. Keyword matches

Verify Irish terminology can retrieve appropriate candidates.

## 5. Fuzzy matches

Verify reasonable variations resolve correctly without incorrectly selecting UK/DEFRA factors.

## 6. Ambiguous matches

Create cases where multiple Irish factors are plausible.

Expected:

AMBIGUOUS rather than silently selecting the wrong factor.

## 7. No-match cases

Expected:

NO_MATCH with appropriate suggestions.

## 8. Country/provider isolation

This is mandatory.

Test equivalent/similar activities existing in both:

DEFRA/GB

and

Ireland.

Verify the engine does not accidentally select the wrong country's factor when the request is scoped to Ireland.

---

# PHASE G — CALCULATION ENGINE VALIDATION

Use the existing Phase 5 CalculationEngine.

Do NOT create an Ireland calculation engine.

For representative Irish factors:

1. Match factor.
2. Construct CalculationRequest.
3. Calculate emissions.
4. Verify co2e_kg.
5. Verify co2e_tonnes.
6. Verify unit validation.
7. Verify snapshot creation.
8. Verify content hash.
9. Verify calculation verification.
10. Verify provenance contains the correct Irish factor/provider/source/version.

Also test at least one equivalent UK/Irish activity pair to prove that provider identity remains traceable through:

MATCH → CALCULATE → SNAPSHOT → LOG → AUDIT.

---

# PHASE H — CROSS-PROVIDER REGRESSION

Run the existing DEFRA test suite.

Then run Ireland tests.

Then run cross-provider tests.

Required invariants:

DEFRA behavior must remain unchanged.

Existing 7,029 DEFRA factors must remain unchanged.

Ireland must not alter DEFRA factor matching.

Ireland must not alter calculation behavior.

Provider selection must remain deterministic.

---

# PHASE I — TEST ISOLATION

The integration-test suite MUST NOT destroy the authoritative database.

Before running integration tests:

* identify the test DB
* identify the application/authoritative DB
* prove they are separate OR prove the test fixture cannot truncate authoritative production data

Run tests only after this is established.

After tests verify:

AUTH DB DEFRA = 7,029

and the Irish factor count remains unchanged.

---

# PHASE J — VERIFICATION

Run:

1. Ireland provider unit tests
2. Ireland provider integration tests
3. Mapping engine cross-provider tests
4. Calculation engine cross-provider tests
5. Full unit suite
6. Full integration suite against isolated test DB
7. mypy --strict
8. compile/import checks
9. architecture/dependency checks
10. provider registry checks
11. database verification

---

# ACCEPTANCE CRITERIA

The Ireland expansion is complete only if ALL are true:

### Provider

* Ireland provider implemented using existing provider architecture
* no duplicated generic engine logic

### Data

* authoritative Irish dataset imported
* exact imported factor count reported
* version/reporting year recorded
* provider/source/country recorded
* no unintended DEFRA modifications

### Mapping

* exact matching verified
* natural-key matching verified
* alias matching verified where applicable
* keyword matching verified
* fuzzy matching verified
* ambiguous matching verified
* no-match behavior verified
* UK/Ireland provider isolation verified

### Calculation

* Irish factor calculates correctly
* unit validation works
* snapshot persists
* content hash verifies
* provenance is correct
* audit/event behavior remains correct

### Regression

* DEFRA 7,029 factors remain intact
* existing tests remain green
* no architecture violations
* mypy strict clean

### Database safety

* authoritative database is not truncated by integration tests
* test database is isolated
* post-test DEFRA count = 7,029
* post-test Ireland count unchanged

---

# FINAL REPORT

Return a structured report:

## 1. Ireland Source

## 2. Provider Implementation

## 3. Import Results

## 4. Database Results

## 5. Mapping Engine Results

## 6. Cross-Provider Tests

## 7. Calculation Results

## 8. DEFRA Regression

## 9. Test Isolation

## 10. mypy / Architecture

## 11. Files Changed

## 12. Risks / Gaps

## 13. Recommendation

Then STOP.

Do not start Phase 9 automatically.

Do not commit.

Do not push.


One important correction to your diagram

I would not make the architecture:

UK + Ireland → Mapping Engine

with the implication that the mapping engine itself chooses countries.

Instead, make provider/source/country part of the factor identity and matching context:

                 CARBONTALLY CORE
                       │
             ┌─────────┴─────────┐
             │                   │
          UK/GB              Ireland/IE
             │                   │
        DEFRA Provider      IE Provider
             │                   │
             └─────────┬─────────┘
                       │
                 Factor Registry
                       │
                 Factor Search
                       │
               Matching Engine
                       │
            ┌──────────┼──────────┐
         Extract      Map       Validate
                       │
                 Matched Factor
                       │
                CalculationEngine
                       │
              Calculation Snapshot
                       │
             ┌─────────┼─────────┐
          Dashboard   Export      API

That distinction is important for CarbonTally's long-term architecture. Ireland is a provider expansion test of the core platform, not a separate product implementation.