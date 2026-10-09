# CT-MP-SUB-004 — Production Readiness Remediation (PROD-READINESS-01)

| Field | Value |
| --- | --- |
| **Task ID** | `CT-MP-SUB-004-PROD-READINESS-01` |
| **Title** | CT-MP-SUB-004 — Production Readiness Remediation for PO-Required Items |
| **Author** | Cline (implementation engineer) |
| **Report date** | 2026-10-05 |
| **Repository HEAD at time of work** | `375a48dc1b9e9cfd74090bbf747554ae997acb59` |
| **Branch** | `p8-release-reconciled` |
| **Scope** | F-4, F-7, F-9, F-11, NV-5, NV-6, NV-9, NV-10 (only) |
| **Status** | **IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION** |
| **Governance status (updated 2026-10-05)** | **P-1 and P-2 are CLOSED.** The *"PO decision required"* markers in §11/§12/§13/§19/§20 below are the **historical** state at the time of implementation and are **superseded for P-1/P-2** by `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` (see §21). No implementation evidence in this report is altered. |
| **Type** | Implementation + tests + verification tooling + documentation. No commit, no push, no deploy, no production access, no migration applied. |

> This report is a *self-verification* record. It is **not** an independent
> acceptance. CT-MP-SUB-004 is **not** declared production-ready here; the next
> step is a separate independent verification task covering the eight items.

---

## 1. Task ID and scope

The Product Owner classified eight CT-MP-SUB-004 findings as **REQUIRED BEFORE
PRODUCTION** and authorised remediation of exactly those items:

| Item | Topic | Disposition in this task |
| --- | --- | --- |
| **F-4** | test/tooling attribution + reliable test baseline | IMPLEMENTED / TESTED / VERIFIED |
| **F-7** | broad exception handling on allocation | IMPLEMENTED / TESTED / VERIFIED |
| **F-9** | idempotency / concurrency for allocate + release | IMPLEMENTED / TESTED / VERIFIED |
| **F-11** | safer Admin client selection (no manual client-ID entry) | IMPLEMENTED / TESTED / VERIFIED |
| **NV-5** | responsive UI verification / remediation | IMPLEMENTED / TESTED / VERIFIED |
| **NV-6** | accessibility baseline / remediation | IMPLEMENTED / TESTED / VERIFIED |
| **NV-9** | performance baseline + acceptance thresholds | IMPLEMENTED / TESTED / VERIFIED (thresholds = PO decision P-1) |
| **NV-10** | notification behaviour definition + verification | IMPLEMENTED / TESTED / VERIFIED (audit-only; P-2) |

Every row above is **self-verified only**; none is `ACCEPTED`. Per-item detail,
evidence and remaining limitations are in §19.

**Explicitly NOT in scope and NOT performed:** NV-7 (pixel-level D2 comparison),
I4, F-3, F-10, CoStrict N-1/N-2, any new role, new authorization model, new
business rule, new external provider, production deployment/migration/DB
mutation, schema/RLS change, `git commit`, `git push`.

---

## 2. PO authority used

The task instruction `CT-MP-SUB-004-PROD-READINESS-01` is the PO authority for
this work. It supersedes, **for these eight items only**, the narrower
`PD-5`-era scope limit, under which PD-5 §7.1 authorised *QA-fixture work only*
and explicitly did **not** authorise application-code change.

| Governing decision | Relevance here |
| --- | --- |
| **PO task instruction — PROD-READINESS-01** | Authorises remediation of F-4, F-7, F-9, F-11, NV-5, NV-6, NV-9, NV-10; prohibits production deployment, migration application, schema/RLS change, new roles/authorization models/business rules, NV-7 and I4. |
| **PD-1 … PD-4** | Ratified; respected unchanged (authorization guards, capability split, tab label). |
| **PD-5** | Its QA fixture (`tools/demo_lab/fixture_mp_coverage.py`) is reused unchanged as the deterministic environment for NV-5/NV-6/NV-9 evidence. |
| **PD-6** | In force. Its per-migration review gate is honoured: **no migration was authored or applied** by this task. |
| AGENTS.md §46 (error handling), §66 (database change policy), §67 (RLS), §70 (Git safety), §72 (testing) | Applied throughout. |

**PO decision required (recorded, not resolved):** see §12 (proactive allocation
notification) and §11/§18 (production-scale latency/throughput SLO). Neither was
silently invented.

---

## 3. Files inspected

Authoritative material (read before editing):

* `docs/architecture/CT-MP-SUB-004-PO-decision-record.md` (PD-1 … PD-6)
* `docs/architecture/CT-MP-SUB-004-independent-verification-report.md`
  (findings F-4, F-7, F-9, F-11, NV-1 … NV-10; §19, §20, §21)
* `docs/architecture/CT-MP-SUB-004-PD5-FIXTURE-01-report.md`
* `docs/architecture/CT-MP-SUB-004-PD5-VERIFY-01-report.md`
* `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md`
* `tools/demo_lab/README.md`

Implementation inspected:

* `backend/api/v3_manual_processing_coverage.py`
* `backend/api/manual_processing_admin.py`
* `backend/api/v3_search.py`, `backend/api/v3_operations.py`,
  `backend/api/v3_commercial.py` (existing organisation-search contracts)
* `backend/data/manual_processing.py`, `backend/data/organizations.py`,
  `backend/data/base.py`, `backend/services/manual_processing_routing.py`
* `backend/domain/manual_processing.py`
* `supabase/migrations/20261030000000_manual_processing_routing.sql`,
  `supabase/migrations/20261101000000_ct_mp_sub_003_consultant_coverage.sql`
* `frontend/src/v3/ops/ManualProcessingCoverageTab.jsx`,
  `frontend/src/v3/customer/ManualProcessingPage.jsx`, `frontend/src/v3/api.js`
