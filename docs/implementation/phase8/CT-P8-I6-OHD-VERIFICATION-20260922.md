# CT-P8-I6-OHD-VERIFICATION-20260922

**Independent verification of CarbonTally Insight I6 — UI.**

| Item | Value |
| --- | --- |
| **Verification ID** | `P8-I6-OHD-VERIFY-20260922-01` |
| **Final OHD verdict** | **`I6 VERIFIED PASS`** |
| Verified revision | `ea7ccc28be3756ec9c5e569a24d36c5811752c4d` (`ea7ccc2`) — current `p8-release-reconciled` HEAD |
| Implementation commit | `09e231503703895ebeec637e846cac6ce8523091` (`09e2315`) — **see A-1**: the authorization text and the I6 report both quote the digest `09e2315141a4df6fc90e78f70d53d74cbd0c9d3a`, which **is not an object in this repository** |
| Implementation baseline | `4887c668ac618cff5974bc510b355a6a6c84e149` (`4887c66`, I5 closure) |
| Verifier | OHD — independent, read-only |
| Date | 2026-09-22 |
| Blockers | **none** |
| Nonblocking observations | A-1…A-5 (§19) + dispositions of Cline's O-1…O-10 (§19) |
| PO decisions requested | **4 nonblocking product/PO items** (§26) — none affects I6 compliance |

> **Verification only.** No implementation, test, backend, API contract, schema, migration, RLS, billing, configuration or frontend file was modified, refactored, fixed or reverted. No remediation was committed or pushed. The only repository change is this report. Mutations and adversarial tests were applied to **isolated copies under `/tmp`**, never to the authoritative checkout.

Legend: **[FACT]** independently reproduced · **[OBS]** observation · **[NB]** nonblocking · **[PO]** PO/product decision required · **[BLOCKER]** blocking defect.

---

## 1. Verification ID

`P8-I6-OHD-VERIFY-20260922-01` — issued 2026-09-22 as **independent verification only; no remediation authorized**.

## 2. Verification authority and scope

Authority: the OHD authorization of 2026-09-22 (this task), bounded by the PO decision record's I6 sections and the I6 authorization boundary. Scope: independent determination of whether I6 conforms to the PO-authorized I6 scope, plus regression, sensitivity, scope-audit and production-boundary checks. Cline's report `I6 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION` was treated as a **claim**, never as evidence: every item below was obtained by independent inspection, tracing, execution and adversarial testing. Where Cline's figures and mine agree, that is recorded as independent corroboration; where they differ, the difference is documented (A-1, A-5). No PO decision was reinterpreted; ambiguity was reported, not resolved. I5 was not reopened (no I5 regression was observed, §18).

## 3. PO source documents

| Document | Commit | Use |
| --- | --- | --- |
| `docs/architecture/CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` | `43f572d` | §5 (I6 status, I6-1…I6-10 decisions, **I6 authorization boundary**), §3.1–§3.7, §14 |
| `docs/architecture/CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md` | `4887c66` | I5 `CLOSED — VERIFIED PASS`; **O-1 decision** (20,000 characters = initial/default budget, *not* a ceiling; no clamp may be added) |
| `docs/implementation/phase8/CT-P8-I6-INSIGHT-UI-20260922.md` | `09e2315`/`ea7ccc2` | Cline's I6 implementation report (claims under test) |
| `docs/implementation/phase8/CT-P8-I5-I8-PREAUTHORIZATION-READINESS-AUDIT-20260921.md` | `fef4e70` | I6 readiness: "READY WITH PO DECISIONS", no backend contract gap |
| Master Specification v1.1 | `4887c66` | §14 answer vocabulary, §15.4 tokens/cost, reference kinds, §3.1 stage state |

Ratified I6 requirements verified: authenticated customer-workspace entry point (I6-1); dedicated route/navigation without a navigation redesign (I6-2); creator-private conversation list/view/history with start/continue and no shared workspace (I6-3); references as evidence/provenance locators, never access, with backend re-authorization and non-disclosing failure (I6-4); the complete fourteen-state I4 answer vocabulary with `no_data` never rendered as `zero` (I6-5); provider-unavailable behaviour (I6-6); empty/loading/no-data/clarification/unauthorized/provider-unavailable/general-error states with non-disclosing errors (I6-7); replay as informational only (I6-8); no public-assistant reuse (I6-9); accessibility and responsive acceptance without a new framework (I6-10). Boundary: no backend authorization change, **no new Insight API** unless a contract gap is demonstrated and separately authorized, no I3/I4 semantic change, no shared/private data exposure, no billing, no retention/export, no public Insight access.

## 4. Repository/branch/commit verified

| Check | Result |
| --- | --- |
| Checkout | `/home/shomonrobie/ct_93d5cdd` (the authoritative repository; no other checkout touched) |
| Branch | `p8-release-reconciled` — never switched |
| Actual HEAD | `ea7ccc28be3756ec9c5e569a24d36c5811752c4d` **[FACT]** equals the reported HEAD |
| Remote | `github/p8-release-reconciled` = `ea7ccc2…`; `git rev-list --left-right --count` = `0 0` (aligned) **[FACT]** |
| Working tree | clean (`git status --porcelain --untracked-files=all` empty), stash empty **[FACT]** |
| Tree after verification | **0 changes**; the build directory created by the required build run was removed; `node_modules` is git-ignored and untracked **[FACT]** |

## 5. Implementation commits verified

**[FACT] A-1 — the quoted implementation digest does not exist.** `git cat-file -t 09e2315141a4df6fc90e78f70d53d74cbd0c9d3a` → `fatal: could not get object info`. The repository's I6 implementation commit is **`09e231503703895ebeec637e846cac6ce8523091`** (`09e2315`), the parent of the documentation commit `ea7ccc2`; the two strings share the leading `09e2315` and diverge at the 8th hex digit. The same incorrect digest is recorded in `CT-P8-I6-INSIGHT-UI-20260922.md`. The commit is unambiguously identifiable by its abbreviated form and its position in history, so verification proceeded against it; the wrong digest is a **documentation accuracy defect** (§19 A-1), not an implementation defect. (The I5 authorization text contained the analogous error — a 39-character digest.)

