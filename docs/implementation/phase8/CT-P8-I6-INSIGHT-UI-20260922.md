# CarbonTally Insight I6 — UI Implementation Report

| Item | Value |
| --- | --- |
| Stage | **I6 — UI** (CarbonTally Insight) |
| Authorization | PO I6 UI Implementation Authorization (2026-09-22), issued against `docs/architecture/CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` |
| I5 baseline | `I5 CLOSED — VERIFIED PASS` (`docs/architecture/CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md`) |
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| Starting HEAD | `4887c668ac618cff5974bc510b355a6a6c84e149` (`4887c66`) |
| Implementation revision | `09e2315141a4df6fc90e78f70d53d74cbd0c9d3a` (`09e2315`) — 18 files changed, +3,678 / −0 |
| Implementation status | **I6 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION** |
| Independent verification | **NOT PERFORMED** — Cline does not verify, accept or close I6 |

---

## 1. PO authorization source

The implementation was carried out under, and strictly bounded by:

* `docs/architecture/CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` — §5 (I6-1 … I6-8, the ratified I6 decisions), §3.1–§3.7 (global PO decisions) and §14 (explicit non-authorizations);
* `docs/architecture/CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md` — I5 `CLOSED — VERIFIED PASS`, and the O-1 decision (the 20,000-character context budget is a default, not an immutable ceiling);
* the PO I6 authorization of 2026-09-22 (the task authorization this report answers);
* `docs/implementation/phase8/CT-P8-I5-I8-PREAUTHORIZATION-READINESS-AUDIT-20260921.md` §9–§11 — `I6 — READY WITH PO DECISIONS`, **no backend contract gap found**.

No PO decision was reinterpreted, expanded or renegotiated. No business policy was invented; no state requiring a PO decision was resolved by assumption.

## 2. Repository, branch and starting HEAD

| Item | Value |
| --- | --- |
| Working directory | `/home/shomonrobie/ct_93d5cdd` (the authoritative repository named in the authorization) |
| Branch | `p8-release-reconciled` |
| Starting HEAD | `4887c668ac618cff5974bc510b355a6a6c84e149` |
| Starting working tree | clean (`git status --porcelain` empty) |
| Push remote | `github` → `https://github.com/shomonrobie/CarbonTally.git` (push target `github/p8-release-reconciled`) |
| Other checkouts | **not touched** (`/home/shomonrobie/carbon_tally` and all other checkouts were read-only and were not modified) |

## 3. Exact scope implemented

Implemented (and nothing else):

1. an authenticated **Insight workspace route** `/insight` inside the existing customer workspace (PO I6-1/I6-2);
2. a **creator-private conversation list** (loading / empty / error / selection) (I6-3);
3. a **conversation view**: message history, answer state per interaction, deterministic tool evidence and provenance references (I6-3/I6-4);
4. **start and continue** a conversation (title-based creation + a composer that runs an I4 interaction);
5. **evidence/reference presentation** as locators, with resolution always going through the backend and a non-disclosing state for every failure mode (I6-4);
6. the **complete fourteen-state I4 `AnswerStatus` vocabulary**, `no_data` never rendered as `zero` (I6-5);
7. **provider-unavailable** behaviour: deterministic result retained, gap named, nothing fabricated (I6-6);
8. explicit **empty / loading / no-data / clarification / unauthorized / provider-unavailable / general-error** states (I6-7);
9. `replayed=true` as an informational lifecycle fact (I6-8);
10. responsive authenticated workspace, keyboard access, accessible labels, focus management (I6 acceptance);
11. five automated test suites covering the major UI states.

## 4. Frontend architecture inspected before changing anything

| Area | Evidence inspected |
| --- | --- |
| Routing | `frontend/src/App.js` — `BrowserRouter` + `Routes`, `ProtectedRoute`, `RoleRoute`, per-workspace `V3Layout` wrapping |
| Authentication / guards | `frontend/src/v3/components/RoleRoute.jsx` (server-authoritative `/api/v3/me/context`, fail-closed), `frontend/src/App.js` `ProtectedRoute` |
| Application shell | `frontend/src/v3/components/V3Layout.jsx` (D18 nav model, D20 tray drawer) |
| API client | `frontend/src/v3/api.js` (`v3Fetch`, request timeout, error shaping, `resolveV3Organization`) |
| Design system | `frontend/src/v3/tokens.css`, `frontend/src/v3/v3.css`, `frontend/src/v3/components/ui/*` (`Button`, `Badge`, `Alert`, `Icon`, `StateViews`, `Card`, `hooks.js`) |
| Provenance precedent | `frontend/src/v3/components/EvidenceTrail.jsx`, `EvidenceRecordPanel.jsx` |
| Page precedent | `frontend/src/v3/customer/MessagingPage.jsx` (list + thread + composer) |
| Tests | `frontend/src/v3/__tests__/*` (RTL + Jest + `@testing-library/user-event`), `frontend/src/setupTests.js`, the `jest.mock('../api')` convention |
| Public surface (deliberately untouched) | `frontend/src/public/assistant/AssistantWidget.jsx`, `PUBLIC_ROUTE_PREFIXES` in `App.js` |

