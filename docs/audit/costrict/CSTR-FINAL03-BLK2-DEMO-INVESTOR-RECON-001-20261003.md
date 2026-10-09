# CSTR-FINAL03-BLK2-DEMO-INVESTOR-RECON-001 — Demo/Investor Environment ↔ FINAL-03 BLK-2 Reconciliation + Production Sign-In Forensics

**Report ID:** CSTR-FINAL03-BLK2-DEMO-INVESTOR-RECON-001-20261003
**Date:** 2026-10-03
**Investigator:** CoStrict (independent, read-only forensic verification — NOT the implementation agent)
**Frozen release:** `375a48dc1b9e9cfd74090bbf747554ae997acb59` · branch `p8-release-reconciled` · remote `github`
**Type:** READ-ONLY FORENSICS. No mutation, no fix, no deploy, no commit, no push.

**Evidence labels:** `[observed]` · `[code-traced]` · `[documented]` · `[runtime]` · `[browser]` · `[inference]` · `[limitation]`

---

## 1. Executive summary

1. **The repository's actual demo environment is the "Demo Lab"** (`tools/demo_lab/`), a **local, disposable** stack on the developer machine — **not** the ~1,185-identity "investor dataset" named in `AGENTS.md` §54, whose tooling (`tools/seed_investor_demo/`) is **absent** from this checkout. `[observed]` `[documented]`
2. The Demo Lab provisions **14 role-bearing actors** (staff, internal operator, two PE managers, four org-A roles, two org-B roles, consultant owner+member, two client owners) with a deterministic, idempotent, resettable mechanism — including, critically, the **staff (`/ops`), consultant (`/consultant`) and PE (`/pe`) actors that production lacks**. `[observed]` `[code-traced]`
3. **Demo Lab authentication is local GoTrue password-grant only. Google OAuth was never exercised in any Demo Lab verification** (DR-002…DR-007). `[documented]` `[code-traced]`
4. The Demo Lab's **schema/auth/RLS/storage are not equivalent to production** (local GoTrue; a stale lab schema revision; no hosted Supabase). It is **PARTIALLY SUFFICIENT** for FINAL-03: it can prove model/role/isolation **behaviour**, but it cannot prove **production-specific** facts (production RLS posture on the production schema, production storage, production OAuth, production email, production routing/origins). `[inference]`
5. The **"Completing sign in... Please wait while we verify your account"** string is the **`AuthCallback` initial loading state** ([`AuthCallback.js:111`](frontend/src/AuthCallback.js:111)) `[code-traced]`. Its two clearing paths are bounded (`navigate` on success; the error branch on a bounded 25 s `/me/context` failure); the **initial/retry `supabase.auth.getSession()` calls have no timeout**, so a hang there is the only unbounded path that would leave this view indefinitely. `[code-traced]` `[inference]` The **production-specific trigger is not observable read-only** → the symptom is **PARTIALLY EXPLAINED** as a mechanism, **unexplained** as a live cause.
6. The **"Failed to load your workspace. Please try again."** symptom is the **`AuthCallback` error branch** ([`AuthCallback.js:43`](frontend/src/AuthCallback.js:43)) — a **bounded** post-session workspace-resolution failure. It and the stall are **mutually exclusive render branches** of the same component → **distinct symptoms**, not demonstrably one causing the other. `[code-traced]` The production OAuth configuration is **NOT OBSERVABLE FROM CURRENT READ-ONLY ACCESS**.
7. **BLK-2 is a test-identity/data readiness gap, not a product defect.** No executed check has failed; the criteria are **NOT TESTED**. `[documented]`

---

## 2. Scope and read-only boundary

**In scope:** reconstruct the Demo/Investor environment and its identity provisioning; build the actor matrix; map FINAL-03 BLK-2 criteria to Demo actors; assess Demo-Lab↔production equivalence; forensically trace the two production authentication symptoms; assess existing production identities; propose a safe acceptance model; determine the `/ops` relationship.

**Boundary (hard):** no code/migration/schema/RLS/policy/grant/data/storage/auth/OAuth/Vercel/Render/DNS/env/secret change; no user/session/organisation/doc/report/calculation created; no authenticated production write; no approval/rejection/finalisation; no deploy/commit/push/reset/seed. Production and Demo-Lab data were read only. No credential is printed.

**Files/paths inspected:** `docs/demo-investor/DR-001…DR-007`; `tools/demo_lab/{manifest.json,provision.py,README.md}`; `frontend/src/{AuthCallback.js,Login.js,v3/api.js,v3/components/RoleRoute.jsx,App.js}`; `backend/api/v3_context.py`; `docs/architecture/CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md`; `docs/architecture/CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927-REPORT.md`; `docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md`; `docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md`; `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md`; `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/**`; `docs/audit/costrict/CSTR-FINAL03-LIVE-ACCEPTANCE-001-20261003.md`.

---

## 3. Frozen release verification

- Local `git rev-parse HEAD` = `375a48dc1b9e9cfd74090bbf747554ae997acb59`; branch `p8-release-reconciled`. `[observed]`
- The live production bundles carry the same frozen SHA (verified in `CSTR-FINAL03-BLK1-POST-REMEDIATION-VERIFY-20261003`). `[observed]`
- The frozen source is **unchanged** by this investigation (no file written except this report). `[observed]`

---

