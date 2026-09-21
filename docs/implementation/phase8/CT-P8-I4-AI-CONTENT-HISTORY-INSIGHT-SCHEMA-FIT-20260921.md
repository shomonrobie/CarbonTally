# CT-P8-I4-AI-CONTENT-HISTORY-INSIGHT-SCHEMA-FIT-20260921

**Task:** read-only architectural / schema-fit analysis of `public.ai_content_history` against the CarbonTally Insight architecture (I4).
**Checkout:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **Starting HEAD:** `2c67a310ac1c50ef791f1d79401c458318f00e10`
**Scope discipline:** no schema, migration, application code, test, configuration, Master Specification or other document was modified; no database was queried; no migration was created; no table was introduced or deleted; **Q1 was not resolved**.
**Certification:** `DIRECT` = established by an inspected artefact · `INFERENCE` = architectural reasoning from evidence · `UNKNOWN` = not established.
**Authority inputs:** Master Specification v1.1 (lines cited inline); D2 PO Ratification; `CT-P8-I4-PREAUTHORIZATION-READINESS-AUDIT-20260921.md`; `CT-P8-I4-AI-CONTENT-HISTORY-ORIGIN-FORENSIC-20260921.md`; `supabase/migrations/00000000000000_init_schema.sql`; `20261001000000_p8_i1_insight_persistence.sql`; `20261002000000_p8_i2_insight_authorization.sql`; `backend/api/insight_authz.py`; `backend/services/insight_tools.py`; `backend/domain/insight_tool.py`; `backend/infra/llm_client.py`; `backend/infra/ai_runtime.py`; `backend/domain/audit.py`.

---

## 1. Executive conclusion

1. `DIRECT` — `public.ai_content_history` is a **16-column legacy AI-content journal** carried into the V3 baseline from the RC1/RC2 (V1/V2-era) design, documented as `Track AI-generated content with feedback` and scoped to report generation. It has never been altered, has **no FK on `report_id`**, **no index**, **no RLS policy**, and no application writer or reader in this repository (forensic report §§2–9).
2. `DIRECT` — its columns are **semantically generic enough** to plausibly represent an *individual AI generation* with telemetry and feedback (`organization_id`, `model_used`, `prompt_text`, `generated_content`, `content_format`, `tokens_used`, `processing_time_ms`, `cost`, `user_rating`, `user_feedback`, `was_accepted`, `created_at`, `created_by`). Nothing in its DDL structurally prevents extension by additive columns.
3. `DIRECT` — but it is **not** an Insight artefact and **not** a substitute for any ratified Insight layer: no conversation/message link, no interaction identity, no intent, no tool-call or reference fields, no answer status, no provider, no model version, no finish reason, no correlation identifier; its creator key is nullable with no creator-private predicate; and Phase 8 deliberately left it untouched (I1/I2 migration comments and tests).
4. `DIRECT` — **canonical naming is ratified against reuse-in-place for new work**: D2 R24/§3.2/§3.8 make `CarbonTally Insight / carbontally_insight_* / CarbonTallyInsight*` "the canonical technical/domain terminology for new implementation" and supersede `ask_*`. A D3-era legacy-named table therefore sits outside the ratified namespace for **new** Insight implementation.
5. `DIRECT` — **duplication risk is real and already documented**: AI cost/usage telemetry for report generation already lives in `report_generation_queue.ai_model_used / ai_tokens_used / ai_cost / ai_processing_time_ms` (the RC2 Architecture Freeze calls this "the committed FinOps surface"), and per-organisation allowance counters live in `usage_tracking` (`ai_files_processed`, `reports_generated`, `UNIQUE (organization_id, usage_month)`). Adding a third AI-telemetry home without a single-bounded-home rule would create a **fourth** record of AI cost — precisely what D2 §22.4 and Master Spec §23 forbid.
6. `INFERENCE` — a **conversation or audit role for this table is architecturally wrong**: Master Spec §20.1 forbids collapsing the three layers; Layer 1 is already built (I1) and naming-consistent; Layer 3 is the append-only `public.audit_trail` (Phase 7 trigger-enforced). The only defensible future role for this shape is an **AI-generation / telemetry / evaluation record** — a supporting AI-operations component, not the conversation and not the ledger.
7. `INFERENCE` (architectural, **not** a PO decision) — **direct reuse without restructuring is not appropriate**; broader reuse is **technically plausible** but requires restructuring plus a naming/ownership decision; a **separately-scoped Insight AI-generation record** is architecturally cleaner, provided the single-bounded-home constraint is enforced and the legacy table's disposition is decided at the same time.
8. `UNKNOWN` — whether any environment holds rows (`PRODUCTION ROW PRESENCE NOT VERIFIED`), whether an external/legacy writer exists, and whether a pre-baseline V1/V2 authoring task ever governed the table. No reuse, extension, rename or retirement may assume the table is data-free.
9. `DIRECT` — **Q1 is not closed by this analysis** and no PO disposition is chosen; §19 records the architectural evidence result only.
---

## 2. Existing table schema (shipped DDL, verbatim)

`DIRECT` — `supabase/migrations/00000000000000_init_schema.sql:1038–1060`, under the banner `-- PHASE D3 CONTINUED: AI CONTENT`; introduced by `2d23fb8` (2026-08-06) and **unchanged to HEAD** (0 `ALTER TABLE`, 0 `ADD COLUMN` in all refs).

```sql
CREATE TABLE public.ai_content_history (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    report_id UUID,
    prompt_type VARCHAR NOT NULL,
    prompt_text TEXT,
    model_used VARCHAR,
    generated_content TEXT,
    content_format VARCHAR,
    tokens_used INTEGER CHECK (tokens_used IS NULL OR tokens_used >= 0),
    processing_time_ms INTEGER CHECK (processing_time_ms IS NULL OR processing_time_ms >= 0),
    cost NUMERIC CHECK (cost IS NULL OR cost >= 0),
    user_rating INTEGER CHECK (user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5)),
    user_feedback TEXT,
    was_accepted BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);
COMMENT ON TABLE public.ai_content_history IS 'AI generation history';
```

