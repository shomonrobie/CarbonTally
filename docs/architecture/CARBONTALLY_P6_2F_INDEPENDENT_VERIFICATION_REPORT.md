# CarbonTally — P6-2F Independent Verification Report

**Prompt Ref:** `CT-P6-2F-IV-20260910-001`
**Date/time:** 2026-09-11, 00:33 → 01:05 (+0600); repository clock captured `2026-09-11 00:47:58 +0600`
**Phase / Gate:** Phase 6 · P6-2F — Full UI/UX + E2E Security Acceptance
**Mode:** INDEPENDENT VERIFICATION — READ ONLY
**Verifier:** OpenHands (OHD), fresh independent-verification session
**Implementation agent (verified subject):** Cline — `CT-P6-2F-IMPL-20260910-001`
**Independence:** FRESH SESSION — no implementation context, no continuation of the implementation session

**Final verdict:**

> **`P6-2F INDEPENDENT VERIFICATION — ENVIRONMENTALLY BLOCKED`**

with **three blocking acceptance findings (BLK-1 … BLK-3)** and eleven non-blocking findings (NB-1 … NB-11).

---

## 1. Prompt Ref

`CT-P6-2F-IV-20260910-001` — "CarbonTally — P6-2F Independent Verification" (46 sections).

## 2. Date/time

2026-09-11 00:33 → 01:05 (+0600). Repository clock at verification: `2026-09-11 00:47:58 +0600`.

## 3. Verifier identity

OpenHands (OHD), acting as the independent verification agent. Read-only session. No remediation.

## 4. Independence statement

This session is a fresh verification session. It did not inherit the implementation session's
context, did not read the implementation report as proof, and re-derived every material claim from
the repository, the executable tests, and direct execution.

* Every test result quoted below was produced by **this** session (commands in §31), not copied from
  the implementation report.
* Every code claim was checked by reading the actual file, including files the implementation report
  did **not** mention (routing table, authorization helpers, migrations, git state).
* Three claims in the implementation report were found to be **inaccurate** (§8, §32).
* The verifier deliberately did **not** treat the implementation report's prose as evidence; where
  only repository evidence (not execution) was available, this is stated explicitly.

**Disclosed limitation of independence:** the implementation session ended at approximately
2026-09-11 00:28 and this verification session began at approximately 00:33 — minutes later, on the
same machine and the same (uncommitted) working tree. The session itself is fresh and shares no
context, but the temporal adjacency is recorded for transparency: the verification is independent in
context, not distant in time.

## 5. Authority sources inspected

| # | Authority | Used for |
|---|---|---|
| 1 | `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` | architecture source of truth |
| 2 | `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` | gate sequence P6-2C to D to E to F |
| 3 | `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md` | D6/D7/D8/D11, D11-C1, `PO-PHASE6-F-ACC-20260910`, `PO-PHASE6-F-ENV-20260910`, `PO-PHASE6-CAMPAIGN-20260910`, `PO-PHASE6-BILL-DEFER-20260910`, frozen P6-2C invariants |
| 4 | `docs/architecture/CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md` | §4, §6 to §8, §10, **§11 CP3**, **§12 E2E environment**, §13 checkpoints, §14 fresh session, §15 invariants, §16 scope, §17 classification, §18 evidence, §19 stop conditions |
| 5 | `docs/architecture/CARBONTALLY_CP2_CLOSURE_P6_2F_PREFLIGHT_REPORT.md` | CP2 closure, P6-2F ratified definition, gaps G1 to G8 |
| 6 | `docs/cline/CARBONTALLY_CP1_CLOSURE_REPORT.md` | CP1 closure (note: under `docs/cline/`, not `docs/architecture/`) |
| 7 | `docs/cline/CARBONTALLY_P6_2E_PREFLIGHT_REPORT.md` | P6-2E readiness (same location note) |
| 8 | `docs/cline/CARBONTALLY_P6_2E_INDEPENDENT_VERIFICATION_REPORT.md` | IV-N1 to IV-N8, IV-E1 to IV-E3 |
| 9 | `docs/cline/CARBONTALLY_P6_2E_IMPLEMENTATION_REPORT.md` | P6-2E baseline behaviour |
| 10 | `docs/architecture/CARBONTALLY_P6_2F_IMPLEMENTATION_REPORT.md` | the claims under verification |
| 11 | `docs/cline/prompt-history/CT-P6-2F-IMPL-20260910-001.md` | the exact P6-2F implementation prompt (CP-F0 to CP-F8, §40 completion criteria) |
| 12 | `docs/cline/prompt-history/CT-CP2-CLOSE-P6-2F-PREFLIGHT-20260910-001.md` | CP2 closure prompt |
| 13 | `docs/cline/CARBONTALLY_PHASE6_REMAINDER_PO_RATIFICATION_REPORT.md` | PO ratification of the remainder decisions |
| 14 | Repository source: `backend/api/**`, `backend/services/consultant_lifecycle.py`, `backend/domain/processing_origin.py`, `backend/tests/**`, `frontend/src/App.js`, `frontend/src/v3/**`, `supabase/migrations/**`, `qa_harness/**`, `playwright.config.ts`, `tests/**` | implementation truth |

Documents named in the task's source list that are **not** at `docs/architecture/`:
`CARBONTALLY_PHASE6_REMAINDER_PO_RATIFICATION_REPORT.md` (found at `docs/cline/`),
`CARBONTALLY_CP1_CLOSURE_REPORT.md` and `CARBONTALLY_P6_2E_PREFLIGHT_REPORT.md` (both at
`docs/cline/`). This is the pre-existing preflight gap **G8**, recorded and not corrected.

## 6. Scope

Verification of the P6-2F implementation against the ratified P6-2F requirements: UI/UX completion
(consultant surface + IV-N6 deep link), isolated E2E environment, browser/application ALLOW and DENY
coverage, D6/D7/D8/D11 preservation, processing-origin and billing preservation, IDOR / alternate
route / injection / replay resistance, regression, and test integrity.

Not in scope: remediation, implementation, environment provisioning, Phase 7, Phase 8, PO
adjudication.

## 7. Repository state

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `16391217103b98dcea520070c5a22c68f12fe607` (`1639121`) — **unchanged by P6-2F and by this verification** |
| Working tree | 679 porcelain entries: 242 untracked (`??`), remainder modified/deleted — **all pre-existing / previous-phase work; nothing staged** |
| Staged | none (`git diff --cached --stat` empty) |
| Commit / push | **none** — the implementation agent's no-commit/no-push claim is **CONFIRMED** |
| P6-2F footprint (mtime-derived, 2026-09-10 22:00 to 2026-09-11 01:00) | **modified:** `backend/services/consultant_lifecycle.py` (00:10), `frontend/src/v3/api.js` (00:12), `frontend/src/v3/consultant/ConsultantItemPage.jsx` (00:23), `playwright.config.ts` (00:18). **created:** `backend/tests/e2e/**` (8 files), `tests/e2e/**` (6 files), `docs/architecture/CARBONTALLY_P6_2F_IMPLEMENTATION_REPORT.md`, `docs/cline/prompt-history/CT-P6-2F-IMPL-20260910-001.md` |
| Files P6-2F did **not** touch | `frontend/src/v3/__tests__/api.test.js` (mtime 2026-08-31, so its tracked modification is pre-existing), no `supabase/migrations/**` file, no billing file, no RLS file, no `qa_harness/**` file |
| New migrations by P6-2F | **none** — the newest migration is `20260910120000_p6_2d_consultant_provenance.sql` (2026-09-10 19:21) |