## 4. Demo/Investor environment reconstruction

| Question | Finding | Label |
|---|---|---|
| What environment did it use? | Database `carbontally_demo_local` inside the developer's **local** Supabase stack (`127.0.0.1:54426`); lab gateway (nginx) at `127.0.0.1:54430`; release backend at `127.0.0.1:8070`. | `[documented]` `[code-traced]` |
| Local / disposable / persistent / production-connected? | **Local only. Disposable** (three lab containers prefixed `carbontally_demo_lab_`, a droppable DB). **Not production-connected.** | `[documented]` |
| How were identities provisioned? | `tools/demo_lab/provision.py` — idempotent, deterministic UUIDv5 ids, GoTrue admin API; manifest-driven. | `[code-traced]` |
| Supabase Auth users, application users, seeded records, or other? | **Real Supabase Auth (GoTrue) users** on the lab's local GoTrue, mirrored into the lab DB `auth.users` for FK integrity; plus app rows (orgs, memberships, staff profiles, consultant firm, client grants). | `[documented]` |
| Deterministic/test-only passwords? | **One locally generated synthetic password** for all lab actors; stored **outside the repo** (`~/ct_local_env/demo_lab/credentials.local.json`, mode 0600). | `[documented]` |
| Was Google OAuth used? | **No.** Every verification logged in via the **local GoTrue password grant** (`POST /auth/v1/token?grant_type=password`) or lab-issued session seeding. | `[documented]` `[code-traced]` |
| Which identities existed? | 14 actor entries (see §6). | `[observed]` |
| Which roles? | staff `admin`; staff `operator`; PE `pe_manager` (×2 entities); org `owner/admin/member/viewer`; consultant firm `owner`/`consultant`; client `owner`. | `[observed]` |
| Which organisations? | Org A, Org B, Client A, Client B (4 customer/client orgs) + 1 consultant firm + 2 processing entities. | `[observed]` |
| Which consultant/client relationships? | 1 firm (`Demo Lab Carbon Consultants`) with clients Client A and Client B; engagements present. | `[observed]` |
| Pre-seeded data? | Identities first (DEMO-T1); factors DEMO-T2-C (DEFRA-2025 7,029 + SEAI-2025 20 = **7,049**); corpus/scenarios DEMO-T3; later a real calculation (R-A `2469.16978 kg CO₂e`). | `[documented]` |
| Reusable across sessions? | **Yes** — idempotent; lab tokens/credentials persist in the state dir until `reset`. | `[documented]` |
| Explicit reset/rebuild mechanism? | **Yes** — `reset_demo_lab.sh` (+ `--purge-state`), `run_demo_lab.sh`. | `[documented]` |
| Safe for investor demos? | **Not established as such.** The DR series is a **demo-readiness investigation**; DR reports state passing is **not production authorization**. It is a local developer environment, never presented as the live investor surface. | `[documented]` |
| Ever intended for production acceptance? | **No.** README §1 "local only"; the lab never touches production or the investor dataset. | `[documented]` |

**Documentation conflict (recorded, not resolved):** `AGENTS.md` §54 names `tools/seed_investor_demo/DEMO_IDENTITIES.md` (~1,185 identities). **That directory does not exist in this checkout**; the real manifest is `tools/demo_lab/manifest.json`. This is recorded as `X-5` / **PO DECISION REQUIRED** in `CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md:192`. `[observed]` `[documented]`

---

## 5. Identity provisioning reconstruction

| # | Item | Finding |
|---|---|---|
| 1 | **Exact file/path** | `tools/demo_lab/provision.py` (mechanism) · `tools/demo_lab/manifest.json` (identity contract) · `tools/demo_lab/lab.py` (state dir, deterministic UUIDs, service key) · `tools/demo_lab/stack.py` (schema + containers) · `tools/demo_lab/run_demo_lab.sh` / `reset_demo_lab.sh` (orchestration). `[code-traced]` |
| 2 | **Mechanism** | Deterministic **UUIDv5** entity ids from manifest keys; auth users created/updated via the lab GoTrue admin API (matched by e-mail → same id reused); every write is an idempotent upsert. `[code-traced]` |
| 3 | **Actors produced** | 14 actor entries (§6) across customer roles, staff, PE, consultant, client. `[observed]` |
| 4 | **Relationships produced** | 4 orgs, 8+ `organization_members`, 1 consultant firm + firm members + client engagements, 2 processing entities, staff profiles + staff roles (`admin`, `operator`, `pe_manager`). `[code-traced]` |
| 5 | **Deterministic?** | **Yes** — deterministic ids + upsert; re-running updates the same rows. `[documented]` |
| 6 | **Resettable?** | **Yes** — `reset_demo_lab.sh`; `--purge-state` also clears credentials/evidence. `[documented]` |
| 7 | **Safe for investor demos?** | The infrastructure is repeatable and truthful, but the DR series explicitly frames passing as *not* production authorization; the **canonical investor surface is a PO decision** (`CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md`). **Not asserted as safe** here. `[documented]` |
| 8 | **Safe for FINAL-03 verification?** | **Yes for model/role/isolation behaviour** (local, disposable, no production contact). **No for production-specific facts** (§12). `[inference]` |
| 9 | **Production use supported or prohibited?** | **Prohibited / not supported.** The lab is local-only; the seeder hard-refuses any database name other than `carbontally_demo_local`; the investor dataset and production are explicitly never touched. `[documented]` `[code-traced]` |

