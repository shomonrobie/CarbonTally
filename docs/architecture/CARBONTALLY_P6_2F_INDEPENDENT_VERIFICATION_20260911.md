# CarbonTally — P6-2F Independent Verification Report

**Prompt Ref:** `CT-P6-2F-IV-20260911-001`
**Response Ref:** `CT-P6-2F-IV-20260911-001-R1`
**Datetime:** 2026-09-11
**Verifies:** `CT-P6-2F-RESUME-20260911-001` (P6-2F implementation, final Phase 6 gate)
**Implementation HEAD:** `daad396523ac693352cc2f4ebb7fc58814a9e60b` (unchanged before and after)
**Role:** independent verification agent — **verification-only**; no implementation, test, schema,
RLS, seed-logic, frontend or backend change was made.
**Final verdict:** **`P6-2F VERIFIED — PASS WITH NON-BLOCKING FINDINGS`**

---

## 1. Independence statement

This verification was performed in a **fresh context** with its own instruments. Nothing below is
taken from the implementation agent's report: every result was re-derived by the verifier by driving
the real isolated services. The verifier did **not** import repository test assertions or the
implementation under test to produce evidence (the single exception is documented in §7 — the LT-1
SQL probe, where the *shipped statement text* is extracted from the repository at runtime precisely so
that the artefact under test is what is executed, and the statements are executed directly against
PostgreSQL, not through the repository or a fake).

## 2. Verification environment

| Item | Value |
|---|---|
| Isolated Supabase / GoTrue | `http://127.0.0.1:55325` (project `carbontally_e2e`) |
| Isolated PostgreSQL | `127.0.0.1:55326` |
| Backend | `uvicorn main:app --host 127.0.0.1 --port 8051` (662 routes), env exported per-process from `.env.e2e` |
| Frontend | CRA dev server `http://localhost:3000`, `REACT_APP_*` → `:55325` / `:8051` |
| Authentication | real GoTrue password grants for 8 personas (org A owner/member, org B owner, consultant A/B, PE A/B manager, internal QC) |
| Reset used | `e2e/environment/scripts/reset.sh` (isolated project only) → `APPLIED=27 SKIPPED=26 ALL_APPLIED`; then `seed_e2e.py` (`SEED OK`, 0 errors) + `seed_lifecycle_fixtures.py` |
| Production / demo / investor | **not contacted** (`backend/.env` never sourced; no production host appears in the served bundle) |

## 3. Independent instruments (written for this verification, `/tmp`, not committed)

| Instrument | Purpose |
|---|---|
| `/tmp/iv_p6_2f.py` | Authorization matrix (A), RLS boundary (B), workflow-state enforcement (C), D11 lifecycle events (D). Own assertions, real JWTs, direct API + PostgREST calls, evidence read from persisted rows. |
| `/tmp/iv_chain_probe.py` | Walks the full item chain capturing **status + response body** at each step (used to root-cause a 409). |
| `/tmp/iv_lt1_sql.py` | Extracts the **shipped** SQL from `backend/data/consultants.py` at runtime and executes it — and a cast-removed variant — against real PostgreSQL, each probe inside a rolled-back transaction. |

## 4. API results — authorization matrix (section A: 25/25 PASS)

| Case | Identity | Observed | Expected |
|---|---|---|---|
| org A reads its own organisation | org_a_owner | **200** | 200 |
| org B reads org A organisation | org_b_owner | **403** | 403/404 |
| org A reads org B organisation | org_a_owner | **403** | 403/404 |
| org A owner opens its own item workspace | org_a_owner | **200** | 200 |
| org B owner opens an org-A item workspace | org_b_owner | **403** | 403/404 |
| consultant A `me` | consultant_a | **200** | 200 |
| consultant A reads its entitled client's items | consultant_a | **200** | 200 |
| consultant B reads firm-A client items | consultant_b | **403** | 403/404 |
| consultant B → firm-A item workspace (IDOR) | consultant_b | **403** | 403/404 |
| consultant A → internal ops QC queue | consultant_a | **403** | 403 |
| consultant A → admin control plane API (`/api/v3/admin/review-queue`) | consultant_a | **403** | 403 |
| consultant A → customer decision | consultant_a | **403** | 403 |
| consultant A → CarbonTally QC decision | consultant_a | **403** | 403 |
| consultant A → customer engagement acceptance | consultant_a | **403** | 403 |
| org member → customer decision | org_a_member | **403** | 403 |
| org A owner → internal ops queue | org_a_owner | **403** | 403 |
| PE A `me` / PE A work list | pe_a_manager | **200 / 200** | 200 |
| PE B → PE-A item workspace | pe_b_manager | **403** | 403/404 |
| PE A → internal ops queue | pe_a_manager | **403** | 403 |
| internal QC → ops QC queue | internal_qc | **200** | 200 |
| internal QC → admin control plane API (staff-admin only) | internal_qc | **403** | 403 |
| anon → notifications / item workspace / admin API | anon | **401 / 401 / 401** | 401/403 |

