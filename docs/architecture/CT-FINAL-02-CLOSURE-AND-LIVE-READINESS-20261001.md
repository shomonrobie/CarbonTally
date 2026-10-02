# CT-FINAL-02 — Closure and Live-Readiness Report

**Date:** 2026-10-01 · **Operator:** Cline (implementation / rehearsal operator)
**Acceptance authority:** CoStrict / OHD — **this report does not accept anything.**
**Scope:** finish the remaining FINAL-02 evidence (B3 browser/admin acceptance; B2′ managed
backup/PITR), make the local system genuinely usable by every actor, re-run the FINAL-02
regression set, and **prepare — but not execute —** the clean production cutover.

**Headline:** **B3 is now evidenced by real authenticated browser journeys (10/10 actors) and B4/B5 are
re-verified, but B2′ is BLOCKED: no Supabase management credential exists in this environment, so
managed backup/PITR cannot be verified. FINAL-02 therefore remains OPEN and is NOT ready for a
"ready-for-acceptance" statement until that credential is supplied and the verifier rules.**

> **Reconciled 2026-10-02 (Cline — documentation + read-only/local evidence only; no repository code
> change, no commit).** Three things changed after the 2026-10-01 text above, and all are recorded in
> full in **§15 (current status matrix)**, **§16 (re-run evidence)** and **§17 (verdict)**:
>
> 1. **§2 below is SUPERSEDED.** The Supabase management credential *was* subsequently supplied, and
>    the read-only Management-API verification *was* performed (2026-10-01 and again 2026-10-02) —
>    see `CT-FINAL-02-B2-READONLY-VERIFICATION-20261001.md`. B2′ is therefore no longer an *evidence*
>    blocker; it is now a **capability** blocker: the live project has **0 managed backups, PITR
>    disabled, no PITR add-on, `backup.retention_days = 0`, and the owning organisation is on the
>    `free` plan.** The "credential unavailable" reason must not be re-used.
> 2. **A new FINAL-02 blocker was found on 2026-10-02 — `B7`.** The BACKUP-01/02 workstream's new
>    backup worker, started from the application lifespan, **leaks one pooled PostgreSQL connection
>    per tick** and exhausts the application's asyncpg pool ≈45 s after start-up; every DB-backed
>    endpoint (including `/health` and `/api/v3/accounting/context`) then hangs. Full evidence,
>    reproduction, code locations and the recommended minimal fix are in **§15.2 / §17**.
>    **Update, 2026-10-02 (second pass): B7 is remediated in the working tree and locally verified —
>    §15.2.1.** Two 600 s soaks clean (schema-complete and migration-behind), the pre-fix control still
>    firing, suites **275/275 EXIT=0**, the canonical drill completing with §16.5 reproduced. It is *not*
>    closed: nothing was committed (§17 item 2 / cutover gate **P2**), and the B4 re-run is outstanding.
> 3. **FINAL-03 is prepared, but NOT executed.** The clean-production package —
>    `docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md` — is a **22-step gated
>    sequence** (preconditions P1–P6, evidence and stop condition per step, abort/rollback criteria) that
>    replaces §11's operational detail. It is explicitly **not authorized to run while B7 stands** and
>    while the BACKUP-01/02 file set is uncommitted.
>
> **Current status is the §15 matrix; the verdict is §17.** Nothing in §0–§14 was deleted, and no
> previously recorded measurement was altered; stale *current-status* statements are marked inline.

| Blocker | Status after this task |
| --- | --- |
| **B1** | **CLOSED / SATISFIED BY EXISTING EVIDENCE** (unchanged; owner-supplied 2026-09-29 delivery evidence) |
| **B2′** | **BLOCKED** — managed backup/PITR credential unavailable (§2) → ***reconciled 2026-10-02: the credential dependency is resolved; B2′ is now a CAPABILITY blocker — §15 row 2 / §15.1 / §17*** |
| **B3** | **EVIDENCED** — authenticated browser/admin acceptance executed against the disposable rehearsal stack (§1) |
| **B4** | **PASS** — D-7 live/PostgREST proof re-run 35/35 (§5) |
| **B5** | **PASS** — JWT/PostgREST + Storage isolation matrix re-run 29/29 (§6) |
| **Acceptance** | **NOT granted** — CoStrict/OHD decides (§8) |

> **This table is the 2026-10-01 record and is not the current one.** A seventh item was added on
> 2026-10-02 — **B7**, the backup-worker connection leak, a genuine blocker (§15.2 / §17) — and B2′'s
> basis changed. **For current status read the §15 matrix; for the current verdict read §17.**

---

## 0. What was and was not done

**Authorized and performed:** sanctioned authenticated browser/QA verification (B3) against the
disposable rehearsal stack over `ct_final02_src`; read-only Supabase managed-backup/PITR attempt
(B2′, blocked); local all-actor usability repair and verification; FINAL-02 canonical regression
re-run; preparation (not execution) of the production cutover.

**Never done:** no production deploy; no production database write; no production email; no real
customer account; no RLS/auth/storage/subscription-semantics change; no closed-decision change; no
FINAL-03 execution; no commit or push; no demo-data deletion.

**Repository preservation:** `git rev-parse HEAD` = `cabdca8380415e73a25cf23eb393d0b15c0af391`
(branch `p8-release-reconciled`) before and after; the pre-existing working-tree change count was
**131** and the only addition made is this report file (**132** total, §12; *2026-10-01 pass — for the
current working-tree count see §16.7*); `qa_harness/` is untouched
(0 entries); `frontend/.env.local` still carries its 2026-09-21 mtime.

---

## 1. B3 — authenticated browser / admin acceptance

### 1.1 The sanctioned mechanism, and why a runner wrapper was required

The sanctioned mechanism is the repository QA harness browser sweep
(`qa_harness/browser/sweep.py`, driven by `qa_harness/scripts/run_browser.py`). Two facts forced a
thin wrapper rather than calling that script directly:

1. **The working copy of the harness cannot run at all.** `qa_harness/evidence/` and
   `qa_harness/reports/` are absent from `ct_93d5cdd` (never tracked in git, no history, no deletion
   in `git status`), so `qa_harness.core.run_context` fails at import
   (`ModuleNotFoundError: No module named 'qa_harness.evidence'`) and every runner — `run_browser.py`,
   `run_api.py`, `run_db.py`, `run_workflows.py`, `run_all.py` — dies at import. This is a
   pre-existing harness-packaging gap, not a product defect, and it is reported rather than "fixed",
   because repairing it would modify the repository.
2. **The complete harness tree** (identical `browser/sweep.py`, `identities/loader.py`,
   `config/environments.yaml`, `core/run_context.py` — byte-compared with `diff`) exists in the
   sibling clone `/home/shomonrobie/carbon_tally/qa_harness`, which does contain `evidence/` and
   `reports/`. The sanctioned engine was therefore executed from that copy, with the target
   environment injected in code (`config/environments.yaml` has no rehearsal entry and the loader
   applies no environment-variable override; no harness config file was edited).

Runner: `/home/shomonrobie/ct_local_env/final02_rehearsal/b3_browser.py`. Target:
frontend `http://localhost:3000`, API `http://127.0.0.1:8090`, auth/PostgREST/Storage gateway
`http://127.0.0.1:54440`, database `ct_final02_src`. All findings/evidence are written **outside**
both repositories (`final02_rehearsal/b3/`). Chromium 1.62.0 (Playwright, headless) — the browser
tool that was unavailable in the 2026-10-01 rehearsal — is now installed and was used.

### 1.2 Two real login blockers were found and fixed — environment only

The first authenticated attempt **failed in the browser while succeeding at the API** — the exact
condition B3 exists to catch. Both causes were in the disposable rehearsal *environment*, not in the
product, and both were fixed outside the repository (§12):

| # | Symptom | Root cause (measured) | Fix |
| --- | --- | --- | --- |
| 1 | Browser login threw `net::ERR_FAILED`; console: *"The 'Access-Control-Allow-Origin' header contains multiple values '\*, http://localhost:3100', but only one is allowed"* | The rehearsal gateway's nginx `add_header` **appends** to the CORS headers GoTrue/PostgREST already send, producing a duplicate `Access-Control-Allow-Origin` (`*, <origin>`). Browsers reject that; `curl` does not, which is why every API-only probe had passed. | `proxy_hide_header` for the upstream CORS headers in the `/auth/v1/`, `/rest/v1/`, `/storage/v1/` locations; verified **one** `Access-Control-Allow-Origin` per response. |
| 2 | After fix 1 the session was created (`sb-127-auth-token` in `localStorage`) but every post-login API call still failed with *"No 'Access-Control-Allow-Origin' header"* on `http://127.0.0.1:8090` | The backend's hard-coded `Config.ALLOWED_ORIGINS` (`backend/config.py`) lists `localhost:3000/3001/3002` — **not** `3100`, the port the rehearsal frontend was using. | Serve the frontend on the allowed port **3000** (no code change), and align the disposable gateway CORS map and `GOTRUE_SITE_URL` to `http://localhost:3000`. |

After both fixes the *real* form login works end-to-end (measured in §1.3/§1.4). **The owner
therefore could not log in through a browser before this task**, whatever the API layer reported —
this is the substance of the B3 gap the harness was built to close.

### 1.3 Sanctioned sweep — 10/10 actors authenticated through the real login form

Run `20261001T100647_cabdca8` (git `cabdca8`), 21 route visits, 10 role sweeps.

| Persona (representative identity) | Logged in | Landing | Expected |
| --- | --- | --- | --- |
| customer_owner | ✅ | `/home` | `/home` |
| customer_viewer | ✅ | `/home` | `/home` |
| consultant | ✅ | `/consultant` | `/consultant` |
| pe_manager | ✅ | `/pe` | `/ops` (see §1.6) |
| pe_staff | ✅ | `/pe` | `/ops` (see §1.6) |
| internal_operator | ✅ | `/ops` | `/ops` |
| internal_reviewer | ✅ | `/ops` | `/ops` |
| internal_qc | ✅ | `/ops` | `/ops` |
| staff_admin | ✅ | `/ops` | `/ops` |
| system_admin | ✅ | `/ops` | `/ops` |

Every sweep: login via `/login` form (`input[type=email]`, `input[type=password]`,
`button[type=submit]`), session confirmed by a `sb-` key in `localStorage` plus an authenticated
route, then per-route console/network/blank/JS-exception capture with screenshots. `auth_classification
= AUTHENTICATED` for all ten.

### 1.4 Supplementary journeys — the checks the sweep does not make

Runner `b3_journeys.py` (26/30 checks) plus a timing-aware probe `b3_textprobe.py`:

