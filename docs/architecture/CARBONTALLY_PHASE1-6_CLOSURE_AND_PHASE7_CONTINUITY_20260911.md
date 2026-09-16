# CarbonTally — Phases 1–6 Closure & Phase 7 Continuity Record

**Date:** 2026-09-11
**Status:** `PHASES 1–6 CLOSED — PHASE 7 HANDOFF READY` (Phase 7 implementation **NOT** authorised by this record)
**Prompt Ref:** `CT-PHASE1-6-FINAL-CLOSURE-HANDOFF-20260911-001`
**Repository:** `/home/shomonrobie/carbon_tally` · **Branch:** `main` · **HEAD = `origin/main` =** `9e13236149b8132d737258abc0aa7d69a974a85b`
**Nature of this document:** a **historical closure and continuity handoff record**. It is **not** a Project
Control Center, **not** a replacement for the Blueprint or the Master Roadmap, and it creates no new authority.

**Authority statement.** This record does **not** outrank the Blueprint or the Master Roadmap, and it cannot
change any ratified decision. It summarises, points to, and preserves them. Where this record and an
authoritative source disagree, the authoritative source wins and the disagreement must be reported, not
silently reconciled. Nothing in this record authorises Phase 7 or Phase 8 implementation.

---

## A. Document identity

| Field | Value |
|---|---|
| Title | CarbonTally — Phases 1–6 Closure & Phase 7 Continuity Record |
| Date | 2026-09-11 |
| Status | Phases 1–6 closed; Phase 7 handoff ready; **no Phase 7/8 implementation authorised** |
| Purpose | Let the Product Owner, ChatGPT, Cline and any future agent resume CarbonTally development without losing the authoritative architecture, roadmap, decisions, implementation history, verification status, production state, known residuals, or Phase 7 starting conditions |
| Scope | Documentation, verification, closure, continuity — **no code, schema, migration, RLS, API, billing, configuration, or deployment change** |
| Authority | Subordinate to the Blueprint V1.3 and Master Roadmap V1.0 (see §C) |

## B. CarbonTally identity

**Product purpose.** CarbonTally is a commercial, multi-tenant emissions-data processing platform. It
transforms messy organisational activity data into structured, validated, calculated, traceable emissions
data and reporting outputs. The core value chain is:

```text
SOURCE DATA → EXTRACTION → MAPPING → VALIDATION → CALCULATION → EVIDENCE
            → REVIEW → CUSTOMER APPROVAL → REPORTING
```

**Actors.** Four processing actors are first-class: **Organisation** (customer), **Consultant** (acting for an
engaged client organisation), **CarbonTally internal staff**, and **Processing Entity**. Automatic processing
additionally executes through the platform's system/automatic worker. Actor identity, processing **mode**
(automatic vs manual), **processing origin** (internal vs PE — the manual-capacity/control path),
**provenance**, **entitlement**, **capability**, **authorization** and **workspace** are distinct dimensions
that must never be collapsed (Blueprint §9 dimensional amendment, 10 Sept 2026).

**Current architecture.** React application (CRA) + Vite-era public surface in one router; FastAPI
business/domain API; Supabase PostgreSQL with RLS; Supabase Auth; Supabase Storage; Supabase Realtime; Resend
for email. Frontend handles auth/session/simple RLS-protected reads/presentation; FastAPI handles
factor matching, calculation, validation, extraction/OCR, workflow transitions, reports, orchestration and
durable jobs. The frontend is **never** the security boundary.

**Production deployment topology.** Vercel (public website + authenticated application, single Vercel project
linked at the repository root) · Render (FastAPI backend) · Supabase (database, auth, storage, realtime) ·
Resend (email). The public website (`https://carbontally.co.uk`) and the authenticated application are
related but distinct product surfaces.

## C. Authority hierarchy

