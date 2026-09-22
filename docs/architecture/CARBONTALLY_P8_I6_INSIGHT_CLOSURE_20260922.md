# CARBONTALLY P8 I6 — PO CLOSURE RECORD (2026-09-22)

| Item | Value |
| --- | --- |
| **Phase** | 8 |
| **Stage** | **I6 — UI** (CarbonTally Insight) |
| **Verification ID** | `P8-I6-OHD-VERIFY-20260922-01` |
| **I6 status** | **`CLOSED — VERIFIED PASS`** |
| Verified implementation revision | `ea7ccc28be3756ec9c5e569a24d36c5811752c4d` (`ea7ccc2`) |
| Corrected implementation commit | `09e231503703895ebeec637e846cac6ce8523091` (`09e2315`) |
| Implementation baseline | `4887c668ac618cff5974bc510b355a6a6c84e149` (`4887c66`, I5 closure) |
| I6 documentation/report revision | `ea7ccc2` (`docs/implementation/phase8/CT-P8-I6-INSIGHT-UI-20260922.md`) |
| OHD verification revision | `4acc249844860b0746969b2be9a106370a1dca4c` (`4acc249`) |
| OHD verification report | `docs/implementation/phase8/CT-P8-I6-OHD-VERIFICATION-20260922.md` |
| OHD final verdict | **`I6 VERIFIED PASS — READY FOR PO CLOSURE`** |
| Cline implementation report | `docs/implementation/phase8/CT-P8-I6-INSIGHT-UI-20260922.md` |
| Closure date | `2026-09-22` |
| Closure authority | **Product Owner** (this is the PO closure decision, recorded here; OHD verified and did not close) |

---

## A. Stage identity

* **Phase:** 8 (CarbonTally Insight).
* **Stage:** **I6 — UI**.
* **Verification ID:** `P8-I6-OHD-VERIFY-20260922-01`, issued for the independent verification of the I6 UI implementation.
* **Preceding stage:** I5 — Context, `CLOSED — VERIFIED PASS` (`docs/architecture/CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md`).

## B. Authorization

I6 was **separately authorized** under the existing Phase 8 governance: the Product Owner's I6 implementation authorization of 2026-09-22, issued against the durable decision record

`docs/architecture/CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md`

(§5 — I6 decisions I6-1…I6-10 and the I6 authorization boundary; §3.1–§3.7 global decisions; §14 explicit non-authorizations), on the basis of the I5 closure of 2026-09-22 and the readiness audit's finding that I6 was `READY WITH PO DECISIONS` with **no backend contract gap**.

**This document records PO closure only.** It authorizes no implementation, no remediation and no further stage. It is a documentation/status record, exactly as the I4 and I5 closure records were.

## C. Verified implementation

| Item | Commit |
| --- | --- |
| **Corrected implementation commit** | `09e231503703895ebeec637e846cac6ce8523091` (`09e2315`) — 18 files changed, **+3,678 / −0** |
| **I6 documentation / report revision** | `ea7ccc28be3756ec9c5e569a24d36c5811752c4d` (`ea7ccc2`) |
| **OHD verification commit** | `4acc249844860b0746969b2be9a106370a1dca4c` (`4acc249`) |
| **OHD verdict** | **`I6 VERIFIED PASS`** |

**[FACT] A-1 correction (documentation only).** The digest originally recorded in the I6 implementation report — `09e2315141a4df6fc90e78f70d53d74cbd0c9d3a` — **is not an object in this repository** (`git cat-file -t` → `could not get object info`). The actual implementation commit is `09e231503703895ebeec637e846cac6ce8523091`, whose parent is the implementation baseline `4887c668ac618cff5974bc510b355a6a6c84e149` and which is itself the parent of the documentation revision `ea7ccc2` (`4887c66 → 09e2315 → ea7ccc2 → 4acc249`). The chain, the abbreviated form (`09e2315`) and the 18-file / +3,678 / −0 footprint were independently confirmed before this closure. The erroneous digest was corrected **in the report only**, at this closure, as a documentation-accuracy fix; **the implementation represented by that commit was not modified** (0 implementation files changed by this closure).

## D. Verification evidence

The Product Owner closed I6 on the following independently established basis, summarised from `docs/implementation/phase8/CT-P8-I6-OHD-VERIFICATION-20260922.md` (`P8-I6-OHD-VERIFY-20260922-01`, OHD, 2026-09-22, verdict **`I6 VERIFIED PASS`**). Nothing below claims more than that report establishes.

