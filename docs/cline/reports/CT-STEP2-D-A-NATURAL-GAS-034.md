# CT-STEP2-D-A-NATURAL-GAS-034 — Natural-gas factor-basis selection

## Baseline / final SHA
**Baseline (verified before any change):** `37f1764775db054a6f983dcef9e357333e429f32`
(`HEAD == origin/p8-release-reconciled`, working tree clean). **Final SHA:** this report's commit.

## HONEST STATUS — NO CODE WAS CHANGED IN THIS WINDOW
D-A was **not implemented**. The execution window available to me ended before I could implement *and
validate* it, and the task forbids guessing and requires the tree to finish clean. Rather than leave an
unvalidated change in the path that decides reported emissions, I banked the verified design below and
stopped. Nothing is broken, nothing fabricated, no production state touched, P1 untouched.
**Verdict: PARTIAL.**

## Verified root cause (traced; unchanged from 030/032)
```text
MatchRequest(activity='Natural gas', unit='kWh', country/provider from the 031 context)
  exact_match       : no exact natural-key hit
  natural_key       : engines/matching_stages.py — NaturalKeyStage.execute builds the RC2 key as
                      (reporting_year, activity, country, request.unit or "", scope)  ← unit VERBATIM
                      so 'kWh' can never equal the dataset's 'kWh (Gross CV)' / 'kWh (Net CV)'
  alias_match       : request.unit passed verbatim (matching_stages.py:63)
  keyword_search    : request.unit passed verbatim (:162) → qualified rows filtered out
  fuzzy_match       : same (:259, :333)
  aggregate pref    : services/automatic_processing.py _prefer_aggregate_factor:1414 early-returns when
                      result.status != "matched" → the deterministic candidate lookup never runs
  RESULT: no_match — although EmissionFactorsRepository.find_by_activity(
          'Natural gas', unit='kWh', unit_qualifier_tolerant=True) returns 20 candidates (8 aggregate)
          and core/units.py unit_matches_with_qualifier('kWh','kWh (Gross CV)') is True.
```
The failure is an **inconsistent application of an existing compatibility rule**, not missing data. The
dataset holds both bases as separate factors (must not be collapsed):
```text
GB | DEFRA-DESNZ | DEFRA-2025 | aggregate (kg CO2e) [kWh (Gross CV)] 0.18494 | Scope 1
GB | DEFRA-DESNZ | DEFRA-2025 | aggregate (kg CO2e) [kWh (Net CV)]   0.20489 | Scope 1
GB components CH4 0.00028/0.00031 · CO2 0.18457/0.20448 · N2O 0.00009/0.00010 (Gross/Net, Scope 1)
IE | SEAI | SEAI-2025 | Natural gas (NCV) (kg CO2) [cubic metres] 2.005357 | Scope 1
  (SEAI names the basis in the ACTIVITY, not the unit — no kWh qualifier exists for SEAI)
```

