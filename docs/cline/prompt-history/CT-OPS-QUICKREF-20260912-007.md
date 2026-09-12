# CT-OPS-QUICKREF-20260912-007

**Prompt ID:** `CT-OPS-QUICKREF-20260912-007`
**Date:** 2026-09-12
**Type:** Technical operations documentation + configuration capture (documentation/capture only).
**Governance status:** Phase 7 — CLOSED — INDEPENDENTLY VERIFIED WITH ACCEPTED RESIDUALS.

## Objective

Produce a short, verified technical operations quick reference and a Render deployment configuration record; capture what can be verified from the repository, mark what cannot; do not change the application.

## Repository Starting HEAD

`bffe7e4b5e74be32b85fe5db03e900bde61546ed` (branch `main`; `origin/main` = `9e13236…`; `main` 3 ahead, not pushed). Pre-existing worktree: 208 modified, 52 untracked, staged 0.

## Files Inspected

`runtime.txt` · `vercel.json` · `.github/workflows/playwright.yml` · `backend/main.py` · `backend/main_v2.py` · `backend/config.py` · `backend/infra/supabase.py` · `backend/infra/config.py` · `backend/core/logging.py` · `backend/api/router.py` · `backend/api/v3_health.py` · `backend/workers/automatic_processing.py` · `backend/services/v3_email.py` · `backend/services/storage.py` · `backend/requirements.txt` · `backend/backup/*.py` · `frontend/package.json` · `frontend/src/supabaseClient.js` · `supabase/migrations/**` · `docs/architecture/CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md` · `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_RESTORE_ROADMAP_V1.0.md` · `docs/cline/prompt-history/CT-PROD-DEPLOYMENT-READINESS-20260911-001.md` · repository scans for `render*`/`Dockerfile`/`Procfile`.

## Files Created / Modified

**Created**
* `docs/operations/CARBONTALLY_TECHNICAL_OPERATIONS_QUICK_REFERENCE_V1.0.md` (22 sections)
* `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md`
* `docs/cline/prompt-history/CT-OPS-QUICKREF-20260912-007.md` (this record)

**Modified (minimal)**
* `docs/architecture/CARBONTALLY_TECHNICAL_OPERATIONS_DOCUMENTATION_ASSESSMENT_20260912.md` — appended §11 "Update — Newly Verified Evidence"; original findings preserved.

## Render Access Result

**UNVERIFIED — NO SAFE ACCESS.** No `RENDER*`/`RENDER_API_KEY` env var, no `render`/`render-cli` binary, no `~/.render` in the environment. The live Render service configuration could not be inspected. No inference about correctness was drawn.

## Verified Facts

* Repo-root `runtime.txt` = `python-3.11.9`.
* ASGI app `main:app` (`backend/main.py`); server `uvicorn`; `HOST`/`PORT` env-driven (defaults `0.0.0.0`/`8000`); `RELOAD` default `true`.
* Startup starts the durable automatic-processing worker; shutdown stops it and closes the Supabase pool.
* Health: `/`, `/health` (healthy/degraded), `/api/v2/health`, `/api/v3/health/realtime`.
* Backend logging = stdlib logging → stdout (`core/logging.py`).
* Worker = in-process asyncio loop over `document_processing_queue` (`FOR UPDATE SKIP LOCKED`, 1s poll, batch 3, 300s stale-lock recovery); no external queue service.
* **Migrations are not applied at application startup.**
* Frontend = CRA (`npm run build`); `vercel.json` SPA rewrites.
* CORS allow-list references `https://carbontally-api.onrender.com` (`backend/config.py`).
* Backup: encrypted/checksummed logical export capability exists (`backend/backup/**`); **no `restore` implementation**; scheduled backups/restore drill/RTO/RPO not implemented.

## Unverified Facts

Render service name/type/region/plan/instances, root directory, build command, start command, health path, env vars actually set, auto-deploy, separate worker service, current health state, `RELOAD` override; Vercel project settings; exact env values; Supabase region/reachability; production migration state; platform log retention; restore procedure/RTO/RPO; CI beyond Playwright.

## Sensitive Information Intentionally Omitted

All secret values (Supabase service-role key, JWT secret, DSNs, Resend key, AI provider key, Vercel OIDC token); publishable anon key **value** (its existence as a code fallback is noted, value omitted). Only variable names are documented.

## Change Statements

* Code changes: **NONE**
* Database changes: **NONE**
* Production changes: **NONE**
* Migration changes: **NONE**

## Tests / Verification Performed

Read-only only: file-existence checks; `git status`/`rev-parse`; `git diff` scoped to task files; repository greps supporting documented commands/paths; environment scan for Render credentials. No production mutation, no destructive tests, no migrations applied.

## Final Git State

* Ending HEAD: recorded in the completion report (see §21 of the prompt response / commit).
* Commit: one focused commit — `docs: add technical operations quick reference and Render capture`.
* Push status: **NOT PUSHED**
* Unrelated dirty/untracked work: **PRESERVED** (208 modified pre-existing; no reset/clean/stash/checkout; selective staging only).

## Recommendation for Next Task

Capture the live **Render service configuration as infrastructure-as-code (`render.yaml`)** (build/start/health/env names) so the deployment is reproducible, then re-verify the Render record. Optionally extend the quick reference with worker-backlog and email runbooks. **Do not** start the full manual, Phase 7 remediation, or Phase 8 without separate authorisation.

*End of record.*