Mtime attribution is used because the whole Phase-6 remainder is uncommitted, so `git diff` cannot
separate P6-2F from earlier phases. The mtime window is consistent with the implementation report's
own file lists, with the three exceptions recorded in §8 and §32.

## 8. Implementation claims examined

| Claim | Result |
|---|---|
| backend unit: 1654 passed / 0 failed / exit 0 | **INDEPENDENTLY VERIFIED** (1654 passed, 1 warning, exit 0, 267.35s) |
| P6-2E focused: 27 passed / 0 failed / exit 0 | **INDEPENDENTLY VERIFIED** (27 passed, exit 0) |
| backend E2E: 39 passed / 0 failed / exit 0 | **INDEPENDENTLY VERIFIED** (39 collected = 8+4+16+11; 39 passed, exit 0) |
| browser route protection: 7 passed / exit 0 | **INDEPENDENTLY VERIFIED** in real Chromium against an isolated frontend build |
| browser collection: 15 tests / 3 files | **INACCURATE — the actual collection is 16 tests in 3 files** (NB-1) |
| frontend `ConsultantItemPage.jsx` + `api.js` changed | **VERIFIED** (§10 to §12) |
| backend `consultant_lifecycle.py` changed (IV-N6) | **VERIFIED** (§12) |
| `backend/tests/e2e/**`, `tests/e2e/**`, `playwright.config.ts` added/changed | **VERIFIED** |
| No migrations / no RLS changes / no billing changes | **VERIFIED** (mtime + source inspection) |
| D6 / D7 / D8 / D11 / D11-C1 preserved | **VERIFIED** (repository evidence; §13 to §18) |
| IV-N6 fixed | **VERIFIED** (§12) |
| consultant workspace route defect fixed | **VERIFIED** (code + independent test run) |
| ALLOW + DENY application-level security tests | **VERIFIED as application-level (in-memory) tests** — they are **not** browser or RLS tests (§30, NB-6) |
| browser route-protection tests | **VERIFIED** (7 executed / passed) |
| authenticated browser tests authored but skipped (no isolated Supabase E2E env) | **CONFIRMED** — 8 of 16 browser specs skip; this is the core blocking gap (BLK-1/BLK-2) |
| `backend/tests/e2e/README.md` created | **INACCURATE — the file does not exist** (NB-2) |

## 9. CP-F0 result

Independent reconnaissance confirms the structural picture in the implementation report, with these
corrections and additions:

* **Frontend** — CRA React 18 + React Router 7. `/consultant` and
  `/consultant/items/:clientId/:itemId` both exist and are wrapped in `ProtectedRoute` +
  `RoleRoute requireConsultant` (`frontend/src/App.js:2160`, `2169`). `/ops` requires `requireStaff`.
  **There is no `/admin` route at all** (`grep -c 'path="/admin' frontend/src/App.js` = 0); the SPA
  catch-all `*` redirects to `/`, and the admin pages are mounted at `/organization` under
  `requireOrg`. This matters for one browser test (NB-4).
* **Backend** — FastAPI composition root `api.router.create_app`. `GET
  /api/v3/processing/items/{id}/workspace` is guarded by `require_auth()` + `_get_checked_item()` to
  `ensure_processing_org_access()` (organisation member, or consultant with an **active**
  `consultant_clients` grant; PE staff explicitly denied). `POST
  /api/v3/ops/items/{id}/submit-review` is guarded by `require_staff` + `require_internal_staff` +
  `can_review`. Server-side authorization is real and unchanged.
* **E2E layer as delivered** — two layers:
  1. `backend/tests/e2e/**` — the **real FastAPI app** with `get_current_user`, `get_repositories`,
     `get_audit_logger`, `get_event_bus` and `get_factor_search_index` **overridden with in-memory
     fakes** (`conftest.py`). No database, no Supabase Auth, no RLS.
  2. `tests/e2e/**` — Node Playwright specs (unauthenticated route protection executes; the
     authenticated specs skip without env vars).
* **No isolated E2E environment was provisioned.** There is no seeding script, no environment
  configuration, no synthetic-identity creation, no teardown, and nothing that populates the `E2E_*`
  variables `tests/e2e/personas.ts` reads. The personas are env-var placeholders only.

## 10. UI/UX verification

| P6-2F UI/UX requirement | Evidence | Result |
|---|---|---|
| Consultant item workspace loads from a consultant-authorised route | `ConsultantItemPage.jsx` calls `getConsultantItemWorkspace`; `api.js` maps it to `/api/v3/processing/items/{id}/workspace`; independently executed (`test_granted_consultant_reads_client_item_workspace`, `test_deeplink_route_resolves_for_the_granted_consultant`) | **VERIFIED (API execution + repository evidence)** |
| Consultant review / rework / submit-to-QC controls exist | `ConsultantItemPage.jsx` — Pass review, Request rework (reason required), Submit to CarbonTally QC, gated on `calculated` / `consultant_reviewed`, with busy / notice / error handling | **VERIFIED (repository evidence)** |
| Workflow labels in business language (D19/D21) | `STATUS_LABELS` renders e.g. "Calculated — ready for consultant review" | **VERIFIED (repository evidence)** |
| Loading / error / denied states | `LoadingState`, `ErrorState`, inline error on a denied action | **VERIFIED (repository evidence)** |
| The rendered consultant UI actually works in a browser | 4 browser specs cover it, and **all 4 SKIP** (no credentials / ids) | **NOT VERIFIED — BLK-2** |
| The UI work is covered by any executed test | no frontend unit test for the three new helpers (`api.test.js` unchanged since 2026-08-31 and does not list them); no component test; browser specs skip | **NO EXECUTED COVERAGE — NB-8** |
| Customer / Internal / Processing-Entity UI acceptance | browser coverage: one unauthenticated API call, no customer UI, no PE | **NOT VERIFIED for PE — BLK-3** |

No subjective redesign review was performed; only contractual/product requirements were checked. No
visual, token or D21 conformance defect was found in the changed files.

## 11. D19/D21 verification

The P6-2F preflight (G5) listed "Consultant UI surface completeness (review/submit controls,
notification surfacing) not yet verified against D19/D21" as a P6-2F deliverable.

| D19 / D21 requirement | Evidence in the P6-2F change | Result |
|---|---|---|
| Preserve the D19 processing-workbench structure (approved panes, source/data context) | `ConsultantItemPage.jsx` keeps the existing workbench shell (`v3-ops-page` / `v3-ops-header`, `ExtractionPanel` reused for source + data) and **adds** an action bar rather than restyling it | **PRESERVED — VERIFIED (repository evidence)** |
| Do not replace D19 | no route, shell or pane was replaced; the only structural change is that the workspace now loads from the consultant-authorised `processing` route | **VERIFIED** |
| D21 semantic tokens / no legacy or one-off styling | the new controls use the existing `Button` component (`size="sm"`, `variant="secondary"`), existing `LoadingState` / `ErrorState`, and existing CSS classes; no new visual system, no inline colour/typography system | **VERIFIED (repository evidence)** |
| D21 consistency (loaded/empty/error/denied states) | `LoadingState`, `ErrorState`, inline `error`/`notice` states present | **VERIFIED (repository evidence)** |
| Keyboard accessibility of the new controls | the controls are native `Button` elements inside the existing workspace; no custom non-focusable control was introduced | **VERIFIED (repository evidence, not automated)** |
| D19/D21 verified in a rendered browser | the 4 browser specs that would cover it **skip** | **NOT VERIFIED — BLK-2** |
| Processing Entity workspace (D19 PE shell) | untouched and untested | **NOT VERIFIED — BLK-3** |

