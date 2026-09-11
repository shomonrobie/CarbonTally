# CarbonTally — QA Harness V1.2 Forensic Triage

- **Triage date:** 2026-08-31
- **Checkpoint (Git SHA):** `16391217103b98dcea520070c5a22c68f12fe607` (HEAD `main`)
- **QA evidence source:** `qa_harness/reports/latest/` (master/executive/findings/backlog) + findings store (`qa_harness/findings/raw|normalized|deduplicated/*.jsonl`) + archived run reports + `qa_harness/evidence/`
- **Method:** read-only forensic verification against current source, live runtime (frontend :3000, API :8050, Supabase Auth/REST :54425, Postgres 54426), and read-only database probes. No code, database, seed, or harness modifications. No commits.
- **Independent verification performed:**
  - Anonymous separation probed headless (fresh context) for `/home`, `/consultant`, `/ops`, `/messaging`, `/onboarding`.
  - Real-form login probed headless for `customer_owner`, `internal_operator`, `consultant`.
  - Post-login routing endpoints (`/api/organizations/members/user/{id}`, `/api/v3/ops/me`, `/api/v3/consultants/me`, `/api/v3/me/context`) exercised read-only.
  - Live backend FD state inspected (`/proc/<pid>/fd`, `/proc/<pid>/limits`).
  - Database read-only probes of `organization_members`, `staff_profiles`, `consultant_profiles`, `consultant_firm_members`, schema columns.
  - Backend/frontend source inspection for each claimed root cause.

---

## 1. Executive verdict

**The QA Harness V1.2 findings are real observations of the current runtime, but they do NOT represent 27 independent application defects.** Forensic verification shows the findings collapse into a small number of genuine root causes:

1. **P1 — Backend file-descriptor exhaustion (dominant).** `backend/auth.py:get_supabase_client()` creates a **new service-role Supabase client on every call** (no caching, no close). `get_current_user` — the auth dependency on nearly every `/api/v3` endpoint — calls it per request. Under sustained load the backend process exhausts its 1024-FD soft limit and every authenticated API call returns `500 "Failed to initialize Supabase client: [Errno 24] Too many open files"`. **Verified live: the running backend holds 1023/1024 FDs** and every routing endpoint returns 500. This single defect is the root cause of:
   - **QA-AUTH-001..010 (P1, all 10 personas "land on /onboarding")** — the frontend's `resolvePostLoginPath()` probes org → staff → consultant, **all 500**, so every persona falls through to the `/onboarding` fallback. The demo identities are correctly provisioned in the database (org memberships, staff profiles, consultant firm memberships all verified present), so on a healthy backend these personas land on the correct workspaces.
   - **The 500 console errors** contributing to QA-UI-001..013 (P3).

2. **P1 — Frontend error-swallowing routing fallback (secondary but genuine).** `resolvePostLoginPath()` (`frontend/src/v3/api.js`), the `OnboardingPage` guard (still carries the 12 s fallback timer), and `V3Layout` (hardcoded `navigate('/onboarding')`) treat **any** probe failure (500/403/network) as "brand-new customer". The documented `/api/v3/me/context` server-authoritative resolver and the error-throwing routing redesign described in prior implementation reports **do not exist anywhere in the current codebase** (backend and frontend confirmed absent). So even a transient backend hiccup misroutes existing users into "Set up your organisation".

3. **Harness issues (not application defects):**
   - **QA-SEC-001 (P1 "anonymous /home") is a first-load timing artifact.** Headless verification: with the sweep's exact sampling logic (URL read immediately after `networkidle`), `/home` samples as `/home` during ProtectedRoute's transient "Authenticating…" frame, then settles to `/login` ~2 s later. `/consultant`, `/ops`, `/messaging` (visited after the app is loaded) sample as `/login`. No customer data or app functionality is rendered anonymously. The application is correct; the harness check needs to wait for the route to settle.
   - **QA-API-001 / QA-WF-001 / QA-WF-002 (3 REAL API/workflow findings) are harness expectation errors (wrong endpoint bindings).** In each case the application's 403 is the *correct, ratified* boundary (D20 PE isolation; org-member-only generic reports with a dedicated consultant route; N1 PE messaging boundary). The harness workflows probed the wrong routes.
   - The `latest/` report header metadata (`Tests executed: 0`, empty SHA, `UNVERIFIED`, "not a fresh application run") is a **report-regeneration artifact** of `reclassify.py`, not proof that no run occurred — the stored findings carry the run timestamps (07:50–07:52Z) and the current SHA. This should be fixed so regenerated reports carry real run metadata.