* `frontend/package.json`, `frontend/src/setupTests.js`, `frontend/src/App.test.js`
* `frontend/node_modules/react-scripts/scripts/utils/createJestConfig.js`
  (to determine which Jest keys CRA 5 permits and how it merges them)
* `backend/tests/unit/api/conftest.py`, `backend/tests/unit/api/fakes.py`,
  `backend/tests/unit/api/route_paths.py`, and the CT-MP-SUB-003/004 test modules
* `tools/demo_lab/lab.py`, `tools/demo_lab/fixture_mp_coverage.py`,
  `tools/demo_lab/fixture_mp_coverage_browser.py`

**Runtime inspected:** local stack `gateway 127.0.0.1:54430` (200),
`backend 127.0.0.1:8070` (200), `frontend http://localhost:3000` (200).
Frontend was **not** switched to `:3100`; CORS was **not** broadened.

---

## 4. Files changed by this task

Only the files below were touched by `PROD-READINESS-01`. Files modified by the
earlier CT-MP-SUB-003/004 workstream (routing, upload classification, PM
operator surfaces) were **read**, and left functionally unchanged unless listed
here.

| # | File | Change | Item |
| --- | --- | --- | --- |
| 1 | `backend/api/v3_manual_processing_coverage.py` | Allocation/release refusals narrowed to the two typed domain errors; every other exception surfaces as a 5xx instead of a misleading 409 | F-7 |
| 2 | `backend/domain/manual_processing.py` | Added typed refusal vocabulary `ManualProcessingAllocationError` / `DuplicateActiveAllocationError` / `CapacityExceededError` | F-7, F-9 |
| 3 | `backend/data/manual_processing.py` | Capacity re-check moved **inside** the allocation transaction, guarded by a per-firm `pg_advisory_xact_lock`, so concurrent allocate calls cannot both observe spare capacity | F-9 |
| 4 | `backend/api/manual_processing_admin.py` | Admin client search by **name** (`q`, bounded, `client_names` returned); explicit release confirmation; client-name resolution consolidated to **one** batched `organizations.get_many` call (N+1 removed) | F-11, NV-9 |
| 5 | `backend/data/organizations.py` | Added `get_many(ids)` batch read. **Note:** an intermediate edit of this file clobbered `list_all`; see §17 | F-11, NV-9 |
| 6 | `frontend/src/v3/api.js` | Client-search + release client bindings used by the Admin tab | F-11 |
| 7 | `frontend/src/v3/ops/ManualProcessingCoverageTab.jsx` | Searchable by-name client selector replacing manual client-ID entry; explicit "Load client state" confirmation gate; selected-client echo | F-11, NV-6 |
| 8 | `frontend/package.json`, `frontend/src/setupTests.js`, `frontend/src/App.test.js` | CRA/Jest resolution fixed so the suite runs and reports honest totals (react-router/dom resolution, jsdom globals guard) | F-4, NV-6 |
| 9 | `frontend/src/v3/__tests__/manual-processing-coverage.test.jsx` | Coverage for the selector flow, gate behaviour and a11y attributes | F-11, NV-6 |
| 10 | `backend/tests/unit/api/fakes.py` | In-memory fakes extended for the new admin endpoints/typed errors | F-7, F-9, F-11 |
| 11 | `backend/tests/unit/api/test_ct_mp_sub_004_prod_readiness.py` | **New** (~530 lines): typed-refusal contract, concurrency/idempotency contract, admin search contract, audit-only notification behaviour | F-7, F-9, F-11, NV-10 |
| 12 | `tools/demo_lab/perf_mp_baseline.py` | **New**: NV-9 performance baseline + budget assertions over the live stack | NV-9 |
| 13 | `tools/demo_lab/nv_mp_ui_check.py` | **New**: NV-5/NV-6 responsive + accessibility harness (6 surfaces × 8 viewports) | NV-5, NV-6 |
| 14 | `tools/demo_lab/fixture_mp_coverage_browser.py` | Fixture browser harness updated to select the Admin client **by name** (the selector is no longer a raw-ID field) | F-11 |
| 15 | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-01-report.md` | **New**: this report | — |

**No** migration was authored or applied. **No** schema, RLS, policy, role,
authorization-model, business-rule or external-provider change was made. **No**
`git commit`, `git push`, force-push, reset or history rewrite was performed.

---

---

## 5. Test baseline and failure attribution (F-4)

**Finding (F-4):** the automated suites could not be trusted as evidence. The
Create-React-App scaffold test (`frontend/src/App.test.js`) failed to resolve
`react-router`/`react-dom`, and there was no reliable statement of what the
totals meant — so "tests pass" and "tests fail" were both uninformative, and no
finding could be attributed to a workstream.

**Implemented:**

* `frontend/src/App.test.js` — the CRA scaffold assertion was replaced with a
  test that genuinely exercises the application shell, plus module resolution so
  `react-router-dom` loads under CRA 5 (the scaffold's failure was masking the
  real state of the suite).
* `frontend/src/setupTests.js` — a jsdom globals guard so tests fail for
  *behavioural* reasons rather than environment ones.
* `frontend/package.json` — Jest resolution configuration matching CRA 5's
  permitted keys (verified against
  `frontend/node_modules/react-scripts/scripts/utils/createJestConfig.js`).
* `backend/tests/unit/api/fakes.py` and the new backend test module provide the
  in-memory seams the Manual-Processing contract tests need.

**Baseline after this task's changes (all re-run on the current working tree):**

| Suite | Command | Result |
| --- | --- | --- |
| Frontend — Manual Processing | `react-scripts test --watchAll=false --testPathPattern=manual-processing-coverage` | **22 / 22 passed**, 1 suite |
| Frontend — full | `CI=true react-scripts test --watchAll=false` | **571 passed / 572 tests**, 48 / 49 suites |
| Backend — Manual Processing (6 modules) | `pytest tests/unit/api/test_ct_mp_sub_004_prod_readiness.py tests/unit/api/test_ct_mp_sub_004_coverage_surfaces.py tests/unit/api/test_ct_mp_sub_003_consultant_coverage.py tests/unit/api/test_manual_processing_routing.py tests/unit/domain/test_consultant_mp_coverage.py tests/unit/domain/test_manual_processing_routing.py` | **151 / 151 passed** |
| Backend — full unit suite | `pytest tests/unit -q` | **4 948 passed / 4 956 collected**, **8 failed** |

The 6 backend Manual-Processing modules are: `test_ct_mp_sub_004_prod_readiness.py`
(32), `test_ct_mp_sub_003_consultant_coverage.py` (32),
`test_manual_processing_routing.py` (27),
`test_ct_mp_sub_004_coverage_surfaces.py` (24),
`test_consultant_mp_coverage.py` (22), `test_manual_processing_routing.py`
(domain, 14).

**Failure attribution — every failure, classified with evidence.** No failure was
skipped, xfailed or silenced, and **none is attributable to the eight remediated
items**; none is Manual-Processing related.

| # | Failing test | Observed assertion | Root cause | Attribution |
| --- | --- | --- | --- | --- |
| 1 | `test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | a post-P16-baseline migration is not a P17 member | the guard freezes the frontier at the P17 set. **17** migration files now carry a timestamp later than the P16 baseline (`20261009000000`); only the P17 set is accepted. The offenders include CT-BACKUP-01/02 (`20261026`/`20261027`) and CT-FINAL-03 RLS (`20261028`/`20261029`) — **before** this workstream's files | **pre-existing drift** across several workstreams |
| 2 | `test_d17_provider_ownership_migration_revision.py::test_migration_ordering_is_unchanged` | `assert 100 == 71` | the guard hard-codes the migration **count** (71). The repository now holds **100** migration files — 98 even with this workstream's two files excluded, so the guard cannot pass without them either | **pre-existing drift** |
| 3 | `test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | non-I1 migrations exist after I1 | same frozen-frontier class; the allowed-later list is extended per PO authorisation and has not tracked later workstreams | **pre-existing drift** |
| 4 | `test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | ditto for I2 | ditto | **pre-existing drift** |
| 5 | `test_v3_discovery.py::test_create_request_as_admin` | `assert body["verification_delivered"] is False` → `assert True is False` | discovery/invitation dispatch behaviour on this branch | **unrelated workstream** (insight/discovery) |
| 6–8 | `test_extraction_suggestions.py::test_suggest_parses_clean_invoice`, `…missing_fields_leave_unresolved`, `…no_fabrication_on_garbage` | `assert '2026-01-15' == '15/01/2026'` | extracted invoice dates are normalised to ISO-8601 while the assertions still expect `DD/MM/YYYY` | **unrelated workstream** (extraction engine) |
| 9 | Frontend `dr007-investor-display-fixes.test.jsx:107` | `expect(row.textContent).not.toContain('—')` | pre-existing investor-display assertion | **unrelated workstream** (DR-007) |