**Staff-role seeding note `[code-traced]`:** `provision.py::ensure_staff_roles` seeds `admin` `{is_superuser, is_staff_admin, can_manage_organizations, can_manage_staff, can_review}`, `operator` `{can_process}`, `pe_manager` `{can_process, can_manage_team}` — using the release's own permission keys, no invented permissions ([`provision.py:101`](tools/demo_lab/provision.py:101)).

---

## 6. Actor matrix

Source: [`tools/demo_lab/manifest.json`](tools/demo_lab/manifest.json:21) (**14 actor entries**) `[observed]`. (README §3 and several reports cite **13 actors**; the manifest additionally contains `pe_beta_manager`, added for PE A/B isolation — a **documentation drift**.) No credentials are recorded anywhere in the manifest.

| Actor | Auth identity | Application role | Organisation | Consultant relationship | Expected landing | Provisioning method | Evidence |
|---|---|---|---|---|---|---|---|
| `platform_admin` | `platform.admin@demo-lab.carbontally.local` | staff `admin` | internal (platform) | — | `/ops` | provision.py (GoTrue + staff_profiles) | `[observed]` |
| `internal_operator` | `operator@…` | staff `operator` | internal staff | — | `/ops` | provision.py | `[observed]` |
| `pe_manager` | `pe.manager@…` | staff `pe_manager` | Processing Entity **Alpha** | — | `/pe` | provision.py | `[observed]` |
| `pe_beta_manager` | `pe.beta.manager@…` | staff `pe_manager` | Processing Entity **Beta** | — | `/pe` | provision.py | `[observed]` |
| `org_a_owner` | `owner.a@…` | customer `owner` | Org A | — | `/home` | provision.py | `[observed]` |
| `org_a_admin` | `admin.a@…` | customer `admin` | Org A | — | `/home` | provision.py | `[observed]` |
| `org_a_member` | `member.a@…` | customer `member` | Org A | — | `/home` | provision.py | `[observed]` |
| `org_a_viewer` | `viewer.a@…` | customer `viewer` | Org A | — | `/home` | provision.py | `[observed]` |
| `org_b_owner` | `owner.b@…` | customer `owner` | Org B | — | `/home` | provision.py | `[observed]` |
| `org_b_viewer` | `viewer.b@…` | customer `viewer` | Org B | — | `/home` | provision.py | `[observed]` |
| `consultant_owner` | `consultant.owner@…` | consultant firm `owner` | firm `Demo Lab Carbon Consultants` | firm holder | `/consultant` | provision.py | `[observed]` |
| `consultant_member` | `consultant.member@…` | consultant firm `consultant` (all `can_*` flags **false**) | firm | least-privilege member | `/consultant` | provision.py | `[observed]` |
| `client_a_owner` | `owner.clienta@…` | customer `owner` | Client A | consultant-managed client | `/home` | provision.py | `[observed]` |
| `client_b_owner` | `owner.clientb@…` | customer `owner` | Client B | consultant-managed client | `/home` | provision.py | `[observed]` |

**Browser-verified actors `[browser]`:** `org_a_owner` (DR-002/003/004/006/007), `consultant_owner` and `client_a_owner` (DR-005). All via the **real `/login` form, password grant** — **no Google OAuth**.

---

## 7. FINAL-03 BLK-2 mapping

Legend — **DL** = Demo-Lab provable (behaviour/model); **PS** = Production-specific (cannot be proven by Demo Lab).

| FINAL-03 criterion | Auth actor? | Required actor type | Demo actor available? | Demo env sufficient? | Production verification still required? | Reason |
|---|---|---|---|---|---|---|
| successful login (password) | Yes | customer | **Yes** (`org_a_owner`) | **DL** | Yes (prod Supabase Auth config) | password grant path is the same code; prod auth config differs |
| logout / re-login | Yes | customer | **Yes** | **DL** | Yes (prod session config) | session mechanics identical; prod env differs |
| session persistence | Yes | customer | **Yes** | **DL** | Yes | localStorage session; prod origin/storage differs |
| `/auth/callback` | Yes | OAuth/email | Has route, but **no OAuth tested** | **PS** | **Yes** | lab uses password grant; callback not exercised for OAuth |
| `GET /api/v3/me/context` | Yes | all actors | **Yes** (all 14) | **DL** | Yes (prod backend/config) | same resolver code |
| correct role landing | Yes | all | **Yes** (staff/PE/consultant/customer) | **DL** | Yes | routing decided server-side; same code |
| D1, D2 (own-data only) | Yes | 2 customers | **Yes** (org A vs org B; client A vs client B) | **DL** | **Yes (prod RLS/schema)** | lab schema revision ≠ production |
| D3 (cross-org denied) | Yes | 2 customers | **Yes** | **DL** | **Yes** | as above |
| D4 (id/path/query substitution) | Yes | 1 customer | **Yes** | **DL** | **Yes** | as above |
| D5 (cross-tenant storage) | Yes | 2 customers | **Partial** (lab storage container, synthetic docs) | **DL partial** | **Yes (prod bucket)** | prod bucket = `documents`, 58 objects |
| E1 (internal staff) | Yes | staff | **Yes** (`platform_admin`, `internal_operator`) | **DL** | Yes | same `require_staff` chain |
| E2 (consultant/client) | Yes | consultant | **Yes** (`consultant_owner`) | **DL** | Yes | same consultant chain |
| E3 (consultant isolation) | Yes | 2 consultants/firms | **Partial** (1 firm; 2 client owners) | **DL partial** | **Yes** | only one firm → cross-firm isolation not covered |
| E4 (owner isolation) | Yes | 2 owners | **Yes** | **DL** | Yes | — |
| E6 (suspended access) | Yes | suspendable actor | **No** (requires mutation) | **PS / mutation** | **Yes** | toggling a state is a mutation |
| G1/G2/G5 (storage) | Yes | customer + object | **Partial** | **DL partial** | **Yes (prod bucket)** | lab storage ≠ prod storage |
| I (calculation/report) | Yes | customer | **Yes** (R-A already real) | **DL (behaviour)** | **Yes (prod data)** | prod run would create commercial data |
| J (email) | Yes | customer + recipient | **No** (no prod provider in lab) | **PS** | **Yes** | provider/recipient are production |

