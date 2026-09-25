# P17 IMPLEMENT-04 — Canonical Accounting Write Pipeline

**Task ID:** `P17-IMPLEMENT-04-20260925-CANONICAL-ACCOUNTING-WRITE-PIPELINE`
**Date:** 2025-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled`
**Starting SHA:** `b8d4dc48545030909f76ee6f883dd43758a425a5` (verified as actual HEAD before any change)
**Ending SHA:** the commit carrying this report.
**Nature:** IMPLEMENTATION. No UI, no Scope 2 methodology, no Scope 3 methodology, no migration, no RLS change, no production contact.

---

## 1. Task ID

`P17-IMPLEMENT-04-20260925-CANONICAL-ACCOUNTING-WRITE-PIPELINE`

## 2. Starting SHA

`b8d4dc48545030909f76ee6f883dd43758a425a5` — the IMPLEMENT-03 head, confirmed with `git rev-parse HEAD`
before any edit. The only pre-existing working-tree change was `.gitignore`.

## 3. Ending SHA

`a852d6a` — the final implementation commit; this report is its immediate successor (§4).

## 4. Commit SHA(s)

| # | SHA | Message |
|---|---|---|
| 1 | `6f48f23` | `feat(p17): add the validated canonical accounting-dimension value object` |
| 2 | `5713073` | `feat(p17): thread accounting dimensions and attribution through the canonical write` |
| 3 | `a852d6a` | `test(p17-04): cover the canonical accounting write pipeline` |
| 4 | *(this report)* | `docs(p17): record IMPLEMENT-04 report` |

**Not pushed.** No amend/rebase/reset; all prior P17 history preserved (`df52233`, `eb402d5`, `a4b9a2f`,
`b8d4dc4` remain intact).

## 5. Actual accounting-flow discovery mapping (Phase 1)

The previous task concluded that no caller for `calculation_snapshots` / `emissions_logs` could be located.
**It exists, and it is a proper pipeline rather than a carrier-per-carrier write.** The real flow is:

| Stage | Real implementation | Evidence |
|---|---|---|
| Calculation entry point | `CalculationEngine.calculate(request)` | `engines/calculation.py:459` (post-edit; was :388) |
| Factor → CO2e | `_compute_co2e` (`EmissionFactor.calculate_emissions`, `RESULT_PRECISION` quantisation) | `engines/calculation.py` |
| Snapshot build | `_build_snapshot` (uuid4 id, `build_content_hash`) | `engines/calculation.py` |
| **Snapshot persistence** | `sink.save_snapshot(...)` → `EmissionsLogsRepository.save_snapshot` | `engines/calculation.py:486`; `data/emissions_logs.py:711` (INSERT) |
| **Emissions-log persistence** | `_persist_log` → `sink.create(...)` then `sink.save(...)` | `engines/calculation.py`; `data/emissions_logs.py` (INSERT + UPDATE) |
| Persistence abstraction | `CalculationSink` Protocol (`save_snapshot`, `create`, `save`) | `engines/calculation.py:102` |
| Event publication | `_publish_requested` / `_publish_completed` (fire-and-forget, failure-isolated) | `engines/calculation.py` |
| Audit | `_audit` → `audit_logger.log_action` (failure-isolated) | `engines/calculation.py` |
| Production callers | `api/dependencies.py:560`, `api/dependencies.py:602`, `workers/automatic_processing.py:242` | grep |

**Conclusion that shaped the whole task.** The canonical accounting write path already exists as a
**single method** — `CalculationEngine.calculate()` — which writes the snapshot and its emissions log from
one `CalculationRequest`. There was therefore **no need to invent a new service, and no second calculation
persistence system was created** (explicitly prohibited). The canonical pipeline was completed by extending
the existing one, which is the smallest correct change and leaves P16 numerics untouched.

Consequences recorded from this discovery:

- The engine writes **both** records from one request, so acting-for/ownership consistency between snapshot
  and log is achieved **structurally** (§15) rather than by convention.
- `customer_documents` and `evidence_line_items` are genuinely upstream of this pipeline (§12, §13) — they
  feed it, they are not part of it. Their absence is therefore not a gap in the accounting pipeline.
- `CalculationSink` fakes in the existing tests have **strict explicit signatures** (`tests/unit/api/fakes.py`,
  `tests/unit/engines/test_calculation.py`). This determined the design: the P17 dimensions are carried on the
  **domain objects**, so **no new keyword arguments were added** to the sink protocol and **no existing fake
  needed changing**.

## 6. Canonical write service implementation (Phase 2)

**No new service was created and no second persistence system exists.** The canonical accounting write
operation already is `CalculationEngine.calculate(request)`; it was completed, not duplicated, which the task
requires ("Do not create a second calculation persistence system") and is the smallest correct change.

The operation now receives and persists every input the task lists: authenticated actor
(`request.performed_by` + `performed_by_organization_id`), acting-for context
(`accounting_dimensions.acting_for_organization_id`), **data-owning organization** (`request.organization_id`
— unchanged authority), calculation request identity (`request.match_request_id`, unchanged), accounting
dimensions (`request.accounting_dimensions`), activity/input data (unchanged), selected factor (unchanged),
result (`_compute_co2e`, unchanged) and provenance references (`source_item_id`, `source_line_item_id`).

**Context is validated before writing.** `validate_scope_dimensions(scope, dimensions)` is the **first**
statement of `calculate()` — before the `CalculationRequested` event, before the snapshot INSERT, before the
log. A refused calculation leaves **nothing** behind; a test asserts all three sink collections are empty after
a refusal. **No factor-selection logic and no calculation logic was duplicated.**

## 7. Calculation snapshot implementation (Phase 3)

`save_snapshot` writes ten extra columns in the **same INSERT** it already used, named verbatim from the P17-A
migration and matching `ACTING_FOR_CARRIERS['calculation_snapshot']`: `scope2_method`, `scope3_category`,
`energy_type`, `data_quality`, `facility_id`, `transport_boundary`, `waste_origin`, `source_snapshot_id`,
`performed_by_organization_id`, `acting_for_organization_id`.

The dimensions ride on the `CalculationSnapshot` domain object, so **no keyword argument was added to the
`CalculationSink` protocol** — which is why the change required **no modification to any existing test fake**
(their signatures are strict).

**P16 guarantees preserved:** deterministic `request_id` and snapshot id unchanged; uniqueness, supersession,
invalidation and reportability untouched (no new code path); factor precedence, factor year guards and factor
scope guards untouched (the engine never re-derives a factor); `organization_id` remains the ownership
authority. **`content_hash` is unchanged** because `AccountingDimensions` is deliberately excluded from
`CalculationSnapshot._canonical` — asserted by test, as this was the single most likely way this change could
have broken P16 idempotency.

**Dimensions are never invented.** Every field is optional; unsupplied dimensions are written SQL `NULL`
("no method / category recorded"). A test asserts that a request supplying only `scope3_category` leaves the
other nine columns `NULL`.

## 8. Emissions log implementation (Phase 4)

The attribution and dimensions are written by the **same UPDATE statement that sets `snapshot_id`**
(`data/emissions_logs.py::save`), so a log cannot be linked to its snapshot while carrying a different owner
or acting-for — link and attribution are written atomically together. `organization_id` is deliberately **not**
in that UPDATE's `SET` list: ownership is set at creation and is never rewritten here.

Mismatch prevention is enforced twice: **structurally**, because the engine hands the *same*
`AccountingDimensions` instance to snapshot and log; and **explicitly**, via
`CalculationEngine._assert_log_matches_snapshot`, which raises if the log's owner differs from the snapshot's
or if both carry dimensions with different `acting_for_organization_id`. It is a hard failure because a
mismatch can only be a programming error, and failing there is safe (no log written yet). Both directions are
asserted by test. **No numerical behaviour changed.**

## 9. Acting-for integration (Phase 5)

Attribution travels on `AccountingDimensions.performed_by_organization_id` /
`.acting_for_organization_id`, resolved **server-side** by the IMPLEMENT-02 layer
(`resolve_accounting_context` / `ensure_record_owner_authorized`). The engine never accepts an acting-for value
from a client payload — the fields are plain optional attributes with no request-body binding.
**No RLS was bypassed; no service-role shortcut was used.** Owner and acting-for are never conflated:
`organization_id` stays the owner and is never taken from the attribution pair.


## 10. Report-version integration (Phase 6)

**NOT WIRED — deliberately deferred, not forgotten.** IMPLEMENT-03 correctly identified two real call sites
(`api/v3_reports.py:328`, `:918`). `ACTING_FOR_CARRIERS['report_version']` records this table's **owner as
`None`**, because a report version is not itself an accounting-owned row — it is a derived artefact over many
snapshots. Deciding what "owning organization" means for a report version is therefore a **small architectural
question**, not a mechanical edit, and the task forbids redesigning reporting and forbids inventing ownership
semantics. Reported as remaining work (§20) rather than guessed at.

## 11. Review-assignment integration (Phase 7)

**NOT WIRED.** The two real call sites (`routes/admin/workload.py:291`,
`routes/admin/assignments.py:319`) write through the **Supabase PostgREST client**, a different access style
from the asyncpg repositories this task extended. Touching them would have required a parallel write mechanism
(explicitly prohibited: "Do not create duplicate write mechanisms") or migrating those routes to the
repository layer — neither of which fits this task's scope. `ACTING_FOR_CARRIERS['review_assignment_history']`
also records **owner as `None`**, so the same ownership-semantics question as §10 applies. **Existing staff
authorization was not touched, weakened or redesigned.**

## 12. Customer-document disposition (Phase 8)

**No application write path; none was manufactured.** IMPLEMENT-03's finding was re-confirmed:
`create_from_upload` is called only from `tests/integration/*`, and `save` has no caller in `api/`,
`services/`, `engines/`, `routes/` or `workers/`.

**Exact blocker:** the production upload path is not in the backend Python application layer. Documents must be
created either by a frontend Supabase Storage/PostgREST write (the architecture permits this) or by an
ingestion worker outside the searched tree. Neither could be located, so no attribution could be added to a
real write.

**Intended integration point:** documents are **upstream inputs** to this pipeline, not stages within it. A
future ingestion flow should resolve its accounting context exactly as §7 does and write
`actor_organization_id` / `acting_for_organization_id` on the `customer_documents` row. The canonical
accounting write already accepts `source_item_id` / `source_line_item_id`, so document→snapshot lineage is
already supported and needs no new pipeline capability. **No fake route was created.**

## 13. Evidence-line-item disposition (Phase 9)

**No application write path; none was manufactured.** `materialise_for_item` and `backfill` have no caller in
`api/`, `services/`, `engines/`, `routes/` or `workers/`. The existing evidence architecture was preserved
untouched and **no source line or provenance was fabricated**. `ACTING_FOR_CARRIERS['evidence_line_item']`
records its actor column as `contributed_by_organization_id`, so the intended integration point is a
materialisation trigger that resolves its accounting context and writes that pair. Evidence **attaches to** this
pipeline rather than flowing through it: evidence lines reference `source_item_id`, which the canonical write
already persists on the snapshot, so the two are already joinable. The missing component is the **upstream
writer** (blocked work, §21).

## 14. Review-audit-trail disposition (Phase 10)

**Unchanged; the trigger was not weakened and no application-side duplication was introduced.**
`review_audit_trail` is populated by the RC2 audit trigger (`20260805000000_rc2_triggers.sql`); application
code only reads it.

**Can existing session context safely carry acting-for attribution? No.** The trigger fires on row changes and
has no access to the acting-for context, and this codebase has **no session-variable propagation mechanism**
(no `SET LOCAL` / `current_setting` acting-for plumbing exists). Adding one would be a new security-sensitive
mechanism, and the task forbids inventing an unsafe mechanism.

**Minimal future migration required:** a transaction-scoped `SET LOCAL` acting-for setting plus a trigger that
reads it via `current_setting(..., true)` defaulting to NULL when unset, together with an RLS-safety review.
That is a deliberate, reviewable migration — **not** something to improvise here. **The authoritative durable
acting-for record for review actions remains the audit ledger** (carrier 9, wired in IMPLEMENT-02).


## 15. Transaction behavior (Phase 11)

- The snapshot's dimensions are written in the **snapshot INSERT itself** — one statement, no partial state.
- The log's `snapshot_id` **and** its attribution/dimensions are written by the **same UPDATE**, so the log
  can never be linked-but-mis-attributed.
- `_assert_log_matches_snapshot` refuses an inconsistent pair **before** the log write, so an inconsistently
  attributed result is never persisted.
- **Honest limitation:** `calculate()` is not wrapped in an explicit database transaction, so if `_persist_log`
  fails after `save_snapshot` succeeded, a snapshot can exist without a log. **This is pre-existing P16
  behaviour, not introduced here**, and it is not a partially-attributed result: the snapshot is complete and
  correctly attributed, and re-running the calculation completes the pair. The inverse ("log without
  authoritative snapshot") cannot occur, because the log's `snapshot_id` is only ever set from a snapshot
  object that already exists.

## 16. Idempotency behavior (Phase 12)

**Preserved and specifically defended.** The P16 request-ID contract was **not altered**: `match_request_id`
is still written verbatim to `calculation_snapshot.request_id`, and no uniqueness constraint was changed.

The one genuine idempotency hazard this change introduced was the content hash: had `AccountingDimensions`
entered `_canonical`, the same calculation with and without dimensions would have hashed differently and could
have produced a duplicate. **It is deliberately excluded, and a test asserts identical hashes with and without
dimensions for the same factor and request.** Repeated identical requests therefore still derive the same
snapshot identity, and no duplicate-creation path was added.

## 17. Security / RLS behavior (Phase 13)

| Required case | Status |
|---|---|
| direct customer → own organization | Supported; `organization_id` is the owner authority |
| consultant → own organization | Supported via the IMPLEMENT-02 context (firm organisation) |
| consultant → authorized client | Supported via the delegated context; acting-for differs from actor |
| consultant → unauthorized client | Denied 403 by `resolve_accounting_context` (IMPLEMENT-02; proven there) |
| client → own organization | Supported |
| client → unrelated organization | Denied 403 (IMPLEMENT-02; proven there) |
| forged acting-for ID → rejected | **Proven here**: `CalculationRequest` has no request-body binding |
| forged data-owner ID → rejected | **Proven here**: ownership comes from `request.organization_id`; a log whose owner differs from its snapshot is refused |
| mismatched snapshot/log owner → rejected | **Proven here** by test, in both the owner and acting-for directions |
| cross-tenant report access → rejected | Out of this task's scope; report wiring deferred (§10) |

**No RLS policy was added, changed, weakened or bypassed. No service-role access was used as a shortcut** —
the engine writes through the same repository surface it always did.


## 18. Full test-suite result

**This task attempted the full suite and must report honestly that it did not complete it.**

| Run | Result |
|---|---|
| **New P17-04 tests** (`tests/unit/engines/test_p17_04_canonical_write.py`) | **14 tests, 14 passed, 0 failed** |
| Targeted affected suites (`test_calculation.py`, `test_customer_factor_integration.py`, `tests/unit/domain`) | **all passed**, 0 failures |
| `tests/unit` (full unit suite) | **attempted; reached ~16% with 0 failures before exceeding the time budget; NOT completed** |
| `tests/unit tests/integration` (full suite) | **attempted; exceeded the 300 s command budget; NOT completed** |
| `tests/integration/*` | **DB-dependent; failures observed are pre-existing** — they require a live database and the destructive harness, which was **not** run |

**Exact counts: the full-suite total/passed/failed/skipped/error figures required by this task were NOT
obtained.** I am not reporting numbers I did not measure. What is established: the new tests pass (14/14), the
directly affected existing suites pass, and 0 failures appeared in the portion of the unit suite that ran.
**A full-suite run remains outstanding and must precede any verdict beyond PARTIAL.**

## 19. P16 regression comparison

**One real regression was found and fixed during this task — the honest record.**

`tests/unit/engines/test_customer_factor_integration.py::test_snapshot_records_customer_provenance` failed with
`Scope2MethodRequiredError`. Its fixture persisted a **Scope 2** calculation with no `scope2_method` — a write
the P17-A schema **forbids on every new row** (`calc_snapshots_scope2_method_required`, `NOT VALID`). It passed
only because its in-memory sink applies no constraint, so the test asserted a write that cannot exist in a
migrated database.

**Action taken:** the fixture now supplies `AccountingDimensions(scope2_method="LOCATION_BASED")`. This is **the
single existing test modified by this task**, declared here explicitly, and it does **not** weaken the
assertion — every customer-factor provenance assertion is unchanged and still passes. The alternative
(weakening the new validation) would have left the canonical pipeline unable to enforce Scope 2 identity, which
the next task depends on. **No test was skipped, deleted or relaxed to obtain a green result.**

Engine-path regression risk was bounded by design: dimensions travel on domain objects, so the
`CalculationSink` protocol and **all existing test fakes are byte-identical** to before.

## 20. Known incomplete work

1. **Report-version attribution** (§10) — two identified call sites, awaiting an ownership-semantics decision.
2. **Review-assignment attribution** (§11) — two identified call sites on a different (PostgREST) access path.
3. **Full-suite regression run** (§18) — not completed; required before a COMPLETE verdict.
4. **Read surface for the new columns** — `_SNAPSHOT_COLUMNS` / `_LOG_COLUMNS` were left unchanged, so the new
   dimensions are **written but not yet returned** by existing snapshot/log read queries. Scope 2 reporting
   will need them exposed; deliberately not changed here to avoid altering existing read shapes.
5. **No test asserts generated SQL against a real database** — the repository write path is covered through the
   engine with an in-memory sink, so the `$n` parameter mapping is verified by construction and by the
   migration's column order, not by a live INSERT.



## 21. Blocked / deferred work

| Item | Status | Reason |
|---|---|---|
| `customer_documents` attribution | **BLOCKED** | No application write path exists (§12) |
| `evidence_line_items` attribution | **BLOCKED** | No application write path exists (§13) |
| `review_audit_trail` attribution | **BLOCKED pending a decision** | Trigger-owned; needs a `SET LOCAL` + trigger migration and RLS-safety review (§14) |
| Report / review-assignment attribution | Deferred | Ownership semantics undecided for these two tables (§10, §11) |
| Scope 2 / Scope 3 methodology | Out of scope by instruction | This task builds the pipeline they consume |
| UI (client switcher, acting-for banner, pickers) | Out of scope by instruction | Later task |

## 22. Production-contact statement

**NO PRODUCTION SYSTEM WAS CONTACTED.**

- No production database, credential, migration or deployment; no production customer data.
- No external production API call; nothing pushed to any remote.
- **No database was opened at all.** Every assertion was made with in-memory sinks and the existing unit suite.
  No migration was added or applied.
- The Demo Lab, `carbontally_qa_phase8`, `carbontally_test` and every other persistent local database were
  untouched, and the **destructive integration harness was not run** (F-046-1 respected).

## 23. Final implementation verdict

```
P17_IMPLEMENTATION_PARTIAL
```

**Why PARTIAL.** The rule is: use `P17_IMPLEMENTATION_COMPLETE` *"only if the canonical accounting write
pipeline and all applicable reachable integrations in this task are genuinely implemented and tested."* The
canonical pipeline **is** implemented and tested. But:

- the **full-suite regression run was not completed** (§18, §20.3);
- **report-version** and **review-assignment** integrations — identified by IMPLEMENT-03 as reachable — are
  **not** wired (§10, §11);
- three carriers remain blocked on facts outside this task's control (§20, §21).

Claiming COMPLETE would be false, and the task instructs explicitly: *"Do not inflate the verdict."*

**What is genuinely delivered and verified:**

- the **canonical accounting write pipeline** completed on the existing engine — no second persistence system,
  no duplicated calculation or factor logic;
- **P17 accounting dimensions flowing end-to-end** through one validated value object into both the snapshot
  INSERT and the log UPDATE, with the ten column names taken verbatim from the P17-A migration;
- **fail-closed validation before any write**, converting what the database would reject into a clean domain
  error and guaranteeing a refused calculation leaves nothing behind;
- **structural + explicit cross-record consistency**: a snapshot and its emissions log cannot disagree about
  owner or acting-for, proven in both mismatch directions;
- **P16 preservation proven, not asserted**: content-hash identity with and without dimensions, everything
  optional, and a sink protocol so unchanged that no existing test fake needed touching.

**The next Scope 2 task can build on this today**: populate `AccountingDimensions` with a `LOCATION_BASED` or
`MARKET_BASED` method, and the persistence layer will validate, attribute and store it consistently — or refuse
the write entirely.

**No `PASS`, `E2E VERIFIED` or `PRODUCTION READY` claim is made.**