| Journey | Result |
| --- | --- |
| **J1 anonymous separation** (`/home`, `/ops`, `/consultant`, `/documents`, fresh context per route) | **PASS** — redirected to `/login` in **2.6–3.3 s**, login page rendered (394 chars), and **no protected marker was ever visible** at any sample |
| **J2 customer-owner workspace** | **PASS** — `/home` 420 chars with the org name *and* `Sign out`; `/documents` 1 645; `/emissions` 737; `/organization` 1 404; `/reports` 535 — all rendered, **zero non-realtime console errors** |
| **J2 cross-tenant** | **PASS** — the other tenant's name (`Granite Distribution`) appears **nowhere** in the customer workspace; own org (`Quayside Energy`) does |
| **J3 logout / re-login cycle** | **PASS** — logout control found and clicked → `/login`, **0** `sb-` keys left in `localStorage`, re-login → `/home` |
| **J4 consultant workspace** | **PASS** — lands `/consultant`, 876–1 483 chars rendered, and it does **not** expose the internal `/ops` shell |
| **J5 internal admin `/ops`** | **PASS** — lands `/ops`; control-plane navigation rendered (`Internal Operations`, `Dashboard`, data-entry/review/staff/roles/entities/SLA…) |
| **J6 D-7 inactive organisation in the UI** | **PASS** — see §1.5 |

**A measured correction to a first-read implication.** An early reading of the sweep data suggested
several customer routes rendered "empty" (bodies of 17–180 chars). A timing-aware re-measurement shows
this was a **sampling race, not a product fault**: the CRA development bundle bootstraps
asynchronously, and content stabilises in **1.9–4.3 s** (`t=` column above). Once settled, the same
routes render fully with **no non-realtime console errors**. The sweep's own per-route reads are taken
earlier than that, so its short-body observations must not be read as product findings.

### 1.5 D-7 suspension/reactivation observed through the UI (self-restoring)

`b3_d7_ui.py` — org A suspended **through the product's own admin handler**
(`POST /api/admin/bulk/organizations/status`, `{"success": true}`), always reactivated in a
`finally` block:

| State | `/home` body | Observed |
| --- | --- | --- |
| ACTIVE | 1 651 chars | tiles: READY REPORTS 1 · QUEUED 1 · DOCUMENTS 51 · MEMBERS 4 · EMISSIONS ROWS 78 · TOTAL 120.87 tCO₂e |
| **SUSPENDED** | 1 474 chars | every org-scoped tile drops to **0**; browser console carries the product's own denials: `GET /api/v3/reports?… → 403: This organization is suspended`, same for `/api/v3/documents?…`, `/api/v3/organizations/{A}/members`, `/api/v3/exports/emissions.json?…` |
| REACTIVATED | 1 651 chars | counters restored identically (1 · 1 · 51 · 4 · 78 · 120.87) |

Database re-verified afterwards: `organizations.is_active` for org A = `true`, and **975/975**
organisations active — the suspension was fully undone.

### 1.6 The sweep's 352 findings, classified — none is a P0, and none is a B3 blocker

The sweep emitted 352 raw findings (72 after deduplication). Raw counts must not be read as defect
counts. Measured composition:

| Class | Count (raw) | Assessment |
| --- | --- | --- |
| `UX P2` — "Table rule *X* violated on *route*" | 326 | **Harness calibration artifact.** The table auditor finds one table per page and reports it as the pseudo-table `"page"`, then evaluates **all eight** configured table rules against it (`measurements.table = "page"`), so one page produces up to 8 findings with unrelated rule names ("documents"/"emissions"/"processing_queue"/… on `/documents`). These are not eight product defects per page. Flagged for harness calibration (`reclassify.py` exists for exactly this) — not a CoStrict acceptance item. |
| `UI P3` — "Console errors on *route*" | 21 | **Environment-induced.** Every one is the Supabase Realtime WebSocket (`ws://127.0.0.1:54440/realtime/v1/websocket`): the disposable rehearsal stack provides auth + PostgREST + Storage only — **no Realtime service** (and pointing Realtime at the other local stack would subscribe on the wrong database). Non-realtime console errors on the settled pages: **0** (§1.4). |
| `SEC P1` — "Anonymous visitor reached protected route" (`/home`, `/consultant`, `/ops`) | 3 | **False positive (measured).** The check compares `page.url` immediately after a possibly-timed-out `networkidle` wait; the SPA's client-side redirect completes at **2.6–3.3 s**. With a fresh context per route and continuous sampling, all four protected routes land on `/login`, and **no protected marker is ever visible** (§1.4 J1). |
| `AUTH P1` — "pe_manager/pe_staff landed on `/pe`, expected `/ops`" | 2 | **Harness-configuration mismatch, not a product fault.** The product's PE workspace is routed at `/pe` (renders; `PEShell.jsx`); the harness expectation comes from `config/routes.yaml` (`landings: pe: /ops`). The product route is the closed decision; the harness config is the stale artifact. |

**No P0 finding was emitted. No P1 finding survived measurement.** The findings are recorded as
they are (not deleted, not silently reclassified) with the measurements above so CoStrict can judge
each class independently.

### 1.7 B3 verdict

**B3 is satisfied as an acceptance-evidence item**: a real browser — not an API client — logs in as
organisation owner/admin/member/viewer, consultant, PE manager/staff and five internal roles;
workspaces render their data; organisation scoping holds in the browser (no other-tenant content);
internal `/ops` navigation renders; anonymised access is redirected; logout/login cycles; and D-7
suspension/reactivation is observable end-to-end. The remaining `/ops` upload-policy, email-delivery
and factor-management *interaction* depth is a matter for the verifier's own run of the (now
runnable) harness — the mechanism, stack and credentials are in place and documented in §9.

---

## 2. B2′ — managed Supabase backup/PITR: **BLOCKED (credential unavailable)** — SUPERSEDED 2026-10-02 (§15)

> **Superseded.** The credential described here as absent was supplied afterwards; the read-only
> verification was performed and **the evidence now exists**. The §2 text below is retained as the
> historical record of the 2026-10-01 attempt. **Current B2′ status: §15.1 — evidence obtained,
> capability absent (0 backups · PITR disabled · no add-on · org plan `free` · `backup.retention_days`
> = 0).** Do not re-use "credential unavailable" as the B2′ reason.

Performed, read-only, no mutation:

| Probe | Result |
| --- | --- |
| `supabase projects list` (CLI v2.115.0) | No session — prints an empty project table and *"Cannot find project ref. Have you run supabase link?"* |
| `~/.supabase/access-token`, `~/.config/supabase/access-token`, `~/.config/supabase/access_token`, `<repo>/.supabase/access-token` | **absent** (all four) |
| `SUPABASE_ACCESS_TOKEN` / `Management`-style env vars in the process environment | **not set** |
| `sbp_…` personal-access-token literal in shell rc files or the Supabase config dirs | **none** |
| `GET https://api.supabase.com/v1/projects` (management API) | **401** — reachable, unauthenticated |
| `GET https://api.supabase.com/v1/projects/{ref}/database/backups` | **401** |
| `GET https://api.supabase.com/v1/projects` with the project `service_role` key | **401** — a service-role key is *not* a management credential |

**Exact access required to close B2′ (one of):**

1. a Supabase **personal access token** (`sbp_…`) for the organisation owning project ref
   `pvwiojoyaqywtydzcpbg` (from `SUPABASE_LIVE_URL` in `backend/.env`), supplied either by
   `supabase login` (writes `~/.supabase/access-token`) or as `SUPABASE_ACCESS_TOKEN`; then
   read-only `GET /v1/projects/{ref}/database/backups` + the project's backup/PITR configuration; **or**
2. **dashboard** access to Project → Settings → Database → Backups / Add-ons, captured as dated
   evidence (backup enabled, retention window, PITR add-on state) by whoever holds that access.

**No substitute evidence exists.** The credentials present in this environment (anon key,
`service_role` key, live Postgres DSN) cannot read platform-level managed-backup/PITR configuration —
they are data-plane credentials. No production connection was opened, and nothing was inferred.
Recording *"the hosted project is covered"* without this credential would be inventing evidence, so
B2′ **stops here** exactly as the task directs.

---

## 3. Local all-actor usability — one coherent path, verified

**Before this task** the local browser path was incoherent in two independent ways: the running
frontend's `frontend/.env.local` points at the *old demo-lab* stack (`REACT_APP_SUPABASE_URL=
http://127.0.0.1:54430`, `REACT_APP_API_URL=http://localhost:8070` — a port with **nothing
listening**), and even when re-pointed at the rehearsal stack the backend's CORS allowlist refused
port 3100 (§1.2). **After this task** the path is coherent and verified end-to-end:

```
Browser  http://localhost:3000
  └─ Frontend   CRA dev server, port 3000   (REACT_APP_API_URL=http://localhost:8090,
                                             REACT_APP_SUPABASE_URL=http://127.0.0.1:54440)
       └─ Backend FastAPI 127.0.0.1:8090    (DATABASE_URL=…@127.0.0.1:54426/ct_final02_src,
                                             SUPABASE_URL=http://127.0.0.1:54440)
            └─ Disposable rehearsal gateway 127.0.0.1:54440
                 ├─ /auth/v1/     GoTrue   → ct_final02_src (real password grants)
                 ├─ /rest/v1/     PostgREST→ ct_final02_src (RLS enforced)
                 └─ /storage/v1/  Storage  → ct_final02_src (+ private byte store)
```

Evidence: gateway `auth/v1/health` **200**, `rest/v1/` **200**, `storage/v1/status` **200**;
backend `/health` **200**; frontend `/` **200**; the served bundle contains the rehearsal gateway
(`54440` ×3) and the backend (`8090` ×21) and contains **neither** `54430` nor `8070`; a real browser
login as each actor class lands on the correct workspace (§1.3/§1.4).

**Deliberately NOT changed:** `frontend/.env.local` (a pre-existing untracked file, mtime
2026-09-21) still holds the stale demo-lab values. It is overridden in-process — CRA lets an
already-set `REACT_APP_*` process value win over `.env` files — so the coherent wiring is delivered
by the launcher (§9) and the stale file is left exactly as found for the owner to manage.

**Known limitation of the disposable stack (not a product defect):** no Realtime service, so the
browser's Realtime WebSocket fails and logs a console error on each page (§1.6). Everything else
used by the app (auth, PostgREST, Storage) is present and healthy.

**Owner-facing artefacts:** `start_local_all.sh` (idempotent bring-up), `stop_local_all.sh`,
and `b3/OWNER-LOGIN.md` (identities, roles, which portal each actor sees).

