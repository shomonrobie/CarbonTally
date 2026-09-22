# CT-P8 — PO DECISION INVENTORY / HISTORICAL CONTEXT AUDIT (2026-09-22)

**Kind:** Read-only discovery and reconciliation audit. **Not** an authorization.
**Date:** 2026-09-22 · **Author:** Cline (implementation agent) — this document makes **no** PO decision, closes **no** stage, and authorizes **no** work.
**Purpose:** identify every currently unresolved Product Owner decision that may need to be made next, and prevent re-opening decisions that are already closed.

**Repository / release authority**

| Item | Value |
| --- | --- |
| Authoritative checkout | `/home/shomonrobie/ct_93d5cdd` (per `docs/verification/CT-P8-RELEASE-REPOSITORY-TOPOLOGY-RECONCILIATION-20260921.md` §12) |
| Branch | `p8-release-reconciled` |
| Authoritative remote | `github` → `https://github.com/shomonrobie/CarbonTally.git` |
| **Starting HEAD** | `5d5f7ed94c5821894e8eac6d05ad9af83138746e` |
| Working tree | clean (`git status --porcelain` empty) |
| Remote alignment at start | `HEAD...github/p8-release-reconciled` = `0 0` |
| **Ending HEAD** | see §I (filled at commit time) |
| Report path | `docs/architecture/CT-P8-PO-DECISION-INVENTORY-20260922.md` |

**Method.** Read-only inspection of the Phase 8 governance corpus: the Master Specification v1.1, the I2/I3/I4/I5/I6 closure records, the I5–I8 PO decision and authorization record, the I5–I8 pre-authorization readiness audit, the I5/I6 OHD verification reports, the I4 Q1 closure, the Source Evidence forensic report, the Source Evidence Viewer implementation report, the Source Evidence Viewer OHD verification report, the release repository topology reconciliation, and `CT-P8-SPEC-001`. Git history was used to establish what was subsequently resolved. Three OHD observations were re-checked against the current HEAD (§D.3, §H) rather than trusted as still current.

**No change of status.** Every status below is quoted from its authoritative record. Where an older document and a newer closure record disagree about *status*, both are quoted and the conflict is reported in §H — no status is rewritten here.

**Evidence classes** (readiness-audit convention): `VERIFIED` (code/test/runtime evidence or a signed-off closure record) · `DOCUMENTED` (stated in an authoritative record, not independently re-traced) · `INFERRED` (reasoned from ≥2 documents) · `AMBIGUOUS` (documents conflict or are stale) · `UNKNOWN`.

## 0. Status reconciliation note — PO closure of 2026-09-22 (documentation update)

This inventory was written on 2026-09-22 **before** the Product Owner's closure decision for the source-evidence capability. That decision has since been recorded at

`docs/architecture/CT-P8-PO-DECISION-DISPOSITION-CLOSURE-DECISIOIN-FOR-SOURCE-EVIDENCE-VIEWER-AND-INSIGHT-20260922.md`

That record is the authoritative instrument for the statuses below. The sections that follow remain the **pre-closure inventory snapshot** and are retained as historical context (the same convention the Phase 8 closures use: historical text is left as written and superseded for status).

| Item | Authoritative status after the PO decision |
| --- | --- |
| Source Evidence Viewer + Insight Evidence Navigation | **`CLOSED — VERIFIED PASS WITH NON-BLOCKING OBSERVATIONS`** (implementation `999e4fb`; OHD `5d5f7ed`, verdict `PASS WITH NON-BLOCKING OBSERVATIONS`, verification ID `OHD-P8-SEV-20260922`) |
| C-01 | `RATIFIED FOR CURRENT RELEASE; FUTURE SECURITY REVIEW DEFERRED` — **no remediation authorized** |
| C-02 | `DEFERRED — SECURITY POLICY` — **no code change authorized** |
| C-03 | `DEFERRED — AUDIT/PROVENANCE POLICY` — **no export/reporting remediation authorized** |
| C-04 | `ACCEPTED` — no remediation authorized |
| C-05 | `RATIFIED` — no implementation change authorized |
| C-06 | **`CLOSED`** by the PO decision |
| I6 | `CLOSED — VERIFIED PASS` (unchanged; **not** reopened) |
| I7 | `NOT AUTHORIZED / NOT READY` (unchanged) |
| I8 | `NOT AUTHORIZED AS FULL STAGE` (unchanged; the I8-A principles remain intact) |
| Production deployment | `NOT AUTHORIZED` (unchanged) |
| New implementation arising from the closure | **NONE** |

Consequences for this inventory:

* six items (C-01…C-06) are **disposed of** by the PO decision — C-01, C-04 and C-05 ratified/accepted; C-02 and C-03 deferred by explicit PO decision with no remediation authorized; C-06 closed;
* the remaining **26 items (C-07…C-32) remain open exactly as recorded**; the deferred product/security/audit items the PO re-listed (C-08…C-12, C-13…C-17, C-18…C-24) are unchanged;
* **no remediation of C-01/C-02/C-03 is authorized**, so §F.1's remediation branch is not taken and no implementation follows from the closure;
* the pre-closure statements in §A.2, §A.3, §A.8, §B.7, §C.1, §D.3, §F.1 and §H.1 are superseded **for status only** by this note; their evidence findings stand and were not re-opened;
* C-32 (durability of capability-level PO authorizations) is partly resolved in practice by the fact that the closure decision is itself a committed PO record; the underlying 2026-09-22 authorization text remains cited by reference only.

**Nothing in this note authorizes implementation.** It records a PO documentation decision only.

---

## A. Executive status

### A.1 Closed

| Stage / item | Status | Authority |
| --- | --- | --- |
| D1 Discovery | `COMPLETE` | Master Spec §3.1 |
| D2 PO ratification | `RATIFIED` | Master Spec §3.1; `CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` |
| I1 Persistent foundation | `IMPLEMENTED / INCORPORATED INTO VERIFIED BASELINE` | Master Spec §3.1 (I1/I2 records) |
| I2 Authorization & visibility | `CLOSED — VERIFIED PASS` | Master Spec §3.1, §3.2 (verified revision `177dff5`) |
| I3 Controlled read-only tools | `CLOSED — VERIFIED PASS` | Master Spec §3.1, §3.3, §48.1 (remediation `651f8c1`, OHD `7faaa57`) |
| I4 AI interaction + canonical audit | `CLOSED — VERIFIED PASS` | Master Spec §3.1, §48.5; `CARBONTALLY_P8_I4_INSIGHT_CLOSURE_20260921.md` (`725f9f8`) |
| I5 Context | `CLOSED — VERIFIED PASS` | Master Spec §3.1, §48.5; `CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md` (`4887c66`) |
| I6 UI | `CLOSED — VERIFIED PASS` | Master Spec §3.1, §48.5; `CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` (`67d399f`) |
| I4 Q1 (`ai_content_history`) | `CLOSED — OPTION C` | `CARBONTALLY_P8_I4_Q1_AI_CONTENT_HISTORY_CLOSURE_20260921.md`; re-affirmed by I7-C |
| I5 O-1 (context budget clamp) | `CLOSED` — 20,000 default, **no** hard clamp | `CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md` §2 |
| Release repository authority | `ESTABLISHED` | Topology reconciliation §12 (the *surrounding* divergence is **not** closed — §C.6) |

### A.2 Implemented but not yet independently verified

**None.** No Phase 8 item is in the "implemented, awaiting independent verification" state at this HEAD. The most recent implementation (Source Evidence Viewer, `999e4fb`) has been independently verified (A.3).

### A.3 Verified and PO-closed (2026-09-22)

> **Updated by the PO closure decision** — see §0. The status below is the authoritative post-decision status; the pre-closure wording is recorded in §0 and in the PO decision itself.

| Item | Implementation | Independent verification | Status |
| --- | --- | --- | --- |
| **Shared Source Evidence Viewer + Insight evidence handoff** (incl. the `source_page` provenance correction) | `999e4fb` (documentation revision `de021ab`) | `docs/verification/phase8/CT-P8-SOURCE-EVIDENCE-VIEWER-OHD-VERIFICATION-20260922.md`, commit `5d5f7ed`, verdict **`PASS WITH NON-BLOCKING OBSERVATIONS`** (`OHD-P8-SEV-20260922`) | **`CLOSED — VERIFIED PASS WITH NON-BLOCKING OBSERVATIONS`** — PO closure 2026-09-22, `docs/architecture/CT-P8-PO-DECISION-DISPOSITION-CLOSURE-DECISIOIN-FOR-SOURCE-EVIDENCE-VIEWER-AND-INSIGHT-20260922.md`. The accepted observations are not implementation blockers; **no remediation is authorized**. |

### A.4 In progress

**None.** No Phase 8 stage is in an open implementation state.

### A.5 Blocked

**None** technically. The readiness audit records no technical blocker for I5/I6/I8 (`READY WITH PO DECISIONS`) and I7 as `NOT READY` because its parameter set is deliberately undecided — a decision gap, not a technical block. One non-blocking governance irregularity is recorded in §D.2/§H.4 (the Source Evidence Viewer authorization is cited only by reference).

### A.6 Deferred

* Master Spec **§42 "Explicit Deferred Capabilities"** — RAG; embeddings; vector databases; LangChain or another orchestration framework; unrestricted retrieval; autonomous actions; consultant Insight; auditor Insight; PE Insight; broad staff Insight; billing; retention enforcement; export; production hardening; report-lifecycle modification.
* I4 **Q12** (retention/deletion/export) and **Q13** (billing/credits) — deferred to I7 / I8 respectively (Master Spec §48.5).
* **Q1 future disposition** of `public.ai_content_history` — deferred indefinitely ("future disposition remains a separate PO decision", I7-C).
* I5 v1 accepted limitations (`CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md` §5): raw message text not injected (O-4); context metadata not persisted (would require an unauthorized migration); message-level history selection not implemented (I1 repository deliberately unmodified); sub-block budget overflow behaviour; integration-suite environment dependence.
* I6 **A-2…A-5** — accepted nonblocking, no remediation (`CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` §E); the four **§F** follow-ups remain future PO decision/authorization items.
* Source Evidence Viewer §15 — **date/amount discovery** ("why did I have 20K CO₂e on 2024-02-02?") is not implemented and is not faked; recorded as a deferred capability, not a defect.
* Master Spec **§41 "Open Product Decisions"** — several items remain open; inventoried in §C.5.

### A.7 Not authorized

I7 implementation · I8 implementation as a full stage (only I8-A *principles* are PO-approved) · production deployment · payment-provider integration · pricing/subscription/commercial-entitlement changes · retention periods · legal deletion policies · residency/subprocessor/privacy-notice decisions · new I3 tools or widened tool inputs · consultant / internal-staff / auditor / PE Insight surfaces · new personas, roles or permissions · cross-conversation memory · persistent AI summaries · summarization/compaction · RAG, embeddings, vector search, LangChain · autonomous actions.
(Authorities: I5–I8 PO record §11 and §14; I5 closure §7 and §9; I6 closure §2 and §4; Master Spec §42.)

### A.8 Genuine unresolved PO decisions

**32 inventoried items in §C**, of which **6 (C-01…C-06) have since been disposed of by the PO closure decision of 2026-09-22** and **26 remain open** — see §0. Groups (pre-closure): Source Evidence Viewer closure and residual policy (C-01…C-08), I6 accepted follow-ups (C-09…C-12), I7 prerequisites (C-13…C-17), I8 prerequisites (C-18…C-24), Master Spec §41 residuals and I5 v1 follow-ons (C-25…C-29), repository governance and record durability (C-30…C-32). Evidence quality per item is classified in §H.

---

## B. Historical PO decisions already resolved

Listed so that PO does not re-open them. Status is quoted from the authoritative record.

### B.1 Global Insight principles and boundaries (still binding)