No backend file was modified. The backend was inspected **read-only** in order to consume its contracts (`backend/api/v3_insight.py`, `backend/api/v3_insight_interactions.py`, `backend/api/v3_insight_tools.py`, `backend/api/insight_authz.py`, `backend/domain/insight_interaction.py`, `backend/domain/insight_tool.py`, `backend/services/insight_interactions.py`, `backend/services/insight_tools.py`).

## 5. Routes added / changed

**Added** (`frontend/src/App.js`):

```jsx
<Route path="/insight" element={
  <ProtectedRoute>
    <RoleRoute requireOrg>
      <V3Layout>
        <InsightPage />
      </V3Layout>
    </RoleRoute>
  </ProtectedRoute>
} />
```

* It reuses the existing `ProtectedRoute` (Supabase session) and the existing `RoleRoute requireOrg` guard exactly like `/home`, `/messaging`, `/reports` and the rest of the customer workspace. **No new authentication mechanism** was introduced.
* The route is deliberately **not** added to `PUBLIC_ROUTE_PREFIXES`, so the public FAQ assistant is never rendered on it.
* No existing route was changed, removed or reordered.

**Navigation** (`frontend/src/v3/components/V3Layout.jsx`): one entry added to the existing `CUSTOMER_LINKS` array — `{ to: '/insight', label: 'Insight', icon: 'insight' }` — plus one icon name (`insight`) in the existing single D21 icon vocabulary (`frontend/src/v3/components/ui/Icon.jsx`). This is an addition inside the ratified D18 customer nav model, not a navigation redesign: no other link, structure, breakpoint or shell behaviour was altered.

**Consultant / staff / PE entry points were deliberately not added**: PO I6-1 places Insight in the authenticated **customer** workspace. Extending the UI entry point to the consultant or staff shells would be a new PO decision, not an I6 implementation choice (see §17 and §18).

## 6. Components added / changed

All new files live under `frontend/src/v3/insight/` — the workspace package, following the existing `v3/<workspace>/` layout convention (`customer/`, `consultant/`, `ops/`, `pe/`, `reports/`, `admin/`).

| File | Lines | Purpose |
| --- | --- | --- |
| `insight/InsightPage.jsx` | 494 | The workspace: conversation list, conversation view, composer, start/continue, focus management |
| `insight/InsightInteraction.jsx` | 197 | One interaction: answer state, tool-call evidence, references, lazy persisted-detail read |
| `insight/InsightAnswerState.jsx` | 91 | The answer-state block (label, summary, guidance, narration, replay/lifecycle) |
| `insight/InsightReferences.jsx` | 153 | Reference locators + re-authorized resolution + non-disclosing states |
| `insight/answerStates.js` | 257 | The I4 answer vocabulary, narration and replay presentation (pure) |
| `insight/references.js` | 188 | Reference kinds, the ratified identifier→tool mapping, non-disclosing copy, evidence projection (pure) |
| `insight/format.js` | 17 | Timestamp / conversation-title display helpers |
| `insight/insight.css` | 484 | Workspace presentation on the D21 tokens, with the D20 responsive breakpoints |

Modified files (**111 inserted lines, 0 deleted lines** — the change is purely additive):

| File | Change |
| --- | --- |
| `frontend/src/App.js` | `InsightPage` import + the `/insight` route |
| `frontend/src/v3/api.js` | the Insight API section (§7) |
| `frontend/src/v3/components/V3Layout.jsx` | one `CUSTOMER_LINKS` entry |
| `frontend/src/v3/components/ui/Icon.jsx` | one icon-name mapping |

No existing component was refactored, no shared primitive was changed, and no legacy component was removed. `EvidenceTrail`/`EvidenceRecordPanel` were **not** reused for Insight evidence: they render the D33 extraction→calculation chain, which is a different provenance shape from I3 reference locators.