No subjective redesign assessment was performed; only contractual D19/D21 requirements were checked.
No D21 token violation, no new design system, no new route, no new role and no new capability was
introduced by the P6-2F UI change.

## 12. IV-N6 deep-link verification

The P6-2E defect: notifications linked to `/consultant/items/{itemId}`, while the real frontend route
is `/consultant/items/:clientId/:itemId`.

Independently verified end to end:

1. **Notification generation / link** — `_consultant_item_link(item_id, client_id)` returns
   `"/consultant/items/{client_id}/{item_id}"` (`backend/services/consultant_lifecycle.py:228-239`),
   falling back to `_NOTIFICATIONS_LINK = "/notifications"` when the engagement id cannot be resolved.
2. **Generated URL** — `_consultant_link_for()` builds `{user_id: link}` from the organisation's
   **active** grants (`_client_id_by_firm` to `list_active_client_grants`) and is passed to `_emit` as
   `link_for` for events 2-5; `_emit` resolves it **per recipient**
   (`link=(link_for(user_id) if link_for is not None else link)`). Event 1 (`accepted`) keeps
   `/consultant`.
3. **Actual route** — `frontend/src/App.js:2169`
   `<Route path="/consultant/items/:clientId/:itemId" ...>` wrapped in `ProtectedRoute` +
   `RoleRoute requireConsultant`. The emitted shape now matches.
4. **Required identifiers** — `:clientId` is the recipient firm's engagement id
   (`consultant_clients.id`), resolved **server-side**; `:itemId` is the item id. The page consumes
   both via `useParams()` and calls `getClientProcessingItems(clientId)` plus the processing workspace.
5. **Navigation** — `NotificationsPage.jsx:135` renders `<Link to={notification.link}>`, and the
   P6-2F browser spec asserts the heading "Client item workspace" after the click.
6. **Authorization on navigation** — the deep link is a presentation aid only; the item page then
   calls two **server-authorised** endpoints.
   `test_deeplink_route_resolves_for_the_granted_consultant` (200) and
   `test_deeplink_route_is_denied_for_an_unrelated_consultant` (403/404) both pass.
7. **Manipulated identifiers** — firm B substituting firm A's `clientId`/`itemId` is denied
   (`test_deeplink_route_is_denied_for_an_unrelated_consultant`,
   `test_idor_swapped_identifiers_are_denied`).

**ALLOW — VERIFIED** (application level). **DENY — VERIFIED** (application level).
**Browser-level ALLOW/DENY — NOT EXECUTED** (the specs skip; BLK-2). The link string was not merely
changed: the route it targets exists, its identifiers are correct and server-derived, and the
authorization behind it holds in the executed tests.

Residual (carried, pre-existing, unchanged by P6-2F): recipients for events 2-5 that are **not** firm
members (internal ops) fall back to `/notifications`; and per IV-N5 a repeated occurrence can be
suppressed, so no link is re-emitted.

## 13. D6 verification

| Requirement | Evidence | Result |
|---|---|---|
| Preflight does not consume entitlement | `POST /items/{id}/consultant-submit` calls `BillingService.ensure_processing_entitlement()` **read-only**, after authorization and state eligibility, **before** any mutation (`backend/api/v3_processing_workflow.py:766-776`) | **VERIFIED (repository evidence)** |
| Canonical approval-time enforcement | single charge site at customer approval: `charge_processing(..., idempotency_key=f"charge:item:{item.id}")` (`v3_processing_workflow.py:987-999`); no billing file touched by P6-2F | **VERIFIED (repository evidence)** |
| Insufficient entitlement denies | `test_d6_entitlement_is_required_and_org_owned` — Org B (no entitlement) submit = 402/403 and the item is unchanged. **Independently executed: PASS** | **VERIFIED** |
| Organisation ownership | the preflight and the charge both use `batch.organization_id`, derived server-side; the request body is never consulted | **VERIFIED (repository evidence)** |
| No accidental billing change | no billing file in the P6-2F footprint; no new migration; `PO-PHASE6-BILL-DEFER-20260910` intact | **VERIFIED** |
| No charge on denial | `test_d6_no_charge_on_denied_submission` asserts the denial and the unchanged item but does **not** assert credit/ledger state | **PARTIALLY VERIFIED — NB-5** |
| Real entitlement behaviour at the live boundary (DB / browser) | not exercised (in-memory only) | **NOT VERIFIED — BLK-2** |

## 14. D7 verification

* **Server-derived firm** — `_record_consultant_provenance()` resolves the firm through
  `resolve_consultant_firm_id()` from the authorised membership/engagement relationship; a
  request-supplied firm or organization value is never consulted
  (`backend/api/v3_processing_workflow.py:204-210`).
* **A client cannot supply a firm** — `test_actor_and_firm_injection_is_ignored` posts
  `consultant_firm_id: firm-b` and the stored firm remains `firm-a`. **Independently executed: PASS.**
* **Write-once / durable** — `test_d7_provenance_is_server_derived_and_write_once` shows a second
  `record_consultant_provenance(...)` returns `False` and changes nothing. **PASS.**
* **Authenticated actor is authoritative** — the provenance actor is `current_user.user_id`, never a
  body field.
* **Mode separate from origin** — `processing_mode` lives in the provenance record; `processing_origin`
  is a distinct field. Repository evidence confirms the separation; however the
  `test_d7_mode_is_separate_from_processing_origin` assertion is effectively vacuous for the seeded
  item (origin is `None`, and the test accepts `None`) — **NB-5**.
* **No historical backfill** — no migration added; the D7c prohibition is intact.

**D7: PRESERVED (VERIFIED at the application layer).** Live-database write-once enforcement
(constraint / RLS level) is **NOT VERIFIED** (BLK-2).

## 15. Processing-origin verification

* `backend/domain/processing_origin.py` defines exactly `CARBONTALLY_INTERNAL` and
  `PROCESSING_ENTITY`, plus `processing_origin_for_batch(entity_id)`.
* The CHECK constraint is intact and two-valued:
  `processing_origin IN ('CARBONTALLY_INTERNAL', 'PROCESSING_ENTITY')`
  (`supabase/migrations/20260902020000_v1_2_dual_origin_workflow.sql:78-80`).
* The P6-2D migration explicitly records that `processing_origin` is **untouched**
  (`20260910120000_p6_2d_consultant_provenance.sql:20,28`).
* P6-2F added no origin value, no routing change and no origin semantics (footprint §7).
* Injection: `test_processing_origin_injection_is_ignored` posts `processing_origin: "CONSULTANT"`;
  the stored value is `None` / `CARBONTALLY_INTERNAL` / `PROCESSING_ENTITY`, never `CONSULTANT`.
  **Independently executed: PASS.**

**Processing origin: PRESERVED — two values only, no third value, no client injection path.**

## 16. D8 verification

* Existing conversation model reused; no consultant conversation kind, no `consultant_conversations`
  table. `test_d8_conversation_kind_vocabulary_unchanged` scans `supabase/migrations/**` and asserts
  the vocabulary is a subset of `{org, entity}` — **independently executed: PASS**.
