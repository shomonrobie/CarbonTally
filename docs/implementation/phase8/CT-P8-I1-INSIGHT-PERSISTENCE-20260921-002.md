# CT-P8-I1 — CarbonTally Insight Layer-1 Persistent Conversation Foundation

**Authorization ID:** `CT-P8-I1-INSIGHT-PERSISTENCE-20260921-002` (I1 only)
**Implementation date:** 2026-09-21
**Branch:** `p8-release-reconciled`
**Starting commit:** `e48ee55273eb5f018b091bfeed7b6c2e8917f5f9`
**Implementation commit:** `5633798a955a26381c579f223863559adebaf33c`
**Primary verdict:** `I1 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`

## 1. Authoritative specification inspected

`docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md`
(D2, PO-ratified Rev 2) — §5.1 (conversations are persisted), §6 (separate
conversational domain), §7 (three-layer model; Layer 1 = I1), §3.2.1/§3.8
(canonical `carbontally_insight_*` naming for new implementation), §8 (every read
re-authorised; a stored reference is not a grant), §9.2 (initial creator-private
visibility), §10.2 (staff Insight access deferred), §11.6 (answer-state vocabulary
deferred), §20 (retention/archival deferred), §21 (billing deferred), §22 (AI
audit/`ai_content_history` treatment open), §24.2/§24.3/§24.4/§24.5/§24.6 (I1
MAY/MUST-NOT lists and the explicit RLS-posting requirement).

Also inspected before implementation: D1 persistence discovery (proposal-only,
`ask_*` naming superseded by D2 §3.8), the current migration chain (latest
`20260931000000_p8_fs_adjudication_context_lineage.sql`), RLS conventions
(`20260803000000_rc2_rls.sql` → `public.is_org_member`; `20260925000000_p8_rls_4b_group1_enablement.sql`;
`20260916000000_p8_b2_evidence_line_items.sql` privilege/policy pattern),
auth/authorization conventions (`backend/auth.py`, `backend/api/dependencies.py`),
repository conventions (`backend/data/base.py`, `RepositoryBundle`), router
composition (`backend/api/router.py`), human messaging tables
(`public.conversations`, `public.messages`, `public.message_activity_log`), and the
dormant `public.ai_content_history` table.

Repository state matched the expected Phase 8 baseline: clean working tree at
`e48ee55`, branch `p8-release-reconciled`, no pre-existing
`carbontally_insight_*`/`ask_*` objects in migrations or backend code.

## 2. Status matrix (I1)

| I1 item (D2 §24.2) | Status |
| --- | --- |
| Dedicated Insight conversation persistence | IMPLEMENTED |
| Dedicated Insight message persistence | IMPLEMENTED |
| Organization scoping (schema + RLS + repository) | IMPLEMENTED |
| Explicit RLS/security posture | IMPLEMENTED |
| Indexes / constraints / referential integrity | IMPLEMENTED |
| Minimal repository/domain layer | IMPLEMENTED |
| Minimal create/list/read functionality | IMPLEMENTED |
| Basic persistence API foundation | IMPLEMENTED |
| Model able to carry later layers without implementing them | IMPLEMENTED |
| Every read re-authorised | IMPLEMENTED |
| Creator-private visibility expressible **and enforced** | IMPLEMENTED |
| Persistence / isolation / authorization tests | IMPLEMENTED + VERIFIED BY TESTS |
| Live database RLS behaviour | VERIFIED (disposable `carbontally_test` clone) |

## 3. Files, tables, routes

**Created**

* `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql` (219 lines)
* `backend/domain/insight.py` — `InsightConversation`, `InsightMessage`
* `backend/data/insight.py` — `InsightRepository`
* `backend/api/v3_insight.py` — `APIRouter(prefix="/api/v3/insight")`
* `backend/tests/unit/data/test_i1_insight_migration.py` (9 tests)
* `backend/tests/unit/api/test_v3_insight_endpoints.py` (8 tests)

**Modified**

* `backend/api/dependencies.py` — `RepositoryBundle.insight` + construction in `get_repositories()`
* `backend/api/router.py` — router import + `include_router` on the V3 composition root
* `backend/tests/unit/api/fakes.py` — bundle field for the shared in-memory harness

**Tables:** `public.carbontally_insight_conversations`,
`public.carbontally_insight_messages` (both new; nothing else created, altered or dropped).

**Routes (5 operations, 3 paths):**