## 7. API contracts consumed

**No API was created.** Every call targets an existing, closed contract, and the client functions were added to the **existing** `frontend/src/v3/api.js` (no parallel client, no new transport, no new authentication):

| Client function | Backend contract | Authority |
| --- | --- | --- |
| `listInsightConversations(org)` | `GET /api/v3/insight/conversations?organization_id&limit&offset` | I1, creator-private |
| `createInsightConversation(org, title)` | `POST /api/v3/insight/conversations` | I1 |
| `listInsightMessages(org, conversationId)` | `GET /api/v3/insight/conversations/{id}/messages?organization_id` | I1 |
| `runInsightInteraction({...})` | `POST /api/v3/insight/interactions` (`organization_id`, `conversation_id`, `question`, `idempotency_key`, `narration`) | I4 |
| `listInsightInteractions(org, {conversationId})` | `GET /api/v3/insight/interactions?organization_id&conversation_id` | I4 |
| `getInsightInteraction(org, interactionId)` | `GET /api/v3/insight/interactions/{id}?organization_id` | I4 |
| `invokeInsightTool(org, tool, input)` | `POST /api/v3/insight/tools/invoke` | I3 (ratified read-only tool surface) |

Consumed response fields (read-only, exactly as the backend returns them): `conversations[].{id,title,created_at,updated_at}`; `messages[].{id,role,content,created_at}`; interaction `answer_status`, `narration_state`, `narration_text`, `lifecycle`, `intent`, `tool_calls[]`, `references[]`, `replayed`, `tool_call_count`, `reference_count`; tool result `{tool,status,data,references,reason}`.

**No backend change was required or made**, exactly as the pre-authorization readiness audit predicted ("no backend contract gap found").

The submit sends `narration: 'optional'` (the backend default, so an unconfigured provider yields a deterministic answer rather than a failure) and a bounded client-generated `idempotency_key` so a retried submit cannot record a second interaction. The UI never displays the key, and the replay **decision** belongs to the backend (`replayed`).

### The one contract boundary found (reported, not improvised)

`evidence_line_item` is a ratified reference **kind** (I3 `REFERENCE_KINDS`) but **no ratified by-identifier lookup accepts an evidence-line-item id**: `report_lookup` takes `report_id`; `report_version_lookup` takes `version_id` or `report_id`+`version_number`; `report_evidence_lookup` takes `report_version_id`; `calculation_snapshot_lookup` takes `snapshot_id`. Adding one would mean a **new tool** — a PO decision (PO §3.5, §14).

The UI therefore renders the `evidence_line_item` locator as provenance and shows the non-disclosing "can't be opened from Insight" state, rather than inventing an identifier route. `report`, `report_version` and `calculation_snapshot` **do** resolve, through the existing ratified tools. Recorded for the PO in §18; not a blocker, because PO I6-4 explicitly provides for the "resolution is unavailable" case.

## 8. Authentication / authorization behaviour

* **Authentication**: the existing Supabase session and the existing `ProtectedRoute` — unchanged, not duplicated.
* **Route guard**: the existing `RoleRoute requireOrg` (server-authoritative `/api/v3/me/context`, fail-closed on resolution failure, no silent redirect). Verified by test: an org member is admitted; consultant, PE staff, internal staff and org-less users are redirected to their own workspace; a failed context resolution shows a controlled error and admits nobody.
* **No client-side authorization**: the UI never decides access. It always supplies the caller's own `organization_id` and re-reads through the backend; the I2 boundary (`require_insight_user` + `authorize_insight_scope` + `conversation_is_visible`) remains the only authorization authority. Advisory `role` checks from AGENTS.md §44 are deliberately not used: the guard is UX navigation only, and every read/write is enforced server-side.
* **Creator privacy**: the conversation list is whatever the backend returns for the caller (`created_by` filtered server-side). The UI holds no "shared/team" concept, renders no cross-creator control, and never caches an authorization decision — re-opening a reference or an interaction always issues a fresh authorized request.
* **Non-disclosure**: a foreign conversation (404) or a foreign/absent reference (`no_data` / `not_authorized`) produces the same non-disclosing state. A failing ask shows one message that matches neither "it exists" nor "it does not".

## 9. Conversation UX

