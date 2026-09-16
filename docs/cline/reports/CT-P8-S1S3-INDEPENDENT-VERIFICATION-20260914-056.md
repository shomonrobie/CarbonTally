# CT-P8 — S1/S3 INDEPENDENT VERIFICATION — REPORT

**Task:** `CT-P8-S1S3-INDEPENDENT-VERIFICATION-20260913-030`
**Programme:** CarbonTally Phase 8 / Phase 8-X — `CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260913-050`
**Date:** 2026-09-14
**Report id:** `CT-P8-S1S3-INDEPENDENT-VERIFICATION-20260914-056`
**Subject:** Phase 8 **S1** (report-version correctness — `is_current`) and **S3**
(report-version lifecycle state), reported as *"implemented — independent
verification not evidenced"*.
**Verdict:** **PASS — independently verified on a disposable clone.** Finding
**F-049-6** is **DISCHARGED**. Two non-blocking observations recorded (§7).

---

## 1. Why this task was executable now (and what was not)

The master playbook recorded `…030` as *"done | none | n/a | **Verification
authorisation** (no PO decision prerequisite)"* (`…049` §"gate ledger", §F-049-6).
Its only gate was **authorisation**, not a product/security decision.

Under the blanket authorisation `…050` — *"do NOT stop merely because an
individual task lacks a separate authorisation artefact"* — an authorisation-only
gate is **satisfied**, so `…030` is **type A (already authorised and
executable)** and was executed.

The same test was applied to the adjacent RLS item and produced the **opposite**
result, which is why RLS-4A-2 was **not** touched:

| Item | Gate nature | Authoritative record | Classification |
|---|---|---|---|
| `…030` S1/S3 IV | authorisation only | *"no PO decision prerequisite"*; needs only a verification authorisation | **A — executed** |
| **RLS-4A-2** (authenticated grant hardening) | **security-control authorisation** | register: *"Status: **NOT AUTHORIZED — NOT IMPLEMENTED**"* + *"Each group is a **separately authorized** change with its own verification gate. **No batched release.**"* | **C — true decision required (§8)** |

A register-designated, *separately authorised* **security** change whose status
field states **NOT AUTHORIZED** is a genuine governance gate, not a missing
paperwork artefact. Inferring authorisation for it would have been inventing a
security decision (AGENTS §62, §67).

---

## 2. Normative contract used (verification baseline)

| Source | Used for |
|---|---|
| `CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` §7.3 | `is_current` must be a **derived, single-valued invariant**, enforced transactionally (G5) |
| …spec §12–§13, §13.1 | the state machine and transition invariants (T3/T7/T8/T11/T12; `FINAL` terminal) |
| …spec §14, §14.1, §18 | versioning semantics: supersession, approval bound to a version, non-inheritance |
| …spec §10.2, §11, §23.2/§23.3, §26.1 | immutability rules, version-scoped mutations, the guarded-transition requirement |
| `supabase/migrations/20260913000000_p8_report_lifecycle_status.sql` header | **ADDITIVE + IDEMPOTENT**; **NO RLS change**; **no other table/column/constraint/index/policy touched**; six ratified states |
| `CT-P8-CURRENT-STATE-RECOVERY-…023` §10.6, §11.1 | the verification asymmetry being discharged |
| `docs/cline/reports/CT-P8-REPORTING-S1-CORRECTNESS-20260912.md` | the S1 implementer's own claims |

The acceptance properties were derived from these sources **before** running
anything, and are asserted against the *system*, not against the implementer's
test names.

---

## 3. Environment and F-046-1 compliance

| Item | Value |
|---|---|
| Integration target | **disposable clone `ct_s13_iv_20260914`** (created for this task) |
| Target verification | `SELECT current_database()` → `ct_s13_iv_20260914` **before any destructive statement** |
| Protected markers | name contains none of `qa` / `demo` / `investor` / `prod` / `live` |
| Destructive-setup check | `tests/integration/conftest.py` performs `TRUNCATE … RESTART IDENTITY CASCADE`; the code-enforced refusal guard was **active** and did not fire (correct target) |
| Clone provenance | `pg_dump --schema-only` of `carbontally_qa_phase8` (authoritative lineage) — schema, RLS policies and ACLs, **no data rows** |
| Persistent QA | **read-only** (`SELECT` only) — no writes, no truncation |
| Production | **untouched — not connected to at any point** |
| Standalone unit probes | in-memory world, **no database access** |