1. **Authenticated `/insight` entry point** — the route exists inside the authenticated customer workspace using the existing v3 architecture (`ProtectedRoute → RoleRoute requireOrg → V3Layout`), with no new authentication mechanism, and the navigation change is one added customer link plus one icon mapping (additive, no redesign).
2. **No public reachability** — `/insight` is absent from the 18 `PUBLIC_ROUTE_PREFIXES`, and the public assistant returns `null` off-prefix, so no public or assistant path reaches Insight; the public FAQ assistant was not reused (I6-9).
3. **Creator-private conversation behaviour** — conversation list, conversation view, current message history and start/continue are implemented with explicit loading/empty/error handling; the UI states that conversations are private to the caller, creates no shared-access impression, holds no client-side authorization, and renders a generic failure (no existence disclosure) for a foreign or inaccessible conversation.
4. **Existing seven endpoints / no new backend API** — every read and write uses a pre-existing, closed I1–I4 endpoint (conversations list/create, messages list, interactions create/list/get, the ratified I3 tool invocation). The backend footprint of the change is **0 files**: no API, service, domain, repository, SQL, migration, schema, RLS or authorization change.
5. **The complete fourteen-state I4 `AnswerStatus` vocabulary** is present and rendered distinctly, including the states the current orchestration does not reach in production; the I3 `ToolStatus` vocabulary remains separate and is never merged.
6. **`no_data` is distinct from `zero`** — verified three ways (the `answerIsZero()` guard, the machine-checkable `data-answer-zero` marker, and an independent probe rendering all fourteen states), with `no_data` never presented as a zero result and unknown states never presented as an answer or as zero.
7. **Reference resolver behaviour and non-disclosure** — references are presented as provenance locators with an explicit "locators, not access" statement; resolution always re-authorizes through the ratified I3 tool surface with input keys matching the tool specs exactly; every failure mode (thrown 404, `not_authorized`, `no_data`, `invalid_input`, `provider_unavailable`, `error`) renders **byte-identical** non-disclosing text, and an unresolvable kind is offered no open control at all.
8. **Provider-unavailable deterministic-result behaviour** — the deterministic result and its tool evidence remain visible, the narration gap is named explicitly and distinguished from CarbonTally data, and no narration is fabricated.
9. **Preservation of I5 and I1–I4 contracts** — 0 files changed under `backend/`, `supabase/`, `prisma/` or `docs/architecture/` by the implementation; I5 is byte-identical and not reopened (20,000-character default untouched, no clamp added or removed, no summarization/compaction/cross-conversation memory/RAG/embeddings/vector search/LangChain); I1, I2, I3 and I4 contracts are unchanged.
10. **Adversarial probe `16 / 16`** — the verifier's own independent suite (written outside the repository, on an isolated `/tmp` copy) passed 16/16 against the unmodified implementation, including the non-disclosure, privacy-wording, error-leakage and reference-resolution assertions.
11. **I6-focused tests `110 / 110`** — 5 suites, 110 tests, exit 0; independently reproduced at the verified revision.
12. **Build success** — `react-scripts build` exit 0 ("Compiled with warnings"); the pre-existing warning profile is identical to the pristine baseline (no I6 warning).
13. **Baseline comparison confirming the two unrelated pre-existing failures** — at the verified revision the full suite is `39 suites / 430 tests` with `1 failed test` in `2 failed suites`, and on the pristine `4887c66` tree it is `34 suites / 320 tests` with the **same** `1 failed test` in the same 2 failed suites (`src/App.test.js` — `Cannot find module 'react-router/dom'`; `src/v3/__tests__/dr007-investor-display-fixes.test.jsx` — "Mapped activity" vs "Natural gas"). The delta is exactly the additive `+5 suites / +110 I6 tests`, with **0 pre-existing tests modified, skipped or deleted**.
14. **No blocker** — the verifier recorded **no blocker**: no material PO requirement unsatisfied, no security or authorization weakening, no new API, no I1–I5 contract change, no I7/I8 scope violation, no new regression and no new build warning.
15. **No production boundary crossed** — no deployment occurred; no deployment configuration was touched; the push is a source push, not a deployment.

## E. OHD observations — recorded as NONBLOCKING

All five are recorded by the Product Owner as **nonblocking** and **accepted without remediation**. None is converted into implementation work by this closure.

