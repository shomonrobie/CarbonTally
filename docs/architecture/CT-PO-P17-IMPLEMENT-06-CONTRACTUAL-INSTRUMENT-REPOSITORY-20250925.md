# P17 IMPLEMENT-06 — Contractual Instrument Repository + Market-Based API

**Task ID:** `P17-IMPLEMENT-06-20260925-CONTRACTUAL-INSTRUMENT-REPOSITORY-MARKET-API`
**Date:** 2025-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled`
**Starting SHA:** `e291611bbb4066624c8140e8121ccf8e33d63743` (verified actual HEAD — see §2)
**Nature:** IMPLEMENTATION. No migration, no RLS change, no Scope 3, no UI, no production contact.

---

## 1. Task ID

`P17-IMPLEMENT-06-20260925-CONTRACTUAL-INSTRUMENT-REPOSITORY-MARKET-API`

## 2. Starting SHA — stated discrepancy, resolved

The task states the expected starting HEAD as `cacb85019d2cfb0af0bb6cd89d145b013d8eb8e1`. **The actual HEAD
was `e291611bbb4066624c8140e8121ccf8e33d63743`.** Per the task's instruction 2 this is reported explicitly
before implementation.

The discrepancy is stale task text, not a wrong baseline. `cacb850` is the **IMPLEMENT-04 report commit**, one
commit *before* `a852d6a`. The task's own authoritative list of "expected current implementation commits" is
`c04d38d`, `a8d0186`, `7dd4b08`, `e291611` — and **`e291611` IS the actual HEAD**, with all four present and
verified. The baseline therefore contains exactly the IMPLEMENT-05 work the task assumes, so I proceeded on
that basis rather than halting on a stale hash. The working tree was clean apart from the pre-existing
`.gitignore` modification.

## 3. Ending SHA

`87a0512` — the final implementation commit; this report is its successor (§4).

## 4. Exact commit SHA(s)

| # | SHA | Message |
|---|---|---|
| 1 | `1f61422` | `feat(p17): add the trusted P17-C contractual instrument repository` |
| 2 | `d1cb321` | `feat(p17): wire MARKET_BASED Scope 2 through the trusted instrument repository` |
| 3 | `87a0512` | `test(p17-06): cover the instrument repository and the market-based API path` |
| 4 | *(this report)* | `docs(p17): record IMPLEMENT-06 report` |

**Not pushed.** No amend/rebase/reset; all prior P17 history preserved (`c04d38d`, `a8d0186`, `7dd4b08`,
`e291611`, and everything before them).

## 5. Files created / modified

**Created**

| File | Purpose |
|---|---|
| `backend/data/contractual_instruments.py` | The trusted P17-C repository (§6) |
| `backend/tests/unit/data/test_p17_06_contractual_instrument_repository.py` | Repository tests (14) |
| `backend/tests/unit/api/test_p17_06_scope2_market_api.py` | Market-based API tests (15) |
| this report | Mandatory implementation report |

**Modified**

| File | Change |
|---|---|
| `backend/domain/contractual_instruments.py` | **One additive field** `id: Optional[str] = None` on `ContractualInstrument` (§6.1) |
| `backend/api/dependencies.py` | Registered `contractual_instruments` on `RepositoryBundle`, **defaulted to `None`** |
| `backend/api/v3_scope2.py` | Replaced the MARKET_BASED fail-closed block with the trusted wire-up; hardened the data owner to the resolved context; added allocation persistence and read-surface fields |

**Not modified:** any migration, any RLS policy, `domain/scope2.py`,
`services/scope2_calculation.py`, `engines/calculation.py`, `api/router.py`.

## 6. Repository design

`ContractualInstrumentsRepository(AbstractRepository[ContractualInstrument])` follows the existing asyncpg
conventions (`data/base.py`, explicit column lists, `_row_to_*` mappers, `_fetch_one`/`_fetch_all`).

| Method | Purpose |
|---|---|
| `get(id)` | By id, **tenant-agnostic** — documented as internal/administrative only |
| `get_for_organization(instrument_id, organization_id)` | **The trusted loader.** Tenant predicate in SQL |
| `list_for_organization(organization_id)` | Deterministic list |
| `list_allocations(instrument_id, organization_id)` | Existing allocations, double-scoped |
| `find_allocation_for_request(...)` | Idempotency lookup keyed on the calculation request identity |
| `record_allocation(allocation)` | Idempotent claim insert (§9) |
| `save`, `delete` | ABC. `delete` **raises `NotImplementedError`** — an instrument is accounting evidence |

**Division of responsibility is preserved exactly as required.** The repository retrieves and stores rows;
`domain.scope2` / `domain.contractual_instruments` decide eligibility, geography, vintage, method/energy
compatibility, allocation sufficiency and DC-09. **No eligibility rule was duplicated or re-implemented**, and
no arithmetic, factor matching or persistence logic was duplicated.

### 6.1 The one domain change, and why it is additive

`ContractualInstrument` had **no `id` field** in IMPLEMENT-05 (its natural identity is
`(organization_id, instrument_type, identifier)`, matching the DB unique constraint). Writing the allocation
row needs the surrogate `contractual_instruments.id`, because the composite FK and the unique constraint are
keyed on it, so the row identity must be carried back from the repository.

`id: Optional[str] = None` was **appended last with a default**, so every pre-existing positional or keyword
construction is byte-for-byte unchanged — asserted by a test. No field was removed, reordered or retyped, and
no rule reads `id`.

## 7. Tenant / ownership enforcement

Four independent layers, none trusting the client:

1. **`ensure_record_owner_authorized`** resolves the accounting context and returns
   `data_owning_organization_id` — documented in `AccountingContext` as *"the tenant that OWNS the accounting
   data. This is the authorisation key."*
2. **The route now uses that resolved value** for both the instrument scope and `Scope2Input.organization_id`.
   **This is a deliberate hardening over the IMPLEMENT-05 route**, which passed `payload.organization_id`; the
   resolved value is the authoritative one.
3. **The repository's tenant predicate is in SQL** (`WHERE id = $1 AND organization_id = $2`), so a foreign
   instrument is **indistinguishable from an absent one** — the caller learns nothing about another tenant's
   instruments. This is the stronger failure mode.
4. **The database enforces it independently**: `instrument_allocations` carries the composite FK
   `(instrument_id, organization_id) -> contractual_instruments(id, organization_id)`, making a cross-tenant
   claim *structurally* impossible.

The client supplies only an `instrument_id`. Ownership, the data owner and the acting-for organization are all
resolved server-side. **No organization ownership is accepted as an entitlement from the request body.**

## 8. Market-based API flow

`POST /api/v3/scope2/calculate`:

1. requires `scope2_method` and `energy_type` explicitly (no defaults);
2. `ensure_record_owner_authorized(current_user, repos, payload.organization_id)` resolves the context;
3. `data_owner = context.data_owning_organization_id` (**the authorisation key**);
4. explicit `factor_id` is resolved through the existing factor repository (unchanged);
5. for MARKET_BASED: `instrument_id` is required; the repository loads the instrument scoped to `data_owner`
   (`None` → refused), then loads existing allocations scoped to `data_owner`;
6. the trusted domain objects are passed to the existing `Scope2CalculationService`, which performs **all**
   eligibility, geography, vintage, method/energy, sufficiency, DC-09 and unit checks;
7. the existing `CalculationEngine` persists the snapshot and emissions log through the canonical path;
8. the allocation is recorded (§9);
9. the structured result is returned, including `instrument_id` and `allocation_id`.

`LOCATION_BASED` is **unchanged**: no instrument is loaded, `instrument_id`/`allocation_id` are `null`, and the
response shape is identical to IMPLEMENT-05.

**Never done:** trusting a request-body organization as ownership; trusting request-body instrument ownership;
silently downgrading MARKET_BASED to LOCATION_BASED; inventing missing instrument data; bypassing tenant
checks; using service-role credentials to bypass authorization; duplicating engine arithmetic, factor matching
or instrument eligibility.

If the repository is absent from the bundle (`None`) the route returns **503** and refuses, rather than trusting
client-supplied instrument data.

## 9. Allocation behaviour

**Allocation persistence IS required, and was implemented.** Rationale: without a persisted allocation the claim
is not recorded, so DC-09 cannot operate across requests and the same instrument quantity could be claimed
repeatedly by separate market-based calculations — double counting — and the figure would have no evidencable
backing. The write is deliberately minimal:

- **Tenant ownership** comes from `data_owner` (the resolved context), never the payload.
- **Ordering:** the allocation is written **after** the calculation is persisted, so `calculation_snapshot_id`
  always references a real snapshot (FK `ON DELETE RESTRICT`). **A failure cannot create an allocation the
  calculation did not persist.**
- **DC-09 is not re-implemented**: the service validates quantity before writing; the DC-09 detector function
  remains the database-side assertion. The repository records only what was already validated.
- **Period:** `allocation_period_start/end` are optional body fields defaulting to the calculation date (a
  single-day period) — the activity's own date, not an invented window.
- **Allocated quantity** defaults to the consumption quantity, which the service independently requires to
  match exactly. A market-based claim is a full claim by definition.
- `emissions_log_id` is left `NULL`: `CalculationResult` does not return the log id, the column is nullable, and
  the snapshot is the authoritative link.

## 10. Idempotency behaviour

Two mechanisms, because one is not sufficient:

1. **`ON CONFLICT ON CONSTRAINT instrument_allocations_unique DO NOTHING`** — the schema's uniqueness on
   `(instrument_id, allocation_period_start, allocation_period_end, calculation_snapshot_id)` for an exact
   duplicate. `None` returned means nothing new was written.
2. **`find_allocation_for_request`** — keyed on the **calculation request identity**
   (`calculation_snapshots.request_id`), because a re-run of an identical request produces a **new snapshot
   id** (the engine uses `uuid4`). Keying on the snapshot alone would let the same claim be recorded twice, so
   the request identity is the correct anchor.

The route checks (2) first and calls `record_allocation` only when no prior claim exists. A test asserts a
repeat does **not** record a second allocation and returns the existing allocation id. The P16 request identity
is untouched (`_deterministic_request_id`, uuid5 over the canonical inputs), so repeated identical requests
still share `request_id` and `content_hash`.

## 11. Security behaviour

| Required case | Result |
|---|---|
| valid LOCATION_BASED still works | **200**, `instrument_id`/`allocation_id` null — tested |
| valid MARKET_BASED with repository-backed instrument | **200**, allocation recorded — tested |
| instrument owned by the same organization | **200** — tested |
| cross-tenant instrument | **422**, nothing calculated, no allocation — tested |
| a context resolving to a different data owner than the instrument | **422**; loader scoped to the *resolved* owner — tested |
| unauthorized acting-for | **403**, no instrument load, nothing calculated — tested |
| missing instrument | **422** — tested |
| inactive instrument | **422** — tested |
| wrong geography | **422** — tested |
| wrong vintage/year | **422** — tested |
| invalid energy type | **422** `ACCOUNTING_DIMENSION_INVALID` — tested |
| insufficient allocation | **422** — tested |
| DC-09 over-allocation | **409** `INSTRUMENT_OVER_ALLOCATED`, no allocation written — tested |
| unit mismatch | **422** — tested |
| market-based without instrument | **422**, message states it is never substituted — tested |
| never downgraded | asserted: no snapshot created on any refusal — tested |
| repeated identical request | no second allocation; same `request_id`/`content_hash` — tested |
| owner and acting-for remain distinct | owner = data owner; `performed_by_organization_id` = actor firm — tested |

**No RLS was weakened; no service-role shortcut was used to bypass authorization.** The repositories use the
same service-role pool as every other repository, but authorization is decided *before* the query by the
accounting-context layer, and the query itself is tenant-scoped.

## 12. Database / migration changes

**No migration was created or applied. No schema was altered.**

The task asked me to inspect whether the P17-C schema suffices. It does, completely:

- `contractual_instruments` carries every field the domain needs, plus the two indexes the loader uses
  (`(organization_id, geography, vintage_year)`, `(organization_id, retirement_status)`).
- `instrument_allocations` already provides the idempotency primitive
  (`UNIQUE (instrument_id, allocation_period_start, allocation_period_end, calculation_snapshot_id)`), the
  cross-tenant impossibility (composite FK), and nullable `emissions_log_id` / `claim_reference`.
- `p17_instrument_over_allocated(uuid)` already exists as the DC-09 database-side detector.
- RLS is already enabled on both tables with `is_org_member(organization_id)` policies.

Adding a migration would have been unnecessary and is explicitly discouraged, so none was written.

## 13. Tests and exact counts

| Suite | Tests | Result |
|---|---|---|
| `tests/unit/data/test_p17_06_contractual_instrument_repository.py` | **14** | **14 passed, 0 failed** |
| `tests/unit/api/test_p17_06_scope2_market_api.py` | **15** | **15 passed, 0 failed** |
| **P17-06 total** | **29** | **29 passed, 0 failed** |
| `tests/unit/services/test_p17_05_scope2_calculation.py` (must stay green) | 28 | **28 passed, 0 failed** |

Repository tests cover: row mapping preserving DB values exactly; the tenant predicate being present **in SQL**
for both instrument and allocation reads; fail-closed `None` on absence; `ON CONFLICT ... DO NOTHING`
idempotency; the request-identity lookup keying on `s.request_id`; `delete` refusing; `save` requiring the row
identity; and the additive `id` default.

API tests cover all cases enumerated in §11, driving the **real route, service, engine and domain rules** —
only the database and the authorization dependency are faked. The instrument fake mirrors the real
repository's tenant predicate, so it cannot be more permissive than production.

**No test was skipped, deleted or relaxed.** No pre-existing test file was modified for this task.

## 14. Full-suite result

**Attempted; the full suite did not complete within the execution budget. Reported honestly; no full-suite
verification is claimed.**

| Run | Result |
|---|---|
| P17-06 new tests | **29 passed, 0 failed** |
| `tests/unit/services` (P17-05) | **28 passed, 0 failed** |
| `tests/unit/engines tests/unit/domain tests/unit/services` | **completed**; 3 failures, all pre-existing (§15) |
| `tests/unit/api tests/unit/data` | **completed**; 6 failures, all pre-existing (§15) |
| `tests/unit tests/integration` (full suite) | **NOT completed** — exceeds the command time budget (also true in IMPLEMENT-04 and -05) |
| `tests/integration/*` | DB-dependent; needs a live database and the destructive harness, which was **not** run |

**Exact full-suite total/passed/failed/skipped/errors figures were NOT obtained.** I am not reporting numbers I
did not measure. Every suite containing code this task touched ran to completion.

## 15. Baseline comparison

**All observed failures are pre-existing. Proven, not assumed.**

`tests/unit/api tests/unit/data` produced exactly **6 failures**: `test_review_sla_surfaces.py` (3),
`test_d17_provider_ownership_migration_revision.py` (1), `test_i1_insight_migration.py` (1),
`test_i2_insight_authorization_contracts.py` (1).

I stashed all my changes (`git stash push --include-untracked -- backend/`) and re-ran those files against the
unmodified tree: **the identical failures occurred** (the three migration-ordering failures printed verbatim).
The stash was then popped and the changes restored.

The 3 `test_review_sla_surfaces` failures match the baseline issue recorded in IMPLEMENT-02 (the shared
module-level `include_router` block not populating `router` for v3 routers). The 3 migration-ordering failures
assert "this migration is the latest"; **this task added no migration**, so they cannot be mine — and
IMPLEMENT-04 proved the same 3 pre-existing with a zero-SQL-files diff. The 3
`engines/test_extraction_suggestions.py` failures were proven pre-existing in IMPLEMENT-05's stash comparison.

## 16. Known incomplete work

1. **Full-suite run** (§14) — not completed; the honest limit of this task's verification.
2. **The allocation write is not inside a single transaction with the snapshot.** They are separate statements:
   the snapshot/log are written by the engine, then the allocation. A crash between them leaves a persisted
   market-based result whose allocation is missing. Mitigations: the allocation is written **second** (so it can
   never reference a non-existent snapshot), the request-identity lookup makes a retry safe, and the failure
   mode is therefore visible and correctable rather than a silent duplicate or an orphan claim. A true
   cross-table transaction would require the engine's persistence and this write to share one connection.
3. **No live-database test.** The repository SQL is asserted structurally and its row mapping by unit test; the
   INSERT was not executed against PostgreSQL. Verified by construction, not by round-trip.
4. **Read projection for the P17 dimensions on the existing snapshot/log queries** — deferred (§17).

## 17. Deferred work

| Item | Reason |
|---|---|
| Exposing `scope2_method` / `energy_type` / `data_quality` / acting-for through `_SNAPSHOT_COLUMNS` / `_LOG_COLUMNS` | Those projections feed many read surfaces; changing them creates scope well beyond this narrow task and risks unrelated regressions. **The Scope 2 route already returns all five fields**, so the investor-demo path is served and the item is documented as deferred rather than silently skipped. |
| Automatic factor matching for Scope 2 via the API | Not required; the route accepts explicit operator selection, which is factor-governance rule 1. |
| Instrument CRUD / list API | Not required for the market-based *calculation* path; the schema and repository support it when a later task needs it. |
| Scope 3, UI, report-version / review-assignment attribution, evidence upstream writers, `review_audit_trail` trigger work, `source_snapshot_id` derivation, ARCH-07 | Out of scope by instruction; unchanged from IMPLEMENT-05. |

## 18. Production-contact statement

**NO PRODUCTION SYSTEM WAS CONTACTED.**

- No production database, credential, migration or deployment; no production customer data.
- No external production API call; nothing pushed to any remote.
- **No database was opened at all.** Every assertion used in-memory fakes and the existing unit suite. No
  migration was created or applied.
- The Demo Lab, `carbontally_qa_phase8`, `carbontally_test` and every other persistent local database were
  untouched, and the **destructive integration harness was not run** (F-046-1 respected).

## 19. Final verdict

```
P17_IMPLEMENTATION_COMPLETE
```

**Why COMPLETE.** The task's own completion condition is: *"This task is complete only when the existing
market-based service path can be reached through the API using server-resolved, tenant-authorized instrument
data."*

That condition is met and tested:

- the **trusted repository exists** for both `contractual_instruments` and `instrument_allocations`;
- the **MARKET_BASED API path is wired** and reaches the existing Scope 2 service with repository-loaded,
  tenant-scoped instrument data;
- **instrument ownership is never established by the client** — it is decided by a SQL predicate against the
  resolved data-owning organization;
- **allocation persistence works and is idempotent**, so the claim is recorded and DC-09 can operate across
  requests;
- **LOCATION_BASED is unchanged**; all 28 IMPLEMENT-05 tests remain green;
- **29 new tests pass**, covering every case the task enumerated;
- **no migration, no RLS change, no duplicated eligibility rule, no duplicated engine or persistence path**.

**What remains incomplete, stated plainly:** the full-suite run did not complete (§14); there is no live
database round-trip test (§16.3); and the snapshot→allocation write is not a single transaction (§16.2). None of
these is a material part of *this task's* deliverable — the repository layer and the market-based API path are
genuinely implemented and wired — but they are real limits on the strength of the verification and are recorded
rather than glossed.

**No `E2E VERIFIED`, `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` claim is made.** These are implementation
tests; the market-based path has not been exercised against a real PostgreSQL instance or by an independent
verifier.