---

## 4. FINAL-02 regression — re-run and green

| Run | Command | Result |
| --- | --- | --- |
| **Canonical FINAL-02 set** (the 7 files named by the FINAL-02 matrix §4.1: F-05-R1 org-scope, D-7 lifecycle decisions, D-7 F1/F2/F3, Storage Step 1, Storage Step 2, G1/G2 emissions scope + staff access, FINAL-02 email provider) | `backend/.venv/bin/python -m pytest -q -p no:cacheprovider <7 files> --junitxml=…` | **314 tests · 0 failures · 0 errors · 0 skipped — EXIT=0** (107.3 s; counts read from the JUnit XML, which is authoritative — the stdout summary line is swallowed by this terminal's shell integration) |
| **B5 isolation matrix** (`matrix_b5.py`) | `backend/.venv/bin/python matrix_b5.py` | **29/29 PASS — EXIT=0** (real password grants; JWT sig/scheme/expiry refusals; cross-org PostgREST read/write denials; per-org Storage download/sign/upload isolation) |
| **B4/D-7 matrix** (`matrix_b4_d7.py`) | `backend/.venv/bin/python matrix_b4_d7.py` | **35/35 PASS — EXIT=0** (suspend → 403 "suspended" for owner/admin/member/viewer; non-disclosing single message; tenant-scoped; staff unaffected; reactivate → all restored) |
| **Login/password-grant probe** (`login_probe.py`) | `backend/.venv/bin/python login_probe.py` | **9/9 real password grants — EXIT=0** |

**Database integrity (`ct_final02_src`, read-only SQL):** 149 public tables · **149** RLS-enabled ·
**271** policies · 1 206 auth users · 1 183 `@demo.carbontally.local` users (1 183 with passwords) ·
975 organisations, **975 active** (org A restored) · **7 049** emission factors (untouched) ·
686 storage objects · `documents` bucket private (`public=false`, 10 485 760-byte limit).

**Repository integrity:** HEAD `cabdca8…`, branch `p8-release-reconciled`, working-tree entries
**131 → 131 + this report**, `qa_harness/` untouched, no commit/push. ***Reconciled 2026-10-02:** still
no commit and no product-code change; the 2026-10-02 pass added only documentation — the FINAL-03
package plus the in-place edit of this report — so the working tree is now **161** entries
(112 untracked / 49 modified), `qa_harness/` untouched — §16.7.*

---

## 5. B4 status — D-7 inactive-organisation denial (live/PostgREST proof)

**PASS.** Re-derived live against the rehearsal stack this session: **35/35 checks**, EXIT=0, using
the product's own admin handler to suspend and reactivate and seven pre-existing demo identities. The
implementation facet was already independently verified (94/94 unit tests, CoStrict 2026-09-30); this
run supplies the outstanding **live/RLS/PostgREST** facet, and §1.5 additionally shows the same denial
reaching the **browser UI**. The IV report's §11/§19 B4 wording (2026-09-29, pre-implementation)
remains stale and is CoStrict's to revise.

## 6. B5 status — JWT/PostgREST + Storage object isolation

**PASS.** Re-derived live this session: **29/29 checks**, EXIT=0 — real password grants, token
role/aud claims, expired/wrong-secret/malformed JWT refusals (401), org A owner→A rows 78 / →B rows 0,
org B owner→A rows 0 / →B rows 1, member/admin/viewer scope, anonymous denial, cross-org
INSERT/UPDATE/DELETE refused, and Storage per-org download/sign/upload isolation including
cross-tenant refusal and anonymous refusal.

## 7. B1 status — **CLOSED / SATISFIED BY EXISTING EVIDENCE** (unchanged)

The B1 criterion is *controlled external delivery*, satisfied by the owner-supplied 2026-09-29
"CarbonTally SMTP Delivery Test" message received through the canonical path. Nothing in this task
changes that finding; the reconciliation stands, and two non-B1 observations remain as recorded
(pre-existing F.3 implicit-TLS/465 capability limitation; live `system_settings` has no
`email_provider` row). B1 must not appear in the open FINAL-02 blocker list.

## 8. Remaining blockers

| # | Blocker | Owner / next action |
| --- | --- | --- |
| 1 | **B2′** managed Supabase backup/PITR — *recast 2026-10-02* | **Owner**: the §2 credential dependency is **resolved** (the `sbp_…` token is present in the gitignored `backend/.env` and authenticates). B2′ is now a **capability** blocker: decide the production recovery posture (move the `CarbonLedger` organisation off the `free` plan so managed backups with non-zero retention exist, and/or purchase the `pitr` add-on), then re-run the read-only verifier (§15.1) — it closes in minutes. |
| 2 | **Independent acceptance** | **CoStrict/OHD**: run its own verification over the artefacts in §9/Appendix B and grant or refuse acceptance. |
| 3 | Document-owner actions carried from the prior reconciliation | annotate the superseded B1 references (gap matrix §L563, live-evidence pass, IV §19 B1/§5.1) and remove B1 from the open blocker list — a **list correction**, not an acceptance-state change. |
| 4 | **B7** — backup worker ↔ asyncpg pool exhaustion *(added 2026-10-02; **remediated + locally verified in the working tree — §15.2.1**)* | **Implementer**: ~~release the leased connection in `backend/backup/jobs.py` (and the same idiom in `backend/backup/service.py`); make a missing backup table a terminal, backed-off condition; apply the two BACKUP migrations before the worker runs anywhere; then re-run the backup suites, the canonical drill and the B4 matrix.~~ **DONE 2026-10-02 second pass except the B4 matrix**: fix applied, suites 275/275 EXIT=0, drill completes, two 600 s soaks clean. **Remaining: commit (P2), apply the migrations before the worker runs anywhere, and re-run B4.** Detail: **§15.2 / §15.2.1 / §17**. |

The 2026-09-30 matrix's blocker register also carries **B6**; its definition, status and any update
remain with the document owner / CoStrict — this task did not survey it and asserts nothing about it.

**Both B3 and B2′ could not be closed together**: B3 is now evidenced, B2′ is blocked on a credential.
Per the task's stop condition, the correct verdict is therefore **not** "ready for independent
acceptance", but below.

> ***Reconciled 2026-10-02:*** the sentence above is the 2026-10-01 reading. B2′ is no longer
> *blocked on a credential* — the credential was supplied and the read-only verification ran, showing a
> **capability** gap; and **B7** (row 4) is a second, newly introduced blocker. §17 is the current
> verdict; this section is kept as the historical blocker register for that pass.

---

## 9. Exact local login / use instructions for the Product Owner

**Bring the environment up** (idempotent; nothing is written inside the repository):

```bash
bash /home/shomonrobie/ct_local_env/final02_rehearsal/start_local_all.sh
```

It verifies the disposable gateway (`auth`/`rest`/`storage` → 200), starts the backend on `:8090`
if absent, starts the frontend on `:3000` with the coherent `REACT_APP_*` overrides, and prints the
URLs. Then **open <http://localhost:3000>** and sign in on the normal login page. To stop:

```bash
bash /home/shomonrobie/ct_local_env/final02_rehearsal/stop_local_all.sh
```

**Password:** the shared local demo password, from the gitignored credential file
`/home/shomonrobie/carbon_tally/.local-demo-credentials.md` (or `CARBON_TALLY_DEMO_PASSWORD`). It is
never printed, logged or committed by any script here.

**Which identity to use for which job** — all `@demo.carbontally.local`; full table in
`final02_rehearsal/b3/OWNER-LOGIN.md`:

| You want to see… | Sign in as |
| --- | --- |
| Customer workspace (dashboard, documents, emissions, reports, org profile, review, messaging) | `owner.demo0001@demo.carbontally.local` (*Quayside Energy*) |
| Customer — read-only role | `viewer.demo0001@demo.carbontally.local` |
| Consultant workspace / client portfolio | `consultant.demo0001@demo.carbontally.local` |
| Internal CarbonTally admin control plane (`/ops`: dashboard, data entry, review, staff, roles, entities, SLA) | `staff-admin.demo@demo.carbontally.local` |
| Internal operator / reviewer / QC | `operator.demo@`, `reviewer.demo@`, `qc.demo@` |
| Processing entity workspace (`/pe`) | `pe-manager-1.demo@`, `pe-staff-1.demo@` |
| Legacy single-org demo fixture (org A, the D-7 subject) | `owner@demo.carbontally.local` |

Expected after sign-in: customer roles land on `/home`, consultant on `/consultant`, internal roles
on `/ops`, PE roles on `/pe`. Allow ~2–4 s after load for data panels to fill (dev-server bootstrap).

## 10. Actor identities and roles used (no passwords are recorded anywhere)

| Actor class | Identities used | Role / membership |
| --- | --- | --- |
| Organisation owner | `owner.demo0001@…` (Quayside Energy), `owner@demo…` (org A, *CarbonTally Demo Ltd*) | `organization_members.role = owner` |
| Organisation admin | `admin.demo0001@…`, `admin@demo…` | `role = admin` |
| Organisation member | `member.demo0001@…`, `member@demo…` | `role = member` |
| Organisation viewer (read-only) | `viewer.demo0001@…`, `viewer@demo…` | `role = viewer` |
| Consultant | `consultant.demo0001@…`, `consultant@demo…` | consultant (active client grant to org A) |
| Processing entity | `pe-manager-1.demo@…`, `pe-staff-1.demo@…` | PE manager / operator |
| Internal CarbonTally staff | `staff-admin.demo@…` (admin), `operator.demo@…`, `reviewer.demo@…`, `qc.demo@…`, `system-admin.demo@…` | internal staff roles |
| Second tenant (isolation) | `owner.demo0002@…` (Granite Distribution), `owner@demo…`/org B `e5218a70-…` | cross-tenant control |

Every identity is a **pre-existing local demo/test** account in `ct_final02_src` (1 183
`@demo.carbontally.local` users). No account was created. Passwords are supplied only through the
gitignored credential mechanism and are redacted from all findings, logs and evidence by the harness
redactor; no password appears in this report or in any artefact it references.

---

## 11. Production cutover checklist — PREPARED, NOT EXECUTED

> **Reconciled 2026-10-02:** this 17-step checklist remains the *intent* record, but the operational
> package is now the gated **22-step** FINAL-03 sequence in
> `docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md`, which adds the B7/B2′
> preconditions, a migration-order gate, and the evidence / stop condition for every step. **Neither has
> been executed.**

> **Production is a CLEAN INITIALIZATION, not a customer-data migration.** CarbonTally currently has
> **no real customer data**: every organisation, user, consultant, client, report, document,
> calculation, evidence and activity record in the current database is demo/test data. The **7 049
> emission factors are the authoritative non-demo dataset and are preserved.** Nothing below has been
> executed; it is the artefact for the next authorized step.

**Preserve / initialize**

- `supabase/migrations/**` applied in order to the new production database (exact shipped set);
- platform configuration: auth providers/redirect allow-list, JWT secret/key set, `storage` bucket
  definitions (private `documents`, size ceiling), PostgREST roles/grants, RLS enablement;
- the **7 049 emission factors** (authoritative reference dataset) — verified row-for-row;
- required system/bootstrap configuration (platform admin/staff rows, system settings);
- production secrets delivered through the proper secret mechanism (never committed): Supabase URL,
  anon + service keys, JWT secret, database URL, SMTP/email provider credentials, analytics keys.

**Do NOT carry into production as customer data** — demo organisations, demo users, demo consultants,
demo clients, demo reports, demo documents, demo calculations, demo evidence, demo
activity/audit/business records, and the demo credential file.

**Steps**

1. **Backup** — take/verify a managed backup of the *current* state and record the restore point (this
   step is also where B2′ evidence should be captured).
2. **Final database migration** — apply the frozen migration set to the new production database.
3. **Schema verification** — 149 public tables, 149 RLS-enabled, 271 policies (or the then-current
   frozen counts).
4. **7 049-factor verification** — exact count and spot-check checksums; no factor row altered.
5. **Clean production initialization** — bootstrap only platform/system configuration; **no demo
   tenant data**.
6. **Production admin/bootstrap setup** — create the real CarbonTally admin/staff identities through
   the product's own mechanisms (no shared demo password).
7. **Backend deployment** — deploy the frozen commit; environment from the secret store.
8. **Frontend deployment** — deploy the frozen build; verify the production `REACT_APP_*` wiring.
9. **Live authentication** — real sign-up/sign-in, session, logout, password reset.
10. **Live storage** — upload/download/sign through the production bucket with RLS in force.
11. **Live email** — send through the configured provider and confirm *external* receipt (B1's
    criterion, re-proved in production).
12. **Live organisation/customer actor** — owner/admin/member/viewer journeys.
13. **Live consultant actor** — portfolio, client switching, cross-tenant refusal.
14. **Live CarbonTally admin actor** — `/ops` control plane, review/audit surfaces.
15. **Cross-tenant regression** — anonymous + cross-org read/write/Storage refusals (B5 matrix).
16. **Investor/demo journey** — the first real user path end-to-end.
17. **Final acceptance** — recorded by the acceptance authority, not the operator.

---

## 12. Exact repository / environment changes made

> **Reconciled 2026-10-02:** unchanged for the 2026-10-01 pass. The 2026-10-02 reconciliation pass added
> **documentation only** — the in-place edit of this report and the new
> `CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md`; no product code, configuration, migration or test
> file was touched. Working tree now **161** entries (112 untracked / 49 modified), no commit — §16.7.

**Repository (`ct_93d5cdd`) — exactly one addition, no edits:**

- **NEW:** `docs/architecture/CT-FINAL-02-CLOSURE-AND-LIVE-READINESS-20261001.md` (this report).
- Nothing else. `git status` working-tree entries 131 → 132 (this file); `qa_harness/` untouched;
  `frontend/.env.local` untouched (mtime still 2026-09-21); no commit, no push, no stash, no reset,
  no checkout, no cleanup; all pre-existing modifications and untracked files preserved.

**Outside both repositories** (`/home/shomonrobie/ct_local_env/final02_rehearsal/`, disposable and
local-only):

| Artefact | Change |
| --- | --- |
| `nginx.conf` | patched — `proxy_hide_header` for upstream CORS headers in the three proxy locations; added `http://localhost:3000` / `http://127.0.0.1:3000` to the CORS origin map. **Original preserved as `nginx.conf.orig-b3`.** |
| `auth.env` | `GOTRUE_SITE_URL` `http://localhost:3100` → `http://localhost:3000`. **Original preserved as `auth.env.orig-b3`.** |
| containers | `ct_final02_gateway` and `ct_final02_auth` recreated from their (patched) env files on the same network/ports/images (`nginx:alpine`; `public.ecr.aws/supabase/gotrue:v2.195.0`). `ct_final02_rest` and `ct_final02_storage` were **not** restarted. |
| new scripts | `start_local_all.sh`, `stop_local_all.sh`, `b3_browser.py`, `b3_diag_login.py`, `b3_journeys.py`, `b3_textprobe.py`, `b3_d7_ui.py` |
| evidence | `b3/` — sweep JSON + 21 screenshots + findings (raw/normalized/dedup), `b3/journeys/`, `b3/textprobe/`, `b3/d7ui/`, `b3/diag/`, `b3/results/`; `logs/` (sweep, journeys, textprobe, D-7 UI, B5, B4/D-7, login probe, canonical pytest + JUnit XML) |
| processes | frontend dev server restarted on port **3000** with the coherent `REACT_APP_*` exports (the old incoherent server on 3100 was stopped); backend left running (`:8090`, `backend.env`). |

**Files explicitly NOT edited or repaired** (reported instead, as required): the repository
`qa_harness` tree (incomplete packaging), `frontend/.env.local` (stale wiring), project code/config,
RLS/auth/storage/subscription definitions.

## 13. Production mutation statement

**No production mutation of any kind occurred.** Specifically: no production deploy; no production
database connection, read or write; no production rows inserted, updated or deleted; no demo data
deleted or migrated; no production email sent; no real customer account created; no backup created,
restored or reconfigured; no retention, RLS, auth, storage or billing configuration changed; no
migration applied; no commit or push.

> **Reconciled 2026-10-02:** the *unauthenticated* **401** `GET`s described below are the 2026-10-01
> state. On 2026-10-02 the credential existed and the same **GET-only** verifier returned authenticated
> **200**s and read platform backup/PITR state — still **read-only, still no mutation** (§15.1). The
> mutation statement below is otherwise unchanged and remains true for **both** passes.

All work ran against the **disposable local rehearsal stack** (`ct_final02_src` on the local Supabase
container cluster). The only contact with a production-adjacent service was three **unauthenticated,
credential-less `GET` requests** to the Supabase management API while establishing that B2′ cannot be
verified (`api.supabase.com/v1/projects`, `…/projects/{ref}/database/backups`, and one with the
service-role key) — each returned **401**; no data was read and nothing was written. The
`ct_final02_src` database contents were verified unchanged at the end of the task (§4): 149/149/271,
1 206 users, 1 183 demo users, 975/975 organisations active, 7 049 emission factors, 686 storage
objects.

## 14. STOP-CONDITION verdict — **SUPERSEDED 2026-10-02 by §17**

> **Superseded.** The *conclusion* recorded below (no readiness statement is issued) still stands and is
> reinforced by B7 — but the *reason* no longer applies: B2′ is not blocked on a credential any more. The
> credential was supplied and the read-only verification ran, showing a **capability** gap instead
> (§15.1). **Read §17 for the current verdict; the text below is kept as the 2026-10-01 record only.**

**B3: sufficient evidence captured. B2′: BLOCKED — Supabase management credential unavailable.**

Because one of the two required evidence items remains blocked, this task reports the exact blocker
and **does not** issue the "READY FOR INDEPENDENT ACCEPTANCE" statement.

> **FINAL-02 STATUS (operator view):** implementation/verification **preparation complete**, with
> **one open environmental evidence blocker (B2′)** plus the acceptance decision itself.
> **FINAL-02 is NOT accepted, and nothing here should be read as acceptance.**
> When the `sbp_…` credential (or dashboard evidence) is supplied for project `pvwiojoyaqywtzcpbg`,
> B2′ can be closed read-only in minutes using the command in Appendix A — after which the remaining
> open items would be the verifier's decision and the document-owner list corrections (§8).

**For CoStrict / OHD to verify independently** (all inputs are on this machine, read-only):

1. re-run the sanctioned sweep and the journeys (Appendix A) against `ct_final02_src` and confirm
   10/10 authenticated actors and the redirect/scoping behaviour;
2. inspect `final02_rehearsal/b3/**` (raw findings, screenshots, JSON) and judge the three finding
   classes in §1.6 — in particular confirm the anonymous-separation findings as timing artifacts and
   the table-rule findings as calibration artifacts;
3. re-run the canonical pytest set (expect **314/0/0/0, EXIT=0**), the B5 matrix (**29/29**) and the
   B4/D-7 matrix (**35/35**) and confirm the database integrity figures in §4;
4. confirm the repository delta is exactly this one new document (§12) and that
   `ct_final02_src`/production were not mutated (§13).

---

## 15. FINAL-02 current status matrix — the single authoritative table (reconciled 2026-10-02)

> **This is the one current status table for FINAL-02.** Everything above dated 2026-10-01 is the
> historical record; where a statement above disagrees with this table, **this table is current**.
> No open item was removed and no recorded measurement was altered.

| # | Acceptance area | Current status (2026-10-02) | Evidence | Remaining dependency / owner action |
| --- | --- | --- | --- | --- |
| **B1** | External email delivery (A2Hosting SMTP) | **CLOSED / SATISFIED BY EXISTING EVIDENCE** | Owner-supplied 2026-09-29 "CarbonTally SMTP Delivery Test" received through the canonical path; the "credential unavailable" premise was withdrawn 2026-10-01 (live-evidence pass Part H.2) | none — **must not appear in the open blocker list** (two non-B1 observations stand: F.3 implicit-TLS/465 limitation; live `system_settings` has no `email_provider` row) |
| **B2′** | Managed Supabase backup / PITR | **EVIDENCE OBTAINED — CAPABILITY ABSENT** (open) | §15.1 — read-only Management API, `GET` only, 2026-10-01 and again 2026-10-02 | **Owner (commercial / configuration)**: production recovery-posture decision; then re-run the same read-only verifier. Cline cannot close it |
| **B3** | Authenticated browser / admin acceptance | **EVIDENCED — no B3 blocker remains** | 2026-10-01 sanctioned sweep: 10/10 actors, J1–J6 journeys, anonymous separation, logout/re-login, cross-tenant separation, D-7 through the UI (§1; evidence index in Appendix B). **Not re-run on 2026-10-02** | none for evidence. *Re-running browser work was impaired while B7 stood (§15.2); B7 is now remediated in the working tree (§15.2.1), so re-runs are unblocked* |
| **B4** | D-7 inactive-organisation denial | **PASS — application layer independently verified (94/94, CoStrict 2026-09-30), live/PostgREST facet re-derived 2026-10-02 (35/35, exit 0), and re-run 35/35 at the B7-fixed working tree 2026-10-02 (§16.10)** | §5 + §16.3 + §16.10 | none |
| **B5** | JWT / PostgREST + Storage object isolation | **PASS — 29/29, exit 0, re-derived 2026-10-02** | §6 + §16.2 | none |
| **B6** | Canonical schema / local-rehearsal gap | **RECONCILED — the 19 → 33 enumeration was corrected; B6 remains CONFIRMED (strengthened, not weakened)** | matrix §5.0/§5.11/§6/§8.1; CoStrict verification §5 (the single material evidence defect it found) | document-owner action only; no "19 missing" reading remains current |
| **Backup / restore** | BACKUP-01 · BACKUP-02 · D1–D4 · artifact/restore/drill | **IMPLEMENTED + LOCALLY VERIFIED — 297 backup tests green; canonical drill re-run 2026-10-02** | §16.4–§16.5 | **independent verification of the artifact/restore/DR-20 evidence still outstanding**; H-series handoff items remain (DR-20 report §10, now **+ H13**) |
| **DR-20** | Recovery drill (RPO = 0 for a completed backup; RTO ≈ 24 s) | **RECORDED, REPRODUCIBLE, APPLICATION-LEVEL VALIDATED; PO gate accepted — recovery evidence CLOSED** | DR-20 report §4.1 / §11 | **runtime basis reopened for re-verification by B7** (§15.2): the running app is not stable for more than ≈45 s against a database lacking the BACKUP tables; **B7 is now remediated in the working tree (§15.2.1)** — the reopened basis is re-verifiable |
| **Storage-object backup** | Object-byte backup | **IMPLEMENTED / WIRED — NOT INDEPENDENTLY VERIFIED — P2 under the current architecture** (no real customer documents exist) | DR-20 report §4.3; matrix §5.6 | none added — **do not invent a P1 requirement** |
| **B7** *(NEW 2026-10-02)* | Backup worker ↔ asyncpg pool exhaustion | **REMEDIATED + LOCALLY VERIFIED (2026-10-02 second pass — §15.2.1); not yet closed** — the fix is in the working tree only, so the gate stays open until it is committed (cutover gate P2) and B4 is re-run | §15.2 **(defect)** · §15.2.1 **(remediation + evidence)** | **Implementer**: ~~release the leased connection in `backup/jobs.py` (+ the same idiom in `backup/service.py`); then re-run the backup suites, the drill and B4~~ — **done, including the B4 re-run (§16.10: 35/35, EXIT=0)**; **remaining: commit the fix, apply the two BACKUP migrations before the worker runs anywhere**. Blocks §12 local readiness *until committed*; would exhaust production connections from a commit that predates the fix |
| **Acceptance** | FINAL-02 independent acceptance | **NOT granted — and not claimable on this evidence** | — | **CoStrict / OHD** |

### 15.1 B2′ — read-only managed backup/PITR re-verification (2026-10-02)

The same GET-only verifier as 2026-10-01 (`~/ct_local_env/final02_rehearsal/b2/b2_verify.py`; it
contains **no** POST/PATCH/PUT/DELETE). Credential present in the gitignored `backend/.env`
(`SUPABASE_ACCESS_TOKEN`, `sbp_` prefix, 47 chars, `sha256[:12] = 6c2b00cea2bf`); project ref pinned
from `SUPABASE_LIVE_URL` = `pvwiojoyaqywtydzcpbg`. Run at **2026-10-02T08:27:16Z**; summary written to
`b2_verification_20261002T082716Z.json`.

```text
GET /v1/projects                                  -> 200  authenticated=True  target_ref_present=True
GET /v1/projects/{ref}                            -> 200  status ACTIVE_HEALTHY · region eu-west-2
GET /v1/projects/{ref}/database/backups           -> 200  backups_count=0 · pitr_enabled=False · walg_enabled=True
GET /v1/projects/{ref}/database/backups/schedule  -> 402  entitlement_required — "requires the Enterprise organization plan"
GET /v1/projects/{ref}/billing/addons             -> 200  selected_addons=[]  (pitr offered, not selected)
GET /v1/organizations/{org}                       -> 200  plan=free · name=CarbonLedger
GET /v1/organizations/{org}/entitlements          -> 200  backup.retention_days value=0 enabled=false;
                                                         backup.schedule enabled=false; pitr.available_variants set=[]
```

**Result: unchanged from 2026-10-01 — the live project has neither managed backups nor PITR.** The
acceptance criterion ("managed backup/PITR confirmed") is **not satisfied**; only the *evidence*
requirement is. Closing it requires an **owner commercial/configuration action** (leave the `free`
plan so daily backups with non-zero retention exist, and/or purchase the `pitr` add-on), after which
the same verifier closes it in minutes. There is no substitute: the anon key, the `service_role` key
and the Postgres DSN are data-plane credentials and cannot read platform backup/PITR state. Nothing
was mutated — no plan change, no add-on purchase, no schedule PATCH, no production connection.

### 15.2 B7 — NEW: the backup worker exhausts the application's asyncpg pool (measured 2026-10-02)

**A genuine, newly introduced FINAL-02 blocker**, found while re-running the FINAL-02 regression set.
It blocks §12 (local readiness), makes browser/API rehearsals unreliable beyond a few tens of seconds,
and on a production database it would exhaust connections.

**Symptom.** After a clean backend start the API answers normally for ≈45 s and then every DB-backed
endpoint stops responding. `/health` and `/api/v3/accounting/context` time out; routes served through
**PostgREST** (org/member routes) keep working — which is why a PostgREST-only matrix can still pass.
The B4 (D-7) matrix fails only its `accounting/context` assertions (`actual=0`, transport timeout)
while every member-path assertion still passes.

**Measured timeline** (backend started ≈14:55:05; `/health` polled every 15 s; `conns` = connections
to `ct_final02_src` in `pg_stat_activity`; `worker_tick_failures` = occurrences of
`backup worker tick failed` in `backend.log`):

```text
14:55:15  health=200/0.006s  conns=17  worker_tick_failures=1
14:55:30  health=200/0.010s  conns=18  worker_tick_failures=2
14:55:45  health=200/0.021s  conns=19  worker_tick_failures=4
14:56:00  health=000/20.0s TIMEOUT      worker_tick_failures=5
14:56:36  health=000/20.0s TIMEOUT      worker_tick_failures=5
```

Connections grow **monotonically, ≈1 per worker tick**, and latency degrades with them.

**Two compounding causes.**

1. **The rehearsal database does not carry the two new BACKUP migrations**, so the worker errors on
   every tick:

   ```text
   backup worker tick failed (loop continues)
     File "backend/backup/worker.py", line 151, in _run_loop     -> await self.tick()
     File "backend/backup/worker.py", line 162, in tick          -> await self._jobs.release_stale(...)
     File "backend/backup/jobs.py",   line 485, in release_stale -> await connection.execute("UPDATE public.backup_jobs ...")
   asyncpg.exceptions.UndefinedTableError: relation "public.backup_jobs" does not exist
   ```

   `ct_final02_src` sits at the pre-BACKUP schema; the two new migrations are
   `20261026000000_ct_backup_01_backup_jobs.sql` and
   `20261027000000_ct_backup_02_backup_sets_and_verification.sql`.

2. **The connection lease is never released — the cause of the growth, and the reason a schema fix
   alone would not be enough:**

   ```text
   backend/backup/jobs.py:276-286      async def _pool_connection_factory():
                                           pool = await get_service_pool()
                                           return await pool.acquire()      # acquired, never released
   backend/backup/service.py:390-399   same idiom
   ```

   Every `BackupJobStore` method does `connection = await self._connection()` and never releases it;
   a `grep` for `release(` / `async with` across `backend/backup/` finds **no release path at all**.
   The shared pool is `asyncpg.create_pool(dsn, min_size=1, max_size=5)`
   (`backend/infra/supabase.py:139`), so the application's DB path is starved after ≈5 leaked
   acquisitions and the leak then eats into the PostgreSQL budget (`max_connections = 100`).

**What is new.** The leak idiom in `backup/service.py` predates this workstream; what is **new** is
(a) `backend/backup/jobs.py` and `backend/backup/worker.py` (both **untracked**), and (b) the
composition-root wiring that makes the loop run continuously inside the API process —
`backend/main.py:318-355` starts `get_backup_worker(...)` from the FastAPI `startup` event. Before that
wiring, the idiom was never exercised by a long-running process.

**Why the backup suites do not catch it.** They inject their own `connection_factory`, so the default
pool-acquiring path — and therefore the lease leak — is never exercised by the 275 unit + 22
integration tests, nor by the drill (a process that exits).

**Blast radius.** Local rehearsal (§12) unusable beyond ≈45 s; browser evidence re-runs compromised;
**production would lose its DB-backed API within minutes of start-up for every backup tick.**

**Recommended minimal fix (NOT applied in this pass — see §17).** Give the store/service a real lease:
either convert `_connection()` into an async context manager doing
`async with pool.acquire() as connection: yield connection` (which releases the asyncpg
`PoolConnectionProxy`) and switch each call site to `async with self._connection() as connection:`, or
keep the factory API and add `finally: await connection.release()` wherever a pooled connection is
leased. Then re-run the backup suites, the canonical drill and the B4 matrix. Independently, the
worker should treat "the backup tables are absent" as a terminal, backed-off condition rather than an
error per tick.

### 15.2.1 B7 remediation — post-fix verification, second pass (2026-10-02)

**Status: remediated in the working tree and locally verified. Not committed — and therefore not yet a
closed gate.** Evidence pack: `docs/cline/evidence/FINAL-03-P1-B7-20261002/01-b7-gate/` (artifacts,
method, clause tables, reproduce commands). This subsection records the outcome; §17 records the
position.

**The fix (working tree, uncommitted).** `backend/backup/jobs.py` and the same idiom in
`backend/backup/service.py` now pair the acquire with a release on **every** path — normal, raising and
cancelled. `backend/backup/worker.py` gained `is_missing_backup_table()` (SQLSTATE `42P01` **and** a
`backup_` relation name) so an absent backup schema is **one** structured report followed by back-off
(`DEFAULT_MISSING_TABLE_BACKOFF_SECONDS`), re-armed only after a successful tick — no per-tick
traceback. New regression module `backend/tests/unit/backup/test_b7_connection_lease.py`
(**untracked**, 12 tests: the pre-fix control double; lease return across tick cycles; no connection
held *between* ticks; lease return on the normal / raising / **cancelled** paths; injected bare
connection and injected acquire context; `is_missing_backup_table` matching only `backup_*` relations;
report-once + back-off; re-arm after success). `grep` for the release sites is evidence item
`lease-site-grep.txt` — the pre-fix statement in §15.2 that the grep "finds **no release path at all**"
is now, correctly, historical.

**The measurement.** `tools/b7_pool_soak.py` (new, untracked) drives the real worker against a real pool
and a real `/health`, refuses any non-loopback or non-`ct_*` database, and — decisively — counts a
shortfall as a leak **only if it persists through quiescence**. That is why the control exists and why
the control is part of the evidence:

| Run (600 s each, loopback only) | Database | Verdict |
| --- | --- | --- |
| schema-complete | `ct_b7_schema_1790937075` — schema-only clone of `ct_local_93d5cdd` with both BACKUP migrations applied (136 tables; `backup_jobs` has `kind`/`backup_set_id`/`verification_status`) | **CLEAN — 5/5 clauses true** |
| migration-behind | `ct_local_93d5cdd` (the §15.2 rehearsal condition: no `backup_*` tables) | **CLEAN — 5/5 clauses true**, taken twice: harness revision 1 and again with the **final** shipped revision (`soak-b7-after-rev2.json`: `elapsed_s = 600.1`, 2,902 statements all `missing-table`, 1 shortfall observed / 1 cleared, `pool_size_max = 2`, `pool_idle_min = 1`, **`health_timeouts = 0`**, `worker_missing_table_reports = 1` for 120 attempts, `worker_per_tick_failures = 0`, `violations = []`) |
| **control** (pre-fix idiom `return await pool.acquire()`, same detector) | same | **leak reproduced — the detector fires**: 3 shortfalls observed, **0 cleared**; the run self-stops after the 3rd at `elapsed_s = 6.6`, so its `health_pool_path_responsive = true` is an artifact of the early stop, not evidence of health |

Clauses, schema-complete run: `no_leased_connection_kept`, `health_pool_path_responsive`,
`worker_loop_alive_for_the_whole_soak`, `missing_schema_reported_once` (schema present ⇒ **expect 0**
reports; **0** observed ⇒ true) and `missing_schema_not_a_per_tick_error` — all **true**; **2,862**
worker statements, **0** `missing-table`, **318** no-op (`BackupJobConflictError` = another worker holds
the job), pool `size == idle` for the whole run (`pool_size_max = 2`), **2,862** `/health` probes with
`health_max_ms = 33.9` and **`health_timeouts = 0`**, `worker_missing_table_reports = 0`. Leases:
**393 shortfalls observed, 393 cleared, 0 permanent** (the migration-behind run: 1 report for 120 worker
attempts, `worker_per_tick_failures = 0`, 0 timeouts, and the pool *shrinks* — the opposite of §15.2's
monotonic ≈1-connection-per-tick growth).

**Suites and drill.** `tests/unit/backup` + `tests/integration/backup` = **275 tests · 0 failures ·
0 errors · 0 skipped · EXIT=0** — authoritative artifact `junit-backup-suites.xml` (with the captured
stdout `pytest-backup-suites.stdout.txt`) in the evidence pack, re-taken at the end of the pass,
`timestamp="2026-10-02T17:09:54.458948+06:00"`. The 12-node B7 regression module is green on its own
(12 passed, EXIT=0). The canonical recovery drill
(`tools/backup_recovery_drill.py`) **completes, EXIT=0**, and against `ct_final02_src` — the exact
source of the §16.5 record — it reproduces §16.5 in detail (phase 3: 96 migrations, **94 applied, 1
already present, 1 failed = `20260801000000_rc2_constraints.sql`**; phase 2 `pg_restore` rc=1 for the
Supabase-internal `secrets` table only, all deltas 0; phase 4 the known harness truncate refusal). The
fix is drill-neutral; the drill drives the production `BackupService`, i.e. the repaired code, and
completes without pool exhaustion.

**Count reconciliation (the "275" question).** §16.1's and FINAL-03 §5's **275 unit** is the *four-path*
composite: `tests/unit/backup` **241** (pre-fix) + `test_backup_admin_api.py` **17** +
`test_backup_export.py` **8** + `test_backup_recovery_drill_guard.py` **9**. Post-fix the same composite
is **287**, because the new B7 module adds **12** to `tests/unit/backup` (**241 → 253**). Separately,
the two-path run `tests/unit/backup` + `tests/integration/backup` (253 + 22) also totals **275** — a
coincidence; quote the paths with any count. §16.6's **314** is a different set (the seven §4.1 matrix
files).

