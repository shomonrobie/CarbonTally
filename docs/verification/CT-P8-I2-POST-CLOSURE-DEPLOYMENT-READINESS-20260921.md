# CT-P8-I2 — Post-Closure Deployment Readiness Audit

**Type:** read-only deployment-readiness audit (documentation only)
**Date:** 2026-09-21
**Auditor role:** Cline — audit only; no application code, migration, schema, test, configuration, frontend, deployment or production data was modified; nothing was deployed; I3 was not started.
**Final status:** `NOT READY — CHANGE REQUIRES REVIEW` (§13)

---

## 1. Repository state (verified now, not assumed)

| Item | Observed |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD | `a11c7d5e5d42cd2ad2bf20fd365a36fcec16c8a4` (`a11c7d5`) |
| Working tree | clean (`git status --porcelain` empty) |
| Remote | `github/p8-release-reconciled` aligned — `git rev-list --left-right --count` = `0 0` (behind 0, ahead 0) |
| I2 application revision `177dff5` | **present in branch history** (`git cat-file -t` → `commit`; `git log -1 177dff5` → `fix(p8-i2): remediate OHD I2 FAIL …`) |
| PO closure doc `docs/architecture/CarbonTally PO I2 Closure.md` | **NOT PRESENT** — not on disk (`ls` → No such file or directory), not tracked in `HEAD` (`git cat-file -t HEAD:…` → does not exist), and no file matching `*I2*Closure*` exists anywhere under `docs/` |

> **Discrepancy recorded (not resolved by this audit):** the instruction cites
> `docs/architecture/CarbonTally PO I2 Closure.md` as the authoritative closure record, but that
> document — and any equivalent I2 closure document — does not exist in this repository at this
> revision. No closure-documentation commit exists either (§2). The PO closure is therefore
> **asserted externally but not evidenced in the repository**.

## 2. Git history analysis

```
a11c7d5 docs(p8-i2): OHD independent re-verification of the Insight I2 remediation   <-- HEAD
177dff5 fix(p8-i2): remediate OHD I2 FAIL (customer role contract, active organisation, hermetic RLS test)   <-- VERIFIED APPLICATION REVISION
git log --oneline -8 (compact):
  a11c7d5  docs(p8-i2): OHD independent re-verification of the Insight I2 remediation
  177dff5  fix(p8-i2): remediate OHD I2 FAIL (customer role contract, active organisation, hermetic RLS test)
  682d591  docs(p8-i2): OHD independent verification of the CarbonTally Insight I2 authorization layer
  ad49f57  docs(p8-i2): CT-P8-I2 Insight authorization implementation report
  de18c35  feat(p8-i2): CarbonTally Insight authorization and visibility layer
  66adfb5  docs(p8-i1): OHD independent verification of the CarbonTally Insight I1 foundation
  5bd5e29  docs(audit): CT-FEATURE-AUDIT-P1-P8X-001 … feature completeness and implementation matrix
  97b50c3  docs(p8-i1): record I1 regression baseline evidence
```

**Commits after the verified revision `177dff5`:** exactly **one** — `a11c7d5`.

```
$ git diff --name-status 177dff5..HEAD
A  docs/verification/OHD-P8-I2-INSIGHT-AUTHORIZATION-REVERIFICATION-20260921.md
$ git diff --name-only 177dff5..HEAD -- backend/ supabase/ frontend/
   (empty)
```

| Classification | Revision(s) | Content |
| --- | --- | --- |
| **Verified application revision** | `177dff5` | I2 remediation implementation + tests + report addendum |
| **I2 implementation commits (pre-verification)** | `de18c35` (I2 + I1 hardening), `ad49f57` (I2 report) | application + documentation |
| **I2/OHD verification-report commits** | `682d591` (OHD I2 FAIL report), `a11c7d5` (OHD I2 re-verification report) | **documentation only** |
| **PO closure documentation commit** | **does not exist** | — |
| **Commits after `177dff5`** | `a11c7d5` | **documentation only** (one added file) |

No application commit exists after `177dff5`; nothing after it is being carried as “probably safe” — it was checked and contains **no** `backend/`, `supabase/` or `frontend/` change.