4. **Secondary environment defect (P3):** the configured Supabase endpoint serves auth and REST but **Realtime returns 503** (`/realtime/v1/websocket`), so the Realtime-based notification/chat channels cannot connect and produce `ERR_SOCKET_NOT_CONNECTED` / `ERR_CONNECTION_RESET` console noise on every page.

5. **One documented product gap requires a PO decision:** PE-internal/operational messaging (entity-scoped conversations) is not implemented; `conversations` has no `entity_id` column and PE users are structurally denied on the org-scoped messaging surface. N1 requires "operational CarbonTally messaging" for PE, so the current 403 is correct *for the org-scoped surface* but the PE messaging capability itself is missing.

**Bottom line:** the Phase 2 "COMPLETE" verdict must be treated as historical implementation evidence, not as proof the product is defect-free. The most urgent issue is **not** any of the 24 reported findings individually — it is the backend resource leak that makes every verified finding observed under a partially-degraded runtime. Restart/recover the backend, fix the FD leak, and the QA-AUTH/QA-UI findings must be re-run.

---

## 2. P0/P1 security findings

### 2.1 P1 — QA-SEC-001 "Anonymous visitor reached protected route /home"

| Attribute | Value |
|---|---|
| Finding | QA-SEC-001 (P1, SEC, anonymous, `/home`) |
| Harness claim | Anonymous visitor reached `/home` (URL stayed `http://localhost:3000/home`); expected redirect to `/login` |
| **Forensic verdict** | **HARNESS TIMING ARTIFACT — NOT an application security defect. Downgrade; re-verify with a settle-aware check.** |
| Evidence | Headless fresh-context probe (sweep-equivalent timing): `/home` samples as `/home` at the networkidle instant, **settles to `/login`**; `/consultant`, `/ops`, `/messaging` sample and settle as `/login`. Second probe with +1.5 s settle shows all five protected routes redirect to `/login`. |
| Root cause | `ProtectedRoute` (`App.js`) renders a transient "Authenticating…" loading frame while `supabase.auth.getSession()` resolves. On the **first** navigation (bundle load + React mount + async session check + re-render) this window is long enough that the sweep's immediate URL read observes `/home`. Subsequent routes reuse the loaded app and settle faster. |
| Security impact | **None.** No authenticated functionality or customer data is rendered during the transient frame; the final settled state is the public `/login` page. `RoleRoute` is never reached anonymously (ProtectedRoute is the parent). |
| Recommendation | 1) Harness: `_anonymous_separation` should wait for the route to settle (e.g., poll URL until stable for 2 s, or assert no application-shell content) before classifying. 2) Optionally (P3): add a real route-transition assertion. 3) Re-run after harness fix. |

### 2.2 Security negatives that were re-confirmed correct (must NOT be changed)

The API/workflow probes re-confirmed that these boundaries hold (each is the *expected* 403):

- PE staff cannot access customer organisations (`ensure_processing_org_access` / `ensure_org_access` — D20).
- PE staff cannot list/message customer-org conversations (N1; `_authorize_org_actor`).
- Consultant cannot call the generic org-member-only reports surface (`require_org_member` + `ensure_org_access`) — a dedicated consultant-scoped route exists.

No unexpected ALLOW was found in the triaged findings.


---

## 3. P1 functional findings

### 3.1 P1 — Backend FD leak (`auth.py get_supabase_client` no-cache) — NEW confirmed root cause