**F-046-1 is restated here as a programme invariant** and is carried forward to
all subsequent reports: *the integration harness performs destructive setup and
must only ever be pointed at a disposable `ct_*` clone or the dedicated test
database.*

---

## 4. Method — why this is independent, not a re-run

The implementer's suites (`test_report_versions.py`, `test_report_lifecycle.py`,
`test_v3_report_lifecycle.py`) were executed as the **regression baseline**, and
then deliberately **extended by probes they do not contain**. Every IV probe
asserts a ratified property that previously had **no direct evidence**:

| # | IV probe | Ratified property (source) | Previously tested? |
|---|---|---|---|
| IV-S1-1 | demotion **and** insert are one transaction | §7.3 "transactionally enforced" | **no** |
| IV-S1-2 | duplicates unreachable at the **DB** layer too | §7.3 single-valued invariant | **no** |
| IV-S1-3 | §7.3 legacy two-current-rows case: single/batch reads agree | §7.3 (E12/E13) | **no** |
| IV-S1-4 | `next_version_number` = `MAX+1`, gaps kept, `is_current`-independent | §14.1 | partly |
| IV-S1-5 | invariant scoped per report instance | §7.3 | **no** |
| IV-S3-5 | the **column** default is `DRAFT` (migration, not Python) | §12.3 | **no** |
| IV-S3-6 | the CHECK admits **exactly** the six ratified states | migration header; §12.2 | partly |
| IV-S3-7 | `status` is `NOT NULL` | §26.1 guard correctness | **no** |
| IV-S3-A1 | supersession creates a new DRAFT; approval never inherited/mutated | §14.1, §18 | **no** |
| IV-S3-A2 | supersession refused from `DRAFT`; writes nothing | §23.2 | **no** |
| IV-S3-A3 | Processing Entity staff have no lifecycle authority | §10.2 | **no** |
| IV-S3-A4 | 403/409 ⇒ no state change and **no audit event** | §26.1 | partly |
| IV-S3-A5 | `APPROVED` cannot be skipped | §13 | **no** |
| IV-S3-A6 | `FINAL` terminal for **every** action | §13 | partly |
| IV-S3-A7 | history readable after supersession | §14 | **no** |
| IV-MIG-1 | migration is **additive** (delta = exactly 3 objects) | migration header | **no** |
| IV-MIG-2 | migration re-applies as a **no-op** | migration header | **no** |
| IV-MIG-3 | migration changes **no RLS** (flags/policies/ACLs byte-identical) | migration header | **no** |

IV-S1-1 is the strongest of these: it forces the `INSERT` inside `create()` to
fail on the `(report_id, version_number)` natural key **after** the demotion has
run, and asserts the demotion was rolled back. A separately-committed demotion
would have left the report with **zero** current versions — the exact defect S1
exists to prevent. It passes, which proves the demotion and insert share one
transaction (verified against the implementation: `async with conn.transaction():`
wrapping both statements).

---

## 5. Results

### 5.1 Regression baseline (unchanged suites, disposable clone)

| Suite | Result |
|---|---|
| `tests/integration/test_report_versions.py` (S1) + `test_report_lifecycle.py` (S3) | **12 passed** |
| `tests/unit/api/test_v3_reports.py` + `test_v3_report_lifecycle.py` | **78 passed** |

### 5.2 Independent probes

| Suite | Result |
|---|---|
| `tests/integration/test_s1s3_iv_invariants.py` (IV-S1-1…5, IV-S3-5…7) | **8 passed** |
| `tests/unit/api/test_s1s3_iv_supersession.py` (IV-S3-A1…A7) | **7 passed** |
| Combined S1/S3 + IV integration re-run after the migration-DDL probe | **20 passed** |
| Combined S1/S3 + IV unit re-run | **85 passed** |