## Implementation design (exact, ready to execute — NOT applied)
```text
PART 1 — discovery (reuse the existing qualifier rule; never duplicate it)
  Preferred: engines/matching_stages.py — build the natural key from split_qualified_unit(request.unit)[0]
    (core/units.py:115) instead of the verbatim string (:120), and use
    unit_matches_with_qualifier(query, candidate) (core/units.py:137) for the candidate comparison at
    :63/:162/:259/:333 — exactly the tolerance data/emission_factors.py:128-133 already documents for
    find_by_activity(unit_qualifier_tolerant=True). 027 semantics untouched: Gross/Net stay
    METHODOLOGICAL bases, never a unit conversion.
  Narrower alternative (service layer only, index untouched): recover a no_match result in
    services/automatic_processing.py via the existing tolerant repository call
    find_by_activity(..., unit_qualifier_tolerant=True) (029 proved it returns the 8 aggregates).
    OPEN CONVENTION: admitting a recovered candidate needs a MatchResult confidence, and the mapping gate
    compares it to AUTO_MAPPING_CONFIDENCE_MIN. The precedent to mirror is the natural_key stage's
    confidence=1.0 for an exact deterministic key hit; a deterministic
    activity+unit(-qualifier-family)+basis lookup is that same class of decision. I did not invent a
    threshold unilaterally — confirm or explicitly delegate this before wiring the alternative path.

PART 2 — deterministic basis policy (the PO rule; applied only where appropriate)
  source_basis(evidence) → "gross" | "net" | None from explicit source-only evidence —
    gross: "Gross CV" | "GCV" | "Gross calorific value";  net: "Net CV" | "NCV" | "Net calorific value"
    (never inferred from unrelated words; absent ⇒ None)
  candidate basis from the factor's own unit: split_qualified_unit(factor.unit)[1]; selection order:
    source gross → Gross-qualified candidate · source net → Net-qualified candidate ·
    source unqualified → the factor set's documented default basis = **Net / NCV**
  Application scope: CV-based fuel candidates (natural gas) ONLY — electricity kWh, water, diesel and
    waste selection semantics must not be altered by this policy.
  Determinism: sort candidates by a stable data-derived key (e.g. factor id) before choosing so the
    result never depends on enumeration order; assert it in tests (required test 8).
```

## Five-row oracle (D-A row) — NOT RUN in this window
```text
Row 1 'Gas usage 5,362.2000 kWh' → expected: Natural gas · unqualified kWh → Net CV default ·
      deterministic · DEFRA-2025 aggregate factor on kWh (Net CV)   |  RESULT: not exercised
Rows 2–5 are controls and must not change under D-A                |  not exercised
No factor was selected and no match status is claimed for any row.
```

## Tests — designed, not written (the 14 required cases map onto the design above)
```text
1 kWh discovers …(Gross CV) · 2 kWh discovers …(Net CV) · 3 explicit Gross CV → Gross ·
4 explicit GCV → Gross · 5 explicit Net CV → Net · 6 explicit NCV → Net ·
7 unqualified NG kWh → Net · 8 no first-enumerated selection (order-independent) ·
9 Gross/Net are not a unit conversion · 10 027 family protections intact ·
11 electricity kWh matching unbroken · 12 non-qualified matching intact ·
13 031 factor-set context intact · 14 SEAI NCV terminology compatible
planned file: backend/tests/unit/services/test_d_a_natural_gas_basis.py (+ real-DB oracle run for row 1)
```

## Regression / cleanup / impact
```text
tests added/executed this window : NONE (no code changed) → no new failures possible; nothing presented
                                   as integration evidence
023 / 026 / 027 / 031            : not re-run (no code change); last green (023 candidates=5/items=5 ·
                                   026 16/16 · 027 75/75 · 031 factor-set 6/6)
cleanup                          : none required — nothing created
production impact                : NONE — no production access/upload/job/queue/DB write/EF change/
                                   deployment/Render/Vercel change; protected job
                                   9ef61662-1c0a-497a-b5e9-c179e2134784 untouched; all DB access was
                                   read-only against the LOCAL authoritative database
P1                               : SHADOW (unchanged)
known limitations                : (a) D-A unimplemented; (b) the recovery-confidence convention in the
                                   narrower Part-1 path needs confirmation or delegation; (c) the real-DB
                                   oracle row has not been re-run since 029
```

## UPDATE — D-A PARTIAL IMPLEMENTATION DELIVERED (re-authorized window)

```text
commit 46a5534  feat(034-D-A): deterministic calorific-basis selection + stop Gross/Net being
               treated as interchangeable spellings      (pushed: c7ee7f4 → 46a5534)
files   backend/core/units.py  (+ new policy helpers, + qualifier-strictness fix)
        backend/tests/unit/test_d_a_natural_gas_basis.py  (26 tests)
```