| # | Decision | Status | Authoritative document | Section | Revision |
| --- | --- | --- | --- | --- | --- |
| B-01 | I2 authorization remains the sole authorization authority; context, UI state, stored references, summaries, tool results, audit records and LLM instructions never grant access; every protected read re-authorizes | `CLOSED` | `CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` | §3.1 | `43f572d` |
| B-02 | Deterministic CarbonTally data and domain services remain authoritative over conversation/summary/narration | `CLOSED` | same | §3.2 | `43f572d` |
| B-03 | Stored Insight references remain locators, never authorization grants; resolution passes through the authorization boundary | `CLOSED` | same | §3.3 | `43f572d` |
| B-04 | `public.audit_trail` is the canonical Insight audit ledger; no second ledger | `CLOSED` | same + Master Spec §48.5 Q2 | §3.4 | `43f572d` |
| B-05 | The four ratified I3 tools and `ToolStatus` remain unchanged; no new I3 tool | `CLOSED` | same | §3.5 | `43f572d` |
| B-06 | I4 interaction/tool-call/answer-state/audit-correlation/creator-private contracts remain the baseline; no I4 redesign | `CLOSED` | same | §3.6 | `43f572d` |
| B-07 | Provider attribution must be truthful; nullable `tokens_used`/`cost` acceptable; no fabricated usage/cost | `CLOSED` | same + Master Spec §48.5 Q14 | §3.7 | `43f572d` |
| B-08 | The mandatory release chain (PO authorization → implementation → OHD → PO closure → controlled deployment authorization → deployment → post-deployment verification); no stage reaches production because code exists | `CLOSED` | same; Master Spec §37 | §8 "Deployment" | `43f572d` |
| B-09 | Cross-cutting prerequisite for every remaining stage: per-request authorization via `authorize_insight_scope`, references as locators, `public.audit_trail` canonical | `VERIFIED` conclusion | `CT-P8-I5-I8-PREAUTHORIZATION-READINESS-AUDIT-20260921.md` | §28.7 | `fef4e70` |

### B.2 I4 pre-authorization decisions Q1–Q14 (2026-09-21)

Authoritative record: Master Spec **§48.5** "PO decision intake — Q1–Q14 and I4 authorisation (2026-09-21)"; Q1's own decision text in `CARBONTALLY_P8_I4_Q1_AI_CONTENT_HISTORY_CLOSURE_20260921.md`.

| # | Decision | Resolution |
| --- | --- | --- |
| Q1 | Dormant `ai_content_history` | `CLOSED — Option C`: retained unchanged, **outside I4**; no migration/rename/deletion/RLS/Prisma/app integration; future disposition deferred |
| Q2 | Canonical audit ledger | `public.audit_trail` via `infra/audit_logger.py` + `data/audit.py`; other ledgers not canonical |
| Q3 | Status vocabularies | I3 six-value `ToolStatus` unchanged; I4 keeps a separate fourteen-state answer vocabulary |
| Q4 | Raw question persistence | Persisted once in the I1 message layer; Layer 2 stores only a content hash (+ references/ids) |
| Q5 | Layer-2 mutability | Append-only/immutable after creation; corrections are new linked records |
| Q6 | Tool arguments/results | Allowlisted structured projections only; no raw payloads, secrets or unrestricted result content |
| Q7 | Interaction lifecycle | Owned by Layer 2 (I1 stays the conversation/message layer) |
| Q8 | Visibility | **Creator-private only**; no new shared visibility, personas or permissions |
| Q9 | Correlation | Immutable `interaction_id` with child `tool_call_id`s, correlatable to the canonical audit event |
| Q10 | Idempotency/retry | Bounded retry; no duplicate interaction identities or duplicate logical tool calls; truthful partial-failure state |
| Q11 | Provider unavailable | Degraded service, never fabrication; deterministic results preserved; `provider_unavailable` where provider work is required |
| Q12 | Retention/deletion/export | **Deferred to I7**; not implemented at I4 |
| Q13 | Billing/credits | **Deferred to I8**; not implemented at I4 |
| Q14 | Provider/evaluation/SLO | Existing provider abstraction only; truthful attribution; usage/cost may remain NULL; no evaluation platform, RAG, embeddings or orchestration framework |

### B.3 I5 — Context decisions (2026-09-21, `CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` §4)

| # | Decision | Status |
| --- | --- | --- |
| I5-1 | Bounded deterministic selection; current question first; current conversation before unrelated conversations; chronological ordering; most-recent relevant material within budget; **current-conversation context only**; no semantic/vector relevance engine | `CLOSED` |
| I5-2 | **No AI summarization/compaction** in initial I5; bounded selection/truncation instead; a future summarization capability requires a separate PO decision | `CLOSED` |
| I5-3 | Character-based context budget; **20,000-character** initial maximum; enforced before provider submission; configurable, not a scattered magic number; no token-counting library authorized | `CLOSED` |
| I5-4 | **No conversation summaries persisted**; no summary table/column authorized; deliberately avoids an I5→I7 persistence dependency | `CLOSED` |
| I5-5 | Context is never authoritative merely because it contains a reference; current authorized lookup wins; no autonomous correction of historical records | `CLOSED` |
| I5-6 | Bounded structured historical interaction/tool-result context only; no indiscriminate historical tool-payload injection; unrestricted replay not authorized | `CLOSED` |
| I5-7 | Canonical audit records are **not** conversational context; `public.audit_trail` not injected into LLM context | `CLOSED` |
| I5-8 | Empty context is normal; no fabricated context; absence of context must not become `zero` | `CLOSED` |
| I5-9 | Initial I5 is single-conversation scoped; no cross-conversation memory (a future capability needs a separate PO decision covering authorization, selection, privacy, retention, UX, export) | `CLOSED` |

### B.4 I5 — OHD observations disposed by PO closure (`CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md` §2–§3)

| # | Content | Disposition |
| --- | --- | --- |
| O-1 | Configurable context override had no upper clamp (a configured value above 20,000 produced a larger effective bound) | **PO DECISION — CLOSED**: 20,000 is the default, **not** an immutable hard ceiling; the effective maximum is the valid configured value; implementation must **not** be changed to add a clamp; a future PO decision may establish a hard ceiling |
| O-2 | Shipped unit tests assert the call boundary with fakes | `NONBLOCKING — VERIFIED THROUGH LIVE OHD TESTING` |
| O-3 | Cline's reported test counts derived from runner progress markers | `NONBLOCKING — INDEPENDENTLY CONFIRMED` |
| O-4 | I5 v1 excludes raw I1 message text (structured interaction history used instead) | `NONBLOCKING LIMITATION — ACCEPTED FOR I5 v1`; I5 must **not** be expanded to raw message text |
| O-5 | 500-character question truncation is pre-existing I4 behaviour | `NONBLOCKING — PRE-EXISTING I4 BEHAVIOR`; **not** to be remediated as part of I5 |
| O-6 | Ten initial OHD E2E failures were verifier-probe defects | `NONBLOCKING — VERIFIER PROBE ISSUE` |

### B.5 I6 — UI decisions and dispositions

Authoritative record: I5–I8 PO record **§5** (I6-1…I6-10 and the I6 authorization boundary), closed by `CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md`.

| # | Decision | Status |
| --- | --- | --- |
| I6-1 | Insight lives inside the **authenticated customer workspace** (existing v3 architecture); not the public FAQ assistant | `CLOSED` |
| I6-2 | A dedicated authenticated Insight route/workspace; route name per existing v3 conventions; **do not redesign global navigation** | `CLOSED` |
| I6-3 | Creator-private conversation list, conversation view, current interaction/message history, start/continue; **no shared conversation workspace authorized** | `CLOSED` |
| I6-4 | References displayed as evidence/provenance locators; UI must not imply possession grants access; resolution re-authorizes server-side; non-disclosing state when resolution is unavailable/unauthorized | `CLOSED` |
| I6-5 | The complete fourteen-state I4 answer vocabulary must be handled distinctly; `no_data` must never become `zero` | `CLOSED` |
| I6-6 | Provider-unavailable: show the deterministic result, name the narration gap, fabricate nothing, do not present provider failure as a data failure | `CLOSED` |
| I6-7 | Explicit empty / loading / no-data / clarification / unauthorized / provider-unavailable / error states; error wording must not disclose resource existence | `CLOSED` |
| I6-8 | Lifecycle/replay information optional but no internal implementation detail; `replayed=true` may be informational; **no new lifecycle model** | `CLOSED` |
| I6-9 | The public FAQ assistant is **not** the Insight UI; no reuse/integration in I6 | `CLOSED` |
| I6-10 | Follow existing responsive/accessibility conventions; acceptance = keyboard access, accessible labels, usable focus, responsive authenticated workspace, automated tests; no new external a11y framework | `CLOSED` |
| I6 boundary | I6 must not modify backend authorization, introduce new Insight APIs without a demonstrated+separately authorized contract gap, alter I3/I4 semantics, expose shared/private data, implement billing or retention/export, or introduce public Insight access | `AUTHORIZED` within that boundary (now `CLOSED — VERIFIED PASS`) |
| A-1 | I6 report recorded a non-existent implementation digest | **Accepted nonblocking**; corrected in the report (documentation only); implementation unchanged |
| A-2…A-5 | Further I6 observations | **Accepted nonblocking**, no remediation |

### B.6 I7 boundaries closed, I8 principles approved (I5–I8 PO record §6, §8)

| # | Decision | Status |
| --- | --- | --- |
| I7-A | Retention/export operations must respect the existing I2 authorization model | `CLOSED` |
| I7-B | Conversation transcripts and provider payloads do not become unrestricted audit payloads; `public.audit_trail` remains the canonical ledger | `CLOSED` |
| I7-C | Continue Q1: retain `public.ai_content_history` unchanged and **outside** I4; no migration/deletion/rename/integration; future disposition a separate PO decision | `CLOSED` |
| I7-D | I7 must respect the I4 append-only design; any future deletion/archive must account for interaction immutability, tool-call immutability, canonical audit retention, database triggers and conversation cascades; must not disable/bypass those controls | `CLOSED` |
| I8-A (rate limiting) | Bounded protection against user/organization abuse, endpoint bursts and provider overuse; reuse existing infrastructure; production thresholds subject to implementation/audit evidence and not to be invented as commercial policy | `CLOSED PRINCIPLE` |
| I8-A (observability) | Cover interaction correlation, authorization outcome, tool selection, tool success/failure, answer status, provider availability, latency, safe error category, rate limiting, identifiers; never log secrets, tokens, unrestricted customer content or provider payloads | `CLOSED PRINCIPLE` |
| I8-A (provider resilience) | Provider failure degrades safely; no fabricated provider response; deterministic results survive narration failure where possible | `CLOSED PRINCIPLE` |
| I8-A (deployment) | No Insight stage reaches production merely because implementation exists; the mandatory release chain applies | `CLOSED` |

### B.7 Stage closures and verified revisions

| Stage | Status | Implementation | OHD | PO closure |
| --- | --- | --- | --- | --- |
| I2 | `CLOSED — VERIFIED PASS` | `177dff5` | — | `CARBONTALLY_P8_I2_INSIGHT_CLOSURE.md` |
| I3 | `CLOSED — VERIFIED PASS` | remediation `651f8c1` | `7faaa57` | Master Spec §48.1 |
| I4 | `CLOSED — VERIFIED PASS` | `310a62a` | `6a4fda1` | `725f9f8` |
| I5 | `CLOSED — VERIFIED PASS` | `f9d91e1` (report correction `4d23031`) | `cd718d6` | `4887c66` |
| I6 | `CLOSED — VERIFIED PASS` | `09e2315` (docs `ea7ccc2`) | `4acc249` | `67d399f` |
| **Source Evidence Viewer** | **`CLOSED — VERIFIED PASS WITH NON-BLOCKING OBSERVATIONS`** | `999e4fb` (docs `de021ab`) | `5d5f7ed` — `PASS WITH NON-BLOCKING OBSERVATIONS` | `docs/architecture/CT-P8-PO-DECISION-DISPOSITION-CLOSURE-DECISIOIN-FOR-SOURCE-EVIDENCE-VIEWER-AND-INSIGHT-20260922.md` (2026-09-22) |

### B.8 Repository release authority (established)

| # | Decision | Status | Authority |
| --- | --- | --- | --- |
| B-10 | Authoritative release checkout is `/home/shomonrobie/ct_93d5cdd`; authoritative remote for `p8-release-reconciled` is **`github`** → `https://github.com/shomonrobie/CarbonTally.git`; `carbon_tally_p8_release` is `STALE / SUPERSEDED`; `carbon_tally` is not the release checkout | `ESTABLISHED` (surrounding divergence open — §C.6) | `docs/verification/CT-P8-RELEASE-REPOSITORY-TOPOLOGY-RECONCILIATION-20260921.md` §12, §14 ("Final status: `TOPOLOGY DIVERGENCE REQUIRES PO DECISION`") |