**What this pass did not do.** The B4/D-7 35/35 matrix was **not** re-run *in this pass* (it stands as
§16.3). Nothing was committed, staged, pushed, reset or cleaned; no production and no non-loopback
database was contacted. Acceptance, and any independent verification of this evidence, remains with
CoStrict / OHD.

**Update (2026-10-02, later).** The B4/D-7 matrix **has since been re-run** at this same B7-fixed
working tree — **35/35 checks passed, EXIT=0**, with **no D-7 regression** (§16.10). The B7 item itself
is still *not* a closed gate: the fix lives only in the working tree until it is committed (cutover gate
**P2**).

---


## 16. FINAL-02 regression re-run — 2026-10-02 (the bounded set)

### 16.1 Environment, and the summary of every suite

**Environment.** HEAD `cabdca8380415e73a25cf23eb393d0b15c0af391` (branch `p8-release-reconciled`) —
unchanged. Local **disposable** rehearsal stack: gateway `127.0.0.1:54440`
(`auth/v1/health` 200 · `rest/v1/` 200 · `storage/v1/status` 200), application database
`ct_final02_src` (PostgreSQL 17.6 on `127.0.0.1:54426`), backend `127.0.0.1:8090` (restarted cleanly
before the B4 run so that B7 had not yet bitten), frontend `localhost:3000`. **No production system was
contacted** except the read-only Management-API `GET`s of §15.1.