**[FACT] Footprint `4887c66 → ea7ccc2`: 18 files, +3,678 / −0** — 17 frontend files + 1 documentation file; `backend/`, `supabase/`, `prisma/`, `docs/architecture/` each changed **0** files. Commits: `09e2315` (implementation) and `ea7ccc2` (the report's implementation-revision line).

| Area | Files |
| --- | --- |
| Routing/shell | `frontend/src/App.js` (+13), `v3/components/V3Layout.jsx` (+3), `v3/components/ui/Icon.jsx` (+1) |
| API client | `frontend/src/v3/api.js` (+94, additive; **no new endpoint**) |
| Insight module | `v3/insight/InsightPage.jsx` (494), `InsightInteraction.jsx` (197), `InsightAnswerState.jsx` (91), `InsightReferences.jsx` (153), `answerStates.js` (257), `references.js` (188), `format.js` (17), `insight.css` (484) |
| Tests | `v3/__tests__/insight-answer-states.test.js`, `insight-api.test.js`, `insight-page.test.jsx`, `insight-references.test.jsx`, `src/__tests__/insight-routing.test.jsx` |
| Documentation | `docs/implementation/phase8/CT-P8-I6-INSIGHT-UI-20260922.md` |

## 6. Files inspected

Read in full: all eight `frontend/src/v3/insight/*` files; the `api.js` I6 addition; the `App.js` route block, `PUBLIC_ROUTE_PREFIXES`, `PublicAssistant`, `ProtectedRoute`; `V3Layout.jsx`/`Icon.jsx` diffs; all five I6 test files; `v3/components/RoleRoute.jsx`; `components/ui/StateViews.jsx`, `Button`, `Alert`, `Badge`, `uuidFallback`. Backend contracts consulted (unchanged): `api/v3_insight.py`, `api/v3_insight_interactions.py`, `api/v3_insight_tools.py`, `api/router.py`, `api/insight_authz.py`, `domain/insight_tool.py` (`REFERENCE_KINDS`, `ToolInputSpec`), `domain/insight_interaction.py` (`AnswerStatus`, `NarrationState`, `MAX_QUESTION_LENGTH`, `MAX_IDEMPOTENCY_KEY_LENGTH`), `services/insight_tools.py` (`TOOL_DEFINITIONS` output/input allowlists), `services/insight_interactions.py` (`NARRATION_MODES`), `data/insight.py`, `data/insight_interactions.py`. Documents: PO record, I5 closure, I6 report, readiness audit. Environment: `frontend/package.json`, `.gitignore`.

## 7. Route/authentication verification

**[FACT] The route exists in the authenticated customer workspace and follows the existing v3 convention.** `App.js`:

```jsx
<Route path="/insight" element={
  <ProtectedRoute>
    <RoleRoute requireOrg>
      <V3Layout><InsightPage /></V3Layout>
    </RoleRoute>
  </ProtectedRoute>
} />
```

This is the same composition used by the neighbouring customer routes (`/issues`, `/messaging`), and it does not use the coarse staff-union guard. **[FACT] Authentication is enforced**: `ProtectedRoute` (App.js:190) resolves the Supabase session and returns `<Navigate to="/login" replace />` when there is no session. `RoleRoute requireOrg` additionally requires a server-resolved organisation.

**[FACT] Not on the public surface.** `PUBLIC_ROUTE_PREFIXES` (App.js:1877, 18 prefixes: `/login`, `/privacy`, `/cookies`, `/terms`, `/about`, `/platform`, `/services`, `/processing-services`, `/consultants`, `/pricing`, `/contact`, `/faq`, `/carbon-reduction-plan`, `/signup`, `/beta/signup`, `/beta-login`, `/glossary`, `/auth/callback`, `/auth/magic`) does **not** contain `insight`; `PublicAssistant` computes `isPublic` from exactly that list plus `/` and returns `null` when `!isPublic`. An unauthenticated request to `/insight` therefore renders no Insight content and no public assistant.

**[FACT] The real security boundary is the backend, and it is unchanged** (0 backend files modified): every endpoint the UI calls requires an authenticated `require_insight_user` dependency plus I2 scope re-authorization. The route guard is UX only. Nothing in the I6 diff weakens the API.

## 8. Conversation UX verification

**[FACT] Implemented as required (I6-3).** The workspace provides a creator-private conversation list (newest-first from the backend), a conversation view, the persisted message history loaded from the backend, start-a-conversation, continue-a-conversation, and per-state handling. The backend — not the UI — decides which conversations exist: no client-side filtering, ordering or authorization exists anywhere in the module (grep for role/authorization logic returns only `role="alert"` and the display of `message.role`).

| UX state | Where | Verified |
| --- | --- | --- |
| context loading / context failure + retry / no-organisation | `InsightPage.jsx` 204–248 | [FACT] my probe renders the empty and error paths |
| conversation list loading / error + retry / empty / populated | 303–345 | [FACT] |
| nothing selected / conversation view | 348–365 | [FACT] |
| history loading / error + retry / empty / populated with roles | 401–442 | [FACT] |
| answers loading / error + retry / empty / populated | 450–483 | [FACT] |
| ask in-flight, ask failure (generic, draft preserved) | 171–201 | [FACT] |
| interaction evidence loading / failure + retry | `InsightInteraction.jsx` 143–153 | [FACT] |

**[FACT] No false impression of shared access.** The page header states "Your conversations are private to you", and an opened conversation states "This conversation is private to you. CarbonTally never shows it to another user." My independent probe asserts that privacy wording is present and that no "shared with"/"team members"/"visible to your organisation" wording appears. **[FACT] Foreign/inaccessible conversations**: a conversation id whose reads fail renders only the generic "CarbonTally couldn't load this conversation's history." with a retry — no disclosure of existence (probe-verified; see §9).

## 9. Authorization/security verification

**[FACT] The UI is not a security boundary and makes no access decision.** Every read and write goes through `v3Fetch` to a closed I1–I4 endpoint; reference resolution goes through the ratified I3 tool-invocation endpoint. There is no client-side authorization logic, no cached entitlement, and no id-based trust.

**Independent non-disclosure testing (my probe, 16/16 passed against the unmodified HEAD code).** For a reference whose resolution fails, the rendered text is **byte-identical** across a thrown 404, `not_authorized`, `no_data`, `invalid_input`, `provider_unavailable` and `error`. **[FACT] The mechanism is structural, not incidental (A-2):** `resolutionPresentation()`'s return value is consumed only as a `=== null` discriminator (`InsightReferences.jsx:53`); the rendered note is a single shared constant (`REFERENCE_UNAVAILABLE`), so failure modes cannot be distinguished regardless of tool status. A mutation that made `not_authorized` return a distinguishing message was **inert** (§22 M5) — the mutation could not leak because the payload is never displayed.

| Case | Independent result |
| --- | --- |
| authorized creator | allowed (all reads 200; the UI renders the returned data) |
| foreign conversation / inaccessible conversation | generic failure text, non-disclosing; verified by probe with a mocked 404 |
| cross-organisation resource | the UI has no cross-org path (it always sends its own `organization_id`); backend 403/404 unchanged |
| inactive relationship / non-member | backend-enforced (I2, unchanged); the UI renders the generic failure state |
| absent/unknown resource | identical to unauthorized (non-disclosing) |
| unauthenticated | `ProtectedRoute` → `/login`; `/insight` is not a public prefix; no Insight content rendered |
| IDs / references / client state / URL parameters | `data-reference-kind` and the short id are display-only; opening always re-calls the backend; no URL parameter selects a conversation or resource |

**[FACT] No leakage in error surfaces.** My probe asserted that a rejected read (mocked `401` carrying an `internal trace` body) yields only "CarbonTally couldn't load your conversations." and that the document contains no `internal trace|stack|supabase|postgres|service_role|secret|token` text. Interaction-evidence failures render a fixed "Evidence not available" alert. Error copy never names a foreign resource, its owner, or whether it exists.

## 10. Reference/evidence verification

**[FACT] The four ratified kinds are exactly the backend's** — `report`, `report_version`, `evidence_line_item`, `calculation_snapshot` (`domain/insight_tool.py → REFERENCE_KINDS`) — and each is labelled.

**[FACT] Resolution uses only ratified tools, with exactly matching input keys.** The UI maps: `report → report_lookup {report_id}`; `report_version → report_version_lookup {version_id}`; `calculation_snapshot → calculation_snapshot_lookup {snapshot_id}`. The registry's authoritative specs are `report_lookup.required=("report_id",)`, `report_version_lookup.optional=("version_id","report_id","version_number")`, `calculation_snapshot_lookup.required=("snapshot_id",)` — **every key the UI sends is a ratified key of that tool** [FACT]. Success renders the backend's already-allowlisted projection (`projectEvidenceRows`: scalars as rows, arrays as counts, objects as `id · status`) and nothing is inferred client-side.

**[FACT] References are presented as locators, never as access.** The section note reads: "These identify the CarbonTally records behind the answer. They are locators, not access: CarbonTally authorizes each one again whenever it is opened." A successful resolution re-invokes the backend on every open (probe asserts exactly one call per open).

**[FACT] Failure modes:** unauthorized, unavailable and malformed all collapse into the single non-disclosing state (§9). An unresolvable kind is offered **no** open control and shows a separate "cannot be opened from Insight" note (no client-side route is guessed).

### `evidence_line_item` (special observation O-1) — determination

1. **Is `evidence_line_item` required by the I6 contract to be openable?** **No.** PO I6-4 requires references to be *displayed as evidence/provenance locators*, requires the UI not to imply that possession grants access, requires backend re-authorization when a reference is resolved, and requires a **non-disclosing state "if resolution is unavailable or unauthorized"** — i.e. the contract explicitly contemplates unresolvable references.
2. **Does the contract require every reference kind to have a navigation/open action?** **No.** No such requirement appears in I6-4 or elsewhere in §5; the contract's operative requirement is the *locator* semantics.
3. **Is showing an unopenable provenance locator compliant?** **Yes — compliant.** [FACT] The claim's premise is itself verified: `report_evidence_lookup` requires a `report_version_id` (not an evidence-line-item id), and the other three tools accept a report id, a version id or a snapshot id — **no ratified tool accepts an `evidence_line_item` id as input**. Guessing a mapping would have been an unauthorized new identifier route; the implementation correctly refused. My mutation M3 (adding a guessed `evidence_line_item → report_lookup` mapping) was caught by two shipped tests (§22).
4. **Classification: PASS (compliant).** If the product wants `evidence_line_item` resolvable by id, that requires a **new or widened I3 tool — a separate PO decision outside I6's authorization** ("I6 must not … introduce new Insight APIs unless an actual contract gap is demonstrated and separately authorized"). Recorded as a nonblocking product limitation (§26 item 1). No remediation is proposed or implied.

## 11. Answer-state verification

**[FACT] The vocabulary is exactly the backend's fourteen states.** `ANSWER_STATUS_VALUES` = `success, zero, no_data, not_authorized, insufficient_data, needs_clarification, tool_failure, provider_unavailable, partial, rate_limited, refused, ungrounded, invalid_input, error` — identical (as a set) to `AnswerStatus` in `domain/insight_interaction.py`. The I3 `ToolStatus` vocabulary is presented separately for evidence and is never merged.

**[FACT] `no_data` is never rendered as `zero`** — verified three ways:
1. `answerIsZero(status)` is `true` only for `'zero'`, and `InsightAnswerState` emits `data-answer-zero="true|false"` from it (a machine-checkable marker).
2. My independent probe rendered **all fourteen** states: every state has a distinct, non-empty label (14 distinct labels, no collapsing), `data-answer-zero` is `true` **only** for `zero`, the `no_data` copy reads "No matching CarbonTally records were found" and never "result is 0", and the `zero` copy explicitly says a zero is "a real calculation … not an absence of data" while `no_data`'s guidance says "This is not the same as a result of 0".
3. Unknown/missing/malformed statuses (`''`, `'not_a_real_state'`, `'ZERO'`, `'zero '`, `undefined`) render the neutral "not recognised" presentation with `data-answer-zero="false"` — never zero, never an answer [FACT].

**[FACT] All fourteen states are reachable in the UI and rendered end-to-end** (the shipped page suite drives each state through the page; my probe drives each state through the component). No state is silently upgraded or downgraded: each has its own label, tone, icon and guidance, and the status is conveyed by text **and** icon, never colour alone.

## 12. Provider-unavailable verification

**[FACT] I6-6 satisfied.** With `answer_status=provider_unavailable` and `narration_state=unavailable`, my probe confirms: the answer state is presented truthfully; the deterministic CarbonTally summary line states the result "below is authoritative and is unaffected"; the deterministic tool evidence (the I3 lookup with its status) remains rendered; and **no narration text is shown** — the "CarbonTally summary" block is absent, so nothing is fabricated. The gap is named ("CarbonTally could not generate the written summary … no summary has been invented to replace it"). Provider failure is never presented as a CarbonTally data failure: the copy distinguishes the *written summary* from *your data*.

**[FACT] Truthful narration handling in all four `NarrationState` values:** `completed` → the backend's `narration_text` is displayed as CarbonTally content; for a *historical* row whose text lives in the transcript the UI points at the transcript ("Summary in the conversation") rather than denying it; `unavailable` → the explicit notice above; `skipped`/`not_attempted` → the deterministic result alone with an informational note (not an error). The UI sends `narration: 'optional'`, which is in the backend's `NARRATION_MODES = (none, optional, required)`, so an unconfigured provider yields a deterministic answer rather than a failure [FACT].

## 13. Empty/loading/error verification

All seven PO-required states are implemented as *distinct, explicit* presentations: initial empty (no conversations; nothing selected; no history; no answers), loading (context, conversations, history, answers, evidence — all inline or full-page), no-data (`no_data` answer state, plus the empty-evidence note), clarification (`needs_clarification`), unauthorized/hidden resource (single non-disclosing reference note; generic conversation/evidence failure states), provider-unavailable (§12), and general error (context failure, list/history/answers failures, ask failure, evidence failure — each with a retry where appropriate) [FACT].

**[FACT] Non-disclosure of errors:** failure copy is fixed, generic and technical-detail-free; my probe asserted the absence of stack, infrastructure, provider-secret and foreign-resource-existence terms in the rendered document. No raw `error.message` is ever rendered (mutation M6, which surfaced `error.message`, was caught by the shipped tests).

## 14. Replay/lifecycle verification

**[FACT]** `replayed=true` renders an informational alert ("Already answered — this is the existing answer for this question; it was not run or recorded twice"). It is **not** presented as a failure. **[FACT] No new lifecycle model**: the four displayed lifecycle labels (`received`/`executing`/`completed`/`failed`) are presentation of the existing I4 `lifecycle`; no client-side lifecycle state machine exists. **[FACT] No internal idempotency detail is exposed**: the client generates a UUID request key but never displays it (my probe asserts the rendered interaction contains no "idempotenc" text); the replay *decision* remains the backend's.

## 15. Accessibility verification

**[FACT] Keyboard/semantics.** Every interactive control is a native `<button>` (conversation select, "New", "Ask", "Open reference", "View/Hide answer details", retry actions) or a labelled form control (`label htmlFor` on the topic input and the question textarea); the composer's submit is disabled until a question exists. Expand/collapse controls expose `aria-expanded` and `aria-controls`; the active conversation exposes `aria-current`; regions expose `aria-labelledby`/`aria-label`; decorative icons are `aria-hidden="true"`.

**[FACT] Focus behaviour.** After a question is asked the page moves focus to the new answer's heading (`tabindex=-1` + `.focus()`, `InsightPage.jsx` 128–138, keyed on the returned interaction id) so a keyboard/screen-reader user lands on the result without hunting. My probe confirmed the workspace renders with a usable, labelled control set and no interaction traps (no click-only handlers, no hidden focusable overlays).

**[FACT] Status is never colour-only** — every answer state renders a text label and an icon in addition to its tone.

**[NB] O-9 — automated accessibility tooling.** `jest-axe` and `@axe-core/react` are **not** present in this project, and I6 correctly added no new accessibility framework (PO I6-10: "No new external accessibility framework is required"; the project's existing practice is assertion-level `@testing-library` tests, which are present and substantive). **Limitation:** there are therefore no automated axe-style assertions; this verification is static/manual plus executed behavioural tests. **Disposition:** the absence does not breach the PO acceptance criteria (keyboard accessibility, meaningful labels, usable focus states, responsive presentation, automated tests for major states — all present); adding axe would be a **PO/product decision**, not an I6 defect.

## 16. Responsive verification

**[FACT]** `insight.css` adapts the workspace with three media queries — `max-width: 900px` (sidebar/layout collapse, twice) and `max-width: 640px` (compact layout) — using the **same breakpoints as the existing v3 house style** (`v3.css`/`tokens.css` use 900px and 640px among others). The layout is a two-column sidebar + main that stacks at narrow widths, so the conversation list, conversation view, composer, answer states, references, and loading/error states all remain reachable at representative viewport sizes. Tone, tokens and primitives are the existing v3/D21 system; no new design system was introduced, consistent with I6-10 and the project conventions. The shipped page suite asserts the responsive/stylesheet contract for the major states.

## 17. API/client integration verification

**[FACT] No new API and no duplicate client.** The backend diff is **0 files**, so every endpoint must pre-exist — and it does: `GET/POST /api/v3/insight/conversations`, `GET /api/v3/insight/conversations/{id}/messages`, `POST/GET /api/v3/insight/interactions`, `GET /api/v3/insight/interactions/{id}`, `POST /api/v3/insight/tools/invoke` are all present in `api/v3_insight.py`, `api/v3_insight_interactions.py` and `api/v3_insight_tools.py` (included by `api/router.py`). The `api.js` addition is additive and reuses the existing `v3Fetch` helper and `resolveV3Organization` (which pre-exists — present in `4887c66:frontend/src/v3/api.js`); no second client, no new fetch wrapper, no new auth mechanism.

**[FACT] Request/response parity with the backend contracts:**

| UI call | Backend contract | Parity |
| --- | --- | --- |
| `listInsightConversations(org, {limit:50, offset:0})` | `organization_id` (required), `limit` 1..200 default 50, `offset` | ✅ |
| `createInsightConversation(org, title)` | `{organization_id, title?}`; `title` optional, max **200** | ✅ UI `maxLength=200` |
| `listInsightMessages(org, conv, {limit:200})` | `organization_id`, `limit` 1..500 default 200, `offset` | ✅ |
| `runInsightInteraction({..., question, idempotencyKey, narration})` | `{organization_id, conversation_id, question (max **2000**), idempotency_key (max **128**), narration}` | ✅ UI `maxLength=2000`; UUID key = 36 chars ≤ 128; `narration='optional'` ∈ `NARRATION_MODES` |
| `listInsightInteractions(org, {conversationId, limit:50})` | `organization_id`, `conversation_id?`, `limit` ≤200, `offset` | ✅ |
| `getInsightInteraction(org, id)` | `/interactions/{id}?organization_id=` | ✅ |
| `invokeInsightTool(org, tool, input)` | `ToolInvokeIn{organization_id, tool, input}` | ✅ |

**[FACT]** URL parameters are `encodeURIComponent`-escaped; `undefined`/`null` query values are omitted. The UI **never** posts a message directly (there is no `POST /messages` client), so it cannot forge a role or write conversation content — messages are written only by the I4 interaction path. The UI reads only the fields Cline's report lists and ignores everything else (fixture-verified, §19 A-4). Credentials flow through the existing `v3Fetch`/Supabase mechanism; no token handling was added.

## 18. I5/I1–I4 contract preservation

**[FACT] No I1–I4 contract was changed.** The change set contains **0** files under `backend/`, `supabase/`, `prisma/` and `docs/architecture/`; no migration, no RLS, no schema, no route, no service, no model and no test of the backend was touched. Consequently: authorization (I2) unchanged; conversation/message contracts (I1) unchanged; the I3 tool set, statuses and output allowlists unchanged; the I4 interaction lifecycle, `AnswerStatus`, evidence/reference contract, audit correlation and creator-private visibility unchanged. Frontend changes to shared files are three additive lines (`App.js` route, `V3Layout` nav entry, `Icon` mapping) and one additive `api.js` block.

**[FACT] I5 is untouched and not reopened.** No I5 file was modified; the I5 service module and its tests are byte-identical to `cd718d6`. The I6 UI does not implement a second context engine, does not add cross-conversation memory, summaries, RAG/embeddings/vector search or LangChain, does not change the 20,000-character default (no `CARBONTALLY_INSIGHT_CONTEXT_MAX_CHARS` reference exists in the frontend at all), and introduces no new backend authorization model. The PO O-1 decision (20,000 = default, no clamp) was respected: nothing in I6 adds or removes a clamp.

## 19. Cline observation disposition

**Verifier findings first.**

* **[NB] A-1 — the recorded implementation SHA does not exist (documentation defect).** Both the authorization text and `CT-P8-I6-INSIGHT-UI-20260922.md` record `09e2315141a4df6fc90e78f70d53d74cbd0c9d3a`; the repository object is `09e231503703895ebeec637e846cac6ce8523091`. The I6 report is a permanent artifact whose purpose is future traceability, so a wrong digest is a real (if small) record-integrity defect. **Not a code defect, not a blocker** (the commit is identifiable by abbreviation and position, and every claim I checked against the commit was correct). A **docs-only correction** is advisable; none was made (§29 forbids it here).
* **[NB] A-2 — non-disclosure is by construction (a strength, recorded for future maintainers).** `resolutionPresentation()`'s payload is unused; the single shared constant is what renders. This makes failure modes indistinguishable regardless of backend status, but it also means the producer's return object is dead data — if a future change starts rendering that payload, the property would depend on the mapping again. The shipped tests do pin the rendered constant, so such a regression would fail them.
* **[NB] A-3 — the routing test is a source-text test.** `insight-routing.test.jsx` regex-matches `App.js`/`V3Layout.jsx` source rather than rendering the route. It is nonetheless effective: mutation M4 (removing `<ProtectedRoute>` from the `/insight` route) was **caught** by it. Recorded as a method note, not a defect.
* **[NB] A-4 — a frontend data-layering dependency.** `projectEvidenceRows` renders every key the backend returns (labels only are mapped client-side). This is safe precisely because the I3 tools' `output_fields` allowlists are the boundary (verified in the I3/I5 rounds); the UI adds no fields but also performs no second allowlist. No exposure exists today; noted so that a future change to a tool's output is recognised as the place where exposure would be introduced.
* **[NB] A-5 — test-environment dependency in the evidence.** Cline's documented environment repair persists: `frontend/node_modules/canvas` is absent and `frontend/node_modules/.canvas-disabled-unbuilt-2.11.2` exists (jsdom 16 otherwise fails to load). `node_modules` is git-ignored and untracked (`git ls-files frontend/node_modules` = 0), so **no repository content changed**, and the working tree is clean. Disclosure: my measurements depend on that repaired environment (as did Cline's), and I made no further change to it.

**Cline's observations, independently evaluated.**

| # | Cline's observation | OHD determination |
| --- | --- | --- |
| O-1 | `evidence_line_item` is a ratified kind with no ratified tool accepting its id, so it is shown as an unopenable locator | **VERIFIED CORRECT and COMPLIANT.** §10 above: the premise is independently confirmed against `domain/insight_tool.py`; I6-4 requires locator semantics and a non-disclosing state when resolution is unavailable, not universal openability. **PASS** + **[PO]** product decision if resolvability is wanted (new/widened I3 tool, outside I6). |
| O-2 | I6-1 scope is customer workspace only; consultant/internal-staff access is out of scope | **VERIFIED.** The PO record contains **no** I6 requirement for consultant or internal-staff Insight access (grep of the I6 decision text: no such entry); I6-1 says "authenticated customer workspace". The routing test additionally pins that consultants, PE staff and internal staff are routed to their own workspaces rather than into Insight. **[PO]** product decision, not an implementation defect — no inferred requirement. |
| O-3 | `org_viewer` interaction execution | **NOT AN I6 DECISION.** The UI contains no role rule for execution and must not invent one: it sends the request and renders whatever the backend authorizes; `RoleRoute requireOrg` governs workspace navigation, not execution rights. Whether a viewer may execute is an existing I2/I4 authorization-contract question. **[PO]** product decision if a stricter rule is desired; changing it would be a backend change outside I6. |
| O-4 | pagination | **VERIFIED LIMITATION [NB].** The UI requests backend defaults and offers no paging controls: conversations (newest 50 of `ORDER BY created_at DESC`), interactions (newest 50), messages `ORDER BY ordinal ASC LIMIT 200` — i.e. for a conversation beyond 200 messages the **oldest** 200 are shown and the newest transcript entries are not, with no way to page. The PO I6 scope requires list/view/history and start/continue, not pagination; the backend already exposes `limit`/`offset`. **Nonblocking product limitation** — see §26 item 4. |
| O-5 | narration appearing twice | **VERIFIED, ACCEPTABLE [NB].** Mechanism confirmed: the I4 backend persists the narration as an `insight`-role message (`content=narration_text`, `services/insight_interactions.py:495–501`) **and** returns `narration_text` in the interaction response, which the answer panel renders for the session's fresh outcome. The duplication therefore occurs only for a just-asked interaction; for historical rows the UI deliberately says "Summary in the conversation" instead. Faithful to the I4 contract; de-duplication would be a **PO presentation choice**, not a defect. |
| O-6 | `tokens_used` / `cost` | **CORRECTLY NOT IMPLEMENTED.** Zero UI references; the only occurrences are in a test fixture mirroring the real response shape. Master Spec §15.4 keeps tokens/cost NULL until truthful; I6 was not required to display them. **[NB]** no action. |
| O-7 | conversation deep-link | **CORRECTLY NOT IMPLEMENTED.** The only route is `/insight`; there is no conversation URL parameter. The PO does not require deep linking, and adding it would change routing behaviour beyond I6-2's "do not redesign global navigation". **[NB]** no action. |
| O-8 | `audit_record_id` | **CORRECTLY NOT EXPOSED.** Zero UI references (fixture-only). The PO does not require exposing audit identifiers to users; internal audit identity is not user-facing UI. **[NB]** no action. |
| O-9 | `jest-axe` | **ABSENT AND NOT REQUIRED** (§15). **[NB]** / **[PO]** only if automated a11y assertions are wanted later. |
| O-10 | ignored build output | **CONFIRMED CLEAN.** `.gitignore` has `build/`; 0 tracked files under `frontend/build/`; the build I ran produced no tracked change. **[NB]** no action. |

## 20. Regression testing and exact results

All runs on this machine (Node v22.22.1, npm 9.2.0, `react-scripts` Jest), executed by the verifier.

| Run | Scope | Exact result |
| --- | --- | --- |
| **T1 I6-focused** | `--testPathPattern="insight"` | **5 suites passed / 5; 110 tests passed / 110; exit 0** [FACT] |
| **T2 v3 subset at HEAD** | `--testPathPattern="src/v3/"` | **30 suites: 29 passed / 1 failed; 328 tests: 327 passed / 1 failed** [FACT] |
| **T3 full frontend suite at HEAD** | all tests | **39 suites: 37 passed / 2 failed; 430 tests: 429 passed / 1 failed** [FACT] |
| **T5 v3 subset on pristine `4887c66`** | `--testPathPattern="src/v3/"` | **26 suites: 25 passed / 1 failed; 228 tests: 227 passed / 1 failed** [FACT] |
| **T6 full suite on pristine `4887c66`** (my addition) | all tests | **34 suites: 32 passed / 2 failed; 320 tests: 319 passed / 1 failed** [FACT] |
| **Build** | `react-scripts build` at HEAD | **exit 0, "Compiled with warnings."** — 105 warning lines across 26 **pre-existing** files; **0 warnings mentioning insight**; identical count to the pristine baseline build (105/26) [FACT] |
| **My independent probe** | `/tmp` copy of HEAD + verifier-written adversarial suite | **16 passed / 16; exit 0** [FACT] |

**[FACT] The two full-suite failures are genuinely pre-existing.** They are identical at HEAD and on the pristine `4887c66` tree (T3 vs T6): (1) `src/App.test.js` → "Test suite failed to run: Cannot find module `react-router/dom` from `node_modules/react-router-dom/dist/index.js`" (a `node_modules` resolution problem on the pre-existing `App.js:4` import); (2) `src/v3/__tests__/dr007-investor-display-fixes.test.jsx` → "Issue 3 — customer review detail shows Mapped activity from mapped_data.activity" (expected "Natural gas", received "Mapped activity"). Neither involves Insight; the same two failures appear in both scopes. **[FACT] The I6 delta is exactly additive:** +5 suites and +110 tests at full-suite scope (39−34, 430−320) and +4 suites/+100 tests at v3 scope (30−26, 328−228) — matching the new I6 tests precisely, with no change to any pre-existing test file (0 pre-existing tests modified, skipped or deleted; `git diff --name-status` shows additions only).

**[FACT] Independent corroboration of Cline's figures.** T1, T2, T3 and T5 reproduce Cline's reported numbers **exactly** (110 / 328 with 1 failure / 430 with 1 failure / 228 with 1 failure). Cline's "T5 pre-change baseline" is scoped `--testPathPattern="src/v3/"`, which is why it reports 26 suites/228 tests rather than the full-suite figure; my T6 extends that baseline to the **full** suite (34/320) and confirms the same two pre-existing failures. No claim of Cline's failed reproduction.

## 21. Baseline comparison

Method: `git archive 4887c66 | tar -x -C /tmp/ct_i6_base` (a pristine tree, repository untouched) with `node_modules` **symlinked** to the existing installation so both trees share one dependency state; the extracted tree contains no `src/v3/insight/` directory and 34 test files (HEAD: 39) [FACT].

| Metric | Pristine `4887c66` | HEAD `ea7ccc2` | Delta |
| --- | --- | --- | --- |
| Suites (full) | 34 (2 failed) | 39 (2 failed) | +5 (I6) |
| Tests (full) | 320 (1 failed) | 430 (1 failed) | +110 (I6) |
| Suites (v3) | 26 (1 failed) | 30 (1 failed) | +4 (I6) |
| Tests (v3) | 228 (1 failed) | 328 (1 failed) | +100 (I6) |
| Build | exit 0, 105 warnings / 26 files | exit 0, 105 warnings / 26 files | none |
| Failing tests | `App.test.js` (module resolution), `dr007…` (assertion) | the same two | none |

**Conclusion [FACT]:** the pre-existing failures are pre-existing by direct measurement, not by assertion; I6 adds only passing tests; the build introduces no new warning; no regression was introduced by I6.

## 22. Sensitivity/negative testing

**[FACT] Independent adversarial suite (verifier-written, run against the unmodified HEAD code copied to `/tmp`): 16/16 passed**, asserting: all fourteen states render distinctly with the zero marker only for `zero`; no_data never shows a zero result; unknown/malformed statuses never become zero or an answer; **byte-identical non-disclosing text across six failure modes**; non-disclosing copy never implies existence or non-existence; `evidence_line_item` offers no client route and no open control; the three resolvable kinds map to the correct ratified tools and input keys; provider-unavailable retains the deterministic result, shows the evidence, names the gap and fabricates nothing; replay is informational with no idempotency detail; rejected reads yield generic non-technical text with no stack/secret/infrastructure leakage; `null`/`{}`/`{conversations:null}`/`{conversations:undefined}`/`[]` bodies degrade to empty states without crashing; a foreign conversation yields only the generic failure text; the workspace states privacy and never implies shared access.

**[FACT] Mutation sensitivity against the shipped tests** (mutations applied only to the `/tmp` copy; the authoritative checkout was never modified; each file was restored and the restoration verified):

| Mutation | Detected? | Caught by |
| --- | --- | --- |
| **M1** `answerIsZero` returns true for everything but `error` (breaks `no_data ≠ zero`) | **28 failures** | "answerIsZero is true for `zero` only", "an unknown state is never presented as an answer or as zero", "state success renders its own label and never a false zero", … |
| **M2** every resolution failure presented as success | **5 failures** | "a not_authorized outcome is non-disclosing", "a no_data outcome is non-disclosing", "a invalid_input outcome is non-disclosing", … |
| **M3** a client-side route guessed for `evidence_line_item` | **2 failures** | "evidence_line_item has no ratified by-identifier lookup and is not guessed", "an unresolvable kind is offered no client-side route at all" |
| **M4** `<ProtectedRoute>` removed from the `/insight` route | **1 failure** | "the route is wired to InsightPage inside ProtectedRoute + the org guard + the v3 shell" |
| **M5** `not_authorized` given a distinguishing ("this resource exists") message | **inert — not a gap** | See A-2: the component renders the shared constant, so the mutation cannot alter the UI; the same change *would* be caught if it ever reached rendering, because the tests assert the rendered constant's body |
| **M6** raw `error.message` surfaced to the user | **1 failure** | "a failed question is reported without disclosing anything and keeps the draft" |
| **M7** one ratified answer state removed | **1 failure** | "covers exactly the fourteen ratified states" |

Six of seven mutations are detected by the shipped tests, including the two highest-risk invariants (`no_data ≠ zero`, non-disclosing reference failures) and the authentication guard. M5 is reported as **inert rather than a sensitivity gap** — an important distinction I verified by reading the consumer, not by assuming.

## 23. I7/I8 scope audit

**[FACT] No scope violation.** The I6 change set contains **no** retention, deletion, export/download, privacy-policy, residency, provider-retention, billing, pricing, credit, entitlement, payment-provider, SLO-enforcement or backup/recovery implementation: those terms appear **only in the report document's non-authorization narrative** (0 occurrences in frontend source — the only frontend hits for `billing`/`credit` are pre-existing context lines belonging to the existing `/billing` route and the `FiCreditCard` icon mapping). `stripe`, `vercel` and `netlify` appear 0 times anywhere in the diff. There is no export/download control, no delete action and no account/data-request surface. `tokens_used`, `cost` and `audit_record_id` appear only inside a test fixture that mirrors the backend response shape, with **0** UI references (§19 O-6/O-8). No new Insight API, endpoint, package, or dependency was added (`package.json` unchanged).

## 24. Production boundary

**[FACT] No production deployment occurred and none was performed by the verifier.** The change set touches no deployment configuration (no Vercel/Netlify/CI-CD files, no environment configuration, no Docker or hosting manifests); the build was executed locally only, its output is git-ignored, and the build directory was removed from the checkout afterwards. The remote `github/p8-release-reconciled` contains the two I6 commits plus this report — a source push, not a deployment. The Master Specification remains unchanged, so nothing in I6 or in this report constitutes PO closure or a production authorization.

## 25. Blockers

**None.** No material PO requirement was found unsatisfied; no security/authorization weakening; no new API or endpoint; no I1–I4 or I5 contract change; no I7/I8 scope violation; no new regression; no new build warning. The two full-suite failures are pre-existing and unrelated to Insight (proven against the pristine tree).

## 26. Nonblocking observations

All are recorded as **[NB]**; the four marked **[PO]** require a product/PO decision but do **not** make I6 non-compliant.

1. **[PO] `evidence_line_item` resolvability.** Compliant today (§10). Making it openable would require a new or widened I3 tool — beyond I6's authorization ("no new Insight APIs unless an actual contract gap is demonstrated and separately authorized"). No remediation is proposed. Independently matches Cline's O-1.
2. **[PO] Consultant / internal-staff entry point.** The PO record contains no I6 requirement for it; the implementation correctly scopes Insight to the authenticated customer workspace and routes other actor types to their own workspaces. Any future consultant view is a product decision requiring a new authorization. Matches Cline's O-2.
3. **[PO] `org_viewer` execution rights.** Not an I6 decision; the UI follows the backend authorization contract and invents no role rule. Any stricter rule is an I2/I4 backend change outside I6. Matches Cline's O-3.
4. **[PO] Pagination.** The UI inherits backend defaults with no paging controls; **messages are ordered ascending and finite at 200**, so a conversation beyond 200 messages displays the *oldest* 200 and hides the newest transcript entries (while the newest 50 interactions remain visible in the answers section). Conversations and interactions are newest-first and finite at 50. Nothing in the PO I6 scope requires pagination; the backend already exposes `limit`/`offset`. If the PO wants paging — or newest-first message windows — that is a bounded follow-on decision. Matches Cline's O-4 with the truncation direction made explicit.
5. **[NB] Narration appears twice for a freshly asked interaction** (transcript message + answer panel); historical rows deliberately point at the transcript instead. Faithful to the I4 contract; de-duplication is a PO presentation choice. Matches Cline's O-5.
6. **[NB] No automated accessibility assertions** (`jest-axe` not in the project and correctly not added); accessibility is covered by assertion-level tests plus this static/manual verification. Matches Cline's O-9.
7. **[NB] `tokens_used`/`cost` and `audit_record_id` are not surfaced** — correct per §15.4 and the PO scope; fixtures only. Matches Cline's O-6/O-8.
8. **[NB] No conversation deep-link** — not required by the PO; adding one would touch routing behaviour beyond I6-2. Matches Cline's O-7.
9. **[NB] A-1 (report integrity):** the I6 report and the authorization text both record the non-existent digest `09e23151…c9d3a`; the real object is `09e23150…3091`. A docs-only correction is advisable so the permanent record is unambiguous. Not made here (§29).
10. **[NB] A-5 (environment dependency):** the frontend suite requires the documented `node_modules/canvas` disablement (git-ignored, no repository change); my evidence, like Cline's, was obtained in that state.

## 27. Final verdict

```
I6 VERIFIED PASS
```

Independently established against `ea7ccc2` (implementation `09e231503703895ebeec637e846cac6ce8523091`), from the PO decision record's I6 sections and authorization boundary:

* **I6-1/I6-2** — `/insight` exists inside the authenticated customer workspace using the existing v3 architecture (`ProtectedRoute → RoleRoute requireOrg → V3Layout`), is not publicly reachable (`/insight` absent from the 18 public prefixes; the public assistant returns `null` off-prefix), and the navigation change is one added customer link plus one icon mapping — additive and bounded, with no redesign.
* **I6-3** — creator-private conversation list, conversation view, current message history, start and continue, with explicit loading/empty/error handling; privacy is stated in the UI and no shared-access impression is created; no client-side authorization exists.
* **I6-4** — references are displayed as provenance locators with an explicit "locators, not access" statement; resolution always re-authorizes through the ratified I3 tool surface with exactly matching input keys; every failure mode is non-disclosing **by construction** (byte-identical text verified across a thrown 404, `not_authorized`, `no_data`, `invalid_input`, `provider_unavailable`, `error`); `evidence_line_item` is a compliant unopenable locator (no ratified tool accepts its id).
* **I6-5** — the complete fourteen-state I4 vocabulary is present and rendered distinctly; **`no_data` is never rendered as `zero`** (machine-checkable marker plus independent probe); unknown states never become zero or an answer.
* **I6-6** — provider unavailability retains the deterministic result and its tool evidence, names the narration gap, distinguishes it from CarbonTally data, and fabricates nothing.
* **I6-7** — initial empty, loading, no-data, clarification, unauthorized/hidden-resource, provider-unavailable and general-error states all exist and are distinct; errors are generic and leak no existence, stack, infrastructure or provider detail.
* **I6-8** — `replayed=true` is informational only; no new lifecycle model; no internal idempotency detail exposed.
* **I6-9** — no public FAQ reuse; no public Insight access.
* **I6-10** — keyboard-operable, labelled, focus-managed, semantic controls; status never colour-only; responsive breakpoints consistent with the existing v3 house style; substantial automated tests for the major states; no new framework added.
* **Boundary** — no backend authorization change, **no new API** (all seven endpoints pre-exist; backend diff 0 files), no I3/I4 semantic change, no shared/private data exposure, no billing, no retention/export, no public access, and no I5 change (20,000-character default untouched; no clamp added or removed).
* **Regression** — full suite at HEAD `39 suites / 430 tests` with `1 failed test` in `2 failed suites`, **identical to the pristine baseline's same two failures** (full-suite baseline `34 / 320`, `1 failed`); the delta is exactly the +5 suites / +110 I6 tests; build exit 0 with no I6 warning; my independent adversarial probe 16/16; six of seven meaningful mutations caught by the shipped tests, the seventh proven inert.

No blocker exists. Ten nonblocking items are recorded, four of which are product/PO decisions (evidence-line-item resolvability, consultant access, viewer execution rights, pagination) and six of which are informational — including one documentation-accuracy item (A-1: the recorded implementation SHA does not exist) that concerns the permanent record rather than the code.

**This report does not declare PO closure, does not modify the Master Specification, and does not authorize or begin I7 or I8. No remediation is authorized or performed. STOP.**

**I6 VERIFIED PASS — READY FOR PO CLOSURE**
