# Gap 5 — Conversational AI / Copilot: Current State Research

**Prompt ID:** CT-GAP5-CONVERSATIONAL-AI-RESEARCH-2026-09-30-001
**Repository:** /home/shomonrobie/ct_93d5cdd
**Date:** 2026-09-30
**Mode:** READ-ONLY

---

## 1. Executive Summary

- **Overall stage: SUBSTANTIALLY BUILT — a full conversational-AI surface already
  exists under the repo's own product name ("CarbonTally Insight", phases I1–I6),
  wired end to end: bounded conversation persistence, server-side authorization,
  a closed deterministic read-only tool catalogue, an LLM-narration interaction
  stage, bounded follow-up context, structured evidence **references**, and an
  append-only audit trail.** This is materially more than the gap table assumes
  ("CarbonTally has AI runtime (FTR-270) but no conversational interface"). The
  conversational interface is present in code and UI:
  1. **query understanding** — a deterministic planner + keyword classifier
     (`services/insight_query_planner.py`, `services/insight_tools.py`), which
     deliberately never uses the LLM as a query engine (PO D-01);
  2. **scoped data access** — the closed I2 authorization boundary
     (`api/insight_authz.py`) plus organization-scoped repositories and RLS;
  3. **response generation** — provider narration over the tool's declared output
     (`services/insight_interactions.py`), with structured **references** returned
     as evidence locators;
  4. **follow-up query support** — conversations/messages (I1) + bounded,
     deterministic context assembly (I5, `services/insight_context.py`);
  5. **audit trail for every AI query** — append-only Layer-2
     `carbontally_insight_interactions` / `carbontally_insight_tool_calls` **plus**
     a canonical `public.audit_trail` event (`AuditLogger`).
- **What the gap names that is genuinely ABSENT or only PARTIAL.**
  1. **On-demand chart generation is ABSENT.** No chart/visualization is produced
     by, or rendered inside, the conversational surface. The Insight UI renders
     **tables only** (`frontend/src/v3/insight/InsightComparison.jsx:163`); the
     only charting in the codebase is a fixed emissions-trend bar chart in the
     customer dashboard (`frontend/src/v3/customer/DashboardPage.jsx:14-15,185`),
     which is neither conversational nor on-demand.
  2. **The "critical guardrail" — every AI response must include evidence
     citations — is only PARTIAL.** The backend returns typed reference locators
     and the narration prompt *instructs* the model not to invent citations
     (`services/insight_interactions.py:82-88`), but there is **no machine
     enforcement binding each narration sentence to a reference**; citations are a
     returned side-channel (`references[]`), not a verified per-claim binding.
  3. **The audit trail does NOT reuse `ai_content_history` (contrary to the gap's
     stated reuse).** `ai_content_history` is a **dormant, deliberately
     untouched** table (D2 §22); the I1/I2/I4 migrations explicitly refuse to
     reuse or alter it. Auditability is delivered through the new
     `carbontally_insight_*` tables + `audit_trail` instead.