- **Evidence:** `backend/auth.py:92-108` creates `create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)` on every call; `get_current_user` (auth.py:149) and the org-role fallback (auth.py:487) call it per request; no `close()` anywhere. Live: backend PID has **1023/1024** open FDs; every authenticated endpoint returns `500 … [Errno 24] Too many open files`. `database.py:get_supabase_client()` (cached) is a different function and is not the problem; `auth.py`'s is.
- **Impact:** under sustained use (a real customer session, the QA sweep, or automated workflows) the entire API degrades to 500s → every screen loses data, routing falls back to `/onboarding`, console floods with 500s. This is the primary cause of the QA-AUTH and QA-UI clusters.
- **Suggested fix (implementation only, not done here):** cache the client (module-level singleton with lifecycle), or reuse `database.get_supabase_client()`; add graceful close; raise the process soft FD limit as a stopgap; add a regression test that performs N authenticated requests and asserts FD count / healthy responses.
- **Severity:** P1.

### 3.2 P1 — QA-AUTH-001..010 (all personas land on `/onboarding`)

| Finding | Role | Expected | Actual (observed) | Classification |
|---|---|---|---|---|
| QA-AUTH-001 | customer_owner | `/home` | `/onboarding` | REAL (symptom) — backend 500s → probe fallback |
| QA-AUTH-002 | customer_viewer | `/home` | `/onboarding` | REAL (symptom) — same root cause |
| QA-AUTH-003 | consultant | `/consultant` | `/onboarding` | REAL (symptom) — same root cause |
| QA-AUTH-004 | pe_manager | `/ops` | `/onboarding` | REAL (symptom) — same root cause |
| QA-AUTH-005 | pe_staff | `/ops` | `/onboarding` | REAL (symptom) — same root cause |
| QA-AUTH-006 | internal_operator | `/ops` | `/onboarding` | REAL (symptom) — same root cause |
| QA-AUTH-007 | internal_reviewer | `/ops` | `/onboarding` | REAL (symptom) — same root cause |
| QA-AUTH-008 | internal_qc | `/ops` | `/onboarding` | REAL (symptom) — same root cause |
| QA-AUTH-009 | staff_admin | `/ops` | `/onboarding` | REAL (symptom) — same root cause |
| QA-AUTH-010 | system_admin | `/ops` | `/onboarding` | REAL (symptom) — same root cause |

**Verification:**
- DB read-only: `owner.demo0001` and `viewer.demo0001` have active `organization_members` rows; `operator.demo`, `pe-manager-1.demo`, `staff-admin.demo` have active `staff_profiles` (PE users with `entity_id`); `consultant.demo0001` has `consultant_profiles` + `consultant_firm_members`. **The data is correct** — these are not "brand-new customers".
- Real-form login probe (current degraded runtime): all three tested personas land on `/onboarding`, rendering "Set up your organisation", because `resolvePostLoginPath()`'s probes all 500.
- With a healthy backend the first probe returned `org_members: 200 primary_organization=True` for customer_owner → `/home` would be chosen.

**Conclusion:** the observed landing is real, but it is **one** defect cluster (backend leak + error-swallowing fallback), **not ten independent routing bugs**. Fixing only the frontend (fail-closed routing) is still required; fixing only the backend leak would likely make these findings disappear on re-run. **Do not treat these as ten separate routing regressions.**

### 3.3 P1/P2 — Frontend routing fallback routes real users to onboarding on ANY probe failure

- `frontend/src/v3/api.js` `resolvePostLoginPath()` — swallows all errors; falls through to `/onboarding`.
- `frontend/src/OnboardingPage.jsx` — guard probes same endpoints, has a **12 s fallback timer** (line ~79) that forces the onboarding UI even if resolution is slow; docs claimed this timer was removed.
- `frontend/src/v3/components/V3Layout.jsx` — hardcoded `navigate('/onboarding')` when `!org && !staff && !consultant`.
- The documented `/api/v3/me/context` server-authoritative resolver is **absent** from current backend and frontend (confirmed by source search and live 404).
- **Impact:** any backend 500/network blip (or real degradation) during login misroutes existing users into org-onboarding — a severe, confusing UX and a workflow interruption, plus a wrong "existing data" adoption path. Functional P1, security-neutral.


---

## 4. P2 findings