**Why this is not an escape hatch:** the four migration-frontier failures are a
*known, reproducible* consequence of the migration inventory having grown past a
frozen guard, and the user-visible impact is limited to those guard tests
themselves — no product behaviour depends on them. They are recorded here so the
next agent does not mistake them for a Manual-Processing defect, and so the
owning workstreams can bump the frontiers deliberately rather than silently.
This task did **not** edit those four guards: they encode a review frontier
belonging to other workstreams, and rewriting them would conceal real inventory
drift instead of surfacing it.

---

## 6. F-7 — precise allocation-failure handling

**Finding (independent verification report):** allocation failures were reported
to the consultant as a *duplicate allocation* (HTTP 409) even when the real
cause was a different error, because a broad `except Exception` was mapped to a
409. This misreports server faults as business refusals and hides genuine
failures from the operator.

**Implemented:** refusals are now **typed in the domain layer** and mapped
explicitly at the API boundary.

* `backend/domain/manual_processing.py` declares the refusal vocabulary:

  | Class | Meaning | HTTP |
  | --- | --- | --- |
  | `ManualProcessingAllocationError` | base class for *expected* refusals | — |
  | `DuplicateActiveAllocationError` | the (firm, organisation) pair already holds an ACTIVE allocation | 409 |
  | `CapacityExceededError` | the firm has no remaining purchased capacity | 409 |

* `backend/api/v3_manual_processing_coverage.py` catches **only** those two
  types (`:330`, `:336`) and converts them to 409 with a business-readable
  message. The comment at `:345–346` records the contract: any other failure
  propagates unchanged and surfaces as a genuine server error (5xx) — it is
  never reported as a duplicate allocation.

**Verification.** `backend/tests/unit/api/test_ct_mp_sub_004_prod_readiness.py`
asserts the contract in both directions: the two typed refusals produce 409 with
the expected message, and an *unexpected* exception raised by the repository
does **not** produce 409 (i.e. it is not silently swallowed or re-labelled).

---

## 7. F-9 — idempotency and concurrency for allocate/release

**Finding:** capacity was checked *outside* the write, so two concurrent
allocate requests could both observe spare capacity and over-allocate. Repeated
requests could also produce a second active allocation.

**Implemented** (`backend/data/manual_processing.py::create_allocation`, `:452`):
all protection now happens **inside one transaction on one connection**:

1. `pg_advisory_xact_lock(hashtextextended('consultant_mp_allocations:<firm>', 0))`
   — a per-firm advisory transaction lock serialises allocation writes for that
   firm. Concurrent attempts run one at a time; the loser re-reads the
   *committed* count under the lock and is refused deterministically instead of
   over-allocating.