- **Repo-language note on the gap label.**
  - The string **"Gap 5"** in this repository does **not** refer to conversational
    AI. The only in-repo `Gap 5` is an unrelated regulatory-verification item:
    `docs/architecture/CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md:769`
    ("Gap 5 — Irish competent authority: PARTIALLY VERIFIED"). `FTR-GAP-5` is a
    different, unrelated traceability gap ("features living only in the 43
    unapplied migrations", `docs/architecture/CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md:445`).
    The "internal gap reference: Gap 5" is therefore an **external programme label
    not recorded in this repository** (same situation as the Gap 4 and Gap 6
    passes).
  - **"Copilot" is an explicitly forbidden product name.** The ratified product
    decision D2 §3.5 (`INS-D2-F26`) states: **"CarbonTally Copilot" must not be
    used as the product name** (`docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md:175`).
    The shipped product name is **"Ask CarbonTally" / "CarbonTally Insight"**
    (`docs/cline/prompt-history/CT-P8-CARBONTALLY-INSIGHT-D2-PO-RATIFICATION-20260912.md:70-72`).
    Any Gap 5 build must respect that naming constraint.
  - **Feature-ID numbering caution.** The FTR IDs in the gap prompt align with the
    **feature catalogue** (domain 37, `FTR-234…242`), e.g. `FTR-236` = Insight tool
    catalogue, `FTR-240` = Insight data-quality/reproducibility, `FTR-241` = Insight
    customer UI (page, **references**, answer-state model), `FTR-242` = Insight AI
    content history, `FTR-270` = LLM/AI runtime. A **second** doc
    (`CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md:171-177`) uses an
    **offset numbering** for the same domain (it maps temporal comparison to
    `FTR-242`, whereas the catalogue maps it to `FTR-239`). The catalogue is treated
    as authoritative below; the discrepancy is flagged as a consistency risk (§8).

- **Highest-risk unknowns.**
  1. **Schema durability — the dominant risk.** Every Insight surface is catalogued
     `IMPLEMENTED_AND_WIRED` **but `BLOCKED_BY_SCHEMA`**: the I1/I2/I3/I4/P2/P3
     tables are recorded **ABSENT in the flagship environment** and present only in
     clones/qa (`docs/architecture/CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md:124-131`,
     `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:658`).
     The conversational interface exists in Git; whether it has **any durable
     database** is not determinable by static inspection. No DB connection was
     attempted for this pass.
  2. **Whether an LLM provider is actually configured in any environment.** The
     narration path is **environment-gated** (`CARBONTALLY_AI_BASE_URL` /
     `CARBONTALLY_AI_API_KEY` / `CARBONTALLY_AI_MODEL`); with no provider the
     system returns the deterministic answer with `narration_state = skipped`
     (`services/insight_interactions.py:184-199,555-560`). The "conversational"
     experience therefore degrades to structured evidence unless a provider is set.
  3. Whether an unmerged/conversational branch or a second repository exists outside
     this tree — not determinable from this workspace.

- **Estimated build distance.** **Small-to-medium, and mostly hardening, not
  greenfield.** The conversational spine (I1–I6) already exists. The named gap
  components that remain are: (a) an **on-demand chart/visualization layer** over
  the existing aggregate tool output (new, frontend-heavy); (b) **hard
  evidence-citation enforcement** on narration (new backend guard); and (c)
  reconciling the **audit-trail target** (the gap says `ai_content_history`, the
  build uses insight tables + `audit_trail`) and **applying/confirming the blocked
  schema** (ops). The reuse targets the gap names (AI runtime, tool catalogue,
  references, data quality) are present and wired. The binding constraint is not
  engineering effort but the **schema/environment gap** and the **naming/guardrail
  PO decisions**.

---

## 2. Component-by-Component Findings

### 2.1 Natural-language query → structured query against evidence data
- **Classification: IMPLEMENTED_AND_WIRED (deterministic; the LLM is deliberately
  NOT the query engine).**
- **Evidence:**
  - Deterministic bounded planner: `services/insight_query_planner.py`
    (module header `:1-20`: "**deterministic regular-expression parsing only** …
    no provider/LLM call, no database access, no SQL, no authorization decision");
    `plan_question(...)` at `:381`; four statuses `planned`/`clarification`/
    `invalid`/`unsupported` (`:42-45`).
  - Ratified four-tool keyword classifier: `services/insight_tools.py:381`
    (`classify_intent`), keyword table at `:373-378`; HTTP surface
    `POST /api/v3/insight/tools/intent` (`api/v3_insight_tools.py:105`).
  - The planner emits only the **closed** schema from `domain/insight_query.py`
    (imports at `services/insight_tools.py:38-60`), and every produced parameter is
    re-validated inside the tool before any read (`services/insight_tools.py:459-508`).
  - Free-text is bounded: `MAX_QUESTION_LENGTH = 2000`
    (`domain/insight_interaction.py:33`); UUID extraction only
    (`services/insight_interactions.py:209-211`).
- **Gaps and unknowns:** No natural-language *semantic* parsing (by design — the
  LLM must never become a query engine, `services/insight_query_planner.py:3-5`).
  A question outside the closed vocabulary returns `unsupported`, and the caller
  falls back to the four-tool keyword classifier — never to a generated query.

### 2.2 Scoped data access (gap reuse: authorization FTR-031, RLS FTR-030)
- **Classification: IMPLEMENTED_AND_WIRED.**
- **Evidence:**
  - **FTR-031** (server-side role/authorization guards): the single Insight entry
    point `api/insight_authz.py` — router gate `require_insight_user` (`:184`),
    scope resolver `authorize_insight_scope` (`:206`), persona decision table
    (`:93-101`), explicit auditor refusal (`:243-246`), PE refusal (`:200-202`).
    Catalogue row `FTR-031` lists `insight_authz.py` among the guard modules
    (`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:285`).
  - **Defence in depth:** the service-role pool bypasses RLS, so every repository
    read is **explicitly** `organization_id`-scoped
    (`data/insight.py:8-14`, `:110-270`), and creator-private visibility is
    re-applied per request (`api/insight_authz.py` + `api/v3_insight.py:97-117`).
  - **Tool-level scope:** `invoke_tool` re-resolves the caller's scope through the
    closed I2 boundary on **every** invocation and re-checks each object's
    organisation (`services/insight_tools.py:447-508`; e.g. `:524-525`, `:598-599`).
  - **FTR-030** (RLS): the Insight tables carry explicit RLS policies in their own
    migrations (e.g. I1 posture stated at
    `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql:30-38`);
    the platform-wide RLS isolation is `FTR-030`
    (`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:284`).
- **Gaps and unknowns:** RLS/guard code is present; the **applied state** of the
  policies is unverified (see §1 risk 1). Staff/consultant scope over Insight is
  present but creator-private (D2 §9.2) — staff cannot read another user's
  conversations; whether that matches a future "ops Copilot" intent is a PO decision.

### 2.3 Response generation with citations to source records
- **Classification: PARTIALLY_IMPLEMENTED (narration + typed references exist;
  *enforced* per-claim citation does NOT).**
- **Evidence:**
  - **Narration:** `run_interaction(...)` builds a bounded prompt from the tool's
    **declared output only** (`services/insight_interactions.py:228-241,547-612`),
    with the system prompt forbidding invented citations: `_SYSTEM_PROMPT`
    (`:82-88`) — "Never invent … citations … If the evidence does not establish
    something, say so plainly." Provider is the existing `LLMClient`
    (`infra/llm_client.py:44,90`); temperature 0.0; failure is a truthful
    `narration_state = unavailable` (`:603-607`), never a fabricated answer.
  - **Citations as structured references:** each tool returns typed
    `InsightReference` locators (`domain/insight_tool.py:63-79`, allowed kinds
    `:55-60`: `report`, `report_version`, `evidence_line_item`,
    `calculation_snapshot`); these are persisted per tool call
    (`services/insight_interactions.py:510-529`) and returned in the outcome
    (`references`, `:700`; contract `domain/insight_interaction.py:98-104`).
  - **Rendered in UI:** `frontend/src/v3/insight/InsightReferences.jsx`
    (built from `referencesFromDetail`, `InsightInteraction.jsx:41-54`), reaching
    the shared Source Evidence Viewer (`frontend/src/App.js:2079-2089`).
  - The narration text is persisted as a conversation message with role
    `"insight"` (`services/insight_interactions.py:634-642`).
- **Gaps and unknowns:** There is **no machine verification** that the narration
  text cites the evidence it was given, and no per-claim reference binding. The
  guardrail "all AI responses must include evidence citations" is satisfied at the
  **structured-output** level (references are always returned and displayed) but
  **not** at the **natural-language** level. Confirming whether the structured
  reference set is an acceptable "citation" is a PO decision.

### 2.4 On-demand chart and table generation
- **Classification: PARTIAL — TABLE generation exists (one view); CHART
  generation is ABSENT in the conversational surface.**
- **Evidence:**
  - The only table the Insight conversation renders is the temporal-comparison
    detail: `frontend/src/v3/insight/InsightComparison.jsx:55` (re-reads the tool
    on demand), `<table className="ct-table …">` at `:163`. No chart is rendered
    anywhere under `frontend/src/v3/insight/**` (search for
    `chart|Chart|recharts|ResponsiveContainer` returns only the `<table>` hit).
  - The only charting in the entire codebase is the fixed customer-dashboard
    emissions-trend bar chart, which is **not** conversational and **not**
    on-demand: `frontend/src/v3/customer/DashboardPage.jsx:14-15` (recharts
    import) and `:183-186` (`<ResponsiveContainer>` / `<BarChart>`).
  - The aggregate tools already produce chart-ready structured data (grouped
    totals): `insight_aggregation` and `insight_temporal_comparison`
    (`services/insight_tools.py:170-274`, basis `_BASIS_CO2E` `:619`), but no
    rendering layer consumes them as charts.
- **Gaps and unknowns:** No on-demand chart generation endpoint or component; no
  "make a chart of this" intent in the planner. The reporting intelligence API
  (FTR-216, §2.10) provides aggregate series a chart layer could reuse.

### 2.5 Follow-up query support
- **Classification: IMPLEMENTED_AND_WIRED.**
- **Evidence:**
  - Conversation/message persistence: I1 tables + repo
    (`data/insight.py:111-270`; `api/v3_insight.py:120-238`); messages ordered by
    an atomic 1-based `ordinal` (`data/insight.py:60-67,222-249`).
  - Bounded follow-up **context** assembly: `services/insight_context.py`
    (`assemble_context` `:223`; 20,000-char ratified budget
    `DEFAULT_MAX_HISTORY_CHARS` `:46`); current-conversation only, newest-first,
    deterministic; history is explicitly marked **non-authoritative** and cannot
    override current evidence (`:1-24,346-358`).
  - Wired into the interaction: `run_interaction` assembles context before the
    provider call (`services/insight_interactions.py:562-586`).
  - A conversation is continued by posting another question to the same
    `conversation_id` (`api/v3_insight_interactions.py:43-76`).
- **Gaps and unknowns:** No cross-conversation memory (by design, I5-1/I5-9); no
  AI summarization/compaction (I5-2/I5-4). Rate limiting and concurrency leases
  apply (`services/insight_interactions.py:356-363,412-456`).

### 2.6 Audit trail for every AI query (gap reuse: `ai_content_history`, FTR-242)
- **Classification: IMPLEMENTED_AND_WIRED — but via NEW tables, NOT
  `ai_content_history`. The gap's stated reuse is a deliberate non-reuse.**
- **Evidence:**
  - **Append-only Layer-2 evidence:** `carbontally_insight_interactions` +
    `carbontally_insight_tool_calls`
    (`supabase/migrations/20261003000000_p8_i4_insight_interactions.sql`; table
    comments `:368-370`), populated by `data/insight_interactions.py` and
    `services/insight_interactions.py:393-407,511-526,664-680`.
  - **Canonical audit event:** every interaction appends to `public.audit_trail`
    through the existing `AuditLogger` (`services/insight_interactions.py:251-283,644-662`;
    `infra/audit_logger.py`).
  - **`ai_content_history` is a dormant, deliberately-untouched table.** Its DDL is
    `supabase/migrations/00000000000000_init_schema.sql:1041-1060`
    ("AI generation history"); `FTR-242` catalogues it as "present in flagship,
    qa133, clones"
    (`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:666`).
    The I1 migration states it is **NOT** reused/altered/deleted (D2 §22):
    `…p8_i1_insight_persistence.sql:24-25`; the I4 migration repeats the
    non-scope (`…p8_i4_insight_interactions.sql:30-32`); the I1/I4 migration
    tests assert it is untouched (`tests/unit/data/test_i1_insight_migration.py:16-17,165-167`,
    `tests/unit/data/test_i4_insight_migration.py:44-45`).
  - **No reader/writer of `ai_content_history` exists** in `backend/**` — a
    whole-tree search returns only test references (see §10).
- **Gaps and unknowns:** If Gap 5 literally requires the AI-answer auditability to
  live in `ai_content_history`, the current build **deviates** (it uses
  insight tables + `audit_trail`). Reconciling the audit target — and whether
  `ai_content_history` is retired, reused, or left dormant — is a PO decision
  (the D2 ratification itself deferred `ai_content_history` treatment).

### 2.7 AI runtime reuse (FTR-270)
- **Classification: IMPLEMENTED_AND_WIRED (reused as-is).**
- **Evidence:** `infra/llm_client.py` (`LLMClient` `:44`, `complete` `:90`);
  `infra/ai_runtime.py` (config gate `configured_ai_extraction_engine` `:43`,
  attribution `configured_ai_attribution` `:103`, `provider_label` `:82`). The
  conversational client reuses the **same** environment variables and the **same**
  `LLMClient` — no second provider architecture
  (`services/insight_interactions.py:184-206`). Catalogue:
  `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:719`.
- **Gaps and unknowns:** Provider identity is host-derived and truthful; key is
  environment-only, never logged/persisted (`infra/ai_runtime.py:8-12`). No
  provider is configured by default — the system falls back to deterministic
  output.

### 2.8 Query-understanding / extraction-pattern reuse (gap reuse: FTR-104)
- **Classification: IMPLEMENTED_AND_WIRED for extraction; NOT reused by the
  conversational planner (the planner is independent and deterministic).**
- **Evidence:** `FTR-104` AI-assisted document extraction —
  `engines/ai_extraction.py`, `services/ai_document_extraction.py`,
  `infra/ai_runtime.py`, `infra/llm_client.py`
  (`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:418`).
  The conversational **query understanding** does **not** extend the extraction
  LLM path; it is a separate deterministic parser
  (`services/insight_query_planner.py`, §2.1). The two share only the provider
  client, not the parsing logic.
- **Gaps and unknowns:** The gap's step 1 ("extend AI extraction patterns") is only
  satisfied at the *runtime* level (shared `LLMClient`); the actual query
  understanding is regex/deterministic by ratified design, not an extension of the
  extraction prompts.

### 2.9 Insight tool catalogue (FTR-236), references (FTR-241) and data quality (FTR-240)
- **Classification: IMPLEMENTED_AND_WIRED (all three reusables present).**
- **Evidence:**
  - **FTR-236** tool catalogue (I3): `domain/insight_tool.py` (`ToolDefinition`
    `:96`, six-point contract `:13-20`), `services/insight_tools.py`
    (`TOOL_DEFINITIONS` `:133`, registry `:347`, execution `:459`),
    `api/v3_insight_tools.py` (`GET ""` `:51`, `POST /invoke` `:57`, `POST /intent`
    `:105`). Catalogue: `…FEATURE-CATALOGUE-20260927.md:660`. Ten tools are
    registered (four ratified + Phase-8 analytics: discovery, aggregation,
    aggregate-provenance, temporal comparison, data quality, reproducibility).
  - **FTR-241** Insight customer UI (page, **references**, answer-state model):
    `frontend/src/v3/insight/InsightPage.jsx`, `InsightReferences.jsx`,
    `InsightAnswerState.jsx`, `InsightInteraction.jsx` (catalogue `:665`).
  - **FTR-240** data-quality + reproducibility (P3): `domain/insight_quality.py`;
    tools `insight_data_quality` / `insight_calculation_reproducibility`
    (`services/insight_tools.py:278-343`). Catalogue `:664`.
- **Gaps and unknowns:** All `IMPLEMENTED_AND_WIRED` but **`BLOCKED_BY_SCHEMA`**
  (flagship absence) in the FIEW register
  (`…FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md:125,129,130-131`).

### 2.10 Reporting intelligence reuse (gap reuse: FTR-216)
- **Classification: IMPLEMENTED_AND_WIRED (present; NOT consumed by the
  conversational surface).**
- **Evidence:** `FTR-216` reporting intelligence API — `/api/v3/reporting` with
  `customer-dashboard`, `emissions-trend`, `member-activity`, `audit-readiness`,
  `consultant-portfolio`, etc.
  (`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:625`;
  router wired at `api/router.py:237`). The only consumer of a trend series for a
  chart is the customer dashboard (`frontend/src/v3/customer/DashboardPage.jsx`).
- **Gaps and unknowns:** No conversational path consumes FTR-216 series, and no
  chart-generation layer sits over it (§2.4). It is reusable infrastructure for a
  future visualization component, not currently wired into the conversation.

---

## 3. Reuse Infrastructure Verification

| Feature ID | Table / Route / File | Present? | Reachable? | Notes |
|---|---|---|---|---|
| FTR-234 Insight L1 persistence (I1) | `carbontally_insight_conversations`,`…_messages` (`…p8_i1_insight_persistence.sql:43,66`); `data/insight.py`; `api/v3_insight.py` | Yes | Yes (code) | Tables **ABSENT in flagship**, present in clones/qa (`…FALSE-IMPLEMENTED…:124`; catalogue `:658`) |
| FTR-235 Insight L1 authorization (I2) | `api/insight_authz.py`; `20261002000000_p8_i2_insight_authorization.sql` | Yes | Yes | creator-private for every persona; PE/auditor denied by name (`insight_authz.py:243-246`) |
| FTR-236 Insight tool catalogue (I3) | `domain/insight_tool.py`,`services/insight_tools.py`,`api/v3_insight_tools.py` | Yes | Yes | closed read-only catalogue; `BLOCKED_BY_SCHEMA` in flagship |
| FTR-237 Insight L2 orchestration (I4) | `carbontally_insight_interactions`,`…_tool_calls` (`…p8_i4_insight_interactions.sql`); `services/insight_interactions.py` | Yes | Yes (code) | narration + references + audit; `BLOCKED_BY_SCHEMA` |
| FTR-238 planner/context/rate-limit | `services/insight_query_planner.py`,`insight_context.py`,`insight_rate_limit.py`; `20261005000000…` | Yes | Yes | rate-limit tables clone-only |
| FTR-239 Insight temporal comparison (P2) | `20261006000000_p8_insight_temporal_comparison.sql`; `insight/InsightComparison.jsx` | Yes | Yes | the only in-conversation **table** view |
| FTR-240 data-quality + reproducibility (P3) | `domain/insight_quality.py`; `20261007000000…` | Yes | Yes | `BLOCKED_BY_SCHEMA` |
| FTR-241 Insight customer UI (page, references, answer-state) | `frontend/src/v3/insight/InsightPage.jsx`,`InsightReferences.jsx`,`InsightAnswerState.jsx`,`InsightInteraction.jsx` | Yes | Yes | route `/insight` (`App.js:2070`) |
| FTR-242 Insight AI content history | `ai_content_history` (`init_schema.sql:1041`) | Yes (DDL) | **No writer/reader** | **DORMANT** — deliberately not reused by I1/I4 (D2 §22) |
| FTR-270 LLM/AI runtime | `infra/llm_client.py`,`infra/ai_runtime.py`,`services/ai_document_extraction.py` | Yes | Yes | env-gated; reused by narration; key never persisted |
| FTR-104 AI document extraction | `engines/ai_extraction.py`,`services/ai_document_extraction.py` | Yes | Yes | shares `LLMClient` only; **not** the query-understanding path |
| FTR-216 reporting intelligence API | `/api/v3/reporting` (`api/v3_reporting.py`; `router.py:237`) | Yes | Yes | not consumed by the conversation; feeds only the dashboard chart |
| FTR-030 RLS enforcement | `20260803000000_rc2_rls.sql`,`20260925000000_p8_rls_4b_group1_enablement.sql` | Yes | UNKNOWN | applied coverage varies per DB; no live read |
| FTR-031 server-side guard modules | `api/dependencies.py`,`insight_authz.py`,… | Yes | Yes | `insight_authz.py` is the Insight entry point |
| On-demand **chart** generation | — | **No** | **No** | no chart in `frontend/src/v3/insight/**`; only dashboard bar chart |
| `ai_content_history` reuse for AI answers | `ai_content_history` | **No** | **No** | build uses insight tables + `audit_trail`; deviation from gap reuse |

---

## 4. Migration Inventory (Conversational-AI / Insight Related)

> Note: there is **no top-level `migrations/` directory** inside the `backend/`
> workspace. Migrations live at **repo-root `supabase/migrations/`** (102 files),
> referenced below with that prefix.

| Migration File | Objects Created | Applied in Which DBs (if determinable) |
|---|---|---|
| `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql` | `carbontally_insight_conversations`, `carbontally_insight_messages` (+ RLS) | **ABSENT in flagship**; present in `ct_p17k_20260926`,`carbontally_test` (catalogue `:658`) |
| `supabase/migrations/20261002000000_p8_i2_insight_authorization.sql` | Insight RLS policies; `ai_content_history` not reused (`:27-28`) | Not determinable; `BLOCKED_BY_SCHEMA` (`…FALSE-IMPLEMENTED…:124`) |
| `supabase/migrations/20261003000000_p8_i4_insight_interactions.sql` | `carbontally_insight_interactions`, `carbontally_insight_tool_calls`; `ai_content_history` NOT touched (`:30-32`) | `BLOCKED_BY_SCHEMA` (`…:126`) |
| `supabase/migrations/20261005000000_p8_insight_discovery_aggregation_rate_limit.sql` | `insight_rate_limit_buckets`, `insight_concurrency_leases` (`lease_expires_at`) | clone-only (`…:128`; catalogue `:662`) |
| `supabase/migrations/20261006000000_p8_insight_temporal_comparison.sql` | temporal-comparison structures | `BLOCKED_BY_SCHEMA` (`…:128`) |
| `supabase/migrations/20261007000000_p8_insight_data_quality_reproducibility.sql` | quality/reproducibility structures | `BLOCKED_BY_SCHEMA` (`…:129`) |
| `supabase/migrations/00000000000000_init_schema.sql` | `ai_content_history` DDL (`:1041-1060`) | present (long-standing base schema) |
| `supabase/migrations/20260925000000_p8_rls_4b_group1_enablement.sql` | enables RLS for `ai_content_history` and other tenant surfaces (`:79-80`) | not determinable |
| `supabase/migrations/20260803000000_rc2_rls.sql` | platform RLS baseline (FTR-030) | not determinable |

**Applied-state caveat:** repository verification docs consistently record a large
block of migrations as **unapplied** in the flagship (the "43 unapplied
migrations", `docs/architecture/CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md:124,184`).
The entire Insight family (`20261001000000` → `20261007000000`) is recorded
`BLOCKED_BY_SCHEMA`. No live DB reads were performed for this pass, so
per-database application state is **UNKNOWN**.

---

## 5. Route Inventory (Conversational-AI / Insight Related)

| Route Path | Method | Module | Auth Required? | Purpose |
|---|---|---|---|---|
| `/api/v3/insight/conversations` | POST | `api/v3_insight.py:120` | Yes — `require_insight_user` + `authorize_insight_scope` | Create creator-private conversation |
| `/api/v3/insight/conversations` | GET | `api/v3_insight.py:138` | Yes — same | List caller's conversations |
| `/api/v3/insight/conversations/{id}` | GET | `api/v3_insight.py:166` | Yes — same | Read one conversation |
| `/api/v3/insight/conversations/{id}/messages` | POST | `api/v3_insight.py:179` | Yes — same | Append human-authored message (role `user` only) |
| `/api/v3/insight/conversations/{id}/messages` | GET | `api/v3_insight.py:215` | Yes — same | List messages (ordinal order) |
| `/api/v3/insight/tools` | GET | `api/v3_insight_tools.py:51` | Yes — `require_insight_user` | Ratified tool registry (definitions) |
| `/api/v3/insight/tools/invoke` | POST | `api/v3_insight_tools.py:57` | Yes — + rate limit + leases | Deterministic read-only tool execution |
| `/api/v3/insight/tools/intent` | POST | `api/v3_insight_tools.py:105` | Yes — same | Deterministic intent classification |
| `/api/v3/insight/interactions` | POST | `api/v3_insight_interactions.py:54` | Yes — + rate limit/leases + narration | **Run one conversational question (the Copilot call)** |
| `/api/v3/insight/interactions` | GET | `api/v3_insight_interactions.py:79` | Yes — same | List caller's interactions |
| `/api/v3/insight/interactions/{id}` | GET | `api/v3_insight_interactions.py:99` | Yes — same | Read one interaction |
| `/api/v3/evidence/line-items/{line_item_id}` | GET | `api/v3_evidence.py:103` | Yes — `require_org_member` + DM-6 | Source Evidence Viewer (citation drill-down) |

**Router registration:** `api/router.py:250,253,255` (I1/I3/I4); the insight
routers are imported at `api/router.py:72-74`.

**Negative result:** No route string in `backend/**` contains `copilot`, `chart`,
`visuali[sz]`, or `plot` (searches returned zero matches). There is **no**
chart/visualization endpoint.

---

## 6. UI Inventory (Conversational-AI / Insight Related)

| Component Path | Route | Purpose | Wired? |
|---|---|---|---|
| `frontend/src/v3/insight/InsightPage.jsx` | `/insight` (`App.js:2070`) | Authenticated Insight workspace: conversation list + view + composer | Yes — `ProtectedRoute` + `RoleRoute requireOrg` (`App.js:2071-2077`) |
| `frontend/src/v3/insight/InsightInteraction.jsx` | Embedded | One interaction: answer state, tool-call evidence, references | Yes |
| `frontend/src/v3/insight/InsightAnswerState.jsx` | Embedded | The I4 answer-state presentation | Yes |
| `frontend/src/v3/insight/InsightReferences.jsx` | Embedded | Evidence reference locators (citations) | Yes |
| `frontend/src/v3/insight/InsightComparison.jsx` | Embedded | P2 temporal-comparison **table** (re-read on demand) | Yes |
| `frontend/src/v3/evidence/SourceEvidenceViewer.jsx` | `/evidence/line-items/:lineItemId` (`App.js:2083`) | Reached from Insight references (citation drill-down) | Yes |
| `frontend/src/v3/customer/DashboardPage.jsx` | (dashboard) | Fixed emissions-trend **bar chart** (recharts) | Yes — **not** conversational, not on-demand |
| *(none)* named `Copilot` / chart / visualization in Insight | — | — | **Absent** — whole-tree search for `copilot`/chart components in `frontend/src/v3/insight/**` returns 0 |

**Negative result:** `frontend/src/v3/insight/**` contains **no** chart component
and **no** "Copilot"-branded component. The only `Copilot` string in the whole
repository is in **marketing/pricing and PO-ratification documents**, not code —
and the ratified decision **forbids** it as a product name
(`…D2_PO_RATIFICATION_20260912.md:175`).

---

## 7. Build Distance Assessment

| Build Component (gap) | Current State | Remaining Work | Estimated Effort |
|---|---|---|---|
| NL query → structured query | IMPLEMENTED (deterministic) | None required for parity; optionally extend the closed vocabulary (PO decision) | None / Small |
| Scoped data access (FTR-031/FTR-030) | IMPLEMENTED_AND_WIRED | Confirm applied RLS policies in authoritative DB | Small (ops) |
| Response generation w/ citations | PARTIAL | Add **machine-enforced** citation binding (each claim → reference) if the guardrail is to be hard | Small–Medium |
| On-demand **chart** generation | **ABSENT** | New visualization layer over aggregate tools + FTR-216 series; new UI + intent | Medium |
| On-demand **table** generation | PARTIAL (one table view) | Generalize table rendering beyond comparison | Small |
| Follow-up query support | IMPLEMENTED (I5 context) | None (cross-conversation memory intentionally excluded) | None |
| Audit trail per AI query | IMPLEMENTED (insight tables + `audit_trail`) | Reconcile target vs gap's `ai_content_history`; confirm durable schema | Small (PO + ops) |
| AI runtime reuse (FTR-270) | IMPLEMENTED | Ensure a provider is configured where a "conversational" UX is expected | Small (config) |
| Tool catalogue / references / data-quality reuse (FTR-236/241/240) | IMPLEMENTED_AND_WIRED | Apply/confirm blocked schema | Small (ops) |
| Extraction-pattern reuse (FTR-104) | Runtime-only reuse | Decide whether query-understanding should extend extraction prompts | PO decision |
| Schema durability (all Insight migrations) | **BLOCKED_BY_SCHEMA** | Apply/confirm `20261001000000`…`20261007000000` in the authoritative DB | Medium (ops/PO) |

---

## 8. Risks and Unknowns

- **Unverified items.**
  - **Applied state of the Insight migrations** (`20261001000000_p8_i1…` through
    `20261007000000_p8_insight_data_quality_reproducibility.sql`) — recorded
    `BLOCKED_BY_SCHEMA` / flagship-absent in repository verification docs; **no
    live confirmation** (`…FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md:124-131`).
  - Whether an **LLM provider is configured** in any target environment (the
    narration experience depends on it; `services/insight_interactions.py:184-199`).
  - Whether a conversational branch or second repository exists outside this tree.
- **Assumptions requiring PO / engineering confirmation.**
  1. **Product name.** "Copilot" is forbidden (D2 §3.5); confirm the Gap 5
     deliverable uses "Ask CarbonTally / CarbonTally Insight".
  2. **Audit target.** Does the gap require `ai_content_history` specifically, or is
     the `carbontally_insight_interactions` + `audit_trail` model the intended
     auditability? (Current build deliberately does **not** reuse
     `ai_content_history`.)
  3. **Citation strength.** Is the structured `references[]` set sufficient as
     "evidence citations", or must narration text be machine-bound to references?
  4. **Chart scope.** Which aggregate results must be chartable (by scope / month /
     year / supplier / facility), and does the chart reuse FTR-216 series or the
     Insight tools directly?
- **Documentation consistency risk.** The `FTR` numbering for domain 37 differs
  between the **catalogue** (`FTR-234…242`) and the **traceability doc**
  (`FTR-237/238` tools, `FTR-242` comparison), an offset of the same domain. The
  gap prompt's IDs match the **catalogue**; the traceability doc must not be read
  as the authoritative index for these IDs.

---

## 9. Recommendations for Next Research Pass

- **Specific files / DBs to inspect.**
  - Confirm applied state of `20261001000000_p8_i1…`, `20261002000000_p8_i2…`,
    `20261003000000_p8_i4…`, `20261005000000…`, `20261006000000…`,
    `20261007000000…` in the authoritative DB (read-only `information_schema`
    query), plus `ai_content_history` and the RLS policies on the Insight tables.
  - Read `docs/architecture/CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md` and
    `CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` for the ratified I5/I6 scope.
  - Read `docs/architecture/CARBONTALLY_P8_I4_Q1_AI_CONTENT_HISTORY_CLOSURE_20260921.md`
    — the closure that decided the `ai_content_history` treatment (FTR-242).
  - Inspect `frontend/src/v3/api.js:1786-1876` (the complete Insight client
    surface) and `InsightComparison.jsx` fully for the table-rendering pattern a
    chart layer would extend.
- **Questions for engineering / PO.**
  1. Is the conversational interface **"Ask CarbonTally / CarbonTally Insight"**
     (not "Copilot"), per D2 §3.5?
  2. Is the auditability target the new `carbontally_insight_interactions` +
     `audit_trail`, or must `ai_content_history` be reused?
  3. Must narration citations be **machine-enforced** per claim, or is the typed
     `references[]` set the accepted guardrail?
  4. Which aggregate dimensions must be **chartable**, and does the chart consume
     FTR-216 series or the Insight aggregate tools?
  5. Which database is authoritative for applying the blocked Insight migrations?

---

## 10. Appendix — Raw Search Evidence

**Commands / searches run (read-only; no execution of npm/pip/make/python/pytest/
playwright/migrations/seeders; no git; no DB mutation).**

- `list_files` over `backend/`, `backend/infra/`, `backend/services/`,
  `docs/architecture/`, `supabase/migrations/`, `frontend/src/v3/insight/`.
- `read_file` on: `backend/api/v3_insight.py`, `backend/api/v3_insight_tools.py`,
  `backend/api/v3_insight_interactions.py`, `backend/api/insight_authz.py`,
  `backend/api/router.py`, `backend/data/insight.py`,
  `backend/services/insight_tools.py` (1–699), `backend/services/insight_interactions.py`
  (full), `backend/services/insight_query_planner.py` (1–400),
  `backend/services/insight_context.py`, `backend/domain/insight_tool.py`,
  `backend/domain/insight_interaction.py` (1–200), `backend/infra/ai_runtime.py`,
  `backend/infra/llm_client.py`,
  `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql`,
  `supabase/migrations/00000000000000_init_schema.sql` (1035–1064),
  `frontend/src/v3/insight/InsightPage.jsx`,
  `frontend/src/v3/insight/InsightInteraction.jsx`,
  `frontend/src/v3/insight/InsightComparison.jsx`, `frontend/src/App.js` (2060–2089).
- `search_files` (recursive regex):
  - `ai_content_history` across the repo → only test references
    (`tests/unit/data/test_i1_insight_migration.py`,
    `test_i2_insight_authorization_contracts.py`, `test_i4_insight_migration.py`);
    SQL hits only in comment/non-scope lines.
  - `ai_content_history` across `supabase/migrations/*.sql` → DDL
    (`00000000000000_init_schema.sql:1041`), RLS enablement
    (`20260925000000…:80`), and the explicit non-reuse comments in
    `20261001000000…:24`, `20261002000000…:27-28`, `20261003000000…:30-32`.
  - `FTR-270|FTR-236|FTR-241|FTR-242|FTR-240` across `docs/**` → catalogue rows
    `CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:660,664-666,719`,
    FIEW register `…FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md:124-131`,
    and the traceability/canonical-matrix docs (numbering discrepancy noted §1/§8).
  - `FTR-104|FTR-216|FTR-031|FTR-030|FTR-234|FTR-238|FTR-239` in the catalogue →
    `:284,285,418,625,658,662,663`.
  - `from ['\"](recharts|chart\.js|…)|<LineChart|<BarChart|<PieChart` across
    `frontend/src/v3/**/*.jsx` → only
    `frontend/src/v3/customer/DashboardPage.jsx:14-15,185` (dashboard only).
  - `chart|Chart|<table|recharts|ResponsiveContainer` across
    `frontend/src/v3/insight/*.jsx` → only
    `InsightComparison.jsx:163` (`<table>`); **no chart**.
  - `conversation_is_visible|authorize_insight_scope|require_insight_user` in
    `backend/**` → `api/insight_authz.py`, `api/v3_insight.py`,
    `api/v3_insight_interactions.py`, `api/v3_insight_tools.py`,
    `services/insight_tools.py`, `services/insight_interactions.py`,
    `services/insight_context.py`.
  - `Insight|insight` in `frontend/src/v3/api.js` → client functions at
    `:1800-1876`.
  - `ask_` in `backend/**/*.py` → only tests asserting the `ask_*` legacy naming
    is **not** introduced (`tests/unit/data/test_i1_insight_migration.py:94-96`,
    `test_i4_insight_migration.py:38-39`).

**Negative results (searched but not found).**
- No conversational **chart** endpoint, component or intent (no `chart`/`plot`/
  `visuali[sz]` route or `frontend/src/v3/insight/**` chart).
- No **writer/reader** of `ai_content_history` anywhere in `backend/**` (dormant;
  explicitly not reused by I1/I2/I4).
- No code artifact named **"Copilot"** (the string appears only in marketing and
  PO-ratification docs; the name is forbidden by D2 §3.5).
- No `README`-level "conversational AI" doc beyond the Insight phase-auth docs.
- No cross-conversation memory, no RAG/embeddings/vector search, no summarisation
  (by ratified design, I5-1/I5-2/I5-9).

**Files inspected (representative).** See the `read_file` list above plus the
catalogue and register docs cited inline:
`CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md`,
`CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md`,
`CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md`,
`CT-PO-CARBONTALLY-CANONICAL-SCHEMA-FEATURE-SUPPORT-MATRIX-20260927.md`,
`CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md`,
`CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md`,
`CT-GAP4-SUPPLIER-ENGAGEMENT-PORTAL-CURRENT-STATE-2026-09-30.md` (format reference),
`CT-GAP6-AUDITOR-READ-ONLY-PORTAL-CURRENT-STATE-2026-09-30.md` (format reference).