Use this order when sources disagree. **Current runtime truth** (1) actual running behaviour, (2) actual
database state, (3) actual API/OpenAPI contract, (4) current Git source, (5) current migrations, (6) current
automated tests. **Product/design truth** (7) ratified Product Owner decisions, (8) frozen UX/design
architecture, (9) current implementation backlog, (10) historical audit reports. **Historical context**
(11) Hindsight memories, (12) older conversations, (13) older implementation claims.

Within documentation specifically:

1. `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`
2. `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`
3. Phase-specific architecture / gate documents (e.g. `CARBONTALLY_PHASE6_*`, `CARBONTALLY_P6_*`)
4. Implementation reports
5. Verification reports
6. Ratified PO decisions recorded in durable history

**Neither master document is replaced, renamed, reorganised or consolidated by this record.**

---

## D. Phase 1–6 status (phase-by-phase closure table)

Statuses below are taken from the authoritative records; none is upgraded here.

| Phase | Name | Status (as recorded) | Major outcomes | Verification position | Residual / PO-owned item |
|---|---|---|---|---|---|
| **1** | *(unresolved)* | **UNRESOLVED — NO AUTHORITATIVE PRODUCT PHASE-1 ARTIFACT LOCATED** (PO-ratified) | None claimable — no Phase-1 name or scope was ever invented (`CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` §4) | PO-ratified as an accepted documentation gap | **Does NOT block Phase 7** — no action required; recorded, not repaired |
| **2** | Product Requirement Completion (D–M) | **COMPLETE** (as documented) | D–M requirement domains completed; completion matrix is the authority | `CARBONTALLY_V3_PHASE2_COMPLETION_MATRIX.md` (+ Phase 2 completion/implementation reports) | Residual rows recorded inside the matrix |
| **3** | Runtime Stability & Fail-Closed Routing | **COMPLETE** | Removed the frontend probe-chain; introduced the **server-authoritative** `GET /api/v3/me/context` workspace resolver; **fail-closed** routing (an error can never be read as "new customer"); explicit auth error classification distinguishing outage from credential/authorization failure | Phase 3 runtime-stability report + unit/browser regression suites; behaviour re-confirmed in this closure | None blocking |
| **4** | Individual User Architecture | **DESIGN COMPLETE — AWAITING PO APPROVAL** | Design artifacts produced (`CARBONTALLY_PHASE4_INDIVIDUAL_USER_ARCHITECTURE_DESIGN.md`; Blueprint §33.1) | Design review only — no implementation verification (none authorised) | **PO decision on the §21 design options** remains open |
| **5** | D38 / D39 / D40 (Work management, conversations, notifications) | **IN PROGRESS / ACCEPTANCE PARTIAL** | WS0–WS4 workstreams delivered; WS4 Gate 1 + Gate 2 PASS; D38 assignment, D39 conversations and D40 notification surfaces implemented and later carried forward into Phase 6 | `CARBONTALLY_PHASE5_*` plan + WS4 Gate reports; **documented execution gaps** recorded | **PO decision on the WS4 closure run** remains open |
| **6** | Consultant Workflow | **CLOSED** | Consultant becomes a first-class operating actor: identity/membership/engagement, scoped client-organisation access, consultant processing on the shared engines (automatic **and** manual), consultant review, submission to CarbonTally QC, and the correct boundaries (never CarbonTally QC, never Customer Approval) | `CARBONTALLY_PHASE6_CLOSURE_AND_RELEASE_BOUNDARY_20260911.md` — every gate `P6-0 → P6-1B → P6-1C → P6-2A(+R1) → P6-2B-1…4 → P6-2C → P6-2D → P6-2E → P6-2F` implemented, **independently verified** and closed | Non-blocking P3 findings only (§H) |

**Phase 6 gate ledger (exact, as closed):**