| Requirement (I6-3) | Implementation |
| --- | --- |
| Creator-private conversation list | `aside` panel: the backend's list, `aria-current="true"` on the open one, empty/loading/error states, retry |
| Start a conversation | labelled topic field + "New"; `POST /conversations`, list refreshed, new conversation opened |
| Continue a conversation | open a conversation, then ask — `POST /interactions` records the question and the answer in that conversation; the composer clears for the next turn |
| Current message history | ordered transcript with speaker labels ("You asked" / "CarbonTally"), timestamps, and an explicit empty state |
| Answer states | per-interaction answer block (§10) with a "View answer details" toggle |
| No shared workspace | no sharing, assignment, mention, export or team affordance exists in the UI |

Deliberate UX decisions inside the granted scope:

* the persisted-interaction detail is fetched **lazily** on toggle, so history is only read when the user asks for it;
* a fresh answer arrives with the backend's own response and is therefore shown without a duplicate read (the row is expanded automatically once);
* **background refreshes never blank working content**: the context effect does not re-run on a data refresh, and the list/thread/answer panels keep rendering their existing content while a refresh is in flight (the loading indicators appear only where there is nothing to show). This was a real defect found by the test suite during implementation and fixed rather than worked around.

## 10. Answer-state handling

`insight/answerStates.js` holds the complete I4 vocabulary as data (label, tone, icon, summary, guidance), plus narration, lifecycle and replay presentation. Tones are the existing D21 badge tones; no new visual system.

| State | Presented as |
| --- | --- |
| `success` | "Answered" |
| `zero` | "Answered — result is zero" (+ "a real calculation from records that were found") |
| `no_data` | "No data found" (+ "not the same as a result of 0: nothing was found to calculate from") |
| `not_authorized` | "Not available" — non-disclosing |
| `insufficient_data` | "Not enough data" |
| `needs_clarification` | "More detail needed" (+ include a reference) |
| `tool_failure` | "Lookup failed" |
| `provider_unavailable` | "Summary unavailable" (+ deterministic result unaffected) |
| `partial` | "Partial answer" |
| `rate_limited` | "Too many requests" |
| `refused` | "Not answered" |
| `ungrounded` | "Not shown — unverified wording" |
| `invalid_input` | "Couldn't process that question" |
| `error` | "Something went wrong" |

* **`no_data` is never rendered as `zero`.** Two independent guards: `answerIsZero(status)` is true only for `zero`, and the rendered block exposes `data-answer-zero="true|false"`. Tests assert this for all fourteen states, both at the component boundary and through the whole workspace. `no_data` and `zero` also differ in tone and icon, not only in wording.
* Unknown/future states render a neutral "not recognised" presentation and are **not** shown as zero or as an answer.
* No state is invented, renamed or merged, and no backend semantics are altered. States the current orchestration does not reach in production are still implemented and tested (PO I6-5).
* The I3 `ToolStatus` vocabulary used for **tool-call evidence** is kept strictly separate from the I4 answer vocabulary (PO Q3) — two different mappings, never merged.

## 11. Evidence / reference behaviour

* References are displayed as **provenance locators**: kind label + short id, with the full id in the element's `title`, and an explicit statement that "they are locators, not access: CarbonTally authorizes each one again whenever it is opened".
* Opening a reference (`report`, `report_version`, `calculation_snapshot`) calls the **ratified I3 read-only tool surface** (I3 §8, PO §3.3) — the only authorized by-identifier path. The UI performs **no** access decision: it maps kind → tool + identifier, sends it, and renders the backend's allowlisted projection (business-labelled scalar rows plus collection counts). Signed URLs are neither requested nor displayed (AGENTS.md §68).
* Non-success outcomes (`no_data`, `not_authorized`, `invalid_input`, `provider_unavailable`, `error`) and thrown request errors (including 404) all render **one** shared non-disclosing state: "CarbonTally can't open this reference for you…". It asserts neither existence nor absence, so nothing is leaked in either direction, and the backend's own wording is never echoed. The mapping is a single pure function (`resolutionPresentation`) that both the component and the tests use, so the copy cannot drift from the behaviour.
* There is **no client-side authorization logic and no cached grant**: re-opening a reference always issues a new authorized request (asserted by test). Possessing an id, a URL or a previous response grants nothing.
* `evidence_line_item` has no ratified by-id lookup and is therefore presented as an unopenable locator (§7).
* Historical evidence is read lazily through `GET /interactions/{id}` (creator-private); a failed read shows a non-disclosing "Evidence not available" state with a retry.

## 12. Provider-unavailable behaviour