| Suite | Result |
| --- | --- |
| Canonical FINAL-02 pytest set (the 7 files of matrix §4.1) | **314 tests · 0 failures · 0 errors · 0 skipped · EXIT=0** (counts read from the JUnit XML) |
| B5 isolation matrix (`matrix_b5.py`) | **29/29 PASS · EXIT=0** |
| B4/D-7 matrix (`matrix_b4_d7.py`) | **35/35 PASS · EXIT=0** |
| Login / password-grant probe (`login_probe.py`) | **9/9 real password grants · EXIT=0** |
| Backup unit suites (`tests/unit/backup`, `test_backup_admin_api.py`, `test_backup_export.py`, `test_backup_recovery_drill_guard.py`) | **275 tests · 0 failures · 0 errors** — this is the *four-path* composite; for the same four paths **post-fix it is 287**, because the new B7 module adds 12 to `tests/unit/backup` (**§15.2.1**, count reconciliation) |
| Backup integration (`tests/integration/backup`, incl. the 13-case restore suite) | **22 tests · 0 failures · 0 errors** |
| Canonical recovery drill (`tools/backup_recovery_drill.py --source ct_final02_src --target ct_final02_src_restored_1790929982 --keep-target`) | Phases 1–4 as below |
| Database integrity (read-only SQL on `ct_final02_src`) | 149 public tables · **149 RLS-enabled** · 271 policies · **7,049 emission factors** · 975 organisations, **975 active** · 1,206 auth users (1,183 `@demo.carbontally.local`) · 686 storage objects · `documents` bucket private with the 10,485,760-byte ceiling |
| Repository integrity | HEAD unchanged; working tree **160** entries (**111** untracked, **49** modified) at the time of this measurement; `qa_harness/` untouched; no commit / push / reset / clean / stash. Including this pass's two documentation additions (this report + the FINAL-03 package) the current count is **161** (**112** untracked, **49** modified) — §16.7 |