**Distinction applied:** Demo Lab can prove **behaviour/model/boundaries** (same release code); it **cannot** certify **production RLS posture, production storage, production OAuth, production email, production routing/origins**. Equivalence evidence is not claimed where the architecture/deployment path does not make it demonstrable.

---

## 8. Production identity assessment

Established by `CSTR-FINAL03-BLK2-TEST-IDENTITY-READINESS-20261003` (read-only) `[observed]`:

| Aggregate | Value |
|---|---|
| organisations | 2 (Babui Technologies UK Limited, Faria Green Company UK LTD — both active) |
| `auth.users` | 2 (1 `email` provider, 1 `google` provider; both confirmed, not banned) |
| `organization_members` | 2 (both `owner`, active) |
| `consultant_profiles` / `consultant_firm_members` / `consultant_clients` | **0 / 0 / 0** |
| `processing_entities` | **0** |
| `staff_profiles` (total/active) | **0 / 0** |
| `staff_roles` | 1 (`pe_manager`) |

**Conclusion:** the two existing owner identities can satisfy **only the customer/tenant/storage subset** (and would need their runtime credential). **All staff (`/ops`), consultant (`/consultant`) and PE (`/pe`) criteria remain blocked solely because no such identity exists in production — and no usable test credential is present in the workspace.** `[observed]` `[inference]`

---

## 9. Current sign-in-stall forensic trace ("Completing sign in... Please wait while we verify your account")

**Exact source:** [`frontend/src/AuthCallback.js:111-116`](frontend/src/AuthCallback.js:111) — the component's **initial/default render** (no session handling has completed yet). `[code-traced]`

**Sequence traced (all `[code-traced]`):**

| Step | Where | Finding |
|---|---|---|
| `/login` | `Login.js` | renders; password `signInWithPassword` **or** Google `signInWithOAuth` |
| OAuth initiation | [`Login.js:189`](frontend/src/Login.js:189) | `signInWithOAuth({provider:'google', options:{redirectTo}})` |
| `/auth/callback` reached? | `App.js` route `/auth/callback` → `AuthCallback` | **Yes** (the component renders; the reported text proves the route resolved) |
| loading state shown | [`AuthCallback.js:111`](frontend/src/AuthCallback.js:111) | the reported string |
| session check | [`AuthCallback.js:23`](frontend/src/AuthCallback.js:23) | `await supabase.auth.getSession()` — **no timeout** |
| retry | [`AuthCallback.js:51`](frontend/src/AuthCallback.js:51) | 2 s wait, second `getSession()` — **no timeout** |
| success path | [`AuthCallback.js:40`](frontend/src/AuthCallback.js:40) | `await goToWorkspace(navigate)` → `navigate(destination)` → component unmounts |
| failure path | [`AuthCallback.js:43`](frontend/src/AuthCallback.js:43) | `setError('Failed to load your workspace. Please try again.')` → **error screen** ([`:102`](frontend/src/AuthCallback.js:102)) |
| infra path | [`AuthCallback.js:74`](frontend/src/AuthCallback.js:74) | `setServiceUnavailable('callback')` → branded notice |
| `/me/context` call | [`api.js:110`](frontend/src/v3/api.js:110) `getMeContext` → `v3Fetch('/api/v3/me/context')` | **bounded by a 25 s timeout** ([`api.js:17`](frontend/src/v3/api.js:17), AbortController) |

**Answers to §F questions (1–16):**