## 3. Application-tree comparison (`177dff5` → HEAD)

Per-file blob identity (`git rev-parse <rev>:<path>`) — all **UNCHANGED**:

| File | Blob (identical at `177dff5` and HEAD) |
| --- | --- |
| `backend/api/insight_authz.py` | `63e0699d996f38a543ec3f2aad2ddda0a769a669` |
| `backend/api/v3_insight.py` | `6cb2fa4645e2c2932e05d1393e7eb840563c09a9` |
| `backend/data/insight.py` | `ec63b6f2a276aa510d5cc0ea6193258039d71115` |
| `backend/api/operations_auth.py` | `1494a524ce7bc36861d688474bf4779dc349ca74` |
| `backend/tests/unit/api/test_v3_insight_i2_authorization.py` | `22497f9719e0c757631efb8bb5a8cde76b22ce00` |
| `backend/tests/unit/api/test_v3_insight_endpoints.py` | `fe543feaac346e3380654921180d0d23110024e9` |
| `backend/tests/unit/data/test_i2_insight_rls_live.py` | `210da86a1875d7517ed855da28d07c1882a8d1a0` |
| `backend/tests/unit/data/test_i2_insight_authorization_contracts.py` | `6af66ec1ff091f115fac79d1a8d9c5159735cff6` |
| `backend/tests/unit/data/test_i1_insight_migration.py` | `68c69412ef25295dba62937b191d25852a5ed329` |
| `supabase/migrations/20261002000000_p8_i2_insight_authorization.sql` | `28cbebadb43634d5783d0622235040217d824fe5` |
| `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql` | `58e7a3ab4997d8fb9cd1abe873e88305bb7e2a4d` |

**Changed:** none. **Added:** `docs/verification/OHD-P8-I2-INSIGHT-AUTHORIZATION-REVERIFICATION-20260921.md` (documentation). **Removed:** none. No exact-commit attribution is needed because no application file differs.

## 4. Migration / deployment dependency

| Question | Finding |
| --- | --- |
| Migrations present in the repository | `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql` (introduced in `5633798`, I1) and `supabase/migrations/20261002000000_p8_i2_insight_authorization.sql` (introduced in `de18c35`, I2) — both tracked, both blob-identical to the verified revision |
| Migration added **after** `177dff5` | **None** (`git diff 177dff5..HEAD -- supabase/` is empty) — the remediation added **no** migration |
| Migration **required to deploy** the verified revision | **Yes, both** — the Insight tables/policies exist only via `20261001000000`, and the F-03 author-kind hardening (`WITH CHECK … AND role = 'user'`) exists only via `20261002000000`. The application boots without them, but the Insight API would fail at runtime and the RLS hardening would be absent |
| Migration already applied in **production** | **UNKNOWN** — not determinable from the repository (no deployment manifest, no migration ledger, no environment state in Git) |
| Migration state in the **disposable** database | `carbontally_test` has both Insight migrations applied plus the p6_1c/p6_2a consultant columns (applied during the I2 remediation for test execution only) |
| Demo Lab / QA / production | **Not modified** by the I1 work, the I2 implementation, the I2 remediation or this audit |

No production migration was run and none is run by this audit.

## 5. Render backend readiness

