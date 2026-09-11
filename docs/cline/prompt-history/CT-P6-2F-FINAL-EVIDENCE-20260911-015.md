# CT-P6-2F-FINAL-EVIDENCE-20260911-015

**Prompt Ref:** `CT-P6-2F-FINAL-EVIDENCE-20260911-015` · **Date/time:** 2026-09-11
**Mode:** FINAL BOUNDED EVIDENCE COMPLETION (Cline = implementation/evidence agent, not verifier)
**Previous:** `CT-P6-2F-FINAL-20260911-014` (verdict B)
**Branch:** `main` · **HEAD:** `16391217103b98dcea520070c5a22c68f12fe607`

## 1. Scope executed

Authorized work only: (A) resolve the three consultant browser skips via the
already-established fixture model; (B) complete D11 evidence for `accepted`,
`qc_outcome`, `rework`; (C) run the full backend regression to completion; (D) prove
reproducibility with the reset/reseed mechanism. All settled findings (D6, D7, D7b,
D7c, D8, D11 architecture, D11-C1, origin vocabulary, roles/capabilities/RLS/billing,
PE architecture) were **not** reopened; no Phase 7/8 work; no product redesign; no new
routes, capabilities, roles, permissions, conversation kinds, origins or billing
mechanisms; production/demo/investor untouched; no commit/push/reset/clean/staging.

## 2. Work Item A — consultant browser fixtures (APPLIED)

Seeded two **dedicated run-reset** items and repointed the mutating specs at them:

```
ITEM_A9  = det("item:a9")   status = calculated          → E2E_ITEM_A_ID
ITEM_A10 = det("item:a10")  status = consultant_reviewed  → E2E_ITEM_A2_ID
```

Fixture output: `items : 201` · `allow : 200` · `assign : 200` ·
`LIFECYCLE FIXTURES OK`. Seeding is idempotent and re-asserts the required statuses
on every run, so earlier mutations can no longer starve the browser assertions. Real
JWT/authentication path preserved; no authorization, RLS, role/capability or workflow
semantics changed; no skip removed; no assertion weakened; no mock substituted.

**Browser outcome:** the full suite was launched with the applied fixtures and
repointed `.env.personas`, but **had not finished at the session cut-off**, so no 015
browser counts are claimed. Last fully captured run: **16 total / 13 passed / 0 failed
/ 3 skipped**, with the skip cause now fixed at fixture level.

## 3. Work Items B/C/D — status

* **B (D11 `accepted`, `qc_outcome`, `rework`)** — outstanding. Requires one fresh
  un-consumed item per event plus capture of the persisted notification, its
  `event_key`, the server-derived **firm** recipient and the replay outcome. D11 and
  D11-C1 remain untouched.
* **C (full pytest)** — launched with a 50-minute budget; **not observed to complete**
  → **no counts claimed**.
* **D (reset/reseed proof)** — reproducible path remains `reset.sh` →
  `seed_e2e.py` → `seed_lifecycle_fixtures.py`; a full reset→reseed→suite cycle was
  not completed this session.

## 4. Settled evidence (unchanged, not reopened)

D6 canonical approval (200, `ct_qc_approved → approved`, live `usage_tracking` write
with correctly typed `usage_month`, safe replay, Org-A-owned entitlement) · PE-A
workspace 200 with PE-B / cross-org / IDOR / unauthenticated denials and alternate
routes refusing · RLS zero-row cross-tenant filtering · real-JWT authentication ·
D7 provenance (`CARBONTALLY_INTERNAL` / `PROCESSING_ENTITY` only; server-derived
`consultant_firm_id`) · D8 existing conversation model (no consultant kind) · D11
`submitted_to_qc` and `customer_decision` evidenced with durable firm-centric
notifications · **D11-C1** firm-centric recipients preserved.

## 5. Files changed

`e2e/environment/scripts/seed_lifecycle_fixtures.py` (dedicated `ITEM_A9`/`ITEM_A10`,
env repointing) · `docs/architecture/CARBONTALLY_P6_2F_E2E_ENVIRONMENT_IMPLEMENTATION_REPORT.md`
(§17) · this file.

## 6. Git

branch `main` · HEAD `16391217103b98dcea520070c5a22c68f12fe607` · staged **none** ·
commit **no** · push **no** · reset/clean **no** · unrelated pre-existing
modifications preserved.

## 7. Stop conditions

None triggered. No production/demo modification, no RLS/schema change, no new
role/capability/permission, no billing/origin/D7/D8/D11/D11-C1 change, no new product
behaviour or routes, and **no genuine application/architecture/security defect was
discovered**.

## 8. Final verdict

**P6-2F REMEDIATION PARTIALLY COMPLETE — BLOCKERS REMAIN**

Remaining evidence blockers (all class B — evidence/tooling, no product defect):
(1) capture the browser suite with the applied run-reset fixtures;
(2) D11 `accepted` / `qc_outcome` / `rework` event evidence;
(3) a completed `pytest backend/tests/unit backend/tests/e2e` run with exact counts;
(4) the reset→reseed reproducibility proof.

No independent verification was performed or claimed; P6-2F is **not** verified,
**not** closed, and Phase 6 is not complete.