### 16.2 B5 isolation matrix — 29/29, EXIT=0

Re-derived live against the rehearsal stack: real password grants (no fakes), token `role`/`aud`
claims, expired / wrong-secret / malformed JWT refusals (**401**), org A owner → A rows **78** /
B rows **0**, org B owner → A rows **0** / B rows **1**, member/admin/viewer scoping, anonymous
denial, cross-org `INSERT`/`UPDATE`/`DELETE` refused, and per-org Storage download/sign/upload
isolation including cross-tenant and anonymous refusal. Same result as the 2026-10-01 run (§6) —
**no regression**.

### 16.3 B4 / D-7 matrix — 35/35, EXIT=0

**B4 detail (fresh backend, single instance).** Baseline: owner/admin/member/viewer member-path **200**,
accounting context **200**, org B **200**, staff audit **200**, consultant `[200, 200]`. After the
product's own `POST /api/admin/bulk/organizations/status` suspends org A: all four roles **403
"suspended"**, accounting context **403**, owner/admin do **not** bypass the guard, the denial is
**non-disclosing (1 distinct message)**, org B unaffected (**200**), internal staff unaffected
(**200** ×2), consultant portfolio unaffected (**200**) but denied on the suspended client's context
(**403**) — then reactivation through the same handler restores every path (**200** ×8). Total
**35/35**, exit 0. `organizations.is_active` for org A = **`t`** before and **`t`** after
(**975/975** organisations active).

### 16.4 Backup unit and integration suites — 275 + 22 tests, 0 failures, 0 errors

```text
tests/unit/backup  +  tests/unit/api/test_backup_admin_api.py
                   +  tests/unit/tools/test_backup_export.py
                   +  tests/unit/tools/test_backup_recovery_drill_guard.py
                     -> 275 tests · 0 failures · 0 errors · 0 skipped
tests/integration/backup   ->  22 tests · 0 failures · 0 errors · 0 skipped
                              (incl. the 13-case restore-integration suite)
```

Counts read from the JUnit XML. **These green suites are not evidence against B7** (§15.2): every one
of them injects its own `connection_factory`, so the default pool-acquiring path — the leaking one —
is never exercised.

### 16.5 Canonical recovery drill — 2026-10-02

**Drill detail (2026-10-02).**

```text
Phase 1  artifact 967,854 B · ciphertext_only True · envelope v1/AES-256-GCM/key-v1 · members 154
         checksums verified 152 · 149 tables · 14,263 rows · 271 policies · 103 triggers · 37 functions
Phase 2  pg_dump 3,233,160 B · pg_restore rc=1 (only: permission denied for table secrets — a
         Supabase-internal object) · missing tables 0 · row mismatches 0
         index/constraint/policy/rls-table/bucket deltas all 0
Phase 3  96 migrations · 94 applied · 1 already present · 1 failed =
         20260801000000_rc2_constraints.sql (NOT NULL conversations.organization_id vs 1 NULL row)
         — the known data-dependent, immutable-migration case; unchanged
Phase 4  the known harness truncate refusal (append-only ledger guard) — environment/harness; also
         positive evidence that the restore preserved the guard
```