### What was implemented (the deterministic policy half of D-A)
```text
source_calorific_basis(evidence) -> "gross" | "net" | None
  gross tokens: "Gross CV" · "GCV" · "Gross calorific value"
  net tokens  : "Net CV" · "NCV" · "Net calorific value"
  never inferred from unrelated words ("gross tonnage", "net payable" → None); a document
  declaring BOTH bases is ambiguous → None (caller then uses the default, never a guess).

DEFAULT_CALORIFIC_BASIS = "net"   ← the PO rule for unqualified natural-gas kWh (DEFRA and SEAI)

select_basis_factor(candidates, *, source_basis=None, default_basis="net")
  acts ONLY when the candidate set offers more than one distinct qualifier of the same base unit
  (the Gross/Net case) — so electricity, water, diesel and waste selection are provably untouched;
  otherwise returns None.  Ordering is by factor id before the qualifier map is built, so
  enumeration order can never decide the result (asserted in tests both directions).
```

### Root-cause defect found while validating D-A (and fixed)
```text
resolve_unit_for_factor("kWh (Gross CV)", "kWh (Net CV)")  previously returned "kWh (Net CV)"
  — i.e. the same-base qualifier rule adopted the FACTOR's spelling even when the two qualifiers
  were DIFFERENT methodological bases. A gross-based source row could therefore have been silently
  calculated on a net-based factor with the unit rewritten, with no basis decision anywhere.
Fix (generic, backend/core/units.py): the factor's spelling is now adopted only when the two are not
  differently qualified — unqualified ↔ qualified still tolerates (kWh ↔ kWh (Gross CV)) and equal
  qualifiers still agree; two different qualifiers leave the SOURCE unit unchanged so the basis
  policy (or the engine's UNIT_MISMATCH guard) decides. 027 unit-family semantics untouched:
  Gross/Net remain bases, never conversions.
```

### Test evidence (all green in this window)
```text
tests/unit/test_d_a_natural_gas_basis.py            26 passed  (covers required cases 3,4,5,6,7,8,9,10
                                                    plus explicit-Gross/GCV/Net/NCV detection, the
                                                    unrelated-word guard, ambiguity → None,
                                                    single-qualifier no-op, plain-kWh + alias regression)
tests/unit/test_units*.py (027 family-compat + qualifier + units)   100% pass
tests/unit/services (023 detector · 026 provenance · 029/031 · D-F) 0 failures
tests/unit/engines (calculation · matching)                          100% pass
no test was modified for green status; no new failures; no infrastructure failures
```

### Still outstanding for D-A (unchanged scope, next window)
```text
· wiring select_basis_factor + source_calorific_basis into the SHARED matching path
  (engines/matching_stages.py :63/:120/:162/:259/:333) so the qualifier-aware search DISCOVERS the
  Gross/Net candidates for an unqualified `kWh` request, with the confirmed convention
  confidence = 1.0 for a policy-selected candidate (PO decision, this window's brief);
· the real five-row oracle for row 1 ('Gas usage 5,362.2000 kWh' → Natural gas → Net CV factor,
  confidence 1.0) and the 023/026/027/031 oracle regression re-run;
· therefore the discovery half of Part 1 is NOT yet delivered: today the policy exists, is
  deterministic and is test-covered, but the unqualified-kWh request still cannot REACH the
  qualified candidates.
```

### Verdict for this window
**PARTIAL** — the D-A policy core is implemented, tested, committed and pushed, and one genuine
correctness defect (Gross/Net treated as interchangeable spellings) is fixed generically. The
discovery wiring in the shared matching stages and the real-DB five-row oracle evidence remain
outstanding. Production untouched; P1 SHADOW; working tree clean.


## Next PO gate
Authorise a dedicated D-A window with the Part-1 path chosen (preferred: qualifier-aware key/candidate
comparison in `engines/matching_stages.py`; alternative: service-layer recovery) and the
recovery-confidence convention confirmed if the alternative is chosen. Deliverables: the two code changes,
the 14 tests, the real-DB five-row oracle run for row 1, and the 023/026/027/031 regression re-run — then
report **D-A COMPLETE — READY FOR INDEPENDENT VERIFICATION**.

