# CT-P6-2F-FINAL-EVIDENCE-EXECUTION-20260911-017

**Prompt Ref:** `CT-P6-2F-FINAL-EVIDENCE-EXECUTION-20260911-017` · **Date/time:** 2026-09-11
**Mode:** EVIDENCE EXECUTION ONLY (no product remediation; implementation/fixtures frozen)
**Previous:** `CT-P6-2F-FINAL-EXECUTION-20260911-016` (verdict B)
**Branch:** `main` · **HEAD:** `16391217103b98dcea520070c5a22c68f12fe607`

## 1. Command executed (sequentially, to completion, observed)

```
cd /home/shomonrobie/carbon_tally
set -a; . tests/e2e/.env.personas; set +a
E2E_BASE_URL=http://localhost:3000 npx playwright test
```

Environment: isolated frontend `:3000`, API `:8051`, Supabase `:55325`, Postgres
`:55326`, real GoTrue JWTs; **no** production/demo/investor endpoint or credential.

Fixtures in force: `ITEM_A9` = `calculated` → `E2E_ITEM_A_ID`; `ITEM_A10` =
`consultant_reviewed` → `E2E_ITEM_A2_ID` (applied in 015, reasserted, unchanged here).

## 2. Complete, observed result

```
Running 16 tests using 2 workers
 ✓  1 consultant-lifecycle  consultant opens the deep-linked item workspace (14.8s)
 ✓  5,6,7,8,9,10,11 route-protection ×7 (unauthenticated redirects + sign-in surface)
 ✓ 12 security-denies  cross-firm consultant cannot open another firm client item
 ✓ 13 security-denies  organisation member cannot approve a customer decision
 ✓ 14 security-denies  unauthenticated API calls are rejected
 ✓ 15 security-denies  consultant cannot invoke the internal ops workspace route
 ✓ 16 security-denies  consultant cannot reach the admin control plane
 -  2 consultant-lifecycle  consultant submits reviewed work to CarbonTally QC
 -  3 consultant-lifecycle  consultant completes the review action on a calculated item
 -  4 consultant-lifecycle  the consultant's own notification deep link resolves to the item
 3 skipped / 13 passed (34.1s)     PW_EXIT=0
```

**16 total · 13 passed · 0 failed · 3 skipped · exit code 0 · 34.1 s.**

## 3. Assessment of the three skips

The three consultant-lifecycle ALLOW specs skip on a **visible-UI-control** guard
(`Pass review` / `Submit to CarbonTally QC` button visibility; an `/^open$/i`
notification link) — **not** on authorization: the same items return HTTP 200 from
`GET /api/v3/processing/items/{id}/workspace` as `consultant_a`, with the expected
statuses after the 015 fixture reassert. Every executable spec passed, including all
DENY, route-protection and IV-N6 deep-link specs. Per §4/§18 no fixture, harness or
product change was made to force them.

## 4. Outstanding evidence (exact)

1. The three consultant-lifecycle ALLOW specs (control-visibility gating).
2. D11 `accepted` — not executed this cycle.
3. D11 `qc_outcome` — not executed this cycle.
4. D11 `rework` — not executed this cycle.
5. `pytest backend/tests/unit backend/tests/e2e` — not completed; no counts claimed.
6. reset → reseed → acceptance → browser — not executed.

## 5. Preserved evidence (not reopened, not re-executed)

D6 approval (200, `ct_qc_approved → approved`, live usage write, safe replay, Org-A
entitlement ownership) · PE-A 200 with PE-B / cross-org / IDOR / unauthenticated /
alternate-route denials · RLS zero-row cross-tenant filtering · real-JWT
authentication · D7 provenance (`CARBONTALLY_INTERNAL` / `PROCESSING_ENTITY` only) ·
D8 existing conversation model · D11 `submitted_to_qc` + `customer_decision` ·
**D11-C1** firm-centric recipients. `run_acceptance.py` remains **16/16 PASS**.

## 6. File-modification policy

```
Application code changed: NO
Fixture logic changed:   NO
Schema changed:          NO
RLS changed:             NO
Roles/capabilities:      NO
Billing changed:         NO
Product behavior:        NO
```

Documentation only: §19 of
`docs/architecture/CARBONTALLY_P6_2F_E2E_ENVIRONMENT_IMPLEMENTATION_REPORT.md` and
this file.

## 7. Git

branch `main` · HEAD `16391217103b98dcea520070c5a22c68f12fe607` · staged **none** ·
commit **no** · push **no** · reset/clean **no** · unrelated pre-existing
modifications preserved.

## 8. Verdict

No material defect discovered; all executable acceptance specs pass; the evidence set
is incomplete for execution/tooling reasons only.

**P6-2F REMEDIATION PARTIALLY COMPLETE — EVIDENCE EXECUTION BLOCKED**

No independent verification was performed or claimed; P6-2F is **not** verified,
**not** closed, and Phase 6 is not complete.