1. **What condition causes it?** The component's default render — i.e. the callback effect has not yet **settled** (no success-navigate, no `setError`, no `setServiceUnavailable`). `[code-traced]`
2. **What event clears it?** `navigate(destination)` (success), `setError(...)` (callback failure), or `setServiceUnavailable(...)` (infra failure). `[code-traced]`
3. **What causes redirect?** On success `goToWorkspace` navigates; on failure the error screen auto-redirects to `/login` after 2 s ([`:29`](frontend/src/AuthCallback.js:29), [`:81`](frontend/src/AuthCallback.js:81), [`:66`](frontend/src/AuthCallback.js:66)). `[code-traced]`
4. **Is the callback reached?** **Yes** — the reported text is that component's default render. `[code-traced]` `[inference]`
5. **Does a session exist after callback?** **Not determinable read-only** on production. `[limitation]` `NOT OBSERVABLE FROM CURRENT READ-ONLY ACCESS`
6. **Is `/api/v3/me/context` called?** Only **after** a session is found ([`AuthCallback.js:33-40`](frontend/src/AuthCallback.js:33)). If the stall is before step 5, it is **not** called. `[code-traced]`
7. **Expected response?** `200` with `{actor_type, destination, …}` ([`v3_context.py:34`](backend/api/v3_context.py:34)). `[code-traced]`
8/9/10/11/12. **On 401 / 403 / 500 / org-resolution failure / role-resolution failure?** All surface through `v3Fetch`'s status mapping ([`api.js:21-33`](frontend/src/v3/api.js:21)); 500 → the resolver's fail-closed `HTTP 500` ([`v3_context.py:19`](backend/api/v3_context.py:19)); every such case **rejects `goToWorkspace` → the ERROR branch**, i.e. *"Failed to load your workspace…"*, **not** the stall. `[code-traced]`
13. **Supabase Auth configured correctly in source?** The client uses the hard-coded fallback URL/key if env is absent ([`supabaseClient.js:5`](frontend/src/supabaseClient.js:5)); `detectSessionInUrl` default is used; **no explicit flow type / `exchangeCodeForSession` handling exists in `AuthCallback`** (it relies solely on `getSession()`). `[code-traced]`
14. **Are production env vars required?** The frontend has a fallback; the backend needs `SUPABASE_URL`/keys. Production values are **not observable** here. `[limitation]`
15. **Is production URL/origin/redirect involved?** Yes — `redirectTo` derives from `window.location.origin` unless `REACT_APP_OAUTH_REDIRECT_URL` overrides ([`Login.js:199`](frontend/src/Login.js:199)). `[code-traced]`
16. **Classification of the problem:** **The string's source and clearing logic are frontend (`[code-traced]`). The live trigger is likely one of: (a) a hang in `getSession()`/`detectSessionInUrl` (the only unbounded path), or (b) an OAuth/PKCE configuration mismatch at the Supabase project (not observable). Frontend-only vs auth-provider configuration is NOT determinable read-only.** → **PARTIALLY EXPLAINED.**

**Key structural finding `[inference]`:** every workspace-resolution failure is **bounded** (25 s abort → the **error** screen), so a *persistent* "Completing sign in…" cannot be produced by the `/me/context` leg. The **only unbounded leg** is the initial/retry `supabase.auth.getSession()` (no timeout). This is the single most probable mechanism for an indefinite stall.

---

## 10. Google OAuth trace

| Check | Finding | Label |
|---|---|---|
| Google client ID references | `REACT_APP_GOOGLE_CLIENT_ID` is only **logged** ([`Login.js:203`](frontend/src/Login.js:203)); the actual OAuth client is the **Supabase project's** provider config | `[code-traced]` |
| OAuth initiation | `supabase.auth.signInWithOAuth({provider:'google'})` ([`Login.js:207`](frontend/src/Login.js:207)) | `[code-traced]` |
| Redirect URL source | `REACT_APP_OAUTH_REDIRECT_URL || ${window.location.origin}/auth/callback` ([`Login.js:199`](frontend/src/Login.js:199)) | `[code-traced]` |
| Expected callback | **`https://carbontally.co.uk/auth/callback`** (origin-derived) unless overridden | `[code-traced]` `[inference]` |
| `/auth/callback` route | present (`App.js:1974`) | `[code-traced]` |
| `www.carbontally.co.uk` / alternate hosts / Vercel hostnames | No alternate callback host is referenced in source; the origin is dynamic | `[code-traced]` |
| Supabase OAuth provider config / allowed redirect URLs / Google Cloud config | **NOT OBSERVABLE FROM CURRENT READ-ONLY ACCESS** | `[limitation]` |
| Was OAuth ever exercised in Demo Lab? | **No** — all DR logins are password grant | `[documented]` |

**Historical OAuth symptom ("Failed to load your workspace…"):** located in the **same callback/error path** (`AuthCallback.js:43`, `Login.js:45/78/104`, `MagicLink.jsx:69`, `SelfServiceSignup.jsx:58`, `BetaSignup.jsx:150`) — emitted whenever `goToWorkspace()` **rejects**. `[code-traced]` A previously identified local root-cause candidate: `backend/.env` `SUPABASE_URL=http://127.0.0.1:19999` (dead port) → token validation fails → `/me/context` 500 → the workspace error ([`CT-PO-CT-READINESS-02-…-REPORT.md:88-89`](docs/architecture/CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927-REPORT.md:88)). That is a **local configuration** cause; the **production** cause is not established. `[documented]` `[inference]`

---

## 11. Relationship between the two authentication symptoms

| | Symptom A (current) | Symptom B (historical/Google) |
|---|---|---|
| Text | "Completing sign in... Please wait while we verify your account" | "Failed to load your workspace. Please try again." + "Redirecting to login..." |
| Source | `AuthCallback` **loading** branch ([`:111`](frontend/src/AuthCallback.js:111)) | `AuthCallback` **error** branch ([`:102`](frontend/src/AuthCallback.js:102)) with `error` set at [`:43`](frontend/src/AuthCallback.js:43) |
| Failure locus | **session resolution** (before `/me/context`) | **workspace resolution** (`goToWorkspace` rejected, after session) |
| Bounded? | **No** (the `getSession()` leg has no timeout) | **Yes** (25 s `v3Fetch` abort; 401/403/5xx mapping) |

