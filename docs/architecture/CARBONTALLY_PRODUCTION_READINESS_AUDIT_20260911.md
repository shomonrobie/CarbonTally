# CarbonTally — Production Readiness Audit

**Prompt Ref:** `CT-PROD-READINESS-AUDIT-20260911-001` · **Date:** 2026-09-11
**Auditor role:** independent production-readiness assessor (read-only; no fixes applied)
**Repository:** CarbonTally · **Branch:** `main` · **HEAD:** `16391217103b98dcea520070c5a22c68f12fe607`
**Authority used:** Blueprint V1.3, Master Roadmap V1.0, `AGENTS.md` operating constitution,
phase-6 gate reports + prompt history 001–017, `backend/**`, `frontend/**`,
`supabase/migrations/**`, live isolated E2E environment (`:55325` / `:55326` /
`:8051` / `:3000`).

## 1. Executive conclusion

CarbonTally is a **real, working multi-tenant emissions-processing platform** with a
genuine Auth/RLS/database foundation, a large implemented API surface (662 routes), a
functioning processing/QC/billing/notification model, and — critically — **no known
material security defect**. RLS was directly verified at the database boundary (cross-
tenant reads return **200 with zero rows**), real GoWTN auth and persona login work,
and the PE/consultant/organisation isolation denials all behave correctly.

The blockers between today and a first paying customer are **not** architectural. They
are three deployment/engineering realities:

1. **Nothing is committed.** The working tree carries **682 modified/untracked entries**
   while HEAD is an old commit — including a *real, reproduced production defect fix*
   (the D6 approval `to_char`/`usage_month` SQL crash). A production deploy from HEAD
   would ship the broken billing path and none of the Phase-6 work.
2. **The calculation/processing path has never been exercised end-to-end on real
   customer-shaped data** with automated evidence at the level a paying customer needs
   (extraction → mapping → factor match → calculate → validate → approve → export).
3. **Operational floor** (observability, backups/DR proof, OCR dependency verification,
   retention enforcement) is partially unverified — some of it Supabase-managed,
   some genuinely unknown.

**Verdict shape:** `YES, AFTER P0 FIXES` (the P0 list is short and mostly engineering
hygiene, not redesign).

## 2. Current system capability (evidence-classed)

| Capability | State | Evidence class |
|---|---|---|
| Multi-tenant data model (organisations, firms, PEs, membership, grants) | Present | VERIFIED (schema + live queries) |
| RLS boundary (116 RLS tables, 175 policies) | Working | VERIFIED (PostgREST + real JWTs: cross-org = 200/0 rows) |
| Authentication (GoTrue, real JWTs, 7 personas) | Working | VERIFIED (token issuance + API calls) |
| API surface (662 routes: processing, QC, ops, billing, messaging, admin) | Present | VERIFIED (route inventory) |
| Entitlement gate (D6) fail-closed when no subscription | Working | VERIFIED (403 `No active processing entitlement`) |
| Billing charge path (STANDARD allowance → `usage_tracking`) | **Was broken, fixed in working tree** | VERIFIED (500 `AmbiguousFunctionError` → then `usage_month` type error → fixed to `date_trunc(...)::date`; approval then returned **200** with item `approved`) |
| D11 lifecycle notifications (5 events, deterministic keys, durable rows) | Architecture present; 2 of 5 events evidenced | PARTIALLY VERIFIED |
| PE isolation (workspace ALLOW via assignment + `can_process` role) | Working | VERIFIED (PE-A 200 after role fixture; PE-B/cross-org/IDOR 403/401) |
| Consultant lifecycle UI (review / submit-to-QC / notification deep link) | Implemented; browser specs still skip on control visibility | PARTIALLY VERIFIED |
| Frontend (CRA) + public site separated from app | Present | VERIFIED (route protection specs pass) |
| Regression suite | 1,693 unit+e2e passed at one observed point; full run not reproducible to completion in-session | PARTIALLY VERIFIED |
| OCR / PDF extraction in production | Implementation present; OCR is an environment dependency | **UNKNOWN** in production |
| Backups / PITR / restore drill | Supabase-managed; no restore evidence | **UNKNOWN** |
| Observability (metrics/alerting) | Logging + health-ish endpoints only | PARTIALLY VERIFIED |

