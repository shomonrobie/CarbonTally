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

---

# 13. I3 IMPLEMENTATION (PO tool catalogue ratified)

**Authorization:** PO I3 Tool Catalogue Ratification Decision Record (2026-09-21) —
*"I3 IS AUTHORIZED TO BEGIN"*; four tools RATIFIED; six-point contract adopted;
references are locators; status vocabulary fixed; report-reading §30.3 adopted; I4+ not authorized.
**Implementation baseline:** `bfcb04c4a59a3ff6c6bd627d35c7fbd939c30a63` (`bfcb04c`) on `p8-release-reconciled`.
**Stage verdict (this section):** `I3 IMPLEMENTED — READY FOR INDEPENDENT OHD VERIFICATION` (not closed by Cline).

This section supersedes the *stage* verdict of §11 for the implementation attempt it describes;
the §1–§10 record above is retained unchanged as the decision history that produced the ratification.

## 13.1 Files created / modified

| File | State | Purpose |
| --- | --- | --- |
| `backend/domain/insight_tool.py` | **new** (160 lines) | Six-point contract types: `ToolStatus`, `InsightReference`, `ToolInputSpec`, `ToolDefinition`, `ToolResult`, `bounded()`, `TOOL_CONTRACT_VERSION = i3-6point-v1`. Pure types — no I/O. |
| `backend/services/insight_tools.py` | **new** (354 lines) | The four ratified tool definitions, the registry, deterministic intent classification, input validation, the deterministic execution path, and the four read-only runners with field projection. |
| `backend/api/v3_insight_tools.py` | **new** (70 lines) | The I3 HTTP surface: `GET /api/v3/insight/tools`, `POST …/tools/invoke`, `POST …/tools/intent`. Router-level I2 gate. |
| `backend/api/router.py` | modified (+2 lines, comment + include) | Mounts the I3 router on the V3 composition root. No existing route changed. |
| `backend/tests/unit/api/test_v3_insight_i3_tools.py` | **new** (490 lines) | The I3 verification suite (30 tests). |
| `docs/implementation/phase8/CT-P8-I3-INSIGHT-TOOLS-20260921.md` | modified | This report. |

**The closed I1/I2 foundation was not modified**: `backend/api/v3_insight.py`,
`backend/api/insight_authz.py`, `backend/data/insight.py`, the I1/I2 migrations and the
I2 tests are byte-unchanged. I3 consumes the I2 boundary through its public entry points only.

## 13.2 The four ratified tools (PO §3/§4)

| Tool | Input (required / optional) | Output allowlist basis | References returned |
| --- | --- | --- | --- |
| `report_lookup` | `report_id` | `api.contracts.ReportOut` subset + version summary + `current_version` + `is_approved_or_final` | `report`, `report_version` |
| `report_version_lookup` | `version_id` **or** `report_id` + `version_number` | report-version identity/state columns | `report_version`, `report` |
| `report_evidence_lookup` | `report_version_id` | disclosure projection (line identity/coverage) | `report_version`, `evidence_line_item`, `calculation_snapshot` |
| `calculation_snapshot_lookup` | `snapshot_id` | ratified `CalculationSnapshot` provenance set (PO §3.4) | `calculation_snapshot`, `evidence_line_item` |

`GET /api/v3/insight/tools` exposes exactly these four definitions (names, purpose,
read-only flag, inputs, authorization, output fields, reference kinds, statuses). No other tool
exists, and the registry is a closed dict — an unratified name returns `invalid_input` /
`unratified_tool` rather than being dispatched.

## 13.3 Six-point contract → implementation (PO §5)

| Point | Implementation |
| --- | --- |
| 1 identity | `ToolDefinition.name/purpose/read_only`; registry is a closed 4-entry dict |
| 2 input | `ToolInputSpec` (required/optional) + `_validate_input()`: unknown parameter → `unknown_parameter`; missing required → `missing_required_parameter`; non-string/non-int → `invalid_parameter_type`; >124 chars → `parameter_too_long`; non-numeric version number → `invalid_version_number`; input size bounded by those rules |
| 3 authorization | every invocation calls `authorize_insight_scope(...)` (the closed I2 layer) and then re-checks the **resolved object's** organisation; a stored id/reference is never a grant |
| 4 output | explicit allowlists (`_REPORT_FIELDS`, `_REPORT_VERSION_FIELDS`, `_EVIDENCE_LINE_FIELDS`, `_COVERAGE_FIELDS`, `_SNAPSHOT_FIELDS`); `_project()` never passes a stored row through — it copies only allow-listed keys |
| 5 reference | `InsightReference(kind, id)` restricted to `REFERENCE_KINDS` (unratified kind raises at construction); results carry locators only |
| 6 failure/status | `ToolResult(status, reason, data, references, truncated)` + `ToolStatus`; no fabricated data; no silent fallback |

