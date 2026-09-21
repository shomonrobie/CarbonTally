# CT-P8-I3 — CarbonTally Insight Controlled Read-Only Tools

**Authorization:** PO I3 authorization decision (2026-09-21) — *"I3 IS AUTHORIZED TO BEGIN — WITH THE ABOVE BOUNDED SCOPE ONLY."* Predecessors: I1 closed/verified; **I2 CLOSED — VERIFIED PASS at `177dff5`** (OHD re-verification `a11c7d5`; PO closure `551f121`).
**Branch / baseline:** `p8-release-reconciled` @ `985365b97274888283ec749d9640699cb0868a6c` (`985365b`, authoritative release checkout `/home/shomonrobie/ct_93d5cdd`; the exact baseline SHA is recorded in §9).
**Type:** stage inspection + decision-required report. **No application code was written or modified.**
**Stage verdict:** `I3 BLOCKED — PO DECISION REQUIRED (initial read-only tool catalogue)`

---

## 1. Authorized I3 scope (as given)

Controlled read-only Insight tools; intent classification; tool registry; initial approved read-only tools; tool/reference definitions; deterministic-first execution; authorization-aware invocation through the **established I2 boundary**; structured result handling sufficient to support later answering.

Explicitly excluded by the authorization: final natural-language answering, broad LLM/provider integration, RAG, LangChain, embeddings/vector search, broad context/memory, frontend UI, retention/export, billing, automatic consequential actions, auditor/PE/public Insight access — and: *"Do not expand the initial tool catalogue without a separate PO decision."*

## 2. Governing authority inspected

* `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` — §4.3 (representative intended questions, *illustrative only*), **§4.4**, §4.5, §8 (authorization boundary), §11 (deterministic-first), §12 (RAG deferred), §13 (LangChain deferred), §16 (threat model), §17 (tool-call provenance), §23.2 (I3 stage definition), §24.3–§24.5.
* `docs/architecture/CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` — **§30.3** (normative assistant rules) and **§30.4** (recommended tool contract additions, which state *"Do not implement."*).
* D1 persistence/auditability discovery (`…ASK_CARBONTALLY_PERSISTENT_CONVERSATION_AND_AI_AUDITABILITY_DISCOVERY_20260912.md`) — referenced by §30.4 as the source of "the tool concept".
* The closed I1/I2 implementation (persistence foundation + authorization boundary) and the existing authoritative read-only repository surface (§5).

## 3. Blocking finding — the initial tool catalogue is **not** ratified

D2 §4.4 is normative and explicit:

> **The exact future tool catalogue remains an implementation/design concern and MUST NOT be invented during this ratification task.**

D2 §4.4 *does* ratify the **constraints** any catalogue must satisfy (controlled and server-side; read-only initially; authorization-checked against the caller's current scope; returning **only** fields the caller's role may already see; report-reading tools additionally satisfying `REPORTING_LIFECYCLE_SPEC` §30.3 with version+state stated and every report-reading call audited). It does **not** name a single tool.

Repository search for a ratified catalogue (or any ratified initial tool list):