* Authorised consultant creates a conversation (201) and the participant role is `consultant`
  (`test_granted_consultant_can_message_client_org`, `test_d8_consultant_participates_with_role`) —
  **PASS**.
* Unauthorised consultant denied: `test_ungranted_consultant_cannot_message_client` returns 403 —
  **PASS**.
* Cross-organisation denial flows through the same `ensure_consultant_org_access` grant check used by
  the processing routes (repository evidence).
* **Direct URL in a browser / message creation through the real authenticated boundary: NOT EXECUTED**
  (the browser specs skip; BLK-2).

**D8: PRESERVED (contract model verified; live boundary NOT VERIFIED).**

## 17. D11 verification

Five lifecycle events verified independently in the executed application suite:

| Event | Trigger route | Deterministic key | Recipients | Result |
|---|---|---|---|---|
| 1 `accepted` | `POST /organizations/{org}/consultant-engagements/{id}/accept` | `consultant.lifecycle.accepted:engagement:<id>` | firm members | **PASS** |
| 2 `submitted_to_qc` | `POST /processing/items/{id}/consultant-submit` | `consultant.lifecycle.submitted_to_qc:item:<id>` | firm members **plus internal ops** | **PASS** |
| 3 `qc_outcome` | `POST /ops/qc/items/{id}/decision` | `...qc_outcome:item:<id>:approved` or `:rejected` | firm members | **PASS** |
| 4 `customer_decision` | `POST /processing/items/{id}/customer-review` | `...customer_decision:item:<id>:approved` or `:rejected` | firm members | **PASS** |
| 5 `rework` | QC rejection / consultant-review rejection | `...rework:item:<id>:ct_qc_rejected` or `:consultant_review_rejected` | firm members | **PASS** |

* **Durable and idempotent** — `notifications.create_idempotent` with the unique index
  `uq_notifications_event_key` (`supabase/migrations/20260902050000_phase5_notification_event_key.sql:16`).
  `test_d11_service_layer_replay_is_idempotent` shows a second call returns the same recipients and
  creates no new rows — **PASS**. Route-level replay: a second `consultant-submit` returns **409** with
  no new rows (`test_replay_does_not_duplicate_side_effects`) — **PASS**.
* **Server-derived recipients / injection** — `test_recipient_injection_is_ignored` posts
  `recipients`, `event_key` and `actor_domain`; exactly one key exists and `u-attacker` receives
  nothing — **PASS**.
* **Isolation** — `test_d11_recipients_never_leak_cross_tenant` asserts recipients are a subset of
  `{u-firm-a, u-ops}`, never firm B and never the client actor — **PASS**.
* **UI visibility of notifications** — repository evidence only (`NotificationsPage.jsx` renders
  recipient-scoped notifications with links). **Browser NOT EXECUTED** (BLK-2).

**D11: five events VERIFIED at the application layer, with durable, keyed, idempotent, isolated and
injection-proof recipients. Live-database idempotency and browser visibility are NOT VERIFIED
(BLK-2, NB-5).**

## 18. D11-C1 verification

The PO-ratified firm-centric recipient model is **INTACT**:

* Recipients are computed only by `_firm_recipient_user_ids`, `_engaged_firm_ids` and
  `_internal_ops_recipient_user_ids`, i.e. **firm members** plus internal ops for event 2.
* **No client-organisation recipient** is added anywhere: the client organisation is the *actor* for
  events 1 and 4 and is deliberately not notified of its own decision.
* `test_customer_approval_emits_decision_to_firm_only` asserts `recipients_for(key) == ["u-firm-a"]`
  **and** `"u-own" not in recipients_for(key)` — executed: **PASS**.
* P6-2F's only change to the emitter was the **link resolver**; the recipient derivation, the event
  keys and the event set are unchanged. No new D11 client-recipient behaviour was added.
* Existing client-facing workflow notifications remain governed by their own workflows; no D11
  surface was re-purposed.

**D11-C1: PRESERVED — VERIFIED.** The absence of client recipients is the ratified design and is
**not** classified as a defect.

## 19. Organisation isolation

* **ALLOW** — Org A owner, and a consultant granted Org A, read the Org A item workspace: 200
  (`test_org_owner_reads_own_item_workspace`, `test_granted_consultant_reads_client_item_workspace`)
  — **independently executed: PASS**.
* **DENY** — the Org B owner reading an Org A item: 403/404 (`test_cross_organisation_access_is_denied`)
  — **PASS**.
* Enforced server-side by `ensure_processing_org_access()` to `ensure_org_access()` for members and
  `ensure_consultant_org_access()` for consultants (repository evidence). Not a frontend check.
* **Browser-level cross-organisation DENY: NOT EXECUTED** — the browser suite contains **no**
  cross-organisation test at all (BLK-2, NB-8).
* Live RLS level: **NOT EXERCISED**.

## 20. Consultant-firm isolation

* **ALLOW** — Firm A (active grant for Org A) reads and acts on Org A work: **PASS**.
* **DENY** — Firm B (granted Org B only) submitting Org A work: 403/404
  (`test_cross_firm_consultant_is_denied`) — **PASS**.
* **DENY** — consultant with no grant: 403/404 (`test_consultant_without_grant_is_denied`) — **PASS**.
* **DENY** — suspended grant: 403/404 **and zero notification rows**
  (`test_suspended_grant_is_denied`) — **PASS**.
* **Grant scope** — `ensure_consultant_org_access` requires `consultant_clients.status == 'active'`;
  the `client_access` per-member shortcut does not independently grant organisation access
  (repository evidence).
* **IV-N2 breadth observed and consistent with the ratified model** — recipients derive from all
  **active grants for the organisation**, so two firms both holding active grants for one organisation
  are both notified about one firm's item. This is the P6-2E accepted residual (over-breadth among
  firms already authorised for that organisation, not cross-tenant leakage) and **no narrower policy
  was invented** by P6-2F. It is not a P6-2F defect.

## 21. Grants / capabilities

* Active grant permits the intended action: **ALLOW PASS** (§20).
* Missing grant denies: **DENY PASS** (`test_consultant_without_grant_is_denied`).
* Inactive/suspended grant denies: **DENY PASS** (`test_suspended_grant_is_denied`).
* Capability enforcement is server-side: a firm member with `can_submit=False` gets 403 with zero
  notifications (`test_consultant_without_submit_capability_is_denied`) — **PASS**.
* The capability resolver is the existing canonical one; no new capability, permission or role was
  created (no migration; footprint §7). `can_qc` is required for the CT-QC decision
  (`test_qc_decision_requires_can_qc`) — **PASS**.

## 22. IDOR

* Swapped **item** id (`GET /api/v3/processing/items/{itemA}/workspace` as firm B): 403/404 — **PASS**.
* Swapped **engagement** id (`GET /api/v3/consultants/clients/{clientA}/processing/items` as firm B):
  403/404 — **PASS**.
* (`test_idor_swapped_identifiers_are_denied`, independently executed.)

**IDOR: DENY VERIFIED at the application layer; browser and database layers NOT EXECUTED (BLK-2).**

## 23. Alternate routes

* `POST /api/v3/ops/items/{id}/submit-review` — guarded by `require_staff` +
  `require_internal_staff` + `can_review` (`backend/api/v3_operations.py:1956-1971`); DENY for an org
  owner **and** for a consultant: 403 (`test_alternate_internal_route_requires_staff`) — **PASS**, and
  **independently confirmed by source inspection**.