## 13.4 Field allowlists — documented mapping (PO §7)

* **Report** (`report_lookup`): `id, organization_id, report_type, reporting_year, report_name, status,
  created_at, completed_at` + `versions[]`, `current_version`, `is_approved_or_final`.
  **Omitted deliberately:** `final_report_url`/`storage_url` (signed/artefact URLs — AGENTS.md §68),
  `user_id`/`created_by`/`updated_by` (internal actors), `generated_content`/`user_edits`/`metadata`/
  `error_log` (unbounded or internal), `template_id`/`data_sources`/`progress_percentage`/`current_step`.
* **Report version**: `id, report_id, version_number, status, is_current, created_at`.
  **Omitted:** `content`, `file_url`, `file_name`, `created_by`, `notes`, `change_summary`.
* **Evidence line**: `disclosure_value_id, requirement_version_id, calculation_snapshot_id,
  evidence_line_item_id, line_number, materialisation_kind` + coverage counts
  (`reference_count`, `line_linked_count`, `snapshot_linked_count`).
  **Omitted:** `raw_description`, `raw_quantity`, `raw_unit`, `source_page` (extracted source content
  is not established as caller-visible for this tool — omitted rather than inferred).
* **Calculation snapshot** (ratified PO §3.4 set): `id, organization_id, activity, activity_type,
  quantity, quantity_unit, co2e_multiplier, co2e_kg, scope, date, reporting_year, methodology,
  algorithm_version, content_hash, factor_id, factor_kind, customer_factor_id, factor_source,
  source_item_id, source_line_item_id`.
  **Omitted:** `calculated_by`/`performed_by` (internal actors), `request_id`/`import_batch_id`/
  `factor_set` (internal ingest identifiers), `source_file`/`source_page` (not named in the ratification).

Where visibility was not established by an existing, already-authorized projection, the field was
**omitted** — the compliant course under PO §7 — so no unresolvable field-visibility decision arose and
no PO stop condition was triggered.

## 13.5 References and re-resolution (PO §8)

References are locators only, typed to the four ratified domains. Every invocation re-derives the
caller's scope through I2 and re-checks the resolved object's organisation, so a reference that was
valid earlier does not carry authority forward: a revoked consultant grant, a removed membership, a
suspended organisation or another organisation's id all resolve to `not_authorized` with no data
returned (`data == {}`, `references == []`).

## 13.6 Status vocabulary and report-reading behaviour (PO §9/§10)

`success`, `no_data`, `not_authorized`, `invalid_input`, `error` are implemented; `provider_unavailable`
is declared but never produced (the four tools are not provider-dependent). Intent refusals
(`unsupported_intent`, `ambiguous_intent`) use `invalid_input` — no new status category was introduced.

For the three report tools the result always states the version identity **and** lifecycle state, and
`report_lookup` computes `is_approved_or_final` from the ratified immutable set
(`IMMUTABLE_REPORT_VERSION_STATUSES = ("APPROVED", "FINAL")`), so a `DRAFT`/`REVIEWED`/
`CHANGES_REQUESTED`/`REJECTED` current version is never presented as approved or final.

## 13.7 Deterministic intent classification (PO §12)

Keyword routing only — no LLM, no provider, no generation. Most specific intents first; a match on
two tools is refused as `ambiguous_intent`. Example routes: "show me the report for 2025" →
`report_lookup`; "which version is current" → `report_version_lookup`; "show the evidence behind
this number" → `report_evidence_lookup`; "what emission factor was used" →
`calculation_snapshot_lookup`.

## 13.8 Execution path (PO §13)

`request → deterministic intent classification → ratified tool selection → input validation → I2
authorization → deterministic domain/data read (existing repositories/projections only) → bounded
structured result → references + status`. No SQL is composed by the tool layer, no arbitrary query or
code execution exists, no provider is called, and nothing mutates business state (proved structurally:
the service module contains no `INSERT`/`UPDATE`/`DELETE`/`save_snapshot`/`set_status` statement).

## 13.9 Audit boundary (PO §11)

No I4 functionality was implemented. Every result carries a deterministic structured `invocation`
record (`tool`, `contract_version`, `status`, `authorization: "i2-boundary"`, `reference_kinds`) so a
later canonical audit can persist the invocation **without redesigning the tool contract**. Canonical
audit persistence itself (including the §30.3 "every report-reading tool call must be audited"
requirement) remains I4 and is therefore **not** implemented.