2. Under the lock, when a finite `capacity` is supplied, the active count is
   re-read and `CapacityExceededError` is raised if already full (the
   race-losing path of the request-level pre-check).
3. The **existing** partial unique index
   `uq_consultant_mp_allocations_active` remains the authoritative duplicate
   guard; an `asyncpg.UniqueViolationError` is translated to
   `DuplicateActiveAllocationError`.
4. `capacity=None` preserves prior behaviour (no finite capacity configured ⇒ no
   cap enforced), so no existing caller changes meaning.

**Why no migration was needed:** both mechanisms already exist in the
repository — the partial unique index and the advisory-lock capability. F-9 was
therefore a *correctness* defect in *ordering/atomicity*, not a schema gap.

**Verification.** `test_ct_mp_sub_004_prod_readiness.py` exercises the contract
against the repository seam: duplicate attempts yield the typed duplicate
refusal; an allocation that would exceed capacity yields the typed capacity
refusal; the fake is sequential, so the tests assert the *contract* (typed
refusal + no second active row), while the live stack exercises the real
locking path (§16). Repeated `release` on an already-released allocation is a
404, not a second mutation.

---

## 8. F-11 — safer Admin client selection

**Finding:** the Admin control plane required operators to paste a raw
organisation UUID to act on a client. That is error-prone, unauditable and
violates the business-context principle (a UUID is not a client).

**Implemented — backend (`backend/api/manual_processing_admin.py:896`):** a new
**read-only, bounded, name-searchable** lookup:

| Property | Value |
| --- | --- |
| Route | `GET /organizations` on the Manual Processing admin router |
| Query | `q` (name substring), `limit` (1–50, default 20), `offset` |
| Gate | `require_manual_processing_admin` — internal CarbonTally staff **and** the existing admin-grade `can_manage_organizations` permission |
| Reuse | the **existing** `organizations.search()` repository method (CL-63) — no duplicate search implementation |
| Returns | `id`, `name`, `country`, `is_active`, plus `total`/`limit`/`offset`/`q` for stable pagination |
| Mutation | **none** — selecting a result changes nothing; the caller must issue a separate server-validated action |

No new authorization model, no new permission vocabulary and no schema change
were introduced. The gate is the CarbonTally-internal admin control plane, so
this is not a customer-facing tenant-scope surface.

**Implemented — frontend (`frontend/src/v3/ops/ManualProcessingCoverageTab.jsx`):**

* a by-name search field (`#mp-cov-org-search`) with a labelled results list
  (`#mp-cov-org-results`, `aria-label="Organisation search results"`,
  `aria-describedby` help text) — the raw-UUID entry path is gone;
* an explicit selected-client echo (`[data-testid="mp-cov-org-selected"]`) so
  the operator can see **which** client the next action applies to;
* an **explicit confirmation gate**: "Load client state" stays disabled until a
  client is deliberately selected, and release requires explicit confirmation.
  This prevents an accidental action against the wrong client.

**N+1 removal (also NV-9):** allocation rows previously resolved one client name
per row. `manual_processing_admin.py:666` now performs **exactly one** batched
`repos.organizations.get_many(sorted(referenced))` call and publishes the result
as `client_names` (`:672`). A missing id resolves to `None` — the UI never
invents a name for an unknown organisation.

**Verification:** `test_ct_mp_sub_004_prod_readiness.py` covers the search
contract (bounded limit, name ordering, no mutation on read) and the
`get_many`-based name mapping; `fixture_mp_coverage_browser.py` was updated to
drive the selector by name and still passes 10/10 (§16); `nv_mp_ui_check.py`
verifies the gate opens only after selection, at every viewport (§9).

---

## 9. NV-5 — responsive UI verification

**Implemented tooling:** `tools/demo_lab/nv_mp_ui_check.py` — a Playwright harness
that logs in as real fixture identities and audits **6 live surfaces across 8
viewports** (1920×1080, 1440×900, 1280×800, 1024×768, 768×1024, 430×932,
390×844, 375×812) = **48 checks per run**.

Surfaces: `customer_manual_processing`, `consultant_coverage_unselected`,
`consultant_coverage_selected`, `admin_commercial_coverage`,
`admin_client_selector_open`, `admin_client_selected`.

Per viewport the harness asserts:

* horizontal overflow ≤ 2 px on the document;
* no element wider than its box that is **not** inside a scroll container (a
  scrollable table wrapper is legitimate; a clipped critical control is not);
* exactly one `<h1>` (semantic heading structure);
* every interactive control has an accessible name;
* each configured critical control is present, inside the viewport and enabled;
* gated controls are **present and disabled** while their prerequisite is
  unsatisfied — a regression that arms a control early also fails;
* required business text remains legible;
* where applicable, the capacity meter exposes progress semantics.

**Result (final run): 48/48 clean** — evidence `mp_nv_ui_20261005T020514Z.json`.

**Methodology correction recorded (no product defect):** the first run reported
32 problems that were **harness policy errors, not UI defects**:

1. `customer_manual_processing` demanded the "View available plans" call-to-action
   — but that CTA renders only in the *non-entitled* branch, and `u_owner_dual`
   **is** entitled, so its absence is correct. The check now audits the covered
   state instead.
2. `Allocate` and `Load client state` were flagged as disabled. Both are
   **intentionally gated** (F-11 / ratified PD design) until a client is
   selected. The harness now asserts the gate in both directions, then satisfies
   the prerequisite to prove the control becomes usable at every width.

The corrected harness is therefore *stricter* than the original: it fails both
when a control is missing **and** when a gated control is armed prematurely.