* `GET /api/v3/ops/items/{id}/workspace` — the route the consultant page previously used — remains
  staff-only, so the consultant UI change did not create a bypass; it removed one.
* **IV-N4 alternate routes are NOT covered by any test** — the implementation report claims IV-N4
  "authorization verified (alternate-route DENY tests)", but the suite contains **no** test for
  `POST /api/v3/automatic-processing/jobs/{job_id}/review` or
  `POST /api/v3/consultants/clients/{id}/reactivate` (grep: zero matches). **NB-3.**
* Browser DENY for an alternate route: one spec (`consultant cannot invoke the internal ops workspace
  route`) — **SKIPPED**.

## 24. Actor injection

* `test_actor_and_firm_injection_is_ignored` — an injected `actor` / `consultant_firm_id` is ignored;
  the stored firm is server-derived — **PASS**.
* Structurally, the actor comes from the authenticated `AuthUser` (`current_user.user_id`) and the
  `require_staff()` context; nothing in the changed code reads a client-supplied actor.
* **Test-strength note:** the injected fields are not declared by the endpoint's request model, so the
  "ignored" outcome is partly structural rather than behavioural. The property (a client-supplied
  actor is never trusted) is nonetheless sound in the source. Recorded as NB-9; same class as IV-N7(a).

## 25. Recipient injection

* `test_recipient_injection_is_ignored` — a body supplying `recipients`, `event_key` and
  `actor_domain` produces exactly one server-derived key and **no** row for `u-attacker` — **PASS**.
* Recipient selection is server-derived end to end (`_firm_and_ops` / `_consultant_link_for`); no code
  path accepts a recipient list from the request (source inspection).
* **Browser-level recipient-injection test: none** (NB-8).

## 26. Provenance injection

Covered in §14. Injected firm, actor and mode values have no effect; the persisted firm remains the
authenticated consultant's firm (**PASS**). No arbitrary mode or processing origin can be supplied
(§15).

## 27. Replay / idempotency

1. Legitimate action succeeds (submit returns 200, status becomes `reviewed`) — **PASS**.
2. The same operation replayed returns **409** (the state machine refuses) — **PASS**.
3. No duplicate durable side effect: the notification row count is unchanged — **PASS**.
4. No duplicate durable notification: deterministic key plus `uq_notifications_event_key`; the
   service-layer replay returns the same recipients and creates no rows — **PASS**.
5. Appropriate conflict response: 409 — **PASS**.

Residual (accepted, unchanged): **IV-N5** per-cycle idempotency collapse — keys carry no cycle
discriminator, so a second identical occurrence for the same item is suppressed. P6-2F did **not**
introduce a cycle discriminator or a schema change (correct per contract §19(3)).

## 28. Entitlement / billing security

* No entitlement bypass: the preflight fails closed and the denial path performs no mutation — **PASS**.
* No charge on a denied preflight: no billing call is reached on denial — **PASS** by source
  inspection; the *test* does not assert credit state (NB-5).
* Canonical approval-time consumption: single charge site `charge:item:{id}` at customer approval,
  organisation-owned — **VERIFIED (repository evidence)**.
* No consultant or PE transfer of entitlement: both the preflight and the charge use
  `batch.organization_id` — **VERIFIED**.
* No production billing change: no billing file in the P6-2F footprint; no new migration — **VERIFIED**.
* No real financial transaction was performed by the implementation or by this verification.

## 29. Browser / E2E verification

**Collection: 16 tests in 3 files** (`npx playwright test --list`, this session). The implementation
report's "15 tests" is inaccurate (NB-1).

Execution in this session against the isolated frontend build served by `tests/e2e/static-server.mjs`
(`/tmp/p6f_build`, built with an unreachable non-production Supabase endpoint), with **no** persona
environment variables set:

| File | Specs | Executed | Passed | Skipped | Failed |
|---|---|---|---|---|---|
| `carbontally/route-protection.spec.ts` (unauthenticated) | 7 | 7 | **7** | 0 | 0 |
| `carbontally/security-denies.spec.ts` | 5 | 1 | 0 | 4 | **1** |
| `carbontally/consultant-lifecycle.spec.ts` (authenticated ALLOW) | 4 | 0 | 0 | 4 | 0 |
| **Total** | **16** | **8** | **7** | **8** | **1** |

* `route-protection.spec.ts` run in isolation: **7 passed, 0 failed, exit 0** — **INDEPENDENTLY
  VERIFIED**, genuinely executed in real Chromium.
* Full-suite run: **7 passed, 8 skipped, 1 failed, exit 1**. The single failure is
  `security-denies.spec.ts > unauthenticated API calls are rejected`, which asserts `[401, 403]` for
  `GET /api/v3/notifications`; in this harness the request is served by the **static file server**,
  which answers 200 via SPA fallback. The spec therefore requires an API-proxied origin and is not
  reproducible against the documented static-server recipe (**NB-7**).
* **50% of the browser suite (8/16) never executes.** The entire authenticated browser layer — the
  consultant ALLOW workflow (deep link, review, rework, submit, notification click-through),
  cross-firm DENY, org-member approval DENY, ops-route DENY and the admin DENY — is **skipped**.
* **Browser coverage that does not exist at all:** cross-organisation DENY, entitlement/D6,
  messaging/D8, D11 notification behaviour, Processing-Entity workflow, recipient injection,
  replay/idempotency, and provenance/processing-origin injection.
* No executed browser spec touches a real authenticated security boundary; all executed specs are
  unauthenticated redirection checks. That satisfies the "client fails closed" presentation check but
  is **not** security-boundary acceptance.

**Conclusion: the unauthenticated browser layer is verified; the mandatory authenticated browser
ALLOW/DENY acceptance was NOT executed and is NOT verifiable here — the substance of BLK-2.**

## 30. ALLOW / DENY coverage matrix

| Invariant | ALLOW | DENY | Evidence | Live boundary |
|---|---|---|---|---|
| Organisation isolation | PASS (app) | PASS (app) | `test_org_owner_reads_own_item_workspace` (200); `test_cross_organisation_access_is_denied` (403/404) | NOT VERIFIED (no browser or DB test) |
| Consultant-firm isolation | PASS (app) | PASS (app) | `test_granted_consultant_reads_client_item_workspace` (200); `test_cross_firm_consultant_is_denied`, `test_consultant_without_grant_is_denied` (403/404) | NOT VERIFIED |
| Grant / capability | PASS (app) | PASS (app) | active grant 200; `test_suspended_grant_is_denied`, `test_consultant_without_submit_capability_is_denied` (403, zero notifications) | NOT VERIFIED |
| D6 entitlement | PASS (app) | PASS (app) | `test_d6_entitlement_is_required_and_org_owned` (200 / 402-403, item unchanged) | NOT VERIFIED |
| D7 provenance | PASS (app) | PASS (app) | `test_d7_provenance_is_server_derived_and_write_once`; `test_actor_and_firm_injection_is_ignored` | NOT VERIFIED (write-once at DB/RLS level) |
| Processing origin | PASS (app) | PASS (app) | two-value vocabulary and CHECK intact; `test_processing_origin_injection_is_ignored` | PRESERVED (no live exercise needed) |
| D8 messaging | PASS (app) | PASS (app) | 201 with participant role `consultant`; `test_ungranted_consultant_cannot_message_client` (403) | NOT VERIFIED (browser / direct URL) |
| D11 notification | PASS (app) | PASS (app) | five events; `test_d11_recipients_never_leak_cross_tenant`; `test_recipient_injection_is_ignored`; replay idempotent | NOT VERIFIED (live DB idempotency, browser) |
| IDOR | n/a | PASS (app) | `test_idor_swapped_identifiers_are_denied` (403/404) | NOT VERIFIED |
| Alternate route | PASS (source) | PASS (app + source) | `test_alternate_internal_route_requires_staff` (403); route guard inspected | IV-N4 routes **untested** (NB-3) |
| Actor injection | PASS (source) | PASS (app) | `test_actor_and_firm_injection_is_ignored` | NOT VERIFIED |
| Recipient injection | PASS (source) | PASS (app) | `test_recipient_injection_is_ignored` | NOT VERIFIED |
| Replay / idempotency | PASS (app) | PASS (app) | 409 plus unchanged rows; service-layer idempotency | NOT VERIFIED (DB-level `uq_notifications_event_key`) |
| **Processing Entity** | **NOT TESTED** | **NOT TESTED** | no PE in the scenario; the `pe_operator` persona is unused | **BLK-3** |
| **Browser authenticated boundary** | **NOT EXECUTED** | **NOT EXECUTED** | 8 of 16 specs skip | **BLK-2** |