## 3. P0 — MUST FIX BEFORE A REAL CUSTOMER

| # | Problem | Evidence | Impact | Minimum fix | Complexity |
|---|---|---|---|---|---|
| **P0-1** | **Phase-6 work and the defect fix are uncommitted.** HEAD `1639121710…` with **682 modified/untracked entries**, nothing staged | `git status --short \| wc -l` = 682; staged = 0 across all cycles | A deploy from HEAD ships the **broken billing path** and none of the Phase-6 work; no rollback point | Review + commit the intended change set (secrets excluded), tag a release | Low |
| **P0-2** | **Approval/billing charge crashed every time** — `AmbiguousFunctionError: to_char(unknown, unknown)`, then `usage_month is date but expression is text` | live API traceback → 500; after fix → **200**, item `approved`, `usage_tracking` written | No subscribed org could complete an approval; entitlement consumption never recorded | Fix **applied in the working tree** (`date_trunc('month', $2::timestamptz)::date`, `backend/data/billing.py`); commit → deploy → re-verify | Low |
| **P0-3** | **Core processing not evidenced end-to-end on customer-shaped data** (upload → extract/OCR → map → factor match → calculate → validate → approve → export) | Phase-6 evidence is security/workflow-focused; no calculation-correctness record | Silent wrong numbers = worst failure mode for an emissions product | Run one realistic dataset through the whole pipeline; record numbers + provenance | Medium |
| **P0-4** | **Subscription/allowance creation not proven operable** — the isolated env needed a hand-built `customer_subscriptions` row + `billing_commercial_config['standard_allowance']` | fixtures cycles 006–017; 403 fail-closed confirmed | A paying customer is blocked and cannot be unblocked from the UI | Confirm the admin path, or publish the SQL runbook as the launch workaround | Medium |

## 4. P1 — SHOULD FIX BEFORE LAUNCH IF PRACTICAL

Full regression never completed (1,693 passed once) · three consultant browser specs
skip on **control visibility** while the API returns 200 · OCR/extraction availability
in production unverified · no metrics/alerting for background failures · frontend env
defaults point at production Supabase / localhost API unless overridden · retention
enforcement unevidenced.

## 5. P2 — CONTROLLED MANUAL WORKAROUND IS ACCEPTABLE

Manual org onboarding · manual entitlement/subscription setup (documented runbook) ·
manual invoicing · manual work assignment by CarbonTally staff · manual failure triage
from ops/QC queues · controlled customer count/volume.

## 6. P3 — POST-LAUNCH

Advanced analytics · benchmarking · Phase-7 auditor/assurance · cross-customer
aggregation · UI polish · harness re-runnability tooling · scale optimisation.

## 7. E — EVIDENCE GAPS (not launch blockers by themselves)

D11 `accepted` / `qc_outcome` / `rework` records (architecture delivers; 2 of 5
evidenced) · the three browser skips (UI visibility; API 200) · full pytest completion ·
reset/reseed reproducibility · P6-2F independent verification (a process gate).

## 8. Domain summary

Security → implemented & verified, **no material defect** · Data isolation → VERIFIED
(zero-row cross-tenant RLS) · Core processing → PARTIALLY VERIFIED + P0-3 · Billing →
real model, P0-2/P0-4 · Human processing → operable manually (P2) · Admin → present,
sufficiency PARTIALLY VERIFIED (P0-4) · Deployment → topology ready, **release
uncommitted (P0-1)** · Observability → P1 · Backup/DR → UNKNOWN · Privacy/governance →
P1-6 + UNKNOWN vendor handling · Product claims → PO review before marketing.

## 9. FIRST CUSTOMER LAUNCH PATH