**Known limitation:** NV-5 verifies these six Manual-Processing surfaces, not
the whole application, and NV-7 (pixel-level D2 comparison) remains out of
scope.

---

## 10. NV-6 — accessibility baseline

Covered by the same 48-check run plus targeted frontend tests:

| Check | Method | Result |
| --- | --- | --- |
| Accessible name on every interactive control (button, link, input, select, `[role=button]`) | live DOM audit, all 8 viewports | PASS |
| Search results list is labelled and described | `aria-label` + `aria-describedby` on `#mp-cov-org-results` | PASS |
| Exactly one `<h1>` per surface | live DOM audit | PASS |
| Capacity meter is a real progress indicator | `role="progressbar"` with `aria-valuenow`/`min`/`max` | PASS |
| Operator can always see which client is selected | `data-testid="mp-cov-org-selected"` echo | PASS |
| Gate state is communicated, not silently dead | disabled-until-selected assertion + help text | PASS |
| Controls are keyboard-reachable | component tests in `manual-processing-coverage.test.jsx` | PASS |

**Known limitation:** this is a **baseline**, not a WCAG 2.2 AA audit. Automated
contrast-ratio, screen-reader-transcript and reduced-motion verification were
not performed.

---

## 11. NV-9 — performance baseline and acceptance thresholds

**Implemented tooling:** `tools/demo_lab/perf_mp_baseline.py` — a reproducible
baseline that logs in with **real password grants** against the local stack,
times the six Manual-Processing hot paths, and asserts p95 against a declared
budget. It also asserts that the index set the hot queries depend on exists.

Budgets are declared in the script (per cent, p95, milliseconds):

| Operation | Endpoint class | Budget (p95) |
| --- | --- | --- |
| `customer_entitlement` | customer effective-entitlement read | 500 ms |
| `consultant_coverage` | consultant coverage/state read | 500 ms |
| `admin_coverage` | admin coverage read (batched names) | 500 ms |
| `admin_client_search` | F-11 by-name client search | 500 ms |
| `allocate` | write (typed refusals) | 750 ms |
| `release` | write | 750 ms |

**Result — 12 iterations, live stack: all budgets PASS (run EXIT=0)** —

| Operation | n | p50 | p95 | max | Budget | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `customer_entitlement` | 12 | 106 ms | 154 ms | 209 ms | 500 ms | PASS |
| `consultant_coverage` | 12 | 89 ms | 103 ms | 122 ms | 500 ms | PASS |
| `admin_coverage` | 12 | 76 ms | 100 ms | 110 ms | 500 ms | PASS |
| `admin_client_search` | 12 | 71 ms | 81 ms | 84 ms | 500 ms | PASS |
| `allocate` | 4 | 79 ms | 94 ms | 94 ms | 750 ms | PASS |
| `release` | 4 | 78 ms | 88 ms | 88 ms | 750 ms | PASS |

Index assertions: `uq_consultant_mp_allocations_active`,
`idx_consultant_mp_allocations_firm`, `idx_consultant_mp_allocations_org` — all
present (PASS). Evidence: `mp_perf_baseline_20261005T020040Z.json`.

The N+1 removal (§8) is visible here: `admin_coverage` returns client names in a
single batched query, at p50 76 ms with the fixture's allocation set.

**PO DECISION REQUIRED — production-scale SLO.** No production
latency/throughput SLO exists anywhere in the repository. The thresholds above
are **local Demo-Lab interactive budgets** (the UI must render its data within
about a second on a developer workstation), explicitly **not** a production
SLO. Declaring production targets (p95/p99, sustained request rate, concurrent
users, instance sizing) is a commercial/PO decision and was **not** invented
here. Per the PO instruction, thresholds are documented so they can be reviewed;
see §13.

> **→ P-1 is now CLOSED (2026-10-05).** No dedicated production SLO is required
> for this release, so these budgets remain **engineering/verification budgets
> only** and this report makes **no** production SLO or capacity claim.
> Authoritative PO decision: `CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md`
> §3–§4 (see §21).

---

## 12. NV-10 — notification behaviour: defined and verified

**Finding:** the notification behaviour for allocation/release was undefined,
so a reviewer could not tell whether a missing notification was a defect or
intended behaviour.

**Implemented:** the behaviour is now **explicitly documented and tested as
audit-only**:

* every Manual-Processing allocation/release state change writes a durable
  append-only audit record (`manual_processing:allocation_created`,
  `manual_processing:allocation_released`) through the existing audit
  infrastructure — no parallel audit system exists;
* **no** user-facing notification (email, in-app, Realtime) is emitted;
* a response body never claims a notification was sent.

`test_ct_mp_sub_004_prod_readiness.py::TestNV10NotificationBehaviour` asserts all
three cases in the presence of a real notification store: consultant allocate,
consultant release, and admin allocate each write the audit action **and** leave
the notification row count unchanged.

**Rationale and boundary:** proactively notifying a client that they have been
allocated (or unallocated) sponsored Manual-Processing coverage is a **new
product behaviour** with email-provider, consent and anti-spam implications. It
is therefore **PO DECISION REQUIRED** and was deliberately not invented. Until
that decision, audit-only is the defined, verifiable behaviour. See §13.

> **→ P-2 is now CLOSED (2026-10-05).** Proactive MP notifications are **not
> required** for this release; allocation/release remain **audit-only**, exactly
> as implemented and verified here. The absence of MP notification rows for these
> transitions is acceptable and expected. Authoritative PO decision:
> `CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` §5–§6 (see §21).

---

## 13. PO decisions required (recorded, NOT resolved)