* `grep -rln 'tool catalogue|tool registry|tool_catalogue|tool_registry' docs/` → the phrase appears only in **incidental** documents (the P8X feature audit, prompt-history records, I1/I2 verification reports, this proposal's predecessors). **None of them ratifies a catalogue.**
* `REPORTING_LIFECYCLE_SPEC` §30.4 lists three *recommended* report tools (`report_lookup`, `report_version_lookup`, `report_evidence_lookup`) and then states **"Do not implement. This section constrains a future implementation."** — a recommendation, not a ratification.
* Backend search for existing Insight tool artefacts (`tool_registry`, `intent_classif`, `insight_tool`) → **none exist**.

Therefore the PO's authorization condition *"Do not expand the initial tool catalogue without a separate PO decision"* presupposes an initial catalogue that the repository does not contain. Per the standing governance rule for this workstream — *"Where the specification deliberately leaves the final catalogue undecided: **STOP and report the decision required**"* — and D2 §4.4's express prohibition on inventing the catalogue, **I have not invented one**, and no tool, registry entry, intent mapping or reference definition has been created.

## 4. What was deliberately NOT implemented (and why)

| Authorized I3 element | Status | Reason |
| --- | --- | --- |
| Initial approved read-only tools | **NOT IMPLEMENTED** | the catalogue is not ratified (D2 §4.4); implementing named tools would invent requirements |
| Tool/reference definitions | **NOT IMPLEMENTED** | a tool definition (name, inputs, output fields, reference kind) is precisely what §4.4 defers; §4.4 also fixes field-visibility and report-state rules per tool |
| Tool registry | **NOT IMPLEMENTED** | a registry is a container of tool definitions; shipping it with invented entries would embed the unratified decision, and shipping it empty cannot be verified against I3's "initial read-only tools" or "deterministic path" |
| Intent classification | **NOT IMPLEMENTED** | an intent taxonomy is meaningful only against a ratified tool set (mapping utterances → tools) |
| Deterministic-first execution path | **NOT IMPLEMENTED** | the deterministic path *is* the tool invocation chain; without ratified tools there is nothing to execute |
| Structured result handling for later answering | **NOT IMPLEMENTED** | its shape is a function of the ratified tool outputs and reference semantics |

Also **not** created, per the authorization's exclusions: no LLM/provider integration, no prompts, no answering, no RAG/LangChain/embeddings, no context, no UI, no retention/export, no billing, no automatic actions, no auditor/PE/public access.

**No application file, migration, test or configuration file was modified by this task.** The I2 authorization boundary (`backend/api/insight_authz.py`) was **inspected only** and is unchanged.

## 5. Read-only capability inventory (what a ratified catalogue could wrap)

Verified present in the repository (read-only inspection, method in §9). No "new build" is implied by any of these
— D1 classifies them as REUSE sources:

| Authoritative source | Shape |
| --- | --- |
| `domain/calculation.py` → `CalculationSnapshot` | authoritative emissions value with `content_hash`, factor provenance, `source_item_id`, source file/page (D1 §6.4 "the ideal tool result and natural provenance reference") |
| `backend/data/emissions_logs.py` | 17 repository methods (persisted emissions results) |
| `backend/data/emission_factors.py` / `customer_factors.py` | 10 / 8 methods (factor provenance; customer-factor precedence per AGENTS.md §15) |
| `backend/data/evidence_line_items.py` | 11 methods (immutable line-level evidence/provenance) |
| `backend/data/disclosure.py` / `disclosure_projection.py` | 24 / 18 methods (disclosure/evidence projection) |
| `backend/data/issues.py` / `review_queue.py` | 12 / 8 methods (blocking issues; review/workflow state) |
| `backend/data/manual_extraction.py` | 56 methods (extraction/line items feeding calculation) |
| `report_generation_queue` + `backend/data/report_versions.py` | report instances/versions — constrained by `REPORTING_LIFECYCLE_SPEC` §30.3/§30.4 |

## 6. The PO decision required (decision instrument)

To unblock I3, a single ratification covering the following is required. Each item is currently **deferred** by the
ratified authority, so none may be assumed:

1. **The initial read-only tool set.** D2 §4.4 does not name a single tool. Two repository-sourced candidates exist to
   ratify from (or amend):
   * the **D1 §7.1–7.3 tool concept** — a *persona* tool registry plus a **six-point tool contract** (D1 is
     proposal-only and self-declares as not ratifiable on its own);
   * the **three report tools recommended by `REPORTING_LIFECYCLE_SPEC` §30.4** (`report_lookup`,
     `report_version_lookup`, `report_evidence_lookup`), which that document marks *"Do not implement."*
   and, if a *direct factual* tool is wanted for D2 §4.3's illustrative intents, an explicit emissions/snapshot tool
   (the `CalculationSnapshot` path above).
2. **Whether the six-point tool contract (D1 §7.3) is adopted as the I3 contract** or replaced by a narrower one.
3. **Per-persona field visibility** — D2 §4.4 requires tools to return *only* fields the caller's role may already
   see; the concrete field allowlists per persona are not ratified.
4. **Reference semantics** — what a stored reference may point at, and how re-resolution is proven (D2 §8.4 requires
   re-resolution against current authorization; §17.4 gives illustrative targets only).
5. **Status vocabulary for I3's deterministic path** — D2 §11.4 requires distinct states (zero / no data / not
   authorized / provider-unavailable), while D2 §11.6 **defers the exact taxonomy**; the subset I3 may emit needs
   ratification.
