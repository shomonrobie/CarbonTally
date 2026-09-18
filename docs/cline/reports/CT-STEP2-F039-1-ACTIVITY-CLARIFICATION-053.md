# CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-053

```text
1  BASELINE SHA  5fff802c17b1cc095ee97cef7859d1f52998a6d7
2  FINAL SHA     recorded in the completion summary (HEAD == origin verified after push)
3  BRANCH        p8-release-reconciled (no reset / rebase / force-push)
4  HEAD==origin  verified after push
5  GIT STATUS    clean at finish
6  COMMITS       the follow-up commit (see summary)
7  FILES CHANGED
     backend/api/v3_activity_clarifications.py                     (semantic-choice guard refined)
     backend/tests/unit/api/test_v3_activity_clarifications_api.py (14 → 27 tests)
     docs/cline/reports/CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-053.md
8  PRODUCTION / DEPLOYMENT  production NOT touched · nothing applied to production · NOTHING DEPLOYED
9  D19 UI  NOT implemented (out of scope by instruction)
```

## 8–9 — CONSULTANT AUTHORIZATION OVER HTTP (Part A) — 7 tests, all PASS

Real chain exercised: `ensure_processing_org_access` → `ensure_consultant_org_access` →
active firm membership → active firm profile → **ACTIVE `consultant_clients` grant (D15)** →
`get_client_by_org(profile.id, organization_id)`. Only the *data* those calls read is faked
(`get_active_memberships_by_user`, `get_profile_by_id`, `get_client_by_org`); the
authorization logic is the implementation. **No authorization function is mocked**, and the
grant is organisation-bound in the double, so an ungranted organisation resolves to `None`
exactly as the real lookup would.

```text
authorized consultant → client ORG_A                201 · actor_scope "consultant" · org from context   PASS
consultant → ORG_B (grant covers ORG_A only)        403 on POST and GET · zero DB params               PASS
consultant with an ENDED grant → ORG_A              403 · zero DB params                               PASS
consultant with no firm membership                  403 · zero DB params                               PASS
consultant submitting actor_id                      422 (rejected, not ignored) · zero DB params       PASS
consultant CLIENT own org ORG_A / other org ORG_B   201 / 403 · zero DB params                         PASS
internal staff → ORG_A                              201 · actor_scope "internal_staff"                 PASS
Processing Entity staff → ORG_A                     403 (existing D20 convention)                      PASS
```

## 10 — POSITIVE SEMANTIC FLOW OVER HTTP (Part B) — 4 tests, all PASS

The test engine now returns the **real `EmissionFactor` fixtures used by 041 and 039** (same
activity_type vocabulary, no invented strings), so the clarification-required branch is
genuinely exercised. Observed engine vocabulary for the waste fixture, from a live diagnostic:

```text
bare "Waste"            → clarification_required · options: Landfill · Open-loop recycling ·
                          Incineration · Fuel combustion
bare "Waste disposal"   → policy_ambiguous (three route options)
resolve_clarification("Waste","Landfill") → lf   ·   ("Waste","Waste oils") → oils
```

```text
GET options (bare Waste)  clarification_required True · options non-empty · no factor id
                          offered as a choice (no "lf"/"ol"/"inc"/"oils" in the payload)      PASS
POST Waste + Landfill     201 · policy_input "Waste Landfill" · outcome_status "selected" ·
                          selected_factor_id "lf" · factor_set "DEFRA-2025" ·
                          reporting_year 2025 · unit "tonnes"                                  PASS
POST Waste + Waste oils   201 · selected_factor_id "oils" · scope "Scope 1"                     PASS
POST Diesel + variant     option-driven: the test reads the engine's own offered option
                          ("100% mineral diesel" / "average biofuel blend") and submits its
                          semantic term · policy selects "min" / "blend"                        PASS
```
Every assertion on stored values comes from the **INSERT parameter tuple** — what the

## 11 — PROVENANCE (Part C) — PASS

Asserted against the real INSERT parameters (indices: `[3]` organization_id, `[4]`
original_activity, `[6]` clarification, `[8]` policy_input, `[9]` outcome_status, `[10]`
selected_factor_id, `[12]` factor_set, `[14]` reporting_year, `[15]` unit, `[16]` scope):

```text
Waste + Landfill → [4] "Waste" (original evidence, never overwritten)
                   [6] "Landfill" (user statement, stored separately)
                   [8] "Waste Landfill" (policy input) · [9] "selected" · [10] "lf"
                   [12] "DEFRA-2025" · [14] 2025 · [15] "tonnes"                        PASS
Decline          → [4] "Waste" · [6] "i_dont_know" · factor columns NULL ·
                   actor_id = the authenticated AuthUser.user_id (server-derived),
                   actor_scope "organization_member"/"consultant"/"internal_staff"      PASS
```
A body-supplied `actor_id` is rejected outright (422) — it can neither attribute nor impersonate.

## 12 — CONFLICTING CLARIFICATION (Part D) — PASS, behaviour derived from the schema