| Gate | Subject | Verification evidence | Status |
|---|---|---|---|
| P6-0 | PO policy ratification (D-1…D-7) | `CARBONTALLY_PHASE6_P0_PO_RATIFICATION_REPORT.md` — `PHASE 6 POLICY RATIFIED` | COMPLETE |
| P6-1B | Consultant membership / team / workspace authorization | implementation + suite | IMPLEMENTED |
| P6-1C | Consultant engagement confirmation (customer-only `pending → active`) | re-verified end-to-end in P6-2F | COMPLETE |
| P6-2A (+R1) | Consultant processing authorization contract | `CT-P6-2A` re-verification PASSED | COMPLETE — VERIFIED |
| P6-2B-1…-4 | Consultant review, submission, CT-QC decision, mandatory CT-QC prerequisite | `CT-P6-2B-*` records | COMPLETE — VERIFIED |
| **P6-2C** | Approval-boundary hardening (`calculated → approved` automatic-only); consultant review claiming requires the capability; D3 billing deferred | `CT-P6-2C-IV-20260910-001.md` — **"PASS with three genuinely non-blocking findings"** | **CLOSED** |
| **P6-2D** | Durable server-derived provenance (consultant firm, actor-agnostic processing mode, seven consultant action boundaries) | `CT-P6-2D-IV-20260910-001.md` — **"PASS WITH NON-BLOCKING FINDINGS"** | **CLOSED** |
| **P6-2E** | Durable D11 notification lifecycle with firm-centric recipients | `CT-P6-2E-IV-20260910-001.md` — **"PASS WITH NON-BLOCKING FINDINGS"** | **CLOSED** |
| **P6-2F** | `/consultant` processing UI (D19/D21) + E2E security acceptance | `CARBONTALLY_P6_2F_INDEPENDENT_VERIFICATION_20260911.md` — **"P6-2F VERIFIED — PASS WITH NON-BLOCKING FINDINGS"** | **CLOSED** |

**P6-2F residual evidence limitations (preserved verbatim in substance, not upgraded):** the acceptance
evidence rests on the **isolated verification environment** whose schema is current (the reset re-applies all
53 migrations). The dedicated integration database `carbontally_test` has a **stale schema** (`can_extract`,
`can_submit` absent), so `tests/integration/test_consultants.py` fails inside `create_profile` before reaching
any statement — the **LT-2 (P3) evidence/coverage gap**, owned by test infrastructure. The browser suite
passed **16/16/0** on the documented pristine fixture state; one spec is fixture-order sensitive (**V1**, P3);
`seed_e2e.py` mis-reports on re-run without reset (**V2**, P3); and ALLOW specs guard with `test.skip(!visible)`
(**V3**, P3, pre-existing, mitigated by a 0-skip acceptance expectation plus API-layer assertions). The LT-1
real-SQL defect **was verified fixed** by executing the shipped SQL against real PostgreSQL with a
cast-removed comparison, not by a fake-repository test.

> **Strategic decision preserved:** these P6-2F evidence residuals are **not** to become an endless reopening
> loop. They are accepted, recorded, owned, and are to be revisited **only** if a material production conflict
> is discovered. No P0/P1 finding remains, and no finding was silently downgraded to reach closure.

---

## E. Major ratified decisions (durable, through Phase 6)

**Processing model (Blueprint §9 dimensional amendment, 10 Sept 2026 — documentation clarification only).**
Seven concepts are distinct and must never be conflated: **actor**, **processing mode**, **input type**,
**workflow state**, **processing origin**, **provenance**, **entitlement**. Four processing actors exist
(Organisation, Consultant, CarbonTally internal, Processing Entity). Automatic/manual **mode is independent of
actor identity** — an actor's identity never determines the mode. **`processing_origin` is not actor identity
and is not processing mode**: it identifies the manual-processing capacity/control path (internal vs PE),
is stored once and immutably on the item, and benefits from no consultant value
(`PO-P6-2D-D7b-R-20260910`). PEs are *additional controlled manual capacity*, not the exclusive source of
manual processing.

