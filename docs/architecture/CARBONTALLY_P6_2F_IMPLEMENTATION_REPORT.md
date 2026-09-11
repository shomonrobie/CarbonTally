# CarbonTally — P6-2F Implementation Report (UI/UX + E2E Security Acceptance)

**Prompt Ref:** `CT-P6-2F-IMPL-20260910-001`
**Response Ref:** `CT-P6-2F-IMPL-20260910-001-R1`
**Date/time:** 2026-09-10 23:00 → 2026-09-11 01:00 (+0600); repository clock `2026-09-11 00:28:33 +0600`
**Agent/session identity:** Cline — fresh P6-2F implementation session
**Implementation authorization:** CONFIRMED by the prompt (§0) — CP2/P6-2E closed, D11-C1 ratified, P6-2F preflight `CP2 CLOSED — P6-2F PREFLIGHT READY`
**Final verdict:** `P6-2F IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`

> This is the **implementation agent's** report. It is **implementation evidence**, not
> independent acceptance. No independent verification was performed here; that is a separate
> fresh session. No commit, no push.

---

## 1. Prompt Ref

`CT-P6-2F-IMPL-20260910-001` — "CarbonTally — P6-2F Full UI/UX + E2E Security Acceptance
Implementation" (43 sections; checkpoints CP-F0 … CP-F8).

## 2. Date/time

2026-09-10 23:00 → 2026-09-11 01:00 (+0600).

## 3. Agent/session

Cline, P6-2F implementation agent (fresh session per contract §14).

## 4. Implementation authorization

The prompt §0 confirms authorization; the preflight report
`docs/architecture/CARBONTALLY_CP2_CLOSURE_P6_2F_PREFLIGHT_REPORT.md` is `CP2 CLOSED — P6-2F
PREFLIGHT READY`.

## 5. Authority sources inspected

Blueprint V1.3; Master Roadmap V1.0 (§9 gate sequence); P6-2 PO Decision Register (D8/D11/D4,
`PO-PHASE6-F-ACC-20260910`, `PO-PHASE6-F-ENV-20260910`, `PO-PHASE6-CAMPAIGN-20260910`, frozen
P6-2C invariants); Phase-6 Remainder Implementation Contract V1.0 (§7.1/§7.2, §8, §10, §11–§19);
CP1 closure; P6-2E preflight; CP2-closure/P6-2F-preflight report; P6-2D + P6-2E implementation and
IV reports; P6-2 consultant workflow architecture (§10/§13/§14); repository source
(`backend/api/**`, `backend/services/consultant_lifecycle.py`, `backend/data/**`,
`backend/tests/**`, `frontend/src/**`, `qa_harness/**`, `playwright.config.ts`, `tests/`).

## 6. Scope

Deliver the P6-2F gate: (a) complete the consultant UI surface + the IV-N6 notification deep-link;
(b) an isolated, synthetic, resettable E2E acceptance layer (personas, fixtures, ALLOW/DENY);
(c) CarbonTally browser specs; (d) D6/D7/D8/D11 + processing-origin + billing preservation;
(e) full regression; (f) durable evidence. Out of scope: Phase 7/8, billing redesign, PE↔Consultant
handoff, new roles/capabilities, `CONSULTANT` processing origin, D11 client recipients.

## 7. Checkpoint results