### 5.3 Migration probes (structural, on the disposable clone)

Fingerprint = **3,423** public-schema objects (columns, constraints, indexes, RLS
flags, policies, ACLs, column comments), sorted.

| Probe | Evidence | Result |
|---|---|---|
| **IV-MIG-1** additive | `pre-S3 → post-migration` delta = **exactly 3 lines**: the `status` column (`varchar`, `NOT NULL`, default `'DRAFT'`), `report_versions_status_check`, and the column comment. **No other table, column, constraint, index, policy or ACL appears or changes.** | **PASS** |
| **IV-MIG-2** idempotent | apply #1 `rc=0`, apply #2 `rc=0`; second-apply delta = **empty** | **PASS** |
| **IV-MIG-3** no RLS change | `rls` flags + **all 197** public policies + all ACLs **identical** pre vs post | **PASS** |
| Restore fidelity | after re-application the clone is semantically identical to its pre-probe state; the single textual difference is Postgres normalising the re-created CHECK expression (`ARRAY[…]` vs `((…)::text = ANY(…))`) — the same six values | expected |


---

## 6. Security verification (independent, read-only on persistent QA)

| Check | Evidence | Result |
|---|---|---|
| `anon` cannot read report versions | `has_table_privilege('anon','public.report_versions','SELECT')` = **false**; `INSERT` = **false** | **PASS** |
| Client-side bypass of the guarded transition | `report_versions` has RLS **enabled** with **0 policies** ⇒ default-deny for `anon`/`authenticated`; every read/write must pass the server-authorised API or the backend service role | **no client bypass exists** |
| S1/S3 invariants hold against a writer that bypasses the repository | IV-S1-2 (`UniqueViolation`) | **PASS** |
| Authorisation is server-side, not UI-side | IV-S3-A3/A4 (403 with no state change, no audit event) | **PASS** |
| Approval is version-bound and not inherited | IV-S3-A1 (approval audit entry still references `v1.id`; `v2` is `DRAFT`) | **PASS** |
| No new `anon` exposure introduced | `anon`-exposed relations in `public` = **1** (`emission_factors`, which is `D-4`-gated) — unchanged | **PASS** |
| S1/S2/S3 artefacts present on the authoritative lineage | `status` column present; `report_versions_one_current_per_report` index present | **PASS** |

### 6.1 No-bypass argument (why S1/S3 correctness is not merely an app-layer promise)

The single-current invariant is enforced **twice** — transactionally in the
repository **and** by the S2 partial unique index — and the lifecycle state is
closed by a database CHECK constraint. Because the table is deny-all for browser
clients, the only paths to it are the guarded API and the privileged backend, so
neither a client nor a careless server-side write can produce two current
versions or an unratified state.

---

## 7. Findings

### 7.1 `F-049-6` — S1/S3 lacked independent verification → **DISCHARGED (PASS)**

`…049` §F recorded: *"S1/S3 are implemented but have **no independent
verification**, and no verification task is currently authorised"* (Medium,
verification gap). This report supplies that verification: 15 independent probes
(8 integration + 7 API) plus 3 structural migration probes, all passing, with the
implementer's suites re-run green as a regression baseline. The evidence gap in
`-023` §10.6/§11.1 is closed.

### 7.2 `IV-OBS-1` — three legacy S1 tests leak rows (test hygiene, **Low**, no product impact)

`test_next_version_number_starts_at_one`, `test_create_and_roundtrip_version` and
`test_version_numbers_increment` create `report_versions` rows and have **no
cleanup**, unlike the later tests in the same file (which use
`_cleanup_report`). Measured post-run: `leaked_versions=3` on the clone.

* **Impact:** none on product behaviour or on the persistent environment — the
  session fixture `TRUNCATE`s its target at the start of every suite run, and the
  clone is disposable. It only violates the suite's own *"clean up only what you
  created"* standard.