**Consultant operating model (Phase 6).** The Consultant is a **first-class operating actor**, not a
read-only adviser: firm membership/team, engagement relationships, scoped client-organisation access,
processing on the shared engines (automatic and manual), review, and submission to CarbonTally QC — but
**never** CarbonTally QC itself and **never** Customer Approval (`PO-P6-2C-D1-20260910`: `calculated →
approved` is automatic-processing-only). Consultant processing is gated by **additive `can_*` capability
flags** (`can_extract`, `can_submit`, … — `P6-2-D1`) with per-request re-checked engagement scope
(`P6-2-D2`); review-stage claiming requires the capability (`PO-P6-2C-D2-20260910`). A consultant firm is a
grouping expressed through its members' provenance, not a separate login identity.

**Provenance.** Provenance is **durable and server-derived**, never client-asserted: the actor who performed
a stage, the consultant **firm** at action time (`P6-2-D7` / `PO-PHASE6-D7-R-20260910`), the
processing **mode** where relevant, processing origin, and the calculation chain
(document/source → extraction item → mapped factor → validation → calculation snapshot → emissions →
evidence → approval/report). Historical backfill is handled as ratified (`PO-PHASE6-D7c-R-20260910`).

**Lifecycle notifications (D11 / D40).** A durable five-event lifecycle with deterministic keys and
firm-centric recipients: **request accepted · submitted to CT-QC · QC outcome · customer decision · rework**
(`PO-PHASE6-D11-20260910`, verified 52/52 in P6-2E and re-verified in P6-2F).

**Billing boundaries.** Entitlement is owned by the **client organisation** and checked at **approval time**
as the canonical gate (`PO-PHASE6-D6-R-20260910`); a non-charging availability check may exist at submission.
Automatic **job-review billing is unchanged and deferred** (`PO-PHASE6-BILL-DEFER-20260910`,
`PO-P6-2C-D3-20260910`). Billing configuration is administrative (`can_manage_billing`), not hard-coded in
the frontend.

**Boundaries deliberately NOT opened.** PE ↔ Consultant handoff remains **outside Phase 6** and out of scope
(`PO-PHASE6-D4-20260910` — no new state transitions, assignment semantics or authorisation flows).
D38 interaction/assignment conflict denies on any open D38 assignment (`P6-2-D3`). Organisation-member manual
processing scope preserves existing behaviour (`P6-2-D10`).

**Acceptance discipline.** P6-2F was ratified as the final Phase-6 UI/UX and E2E security acceptance gate with
**full acceptance required**, and **cannot self-certify** — mandatory independent verification was required
(`PO-PHASE6-F-ACC-20260910`).

**Access-control decisions carried forward.** Frontend route guards are **UX only** (D25); post-login
landing is **server-authoritative** (D29/F5 via `/api/v3/me/context`); a brand-new authenticated user goes to
`/onboarding` (D35); **`entity_staff` never passes role-name authorization guards** (D20) and cannot hold
internal admin authority; **`system_admin` is a superset** of legacy `admin` gates (PO Decision 2);
a Customer **Owner may self-approve a custom factor** (ratified; the blanket "no self-approval" rule must not
be reintroduced).

**Production-readiness pivot.** The independent production-readiness audit
(`CARBONTALLY_PRODUCTION_READINESS_AUDIT_20260911.md`, `CT-PROD-READINESS-AUDIT-20260911-001`) concluded
`YES, AFTER P0 FIXES`, explicitly **not** an architectural problem. The pivot it drove — commit and publish
the intended change set (P0-1), fix and commit the approval/billing crash (P0-2), evidence the
calculation pipeline end-to-end on customer-shaped data (P0-3), and prove subscription/allowance operability
(P0-4) — is now partially executed: **P0-1 and P0-2 are addressed**, P0-3 and P0-4 remain open (§F).

---

## F. Current production state

Recorded as at **2026-09-11**, `HEAD = origin/main = 9e13236149b8132d737258abc0aa7d69a974a85b`. This is a
position statement, **not** a new production-readiness master document — the authority remains
`CARBONTALLY_PRODUCTION_READINESS_AUDIT_20260911.md` and the release records.