| # | Observation (as established by OHD) | PO disposition |
| --- | --- | --- |
| **A-1** | The I6 implementation report recorded a full SHA (`09e2315141a4df6fc90e78f70d53d74cbd0c9d3a`) that is **not an object in this repository**; the real implementation commit is `09e231503703895ebeec637e846cac6ce8523091` (`09e2315`). A record-integrity defect in the documentation, not a code defect. | **NONBLOCKING — ACCEPTED and CORRECTED IN DOCUMENTATION ONLY.** The digest was corrected in the report at this closure (§C). No implementation, test or contract was changed. |
| **A-2** | The non-disclosure payload returned by `resolutionPresentation()` is **dead data**: only its `=== null` discriminator is consumed, and the rendered note is a single shared constant. The property holds by construction, but the producer's return object is unused. | **NONBLOCKING — ACCEPTED.** This strengthens the non-disclosure guarantee rather than weakening it. Recorded so that a change which starts rendering that payload is recognised as the point where the property would become mapping-dependent; the shipped tests pin the rendered constant. No remediation. |
| **A-3** | The routing test (`insight-routing.test.jsx`) is **source-text based** (it regex-matches `App.js`/`V3Layout.jsx`) rather than rendering the route. | **NONBLOCKING — ACCEPTED.** Independently verified as **effective**: the verifier's mutation that removed `<ProtectedRoute>` from the `/insight` route was **caught** by it. Recorded as a method note, not a defect. No remediation. |
| **A-4** | `projectEvidenceRows` renders **every key the backend returns** (only labels are mapped client-side); the I3 tools' `output_fields` allowlists remain the exposure boundary, and the UI performs no second allowlist. | **NONBLOCKING — ACCEPTED.** The I3 allowlist remains authoritative and unchanged; **no exposure exists today**. Recorded so that a future change to a tool's `output_fields` is recognised as the point where exposure would be introduced. No remediation, and **no client-side allowlist is to be added by this closure**. |
| **A-5** | Verification evidence depends on the documented **git-ignored `node_modules/canvas` disablement** (jsdom 16 cannot load the unbuilt optional native module); `node_modules` is untracked, so no repository content changed. | **NONBLOCKING — ACCEPTED.** The dependency is disclosed, reproducible and outside version control; the working tree remained clean. No repository or environment change is authorized by this closure. |

**Other OHD observations preserved as nonblocking** (recorded, not converted into work): duplicated narration for a freshly asked interaction is **by design** (the I4 contract persists the narration as an `insight` message *and* returns `narration_text`; historical rows point at the transcript instead); **`jest-axe` was not added because it was outside authorization** (accessibility is covered by assertion-level tests plus verification; adding an accessibility framework remains a separate decision); **`tokens_used`, `cost` and `audit_record_id` are not surfaced** (truthful omission — no fabricated usage/cost, no internal audit identity exposed); **ignored build artifacts remain clean** (0 tracked files under `frontend/build/`); **no conversation deep-link** exists and none is required.

## F. Accepted PO follow-ups — future decision / authorization items (not I6 blockers)

These four items are recorded as **future PO decision/authorization items**. They do **not** make I6 non-compliant, they are **not** I6 blockers, and **no work on them is authorized by this closure**.

1. **`evidence_line_item` resolvability.**
   `evidence_line_item` **remains an unopenable provenance locator** under the current ratified I3 tool catalogue: no ratified tool accepts an evidence-line-item id as input (`report_lookup` → `report_id`; `report_version_lookup` → `version_id`/`report_id`+`version_number`; `report_evidence_lookup` → `report_version_id`; `calculation_snapshot_lookup` → `snapshot_id`). This is **compliant** with I6-4, which requires locator semantics and a non-disclosing state when resolution is unavailable, not universal openability. Making it directly openable would require a **new or widened I3 tool** — a separate PO decision. **No such tool is authorized by this closure.**
2. **Consultant / internal-staff entry point.**
   Insight for consultants or internal CarbonTally staff is **not part of the I6 customer-workspace authorization** (the PO record contains no such I6 requirement; the implementation scopes Insight to the authenticated customer workspace and routes other actor types to their own workspaces). **No consultant or internal-staff Insight UI is to be added as part of this closure**, and any future such surface requires **separate authorization**.
3. **`org_viewer` execution rights.**
   I6 **does not invent or modify role execution rights**. Existing **I2/I4 authorization remains authoritative**: the UI sends the request and renders whatever the backend authorizes. Whether an `org_viewer` may execute interactions is an existing authorization-contract question. **No permission change is authorized by this closure.**
4. **Pagination.**
   I6 **remains bounded by the existing backend limits** (conversations and interactions newest-first, finite at 50; messages ascending, finite at 200 — so a conversation longer than 200 messages displays the oldest 200 transcript entries while the newest 50 interactions remain visible in the answers section). **No pagination redesign and no backend change is authorized by this closure**; the backend already exposes `limit`/`offset` should the PO later require paging or newest-first message windows.

## G. Final stage status

# `I6 — UI: CLOSED — VERIFIED PASS`