| Question | Finding |
| --- | --- |
| Would deploying the verified revision change **backend application code**? | **Yes** — three backend application files and one shared authorization module are part of the I2 work (`backend/api/insight_authz.py` new; `backend/api/v3_insight.py`, `backend/data/insight.py`, `backend/api/operations_auth.py` modified). Whether that is a *change on Render* depends on the currently deployed revision, which is **not determinable from the repository** |
| Would it introduce a **migration**? | **Yes** — §4: two Insight migrations must exist in the target database (`20261001000000`, `20261002000000`) |
| Would it change **environment variables**? | **No Insight-specific configuration exists**: no `INSIGHT*` setting, flag or variable in the backend configuration and no `.env.example` entry. **Render's actual environment variables cannot be verified from the repository** |
| Would it change **startup commands**? | **No repository evidence of any change.** There is **no** `render.yaml`, `Dockerfile`, `Procfile`, `backend/render.yaml` or `start.sh` tracked in this repository, so Render's build/start configuration **cannot be determined from the repository** — stated explicitly rather than assumed |
| Would it change **dependencies**? | **No** — `backend/requirements.txt`, `backend/pyproject.toml`, `backend/requirements-dev.txt` are unchanged since `177dff5`; the Insight code uses only already-present libraries (`asyncpg`, FastAPI, pydantic). The live-RLS test additionally uses `pytest-asyncio`/`asyncpg`, both already in the dev/test environment |
| Would it alter **authorization behaviour outside Insight**? | **No Insight-driven change.** The only shared-file change is a small **additive public alias** in `backend/api/operations_auth.py` (`resolve_staff_context` delegating to the pre-existing `_resolve_context`) — no behaviour change to existing callers. `auth.py`, `api/dependencies.py` and `api/consultant_auth.py` are untouched by I1/I2, so platform-wide authorization is unchanged. (Note for the deployer: platform-wide authorization behaviour on the *deployed* revision depends on which revision is currently live, which is unknown) |

**Render-specific configuration: cannot be determined from the repository.** No Render manifest or Docker/Procfile entrypoint is tracked, and no deployment record or environment inventory is available in Git.

## 6. Vercel frontend readiness

* **No frontend file changed** in I1, the I2 implementation or the I2 remediation:
  `git diff --name-only 177dff5..HEAD -- frontend/ vercel.json` → **empty**;
  `git diff --name-only 177dff5..HEAD -- backend/ supabase/ frontend/` → **empty**.
* Configuration present (unchanged, for reference only): root `vercel.json` (legacy/admin static rewrites to `/admin/index.html`) and `frontend/vercel.json` (`/(.*) → /index.html`). Neither is touched by I2.
* **No Insight frontend exists at all**: a search for `insight` under `frontend/src` returns nothing (the Insight UI is I6, which is not authorised).

**Conclusion: the I2 closure does not require a Vercel deployment.** I2 is backend/domain authorization work; a Git commit existing on the branch is not, by itself, a frontend deployment trigger.

## 7. I2 authorization-boundary sanity check (read-only trace)

Performed against the blob-identical verified file (`backend/api/insight_authz.py`,
`63e0699d…`). This is a **sanity check only**; it does not reopen OHD's verification.

| Required property | Present in the verified revision | Evidence (line refs in the verified blob) |
| --- | --- | --- |
| Customer own-organisation authorization | **Yes** | `CUSTOMER_INSIGHT_ROLES` (L65), `ORG_ROLE_PREFIX = "org_"` (L68), `normalize_org_role()` (L104-115) — production `org_owner`/`org_admin`/`org_member`/`org_viewer` shape accepted; own-org-only comparison in the customer branch |
| Organisation-active check | **Yes** | `organization_is_active()` (L146-158) called **before** any scope branch (L250); fails closed on missing/inactive/absent repository surface |
| Consultant authorization via existing `consultant_clients` | **Yes** | `ensure_consultant_org_access` imported (L50) and called (L284) — the platform's D15 ACTIVE-grant resolver; no parallel model |
| Staff authorization via existing permissions | **Yes** | `STAFF_INSIGHT_PERMISSIONS = ("can_view_all",)` (L80), `STAFF_SUPERUSER_FLAG = "is_superuser"` (L81), `staff_context_grants_insight_scope()` (L133) + `resolve_staff_context`; `entity_id is not None` → PE denial (L259) |
| Explicit auditor denial | **Yes** | `AUDITOR_ROLE_NAMES` (L73), `is_auditor_principal()` (L118-130), checked **first** in both the classifier (L294) and the gate |
| Creator-private visibility | **Yes** | `visibility_created_by()` returns the principal id (L322); `conversation_is_visible()` requires organisation **and** creator (L331) |
| Every-read re-authorization | **Yes** | Router-level gate `dependencies=[Depends(require_insight_user)]` (`v3_insight.py` L51) **and** per-request `authorize_insight_scope(...)` in every endpoint; no caching of an authorization result |
| Forged Insight-role protection | **Yes** | RLS policy `WITH CHECK (… AND role = 'user')` in `20261002000000` (L64); API rejects `role != 'user'` with 422 |
| Deny-by-default | **Yes** | Uniform `_denied()` 403; unrratified role → DENY; PE → DENY; auditor → DENY; unknown/blank organisation → 422/403 |

