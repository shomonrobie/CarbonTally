# CarbonTally — Post-Publication Changelog (2026-09-11)

**Purpose:** durable record of what changed between the previously published `origin/main` boundary and the
verified publication commit, so a future agent can answer *"what changed since the last published state?"*
without relying on conversation memory.

**This is NOT a master architecture document.** The authoritative hierarchy remains
`CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` and `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`.

| Item | Value |
|---|---|
| Previous `origin/main` | `6148c86826e25e1889d8cf86bb02dbb2901577c6` |
| Publication commit | `5a1e45e0203b822b3a488a6004b904ef40abb059` |
| Commit message | `release: publish reconciled CarbonTally development state` |
| Parent of publication commit | `c864d729526ef2c5e40cd19fdc451e8f0975144b` (*"feat: close CarbonTally Phase 6 consultant workflow"*) |
| Publication date | 2026-09-11 |
| Commits published | **31** (30 accumulated development commits + the publication commit) |
| Pushed via | `git push origin main` — fast-forward `6148c86..5a1e45e` (no force, no tags, no other branch) |
| Remote verification | local `HEAD` == `origin/main` == `ls-remote origin refs/heads/main` == `5a1e45e…` |
| Local commits after publication | 178 |

## 1. What the publication commit itself contained (276 entries)

| Class | Count | Detail |
|---|---|---|
| Added (product/engineering) | 121 | `backend/backup/**` (9 modules), `backend/tests/{unit,integration}/backup/**` (8), `qa_harness/**` v1.1/v1.2 code+metadata (64), `AGENTS.md`, `playwright.config.ts`, plus the documentation set below |
| Modified | 3 | `backend/requirements.txt` (+`cryptography>=41.0.0`, for the backup subsystem), `.gitignore` (investor-demo + Playwright artefact ignores), `package-lock.json` (realigned to the committed `package.json` — 0 mismatches) |
| Deleted (intentional) | 152 | `.claude/skills/**` 69 and `.windsurf/skills/**` 69 (per-tool duplicate skill copies, replaced by `.agents/skills/**` + local symlinks), `output/{json,reports,sql}/**` 13 (generated pipeline output), `frontend/src/StaffDashboard.jsx` 1 (unreferenced legacy UI) |
| Documentation added | 8 `docs/architecture/**`, 10 `docs/legal/**`, 1 PO decision register, 19 `docs/cline/prompt-history/**` | production/backup architecture, deployment readiness, migration safety plan, Supabase reconciliation; legal risk register, third-party processor register, policy↔product consistency audit + 7 draft policies; the PO decision register; the full prompt-history audit trail |

## 2. Change classes (per Phase 1 requirement)

1. **Product changes** — none introduced by the publication commit itself: its only production-runtime
   surface additions are the (unmounted) backup subsystem and the `cryptography` dependency. The V3 product
   work (Phases A–L, Phase 2 close-out, Release-1) had already been committed in the 30 earlier commits
   (`17665d0` … `daad396`), which the same push published.
2. **Architecture / documentation changes** — the 8 production/backup architecture documents, the legal
   corpus, and the prompt-history audit trail (above).
3. **Tests / tooling** — backup unit + integration tests (8 files); the QA Harness v1.1/v1.2 source tree
   (64 files); root `playwright.config.ts`.
4. **Backup / DR work** — `backend/backup/**` (9 modules, 2,449 lines) + tests + 5 backup documents.
   PO-ratified decisions **D1–D5** (asyncpg exporter; private off-site object storage; application-level
   encryption with separate key custody; restore as a separately authorised capability; restricted
   `ct_backup` role). **Not activated**: 0 importers outside `backend/backup/`; no role created; no key
   generated; no backup executed.
5. **Production-readiness work** — deployment readiness, migration-safety plan, Supabase reconciliation,
   plus the previously committed readiness/manifest/pre-commit-gate documents.
