# CarbonTally — Phase 8: Ask CarbonTally Persistent Conversation & AI Auditability Discovery

**Prompt ID:** `CT-P8-ASK-CARBONTALLY-PERSISTENCE-DISCOVERY-20260912-013`
**Document type:** Architecture discovery / design proposal — **NOT ratifiable as implementation authorisation**
**Date:** 2026-09-12
**Starting HEAD:** `6409956b714b291eea6cd2e76c080aca9c00e3ec` (branch `main`, 8 ahead of `origin/main`)
**Method:** repository evidence only (source, migrations, docs). No production access. No database access. No implementation.
**Status:** `DISCOVERY COMPLETE — READY FOR PO REVIEW` (see §J)

---

## 1. Executive summary

The Product Owner has decided that **Ask CarbonTally conversations are persisted**.

This document establishes, from repository evidence, what that decision means for
CarbonTally's architecture, what already exists that can carry it, what must be
extended, and what genuinely has to be built.

Six findings dominate.

**1. Ask CarbonTally does not exist yet in any form.** A strict repository search for
`ask_*` tables, `/api/v3/ask*` routes, and `AskCarbonTally` identifiers returns
**zero** results across `backend/`, `supabase/`, and `frontend/src/`. There is no
route, table, service, UI component, or provider binding for an authenticated
assistant.

**2. A substantial Ask CarbonTally *design* already exists — as an OHD audit
artifact, not as ratified architecture.**
`docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` (633 lines)
already specifies: the public assistant (Phase 1, implemented), an authenticated
assistant model for customer/consultant/PE/staff/admin (§5), a knowledge/chunk
architecture with a provider-neutral hybrid retrieval design (§6.3–6.4), a tool
architecture with a persona tool registry and a six-point tool contract (§7.1–7.3),
prompt-injection defence (§7.4), the PE document boundary (§7.5), a provider
abstraction (§8), conversation context (§9), security and audit (§10), an
implementation roadmap of Phases 1–7 (§11), a testing strategy (§12), and already-open
PO decisions (§13). **This task's subject matter is therefore mostly a *delta*
against an existing design, not a greenfield design.**

**3. That existing design contradicts the new PO decision on the specific point of
persistence.** The existing design assumes **non-persistent, session-bounded**
conversations: *"Bounded rolling context (last N turns) per session. Sessions are
short-lived in the browser"* (§9) and specifies *"Log per conversation event:
timestamp, session id, …"* (§10.2) — i.e. **logging**, not a persisted conversation
domain. The PO decision to persist conversations **supersedes** those two statements.
This is a documented architectural contradiction (§23, R-1); it requires PO
acknowledgement, not a silent rewrite.

**4. CarbonTally already has the deterministic AI foundation to reuse, and it is
consistent with every non-negotiable rule in this brief.**
`backend/infra/llm_client.py` is the single provider abstraction
(OpenAI/Anthropic-compatible `/chat/completions`, injectable transport,
`AIExtractionFailedError` on every failure). `backend/infra/ai_runtime.py` supplies
truthful provider attribution via `provider_label()` and
`configured_ai_attribution()` — provider/model read from environment, API key
deliberately never read. `backend/services/ai_document_extraction.py` already encodes
the exact AI boundary Ask CarbonTally needs: *"AI output is **candidate** data only"*,
*"never a false success"*, *"No credentials or raw document contents are logged or
persisted"*, *"The LLM is the only non-deterministic input."*
**No second LLM abstraction is required or permitted.**

**5. The human messaging tables cannot carry Ask CarbonTally, and the evidence is
concrete.** `public.messages` is person-to-person by construction (`sender_id`,
`receiver_id`, `is_read`, `delivered_at`, `read_at`, `read_by UUID[]`, `read_count`,
`is_deleted`, `is_archived`) — it has no actor-type for "CarbonTally system", no
tool-call linkage, and no authoritative-reference fields. `public.conversations`
carries support-ticket semantics (`staff_id`, `customer_id`, `is_urgent`, `priority`,
`read_by UUID[]`, `unread_count`, `participant_count`). Critically,
`MessagingRepository.list_conversations_for_org()` filters on `organization_id`
**only** (`backend/data/messaging.py:129-141`) — there is no `conversation_kind`
filter. Entity threads escape only because `create_entity_conversation()` sets
`organization_id = NULL` (`backend/data/messaging.py:37-51`). **Any Ask conversation
carrying an `organization_id` would therefore appear in the human messaging list of
every member of that organisation.** That is a direct, verifiable argument for a
separate domain, not a stylistic preference.

**6. The audit architecture is stronger than the brief assumes, and it constrains the
design in two important ways.** `public.audit_trail` is enforced **append-only at the
database level** for every role by the Phase 7 trigger `p7_audit_trail_immutable()`
(`supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql:32-48`),
whose own comment states that a future retention/purge process *"must deliberately
drop this trigger first (documented, controlled)"*. The Phase 7 taxonomy
(`backend/domain/audit.py:14-62`) provides `ACTOR_TYPES` (including `system`),
`ORIGINS`, `OUTCOMES` **deliberately limited to `success`/`failure`**, and eleven
`CATEGORIES` — **none of which is an AI/assistant category**. The answer lifecycle
required by §21 (`no_data`, `insufficient_data`, `unauthorized`, `tool_failure`,
`provider_failure`, `ungrounded`, `partial`, `needs_clarification`) **cannot** be
expressed in that vocabulary and must not be forced into it.

**Net architectural conclusion.** Ask CarbonTally requires a **new, bounded
conversation domain** (`ask_*`) with `organization_id` on every row and Phase 8-grade
RLS from day one, reusing: the existing `LLMClient` + `ai_runtime` attribution, the
existing identity/authorization guards, the existing `audit_trail` ledger for
reference-level events, the existing `billing_commercial_config` versioned rule
mechanism for allowance policy, the existing `usage_tracking` counter pattern, the
existing repository/API conventions, and the existing chat UI primitives.
**No decisions are required before the design is ratified. Implementation is NOT
authorised by this document.**

---

## 2. Product decision baseline

### 2.1 The decision (given, not re-litigated)

> **Persistent Ask CarbonTally conversations = YES.**

Persistence exists to provide: (1) conversational context and continuity; (2) useful
follow-up questions; (3) historical analytical context; (4) reconstructable AI
interactions; (5) appropriate future audit/evidence support.

### 2.2 The binding invariant

> **Conversation history is NOT authoritative carbon data.**

The authoritative system of record remains: emissions/calculation data,
`calculation_snapshots`, emission factors, evidence, provenance, `report_versions`,
`audit_trail`, and the other domain records. A stored sentence such as *"Your Scope 2
emissions were 184.6 tCO₂e"* is **conversational output**; the authoritative value
remains the persisted calculation/snapshot it was derived from.

### 2.3 What this decision changes relative to the existing design

| Existing design statement | Source | Effect of the PO decision |
|---|---|---|
| "Bounded rolling context (last N turns) **per session**" | AI-assistant arch. §9 | Superseded — context is now persisted per conversation |
| "Sessions are **short-lived in the browser**" | AI-assistant arch. §9 | Superseded for Ask CarbonTally (public assistant unaffected) |
| "**Log** per conversation event … session id" | AI-assistant arch. §10.2 | Extended from logging to a durable, queryable interaction record |
| "Open PO decision: **Retention of chat/audit logs**" | AI-assistant arch. §13.5 | Now a live blocker for the persistence domain (§21) |

Everything else in that document (tool contract, persona registry, injection
defence, PE boundary, retrieval design, grounding check) remains **compatible and
reusable unchanged**.

### 2.4 Why this is a *delta* document, not a replacement

`CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` lives under `docs/audit/openhands/`
and is not part of the frozen D1–D21 UX decision set. Per AGENTS.md §63 and §80 it is
**design evidence requiring ratification**, not a frozen decision. This document does
not reopen it; it specifies precisely the persistence and auditability layer it
leaves undefined, and flags the two statements the PO decision supersedes.

---

## 3. Current repository state (verified 2026-09-12)

| Fact | Value | How verified |
|---|---|---|
| Branch | `main` | `git branch --show-current` |
| Starting HEAD | `6409956b714b291eea6cd2e76c080aca9c00e3ec` | `git rev-parse HEAD` |
| Ahead/behind `origin/main` | 8 ahead / 0 behind | `git rev-list --left-right --count` |
| Working tree | 208 modified, 52 untracked, 0 staged | `git status --porcelain` |
| Push status | **not pushed** | local only |

The 208/52 pre-existing worktree state is **preserved exactly**; this task added only
two documentation files and touched no application code, migration, RLS policy,
route, or frontend file.

### 3.1 What exists that is relevant to this discovery

| Area | Artifact | Nature |
|---|---|---|
| LLM provider | `backend/infra/llm_client.py` | Implemented, single abstraction |
| AI runtime config/attribution | `backend/infra/ai_runtime.py` | Implemented |
| AI extraction engine | `backend/services/ai_document_extraction.py` | Implemented (candidate-only) |
| Public assistant | `frontend/src/public/assistant/*` | Implemented, **deterministic, no backend, no persistence** |
| Authenticated assistant | `docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` | **Design only** (OHD); Phases 3–7 unimplemented |
| Human messaging | `conversations`, `messages`, `conversation_participants`, `typing_status`, `file_attachments`, `message_activity_log`, `conversation_activity_log` + `backend/api/v3_messaging.py` | Implemented |
| Messaging UI | `frontend/src/components/chat/*` (8 components) | Implemented |
| Audit ledger | `public.audit_trail` + `AuditRepository` + `/api/v2/admin/audit` | Implemented, append-only |
| Audit evidence package | `reporting.audit_package()` | Implemented |
| AI content history | `public.ai_content_history` | **Dormant — zero code references** |
| Usage counters | `public.usage_tracking` | Implemented |
| Commercial config | `public.billing_commercial_config` | Implemented (versioned rules) |
| Ask CarbonTally | — | **Does not exist** |

### 3.2 Verification statement

Every claim in this document is derived from files readable in this repository at
the HEAD above. No claim is derived from a live database, a running service,
production, or provider credentials. Where a claim could not be closed from
repository evidence it is marked `[UNVERIFIED]` and appears in §23.

---

## 4. Existing AI architecture

### 4.1 Provider transport — `backend/infra/llm_client.py`

| Property | Evidence |
|---|---|
| Single abstraction | Class `LLMClient(base_url, api_key, model, timeout_seconds, transport)` |
| Wire protocol | OpenAI/Anthropic-compatible; POSTs to `<base_url>/chat/completions` |
| Determinism | `temperature` defaults to `0.0`; `max_tokens` defaults to `512` |
| Testability | Injectable `LLMTransport` (`Callable[[LLMRequest], ChatCompletionResponse]`); real HTTP otherwise |
| Failure contract | **Every** failure — connection error, non-2xx, malformed body — raises `core.exceptions.AIExtractionFailedError` (HTTP 502) |
| Dependency rule | Imports only from `core` (exceptions); "contains no business logic" |
| Signature | `async complete(prompt, *, system=None, temperature=0.0, max_tokens=512) -> str` |

**Gaps relevant to Ask CarbonTally (EXTEND, not replace):**

1. **Single-turn only.** `complete()` builds `[system?, user]`; there is no
   multi-message / conversation-history parameter. Ask CarbonTally needs a bounded
   history path.
2. **No tool/function-calling surface.** There is no `tools=` parameter and no
   tool-call parsing. The existing design's tool model (§7) is *server-side tool
   execution by the gateway*, not provider-side function calling — this is
   **compatible** with the current client and is the correct reading of the design.
3. **No usage/token/cost surfaced.** `complete()` returns `str` only. Therefore
   `ai_content_history.tokens_used` / `cost` and any token-based allowance
   accounting **cannot be populated today**. This is a real, concrete gap (§16).
4. **No streaming.**

### 4.2 Runtime configuration & truthful attribution — `backend/infra/ai_runtime.py`

Three environment variables gate everything:
`CARBONTALLY_AI_BASE_URL`, `CARBONTALLY_AI_API_KEY`, `CARBONTALLY_AI_MODEL`.
Documented invariant (module docstring): *"No credentials are ever written to the
database or logs by this module."*

| Function | Behaviour | Reuse for Ask CarbonTally |
|---|---|---|
| `configured_ai_extraction_engine()` | Returns an engine only when all three vars are set; returns `None` on any malformed config or import error so the deterministic pipeline always runs | **Pattern (loud-degrade)** — Ask must likewise be inert when unconfigured |
| `provider_label(base_url)` | Derives a provider label from the endpoint **host**; well-known domains map to canonical labels (`openai`, `anthropic`, `openrouter`); anything else returns the hostname — *"never a fabricated canonical name"* | **REUSE — directly** for `provider` attribution |
| `configured_ai_attribution(model_version=None)` | Returns `{provider, model, model_version}`; **never reads the API key**; `model_version` is `None` unless truthfully known — *"never fabricated or guessed from the model id"* | **REUSE — directly** for AI-interaction provider/model metadata |
| `_MAX_PROVIDER_LABEL_LENGTH = 120` | Column-length bound (currently tied to `document_processing_queue.automation_provider`) | Constraint to carry into any new provider column |