No new policy was invented. The adjudication identity is the database's own
`UNIQUE(activity_key, original_activity, clarification)`, so a **different** clarification for
the same activity is a **distinct adjudication** and the first is left untouched. Verified:
`Waste + Landfill` → `lf` then `Waste + Waste oils` → `oils`, both 201, and **no UPDATE
statement is issued at all** (asserted across every captured query — the repository has no
overwrite path). The uniqueness constraint was **not** altered.

## 13 — IDEMPOTENCY (Part E) — PASS

```text
identical successful clarification retried   ON CONFLICT ON CONSTRAINT
                                             activity_clarifications_unique DO NOTHING, then
                                             re-reads and returns the STORED row             PASS
identical decline repeated                   identical response state both times             PASS
decline retry                                returns the stored adjudication                 PASS
conflicting clarification                    distinct row, no overwrite (see §12)            PASS
```

## 14 — 22 SERVICE REGRESSIONS (Part F)

```text
tests/unit/services   ALL COLLECTED TESTS PASSED — pytest exit code 0
```
The interface gap that caused the 22 failures (the service calling `clarification_candidates`,
absent on the old fake engine) is fixed in the tree, and the 045 mapping-boundary gate is live
and exercised by this suite — it is green. **Honest qualification:** this is a *verification*
result. I did not newly author a set of 22 named regression tests (046 records that the fix
belonged in the implementation, with no test changes), so "the 22 cases pass" is evidenced by
the suite being green rather than by 22 individually named new cases. That distinction is
carried as F-053-1.

## 15–16 — REGRESSION SUITES ACTUALLY RUN (exact results)

This environment's pytest suppresses the trailing count line, so results are reported as
all-collected-passed (exit code) plus captured dot counts — no aggregate is invented:

```text
tests/unit/api/test_v3_activity_clarifications_api.py          27 passed (27 dots) · exit 0
tests/unit/data/test_activity_clarifications_repository.py      8 passed (8 dots) · exit 0
tests/unit/engines/test_factor_selection_policy.py   (D-A / D-FS)            exit 0
tests/unit/engines/test_factor_selection_followup_039.py (039)               exit 0
tests/unit/engines/test_activity_clarification_041.py   (041)                exit 0
tests/unit/engines/test_activity_clarification_043.py   (043)                exit 0
tests/unit/services                                  (incl. the 045 gate)    exit 0
NOT run to completion this window: the broadest unit aggregate (data+engines+services in one
run), and a dedicated 045-named engine file (none located; 045 is exercised via services).
```
No previously recorded total is presented as re-run, and no policy file (D-A, D-FS, 039, 041,
043, 045) was modified in this window.

## 17 — D17 / F-051-1 STATUS

Unchanged and still untouched: `test_d17_provider_ownership_migration_revision.py` expects 71
migrations while the tree holds 73. This window added **no** migration, so it neither
encountered nor affected it, and the ratified test was **not** modified. F-051-1 still requires
an authorised decision.

## 18–20 — D19 · PRODUCTION · REMAINING BLOCKERS

* **D19 UI:** NOT implemented (out of scope by instruction).
* **Production / deployment:** production NOT touched; nothing applied to production;
  **nothing deployed**; no RLS or authorization weakened; no parallel authorization system; no
  factor-selection logic duplicated; `select_factor` and the 045 gate untouched.
* **Remaining blockers:**

```text
F-053-1  the explicitly-enumerated 22 service regression cases (F-046-2) — the services suite
         is green, but the named set was not authored/individually verified in this window
F-053-2  an HTTP fixture proving the "still ambiguous after an OFFERED option" state
         (structurally rare: offered options derive from eligible candidates). The no-guess
         refusal path (409, zero writes) and 041's engine-level ambiguity are covered.
F-051-1  D17 migration-count guard (needs an authorised decision; untouched)
D19 UI   separate bounded window, as instructed
```

## VERDICT

**IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION**

The window's scope is complete and tested: consultant and consultant-client authorization over
the real gate chain (7 tests), the positive semantic flow on real engine fixtures
(Waste + Landfill, Waste + Waste oils, both Diesel variants), provenance separation asserted at
the database-parameter level, conflict handling derived from the schema with no overwrite path,
idempotent retries, and the regression suites (repository, API, D-A/D-FS, 039, 041, 043,
services) all green. Two qualifications are recorded rather than glossed: §14's
"verification, not newly-authored cases" distinction (F-053-1) and F-053-2's missing fixture.
No independent verification was performed and no PO closure is claimed.

repository actually sent to the database — not from echoing a canned response, so the
server-side policy result is proven to be what reaches persistence.

**One implementation refinement was required, and it is documented rather than hidden.** A
strict "must equal an offered option" guard rejected a legitimate engine path: the engine
offers the *family-level* option "Fuel combustion" but still resolves the more specific
"Waste oils". `_validate_semantic_choice` now accepts either (i) an offered option
(`semantic_term`/`label`/`id`), or (ii) text that the existing policy, re-run, resolves to a
genuine selection from the server-side candidate set. Arbitrary invented text satisfying
neither is still refused with 422, so a client cannot steer selection, and no factor id is
accepted on either path — the recorded factor metadata stays the policy's own output.