### F.1 Implemented and published

| Item | State |
|---|---|
| Phase 1–6 workstreams (as recorded in §D) | Implemented; published |
| Published commits | `daad396` (release 1) → `c864d72` (Phase 6 consultant workflow) → `5a1e45e` (reconciled development state) → `36cbd3f` (production authentication & access gaps) → **`9e13236`** (routing fix). Local `main` == `origin/main` |
| Approval/billing crash (P0-2) | **Fixed and published** — `date_trunc('month', $2::timestamptz)::date` in `backend/data/billing.py`; live API evidence: 500 → **200** with item `approved` and `usage_tracking` written |
| Routing/deep-link defect | **Fixed and published** in `9e13236` (`cleanUrls: false`) |
| Production Supabase migration state | Migrations **22 → 53 remain NOT AUTHORIZED** for production application; no production migration was applied by any of these publications |

### F.2 Production verified

| Item | Evidence |
|---|---|
| Vercel deployment for `9e13236` | GitHub commit status `success` — `Vercel: "Deployment has completed"`, 2026-09-11T14:45:54Z |
| `cleanUrls: false` is live | `/index.html` returns **200** (previously 308 → `/`) |
| Public deep links, HTTP | `/`, `/login`, `/privacy`, `/terms`, `/auth/callback`, `/platform`, `/pricing`, `/admin` all **200** with the real SPA shell |
| Real-browser cold load **and in-place refresh** | Chromium 1440×900: `/`, `/login`, `/privacy`, `/terms`, `/auth/callback` all render on cold load **and** after reload; **0 console errors**; the original `/login` refresh defect no longer reproduces |
| Independent vantage point | A third-party JS-rendering client (different egress IP) rendered `/login` and the full `/privacy` policy |
| Authentication/authorization boundaries | Server-authoritative landing + fail-closed resolution + RLS isolation (cross-tenant reads return zero rows) independently verified |

**Verification record:** `docs/cline/prompt-history/CT-PROD-DEEP-LINK-DEPLOY-VERIFY-20260911-001.md` —
`PRODUCTION DEEP-LINK ROUTING VERIFIED — PASS`.

### F.3 Externally configured — NOT repository-controlled

| Item | Position |
|---|---|
| Supabase Auth **Site URL** + redirect allow-list | Must include `https://carbontally.co.uk` and `https://carbontally.co.uk/auth/callback`. PO-owned dashboard item |
| Google Cloud **OAuth consent** (app name "CarbonTally", authorised domain `carbontally.co.uk`, privacy/terms URLs, support email, redirect URI to the Supabase project callback) | PO-owned dashboard item. The consent screen's hostname is Google/Supabase-controlled |
| Optional Supabase **custom domain** (e.g. `auth.carbontally.co.uk`) | Commercial decision; a paid add-on |
| Vercel project settings (Root Directory = repository root, Output Directory) | Repository config is the authority; any dashboard override is PO-owned |

### F.4 Controlled workarounds (acceptable today, manual by design)

Manual organisation onboarding · manual entitlement/subscription provisioning via a **documented SQL
runbook** (P0-4) · manual invoicing · manual work assignment by CarbonTally staff · manual failure triage
from the ops/QC queues · controlled customer count and processing volume.

### F.5 Deferred, evidence gaps, and post-launch items

