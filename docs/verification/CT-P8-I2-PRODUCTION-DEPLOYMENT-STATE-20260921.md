# CT-P8-I2 — Production Deployment State Verification

**Type:** READ-ONLY production state verification. **No production changes were performed** (§12).
**Date:** 2026-09-21
**Verifying checkout:** `/home/shomonrobie/ct_93d5cdd` (authoritative release checkout)
**Final status:** `BLOCKED — PRODUCTION STATE UNKNOWN` (§13)

---

## 1. Authoritative release revision (verified)

| Item | Verified value |
| --- | --- |
| Checkout | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD | `989834be91b634a28002e4981b70e6a833b36c36` (`989834b`) |
| Working tree | **clean** (`git status --porcelain` empty) |
| GitHub remote | `github` → `https://github.com/shomonrobie/CarbonTally.git` |
| GitHub `refs/heads/p8-release-reconciled` | `989834be91b634a28002e4981b70e6a833b36c36` (`git ls-remote`, read-only) — **exactly aligned**, `rev-list --left-right --count` = `0 0` |
| Verified I2 application revision | `177dff51f59e9b904c021b4bbb7a6c7ee236adf1` — **present** (`git cat-file -t` → commit) and an **ancestor of HEAD** |
| Commits after `177dff5` touching application/migration/config | **none** (`git diff --name-only 177dff5..HEAD -- backend/ supabase/ frontend/ vercel.json` → empty) |

**I2 status restated:** `I2 CLOSED — VERIFIED PASS at 177dff5` (PO closure `551f121`, OHD re-verification `a11c7d5`, readiness audit `0848671`, topology reconciliation `989834b`).

## 2. Current Render production revision

> **Render production revision: UNKNOWN**

**Why (evidence, not assumption):**

* **No Render tooling**: `render` CLI is **not on PATH**, and there is no `~/.render`, `~/.config/render` or `~/.netrc` credential/config file.
* **No Render configuration in the repository**: no `render.yaml`, `Dockerfile`, `Procfile`, `backend/render.yaml` or `.render.yaml` exists, so no service, branch or environment mapping is available to inspect.
* Therefore the current production service, deployed commit/revision, deployment timestamp and source branch **cannot be directly verified**, and are **not** inferred from Git history, Vercel or any local checkout.

The Render production hostname is *documented* in the repository (`https://carbontally-api.onrender.com`, e.g. `/health`), but a documented hostname is **not** evidence of the deployed revision; no authorised read-only request was made against it.

## 3. Current Vercel production revision

> **Vercel production revision: UNKNOWN**

**Why:** no `vercel` CLI on PATH and no `~/.vercel` / `~/.config/vercel` credential or project link; the repository's `vercel.json` files are static rewrite rules only and identify no project, team or deployment. The current production deployment and its commit cannot be verified directly, and were **not** inferred from Git or from any preview URL. No promotion, rebuild or deployment was triggered.

For completeness (repository evidence, not deployment state): **I2 introduced no frontend change** — `git diff --name-only 177dff5..HEAD -- frontend/ vercel.json` is empty, and no Insight frontend exists in the tree.

## 4. Production database migration state

| Migration | Purpose | Production state |
| --- | --- | --- |
| `20261001000000_p8_i1_insight_persistence.sql` (I1 foundation: tables, indexes, constraints, RLS posture, four creator-private policies) | prerequisite for any Insight persistence | **UNKNOWN** |
| `20261002000000_p8_i2_insight_authorization.sql` (I2 author-kind policy: adds `AND role = 'user'` to the client message insert policy) | prerequisite for the verified I2 boundary | **UNKNOWN** |

**Why UNKNOWN:** no authorised production database inspection path was provided for this task. `psql` and `supabase` CLIs exist locally and a local `backend/.env` contains connection-shaped keys (`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ENVIRONMENT`), but:

* no explicit authorisation was given to connect to **production** with them;
* their target cannot be established without reading secret values, which this task must not do (and secrets must never be printed);
* the local environment is documented elsewhere in this project as the **local/demo** Supabase stack, so those values are not evidence of production state in any case.

Migration state was **not** inferred from Git, any local database, the Demo Lab, QA, `carbontally_test`, or deployment timestamps. No migration was run and none was inspected.

## 5. Production Insight schema state

> **Production Insight schema state: UNKNOWN**

The I2-required structures that would need to exist in production are:

* tables `public.carbontally_insight_conversations`, `public.carbontally_insight_messages` (with their indexes, constraints and composite FK);
* RLS enabled on both, with the four creator-private policies, and the I2 `role = 'user'` condition on the client message insert policy;
* grants: `anon` revoked; `authenticated` SELECT/INSERT only; `service_role` ALL.

None of these could be verified against production (same reason as §4). **Nothing was repaired, created or altered.**

## 6. Backend deployment dependency

* **Evidence:** the Insight backend code (new `backend/api/insight_authz.py`; modified `backend/api/v3_insight.py`, `backend/data/insight.py`, `backend/api/operations_auth.py`) exists **only on the release line** — it is absent from the other local checkouts (verified in the topology reconciliation) — and it is unchanged since the OHD-verified revision `177dff5`.
* **Conclusion (repository evidence):** delivering the **closed I2 behaviour** requires a backend revision **at or after `177dff5`** (any later release-line commit adds documentation only).
* **Whether production already runs such a revision:** **UNKNOWN** (§2).