* **No remediation was required** for I6, and **none was performed** by this closure.
* **No blocker remains** for I6 closure: the OHD verdict is `I6 VERIFIED PASS` with **no blockers**, and all remaining observations are nonblocking (§E) or future PO decisions (§F).
* **I7 is NOT AUTHORIZED by this closure.**
* **I8 is NOT AUTHORIZED by this closure.**
* **Production deployment is NOT AUTHORIZED by this closure.**

---

## 1. Closure confirmations

* **No remediation was required** for I6, and none was performed: OHD's verdict is `I6 VERIFIED PASS` with **no blockers**.
* **No implementation file was changed by this closure.** The closure is **documentation only**: the I6 implementation report received a **SHA correction and a status note** (§C), this record was created, and the Master Specification received a **status-only** update. No application code, test, contract, schema, migration, configuration, frontend, RLS, billing or provider integration was modified.
* The I6 contracts closed under this record are those verified by OHD at `4acc249` against the implementation commit `09e2315` and the documented revision `ea7ccc2`.
* Independent verification was performed by **OHD**, not by Cline; Cline does not claim verification.
* **No OHD observation was converted into implementation work**, and no PO follow-up (§F) was started.

## 2. Authorization boundary after this closure

* **I6 is `CLOSED — VERIFIED PASS`.**
* **I7** remains **NOT AUTHORIZED** (external/legal/privacy decisions outstanding).
* **I8** remains **NOT AUTHORIZED** as a full stage (commercial/operational decisions outstanding).
* **Production deployment** remains **NOT AUTHORIZED**.

This closure does **not** authorize: any further I6 work; I7 implementation; I8 implementation; production deployment; new I3 tools or widened tool inputs (including `evidence_line_item` resolvability); new APIs or endpoints; consultant or internal-staff Insight surfaces; `org_viewer` execution-right changes; pagination or backend limit changes; payment-provider integration; pricing changes; retention or export changes; new permissions, roles or personas; cross-conversation memory; persistent summaries; summarization or compaction; RAG, embeddings, vector search or LangChain; autonomous actions.

## 3. Evidence and traceability

| Evidence | Repository path | Commit |
| --- | --- | --- |
| PO I5–I8 decision record (I6-1…I6-10 + authorization boundary) | `docs/architecture/CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` | `43f572d` |
| I5 closure (baseline for I6) | `docs/architecture/CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md` | `4887c66` |
| I6–I8 pre-authorization readiness audit (`READY WITH PO DECISIONS`, no contract gap) | `docs/implementation/phase8/CT-P8-I5-I8-PREAUTHORIZATION-READINESS-AUDIT-20260921.md` | `fef4e70` |
| **Cline I6 implementation** (code + tests) | `frontend/src/v3/insight/**`, `frontend/src/v3/api.js`, `frontend/src/App.js`, `frontend/src/v3/components/V3Layout.jsx`, `frontend/src/v3/components/ui/Icon.jsx` | **`09e2315`** |
| Cline I6 implementation report (SHA corrected at this closure) | `docs/implementation/phase8/CT-P8-I6-INSIGHT-UI-20260922.md` | `ea7ccc2` (+ this closure) |
| **OHD I6 independent verification (`I6 VERIFIED PASS`)** | `docs/implementation/phase8/CT-P8-I6-OHD-VERIFICATION-20260922.md` | **`4acc249`** |
| Master Specification I6 status update (factual/status only) | `docs/architecture/CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION_v1.1_20260921.md` | this commit |
| **This PO closure record** | `docs/architecture/CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` | this commit |
| I4 closure (unchanged) | `docs/architecture/CARBONTALLY_P8_I4_INSIGHT_CLOSURE_20260921.md` | `725f9f8` |

## 4. What this closure does not do

* It does not authorize, prepare or imply any I7 or I8 implementation, and it does not authorize production deployment.
* It does not alter the I6 architecture, the I1/I2 authorization model, the closed I3 tool catalogue or `ToolStatus`, the I4 interaction/answer/audit contracts, the I5 context contract, `public.ai_content_history`, or the canonical `public.audit_trail` ledger.
* It does not remediate, withdraw or downgrade any OHD observation: A-1 is accepted and corrected in documentation only; A-2…A-5 and the remaining nonblocking observations are recorded as accepted without remediation.
* It does not decide any of the four PO follow-ups (§F); they remain future decision/authorization items.
* The Master Specification was updated **only factually, for I6 status**: the I6 row in the §3.1 stage-state table, the I6 stage status line, and one factual status note adjacent to the I5 status note. No technical requirement, no I6 scope statement and no I7/I8 decision was rewritten; historical `NOT AUTHORIZED` statements elsewhere in the specification (for example the governance note written at I3 closure) are left **as written** and are superseded for I6's *status* by §3.1 and by this closure record.