> **GOVERNANCE STATUS UPDATE (2026-10-05).** This section records the state **at
> the time of implementation**: both items were **open**. Both have since been
> **decided by the Product Owner** and are **CLOSED** — see §21 and
> `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md`
> (P-1 CLOSED: no dedicated production SLO required for this release;
> P-2 CLOSED: MP allocation/release remain audit-only). The table below is
> preserved as the historical record.

Two items cannot be completed by an implementation agent because they are
product/commercial policy. Neither was silently invented.

| # | Decision required | Why it is a PO decision | State pending the decision |
| --- | --- | --- | --- |
| **P-1** | **Production performance SLO** — p95/p99 latency, sustained request rate, concurrency, instance sizing, and whether the Demo-Lab interactive budgets become contractual | Commercial/operational commitment, not an implementation detail; no production SLO exists in the repository | Local interactive budgets implemented and documented (§11); passing |
| **P-2** | **Proactive allocation/release notification** — should a client be notified when sponsored Manual-Processing coverage is granted or withdrawn, on which channel, with what consent/copy? | New user-facing behaviour with email-provider, consent and anti-spam implications | Audit-only behaviour implemented, documented and tested (§12) |

Neither P-1 nor P-2 blocks the eight remediated items; both are recorded so the
PO decides rather than the agent assuming.

---

## 14. Database and migration statement

* **No migration was authored, edited or applied by this task.**
* **No** schema, column, constraint, index, policy, RLS, role or grant change was
  made. **PD-6's per-migration review gate** is therefore untouched.
* **F-9 required no schema change.** Both mechanisms it relies on already exist
  in the repository:
  * the partial unique index `uq_consultant_mp_allocations_active` (the
    authoritative duplicate guard), and
  * PostgreSQL advisory transaction locks.
  F-9 was a defect of *ordering and atomicity* in application code, not a
  missing constraint.
* The two Manual-Processing migrations
  (`20261030000000_manual_processing_routing.sql`,
  `20261101000000_ct_mp_sub_003_consultant_coverage.sql`) were authored by the
  **earlier** CT-MP-SUB-003/004 workstream and sit in the working tree as
  untracked files. This task neither authored nor applied them.
* Their consequence for the test suite is recorded in §5 (migration-frontier
  guard failures).

---

## 15. Security verification

| Property | How it was verified | Result |
| --- | --- | --- |
| New endpoint is server-gated, not UI-gated | `require_manual_processing_admin` (`backend/api/manual_processing_admin.py:75`) requires **internal staff** *and* the admin-grade `can_manage_organizations` permission | enforced in code |
| Customer cannot reach the admin lookup | **Live negative test**: `mp.owner.dual` → `GET /api/v3/admin/manual-processing/organizations?q=ab` → **403** `Staff access required (active staff profile)` | DENY confirmed |
| Authorised internal admin can reach it | **Live positive test**: `platform.admin` → same route → **200** with `organizations[].name` present | ALLOW confirmed |
| No new authorization model / permission vocabulary | the diff adds typed *refusal* classes only; the existing `can_manage_organizations` permission is reused | confirmed |
| Tenant isolation unchanged | the lookup is the CarbonTally-internal control plane and is read-only; no customer surface consumes it | confirmed |
| No RLS weakened | no policy, table or role change; no service-role shortcut added | confirmed |
| Frontend is not the security boundary | the disabled "Load client state" control is a *safety* affordance; the server re-validates the selected client on the subsequent action | confirmed |
| No secrets introduced | no credential, token, JWT or signed URL added to source, tests or this report | confirmed |
| Reads do not mutate | selecting a search result performs no state change; the endpoint has no write path | confirmed by test |

**Security testing performed here:** the new surface was exercised in both
directions (ALLOW for internal admin, DENY for a customer owner). The full
cross-tenant matrix (Consultant A→B, PE A→B, and the rest of AGENTS.md §45) was
**not** re-run and remains with the independent verification task; nothing in
this change alters those boundaries.

---

## 16. Runtime verification (live local stack)

**A backend restart was a technical necessity and is disclosed here.** The
`uvicorn` process on `:8070` predated these edits and runs **without**
`--reload`, so the new F-11 route was not mounted (it returned 404, and live UI
checks could not pass). The backend was restarted using the repository's own
documented mechanism — `tools/demo_lab/lab_env.py --write` plus
`set -a; . "<env>"; set +a` before `uvicorn main:app` from `backend/`, exactly as
`tools/demo_lab/run_demo_lab.sh` does. A first restart attempt used a plain shell
environment and produced misleading 401 responses; that attempt was discarded
and is **not** the basis of any evidence below.

| Check | Command / artefact | Result |
| --- | --- | --- |
| Backend health | `GET /health` on `127.0.0.1:8070` | 200 |
| New route mounted | `GET /api/v3/admin/manual-processing/organizations?q=ab` | 401 pre-auth → 403 (customer) / 200 (admin) |
| Authenticated reads are real | real GoTrue password grants (no minted/forged tokens) | 200 |
| NV-5/NV-6 | `python3 tools/demo_lab/nv_mp_ui_check.py` | **48/48 clean**, EXIT=0 |
| PD-5 fixture browser regression | `python3 tools/demo_lab/fixture_mp_coverage_browser.py` | **10/10 as expected**, EXIT=0 |
| NV-9 baseline | `python3 tools/demo_lab/perf_mp_baseline.py --iterations 12` | **6/6 budgets PASS + 3/3 indexes**, EXIT=0 |
| Fixture baseline preserved | allocate→release in the browser harness returns the meter to 1/3 | confirmed |
| Fixture baseline intact (DB) | `SELECT count(*) FROM consultant_mp_allocations WHERE consultant_id = <firm_selected> AND state='active'` | **1** (expected baseline) |
| F-9 invariant on the real DB | duplicated active `(consultant_id, organization_id)` pairs | **0** |

