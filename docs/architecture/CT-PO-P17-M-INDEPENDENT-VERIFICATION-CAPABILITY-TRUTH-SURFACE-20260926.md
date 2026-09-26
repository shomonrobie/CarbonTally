# CT-PO-P17-M — INDEPENDENT VERIFICATION — CAPABILITY TRUTH SURFACE (2026-09-26)

**Task id:** P17-M-20260926-INDEPENDENT-VERIFICATION-CAPABILITY-TRUTH-SURFACE
**Author:** Independent Verification Agent (read-only verification; **no implementation changes**)
**Environment:** local disposable PostgreSQL clones on `127.0.0.1:54426` (supabase `postgres` container)
**Verdict class:** exactly one — see §21
**Supersedes:** an earlier untracked draft of this same path (see §3.3)

---

## 1. Task identity

Independent verification of the **P17-K** (governed capability catalogue) and
**P17-L** (capability truth surface) claims. Both reports were treated as
*claims to be tested*, never as proof. Nothing in the application was modified.
No production system was contacted. Nothing was pushed.

The verification question is deliberately narrow and adversarial:

> Does CarbonTally, as it exists in the repository **right now**, actually serve a
> capability statement that (a) is derived from a governed catalogue, (b) is
> reproducible, (c) is the same statement for every tenant, (d) cannot be
> fabricated, upgraded or downgraded by residue, and (e) is truthful about what
> is *not* known?

## 2. Repository truth (starting state)

| Item | Observed value |
|---|---|
| Authoritative repo | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD (start = end) | `19c850b9f1cfe7e77aacca5338aad29921f0e193` |
| P17-K implementation SHA | `3f3dfa41` |
| P17-L change set | `git diff --stat 3f3dfa4 19c850b` → **15 files, 5247 insertions(+), 2 deletions(-)**, no migration |
| Working tree | `.gitignore` modified (pre-existing, CRLF→LF + `.aider*`); 18 pre-existing untracked paths |
| Commits made by this task | **none** |
| Push issued | **no** |

### 2.1 Material discrepancy about the working directory named in the task

The task statement located the repository at `/home/shomonrobie/carbon_tally`.
That path contains **none** of the P17-K/P17-L artifacts (no
`20261020000000_p17k_governed_capability_catalogue.sql`, no
`backend/domain/capability_catalogue.py`, no `frontend/src/v3/capabilities/`).
All P17-K/P17-L material exists only in `/home/shomonrobie/ct_93d5cdd`
(branch `p8-release-reconciled`, HEAD `19c850b9`). Verification was therefore
performed against `ct_93d5cdd`, and this discrepancy is reported rather than
silently worked around.

## 3. Evidence environment

### 3.1 Clones used (all disposable, all on the local container)

| Clone | Purpose | Catalogue state |
|---|---|---|
| `ct_iv_p17m_20260926` | earlier same-lineage clone (tenant-isolation / API scenario runs) | governed catalogue present |
| `ct_iv_p17m_b_20260926` | migration idempotency (3rd application) | governed catalogue present |
| `ct_iv_p17m_c_20260926` | API/DB/DOM verification, adversarial injection | governed catalogue present (18 rows) |
| `ct_p17m_nocat_20260926` | fail-closed probe | **no** framework versions |
| `ct_iv_demo_guard_probe_20260926` | F-046-1 guard probe (created + dropped inside this task) | empty, never used for data |

### 3.2 Protected environments — never written

| Environment | Observed |
|---|---|
| `carbontally_demo_local` | `disclosure_framework_versions = 0`, `disclosure_requirement_versions = 0`, `organizations = 4`, P17-K migration marker `= 0` |
| `ct_local_93d5cdd` | `0`, `0`, `organizations = 25`, marker `= 0` |
| `carbontally_test` | no `disclosure_*` tables at all (different schema lineage) |
| Production (`carbontally-api.onrender.com`, `carbontally.co.uk`) | not contacted; only referenced read-only in configuration |

No statement issued by this task named a protected database. Every write
(`INSERT`, `DELETE`, DDL, migration application) was executed against a
`ct_iv_*` clone. The demo environment shows **zero** P17-K catalogue rows both
because the catalogue was never applied there and because nothing in this task
touched it.

### 3.3 Report-file provenance

An earlier untracked draft of this path existed at verification start:

```
mtime  2026-09-26 12:29:58 +0600
size   28660 bytes
sha256 11882ac69e49430e5684a3af13300db32c010489813d67d26212f5b389e3fbeb
git    untracked (no log, no blame)
```

It was backed up before any write, its claims were re-derived independently
during this task, and this document supersedes it. Its headline conclusion
(the framework-version selection defect) was **independently reproduced by
primary evidence produced in this task** — see §10 — so the supersession is a
strengthening of evidence, not a reversal.

