# P17 IMPLEMENT-05 — Scope 2 Calculation

**Task ID:** `P17-IMPLEMENT-05-20260925-SCOPE2-CALCULATION`
**Date:** 2025-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled`
**Starting SHA:** `cacb85019d2cfb0af0bb6cd89d145b013d8eb8e1` (verified actual HEAD before any change)
**Nature:** IMPLEMENTATION. No UI, no Scope 3, no architecture reconciliation, no migration, no RLS change, no production contact.

---

## 1. Task ID

`P17-IMPLEMENT-05-20260925-SCOPE2-CALCULATION`

## 2. Starting SHA

`cacb85019d2cfb0af0bb6cd89d145b013d8eb8e1` — the IMPLEMENT-04 head, confirmed with `git rev-parse HEAD`
before any edit. The only pre-existing working-tree change was `.gitignore`.

## 3. Ending SHA

`7dd4b08` — the final implementation commit; this report is its successor (§4).

## 4. Commit SHA(s)

| # | SHA | Message |
|---|---|---|
| 1 | `c04d38d` | `feat(p17): add the Scope 2 calculation service` |
| 2 | `a8d0186` | `feat(p17): expose the Scope 2 calculation API surface` |
| 3 | `7dd4b08` | `test(p17-05): cover the Scope 2 calculation vertical slice` |
| 4 | *(this report)* | `docs(p17): record IMPLEMENT-05 report` |

**Not pushed.** No amend/rebase/reset; all prior P17 commits preserved (`6f48f23`, `5713073`, `a852d6a`,
`cacb850`).

## 5. Scope 2 architecture implemented

```
INPUT (Scope2Input: activity, quantity, unit, geography, method, energy_type)
  → ACCOUNTING CONTEXT   (AccountingDimensions; attribution supplied server-side)
  → SCOPE2 VALIDATION    (domain.scope2: assert_scope2_dimensions, validate_scope2_method,
                          validate_energy_type — `fuel` refused)
  → FACTOR GOVERNANCE    (scope / year / geography checks over the matched factor)
  → FACTOR SELECTION     (existing Phase 4 MatchResult — NOT re-implemented)
  → MARKET-BASED GATE    (domain.contractual_instruments eligibility + DC-09 allocation)
  → CALCULATION          (existing CalculationEngine._compute_co2e — untouched)
  → CANONICAL SNAPSHOT   (engine → sink.save_snapshot, IMPLEMENT-04 columns)
  → EMISSIONS LOG        (engine → sink.create/save, same dimensions object)
  → PROVENANCE           (factor_id, factor year, source, energy_type, method, attribution)
  → LIFECYCLE            (unchanged; nothing is auto-marked REPORTABLE)