### 16.6 Canonical FINAL-02 pytest set — 314 tests, 0 failures, 0 errors, EXIT=0

The 7 files named by the FINAL-02 matrix §4.1 (F-05-R1 org-scope, D-7 lifecycle decisions, D-7
F1/F2/F3 enforcement, Storage Step 1, Storage Step 2, G1/G2 emissions scope + staff access, FINAL-02
email provider), run with `-q -p no:cacheprovider --junitxml=…`: **314 tests · 0 failures · 0 errors ·
0 skipped · 68.9 s · EXIT=0**. The JUnit XML is authoritative; the stdout summary line is swallowed by
this terminal's shell integration (Appendix A).

### 16.7 Repository status, and the exact backup files awaiting a commit

**Nothing was committed, staged, reset, cleaned, stashed or checked out.** HEAD and branch are
unchanged from the start of this pass; the entries found at the start (111 untracked + 49 modified —
**160** total) are preserved exactly as found. This reconciliation pass added **two documentation files
and nothing else** — this report (edited in place; it was itself untracked from the 2026-10-01 pass) and
`docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md` — so the working tree is now
**161** entries (**112** untracked + **49** modified). **No product code, configuration, migration or
test file was touched by the reconciliation.**

**The backup/restore implementation is not yet on the repository's normal tracking path**
(DR-20 handoff item **H6**); the exact set is:

```text
 M backend/backup/__init__.py                         M backend/backup/errors.py
 M backend/backup/settings.py                         M backend/backup/storage.py
 M backend/tests/unit/backup/test_storage_and_settings.py
?? backend/api/v3_backups.py                          ?? backend/backup/jobs.py
?? backend/backup/objects.py                          ?? backend/backup/policy.py
?? backend/backup/restore.py                          ?? backend/backup/retention.py
?? backend/backup/s3store.py                          ?? backend/backup/sigv4.py
?? backend/backup/verification.py                     ?? backend/backup/worker.py
?? backend/tests/integration/backup/test_restore_local.py
?? backend/tests/unit/api/test_backup_admin_api.py    ?? backend/tests/unit/backup/test_jobs.py
?? backend/tests/unit/backup/test_sigv4_and_s3store.py
?? frontend/src/v3/__tests__/backup-admin-api.test.js ?? frontend/src/v3/ops/BackupsTab.jsx
?? supabase/migrations/20261026000000_ct_backup_01_backup_jobs.sql
?? supabase/migrations/20261027000000_ct_backup_02_backup_sets_and_verification.sql
?? docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_RESTORE_COMPLETE_IMPLEMENTATION_20261002.md
```

This pass holds **no authorization to commit or push**, and the instruction was explicit: leave them
untouched and document exactly what must be committed before production. That is what was done. Two
operational consequences must be respected at handoff: (1) the two BACKUP migrations must be applied
**before** the backend is started in any environment where the backup worker runs, otherwise B7
manifests immediately; and (2) per §15.2 the lease leak remains even *with* the migrations applied,
until the code fix lands.

### 16.8 Classification of every failure observed in this pass