### B.9 Historical authority that is now fully superseded

`CT-P8-SPEC-001` (`docs/implementation/phase8/CT-P8-SPEC-001-carbon-tally-insight-specification-reconciliation.md` §P, §Q) listed I1 authorisation mechanics as blocking, the tool catalogue/status vocabulary/dormant-table/privacy/billing items as later-stage decisions, and recorded "I1 implementation authorization: `AMBIGUOUS`". **Every item in that list has since been resolved or superseded** by the I1 implementation, the I3 closure (§48.1), the Q1–Q14 intake (§48.5) and the I5/I6 closures. It is retained as history only and must not be re-opened as a current question.

---

## C. Currently unresolved PO decisions

Every item below is traceable to repository evidence (field 4 = supporting document, field 5 = section/heading). "Authorized today?" states whether implementing the item is currently authorized. "Blocking?" states whether the decision blocks a *next* authorized implementation step. Evidence class refers to §H.

### C.1 Source Evidence Viewer — closure and residual policy

> **All six items in this group (C-01…C-06) have since been disposed of by the PO closure decision of 2026-09-22 — see §0.** Each item below carries its PO disposition line. The 10-field bodies are the pre-closure inventory record and are retained as historical context; **no remediation is authorized by the disposition**.

**C-01 — `source_item.file_url` returned below DM-6 `FULL` on the customer evidence route**

> **PO disposition (2026-09-22): `RATIFIED FOR CURRENT RELEASE; FUTURE SECURITY REVIEW DEFERRED`.** The PO does **not** authorize changing this behaviour as part of the closure, and records it as a security-sensitive policy inconsistency rather than an endorsement of exposing the pointer. The ratification must not be read as authorization to expose signed URLs, storage credentials, tokens, unrestricted document content, additional storage paths or additional metadata. **No remediation is authorized.** *Authorized today: No (unchanged).*
1. **Question:** Ratify the existing behaviour, or correct it so the source-document pointer family is withheld below `FULL`?
2. **Why required:** The route nulls `source_document.path`, `metadata` and the signed URL below `FULL`, but still returns `source_item.file_url` — "the exact value `path_from_url()` converts into a signable storage path". The ratified policy and the shipped behaviour disagree.
3. **Exposed by:** the Source Evidence Viewer verification (verifier adversarial probe as an org Member).
4. **Documents:** `docs/verification/phase8/CT-P8-SOURCE-EVIDENCE-VIEWER-OHD-VERIFICATION-20260922.md` §14 observation 1; DM-6 policy `backend/domain/disclosure_exposure.py` as described in `CT-P8-SOURCE-EVIDENCE-FORENSIC-20260922.md` §21 and M10.
5. **Section/heading:** OHD report §14 "Defects and observations", item 1.
6. **Dependencies:** DM-6 policy; the same policy question as C-02; the viewer's PO closure (C-06).
7. **Authorized today?** **No** — the OHD report refers disposition to the PO; no authorization covers changing it.
8. **Blocking?** **Not acceptance-blocking** (OHD: severity medium, "Blocks acceptance: no — but the PO should ratify or correct it"). It becomes blocking only if the PO requires the boundary to be absolute before closing the viewer stage.
9. **Documented alternatives:** (a) ratify as-is; (b) "omit or null `file_url`/`file_id` in the `source_item` block unless the exposure policy grants document references — a zero-consumer, zero-risk change" (OHD report §14.1).
10. **Still current?** Re-verified at HEAD `5d5f7ed`: `backend/api/v3_emissions.py:509` returns `"file_url": item.file_url` with no exposure gate, while lines 526/531 gate `path`/`metadata`. `VERIFIED`.

**C-02 — DM-6 is not enforced on the customer documents signed-URL route**

> **PO disposition (2026-09-22): `DEFERRED — SECURITY POLICY`.** `GET /api/v3/documents/{file_id}/signed-url` is left unchanged; the PO explicitly does **not** ratify the current arrangement as a permanent security design. A future decision must determine whether (1) document-management access and evidence-disclosure access intentionally have different authorization models, or (2) the DM-6 evidence-depth model becomes a broader document-reference policy. "No implementation may be inferred from this deferral." **No code change is authorized.** *Authorized today: No (unchanged).*
1. **Question:** Should DM-6 evidence-depth policy apply to `GET /api/v3/documents/{file_id}/signed-url`, which any organisation member can call for their own organisation's file?
2. **Why required:** This is "the larger policy question behind observation 1"; the two authorisation postures (DM-6 on evidence paths vs `require_org_member()` on the document surface) are unreconciled.
3. **Exposed by:** the Source Evidence Viewer verification; also recorded as limitation 7 of the implementation report.
4. **Documents:** OHD report §14 observation 2; `docs/implementation/phase8/CT-P8-SOURCE-EVIDENCE-VIEWER-IMPLEMENTATION-20260922.md` §10; forensic `P-1` and `M10`.
5. **Section/heading:** OHD report §14 item 2; implementation report §10 "Limitations".
6. **Dependencies:** DM-6 semantics; the I2 authorization contract (a stricter rule is an I2-level change); C-01.
7. **Authorized today?** **No** — explicitly "a **PO decision**, not something this change introduced or could silently fix".
8. **Blocking?** No.
9. **Documented alternatives:** documented framing only — the route is "arguably the customer's own document-management surface rather than the evidence path"; the strict alternative is to enforce DM-6 there as well.
10. **Still current?** Re-verified at HEAD `5d5f7ed`: `backend/api/v3_documents.py:574-576` (`get_document_signed_url`) still depends only on `require_org_member()`. `VERIFIED`.

**C-03 — export/reporting still infer evidence COMPLETE from the presence of a page**

> **PO disposition (2026-09-22): `DEFERRED — AUDIT/PROVENANCE POLICY`.** The PO accepts the Source Evidence Viewer correction distinguishing authoritative `source_page`, historical/unverified page information and unavailable source location, but does **not** authorize changes to existing exports/reporting. A future decision must determine whether the platform enforces a uniform rule that `source_page IS NOT NULL` must not by itself establish evidence completeness, considering historical data, exports, reporting, reviewer-facing displays, provenance semantics and I7 export policy. **No historical-data rewriting and no export/reporting remediation are authorized.** *Authorized today: No (unchanged).*
1. **Question:** Remediate the residual `source_page IS NOT NULL ⇒ COMPLETE` inference (and confirm whether exports/reporting remain out of scope)?
2. **Why required:** Historical page-*count*-derived values still read as COMPLETE on those two surfaces although the same row correctly reads `PARTIAL`/`unverified` on the corrected customer surfaces — the `page_count`/`source_page` distinction is not uniform platform-wide.
3. **Exposed by:** the Source Evidence Viewer verification; originally forensic finding `F-B2-7`.
4. **Documents:** OHD report §14 observation 3; `CT-P8-SOURCE-EVIDENCE-FORENSIC-20260922.md` §8 and §32 `P-7`; implementation report §10.
5. **Section/heading:** OHD report §14 item 3; forensic §32 `P-7`.
6. **Dependencies:** `P-7` (historical-row treatment); export policy (C-15); the interpretation of historical evidence completeness in reviewer-facing outputs.
7. **Authorized today?** **No** — "Neither file is in the change footprint, so this is a pre-existing residual … not a regression".
8. **Blocking?** No for the viewer; it is the mechanism by which unrepaired historical provenance can still be presented as complete.
9. **Documented alternatives:** the OHD report records the PO's "stated preference to keep exports out of scope"; the alternative is a bounded correction at the two inference sites.
10. **Still current?** Re-verified at HEAD `5d5f7ed`: `backend/data/exports.py:57` (`"COMPLETE" if source_page is not None`) and `backend/data/reporting.py:1107/1111` (`AND source_page IS NOT NULL`) are unchanged. `VERIFIED`.

**C-04 — foreign-organization identifiers return 403 while absent ones return 404**

> **PO disposition (2026-09-22): `ACCEPTED`.** The existing 403/404 distinction is accepted for this release; no remediation is authorized. A future platform-wide non-disclosure policy may revisit this independently.
1. **Question:** Accept the platform-wide convention (403 for a foreign resource) or require strict non-disclosure (404) on evidence-reading routes?
2. **Why required:** 403-vs-404 distinguishes "no such line" from "a line exists in another organization" for a caller holding a valid UUID, albeit with a generic body that names nothing.
3. **Exposed by:** the Source Evidence Viewer verification.
4. **Documents:** OHD report §14 observation 4.
5. **Section/heading:** OHD report §14 item 4.
6. **Dependencies:** the platform-wide `ensure_org_access` convention (also used by the pre-existing D33 route); the UI collapses every failure into one state.
7. **Authorized today?** **No.**
8. **Blocking?** No ("Severity: low; not blocking").
9. **Documented alternatives:** "If the PO wants strict non-disclosure, the smallest remediation is to return 404 for foreign evidence resources on the evidence-reading routes."

**C-05 — ratify `raw_description` being withheld at CONTROLLED depth**

> **PO disposition (2026-09-22): `RATIFIED`.** The current withholding of `raw_description` at CONTROLLED depth is ratified as the current allowlist behaviour, and the PO considers the narrower disclosure posture preferable to unintentionally exposing additional source text. **No implementation change is authorized**; any future change must be an explicit policy decision.
1. **Question:** Ratify that a Member sees mapped field values but not the raw description, or treat the raw description as a structural key?
2. **Why required:** The DM-6 allowlist recognises structural key names (`description`, `activity`, `amount`, …) but not `raw_description`, so the withheld key is "a *behavioural* consequence of a key-name choice rather than a stated policy decision".
3. **Exposed by:** the Source Evidence Viewer verification.
4. **Documents:** OHD report §14 observation 5.
5. **Section/heading:** OHD report §14 item 5.
6. **Dependencies:** DM-6 allowlist policy; C-01 (same family of ratification questions).
7. **Authorized today?** **No.**
8. **Blocking?** No ("Severity: low; never over-exposes"). The unit tests pin the exact CONTROLLED key set, so a change would be a deliberate contract change.
9. **Documented alternatives:** none recorded beyond ratify-or-not.

**C-06 — PO closure of the Source Evidence Viewer stage (and disposition of the OHD observations)**

> **PO disposition (2026-09-22): `CLOSED`.** The PO formally closed **Shared Source Evidence Viewer + Insight Evidence Navigation** with the final state **IMPLEMENTED → INDEPENDENTLY VERIFIED → PASS WITH NON-BLOCKING OBSERVATIONS → PO ACCEPTED → CLOSED**, i.e. `CLOSED — VERIFIED PASS WITH NON-BLOCKING OBSERVATIONS`. The accepted observations are not implementation blockers. **No code remediation is authorized as a condition of this closure, and no implementation task is created by it.**
1. **Question:** Accept the OHD verdict, dispose of observations 14.1–14.3 (and optionally 14.4/14.5), and close the stage — or authorize bounded remediation before closure?
2. **Why required:** The stage is implemented (`999e4fb`) and independently verified (`5d5f7ed`, `PASS WITH NON-BLOCKING OBSERVATIONS`), but the verification explicitly does not accept it and does not close it: "The implementation is **not** declared accepted and the PO stage is **not** closed. That decision, and the disposition of observations 14.1–14.3, remains with the PO."
3. **Exposed by:** the Source Evidence Viewer implementation and its independent verification.
4. **Documents:** OHD report §1 "Verdict", §14, §16; implementation report §1 and §14.
5. **Section/heading:** OHD report §1 "Verdict"; §14 "Defects and observations"; §16 "Statement of independence and limits".
6. **Dependencies:** C-01, C-02, C-03 are the observations whose disposition the closure must settle; C-04/C-05 optional.
7. **Authorized today?** Closure is a PO act; **no implementation is authorized** as a consequence, and no remediation was proposed by the verifier.
8. **Blocking?** **Yes — this is the governing next step for the only open stage.** Under the mandatory release chain (B-08) no further authorization for this capability follows until closure (or an explicit remediation authorization) is recorded.
9. **Documented alternatives:** the I6 precedent shows the PO closed a verified stage while converting accepted observations into *future* decision items (`CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` §E/§F); the alternative is a bounded remediation authorization first (the OHD report names the smallest remediations for 14.1, 14.2 and 14.4).