| # | Finding | Evidence / root cause | Classification |
|---|---|---|---|
| 1 | PE operational/entity-scoped messaging not implemented | `conversations` has no `entity_id` column (DB verified); `v3_messaging.py` authorizes only org members / active-grant consultants / internal support-admin; PE users denied on every org-scoped messaging route. Prior audits record "PE-internal messaging needs an entity-scoped conversation model … **BLOCKED_BY_PO_DECISION**". | PRODUCT GAP / PO DECISION |
| 2 | Consultant cannot reach the generic `/api/v3/reports` surface for an active client | `require_org_member` + `ensure_org_access` deny consultants. **However** the consultant has a dedicated authorized route `GET /api/v3/consultants/clients/{client_id}/reports` (`v3_consultants.py:998`), and the consultant UI calls the dedicated route. So this is a design asymmetry, not a functional break for the consultant UI. | EXPECTED BEHAVIOR (app) / HARNESS EXPECTATION ERROR (probe) |
| 3 | Realtime websocket unavailable on the configured Supabase endpoint (`/realtime/v1/websocket` → 503) | Verified live. Causes `ERR_SOCKET_NOT_CONNECTED`/`ERR_CONNECTION_RESET` console noise and no realtime delivery on every page. Local-stack config issue; production equivalent must be validated. | ENVIRONMENT DEFECT (P3 at runtime, but blocks realtime messaging → note) |

---

## 5. P3 UX findings (QA-UI-001..013 — console errors)

All 13 findings share **two** root causes; none is an independent frontend logic defect.

| Finding | Route | Persona | Reported | Root-cause group |
|---|---|---|---|---|
| QA-UI-001 | `/home` | customer_owner | 22 err (500) | A (backend FD leak) |
| QA-UI-002 | `/emissions` | customer_owner | 21 err (ERR_SOCKET_NOT_CONNECTED) | A + B (realtime 503) |
| QA-UI-003 | `/documents` | customer_owner | 22 err (500) | A |
| QA-UI-004 | `/processing` | customer_owner | 21 err (500) | A |
| QA-UI-005 | `/review` | customer_owner | 22 err (500) | A |
| QA-UI-006 | `/messaging` | customer_owner | 22 err (500) | A (+ B) |
| QA-UI-007 | `/issues` | customer_owner | 21 err (500) | A |
| QA-UI-008 | `/notifications` | customer_owner | 18 err (500) | A (+ B) |
| QA-UI-009 | `/reports` | customer_owner | 22 err (ERR_CONNECTION_RESET) | A (accept/reset under FD pressure) |
| QA-UI-010 | `/billing` | customer_owner | 22 err (500) | A |
| QA-UI-011 | `/organization` | customer_owner | 21 err (500) | A |
| QA-UI-012 | `/consultant` | consultant | 22 err (ERR_SOCKET_NOT_CONNECTED) | A + B |
| QA-UI-013 | `/ops` | pe_manager | 21 err (ERR_SOCKET_NOT_CONNECTED) | A + B |

**Classification:** REAL as observed (console is genuinely noisy), but **one** P1 defect (backend leak) plus **one** P3 environment defect (Realtime 503) explain the group. Recommend fixing the backend leak + realtime config, then re-running; do not spend effort on per-page console cleanup until the shared causes are resolved. Quiet role probes already exist (CL-49); expected 403 probes are not the source here (500s dominate).

---

## 6. PO decisions required

| # | Decision | Context | Recommended direction |
|---|---|---|---|
| PO-1 | **PE-internal / operational messaging scope** | N1 states PE = "operational CarbonTally messaging"; no entity-scoped conversation model exists (no `entity_id` on `conversations`; PE denied on all org-scoped messaging). The 403 is correct; the missing surface is the gap. | Decide the PE messaging surface (entity-scoped support conversations vs. mediated-issue-only). Requires a small schema addition + server-side participant model. |
| PO-2 | **(Confirm) Existing users must never be routed to onboarding on probe failure** | Prior D35 remediation documented intent: failures must not become "new customer". Current code regressed to error-swallowing. | Confirm the fail-closed behavior (controlled error/retry instead of `/onboarding`) as the ratified behavior; treat as an implementation defect. |
| PO-3 | **(Confirm) Generic `/api/v3/reports` stays org-member-only; consultants use the dedicated route** | Verified intended design; consultant UI already uses the dedicated route. | Keep as-is; no change required. Informational only. |


---

## 7. Harness / inconclusive findings