No cell is marked PASS on the strength of the implementation report alone. "PASS (app)" means: the
real FastAPI route and the real authorization code, with repositories and `get_current_user`
overridden to in-memory fakes. The "Live boundary" column states whether the property was
demonstrated at the real database / RLS / browser boundary — except for presentation-level checks, it
was not.

## 31. Test results

All commands were run by this verifier; all counts are observed, not quoted.

| # | Command | Result | Exit |
|---|---|---|---|
| 1 | `cd backend && .venv/bin/python -m pytest tests/unit -p no:cacheprovider --tb=line` | **1654 passed, 1 warning in 267.35s** | **0** |
| 2 | `cd backend && .venv/bin/python -m pytest tests/unit/api/test_p6_2e_consultant_lifecycle.py -p no:cacheprovider -q` | **27 passed** | **0** |
| 3 | `cd backend && .venv/bin/python -m pytest tests/e2e -p no:cacheprovider -q` | **39 passed** | **0** |
| 4 | `cd backend && .venv/bin/python -m pytest tests/e2e --collect-only -q` | 8 + 4 + 16 + 11 = **39** | 0 |
| 5 | `npx playwright test --list` | **16 tests in 3 files** (report says 15 — NB-1) | 0 |
| 6 | `E2E_BASE_URL=http://localhost:3100 npx playwright test tests/e2e/carbontally/route-protection.spec.ts` | **7 passed (8.3s)** | **0** |
| 7 | `E2E_BASE_URL=http://localhost:3100 npx playwright test` | **7 passed, 8 skipped, 1 failed** | **1** |
| 8 | `cd frontend && CI=true npx react-scripts test --watchAll=false --silent` | **200 tests passed; 21 suites passed; 1 suite failed to run** (`src/App.test.js` — `Cannot find module 'react-router/dom'`, pre-existing/environmental, not P6-2F) | **1** |
| 9 | read-only `docker exec supabase_db_carbon_ledger psql ...` (catalogue queries only) | 116 public tables; `manual_extraction_items`, `consultant_clients`, `notifications`, `conversations`, `organizations`, `processing_entities` present; RLS **enabled** (`relrowsecurity = t`) on the four tables checked; 975 organisations, 917 consultant grants | 0 |

Interpreter: `backend/.venv/bin/python` (pytest 9.1.1, pytest-asyncio 1.4.0), the interpreter the
repository memory records as required. No spurious async failures occurred; the implementation
report's "transient wrong-interpreter run" did **not** reproduce.

**All four implementation-reported suites reproduce exactly**, with one collection-count discrepancy
(15 reported vs 16 actual) and one suite the implementation never ran (frontend) which is not green
for a pre-existing environmental reason.

## 32. Test-integrity assessment

1. **The `backend/tests/e2e` layer is not end-to-end.** `conftest.py` overrides `get_current_user`,
   `get_repositories`, `get_audit_logger`, `get_event_bus` and `get_factor_search_index` with
   in-memory fakes. There is no database, no Supabase Auth and no RLS. It is a real-route,
   real-authorization-code API suite — valuable, but **not** the browser/RLS acceptance the gate
   mandates, and it cannot evidence RLS enforcement or real authentication. (BLK-2)
2. **Authentication is faked.** `UserProvider.set_user()` / `set_unauthenticated()` replaces
   `get_current_user`. The 401 test exercises the dependency contract, not Supabase Auth.
3. **The authorisation code paths are not mocked** — only persistence and identity are substituted —
   so the suite is genuine evidence of server-side authorization decisions, and no test was written
   to pass while authorization was broken.
4. **Skips are honest but numerous.** The 8 skipped browser specs skip explicitly (`test.skip(...)`)
   when credentials or ids are absent; they never silently pass. They are nevertheless **not**
   passing verification.
5. **One browser spec cannot fail meaningfully** (NB-4): `security-denies.spec.ts > consultant cannot
   reach the admin control plane` asserts the absence of an "admin control plane" heading. There is
   **no `/admin` route**; the SPA catch-all redirects to `/`. The assertion holds for any app state,
   so the spec would pass even if a consultant could reach every privileged surface that exists.
6. **A vacuous invariant assertion** (NB-5): `test_d7_mode_is_separate_from_processing_origin`
   accepts `origin is None`, so the "separation" property is not exercised for the seeded item.
7. **A denial test that does not assert the financial property** (NB-5):
   `test_d6_no_charge_on_denied_submission` asserts a 409 and an unchanged status but never checks
   credits or the ledger, so "no charge on denied submission" is not demonstrated by an assertion.
8. **Weak-but-acceptable matchers**: several DENY assertions accept `in (403, 404)`
   (`test_cross_organisation_access_is_denied`, `test_consultant_without_grant_is_denied`,
   `test_cross_firm_consultant_is_denied`, `test_suspended_grant_is_denied`, IDOR, deep-link deny) —
   the same class as the accepted IV-N7(b).
9. **No database-level idempotency test** — IV-N7(d) remains open: `uq_notifications_event_key` is
   exercised only through the fake's `event_keys()` accessor.
10. **No global or unconditional skips.** The Python suites report zero skips; the browser skips are
    environment-conditional, not blanket. No `pytest.ini` or global `conftest` skip was added.
11. **No test was weakened or modified to make anything pass**; no test file from an earlier phase
    was edited by P6-2F (mtime evidence, §7).
12. **Harness integration**: the new layer does not use `qa_harness` and produces no
    PASS / FAIL / SKIPPED / BLOCKED / UNVERIFIED status output (NB-6). `qa_harness` was left intact,
    and its browser runner does not consume `playwright.config.ts`, so the `testDir` change caused no
    qa_harness regression.

**Documentation accuracy (implementation report and prompt history).** Three claims are
contradicted by the repository:

* **"Browser suite collection: 15 tests in 3 files"** — the actual collection is **16 tests in 3
  files** (4 + 7 + 5). (NB-1)
* **`backend/tests/e2e/README.md`** is listed as created (implementation report §10; prompt history
  C.1) — **the file does not exist**. (NB-2)
* **"[IV-N4] accepted residual; authorization verified (alternate-route DENY tests)"** — the only
  alternate-route DENY test covers `/api/v3/ops/items/{id}/submit-review`; the two IV-N4 routes are
  not tested at all. (NB-3)