**C-07 — OHD report path convention (`docs/verification/phase8/` vs `docs/implementation/phase8/`)**
1. **Question:** Unify the verification-report location (keep `docs/verification/phase8/`, move it, or accept both)?
2. **Why required:** "Prior OHD reports live under `docs/implementation/phase8/`; this report is at the PO-specified `docs/verification/phase8/`. Harmless, but the PO may wish to unify the location."
3. **Exposed by:** the Source Evidence Viewer verification.
4. **Documents:** OHD report §14 observation 8.
5. **Section/heading:** OHD report §14 item 8.
6. **Dependencies:** none (administrative).
7. **Authorized today?** **No** — no repository reorganisation is authorized.
8. **Blocking?** No.
9. **Documented alternatives:** none beyond the two directories named.

**C-08 — date/amount discovery ("why did I have 20K CO₂e on 2024-02-02?")**
1. **Question:** Authorize a capability that takes a date/amount/emissions observation to the exact evidence line (or to an entry point that does not require a pasted identifier), or leave it deferred?
2. **Why required:** It is the original customer scenario behind the forensic work; the viewer proves a *known* emission back to its evidence, which is what was authorized, and the discovery half is neither implemented nor faked.
3. **Exposed by:** the Source Evidence forensics (capability M8) and restated as the deferred capability in the verification.
4. **Documents:** `CT-P8-SOURCE-EVIDENCE-FORENSIC-20260922.md` §20, §24, §26 `M8`, §32 `P-3`; OHD report §15.
5. **Section/heading:** OHD report §15 "Known deferred capability"; forensic §26 (M8) and §32 (P-3).
6. **Dependencies:** any such capability touches the closed I3 catalogue (B-05) and/or a new bounded read; it therefore depends on C-09 (I3 question) and on a fresh PO authorization.
7. **Authorized today?** **No** — "Date/amount discovery … is **not implemented and is not faked** … recorded as a deferred capability, not a defect".
8. **Blocking?** No for closure of the viewer; it is the largest documented capability gap in the evidence chain.
9. **Documented alternatives:** forensic `P-3` records the candidate means — by-id `evidence_line_item` resolution, a document/page locator, and/or "an entry point that does not need a pasted id".

### C.2 I6 accepted follow-ups (recorded as future PO decision/authorization items)

Source for all four: `CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` **§F "Accepted PO follow-ups — future decision / authorization items (not I6 blockers)"**, mirrored in the I6 OHD verification **§26** items 1–4 (each marked `[PO]`), and noted as "four items remain **future PO decisions** outside I6" in Master Spec §48.5. In every case: "**No such tool is authorized by this closure**" / "requires **separate authorization**" / "**No permission change is authorized by this closure**" / "**No pagination redesign and no backend change is authorized by this closure**".

**C-09 — `evidence_line_item` resolvability**
1. **Question:** Should an `evidence_line_item` reference become directly resolvable by id, and if so by a **new or widened I3 tool**?
2. **Why required:** It "remains an unopenable provenance locator under the current ratified I3 tool catalogue: no ratified tool accepts an evidence-line-item id as input" (`report_lookup`→`report_id`; `report_version_lookup`→`version_id`/`report_id`+`version_number`; `report_evidence_lookup`→`report_version_id`; `calculation_snapshot_lookup`→`snapshot_id`).
3. **Exposed by:** the I6 implementation/verification (Cline observation O-1; OHD classified it PASS/compliant but referred the product question to the PO).
4. **Documents:** I6 closure §F.1; `docs/implementation/phase8/CT-P8-I6-OHD-VERIFICATION-20260922.md` §10 and §26.1; I6-4 in the I5–I8 PO record §5.
5. **Section/heading:** I6 closure §F item 1 "`evidence_line_item` resolvability"; OHD I6 report §26 item 1 (`[PO]`).
6. **Dependencies:** B-05 (the I3 catalogue is closed — a change is a separate PO decision); I6-4 (compliant without it, since the contract requires a non-disclosing state when resolution is unavailable). **Note:** the later Source Evidence Viewer authorization added a bounded by-id evidence-line **read as a customer API route** (`GET /api/v3/evidence/line-items/{id}`), which is *not* an I3 tool and does not by itself answer this question — whether it satisfies the underlying need is a PO interpretation (see §H.3).
7. **Authorized today?** **No.**
8. **Blocking?** No — I6 is closed and compliant; it is a prerequisite for any future I3 change.
9. **Documented alternatives:** "Making it directly openable would require a **new or widened I3 tool**" (i.e. new tool vs widened input vs no change).

**C-10 — Consultant / internal-staff Insight entry point**
1. **Question:** Should consultants (and/or internal CarbonTally staff) get an Insight surface, and if so under what authorization relationship?
2. **Why required:** "Insight for consultants or internal CarbonTally staff is **not part of the I6 customer-workspace authorization**"; the PO record contains no such I6 requirement.
3. **Exposed by:** the I6 implementation/verification (Cline O-2; OHD §26 item 2).
4. **Documents:** I6 closure §F.2; I6 OHD report §26.2; Master Spec §7.4, §7.5, §42.
5. **Section/heading:** I6 closure §F item 2; Master Spec §7.4 "Consultant" and §7.5 "Staff".
6. **Dependencies:** the consultant-to-customer authorization relationship (Master Spec §7.4: "If later authorized, it must use the existing consultant-to-customer authorization relationship"); the existing Q8 creator-private visibility decision; new personas are explicitly not authorized (I5–I8 PO record §14).
7. **Authorized today?** **No** — "**No consultant or internal-staff Insight UI is to be added as part of this closure**, and any future such surface requires **separate authorization**".
8. **Blocking?** No.
9. **Documented alternatives:** two actor types named (consultant, internal staff); Master Spec §7.5 adds that "identity alone is insufficient" if staff access is later authorized.

**C-11 — `org_viewer` execution rights**
1. **Question:** May an `org_viewer` (read-only customer role) execute Insight interactions, or must that be restricted?
2. **Why required:** The I6 UI "sends the request and renders whatever the backend authorizes"; whether `org_viewer` may execute interactions "is an existing authorization-contract question".
3. **Exposed by:** the I6 implementation/verification (Cline O-3; OHD §26 item 3).
4. **Documents:** I6 closure §F.3; I6 OHD report §26.3; Master Spec §7.2 (the four verified customer roles).
5. **Section/heading:** I6 closure §F item 3; I6 OHD report §26 item 3.
6. **Dependencies:** the I2/I4 authorization contract; a stricter rule would be an I2/I4 **backend** change, outside I6.
7. **Authorized today?** **No.**
8. **Blocking?** No.
9. **Documented alternatives:** keep the current backend contract (no change) vs a stricter rule implemented in the backend.

**C-12 — Insight pagination / newest-first message windows**
1. **Question:** Add paging (or newest-first message windows) to the Insight UI, or continue to inherit the backend limits?
2. **Why required:** Messages are ordered ascending and finite at 200, so "a conversation beyond 200 messages displays the *oldest* 200 and hides the newest transcript entries" (newest 50 interactions remain visible in the answers section); conversations and interactions are newest-first, finite at 50.
3. **Exposed by:** the I6 implementation/verification (Cline O-4; OHD §26 item 4, with the truncation direction made explicit).
4. **Documents:** I6 closure §F.4; I6 OHD report §26.4.
5. **Section/heading:** I6 closure §F item 4; I6 OHD report §26 item 4.
6. **Dependencies:** the backend already exposes `limit`/`offset`; a UI-only change differs from a backend default change.
7. **Authorized today?** **No** — "**No pagination redesign and no backend change is authorized by this closure**".
8. **Blocking?** No ("Nothing in the PO I6 scope requires pagination").
9. **Documented alternatives:** "the backend already exposes `limit`/`offset` should the PO later require paging or newest-first message windows".

### C.3 I7 — Privacy / Retention / Export prerequisites

Source for all: `CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` **§6 "I7 — Privacy / Retention / Export"** (sub-headings "I7 decisions requiring external/legal/business authority" → Retention / Deletion / Export / Provider-privacy; "I7 authorization decision": **NOT AUTHORIZED**), plus Master Spec §21 and the readiness audit §28.4 (`I7 — NOT READY`). Every listed sub-item is quoted from the PO record; none is to be invented by an implementation agent ("These must not be invented by Cline.").

**C-13 — Retention durations**
1. **Question:** What retention periods apply to conversations, messages, interactions, tool-call evidence, the canonical audit ledger, and any future summaries?
2. **Why required:** I7 cannot be specified without durations; the Master Spec explicitly leaves retention "deliberately OPEN until I7" and forbids invention.
3. **Exposed by:** the I7 parameter set recorded by the PO and the readiness audit's `NOT READY` finding.
4. **Documents:** I5–I8 PO record §6 "Retention"; Master Spec §21; readiness audit §28.4; forensic `P-5` (evidence lines/snapshots/documents).
5. **Section/heading:** I5–I8 PO record §6 "I7 decisions requiring external/legal/business authority" → "Retention".
6. **Dependencies:** C-14 (deletion), C-16 (provider/privacy), C-17 (acceptance criteria); I7-D (append-only/immutability constraints) and I5-4 (no summaries exist yet).
7. **Authorized today?** **No** — `NOT YET AUTHORIZED — REQUIRES EXTERNAL DECISION`.
8. **Blocking?** **Yes for I7**, and transitively for any production-deployment authorization (the chain requires stage closure first).
9. **Documented alternatives:** none — durations must not be invented.

**C-14 — Deletion semantics**
1. **Question:** User deletion rights; hard vs soft deletion; organization deletion semantics beyond current cascades; legal-hold requirements; deletion exceptions.
2. **Why required:** Required to specify I7; I7-D additionally requires any deletion/archive mechanism to account for interaction/tool-call immutability, canonical audit retention, existing triggers and conversation cascades.
3. **Exposed by:** the I7 parameter set; the I4 append-only design.
4. **Documents:** I5–I8 PO record §6 → "Deletion", §6 I7-D; Master Spec §21.
5. **Section/heading:** I5–I8 PO record §6 "Deletion" and "I7-D — Append-only I4 evidence".
6. **Dependencies:** retention (C-13), audit retention (part of C-13), audit-export authorisation rules (C-15 has an interaction with the existing `backend/api/admin_audit.py GET /export` path, which the readiness audit records as untraced).
7. **Authorized today?** **No.**
8. **Blocking?** **Yes for I7.**
9. **Documented alternatives:** the alternatives ("hard vs soft") are named as questions, not as PO-selected options.

**C-15 — Export policy**
1. **Question:** Who may export; export scope; export format; redaction requirements; whether raw questions/narration are exportable; whether provider metadata is exportable; whether export is audited.
2. **Why required:** Required to specify I7; export is a deferred capability (Master Spec §42) and Q12 deferred it from I4.
3. **Exposed by:** the I7 parameter set.
4. **Documents:** I5–I8 PO record §6 → "Export"; Master Spec §21, §42; readiness audit §26.7 (export-path rules `UNKNOWN / NOT VERIFIED`).
5. **Section/heading:** I5–I8 PO record §6 "Export".
6. **Dependencies:** C-13/C-14; the existing audited admin export path (must not be assumed).
7. **Authorized today?** **No.**
8. **Blocking?** **Yes for I7**; also referenced by C-03 (export completeness semantics).
9. **Documented alternatives:** the seven sub-questions above are the documented decision surface; no option is pre-selected.

**C-16 — Provider / privacy decisions**
1. **Question:** Provider data retention; provider training/data-use policy; residency; subprocessors; PII classification; privacy notices.
2. **Why required:** These determine whether Insight may be offered and on what terms; the PO record states they "must not be invented by Cline".
3. **Exposed by:** the I7 parameter set.
4. **Documents:** I5–I8 PO record §6 → "Provider/privacy"; Master Spec §21.
5. **Section/heading:** I5–I8 PO record §6 "Provider/privacy".
6. **Dependencies:** external/legal authority; interacts with C-18 (provider cost) and C-22 (payment provider), and with Master Spec §15 (AI/LLM boundary).
7. **Authorized today?** **No.**
8. **Blocking?** **Yes for I7.**
9. **Documented alternatives:** none recorded.