| Method | Path |
| --- | --- |
| POST | `/api/v3/insight/conversations` |
| GET | `/api/v3/insight/conversations` |
| GET | `/api/v3/insight/conversations/{conversation_id}` |
| POST | `/api/v3/insight/conversations/{conversation_id}/messages` |
| GET | `/api/v3/insight/conversations/{conversation_id}/messages` |

Verified present in the composed app's OpenAPI contract (05 paths query:
`/api/v3/insight/conversations`, `.../conversations/{conversation_id}`,
`.../conversations/{conversation_id}/messages`).

## 4. Schema design

`public.carbontally_insight_conversations`

| Column | Notes |
| --- | --- |
| `id uuid PK` | `DEFAULT extensions.uuid_generate_v4()` (repository convention) |
| `organization_id uuid NOT NULL` | `REFERENCES public.organizations(id) ON DELETE CASCADE` |
| `created_by uuid NOT NULL` | creator principal (creator-private authority) |
| `title text` | optional label for conversation listing |
| `created_at`, `updated_at timestamptz NOT NULL DEFAULT now()` | technical timestamps |
| `UNIQUE (id, organization_id)` | composite-FK target (integrity) |

`public.carbontally_insight_messages`

| Column | Notes |
| --- | --- |
| `id uuid PK` | as above |
| `conversation_id uuid NOT NULL` | parent conversation |
| `organization_id uuid NOT NULL` | denormalised so the RLS predicate is expressible on the row (D2 §24.6) |
| `created_by uuid` | author principal; `CHECK (role <> 'user' OR created_by IS NOT NULL)` |
| `role varchar(16) NOT NULL` | `CHECK (role IN ('user','insight'))` — author kind only |
| `content text NOT NULL` | `CHECK (length(content) > 0)` |
| `ordinal integer NOT NULL` | `CHECK (ordinal >= 1)`, `UNIQUE (conversation_id, ordinal)` |
| `created_at timestamptz NOT NULL DEFAULT now()` | technical timestamp |
| `FOREIGN KEY (conversation_id, organization_id)` | → conversations `(id, organization_id)` `ON DELETE CASCADE` |

Indexes: `idx_ci_conversations_org_created`, `idx_ci_conversations_org_creator_created`,
`idx_ci_messages_conversation_ordinal`, `idx_ci_messages_org`.

**Non-obvious technical design decisions (documented per prompt §7):**

1. **Composite FK instead of a trigger.** `(conversation_id, organization_id)` →
   `conversations (id, organization_id)` makes a message structurally unable to
   belong to a different organisation than its conversation — no trigger and no
   application trust required, and the RLS predicate becomes expressible
   directly on the message row.
2. **`role` is an author kind, not a product status.** A persisted conversation
   cannot be represented without an author kind; D2 §11.6 defers the answer-state
   vocabulary, so exactly two values exist (`user`, `insight`) and no status,
   review or lifecycle column is introduced.
3. **Explicit `ordinal`.** Ordering is a persistence requirement; allocating the
   next ordinal inside the INSERT (`max(ordinal)+1`) with a UNIQUE constraint as
   the authority means a concurrent writer surfaces as an integrity error rather
   than a silent re-order. No retry loop is added in I1 (single writer path).
4. **`title` is optional** — it exists only so a conversation list is readable.
5. **No delete/rename surface.** `InsightRepository.delete()` raises
   `NotImplementedError`; no client DELETE was granted (retention/deletion = I7).

## 5. RLS / security design

Privilege posture (`20261001000000_p8_i1_insight_persistence.sql` §3):

* `anon`: `REVOKE ALL` — no anonymous surface.
* `authenticated`: `SELECT, INSERT` on both tables, immediately
  `REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, MAINTAIN`.
