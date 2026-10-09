# CSTR-CARBONTALLY-ENVIRONMENT-RECON-001 — Three-Environment Operating-Model Reconciliation

**Report ID:** CSTR-CARBONTALLY-ENVIRONMENT-RECON-001-20261003
**Date:** 2026-10-03
**Agent:** CoStrict (independent verification/audit) — **READ-ONLY RECONCILIATION**
**Branch:** `p8-release-reconciled` · frozen release `375a48dc1b9e9cfd74090bbf747554ae997acb59`
**Type:** Reconstruction + gap register. **No remediation.** Nothing modified.

**Evidence labels:** `[observed]` · `[code-traced]` · `[documented]` · `[runtime]` · `[browser]` · `[inference]` · `[limitation]`
**State labels:** CURRENT/RATIFIED · IMPLEMENTED · VERIFIED · HISTORICAL/SUPERSEDED · OPEN · BLOCKED · DEFERRED · NOT YET AUTHORIZED.

---

## 1. Source-of-truth reconstruction

| Source | Content | Classification | Note |
|---|---|---|---|
| `AGENTS.md` | Project constitution; §5 topology (Render/Vercel/Supabase); §54 demo identities; §85 workflow | **CURRENT/RATIFIED** | §54 names `tools/seed_investor_demo/DEMO_IDENTITIES.md` which is **absent** (see X-5) — stale reference |
| `docs/architecture/CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md` | Canonical Demo Lab environment record | **CURRENT/RATIFIED (canonical-env record)** | `[documented]` |
| `docs/architecture/CT-PO-COMPREHENSIVE-INVESTOR-READY-PLATFORM-STUDY-20260924.md` §H | Canonical investor-demo environment recommendation | **CURRENT/RATIFIED (recommendation)** | "freshly provisioned Demo Lab on the current release schema" `[documented]` |
| `docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md` | D-P2-02 `/ops` canonical, `/admin` deprecated | **CURRENT/RATIFIED** | `[documented]` |
| `docs/architecture/CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md` | Production auth/access matrix | **CURRENT/RATIFIED** | `[documented]` |
| `docs/demo-investor/DR-001…DR-007` | Investor/demo browser verification records | **HISTORICAL evidence (2026-09-20/21)** at older SHAs | `[browser]` |
| `docs/architecture/CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927-REPORT.md` | Real-readiness baseline (local DB empty, demo not loaded) | **CURRENT-ish snapshot (2026-09-27)** | `[documented]` |
| `docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md` | Database instance census | **CURRENT snapshot (2026-09-27)** | `[documented]` |
| `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md` | Capability census; ISS-001 Google-auth regression; X-5 | **CURRENT snapshot (2026-09-26)** | `[documented]` |
| `docs/audit/costrict/CSTR-FINAL03-*` | FINAL-03 independent verification series | **CURRENT (2026-10-03)** | `[observed]` |
| `docs/RECONSTRUCTED_TASK_HISTORY.md`, `docs/Todos.md` | Task history / todo lists | **HISTORICAL — do not treat as current** | per task instruction `[documented]` |
| `tools/demo_lab/*` | Demo Lab tooling | **IMPLEMENTED + (historically) VERIFIED** | `[code-traced]` |

**Conflict policy applied:** where documents disagree, both are reported and the later/ratified source is identified. Documented conflicts found: **X-5** (AGENTS §54 vs actual `tools/demo_lab/manifest.json`), the **13-vs-14 actor** drift, and the **Demo Lab schema revision** drift (§4).

---

## 2. Original three-environment intent