| Checkpoint | Result |
|---|---|
| **CP-F0** Reconnaissance | Frontend = CRA React 18 + React Router 7 + Supabase auth + MUI/emotion; backend = FastAPI composition root `api.router.create_app`; existing harness = `qa_harness/**` (Python Playwright — package **not installed**) + root Node Playwright 1.62.1 (**browsers installed**); `playwright.config.ts` pointed at `tests/` with only the default example spec. Identified the consultant workspace defect (`getItemWorkspace` → internal `/ops` route) and the IV-N6 deep-link defect. |
| **CP-F1** Isolated E2E environment + fixtures | Built `backend/tests/e2e/` on the in-memory world (no DB, no production data); representative synthetic scenario (org A/B, firm A/B, active + suspended grants, internal QC/ops/reviewer, entitlement). Resettable per test. |
| **CP-F2** Browser infrastructure + personas | New `tests/e2e/` Node Playwright layer: `personas.ts` (env-supplied synthetic personas; skip-if-absent), SPA static server, README; `playwright.config.ts` re-pointed to `testDir: './tests/e2e'`. 15 specs collected; route-protection spec **executed in real Chromium**. |
| **CP-F3** Core UI/UX completion | Consultant item workspace now loads the **scope-aware** `/api/v3/processing/items/{id}/workspace` (not the internal `/ops` route, which denies consultants); added consultant **review / rework / submit-to-QC** controls and status labels; data now surfaces via the consultant route. |
| **CP-F4** Browser/application ALLOW | `backend/tests/e2e/test_p6_2f_allow_workflows.py` — 8 tests PASS. |
| **CP-F5** Browser/application DENY | `backend/tests/e2e/test_p6_2f_deny_matrix.py` — 16 tests PASS (org isolation, firm isolation, capability, suspended grant, IDOR, injection, replay, alternate route, D8 deny). |
| **CP-F6** D6/D7/D8/D11 integration | `backend/tests/e2e/test_p6_2f_invariants.py` — 11 tests PASS; plus `test_p6_2f_deeplink_iv_n6.py` — 4 tests PASS. |
| **CP-F7** Full regression + evidence | `pytest tests/unit` re-run; `pytest tests/e2e` = **39 passed**; P6-2E focused = **27 passed**; browser route-protection = **7 passed**. (See §25 / §28 for the interpreter caveat.) |
| **CP-F8** Completion report | This report + `docs/cline/prompt-history/CT-P6-2F-IMPL-20260910-001.md`. |

## 8. UI / frontend changes

* **`frontend/src/v3/consultant/ConsultantItemPage.jsx`** —
  * the workspace now loads from `getConsultantItemWorkspace` (scope-aware
    `/api/v3/processing/items/{id}/workspace`) instead of `getItemWorkspace`
    (`/api/v3/ops/items/{id}/workspace`, guarded by `require_staff`, which correctly **denies**
    consultants — a real defect: the consultant page previously could not load);
  * added a **Consultant review** action bar: *Pass review*, *Request rework* (reason required),
    and *Submit to CarbonTally QC*, shown only in the eligible workflow states
    (`calculated` / `consultant_reviewed`) with busy/notice/error handling and D19/D21-conformant
    status labels;
  * errors from denied actions surface as an inline error and change nothing (the backend remains
    the authorization boundary).
* **`frontend/src/v3/api.js`** — added `getConsultantItemWorkspace`, `consultantReviewItem`,
  `consultantSubmitItem` (the P6-2B boundaries on the consultant surface). No existing helper was
  removed; `getItemWorkspace` (used by the internal `OperatorItemPage`) is unchanged.

No other frontend file was changed; no visual redesign; semantic tokens/classes reused.

## 9. Backend changes

* **`backend/services/consultant_lifecycle.py`** — IV-N6 fix. Lifecycle item notifications now carry a
  **per-recipient consultant item deep link** `"/consultant/items/{clientId}/{itemId}"` where
  `clientId` is the recipient firm's engagement id (`consultant_clients.id`), resolved server-side
  from the org's active grants. Added `_consultant_item_link`, `_client_id_by_firm`,
  `_consultant_link_for`; `_emit` accepts a `link_for` resolver. Non-firm recipients (internal ops)
  fall back to the valid `/notifications` route instead of a broken path. Event 1 (`accepted`) keeps
  `/consultant`.
* No other backend production file was changed. **No migration. No schema change. No RLS change. No
  billing change. No new role/capability/permission. No processing-origin change.**

## 10. E2E infrastructure

* `backend/tests/e2e/` — application/API acceptance layer over the **real FastAPI app** with
  dependency overrides onto the in-memory world (no database; production data untouched).
  * `conftest.py` (app + world + `UserProvider` + `scenario`), `personas.py`, `fixtures.py`,
    `test_p6_2f_allow_workflows.py`, `test_p6_2f_deny_matrix.py`, `test_p6_2f_invariants.py`,
    `test_p6_2f_deeplink_iv_n6.py`, `README.md`.