| Item | Verdict | Detail |
|---|---|---|
| QA-SEC-001 | **HARNESS ISSUE (false positive)** | First-load URL-sampling race in `_anonymous_separation` (see §2.1). Application correct. Re-verify with settle-aware check. |
| QA-API-001 (pe_manager `GET /api/v3/processing/status?organization_id={org_a}` → 403, expected 200) | **HARNESS EXPECTATION ERROR** | `{org_a}` bound to a customer org; PE is correctly denied (D20). PE entity-scoped status lives under `/api/v3/ops/entities/{entity_id}/…`. Re-bind the smoke probe to the entity surface (or assert the 403 as the boundary). |
| QA-WF-001 (consultant `reporting` step → 403 on `/api/v3/reports?organization_id={client_org}`) | **HARNESS EXPECTATION ERROR** | Consultant reporting must use `GET /api/v3/consultants/clients/{client_id}/reports`. Application correct. |
| QA-WF-002 (pe_staff `allowed_messaging` step → 403 on `/api/v3/messaging/conversations?organization_id={msg_org}`) | **HARNESS EXPECTATION ERROR** | N1 requires PE to be denied on org-scoped conversations (403 verified correct). The workflow's "allowed_messaging" step has no implemented route yet → surfaces the PO-1 gap. Re-bind or mark SKIPPED until PO-1 lands. |
| `latest/` report header (`Tests executed: 0`, empty SHA, `UNVERIFIED`, "regenerated … not a fresh application run") | **HARNESS REPORTING QUIRK** | `reclassify.py:_regenerate_reports` writes a static `ReportBundle` with no run stats. The underlying findings DO carry the 07:50–07:52Z run timestamps and the current SHA. Regenerated reports should preserve the originating run's git SHA / test counts. |
| 06:26 API-run findings (QA-API-002..008 etc., 422s) | **SUPERSEDED** | The 07:26 run corrected the deny-gate probes (valid bodies) and produced the 3 REAL findings triaged above. The 422s were inconclusive body-validation-before-authz artifacts. |
| Database-collector note (from calibration report §6: pending migrations, missing indexes, missing `organization_members` unique constraint, `beta_users` RLS 0 policies, schema gaps) | **RE-VERIFY (DB evidence, not in the verdict-counted 24)** | Reported in the calibration session as candidates; not re-verified in this triage. These are separate DB-quality items to track, not part of the 24 browser findings. |

---

## 8. Root-cause grouping

| Group | Root cause | Findings |
|---|---|---|
| **A** | `backend/auth.py:get_supabase_client()` per-request client creation → FD exhaustion → all authenticated API calls 500 | QA-AUTH-001..010, QA-UI-001..011 (500s), QA-UI-012/013 (partially), QA-UI-009 (resets) |
| **B** | Supabase Realtime 503 on configured endpoint | QA-UI-002, QA-UI-012, QA-UI-013 (ERR_SOCKET_NOT_CONNECTED) + contributes to others |
| **C** | Frontend error-swallowing routing fallback (probe-chain + 12 s timer + V3Layout hardcoded onboarding; `/api/v3/me/context` absent) | Mechanism behind QA-AUTH-001..010; a genuine independent defect |
| **D** | Harness anonymous-check first-load timing race | QA-SEC-001 |
| **E** | Harness workflow/smoke endpoint bindings wrong for PE and consultant | QA-API-001, QA-WF-001, QA-WF-002 |
| **F** | Product gap: no entity-scoped PE messaging model | Underlying QA-WF-002; PO-1 |

---

## 9. Recommended implementation order

1. **Fix Group A (P1, highest priority):** cache the Supabase client in `auth.py` (reuse `database.get_supabase_client()` or a singleton), add lifecycle close, restart the backend, verify FD count stabilizes and all authenticated endpoints return 200. Add a regression test (N authenticated requests → FD count/health stable).
2. **Fix Group C (P1):** make post-login routing fail closed — implement the server-authoritative `/api/v3/me/context` (documented, absent), or at minimum make `resolvePostLoginPath()`/`OnboardingPage`/`V3Layout` never fall through to onboarding on failure; remove the 12 s fallback timer; add a controlled error/retry state.
3. **Fix Group B (P3):** configure/start Supabase Realtime on the port the frontend expects (local stack); verify `/realtime/v1/websocket` handshake; add a production Realtime readiness check.
4. **Harness fixes (P3):** settle-aware anonymous check; correct the PE/consultant probe bindings (E); preserve run metadata in regenerated reports.
5. **PO-1:** decide PE operational messaging; implement entity-scoped conversations if approved.
6. **Product-surface follow-ups (P3):** see §12.