**C-17 — I7 acceptance criteria and authorization package**
1. **Question:** What acceptance criteria will I7 be verified against, and does I7 remain a single stage or is it split?
2. **Why required:** "§35's I7 and I8 stage blocks contain **no acceptance criteria**, unlike I1–I3 … Any I7/I8 authorization must supply them"; I7 is `NOT READY` precisely because the parameter set is open.
3. **Exposed by:** the readiness audit.
4. **Documents:** `CT-P8-I5-I8-PREAUTHORIZATION-READINESS-AUDIT-20260921.md` §27 item 9 and §28.4; Master Spec §35/I7.
5. **Section/heading:** readiness audit §27 (item 9) and §28 (conclusion 4); Master Spec §35 "I7 — Privacy / Retention / Export".
6. **Dependencies:** C-13…C-16 must be decided first; the readiness audit records that "the engineering prerequisites (inventory, controls, append-only guarantees, retention machinery, audit-export precedent) already exist, so the gap is decision-making, not capability".
7. **Authorized today?** **No.**
8. **Blocking?** **Yes — no bounded I7 authorization can be written until the parameter set and acceptance criteria exist.**
9. **Documented alternatives:** none recorded; I7 is explicitly "NOT READY" rather than "READY WITH PO DECISIONS".

### C.4 I8 — Billing / Production Hardening prerequisites

Source: `CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` **§7** (I8 status: "PARTIALLY AUTHORIZED ONLY — ENGINEERING HARDENING BOUNDARY"; split into **I8-A** production/operational hardening and **I8-B** commercial/billing policy), **§8** ("SLOs", "Backup/recovery", "Incident response" each `NOT YET AUTHORIZED — PO/PRODUCT/OPERATIONS DECISION REQUIRED`), **§9** (I8-B list), **§10** (payment provider), **§11** (eight I8 authorization prerequisites), **§12**, **§14**; Master Spec §22; readiness audit §28.5.

**C-18 — I8-B commercial / billing policy set**
1. **Question:** Insight usage unit; whether Insight consumes existing credits; Insight allowances; entitlement enforcement point; pricing; plan/tier inclusion; overage; provider-cost absorption/pass-through; billing-failure behaviour; refunds/credit adjustments; whether Insight appears in `/me/credits`.
2. **Why required:** These are the I8-B decisions; "No Cline implementation may invent these policies."
3. **Exposed by:** the readiness audit's finding of "a substantial existing billing/commercial foundation, but also unresolved commercial and provider questions".
4. **Documents:** I5–I8 PO record §9 "I8-B — Commercial / billing decisions"; Master Spec §22; readiness audit §28.5.
5. **Section/heading:** I5–I8 PO record §9, and §11 items 1–2.
6. **Dependencies:** C-16 (provider/privacy, for provider-cost questions); C-22 (payment-provider determination); C-23 (acceptance criteria). Master Spec §22 requires reusing existing billing infrastructure — "Do not create a parallel Insight billing system."
7. **Authorized today?** **No** — `NOT YET AUTHORIZED — REQUIRES BUSINESS/COMMERCIAL DECISION`.
8. **Blocking?** **Yes for full I8**, and transitively for production deployment.
9. **Documented alternatives:** none pre-selected; the eleven named sub-decisions are the documented surface.

**C-19 — Insight SLO targets**
1. **Question:** What numerical service-level objectives apply to Insight?
2. **Why required:** `NOT YET AUTHORIZED — PO/PRODUCT DECISION REQUIRED`; "No numerical SLO may be invented by Cline."
3. **Exposed by:** the I8-A hardening boundary.
4. **Documents:** I5–I8 PO record §8 "SLOs"; §11 item 3; Master Spec §41 ("exact performance/SLO targets").
5. **Section/heading:** I5–I8 PO record §8 "SLOs".
6. **Dependencies:** C-21 (incident response), C-23 (acceptance criteria).
7. **Authorized today?** **No.**
8. **Blocking?** **Yes for full I8.**
9. **Documented alternatives:** none.

**C-20 — Backup / recovery policy**
1. **Question:** What production backup/recovery policy applies?
2. **Why required:** `NOT YET AUTHORIZED — OPERATIONS DECISION REQUIRED`; "No production backup/recovery policy may be invented by implementation agents."
3. **Exposed by:** the I8-A hardening boundary.
4. **Documents:** I5–I8 PO record §8 "Backup/recovery"; §11 item 5.
5. **Section/heading:** I5–I8 PO record §8 "Backup/recovery".
6. **Dependencies:** C-13 (retention interacts with backup scope); C-23.
7. **Authorized today?** **No.**
8. **Blocking?** **Yes for full I8.**
9. **Documented alternatives:** none.

**C-21 — Incident-response / runbook requirements**
1. **Question:** What Insight-specific incident/runbook requirements must be established?
2. **Why required:** `NOT YET AUTHORIZED — OPERATIONS DECISION REQUIRED`; "must be established before final I8 production-hardening closure."
3. **Exposed by:** the I8-A hardening boundary; the readiness audit's `UNKNOWN` finding that "no Insight SLO/runbook/backup artefact" was identified.
4. **Documents:** I5–I8 PO record §8 "Incident response"; §11 item 6; readiness audit §28.5.
5. **Section/heading:** I5–I8 PO record §8 "Incident response".
6. **Dependencies:** C-19 (SLOs), C-23.
7. **Authorized today?** **No.**
8. **Blocking?** **Yes for full I8 closure.**
9. **Documented alternatives:** none.

**C-22 — Payment-provider factual determination**
1. **Question:** Does a payment-provider/webhook integration exist, and if not, is one to be created — by whom and on what provider?
2. **Why required:** The readiness audit "could not establish whether a payment provider/webhook integration exists"; therefore "do not assume Stripe; do not assume another provider; do not create a payment integration; do not replace the existing billing system."
3. **Exposed by:** the readiness audit (`UNKNOWN / NOT VERIFIED`).
4. **Documents:** I5–I8 PO record §10 "Payment provider"; §11 item 7; readiness audit §26 item 8 and §28.5.
5. **Section/heading:** I5–I8 PO record §10 "Payment provider"; readiness audit §26 item 8.
6. **Dependencies:** C-18 (commercial policy) — the provider question may arise only once the commercial model is chosen.
7. **Authorized today?** **No** — but the record permits a *separate bounded forensic investigation* to be authorized ("A separate bounded forensic investigation may be authorized if required").
8. **Blocking?** **Yes for full I8** (prerequisite 7 of the eight in §11).
9. **Documented alternatives:** documented as (a) establish the fact by bounded investigation, or (b) explicitly exclude it — the readiness audit requires the unknown "be established or explicitly excluded".

**C-23 — I8 acceptance criteria and the eight authorization prerequisites**
1. **Question:** What acceptance criteria apply to I8 (and to a narrower I8-A), and how is the stage bounded?
2. **Why required:** §11 lists the eight prerequisites for a concrete I8 authorization: commercial decisions; usage/entitlement policy; SLO targets; operational monitoring requirements; backup/recovery requirements; incident/runbook requirements; payment-provider factual determination; acceptance criteria. The readiness audit adds that §35's I8 block contains **no** acceptance criteria.
3. **Exposed by:** the I5–I8 PO record §11 and the readiness audit.
4. **Documents:** I5–I8 PO record §11 "I8 implementation authorization"; readiness audit §27 item 9 and §28.5.
5. **Section/heading:** I5–I8 PO record §11 (items 1–8); readiness audit §27 item 9.
6. **Dependencies:** C-18…C-22.
7. **Authorized today?** **No.**
8. **Blocking?** **Yes — no bounded I8 implementation authorization can be written before these exist.**
9. **Documented alternatives:** §8 records that I8-A "is potentially authorizable after bounded specification", i.e. a narrower step than full I8-B.

**C-24 — Commercial posture of evidence viewing (metered / plan-gated / free)**
1. **Question:** Is source-evidence viewing metered, plan-gated or free?
2. **Why required:** "No entitlement code touches evidence today; a viewer adds per-view signed URLs and client-side document fetches."
3. **Exposed by:** the Source Evidence forensics (finding only — nothing authorized).
4. **Documents:** `CT-P8-SOURCE-EVIDENCE-FORENSIC-20260922.md` §30 and §32 `P-6`.
5. **Section/heading:** forensic §32 `P-6`; §30 "I8 implications".
6. **Dependencies:** C-18 (usage unit / entitlement point) — this is that decision applied to the evidence capability.
7. **Authorized today?** **No.**
8. **Blocking?** No (the implemented viewer is not metered; adding metering would be new work).
9. **Documented alternatives:** the three named postures only.

### C.5 Master Spec §41 residuals and I5 v1 follow-ons

**C-25 — Auditor and PE Insight surfaces (deferred personas)**
1. **Question:** Should auditor and/or Processing-Entity personas ever receive an Insight surface, and under what boundary?
2. **Why required:** Master Spec §41 lists "auditor access" and "PE access" as decisions that "remain PO/design decisions until explicitly closed"; §7.6 records auditor access as deferred and §7.7 that PE Insight "is not included in the initial capability".
3. **Exposed by:** the Master Spec persona/access model and its deferred-capability list.
4. **Documents:** Master Spec §7.6, §7.7, §41, §42; I5–I8 PO record §14 ("new personas" not authorized).
5. **Section/heading:** Master Spec §41 "Open Product Decisions" (auditor access; PE access); §7.6 "Auditor"; §7.7 "Processing Entity / PE".
6. **Dependencies:** for PE, the Processing Entity operating model and its authorization boundary; for auditor, the assurance boundary ("Nothing in Insight changes CarbonTally's assurance boundary").
7. **Authorized today?** **No** — §42 defers auditor Insight and PE Insight unless separately authorized.
8. **Blocking?** No.
9. **Documented alternatives:** none beyond "deferred unless separately authorized"; §7.7 forbids inventing a persona "without a separate PO decision".

**C-26 — Conversation/insight rename and archive semantics**
1. **Question:** Are conversations renamable and archivable, and with what semantics (e.g. does archive affect retention or visibility)?
2. **Why required:** Master Spec §41 lists "rename/archive" as an open PO/design decision; §21 lists it among the deliberately open policies.
3. **Exposed by:** the Master Spec's open-product list.
4. **Documents:** Master Spec §41, §21.
5. **Section/heading:** Master Spec §41 "Open Product Decisions" (rename/archive); §21 "Privacy, Retention, Deletion, and Export".
6. **Dependencies:** Q5 (Layer-2 append-only/immutability), C-13/C-14 (retention/deletion interplay).
7. **Authorized today?** **No.**
8. **Blocking?** No.
9. **Documented alternatives:** none recorded.

**C-27 — Regeneration / edit semantics**
1. **Question:** May a user regenerate or edit an answer, and how are the earlier and replacement records related?
2. **Why required:** Master Spec §41 lists "regeneration/edit semantics" as open, while Q5 fixes Layer-2 immutability (corrections are new linked records), so regeneration semantics must be defined consistently with it.
3. **Exposed by:** the Master Spec's open-product list and Q5.
4. **Documents:** Master Spec §41, §21, §48.5 Q5.
5. **Section/heading:** Master Spec §41 (regeneration/edit semantics).
6. **Dependencies:** Q5, B-06 (no I4 redesign), Q10 (idempotency / no duplicate logical calls).
7. **Authorized today?** **No.**
8. **Blocking?** No.
9. **Documented alternatives:** none recorded.

**C-28 — Provider selection**
1. **Question:** Must a specific AI provider be selected/committed for Insight, or does the existing provider abstraction plus configuration suffice?
2. **Why required:** Master Spec §41 lists "provider selection" as a decision that remains open until explicitly closed; Q14 constrains Insight to "the existing provider abstraction only" without selecting a provider.
3. **Exposed by:** the Master Spec's open-product list.
4. **Documents:** Master Spec §41, §15.2, §48.5 Q14; readiness audit §28.
5. **Section/heading:** Master Spec §41 (provider selection); §15.2 "Provider configuration"; §48.5 Q14.
6. **Dependencies:** C-16 (provider retention/training/residency), C-18 (provider-cost policy).
7. **Authorized today?** **No.**
8. **Blocking?** No — the current abstraction and configuration are in place and I5/I6 are closed against them.
9. **Documented alternatives:** none; Q14 states what is *not* required (no evaluation platform, RAG, embeddings or orchestration framework).