**No post-verification code change and no contradiction was found, so OHD's PASS is not reopened.**

## 8. I3 scope check

Searches over the Insight modules and the application tree found:

* **no** provider/LLM integration in Insight (`openai`, `anthropic`, `langchain`, `embedding`, `pgvector`, `llm`, `completion` — none in `backend/api/insight_authz.py`, `backend/api/v3_insight.py`, `backend/data/insight.py`, `backend/domain/insight.py`);
* **no** tool registry, tool execution, intent classification or natural-language answering module (pattern search for `*tool*`, `*intent*`, `*rag*`, `*interaction*` matched only `backend/.venv` third-party files);
* **no** AI interaction records or canonical AI audit events (nothing beyond the I1 Layer-1 conversation/message tables);
* **no** context/memory layer;
* **no** Insight frontend (no `insight` reference under `frontend/src`);
* **no** retention/export, billing/allowance or automatic-consequential-action code for Insight;
* the only Insight routes are the five persistence routes mounted once from `backend/api/router.py` (L68 import, L237 include) — no new route surface was added after `177dff5`.

> **No I3 implementation detected.**

## 9. Unresolved deployment dependencies (why the status is not “ready”)

1. **Two migrations must be applied** to whichever persistent database the deployed backend uses (I1 tables/policies `20261001000000`; I2 author-kind policy `20261002000000`) — an operational step requiring separate authorisation and a rehearsed order.
2. **The target environments' migration state is unknown** from the repository (no ledger/manifest in Git).
3. **Render configuration cannot be verified** from the repository (no manifest/Dockerfile/Procfile tracked), so build/start commands and environment variables cannot be confirmed unchanged.
4. **The currently deployed application revision is unknown**, so “what changes on deploy” cannot be stated as a fact from repository evidence alone.

None of these is an application-code defect, and none contradicts OHD's PASS on `177dff5`.

## 10. Evidence limitations

* No access to Render/Vercel/Supabase deployment consoles, so environment variables, service configuration, deployed revisions and production migration state could not be inspected — they are reported as **unknown**, not assumed.
* Production/demo/QA databases were deliberately not queried for this audit (a read-only query would still be an environment action not authorised here).
* The PO closure record could not be inspected because it is **absent** from the repository (§1).
* Test execution was **not** re-run for this audit: it is a read-only audit and the application blob is identical to the verified revision, whose test evidence is already recorded in `docs/implementation/phase8/CT-P8-I2-INSIGHT-AUTHORIZATION-20260921.md` §12.8.

## 11. Confirmations

* No application code, migration, schema, test, configuration, frontend or production data was modified by this audit; nothing was deployed; no Render/Vercel action was taken; **I3 was not started** and no I3 artefact was created.
* The repository modification made by this task is this single permanent report (documentation only).
* OHD's verification reports (`682d591`, `a11c7d5`) and the audit report were **not** modified.

## 12. Final factual readiness status

`NOT READY — CHANGE REQUIRES REVIEW`

**Basis (exactly per the defined criteria):** the verified application revision `177dff5` and its
application tree are **unchanged** at HEAD (`a11c7d5` is documentation-only, and every I2 file is
blob-identical), so there is **no post-verification application change** and no reason to reopen
OHD's PASS. However, **a deployment dependency requires review**: the two Insight migrations must be
applied to the target database, and the target environments' migration state, the deployed revision
and the Render service configuration **cannot be determined from repository evidence**.

This audit does **not** make the deployment decision. The PO decides, after reviewing this report,
whether to authorise (a) the migration plan and ordering, (b) the backend deployment of `177dff5`
(or of the documentation-only HEAD), and (c) whether any frontend action is wanted at all (I2 requires none).