**Determination:** A and B are **mutually exclusive render branches of the same component** — they **cannot co-occur**, so B does not cause A within a single render, and A does not cause B. They are **distinct symptoms at different stages** (pre-session vs post-session). Whether they share a root cause (e.g. the same Supabase auth misconfiguration) is **NOT ESTABLISHED** — **evidence insufficient**. `[code-traced]` `[inference]`

---

## 12. Demo Lab vs production equivalence assessment

| # | Dimension | Equivalent? | Basis |
|---|---|---|---|
| 1 | Authentication implementation | **Same code**, different provider instance | `[code-traced]` |
| 2 | Frontend build | **Same source**; lab runs the CRA dev server, prod runs the Vercel build | `[documented]` |
| 3 | Backend/API build | **Same release backend**; lab instance vs Render | `[documented]` |
| 4 | Supabase Auth configuration | **Different** — local GoTrue, password grant, **no Google OAuth**, different redirect URLs | `[documented]` |
| 5 | RLS / schema | **Different revision** — lab schema is stale / assembled by `stack.py` (136–141 tables); prod = 150 tables, 98 migrations | `[documented]` |
| 6 | Storage behaviour | **Different** — lab container/volume vs prod private `documents` bucket (58 objects) | `[documented]` |
| 7 | Role/permission equivalence | **Equivalent** — same `staff_roles.permissions` / org-role / consultant-flag / PE-role model | `[code-traced]` |
| 8 | Organisation/consultant relationships | **Equivalent model** (lab has them; prod has **none**) | `[observed]` |
| 9 | Production-specific config dependencies | **Not equivalent** — prod needs hosted Supabase keys/URLs, CORS allow-list, Render env | `[documented]` |
| 10 | Email provider | **Not equivalent** — lab has none; prod provider is production-only | `[documented]` |
| 11 | OAuth | **Not equivalent** — lab never used OAuth | `[documented]` |
| 12 | Environment variables | **Not equivalent** | `[documented]` |
| 13 | Deployment-specific routing | **Not equivalent** — lab dev-server vs Vercel rewrites | `[documented]` |

**Conclusion (factual, per §D): PARTIALLY SUFFICIENT.** The Demo Lab is **sufficient** to prove **role/routing/isolation behaviour** and to exercise staff/consultant/PE actors that production lacks; it is **insufficient** to certify any **production-specific** fact (production RLS on the production schema, production storage, production OAuth, production email, production routing/origins, production tenant data).

---

## 13. Safe acceptance model (proposed — NOT implemented)

### Environment 1 — Demo / Investor Lab (`tools/demo_lab/`, local, disposable)
- **Actor identities:** the 14 manifest actors (staff, PE ×2, consultant owner/member, client owners, 4 org-A roles, 2 org-B roles). `[documented]`
- **Tenant data:** lab orgs A/B + Client A/B, synthetic corpus, 7,049 factors, R-A calculation. `[documented]`
- **Test scope (safe here):** C (password login/logout/relogin/session/`me/context`/role-landing), **D1–D5**, **E1/E2/E4** (and E3 partially), **I** (behaviour), storage **behaviour** (G1/G2/G5 partially). `[inference]`
- **Expected evidence:** `verify.py` output (actor contexts + ALLOW/DENY probes), browser screenshots, evidence JSON. `[documented]`
- **Limitations:** **no OAuth**, lab schema ≠ production, lab storage ≠ production, single consultant firm, E6 needs a mutation. `[limitation]`

### Environment 2 — Production
- **Actor identities:** the **2 existing owner identities** (runtime credentials) — customer/tenant/storage subset only. `[observed]`
- **Tenant data:** the preserved 2 orgs (Babui 3 files/0 evidence; Faria 8 files/74 evidence). `[documented]`
- **Test scope (must remain production-specific):** production **OAuth** + `/auth/callback` + `/me/context` for the two owners, production **RLS** behaviour on the production schema, production **storage** authorisation, production **email** (J), production **routing/origins**. `[inference]`
- **Expected evidence:** authenticated browser flows, API status codes, storage authorisation. `[inference]`
- **Limitations:** no staff/consultant/PE identity exists; authenticated acceptance cannot run without a PO-authorized identity. `[observed]`

### Environment 3 — Disposable verification environment (if needed)
- **Actor identities:** a *disposable* Supabase/local environment provisioned with staff/consultant/PE actors **if** a combination must be tested that cannot safely be created in production and is not model-provable in the Demo Lab. `[inference]`
- **Tenant data:** synthetic only; **never** the investor dataset or production. `[documented]`
- **Test scope:** any actor combination the Demo Lab lacks (e.g. two consultant firms for E3) — **model-level** only. `[inference]`
- **Limitations:** still cannot certify production-specific facts. `[inference]`

**No environment is implemented by this task.**

---

## 14. Admin `/ops` relationship