* **Disposition:** recorded, **not** fixed here, because the IV pass must not
  modify the artefact it is verifying; recommended as a trivial follow-up batch.

### 7.3 `IV-OBS-2` — `authenticated` retains blanket table grants (**Low**, gated by `RLS-4A-2`)

On persistent QA, `has_table_privilege('authenticated','public.report_versions','TRUNCATE')`
= **true** (blanket grants exist) while RLS denies every row. The grant is
therefore **inert today**, but it is a least-privilege gap and it is **exactly the
declared scope of RLS-4A-2** (*"reduce `authenticated` from `ALL` to
`SELECT,INSERT,UPDATE,DELETE`"*). Recorded as evidence supporting that gated
decision; **not** remediated (see §8).

---

## 8. Decision required (recorded, not invented)

**TRUE PO / SECURITY AUTHORISATION REQUIRED — `RLS-4A-2` (Authenticated Grant Hardening).**

> Authorise RLS-4A-2: `REVOKE TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public FROM authenticated`
> (QA/non-production only, `REVOKE`-only, with its own verification gate), so that
> `authenticated` holds exactly `SELECT,INSERT,UPDATE,DELETE`, matching the 8 tables
> that already follow the explicit-grant convention.

Basis: the remediation register states the scope and requires **separate
authorisation per group** ("No batched release") and its status field reads
**NOT AUTHORIZED — NOT IMPLEMENTED**. The blanket authorisation covers *old
authorisation artefacts*, not an un-taken security decision. `IV-OBS-2` above is
the concrete evidence that the gap still exists. Steps 3–5 of the RLS sequence
remain gated on `D-4`…`D-10`, `D-12` for the same reason.


---

## 9. Verdict

**S1 — INDEPENDENTLY VERIFIED (PASS).** The single-current-version invariant is
transactional, enforced at the database layer as well, correctly scoped per
report, resolvable identically through both read paths, and unaffected by
version-number gaps.

**S3 — INDEPENDENTLY VERIFIED (PASS).** The six-state vocabulary is closed and
case-exact at both the declared-definition and runtime level; the column default
is `DRAFT` in the database itself; state is `NOT NULL` and version-scoped; the
guarded transition never clobbers an unobserved state; `FINAL` is terminal;
approval is version-bound, non-inherited and never granted to a Processing
Entity; denied and invalid transitions change nothing and emit no audit event.
The `20260913000000` migration is **additive** (3 objects), **idempotent**
(`rc=0` ×2) and changes **no RLS** (flags, policies and ACLs byte-identical).

**Acceptance status:** *implemented + tested + **independently verified***.
This is a verification verdict for S1/S3 only; it is **not** a Phase 8 programme
acceptance, and it asserts nothing about S4–S8 or the B-series.

---

## 10. Limitations and remaining unknowns

* The S1/S3 **UI** surfaces are out of scope of this task (they belong to S6,
  which is unallocated — see the final programme report).
* No browser/E2E pass was run; this is a repository/API/database-level
  verification.
* IV-S1-3 must drop the S2 index to *represent* a pre-S2 row set; it restores the
  index in `finally` and asserts restoration. Post-run confirmation:
  `to_regclass('public.report_versions_one_current_per_report')` is present.
* The clone is disposable test infrastructure, not a deployment target; no
  conclusion is drawn here about any deployed environment.

---

## 11. Artefacts and Git state

**Added (verification artefacts — no product code changed):**

* `backend/tests/integration/test_s1s3_iv_invariants.py` (382 lines, 8 probes)
* `backend/tests/unit/api/test_s1s3_iv_supersession.py` (235 lines, 7 probes)
* this report

**Changed:** **none** of `backend/data/report_versions.py`,
`backend/api/v3_reports.py`, `backend/domain/report_lifecycle.py` or the
`20260913000000` migration — the verified artefacts were not modified.

**Databases:** disposable clone `ct_s13_iv_20260914` created for this task;
persistent QA read-only; production untouched.

**F-046-1:** enforced (code) and restated (report). **Phase 9:** no Phase 9 work
performed; Phase 8-X remains inside Phase 8.