* When the backend reports narration unavailable (`answer_status=provider_unavailable` and/or `narration_state=unavailable`) the deterministic result stays on screen: the answer state, the CarbonTally data lookups with their I3 statuses, and the reference locators remain visible.
* The gap is named explicitly ("Written summary unavailable … the result from your data is shown here and is unchanged"). The copy makes clear that CarbonTally's own result is **not** what failed.
* **No narration is fabricated**: the UI renders `narration_text` only when the backend produced it; there is no client-side provider fallback, no placeholder text and no generated summary. Asserted by test (the "CarbonTally summary" block is absent when there is no narration).
* `narration_state=skipped` (no provider configured) shows the deterministic result alone with an informational note, not an error.
* A **completed** narration read from history (where the text lives in the transcript, not in the list row) says "Summary in the conversation" — it must not claim that no summary was generated. This was a truthfulness defect found during testing and fixed.

## 13. Accessibility and responsive implementation

| Requirement | Implementation |
| --- | --- |
| Keyboard navigation | only native `<button>`, `<input>`, `<textarea>` and `<a>` controls; no click-only handlers; tab order follows the visual reading order (asserted with `userEvent.tab()`) |
| Meaningful accessible labels | every control is labelled (`Start a new conversation`, `Ask a question about your emissions data`, `New`, `Ask`, `Open <Kind> <id>`, `View/Hide answer details`) |
| Focus management | after an answer arrives, focus moves to that answer's heading (which receives `tabindex="-1"`); the move waits for the element to be committed rather than being dropped |
| Semantic structure | `<section>` with `aria-labelledby` for the answer state, the tool evidence, the provenance references and both panels; `<ol>`/`<ul>` for transcripts and lists; headings are real `h1`–`h4` |
| Status not by colour alone | every answer state carries a visible text label plus an icon (D21.4 rule); tone classes only reinforce it |
| Disclosure semantics | the evidence toggle exposes `aria-expanded` and `aria-controls`, and the controlled panel id resolves to a real element; the selected conversation carries `aria-current="true"` |
| Live/announcement regions | the existing `LoadingState` (`role="status"`) and `Alert` (`role="status"`/`role="alert"`) conventions are reused |
| Responsive | the workspace uses the D20 two-pane grid (`300px | 1fr`) collapsing to a single column at ≤900px; ≤640px stacks the evidence rows and narrows the answer gutter; long identifiers wrap (`overflow-wrap: anywhere`) and no element can force horizontal page overflow (`min-width: 0` on every flex/grid child) |
| Design system | D21 tokens only (`var(--ct-*)`); the stylesheet contains **no** private hex palette (asserted by test) |

No new accessibility or responsive framework was introduced; no global design-system change was made.

## 14. Tests added

| Suite | Path | Tests | Covers |
| --- | --- | --- | --- |
| Answer states | `frontend/src/v3/__tests__/insight-answer-states.test.js` | 29 | the fourteen-state vocabulary, distinct labels, `answerIsZero` for every state, the `data-answer-zero` marker, `no_data` ≠ `zero`, unknown states, narration (completed / unavailable / skipped), replay, lifecycle |
| References | `frontend/src/v3/__tests__/insight-references.test.jsx` | 18 | the four ratified kinds, the identifier→tool mapping, `evidence_line_item` unresolvable, the allowlisted projection, locator rendering, successful resolution, re-read (no cached grant), every non-success status non-disclosing, thrown 404/network non-disclosing |
| Workspace | `frontend/src/v3/__tests__/insight-page.test.jsx` | 45 | entry/context (loading, no org, failure+retry), conversation list (render, current, empty, error+retry), conversation view (history, roles, empty, errors), start/continue, ask + outcome rendering, ask failure non-disclosing + draft preserved, all fourteen answer states end-to-end, `no_data` ≠ `zero`, `not_authorized` non-disclosure, provider-unavailable (deterministic evidence retained, no fabricated narration), replay, historical evidence read + non-disclosing failure, accessibility (labels, tab order, focus, status not colour-only), responsive layout + stylesheet contract |
| API client | `frontend/src/v3/__tests__/insight-api.test.js` | 8 | every Insight call target, method, organization scope, conversation filter, idempotency key/narration handling, the I3 tool surface used for reference resolution |
| Routing / guards | `frontend/src/__tests__/insight-routing.test.jsx` | 10 | the `/insight` route wiring (`ProtectedRoute` + `RoleRoute requireOrg` + `V3Layout` + `InsightPage`), no staff-union guard, not on the public surface (so no public assistant), guard allow/deny for customer / consultant / PE / staff / org-less / fail-closed, the customer navigation entry |

