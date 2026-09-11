# CT-PROD-READINESS-AUDIT-20260911-001

**Prompt Ref:** `CT-PROD-READINESS-AUDIT-20260911-001` · **Date:** 2026-09-11
**Role:** independent production-readiness auditor / technical assessor — **read-only**
**Repository:** CarbonTally · **Branch:** `main` · **HEAD:** `16391217103b98dcea520070c5a22c68f12fe607`
**Durable output:** `docs/architecture/CARBONTALLY_PRODUCTION_READINESS_AUDIT_20260911.md`

## 1. Prompt record (digest)

Audit the real repository and authoritative documentation to determine what genuinely
prevents CarbonTally from being safely delivered to a first real paying customer, and the
shortest credible path to launch. Strictly read-only (no code, schema, RLS, RBAC, billing,
fixtures, harness, config or deployment changes; no commit/push/reset/clean). Respect the
authority hierarchy (Blueprint V1.3 → Roadmap V1.0 → phase gates → ratified PO decisions →
reports → tests → code). Distinguish **Phase 6 acceptance / Phase 7 / Phase 8 / production
launch requirements**, and classify findings as **P0** (must fix before a real customer),
**P1** (should fix if practical), **P2** (launch with controlled manual workaround),
**P3** (post-launch) or **E** (evidence gap — never equated with P0). Cover domains A–N
(customer journey, core processing, real customer data, authorization/security, billing,
human processing, admin ops, deployment, observability, backup/recovery,
privacy/governance, product claims, testing, first-customer operating model). Produce a
scorecard, the P0 list, the deferrable list, the launch path, and explicit Phase 6 / 7 / 8
recommendations. Fix nothing; create no new master/control document; claim no P6-2F
verification; finish with `CAN WE LAUNCH?`, `THE 3–10 THINGS THAT ACTUALLY MATTER NEXT`,
`WHAT WE SHOULD STOP WORKING ON`, `RECOMMENDED NEXT PHASE`.

## 2. Deliverable

Created `docs/architecture/CARBONTALLY_PRODUCTION_READINESS_AUDIT_20260911.md`
(183 lines) with: executive conclusion · capability table labelled
VERIFIED / PARTIALLY VERIFIED / UNKNOWN · **P0 list** · P1 · P2 · P3 · E-class gaps ·
per-domain assessments · scorecard · first-customer launch path · Phase 6/7/8
recommendations · evidence used · files inspected · commands executed · git status ·
plus the four mandatory closing sections.

## 3. Executive result

**CAN WE LAUNCH? → YES, AFTER P0 FIXES.** The security foundation, tenant isolation and
core workflows are real and verified (RLS zero-row cross-tenant enforcement; real GoTrue
auth; fail-closed entitlement; correct PE/consultant/org denials; no material security
defect found in any cycle). The distance to launch is engineering hygiene, commercial
operability and one end-to-end correctness proof — not architecture.

## 4. P0 findings

1. **P0-1 — Uncommitted release.** HEAD `1639121710…` while the working tree carries
   **682 modified/untracked entries** with **0 staged**. A deploy from HEAD ships the
   **broken billing path** and none of the Phase-6 work, with no rollback point. Fix:
   review + commit the intended change set (secrets excluded) and tag a release. *Low.*
2. **P0-2 — Approval/billing crash (fixed in tree, not deployed).** Reproduced
   `AmbiguousFunctionError: to_char(unknown, unknown)` → then
   `usage_month is date but expression is text` on
   `POST /api/v3/processing/items/{id}/customer-review`. After the working-tree fix
   (`date_trunc('month', $2::timestamptz)::date`,
   `backend/data/billing.py::UsageTrackingRepository.record`) approval returned **200**
   with the item `approved` and `usage_tracking` written. Must be committed, deployed and
   re-verified in production. *Low.*
3. **P0-3 — Core processing not evidenced end-to-end on customer-shaped data**
   (upload → extract/OCR → map → factor match → calculate → validate → approve → export).
   *Medium.*
4. **P0-4 — Subscription/allowance creation not proven operable** — the isolated
   environment needed a hand-built `customer_subscriptions` row and a
   `billing_commercial_config['standard_allowance']` row. Confirm the admin path or
   publish the SQL runbook as the launch workaround. *Medium.*

## 5. Explicitly NOT P0

Phase 7 (Auditor/Assurance) and Phase 8 (Advanced Analytics) are **not** launch gates. The
residual P6-2F items (three consultant browser skips on control visibility; D11
`accepted`/`qc_outcome`/`rework` records; incomplete full pytest run; reset/reseed
reproducibility; independent verification) are **E-class evidence gaps**, not launch
blockers. **Phase 6 recommendation: Option B** — close the known P6-2F implementation
scope, reclassify the rest as E-class launch evidence, and proceed to
production-readiness work.

## 6. Commands executed (read-only)

`git branch/rev-parse/status/diff --cached`; `information_schema` / `pg_policies` /
`pg_constraint` queries against the isolated Postgres (`:55326`); live API probes with
real GoTrue JWTs; PostgREST RLS matrix; `run_acceptance.py` (**16/16**);
`run_p6f_acceptance.py` (**35/37**); `npx playwright test`
(**16 = 13 passed / 0 failed / 3 skipped, exit 0**).

## 7. Files inspected

`AGENTS.md`; `backend/api/**` (incl. `v3_pe.py`, `v3_processing_workflow.py`,
`v3_billing.py`, `v3_messaging.py`, `admin_*.py`), `backend/data/billing.py`,
`backend/services/billing.py`, `backend/domain/partners.py`;
`frontend/src/supabaseClient.js`, `frontend/src/v3/api.js`,
`frontend/src/v3/consultant/ConsultantItemPage.jsx`; `supabase/migrations/**`;
`tests/e2e/**`; `playwright.config.ts`; Phase-6 reports and prompt history 001–017.

## 8. Git status / safety

branch `main` · HEAD `16391217103b98dcea520070c5a22c68f12fe607` · staged: **none** ·
modified/untracked: **682** (pre-existing, preserved) · committed: **no** · pushed:
**no** · reset/clean: **no**. **No fixes were made by this audit** — the only new files
are the audit report and this history record.

## 9. Environment note at closure

The isolated **Supabase/Postgres stack (`:55325` / `:55326`) was still running**, while
the **FastAPI (`:8051`) and frontend (`:3000`) application servers had stopped** (probes
returned `000`). Any subsequent verification session must restart them —
`backend/.venv/bin/uvicorn main:app --port 8051` with the isolated environment overrides
(`E2E_SUPABASE_URL` / `E2E_SERVICE_ROLE_KEY` / `E2E_ANON_KEY` / `E2E_DB_URL` from
`e2e/environment/.env.e2e`), and the CRA frontend on `:3000` with `REACT_APP_SUPABASE_URL`,
`REACT_APP_SUPABASE_ANON_KEY` and `REACT_APP_API_URL` pointing at the isolated stack —
before running API or browser acceptance.

## 10. Verdict of this prompt

Production-readiness audit **delivered** (report + this record). P6-2F remains
**NOT VERIFIED / NOT CLOSED**; no verification claim is made.

**Recommended next action for the Product Owner — Production-Readiness Execution:**
commit/tag → deploy the billing fix and re-verify approval and the entitlement path in
production → one real dataset end-to-end → minimal alerting + verified backup/restore →
first controlled customer with manual commercial operations.