## 4. Method and independence

1. **Ground truth first** — branch, HEAD, working tree, toolchain, then the
   implementation files themselves (`v3_disclosure.py`, `capability_catalogue.py`,
   the migration, both frontend pages, the P17-K and P17-L reports).
2. **Own clones, own schema** — the migration was applied by this task to
   disposable clones; the DB was then interrogated with hand-written read-only
   SQL (sections A–I), not with the project's own assertions.
3. **Own probes** — the real FastAPI router was mounted in-process
   (`httpx.ASGITransport`) with only the pool and the authenticated user
   dependency overridden, so the route, its projection module and its SQL were
   exercised exactly as production would exercise them.
4. **Adversarial tests** — deliberately constructed DB states (a competing
   framework version carrying a *governed* requirement identity) to test the
   selection rule outside its happy path.
5. **Negative tests** — no catalogue, malformed token, absent org, staff actor,
   non-member actor, and a same-day tripwire for destructive harness setup.
6. **Cross-context comparison** — the *same* endpoint called from six+ different
   authenticated identities, byte-compared.
7. **In/out of band counting** — test outcomes were taken from JUnit XML written
   by pytest itself, because this terminal's stdout capture is unreliable
   (see §20).

Independence statement: the verification did not import the P17-K/P17-L reports'
conclusions into the checks. Where a claim could be tested two ways
(e.g. "18 rows" — by SQL and by served payload), both were executed.

## 5. Artifacts inspected (read-only)

| Artifact | Role |
|---|---|
| `supabase/migrations/20261020000000_p17k_governed_capability_catalogue.sql` | governed catalogue DDL/seed |
| `backend/domain/capability_catalogue.py` | canonical projection (single source of truth) |
| `backend/api/v3_disclosure.py` | `GET /api/v3/capabilities` route |
| `frontend/src/v3/capabilities/CapabilitiesPage.jsx` | customer surface `/capabilities` |
| `frontend/src/v3/capabilities/InvestorCapabilityPage.jsx` | product surface `/capabilities/product` |
| `frontend/src/v3/components/CapabilityTruthSurface.jsx` | shared renderer (both surfaces) |
| `frontend/src/v3/capabilities/capabilities.css` | presentation |
| `backend/tests/integration/conftest.py` | F-046-1 destructive-setup guard |
| `docs/architecture/CT-PO-P17-L-CAPABILITY-TRUTH-SURFACE-20260926.md` | the claims under test |
| P17-K report / master workplan | the claims under test |

## 6. Verification matrix

Proof levels used: **DB** = direct SQL on the clone; **API** = real route driven
in-process; **DOM** = rendered React output; **SRC** = source inspection; **RUN**
= test-suite execution.

| # | Claim under test | Proof | Verdict |
|---|---|---|---|
| 1 | Migration applies cleanly | DB | **PASS** |
| 2 | Migration is idempotent on re-application | DB+RUN | **PASS** |
| 3 | Catalogue contains exactly 18 governed rows, 18 distinct codes | DB+API | **PASS** |
| 4 | Uniqueness enforced structurally (PK + UNIQUE(version, code)) | DB | **PASS** |
| 5 | Capability vocabulary is a closed, constraint-enforced set of 7 | DB | **PASS** |
| 6 | Category→capability mapping equals the ratified M-1 mapping | DB | **PASS** |
| 7 | Rollup equals 4/6/3/2 and is served | API | **PASS** |
| 8 | Provenance complete (locator + authoritative text ref + tier 1) | DB | **PASS** |
| 9 | Official identifiers are not invented | DB | **PASS** |
| 10 | RLS/tenant columns: catalogue is global, not tenant-scoped | DB | **PASS** |
| 11 | Endpoint exists at `GET /api/v3/capabilities` and is authenticated | API | **PASS** |
| 12 | Endpoint accepts no org/tenant selector | API+SRC | **PASS** |
| 13 | Same statement for every tenant (byte-identical, 6+ contexts) | API | **PASS** |
| 14 | No tenant identifier or tenant data in the payload | API | **PASS** |
| 15 | No-fabrication: no catalogue ⇒ explicit refusal, not an empty claim | API | **PASS** |
| 16 | Customer surface renders the governed vocabulary | DOM | **PASS** |
| 17 | Product surface renders product-level, not customer-level, truth | DOM | **PASS** |
| 18 | Both surfaces state "capability is not a result" | DOM | **PASS** |
| 19 | Failing load ⇒ bounded error + retry, never a fabricated claim | DOM | **PASS** |
| 20 | Gates AG-1…AG-8 hold | RUN+DB+API+DOM | **PASS** |
| 21 | P17-L's framework-version selection rule is sound | API+DB | **FAIL** |
| 22 | P17L-F2 is "closed" with "no residual limitation" | API+DB | **FAIL** |
| 23 | "No applicability model exists" (as worded) | DB+SRC | **PASS (qualified)** |
| 24 | P17-J boundary not absorbed; demo/production untouched | SRC+DB | **PASS** |