No existing test was modified, weakened or deleted. The five new files are the **only** test-file changes; `git status` shows no modification to any pre-existing test.

## 15. Tests executed and exact results

Environment: `/home/shomonrobie/ct_93d5cdd/frontend`, Node `v22.22.1`, npm `9.2.0`, `react-scripts` 5 (Jest 27 + jsdom 16 + RTL), `CI=true npx react-scripts test --watchAll=false`.

| Run | Command | Result |
| --- | --- | --- |
| **T1 — new I6 suites** | `--testPathPattern="insight"` | **5 suites passed / 0 failed; 110 tests passed / 0 failed** (29 + 18 + 45 + 8 + 10) |
| **T2 — v3 regression suite** (`src/v3/`) | `--testPathPattern="src/v3/"` | **30 suites: 29 passed / 1 failed (pre-existing); 328 tests: 327 passed / 1 failed (pre-existing)** |
| **T3 — full frontend suite** | (all tests) | **39 suites: 37 passed / 2 failed (both pre-existing); 430 tests: 429 passed / 1 failed** |
| **T4 — compilation** | `npx react-scripts build` | **compiled successfully** (exit 0). The 27 files carrying pre-existing ESLint warnings do **not** include any I6 file or any file whose only change is I6 |
| **T5 — pre-change baseline** | `--testPathPattern="src/v3/"` on the pristine 4887c66 tree | **26 suites: 25 passed / 1 failed; 228 tests: 227 passed / 1 failed** |

Per-suite results for the new I6 work:

```
PASS src/v3/__tests__/insight-answer-states.test.js
PASS src/v3/__tests__/insight-references.test.jsx
PASS src/v3/__tests__/insight-page.test.jsx
PASS src/v3/__tests__/insight-api.test.js
PASS src/__tests__/insight-routing.test.jsx
Test Suites: 5 passed, 5 total
Tests:       110 passed, 110 total
```

The specific properties the authorization asked to verify are each asserted by test:

* `no_data` is never rendered as `zero` — `answerIsZero()` is `true` only for `zero`, and `data-answer-zero` is `"false"` for all thirteen other states, at both the component and the workspace boundary;
* provider-unavailable does not fabricate narration — the deterministic tool evidence and references remain, the unavailability notice is explicit, and no summary text is rendered;
* unauthorized resource failures do not leak resource existence — a single non-disclosing message for `no_data`/`not_authorized`/`invalid_input`/`provider_unavailable`/`error`/404/network, asserted not to match existence/denial wording;
* references do not create client-side authorization — resolution always issues an authorized backend request (re-opening re-requests), and an unresolvable kind offers no client-side route at all;
* creator-private boundaries are respected by contract — the UI reads only the backend's creator-filtered lists and every interaction/reference read is a fresh authorized request carrying the caller's organisation.

## 16. Pre-existing failures (unchanged, not caused by I6)

Two pre-existing failures remain, both reproduced on the **pristine** `4887c66` tree before any I6 change:

| Pre-existing failure | Evidence |
| --- | --- |
| `src/v3/__tests__/dr007-investor-display-fixes.test.jsx` → "Issue 3 — customer review detail shows Mapped activity from mapped_data.activity" (`Expected substring: "Natural gas"` / `Received string: "Mapped activity"`) | present in the pre-change v3 baseline (T5: 227 passed / 1 failed) and unchanged after I6 |
| `src/App.test.js` → suite fails to run: `Cannot find module 'react-router/dom' from 'node_modules/react-router-dom/dist/index.js'` | reproduced on the **stashed (pristine) tree** with the identical error before the change was restored |

Neither is related to Insight, and neither was "fixed", suppressed, skipped or deleted.

**Environment repair (not a repository change).** On this checkout the frontend suite could not run **at all** at the start of the task: 26/26 suites failed with `Cannot find module '../build/Release/canvas.node'` because the optional `canvas@2.11.2` (a transitive optional dependency of `pdfjs-dist` and `jsdom@16`) is present in `node_modules` without its native binary, and jsdom 16 resolves the package directory and then requires it unguarded. `libcairo` is not installed, so the native module cannot be built here. The unbuilt package directory was moved aside (`frontend/node_modules/canvas` → `frontend/node_modules/.canvas-disabled-unbuilt-2.11.2`), which is the state jsdom treats as "canvas not installed" (`require.resolve` fails → canvas features disabled). `node_modules` is git-ignored (`frontend/.gitignore: /node_modules`), so **no repository content changed**. Reversal: `mv frontend/node_modules/.canvas-disabled-unbuilt-2.11.2 frontend/node_modules/canvas`. This is recorded because it affects reproducible test evidence, and it also explains why the T5 baseline could only be measured after the repair.