---

## 10. Regression-test requirements

After fixes, the following must be re-run and pass deterministically:

- **Routing:** real-form login for all 10 personas lands on the documented landing (`/home`, `/consultant`, `/ops`) **while the backend is under load and while individual probes fail** (fail-closed test).
- **Anonymous separation:** fresh-context visit to `/home`, `/consultant`, `/ops`, `/messaging` settles on `/login` (settle-aware assertion).
- **Backend FD/health:** N authenticated requests (e.g., 500) → no 500s, FD count stable, all responses 200.
- **Security negatives (must remain DENY):** PE → customer org `processing/status`, PE → customer-org conversations, PE → customer document/signed-url, consultant → unrelated org reports, customer → `/ops/me`. Add both ALLOW and DENY cases per role.
- **Consultant reporting:** `GET /api/v3/consultants/clients/{client_id}/reports` → 200 for an active-grant consultant; generic `/api/v3/reports?organization_id={client_org}` → 403 (intended).
- **Realtime:** authorized conversation delivery works once Realtime is reachable; PE remains denied.
- **Onboarding:** a genuinely new authenticated user (no org/staff/consultant) still reaches `/onboarding` (D35 preserved).
- **DB-quality items** (from calibration §6): pending migrations applied; missing expected indexes added; `organization_members` unique constraint; `beta_users` RLS — verify before any product claim.

---

## 11. Findings that must NOT be changed

- **PE customer-org and messaging denials (D20/N1):** do NOT weaken to make QA-API-001 / QA-WF-002 pass. The 403s are the ratified boundary.
- **Anonymous redirect to `/login`** on all protected routes — correct; do not "fix" by making `/home` public.
- **Consultant reports boundary:** keep the generic `/api/v3/reports` org-member-only; consultants use the dedicated route.
- **RLS:** unchanged in this triage; no RLS change is implied by any finding.
- **Investor demo data / seed:** verified correct for the identities involved; do not re-seed to "fix" the routing findings.
- **QA Harness read-only guarantees:** keep the harness read-only; the fixes are harness *timing/binding* corrections, not a mode change.

---

## 12. Product-surface completeness gaps (source-based, not all producing deterministic failures)

| Surface | Observation | Classification |
|---|---|---|
| Customer Documents page | No pagination / search / sort controls in `DocumentsPage.jsx` (204 lines); demo orgs can hold many documents. | P3 candidate — bounded at demo scale; revisit with DataTable contract when document counts grow. |
| Customer Processing page | Only minimal `limit` reference; no paging UI. | P3 — queue can grow; reuse the ops DataTable pattern. |
| Customer Review / Messaging / Issues / Billing | No pagination; mostly bounded lists; empty states present. | Acceptable at current scale; do NOT force DataTable controls (per table standard). |
| Consultant page | 1025-line monolith; client list bounded (5–30/firm); no pagination. | P3 — acceptable; consider splitting components. |
| Ops queues / entities / emissions | Server-side pagination + sort + counts implemented (Phase 2 DataTable rollout). | OK. |
| Search result navigation | Completion matrix L3 records "result navigation ❌" (search results do not deep-link to the routed workspace). | P3 documented gap. |
| Master data (facilities/assets/vehicles/suppliers) CRUD | Completion matrix J1–J5 mostly 🟡 (live-verify outstanding). | P3 follow-up. |
| Historical `OpsMessagingTab` `orgs.map is not a function` | **FIXED in current code** (CL-63 — uses `getOpsOrganizations`; verified in source). | Resolved — do not re-report. |
| Historical `customer-review` 500 (ambiguous `id`) | **FIXED in current code** (`manual_extraction.list_customer_review` fully column-qualified). | Resolved — do not re-report. |
| `[object Object]` rendering / dead buttons | No evidence in current V3 sources. | Not present. |
| Loading/empty/error states | `LoadingState`/`EmptyState`/`Alert` components in use across pages. | OK (spot-checked). |