| Class | Items |
|---|---|
| **Deferred (low priority, recorded)** | **F1** — a *missing* static asset returns 200 + the HTML shell instead of 404 (the `/static/(.*)` and `/admin/(.*\..*)` rules are identity no-ops, so misses fall through to the catch-all). Pre-existing; Low severity; does not affect any user-facing route. **F3** — an unknown *client* route returns 200 + shell and the client router then goes to `/`, so no "page not found" state is shown (informational UX). P3 test-infrastructure findings LT-2/V1/V2/V3 · the parked **backup/DR** workstream (see below) |
| **Evidence gaps** | **P0-3** — the calculation pipeline has not been evidenced end-to-end on real customer-shaped data with automated evidence (upload → extract/OCR → map → factor match → calculate → validate → approve → export) · **production OCR dependency unverified** · the remaining D11 lifecycle events not all evidenced · full regression completion · reset/reseed reproducibility · P6-2F residual evidence limits (§D) |
| **Operational floor** | Monitoring/alerting: logging plus health-ish endpoints only — no metrics/alerting for background failures (P1) · retention enforcement unevidenced (P1) |
| **Backup / DR** | **NOT PERFORMED — parked**; `DR-20` remains NOT SATISFIED. Roadmap exists (`CARBONTALLY_PRODUCTION_BACKUP_RESTORE_ROADMAP_V1.0.md`) with Phase 1 and P1.1 independently verified; it is **not** part of the Phase 1–6 product scope |
| **Subscription / allowance provisioning** | **P0-4 open** — the isolated environment required a hand-built `customer_subscriptions` row plus `billing_commercial_config['standard_allowance']`; the admin path must be confirmed or the SQL runbook published as the launch workaround. Entitlement gating itself is confirmed **fail-closed** (403 `No active processing entitlement`) |
| **Billing** | P0-2 fixed and published; job-review billing deliberately deferred (D3); commercial configuration is administrative |
| **Launch posture** | `YES, AFTER P0 FIXES` — P0-1 done, P0-2 done, **P0-3 and P0-4 outstanding** |
| **Post-launch (P3)** | Advanced analytics · benchmarking · Phase-7 auditor/assurance capabilities · cross-customer aggregation · UI polish · harness re-runnability tooling · scale optimisation |

---

## G. Authentication and access

The definitive, implementation-verified matrix lives in **§12 "Definitive Authentication & Access Matrix"** of
`docs/architecture/CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md` — dimensions covered: actor/role,
authentication method, public entry point, OAuth callback, post-authentication destination, workspace,
authorization model, capability requirements, organisation/firm/PE data scope, RLS boundary, backend/API
boundary, session restoration, session expiry, logout, unauthorized, forbidden, unprovisioned-user behaviour
and relevant special cases — for organisation users, consultants, Processing Entities, CarbonTally internal
staff, and authenticated-but-unprovisioned users.

Summary invariants (must remain true):

* `/login` is the **common** public authentication entry point; `/auth/callback` is the OAuth return route.
* Landing is **server-decided** by `GET /api/v3/me/context` (`/home`, `/consultant`, `/pe`, `/ops`,
  `/onboarding`) — a client cannot choose its workspace, and a resolution failure **fails closed**.
* **The URL is not the authorization boundary.** Enforcement is server-side authorization + capability checks
  + tenant/firm/PE scope + RLS; frontend guards are UX only (D25).
* **Auth-service unavailability must never be confused with 401/403 authorization failure, and must never
  grant or widen access** — verified in `frontend/src/lib/authErrors.js`
  (`AUTH_SERVICE_UNAVAILABLE` vs `INVALID_CREDENTIALS` vs `UNAUTHORIZED` vs `FORBIDDEN` vs
  `UNKNOWN_APPLICATION_ERROR`) and in the branded notice rendered by `AuthServiceUnavailable.jsx`.
* The verified authentication methods are **email/password** and **Google OAuth**; no method was added,
  removed or weakened by the Phase 1–6 closure work. Magic-link exists as a route but is not a documented
  supported production method; no password-reset or invitation flow was found.

## H. Known residual findings