```text
Current state (working tree = the real system; HEAD is stale)
  ↓ P0-1  commit the intended change set + tag a release
  ↓ P0-2  deploy with the billing fix; re-verify approval in production
  ↓ P0-4  admin path / SQL runbook for subscription + allowance
  ↓ P0-3  one realistic dataset end-to-end (numbers + provenance)
  ↓ Deploy (Vercel + Render + Supabase); rehearse rollback
  ↓ Internal dogfooding on customer-shaped data
  ↓ First controlled customer (manual onboarding, invoicing, work assignment)
```

## 10. Phase 6 recommendation

**B** — close the current P6-2F implementation scope, record the remaining items as
**E-class launch evidence**, and move to production-readiness work. No known P6-2F defect
is a production blocker; the residuals are executor/visibility gaps.

## 11. Phase 7 / Phase 8

* **Phase 7 (Auditor/Assurance): NOT required** for the first customer — unless public
  claims say "assurance"/"verified", in which case the *claims* must change, not the
  product.
* **Phase 8 (Advanced Analytics): NOT required** — defer.

## 12. Evidence used / files inspected / commands

Files: `AGENTS.md`; `backend/api/**` (incl. `v3_pe.py`, `v3_processing_workflow.py`,
`v3_billing.py`, `v3_messaging.py`, `admin_*.py`), `backend/data/billing.py`,
`backend/services/billing.py`; `frontend/src/supabaseClient.js`, `frontend/src/v3/api.js`,
`frontend/src/v3/consultant/ConsultantItemPage.jsx`; `supabase/migrations/**`;
`tests/e2e/**`; `playwright.config.ts`; Phase-6 reports and prompt history 001–017.

Commands: `git branch/rev-parse/status/diff --cached`; `information_schema`,
`pg_policies`, `pg_constraint` queries on `:55326`; live API probes with real JWTs;
PostgREST RLS matrix; `run_acceptance.py` (**16/16**); `run_p6f_acceptance.py` (**35/37**);
`npx playwright test` (**16 = 13 passed / 0 failed / 3 skipped, exit 0**).

## 13. Git status

branch `main` · HEAD `16391217103b98dcea520070c5a22c68f12fe607` · staged: **none** ·
modified/untracked: **682** (pre-existing; preserved) · committed: **no** · pushed: **no**.
**This audit performed read-only inspection only — no fixes, no code or fixture changes.**

---

# CAN WE LAUNCH?

**YES, AFTER P0 FIXES.** The security foundation, isolation model and core workflows are
real and verified. The distance to launch is engineering hygiene (commit/deploy the fix),
commercial operability (entitlement setup) and one end-to-end correctness proof on real
data — not architecture.

# THE 3–10 THINGS THAT ACTUALLY MATTER NEXT

1. **Commit and tag the working tree** (P0-1) — nothing else is trustworthy until the
   release contains the actual code.
2. **Deploy the billing fix and re-verify a real approval** (P0-2).
3. **Prove the admin/runbook path for subscription + allowance** (P0-4).
4. **Run one realistic dataset end-to-end**; record numbers + provenance (P0-3).
5. **Verify OCR/extraction on production infrastructure** (P1-3).
6. **Add minimal alerting** for processing/billing/notification failures (P1-4).
7. **Verify backups/PITR and perform one restore drill** (UNKNOWN → must be known).
8. **Rehearse deploy + rollback** on Vercel/Render/Supabase.
9. **Confirm consultant-surface controls render** for review/submit (P1-2).
10. **PO review of public product claims** (assurance/verification wording).

# WHAT WE SHOULD STOP WORKING ON

* Further P6-2F evidence polish (browser skips, harness re-runnability, D11 executor
  fixtures) — useful for the record, but not what blocks a customer.
* Additional read-only audit cycles over the same state.
* Phase 7/8 design exploration before launch.
* Redesigning billing, RLS, D7/D8/D11 or the PE model — none of it is broken.

# RECOMMENDED NEXT PHASE

**Production-Readiness Execution (short):** commit → deploy → verify the billing fix and
entitlement path in production → one real dataset end-to-end → minimal alerting and a
verified backup/restore → first controlled customer with manual commercial operations.

P6-2F remains **NOT VERIFIED / NOT CLOSED**; this audit makes no verification claim.