**C-29 — I5 v1 follow-ons (context-metadata persistence, optional hard ceiling, raw-text expansion)**
1. **Question:** (a) Should context metadata (used characters, truncation, block count) be persisted (requiring a migration); (b) should a hard upper context ceiling be introduced; (c) should I5 be expanded to raw I1 message text?
2. **Why required:** (a) is "not persisted — persisting it would require a schema migration, which was not authorized"; (b) O-1 clause 9: "A future PO decision may establish a hard upper ceiling if product, operational or provider requirements later justify one"; (c) O-4 is a limitation "accepted for I5 v1" with "no expansion … authorized".
3. **Exposed by:** the I5 closure's recorded limitations and the O-1 decision.
4. **Documents:** `CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md` §2 (O-1 clauses 4–9), §3 (O-4), §5 (limitations 1–3).
5. **Section/heading:** I5 closure §5 "Limitations accepted for I5 v1"; §2 "O-1 — PO DECISION (CLOSED)".
6. **Dependencies:** (a) touches I1/I5 persistence and therefore I7's retention frame; (b) and (c) are I5 scope changes that must not be inferred.
7. **Authorized today?** **No** — each is an explicit non-authorization.
8. **Blocking?** No.
9. **Documented alternatives:** documented as "not required"/"no expansion authorized" today, with future decisions expressly contemplated for (b) and (c).

### C.6 Repository governance and record durability

**C-30 — Repository topology divergence**
1. **Question:** How should the PO dispose of the stale duplicate release checkout, the stale local release branch, the diverged local `main` and dirty tree, the untracked closure document on `main`, the misconfigured release-branch upstream (local path `origin` → `/tmp/ct_step2`) with its prunable `/tmp` worktrees, and the unreviewed `docs/cline/reports/P8-PRODUCTION-MIGRATION-*` artefacts?
2. **Why required:** The topology reconciliation records the release authority as established but states: "**Final status: `TOPOLOGY DIVERGENCE REQUIRES PO DECISION`** … none of which may be cleaned up without PO authorisation."
3. **Exposed by:** the release repository topology reconciliation.
4. **Documents:** `docs/verification/CT-P8-RELEASE-REPOSITORY-TOPOLOGY-RECONCILIATION-20260921.md` §13 (five numbered items), §14.
5. **Section/heading:** §13 "Unresolved ambiguity — requires PO decision" (items 1–5); §14 "Deployment-state findings".
6. **Dependencies:** none for implementation work (pushes to `github` are correct and aligned); a cleanup authorization would be needed before any topology change.
7. **Authorized today?** **No** — "none of which may be cleaned up without PO authorisation".
8. **Blocking?** No for implementation; the reconciliation notes the misconfigured upstream and the unreviewed migration artefacts must not be used as deployment evidence.
9. **Documented alternatives:** item 1 records that "evidence supports" declaring `carbon_tally_p8_release` obsolete/superseded; the other four items list the artefacts awaiting disposition.

**C-31 — Master Specification status/documentation reconciliation**
1. **Question:** Should the Master Specification's stale status statements and its un-annotated §41/§47 lists be reconciled (and if so, how — status notes only, or a revision)?
2. **Why required:** §47 "Final Status" still reads "I3: `IMPLEMENTED — REMEDIATION VERIFICATION PENDING`", "I4–I8: `NOT AUTHORIZED`", "Immediate next PO gate: … I4" — all superseded for status by §3.1 and the later closure records. §41 still lists items that §48.5 Q1–Q14 and the I5/I6 decisions have since resolved (e.g. "raw question storage versus hash", "exact answer-status enumeration", "exact context/compaction policy", "dormant AI structure disposition", "owner/admin shared conversation visibility"). §48.4's "I4, I5, I6, I7 and I8 remain NOT AUTHORIZED" is likewise historical.
3. **Exposed by:** the closure records' own statements that historical `NOT AUTHORIZED` text is "left **as written**" and "superseded … for *status* by §3.1 and by this closure record", combined with the specification's practice of appending dated status notes rather than rewriting.
4. **Documents:** Master Spec §3.1, §41, §47, §48.4, §48.5; `CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md` §9; `CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` §4.
5. **Section/heading:** Master Spec §47 "Final Status"; §41 "Open Product Decisions"; §48.4 "Governance consequence".
6. **Dependencies:** C-32 (record durability); this is a documentation-governance decision, not a technical one.
7. **Authorized today?** **No** — no specification rewrite is authorized (closures have been permitted to append *status-only* notes).
8. **Blocking?** No, but a reader who trusts §47/§41 rather than §3.1/§48.5 will mis-state current status.
9. **Documented alternatives:** the documented practice is status-note-only updates (I5 closure §9, I6 closure §4); a fuller revision would be a different PO choice.