### A. Local environment (intent)
The constitution defines a **local-first, inspect-verify-implement-test** workflow (`AGENTS.md` §82–§85). The **canonical local environment is the Demo Lab** (`carbontally_demo_local` on the developer's local Supabase stack + a release backend on `:8070`), intended to let the owner run **real, role-bearing** actors through the full pipeline. `[documented]`

**Actually supported locally (evidence):**
- **Supported (`[documented]`/`[code-traced]`):** password login; all customer roles; consultant owner/member; PE manager; internal staff `admin`/`operator`; document upload/processing; extraction; mapping; **factor matching** (7,049 factors); **calculation** (R-A `2469.16978 kg CO₂e` real); evidence; review; **customer approval boundary**; reports; report refresh; `/ops` staff plane; tenant isolation. `[documented]` `[browser]`
- **Merely intended / not demonstrated locally:** Google OAuth (**never used in the lab**); billing flows (`customer_subscriptions=0`); non-DRAFT report lifecycle (all `DRAFT`); full PE Alpha↔Beta isolation (single entity at verification time); customer↔support messaging (needs `can_manage_staff`). `[documented]`

### B. Live production environment (intent → deployed)
- **Intended topology** (`AGENTS.md` §5): React on Vercel · FastAPI on Render · Supabase (Auth/DB/Storage/Realtime) · Resend email. `[documented]`
- **Deployed/verified (`[observed]`, `CSTR-FINAL03-*`):** Render API healthy (623 paths/742 ops); Vercel serves the main SPA (`/`) **and** the legacy `/admin`; production Supabase migrated (150 tables / 147 RLS-on / 235 policies / 98 migrations); `/ops` is the canonical staff surface; legacy `/admin` **deprecated but mounted** and now initialises (BLK-1 cleared); Google OAuth enabled but **not production-verified**; production has **2 orgs + 2 owner identities only** (no staff/consultant/PE). `[observed]`
- **Explicit:** production deployment of the FINAL-03 release is authorised/completed; production **acceptance** is **NOT granted** (BLK-2 open). `[documented]`

### C. Investor Demo environment (intent → implemented)
- **Intent** (`CT-PO-COMPREHENSIVE-INVESTOR-READY-PLATFORM-STUDY` §H): a **freshly provisioned Demo Lab on the current release schema**, reproducible, with the historical `postgres` dataset retained **read-only** as reference. `[documented]`
- **Implementation:** `tools/demo_lab/` **is** the implementation of that intent (`[inference]` supported by `CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md`). Canonical identity: `carbontally_demo_local`, gateway `127.0.0.1:54430`, backend `127.0.0.1:8070`, 81 migrations / 141 tables / 6 Insight tables / 298 policies, 14 actors. `[documented]`
- **Status:** identity + factor + corpus foundation **IMPLEMENTED and historically VERIFIED**; **not** declared investor-ready (see §11). `[documented]`

---

## 3. Environment matrix

Tokens: `I`=Implemented · `V`=Verified (behaviour) · `PV`=Production Verified · `DV`=Demo-Lab Verified · `—`=absent · `?`=unknown/not observable.

| Capability | Local (Demo Lab) | Live Production | Investor Demo (intended) | Status | Evidence |
|---|---|---|---|---|---|
| authentication (password) | **I V DV** | **I PV** (2 owners) | **I DV** | CURRENT | `[documented]` `[browser]` |
| Google OAuth | **—** (never used) | **I**, not verified | **—** | OPEN | `[documented]` |
| onboarding | I (route exists) | I (not exercised) | I | IMPLEMENTED | `[code-traced]` |
| post-login routing (`/me/context`) | **I V DV** (13/13 contexts) | **I PV** | **I DV** | CURRENT | `[documented]` |
| customer workspace | **I V DV** | I (2 owners) | **I DV** | CURRENT | `[browser]` |
| consultant workspace | **I V DV** | **—** | **I DV** | CURRENT | `[browser]` |
| Processing Entity workspace | **I V DV** | **—** | I (2 entities now) | IMPLEMENTED/partially | `[documented]` |
| CarbonTally Staff `/ops` | **I V DV** (context) | I (no staff identity) | I (staff actors) | IMPLEMENTED; **not browser-verified** | `[documented]` |
| legacy `/admin` | — (lab has none) | I (deprecated, fixed) | not required | DEPRECATED | `[documented]` |
| organisations | **I DV** (4) | **I PV** (2) | I (4) | CURRENT | `[observed]` |
| memberships | **I DV** (8) | **I PV** (2) | I | CURRENT | `[observed]` |
| document upload | **I V DV** | I (not authenticated) | I | IMPLEMENTED | `[documented]` |
| document processing | **I V DV** | I (worker live) | I | CURRENT | `[documented]` |
| extraction | **I V DV** | I | I | CURRENT | `[browser]` |
| mapping | **I V DV** | I | I | CURRENT | `[browser]` |
| factor matching | **I V DV** (7,049) | **I PV** (7,049) | I | CURRENT | `[observed]` |
| calculation | **I V DV** (R-A real) | I | I | CURRENT | `[browser]` |
| evidence | **I V DV** (trail COMPLETE) | I | I | CURRENT | `[browser]` |
| review | **I V DV** (approve/reject gate) | I (not exercised) | I | IMPLEMENTED | `[browser]` |
| customer approval | **I DV** (owner/admin gate; not executed) | I | I | IMPLEMENTED | `[code-traced]` |
| reports | **I V DV** (`READY 3`) | I | I | CURRENT | `[browser]` |
| report refresh | **I V DV** (DR-006) | I | I | CURRENT | `[browser]` |
| storage | **I DV** (lab container) | **I PV** (private `documents`, 58 objects) | I | CURRENT | `[observed]` |
| RLS / tenant isolation | **I V DV** (18/18 rules) | **I PV** (44 targets) | I | CURRENT | `[documented]` |
| email | — (no provider) | **I**, not verified | — | OPEN | `[documented]` |
| billing/subscription | I, empty | I, none | I | IMPLEMENTED | `[documented]` |
| Demo Lab identities | **I DV** (14) | — | **I** | CURRENT | `[observed]` |
| reset/reprovision | **I DV** (`reset_demo_lab.sh`) | n/a | **I** | CURRENT | `[documented]` |
| investor demo data | I (synthetic corpus) | n/a | I (partial) | PARTIAL | `[documented]` |
| browser verification | **I DV** (DR-002…007) | partial (public pages) | **I DV** | HISTORICAL evidence | `[browser]` |

---

## 4. Demo identity provisioning

| Question | Finding | Label |
|---|---|---|
| How actors are defined | `tools/demo_lab/manifest.json` (keys, roles, `expect.{actor_type,destination,role}`) | `[observed]` |
| How many actors | **14** actor entries | `[observed]` |
| Actor roles | staff `admin`; staff `operator`; PE `pe_manager` ×2; org owner/admin/member/viewer; consultant `owner`/`consultant`; client owners | `[observed]` |
| Organisation relationships | Org A, Org B, Client A, Client B (4) | `[observed]` |
| Consultant relationships | 1 firm + firm members + client engagements (Client A, Client B) | `[observed]` |
| PE relationships | 2 processing entities (Alpha, Beta) | `[observed]` |
| Staff relationships | `staff_profiles` + `staff_roles` (`admin`, `operator`, `pe_manager`) | `[code-traced]` |
| Provisioning mechanism | `tools/demo_lab/provision.py` (idempotent upserts, UUIDv5 ids, GoTrue admin API) | `[code-traced]` |
| Reset mechanism | `reset_demo_lab.sh` (+ `--purge-state`) | `[documented]` |
| Deterministic? | **Yes** | `[documented]` |
| Idempotent? | **Yes** | `[documented]` |
| Safe clean recreate? | **Yes** (lab-scoped DB drop + reprovision) | `[documented]` |
| Credentials documented without exposing secrets? | **Yes** — one synthetic password in `~/ct_local_env/demo_lab/credentials.local.json` (0600), never in the repo | `[documented]` |
| Owner usable repeatedly? | **Yes in principle** (`run_demo_lab.sh` → `provision.py` → `verify.py`), but the release backend must be started and (historically) restarted after the factor load | `[documented]` |

**Is the 14-actor model the intended *investor-demo* identity model, or a test fixture? → `UNKNOWN`.**
Evidence: the manifest is the **DEMO-T1 identity foundation** ("identity and access foundations only"), and the canonical-investor-demo decision says the lab is "the right shell — it needs provisioning to the current schema + population, not replacement". The 14 actors are **sufficient identity coverage**, but no ratified document states that these 14 constitute the **investor-demo narrative identity set**. Per instruction, this is left **UNKNOWN**, not inferred. `[documented]` `[limitation]`

---

## 5. Demo browser journeys (DR-001…DR-007)

| Journey | Demo Lab | Browser verified? | Current evidence | Remaining gap |
|---|---|---|---|---|
| customer login | Yes | **Yes** (DR-002 after CORS fix; DR-003/004/006/007) | `org_a_owner` via real form → `/home` | none (password path) |
| customer `/home` | Yes | **Yes** (DR-004) | KPIs, org banner | — |
| emissions | Yes | **Yes** (DR-004) | `2469.16978` row | — |
| documents | Yes | **Yes** (DR-004/007) | 9 docs, `Uploaded` fixed | no document-detail page |
| processing | Yes | **Yes** (DR-004) | CALCULATED item | — |
| extraction | Yes | **Yes** (DR-004) | 5 fields match | — |
| mapping | Yes | **Yes** (DR-004) | factor mapped | picker empty in that state |
| calculation | Yes | **Yes** (DR-004) | snapshot `af640887…` | — |
| evidence | Yes | **Yes** (DR-004) | trail COMPLETE | human-confirm provenance not surfaced |
| review | Yes | **Yes** (DR-004/005) | review detail | — |
| approval boundary | Yes | **Partial** (form present; approval **not executed**) | owner/admin gate code-traced | approval not demonstrated |
| reports | Yes | **Yes** (DR-005/006) | `READY 3` | — |
| report refresh | Yes | **Yes** (DR-006) | refresh verified | — |
| consultant | Yes | **Yes** (DR-005) | `consultant_owner` shell | only 1 firm (cross-firm not shown) |
| consultant-managed client | Yes | **Yes** (DR-005) | `client_a_owner` scope | — |
| Processing Entity | Yes | **No** (not in DR-001…007) | API-level only | PE browser journey unaudited |
| staff / `/ops` | Yes (identity) | **No** (context only) | `me/context` per actor | `/ops` UI not browser-verified |
| tenant isolation | Yes | **Yes** (DR-003/005 negatives) | org A↮B, client A↮B | — |

All DR evidence is at **older SHAs (2026-09-20/21)**, i.e. **HISTORICAL**, not at the frozen release. `[browser]` `[limitation]`

---

## 6. Current demo login issue ("Completing sign in…")

Baseline: `CSTR-FINAL03-BLK2-DEMO-INVESTOR-RECON-001`. `[code-traced]`

| Element | Finding |
|---|---|
| `AuthCallback` | renders the stall text as its **default view** ([`AuthCallback.js:111`](frontend/src/AuthCallback.js:111)) |
| initial `getSession()` | [`AuthCallback.js:23`](frontend/src/AuthCallback.js:23) — **no timeout** |
| retry `getSession()` | [`AuthCallback.js:51`](frontend/src/AuthCallback.js:51) — **no timeout** |
| `/api/v3/me/context` | [`api.js:110`](frontend/src/v3/api.js:110) via `v3Fetch` — **bounded 25 s** ([`api.js:17`](frontend/src/v3/api.js:17)) |
| OAuth callback route | `/auth/callback` present (`App.js`) |
| password login route | `/login` present |
| Google OAuth route | `/login` → `signInWithOAuth` ([`Login.js:189`](frontend/src/Login.js:189)) |
| post-login routing | server-decided destination ([`v3_context.py:34`](backend/api/v3_context.py:34)) |
| role/context resolution | `getMeContext` fail-closed |

**Environment affected?** `[inference]`
- **Production:** **reported** (`[documented]`, task statement).
- **Demo Lab:** **not observed** — every DR login used the password grant (or lab session seeding) and **succeeded**; no stall is recorded in DR-002…DR-007. `[browser]`
- **Determination:** **cannot currently be determined to be local-only**, and the evidence shows it has been reported on **production**; the Demo Lab path is a **different auth transport** (local GoTrue password grant) that has **not reproduced** it. → **primarily production-reported; local not reproduced.**

**Distinct from** `Failed to load your workspace. Please try again.` — the stall is the **loading** branch; that message is the **error** branch (bounded). They are **mutually exclusive render branches**; **no evidence establishes a shared root cause**. `[code-traced]`

---

## 7. Production sign-in forensics

| Item | Classification |
|---|---|
| Production Supabase Authentication (existential) | **OBSERVED** (auth live; `anonymous_users=false`; password+Google enabled; from live acceptance) |
| Google OAuth **configured** on the project | **OBSERVED** (provider enabled) |
| Google OAuth **behaviour** (end-to-end sign-in) | **REQUIRES AUTHORIZED PRODUCTION TEST** |
| Redirect URI expectation in source | **CODE-TRACED** → `https://carbontally.co.uk/auth/callback` ([`Login.js:199`](frontend/src/Login.js:199)) |
| Callback host configuration (Supabase allowed list / Google console) | **NOT OBSERVABLE** |
| Vercel environment variables (`REACT_APP_OAUTH_REDIRECT_URL`, Supabase keys) | **NOT OBSERVABLE** |
| Supabase URL/key configuration (frontend) | **OBSERVED (bundle)**: falls back to a hard-coded project URL/key ([`supabaseClient.js:5`](frontend/src/supabaseClient.js:5)) |
| `/auth/callback` route | **CODE-TRACED** present |
| `/api/v3/me/context` | **CODE-TRACED** + **OBSERVED** (401 unauth) |
| workspace resolution | **CODE-TRACED** (fail-closed 500) |
| production user identities | **OBSERVED** (2 owners; 1 email, 1 Google provider) |

No production identity was created or modified. `[limitation]`

---

## 8. Admin / Ops reconciliation

| Question | Answer | Label |
|---|---|---|
| `/ops` canonical? | **Yes** — D-P2-02; `/api/v3/me/context` → `/ops` for staff | `[documented]` |
| `/admin` status | **DEPRECATED, quarantined, retained**; served only by the Vercel rewrite | `[documented]` |
| Legacy Admin CRA status | Retained until the §4 retirement conditions are met | `[documented]` |
| Capabilities still depending on `/admin` | Bulk ops, beta management, email templates/logs, document-type CRUD (4 ❌-NONE rows) | `[documented]` |
| Does investor demo require legacy `/admin`? | **No** — the demo narratives are the customer/consultant/PE/ops workspaces; `/admin` is not an investor surface | `[inference]` |
| Does production acceptance require `/ops`? | **Yes** (canonical staff plane) | `[documented]` |
| Does the production `/admin` problem block investor-demo readiness? | **No** (BLK-1 cleared; `/admin` not an investor surface) | `[inference]` |
| Does it block FINAL-03 production acceptance? | **No** — BLK-1 was closed; FINAL-03 acceptance is blocked by **BLK-2** (identity), not by `/admin` | `[documented]` |

---

## 9. FINAL-03 relationship (environments **not** merged)

**Demo evidence (supplementary, model-level):** C (password path), D1–D5, E1/E2/E4 (and E3 partially), G behaviour, I behaviour, routing/role landing. `[inference]`
**Local owner testing:** the owner can personally run the pipeline locally with real role-bearing actors (once the lab backend is started). `[documented]`
**Production acceptance (inherently production-specific):** production Google OAuth + `/auth/callback`, production RLS on the production schema, production storage authorisation, production email (J), production calculation/report on production data (I), production routing/origins, and the production sign-in stall. `[documented]`

**Demo Lab may serve as supplementary evidence for FINAL-03** where the criterion is **model/behavioural**; it **cannot** satisfy the production-specific criteria. `[inference]`

---

## 10. Personal owner testing readiness

> **Can the Product Owner now run CarbonTally locally and systematically test the complete intended product themselves?**

**Partially — after an operational start step.** The Demo Lab infrastructure is **up** (`[observed]`: `carbontally_demo_lab_{gateway,storage,postgrest}` Up 3 days; `supabase_db_carbon_ledger` healthy; gateway `:54430` listening; lab DB `carbontally_demo_local`). **But no CarbonTally application server is running**: nothing listens on `:8060`, `:8070`, `:3000`, `:3100`. `[observed]`

### OWNER TESTING BLOCKERS
1. **The local release backend (and a frontend) is not running** — the owner cannot log in until the Demo Lab backend is started (documented: `run_demo_lab.sh --backend`; historically requires a restart after factor load). `[observed]` `[documented]`
2. **No owner-facing "how to test the whole product" runbook at the frozen release** — the last clean `verify.py` run was 2026-09-24; the DR browser evidence is at older SHAs. `[documented]`
3. **The production sign-in stall** — if it reproduces locally it blocks any OAuth-style login; the Demo Lab password path has not reproduced it. `[inference]`

### OWNER TESTING READY
Password login; customer workspace (`/home`, emissions, documents, processing, review, reports); consultant workspace; consultant-managed client; PE workspace (API-level; UI unaudited); staff `/ops` context; document → extraction → mapping → factor matching → calculation → evidence → review → reports (+refesh); tenant isolation. `[documented]` `[browser]`

### OWNER TESTING PARTIAL
Google OAuth (**lab never used it**); customer approval execution; billing flows; non-DRAFT report lifecycle; PE UI journeys; `/ops` browser UI; email. `[documented]`

---

## 11. Investor demo readiness

**Status: PARTIALLY READY** (not DEMO READY, not INVESTOR READY).

**Evidence-based conditions for the status:**
- **Met:** identity foundation (14 actors incl. staff/consultant/PE), deterministic + idempotent provisioning, reset/reprovision, 7,049 factors, real pipeline with a real calculation (R-A), customer + consultant + consultant-client journeys **browser-verified**, RLS isolation rules enforced. `[documented]` `[browser]`
- **Not met (preventing DEMO READY):** no PE or `/ops` **browser** journey; approval not demonstrated; only **1 consultant firm** (cross-firm isolation unshown); all reports `DRAFT` (no reviewed/approved/finalised state); the last full verification is **2026-09-24** and browser evidence is at **older SHAs**; the 13-vs-14 actor drift is unresolved. `[documented]`
- **Open (not necessarily blocking):** canonical-dataset decision (X-5 / which identity set the demo uses). `[documented]`

### Required before investor demonstration
1. Re-run the Demo Lab to the **current release schema** and re-run `verify.py` green. `[documented]`
2. Browser-verify the **PE** and **`/ops`** journeys. `[inference]`
3. Produce at least one **non-DRAFT** (reviewed/approved/finalised) report so the lifecycle is demonstrable. `[documented]`
4. Ratify **which dataset/actor set** the investor demo uses (X-5). `[documented]`

### Nice-to-have / deferred
Second consultant firm (E3); customer↔support messaging (`can_manage_staff`); billing demo data. `[documented]`

### Production-only requirements
Production OAuth verification; production email; production acceptance. `[documented]`

---

## 12. Required end state (evidence-based sequence)

The evidence supports the **intended** chain, with one dependency made explicit:

```text
LOCAL  (Demo Lab — identity + factor + corpus foundation)
  ↓  [operational start: lab backend + frontend]
Owner functional testing  (currently PARTIAL — see §10)
  ↓
LIVE PRODUCTION  (deployed; /ops canonical; BLK-1 cleared)
  ↓
Production acceptance  (BLOCKED by BLK-2 — no authorized production identity)
  ↓
INVESTOR DEMO  (PARTIALLY READY — see §11)
  ↓
Controlled investor demonstrations
```

**Evidence-based sequencing note:** the **immediate** unblocked work is **owner local testing** (blocked only by an operational start step). **Production acceptance** is **blocked** (BLK-2) and must not be merged with the Demo environment. **Investor-demo readiness** is **partially** achievable from the Demo Lab **without** production acceptance, but its own conditions (§11) must be met first.

---

## 13. Final gap register

| ID | Gap | Environment | Evidence | Blocking owner testing? | Blocking investor demo? | Blocking FINAL-03? | Status |
|---|---|---|---|---|---|---|---|
| G-1 | Local release backend/frontend not running | Local | `[observed]` no :8060/:8070/:3000 listener | **Yes** (operational) | No | No | OPEN |
| G-2 | No authorized production test identity | Production | `CSTR-FINAL03-BLK2-…` | No | No | **Yes** | BLOCKED |
| G-3 | Production sign-in stall ("Completing sign in…") | Production | `AuthCallback` default view | No | No | **Yes** (auth regression) | OPEN |
| G-4 | Google auth unverified (lab never used it; prod unverified) | Prod/Lab | DR series | No | No | Yes | OPEN |
| G-5 | Demo Lab not re-verified at frozen release (last 2026-09-24) | Demo | `[documented]` | No | **Yes** | No | OPEN |
| G-6 | PE and `/ops` browser journeys unaudited | Demo | DR-001…007 | No | **Yes** | No | OPEN |
| G-7 | Approval lifecycle not demonstrated; reports all `DRAFT` | Demo | DR-004/006 | No | **Yes** | No | OPEN |
| G-8 | Canonical demo dataset/actor set undecided (X-5) | Demo/Gov | capability census | No | **Yes** | No | NOT YET AUTHORIZED |
| G-9 | 13-vs-14 actor drift | Demo | manifest vs README | No | No | No | OPEN (doc) |
| G-10 | Only one consultant firm (E3 cross-firm unshown) | Demo | canonical-env record | No | No | Partial | OPEN |
| G-11 | Email path unverified | Production | live acceptance §16 | No | No | Yes | OPEN |

---

## 14. Exact next-action order

**Next action (1) — CoStrict verification:** confirm the Demo Lab can be started to the **current frozen release** and that `verify.py` returns green (read-only until a start is separately authorised). — *first.*
**2 — PO decision:** authorise an **operational start** of the local Demo Lab backend + frontend (`run_demo_lab.sh --backend`) so the owner can test. **NOT YET AUTHORIZED.**
**3 — PO manual testing:** owner runs the local end-to-end journeys (§10 READY/PARTIAL).
**4 — PO decision:** ratify the **canonical demo dataset/actor set** (X-5) and whether the 14-actor model is the investor identity set. **NOT YET AUTHORIZED.**
**5 — Cline implementation (only if §11/§12 evidence shows it is required):** none is currently established as required by evidence alone.
**6 — independent verification:** re-audit the Demo Lab at the frozen release (verify.py + PE/`/ops`/approval browser journeys).
**7 — PO decision:** authorise the **controlled production acceptance identity set** (BLK-2) and production-side observability for the sign-in stall. **NOT YET AUTHORIZED.**
**8 — production acceptance:** execute authenticated FINAL-03 acceptance after (7).
**9 — investor-demo preparation:** satisfy §11 conditions, then schedule controlled demonstrations.

**No implementation is currently established as required by the evidence; the immediate need is an authorised operational start + PO decisions, not code changes.**

---

## 15. Final verdicts

### LOCAL ENVIRONMENT
**PARTIALLY READY** — Demo Lab infra is up and the identity/factor/corpus foundation exists, but the release backend + frontend are **not running**, so end-to-end owner testing requires an operational start step.

### LIVE PRODUCTION
**PARTIALLY READY** — deployed and healthy (`/ops` canonical, BLK-1 cleared), but **authenticated production acceptance is blocked** (no authorized production identity) and the sign-in stall is open.

### INVESTOR DEMO ENVIRONMENT
**PARTIALLY READY** — real UI/workflows, deterministic identities, reset/reprovision; but not re-verified at the frozen release, PE/`/ops`/approval journeys unaudited, all reports `DRAFT`, and the canonical dataset decision is open.

### IDENTITY PROVISIONING
**AVAILABLE** — `tools/demo_lab/provision.py` + `manifest.json`: deterministic, idempotent, resettable, 14 role-bearing actors, credentials outside the repo.

### OWNER END-TO-END TESTING
**PARTIALLY READY** — the product is testable once the local backend/frontend are started; OAuth, approval execution, billing, non-DRAFT reports and PE UI remain partial.

### FINAL-03 PRODUCTION ACCEPTANCE
**BLOCKED** — BLK-1 cleared; **BLK-2 open** (no authorized production identity; no staff/consultant/PE identity in production; I/J require production mutation).

### PRODUCTION SIGN-IN
**PARTIALLY EXPLAINED** — the string's source (the `AuthCallback` default view) and its only unbounded leg (the timeout-less `getSession()`) are code-traced; the live production trigger is **not observable** read-only.

### GOOGLE AUTHENTICATION
**UNVERIFIED** — the Demo Lab never exercised OAuth; the production OAuth provider config, redirect allow-list and end-to-end behaviour are not observable and require an authorised production test.

### NEXT GOVERNANCE ACTION
**One action:** the Product Owner decides whether to authorise the **operational start of the local Demo Lab (backend + frontend) for personal end-to-end testing** — this is the single unblocked next step before owner testing and investor-demo preparation. (Production acceptance and the canonical-dataset decision are separate, subsequent PO decisions.)

---

**NO SOURCE CODE, DATABASE SCHEMA, DATABASE DATA, SUPABASE/RENDER/VERCEL/DNS/AUTH CONFIGURATION, DEMO LAB DATA, CREDENTIALS, SECRETS, GIT HISTORY OR DEPLOYMENT STATE WERE MODIFIED. NO IDENTITY WAS CREATED. THE DEMO LAB WAS NOT RESET OR RESEEDED.**

**READY FOR PO REVIEW — THREE-ENVIRONMENT RECONCILIATION COMPLETE — NO REMEDIATION PERFORMED**