* `service_role`: `ALL` — the FastAPI backend is the writer and **re-authorises
  every read in code** (RLS is not the backend's boundary).

Policies (4, all `TO authenticated`, each idempotently guarded):

* `ci_conversations_creator_select` — `USING (public.is_org_member(organization_id) AND created_by = auth.uid())`
* `ci_conversations_creator_insert` — same predicate as `WITH CHECK`
* `ci_messages_conversation_creator_select` — `USING (public.is_org_member(organization_id) AND EXISTS (… c.created_by = auth.uid()))`
* `ci_messages_conversation_creator_insert` — same predicate plus `created_by = auth.uid()` as `WITH CHECK`

**Organisation isolation** is enforced at three independent layers: (a) RLS
`is_org_member` membership on every row; (b) `ensure_org_access` on every API
request (D20 scope-aware: PE staff denied, internal staff operational-only,
members restricted to their own organisation); (c) repository reads always taken
via `get_conversation(conversation_id, organization_id)` /
`list_messages(…, organization_id=…)`, never by id alone. `InsightRepository.get(id)`
is documented as internal/service-only and is unused by the API.

**Creator-private representation and enforcement (D2 §9.2):** `created_by` plus
the `created_by = auth.uid()` predicate. The API resolves a conversation through
`_authorised_conversation()`, which returns `404` unless
`conversation.created_by == current_user.user_id`; the list path passes
`created_by=current_user.user_id` as a repository filter. **A stored conversation
id therefore confers no access** (D2 §8.4). Internal-staff Insight visibility is
DEFERRED (D2 §10.2), so I1 grants **no** staff exception — every principal,
including CarbonTally staff, is creator-scoped.

**Live RLS evidence** (real PostgreSQL, disposable `carbontally_test` database;
migration applied, `SET LOCAL ROLE authenticated` + JWT-claim role-play, fixture
inside a transaction that was rolled back):

| Check | Observed | Expected |
| --- | --- | --- |
| Creator reads conversations | 1 | 1 |
| Creator reads messages | 1 | 1 |
| Same-org non-creator reads conversations | 0 | 0 |
| Same-org non-creator reads messages | 0 | 0 |
| Other-org member reads conversations | 0 | 0 |
| Cross-tenant INSERT (org-B member → org-A conversation) | `ERROR: new row violates row-level security policy` | rejected |
| Authorised INSERT (own org, own creator) | 1 | 1 |

The same-org **impersonation** write (`created_by ≠ auth.uid()`) is enforced by
the `created_by = auth.uid()` `WITH CHECK` clause; it was not isolated in its own
live probe (the first RLS rejection aborted that transaction), so it is
**contract-tested and API-tested but not separately live-probed** and is
recommended for the OHD scope below. No investor-demo, QA or production database
was touched; `backend/tests/integration/conftest.py` (F-046-1 destructive TRUNCATE
guard) was not invoked.

## 6. Repository / API implementation

`backend/data/insight.py` (`InsightRepository(AbstractRepository[InsightConversation])`):
`create_conversation`, `list_conversations(created_by=…)`, `get_conversation`,
`add_message` (ordinal allocation + `updated_at` touch), `list_messages`,
`count_conversations`, plus the abstract `get`/`save` and a refusing `delete`.
Every organisation-facing read is organisation-scoped.

`backend/api/v3_insight.py`: the five persistence endpoints in §3. Each requires
`require_org_member()` and calls `ensure_org_access`; message creation accepts
only `role="user"` (an `insight`-authored message cannot be persisted while no
LLM exists — fabricating CarbonTally-authored content is refused with `422`),
rejects blank content (`422`), and validates list pagination bounds. Responses
carry business-meaningful fields (id, organisation, title, role, content,
ordinal, timestamps) and never a raw database error.

## 7. Tests executed and results

Command: `cd backend && python -m pytest tests/unit/data/test_i1_insight_migration.py tests/unit/api/test_v3_insight_endpoints.py -q`
→ **17 passed** (9 migration-contract + 8 API behaviour).

Migration contract tests assert: canonical `carbontally_insight_*` tables (and no
`ask_*`), organisation FK on both tables, composite-FK integrity, ordering/identity
constraints, the four indexes, explicit RLS enablement, anon revocation, client
`SELECT, INSERT`-only grants (no `UPDATE`/`DELETE` grant), creator-private
predicates, four idempotent policy guards, no touch of human messaging tables or
`ai_content_history`, and no I2–I8 fields (`provider`, `model`, `prompt`,
`retention`, `deleted_at`, `billing`, `status`, `audit_event`, …).

API behaviour tests (in-memory repository via FastAPI dependency overrides; no
database opened) assert: create/list/read; message append and ordinal ordering;
blank-content rejection; creator-private list/read/append denial (same organisation,
different principal → `404`, nothing written); cross-organisation read denial with
the exact stored id (`404`) and refusal of the other organisation's id (`403`,
nothing written); `401` without authentication; `422` for an `insight`-authored
message.

Composition verification: the composed application's OpenAPI contract exposes all
three insight paths (5 operations).

## 8. Assumptions, open decisions, limitations