6. **Deletions** — the 152 listed above; replacements verified present (`.agents/skills/**` 69 files,
   `frontend/src/v3/ops/**` for the staff surface).
7. **Excluded / local-only material (deliberately NOT published)** — `saas-assurance/**`,
   `agent_swarm/**`, `agent_swarm_v2_artifacts/**`, `.github/workflows/playwright.yml`,
   `tools/seed_investor_demo/**`, `CARBONTALLY_AUDIT_FINDING_VERIFICATION.md`, `docs/Robie/*.txt`,
   `admin/**` (EOL-only churn), `screenshots/**`, `qa_harness/{evidence,reports,*.jsonl,egg-info}`, E2E run
   state, `.openhands/**`, `.clinerules/**`, local configs, `independent_audit/**`, `.env*`, virtual
   environments, `node_modules`, `.tmp_pgdata`. The working tree intentionally remains dirty (207 modified
   EOL-only files + untracked excluded material).

## 3. Phase 6 closure state

Phase 6 (Consultant Workflow) is **CLOSED** — `c864d72` carried the authorised 11-file closure set including
the LT-1 fix in `backend/data/consultants.py` (the only production runtime change in that commit). Phase 7
and Phase 8 are **NOT STARTED**; backup/DR remains **not activated**; migration application remains
**unauthorised**.

## 4. Current authentication / access state (summary)

* Two sign-in methods are implemented: **email/password** and **Google OAuth** (brokered by Supabase Auth).
* Post-login destination is **server-authoritative** (`GET /api/v3/me/context` → `destination` /
  `primary_workspace`): staff → `/ops`, Processing Entity → `/pe`, consultant → `/consultant`,
  customer/org member → `/home`, no workspace → `/onboarding`; resolution failures fail closed (never
  `/onboarding`).
* **Defect found and fixed in this closure:** deep links (`/login`, `/privacy`, and every other nested route)
  returned **HTTP 404** in production because `vercel.json` rewrote them to `/frontend/index.html` — a path
  that does not exist in the build output. Full diagnosis in
  `CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md` §7.
* Google's OAuth consent screen presents the Supabase hostname (`pvwiojoyaqywtydzcpbg.supabase.co`) because
  Supabase brokers the OAuth exchange on its own domain. This is **not** controllable from the repository.

## 5. Known unresolved items (as at 2026-09-11)

| # | Item | Owner |
|---|---|---|
| U1 | Google Cloud OAuth consent screen configuration (app name, authorised domain, privacy/terms URLs, support email) | PO (external dashboard) |
| U2 | Supabase Auth configuration (Site URL, additional redirect URLs) and optional custom domain | PO (external dashboard) |
| U3 | Vercel project/output/root confirmation and redeploy of the corrected `vercel.json` | PO (external dashboard + deploy) |
| U4 | Render backend service variables/health (unchanged by this work) | PO (external dashboard) |
| U5 | Google verification may re-check `/privacy` and may require `/terms` | PO (external) |
| U6 | `admin/**` legacy CRA retention (quarantined, not deleted) | PO, per CL-66 / D-P2-02 |
| U7 | `package.json.allowScripts` still names superseded dependency pins | PO-approved follow-up |
| U8 | Production incident note `docs/Robie/getting this on live website.txt` (route/404 origin, not a DB outage) | PO backlog |

## 6. Evidence basis

`git log`/`diff`/`ls-tree`/`ls-remote` output;
`CT-PROD-PUBLICATION-{RECON,STAGING-PREP,STAGE-EXEC,COMMIT-EXEC,PUSH}-20260911-001`;
`CT-PHASE6-PUSH-AUDIT-20260911-001`; `CARBONTALLY_PHASE6_CLOSURE_AND_RELEASE_BOUNDARY_20260911.md`;
`CARBONTALLY_PRODUCTION_RELEASE_MANIFEST_20260911.md`; and live URL observations of
`https://carbontally.co.uk/` (200), `/login` (404) and `/privacy` (404) taken on 2026-09-11.