- `CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md` (**D-P2-02**) ratifies **`/ops` as the canonical staff surface**; legacy `/admin` is **deprecated, not deleted** ([`…:80`](docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md:80)). `[documented]`
- The **Demo Lab provisions a staff actor** — `platform_admin` (staff `admin`) and `internal_operator` (staff `operator`) — each with `expect.destination = "/ops"` ([`manifest.json:28`](tools/demo_lab/manifest.json:28), [`:36`](tools/demo_lab/manifest.json:36)). `[observed]`
- `verify.py` asserts the staff/ops plane AND the denials around it ([`README.md:76`](tools/demo_lab/README.md:76)). `[documented]`
- **Therefore Demo Lab CAN help verify canonical `/ops` *behaviour*** (staff → `/ops`; ops-plane ALLOW/DENY). **It is NOT proof that production `/ops` is currently functional** — production `/ops` has **no staff identity to exercise it**, and Demo-Lab evidence is separate from production. `[inference]`
- The deprecated `/admin` surface remains a **separate production item** (BLK-1, now cleared per the post-remediation verification) and is **not** the canonical staff acceptance target. `[documented]`

---

## 15. Findings

| # | Finding | Label |
|---|---|---|
| F-1 | The repository's real demo environment is the local, disposable **Demo Lab** (`tools/demo_lab/`), not the absent `tools/seed_investor_demo/` dataset. | `[observed]` `[documented]` |
| F-2 | Demo Lab provisioner yields **14 role-bearing actors** incl. staff (`/ops`), consultant (`/consultant`), PE (`/pe`) — the exact actors production lacks. | `[observed]` |
| F-3 | Demo Lab auth is **local GoTrue password grant only**; **OAuth was never exercised** there. | `[documented]` |
| F-4 | "Completing sign in…" is the `AuthCallback` **default render**; its **only unbounded leg** is `getSession()` (no timeout); the `/me/context` leg is bounded at 25 s. | `[code-traced]` `[inference]` |
| F-5 | "Failed to load your workspace…" is the `AuthCallback` **error branch** (bounded), emitted when `goToWorkspace()` rejects. | `[code-traced]` |
| F-6 | The two symptoms are **mutually exclusive branches** of one component → **distinct**, not causally linked on available evidence. | `[code-traced]` |
| F-7 | Production holds **only 2 customer owners**; **zero staff/consultant/PE** identities. | `[observed]` |
| F-8 | Demo Lab provides **model/role/isolation** coverage but **not production equivalence** (auth/schema/RLS/storage/OAuth/email/routing). | `[inference]` |
| F-9 | `AGENTS.md` §54 names a **non-existent** demo tooling directory (X-5) — a documentation/decision conflict. | `[observed]` `[documented]` |

## 16. Blocking findings

| # | Finding | Impact |
|---|---|---|
| B-1 | **No authorized production identity is available in the workspace**, and production has no staff/consultant/PE identity, so the FINAL-03 authenticated criteria (C, D authenticated, E, G authenticated, I, J) **cannot be executed in production**. | FINAL-03 authenticated acceptance remains **blocked**. `[observed]` |
| B-2 | The **production sign-in stall** ("Completing sign in…") is **unresolved**; its source and unbounded leg are code-traced, but the **live trigger is not observable read-only** and no production browser/session was available. | An **open authentication regression** must be treated as blocking until independently explained. `[limitation]` |

## 17. Non-blocking findings

| # | Finding | Note |
|---|---|---|
| N-1 | Demo Lab manifest has **14 actors** (incl. `pe_beta_manager`) while README/reports cite **13**. | documentation drift `[observed]` |
| N-2 | Demo Lab schema is a **stale revision** (no/partial Insight tables) vs production (150 tables, 98 migrations). | limits equivalence `[documented]` |
| N-3 | `AGENTS.md` §54 / `.gitignore` still reference the absent `tools/seed_investor_demo/` (X-5). | PO decision `[documented]` |
| N-4 | `AuthCallback` never calls `exchangeCodeForSession`; it relies on `getSession()`/`detectSessionInUrl`. | a PKCE-flow mismatch would land in the **error** branch, not the stall `[code-traced]` |
| N-5 | Demo Lab auth CORS gap was fixed in DR-003; earlier DR-002 login failed at the network layer. | historical `[documented]` |

## 18. Unknown / unobservable items

1. Production Supabase OAuth provider configuration, allowed redirect URLs, and Google client config. — **NOT OBSERVABLE FROM CURRENT READ-ONLY ACCESS**
2. Live production session/callback behaviour in a real browser (no credential/session). — **NOT OBSERVABLE**
3. Whether a production session exists after the callback. — **NOT OBSERVABLE**
4. Production `REACT_APP_OAUTH_REDIRECT_URL` / Vercel env values. — **NOT OBSERVABLE**
5. Whether `www.carbontally.co.uk` is used as a callback host. — **NOT OBSERVABLE**
6. Which dataset the demo narrative uses (X-5 / D-A). — **PO DECISION REQUIRED**

## 19. Exact evidence paths

`docs/demo-investor/DR-001-frontend-customer-journey-verification.md` · `DR-002-frontend-runtime-browser-verification.md` · `DR-003-demo-lab-cors-browser-verification.md` · `DR-004-r-a-deep-browser-verification.md` · `DR-005-remaining-investor-workflow-verification.md` · `DR-006-report-refresh-verification.md` · `DR-007-investor-defect-triage-and-remediation.md` · `tools/demo_lab/manifest.json` · `tools/demo_lab/provision.py` · `tools/demo_lab/README.md` · `frontend/src/AuthCallback.js` · `frontend/src/Login.js` · `frontend/src/v3/api.js` · `frontend/src/v3/components/RoleRoute.jsx` · `frontend/src/App.js` · `backend/api/v3_context.py` · `docs/architecture/CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md` · `docs/architecture/CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927-REPORT.md` · `docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md` · `docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md` · `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md` · `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/**` · `docs/audit/costrict/CSTR-FINAL03-LIVE-ACCEPTANCE-001-20261003.md` · `CSTR-FINAL03-BLK2-TEST-IDENTITY-READINESS-20261003.md`.