**Assumptions:** (a) `role ∈ {user, insight}` is a minimum technical field, not a
product status; (b) `title` is a technical label; (c) explicit `ordinal` is the
ordering authority; (d) creator identity is the auth principal id, consistent with
existing platform tables.

**Open decisions (NOT answered here, PO/D2-owned):** answer-state vocabulary
(D2 §11.6, I3/I4); retention/archival/deletion semantics (I7); staff/consultant/
auditor/PE Insight visibility (I2, D2 §10.2); LLM provider configuration and
allowances (I8); the disposition of the dormant `public.ai_content_history`
(D2 §22, I3/I4).

**Limitations:** (1) concurrent writers to the *same* conversation can collide on
`UNIQUE (conversation_id, ordinal)` — I1 has a single writer path, so no retry is
implemented; (2) the migration was applied and RLS-verified on the disposable
`carbontally_test` clone, **not** on the investor-demo or any persistent
environment; (3) the same-org impersonation write is contract/API-tested but not
separately live-probed (§5); (4) the migration is not yet applied to persistent
environments (deployment is outside this authorization).

## 9. Explicit confirmations

* **I2–I8 NOT IMPLEMENTED.** No full authorization/visibility model (I2), no tools
  / intent classification / tool registry / reference semantics (I3), no AI
  interaction records or canonical AI audit events (I4), no context/memory
  assembly (I5), no frontend Insight UI (I6), no privacy/retention/deletion/export
  (I7), no provider configuration/hardening/billing/allowance (I8).
* **NO LLM / PROVIDER INTEGRATION.** No OpenAI/Anthropic/Gemini or other provider,
  no model or provider selection, no API keys, no prompts/system prompts, no tool
  or function calling, no RAG, embeddings, vector search, agent loops, LangChain
  or answer generation. No provider is required to run the I1 tests.
* **NO UI.** No chat page, widget, composer, conversation sidebar, streaming,
  citations, evidence drawer or AI answer cards.
* **NO ACCOUNTING/RUNTIME CHANGES.** No emissions calculation, factor matching,
  factor database, calculation snapshot, emissions log, reporting, evidence
  extraction, document processing, approval or billing logic touched; human
  messaging, authentication/authorization behaviour and the public assistant are
  unmodified.
* **DORMANT TABLE UNTOUCHED.** `public.ai_content_history` is not reused, migrated,
  altered or deleted.
* **NO `ask_*` OBJECT** was created; canonical `carbontally_insight_*` naming only.
* **STOP CONDITIONS NOT TRIGGERED.** D2 did not conflict with repository reality in
  a way that changes I1 product behaviour; no unauthorised product-level schema
  decision was required; RLS expresses the organisation + creator-private boundary
  safely; existing authentication supported I1 directly; no unrelated accounting
  logic, no destructive migration and no I2–I8 requirement was involved.

## 10. Git state and handoff to OHD

* **Branch:** `p8-release-reconciled`
* **Starting SHA:** `e48ee55273eb5f018b091bfeed7b6c2e8917f5f9`
* **Implementation commit:** `5633798a955a26381c579f223863559adebaf33c`
* **Changed files:** the 6 created + 3 modified paths listed in §3 (this report is
  committed separately).
* **Migration:** `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql`
* **API routes:** `/api/v3/insight/conversations` (GET, POST),
  `/api/v3/insight/conversations/{conversation_id}` (GET),
  `/api/v3/insight/conversations/{conversation_id}/messages` (GET, POST)
* **Tests:** `backend/tests/unit/data/test_i1_insight_migration.py` (9),
  `backend/tests/unit/api/test_v3_insight_endpoints.py` (8) — 17 passed
* **Report:** `docs/implementation/phase8/CT-P8-I1-INSIGHT-PERSISTENCE-20260921-002.md`

**Recommended OHD verification scope:** (1) independent live RLS verification on a
disposable clone, including the same-org impersonation write and cross-organisation
message INSERT; (2) confirm no `ask_*`/other Insight object exists beyond the two
tables; (3) confirm the five routes appear in the running OpenAPI contract and
enforce `401/403/404` as specified; (4) confirm the human messaging and public
assistant surfaces are unaffected; (5) confirm I2–I8 are absent and no LLM/provider
is required.

**Known limitations:** as listed in §8.

**Next step:** independent OHD verification, then PO closure of I1. **No I2
implementation is authorized.** The only completion claim made here is completion
of the **I1 persistent conversation foundation**; CarbonTally Insight itself is
NOT complete.

## 11. Final verdict

`I1 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`