**Important nuance the brief anticipated.** `configured_ai_attribution` documents that
*"A non-None result means the runtime is configured; it does not by itself mean an AI
run occurred."* Ask CarbonTally must therefore record attribution **per interaction**
at call time, and must never infer "AI was used" from configuration presence.

### 4.3 The established AI boundary — `backend/services/ai_document_extraction.py`

This module is the repository's canonical statement of how AI may be used. Its
contract (docstring, lines 8–21) is quoted because it is the precedent Ask CarbonTally
must inherit:

- *"The LLM is the only non-deterministic input. The prompt, JSON parsing and
  post-processing are deterministic."*
- *"AI output is **candidate** data only."* — it still passes the deterministic
  completeness gate, factor matching, item validation, and the canonical
  `engines.calculation.CalculationRequest` boundary before anything is persisted.
- *"`unit` values are canonicalised with `core.units.normalize_unit` — the Phase-1
  canonical mechanism. This module never invents a second normaliser."*
- *"Failures (transport, non-JSON, malformed fields) return an `error` /
  low-confidence envelope instead of raising, so the durable caller represents them
  durably (blocked / manual review) — never a false success."*
- *"No credentials or raw document contents are logged or persisted."*
- `DEFAULT_MAX_TEXT_CHARS = 20_000` bounds prompt size for long documents.

**Direct architectural mapping to Ask CarbonTally:**

| Existing AI rule | Ask CarbonTally equivalent |
|---|---|
| AI output is candidate only | **The LLM answer is narrative only**; the authoritative result is the tool's structured output |
| Never a false success | Tool/provider failures become explicit statuses, never an empty-but-green answer |
| No second normaliser | No second LLM client, no second provider registry |
| No creds/raw docs logged | Minimised prompts; no secrets or raw document bytes in conversation rows |
| Bounded prompt size | Bounded context window (§12) |

### 4.4 The public assistant — implemented, and deliberately not a template for persistence

| Property | Evidence |
|---|---|
| Files | `frontend/src/public/assistant/AssistantWidget.jsx` (329 lines), `assistantKnowledge.js` (331 lines), `assistant.css` |
| Engine | `handleQuery(raw)` — pure local scoring: `normalize`, `stem`, `analyzeQuery`, `VOCAB` expansion, `PHRASE_HINTS`, `scoreItem`, `fallbackResponse` |
| Backend calls | **None.** No `fetch(`, no API, no LLM |
| Persistence | **None.** No `localStorage`/`sessionStorage` usage |
| Sources | `SOURCE_FAQ = 'CarbonTally Customer FAQ'`, `SOURCE_ASSISTANT = 'CarbonTally Assistant'` |
| Follow-up suggestions | `SUGGESTED_QUESTIONS` already exported |
| Design authority | AI-assistant arch. §11 PHASE 1 — "**Backend:** none. **APIs/tools:** none (deterministic local layer)." |

This is the *only* working assistant in the product, and it must remain a
**public, unauthenticated, non-persistent** surface. Authenticated Ask CarbonTally is a
different product surface (§19) and must not be implemented by "turning on persistence"
in this widget.

### 4.5 `public.ai_content_history` — a dormant table that is nevertheless important

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
    user_rating INTEGER CHECK (user_rating IS NULL OR (user_rating BETWEEN 1 AND 5)),
    user_feedback TEXT,
    was_accepted BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);