---

## 13. Relationship to the previous Phase 2 completion report

- `CARBONTALLY_V3_PHASE_2_COMPLETION_REPORT.md` / `CARBONTALLY_V3_PHASE2_COMPLETION_MATRIX.md` (baseline `58285e6`, closed out at `1639121710`) are **historical implementation evidence** — they document what was implemented and verified at that checkpoint. They are **not** proof that the product is currently defect-free, and nothing in this triage contradicts the specific fixed items they record (e.g., DataTable rollout, PE workspace, consultant model, customer-review qualification).
- The Phase 2 matrix itself already carried honest 🟡 items (J1–J5 master-data live-verify, L3 search navigation, E8 consultant report generation) — consistent with this triage's completeness findings.
- **New information this triage adds:** (1) the backend FD leak that degrades the whole runtime under load — not covered by Phase 2 acceptance evidence; (2) the routing-fallback regression (error-swallowing path present despite documented remediation); (3) harness-level artifacts in the V1.2 findings that change how the findings should be read (QA-SEC-001, QA-API-001, QA-WF-001, QA-WF-002); (4) Realtime unavailability on the local stack.
- The QA Harness's own verdict discipline is correct: `UNVERIFIED` and "REAL"/"RE-VERIFY" are separate from "ACCEPTED". The harness has not issued an acceptance verdict, and neither does this triage.

---

## Final tallies

- **Total findings triaged:** 27 (24 deduplicated browser findings + 3 REAL API/workflow findings)
- **Total confirmed genuine application defects:** **3**
  1. P1 backend FD leak (`auth.py` per-request Supabase client) — root cause of QA-AUTH-001..010 + the 500 half of QA-UI-001..013
  2. P1 frontend error-swallowing routing fallback to `/onboarding` (incl. 12 s onboarding timer; `/api/v3/me/context` absent)
  3. P3 Realtime unavailable on the configured endpoint (environment defect; realtime console noise + no realtime delivery)
- **Total product-surface gaps (P3, separate):** 4 (documents pagination/search; processing paging; search-result navigation; master-data live-verify)
- **Total PO decisions required:** **1 core** (PE operational messaging — PO-1), plus 2 confirmations (PO-2 routing behavior, PO-3 reports boundary; both have documented precedent and are recommended as "confirm, then implement").
- **Total re-verification items:** **4**
  1. All QA-AUTH-001..010 + QA-UI-001..013 after the backend FD leak is fixed and the backend is restarted (expected to clear)
  2. QA-SEC-001 with a settle-aware anonymous check (expected to clear)
  3. QA-API-001 / QA-WF-001 / QA-WF-002 with corrected harness bindings (expected to pass with 403s asserted as boundaries)
  4. DB-quality candidates from the calibration report (pending migrations, indexes, `organization_members` unique, `beta_users` RLS)
- **Total expected behavior (must NOT be changed):** 4 boundary groups (PE org/messaging 403s; anonymous redirect; consultant reports boundary; onboarding for genuinely new users)
- **Total harness issues:** **5** (anonymous timing race; 3 probe-binding mis-specifications; report-metadata regeneration quirk)
- **Historical misleading findings preserved as RE-VERIFY:** per the calibration report; the current 24 are the re-run REAL set (timestamps 07:50–07:52Z at the current SHA).

## Recommended next implementation phase

**Phase "Runtime Stability & Routing" (immediate):** fix the backend FD leak → restart/verify backend health → implement fail-closed post-login routing (`/api/v3/me/context` or equivalent; remove the onboarding fallback-on-error) → restore Realtime on the local stack → re-run the QA Harness deterministic sweep → confirm QA-AUTH/QA-UI clusters clear and QA-SEC-001 is gone. Then (Phase 2) resolve PO-1 (PE messaging) and apply the harness binding/timing fixes so the next run's evidence is unambiguous.

---

*This document is a forensic triage only. No application, database, seed, or harness code was modified. No commits were made. The runtime observations (backend FD state, live 500s, realtime 503, DB rows) were captured read-only on 2026-08-31.*