Everything else in the implementation report that this verification could check matched the
repository.

## 33. Environmental limitations

**Executable here:** all Python suites; browser collection; the unauthenticated browser
route-protection spec in real Chromium; a read-only database/RLS catalogue inspection.

**Not executable, and why:**

1. **The dedicated isolated E2E environment does not exist.** No synthetic dataset, no creation
   script, no teardown, no personas. Nothing in the repository populates the `E2E_*` variables
   `tests/e2e/personas.ts` reads. This is the deliverable the contract §17 table classifies as
   **"P6-2F E2E environment + fixtures — must be created — class 7"** and that contract §12 and
   `PO-PHASE6-F-ENV-20260910` call **mandatory**.
2. **A live local Supabase stack is running** (`supabase_db_carbon_ledger` plus the local Supabase
   service set; Postgres on 54426, Kong on 54425), carrying the real CarbonTally schema with RLS
   enabled. It holds the **investor-demo / development dataset** (975 organisations, 917 consultant
   grants). It is **not** the P6-2F isolated synthetic environment, and the ratified rules
   (`PO-PHASE6-F-ENV-20260910`; contract §12; AGENTS.md §54-§55) forbid reseeding, truncating or
   repurposing it. The verifier therefore did **not** substitute it for the mandated environment and
   ran only read-only catalogue queries.
3. **The frontend (:3000) and backend (:8050) application servers are not running**, so no
   authenticated browser session could be established even if personas existed.
4. **Provisioning the environment is out of scope for this session** (read-only mandate: do not
   provision missing infrastructure; do not change the environment merely to make a test pass).
5. **Live RLS was not exercised** — it can only be exercised meaningfully inside the isolated
   synthetic environment.

**Classification (per the prompt §33).** Because the authoritative P6-2F requirements make the
dedicated isolated E2E environment **mandatory** (PO selection A; contract §12; contract §17 class 7;
prompt CP-F1) and make browser/RLS security acceptance part of the gate (contract §11.1, §11.2, §15;
`PO-PHASE6-F-ACC-20260910`), the missing environment is a **blocking acceptance gap**, not a
non-blocking implementation limitation and not merely an optional later run. It is simultaneously the
reason this verification cannot reach PASS: the mandatory evidence cannot be obtained here.

## 34. Findings

| ID | Severity | Component | Requirement violated | Evidence | Classification |
|---|---|---|---|---|---|
| **BLK-1** | Blocking | E2E environment (deliverable) | contract §12 (mandatory dedicated isolated E2E environment); contract §17 "P6-2F E2E environment + fixtures — must be created — class 7"; `PO-PHASE6-F-ENV-20260910` (selection A); prompt CP-F1; prompt §40 "isolated E2E environment operational" | No provisioning script, no environment config, no synthetic-identity creation and no teardown anywhere in the repository; `tests/e2e/personas.ts` reads `E2E_*` variables that nothing sets; the implementation report itself states the environment was "not provisionable in this session" (§11, §28.1) | **BLOCKING** |
| **BLK-2** | Blocking | Security acceptance | contract §11.1 (end-to-end, role-complete, security-focused), §11.2 (ALLOW **and** DENY), §15 ("RLS enforcement … at least one DENY-side test proving the negative case"), §12 (realistic Supabase Auth and RLS); `PO-PHASE6-F-ACC-20260910` ("E2E browser workflows"); prompt CP-F4/CP-F5 (**browser** ALLOW/DENY workflows); prompt §29 ("P6-2F must exercise the real security architecture") | 8 of 16 browser specs skip; the delivered ALLOW/DENY layer overrides `get_current_user` and `get_repositories` with in-memory fakes (no database, no RLS, no Supabase Auth); verifier result 7 passed / 8 skipped / 1 failed | **BLOCKING** |
| **BLK-3** | Blocking | Coverage | contract §11.1 ("Processing Entity workflows … PE-origin item processing; PE source-document boundary"); `PO-PHASE6-F-ACC-20260910` (acceptance must cover Processing Entity workflows); contract §12 ("at least two organisations, two firms and **two PEs** so isolation is provable"; cross-PE negative testing) | `seed_standard_scenario()` seeds **no processing entity**; the `pe_operator` persona is defined and never used; zero PE tests in `backend/tests/e2e/**`; no cross-PE DENY anywhere | **BLOCKING** |
| **NB-1** | Non-blocking | Documentation bookkeeping | accuracy | the implementation report and prompt history state "15 tests / 3 files"; `npx playwright test --list` reports **16 tests in 3 files** | **NON-BLOCKING** |
| **NB-2** | Non-blocking | Documentation bookkeeping | accuracy | `backend/tests/e2e/README.md` is claimed created (report §10; history C.1) but **does not exist** | **NON-BLOCKING** |
| **NB-3** | Non-blocking | Documentation accuracy / IV-N4 | contract §11.2 (alternate-route bypass); prompt §25 (verify IV-N4 authorization) | report §26 claims IV-N4 "authorization verified (alternate-route DENY tests)"; grep finds **no** test for `automatic-processing/jobs/{id}/review` or `consultants/clients/{id}/reactivate` | **NON-BLOCKING** |
| **NB-4** | Non-blocking | Test integrity | prompt §32 (no tests that never execute meaningful assertions) | `security-denies.spec.ts > consultant cannot reach the admin control plane` cannot fail: `/admin` is not a route (`grep -c 'path="/admin' frontend/src/App.js` = 0; catch-all `*` to `/`) | **NON-BLOCKING** |
| **NB-5** | Non-blocking | Test quality | prompt §32; contract §15 | `test_d7_mode_is_separate_from_processing_origin` accepts `origin is None` (vacuous); `test_d6_no_charge_on_denied_submission` asserts no credit/ledger state; several `in (403, 404)` matchers (IV-N7(b) class); no database-level idempotency test (IV-N7(d) still open) | **NON-BLOCKING** |
| **NB-6** | Non-blocking | Harness integration | contract §12 ("Existing harness (reuse, extend) … Harness outputs must distinguish PASS / FAIL / SKIPPED / BLOCKED / UNVERIFIED"); prompt CP-F0 ("Use the existing harness rather than replacing it unnecessarily") | the new E2E layer does not integrate with `qa_harness`; acceptance rests on raw pytest/Playwright output with no BLOCKED/UNVERIFIED discipline. `qa_harness` itself is untouched (no regression) | **NON-BLOCKING** |
| **NB-7** | Non-blocking | Browser reproducibility | prompt §10 / CP-F2 (browser suite reproducible) | running the full browser suite against the documented static-server recipe fails one spec (`unauthenticated API calls are rejected`) because the static server has no API proxy and answers 200 via SPA fallback | **NON-BLOCKING** |
| **NB-8** | Non-blocking | UI test coverage | prompt §32 (coverage; tests that can pass while a boundary is broken) | the P6-2F consultant UI deliverable (review/rework/submit controls and the three new `api.js` helpers) has **no executed test**: `api.test.js` unchanged since 2026-08-31 and does not reference `getConsultantItemWorkspace`, `consultantReviewItem` or `consultantSubmitItem`; no component test; all 4 browser specs skip | **NON-BLOCKING** |
| **NB-9** | Non-blocking | Test quality (inherited) | prompt §32 | the IV-N7(a) class persists in a new form: injected fields are not declared by the request model, so the "ignored" assertions are partly structural rather than behavioural | **NON-BLOCKING** |
| **NB-10** | Non-blocking | Documentation location | n/a | `CARBONTALLY_CP1_CLOSURE_REPORT.md` and `CARBONTALLY_P6_2E_PREFLIGHT_REPORT.md` live under `docs/cline/`, not `docs/architecture/` as the task's source list implies (pre-existing preflight gap G8) | **NON-BLOCKING** |
| **NB-11** | Non-blocking | Frontend regression evidence | prompt §34 (regression) | the frontend suite was not run by the implementation. This session ran it: 200/200 tests pass, but `src/App.test.js` cannot run (`Cannot find module 'react-router/dom'`) — a pre-existing environmental failure unrelated to P6-2F | **NON-BLOCKING** |