## 17. Limitations

1. **No browser/E2E or visual verification was performed.** All evidence is unit/component-level (Jest + RTL + jsdom) plus a successful production compilation. Real-browser behaviour (actual media-query layout, real focus traversal, screen-reader output, a live backend) is **not** verified by this report and is left to independent verification (OHD).
2. **Responsive behaviour is asserted statically**, not rendered: jsdom does not evaluate media queries, so the tests pin the DOM structure the classes apply to plus the stylesheet's breakpoint rules for those classes. No pixel-level or viewport-matrix checking was performed.
3. **No live backend was contacted.** Every API response used by the tests is a mock that mirrors the inspected backend contract; end-to-end behaviour against a running FastAPI + Supabase environment is unverified here.
4. **Consultants and internal staff have no UI entry point.** The I2 boundary permits them (`PERSONA_CONSULTANT`, `PERSONA_STAFF_INTERNAL`), but PO I6-1 places Insight in the customer workspace, so `/insight` is guarded by `requireOrg`. Giving consultants/staff an entry point (and a consultant/staff shell rendering) is a **PO decision** beyond this authorization, not an implementation omission within I6.
5. **`evidence_line_item` cannot be opened from the UI** (§7) because no ratified tool accepts that identifier. Resolving it would require a new I3 tool = a PO decision.
6. **`tokens_used` / `cost` are not displayed.** The backend may return them; PO §3.7 forbids fabricating usage/cost, and no authoritative display decision exists for I6, so the UI shows nothing rather than an ambiguous figure.
7. **No retention, deletion, export or consent controls** are exposed (I7), and no billing/entitlement gating is applied to the Insight route (I8) — both explicitly out of scope.
8. **Insight context is not surfaced in the UI.** I5 is current-conversation, bounded context assembled server-side; there is no I6 decision to expose "what context was used", and doing so would imply functionality the contract does not offer. The UI therefore shows the conversation history and the per-interaction evidence only.
9. **One Insight test file asserts the stylesheet contents** (`insight.css`) for the responsive/token contract; if the stylesheet is restructured those assertions must be updated with it (they are intentionally coupled to the classes under test).
10. **Hindsight MCP was unreachable during this task** (`http://127.0.0.1:9077` refused the connection), so no memory recall or retention was possible; the repository, the PO records and the live code were used as the source of truth instead.

## 18. Non-blocking observations (recorded, not expanded)

These are observations for the Product Owner. **None was converted into implementation work, and none changes a contract.**