Two matrix rows fail. Both trace to one property of the system (framework-version
selection) and one over-claim in the P17-L report. Everything else verified.

## 7. P17-K — governed capability catalogue (verified)

### 7.1 Migration and idempotency

The migration `20261020000000_p17k_governed_capability_catalogue.sql` was applied
to a fresh disposable clone and then **applied a third time** by this task.
Measured before → after:

```
versions_total      1        → 1
gov_versions        1        → 1
catalogue_rows     18        → 18
dup_codes           0        → 0
md5 signature       1c3dbaefdefc2936371458f6b5e34045
                             (identical before and after)
reapply exit        0  (no stderr)
```

The re-application neither duplicated rows nor changed the catalogue's content
signature. **PASS.**

### 7.2 Catalogue shape (read-only SQL, sections A/B/C)

| Property | Observed |
|---|---|
| governed requirement rows | **18** |
| distinct `requirement_code` values | **18** |
| duplicate codes | **0** |
| structural uniqueness | primary key **+** `UNIQUE (framework_version_id, requirement_code)` |
| capability vocabulary constraint | closed check set of **7** values |
| classification vocabulary constraint | closed check set (8 values) |
| class distribution | 6 / 6 / 3 / 3 |

### 7.3 Category → capability mapping vs the ratified M-1 mapping (section D2)

| Capability | Categories observed | M-1 expectation | Match |
|---|---|---|---|
| `SUPPORTED` | 3, 4, 5, 6 | 3, 4, 5, 6 | **exact** |
| `PARTIALLY_SUPPORTED` | 1, 7, 8, 9, 12, 13 | 1, 7, 8, 9, 12, 13 | **exact** |
| `FUTURE` | 11, 14, 15 | 11, 14, 15 | **exact** |
| `MISSING_CAPABILITY` | 2, 10 | 2, 10 | **exact** |

Rollup served by the projection matches the row distribution exactly:
**SUPPORTED 4 / PARTIALLY_SUPPORTED 6 / FUTURE 3 / MISSING_CAPABILITY 2**
(monotone, i.e. `4/6/3/2`). **PASS.**

### 7.4 Provenance and truthfulness about the unknown (section E)

| Check | Observed |
|---|---|
| rows with `source_locator` + `authoritative_text_ref` | 18 / 18 |
| rows not at `source_tier = 1` | 0 |
| rows with an invented `official_identifier` | 0 |
| identifier status | every row `UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION` |

The catalogue therefore refuses to assert the official paragraph identifiers it
does not possess. That is the honest behaviour P17-K claimed. **PASS.**

### 7.5 Tenancy shape (sections F/G)

The governed catalogue carries **no tenant column** (no `organization_id`, no
`org_id`). Tenant columns appear only on genuinely tenant-scoped tables.
Foreign keys bind requirement rows to their framework version, and version to
framework. No catalogue table carries an applicability or coverage attribute.
**PASS.**

## 8. P17-L — canonical truth surface (verified, with one falsified claim)

### 8.1 Claims verified TRUE

| P17-L claim | Independent evidence |
|---|---|
| One canonical projection module is the single source of truth | `backend/domain/capability_catalogue.py` consumed by the route and by both frontend surfaces via one shared component |
| Endpoint is authenticated | unauthenticated call is rejected by the auth dependency before business logic |
| Endpoint takes no organisation/tenant selector | route signature and driven requests: no `org`/`tenant` parameter influences the response |
| Statement is tenant-independent | 6+ identities (two real org owners, a real member of a third org, a staff non-org actor, a non-member) returned **one distinct body**, canonical digest `1110d3669d3537e1`, 25637 bytes |
| No tenant identifier leaks | token scan of the served payload: `organization_id` absent, `org_id` absent, `client` absent, `member` absent |
| Capability is never presented as a result | DOM test: both surfaces render the capability-is-not-a-result statement |
| Vocabulary is explained, not just listed | DOM test: the glossary explains the governed vocabulary actually rendered |
| Unrecognised values are surfaced verbatim, not hidden or invented | DOM test: unrecognised capability value still rendered verbatim |
| Fail-closed when unprovisioned | §9.3 — HTTP **503** with an explicit refusal, no fabricated statement |
| Customer vs product separation | DOM tests: product surface visibly labelled product-level; customer surface points to its own results, the product surface does not |

