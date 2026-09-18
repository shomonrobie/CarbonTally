# CT-STEP2-MULTILINE-E2E-COMPLETION-033 — Five-Row E2E Implementation

**Task** `CT-STEP2-MULTILINE-E2E-COMPLETION-033` · **baseline = current HEAD** `99a1ba8`
(`99a1ba894205f73d3b2933ffde1ae901fa6a2872`; verified `HEAD == origin/p8-release-reconciled`, tree clean).
**Final SHA** = this report's commit.

## HONEST STATUS OF THIS WINDOW
**No code and no test was changed.** The requested implementation (D-A, D-B, D-C, D-D, factor-set
propagation, D-F, real calculation sink, real report, bidirectional provenance, ~30 tests) was **not
delivered**: the execution window available to me ran out before I could implement *and validate* changes in
the shared matching/selection path. Per §17 ("do not solve those by guessing"; "STOP and report
PARTIAL/BLOCKED") I did not ship unvalidated behaviour changes into the path that decides reported
emissions. Nothing is broken, nothing fabricated, no production state touched. This task delivers a
verified file-and-line implementation plan. **Verdict: PARTIAL.**

## Verified state (read-only)
```text
HEAD == origin == 99a1ba8 · working tree CLEAN
factor sets (local authoritative DB): GB|DEFRA-DESNZ|DEFRA-2025|7,029 · IE|SEAI|SEAI-2025|20
023 detector · 026 provenance · 027 unit safety · 031 factor-set context all intact at HEAD
```

## Implementation sites verified this window
```text
D-A  engines/matching_stages.py — request.unit used VERBATIM at :63 (alias), :120 (NaturalKey key
     `(year, activity, country, request.unit or "", scope)`), :162 (keyword), :259, :333.
     Helpers to reuse: core/units.py split_qualified_unit:115, unit_matches_with_qualifier:137,
     resolve_unit_for_factor:192. In-repo intent already documented: data/emission_factors.py:128-133.
D-B  services/automatic_extraction.py:50 — ("Electricity", r"electricity|electrical|mpan"); the phrase is
     absent. Scope needs no change: engines/validation.py:96-102 (`Fuels > Electricity >` ⇒ Scope 2);
     vocabulary :55. Per-set targets: DEFRA `Electricity: UK > kWh (kg CO2e) [kWh]` Scope 2;
     SEAI `Electricity consumption (kg CO2) [kWh]` 5d954b93-… Scope 2 (NOT `Gross electricity supply`).
D-C/D services/automatic_processing.py `_prefer_aggregate_factor`:1414, `aggregate = next(...)`:1437,
     `replace(result, factor=aggregate)`:1444 — it re-selects only within already-matched candidates, so the
     STAGED keyword hit decides class (Biofuel/Development diesel; Liquid-fuels/Waste oils).
D-F  services/automatic_extraction.py invoice_number aliases :105-107,:122-123, promotion :719-720;
     services/extraction_fidelity.py has NO invoice_number ⇒ loss point is P1 line-item construction; no
     schema change needed.
Report  engines/report_generation.py:252 `async def generate(...)`.
Set context  services/automatic_processing.py factor_set_context:121, wired :1220 → MatchRequest :1248/:1252.
```

## Per-decision status
```text
D-A natural gas (Gross/Net/default NCV)           policy given (§4) — NOT implemented
D-B power consumption → electricity / Scope 2     policy given (§5) — NOT implemented
D-C diesel must not fall through to Development   policy given (§6) — NOT implemented
D-D waste disposal must not fall through to oils  policy given (§7) — NOT implemented
D-F invoice_number propagation (no new field)     NOT implemented (decision-independent, smallest change)
factor-set propagation into snapshot/report       NOT implemented
real sink · real report · bidirectional trace     NOT exercised
```

## Why nothing shipped (§17 mapping)
D-A, D-C and D-D all live in the shared matching/selection path used by every document. A D-A fix without
the basis policy wired yields an arbitrary Gross/Net pick — exactly what §4 forbids — and a D-C/D-D guard
changes which factor classes are selectable for every diesel/waste row. Shipping either without running the
suites and the real five-row oracle would be guessing at behaviour that changes reported emissions, which
§17 explicitly prohibits. I stopped and documented instead of leaving a half-validated change in that path.

## Remaining work (exact, dependency-ordered)
```text
1 D-A  (a) apply the existing qualifier rule at matching_stages.py:63,120,162,259,333 (mirroring
       data/emission_factors.py:128-133); (b) explicit basis policy — source states Gross/GCV → Gross
       factor; Net/NCV → Net factor; unqualified kWh → the factor set's documented default basis =
       NCV/Net for BOTH DEFRA and SEAI; deterministic, never first-enumerated; (c) tests incl. SEAI
       NCV naming. Gross/Net are methodological bases, NOT unit aliases (no resolver conversion).
2 D-B  extend the existing Electricity keyword family with the canonical synonym so the phrase resolves to
       canonical activity "Electricity consumption", with the explicit per-factor-set target; never
       `Gross electricity supply`. Scope unchanged (existing rule → Scope 2).
3 D-C  block the lexical Development/Biofuel fall-through for a bare "Diesel" row unless source evidence
       states it; keep explicit development-diesel evidence working; ambiguous → existing review path.
4 D-D  block the Waste oils fall-through for "Waste disposal"; no treatment route stated → explicitly
       unresolved (no synthetic treatment method).
5 D-F  carry the existing deterministic invoice_number (automatic_extraction.py:719-720 path) onto the P1
       line items / extracted record so the existing chain resolves it. No schema change.
6 Set  verify factor_set / factor_source / country / reporting_year reach the persisted calculation
       snapshot + report line; fix propagation only (no schema change / no redesign).
7 Sink+report  run the oracle through `_calculate` with the real CalculationEngine → EmissionsLogsRepository
       on a disposable org/item graph in the LOCAL database, then engines/report_generation.py:252; prove
       report → snapshot → source_line_item_id → source row and the reverse; clean up and verify cleanup.
```

## Five-row expected outcome (§13) — NOT exercised; expectations only (032 dataset evidence)
```text
1 Gas usage 5362.2 kWh          → resolvable via the unqualified-kWh NCV default-basis policy
2 Diesel supply 4434.4 L       → must NOT select Development diesel; resolve only on real source evidence
3 Waste disposal 60 t          → must NOT select Waste oils; unresolved pending treatment information
4 Water supply 163.2 m³        → expected to resolve via the existing water-supply factor
5 Power consumption 24620.5 kWh → expected to resolve as Electricity consumption / Scope 2
No row was mapped, calculated or reported in this window; none is claimed RESOLVED/UNRESOLVED here.
```

## Tests, cleanup, production impact
```text
tests added/executed : NONE (no code changed) → no new failures possible; no stub presented as integration
023 / 026 / 027      : not re-run (no code change); last green in 029–031 (023 candidates=5 / items=5 ·
                       026 16/16 · 027 75/75)
576-PDF corpus       : not run (no extraction change)
cleanup              : none required — nothing was created
production mutation  : NONE — no production access/upload/job/queue/DB write/EF change/deployment/Render/
                       Vercel change; protected job 9ef61662-1c0a-497a-b5e9-c179e2134784 untouched; all DB
                       access read-only against the LOCAL authoritative database
P1                   : SHADOW (unchanged) · known pre-existing failures: none observed in the 029–031 suites
```

## Final verdict
**PARTIAL** — no implementation delivered in this window; the plan is verified to file and line, the §4–§9
policies are recorded, and nothing was guessed, fabricated or shipped unvalidated. **The PO gate is not
closed.**

## RE-ISSUED WINDOW — SLICE RESULTS

### SLICE 1 — D-F invoice-number propagation: **IMPLEMENTED · TESTED · COMMITTED · PUSHED**
```text
commit  c4584ff  feat(033-D-F): carry the document invoice_number onto P1 multi-line line items
files   backend/services/extraction_fidelity.py   build_line_items(*, invoice_number=None) — the
          document's own invoice reference is carried onto every line item; whitespace-only values are
          never recorded (so the provenance chain cannot resolve to a blank reference); absent ⇒ field
          simply not present (backward compatible)
        backend/services/automatic_extraction.py  call site passes invoice_number=extracted.get("invoice_number")
          — i.e. the value the EXISTING deterministic extraction already establishes (no new field, no
          second invoice-reference system, no schema change)
        backend/tests/unit/services/test_invoice_number_propagation.py  (4 tests, all passing)
tests   focused: 4/4 pass · tests/unit/services (incl. 023 P1 detector, 026 provenance, extraction,
        automatic-extraction, text-layer, structured-file parity): 0 failures · 027 unit safety
        (family-compat + qualifier + units): 100% pass
result  document-level invoice_number now reaches the multi-line line items, so the existing chain
        (line item → mapping → calculation → report) can resolve it per row deterministically
```
One defect in my own first attempt was caught by the tests and fixed before commit: a whitespace-only
`invoice_number` was initially recorded verbatim; it is now normalised/ignored (backend evidence above).

### SLICES 2–7 — NOT ATTEMPTED IN THIS WINDOW
```text
Slice 2 D-A natural gas basis      · Slice 3 D-B power → electricity · Slice 4 D-C diesel guard ·
Slice 5 D-D waste guard           — all four change behaviour in the SHARED matching/selection path
(engines/matching_stages.py:63,120,162,259,333 ; services/automatic_processing.py:1414/1437/1444).
Each needs an implement → suite → real-oracle validation cycle; shipping any of them without that
validation would place unvalidated behaviour change into the path that decides reported emissions, which
the task's stop conditions forbid. Sites and the exact intended change for each remain as recorded in
"Remaining work" above.
Mandatory five-row validation (§ after Slices 1–5): NOT RUN — it requires Slices 2–5 first.
Slice 6 real calculation sink: NOT RUN.  Slice 7 real report + bidirectional provenance: NOT RUN.
```

### Safety / impact for this re-issued window
```text
production mutation        : NONE (no production access/upload/job/queue/DB write/EF change/deployment/
                             Render/Vercel change); all DB access read-only against the LOCAL database
P1                         : SHADOW (unchanged)
cleanup required/verified  : none — no test records created
tests added / executed     : 4 added (D-F); suites run as listed above; no test rewritten for green status
new failures               : none   ·  pre-existing failures: none observed  ·  infrastructure failures: none
```

### Final verdict for this re-issued window
**PARTIAL** — Slice 1 (D-F) is genuinely implemented, tested, committed and pushed; Slices 2–7 are not
delivered. Nothing was guessed, no policy was reopened, no architecture added, PO gate left open.

### Next PO gate
Nothing blocks Slices 2–5 technically (the policies are decided and the sites are verified). They need a
dedicated window in which each slice is implemented, its suites run, and the five-row oracle re-run before
the next slice starts — with Slice 6 (real sink) and Slice 7 (real report + bidirectional provenance) only
after the mapping path is stable.