1. **`evidence_line_item` resolution gap** — the kind is ratified (I3 §8) but no ratified tool accepts an evidence-line-item id, so it cannot be opened from the UI. Closing it needs a PO decision (a fifth/by-id tool, or widening an existing tool's accepted input). Until then the UI shows it as an unopenable locator.
2. **Consultant / staff Insight entry point** — the I2 boundary authorizes consultants (for granted client organisations) and internal staff (within their existing permissions), but PO I6-1 puts the UI in the customer workspace and there is no I6 decision for a consultant or staff Insight rendering. The backend is ready; the entry point is a PO decision.
3. **Customer Viewer role** — `org_viewer` is authorized by I2 (`CUSTOMER_INSIGHT_ROLES`) and `RoleRoute requireOrg` admits any active member, so a Viewer can use Insight and run interactions. Whether a Viewer should be able to *run* interactions (rather than only read their own history) is a product decision not covered by I6-1/I6-3. Nothing was assumed; the UI follows the backend's answer.
4. **Interaction list pagination** — the conversation view requests the backend default (limit 50, offset 0) and the message history limit 200. Very long conversations would need paging controls; no I6 decision covers it, and the backend already exposes `limit`/`offset`.
5. **Narration appears twice by design** — the I4 contract persists narration as a conversation message *and* returns `narration_text` in the interaction response, so for a fresh answer the same sentence is visible in the transcript and in the answer card. This is faithful to the contract; de-duplicating the presentation would be a PO choice.
6. **`tokens_used` / `cost`** — returned nullable by the model and not displayed (PO §3.7: never fabricate usage/cost). No Insight usage surface exists yet (I8).
7. **No deep-link to a conversation** — conversations are creator-private and the UI has no share affordance by design; a directly addressable conversation URL would need a PO decision and would have to preserve the same creator-private guarantees.
8. **`audit_record_id` is not displayed** — it is an internal correlation detail rather than customer-facing business state (AGENTS.md §75). Recorded, not implemented.
9. **Automated accessibility tooling** — the project does not currently ship `jest-axe` or an equivalent, and I6 was not authorized to add a new accessibility framework (PO §13). Accessibility is covered by assertion-level tests on labels, roles, focus and semantics.
10. **`frontend/build/`** — the verification build produced a git-ignored output directory in this checkout; it is not tracked and is not part of the change.

## 19. Out-of-scope confirmation (nothing else was touched)

Explicit confirmation, verified by `git status` and `git diff --stat` (4 modified files, **+111 / −0**; 13 new files):

* **No backend change of any kind** — no file under `backend/` was modified: no API, no service, no domain contract, no repository/SQL.
* **No authorization change** — I2 (`api/insight_authz.py`) is untouched; no role, permission or capability was added or widened; no RLS policy changed; no `public.audit_trail` change.
* **No I1 change** — conversation/message persistence is consumed as-is.
* **No I3 change** — the four-tool catalogue and `ToolStatus` are consumed as-is; no tool was added.
* **No I4 change** — interaction / tool-call / answer-state / audit contracts are consumed as-is; no new answer state was introduced.
* **No I5 change** — context assembly and the 20,000-character default are untouched; no summarization, compaction, cross-conversation memory, RAG, embeddings, vector search, LangChain or context-budget change exists in the frontend (the UI has no way to address the context assembler).
* **No I7 work** — no retention period, deletion policy, legal hold, export policy, privacy policy, residency, subprocessor or PII-classification content.
* **No I8 work** — no billing, pricing, credit, entitlement, subscription, payment, metering, commercial configuration or SLO/backup/runbook content; the Insight route is not gated on entitlement.
* **No schema or migration** — no migration file was added or changed; no database was contacted.
* **No public-surface change** — `frontend/src/public/**` (including the assistant) is untouched; `/insight` is not a public route.
* **No navigation redesign** — the shell, breakpoints, tray behaviour and every other nav entry are unchanged; no D1–D21 frozen decision was altered.
* **No new dependency** — `frontend/package.json` is unchanged; MUI/Emotion, `react-icons`, `react-router-dom` and `@testing-library/*` were already in use.
* **No unrelated refactor, no legacy deletion, no test weakening** — no pre-existing test file was modified.
* **No production contact** — no deployment, no production database and no production API was contacted.
* **No other checkout touched** — only `/home/shomonrobie/ct_93d5cdd` was modified; `/home/shomonrobie/carbon_tally` was not touched.
* **No secrets** — nothing credential-like was added, printed or committed.

## 20. Git state and evidence

| Item | Value |
| --- | --- |
| Modified | `frontend/src/App.js`, `frontend/src/v3/api.js`, `frontend/src/v3/components/V3Layout.jsx`, `frontend/src/v3/components/ui/Icon.jsx` (+111 / −0) |
| Added (source) | `frontend/src/v3/insight/{InsightPage.jsx, InsightInteraction.jsx, InsightAnswerState.jsx, InsightReferences.jsx, answerStates.js, references.js, format.js, insight.css}` |
| Added (tests) | `frontend/src/v3/__tests__/{insight-answer-states.test.js, insight-page.test.jsx, insight-references.test.jsx, insight-api.test.js}` and `frontend/src/__tests__/insight-routing.test.jsx` |
| Added (docs) | this report |
| Ignored build output | `frontend/build/` (git-ignored, not committed) |
| Database | **not contacted; no change** |
| Remote | pushed to `github/p8-release-reconciled` only |

## 21. Implementation status

> **I6 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION**

* **Implemented**: the authorized I6 UI scope only (§3).
* **Tested**: 110 new I6 tests pass; the pre-existing suites still pass except the two pre-existing failures in §16; the application compiles.
* **Verified**: **no** — this report does not claim verification. Independent verification (OHD) and the PO closure decision are separate, subsequent steps.
* Nothing was deployed, nothing was declared `CLOSED` or `VERIFIED PASS`, and no I7/I8 work was started.