**C-32 — Durability of capability-level PO authorization records**
1. **Question:** Should capability-level authorizations outside the numbered I-stages (e.g. the 2026-09-22 *Shared Source Evidence Viewer + Insight Evidence Navigation* authorization) be recorded as durable PO decision documents under `docs/architecture/`, in the same way as Q1–Q14 and I5–I8?
2. **Why required:** the Source Evidence Viewer implementation report is headed "**Task / authorization ID:** PO Authorization — *Shared Source Evidence Viewer + Insight Evidence Navigation* (2026-09-22)", and the OHD verification cites "**Mandate:** PO authorization, 2026-09-22 — *Shared Source Evidence Viewer + Insight Evidence Navigation*". No separate PO decision/authorization document for this capability exists in the repository (only the implementation and verification reports cite it).
3. **Exposed by:** the Source Evidence Viewer implementation and verification.
4. **Documents:** `CT-P8-SOURCE-EVIDENCE-VIEWER-IMPLEMENTATION-20260922.md` (header, §1); `CT-P8-SOURCE-EVIDENCE-VIEWER-OHD-VERIFICATION-20260922.md` (header).
5. **Section/heading:** implementation report header "Task / authorization ID"; verification report header "Mandate".
6. **Dependencies:** C-06 (closure would naturally record the authorization's disposition); C-07 (report-path convention, a related administrative item).
7. **Authorized today?** **No** — creating such a record is a documentation act requiring PO instruction (this audit does not create it).
8. **Blocking?** No, but the scope boundary of the authorization is currently provable only from the implementation report's own statement of scope plus the verifier's mandate line.
9. **Documented alternatives:** none — this is a record-keeping observation, and the evidence is explicit about *what* was authorized (implementation report §1 and §11) even though the PO text itself is not committed.

---

## D. Source Evidence decision status

### D.1 What the earlier I3/I4/I5/I6 records said (before 2026-09-22)

| Record | Statement | Effect |
| --- | --- | --- |
| I3 closure (Master Spec §3.3, §48.1; B-05) | "The four ratified I3 tools remain unchanged … No new I3 tool is authorized by this record." | The catalogue is closed at four tools; an evidence-line-item id is not an accepted tool input |
| I6-4 (I5–I8 PO record §5) | References are locators; resolution must re-authorize; a non-disclosing state is required **"if resolution is unavailable"** | The contract explicitly contemplates unresolvable references — non-resolvability is compliant, not a defect |
| I6 OHD verification §10 | "**Classification: PASS (compliant).** If the product wants `evidence_line_item` resolvable by id, that requires a **new or widened I3 tool — a separate PO decision outside I6's authorization**" | Referred to PO; no remediation proposed |
| I6 PO closure §F.1 and §2 | `evidence_line_item` "**remains an unopenable provenance locator**"; making it openable requires "a separate PO decision"; the closure does **not** authorize "new APIs or endpoints" or "widened tool inputs (including `evidence_line_item` resolvability)" | **Explicitly not authorized**, and explicitly deferred as a future item |
| I6 PO closure §F.2–§F.4 | Consultant/internal-staff entry point, `org_viewer` rights, pagination | Deferred future items |
| Source Evidence forensic §32 | "None of these is decided here… I7, I8, an I3 extension, an evidence viewer and any change to `evidence_line_item` each remain separate PO decisions, listed in §32." §33: "This document … authorizes nothing" | The forensic report is **finding-only**; it is **not** an authorization |
| Source Evidence forensic §32 P-1…P-7 | Viewer existence/roles (P-1), line-level location (P-2), I3 extension (P-3), shared vs Insight-specific (P-4), retention/erasure/redaction (P-5), metered/plan-gated/free (P-6), `source_page` correction + historical rows (P-7) | The PO decision surface opened by evidence |

### D.2 What subsequently happened (2026-09-22), and its status

A PO authorization dated **2026-09-22** for *"Shared Source Evidence Viewer + Insight Evidence Navigation"* is cited as the mandate by the implementation report (header "Task / authorization ID") and by the independent verification (header "Mandate"). On that basis the capability was implemented (`999e4fb`), documented (`de021ab`) and independently verified (`5d5f7ed`, `PASS WITH NON-BLOCKING OBSERVATIONS`).

Scope delivered, per the implementation report §1: one shared viewer reachable from the customer evidence flow **and** Insight; a bounded re-authorized evidence-line resolution read; the `source_page` provenance correction with honest handling of historical records; the DM-6 correction on the D33 customer evidence path (signed URL only at FULL); and the Insight handoff **with no new I3 tool and no I3 contract change**.

| Forensic item | Status after the 2026-09-22 work |
| --- | --- |
| P-1 viewer exists / which roles | **Implemented** — the viewer exists, is shared, and DM-6 depth is enforced; residual policy edges are C-01, C-02 |
| P-2 line-level location required? | **Implemented as "where authoritative, otherwise explicitly unavailable/restricted"** — `page_state` verified/unverified/unavailable/restricted; ordinals never presented as pages or rows |
| P-3 I3 extension required? | **Answered "no" for the handoff** (no I3 change); the by-id read was added as a customer API route, not an I3 tool. The I3 question survives as **C-09**; the date/amount entry point as **C-08** |
| P-4 shared vs Insight-specific? | **Answered: shared** — one component (`SourceEvidenceViewer`) and one location/URL kernel reused by the customer panel and the Insight handoff (OHD report §8) |
| P-5 retention/erasure/redaction (I7) | **Not decided** — remains C-13…C-17 under I7 (`NOT AUTHORIZED`) |
| P-6 metered/plan-gated/free (I8) | **Not decided** — remains C-24 under I8 (`NOT AUTHORIZED` as a full stage) |
| P-7 `source_page` correction + historical rows | **Delivered as authorized scope**: the write path no longer writes a page count as a page; historical rows are retained and reported `unverified`/`PARTIAL`; the **platform-wide** residual on export/reporting remains **C-03** |

### D.3 Determination

* **Already authorized?** Not before 2026-09-22; **yes, in bounded form, by the 2026-09-22 capability authorization** (scope as recorded in the implementation report).
* **Partially authorized?** **Yes — this is the accurate description.** The authorization was bounded: "no I7 retention/erasure policy, no I8 billing/plan gating/metering, no AI/RAG/vector search, no new I3 tool, no I2 semantic change beyond the DM-6 correction, no schema/migration change, no historical data rewrite, no production deployment" (implementation report §1).
* **Explicitly deferred?** Yes for the surrounding questions — date/amount discovery (C-08), I3 resolvability (C-09), I7 posture (P-5 → C-13…C-17), I8 posture (P-6 → C-24).
* **Explicitly rejected?** **No.** No record rejects the capability or any of its sub-questions.
* **Genuinely still requires a PO decision?** *(Pre-closure answer, retained as history)* **Yes** — C-01, C-02 and C-03 (the observations whose "disposition … remains with the PO"), optionally C-04/C-05, and **C-06 (closure)**. Resolving C-03 in practice means deciding whether the `page_count`/`source_page` distinction must be uniform platform-wide.
* **Post-decision status (2026-09-22):** **resolved by the PO closure decision.** C-06 is **CLOSED**; C-01 is `RATIFIED FOR CURRENT RELEASE; FUTURE SECURITY REVIEW DEFERRED`; C-02 is `DEFERRED — SECURITY POLICY`; C-03 is `DEFERRED — AUDIT/PROVENANCE POLICY`; C-04 is `ACCEPTED`; C-05 is `RATIFIED`. The capability is therefore **`CLOSED — VERIFIED PASS WITH NON-BLOCKING OBSERVATIONS`** — see §0. **No remediation of C-01/C-02/C-03 is authorized**, and the security/audit questions remain explicitly deferred rather than answered.

**The forensic report itself is not, and does not claim to be, an authorization** (§33). The authorization is established only by reference in the implementation and verification reports; see C-32 for the record-keeping consequence.

## E. I7 / I8 status

### E.1 I7 — Privacy / Retention / Export

| Item | Repository evidence |
| --- | --- |
| Authorization status | **`NOT AUTHORIZED`.** I5–I8 PO record §6 "I7 authorization decision": "I7 implementation must wait until the above external/legal/business decisions and acceptance criteria are established." §12 final stage table: I7 = "External/legal decisions outstanding", implementation "**NOT AUTHORIZED**". Reaffirmed by I5 closure §7, I6 closure §2 and Master Spec §3.1 (`NOT_AUTHORIZED`). |
| Prerequisites | The already-decided boundaries I7-A…I7-D (authorization respected; canonical audit separation; Q1/Option C continued; append-only I4 evidence respected) **plus** the undecided parameter set — retention durations, deletion semantics, export policy, provider/privacy — **plus** acceptance criteria (C-13…C-17). |
| Unresolved decisions | C-13 (retention durations), C-14 (deletion), C-15 (export), C-16 (provider/privacy), C-17 (acceptance criteria / authorization package); C-29(a) if context-metadata persistence is wanted. |
| Dependencies | I4 append-only/immutability with its triggers and cascades (I7-D); Q12's deferral from I4; Q1's deferred `ai_content_history` disposition; the I5 limitations that touch persistence; and the forensic retention question (`evidence_line_items` is append-only with no purge and stores raw document text, and a viewer widens exposure — P-5). |
| Authorized to implement now? | **No.** The readiness audit classifies I7 `NOT READY` (not merely "ready with decisions"): "The stage's entire parameter set is deliberately open … and requires PO/legal decisions; there are no acceptance criteria to verify against" (§28.4). |

### E.2 I8 — Billing / Production Hardening

| Item | Repository evidence |
| --- | --- |
| Authorization status | **`NOT AUTHORIZED AS A FULL STAGE`**, with a **partial authorization**: I8 is split into I8-A (production/operational hardening — principles PO-closed: rate limiting, observability, provider resilience, deployment discipline) and I8-B (commercial/billing policy — `NOT YET AUTHORIZED`). Master Spec §3.1 records `NOT_AUTHORIZED`; I5 closure §7 and I6 closure §2 reaffirm. |
| Prerequisites | The eight items in I5–I8 PO record §11: commercial decisions; usage/entitlement policy; SLO targets; operational monitoring requirements; backup/recovery requirements; incident/runbook requirements; payment-provider factual determination; acceptance criteria. |
| Unresolved decisions | C-18 (commercial/billing set), C-19 (SLOs), C-20 (backup/recovery), C-21 (incident/runbook), C-22 (payment provider), C-23 (acceptance criteria/prerequisites), C-24 (evidence-viewing commercial posture). |
| Dependencies | C-16 (provider/privacy) for provider-cost questions; C-13 (retention) for backup scope. Master Spec §22 requires **reuse** of existing billing infrastructure and forbids a parallel Insight billing system. Readiness audit §28.5 records two `UNKNOWN`s: payment-provider/webhook integration, and Insight-specific operational artefacts (no SLO/runbook/backup artefact identified). |
| Authorized to implement now? | **No** — "Only the bounded operational-hardening principles above are PO-approved" (§11). A bounded **I8-A** specification could be written once its own parameters and acceptance criteria exist (§8: I8-A "is potentially authorizable after bounded specification"). |

**Neither stage is re-opened or redesigned by this audit.** The items above are recorded exactly as the PO record, the closures and the readiness audit state them.

## F. Recommended decision sequence

**Dependency-based only.** This section orders decisions by the dependencies the repository documents. It does not rank them by desirability and does not recommend a product choice.

### F.1 Sequence for the open evidence capability — **COMPLETED by the PO decision of 2026-09-22**

> **Outcome:** the PO took the **closure branch, not the remediation branch**. C-01/C-02/C-03 were dispositioned (ratify / defer / defer) with **no remediation authorized**, and C-06 was decided as **CLOSED**. No implementation authorization, implementation, OHD verification or further closure follows from this sequence.

```text
C-01 + C-02 (+ C-03) [PO disposition of the three observations]
        → C-06 [PO closure of the Source Evidence Viewer, or a bounded remediation authorization]
        → (if remediation is chosen) bounded implementation authorization → implementation → OHD verification → PO closure
```

**Why this order is forced by the documents:** the verification states that acceptance and closure "remains with the PO" **and** that "the disposition of observations 14.1–14.3 remains with the PO" — so the closure (C-06) cannot be made before those dispositions exist. Under the mandatory release chain (B-08), any correction the PO elects becomes a *new* bounded implementation followed by its own OHD verification and closure; the verifier proposed no remediation and performed none, so no correction exists today.

### F.2 Sequence for the Insight capability decisions (independent of F.1)

```text
C-09 [I3 evidence_line_item question] ─┬→ (if positive) new/widened I3 tool: authorization → implementation → OHD → PO closure
C-08 [date/amount discovery]           ┘   (depends on the same I3/evidence-read question answered in C-09)

C-11 [org_viewer execution rights] → I2/I4 contract decision → authorization → implementation → OHD → PO closure
C-12 [pagination]                  → bounded UI/backend decision → authorization → implementation → OHD → PO closure
C-10 [consultant / internal-staff] → persona+authorization decision → authorization → implementation → OHD → PO closure
C-25 [auditor / PE personas]       → persona decision → authorization (currently deferred by §42)
```

**Why:** B-05 closes the I3 catalogue — an I3 change is therefore "a separate PO decision" before any implementation can be authorized. C-08 (forensic `P-3`) is documented as depending on the same locator/entry-point question. C-11 is explicitly "an existing authorization-contract question" touching I2/I4, so its decision must precede any backend change. C-10 and C-25 are persona decisions that Master Spec §7.4–§7.7 and §42 defer, each requiring separate authorization before a surface can exist.

### F.3 Sequence for I7

```text
C-13 + C-14 + C-15 + C-16 [external/legal/business parameter set]
        → C-17 [acceptance criteria + bounded authorization package, following a readiness re-audit]
        → bounded I7 implementation authorization → implementation → OHD verification → PO closure
```

**Why:** I7 is `NOT READY` precisely because the parameter set is undecided, and the readiness audit records that "§35's I7 and I8 stage blocks contain **no acceptance criteria** … Any I7/I8 authorization must supply them" — so acceptance criteria (C-17) must follow the parameters, not precede them. I7-D additionally constrains any deletion/archive mechanism, so C-14 cannot be implemented by disabling the existing append-only controls.

### F.4 Sequence for I8

```text
C-22 [payment-provider factual determination — may be a bounded forensic investigation]
C-18 [commercial/usage/entitlement policy]
        → C-19 + C-20 + C-21 [SLOs, backup/recovery, incident/runbook]
        → C-23 [acceptance criteria + split of I8-A vs I8-B]
        → bounded I8 authorization (I8-A narrower than I8-B) → implementation → OHD verification → PO closure

C-24 [evidence-viewing commercial posture] depends on C-18.
```

**Why:** §11 enumerates the eight prerequisites for a concrete I8 authorization, and the readiness audit requires the payment-provider unknown be "established or explicitly excluded". Master Spec §22 requires reuse of the existing billing infrastructure, so commercial policy (C-18) must exist before any enforcement point can be chosen. §8 permits I8-A to be authorized separately once its own bounded specification exists.

### F.5 Deployment

```text
I7 closure + I8 closure → separate controlled deployment authorization → deployment → post-deployment verification
```

**Why:** B-08 (I5–I8 PO record §8 "Deployment", Master Spec §37) states that no Insight stage "may reach production merely because implementation exists", and I5 closure §7, I6 closure §2 and the OHD verification all record that production deployment remains not authorized.

### F.6 Orthogonal governance items (any time; no implementation dependency)

`C-07` (report-path convention) · `C-30` (topology disposition) · `C-31` (specification reconciliation) · `C-32` (durability of capability-level authorizations). None gates implementation; `C-32` affects how later authorizations are recorded, and `C-31` affects how current status is read.

## G. "Do not reopen" list

These are already closed/ratified. They should not be treated as new PO questions unless new evidence explicitly supersedes them. Authorities are given so each can be checked.

**Global principles and boundaries (I5–I8 PO record §3.1–§3.7; `43f572d`)**
1. I2 authorization as the sole authorization authority; every protected read re-authorizes (B-01).
2. Deterministic data above historical context (B-02).
3. References are locators, never grants (B-03).
4. `public.audit_trail` as the canonical ledger; no second ledger (B-04).
5. The four ratified I3 tools and `ToolStatus` unchanged; no new I3 tool (B-05).
6. I4 contracts as the baseline; no I4 redesign (B-06).
7. Truthful provider attribution; nullable usage/cost acceptable (B-07).
8. The mandatory release chain, including that no stage deploys because code exists (B-08).

**I4 decisions Q1–Q14 (Master Spec §48.5; Q1 closure `CARBONTALLY_P8_I4_Q1_AI_CONTENT_HISTORY_CLOSURE_20260921.md`)**
9. Q1 Option C — `ai_content_history` retained unchanged, outside I4; **its future disposition is deferred, not open** (re-affirmed as I7-C).
10. Q2 canonical audit ledger; Q3 status vocabularies; Q4 raw question persisted once in the I1 message layer with a Layer-2 hash; Q5 append-only/immutable Layer 2; Q6 allowlisted structured projections only; Q7 Layer-2 lifecycle ownership; Q8 **creator-private only** (this disposes of Master Spec §41's "owner/admin shared conversation visibility"); Q9 correlation; Q10 bounded idempotent retry; Q11 provider-unavailable degradation; Q14 provider abstraction/evaluation boundary.
11. Q12 and Q13 are **deferred to I7/I8** — not re-opened here; they are carried as C-13/C-15 and C-18.

**I5 (I5–I8 PO record §4; I5 closure §2–§5; `4887c66`)**
12. I5-1…I5-9 (selection policy, no summarization, 20,000 default budget, no persisted summaries, stale references, bounded tool-result context, audit-is-not-context, empty context, single-conversation scope).
13. **O-1** — 20,000 is a default, **not** an immutable ceiling; the implementation must **not** be given a clamp.
14. O-2…O-6 dispositions (fake-based tests verified live; counts independently confirmed; raw text excluded; question truncation pre-existing; probe defects).

**I6 (I5–I8 PO record §5; I6 closure §E; `67d399f`)**
15. I6-1…I6-10 (entry point, route/nav, creator-private history UX, locator semantics, fourteen-state vocabulary and `no_data ≠ zero`, provider-unavailable presentation, empty/loading/error states, replay presentation, public-assistant separation, accessibility/responsive acceptance).
16. A-1 corrected in documentation only; A-2…A-5 accepted nonblocking **without** remediation. The four §F items are the *only* I6-derived open items (C-09…C-12) — the rest of I6 is closed.

**I7 / I8 boundaries already decided (I5–I8 PO record §6, §8)**
17. I7-A (authorization respected), I7-B (canonical audit separation), I7-C (Option C continued), I7-D (append-only I4 evidence must be respected; controls not bypassed).
18. I8-A principles (rate limiting, observability, provider resilience, deployment discipline) — closed as *principles*; only their numeric/operational parameters remain open (C-19…C-21).

**Evidence / DM-6 policy and capability**
19. DM-6 as the evidence-exposure policy per role, and the restrictive reading enforced on the evidence routes (signed URL/storage path/metadata/page locators at FULL only) — **closed by the verified implementation**; C-01/C-02 ask only whether two specific residual surfaces should be aligned with it.
20. The `page_count` ≠ `source_page` distinction in the calculation write path (forensic `F-B2-7`) — **closed**; C-03 concerns two other surfaces that still infer completeness, not the write path.
21. Reference semantics: an unresolvable reference is compliant, not a defect (I6-4 + I6 OHD §10). Do not reopen this as a defect.
22. The public FAQ assistant is not the Insight UI (I6-9; AGENTS.md §29).

**Repository release authority**
23. The authoritative checkout/remote determination (B-10) — established. C-30 concerns only the *surrounding* divergences, not which branch/remote is authoritative.

**Explicitly not to be treated as open questions**
24. `CT-P8-SPEC-001` §P/§Q items (I1 authorization mechanics, tool catalogue, status vocabulary, dormant-table disposition, privacy/billing, "not one-batch authorisation") — all resolved or superseded (§B.9).
25. Master Spec §47's "I3: IMPLEMENTED — REMEDIATION VERIFICATION PENDING" / "I4–I8: NOT AUTHORIZED" and §48.4's governance note — historical statements superseded for *status* by §3.1 and the closure records (see C-31 for the documentation consequence).
26. The four pre-existing backend unit-suite failures and the two pre-existing frontend suite failures recorded by OHD — pre-existing and unrelated; recorded as environment/backlog facts, **not** PO decisions.
27. `NOT ESTABLISHED AS A PO DECISION` items: OHD §14.6 (implementation-report numeric/inventory inaccuracies), §14.7 (no repository test for the modified customer evidence panel), §14.9 (route wiring asserted structurally because `react-router-dom` cannot be resolved in this environment). These are implementation/documentation/test-coverage tasks for an implementation agent, not PO product decisions.

## H. Evidence quality / uncertainty

### H.1 Classification of every unresolved item

> **Scope note (2026-09-22 closure):** the classifications below record the *evidence quality* of each item **as at the inventory date (pre-closure)**. C-01…C-06 have since been disposed of by the PO decision (see §0) — their rows remain as the historical evidence assessment, not as current status.

| Item | Class | Basis / uncertainty |
| --- | --- | --- |
| C-01 `source_item.file_url` below FULL | **Explicitly documented unresolved decision** | OHD §14.1 states the PO "should ratify or correct it"; re-verified still present at HEAD. No ambiguity in the fact, only in the PO's choice |
| C-02 DM-6 on the documents signed-URL route | **Explicitly documented unresolved decision** | OHD §14.2 states "it is a **PO decision**"; re-verified still present at HEAD |
| C-03 export/reporting completeness | **Documented follow-up requiring PO interpretation** | OHD §14.3 reports the residual as pre-existing and notes the PO's "stated preference to keep exports out of scope"; it does not explicitly demand a decision, so whether it must be decided before closure is a PO reading |
| C-04 403 vs 404 | **Documented follow-up requiring PO interpretation** | OHD §14.4 is conditional ("**If** the PO wants strict non-disclosure"); not an instruction |
| C-05 `raw_description` at CONTROLLED | **Documented follow-up requiring PO interpretation** | OHD §14.5 says the PO "**may wish to ratify** it" and records it as "intentional-looking" — a key-name consequence, not a stated policy |
| C-06 stage closure | **Explicitly documented unresolved decision** | OHD §1/§16: acceptance and closure "remains with the PO"; no document treats the stage as closed |
| C-07 report-path convention | **Documented follow-up requiring PO interpretation** | OHD §14.8: "Harmless, but the PO **may wish** to unify the location" |
| C-08 date/amount discovery | **Explicitly documented as deferred; a decision is required to do anything** | OHD §15 and forensic `M8`/`P-3`; nothing is implemented and nothing is fabricated |
| C-09 `evidence_line_item` resolvability (I3) | **Explicitly documented unresolved decision, with one ambiguity** | I6 closure §F.1 and I6 OHD §10/§26.1 are explicit ("a separate PO decision"). **Ambiguity:** the later non-I3 by-id evidence-line route may satisfy the underlying need; whether it does is a PO interpretation, not a recorded fact |
| C-10 consultant / internal-staff entry point | **Explicitly documented unresolved decision** | I6 closure §F.2: "requires **separate authorization**" |
| C-11 `org_viewer` execution rights | **Explicitly documented unresolved decision** | I6 closure §F.3: "an existing authorization-contract question" |
| C-12 pagination | **Explicitly documented unresolved decision** | I6 closure §F.4: "a bounded follow-on decision" |
| C-13 retention durations | **Explicitly documented unresolved decision** | I5–I8 PO record §6 "Retention"; `NOT YET AUTHORIZED — REQUIRES EXTERNAL DECISION` |
| C-14 deletion semantics | **Explicitly documented unresolved decision** | I5–I8 PO record §6 "Deletion" |
| C-15 export policy | **Explicitly documented unresolved decision** | I5–I8 PO record §6 "Export" |
| C-16 provider / privacy | **Explicitly documented unresolved decision** | I5–I8 PO record §6 "Provider/privacy" |
| C-17 I7 acceptance criteria/package | **Explicitly documented unresolved decision** | Readiness audit §27 item 9 and §28.4 (I7 `NOT READY`) |
| C-18 I8-B commercial set | **Explicitly documented unresolved decision** | I5–I8 PO record §9 |
| C-19 SLOs | **Explicitly documented unresolved decision** | I5–I8 PO record §8 "SLOs" |
| C-20 backup/recovery | **Explicitly documented unresolved decision** | I5–I8 PO record §8 "Backup/recovery" |
| C-21 incident/runbook | **Explicitly documented unresolved decision** | I5–I8 PO record §8 "Incident response" |
| C-22 payment provider | **Explicitly documented unresolved decision (factual first)** | I5–I8 PO record §10; the underlying fact is `UNKNOWN / NOT VERIFIED`, so the PO's first choice is investigate vs exclude |
| C-23 I8 acceptance criteria/prerequisites | **Explicitly documented unresolved decision** | I5–I8 PO record §11; readiness audit §27 item 9 |
| C-24 evidence-viewing commercial posture | **Explicitly documented unresolved decision (finding-level)** | Forensic §32 `P-6`; recorded as a PO question by the forensic audit rather than by a PO record |
| C-25 auditor/PE personas | **Explicitly documented unresolved decision** | Master Spec §41 lists "auditor access" and "PE access" as open "until explicitly closed"; §42 defers the surfaces |
| C-26 rename/archive | **Explicitly documented unresolved decision** | Master Spec §41, §21 |
| C-27 regeneration/edit semantics | **Explicitly documented unresolved decision** | Master Spec §41, §21 (constrained by Q5) |
| C-28 provider selection | **Ambiguous / conflicting historical evidence** | Master Spec §41 lists it as open, while §48.5 Q14 constrains Insight to the existing provider abstraction and no later record closes *selection* |
| C-29 I5 v1 follow-ons | **Documented follow-up requiring PO interpretation** | I5 closure §5 records them as accepted limitations; O-1 clause 9 and O-4 contemplate *future* decisions but mandate none now |
| C-30 repository topology | **Explicitly documented unresolved decision** | Topology reconciliation §13 lists five items; §14 states `TOPOLOGY DIVERGENCE REQUIRES PO DECISION` |
| C-31 specification reconciliation | **Ambiguous / conflicting historical evidence** | Master Spec §47/§41/§48.4 conflict with §3.1/§48.5 and with the closures, which state the historical text is "left **as written**" |
| C-32 authorization-record durability | **Documented follow-up requiring PO interpretation** | Header citations exist in two reports; no committed PO text for the 2026-09-22 capability authorization. The *absence* of such a document is itself `VERIFIED` |

### H.2 Evidence that was checked rather than trusted

* C-01, C-02 and C-03 were re-verified in the current source at HEAD `5d5f7ed` (exact file/line evidence recorded per item). They are **not** stale observations.
* The implementation, documentation, OHD and closure revisions for I2–I6 and for the Source Evidence Viewer were read from the records and cross-checked against `git log` (I6's A-1 correction is why the corrected digest is used here).
* The Master Spec §48.5 table and its three dated stage-status notes were read in full rather than inferred.

### H.3 Where the evidence is insufficient or ambiguous — stated explicitly

1. **The exact PO text of the 2026-09-22 capability authorization is not in the repository.** Both the implementation report and the verification report cite it as their mandate, and the implementation report states its delivered and excluded scope; but no committed document contains the PO's own wording. Consequently, whether forensic `P-2` (line-level location), `P-4` (shared viewer) and `P-7` (historical-row handling) were *decided as PO policy* or implemented as reasonable means within a broader mandate is **`INFERENCE`, not `VERIFIED`**. Recorded as C-32. This does not affect what was implemented (which is verifiable) — only how strongly the PO's intent can be quoted.
2. **C-09's standing after the viewer work is genuinely ambiguous.** The I6 record (closed) says making `evidence_line_item` resolvable requires an I3 decision; the later evidence work added a by-id **customer route** (not an I3 tool). Whether the I6 follow-up is now satisfied, still open, or should be re-scoped is a PO interpretation, and both readings are defensible from the committed text.
3. **C-03's framing is a PO choice, not a fact.** The OHD report supports both a "keep exports out of scope" reading (citing the PO's stated preference) and the observation that the `page_count`/`source_page` distinction "is not yet uniform platform-wide". The dependency on export policy (C-15) exists only under the first framing.
4. **C-28 (provider selection) cannot be resolved from the documents.** §41 says open; Q14 constrains the abstraction without closing selection; no closure record mentions it.
5. **Master Spec §41 is demonstrably stale in part.** Several bullets have since been closed (owner/admin shared visibility → Q8; raw question vs hash → Q4; answer-status enumeration → Q3; context/compaction policy → I5-1…I5-9; dormant AI structure → Q1/I7-C; AI credits → Q13/I8; SLO targets → C-19; consultant/staff/auditor/PE → I6 §F and §42). A reader must treat §41 as *indicative* and use §48.5 plus the closure records for status. Recorded as C-31.
6. **Deployment state is `UNKNOWN`.** Topology reconciliation §14 records Render, Vercel and production-migration state as `UNKNOWN` (no access, no repository manifest, no authorised read-only inspection path). Nothing in this inventory should be read as evidence about production.
7. **Pre-existing test failures** (the four backend unit-suite failures identified as `review_sla_surfaces` and the D17 migration-count test, and the two frontend suites) are recorded by OHD as pre-existing and unrelated. They are environment/backlog facts and are **not** established as PO decisions.
8. **No production data, database or runtime state was inspected or modified** by this audit; the findings above are documentary and code-inspection findings only.

---

## I. Repository and report record

| Item | Value |
| --- | --- |
| Authoritative checkout | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| Remote used for the push | `github` → `https://github.com/shomonrobie/CarbonTally.git` |
| **Starting HEAD** | `5d5f7ed94c5821894e8eac6d05ad9af83138746e` |
| Tree state at start | clean; `HEAD...github/p8-release-reconciled` = `0 0` |
| Report path | `docs/architecture/CT-P8-PO-DECISION-INVENTORY-20260922.md` |
| **Commit SHA (this report)** | `910b1849cec3f81e862af3969e452a2b8f71b4f1` — "docs(p8): PO decision inventory / historical context audit"; this commit adds **only** this report file |
| **Ending HEAD** | the documentation follow-up that records this table (SHA reported in the task response and verifiable with `git log -1 --format=%H`) |
| Push result | **pushed** to `github/p8-release-reconciled`: `5d5f7ed..910b184 p8-release-reconciled -> p8-release-reconciled`; alignment after push `HEAD...github/p8-release-reconciled` = `0 0`; working tree clean |

**Changes made by this task:** this report file only. No application code, backend, frontend, test, schema, migration, configuration, RLS, contract, tool, endpoint or runtime behaviour was modified; no branch was created; no other checkout was touched. The unrelated `main` working checkout (`/home/shomonrobie/carbon_tally`, dirty) and the stale `origin` remote (`/tmp/ct_step2`) were **inspected only** — their disposition is C-30.

**Status statement.** This document is an inventory. It sets no status, closes nothing, authorizes nothing, and makes no product recommendation. Every status quoted here belongs to its authoritative record named alongside it.