### 8.2 Claim verified FALSE — "P17L-F2 closed, no residual limitation"

P17-L declares the framework-version selection defect (`P17L-F2`) closed with no
residual limitation. The adversarial test in §10 shows the *specific* earlier
manifestation no longer reproduces, while a **materially wider manifestation
does**: a second `IN_FORCE` tier-1 version carrying its **own governed
requirement identity** is selected in preference to the governed catalogue, and
the served surface then makes a **narrower and upgraded** capability claim
(category 1 rendered `SUPPORTED`, rollup `1/0/0/0`). The claim is over-broad.
**FAIL.**

### 8.3 Claim PASS with qualification — "no applicability model exists"

As stated of the capability surface this is true and verified: the governed
catalogue has no applicability/coverage attribute, the projection emits none,
and the payload contains neither `applicability`, `does_not_apply` nor
`assessed_status`. **However**, the schema does contain a *separate*
tenant-scoped `disclosure_applicability_assessments` relation (referenced from
`disclosure_report_instance_binding.applicability_assessment_id`), and
`disclosure_framework_versions` carries `applicable_from` / `applicable_to`
(temporal validity). The literal phrasing "no applicability column exists" is
therefore too broad: true of the capability catalogue and surface, not of the
schema as a whole. Reported as DEF-3 (documentation precision), not as a
functional defect.

## 9. Endpoint scenarios (`GET /api/v3/capabilities`)

The real ASGI app was driven with only the pool and authenticated identity
overridden, against clone `ct_iv_p17m_c_20260926` unless stated.

| Scenario | Observed | Verdict |
|---|---|---|
| 9.1 Governed baseline | `200`; served version = *Corporate Accounting and Reporting Standard (2004 revised edition)*; 18 requirements; rollup `4/6/3/2`; rollup basis present | **PASS** |
| 9.2 Six+ identities (org owners, member, staff, non-member) | identical canonical body; 1 distinct digest | **PASS** |
| 9.3 No catalogue (`ct_p17m_nocat_20260926`: 0 versions, 0 governed rows) | `503`; body keys `["detail"]` only; detail = *"The governed capability catalogue is not provisioned, so no capability statement can be made."*; 0 requirements; rollup `null` | **PASS** |
| 9.4 Malformed / absent authentication | rejected before business logic (no capability statement) | **PASS** |
| 9.5 Selector injection (`org`, `tenant` params) | no effect on the response; no tenant lookup performed | **PASS** |
| 9.6 Direct-DB contrast | DB holds 18 governed rows for the governed version; payload holds 18; counts agree | **PASS** |

Scenario 9.3 is the decisive truthfulness test: an unprovisioned database
produces an explicit refusal rather than a plausible-looking empty capability
table. That is the opposite of fabrication.

## 10. Adversarial test — framework-version selection (DEF-1, PRIMARY EVIDENCE)

Two variants of a *second* `disclosure_framework_versions` row under the same
framework, each carrying one **governed** requirement identity
(`GP-S3-CAT-01`, a code that legitimately belongs to the governed catalogue and
denotes `SUPPORTED`), both `IN_FORCE`:

* **Variant A** — tier 1, label `AAA-IV-conflict` (sorts *before* the governed version)
* **Variant B** — tier 2, label `ZZZ-IV-conflict` (sorts *after* the governed version)

Observed (real route, real DB, clone `ct_iv_p17m_c_20260926`):

```
baseline     200 version='Corporate Accounting and Reporting Standard (2004 revised edition)'
             requirements=18  category_1='PARTIALLY_SUPPORTED'
             rollup={SUPPORTED:4, PARTIALLY_SUPPORTED:6, FUTURE:3, MISSING_CAPABILITY:2}

variant A    200 version='AAA-IV-conflict'
             requirements=1   category_1='SUPPORTED'          <-- UPGRADED
             rollup={SUPPORTED:1, PARTIALLY_SUPPORTED:0, FUTURE:0, MISSING_CAPABILITY:0}

variant B    ignored -> governed version served, 18 requirements, rollup 4/6/3/2

cleanup      residual injected versions: 0; governed rows restored: 18
             rollup restored: 4/6/3/2   (clone left as found)
```

Interpretation, stated precisely:

1. A conflicting version that itself carries governed requirement identities can
   **replace** the governed catalogue and cause the product surface to publish a
   *narrower and more favourable* capability claim, with HTTP `200` and no
   warning. This is a false-capability-statement path: the value a customer or
   investor would read (category 1 = `SUPPORTED`) is not the governed truth
   (category 1 = `PARTIALLY_SUPPORTED`).