A guard check also asserts the PE personas authenticated successfully, so the PE DENY cases are
**discriminating** (403 ≠ 401) rather than passing for the wrong reason.

**RLS boundary (section B: 4/4 PASS)** — PostgREST with real user JWTs, never service-role: org A
reads its own row (200); org A reading org B returns **no row** (no cross-tenant leak); org B reading
org A returns no row; anon is refused (401).

## 5. Workflow-state enforcement (section C: 13/13 PASS)

**Invalid transitions are refused server-side** (all four rejected; one 403 rather than 409 — see the
note):

| Attempt | Result |
|---|---|
| consultant review of a `reviewed` item | **409** |
| consultant submit of a `calculated` item | **409** |
| CarbonTally QC decision on a `consultant_reviewed` item | **409** |
| customer decision from a non-approvable state (`calculated`) | **403** — refused by the P6-2C automatic-only guard, which runs before the state machine; the request was genuinely refused |
| cross-organisation engagement acceptance (org A owner → org B's engagement) | **403** |

**The full valid chain was driven through the real endpoints** (`/tmp/iv_chain_probe.py` + probe C2),
each step returning 200 and reaching the expected state:

```text
calculated --consultant-review--> consultant_reviewed --consultant-submit--> reviewed
        --internal QC approve--> ct_qc_approved --org owner customer-review--> approved
```

**Replay behaviour:** a repeated QC decision → **409**; a re-submit of a non-submittable item → **409**;
a repeated customer decision → **409** — each with **no additional notification row** (asserted).

## 6. D11 lifecycle results (section D: 52/52 PASS)

| Event | Trigger (real endpoint, real JWT) | Entity result | Notification evidence |
|---|---|---|---|
| `accepted` | org-B owner accepts the pending engagement | `pending` → **`active`** (HTTP 200) | `consultant.lifecycle.accepted:engagement:<id>`; one row per active firm member; recipients = server-derived firm membership; the accepting organisation is **not** a recipient; `actor_domain=organisation_member`; link `/consultant` |
| `submitted_to_qc` | consultant submit | `consultant_reviewed` → `reviewed` | key `…submitted_to_qc:item:<id>`; firm recipients get the **item deep link**; the internal-ops recipient gets the `/notifications` fallback; `actor_domain=consultant` |
| `qc_outcome` approved | internal QC approve | → `ct_qc_approved` | key `…qc_outcome:item:<id>:approved`; firm recipients; `actor_domain=internal_staff`; item deep link |
| `qc_outcome` rejected | internal QC reject | → `ct_qc_rejected` | key `…:rejected`; same guarantees |
| `customer_decision` | org owner approves | `ct_qc_approved` → `approved` | key `…customer_decision:item:<id>:approved`; firm recipients; `actor_domain=organisation_member`; item deep link |
| `rework` | (same rejection, source `ct_qc_rejected`) | — | key `…rework:item:<id>:ct_qc_rejected`; firm recipients; item deep link |

Verified for each: **durability** (independent second read — all six keys still present), **correct type**
and **association** (the key carries the entity id), **no duplicate on replay**, **invalid actor cannot
create the event** (consultant QC decision 403 / org member customer decision 403, each with **zero** new
rows), and **invalid state cannot create the event** (409 paths above).

## 7. LT-1 verification — the real-SQL defect (**VERIFIED FIXED**)

Method: the shipped statements are extracted from `backend/data/consultants.py` at runtime and executed
against real PostgreSQL; a variant with the explicit cast removed is executed for comparison. Every probe
runs in a transaction that is rolled back, so nothing is persisted.

```text
shipped SQL contains the explicit cast: True / True

consultant_clients.transition_client_lifecycle (shipped):
  active / pending / rejected / suspended / ended / inactive   -> OK (every target)
consultant_clients.transition_client_lifecycle (cast removed):
  active -> AmbiguousParameterError: inconsistent types deduced for parameter $2
consultant_tasks.update_task_status (shipped):       completed -> OK
consultant_tasks.update_task_status (cast removed):  completed -> AmbiguousParameterError: ...
```

Conclusion: the pre-fix form fails **for exactly the claimed reason**, and the shipped form executes for
every target status — so the fix is the cause of the working behaviour, not a coincidence. Confirmed
end-to-end as well: the customer acceptance endpoint returns **200** (not 500) and produces the durable
`accepted` event, the `pending → active` transition, and a 409 on replay. **A fake-repository test was
not accepted as evidence for this item.**

## 8. LT-2 classification — **CONFIRMED P3 (non-blocking, test-infrastructure/evidence gap)**

Independently observed: the dedicated integration database `carbontally_test` (port 54426, separate
database — not the demo app database, not production) has **no** `can_extract` column on
`consultant_profiles` (count 0) and **neither** `can_extract` nor `can_submit` on
`consultant_firm_members` (count 0). Running the dedicated suite reproduces the effect:

```text
pytest tests/integration/test_consultants.py  ->  4 failed
  asyncpg.exceptions.UndefinedColumnError: column "can_extract" does not exist
  (fails inside create_profile, before any lifecycle statement is reached)
```

**Why it does not block P6-2F:** the gate's evidence is produced against the **isolated project**, whose
schema is current (the reset re-applies all migrations) — so no required P6-2F acceptance evidence depends
on `carbontally_test`. **Why it matters:** this stale-schema gap is precisely why the LT-1 SQL defect
escaped automated coverage (unit tests use a fake repository; the only real-DB suite cannot run).
**Owner:** test-infrastructure / environment work (not P6-2F product scope). **Blocks first customer:** no.

## 9. Browser E2E results (independently executed)

| Environment state | Result |
|---|---|
| Pristine: `reset.sh` → `seed_e2e.py` → `seed_lifecycle_fixtures.py` (documented order), then `npx playwright test` | **16 passed / 0 failed / 0 skipped** (exit 0) |
| After an engagement-level `accepted` notification became the newest consultant notification (created by this verifier's own probe), same suite | **15 passed / 1 failed / 0 skipped** |

**The three previously-skipped specs are genuine passes**, not weakened assertions:
`consultant submits reviewed work to CarbonTally QC`, `consultant completes the review action on a
calculated item`, and `the consultant's own notification deep link resolves to the item` all execute
their real flows and assert their outcomes. Cross-checked against the harness diff: the only change is
that the guards now *wait* for the SPA's `Checking access…` gate to clear before probing, and the DENY
specs were deliberately left untouched (for them the *absence* of content is the security assertion) —
so the waits cannot mask an authorization failure. The authorization outcome itself is separately
asserted at the API layer in §4 (consultant B 403, org B 403, consultant → ops 403, member 403, anon
401) and by spec 1, which requires the scope-aware workspace route to return content.

**The single failure is a P3 harness fragility, not a product defect** (finding `V1`). Root cause,
evidenced: the spec clicks the **first** `Open` notification and expects the item workspace. In the
failing state the newest consultant notification was the engagement-level `accepted` event, whose link is
`/consultant` — a **valid route**, but not an item deep link (that event has no item context by design):

```text
11:05:24 | consultant.lifecycle.accepted        | /consultant                       <- clicked first
11:05:24 | consultant.lifecycle.rework          | /consultant/items/<client>/<item>
11:05:24 | consultant.lifecycle.qc_outcome      | /consultant/items/<client>/<item>
11:05:24 | consultant.lifecycle.submitted_to_qc | /consultant/items/<client>/<item>
```

Independent confirmation that the *underlying requirement* holds: every item-scoped event's firm
recipient carries `/consultant/items/<client>/<item>` (asserted in §6), and the same spec passes on the
pristine fixture state (16/16 above). The spec's assumption is therefore **notification-order dependent**.

## 10. Security review of the P6-2F change set

Inspected changes: `backend/data/consultants.py` (the LT-1 cast), `tests/e2e/personas.ts` +
`tests/e2e/carbontally/consultant-lifecycle.spec.ts` (waits), `e2e/environment/scripts/seed_lifecycle_fixtures.py`
(pending-engagement fixture), `e2e/environment/scripts/verify_lifecycle_events.py` (new evidence script).

| Concern | Assessment |
|---|---|
| Cross-tenant access | **None found** — org A/B isolation 200/403; RLS returns no cross-tenant row; org B cannot open an org-A item |
| Privilege escalation | **None found** — consultant and PE are refused internal ops (403), the admin control plane (403 API, no admin heading in the browser), customer approval (403) and QC decisions (403); docstring/behaviour for `transition_client_lifecycle` are unchanged by the cast (cast is type-only) |
| Client-side-only authorization | **No** — every DENY above is a server response; the browser merely coexists with it |
| Workflow bypass | **No** — invalid transitions refused; each valid step requires the correct persona |
| Replay / duplicate events | **No** — deterministic event keys plus DB uniqueness; replays 409/403 with zero new rows (asserted, not assumed) |
| Unauthorized approval / QC | **No** — 403 for consultant and for org members; only the org owner/admin approves |
| Internal-operation / admin-plane access | **No** — consultant 403, PE 403, owner 403, internal QC 403 on the admin API (staff-admin is a distinct role) |
| Consultant-firm isolation | **No** — consultant B 403 on firm-A client items and items; notifications are firm-scoped and server-derived |
| Organisation isolation | **No** — as above, plus RLS zero-row cross-tenant reads |

**No P0/P1 security finding remains.**

## 11. Regression results (exact; skips shown, not reinterpreted)

| Suite | Passed | Failed | Skipped | Errors | Exit |
|---|---|---|---|---|---|
| Independent probe `/tmp/iv_p6_2f.py` (A+B+C+D) | **95** | 0 | 0 | 0 | 0 |
| LT-1 SQL probe | shipped statements OK; cast-removed statements fail as claimed | — | — | — | 0 |
| Browser `npx playwright test` (pristine) | **16** | 0 | **0** | — | 0 |
| `pytest tests/unit` | **1,763** | 0 | 0 | 0 | 0 |
| `pytest tests/e2e` | **39** | 0 | 0 | 0 | 0 |
| `pytest tests/integration/test_consultants.py` | 0 | **4** (LT-2 stale test DB) | 0 | 0 | 1 |

Probe section totals: A 25, B 4, C1 5, C2 5, C3 3, D 43, D6 6, D7 2, D8 1, PE-auth guard 1 = **95**.

## 12. Files inspected

| File | Why |
|---|---|
| `docs/cline/prompt-history/CT-P6-2F-RESUME-20260911-001.md` | the implementation claims under verification |
| `docs/architecture/CARBONTALLY_P6_2F_E2E_ENVIRONMENT_IMPLEMENTATION_REPORT.md` (incl. the appended addendum §1–§10) | environment, D11 and LT-1 claims |
| `docs/architecture/CARBONTALLY_P6_2F_IMPLEMENTATION_REPORT.md`, `…_INDEPENDENT_VERIFICATION_REPORT.md` (earlier gate), `CARBONTALLY_CP2_CLOSURE_P6_2F_PREFLIGHT_REPORT.md` | P6-2F context and criteria |
| `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` (§9 Phase 6, §12/§13), `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`, `CARBONTALLY_PRODUCTION_BACKUP_RESTORE_ROADMAP_V1.0.md` | phase scope; the parked backup/DR boundary (reference only) |
| `backend/data/consultants.py` | the LT-1 fix (`transition_client_lifecycle`, `update_task_status`) |
| `backend/services/consultant_lifecycle.py` | D11 event keys, recipient rules, link resolution |
| `backend/api/v3_processing_workflow.py` (consultant review/submit, customer review, workspace), `backend/api/v3_operations.py` (QC decision), `backend/api/v3_organizations.py` (engagement accept) | the probed endpoints and their state/authorization guards |
| `backend/domain/partners.py` (`can_transition_consultant_engagement`) | the ratified customer-only `pending → active` rule |
| `tests/e2e/personas.ts`, `tests/e2e/carbontally/consultant-lifecycle.spec.ts` (diff), `playwright.config.ts`, `tests/e2e/README.md` | the F4 change and the browser harness contract |
| `e2e/environment/scripts/{seed_e2e.py,seed_lifecycle_fixtures.py,verify_lifecycle_events.py,run_acceptance.py,reset.sh,README.md}`, `e2e/environment/.gitignore` | fixture/environment mechanics |
| `backend/tests/integration/{conftest.py,test_consultants.py}`, `backend/tests/unit/api/fakes.py` | LT-2 root cause (fake repository + stale integration DB) |

## 13. Findings

| ID | Severity | Finding | Rationale / disposition |
|---|---|---|---|
| **LT-1** | ~~P1~~ **CLOSED** | Customer engagement acceptance returned HTTP 500 (ambiguous `$2`), plus the same defect in `consultant_tasks` | **INDEPENDENTLY VERIFIED FIXED** (§7): shipped SQL executes for all targets; the cast-removed variant fails with exactly the claimed error; endpoint 200 / `pending → active` / durable event / replay 409 / consultant 403 |
| **LT-2** | **P3** | Dedicated integration DB (`carbontally_test`) schema is stale (`can_extract`, `can_submit` absent) → its consultant suite errors before reaching any statement, so real-SQL repository paths have no automated coverage | **CONFIRMED, not fixed** (verification-only + environment work). Non-blocking: the gate's evidence runs on the current isolated schema. Owner: test infrastructure. Blocks first customer: no |
| **V1** | **P3** | The browser deep-link spec assumes the **newest** consultant notification is item-scoped; it fails when the newest is the engagement-level `accepted` event (link `/consultant`, a valid route) | **Harness fragility, not a product defect** (§9). Pristine fixture state passes 16/16 and the item-deep-link requirement is asserted independently in §6. Owner: test infrastructure (select an item-scoped notification) |
| **V2** | **P3** | `seed_e2e.py` reports `SEED WITH_ERRORS` when re-run **without** a reset: the `organization_members` upsert returns `409 duplicate key (organization_id, user_id)` because it conflicts on `id` only | The row already exists, so data is correct and the suite is unaffected, but the summary is misleading and the row is not re-asserted. Owner: test infrastructure |
| **V3** | **P3** (observation, pre-existing) | The ALLOW specs use `test.skip(!visible)`, so an authorization *regression* that removed a control would surface as a **skip**, not a failure | Mitigated: the acceptance expectation is **0 skips** (a skip is visible), the DENY specs are independent, and §4 asserts the ALLOW/DENY matrix at the API layer. The F4 change did not introduce this (it only added waits) and weakened no assertion |

**No P0/P1 finding remains.** No functional or security defect was downgraded to reach this verdict.

## 14. Production safety

| Item | Status |
|---|---|
| Production contacted / modified | **NO** |
| Production credentials used | **NO** (isolated `.env.e2e` local-dev keys only; `backend/.env` never sourced) |
| Production migrations applied | **NO** — migrations 22 → 53 remain **NOT AUTHORIZED** |
| Production data created | **NO** |
| Backup / restore / DR work | **NOT PERFORMED** — parked; `DR-20` remains NOT SATISFIED |
| Deployment / push / commit | **NO** |
| Isolation check | the served dev bundle contains **no** production Supabase project ref; all mutation was against the isolated stack on `:55326` (the only other database touched was the dedicated `carbontally_test` integration DB on `:54426`, and only through its own documented suite) |

## 15. Git state

* **HEAD:** `daad396523ac693352cc2f4ebb7fc58814a9e60b` (unchanged)
* **Staged:** 0 · **Commit:** no · **Push:** no · working tree neither cleaned nor reset
* **Repository implementation modified by this verification: NO** — all five implementation checksums are
  byte-identical to the pre-verification baseline (`backend/data/consultants.py` `1ae1240a…`,
  `tests/e2e/personas.ts` `30ac1b67…`, `consultant-lifecycle.spec.ts` `5fa15c4d…`,
  `seed_lifecycle_fixtures.py` `6ef2dbaa…`, `verify_lifecycle_events.py` `8f6e5752…`)
* The only writes made by this verification are the two durable records named in §16; unrelated
  pre-existing working-tree changes were preserved untouched

## 16. Verdict

> ### **`P6-2F VERIFIED — PASS WITH NON-BLOCKING FINDINGS`**

All required P6-2F acceptance evidence was independently reproduced: the server-side authorization matrix
(organisation, consultant, processing entity, CarbonTally internal, unauthenticated), the RLS boundary,
workflow-state enforcement (the full valid chain to `approved`, plus refused invalid transitions), all six
D11 lifecycle events with durability / association / replay / invalid-actor / invalid-state guarantees,
the LT-1 real-SQL fix, and the browser suite at **16/16 with 0 skips** on the documented pristine
environment. No P0/P1 security finding remains and no cross-tenant authorization defect was found. The
three P3 findings (`LT-2`, `V1`, `V2`) and the pre-existing observation (`V3`) are harness/infrastructure
issues, each recorded with rationale, ownership and a "blocks first customer: no" assessment.

**P6-2F is independently verified and ready for Phase 6 closure.** Phase 7 requires a separate Product
Owner authorization after Phase 6 closure.

**DR-20 remains NOT SATISFIED · migrations 22 → 53 remain NOT AUTHORIZED · Phase 7 not started ·
Phase 8 not started.**