`DIRECT` — structural facts that determine fit:

* **no index of any kind** — a repo-wide search for `ai_history` in all migrations returns nothing, so the design artefact's `idx_ai_history_org(organization_id)` and `idx_ai_history_report(report_id)` were **not shipped**;
* **no foreign key on `report_id`** — the design's `report_id UUID REFERENCES report_generation_queue(id)` was **not shipped**; `report_id` is a bare nullable `UUID`;
* **no RLS policy** — searching all migrations for `ON public.ai_content_history` / `ON ai_content_history` returns **nothing**, so although Phase 8 enabled RLS on the table (`20260925000000_p8_rls_4b_group1_enablement.sql:80`, commit `1db97ba`), the table has **zero policies** → deny-by-default for `anon`/`authenticated`, with `service_role` bypassing RLS;
* **no trigger** — unlike `public.audit_trail`, which is protected by the Phase 7 `p7_audit_trail_immutable` trigger (`20260912000000_p7_audit_immutability_and_indexes.sql:32–49`);
* **no unique constraint** other than the primary key;
* `created_at TIMESTAMPTZ DEFAULT NOW()` is **nullable** (no `NOT NULL`), and `created_by UUID` is **nullable with no FK** (the design's `REFERENCES organization_members(id)` was not shipped);
* `organization_id` is `NOT NULL` with `ON DELETE CASCADE` to `public.organizations` — the same tenant-root pattern I1 later reused.

`DIRECT` — documented column meaning per the retained design artefact (`docs/Final/UI_UX-Final_Guideline.md:495–531`): `prompt_type` examples `'executive_summary'`, `'analysis'`, `'methodology'`; `content_format` examples `'text'`, `'markdown'`, `'html'`; `user_rating` 1–5; `was_accepted BOOLEAN DEFAULT TRUE` in the design (no default shipped). `INFERENCE` — the presence of `content_format`/'markdown' and a rating implies a **human-reviewable generated artefact**, not a chat turn.
---

## 3. Historical purpose

`DIRECT` (from `CT-P8-I4-AI-CONTENT-HISTORY-ORIGIN-FORENSIC-20260921.md`):

* design artefact verbatim: `-- TABLE: ai_content_history` / `-- Purpose: Track AI-generated content with feedback`, with `report_id UUID REFERENCES report_generation_queue(id)`, `prompt_type VARCHAR(50) NOT NULL -- 'executive_summary', 'analysis', 'methodology'`, and the index entry `ai_content_history — Track AI-generated content`;
* retained legacy architecture set: "AI interactions are journaled in `ai_content_history` for auditability and prompt/version traceability" (`01_application_architecture.md:133`); module purpose "Prompt/response audit" (`03_module_breakdown.md:277`); per-report audit provenance "(model, tokens, cost)" (`04_api_design.md:247`);
* OHD discovery: "AI usage + cost already captured — `ai_content_history` (tokens, cost, model, latency)"; RC2 Architecture Freeze verdict `KEEP` (all columns);
* no writer/reader ever existed in this repository; QA-AI-001 observed 0 rows `[OBS]` locally.

**Which historical semantics survive for broader Insight:**

| Historical semantic | Survives? | Why |
| --- | --- | --- |
| "an AI **generation** occurred; this is its record" | **Yes** — core concept | Matches the only I4 concept that is generation-scoped rather than conversation- or ledger-scoped |
| model attribution (`model_used`) | **Yes, but insufficient** | Insight needs provider **and** model **and** optional truthful `model_version` (§15.3; Gate-5 precedent adds `automation_provider/model/model_version`) |
| latency (`processing_time_ms`) | **Yes, directly** | Provider latency is a legitimate AI-operations metric at any layer |
| token usage / cost | **Yes, as nullable telemetry** | §15.4 mandates `tokens_used = NULL`, `cost = NULL` until truthful; `ChatCompletionResponse` exposes neither |
| prompt/response content | **Partly** | Useful for AI-generation evaluation; conflicts with §16.4/§20.4 if treated as the conversation or audit record; §41 leaves "raw question storage versus hash" open |
| human feedback (`user_rating`, `user_feedback`, `was_accepted`) | **Yes, uniquely** | No ratified Insight layer specifies feedback/acceptance; nothing else provides this capability |
| report linkage (`report_id`) and report prompt taxonomy (`prompt_type`) | **Report-specific** | Belongs to report generation; irrelevant to (and misleading for) conversational Insight |
| "the record of the conversation" | **No** | Layer 1 exists (I1); §20.1 forbids layer collapse |
| "the audit record" | **No** | §8.1/§20.2 plus the append-only `audit_trail` trigger |

`INFERENCE` — the table's historically **generation-scoped** nature is the key fit signal: it is neither a conversation nor a ledger, and the generation-scoped I4 concept is the **AI narration/generation event with telemetry and feedback**.

---

## 4. Current Insight architecture (as observed in code/schema)

`DIRECT` — **Layer 1 (built, I1)**: `carbontally_insight_conversations` (`id`, `organization_id NOT NULL` FK→`organizations` cascade, `created_by NOT NULL`, `title`, `created_at`, `updated_at NOT NULL`, `UNIQUE (id, organization_id)`; indexes on `(organization_id, created_at DESC)` and `(organization_id, created_by, created_at DESC)`) and `carbontally_insight_messages` (`id`, `conversation_id`, `organization_id NOT NULL`, `created_by` nullable, `role varchar(16) CHECK role IN ('user','insight')`, `content text NOT NULL`, `ordinal integer NOT NULL >= 1`, `created_at NOT NULL`, composite FK `(conversation_id, organization_id)`, `UNIQUE (conversation_id, ordinal)`, `CHECK (role <> 'user' OR created_by IS NOT NULL)`). Both: RLS enabled; `anon` REVOKE ALL; `authenticated` SELECT+INSERT only; `service_role` ALL; creator-private policies keyed on `auth.uid()` and `public.is_org_member(organization_id)`.

`DIRECT` — **I2 authorization** (`backend/api/insight_authz.py`): `authorize_insight_scope()` (:206), persona resolution (:294), `organization_is_active()` (:146), `InsightAccess` (:162), `visibility_created_by()`/`conversation_is_visible()` (:322–340), `normalize_org_role()` (:104), `is_auditor_principal()` (:118), `staff_context_grants_insight_scope()` (:133).

`DIRECT` — **I3 tools**: four ratified read-only tools; six-point contract (`TOOL_CONTRACT_VERSION = "i3-6point-v1"`, `MAX_IDENTIFIER_LENGTH = 128`, `MAX_RESULT_ITEMS = 200`); `ToolStatus` = `success | no_data | not_authorized | invalid_input | provider_unavailable | error`; `InsightReference` locators (not grants); allowlisted projections; no provider import anywhere in Insight.

`DIRECT` — **Layer 2 does not exist** (no table, repository, service or migration). **Layer 3** = `public.audit_trail` (`action_type`, `table_name`, `record_id NOT NULL`, `performed_by NOT NULL`, `performed_at`, `old_data`/`new_data`/`changes`, `ip_address`, `user_agent`, `metadata JSONB`, `created_at`), Phase 7 append-only trigger, taxonomy in `backend/domain/audit.py` (categories: authentication, authorization, document, extraction, mapping, validation, calculation, evidence, workflow, report, administration, system — **no AI category**; `OUTCOMES` = `success`/`failure`).

`DIRECT` — **AI/provider infrastructure**: `LLMClient` with injectable transport and `ChatCompletionResponse{text, finish_reason}` (no usage/cost); `ai_runtime.configured_ai_attribution()` → `{provider, model, model_version}`, never fabricated; Gate-5 precedent `document_processing_queue.automation_provider/model/model_version`; report telemetry `report_generation_queue.ai_model_used/ai_tokens_used/ai_cost/ai_processing_time_ms`; billing aggregates in `usage_tracking`.
---

## 5. Column-by-column schema-fit matrix

`DIRECT` — all 16 columns; "reusable" means *semantically usable for an Insight AI-generation record*, not "usable without schema work".

| # | Column | Type / null / default / FK | Constraint | Purpose | Report-specific? | Reusable for Insight? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `id` | `uuid`, PK, default `extensions.uuid_generate_v4()`, no FK | PRIMARY KEY | record identity | No | **Yes** (generation-record identity; not the interaction identity) |
| 2 | `organization_id` | `uuid`, **NOT NULL**, FK→`organizations(id)`, `ON DELETE CASCADE` | FK + cascade | tenant scope | No | **Yes** — identical shape to I1's tenant key (§9.4) |
| 3 | `report_id` | `uuid`, **nullable**, **no FK shipped** | none | report linkage | **Yes** | **Only if generalised** (§12): bare nullable uuid, no FK, no index, no Insight semantics |
| 4 | `prompt_type` | `varchar`, **NOT NULL**, no default | none | prompt/report-section taxonomy (`executive_summary`/`analysis`/`methodology`) | **Yes** | **Partly** — a generation-kind concept is reusable, but the vocabulary is report-section specific and there is no CHECK to extend against |
| 5 | `prompt_text` | `text`, nullable | none | raw prompt | Partly | **Partly** — §41 leaves raw-question storage open; storing Insight questions here puts prompt text outside the Insight domain/namespace |
| 6 | `model_used` | `varchar`, nullable | none | model identifier | No | **Yes, insufficient alone** — no provider, no `model_version`; §15.3 + Gate-5 precedent require all three when truthfully known |
| 7 | `generated_content` | `text`, nullable | none | model output | No | **Yes** for generation evaluation; **no** as the conversation answer (Layer 1/2 territory) |
| 8 | `content_format` | `varchar`, nullable | none | output format (`text`/`markdown`/`html`) | Partly | **Partly** — rendering/evaluation metadata |
| 9 | `tokens_used` | `integer`, nullable | `CHECK (NULL or >= 0)` | token usage | No | **Yes, as nullable telemetry** — §15.4 requires NULL until truthful |
| 10 | `processing_time_ms` | `integer`, nullable | `CHECK (NULL or >= 0)` | provider latency | No | **Yes** |
| 11 | `cost` | `numeric`, nullable | `CHECK (NULL or >= 0)` | cost telemetry | No | **Yes, as nullable telemetry** — but duplicates `report_generation_queue.ai_cost` and `usage_tracking` aggregates |
| 12 | `user_rating` | `integer`, nullable | `CHECK (NULL or 1–5)` | human quality rating | No | **Yes, uniquely** — no Insight layer specifies feedback |
| 13 | `user_feedback` | `text`, nullable | none | free-text feedback | No | **Yes, uniquely** |
| 14 | `was_accepted` | `boolean`, nullable | none (design default `TRUE` not shipped) | acceptance flag | No | **Yes, uniquely** |
| 15 | `created_at` | `timestamptz`, **nullable**, default `NOW()` | none | creation time | No | **Yes**, weaker than I1 (`NOT NULL DEFAULT now()`): ordering/index guarantees differ |
| 16 | `created_by` | `uuid`, **nullable**, **no FK** | none | actor identity | No | **Partly** — I1 requires `NOT NULL` for user-authored rows and uses it as the creator-private key; here it is optional and carries no predicate |

**Aggregate (`INFERENCE`):** 13 of 16 columns are non-report-specific and map onto AI-generation/telemetry/evaluation concepts; 3 are report-flavoured (`report_id`, the `prompt_type` vocabulary, partly `content_format`); and the table carries **no** Insight discriminator (conversation, message, interaction, intent, tool call, reference, status, provider, correlation). Those missing pieces are exactly what makes an I4 record reconstructable (Master Spec §9.3).
---

## 6. Layer-1 fit

`DIRECT` — Layer 1 (conversations, messages, raw user question, creator-private ownership) is **already satisfied** by `carbontally_insight_conversations` / `_messages`: `UNIQUE (conversation_id, ordinal)` ordering, composite-FK organisation consistency, `NOT NULL` content and `created_at`, creator-private RLS, anon denial, UPDATE/DELETE revocation, `service_role` ALL.

| Layer-1 concept | Present in `ai_content_history`? | Verdict |
| --- | --- | --- |
| conversation identity | **No** | cannot represent a conversation |
| message + author kind (`user`/`insight`) | **No** (only `created_by` plus free-text prompt/response) | cannot represent a message stream |
| explicit ordering (`ordinal`) | **No** (only nullable `created_at`) | cannot guarantee stable ordering |
| raw user question | Partly (`prompt_text`) | a generation prompt, not necessarily a human question; no user/assistant asymmetry |
| creator-private ownership | **No** predicate; `created_by` nullable; no policy | would not satisfy I2's creator-private contract |

`INFERENCE` — using `ai_content_history` as Layer 1 would violate §20.1 (layer collapse), duplicate an already-built, ratified, naming-consistent domain, and discard I1's ordering/creation invariants. **Layer-1 fit: none.**

---

## 7. Layer-2 fit

`DIRECT` — Layer 2 (proposed I4 interaction record, §8.1/§9.3) must establish: who asked → what request was interpreted → which authorized tools were invoked → what authoritative references were returned → which model/provider was used, if any → what answer status resulted → what answer was produced.

| Layer-2 element | Present in `ai_content_history`? | Verdict |
| --- | --- | --- |
| interaction identity | **No** | absent |
| actor (`who asked`) | `created_by` (nullable, no FK) | insufficient |
| conversation / message linkage | **No** | absent — and `report_id` is the wrong parent |
| interpreted intent | **No** (`prompt_type` is a report-section label, not classified intent) | absent |
| tool invocation + authorized parameters | **No** | absent |
| references / deterministic result | **No** | absent (no reference, hash or snapshot locator) |
| answer status | **No** | absent; §14's taxonomy has no column here |
| provider/model attribution | `model_used` only | insufficient (no provider, no version) |
| correlation identifiers | **No** | absent (§27 anticipates them at I4) |
| AI narration text | `generated_content` | reusable as the narration artefact, not as the interaction record |
| lifecycle / mutability posture | none (no trigger, no status column) | undecided by this table |

`INFERENCE` — the table can hold **one facet** of an interaction (the generation and its telemetry) but cannot *be* the interaction record. Treating it as Layer 2 would place the interaction in a table that is (a) outside the ratified `carbontally_insight_*` namespace, (b) without a conversation parent, and (c) without any RLS policy — i.e. it would have to be restructured *and* re-governed to satisfy §9.3 and §10. **Layer-2 fit: as a component only, never as the record.**
---

## 8. AI-generation fit

`DIRECT` — an "individual AI generation" record needs: what was asked, what was produced, which model/provider produced it, whether it finished, how long it took, what it cost, and how it was judged. Comparing that requirement set with the shipped columns:

| AI-generation concern | Column present? | Fit |
| --- | --- | --- |
| prompt / input | `prompt_text` | **Present** (nullable; privacy posture unresolved, §41) |
| generated output | `generated_content` | **Present** (nullable, `text`) |
| output format | `content_format` | **Present** |
| model | `model_used` | **Present but incomplete** — no provider, no truthful `model_version` |
| provider | **absent** | **Missing** — §15.3 requires truthful provider attribution; Gate-5 precedent adds `automation_provider` |
| finish reason / termination | **absent** | **Missing** — `ChatCompletionResponse` already carries `finish_reason`, so an I4 generation record is the natural place to persist it |
| latency | `processing_time_ms` | **Present** |
| token usage | `tokens_used` | **Present**, correctly nullable (§15.4) |
| cost | `cost` | **Present**, correctly nullable (§15.4) |
| generation kind | `prompt_type` | **Present**, but report-section vocabulary with no CHECK constraint |
| generation identity | `id` | **Present** |
| linkage to the interaction that caused it | **absent** | **Missing** — the decisive gap |
| actor / tenant | `created_by` (nullable, no FK), `organization_id NOT NULL` | **Partial / Present** |

`INFERENCE` — as a **generation record**, this table's shape is a good fit with **additive** columns (provider, model_version, finish reason, and an interaction/conversation link); it is not a good fit for representing *the interaction* itself (§7). Nothing in its DDL forbids additive evolution, and its two strict NOT NULLs (`organization_id`, `prompt_type`) would each require care (the latter would force a category value for every Insight generation).

---

## 9. AI telemetry fit

`DIRECT` — the platform already records AI cost/usage in **three** other places:

* `report_generation_queue.ai_model_used`, `ai_tokens_used`, `ai_cost`, `ai_processing_time_ms` — described by the RC2 Architecture Freeze as "the committed FinOps surface" for report generation;
* `document_processing_queue.automation_provider`, `automation_model`, `automation_model_version` (Gate-5 provenance migration) — the **truthful attribution precedent**, including a version column that `ai_content_history` lacks;
* `usage_tracking` — per-organisation/per-month **aggregates** (`ai_files_processed`, `batch_files_uploaded`, `manual_pages_extracted`, `reports_generated`, `total_storage_bytes`, `UNIQUE (organization_id, usage_month)`), i.e. the allowance/billing counter layer (I8 territory per §22).

| Insight telemetry concern | Where it belongs (evidence-based) |
| --- | --- |
| per-generation provider/model/version | a generation record (this table's shape) — **not** `usage_tracking`, which is aggregate |
| per-generation tokens/cost | a generation record, nullable per §15.4 — with an explicit rule that report generation's FinOps surface stays in `report_generation_queue` |
| latency | a generation record; §27 lists latency as operational visibility |
| per-organisation allowances / credits | `usage_tracking` + existing billing infrastructure (§22 "Do not create a parallel Insight billing system"; I8 owns policy) |
| request correlation / rate limiting | §27/§28 operational concerns, not this table |

`INFERENCE` — the table fits **per-generation telemetry** well, but only if it is declared the *single* per-generation home for Insight and does not become a second FinOps ledger: D2 §22.4 / Master Spec §23 forbid duplicate AI-history stores, and §22 forbids inventing AI credits or pricing. Telemetry ownership across report generation, document processing and Insight must be explicitly bounded rather than emergent.
---

## 10. Evaluation / feedback fit

`DIRECT` — `user_rating` (`CHECK 1–5`), `user_feedback` (text) and `was_accepted` (boolean) are the table's **only capabilities that no ratified Insight layer specifies**. Master Spec §8.1's Layer-2 content list does not mention feedback, acceptance or evaluation; §9.3's reconstruction chain does not either; §41 does not list an evaluation item; §42 defers no evaluation capability explicitly.

| Evaluation concept | Present | Ratified Insight requirement? |
| --- | --- | --- |
| human rating (1–5) | `user_rating` | **No** — not specified anywhere in the ratified Insight material |
| free-text feedback | `user_feedback` | **No** |
| acceptance flag | `was_accepted` | **No** |
| response quality/groundedness scoring | **absent** | §33.7 requires *AI evaluation* as a testing discipline, which is not the same as persisting end-user evaluation |
| reviewer/human-review workflow | **absent** | Review is a platform capability elsewhere; Insight has no review surface |

`INFERENCE` — a persisted evaluation/feedback capability is **architecturally supportable** by a table of this shape (additively), and D2 §22 explicitly frames the dormant table as holding "AI interaction/**cost/rating** data", so rating data is already contemplated. But because no ratified Insight layer requires end-user feedback, adopting it would be a **product-scope addition** requiring a PO decision, not an I4 engineering decision. `UNKNOWN` — whether end-user rating/acceptance is wanted at all.

---

## 11. Audit relationship

`DIRECT` — Layer 3 is `public.audit_trail`: append-only (Phase 7 trigger `p7_audit_trail_immutable` blocks UPDATE/DELETE for every role), columns `action_type`, `table_name`, `record_id NOT NULL`, `performed_by NOT NULL`, `performed_at`, `old_data`/`new_data`/`changes`, `ip_address`, `user_agent`, `metadata JSONB` (GIN-indexed), `created_at`; written through `backend/data/audit.py` (`AuditRepository.record`) and `backend/infra/audit_logger.py` (`AuditLogger`, `AuditSink`, `default_actor="system"`). Its Phase 7 taxonomy (`backend/domain/audit.py`) has categories authentication, authorization, document, extraction, mapping, validation, calculation, evidence, workflow, report, administration, system — **no AI category** — and outcomes limited to `success`/`failure`.

`DIRECT` — governing requirements: §8.1/§20.2 (the canonical ledger stays authoritative; must not be replaced), §20.4 (the AI audit event should establish that the interaction occurred and **link to the durable interaction record**, and must not carry the whole transcript or provider payload), §8.2 (conversation deletion must never erase the canonical record), §20.1 (layers must not be collapsed).

| Audit concept | Right home (evidence-based) |
| --- | --- |
| "an Insight AI interaction occurred" event | `public.audit_trail` (via the existing logger/repository), with `table_name`/`record_id` pointing at the durable interaction record and `metadata` carrying correlation |
| interaction ↔ audit correlation | `audit_trail.record_id` + `metadata` (already queryable, e.g. `metadata->>'organization_id'`) |
| tool-call correlation | `audit_trail.metadata` (no new ledger); an AI category would be a taxonomy addition, and the Phase 7 taxonomy is a closed set today |
| provider payload / transcript | **neither** the ledger (§20.4) nor a substitute for the interaction record |
| append-only immutability | `audit_trail` only; `ai_content_history` has no trigger and is therefore **not** an audit-grade structure |

`INFERENCE` — the AI-generation table should be **referenced by** the audit event, never **be** the audit event: it is mutable-by-design (no trigger), outside the ledger's append-only guarantee, and its columns are content-bearing, which §20.4 explicitly excludes from the ledger.
---

## 12. `report_id` relationship analysis

`DIRECT` — the **shipped** table has `report_id UUID` with **no foreign key**; the design artefact declared `report_id UUID REFERENCES report_generation_queue(id)` and the baseline did not ship it. There is also **no index** on the column. The relationship is therefore *semantic*, not enforced: nothing today links an `ai_content_history` row to a report, and nothing prevents such a row from carrying `report_id = NULL`.

| Shape | Assessment |
| --- | --- |
| **As shipped (bare nullable uuid)** | Does **not** technically prevent Insight reuse — a NULL `report_id` is valid and unrestricted. But it still encodes report-centric intent: any later attempt to enforce the designed FK would then constrain Insight rows too, and the column name advertises a parent that does not exist for Insight generations. It also means the report-provenance semantics the legacy documentation relies on are **unenforced** today (a latent data-integrity gap, not an Insight problem). |
| **As designed (`REFERENCES report_generation_queue(id)`)** | Would **complicate** broader reuse: to serve Insight it would have to stay nullable, becoming a conditional link with no meaning for most rows; a non-optional FK would simply make Insight rows impossible. It would also couple every Insight generation to a report-generation table unrelated to conversational Insight. |

`INFERENCE` — four consequences:

1. the report linkage **does not block** reuse technically, but it makes a reused table *mean two different things* depending on one nullable column — a polymorphic-parent smell with **no discriminator column** to disambiguate;
2. "**generalise**" would require a parent-type discriminator (or one column per parent type) — new schema and new semantics, with no existing constraint to migrate from;
3. "**replace**" would mean dropping/renaming a legacy column — permitted only under an authorised migration, and only after establishing that no environment holds rows;
4. "**remain report-specific**" plus a **separate** Insight structure avoids both problems and preserves the legacy report-provenance story.

`DIRECT` — a further, stronger consideration: a conversational Insight generation is naturally parented by a **conversation/message/interaction**, not a report, and the forensic report and the I4 pre-authorization audit both record that this table has no conversation parent. `INFERENCE` — the missing parent link matters more than `report_id` itself: *any* reuse option must add linkage anyway, so the incremental cost of a separate table is small relative to bending a report-scoped table into a conversational role.
---

## 13. Privacy / security analysis

`DIRECT` — current security posture: RLS **enabled** (Phase 8, `20260925000000`) but **no policy** exists → deny-by-default for `anon` and `authenticated`; `service_role` bypasses RLS (platform posture). No creator-private predicate; `created_by` nullable, no FK; `organization_id NOT NULL` with `ON DELETE CASCADE`.

| Data | Privacy implication | Governing rule |
| --- | --- | --- |
| raw prompts (`prompt_text`) | Highest-risk content; storing Insight customer questions here places customer text in a legacy-namespace table whose retention/access posture is undecided | §41 open item "raw question storage versus hash" (D2 PR-EX3); §17.1 context must be minimal/bounded |
| generated content (`generated_content`) | Same class as prompts; §20.4 forbids it in the ledger and it must not become the authoritative answer | §20.4, §8.1 |
| provider/model metadata | Never keys, secrets or provider payloads; attribution only when truthfully known | §15.2, §15.3, §27 |
| usage / cost | Commercial data; §22 forbids inventing AI credits/pricing and requires reuse of existing billing infrastructure | §15.4, §22 (I8) |
| feedback / rating | Opinion data about users and outputs; no ratified requirement yet | §10 above; D2 §22 mentions rating data |

`DIRECT` — relationship to the security layers:

* **I2 authorization** — any Insight-visible use of this table (or a successor) requires policies consistent with I2: organization membership plus creator-private visibility, re-evaluated per statement from the caller's identity, with server-side reauthorization. A table with RLS enabled but **no policy** cannot serve an authenticated Insight surface without **new policy design** — repurposing is therefore a security-modelling task, not only a column task.
* **I7 retention / deletion / export** — "deliberately OPEN until I7" (§21); no duration may be invented. `ON DELETE CASCADE` from `organizations` gives organisation-deletion behaviour, but per-record retention, hard/soft deletion, export and provider retention are unresolved, and the legacy table carries **no retention metadata**.
* **canonical audit** — §8.2 requires conversation deletion never to erase the canonical record, and §20.4 forbids payloads in the ledger; a content-bearing generation table therefore needs an explicit, decided relationship to retention and to the ledger before it holds Insight prompt/response text.
* `DIRECT` — carried-over OHD observation (I3 re-verification `:196`, `:287`): server-side log lines can carry offending parameter values. `RECOMMENDATION` — a future Insight generation record must not be echoed into logs, and prompt-bearing errors must stay free of customer text.

`INFERENCE` — privacy is the strongest argument for deciding the bounded home **deliberately** rather than extending a legacy table ad hoc: where raw prompts land determines which retention, deletion and access model governs them, and that is an open PO/legal item (§41).
---

## 14. Historical / production uncertainty carried forward

`DIRECT` (carried forward unchanged from the forensic report, not re-litigated here):

* `PRODUCTION ROW PRESENCE NOT VERIFIED` — no repository artefact measures production; the local demo observation was 0 rows `[OBS]` (QA-AI-001);
* **external/legacy writers `UNKNOWN`** — no writer exists *in this repository*, which is not the same as "no writer exists";
* **original V1/V2 authoring `UNKNOWN`** — pre-baseline history is absent;
* additionally `UNKNOWN` — whether any RLS **policy** exists in the live environment beyond RLS being enabled (no policy definition exists in any migration, but the live database was not queried);
* additionally `DIRECT` — the table has **no index**, so any future Insight query pattern would need indexing regardless of the option chosen.

**Additional evidence required before any future migration or repurposing (all outside this task's authority):**

1. an **authorised read-only production count** (and, ideally, per-organisation and per-report distribution) for `ai_content_history`;
2. confirmation of **whether any external/legacy writer** still targets the table (grants/policy inventory plus provider-level access review, since `service_role` bypasses RLS);
3. a **live policy/privilege inventory** for the table in each environment (`pg_policies`, role grants) — the repository shows RLS enabled with no policy, which must be confirmed rather than assumed;
4. an explicit **product statement on the legacy report AI journal** — is AI-generated report narrative expected to return (in which case the table has a future owner) or not;
5. the **I7 privacy decision** on raw prompt storage (§41 PR-EX3) and on retention/deletion/export;
6. the **PO bounded-home decision (Q1)** — and, if reuse is chosen, an explicit naming/ownership decision given D2 R24's canonical-namespace rule;
7. for any reuse route: an authorised **migration plan review** (policies, indexes, nullability tightening, possible rename) with a separate, explicit authorisation for any **data** handling — no backfill, migration or retirement is authorised today.

---

## 15. Option A — Evolve / reuse `ai_content_history`

**Advantages (`INFERENCE` from `DIRECT` facts):** no new table name is introduced; the existing generation-scoped shape already covers prompt, output, format, model, latency, tokens, cost and the unique feedback/acceptance trio; the table exists in every environment already (no creation migration); `organization_id NOT NULL` + cascade already matches I1's tenant pattern; and D2 §22 explicitly contemplates "an **extension** of the existing AI table" as a legitimate option.

**Disadvantages:** the table is **outside the ratified `carbontally_insight_*` namespace** (D2 R24/§3.8), so Insight data would live under a legacy name; it has **no conversation/interaction parent**, so linkage must be added anyway; `created_by` is nullable and there is **no creator-private policy**, so it cannot satisfy I2 as-is; `prompt_type` is `NOT NULL` with a report-section vocabulary and no CHECK, which forces a semantically wrong value for every Insight generation unless relaxed; it has **no index**, **no lifecycle/status**, **no provider**, **no `model_version`**, **no finish reason**, **no correlation identifier**; and reusing it makes the same table mean two things (report generation vs Insight generation) selected by a nullable `report_id` with no discriminator.

**Schema changes likely required (analysis only, not a migration proposal):** add provider/version/finish-reason/correlation columns; add a conversation/interaction linkage; make `prompt_type` meaningful for Insight (or relax it); make `created_by` reliably present for user-derived rows; add indexes; define RLS policies consistent with I2; decide `report_id` semantics (keep nullable and meaningless for Insight, or generalise); and decide the naming question.

**Semantic risks:** the legacy meaning of the table (report provenance surface, `prompt_type` sections, `report_id` parentage) is diluted or overloaded; any future enforcement of the designed `report_id` FK would collide with Insight rows; a legacy name carrying Insight data invites exactly the confusion the canonical naming rule exists to prevent.

**Backward compatibility:** additive columns are benign, but the `NOT NULL prompt_type`, the missing policies, and any future FK on `report_id` are **behavioural** changes for existing consumers — and existing consumers are `UNKNOWN`, so backward compatibility cannot be assessed from this repository alone.

**Auditability:** the table has **no immutability trigger**, so an audit-grade claim cannot rest on it; it can only be *referenced by* `audit_trail` events.

**Privacy:** the table has no retention metadata and no policy; putting raw Insight prompts here predetermines a privacy posture that I7 has not decided, and it mixes customer questions with legacy report content under one access model.

**Extensibility:** good at the column level (it already carries the telemetry/feedback axes), weak at the boundary level (no parent role, wrong namespace, ambiguous parentage).
---

## 16. Option B — New Insight AI-generation table

**Advantages:** the table is created under the ratified canonical namespace (`carbontally_insight_*`, D2 R24/§3.2/§3.8), which removes the naming conflict entirely; it can be designed with the correct parent (`conversation` and/or `interaction` reference, consistent with I1's composite-FK organisation invariant); creator/actor semantics can be `NOT NULL` where required and can carry I2-consistent creator-private RLS from day one; it can include provider, `model_version`, finish reason, correlation id and the answer-status link that the legacy table lacks; it can be indexed for the actual Insight query patterns; and it can mirror the ratification-friendly posture of I1 (explicit anon/authenticated grants, no UPDATE/DELETE for authenticated, `service_role` ALL) rather than inheriting an un-policied legacy table.

**Disadvantages:** it introduces a **second AI-content table**, which is precisely what D2 §22.4 / Master Spec §23 prohibit **unless** it is declared the single bounded home and the legacy table is explicitly dispositioned at the same time; it duplicates columns that already exist in the legacy table (model, tokens, cost, latency, rating) and would need a deliberate decision to *not* also duplicate `report_generation_queue.ai_*` FinOps semantics; it requires a new migration plus repository/service wiring (with the I3 D-01 lesson: wiring must be proven through the real `RepositoryBundle` factory, not a duck-typed test bundle); and any future migration of legacy rows (if any exist) carries data-handling risk.

**Duplication analysis (`INFERENCE`):** duplication is manageable **only** if scope is bounded as *per-generation Insight telemetry + evaluation*, leaving (a) conversation content in Layer 1, (b) audit in `audit_trail`, (c) report-generation FinOps in `report_generation_queue`, and (d) allowance aggregates in `usage_tracking`. Without those boundary statements the platform would hold four overlapping AI-cost records.

**Clean domain boundaries:** strongest of the three options — the Insight domain owns its own AI-generation record; the legacy table keeps its historical meaning; the canonical audit ledger stays authoritative; and the three-layer model (§20.1) is respected rather than blurred.

**Migration complexity:** one additive `CREATE TABLE` plus policies/indexes/grants, following the I1 migration pattern — materially simpler than restructuring a legacy table with `UNKNOWN` consumers, and it avoids touching data at all.

**Future extensibility:** high — evaluation, quality monitoring, human review flags and AI-performance analysis can be added additively inside the Insight namespace; the record can also remain the durable target that a Layer-3 audit event links to (§20.4).

---

## 17. Option C — Keep `ai_content_history` unchanged; introduce a separate structure only if needed

**Advantages:** zero risk to legacy structures and zero data exposure — nothing is restructured, renamed, purged or backfilled, which respects AGENTS.md §66/§79 (reuse where existing schema supports the requirement; do not remove legacy structures without an authorised disposition) and the D2 §22.2 instruction "Do NOT automatically reuse or delete it. No migration is authorised now"; it defers all schema work until the PO decides the bounded home (Q1) and the I7 privacy posture; and it preserves the option value of both Option A and Option B, since either remains available later.

**Disadvantages:** it leaves the immediate I4 question open, so any I4 implementation that must persist a generation record cannot proceed until the decision is made — the option is a *holding position*, not a resolution; the legacy table remains a permanent anomaly in the schema inventory (RLS enabled with no policy, no index, no FK on `report_id`, outside the canonical namespace) unless separately addressed; and the duplicate-store constraint (§22.4) still has to be satisfied at the moment any new structure appears.

**Legacy complexity:** unchanged but visible — the forensic report and this analysis both flag the un-policied RLS state and the unenforced report linkage; those are latent conditions that a future decision should address rather than inherit silently.

**Clean separation:** excellent in the interim, because nothing Insight-related is written into a legacy table.

**Future migration possibilities:** all remain open — Option A's restructuring, Option B's new table, or a decision to formally retire the legacy table after an authorised data review; none is foreclosed by deferring.

`INFERENCE` — Option C is architecturally the **lowest-risk interim position** and is fully compatible with the governing instruction not to perform an unauthorised migration or repurposing; it is not by itself a solution to the I4 persistence requirement.
---

## 18. Architectural recommendation (not a PO decision)

`INFERENCE`, evidence-based, explicitly **not** a PO disposition:

1. **Do not treat `ai_content_history` as the conversation (Layer 1) or as the audit ledger (Layer 3).** Both are ruled out by direct evidence: Layer 1 is already built and ratified, §20.1 forbids layer collapse, Layer 3 is the append-only `audit_trail` whose Phase 7 taxonomy has no AI category, and §20.4 excludes payloads from the ledger.
2. **Direct reuse of the current table *without restructuring* is not appropriate.** It lacks the interaction parent, provider/`model_version`, finish reason, correlation id, status, indexes and policies, and it sits outside the canonical namespace; reusing it as-is would place an I4 record in a table that cannot be joined to a conversation and cannot be read by `authenticated` at all (RLS enabled, no policy).
3. **Broader reuse is technically plausible but only as a restructured, deliberately bounded evolution** — and it collides with D2 R24's canonical-naming ratification, which points new Insight implementation at `carbontally_insight_*`. If the PO prefers reuse, the architectural prerequisite is an explicit decision on **namespace/name and parent linkage**, plus policy and index design — not merely additive columns.
4. **A separately-scoped Insight AI-generation record is architecturally cleaner**, provided the single-bounded-home constraint (§22.4, §23) is satisfied by deciding the legacy table's disposition **at the same time**, and provided the record is scoped to per-generation telemetry/evaluation rather than to conversation content or audit.
5. **The low-risk interim position (Option C) is compliant with the ratified documents**: D2 §22.2 states that no reuse, deletion or migration is authorised now, so deferring the schema work until the PO decision is the *compliant* default rather than an omission.
6. **Three boundaries must be stated explicitly** under any option, to avoid duplication: per-generation AI telemetry lives in exactly one place; report-generation FinOps stays in `report_generation_queue.ai_*`; allowance aggregates stay in `usage_tracking` and remain I8's concern.
7. **Rejected pattern:** one table representing the conversation **and** interaction **and** generation **and** telemetry **and** evaluation (§4 option F) — precisely the layer collapse §20.1 prohibits.
---

## 19. `Q1 ARCHITECTURAL EVIDENCE RESULT`

**Is broader reuse technically plausible?**
Yes. `DIRECT` — 13 of 16 columns are non-report-specific, the tenant key matches I1's pattern, `report_id` carries no shipped FK so it does not constrain new rows, and the table has never been altered, so additive evolution is unencumbered. `UNKNOWN` — whether it holds data, and whether an external writer exists.

**Is direct reuse of the current table without restructuring appropriate?**
No. `DIRECT` — it has no interaction/conversation parent, no provider or `model_version`, no finish reason, no correlation identifier, no index, no lifecycle status and no RLS policy (deny-by-default for `authenticated`), and it sits outside the ratified `carbontally_insight_*` namespace. As-is it cannot serve as an I4 record, and reuse without restructuring would not satisfy §9.3 (reconstructability) or §10 (authorization/RLS).

**Would a separate table be cleaner?**
Architecturally, yes — `INFERENCE` — because it removes the naming conflict (D2 R24), allows correct parentage and I2-consistent policies from the outset, avoids overloading a report-scoped table, and avoids touching legacy data. The cost is one additive migration plus the requirement to declare a single bounded home (§22.4) — which in turn requires the legacy table's disposition to be decided in the same decision.

**What must remain outside I4?**
`DIRECT` — conversation/message content (Layer 1, I1); the canonical audit ledger and AI audit-event taxonomy (§20; the Phase 7 taxonomy is closed); retention/deletion/export (I7, §21); billing/credits/allowances/provider cost policy (I8, §22); context/compaction (I5, §17.4); RAG, embeddings, vector stores, orchestration frameworks (§42); the answer-status taxonomy definition (§14 vs I3's closed vocabulary — Q3); any migration, rename, backfill or retirement of the legacy table; and any raw-prompt storage decision (§41 PR-EX3).

**What information is still required before a PO decision?**
(1) authorised read-only production row presence and distribution; (2) confirmation of whether any external/legacy writer targets the table; (3) a live RLS/privilege inventory per environment; (4) a product statement on whether AI-generated report narrative is ever returning; (5) the I7 privacy position on raw prompt storage and retention; (6) an explicit naming/ownership decision if reuse is chosen; (7) an authorised migration plan if any legacy column (notably `report_id`) is to be generalised or replaced.

**This is an architectural evidence result only.** It is **not** `Q1 CLOSED`, it does **not** choose a PO disposition, and it does **not** authorise any implementation, migration, rename or data operation.

---

## 20. Explicit non-decisions / items requiring PO authorization

`DIRECT` — nothing below was decided, changed or implemented by this analysis:

1. **Q1** — bounded home for AI interaction/cost/rating data (Option A/B/C): **OPEN**.
2. **Q2** — which ledger is canonical for AI audit events: **OPEN**.
3. **Q3** — answer-status enumeration versus I3's closed six-value vocabulary: **OPEN**.
4. **Q4** — raw prompt/question storage versus hash (§41 PR-EX3): **OPEN**; both the legacy table and any successor are affected.
5. **Q5** — Layer-2 mutability/immutability posture (§8.2 states only "separate lifecycle"): **OPEN**.
6. **Q7** — Layer-1 conversation/message lifecycle status (I1 deliberately omitted it): **OPEN**.
7. **I7** — retention, deletion, export, residency, provider retention: **DEFERRED** and not to be invented (§21).
8. **I8** — billing, credits, allowances, provider cost policy: **DEFERRED** (§22).
9. **Naming/ownership of the legacy table** — any rename into the canonical namespace, or a formal retirement: **requires PO authorization**; none is proposed or performed here.
10. **Any migration, extension, index, policy or constraint change** to `ai_content_history`, and any **data** handling: **NOT AUTHORIZED** (D2 §22.2).
11. **Introducing a new table**: **NOT AUTHORIZED** by this task — analysed only.
12. **End-user feedback/rating/acceptance as an Insight feature**: no ratified requirement; a product decision would be required.
13. **RLS policy design for any Insight generation record**: requires an authorised security-design step consistent with I2; not designed here.

**Stated limitations of this analysis:** it is based on repository artefacts only (no live database inspection, so live policy/privilege state and row presence are `UNKNOWN`); it has not been independently verified; and it must be reviewed by the PO — and independently by OHD if required — before any decision relies upon it.

**I4 remains NOT AUTHORIZED. Q1 remains OPEN.**