Evidence (local, outside the repository):
`mp_nv_ui_20261005T020514Z.json`, `mp_fixture_browser_20261005T020600Z.json`,
`mp_perf_baseline_20261005T020040Z.json`.

---

## 17. Regression found during self-verification and fixed

**Disclosed deliberately: a verification report that hides its own defects is
worthless.**

While adding the F-11/NV-9 batch read, an intermediate edit to
`backend/data/organizations.py` **overwrote the `list_all()` method signature**,
leaving that method's body unreachable as dead code inside `get_many()`. The
Python remained syntactically valid, so neither an import error nor a unit-test
failure revealed it: the unit suites exercise the in-memory fakes, not this
repository class.

* **Root cause:** the new `get_many()` method was inserted directly on top of the
  `async def list_all(...)` signature line rather than above the method.
* **Impact had it shipped:** `repos.organizations.list_all()` is called by the
  commercial/admin surfaces (`backend/api/v3_commercial.py:455` and `:649`).
  Those calls would have raised `AttributeError` at runtime — a 500 on an
  unrelated feature (organisation/billing listing), i.e. a cross-feature
  regression caused by a Manual-Processing change.
* **Detection:** a deliberate AST scan over every file this task edited, looking
  for statements made unreachable by a preceding `return`/`raise`/`continue`/
  `break` in the same block. The scan reported the orphaned block in
  `organizations.py`.
* **Fix:** `get_many()` and `list_all()` are now two intact methods; the file
  compiles, and re-running the same scan across all edited files reports clean.
* **Residual risk:** none identified. `list_all()` is restored to its prior
  behaviour, and the real-repository path is exercised by the live stack
  (§16) and by `tests/integration/test_v3_repositories.py`.

**Lesson recorded for this workstream:** unit suites backed by in-memory fakes
cannot detect repository-class breakage. Structural scanning (or an integration
test against the real repository) is required when editing repository classes.

---

## 18. Git state and artefacts

| Property | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD at time of work | `375a48dc1b9e9cfd74090bbf747554ae997acb59` |
| Commits created by this task | **none** |
| Pushes created by this task | **none** |
| Reset / clean / force-push / history rewrite | **none performed** |
| Working-tree state | this task's changes are present **uncommitted** in the working tree |

**Untracked artefacts created by this task:**

* `backend/api/v3_manual_processing_coverage.py` (pre-existing file, further edited)
* `backend/tests/unit/api/test_ct_mp_sub_004_prod_readiness.py`
* `tools/demo_lab/nv_mp_ui_check.py`
* `tools/demo_lab/perf_mp_baseline.py`
* `docs/architecture/CT-MP-SUB-004-PROD-READINESS-01-report.md`

**Pre-existing working-tree content deliberately preserved:** the branch carries
many modified and untracked files from earlier CT-MP-SUB-003/004 and other
workstreams (routing/upload services, docs, `backend/api/router.py`,
`.gitignore`, and so on). None of it was reverted, cleaned or `git checkout`-ed.
Two stray zero-byte files in the repository root (`8`, `=`) predate this session
(datestamp 2026-09-23) and were left untouched.

**Secrets:** no `.env` file, credential, API key, password, JWT, signed URL or
generated secret was read into, or written to, any artefact of this task. The
local demo environment file lives **outside** the repository
(`/home/shomonrobie/ct_local_env/demo_lab/backend.env`) and is not committed.

---

## 19. Per-item final status

Acceptance vocabulary is used strictly (AGENTS.md §73): **IMPLEMENTED** (code
exists), **TESTED** (automated coverage passes), **VERIFIED** (exercised against
the live local stack with recorded evidence), **READY FOR INDEPENDENT
VERIFICATION** (self-verified; an independent task must confirm). Nothing here is
`ACCEPTED` — the PO/independent verification owns that word.

| Item | Disposition | Tests | Live evidence | Remaining |
| --- | --- | --- | --- | --- |
| **F-4** | **IMPLEMENTED / TESTED / VERIFIED** | FE 22/22 MP, 571/572 full; BE 151/151 MP, 4 948/4 956 full | suites run against the current tree; every failure classified in §5 | 8 backend + 1 frontend failures owned by other workstreams |
| **F-7** | **IMPLEMENTED / TESTED / VERIFIED** | typed-refusal contract incl. the negative case | allocate/release exercised live | none known |
| **F-9** | **IMPLEMENTED / TESTED / VERIFIED** | duplicate + capacity refusal contract | concurrent write path runs against the real DB with the advisory lock and partial unique index | production-scale concurrency not load-tested (P-1) |
| **F-11** | **IMPLEMENTED / TESTED / VERIFIED** | search contract + `get_many` mapping; FE selector tests | live 403 for customer / 200 with names for admin; fixture browser 10/10; NV harness gate checks | none known |
| **NV-5** | **IMPLEMENTED / TESTED / VERIFIED** | 48/48 checks | live browser at 8 viewports | limited to the six MP surfaces; NV-7 out of scope |
| **NV-6** | **IMPLEMENTED / TESTED / VERIFIED** | accessibility checks in the same 48 | live DOM audit | baseline, not a full WCAG audit |
| **NV-9** | **IMPLEMENTED / TESTED / VERIFIED** | 6/6 budgets + 3/3 index assertions | live stack, 12 iterations | production SLO is **P-1 / PO decision required** → **P-1 CLOSED (no dedicated production SLO for this release)**; see §21 |
| **NV-10** | **IMPLEMENTED / TESTED / VERIFIED** | 3 notification-behaviour tests | audit records observed; notification count unchanged | proactive notification is **P-2 / PO decision required** → **P-2 CLOSED (not required; audit-only retained)**; see §21 |

**Nothing in this task is `ACCEPTED`.** The eight items are self-verified only.

---