| Observation | Classification | Notes |
| --- | --- | --- |
| Worker `UndefinedTableError: relation "public.backup_jobs" does not exist`, every tick | **newly introduced** (BACKUP-01/02) **+ environment-dependent trigger** (the rehearsal DB is 2 migrations behind the new head) | error-only; the material part is cause 2 of §15.2 |
| asyncpg pool exhaustion → `/health` and `/api/v3/accounting/context` hang ≈45 s after start | **newly introduced — genuine FINAL-02 blocker (B7)** | reproducible; not pre-existing; production-relevant |
| B4 matrix baseline `FAIL` in the first two attempts (`actual=403`, then `actual=0`) | **environment-dependent / operator-induced** | the 403s came from a demo organisation left suspended by an interrupted concurrent sweep (since restored through the product's own handler); the `0`s were B7. The clean single-instance run is **35/35** |
| Phase 3 `20260801000000_rc2_constraints.sql` failure | **pre-existing, data-dependent** | immutable historical migration vs copied data (matrix §5.4); untouched by this work |
| Phase 2 `pg_restore rc=1` on `vault.secrets` | **pre-existing, provider-internal** | Supabase-owned object; every application object restored exactly |
| Phase 4 integration-suite setup error (append-only ledger refuses `TRUNCATE`) | **environment / harness limitation** | correct product behaviour; the harness target must be empty or purge-authorised |
| 2026-10-01 sweep's 352 raw findings (326 table-rule, 21 anon-separation timing) | **history — not re-run in this pass** | classified in §1.6; no new browser run was made |

### 16.9 Local artefacts left in place (manual cleanup, NOT performed)

Everything the rehearsal created lives **outside the repository**, in the disposable local cluster
(`supabase_db_carbon_ledger`). Nothing was dropped or deleted; the four databases that matter are:

| Database | Size | Origin | Disposition |
| --- | --- | --- | --- |
| `ct_final02_src` | 39 MB | the **reconstructed** FINAL-02 rehearsal source (2026-10-01), rebuilt from the live dump and read-only verified at 149/149/271 · 7,049 factors · 975/975 active | **KEEP** — the source of truth for the FINAL-03 rehearsal |
| `ct_final02_src_restored_1790929982` | 37 MB | **this pass's** drill target (`--keep-target`, epoch 1790929982) | manual drop candidate |
| `ct_final02_src_restored_82482` | 37 MB | the 2026-10-01 drill target | manual drop candidate |
| `ct_dr20_rest_1790925322` | 38 MB | the DR-20 report's restore target (epoch 1790925322) | manual drop candidate |

The full cluster holds ~80 other historical `ct_*` rehearsal/verification databases (13–39 MB each) —
all pre-existing, none created or altered by this pass. **No drop was executed here**; the owner may
run, at their discretion and only when no drill is in flight:

```bash
# MANUAL / NOT EXECUTED — drop only the three superseded drill targets, never ct_final02_src
for db in ct_final02_src_restored_1790929982 ct_final02_src_restored_82482 ct_dr20_rest_1790925322; do
  docker exec supabase_db_carbon_ledger psql -U postgres -c "DROP DATABASE IF EXISTS $db"
done
```

Local containers (`ct_final02_gateway`, `ct_final02_auth`, the frontend dev server, the backend on
`:8090`) are likewise left running for the owner's continued use; `stop_local_all.sh` stops them
without touching any database.

### 16.10 B4 / D-7 matrix — re-run at the B7-fixed working tree (2026-10-02, later pass)

The one part of ordered action 1 that the §16 pass left outstanding — **re-running the B4/D-7 matrix** —
has now been done, against the **same application code that carries the §15.2.1 B7 fix**. This closes
the loop between "B7 remediated in the working tree" and "the application layer is unaffected": the D-7
proof is re-derived **35/35, EXIT=0**, matching §16.3 exactly.

**Environment and boundaries.** Local **disposable** rehearsal stack only — gateway `127.0.0.1:54440`,
database `ct_final02_src` (PostgreSQL, `127.0.0.1:54426`), frontend `localhost:3000`, and a **freshly
restarted single backend** on `127.0.0.1:8090` (§16.1's "fresh backend, single instance" — the stale
duplicate `:8090` workers were stopped first; one listener remained, pid confirmed after the run).
**No production or shared system was contacted**; no implementation code was changed; nothing was
committed, pushed, reset or cleaned. HEAD/branch unchanged (`cabdca8380415e73a25cf23eb393d0b15c0af391` /
`p8-release-reconciled`), and the working tree is **preserved as found** (165 entries: 115 untracked +
50 modified — unchanged by this rerun).

**Command (local only):**

```bash
cd /home/shomonrobie/ct_93d5cdd && \
  backend/.venv/bin/python /home/shomonrobie/ct_local_env/final02_rehearsal/matrix_b4_d7.py
```

**Result — 35/35 PASS, EXIT=0.** Baseline (org A active): the four org-A roles 200 on the member path
and on the accounting context; org B 200; staff 200; consultant `[200, 200]`. After the product's own
`POST /api/admin/bulk/organizations/status` suspends org A: the four roles **403 "suspended"**, the
accounting context **403**, owner/admin do **not** bypass the guard, the denial is **non-disclosing
(1 distinct message)**, org B **200**, internal staff **200 ×2**, the consultant portfolio **200** while
the suspended client's context is **403**; reactivation through the same handler restores **every** path
(**200 ×8**). `organizations.is_active` for org A is **`t`** before and **`t`** after the run (org B
`t` throughout).

**B7 × D-7 interaction.** The §15.2.1 change is confined to the backup worker's connection-lease idiom
(`backend/backup/jobs.py` and `backend/backup/service.py` `_pool_connection_factory` returning the pool's
*acquire context*, plus the worker's terminal handling in `backend/backup/worker.py`); it does not touch
the D-7 auth/scope code paths. Running this matrix **with** the fix in the working tree — and on a fresh
single backend — reproduces §16.3 exactly, so there is **no D-7 regression**, and the earlier
`actual=0` transport timeouts (§16.8) do not recur.

**Evidence (outside the repository).**
`final02_rehearsal/logs/b4_d7_rerun_20261002/` — `b4_d7_rerun.log` (stdout: `B4 (D-7) MATRIX: 35/35
checks passed`, `EXIT=0`), `b4_d7_matrix_20261002.json` (`total 35 / passed 35 / failed 0`),
`commands.log` (environment, commands, `exit_code=0`), `b4_d7_matrix_pre_rerun.json` (the §16.3 result,
preserved before the rerun) and `start_local.log`. The runner's canonical output
`final02_rehearsal/logs/b4_d7_matrix.json` also reflects this run.

**Status effect.** Ordered action 1 (§17) is now **fully done** — B7 fix + suites + drill + **B4/D-7
re-run**. The **B7 gate itself is not closed**: the fix still lives only in the working tree and must be
committed (cutover gate **P2**) before it is. This subsection records the re-run; **it grants no
acceptance** — FINAL-02 remains **OPEN** pending B2′ (owner) and the B7 commit, and acceptance is
CoStrict / OHD's alone.

---

## 17. FINAL-02 verdict (2026-10-02) — the current verdict; §14 is superseded

> **VERDICT: FINAL-02 is still OPEN. It is *not* ready for a "ready for independent acceptance"
> statement, and it must *not* be accepted on this evidence. No acceptance is granted or implied here
> — that decision belongs to CoStrict / OHD alone.**

Three things distinguish this verdict from §14's:

1. **B2′ changed from an *evidence* blocker to a *capability* blocker.** The management credential was
   supplied and the GET-only verification ran (twice), so the evidence requirement is met — and it
   **proves the acceptance criterion is not met**: 0 managed backups, PITR disabled, no add-on,
   `backup.retention_days = 0`, organisation on the `free` plan (§15.1). This is now a commercial /
   configuration decision for the owner, not a verification task for Cline.
2. **B7 was newly introduced and is a genuine blocker.** The BACKUP-01/02 backup worker, wired into the
   API lifespan, leaks one pooled PostgreSQL connection per tick and starves the application's asyncpg
   pool ≈45 s after start-up; every DB-backed endpoint then hangs and, on production, DB access would be
   lost within minutes (§15.2).
3. **B3's evidence stands, but its re-runnability is impaired while B7 stands.** No new browser sweep was
   run in this pass; the 2026-10-01 sweep remains the B3 record.

**Consequently**, the honest current position is:

| Item | Position |
| --- | --- |
| B1 | closed — must not be re-opened or re-listed as a blocker |
| B2′ | **OPEN — capability**; owner decision, then re-run the read-only verifier |
| B3 | evidenced (2026-10-01); not re-run; impaired while B7 stands |
| B4 | PASS, re-derived **35/35** (§16.3) and **re-run 35/35 at the B7-fixed tree** (§16.10) |
| B5 | PASS, re-derived **29/29** (§16.2) |
| B6 | reconciled as a *documentation* correction — status unchanged/confirmed (matrix §5.0/§5.11) |
| Backup / restore / DR-20 | implemented and locally verified; **independent verification still outstanding**; runtime basis reopened by B7 |
| **B7** | **remediated + locally verified (2026-10-02, §15.2.1)** — two 600 s soaks clean (schema-complete and migration-behind), the pre-fix control still fires, suites **275/275 EXIT=0**, the drill reproduces §16.5; **still open as a *gate*** until the fix is committed (P2). The dependent **B4 re-run is done (§16.10: 35/35, EXIT=0, no D-7 regression)** |
| Acceptance | **not granted** |

**Nothing in this pass changed any product code, configuration, migration, RLS/auth/storage/subscription
semantic, or any production system; nothing was committed, staged, pushed, reset or cleaned.** The only
repository changes are **documentation**: this report, edited in place, plus the new
`CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md` (§16.7). B7 is **reported, not fixed** — deliberately,
because a fix would touch product code that this pass is not authorized to change, and because the
implementer's re-run of the backup suites and the drill must follow the fix.

**Second pass, later the same day (2026-10-02) — B7 remediated in the working tree, and verified.** The
paragraph above is the record of the *§16 pass* and stays true of it. In the second pass the
implementer applied the §15.2 minimal fix (lease released on every path in `backend/backup/jobs.py` and
`backend/backup/service.py`; a missing backup schema made a terminal, backed-off condition in
`backend/backup/worker.py`), added the 12-test regression module
`backend/tests/unit/backup/test_b7_connection_lease.py`, and ran the live evidence recorded in §15.2.1
and filed in `docs/cline/evidence/FINAL-03-P1-B7-20261002/01-b7-gate/`: two 600 s soaks **clean** on
both a schema-complete database and the migration-behind one, the pre-fix **control still firing**, the
backup suites **green (275/275, EXIT=0)**, and the canonical drill **completing** with §16.5's outcome
reproduced. That pass also added no commit: the fix, the new test module and the new soak tool are
**untracked/modified working-tree files**, exactly like the rest of the BACKUP set in §16.7 — which is
precisely why **P2** exists and why B7 is *verified* but not yet a *closed gate*.

**Ordered next actions (owners named, none performed here):**

1. **Implementer** — ~~release the leased connection in `backend/backup/jobs.py` (and the same idiom in
   `backend/backup/service.py`); make a missing backup table a terminal, backed-off condition in
   `backend/backup/worker.py`. Re-run the backup unit + integration suites, the canonical drill and the
   B4 matrix.~~ **DONE in the working tree, 2026-10-02 second pass** (§15.2.1): fix applied; suites
   **275/275 EXIT=0**; drill **completes** and reproduces §16.5; two 600 s soaks **clean** with the
   control firing. **The last part of this item — the B4/D-7 matrix re-run — is now DONE as well
   (§16.10: 35/35 checks passed, EXIT=0, at this same B7-fixed working tree).**
2. **Implementer / release owner** — apply the two BACKUP migrations before starting the backend
   anywhere the worker runs, and commit the BACKUP-01/02 file set listed in §16.7 (H6) — which must now
   also include the B7 fix, the B7 test module and `tools/b7_pool_soak.py`.
3. **Owner (commercial / configuration)** — decide the production recovery posture for project
   `pvwiojoyaqywtzcpbg` (managed backups with non-zero retention and/or the PITR add-on), then re-run
   §15.1, which closes B2′ in minutes.
4. **Independent verifier (CoStrict / OHD)** — independently verify the §16 evidence and the artifact /
   restore / DR-20 claim, and grant or refuse acceptance. This report asserts nothing on their behalf.

Until 2–3 are done, the correct statement about FINAL-02 is: **still open — one capability blocker
(B2′), and one technical blocker (B7) that is remediated and locally verified but not yet committed and
therefore not yet closed.** Item 1 is **now fully done** — B7 fix + suites + drill + the §16.10 B4/D-7
re-run (35/35, EXIT=0).

Also still true, and to be re-stated at handoff: **B7's §15.2.1 remedy lives only in the working tree.**
Until it is committed (item 2 / gate P2), any environment started from a built commit still contains the
connection-exhaustion defect — and per §15.2 the crash is *not* prevented by applying the two BACKUP
migrations alone.

---

## Appendix A — exact reproduction commands (read-only / local only)

```bash
W=/home/shomonrobie/ct_local_env/final02_rehearsal
R=/home/shomonrobie/ct_93d5cdd

# 0. bring up the coherent stack (gateway + backend :8090 + frontend :3000)
bash $W/start_local_all.sh

# 1. B3 — sanctioned harness browser sweep (10 personas, screenshots, findings)
/usr/bin/python3 $W/b3_browser.py                    # all personas
/usr/bin/python3 $W/b3_browser.py --role staff_admin # one persona

# 2. B3 — supplementary journeys / timing / D-7 UI  (D-7 self-restores)
/usr/bin/python3 -u $W/b3_journeys.py
/usr/bin/python3 -u $W/b3_textprobe.py
/usr/bin/python3 -u $W/b3_d7_ui.py

# 3. B4 / B5 / auth matrices (real password grants, no fakes)
cd $R && backend/.venv/bin/python $W/matrix_b5.py      # expect 29/29
cd $R && backend/.venv/bin/python $W/matrix_b4_d7.py   # expect 35/35
cd $R && backend/.venv/bin/python $W/login_probe.py    # expect 9/9

# 4. canonical FINAL-02 pytest set (matrix §4.1) — expect 314/0/0/0, EXIT=0
cd $R/backend && .venv/bin/python -m pytest -q -p no:cacheprovider \
  --junitxml=/tmp/canonical_junit.xml \
  tests/unit/api/test_f05_r1_org_scope_authorization.py \
  tests/unit/api/test_d7_org_lifecycle_decisions.py \
  tests/unit/api/test_d7_f1_f2_f3_enforcement.py \
  tests/unit/api/test_storage_management_step1.py \
  tests/unit/api/test_storage_management_step2.py \
  tests/unit/api/test_g1_g2_emissions_query_scope_and_staff_access.py \
  tests/unit/api/test_ct_final_02_email_provider.py

# 5. database integrity (read-only)
docker exec supabase_db_carbon_ledger psql -U postgres -d ct_final02_src -tAc \
  "select 'tables',count(*) from pg_tables where schemaname='public' \
   union all select 'rls',count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace \
     where n.nspname='public' and c.relkind='r' and c.relrowsecurity \
   union all select 'policies',count(*) from pg_policies where schemaname='public' \
   union all select 'factors',count(*) from public.emission_factors"

# 6. B2′ — ONLY ONCE THE MANAGEMENT CREDENTIAL EXISTS (do not run blind)
export SUPABASE_ACCESS_TOKEN='sbp_…'      # the credential the owner must supply
supabase projects list                     # confirm the org/project is visible
curl -s -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  https://api.supabase.com/v1/projects/pvwiojoyaqywtydzcpbg/database/backups | head

# 7. teardown (containers only; the database is never dropped)
bash $W/stop_local_all.sh
```

## Appendix B — evidence index (all outside the repository)

| Path | Contents |
| --- | --- |
| `final02_rehearsal/b3/results/b3_sweep_all_20261001T101139Z.json` | full sweep: 10 role results, 21 route visits, 352 raw findings, evidence index (559 KB) |
| `final02_rehearsal/b3/results/PREFIX_SMOKE_superseded_…json` | pre-fix smoke run (kept, explicitly labelled superseded — the CORS failures it recorded are the ones fixed in §1.2) |
| `final02_rehearsal/b3/evidence/screenshots/` (21) | per-role/route screenshots |
| `final02_rehearsal/b3/findings/{raw,normalized,deduplicated}/` | harness finding pipeline output |
| `final02_rehearsal/b3/journeys/b3_journeys_20261001T101918Z.json` | J1–J6 journeys, 26/30 checks, suspended-state observation |
| `final02_rehearsal/b3/textprobe/textprobe_20261001T102026Z.json` | anonymous redirect timings (2.6–3.3 s) + per-route rendered text/timings; screenshots |
| `final02_rehearsal/b3/d7ui/d7_ui_20261001T102539Z.json` | D-7 ACTIVE → SUSPENDED → REACTIVATED body text and the 403 "organization is suspended" console transcript; 3 screenshots |
| `final02_rehearsal/b3/diag/` | first browser-login diagnostics (CORS failure, then success) + screenshots |
| `final02_rehearsal/logs/` | sweep, journeys, textprobe, D-7 UI, `b5_20261001.log`, `b4_d7_20261001.log`, `login_probe_20261001.log`, `canonical_pytest_junit.log`, `start_local.log` |
| `final02_rehearsal/nginx.conf.orig-b3`, `auth.env.orig-b3` | the pristine originals of the two patched environment files (with sha256 in §12 context) |
| `final02_rehearsal/b3/OWNER-LOGIN.md` | owner-facing login card (identities, portals, expected landings) |