| Class | Findings | Blocking? |
|---|---|---|
| **Blockers (closure)** | **None.** No Phase 1–6 gate is blocked, no P0/P1 security finding remains open, and no cross-tenant authorization defect was found | — |
| **Blockers (first paying customer)** | **P0-3** customer-shaped end-to-end calculation evidence · **P0-4** subscription/allowance provisioning operability. Both are **product/commercial readiness** items, **not** Phase 7 blockers and **not** security defects | Block first customer, not Phase 7 **specification** |
| **Non-blocking findings (accepted)** | LT-2 (P3, stale `carbontally_test` schema → real-SQL coverage gap) · V1 (P3, fixture-order-sensitive browser spec) · V2 (P3, seeder summary on re-run without reset) · V3 (P3, pre-existing `test.skip(!visible)` guard pattern) · the three P6-2C non-blocking findings · P6-2D/P6-2E non-blocking findings — all recorded, none downgraded, none re-opened | No |
| **Controlled workarounds** | Manual onboarding, manual entitlement/subscription provisioning (documented runbook), manual invoicing, manual assignment, manual failure triage, controlled customer volume (§F.4) | No |
| **Deferred improvements** | **F1** missing-asset 404 masking (Low, pre-existing) · **F3** no client-side "not found" state for unknown paths · backup/DR workstream (parked) · monitoring/alerting and retention enforcement | No |
| **Evidence gaps** | P6-2F residual limits (§D) · production OCR dependency · remaining D11 events · full regression completion · reset/reseed reproducibility | No |

**Doctrine (from the operating constitution):** no finding is to be silently downgraded; an unverified item is
never reported as verified; and accepted residuals are revisited only on **material** evidence.

## I. Explicit non-scope

* **No Phase 7 implementation has occurred.** Phase 7 is *name-ratified only* — its scope is **not defined** and
  nothing about it is authorised.
* **No Phase 8 implementation has occurred.** Same position: name-ratified, scope undefined, unauthorised.
* **`/demo` has NOT been implemented** and **must not be implemented** before all roadmap features through
  Phase 8 **and** the final comprehensive system/documentation audit are complete.
* **`/investors` has NOT been implemented** and is deferred under exactly the same condition.
* Verified in the current route table (`frontend/src/App.js`): there is **no `/demo` and no `/investors`
  route**. (Interactive marketing demos exist as components *inside* public pages, e.g. under
  `frontend/src/public/demos/`; that is public-site content, not a `/demo` experience, and it is unchanged by
  this record.)
* No database, migration, RLS, API, billing, frontend, authentication, Google, Supabase, Vercel or deployment
  configuration was changed by this closure task.

---

## J. Phase 7 starting conditions

**Phase 7 is NOT authorised to implement anything by this record.** Phase 7 is *name-ratified only*
("Auditor / Assurance" per `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` §10); no repository artifact defines
its scope, and no Phase-7 architecture, roles, workflows, APIs, schema, migrations, UI or billing change is
authorised.

**Phase 7 must begin with SPECIFICATION, not coding.** The next session must first establish, and the Product
Owner must then ratify:

1. requirements and product objective;
2. architecture;
3. data model;
4. workflows;
5. authorization / RLS;
6. APIs;
7. UI / UX;
8. billing implications (if applicable);
9. audit and provenance;
10. security;
11. acceptance criteria;
12. test strategy;
13. implementation gates;
14. independent-verification criteria.

**No Phase 7 implementation may begin until the PO ratifies that specification.**

**Phase 7 must NOT assume:**

* that any Phase 7 scope already exists — it does not;
* that accepted Phase 1–6 residuals (LT-2, V1–V3, F1, F3, P0-3/P0-4) are resolved or resolve-able inside
  Phase 7 — they are separately owned;
* that unverified items are verified (notably customer-shaped end-to-end calculation evidence);
* that production migrations 22 → 53 have been applied — they remain **NOT AUTHORIZED**;
* that backup/DR exists — it is parked and `DR-20` is NOT SATISFIED;
* that external dashboard configuration (Google OAuth consent, Supabase Site URL/redirect allow-list) is done;
* that `/demo` or `/investors` may be started at any point before the post-Phase-8 audit;
* that any legacy "Phase 7" numbering found elsewhere in the repository applies
  (`CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` §15 — multiple incompatible uses exist);