COMMENT ON TABLE public.ai_content_history IS 'AI generation history';
```
(`supabase/migrations/00000000000000_init_schema.sql:1041-1060`)

**Verified facts:**

- `organization_id` is **NOT NULL** → the `rc2_rls.sql` §3 dynamic loop (which creates a
  tenant policy for every table carrying an `organization_id`) **does** cover it.
- **Zero code references** anywhere in `backend/` or `frontend/src/` — verified by
  repository-wide search. It is a legacy D-phase scaffold, not a live pathway.
- It already carries **prompt / model / tokens / cost / rating / feedback** fields — i.e.
  the *shape* of AI usage accounting exists at schema level.
- It has **no** conversation, message, tool-call, reference, or status semantics.

**Classification:** `REUSE (partial — cost/rating/feedback precedent)` +
`EXTEND (if a per-generated-content record is wanted)` + `DO NOT REUSE as the
conversation domain` (§8.2). Its existence is evidence that the repository already
expects AI-generated content to be persisted with provenance **and** that a
*conversational* domain is a genuinely different thing.

### 4.6 What does not exist

| Missing | Consequence |
|---|---|
| Any Ask CarbonTally table | New domain required |
| Any `/api/v3/ask*` route (`grep` = 0 results) | New router required |
| Any authenticated asking service | New service layer required |
| Any AI/assistant category in `domain/audit.py` | Taxonomy extension or separate status vocabulary required |
| Any AI-query/token counter in `usage_tracking` | New counter (or config-driven accounting) required |
| Any tool registry implementation | Design exists (§7.2), code does not |
| Token/cost surfacing from `LLMClient` | Concrete EXTEND item |
| Any authenticated assistant UI (`grep -i assistant frontend/src/v3/` = 0 results) | New UI required |

---

## 5. Existing messaging architecture (Human ↔ Human)

### 5.1 Schema (verified in `init_schema.sql`)

**`public.conversations`** (lines 673–691):
`id`, `organization_id` (**nullable**), `staff_id`, `customer_id`, `subject`, `status`,
`last_message_at`, `created_by`, `closed_by`, `closed_at`, `is_urgent`, `priority`,
`created_at`, `updated_at`, `read_by UUID[]`, `unread_count`, `participant_count`.

**`public.conversation_participants`** (lines 694–705):
`conversation_id` FK → `conversations` ON DELETE CASCADE, `user_id` NOT NULL,
`joined_at`, `last_read_at`, `is_active` DEFAULT TRUE, `metadata JSONB`.

**`public.messages`** (lines 709–735):
`conversation_id` FK, `sender_id`, `receiver_id`, `organization_id`, `subject`,
`content` NOT NULL, `is_read`, `parent_message_id`, `sent_at`, `delivered_at`,
`read_at`, `is_deleted`, `deleted_at`, `is_archived`, `archived_at`, `read_by UUID[]`,
`read_count`, `last_read_at`, `attachments JSONB`, `has_attachments`.

**Also present:** `file_attachments`, `typing_status`, `message_activity_log`
(line 1803: `message_id`, `conversation_id`, `user_id`, `action_type`,
`action_details JSONB`, `ip_address`, `user_agent`), `conversation_activity_log`
(line 1817).

### 5.2 The entity extension (Phase 5) — precedent for adding a conversation *kind*

`supabase/migrations/20260902040000_phase5_pe_operational_messaging.sql`:
adds `conversation_kind text` (default `'org'`, then NOT NULL) and
`processing_entity_id uuid`; backfills existing rows to `'org'`; adds a CHECK enforcing
**org XOR entity** (`conversation_kind='org' AND organization_id IS NOT NULL AND
processing_entity_id IS NULL`, or `'entity' AND organization_id IS NULL AND
processing_entity_id IS NOT NULL`); adds indexes on
`(processing_entity_id, conversation_kind)` and `(conversation_kind, created_at DESC)`;
and adds **entity-scoped RLS policies** gated on the helper
`public.is_active_pe_member(p_entity uuid)` (line 71).

**This matters twice over.** It proves the team *can* extend `conversations` with a kind
discriminator and correct RLS — and it demonstrates the cost: the human messaging table
now carries two semantics, and the org-scoped list query stays safe only because entity
rows leave `organization_id` NULL.

### 5.3 Authorization model — `backend/api/v3_messaging.py`

`_authorize_org_actor(repos, current_user, organization_id) -> str` resolves exactly one
of three participant roles, or raises 403:

| Participant | Gate |
|---|---|
| `org_member` | `current_user.is_org_member` **and** `current_user.organization_id == organization_id` |
| `consultant` | `ensure_consultant_org_access(current_user, repos, organization_id)` — requires an **ACTIVE** consultant-client grant (D15) |
| `staff` (N1 "CarbonTally Support / Authorised Admin") | `current_user.is_staff` **and** `_resolve_context(...)` yields `context.profile.entity_id is None` (INTERNAL staff only) **and** `ensure_staff_permission(context, "can_manage_staff")` |

Documented denials (module docstring): *"General employees and Processing Entity staff
never get messaging access (entity staff are neither org members nor consultants; RLS
has no entity messaging storey) — the D18 boundary is absolute (D19 §17)."*

**This is the single most directly reusable authorization pattern in the repository for
Ask CarbonTally** (§7.3, §19): already server-side, identity-derived,
scope-from-session, permission-catalog-backed, and explicitly denying PE and general
staff.

### 5.4 Persistence & Realtime

Same module: *"the API persists rows through the service role; the frontend subscribes
with `postgres_changes` (Supabase Realtime) for live updates."*
→ **Established pattern: writes go through the API under the service role; the browser
observes via Realtime.** Any RLS posture for a new domain must be designed knowing the
backend is expected to bypass RLS (§17, §19).

### 5.5 Repository layer — `backend/data/messaging.py`

`MessagingRepository` provides `get`, `create_conversation`,
`list_conversations_for_org`, `count_conversations_for_org`, `close_conversation`,
`add_participant`, `list_participants`, `set_participant_active`, `send_message`,
`list_messages`, `count_messages`, `mark_conversation_read`, `_touch_conversation`,
`list_entity_conversations`, `get_entity_conversation`, `create_entity_conversation`,
`ensure_participant`. The org list/count queries filter on **`organization_id` only**
(no `conversation_kind` predicate) — see §1 finding 5.

### 5.6 Domain layer — `backend/domain/messaging.py`

Pure frozen dataclasses. Module docstring: *"This module is the pure domain model
(immutable dataclasses); it never authorizes."* `CONVERSATION_STATUSES = ("open",
"closed")` is documented as *"presentation only — the conversation row's authority comes
from participation + org/consultant RLS."*

**Convention to inherit:** domain = pure data, no authorization; authorization lives in
the API layer; RLS is the backstop.

### 5.7 UI primitives — `frontend/src/components/chat/`

`ChatWidget.jsx`, `ChatLayout.jsx`, `ChatSidebar.jsx`, `ChatList.jsx`,
`ChatWindow.jsx`, `ChatMessage.jsx`, `ChatInput.jsx`, `ChatHeader.jsx`,
`ChatParticipant.jsx` (+ `css/ChatWidget.css`, `css/realtime_chat.css`).

These are presentation primitives (composer, bubble, list, layout). They are reusable
for Ask CarbonTally **only** if their props are presentation-level; they must not drag
human-messaging semantics (read receipts, typing indicators, participant presence) into
an Ask thread. §23 R-6 records this as a verification item before any UI work.

---

## 6. Existing audit architecture (Phase 7)

### 6.1 The ledger — `public.audit_trail`

```sql
CREATE TABLE public.audit_trail (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    action_type VARCHAR NOT NULL,
    table_name VARCHAR NOT NULL,
    record_id UUID NOT NULL,
    performed_by UUID NOT NULL,
    performed_at TIMESTAMPTZ,
    old_data JSONB, new_data JSONB, changes JSONB,
    ip_address INET, user_agent TEXT, metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```
(`init_schema.sql:1669-1683`) — **no `organization_id` column**; org scoping is carried in
`metadata` (see 6.4).

### 6.2 Append-only enforcement (the critical constraint)

`supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql`:

```sql
CREATE OR REPLACE FUNCTION public.p7_audit_trail_immutable()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'audit_trail is append-only (Phase 7): % is not permitted', TG_OP
        USING ERRCODE = 'raise_exception';
END;
$$;

CREATE TRIGGER p7_audit_trail_immutable
    BEFORE UPDATE OR DELETE ON public.audit_trail
    FOR EACH ROW EXECUTE FUNCTION public.p7_audit_trail_immutable();
```

Comment: *"Phase 7 — blocks UPDATE/DELETE on public.audit_trail so the canonical audit
ledger is append-only for **every role**."* The migration header adds: *"A future
authorised retention/purge process must deliberately drop this trigger first
(documented, controlled)."*

**Consequence:** if AI-interaction audit records are written to `audit_trail`, they
inherit un-deletable-for-anyone immutability — excellent for integrity, **hostile to any
future retention/erasure requirement** (§15, §21.3).

### 6.3 Taxonomy — `backend/domain/audit.py:14-62`

Additive, stored in `audit_trail.metadata` JSONB — *"no schema change"*:

| Vocabulary | Values |
|---|---|
| `ACTOR_TYPES` | `human`, `internal_staff`, `org_user`, `consultant`, `pe_staff`, **`system`** |
| `ORIGINS` | `human`, `system` |
| `OUTCOMES` | `success`, `failure` — *"success/failure only — never a fabricated third state"* |
| `CATEGORIES` | `authentication`, `authorization`, `document`, `extraction`, `mapping`, `validation`, `calculation`, `evidence`, `workflow`, **`report`**, `administration` |

`audit_category(action_type)` maps an action verb to a category via
`_ACTION_PREFIX_CATEGORY` (longest-prefix-first) with surface prefixes stripped
(`pe_calculate` → `calculate`). `AuditEntry` validates `category in CATEGORIES`.

**Two hard findings:**

1. **There is no AI/assistant category.**
2. **`OUTCOMES` cannot express** `no_data`, `insufficient_data`, `unauthorized`,
   `tool_failure`, `provider_failure`, `ungrounded`, `partial`, or
   `needs_clarification`. Forcing them in would either widen a ratified vocabulary or
   misrepresent several of them as `failure`. **Answer status therefore belongs to the
   Ask domain, not to the Phase 7 taxonomy** (§11, §21).

### 6.4 Phase 7 indexes (`.../p7_audit_immutability_and_indexes.sql:34-52`)

`idx_audit_trail_performed_at (performed_at DESC)` ·
`idx_audit_trail_action_type (action_type)` ·
`idx_audit_trail_table_record (table_name, record_id)` ·
`idx_audit_trail_metadata_gin GIN (metadata jsonb_path_ops)` ·
`idx_audit_trail_org ((metadata->>'organization_id')) WHERE metadata ? 'organization_id'`.

The last is the **established convention: organisation scoping in audit is
`metadata->>'organization_id'`**, with a partial expression index to keep it lean.

### 6.5 Read/write surfaces

- **Repository:** `backend/data/audit.py` — `AuditRepository.record()` inserts into
  `audit_trail` using `_actor_uuid(actor)` (a machine zero-UUID marker for system
  actors); plus `query()`, `count()`, `export_csv()`, `get_by_correlation()`, `get()`,
  `save()`, `delete()`.
- **API:** `backend/api/admin_audit.py` — prefix `/api/v2/admin/audit`,
  `Depends(require_admin())`; filters `correlation_id`, `entity_type`, `entity_id`,
  `action`, `actor`, `occurred_after`, `occurred_before`, `limit` (≤500), `offset`.
  Docstring: *"Exposes the existing `data.audit.AuditRepository` — no second audit-log
  system is created."*
- **Evidence package:** `backend/data/reporting.py::audit_package()` — a self-describing
  `carbontally_audit_evidence_package` (package_version 1) containing organisation,
  readiness, `calculation_snapshots` (with factor provenance + `content_hash`),
  `workflow_history`, and an `integrity` block (sha256), explicitly carrying
  `not_assurance: True` and `AUDIT_NOT_ASSURANCE_NOTICE`.

### 6.6 Overlapping log tables already in the schema (a warning)

`public.activity_logs` (`user_id`, `organization_id`, `action`, `resource_type`,
`resource_id`, `details JSONB`, `ip_address`, `user_agent`, `metadata JSONB`,
**`updated_at`** → mutable), plus `message_activity_log` and
`conversation_activity_log`.

CarbonTally **already has three overlapping activity/message log tables**. AGENTS.md §66
and §79 require that a new domain not add a fourth competing log without justification.
The recommendation in §11 is therefore: **one interaction record in the canonical
ledger** plus **one Ask-owned provenance row** — not a new generic activity log.

---

## 7. Authorization / scope analysis

### 7.1 The guards Ask CarbonTally must inherit

| Guard | Location | Function |
|---|---|---|
| `ensure_org_access` | `backend/api/dependencies.py` | Tenant membership gate |
| `require_org_member` | `backend/api/dependencies.py` | Tighter org-member gate |
| `require_admin` | `backend/api/dependencies.py` | Staff/admin gate (used by the audit API) |
| `ensure_consultant_org_access` | `backend/api/consultant_auth.py` | Requires an ACTIVE consultant→client grant |
| `_resolve_context` + `ensure_staff_permission` | `backend/api/operations_auth.py` | Resolves the staff profile (incl. `entity_id`) and checks a capability from the authoritative `staff_roles` catalog |
| `is_active_pe_member(entity)` | SQL helper (`20260902040000_phase5_pe_operational_messaging.sql:71`) | PE membership backstop used in RLS |
| `get_current_user` | `backend/auth.py` | Verified identity (`AuthUser`) |

### 7.2 The five scopes and how a conversation must bind to each

| Domain | Identity source | Scope binding for an Ask conversation | Evidence for the gate |
|---|---|---|---|
| **Customer** | org membership | `organization_id` = caller's org; role from org membership (Owner/Admin/Member/Viewer) | `_authorize_org_actor` `org_member` branch |
| **Consultant** | ACTIVE consultant-client grant | `organization_id` = the **active client**; not the consultant's own firm | `ensure_consultant_org_access`; AI-assistant arch. §5.3 (`*` = always scoped to active client) |
| **PE** | `staff_profiles.entity_id` + `is_active_pe_member` | Would be **entity** scope with `organization_id` NULL — and per §19 the recommendation is **no PE Ask domain in this phase** | AI-assistant arch. §5.4 / §7.5; D18 absolute boundary |
| **Internal staff** | `staff_profiles` with `entity_id IS NULL` | `organization_id` = the authorised org; capability-gated | `_resolve_context` + `ensure_staff_permission` |
| **Public** | none | **No conversation is persisted at all** (§19.1) | AI-assistant arch. §4, §11 PHASE 1 |

### 7.3 The governing rule: a conversation is never an authorization mechanism

> **A conversation must never become an authorization mechanism.**

Concretely, these invariants are **required**:

1. Retrieval of an existing conversation re-runs the **current** scope check on
   **every request** — never trusting that the caller was authorised when the
   conversation was created.
2. Every tool call re-derives scope **from the verified session**, never from
   conversation text and never from stored conversation metadata (AI-assistant arch.
   §7.3 point 2: *"Derive scope … from the session — never from free text in the
   prompt"*; §9: *"Context contains the authorization scope … injected by the gateway —
   never derived from chat text"*).
3. Stored references (report id, snapshot id, evidence id) are **pointers to be
   re-authorised**, not grants. A stored reference to a report the caller can no longer
   see must resolve to **denied**, not to the stored value.
4. Authorization state is **not** cached in the conversation row.

### 7.4 The revoked-access scenario (why this is not theoretical)

The consultant operating model (AGENTS.md §10–11) explicitly allows a consultant-client
relationship to **end** while the organisation, its data, and its history are preserved.
A consultant with persisted Ask conversations about that client must **immediately lose
the ability to open them and receive any data from them** once the grant is revoked —
because each read and each tool call is re-authorised. This is the sharpest test of §7.3
and must be a QA case (AGENTS.md §45: `Consultant A → Consultant B's client`).

### 7.5 Staff capability nuance

The messaging precedent deliberately requires **`can_manage_staff`** for the staff
messaging path. Ask CarbonTally must not inherit that choice by accident: reading the AI
conversations of a customer organisation is a **different capability** from messaging.
Whether any staff role should read customer Ask conversations is a **PO decision**
(§19.5, §21) and must be an explicit capability — not a by-product of `is_staff`
(AGENTS.md §14).

### 7.6 Auditor / Assurance Reviewer

Verified across the Phase 7 and Phase 8 evidence base: **no auditor/assurance/reviewer
role, table, workspace, API, or capability exists.** No reviewer access may be introduced
by this task (AGENTS.md §62; brief §10). The consultant active-grant pattern
(`consultant_clients` + `ensure_consultant_org_access`) is the recommended future
analogue if an auditor capability is later ratified.

---

## 8. Existing schema reuse analysis

### 8.1 Table-by-table classification

| Structure | Classification | Reasoning (repository evidence) |
|---|---|---|
| `conversations` | **DO NOT REUSE** for Ask (§8.2) | Human ticket semantics, no actor type; and the org-list query has no kind filter |
| `messages` | **DO NOT REUSE** | `sender_id`/`receiver_id`/`is_read`/`delivered_at`/`read_by` are person-to-person |
| `conversation_participants` | **DO NOT REUSE** | Participation model is human; Ask has one human + a system actor |
| `typing_status` | **DO NOT REUSE** | Meaningless for a request/response AI turn |
| `file_attachments` | **DEFER** | Relevant only if users may attach files to an Ask turn — unresolved PO decision (§21) |
| `message_activity_log`, `conversation_activity_log` | **DO NOT REUSE** | Message/conversation-keyed; would couple Ask to human FK semantics |
| `activity_logs` | **DO NOT REUSE** | Mutable (`updated_at`), generic, already overlapping — adding Ask dilutes rather than strengthens provenance |
| `audit_trail` | **REUSE (reference-level events only)** | Canonical ledger, append-only, `(table_name, record_id)` addressed, `metadata` carries taxonomy. Perfect for "an Ask interaction occurred, referencing X"; wrong for full prompt/answer content (§11.4) |
| `ai_content_history` | **PARTIAL REUSE precedent / EXTEND** | Has `prompt_type`, `prompt_text`, `model_used`, `tokens_used`, `cost`, `user_rating`, `user_feedback`, `was_accepted`, `report_id`, NOT NULL `organization_id`; dormant; lacks conversation/message/reference/status semantics |
| `report_generation_queue` | **REUSE (referenced artefact)** | Predictable source for a "show me the report" tool |
| `report_versions` | **REUSE (referenced artefact)** | Correct stable reference for "compare this report with the previous version". Note the `is_current` defect, §23 R-2 — owned by S1, **not** expanded here |
| `calculation_snapshots` | **REUSE (referenced artefact)** | Authoritative emissions value plus `content_hash`, `factor_id`, `factor_source`, `source_item_id`, `source_file`, `source_page` — the ideal tool result and natural provenance reference |
| `emission_factors` | **DO NOT EXPOSE for selection** | The LLM must not choose factors (rule 5); factors appear only inside a server-computed result |
| `usage_tracking` | **EXTEND** | Has `ai_files_processed`, `reports_generated`, but **no** AI-interaction/query counter |
| `billing_commercial_config` | **REUSE (data, not schema)** | Versioned key/value rule set — an AI allowance is a new `config_key`, not a new table |
| `billing_plans`, `billing_credit_ledger` | **DEFER** | Whether Ask consumes credits is a PO decision (§21.9) |
| `organizations`, membership tables, `staff_profiles`, `consultant_clients` | **REUSE as authorization inputs** | They are the scope sources and are never duplicated into the Ask domain |

### 8.2 Why `conversations`/`messages` must not be extended for Ask CarbonTally

The brief's strong presumption is correct, and the repository proves it rather than
asserting it:

1. **Semantic mismatch is total.** `messages.content` is a human utterance between
   `sender_id` and `receiver_id`. An Ask turn has **one human** and **one system
   actor**, plus tool calls, references, provider attribution, and a status vocabulary
   that `messages` has no column for. There is no `actor_type` column.
2. **Observable cross-contamination.** Because `list_conversations_for_org()` filters on
   `organization_id` alone, an Ask conversation with a non-NULL `organization_id`
   **would surface in the customer's human messaging list**. Adding a kind filter to
   every human query would be an unbudgeted, cross-cutting change to a **frozen**
   capability (D19 §16 / N1) — exactly what AGENTS.md §71 forbids as a side-effect of a
   new feature.
3. **Realtime and UI semantics would leak.** `postgres_changes` subscriptions and the
   `components/chat/*` primitives encode human expectations (read receipts, typing,
   participants). Reusing the tables invites reusing those semantics.
4. **The Phase 5 precedent cuts against reuse here, not for it.** Entity threads were
   accepted as a *kind* precisely because they remain **human↔human** conversations
   between PE staff and CarbonTally. Ask CarbonTally is **human→machine** — a different
   relational shape (§E).
5. **Message retention is a PO decision.** Human messages can be soft-deleted
   (`is_deleted`, `deleted_at`). Whether Ask conversations are deletable is explicitly
   undecided (§21.2–21.3). Sharing a table would couple the two retention regimes — and
   would place AI audit content under a schema that permits user-level mutations,
   contradicting the stronger integrity expectation for AI interaction records (§13).

**Verdict:** `NEW BUILD` for the Ask conversation domain; `REUSE` for identity,
authorization, provider client, audit ledger, config, and referenced artefacts.

### 8.3 What is reusable verbatim

| Component | Reuse form |
|---|---|
| `LLMClient` + `LLMTransport` + `AIExtractionFailedError` | Instantiate per call; inject a fake transport in tests (existing convention) |
| `ai_runtime.provider_label()` / `configured_ai_attribution()` | Call at interaction time; persist the returned facts |
| `_authorize_org_actor` shape (3-branch org/consultant/staff + explicit PE denial) | Reproduce as the Ask access resolver (shared helper only if extractable without changing messaging behaviour — AGENTS.md §71 smallest change) |
| `AuditRepository.record()` | One reference-level event per interaction |
| `billing_commercial_config` versioned rules | Add an AI allowance `config_key` — decision later |
| `usage_tracking` counter pattern | Extend with an AI-interaction counter — decision later |
| `/api/v2/admin/audit` filters + `require_admin()` | Investigate existing interaction records; no new console required initially |
| `components/chat/*` presentation pieces | Reuse only pure presentation components, after the §23 R-6 check |
| Repository/domain/API layering (`data/` ↔ `domain/` ↔ `api/`) | Mandatory convention for the new domain |

---

## 9. Proposed conceptual architecture

### 9.1 The flow

```text
User (authenticated session)
  ↓
Ask CarbonTally UI (authenticated shell only)
  ↓
/api/v3/ask/* (FastAPI)
  │  1. verify identity            (get_current_user)
  │  2. resolve CURRENT scope      (org member | ACTIVE consultant grant | capability-gated staff)
  │  3. persist the user turn      (ask_conversations / ask_messages)
  │  4. classify intent            (deterministic first; model only to disambiguate)
  │  5. select tools               (persona registry — allowlist)
  │  6. execute tools              (server-side, caller identity, same API/RLS path)
  │  7. persist tool provenance    (ask_interactions + audit_trail reference event)
  │  8. build bounded context      (system + minimised history + structured results)
  │  9. call LLM for NARRATION     (LLMClient.complete — outside the authz boundary)
  │ 10. grounding check            (answer must be traceable to tool results)
  │ 11. persist the answer + status
  ↓
Answer + references (source chunk / report / snapshot / evidence)
```

### 9.2 The separation of powers (the core design principle)

| Concern | Owner | Never the LLM |
|---|---|---|
| Who the user is | backend session | ✔ |
| What the user may see | backend authorization + RLS | ✔ |
| Which data answers the question | deterministic tool selection + tool execution | ✔ |
| The authoritative number | tool result (calculation snapshot / report) | ✔ |
| Factor choice | existing factor matching / customer-factor precedence | ✔ |
| Evidence identity | existing evidence/audit records | ✔ |
| Wording of the explanation | LLM | — |

The LLM is a **narrator over server-computed facts**, never a reasoner over raw data.
This is the same posture `ai_document_extraction.py` already takes (AI output is
candidate; deterministic gates decide).

### 9.3 Two-stage pipeline (deterministic first)

The existing design already prescribes deterministic-first retrieval (AI-assistant arch.
§6.4 stages 1–2: normalization, expansion), and the public prototype is entirely
deterministic. Ask CarbonTally should therefore be:

- **Stage 1 — deterministic:** intent classification, tool selection, parameter
  derivation, tool execution, and the answer *facts*. Works with **no provider
  configured** (mirroring `configured_ai_extraction_engine()` returning `None`).
- **Stage 2 — optional LLM narration:** explains the structured result. Absent or
  failed, the deterministic result is still returned with a truthful status
  (`provider_unavailable`) — never a fabricated prose answer.

This makes the feature **degrade-safe**, matches the existing runtime gate, and means a
provider outage cannot produce a wrong number — only a less fluent sentence.

### 9.4 Where the LLM boundary sits

The LLM receives: the user's question, a bounded window of conversation text, the fixed
knowledge allowlist (product/FAQ explanation only), and the **structured tool results**.
The LLM never receives: credentials, signed URLs, raw document bytes, other tenants'
data, tool definitions it could invoke freely, or a database connection
(AI-assistant arch. §7.1/§7.4).

---

## 10. Conversation persistence model

### 10.1 Recommended conceptual model (`NEW BUILD`)

```text
ask_conversations
    ├── id
    ├── organization_id            NOT NULL  ← tenant scope key (RLS)
    ├── created_by                 (user id)
    ├── title                      (user-editable or derived — PO decision §21.10)
    ├── scope_kind                 ('customer' | 'consultant' | 'staff')
    ├── status                     ('active' | 'archived')   ← PO decision §21.10
    ├── last_message_at
    └── created_at / updated_at

ask_messages
    ├── id
    ├── conversation_id            FK → ask_conversations ON DELETE CASCADE
    ├── organization_id            NOT NULL  ← denormalised for RLS (see §17.3)
    ├── actor_type                 ('user' | 'assistant' | 'system')
    ├── actor_id                   (nullable — NULL for assistant)
    ├── content                    (user text, or assistant narrative)
    ├── status                     (see §21 vocabulary)
    ├── seq                        (ordering within the conversation)
    └── created_at

ask_interactions                   ← one row per assistant turn (the AI audit record)
    ├── id
    ├── conversation_id            FK
    ├── message_id                 FK → ask_messages (the assistant message)
    ├── organization_id            NOT NULL  ← RLS
    ├── actor_id / actor_type      (who asked)
    ├── intent                     (deterministic classification)
    ├── tool_calls                 JSONB (tool name, args, status, latency, result refs)
    ├── provider / model / model_version
    ├── tokens_used / cost         (nullable until LLMClient surfaces usage, §4.1)
    ├── answer_status              (§21 vocabulary — NOT the audit OUTCOMES vocabulary)
    ├── result_hash / references   (stable references, not duplicated datasets)
    └── created_at
```

**This is a proposal only.** It must not be treated as ratified; the repository evidence,
not this sketch, determines the final shape. The three-way split follows the brief's §7
mandate to separate **conversation history** from **AI interaction auditability**, and is
the minimum that satisfies both without duplication.

### 10.2 Why three structures and not one

| Requirement | Fails if merged into one row/table |
|---|---|
| User can delete/rename a conversation (UX) | Deleting the row would delete the AI audit record (§13 forbids that) |
| AI audit must survive conversation deletion | Requires the audit record to be addressable and separately governed |
| One assistant turn may involve several tool calls | Needs a list/JSONB, not a single column |
| Retention policies differ (§15) | Separate structures let conversation and audit retention be configured independently |
| RLS predicates differ | Messages need org scope; interactions may need a narrower read audience (§19) |

### 10.3 Ownership vs visibility

**Recommendation (not a decision).** Model *ownership* (`created_by`) and *visibility*
separately, because they are different questions:

- Ownership: the creator — always retained, even if visibility widens later.
- Visibility: **default private to the creator**, with these consequences:
  - No silent org-wide exposure of one member's questions.
  - Consultant conversations stay private to the consultant who asked (a consultant
    asking about Client A must not have that surfaced to Client A's Owner without an
    explicit decision).
  - A future "share with my organisation" becomes an **additive** change rather than a
    retraction of something already exposed.

This is a **PO DECISION REQUIRED** (§19.3, §21.1). The recommendation is recorded because
the brief asks for a recommendation rather than silence — and because default-private is
the only option that cannot leak data if the decision is delayed.

### 10.4 What must NOT be stored in the conversation domain

- API keys, tokens, signed URLs, or storage paths.
- Raw document bytes or full extracted document text (matches
  `ai_document_extraction.py`: *"No credentials or raw document contents are logged or
  persisted"*).
- Duplicated authoritative datasets (store the reference, not the payload — §13).
- Cross-tenant data in any form.
- Authorization grants or cached permission results (§7.3 invariant 4).

---

## 11. AI interaction / audit model

### 11.1 The three layers (the mandatory distinction, brief §7)

| Layer | Purpose | Lifecycle | Structure |
|---|---|---|---|
| **Conversation history** | User context, continuity, follow-ups, CX | Normal UX lifecycle (may be renamed/archived/deleted — PO decision) | `ask_messages` |
| **AI interaction record** | Reconstruct what CarbonTally did: intent, tools, references, provider, status | Retained under an audit-style policy; not user-deletable | `ask_interactions` |
| **Canonical audit event** | Evidence that an interaction occurred, in the platform's existing ledger | Append-only, immutable for every role | `audit_trail` (+ `metadata` taxonomy) |

### 11.2 Recommended minimum defensible field set

For the **AI interaction record** — the union of the brief's §6 minimum and repository
constraints:

| Field | Rationale | Source |
|---|---|---|
| `conversation_id`, `message_id` | Reconstruct the thread position | Ask domain |
| `actor_id`, `actor_type` | Who asked | Session |
| `organization_id` | Tenant scoping + RLS + audit `metadata->>'organization_id'` | Session scope (§7) |
| `created_at` | Timing | Server clock |
| `intent` | Reproducibility without the model | Deterministic classifier |
| `tool_name` (×N), minimised `tool_args`, `tool_status`, `latency_ms` | Prove which controlled tools ran and whether they succeeded | Tool registry |
| `reference_kind`, `reference_id` | The authoritative artefact used (report version, calculation snapshot, evidence id) | Tool result |
| `result_hash` | Integrity: prove the answer described *this* result | Hash of the structured tool result |
| `provider`, `model`, `model_version` | Truthful AI attribution | `configured_ai_attribution()` |
| `tokens_used`, `cost` | Usage accounting (§16) | Requires the `LLMClient` EXTEND |
| `answer_status` | Explicit outcome (§21 vocabulary) | Answer lifecycle |
| `grounding` | Whether the narrative was traceable to tool results | Grounding check |
| `fallback_reason` | Why a fallback/refusal occurred (quality + security monitoring) | Pipeline |

**Explicitly not required:** the full provider prompt, the full tool payload, and any
document content. Storing them creates a second copy of sensitive data with no additional
evidentiary value beyond what `result_hash` + `reference_id` already provide.

**Subject to data-minimisation decision (§15.4):** whether the raw question text is
stored in the interaction record at all, or only a hash plus the conversation FK.

### 11.3 The canonical audit event (one per interaction)

Written through the **existing** `AuditRepository.record()` — no second audit system
(AI-assistant arch. §10.2 asks for logging; Phase 7 supplies the durable, immutable
ledger). Shape:

| `audit_trail` column | Value for an Ask interaction |
|---|---|
| `action_type` | A new, explicit verb (e.g. `ask:query`) — classified by the existing prefix mechanism |
| `table_name` | `ask_interactions` |
| `record_id` | the interaction id (satisfies `record_id UUID NOT NULL`) |
| `performed_by` | the asking user's UUID (or the machine marker for a system-initiated run) |
| `metadata` | `{category, origin, outcome, organization_id, conversation_id, actor_type, tool_names[], reference_kinds[]}` |

**This is where the Phase 7 taxonomy gap bites (§6.3).** Two options — **decision
required**:

- **Option A (recommended):** add an `AI_INTERACTION`/`assistant` value to `CATEGORIES`
  and map `ask:*` verbs to it. This is additive to a documented *additive* vocabulary
  (*"additive; no schema change"*) and requires no migration. `OUTCOMES` stays
  `success`/`failure`; the finer `answer_status` lives on `ask_interactions`.
- **Option B:** leave `CATEGORIES` untouched; store the Ask category only on
  `ask_interactions`. Audit-console filtering then needs a join rather than a
  `metadata` filter.

**Do not** widen `OUTCOMES`. **Do not** record `no_data` as `failure`.

### 11.4 Why the interaction record must exist separately from `audit_trail`

1. **Immutability cuts both ways.** `audit_trail` cannot be updated or deleted by any
   role, and retention/purge requires deliberately dropping the Phase 7 trigger (§6.2).
   A conversation-linked provenance record that may need retention control or correction
   must not live there.
2. **Payload shape.** `audit_trail` has `old_data`/`new_data`/`changes` — a *diff* shape.
   An AI interaction is not a record mutation; forcing tool calls into a `changes` JSONB
   would be a semantic misrepresentation.
3. **Query patterns.** "What did the assistant do in this conversation?" is a
   `conversation_id` scan over interactions; the ledger should stay the *cross-domain*
   timeline.

**Both are written.** The ledger gives platform-wide, tamper-evident evidence that the
interaction happened; the interaction record gives structured, conversation-scoped
detail. Neither substitutes for the authoritative calculation/report records.

---

## 12. Context-building strategy

### 12.1 Do not send the whole conversation

The brief and the existing design agree: context must be **bounded**
(existing design §9: *"Bounded rolling context (last N turns)"*). The
`LLMClient` already enforces `max_tokens`; `ai_document_extraction` bounds prompt
characters via `DEFAULT_MAX_TEXT_CHARS = 20_000`.

### 12.2 Recommended composition (in priority order)

| Slot | Content | Volatility |
|---|---|---|
| 1. System prompt | Immutable product framing, persona, safety and refusal rules, output format | Fixed |
| 2. Authoritative scope | Scope the server resolved (org, active client, persona) — **injected, never derived from chat text** | Per request |
| 3. Fixed public knowledge | The curated allowlist for "how CarbonTally works" (existing design §6.1–6.2) | Slowly changing |
| 4. Current tool results | **Structured results** for this turn — the only numeric source | Per request |
| 5. Bounded recent history | Last *N* user/assistant turns, verbatim, length-capped | Rolling |
| 6. Conversation summary | Compaction of older turns (if adopted) | Regenerated |

### 12.3 Recommended: rolling summary + recent window (DEFER of the summary itself)

- **Phase 1 of Ask context:** bounded recent window only. Simple, auditable, no extra
  model calls.
- **Later:** add a rolling summary row per conversation, regenerated deterministically-
  triggered (e.g. after M turns), stored as a system/derived message. It is
  **derived data** and must never be presented as authoritative. This is a **PO
  decision** (§21.11).

### 12.4 The stale-context invariant (the worked example in the brief)

> Previous answer: *"Scope 2 was 184.6 tCO₂e."* Later, the underlying report or
> calculation is corrected. New question: *"Why was Scope 2 184.6?"*

**Required behaviour:**

1. The pipeline resolves the question to a **tool call** against current authoritative
   data — it does not answer from conversation text.
2. The tool returns the **current** value (e.g. 171.2 tCO₂e) plus its reference.
3. The assistant must **state the discrepancy** rather than silently repeating the old
   number: the previous 184.6 figure is historical conversational output and must be
   identified as such.
4. The interaction record stores both the historical context used and the current
   reference, so the discrepancy is explainable in evidence.

**Invariant:** *historical conversation context may help interpret a question, but it
must never override current authoritative CarbonTally data.*

### 12.5 Conflicting historical answers

If two stored answers disagree, neither is authoritative. Resolution is **always** via a
fresh tool call against current data. The assistant must not arbitrate between its own
past answers.

### 12.6 Data-period and version references

Questions of the form "in 2025", "last quarter", "this report", "the previous version"
must resolve to explicit, server-derived identifiers (`reporting_year`, `report_id`,
`report_version_id`, date range) — not to free-text inference by the model. Where the
period is ambiguous, the assistant asks for clarification rather than guessing
(`needs_clarification`, §21).

---

## 13. Provenance strategy

### 13.1 The required chain

```text
User question
   ↓  (server-derived)
Intent
   ↓  (allowlist registry)
Tool
   ↓  (caller identity, server-side)
Authorized parameters
   ↓
Authoritative result  ← calculation snapshot / report version / evidence id
   ↓
Reference(s) + result_hash
   ↓
LLM response (narration)
```

### 13.2 Reference, do not duplicate

| Question | Answer for Ask CarbonTally |
|---|---|
| Store the emissions value in the conversation? | **Yes, as the rendered answer text** (it is conversational output) — but the *authority* is the reference |
| Store the whole calculation snapshot? | **No.** Store `(kind='calculation_snapshot', id=<uuid>)` + `result_hash`. `backend/data/reporting.py::audit_package()` already fetches snapshots with factor provenance by id |
| Store the report PDF? | **No.** Store the report/version reference; the UI links to the existing download path (subject to existing authorization) |
| Store the factor? | **No.** Factors appear inside the snapshot's provenance (`factor_id`, `factor_source`, `factor_set`) — never chosen or stored by the assistant |

### 13.3 What the references enable

| Business question (brief §20) | Required references |
|---|---|
| "What was our total CO₂e in 2025?" | `reporting_year` + snapshots (or report version) for that year |
| "Why did Scope 3 increase?" | Two snapshot sets (prior vs current period) + factor provenance |
| "Which facility contributed most?" | Per-snapshot facility/location linkage as exposed by the existing data model |
| "Show me the evidence behind that number." | `calculation_snapshot.id` → evidence/provenance references |
| "Compare this report with the previous version." | `report_id` + two `report_version` ids |
| "What changed after we corrected the supplier data?" | Audit-trail activity window + affected snapshot references |

### 13.4 Integrity

`result_hash` (stable hash of the structured tool result) lets a later investigation
prove the answer described a specific result set. This follows the existing precedent:
`calculation_snapshots.content_hash` and the `integrity` block (sha256) in
`audit_package()`. **Use the platform's existing hashing convention; do not invent a
second one.**

### 13.5 The hard boundary

> **An LLM-generated sentence is never a provenance record.**

If a user's evidence question cannot be answered from an authoritative reference, the
correct answer is an explicit no-data/insufficient-data response — never a plausible
reconstruction (§21).

---

## 14. Security / threat model

### 14.1 The six threats, their controls, and the required negative tests

| Threat | Control (design) | Negative test |
|---|---|---|
| **Prompt injection** (malicious document or user message) | Document text is untrusted data and never enters the system prompt; retrieved snippets are quoted, length-limited and delimited; the system prompt is immutable by user/document; tool calls are validated against the registry (no free-form SQL, no raw URL fetch); output filters remove secrets/internal paths (AI-assistant arch. §7.4) | A document containing "ignore previous instructions / act as admin / reveal secrets" produces no privilege change and no secret disclosure |
| **Cross-tenant leakage** | Every read and every tool call re-authorises against **current** scope (§7.3); retrieval is scoped *before* the model sees anything (§22); no cross-org reference resolution | Org A user cannot obtain Org B data via paraphrase, history replay, a stored reference, or injected instructions |
| **Conversation poisoning** | Stored answers are conversational output, never facts (§2.2); every numeric answer requires a fresh tool result (§12.4–12.5) | A manipulated stored answer cannot cause a later answer to assert a wrong emissions value |
| **Tool abuse** | Read-only tools initially; allowlist per persona (§19); server-side execution with the caller's identity; typed parameters; bounded result sizes; rate limits (AI-assistant arch. §7.2/§7.3, brief §16) | Unknown tool name, out-of-scope tool for the persona, or state-changing intent is refused |
| **Sensitive-data leakage to the provider** | Prompt minimisation (§15.4); no credentials/signed URLs/raw document bytes; provider/model attribution recorded; configurable redaction | An inspection of the composed prompt shows no secrets, no signed URLs, no other-tenant identifiers |
| **Model hallucination** | Grounding check — an answer whose claims cannot be traced to tool results becomes `ungrounded` and is converted to a fallback; the LLM never calculates, chooses factors, or invents evidence (rules 4–6) | A question with no supporting data returns an explicit no-data response, never an invented number |

### 14.2 Two additional threats specific to *persistence*

**P-1. Historical access after revocation.** Persisting conversations creates a new way
to attempt stale access. Control: re-authorisation on every read (§7.3, §7.4). Test:
revoke a consultant grant, then attempt to open an existing conversation — must be denied.

**P-2. Deletion as an audit-evasion route.** If a user can delete a conversation, could
they destroy evidence of a misuse? Control: the AI interaction record and the canonical
audit event are **not** removed by conversation deletion (§11.1, §13, §21.3). Test: delete
a conversation; verify the interaction record and audit event remain and still resolve
references. **This is the single most important consequence of choosing the three-layer
model.**

### 14.3 Audit falsification

> AI conversation records must never be treated as a substitute for the authoritative
> audit trail.

Controls: the canonical ledger remains the cross-domain evidence surface (§11.3); the
interaction record is a provenance *reference* holder; the delivered audit/evidence
package (`audit_package()`) **already excludes AI conversation content** and must continue
to do so unless a PO decision explicitly changes its contents (§15.5, §21.8). The
package's own contract is explicit: `not_assurance: True` plus
`AUDIT_NOT_ASSURANCE_NOTICE`.

### 14.4 Rules 1–19 compliance matrix

| Brief rule | Design disposition |
|---|---|
| 1. Discovery is not implementation | This document changes no code/schema/RLS/route/UI |
| 2. Conversation history is not authoritative data | §2.2, §12.4, §13.5 |
| 3. LLM is never an authorization boundary | §9.2, §7.3 |
| 4. LLM must not calculate carbon | §9.2 (facts come from tools; deterministic calculation engine untouched) |
| 5. LLM must not choose factors | §8.1 (`emission_factors` not exposed for selection) |
| 6. LLM must not invent evidence | §14.1 grounding check; §13.5 |
| 7. LLM must not modify authoritative records | Read-only tools initially (existing design §7.3 point 6) |
| 8. History must not bypass current authorization | §7.3, §7.4, §14.2 P-1 |
| 9. Separate from Human↔Human messaging | §5, §8.2, §E |
| 10. No second LLM/provider abstraction | §4.1, §8.3 |
| 11. No unrestricted RAG/DB access | §22 |
| 12. Controlled read-only tools initially | §19, §22 |
| 13. Traceable to CarbonTally data | §13.1–13.4 |
| 14. No-data ≠ zero | §21 (answer lifecycle) — `no_data` is a distinct status |
| 15/16. No audit/assurance/certification or legal claims | §15.6, §21 |
| 17. Preserve unrelated worktree | §3, §J |
| 18. Do not push | §J |
| 19. Do not authorize implementation | §25, §J |

---

## 15. Privacy / retention considerations

No legal-compliance claim is made anywhere in this section. Every item is labelled
**FACT** (repository), **REC** (architecture recommendation), **PO** (product decision),
or **LEGAL**.

### 15.1 Conversation retention
- **FACT:** no Ask retention exists because no Ask domain exists. Retention is a
  configurable platform concern (AGENTS.md §42, frozen decision N3): *configurable,
  server-side, managed through the Settings/Admin control plane*, and *"must NOT weaken
  auditability, evidence, regulatory traceability"*.
- **PO:** the conversation retention window. **Do not invent a duration** (AGENTS.md §42).
- **REC:** express it as a `billing_commercial_config`-style versioned rule (or the N3
  retention mechanism) rather than a hard-coded constant.

### 15.2 Deletion
- **PO:** whether a user may delete a conversation; whether deletion is soft or hard;
  whether an admin can.
- **REC:** conversation deletion must never delete the interaction record or the
  canonical audit event (§14.2 P-2).

### 15.3 Customer export
- **PO:** whether a customer can export conversations (§18).

### 15.4 PII / sensitive business information / minimisation
- **FACT:** the existing AI extraction module states *"No credentials or raw document
  contents are logged or persisted."* That is the platform's established
  minimisation posture.
- **REC (applying it to Ask):** do not persist the full provider prompt; do not persist
  tool payloads; store references and a `result_hash`; consider storing a hash of the
  question in the interaction record with the text held only in the conversation row;
  redact identifiers from tool arguments before persistence.
- **LEGAL / PO:** whether user questions may contain personal data, and what the
  minimisation/redaction policy must be.

### 15.5 Prompt contents, tool arguments, external provider transmission
- **FACT:** the platform has **no established provider**; the design is explicitly
  provider-neutral and *"The repository has not established a specific paid AI
  provider"* (AI-assistant arch. §8). No provider retention/training policy is
  recorded anywhere in the repository.
- **PO:** provider selection, provider data-retention stance, provider training/use
  stance, DPA/subprocessor position, regional/data-residency requirements, whether
  customers are told that data is sent to a provider, and whether an opt-out is offered.
- **PO/LEGAL:** all of the above.
- **FACT:** `CARBONTALLY_AI_API_KEY` is environment-only, never stored in the database,
  never logged, never exposed to the frontend. Any Ask provider integration must
  preserve this exactly.

### 15.6 No legal claims
- **LEGAL:** nothing in this document asserts GDPR/UK GDPR/EU compliance, lawful basis,
  or adequacy. Whether Ask CarbonTally may transmit customer business data to a
  provider is a **legal + PO** determination.

### 15.7 Retention mechanics warning (concrete)
- **FACT:** `audit_trail` is append-only for every role (§6.2), and its own comment
  requires *"a future authorised retention/purge process must deliberately drop this
  trigger first (documented, controlled)"*. Therefore: **any Ask retention design must
  decide separately** how audit-level Ask records age out — and must not assume the
  existing purge mechanisms cover them. Flagged as a prerequisite (§22, §23).

---

## 16. Billing / allowance considerations

### 16.1 What exists

| Mechanism | Repository fact |
|---|---|
| `usage_tracking` | Per-org, per-month counters: `ai_files_processed`, `batch_files_uploaded`, `manual_pages_extracted`, `reports_generated`, `total_storage_bytes`; `UNIQUE(organization_id, usage_month)`. **No AI-interaction/query counter.** |
| `billing_commercial_config` | **Versioned key/value** commercial rules (`config_key`, `config_value JSONB`, `version`, `effective_from`/`effective_to`, `reason`, `created_by`/`updated_by`, `UNIQUE(config_key, version)`); current row is `effective_to IS NULL`. Documented keys: `default_billing_mode`, `credit_rules`, `structured_data_bands`, `storage`, `assisted_pricing`, `credit_policy`, `standard_allowance`. **Deny-by-default RLS — trusted billing API only.** |
| `billing_plans`, `billing_credit_ledger` | Exist; used by the billing service. |
| `ai_content_history` | Dormant; already has `tokens_used`, `cost` columns. |
| `LLMClient` | **Returns no usage data** (§4.1 gap 3). |

### 16.2 Design disposition

| Question | Disposition |
|---|---|
| New billing architecture required? | **No.** `billing_commercial_config` is explicitly a *configurable commercial capability* mechanism. |
| How is an AI allowance expressed? | **EXTEND (data):** a new `config_key` (e.g. `ai_query_allowance`) with a versioned `config_value`. **PO** decision on the value/limits. |
| How is consumption counted? | **EXTEND:** a per-org counter on `usage_tracking` (mirroring `ai_files_processed`), **or** derived by counting `ask_interactions` per month. The derived option avoids a schema change. |
| How is cost per interaction captured? | Requires the **`LLMClient` EXTEND** to surface usage (tokens/cost). Until then, leave `tokens_used`/`cost` NULL rather than fabricating values. |
| Should Ask consume credits? | **DEFER — PO** (§21.9). Do not assume the commercial model. |
| Rate limiting | Needed regardless of billing (§14.1) — a per-user/per-org limit, not only a commercial quota. |

### 16.3 Explicit non-assumptions

- No credit price, quota, or plan mapping is proposed.
- No change to `billing_plans`/`billing_credit_ledger` is proposed.
- The interaction record's `tokens_used`/`cost` must remain **NULL** until truthful
  usage is available — consistent with `ai_runtime`'s rule that attribution is never
  fabricated.

---

## 17. RLS and authorization design

### 17.1 The Phase 8 warning, restated concretely

Phase 8 established that report-table RLS policy coverage is incomplete: `rc2_rls.sql` §3
builds tenant policies dynamically **only for tables carrying `organization_id`**, so
`report_versions` and `report_comments` (which lack the column) have **no policy** and are
deny-all to `authenticated` — the API works because the backend role bypasses RLS (not
`FORCE`d). **Therefore no existing RLS posture may be assumed to protect a new domain.**

### 17.2 Recommendation: `organization_id NOT NULL` on every Ask table

Every Ask table — `ask_conversations`, `ask_messages`, `ask_interactions` — should carry
`organization_id UUID NOT NULL REFERENCES organizations(id)`. Consequences:

1. The `rc2_rls.sql` §3 dynamic loop **automatically generates a tenant policy** for each
   new table. This is the single highest-leverage decision for defence in depth.
2. The predicate stays consistent with the existing platform-wide pattern.
3. Denormalising `organization_id` onto `ask_messages`/`ask_interactions` (rather than
   joining through the conversation) keeps RLS predicates simple and index-friendly, and
   makes the org scope of every row verifiable without a join.

### 17.3 User-level ownership on top of org scope

`organization_id` alone is insufficient for the recommended default-private visibility
(§10.3). The pattern would be an **additional** predicate requiring the caller to be the
conversation's `created_by` — following the shape of the entity-messaging policies, which
combine a scope predicate with a membership helper (`is_active_pe_member`).
**PO decision required** (§21.1), because it determines the policy shape.

### 17.4 How server-side guards interact with RLS

| Layer | Ask CarbonTally behaviour |
|---|---|
| API authorization | Always enforced — `_authorize_org_actor`-equivalent on **every** route (§7.3) |
| RLS | Defence in depth — a second, independent denial |
| Backend role | Expected to bypass RLS for writes, exactly as messaging does (§5.4). This is the documented existing posture; where elevated access is relied upon, application-level authorization must remain explicit and documented (AGENTS.md §67) |

### 17.5 Prerequisites before any Ask implementation

1. Decide the visibility model (§21.1) so the policy is written once, correctly.
2. Create the Ask tables' policies **in the same migration that creates the tables** —
   not relying on the dynamic loop alone, given §17.1.
3. Apply the same hardening posture recommended for the report tables (the open **A-RLS**
   item from the Phase 8 decision package). **Ask RLS must not repeat A-RLS.**
4. Verify `authenticated` denial explicitly (AGENTS.md §67: same-tenant allow,
   cross-tenant deny, role restrictions) with both ALLOW and DENY cases (AGENTS.md §72).

---

## 18. Conversation export

### 18.1 The three candidate treatments

| Option | Content | Verdict |
|---|---|---|
| **Ordinary UX export** | The user's own conversation text | **REC** — simplest; scoped by the same authorization as viewing the conversation |
| **Part of the audit/evidence package** | Conversation text + interactions inside `audit_package()` | **NOT RECOMMENDED** as a default — see §18.2 |
| **Separate export** | Conversation + references + interaction metadata, generated on request | **REC for the AI-audit view** if a PO wants customer-facing AI transparency |

### 18.2 Why conversation history should NOT be added to the audit/evidence package by default

- **FACT:** `audit_package()` is contractually *"NOT an assurance opinion"*, carries
  `not_assurance: True` and `AUDIT_NOT_ASSURANCE_NOTICE`, and contains CarbonTally-generated
  **evidence** (snapshots with factor provenance + hashes, timeline, readiness).
- Adding conversational content would mix **narrative output** into an **evidence**
  artefact — precisely the confusion rule 2 forbids, and it risks a reader treating prose
  as evidence.
- **PO decision required** (§21.8).

### 18.3 Recommendation

Keep **three** distinct export surfaces, each with one job:

1. **Conversation export (UX):** the user's own thread.
2. **Audit/evidence package (unchanged):** authoritative evidence only.
3. **AI interaction export (optional, later):** interaction records + references, for a
   customer or internal investigation that specifically concerns AI behaviour.

---

## 19. Persona / access model

### 19.1 Public (unauthenticated)

- **REC: no persistence, no Ask domain.** The existing `AssistantWidget` remains
  deterministic, local, backend-free. Nothing in this design changes it.
- **PO** if persistence of public conversations is ever wanted — it should not be assumed.

### 19.2 Customer

- Scope: their own organisation; role-gated (Owner/Admin/Member/Viewer).
- **REC:** Viewer = read-only Ask (may ask, may read own conversations). Member/Admin/Owner
  as their existing capabilities allow. No Ask tool may return data the role cannot already
  see in the UI (AI-assistant arch. §5.2; §7.3 point 4).
- **PO:** whether Owner/Admin can read other members' Ask conversations.

### 19.3 Same organisation, different user

- **PO DECISION REQUIRED** (brief §10). **REC: private to creator by default** (§10.3).
- Must not be decided silently, and the decision must be reflected in the RLS predicate
  (§17.3).

### 19.4 Consultant

- **FACT:** consultants are first-class operators with an ACTIVE grant model
  (`ensure_consultant_org_access`); consultant tools are *"always scoped to the active
  client organisation"* (AI-assistant arch. §5.3).
- **REC:** a consultant sees **their own** Ask conversations, bound to the client org at
  creation; access to each is re-authorised against the **current ACTIVE grant** (§7.4).
- **PO:** whether consultants may see **customer members'** Ask conversations about the
  same client org. **REC: no** — operating a client does not entitle a consultant to read
  that client's users' private questions.
- **Security implication:** grant revocation must instantly remove conversation access.

### 19.5 Staff (CarbonTally internal)

- **FACT:** internal staff are those with `staff_profiles.entity_id IS NULL`; capabilities
  come from the authoritative `staff_roles` catalog via `ensure_staff_permission`.
- **REC:** no staff role reads customer Ask conversations by default. Support access, if
  granted, requires an **explicit, new capability** — not `is_staff`, not
  `can_manage_staff` (§7.5).
- **PO:** whether such a capability exists and which role holds it.

### 19.6 PE (Processing Entity)

- **FACT:** `backend/api/v3_pe.py` (662 lines, 21 routes) contains **zero `report`
  references** — PE has no report route, scope, or UI. The PE document boundary is a
  ratified PO decision, and the assistant *"must not add a new path that bypasses this"*
  (AI-assistant arch. §7.5). Messaging already excludes PE: *"the D18 boundary is
  absolute."*
- **REC: PE Ask CarbonTally = NO in this phase.** No PE Ask domain, no PE conversation
  access, no PE tool that returns customer documents or report content. PE portfolio
  reporting, if wanted, is a **separate entity-scoped surface** — a distinct initiative.
- **PO:** confirm explicitly (§21.6); do not assume.

### 19.7 Auditor / Assurance Reviewer

- **FACT:** does not exist (§7.6).
- **REC:** no access through this task; the consultant active-grant pattern is the future
  analogue if ratified.
- **PO:** future scope only.

### 19.8 Summary matrix

| Persona | Own Ask conversations | Others' Ask (same org) | Client / other-org Ask | Tools |
|---|---|---|---|---|
| Public | n/a (not persisted) | n/a | n/a | knowledge only |
| Customer Viewer | ✔ read + ask | ✖ (REC) | ✖ | read-only, own scope |
| Customer Member/Admin/Owner | ✔ | **PO** | ✖ | per existing capability |
| Consultant | ✔ (bound to client org) | ✖ | only via ACTIVE grant; own conversations | consultant-scoped, active client only |
| Staff | ✔ (if the internal assistant is ratified) | **PO** | **PO** + explicit capability | staff-scoped |
| PE | **✖ (REC — no PE Ask this phase)** | ✖ | ✖ | — |
| Auditor | ✖ (not implemented) | ✖ | ✖ | — |

---

## 20. Decision matrix

### 20.1 Component classification (brief §23 vocabulary)

| # | Component | Classification | Basis |
|---|---|---|---|
| 1 | LLM provider client (`LLMClient`, transport, error contract) | **REUSE** | §4.1 |
| 2 | Runtime attribution (`provider_label`, `configured_ai_attribution`) | **REUSE** | §4.2 |
| 3 | AI boundary conventions (candidate-only, never-false-success, no raw content) | **REUSE (as rules)** | §4.3 |
| 4 | `LLMClient` multi-turn / usage surfacing | **EXTEND** | §4.1 gaps 1 & 3 |
| 5 | Public assistant widget + knowledge | **REUSE (unchanged)** | §4.4 |
| 6 | Identity & session (`get_current_user`) | **REUSE** | §7.1 |
| 7 | Authorization guards (`ensure_org_access`, `ensure_consultant_org_access`, `ensure_staff_permission`) | **REUSE** | §7.1 |
| 8 | Access resolver shape from `_authorize_org_actor` | **REUSE (pattern)** / possible **REFACTOR** to share | §5.3 |
| 9 | `audit_trail` + `AuditRepository` | **REUSE** | §6.5 |
| 10 | Phase 7 audit taxonomy | **EXTEND (option A) or DEFER (option B)** | §11.3 |
| 11 | `audit_package()` | **REUSE unchanged** (no conversation content) | §18.2 |
| 12 | `ai_content_history` | **EXTEND or DEFER** (dormant) | §4.5 |
| 13 | `usage_tracking` | **EXTEND** (counter) or derive from interactions | §16.2 |
| 14 | `billing_commercial_config` | **REUSE (data)** | §16.2 |
| 15 | `billing_plans` / `billing_credit_ledger` | **DEFER — PO** | §16.2 |
| 16 | `conversations` / `messages` / `conversation_participants` / `typing_status` | **DO NOT REUSE** | §8.2 |
| 17 | `message_activity_log`, `conversation_activity_log`, `activity_logs` | **DO NOT REUSE** | §8.1, §6.6 |
| 18 | `components/chat/*` UI | **REUSE (presentation only, after R-6 check)** | §5.7, §23 |
| 19 | Ask conversation domain (`ask_conversations`, `ask_messages`) | **NEW BUILD** | §10 |
| 20 | Ask interaction/provenance record (`ask_interactions`) | **NEW BUILD** | §11 |
| 21 | Tool registry + tool implementations | **NEW BUILD** (design exists in AI-assistant arch. §7) | §8.3 |
| 22 | Persona knowledge allowlist | **EXTEND** (public allowlist exists) | §4.4 |
| 23 | Scoped retrieval (if adopted) | **DEFER** — must stay authorization-first | §22.5 |
| 24 | Ask RLS policies | **NEW BUILD (mandatory, same migration)** | §17 |
| 25 | Ask retention policy | **PO DECISION REQUIRED + then NEW BUILD** | §15.1, §15.7 |
| 26 | Ask UI (authenticated) | **NEW BUILD** | §4.6 |
| 27 | PE Ask domain | **DEFER (recommended: not this phase)** | §19.6 |
| 28 | Auditor Ask access | **DEFER (capability does not exist)** | §19.7 |
| 29 | Evidence that the answer matched the result (`result_hash`) | **NEW BUILD**, reusing the existing hashing convention | §13.4 |

### 20.2 Reuse-vs-build summary

| Disposition | Count | Components |
|---|---|---|
| REUSE | 9 | 1, 2, 3, 5, 6, 7, 9, 11, 14 (+18 conditional) |
| EXTEND | 6 | 4, 10, 12, 13, 22 (+24 if policies follow the dynamic loop) |
| NEW BUILD | 6 | 19, 20, 21, 26, 29 (+24) |
| REFACTOR | 0–1 | 8 (only if a shared resolver can be extracted without behaviour change) |
| DEFER | 6 | 15, 23, 27, 28 (+10 option B, +18 if the UI check fails) |
| DO NOT REUSE | 4 groups | 16, 17 |
| PO DECISION REQUIRED | — | §21 |

**Observation:** the design is overwhelmingly **reuse + extend**. Only two genuinely new
*business* structures are required (the conversation domain and the interaction record),
and both are small. This is the strongest available evidence that the PO decision can be
implemented without architectural disruption.

### 20.3 What "NEW BUILD" does *not* mean here

- It does **not** mean a new provider abstraction (rule 10).
- It does **not** mean a new audit system (rule 15 in spirit; `admin_audit.py`
  explicitly states the opposite).
- It does **not** mean a new authorization system (guards are reused).
- It does **not** mean a new billing system (§16).
- It does **not** mean a vector store or a new retrieval stack (§22.5).

---

## 21. Open PO decisions

### 21.0 AI answer lifecycle and status vocabulary (the "§21 vocabulary")

The pipeline must represent these outcomes as **distinct, explicit statuses** — they may
not be collapsed, and none may be rendered as zero or as success:

| Status | Meaning | Must not be confused with |
|---|---|---|
| `answered` | Grounded answer produced from tool results | — |
| `no_data` | The scope legitimately contains no such data | **zero** (rule 14) |
| `insufficient_data` | Data exists but is incomplete for the question | `no_data` |
| `unauthorized` | The caller is not authorised for the requested data | `no_data` — a denial is not an absence |
| `tool_failure` | A controlled tool failed | `no_data` |
| `provider_unavailable` | The LLM narration stage is unavailable; the deterministic result is still returned | failure of the whole interaction |
| `ungrounded` | Narration could not be traced to tool results → replaced by fallback | `answered` |
| `partial` | Part of the question could be answered | `answered` |
| `needs_clarification` | The question (or its period/scope) is ambiguous | `no_data` |
| `rate_limited` | Allowance/rate limit reached | a tool or provider failure |
| `refused` | Safety/policy refusal (injection, prohibited request) | any data outcome |

**Design consequences:** this vocabulary lives in the Ask domain
(`ask_interactions.answer_status`), **not** in the Phase 7 `OUTCOMES` pair (§6.3, §11.3).
`no_data` ≠ zero is enforced here and must be an explicit QA assertion (rule 14).

### 21.1 Conversation visibility (same org, different user)

- **Question:** private to creator / organisation-visible / explicitly shared /
  role-dependent?
- **Recommendation:** private to creator by default, with additive sharing later.
- **Blocks:** the RLS policy shape (§17.3), and therefore all I2 work.
- **Owner:** PO.

### 21.2 Conversation deletion

- **Question:** may a user delete a conversation? Soft or hard? May an admin?
- **Recommendation:** allow archiving (UX); deletion must never remove interaction or
  audit records.
- **Owner:** PO.

### 21.3 Retention

- **Question:** how long are conversations retained? Are interaction records retained
  differently? Do audit-level Ask records need a purge path given the append-only trigger
  (§15.7)?
- **Recommendation:** configurable (N3-style), never invented.
- **Owner:** PO (+ engineering design once decided).

### 21.4 Customer export

- **Question:** may a customer export conversation text, references, and interaction
  metadata?
- **Recommendation:** yes for the user's own conversation; AI interaction export later.
- **Owner:** PO.

### 21.5 Consultant access to customer conversations

- **Question:** may a consultant read a client's users' Ask conversations?
- **Recommendation:** no.
- **Owner:** PO (security impact: §19.4).

### 21.6 PE access (including whether PE Ask exists at all)

- **Question:** does any PE Ask domain or PE conversation access exist?
- **Recommendation:** no, this phase — preserves the D18 boundary absolutely.
- **Owner:** PO.

### 21.7 Auditor / assurance access

- **Question:** future scope only; the capability does not exist.
- **Recommendation:** defer entirely.
- **Owner:** PO.

### 21.8 AI interaction records in the Phase 7 audit/evidence package; conversation
history in an audit export

- **Question:** does `audit_package()` gain an AI section?
- **Recommendation:** no by default — it is an evidence artefact with a `not_assurance`
  contract (§18.2). A separate AI-interaction export is preferable.
- **Owner:** PO.

### 21.9 AI credit / allowance treatment

- **Question:** does asking consume credits? What allowance? Per-plan limits?
- **Recommendation:** express as a versioned `config_value`; do not assume the commercial
  model.
- **Owner:** PO.

### 21.10 Context retention / compaction policy

- **Question:** how many turns are sent? Is a rolling summary adopted, at what threshold,
  and is it user-visible?
- **Recommendation:** bounded recent window first; summary later.
- **Owner:** PO (thresholds become implementation decisions once the policy is set).

### 21.11 Rename / archive

- **Question:** may users rename and archive conversations?
- **Recommendation:** yes — both are low-risk UX affordances that aid continuity.
- **Owner:** PO.

### 21.12 Regeneration / edit semantics

- **Question:** may a user edit a question or regenerate an answer? What happens to the
  original interaction record?
- **Recommendation:** allow regeneration, but **never** overwrite an interaction record —
  a regeneration creates an additional interaction. Editing a user message must not
  silently rewrite history.
- **Owner:** PO.

### 21.13 AI provider selection and provider data stance

- **Question:** hosted vs self-hosted; provider retention; provider training/use;
  DPA/subprocessor; region/data residency; customer disclosure; opt-out.
- **Status:** **not established anywhere in the repository.** The design is explicitly
  provider-neutral (AI-assistant arch. §8).
- **Owner:** PO + LEGAL.

### 21.14 PII and question-content minimisation

- **Question:** may questions contain personal data? Is the raw question stored in the
  interaction record, or only a hash?
- **Recommendation:** hash in the interaction record; text in the conversation row only.
- **Owner:** PO + LEGAL.

### 21.15 Audit category for AI interactions (taxonomy option A vs B)

- **Question:** extend `CATEGORIES` with an AI value (option A) or keep the category only
  on `ask_interactions` (option B)?
- **Recommendation:** option A — additive, no migration, no change to `OUTCOMES`.
- **Owner:** PO / architecture.

### 21.16 Whether the authenticated assistant is ratified at all, and for which personas

- **Question:** `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` Phases 3–7 are **design-only
  and unratified**. This discovery assumes a customer-first scope.
- **Recommendation:** ratify the persona rollout explicitly rather than inheriting an
  unratified roadmap.
- **Owner:** PO.

### 21.17 Which authenticated surface gets Ask first

- **Question:** customer workspace, consultant workspace, or both?
- **Recommendation:** one persona first (customer), because its authorization path is
  simplest and its RLS story is cleanest.
- **Owner:** PO.

### 21.18 Decision summary table

| ID | Decision | Blocks | Recommendation |
|---|---|---|---|
| 21.1 | Conversation visibility | I2 (RLS) | Private to creator |
| 21.2 | Deletion | I1/I2 | Archive; never delete audit |
| 21.3 | Retention | I7 | Configurable (N3) |
| 21.4 | Customer export | I7 | Own conversation only |
| 21.5 | Consultant → customer conversations | I2/I3 | No |
| 21.6 | PE Ask | I1 scope | No (this phase) |
| 21.7 | Auditor Ask | I1 scope | Defer |
| 21.8 | AI records in audit package | I4/export | No |
| 21.9 | AI credits/allowance | I8 | Config-driven; defer value |
| 21.10 | Context/compaction | I5 | Window first, summary later |
| 21.11 | Rename/archive | I6 | Yes |
| 21.12 | Regeneration/edit | I1/I4 | Regenerate; never overwrite |
| 21.13 | Provider + data stance | I3/I8 | PO + LEGAL |
| 21.14 | PII minimisation | I1/I4 | Hash in interaction |
| 21.15 | Audit category A/B | I4 | Option A |
| 21.16 | Persona ratification | whole scope | Customer first |
| 21.17 | First surface | I6 | Customer workspace |

---

## 22. Implementation staging recommendation

**This task authorises none of these stages.** The sequence below is derived from
repository evidence and dependency order, not from the brief's illustrative example.

### 22.1 The recommended sequence

```text
D1  Architecture discovery                         ← THIS TASK (complete)
D2  PO ratification of this design + the §21 decisions
────────────────────────────────────────────────────── (no work may start above this line)
I1  Persistent conversation foundation
       migration: ask_conversations + ask_messages + RLS policies, together
       + repository + domain + API create/list/read, re-authorising on every read
       + one regression test asserting cross-tenant denial
I2  Authorization hardening + visibility model
       apply the 21.1 decision to the RLS predicate; ALLOW and DENY tests
I3  Controlled read-only tool interaction (customer scope)
       intent classification + registry + 2–3 tools (processing status, item summary,
       emissions result) + references; deterministic result path with no provider
I4  AI interaction record + audit integration
       ask_interactions write path; audit_trail reference event; taxonomy option A/B
I5  Context building (bounded window; summary deferred)
I6  UI (authenticated customer workspace; reuse presentation primitives only)
I7  Privacy / retention / export
I8  Billing/allowance integration (config-driven) + production hardening
─────
DEFER  Consultant workspace Ask  ·  Staff Ask  ·  PE Ask  ·  Auditor  ·  summary/compaction
DEFER  Scoped vector retrieval (only if I3–I5 prove insufficient)
```

### 22.2 Why this order and not the illustrative one

| Ordering decision | Why |
|---|---|
| RLS in the **same migration** as the tables (I1) | §17.1: the Phase 8 discovery found report tables whose policy coverage is incomplete. Creating Ask tables without policies would knowingly repeat **A-RLS**. |
| Authorization hardening (I2) separated from I1 | The visibility decision (21.1) determines the predicate. Building I1's policies before 21.1 is answered would guarantee a rewrite. |
| Tools (I3) before the LLM narration hardening | The deterministic result path **is** the product; narration is optional (§9.3). This also means I3 delivers value even with no provider configured. |
| Audit (I4) before context (I5) | Provenance is a prerequisite for trustworthy context: without references, history is just prose. |
| Retention/export (I7) **before** broad rollout | §15.7: the append-only audit trigger means retention needs a deliberate, documented design. Shipping conversations to customers before retention is decided creates an obligation the platform cannot yet honour. |
| Consultant/staff/PE Ask deferred | Each multiplies the authorization surface (§19). One persona first. |

### 22.3 Explicit gating conditions between stages

| Gate | Condition |
|---|---|
| D2 → I1 | PO ratifies the design **and** answers 21.1 (visibility), 21.2 (deletion), 21.6 (PE), 21.16 (persona) |
| I1 → I3 | Cross-tenant denial proven by test (ALLOW + DENY) |
| I3 → I4 | Every tool proven read-only and authorization-checked |
| I4 → I6 | An interaction record is written for every assistant turn, including failures |
| I6 → I7 | Export/retention design agreed (21.3, 21.4, 21.8) |
| Any personal data in prompts → I8/legal | 21.13 / 21.14 answered |

### 22.4 Test obligations (from existing repository QA conventions)

- **Permission matrix:** every tool × persona × role, asserting exact visibility.
- **Isolation:** Org A cannot reach Org B via paraphrase, history replay, stored
  reference, or injected instruction.
- **Injection:** a malicious document/message cannot escalate or disclose.
- **Revocation:** consultant grant revoked → conversation access denied (P-1).
- **Deletion:** conversation deleted → interaction record and audit event remain (P-2).
- **`no_data` ≠ zero:** an empty result renders as absence, never `0`.
- **Provider-down:** a deterministic answer is still produced with
  `provider_unavailable`.
- **Regression:** the existing `backend/tests/unit/api/test_v3_reports.py` suite must
  continue to pass (this work must not touch report behaviour).

### 22.5 Retrieval constraint (no unrestricted RAG)

If retrieval is adopted (definitively **deferred**), it must remain:

```text
Authorization
   ↓
Scoped retrieval
   ↓
Controlled data
   ↓
LLM
```

**Never:**

```text
LLM
   ↓
Unrestricted database/vector store
```

Concretely: retrieval operates **after** the caller's authorization has resolved a scope,
against an **explicitly allowlisted** corpus (public knowledge, the caller's own org
content where a policy permits), with persona allowlist filtering at rerank time (per
AI-assistant arch. §6.1/§6.4). The LLM never holds a database connection, a vector-store
credential, or an unscoped search primitive. Evidence provenance must survive retrieval
(each retrieved chunk keeps its source label, canonical URL/entity reference, and owning
doc).

### 22.6 Relationship to S1 (report correctness)

**Unchanged and not expanded.** S1 remains exactly as defined in
`CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-011`:
repository-level `is_current` fix, `current_version` in the report listing, the stale
`download_report` docstring correction, and a regression test.

- This discovery adds **no** work to S1.
- Ask CarbonTally implementation must **not** be combined with report lifecycle work.
- The only interaction is a **dependency direction**: Ask tools that cite reports will
  reference `report_versions`. The `is_current` defect (§23 R-2) means "the current
  version" is currently ambiguous at the repository layer — so Ask tools must select
  versions explicitly rather than relying on `is_current` until S1 lands.

---

## 23. Risks and unresolved questions

### 23.1 Architectural risks

| ID | Risk | Severity | Disposition |
|---|---|---|---|
| **R-1** | **Documented contradiction.** `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` §9 ("short-lived in the browser") and §10.2 ("Log … session id") assume non-persistence, which the PO decision supersedes. Left unacknowledged, implementers will read two conflicting specifications. | High | **PO acknowledgement required.** Recommend the OHD doc be updated (additively) *after* ratification — not silently rewritten by this task. |
| **R-2** | `report_versions.is_current` is unreliable at the repository layer (S1's finding). Any Ask tool that says "the current report" would inherit the ambiguity. | Medium | Owned by **S1**. Ask must select versions explicitly; convenience features depend on S1's fix. |
| **R-3** | The exact RLS policies present in the **live** database could not be inspected (no DB access permitted). | Medium | `[UNVERIFIED]` — carried forward from the Phase 8 package. Does not block this design; must close before I2. |
| **R-4** | The effective backend database role and whether `FORCE ROW LEVEL SECURITY` is set could not be verified. | Medium | `[UNVERIFIED]` — must close before I2 (the §17 design assumes the existing bypass posture). |
| **R-5** | `components/chat/*` presentation reusability is inferred from module purpose and file names, not a props-level review. | Low | Verify before I6 (`[UNVERIFIED]` for the specific components). |
| **R-6** | `LLMClient.complete()` returns no usage data, so `tokens_used`/`cost` cannot be recorded and token-based allowances cannot be enforced. | Medium | EXTEND in I3/I8. Until then record NULL — never fabricate. |
| **R-7** | No provider is ratified, so the provider data-retention/training/residency position is unknown. | High (legal) | PO + LEGAL (21.13). Do not transmit customer business data until decided. |
| **R-8** | Two conversational surfaces in one product (human messaging; Ask) may confuse users about where a conversation lives. | Medium | UX naming/entry-point decision during I6; D21 tokens and clear labelling. |
| **R-9** | Persisted conversations grow without bound (financial + data-protection exposure). | Medium | 21.3 retention; enforce server-side. |
| **R-10** | `ai_content_history` (dormant) overlaps a future Ask cost/rating record. Building both would create duplicate AI-history stores (AGENTS.md §66). | Medium | Decide one home before I3/I4: extend `ai_content_history` **or** keep cost data on `ask_interactions` — not both. |
| **R-11** | Phase 7 taxonomy has no AI category; choosing neither option A nor B leaves audit filtering awkward. | Low | 21.15. |
| **R-12** | `audit_trail` is append-only for every role, so Ask audit retention cannot simply be purged. | Medium | 21.3 + engineering design (§15.7). |
| **R-13** | Frontend effort for an authenticated Ask surface is unquantified (no existing authenticated assistant UI). | Medium | Scope during I6 planning. |
| **R-14** | The brief's §21 answer-lifecycle statuses are new vocabulary with no repository precedent; if implementers collapse them, `no_data` becomes zero. | High | §21.0 is binding; add an explicit QA assertion (rule 14). |

### 23.2 Open questions explicitly not resolved here

1. Whether Ask CarbonTally is one surface or per-workspace (customer/consultant/staff) —
   21.16/21.17.
2. Whether the public assistant ever gains persistence — 19.1.
3. Whether conversations can be shared between users — 21.1.
4. Whether the deterministic intent classifier is rule-based only, or may use the model to
   disambiguate. **Recommendation:** rules first; if the model is used, it must choose from
   a **closed** intent list and must never supply parameters (parameters are
   server-derived).
5. Whether `ask_interactions.tool_args` may contain business identifiers (PO/legal).

---

## 24. Explicit non-goals

This discovery does **not**:

1. Implement anything — no code, schema, migration, RLS, route, service, UI, or provider
   binding.
2. Authorise implementation — see §25 and §J.
3. Expand S1 or combine with report lifecycle work.
4. Create a second LLM/provider abstraction.
5. Create unrestricted RAG/vector/database access.
6. Grant PE users any Ask or report-document access.
7. Create any auditor/assurance/reviewer capability.
8. Change Human ↔ Human messaging in any way (tables, RLS, routes, UI, retention).
9. Change billing, plans, credits, or commercial config.
10. Change the Phase 7 audit ledger, its immutability trigger, or its taxonomy (options are
    proposed, not applied).
11. Change `audit_package()` or claim any assurance.
12. Make GDPR/UK GDPR/EU or any legal-compliance claim.
13. Invent retention durations, allowances, prices, or provider policies.
14. Modify the public assistant widget.
15. Modify the roadmap or any frozen D1–D21 decision.

---

## 25. Final recommendation

### 25.1 The recommendation

**Proceed to PO ratification of this design (D2). Do not begin I1–I8.**

Ask CarbonTally persistence should be implemented as a **new, bounded, tenant-scoped
conversation domain** with:

1. `organization_id NOT NULL` on every row, and RLS policies created **in the same
   migration** as the tables (not relying on the dynamic loop alone).
2. Re-authorisation of **current** scope on **every** conversation read and **every** tool
   call — a conversation is never an authorization mechanism.
3. A **deterministic-first** pipeline whose facts always come from server-side, read-only
   tools, with the LLM used only for narration.
4. **Three layers:** conversation history (UX lifecycle), AI interaction record
   (provenance, retained), canonical `audit_trail` event (append-only evidence).
5. References, not duplicated datasets — `report_version`, `calculation_snapshot`,
   evidence ids, plus `result_hash`.
6. Reuse of `LLMClient`, `ai_runtime` attribution, the existing authorization guards, the
   existing audit ledger, the versioned commercial config, and the existing
   repository/domain/API layering.
7. **No** reuse of the human messaging tables, and **no** coupling to their retention,
   RLS, Realtime, or UI semantics.

The evidence supports this strongly: the design is dominated by **reuse + extend**
(§20.2), the AI boundary conventions already exist in the codebase, and the only genuinely
new business structures required are two small, well-understood tables plus a tool
registry whose design already exists in the repository.

### 25.2 What is required before implementation

| Requirement | Type |
|---|---|
| PO ratification of this design | Decision |
| PO acknowledgement of R-1 (the superseded session-based statements) | Decision |
| Answers to 21.1, 21.2, 21.6, 21.16 (the I1/I2 blockers) | Decision |
| Closure of R-3/R-4 (live RLS posture + effective backend role) | Verification |
| Provider + legal position (21.13, 21.14) before any personal data is transmitted | Decision + legal |
| Retention design (21.3) before customer rollout | Decision |

### 25.3 What this document deliberately does not do

It does not authorise implementation, does not expand S1, does not modify any frozen
decision, and does not resolve any PO decision on the Product Owner's behalf. Every
product, commercial, retention, and legal question is surfaced in §21 rather than assumed.

---

## A. What already exists

- **Single LLM provider abstraction:** `backend/infra/llm_client.py` —
  OpenAI/Anthropic-compatible `/chat/completions`, injectable transport,
  `AIExtractionFailedError` on every failure, `temperature=0.0` default.
- **Truthful AI attribution:** `backend/infra/ai_runtime.py` — `provider_label()`,
  `configured_ai_attribution()`, env-gated configuration; API key never read.
- **Canonical AI boundary conventions:** `backend/services/ai_document_extraction.py` —
  AI output is candidate only; never a false success; no credentials or raw document
  content persisted.
- **A working public assistant:** `frontend/src/public/assistant/*` — deterministic,
  local, no backend, no persistence; `SUGGESTED_QUESTIONS` already present.
- **A substantial Ask CarbonTally design:** `docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md`
  — personas, knowledge, tools, injection defence, PE boundary, provider abstraction,
  context, audit-logging intent, phases 1–7, open decisions.
- **Full Human ↔ Human messaging:** `conversations`, `conversation_participants`,
  `messages`, `file_attachments`, `typing_status`, `message_activity_log`,
  `conversation_activity_log`, `backend/api/v3_messaging.py`, and eight
  `frontend/src/components/chat/*` components.
- **A mature authorization layer:** `ensure_org_access`, `require_org_member`,
  `require_admin`, `ensure_consultant_org_access`, `_resolve_context` +
  `ensure_staff_permission`, `is_active_pe_member`, `get_current_user`.
- **An append-only audit ledger:** `public.audit_trail` + `p7_audit_trail_immutable()`
  trigger + five investigation indexes + `AuditRepository` + `/api/v2/admin/audit`
  (`require_admin`).
- **A canonical audit taxonomy:** `ACTOR_TYPES`, `ORIGINS`, `OUTCOMES`, eleven
  `CATEGORIES` in `backend/domain/audit.py`.
- **An audit/evidence package:** `reporting.audit_package()` with integrity hashing and an
  explicit `not_assurance` contract.
- **Usage and commercial infrastructure:** `usage_tracking` counters,
  `billing_commercial_config` versioned rules, `billing_plans`, `billing_credit_ledger`.
- **A dormant AI history table:** `public.ai_content_history` (prompt/model/tokens/cost/
  rating/feedback; `organization_id NOT NULL`; zero code references).
- **A precedent for adding a conversation kind with RLS:**
  `20260902040000_phase5_pe_operational_messaging.sql`.

## B. What can be reused

- `LLMClient` + `LLMTransport` + `AIExtractionFailedError` (no second abstraction).
- `provider_label()` and `configured_ai_attribution()` for per-interaction attribution.
- The `ai_document_extraction.py` boundary rules as binding conventions.
- All authorization guards and `get_current_user`.
- The `_authorize_org_actor` three-branch resolver *shape* (org / consultant-with-ACTIVE-
  grant / capability-gated internal staff, with explicit PE denial).
- `audit_trail` + `AuditRepository.record()` for one reference-level event per interaction.
- The Phase 7 `metadata`-based org scoping convention (`metadata->>'organization_id'`).
- `audit_package()` unchanged (no AI content).
- `billing_commercial_config` for allowance policy; `usage_tracking` for counters.
- The repository/domain/API layering and the pure-domain convention.
- `components/chat/*` presentation primitives (conditional on R-5).
- `report_versions`, `calculation_snapshots`, and evidence records as **referenced
  artefacts**.

## C. What should be extended

- `LLMClient`: bounded multi-turn input; surface usage (tokens/cost) when truthfully
  available.
- Phase 7 audit taxonomy: optionally add one AI-interaction `CATEGORY` (option A) — no
  migration, no change to `OUTCOMES`.
- `usage_tracking`: an AI-interaction counter (or derive counts from `ask_interactions`).
- The public knowledge allowlist: extend for authenticated product explanations.
- RLS coverage: create Ask policies **explicitly** in the creating migration.
- (Decide one home) `ai_content_history` **or** `ask_interactions` for AI cost/rating —
  never both.

## D. What genuinely requires new architecture

1. **`ask_conversations`** — tenant-scoped, owner-recorded, lifecycle metadata.
2. **`ask_messages`** — `actor_type` user/assistant/system; status; ordering.
3. **`ask_interactions`** — the AI interaction/provenance record: intent, tool calls,
   references, `result_hash`, provider/model, `answer_status`, grounding, fallback reason.
4. **The tool registry and its controlled, read-only, authorization-checked tools**
   (design exists; implementation does not).
5. **The Ask RLS policy set** — and the hardening posture that must not repeat A-RLS.
6. **The authenticated Ask API** (`/api/v3/ask/*`) with re-authorisation on every read.
7. **The authenticated Ask UI** — a new surface; presentation primitives reused only.
8. **The answer-status vocabulary and its enforcement** (`no_data` ≠ zero).
9. **The retention/export mechanism for Ask** — must be designed deliberately because
   `audit_trail` is append-only for every role.

## E. What must remain separate from Human ↔ Human messaging

- **Tables:** no Ask rows in `conversations`/`messages`/`conversation_participants`.
  Proof: `list_conversations_for_org()` filters on `organization_id` alone, so an Ask
  conversation carrying an org id would appear in the customer's human messaging list.
- **Semantics:** `sender_id`/`receiver_id`/read receipts/typing/participants do not apply;
  Ask has one human + a system actor + tool calls + references + statuses.
- **Retention:** human messages are soft-deletable; Ask retention is undecided, and Ask
  audit must survive deletion.
- **RLS:** Ask gets its own predicates; it must not inherit or alter messaging policies.
- **Realtime/UI:** `postgres_changes` subscriptions and chat components are not shared by
  default.
- **Audit:** AI interaction records are not human message activity logs
  (`message_activity_log` / `conversation_activity_log` are not reused).

## F. Security invariants

1. A conversation is **never** an authorization mechanism.
2. Every conversation read and every tool call re-authorises the **current** scope.
3. Stored references are re-authorised pointers, not grants.
4. The LLM is **outside** the authorization boundary, never calculates carbon, never
   chooses factors, never invents evidence, never modifies authoritative records.
5. Read-only tools initially; allowlist per persona; server-side execution with the
   caller's identity.
6. No unrestricted RAG/database access — authorization precedes retrieval.
7. `organization_id NOT NULL` + explicit RLS policies created with the tables.
8. No cross-tenant leakage via history, paraphrase, references, or injection.
9. Conversation deletion never removes the interaction record or the audit event.
10. No credentials, secrets, signed URLs, storage paths, or raw document content are stored
    in the Ask domain or sent to a provider.
11. `no_data` is never rendered as zero.
12. No assurance/audit/certification claim is attached to conversational output.

## G. PO decisions required

See §21. Blocking I1/I2: **21.1 visibility · 21.2 deletion · 21.6 PE · 21.16 persona**.
Also required: 21.3 retention · 21.4 export · 21.5 consultant · 21.7 auditor · 21.8 audit
package · 21.9 allowance · 21.10 context/compaction · 21.11 rename/archive ·
21.12 regeneration · **21.13 provider + data stance (PO + LEGAL)** · **21.14 PII (PO +
LEGAL)** · 21.15 taxonomy option · 21.17 first surface. Plus acknowledgement of **R-1**.

## H. Future implementation stages

`D1` (this document) → `D2` PO ratification → `I1` persistent conversation foundation
(tables + RLS together) → `I2` authorization hardening/visibility → `I3` controlled
read-only tools (deterministic path) → `I4` interaction record + audit integration →
`I5` bounded context → `I6` UI → `I7` privacy/retention/export → `I8` billing/allowance +
production hardening. Deferred: consultant/staff/PE Ask, auditor capability,
summary/compaction, scoped retrieval. Gating conditions in §22.3; test obligations in
§22.4.

## I. Risks / unresolved questions

R-1 documented contradiction (persistence vs the existing design doc) · R-2
`report_versions.is_current` (owned by S1) · R-3 `[UNVERIFIED]` live RLS policy list ·
R-4 `[UNVERIFIED]` effective backend role / `FORCE RLS` · R-5 `[UNVERIFIED]` chat
component reusability · R-6 no usage data from `LLMClient` · R-7 no ratified provider /
data stance · R-8 two conversational surfaces may confuse users · R-9 unbounded
conversation growth · R-10 `ai_content_history` overlap · R-11 taxonomy choice ·
R-12 append-only audit vs retention · R-13 unquantified frontend effort · R-14
answer-status collapse risk. Unresolved questions listed in §23.2.

## J. FINAL STATUS

**`DISCOVERY COMPLETE — READY FOR PO REVIEW`**

Justification:

- Both required documents were created; no application code, database schema, migration,
  RLS policy, API route, frontend file, AI provider binding, billing change, messaging
  change, or production access was touched.
- Every major existing AI, messaging, audit, and authorization structure required by the
  brief was traced to specific files and line-level evidence.
- Three claims remain explicitly `[UNVERIFIED]` because closing them would have required
  live database access, which the stop conditions forbid: the live RLS policy list per
  table (R-3), the effective backend database role / `FORCE RLS` posture (R-4), and
  props-level chat-component reusability (R-5). None blocks ratification of the design;
  all three are recorded as I2/I6 prerequisites.
- No blockers under the brief's §30 hard stop conditions were encountered: implementation
  was not required to determine the architecture; live production/database access was not
  required; no migration execution and no provider credentials were needed; no security
  claim depends on unavailable evidence; and the existing architecture does **not**
  contradict the product decision — it contradicts it on exactly one narrow point
  (session-based context, R-1), which is documented for acknowledgement rather than
  silently reconciled.

**This document does not authorise implementation (rule 19).**