## 20. Recommended next decision for PO

**One factual decision point (not implemented):** decide **which environment is authorised to carry the remaining FINAL-03 authenticated acceptance** — and, if the production half is to proceed, **authorise a controlled production acceptance identity set** (per `CSTR-FINAL03-BLK2-TEST-IDENTITY-READINESS-20261003` §H: 2 existing owners for the customer subset + 3 minimal controlled staff/consultant/PE identities, anchored to the existing organisations, runtime-only credentials), **and** separately decide whether the **Demo Lab** is accepted as the evidence environment for the non-production-specific criteria. Separately, the **open production sign-in regression** (§16 B-2) requires a decision on how to obtain production-side observability (a browser session) before it can be explained.

**No implementation is recommended or performed.**

---

## VERDICTS

## DEMO / INVESTOR ENVIRONMENT

**PARTIALLY SUFFICIENT**

The Demo Lab is a **local, disposable, repeatable** environment with **14 role-bearing actors** — including the staff/consultant/PE actors production lacks — and the **same release code**. It is **sufficient** to prove **role/routing/isolation behaviour** (C password path, D, E1/E2/E4, G behaviour, I behaviour). It is **insufficient** to certify **production-specific** facts: production RLS on the production schema, production storage, production Google OAuth, production email, production routing/origins and production tenant data. (Authentication-provider, schema-revision, storage, OAuth, email and environment-variable differences are each non-equivalent — §12.)

## IDENTITY PROVISIONING

**AVAILABLE**

A documented, deterministic, idempotent and resettable mechanism exists — `tools/demo_lab/provision.py` driven by `tools/demo_lab/manifest.json` — producing the full actor set (customer roles, staff, PE ×2, consultant firm owner/member, client owners). It is **lab-local by design** (production use is prohibited) and its staff-role seeding uses the release's own permission keys. The *same pattern* is reproducible in a disposable/non-production environment.

## FINAL-03 BLK-2

**PARTIALLY RESOLVED**

The Demo Lab can cover the **non-production-specific** criteria (behaviour/model/isolation, incl. staff/consultant/PE). The following criteria **remain blocked** in production: **C1/C2/C5/C6 authenticated production login**, **D1–D5 authenticated production isolation**, **E1–E4/E6 production role boundaries**, **G1/G2/G5 production storage authorisation**, **I production calculation/report**, and **J production email** — all blocked by **no authorized production test identity** (and, for staff/consultant/PE, no identity at all) and, for I/J, by the prohibition on creating commercial/email artefacts.

## PRODUCTION SIGN-IN

**PARTIALLY EXPLAINED**

Evidence: the string is the **`AuthCallback` default render** ([`AuthCallback.js:111`](frontend/src/AuthCallback.js:111)); it clears only on `navigate`, `setError`, or `setServiceUnavailable`; the `/me/context` leg is **bounded at 25 s** ([`api.js:17`](frontend/src/v3/api.js:17)) and any failure there produces the **error** screen, not the stall; the **initial/retry `getSession()` calls are unbounded** ([`AuthCallback.js:23`](frontend/src/AuthCallback.js:23), [`:51`](frontend/src/AuthCallback.js:51)) → the only path that can persist the stall. The **production-specific trigger** (session hang vs Supabase OAuth/PKCE configuration vs network) is **NOT OBSERVABLE** read-only.

## GOOGLE AUTH REGRESSION

**PARTIALLY EXPLAINED**

Evidence: "Failed to load your workspace. Please try again." is emitted wherever `goToWorkspace()` **rejects** ([`AuthCallback.js:43`](frontend/src/AuthCallback.js:43), [`Login.js:45`](frontend/src/Login.js:45), `MagicLink.jsx:69`, `SelfServiceSignup.jsx:58`, `BetaSignup.jsx:150`); the OAuth initiation and its redirect expectation are code-traced ([`Login.js:189`](frontend/src/Login.js:189), [`:199`](frontend/src/Login.js:199) → `https://carbontally.co.uk/auth/callback`); a previously documented **local** cause was a dead `SUPABASE_URL` port → `/me/context` 500 ([`CT-PO-CT-READINESS-02-…-REPORT.md:88`](docs/architecture/CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927-REPORT.md:88)). The **production** OAuth configuration and behaviour are **NOT OBSERVABLE FROM CURRENT READ-ONLY ACCESS**.

---

**NO PRODUCTION IDENTITIES, DATA, DATABASE RECORDS, STORAGE OBJECTS, CREDENTIALS, AUTHENTICATION SETTINGS, OR APPLICATION CODE WERE CREATED OR MODIFIED.**
**NO DEMO LAB DATA WAS MODIFIED, RESET OR RESEEDED.**

**READY FOR PO REVIEW — BLK-2 DEMO/INVESTOR RECONCILIATION AND SIGN-IN FORENSICS COMPLETE — NO REMEDIATION PERFORMED**