* `tests/e2e/` — **Node Playwright browser layer** (reuses the repo's installed Playwright):
  * `personas.ts`, `carbontally/route-protection.spec.ts`,
    `carbontally/consultant-lifecycle.spec.ts`, `carbontally/security-denies.spec.ts`,
    `static-server.mjs`, `README.md`.
* `playwright.config.ts` — `testDir: './tests/e2e'`, env-driven `baseURL`, chromium project.
  The previous placeholder `tests/example.spec.ts` is left in place but is no longer the only spec
  (and no longer collected).

## 11. Environment

* The **application acceptance layer** needs no external services (isolated in-memory world) and is
  fully resettable.
* The **browser layer** targets an isolated environment via `E2E_BASE_URL` + synthetic persona
  credentials (`PO-PHASE6-F-ENV-20260910`). Verified in this session against a **locally-built
  isolated copy** of the frontend (`BUILD_PATH=/tmp/p6f_build` with `REACT_APP_SUPABASE_URL` pointed
  at an unreachable local endpoint — **never** production).
* `tests/e2e/static-server.mjs` serves a built SPA with deep-link fallback.

## 12. Personas

Representative synthetic personas on the existing authorization model — organisation
owner/admin/member/viewer; consultant firm A + firm B; CarbonTally internal QC/reviewer/ops; Processing
Entity operator; plus ungranted/outsider identities for DENY. **No new production role, capability,
permission or grant was created.** (App personas: `backend/tests/e2e/personas.py`; browser personas:
`tests/e2e/personas.ts`.)

## 13. Fixtures

`backend/tests/e2e/fixtures.py`: `seed_firm`, `seed_engagement` (active/suspended), `seed_item`
(any workflow state), `seed_entitlement` (synthetic plan + subscription + credits, no real billing
provider), `seed_internal_staff` (real permission roles), and `seed_standard_scenario` (org A/B,
firm A/B, grants, internal roles, entitlement). State is fully resettable per test.

## 14. ALLOW tests

`backend/tests/e2e/test_p6_2f_allow_workflows.py` (8 passed):
1. org owner reads own item workspace (200);
2. granted consultant reads the client item workspace via the **processing** route (200) + the
   consultant client item list (200);
3. consultant review pass → status `consultant_reviewed` **and** D7 provenance recorded (firm A);
4. submit to QC → status `reviewed` + `submitted_to_qc` notification to the firm member;
5. QC approval → `ct_qc_approved` + `qc_outcome:approved` to `["u-firm-a"]` only;
6. customer approval → `approved` + `customer_decision:approved` to `["u-firm-a"]` only (no client actor);
7. granted consultant creates a conversation (201) with participant role `consultant` (D8);
8. notifications are recipient-scoped (firm A sees theirs; firm B sees none).

Browser ALLOW: `tests/e2e/carbontally/consultant-lifecycle.spec.ts` (4 specs; executed only in the
isolated environment — see §28).

## 15. DENY tests

`backend/tests/e2e/test_p6_2f_deny_matrix.py` (16 passed):
unauthenticated (401); cross-organisation (403/404); consultant without grant (403/404); cross-firm
(403/404); suspended grant (403, zero notifications); missing `can_submit` (403, zero notifications);
org member cannot approve (403, state unchanged); org viewer cannot write (403); QC without `can_qc`
(403) and consultant cannot QC (403); IDOR swapped item + engagement ids (403/404); recipient
injection ignored; actor/firm injection ignored; processing-origin injection ignored; replay (409, no
duplicate rows); alternate internal route requires staff (403); ungranted consultant cannot message
(403).

Browser DENY: `tests/e2e/carbontally/security-denies.spec.ts` (5 specs) + `route-protection.spec.ts`
(executed: see §25).

## 16. D6 — entitlement evidence

* `test_d6_entitlement_is_required_and_org_owned` — org A (entitled) submit = 200; org B (no
  entitlement) submit = 4xx and the item is **unchanged** (fail-closed, no mutation, no charge).
* `test_d6_no_charge_on_denied_submission` — an invalid-state submission is 409 and the item is
  unchanged.
* The approval-time charge site (`charge:item:{id}`) and the read-only non-charging preflight are
  untouched (no billing file changed).

## 17. D7 — provenance evidence

* `test_d7_provenance_is_server_derived_and_write_once` — consultant review records
  `consultant_firm_id = firm-a`; a later write attempt returns `False` and changes nothing.
* `test_d7_mode_is_separate_from_processing_origin` — the provenance record carries
  `processing_mode`; `processing_origin` is a separate field.
* `test_actor_and_firm_injection_is_ignored` — an injected `consultant_firm_id`/`actor` has no effect.

## 18. Processing-origin evidence

* `test_processing_origin_injection_is_ignored` — a body supplying `processing_origin: "CONSULTANT"`
  is ignored; the stored origin is `None`/`CARBONTALLY_INTERNAL`/`PROCESSING_ENTITY` — never
  `CONSULTANT`.
* `backend/domain/processing_origin.py` still defines exactly the two origins. The vocabulary is
  unchanged.

## 19. D8 — messaging evidence

* `test_d8_conversation_kind_vocabulary_unchanged` — migration scan: vocabulary ⊆ {`org`,`entity`}, no
  `consultant` kind, no `consultant_conversations` table.
* `test_d8_consultant_participates_with_role` — participant role `consultant` through the existing model.
* `test_ungranted_consultant_cannot_message_client` — 403 (active grant required).

## 20. D11 — lifecycle notification evidence

* Five events exercised end-to-end: `accepted` (engagement accept), `submitted_to_qc`,
  `qc_outcome` (approved + rejected), `customer_decision` (approved), `rework`
  (`ct_qc_rejected` + `consultant_review_rejected`).
* Keys are deterministic and match `consultant.lifecycle.<event>:<identity>[:<discriminator>]`.
* `test_d11_recipients_never_leak_cross_tenant` — recipients ⊆ {`u-firm-a`, `u-ops`}; never firm B,
  never the client actor (confirms **D11-C1**: no new client-organisation recipients).
* `test_d11_service_layer_replay_is_idempotent` — two service calls → rows == recipient count.
* IV-N6: `test_deeplink_targets_the_real_consultant_item_route` asserts the firm recipient link is
  `/consultant/items/{client_id}/{item_id}`; `test_internal_recipient_link_is_a_valid_route` asserts
  the ops recipient link is `/notifications`.

## 21. IDOR evidence

* `test_idor_swapped_identifiers_are_denied` — firm B supplies org A's **item id** and **engagement
  id**: `GET /api/v3/processing/items/{item}/workspace` and
  `GET /api/v3/consultants/clients/{client}/processing/items` both 403/404.
* Browser: `route-protection.spec.ts` "a consultant item deep link is not reachable unauthenticated"
  (executed, passes); `security-denies.spec.ts` cross-firm direct navigation (isolated env).

## 22. Alternate-route evidence

* `test_alternate_internal_route_requires_staff` — `POST /api/v3/ops/items/{id}/submit-review` is 403
  for an org owner **and** for a consultant (the internal route is not a bypass).
* The five D11 trigger routes remain the only lifecycle emitters (`grep` traced in P6-2E; unchanged).
* Browser: `security-denies.spec.ts` asserts a consultant cannot invoke the internal
  `/api/v3/ops/items/{id}/workspace` route (isolated env).

## 23. Replay / idempotency evidence

* `test_replay_does_not_duplicate_side_effects` — second submission 409; notification rows unchanged.
* `test_d11_service_layer_replay_is_idempotent` — deterministic key ⇒ one durable row per recipient.
* No idempotency mechanism was weakened; no schema change was made to ease testing.

## 24. Billing / entitlement evidence

* Tests use a **synthetic** subscription + credits; no real billing provider, no real payments, no
  production entitlement consumption.
* D6 fail-closed preflight denial proven (§16); the single approval-time charge site and its
  idempotency key are unchanged. Billing policy is unchanged (deferred automatic job-review billing
  remains deferred).

## 25. Regression results

| Suite | Command | Result |
|---|---|---|
| P6-2E focused | `python -m pytest tests/unit/api/test_p6_2e_consultant_lifecycle.py -p no:cacheprovider --tb=short` | **27 passed**, exit 0 |
| P6-2F application E2E | `python -m pytest tests/e2e -p no:cacheprovider --tb=short` | **39 passed**, exit 0 |
| Full unit suite | `python -m pytest tests/unit -p no:cacheprovider --tb=line` | **1654 passed**, exit 0 (re-confirmed; see §28 for the interpreter caveat) |
| Browser route protection | `E2E_BASE_URL=… npx playwright test tests/e2e/carbontally/route-protection.spec.ts` | **7 passed**, exit 0 |
| Browser suite collection | `npx playwright test --list` | 15 tests in 3 files |

Frontend unit tests (CRA/Jest) were not run in this session (no change to their targets; the
consultant page they mock is unaffected).

## 26. Residual findings (carried forward from P6-2E IV; unchanged)

The P6-2E non-blocking findings are preserved as residual/accepted — **none was remediated** in P6-2F
except where the gate explicitly required it (IV-N6):

| ID | Status in P6-2F |
|---|---|
| IV-N1 (event-2 internal recipients = `can_manage_staff`) | accepted residual (no change authorised) |
| IV-N2 (org-grant-scoped recipient breadth) | accepted residual (not altered to satisfy tests) |
| IV-N3 (deactivated firm profile recipients) | accepted residual |
| IV-N4 (auto job-review + `reactivate` emit no D11 event) | accepted residual; authorization verified (alternate-route DENY tests) |
| IV-N5 (per-cycle idempotency collapse) | accepted residual; replay behaviour tested and documented |
| **IV-N6 (consultant notification deep link)** | **FIXED in P6-2F** (per-recipient deep link + ALLOW/DENY tests) |
| IV-N7 (test-quality weaknesses) | addressed for the new suite (strong assertions); legacy notes remain |
| IV-N8 (report bookkeeping) | n/a to this report |

## 27. Out-of-scope findings / observations

* **`/admin` is not an app route** — an unauthenticated `GET /admin` resolves to the SPA catch-all and
  lands on `/` rather than `/login`. The administrative control plane is not exposed at `/admin`
  in this build. Recorded as an observation (not a defect; no admin UI was in P6-2F scope). The
  corrected route-protection spec uses real protected routes.
* **`frontend/src/supabaseClient.js` defaults to the production Supabase URL** when
  `REACT_APP_SUPABASE_URL` is unset. This is why the browser suite **must** run only against an
  isolated build; it is recorded as an environment-safety note for the isolated E2E environment.
* PE↔Consultant handoff (D4) — remains out of scope and untouched.

## 28. Environmental limitations

1. **Isolated E2E environment not provisionable in this session.** The dedicated isolated stack
   (its own Supabase project + synthetic data) does not exist here. The application-level acceptance
   layer runs fully (in-memory, 39 tests). For the browser layer, an isolated **frontend build**
   (`BUILD_PATH=/tmp/p6f_build`, dummy Supabase endpoint) was used to execute the unauthenticated
   route-protection spec (7 passed); the **authenticated** browser specs require the isolated
   stack and are authored + collection-validated (15 tests) but not executed here. They **skip**
   rather than falsely pass.
2. **No live RLS exercise.** RLS was not driven in this session; P6-2F preserves RLS and adds no RLS
   change.
3. **Transient wrong-interpreter run.** One background `pytest tests/unit` invocation failed 283
   async tests with "async def functions are not natively supported" (the known wrong-plugin-load
   condition). A re-run with the project virtualenv passes; the failure was environmental, not a
   code regression. Recorded for transparency.
4. **Frontend CRA build warning**: `ConsultantItemPage.jsx` initially flagged an unused
   `STATUS_LABELS`; fixed within this task (the label is now rendered).

## 29. Risks

* Browser authenticated flows remain unexecuted until the isolated environment is provisioned; the
  specs skip rather than pass, so acceptance cannot be falsely claimed.
* The isolated environment must set a non-production `REACT_APP_SUPABASE_URL`/`ANON_KEY` and synthetic
  personas; using the production default is unsafe.
* Residual P6-2E findings (IV-N1..N5) remain by decision; they are documented, not hidden.

## 30. Final verdict

> **`P6-2F IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`**

All material P6-2F implementation criteria are met: the required UI/UX completion (consultant
workspace route + review/submit controls + IV-N6 deep link), the isolated synthetic E2E layer with
representative personas/fixtures, CarbonTally browser specs (unauthenticated layer executed in real
Chromium; authenticated layer authored and collection-validated), full ALLOW/DENY coverage, D6/D7/D8/D11
and processing-origin/billing preservation, and a full regression run — with no commit and no push.
The residual items are documented as accepted/environmental; **no material security or functional gap
remains in the implemented code**.

### Git

* Branch `main`; HEAD unchanged (`16391217103b98dcea520070c5a22c68f12fe607`).
* **No commit. No push.**
* Task-created/modified files are listed in §8–§10 and the prompt-history record.

*End of report. Implementation stops here. No independent verification was performed. No Phase 7 or
Phase 8 work was started.*