6. **Report-reading behaviour** — whether §30.3's normative assistant rules bind the I3 tools now (version+state
   stated; never present non-`FINAL` as approved; every report-reading call audited), and whether "audited" here means
   the I4 canonical audit (not yet authorized) or a lesser I3 record.

## 7. Bounded implementation that would follow ratification (not started)

Once (and only once) the above is ratified, the following is implementable **without** any LLM/provider, and is what a
future I3 prompt should authorize: a server-side tool **registry** holding ratified definitions; **intent classification**
mapping utterances to those tools; **deterministic execution** through the I2 boundary (`authorize_insight_scope` →
`InsightAccess`; never a stored id as a grant); **structured results** with references; explicit refusal for
unsupported/no-data/unauthorized outcomes; and tests covering ALLOW/DENY per persona, per-tool authorization, invalid
inputs, bounded outputs, deterministic repeatability, reference re-resolution, and no arbitrary query execution.

## 8. Boundary with the closed stages (unchanged by this task)

* I2 remains authoritative for **all** access decisions; nothing in I3 may widen it, cache it, or let the LLM or a
  stored reference decide access.
* `backend/api/insight_authz.py` was **inspected only** — unchanged (personas: customer own-active-org, consultant via
  the existing `consultant_clients` grant, internal staff bound to existing staff permissions, explicit auditor refusal,
  PE/public denied, creator-private visibility).
* I1 persistence and the I2 API surface are unchanged.

## 9. Evidence and method (read-only)

| Evidence | Method |
| --- | --- |
| D2 §4.3/§4.4/§4.5, §23.2 stage table | read-only document reads (`sed`/`read`) |
| Reporting lifecycle §30.3/§30.4 | read-only document read (lines 1439–1472) |
| D1 tool concept (persona registry, six-point contract, staged deterministic rollout) | read-only grep of the D1 discovery document (lines 33–34, 206–207, 330, 585, 638–640, 708–713, 741) |
| No ratified catalogue anywhere | `grep -rln 'tool catalogue\|tool registry\|tool_catalogue\|tool_registry' docs/` (incidental mentions only) |
| No existing Insight tool code | `grep -rln 'tool_registry\|intent_classif\|insight_tool' backend/ --include='*.py'` → none |
| Read-only source inventory | file existence + `async def` counts + `grep 'class CalculationSnapshot'` |
| Baseline revision | `git rev-parse HEAD`, `git status --porcelain`, `git ls-remote github refs/heads/p8-release-reconciled` |

No secret was read or printed; no provider, network or database call was made.

## 10. Stage status and governance

* **I3: NOT IMPLEMENTED — blocked on a PO decision (§6).** No tool, registry, intent map, reference definition, LLM
  integration, answering path, UI, retention, billing or automatic action exists as a result of this task.
* **No application change**: this task's only repository change is **this report** (documentation-only), committed and
  pushed from the authoritative release checkout to `github/p8-release-reconciled`. No branch switch, merge, rebase,
  reset, force-push, remote change or worktree cleanup was performed; the deferred topology items were not touched.
* **No deployment and no production change** of any kind (no Render/Vercel action, no migration, no production access).
* I2 remains closed and verified at `177dff5`; I4+ remain unauthorized.

## 11. Verdict

`I3 BLOCKED — PO DECISION REQUIRED (initial read-only tool catalogue)`

Nothing further will be implemented, committed as implementation, or advanced until the PO ratifies the items in §6.
This report is the decision-ready input for that ratification; on receipt of the decision, I3 can proceed within the
bounded scope of §7 without any redesign of the closed I1/I2 foundation.