2. Variant B is ignored because of **ordering**, not because of an identity test.
   Both variants carry governed codes; only sort position and tier differ. The
   surface's safety against residue therefore currently depends on which row the
   selection walk meets first, not on an explicit governed-catalogue identity
   check.
3. The originally reported `P17L-F2` manifestation (non-governed test residue
   being selected) does **not** reproduce — that part of the P17-L fix works.
   What does not hold is the stronger claim that the defect is closed with no
   residual limitation.
4. Severity: **HIGH** as a truthfulness/trust defect on a surface whose entire
   purpose is to make non-overclaimable statements about CarbonTally's
   capabilities; **LOW** as an immediate operational risk (the conflicting state
   requires a second `IN_FORCE` tier-1 version carrying governed identities,
   which today's databases do not contain). It is a latent defect with a
   demonstrable, reproducible exploit path — not a currently-manifest outage.

## 11. Acceptance gates AG-1…AG-8

Each gate was located in the test corpus and its assertion re-run by this task
against the clone.

| Gate | Meaning (as implemented) | Where verified | Verdict |
|---|---|---|---|
| AG-1 | every produced/derived capability value is a member of the governed vocabulary | unit + integration + DOM | **PASS** |
| AG-2 | every category derives a governed outcome and the outcomes stay distinct (`NOT_SUPPORTED` ≠ `INPUT_REQUIRED`; `FUTURE` ≠ `MISSING`) | integration `test_ag_2_every_category_derives_a_governed_outcome`; unit `test_ag_2_*` in three modules; API `test_ag_2_not_supported_and_input_required_stay_distinct` | **PASS** |
| AG-3 | provenance retained through the projection | unit + integration + DOM | **PASS** |
| AG-4 | no applicability semantics enter the capability surface | unit + DOM | **PASS** |
| AG-5 | no tenant identifier rendered on either surface | DOM (`ag_5 …`) + API payload scan | **PASS** |
| AG-6 | capability is not presented as an emissions result | DOM (`ag_6 …`) | **PASS** |
| AG-7 | vocabulary is explained to the reader | DOM (`ag_7 …`) | **PASS** |
| AG-8 | failure to load never becomes a claim | DOM (`ag_8`/error-state tests) | **PASS** |

Gate results were taken from the *tests' own assertions*, run on my clone, with
the frontend gates additionally confirmed at the rendered-DOM level (19/19 DOM
tests green in §13).

## 12. Tenant isolation and payload content

Six-plus distinct authenticated contexts were used, including **real
organisations and real memberships read from the clone** (two distinct org
owners, a member of a third org, a staff actor with no organisation, and a
non-member actor):

```
all_identical        true
distinct_bodies      1
canonical_digest     1110d3669d3537e1
body_len             25637
```

Token scan of the served body:

| Token | Present? | Explanation |
|---|---|---|
| `organization_id` | **no** | — |
| `org_id` | **no** | — |
| `client` | **no** | — |
| `member` | **no** | — |
| `organisation` | yes | appears only inside requirement **detail prose** (e.g. "paid for by the reporting organisation"), i.e. domain vocabulary, not data |
| `tenant` | yes | as above ("whether franchisees are tenants or external parties") |
| `supplier` | yes | as above ("supplier figure vs spend-based") |

Every textual hit was individually inspected in context; none is an identifier
or a tenant value. The statement served to an owner of org A is byte-identical
to that served to a member of org B and to a staff actor. **PASS.**

## 13. Frontend truth surfaces

Both surfaces were rendered in a real test environment (`react-scripts` jest)
and asserted at the DOM level, not by string-in-source inspection:

```
Test Suites: 1 passed, 1 total
Tests:       19 passed, 19 total
```

Included: AG-1/3/4/5/6/7/8 gates; "the capability-is-not-a-result statement is
rendered on both surfaces"; "the customer surface points to its own results, the
product surface does not"; "an unrecognised capability value is still rendered
verbatim"; "a failing load shows a bounded error with a retry, never a claim";
"the error state retries through the same single request"; "the glossary explains
the governed vocabulary it renders"; and the AG-5 no-tenant-identifier and
product-labelling assertions.

The investor/product surface was specifically checked to **lack**: an
organisation resolver, any tenant parameter, customer data, fabricated results,
applicability semantics, and coverage claims. It presents product-level truth and
says so. **PASS.**

## 14. Regression evidence (JUnit XML — pytest's own report, not stdout)

Test outcomes below come from XML files written **by pytest itself**, because
this terminal's stdout capture is demonstrably lossy (§20). Two earlier
dot-line captures in this task were truncated and would have under-reported or
mis-reported counts; the XML runs supersede them.

| Suite | Target | Tests | Failures | Errors | Skipped |
|---|---|---|---|---|---|
| P17-K/P17-L canonical **unit** modules (catalogue, truth surface, projection) | in-process | **152** | **0** | **0** | 0 |
| P17-K runtime + P17-L runtime + P17-09 + P17-10 **integration** | clone `ct_iv_p17m_c_20260926` | **125** | **0** | **0** | 0 |
| Whole `tests/unit` suite | in-process | **3978** | **9** (baseline, §14.3) | **0** | 8 |
| Frontend capability DOM suite | jest/react-scripts | **19** | **0** | 0 | 0 |
| F-046-1 guard (negative) | throwaway `…demo-guard-probe…` DB | 1 | exit 1 **as designed** | — | — |

### 14.1 Whole-unit baseline

Failures in the wider unit suite, where they occur, are in areas unrelated to
the capability surfaces (SLA surface registration, "migration is the latest"
ordering assertions, extraction suggestions). They are pre-existing baseline and
were not caused by this task: **no application or test file was modified by this
task at all**. §14.3 records the count.

### 14.2 P17K-F1 — NOT reproduced on this lineage, and the reason is now explicit

P17K-F1 claims the P17-09/P17-10 integration suites are not reproducible-green on
a *current*-schema clone because `calculation_snapshots.performed_by` carries a
validated FK to `auth.users(id)` while the fixture supplies a random UUID.
Direct `pg_constraint` comparison performed by this task:

| Database | `calculation_snapshots.performed_by` FK |
|---|---|
| `ct_iv_p17m_c_20260926` (my integration target) | **absent** |
| `ct_p17k_20260926` | present → `auth.users(id) ON DELETE SET NULL` |
| `carbontally_demo_local` | present → `auth.users(id) ON DELETE SET NULL` |

P17K-F1's *mechanism* is therefore independently confirmed on current-schema
databases, while **my integration run passed 125/125 precisely because my
disposable clone's lineage lacks that FK**. That green result is **not** evidence
that P17K-F1 is fixed, and it is not reported as such.

The one integration failure observed earlier in this task
(`test_the_p17_runtime_dimensions_exist`, `calculation_snapshots` missing
`scope3_method`, `transaction_provider`) occurred on a clone lacking the P17
migration's dimension columns; on `ct_iv_p17m_c_20260926` those columns exist and
the test passes. A clone-lineage artefact, not a defect claim.

### 14.3 Whole `tests/unit` suite (baseline, measured)

```
tests=3978  failures=9  errors=0  skipped=8
```

All 9 failures sit in five classes, none of which is a capability-surface file:

| # failing | Class |
|---|---|
| 3 | `tests.unit.api.test_review_sla_surfaces` |
| 1 | `tests.unit.data.test_d17_provider_ownership_migration_revision.TestRevisionScope` |
| 1 | `tests.unit.data.test_i1_insight_migration` |
| 1 | `tests.unit.data.test_i2_insight_authorization_contracts` |
| 3 | `tests.unit.engines.test_extraction_suggestions` |

No P17-K/P17-L module appears among the failures, which corroborates the green
P17-scoped result above. These 9 failures are pre-existing baseline (SLA surface
registration, "migration is the latest" ordering assertions, extraction
suggestions); this task modified no application or test file, so it cannot have
caused them, and it does not claim to have fixed them.

## 15. Protected environments, non-mutation, and the destructive-harness guard

### 15.1 Non-mutation

| Environment | Catalogue rows before/after | `organizations` | Verdict |
|---|---|---|---|
| `carbontally_demo_local` | 0 / 0 | 4 | untouched |
| `ct_local_93d5cdd` | 0 / 0 | 25 | untouched |
| `carbontally_test` | no `disclosure_*` tables | — | untouched |
| production | not contacted | — | untouched |

All writes performed by this task were confined to `ct_iv_p17m_b_20260926` and
`ct_iv_p17m_c_20260926`. The adversarial injection of §10 was fully reverted and
verified reverted (0 residual versions, 18 governed rows restored, rollup
restored to `4/6/3/2`).

### 15.2 F-046-1 tripwire — verified by execution, both directions

`backend/tests/integration/conftest.py` performs destructive setup
(`TRUNCATE … RESTART IDENTITY CASCADE`) and is required to refuse protected
targets. This was verified by *executing the real fixture*, not by reading it.

**DENY case.** A throwaway empty database whose *name* matched a protected
marker — `ct_iv_demo_guard_probe_20260926` — was created and the P17-K
integration module was pointed at it:

```
RuntimeError: refusing to run the integration suite against
'ct_iv_demo_guard_probe_20260926': the name matches the protected persistent
marker 'demo', and this fixture performs DESTRUCTIVE setup
(TRUNCATE … RESTART IDENTITY CASCADE). (PO operational control F-046-1.)
tests/integration/conftest.py:120
```

The refusal raised **before** any `TRUNCATE` executed; the probe database was
then dropped. It was deliberately created empty, so the DENY test carried zero
risk to real data.

**ALLOW case.** The same module ran green against `ct_iv_p17m_c_20260926`,
confirming the guard is not a blanket blocker.

**Verdict: PASS** — the F-046-1 invariant is enforced in code and holds under
execution.

## 16. Findings

### DEF-1 — HIGH (truthfulness) / LOW (immediate exposure): the capability statement can be silently *upgraded* by a competing governed version

Defined in §10. Reproduction is deterministic: one `INSERT` into
`disclosure_framework_versions` (tier 1, `IN_FORCE`, label sorting before the
governed version) plus one requirement row carrying a governed code. Impact: the
surface whose entire purpose is to make non-overclaimable statements about
CarbonTally's capabilities can be made to overclaim while returning HTTP `200`
with no warning; and, as variant B shows, the *outcome depends on row
ordering/tier rather than on a governed-identity test*.

Recommended correction (implementation decision — **not** performed here):
selection must be **identity-anchored** — resolve the governed version by an
explicit governed-catalogue identity (framework + governed marker/version code)
and either make any competing `IN_FORCE` version invisible to this surface or
treat it as a hard failure, instead of resolving by sort order. This is the same
*class* of defect the P17-L suite itself found, one scope wider.

### DEF-2 — MEDIUM (report accuracy): "P17L-F2 closed / no residual limitation" is over-stated

The P17-L report states the defect was found and fixed by that task with "none —
closed". The *specific* residue case is fixed (independently verified); the
*class* is not uniformly closed (DEF-1). The report should be amended to state
the residual limitation precisely.

### DEF-3 — LOW (documentation precision): "no applicability column exists" is too broad

Correct for the capability catalogue and the capability surface (verified).
Over-broad as a statement about the schema, which contains
`disclosure_applicability_assessments` (tenant-scoped; `assessed_status` ∈
`APPLIES` / `DOES_NOT_APPLY` / `UNDETERMINED` / `CUSTOMER_INPUT_REQUIRED`) and
framework-version validity dates `applicable_from` / `applicable_to`.

### Pre-existing, carried forward (neither caused nor fixed by this task)

* **P17K-F1** — FK-vs-fixture reproducibility gap. Mechanism independently
  confirmed (§14.2): FK present on current-schema DBs, absent on my clone
  lineage. **Open.**
* **P17K-F2** — `DECISION-03 §12.1` cites a non-existent column
  (`applicability_status`; the real column is `assessed_status`).
  **Open, documentation only.**
* **P17L-F1** — chain clones lacking the
  `disclosure_intensity_denominator_types` seed. Did **not** reproduce on my
  lineage; the earlier report's count of 11 such failures is therefore
  clone-provisioning-specific and is not asserted here as a general defect.
* **Wider unit-suite failures** (SLA surface registration, latest-migration
  ordering assertions, extraction suggestions) — baseline, unrelated to P17.

## 17. Remaining unknowns / non-claims

1. No live production environment was exercised. All conclusions are about the
   code at `19c850b9` plus a locally migrated clone of it.
2. `carbontally_test` does not carry the `disclosure_*` schema, so the project's
   own dedicated test database is **not** currently a viable target for these
   suites. Observation, not a verdict.
3. The provenance of the many same-day `ct_p17m_*` / `ct_p17k_*` / `ct_p17l_*`
   clones could not be established from clone metadata alone; only clones this
   task created or explicitly read are relied upon.
4. Claims outside the capability surface were not audited, except where needed
   as context.
5. **No application, test, migration or frontend file was modified by this
   task** — the only written file is this report.

## 18. Scope boundary: P17-J not absorbed

The change set under test (`3f3dfa4 → 19c850b`) touches **15 files** — the P17-K
migration, `backend/domain/capability_catalogue.py`, `backend/api/v3_disclosure.py`,
the P17-K/P17-L reports, the two capability pages, the shared
`CapabilityTruthSurface` renderer, its stylesheet, the V3 layout navigation
entry, and the associated tests. No P17-J artifact, route, migration or test file
was modified, and no P17-J behaviour was relocated into the capability surface.
The surface consumes the governed catalogue only; it does not absorb the
disclosure-applicability or report-instance machinery. **PASS.**

## 19. Verification-process notes (tooling honesty)

These notes exist so a reader can judge the strength of the evidence, and so the
same traps are avoided next time.

1. **Terminal stdout capture in this environment is lossy.** Several
   `pytest … | grep` invocations returned *empty* output while the same command
   redirected to a file produced content; a captured file ended mid-run while
   the process exited 0. Two early dot-line captures (`8` and `61` dots) were
   artefacts of that truncation. **Mitigation adopted:** pytest was re-run with
   `--junitxml=…` and counts read from pytest's own XML. All counts in §14 come
   from that channel. Future verification here should prefer JUnit XML or a
   database-committed evidence table over piped stdout.
2. **Multiple same-day clones.** The container carries many `ct_p17m_*`,
   `ct_p17k_*` and `ct_p17l_*` databases from earlier attempts. Clone lineage
   materially changes results (§14.2 is the clearest example), so a verification
   report must name the exact clone behind every DB-level claim. This report does.
3. **Cleanup discipline.** Every mutating probe in this task (adversarial
   injection, guard-probe database) was reversed and the reversal verified, not
   assumed.
4. **Guard-rail trade-off.** The DENY test for F-046-1 was executed against a
   purpose-built *empty* database rather than against a valuable environment,
   because pointing a destructive harness at `carbontally_demo_local` to "prove"
   the guard would be exactly the risk the guard exists to prevent. The refusal
   path is therefore proven with zero exposure to real data.

## 20. Summary of what was actually established

**Independently verified as working (with proof level):**

* governed 18-row catalogue, uniqueness, closed vocabularies, exact M-1 mapping — **DB**
* idempotent re-application with a byte-stable content signature — **DB**
* rollup `4/6/3/2` served to clients — **API**
* provenance completeness and refusal to invent official identifiers — **DB**
* authenticated, selector-free, tenant-independent endpoint — **API**, byte-compared across 6+ real identities
* explicit fail-closed behaviour (HTTP 503, one-line refusal, zero fabricated rows) when unprovisioned — **API**
* both frontend surfaces, including gates AG-1…AG-8, at rendered-DOM level — **DOM**
* 152 P17-scoped unit tests and 125 P17-scoped integration tests green — **RUN** (JUnit XML)
* the F-046-1 destructive-harness guard in both DENY and ALLOW directions — **RUN** (executed)
* non-mutation of demo, local, test and production environments — **DB**

**Independently falsified:**

* that framework-version selection is safe against a competing governed version,
  and the derived claim that `P17L-F2` is closed with no residual limitation
  (DEF-1/DEF-2), with a deterministic reproduction that makes the surface publish
  an **upgraded** capability claim.

**Explicitly not claimed:** that P17K-F1 is fixed; that the whole unit suite is
green; that production behaves identically; that any of the above constitutes
investor acceptance.

## 21. VERDICT

> ## `P17_M_INDEPENDENTLY_VERIFIED_FAILED`

**The P17-K governed capability catalogue and the P17-L canonical capability
truth surface are, in themselves, verified as built and honest** — the catalogue,
the projection, the endpoint, the tenancy independence, the fail-closed behaviour
and both frontend surfaces all held under independent DB, API, DOM and test
evidence.

**The P17-L report's own closing claim does not hold.** Framework-version
selection for the capability surface can be taken over by a competing `IN_FORCE`
version that itself carries governed requirement identities, in which case the
customer/product surface returns HTTP `200` while publishing a **narrower and
stronger** claim than the governed catalogue supports (`SUPPORTED` where the
governed truth is `PARTIALLY_SUPPORTED`; rollup `1/0/0/0` instead of `4/6/3/2`).
Because the governing surface exists precisely to prevent overclaiming, and
because the outcome currently depends on row ordering/tier rather than on a
governed-identity test, the correct verdict is **FAILED** — with the failure
scope stated narrowly above, and with the catalogue and truth-surface work
itself acknowledged as verified.

**Consequential follow-ups (no implementation performed here):**

1. **DEF-1 (implementation/PO decision):** anchor selection to a governed
   identity; decide whether a competing `IN_FORCE` version must be ignored, or
   must force a refusal. Deterministic reproduction is in §10.
2. **DEF-2:** amend the P17-L report's residual-limitation statement.
3. **DEF-3:** narrow the "no applicability column" wording to the capability
   surface.
4. **P17K-F1:** decide the fixture/FK question; the mechanism is confirmed but
   the status is environment-dependent (§14.2).
5. Adopt JUnit-XML evidence as the standard channel for verification runs in
   this environment (§19.1).

**Report state:** written to
`docs/architecture/CT-PO-P17-M-INDEPENDENT-VERIFICATION-CAPABILITY-TRUTH-SURFACE-20260926.md`,
untracked, uncommitted, unpushed. No application change accompanies it; the only
file written by this task is this report.