## 20. Declaration and next step

**What was done.** The eight PO-authorised items were remediated in application
code, tests and verification tooling; the work was self-verified with unit,
component, browser and performance evidence on the live local stack; every test
failure on the branch was classified with evidence; one regression introduced
during this task was found and fixed before reporting (§17); two items that are
product policy were escalated rather than invented (§13).

**What was NOT done** (deliberately): no commit, no push, no production
deployment, no migration applied, no schema/RLS/role/authorization/business-rule
change, no new external provider, no NV-7, no I4, no independent acceptance.

**Honest limitations:**

1. All live evidence comes from the **local Demo-Lab stack**, not production.
2. NV-5/NV-6 cover six Manual-Processing surfaces across eight viewports — not
   the whole application, and not a full WCAG audit.
3. The NV-9 thresholds are **local interactive budgets**, not a production SLO
   (P-1).
4. Nine test failures remain on this branch. All nine are classified as
   pre-existing/unrelated with evidence (§5); none is Manual-Processing related.
   They are **not** claimed as fixed.
5. The full cross-tenant security matrix (AGENTS.md §45) was not re-run; the new
   F-11 surface was verified ALLOW/DENY only.
6. A backend restart was required to make the live evidence valid, and that
   restart is disclosed in §16.

**Verdict for this task:**

> **IMPLEMENTED, TESTED AND SELF-VERIFIED — READY FOR INDEPENDENT VERIFICATION.**

The next step is a **separate, independent verification task** covering F-4, F-7,
F-9, F-11, NV-5, NV-6, NV-9 and NV-10 (plus the two PO decisions in §13). This
report must not be treated as, or substituted for, that independent acceptance.

> **Governance update (2026-10-05).** The two PO decisions formerly pending in
> §13 (**P-1**, **P-2**) are now **CLOSED**. The independent verification target
> for **NV-9** and **NV-10** is therefore governed by
> `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` §4 and §6
> (see §21). The remaining items (F-4, F-7, F-9, F-11, NV-5, NV-6) are unchanged.

---

## 21. Governance status update — P-1 / P-2 CLOSED (2026-10-05)

This section is **appended governance metadata**. It does **not** amend any
historical evidence, test result or implementation claim above; it records that
the two questions this report recorded as pending have since been decided by the
Product Owner.

| Item | State recorded in §11/§12/§13 | **PO decision (2026-10-05)** |
| --- | --- | --- |
| **P-1** (NV-9) | *PO DECISION REQUIRED — production-scale SLO* | **CLOSED — no dedicated production performance SLO is required for Manual Processing coverage operations for this release.** The existing budgets remain **engineering/verification** budgets with an explicit **non-production** disclaimer; required indexes remain; **no** production SLO or capacity claim may be made. |
| **P-2** (NV-10) | *PO DECISION REQUIRED — proactive allocation/release notification* | **CLOSED — proactive Manual Processing notifications are not required for this release.** Allocation/release remain **audit-only**; no new notification event/recipient/preference/provider/outbox is authorised; existing notification architecture unchanged. |

**Authoritative source:** `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md`
(Document ID `CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01`, dated 2026-10-05).

**Distinction of authorities (AGENTS.md §73):**

* **What Cline implemented** — the eight remediated items and their verification
  tooling, as evidenced in §§1–20 of this report. **Unchanged.**
* **What the fact-finding established** —
  `CT-MP-SUB-004-PROD-READINESS-PO-FACTFIND-01-report.md`. **Unchanged.**
* **What the PO has now decided** — P-1 CLOSED and P-2 CLOSED, recorded in the
  decision record above. This is **product policy**, not implementation.

**Effect on acceptance:** NV-9 and NV-10 are no longer open PO blockers. Their
acceptance behaviour is now exactly as stated in the decision record §4/§6. This
update does **not** grant production deployment, migration application, or
CT-MP-SUB-004 acceptance — those remain subject to independent verification.

---

## 22. Governance status update — P-2 scope clarification (Notification fact-finding 02, 2026-10-05)

This section is **appended governance metadata**. It does **not** amend any
historical evidence, test result, implementation claim or PO decision above.

**Source:** `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-FACTFIND-02-report.md`
(read-only fact-finding; status *NOTIFICATION FACT-FINDING COMPLETE — READY FOR PO
CLARIFICATION*). The authoritative decision record
`docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` is **unmodified**.

**Scope limit established for P-2:**

| Question | Status |
| --- | --- |
| Are proactive notifications required for Manual Processing **coverage allocation / release** (NV-10)? | **CLOSED — not required; remains audit-only.** Unchanged. |
| Must any actor be notified when a **document batch/item enters Manual Processing** (automatic-extraction fallback routing; a batch/entity or item assignment by operations)? | **OPEN — PO DECISION REQUIRED.** P-2 neither requires nor prohibits it. |

**Effect on the NV-10 statements in §11/§12/§19/§21 of this report:** the NV-10
entry (*notification behaviour defined and verified*; P-2 CLOSED) applies **only**
to the coverage allocation/release surface. It must **not** be read as closing the
MP-entry question, and the current absence of an MP-entry notification is **not**
characterised here as a defect.

**Independent-verification effect:** the NV-10 verification target is **unchanged**
for the coverage surface (audit-only; no unauthorised notification side effect;
existing notification architecture intact; no new notification subsystem). If the
PO amends P-2 with the proposed §5.1a scope limit, verification extends per
`…NOTIFICATION-FACTFIND-02-report.md` §9.2.

**Not changed by this update:** the P-1 decision; the P-2 decision on coverage;
the five prohibition statements in the decision record §8.1; the eight remediated
items (§§6–12); the acceptance target for `F-4`, `F-7`, `F-9`, `F-11`, `NV-5`, `NV-6`.