## 7. Database deployment dependency

* **Conclusion (repository evidence): required.** The Insight tables/policies exist **only** as `20261001000000`, and the verified I2 author-kind hardening **only** as `20261002000000`. Nothing else in the repository creates them, so the closed I2 behaviour cannot be delivered without those migrations being present in the target database.
* **Whether production already has them:** **UNKNOWN** (§4).

## 8. Frontend deployment dependency

* **Conclusion: NOT REQUIRED.** I2 is backend/domain authorization work: zero frontend file and zero frontend configuration change is attributable to I1 or I2 (verified over `177dff5..HEAD`), and no Insight UI exists (I6 is not authorised).
* **Vercel production deployment state** remains **UNKNOWN** (§3) but is **not an I2 dependency**.

## 9. Detected production drift

* **Cannot be assessed:** drift analysis requires the production backend revision, which is **UNKNOWN** (§2).
* Repository-side statement (Git evidence only, no production inference): **no commit after `177dff5` changes application code, migrations, frontend or configuration** — therefore, for any release-line revision at or after `177dff5`, there is no *repository-recorded* post-verification application drift to review.
* No production configuration, authorization or migration file was modified, and none was reverted.

## 10. Evidence and method used

All evidence is read-only and local:

| Evidence | Method |
| --- | --- |
| Branch, HEAD, cleanliness, alignment, ancestry of `177dff5` | `git branch --show-current`, `git rev-parse HEAD`, `git status --porcelain`, `git rev-list --left-right --count`, `git merge-base --is-ancestor`, `git ls-remote github refs/heads/p8-release-reconciled` (no fetch, no local ref writes) |
| Post-verification change scope | `git diff --name-only 177dff5..HEAD -- backend/ supabase/ frontend/ vercel.json` |
| Deployment tooling / credential availability | `command -v` for `render`, `vercel`, `supabase`, `psql`; existence checks only for `~/.vercel`, `~/.config/vercel`, `~/.render`, `~/.config/render`, `~/.netrc`, `backend/.env*` |
| Local env **key names only** | `grep -oE '^[A-Za-z_][A-Za-z0-9_]*=' backend/.env` (names only; **no values read out, and no secret was printed**) |
| Deployment targets documented in repo | read-only `grep` for hostnames (`onrender.com`, `vercel.app`, `supabase.co`, `carbontally.co.uk`) — hostnames only |
| Repository topology facts used (release checkout authority, absence of Insight code elsewhere) | earlier read-only topology reconciliation (`989834b`) |

Secrets were neither read, printed, transmitted, nor used to authenticate anywhere.

## 11. UNKNOWN items and why

| Item | Status | Reason |
| --- | --- | --- |
| Render production revision / service / branch / timestamp | **UNKNOWN** | no Render tooling or credentials available; no Render configuration in the repository |
| Vercel production deployment revision | **UNKNOWN** | no Vercel tooling/credentials or project link available |
| `20261001000000` production applied-state | **UNKNOWN** | no authorised production database inspection path |
| `20261002000000` production applied-state | **UNKNOWN** | same |
| Production Insight schema/policy/grant state | **UNKNOWN** | same |
| Production application drift assessment | **UNKNOWN** | requires the deployed revision, which is UNKNOWN |

None of these UNKNOWN items has been converted into an assumption, and none was inferred from Git, Vercel previews, the Demo Lab, QA, `carbontally_test` or timestamps.

## 12. Statement of no production changes

**No production change of any kind was performed by this task.** Specifically: nothing was deployed to Render or Vercel; no production migration was run; no production schema, policy or grant was created, altered or dropped; no production row was inserted, updated or deleted; no production service was restarted; no Render or Vercel configuration was changed; no production database was connected to.

Repository-side: no Git remote was changed, no worktree pruned, no stale repository cleaned, no branch switched/merged/cherry-picked/reverted, no application code, migration, test or frontend file modified. The only repository change is **this report** (documentation-only), committed from the authoritative release checkout `/home/shomonrobie/ct_93d5cdd` and pushed to `github/p8-release-reconciled`. Nothing in the deferred topology-cleanup list was touched.

## 13. Final status

`BLOCKED — PRODUCTION STATE UNKNOWN`

One or more critical production facts — the deployed Render revision, the Vercel production revision, and the production applied-state of `20261001000000` / `20261002000000` (and therefore the production Insight schema state) — **could not be authoritatively inspected** with the access available to this task. The repository-side facts are fully established (release revision verified and aligned; `177dff5` unchanged since OHD verification; migrations required; no frontend dependency), but production state is **UNKNOWN** and has not been assumed.

**To unblock (PO action, not performed here):** provide an authorised read-only production inspection path — e.g. Render service revision information, the Vercel production deployment revision, and an approved read-only production database connection (or a migration ledger) — after which this verification can be completed without any production mutation.