* that the Phase-6 processing model may be collapsed (Consultant ≠ manual, Organisation ≠ automatic,
  CarbonTally internal ≠ automatic, PE ≠ generic actor/mode equivalence).

**Ratified Phase 7/8 sequencing (must not be altered):**

```text
1. Phase 7 detailed specification
2. PO ratification
3. Phase 7 implementation
4. Phase 7 independent verification
5. Phase 7 closure
6. Phase 8 detailed specification
7. PO ratification
8. Phase 8 implementation
9. Phase 8 independent verification
10. Phase 8 closure
11. comprehensive system + documentation audit
12. only then /demo and /investors
```

---

## K. Continuity protocol (for every future session)

Future ChatGPT / Cline / OHD sessions must:

1. **read the Blueprint** — `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`;
2. **read the Master Roadmap** — `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`;
3. **read this closure/continuity record**;
4. **read the relevant phase-specific architecture / gate records** (e.g. `CARBONTALLY_PHASE6_*`,
   `CARBONTALLY_P6_*`, the authentication/access specification, the production-readiness audit);
5. **inspect prompt history** (`docs/cline/prompt-history/`) for unresolved decisions and the latest verified
   state;
6. **never infer that an unverified item is verified**;
7. **never reopen closed work without material evidence**;
8. **never start implementation before the relevant phase specification is ratified**;
9. **preserve durable Markdown history for every bounded agent task** — and never claim a stronger acceptance
   state (`IMPLEMENTED` / `TESTED` / `VERIFIED` / `ACCEPTED`) than the evidence supports;
10. also consult Hindsight memory for durable decisions, treating it as context and **never** as proof of
    current code, database, runtime, security or test state.

**Start-of-session check:** `git status` · `git branch` · `git rev-parse HEAD` · compare with `origin/main` ·
confirm no Phase 7/8 code, migrations or configuration changes have appeared.

**Documentation set this record depends on (all pre-existing; none replaced, renamed, reorganised or
consolidated):** `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` ·
`CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` ·
`CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md` (incl. §12 matrix) ·
`CARBONTALLY_PRODUCTION_READINESS_AUDIT_20260911.md` ·
`CARBONTALLY_PHASE6_CLOSURE_AND_RELEASE_BOUNDARY_20260911.md` ·
`CARBONTALLY_P6_2F_INDEPENDENT_VERIFICATION_20260911.md` ·
`CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` ·
`CARBONTALLY_PRODUCTION_LOGIN_RUNBOOK_20260911.md` ·
`CARBONTALLY_POST_PUBLICATION_CHANGELOG_20260911.md` ·
`docs/cline/prompt-history/CT-PROD-DEEP-LINK-DEPLOY-VERIFY-20260911-001.md`.

**Consistency observations (recorded, NOT silently reconciled):**

1. The Master Roadmap's phase-status snapshot (§13/§14) shows Phase 6 `IN PROGRESS (P6-2B closed)`, Phase 4
   `DESIGN COMPLETE — AWAITING PO APPROVAL` and Phase 5 `IN PROGRESS / ACCEPTANCE PARTIAL`, because it
   predates the later Phase-6 gate closures. The **later** closure record is the authority for the Phase 6
   position. This is chronological staleness, not an architectural contradiction, and **no authoritative
   document was modified** to reconcile it.
2. The readiness audit reports **116 RLS tables / 175 policies**, measured **live at the database boundary**,
   whereas the repository migrations contain **21** `enable row level security` statements and **68**
   `create policy` statements. These are **different evidence bases** (live database vs repository migration
   history), not a contradiction.
3. The readiness audit's own HEAD and P0-1 statement describes the **pre-publication** state and is superseded
   by the published commits listed in §F.1.

**Two PO-owned items carried forward (neither authorises nor blocks Phase 7 specification):**
the Phase 4 §21 design-option decision, and the Phase 5 WS4 closure-run decision.