**No other defect was found.** In particular: no unexpected ALLOW in any executed test; no
cross-organisation or cross-firm leakage; no entitlement bypass; no provenance or processing-origin
corruption; no billing change; no new role, capability or permission; no migration; no RLS change.

## 35. Blocking findings

* **BLK-1** — the mandatory dedicated isolated E2E environment was not provisioned (class-7
  deliverable).
* **BLK-2** — the mandatory browser ALLOW/DENY and real-authentication/RLS security acceptance was not
  executed (the delivered ALLOW/DENY layer runs on in-memory dependency overrides).
* **BLK-3** — Processing-Entity acceptance coverage is absent (no PEs in the scenario, no cross-PE
  DENY, no PE workflow exercise).

These three are facets of one root cause (no isolated environment, therefore no browser/live-boundary
acceptance, therefore PE workflows never exercised). They are recorded separately because the
authoritative contract treats the environment, the security acceptance and the PE workflow coverage
as three distinct obligations.

## 36. Non-blocking findings

NB-1 to NB-11 (see §34). None of them prevents P6-2F acceptance on its own; all are recorded for the
PO's information and for the future acceptance run.

## 37. Accepted residuals

Carried forward from P6-2E, with no P6-2F regression observed:

| ID | Status after P6-2F |
|---|---|
| IV-N1 (event-2 internal recipients resolve `can_manage_staff`) | **PRESERVED, not modified** (no change was authorised) |
| IV-N2 (org-grant-scoped recipient breadth) | **PRESERVED** — observed and consistent with the ratified model; no narrower policy invented |
| IV-N3 (deactivated firm profile with a retained active grant) | **PRESERVED** — recipients remain inert; no security effect |
| IV-N4 (auto job-review and `reactivate` emit no D11 event) | **PRESERVED** — but the report's "authorization verified" claim is unsupported (NB-3) |
| IV-N5 (per-cycle idempotency collapse) | **PRESERVED** — no cycle discriminator, no schema change (correct) |
| IV-N6 (notification deep link) | **FIXED and VERIFIED** (§12) |
| IV-N7 (test-quality weaknesses) | **PARTIALLY addressed** — (a) and the weak matchers persist in new forms (NB-5, NB-9); (d) the database-level idempotency test is still absent |
| IV-N8 (report bookkeeping) | **RECURRED** in a new form (NB-1, NB-2) |
| IV-E1 (`-q` summary suppression) | **Not reproduced** with `--tb=line`; not a current limitation |
| IV-E2 (no live DB/RLS) | **NOT CLOSED** — BLK-2 |
| IV-E3 (no live browser E2E) | **PARTIALLY CLOSED** — the unauthenticated browser layer now executes in real Chromium; the authenticated layer does not |

## 38. Scope-creep assessment

**No scope creep found.** The P6-2F footprint (mtime-verified, §7) is limited to two frontend files,
one backend service file, the test/browser layer, and the two required documentation artefacts.

Specifically **not** done, as required:

* no migration, no schema change, no backfill;
* no RLS change (no RLS file touched);
* no billing change (no billing file touched; `PO-PHASE6-BILL-DEFER-20260910` intact);
* no new role, capability, permission or grant;
* no `CONSULTANT` processing origin (the vocabulary is still two-valued and the CHECK is intact);
* no consultant conversation kind (the vocabulary is still `{org, entity}`);
* no change to D11 recipient policy (D11-C1 preserved);
* no change to the D11 event set, keys or triggers;
* no PE to Consultant handoff (D4) work;
* no reopening of P6-2C, P6-2D or P6-2E;
* no `qa_harness` modification;
* no Phase 7 or Phase 8 work;
* no unrelated working-tree change absorbed; no `git reset`, `clean`, `rebase` or force-push;
* no commit, no push, no staging.

**Conversely, the gate is under-delivered rather than over-delivered**: the mandatory environment and
the browser/RLS/PE acceptance were not produced (BLK-1 to BLK-3).

## 39. Final verdict

> **`P6-2F INDEPENDENT VERIFICATION — ENVIRONMENTALLY BLOCKED`**

**Basis.**

The implemented code is sound and the regression surface is intact. Independently verified by
execution:

* full backend unit suite **1654 passed / 0 failed / exit 0**;
* P6-2E focused suite **27 passed / exit 0**;
* P6-2F application suite **39 passed / exit 0**;
* browser route protection **7 passed / exit 0** in real Chromium;
* **no** unexpected ALLOW, no cross-organisation or cross-firm leakage, no entitlement bypass, no
  provenance or processing-origin corruption, no billing/RLS/schema change, no scope creep.

The **IV-N6 deep-link defect is genuinely fixed**, the **consultant workspace route defect is
genuinely fixed**, **D6/D7/D8/D11/D11-C1 are preserved**, and the new application-level ALLOW/DENY
suite is honest, fail-closing and free of security mocks in the authorization code paths.

However, the gate's **mandatory acceptance evidence does not exist**:

* the dedicated isolated E2E environment (contract §12; contract §17 class 7;
  `PO-PHASE6-F-ENV-20260910`) was **not provisioned**;
* consequently the mandated **browser** ALLOW/DENY acceptance (contract §11.1, §11.2, §15;
  `PO-PHASE6-F-ACC-20260910`; prompt CP-F4/CP-F5) and any exercise of **real Supabase Auth / RLS**
  never occurred — 8 of 16 browser specs skip, and the delivered ALLOW/DENY layer runs with
  `get_current_user` and `get_repositories` replaced by in-memory fakes;
* **Processing-Entity workflow acceptance is absent entirely** (contract §11.1; §12 "two PEs";
  `PO-PHASE6-F-ACC-20260910`), with zero PE tests and an unused PE persona.

Because that environment is itself a mandatory P6-2F deliverable, the gate is simultaneously **not
implementation-complete**; and because the required environment is unavailable to this session, the
mandatory acceptance evidence **cannot be obtained here**. Neither `PASS` nor
`PASS WITH NON-BLOCKING FINDINGS` is available, and the gate may not be declared accepted.

**Next step (for the PO, not for this session).** Provision the dedicated isolated synthetic E2E
environment (two organisations, two firms, **two processing entities**, synthetic Supabase Auth
personas, resettable fixtures with verified teardown, no production or investor-demo data), execute
the authenticated browser ALLOW/DENY matrix plus the PE workflow and isolation cases against real
RLS, and then re-run independent verification on the resulting evidence. No remediation, no
environment provisioning and no implementation work was performed by this verification session.

---

*End of report. Independent verification stopped here. No production code, schema, RLS, test,
billing, role, capability or UI artefact was modified beyond this report and its companion
prompt-history record; no commit and no push was performed; Phase 7 and Phase 8 were not started.*