```

**No new calculation engine, no second persistence system, no duplicated factor selection.** The new
artefacts are two: `services/scope2_calculation.py` (validation + orchestration) and `api/v3_scope2.py`
(transport). Both delegate all arithmetic and persistence to the existing engine.

**Discovery that shaped the design:** `domain/scope2.py` and `domain/contractual_instruments.py` already
existed in full (from IMPLEMENT-MASTER-01) but had **no production consumer** — `grep` found zero imports of
`domain.scope2` outside its own docstring. Its rules were already correct, so this task **wired** the existing
domain rather than rewriting it.


## 6. Location-based implementation

`LOCATION_BASED` uses the existing emissions-factor infrastructure end to end. No separate Scope 2 factor
table was created: a Scope 2 factor already carries its own `scope`, `reporting_year`, `country`, `unit` and
`co2e_multiplier`, which is everything the calculation needs.

Guarantees, each asserted by test:

- **All four energy types work** (`electricity`, `heat`, `steam`, `cooling`), each producing the correct
  numerical result (100 kWh × 0.20700 = **20.700000 kg CO2e**) and persisting to both records.
- **The method and energy type are persisted** on the snapshot *and* the log, identically.
- **No instrument is required or permitted** — an instrument attached to a location-based claim is refused
  rather than ignored.
- **Owner and acting-for are recorded separately**; the log's `organization_id` (owner) is never derived from
  the attribution pair.

## 7. Market-based implementation

`MARKET_BASED` uses the existing P17 contractual-instrument domain (`ContractualInstrument`,
`InstrumentAllocation`, `assert_allocation_within_quantity`) and the existing eligibility rule
(`instrument.assert_can_support` → `instrument_is_eligible`).

The calculation **refuses** an instrument when it is:

| Condition | Result |
|---|---|
| inactive (retired/cancelled) | `InstrumentEligibilityError` — an already-claimed certificate must not be claimed again |
| incompatible geography | `InstrumentEligibilityError` |
| incompatible vintage/year | `InstrumentEligibilityError` — the factor-year guard applied to instruments |
| incompatible energy type / method | `InstrumentEligibilityError` (a location-based result can never be instrument-backed) |
| insufficient allocation | `InstrumentEligibilityError` — allocation must equal the consumption quantity |
| invalid ownership/tenant | `AccountingDimensionError` — the instrument must belong to the data-owning organization |
| over-allocation (DC-09) | `InstrumentOverAllocatedError` |
| unit mismatch | `AccountingDimensionError` — 500 kWh cannot be allocated against a 500 MWh instrument |

**A market-based request is never silently downgraded.** When the instrument is missing the service raises an
explicit error ("the grid-average figure is a different claim and is never substituted automatically") instead
of computing a location-based number. Asserted by test.

**Methodologies deliberately NOT invented:** no REC/REGO/residual-mix calculation methodology was implemented,
matching the architecture's deferral. The service evaluates *whether a supplied instrument may support the
claim*; it does not model certificate markets.

## 8. Energy-type handling

The canonical vocabulary is used verbatim from `domain.scope2.EnergyType`: `electricity`, `heat`, `steam`,
`cooling`. **`fuel` is rejected with its own explicit, deterministic reason** — "fuel is not a Scope 2 energy
type; fuel-borne energy is a Scope 1 or Scope 3 activity and is identified by its activity/factor
(ARCH-04 // ARCH-03 LOW-02)" — with `details = {field, received, allowed}`. Any other value raises
`ACCOUNTING_DIMENSION_INVALID` listing the allowed set. No additional energy types were invented.

## 9. Factor selection

Factor selection is **not duplicated**. The service consumes the existing Phase 4 `MatchResult` and builds the
request through the existing `CalculationRequest.from_match_result` bridge, preserving by construction:

1. **explicit operator selection where supplied** — the API route resolves the operator's chosen `factor_id`;
2. **customer-factor precedence** — `from_match_result` honours `factor_kind='customer_factor'` unchanged;
3. **compatible scope** — a non-Scope-2 factor is refused;
4. **compatible year** — a mismatched factor year is refused, **never silently substituted**;
5. **geography where required** — mismatch refused when both sides state one;
6. **compatible unit** — enforced by the engine's existing unit resolution/mismatch check.

An approved **customer factor** is exempt from the CarbonTally scope/year checks, deliberately: it is the
organization's own contracted value (P16 precedence) and is not an `emission_factors` row, so it has no
CarbonTally scope or year to compare. **No factor is ever selected merely because it is numerically
available.**

## 10. Contractual instrument handling

The service loads the instrument as a resolved `ContractualInstrument` and delegates every eligibility
decision to the existing domain rule — it does not re-implement it. `ContractualInstrument.assert_can_support`
→ `instrument_is_eligible` applies, in the architecture's order of strictness: the result must be
market-based; the instrument must be `active`; geography must match when both sides state one; vintage must
match when both sides state one. `None` on a comparison field means "not stated" and skips that check,
deliberately, rather than conflating "not recorded" with "known to be wrong".

## 11. Allocation / double-counting controls

| Control | Implementation |
|---|---|
| allocation cannot exceed available instrument quantity | `assert_allocation_within_quantity` (existing, DC-09) |
| the same allocation cannot be silently reused | the same guard sums `existing_allocations`, so re-claiming a consumed quantity raises `InstrumentOverAllocatedError` |
| instrument must belong to the authorized organization | explicit tenant check before eligibility |
| allocation must cover the claim | allocation must equal the consumption quantity (a partial allocation cannot support a full claim) |
| unit coherence | allocation unit must equal the instrument unit |
| location- and market-based results remain distinguishable | `scope2_method` is persisted on snapshot **and** log |
| one activity cannot be treated as two incompatible methods | a single calculation carries exactly one `scope2_method`; the DB `CHECK` refuses a Scope 2 row without one, and the method is never inferred or defaulted |
| method persisted with the calculation | written through IMPLEMENT-04's canonical dimension columns |

**No new parallel double-counting framework was created** — the existing DC-09 guard and P17 schema detectors
were used.

## 12. AccountingDimensions integration

Every Scope 2 calculation carries, via the existing `AccountingDimensions` object (no duplicate fields were
added to the request semantics beyond the attribution inputs):

`organization_id` (the owner, on the snapshot/log themselves), `performed_by_organization_id`,
`acting_for_organization_id`, `scope2_method`, `energy_type`, `data_quality`, `facility_id`, and
`source_snapshot_id` where applicable (left `None` here — Scope 2 derivation from another snapshot is a later
concern and was **not** guessed).

One additive change was needed: `CalculationRequest.from_match_result` gained an optional
`accounting_dimensions=None` parameter so the canonical bridge can carry them. Default `None` means every
existing caller is byte-for-byte unchanged.

## 13. Acting-for / security behaviour

- The **API route** resolves context via `ensure_record_owner_authorized(current_user, repos, organization_id)`
  and takes `actor_organization_id` / `acting_for_organization_id` **only** from that resolved context. No
  attribution value is read from the request body, so a forged acting-for is structurally impossible.
- The **service** accepts the attribution as resolved inputs and never derives the owner from them.
- A **cross-tenant instrument** is refused with `AccountingDimensionError` before any eligibility evaluation —
  acting-for context is never an entitlement.
- **No RLS was weakened; no service-role shortcut was used.**

Mapping to the required security matrix: direct customer → own org ✅ (owner authority); consultant → own org ✅
(context layer, IMPLEMENT-02); consultant → authorized client ✅; consultant → unauthorized client → 403 ✅
(IMPLEMENT-02, unchanged); client → own org ✅; forged acting-for ✅ (structurally impossible);
forged owner ✅ (re-authorised server-side); cross-tenant instrument ✅ (refused, tested).

## 14. API routes

`POST /api/v3/scope2/calculate` (`api/v3_scope2.py`), registered in the existing `api/router.py` include block.
It accepts Scope 2 activity input, **requires** `scope2_method` and `energy_type` (no defaults), resolves the
accounting context server-side, rejects unauthorized acting-for, executes the existing `CalculationEngine` via
the service, persists through the canonical pipeline, and returns the calculation identity/result. Invalid
Scope 2 requests surface the domain error via the existing `CarbonTallyError` envelope with structured
`details` (field, received, allowed).

The request identity is **deterministic**: `uuid5` over the calculation's canonical inputs, so an identical
repeat yields the same `request_id` (the P16 idempotency property applied to a path with no matching-engine
request id).

**Market-based via the API fails closed deliberately.** The P17-C schema (`public.contractual_instruments`,
`public.instrument_allocations`) exists, but **no data repository for it has been implemented** — a fact
discovered during this task. Loading the instrument from the request body would mean a *client-supplied*
organisation id deciding an accounting entitlement, which is precisely what must never happen. The route
therefore returns a 422 explaining the limitation, rather than guessing or silently downgrading. The
market-based calculation path itself **is** implemented and tested at the service layer (§7, §18).

## 15. Read-surface changes

The route returns a focused Scope 2 projection: `snapshot_id`, `request_id`, `organization_id`,
`acting_for_organization_id`, `performed_by_organization_id`, `scope`, `scope2_method`, `energy_type`,
`data_quality`, `factor_id`, `factor_kind`, `factor_year`, `co2e_kg`, `co2e_tonnes`, `methodology`,
`reporting_year`, `content_hash`.

**No existing read shape was changed.** IMPLEMENT-04 deliberately left the new columns out of
`_SNAPSHOT_COLUMNS` / `_LOG_COLUMNS`; that remains true and is reported as outstanding work (§21).

## 16. Provenance

A Scope 2 result retains: the source activity (`activity`, `activity_type`, `source_item_id`,
`source_line_item_id` passed through), the selected factor (`factor_id` or `customer_factor_id` with
`factor_kind`), the factor year and source (`factor.reporting_year`, `factor.factor_source`), the Scope 2
method and energy type, the acting-for and data-owner organizations, and the result (`co2e_kg`) with its
`content_hash`. **No evidence was fabricated.**

On evidence specifically: the canonical write already persists `source_item_id` / `source_line_item_id`, so
Scope 2 results are already linkable to evidence lines. **No upstream evidence writer exists** (IMPLEMENT-03's
finding, unchanged), so there is nothing for this task to integrate with yet; the lineage is preserved.

## 17. Lifecycle / reportability integration

**No lifecycle redesign.** The Scope 2 result persists as an emissions snapshot/log exactly like every other
calculation, so it is compatible with the existing
DRAFT → SUBMITTED → VALIDATED → CALCULATED → REVIEW → APPROVED → REPORTABLE progression. Reportability is
respected: **nothing here marks a result REPORTABLE merely because calculation succeeded** — no lifecycle
field is written by the new code at all.

One lifecycle-relevant gain: because a Scope 2 result now always carries a recorded `scope2_method`, a Scope 2
figure can no longer be reported without its accounting method, which the B1 disclosure model requires.

## 18. Tests with exact counts

`tests/unit/services/test_p17_05_scope2_calculation.py` — **28 tests, 28 passed, 0 failed.**

| Group | Coverage |
|---|---|
| Validation | missing method rejected; invalid method rejected; invalid energy type rejected; **`fuel` rejected with its deterministic reason**; Scope 1 factor rejected; wrong factor year rejected (never substituted); wrong geography rejected; unmatched factor rejected (8) |
| Location-based | all four energy types calculate + persist + correct numerics (20.700000 kg CO2e) + provenance; acting-for vs owner separation; instrument refused; instrument not required (7, incl. 4 parametrized) |
| Market-based | valid instrument+allocation succeeds; **missing instrument refused, not downgraded**; inactive rejected; wrong geography rejected; wrong vintage rejected; cross-tenant instrument rejected; insufficient allocation rejected; DC-09 over-allocation rejected; incompatible unit rejected (9) |
| Regression / double-counting | methods distinguishable; repeated identical requests share request identity + content hash; Scope 1 unaffected; dimensions do not change the content hash (4) |

These exercise the real service and the real engine; the sink is an in-memory stand-in for the repository, as
in the existing engine tests.

## 19. Full-suite result

**Attempted; the full suite did not complete within the execution budget. Recorded honestly; no full-suite
verification is claimed.**

| Run | Result |
|---|---|
| New P17-05 tests | **28 passed, 0 failed** |
| `tests/unit/engines tests/unit/domain tests/unit/services tests/unit/api` | **completed**; 6 failures, all proven pre-existing (§20) |
| `tests/unit tests/integration` (full suite) | **NOT completed** — exceeded the command time budget, as in IMPLEMENT-04 |
| `tests/integration/*` | DB-dependent (needs a live database and the destructive harness, which was **not** run) |

**Exact total/passed/failed/skipped/errors figures for the full suite were NOT obtained.** I am not reporting
numbers I did not measure. All four affected suites did run to completion.

## 20. P16 regression result

**NO REGRESSIONS. Proven by a baseline comparison, not asserted.**

The adjacent suites produced exactly 6 failures: `test_extraction_suggestions.py` (3) and
`test_review_sla_surfaces.py` (3). I verified these are **pre-existing** by stashing all my changes
(`git stash push --include-untracked -- backend/`) and re-running both files against the unmodified tree: **the
identical 6 tests failed.** The stash was then popped and the changes restored.

The 3 `test_review_sla_surfaces` failures match the known baseline issue recorded in IMPLEMENT-02 (the shared
module-level `include_router` block not populating `router`).

P16 behaviour explicitly re-verified by test: **Scope 1 calculations still work and are unaffected**;
`AccountingDimensions` remain `None` for a Scope 1 request; and **Scope 2 dimensions do not change the content
hash**. The only production-code change to a shared path is the optional `accounting_dimensions=None`
parameter on `from_match_result`, which defaults to `None` and is inert for every existing caller.
**No test was skipped, deleted or relaxed.**

## 21. Known incomplete work

1. **Market-based through the API** — implemented and tested at the service layer, but the HTTP route fails
   closed because **no `contractual_instruments` data repository exists**. This is the single highest-value
   next step and it is small: a repository over `public.contractual_instruments` /
   `public.instrument_allocations` (schema already exists from P17-C), after which route wiring is
   straightforward.
2. **Read projection for the new columns** — `_SNAPSHOT_COLUMNS` / `_LOG_COLUMNS` still omit the P17
   dimensions, so they are written but not returned by the existing snapshot/log read queries. The Scope 2
   route returns them from the in-memory result; other consumers will need them exposed.
3. **Full-suite run** — not completed (§19).
4. **`source_snapshot_id` derivation** — accepted as an input but never populated here; Scope 2 derivation
   lineage is a later concern and was not guessed.
5. **No match-against-database test** — the repository write path is verified through the engine with an
   in-memory sink; live SQL parameter mapping is verified by construction, not by a real INSERT.

## 22. Blocked / deferred work

| Item | Status | Reason |
|---|---|---|
| Market-based HTTP route | **BLOCKED** | No instrument repository exists; trusting client-supplied instrument ownership would break tenant isolation |
| Automatic factor matching for Scope 2 via the API | Deferred | The route requires an explicit `factor_id`; the matching-engine path is available at the service layer via `MatchResult` |
| Instrument allocation **persistence** | Deferred | The DC-09 check runs against supplied `existing_allocations`; writing allocation rows needs the missing repository |
| Report-version / review-assignment attribution | Deferred (IMPLEMENT-03/04) | Unresolved ownership semantics for those tables |
| Customer-document / evidence-line-item upstream writers | Blocked (IMPLEMENT-03) | No application write path exists |
| `review_audit_trail` acting-for propagation | Blocked (IMPLEMENT-04) | Trigger-owned; needs a reviewable migration |
| Scope 3, UI, ARCH-07, final P17 verification | Out of scope by instruction | Later tasks |

**None of these blocked Scope 2 implementation**, as the task directed.

## 23. Production-contact statement

**NO PRODUCTION SYSTEM WAS CONTACTED.**

- No production database, credential, migration or deployment; no production customer data.
- No external production API call; nothing pushed to any remote.
- **No database was opened at all.** Every assertion used in-memory sinks and the existing unit suite. No
  migration was created or applied.
- The Demo Lab, `carbontally_qa_phase8`, `carbontally_test` and every other persistent local database were
  untouched, and the **destructive integration harness was not run** (F-046-1 respected).

## 24. Final implementation verdict

```
P17_IMPLEMENTATION_PARTIAL
```

**Why PARTIAL.** The Scope 2 calculation itself — location-based and market-based, validated, attributed,
persisted through the canonical pipeline, with factor governance, instrument eligibility, allocation
double-counting controls and P16 preservation — **is implemented and tested (28/28)**. But two things inside
this task's own scope are unfinished:

- the **market-based HTTP path fails closed** because the instrument repository it needs does not exist (§14,
  §21) — the calculation path is tested, the route is not wired;
- the **full-suite regression run did not complete** (§19).

Claiming COMPLETE would be false, and the task instructs explicitly: *"Do not inflate the verdict."*

**What is genuinely delivered and verified:**

- a working **Scope 2 vertical slice** through the canonical accounting write pipeline — one engine, one
  persistence path, no duplication;
- **both methods**, with the method persisted on the snapshot *and* the log, **never inferred, never
  defaulted, never silently downgraded** — a market-based request with no valid instrument is *refused*, not
  recomputed;
- **`fuel` rejected deterministically** as a Scope 2 energy type, with all four canonical energy types working;
- **factor governance preserved**: wrong scope, wrong year and wrong geography are refused, and a factor year
  is never silently substituted;
- **the existing DC-09 instrument controls wired in**, including cross-tenant refusal, inactive instruments,
  vintage/geography compatibility and over-allocation;
- **P16 verified empirically** by a stash-based baseline comparison, not by assertion.

**The next task (Scope 3 supported/partial categories) can extend this same pipeline**, and the smallest
high-value follow-up is the `contractual_instruments` repository that would unlock the market-based HTTP route.

**No `PASS`, `E2E VERIFIED` or `PRODUCTION READY` claim is made.**



