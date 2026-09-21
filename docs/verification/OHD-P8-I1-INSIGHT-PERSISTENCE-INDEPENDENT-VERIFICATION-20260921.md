# OHD — INDEPENDENT VERIFICATION — CARBONTALLY INSIGHT I1

**Verification ID:** `OHD-P8-I1-INSIGHT-PERSISTENCE-20260921`
**Date:** 2026-09-21
**Verifier:** OHD (independent verification agent) — read-only verification
**Verdict:** **PASS** (see §18 for the exact scope, rule and materiality test applied; this is **not** a closure of I1 and does **not** authorise I2)

---

## 1. Baseline

| Item | Value |
|---|---|
| Branch | `p8-release-reconciled` |
| HEAD | `5bd5e2964540a98c46f91c82551fc883dd398acc` |
| Remote alignment | `github/p8-release-reconciled` = `5bd5e2964540a98c46f91c82551fc883dd398acc` — **identical**; local HEAD is on the remote branch |
| Working tree | **clean** — `git status --porcelain --untracked-files=all` = 0 lines; `git stash list` = 0 entries |
| Other remotes | `origin` is a local path (`/tmp/ct_step2`) and is **not** used as evidence of remote state; `github` is the authoritative remote |

Baseline SHAs named in the brief were verified to exist and to have the stated content (the brief's instruction not to assume them was applied):

| SHA | Subject (verified) |
|---|---|
| `5633798` | `feat(p8-i1): CarbonTally Insight Layer-1 persistent conversation foundation` |
| `6e4b5a1` | `docs(p8-i1): CT-P8-I1 Insight persistence implementation report` |
| `97b50c3` | `docs(p8-i1): record I1 regression baseline evidence` |
| `5bd5e29` | `docs(audit): CT-FEATURE-AUDIT-P1-P8X-001 …` (the independent feature audit; current HEAD) |
| `e48ee55` | `docs: reconcile CarbonTally Insight specification (CT-P8-SPEC-001)` — the parent of `5633798`, used as the pre-I1 comparison point |

The repository is in the clean state described in the brief: no uncommitted or stashed I2 attempt remains.

## 2. Specification used

`docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` (1,555 lines), read directly from the repository, specifically:

* **§24.1–§24.6** — the I1 authorization boundary (MAY-include list, MUST-NOT-expand list, binding constraints, explicit-RLS-posture note).
* **§5.1** (conversations are persistently stored), **§6.1–§6.4** (separate conversational domain; `DO NOT` reuse human messaging), **§7 / §7.5** (three-layer model, Layer 1 at I1; exact schema deliberately deferred), **§8.1–§8.8** (authorization rule: every read re-authorised; stored references are not grants; required order of operations), **§9.1–§9.6** (first persona/surface; creator-private visibility; both organisation scope *and* a creator predicate must be expressible), **§10.1–§10.5** (consultant/staff/auditor/PE deferred), **§11.6** (answer-state vocabulary deferred), **§20.3** (retention must be introducible later), **§26** (non-goals), **§27.1** (R1 naming: earlier `ask_*` terminology superseded).

Older D1 material and superseded `ask_*` terminology were treated as non-authoritative, per the brief.

## 3. Exact implementation baseline

Verified commit `5633798` ("the I1 implementation itself"), footprint confirmed by `git show --stat`:

| File | Lines added |
|---|---:|
| `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql` | 218 |
| `backend/domain/insight.py` | 57 |
| `backend/data/insight.py` | 250 |
| `backend/api/v3_insight.py` | 227 |
| `backend/api/dependencies.py` | 7 |
| `backend/api/router.py` | 5 |
| `backend/tests/unit/api/test_v3_insight_endpoints.py` | 315 |
| `backend/tests/unit/data/test_i1_insight_migration.py` | 159 |
| `backend/tests/unit/api/fakes.py` | 6 |
| **Total** | **1,244 insertions, 0 deletions** |

No frontend, configuration, deployment, dependency or unrelated file was touched by I1 (checked explicitly).

## 4. Verification methodology

Everything below was derived from the repository, PostgreSQL and the code's own runtime behaviour. The Cline implementation report (`docs/implementation/phase8/CT-P8-I1-INSIGHT-PERSISTENCE-20260921-002.md`) was read **only after** the independent work, to compare claims — it was not used as evidence.

1. **Source trace** of the migration, domain, data, API, dependency and router layers (read in full).
2. **Requirement-by-requirement mapping** of D2 §24.2/§24.5/§24.6/§7.5/§8/§9.2 onto code and schema.
3. **Own disposable database**: `ct_i1_verify_20260921`, created as a template copy of the disposable `carbontally_test`, with the I1 objects **dropped** and the repository migration then **applied verbatim** from the repository file — so the verified schema is the auditor's own application of the repo DDL, not someone else's pre-applied state. The migration was then **re-applied** to test idempotency.
4. **Live RLS/authorization probe** — 35 cases under `SET LOCAL ROLE authenticated` with simulated `request.jwt.claims` (the mechanism `auth.uid()` reads), plus `anon` and `service_role` cases and 9 constraint probes.
5. **Live repository probe** — the real `InsightRepository` (`backend/data/insight.py`, unmodified, imported from HEAD) driven against the same database over asyncpg, exercising the exact SQL the FastAPI layer uses, including a 6-way concurrent ordinal race.
6. **Principal probe** — the real `api/v3_insight.py` router mounted in a test app exactly as the I1 suite does, but with principal shapes the I1 suite does not use (internal staff with and without org membership, Processing Entity staff).
7. **Test execution** — the I1 tests re-run, plus the **entire unit suite at HEAD and at the pre-I1 commit `e48ee55`** (in a throwaway clone under `/tmp`) for a regression comparison.
8. **Leakage and naming searches** across `backend/`, `frontend/src/`, `admin/src/` and `supabase/`.

**Environment discipline:** no migration was applied to Demo Lab, QA or production; the Demo Lab, QA and reference databases were only *read* (`information_schema`). No application code, migration, schema, configuration, test, fixture, deployment file or data outside the auditor's own disposable database was modified. The only repository change made by this task is this report.

## 5. I1 Requirement matrix

| # | Requirement (authority) | Result | Evidence |
|---|---|---|---|
| 1 | Dedicated Insight conversation persistence (§24.2) | **PASS** | `public.carbontally_insight_conversations` created by the migration (L43–56); applied live to the auditor's clone; repository `create_conversation`/`list_conversations`/`get_conversation` exercised against real PostgreSQL (19/20 probe cases); API `POST/GET /api/v3/insight/conversations`. No reuse of any pre-existing conversation table. |
| 2 | Dedicated Insight message persistence (§24.2) | **PASS** | `public.carbontally_insight_messages` (L66–92); `add_message`/`list_messages` live-probed; ordinal ordering verified contiguous 1..n. |
| 3 | Organisation scoping (§24.2, §9.3, §9.6) | **PASS** | `organization_id uuid NOT NULL REFERENCES public.organizations(id)` on **both** tables (live-confirmed, count = 2); denormalised org on messages held consistent by the **composite FK** `(conversation_id, organization_id) → conversations(id, organization_id)`; repository reads are org-scoped; cross-org write denied live; cross-org read returns 0 rows live. |
| 4 | Explicit RLS posture (§24.6 — must not rely on the implicit tenant mechanism) | **PASS** | `ENABLE ROW LEVEL SECURITY` on both tables (live `rowsecurity = t` for both); explicit `REVOKE ALL … FROM anon`; explicit `GRANT SELECT, INSERT … TO authenticated`; explicit `REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, MAINTAIN`; explicit `GRANT ALL … TO service_role`; four named policies; the posture is stated in the migration header and table/column comments. Live-probed. |
| 5 | Appropriate indexes (§24.2) | **PASS** | `idx_ci_conversations_org_created`, `idx_ci_conversations_org_creator_created`, `idx_ci_messages_conversation_ordinal`, `idx_ci_messages_org` — all present live (`pg_indexes`), each matched to a real query shape (list by org, creator-private list, ordinal ordering). |
| 6 | Appropriate constraints (§24.2) | **PASS** | Live-enforced: `UNIQUE (id, organization_id)`; composite FK; `UNIQUE (conversation_id, ordinal)`; `CHECK (ordinal >= 1)`; `CHECK (role IN ('user','insight'))`; `CHECK (length(content) > 0)`; `CHECK (role <> 'user' OR created_by IS NOT NULL)`; `NOT NULL` on org/creator-of-conversation. All 9 negative probes were rejected with the expected constraint error. |
| 7 | Minimal create functionality (§24.2) | **PASS** | `POST /api/v3/insight/conversations`, live repository insert verified. |
| 8 | Minimal list functionality (§24.2) | **PASS** | `GET /api/v3/insight/conversations` (limit 1–200, offset ≥ 0, `total`), creator-filtered. |
| 9 | Minimal read functionality (§24.2) | **PASS** | `GET /api/v3/insight/conversations/{id}` plus `GET …/messages`; both re-resolve the conversation per request before returning anything. |
| 10 | Basic persistence API foundation (§24.2) | **PASS** | Five routes on one router, mounted once (`backend/api/router.py:237`, prefix `/api/v3/insight`); router exposed through `RepositoryBundle.insight`. Exactly the persistence surface; no answer generation. |
| 11 | Every read is re-authorised (§8.1, §8.2, §8.4, §24.5) | **PASS** | Every one of the five routes depends on `require_org_member()` **and** calls `ensure_org_access(current_user, organization_id)`; every conversation read additionally passes `_authorised_conversation()`, which applies organisation scope *and* a creator comparison, returning **404** (no existence disclosure). Verified live: a same-org non-creator and a cross-org principal both receive 0 rows from the database with the exact conversation id, and 404/403 from the API. No route ever trusts a stored id. |
| 12 | Creator-private visibility is expressible (§9.2, §9.3, §9.6) | **PASS** | RLS SELECT/INSERT predicates are `public.is_org_member(organization_id) AND created_by = auth.uid()` (conversations) and the org member + parent-conversation-creator `EXISTS` form (messages). Live: other-principal reads (same org and cross-org) return 0; other-principal appends are denied; forged `created_by` is denied; `is_org_member` was read out of the database and confirmed to test *active* membership of an *active* organisation. |
| 13 | Dedicated Insight domain, separate from human messaging (§6.1–§6.4) | **PASS** | The migration names only `public.carbontally_insight_conversations`, `public.carbontally_insight_messages` and `public.organizations` (FK target). No FK, repository, service, route or dependency touches `public.conversations`, `public.messages`, `public.message_activity_log` or `conversation_participants`; the only mention of them in I1 code is the migration's explicit non-scope comment. |

**Scope boundary (must not expand into — §24.3):** no I2 authorization/visibility work, no I3 tools, no I4 AI interaction/audit records, no I5 context orchestration, no I6 frontend, no I7 retention/export, no I8 billing/provider, no report-lifecycle change, no RAG, no LangChain, no consultant/auditor/PE access was found (§8 below).

## 6. Canonical naming

| Check | Result | Evidence |
|---|---|---|
| `carbontally_insight_*` used for all new persistence/domain objects (§3.2.1, §3.8, R1) | **PASS** | The literal namespace appears in exactly three non-test files: the migration, `backend/data/insight.py`, `backend/domain/insight.py` (the API layer reaches it only through `repos.insight`). |
| No `ask_*` object anywhere | **PASS** | Repo-wide search for `ask_conversation|ask_message|ask_insight|ask_session|ask_query|ask_tool` in Python/SQL/JS/TS returns **no object**; the only hit is the I1 migration test asserting the absence of `ask_conversations`/`ask_messages` in the DDL. |
| No accidental reuse of messaging tables/routes/FKs | **PASS** | See matrix item 13; route prefix is `/api/v3/insight`, distinct from the messaging routes. |

## 7. RLS / Authorization verification — exactly what was independently tested

Environment: the auditor's own disposable database `ct_i1_verify_20260921` (a template copy of the disposable `carbontally_test`, I1 objects dropped, **the repository migration applied verbatim by the auditor**; clean apply, exit 0; re-apply also clean → idempotent). Active role was switched with `SET LOCAL ROLE authenticated` and the caller was simulated through `SET LOCAL request.jwt.claims = '{"sub": "<uuid>"}'`, which is the exact mechanism `auth.uid()` reads (the function definition was read from the database).

Seeded: organisation A, organisation B, principal U1 (A, owner), principal U2 (A, member), principal U3 (B, owner); conversations A1 (creator U1), A2 (creator U2) in A, and B1 (creator U3) in B; one message in A1.

**35 of 35 expected outcomes reproduced** (`/tmp/i1_rls_verify.sh` output). The material results:

| Test | Expected | Observed |
|---|---|---|
| U1 creates a conversation in its own organisation | allowed | allowed |
| U1 creates a conversation in the **other** organisation | denied | denied (RLS: `new row violates row-level security policy`) |
| U1 inserts a row claiming `created_by = U2` | denied | denied |
| U1 duplicates an existing conversation id | denied | denied |
| U1 sees only its own conversation among the three seeded rows | 1 | 1 |
| U2 (same org) sees only its own, not U1's | 1 | 1 |
| U3 (other org) sees only its own | 1 | 1 |
| U2 reads U1's conversation **by its exact id** | 0 rows | 0 rows |
| U3 reads U1's conversation by its exact id (cross-org) | 0 rows | 0 rows |
| U1 reads its own conversation by id | 1 | 1 |
| U1 reads its own conversation's messages | 1 | 1 |
| U2 reads U1's conversation's **messages** (same org) | 0 rows | 0 rows |
| U3 reads U1's conversation's messages (cross-org) | 0 rows | 0 rows |
| U1's unfiltered scan of `…_messages` | only its own 1 | 1 |
| U2 appends a message to U1's conversation | denied | denied |
| U3 appends a message to U1's conversation (cross-org) | denied | denied |
| U1 appends to its own conversation | allowed | allowed |
| U1 inserts a message whose `organization_id` contradicts the conversation | denied | denied |
| U1 forges `created_by = U2` on a message | denied | denied |
| U1 UPDATEs its own conversation title | denied | denied (no privilege) |
| U1 DELETEs its own conversation / a message | denied | denied (no privilege) |
| `anon` SELECT/INSERT on either table | denied | denied (no privilege) |
| `service_role` | bypasses RLS by design | sees all rows — see F-05 |
| 9 constraint probes (duplicate ordinal, ordinal 0, bad role, empty content, author-less user message, missing conversation FK, org/conversation mismatch, null org, null creator) | all rejected | all rejected |
| Deleting a conversation | cascades its messages | 3 → 0 messages |

**Conclusion:** organisation isolation and creator-private visibility are enforced **in the database independently of the application**, and message access cannot bypass conversation ownership. Policy conditions correspond to the application's authorization model (`is_org_member` = active membership of an active org; creator predicate = the application's creator check), and the `authenticated` grants do not undermine the boundary (no UPDATE/DELETE, no TRUNCATE, `anon` fully revoked).

## 8. I2–I8 scope leakage

**No unauthorised later-stage implementation was found.** Searched across `backend/`, `frontend/src/`, `admin/src/` and `supabase/`:

| Stage | Artefact searched | Result |
|---|---|---|
| I2 | shared/owner-admin visibility, authorization matrix, consultant/auditor/PE access | **none** — the only matches inside I1 modules are prose stating that staff visibility is deferred |
| I3 | tools, tool registry, intent classification, data tools | **none** |
| I4 | AI interaction records, canonical AI audit events, model/provider attribution | **none** — the only matches are prohibition comments |
| I5 | context/memory layer | **none** |
| I6 | Insight frontend | **none** — the single "insight" string in `frontend/src` + `admin/src` is the word "insights" in an admin Analytics subtitle |
| I7 | retention, deletion, export, privacy controls | **none** — `InsightRepository.delete()` explicitly refuses |
| I8 | billing/allowance, provider hardening | **none in I1** — the only "allowance" hits are pre-existing document-processing billing code (`api/v3_billing.py`, `services/billing.py`, `api/v3_commercial.py`) untouched by `5633798` |
| Other | RAG, LangChain, embeddings, vector store, LLM/provider calls, `ask_*` routes, report-lifecycle changes, dependency/config/deployment changes | **none** |
| — | `public.ai_content_history` | **untouched** — not created, altered, deleted, migrated or referenced by I1; the only I1 mention is the migration's explicit non-scope comment. Its disposition remains a later D2/I3–I4 decision (as the brief requires). |

## 9. Database / environment boundary

| Environment | I1 migration present? | How established |
|---|---|---|
| **Repository (Git)** | Yes — `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql`, the **latest** migration in the tree | file read + `test_i1_migration_is_the_latest_migration` |
| **Auditor's disposable clone** `ct_i1_verify_20260921` | Yes — applied by the auditor from the repository file (clean, idempotent) | `psql -f`, `information_schema` = 2 tables |
| **Disposable `carbontally_test`** | Yes — pre-applied by the implementing agent (2 tables) | `information_schema` (read-only) |
| **Demo Lab** `carbontally_demo_local` | **ABSENT** — 0 tables | `information_schema` (read-only) |
| **QA** `carbontally_qa_phase8` | **ABSENT** — 0 tables | `information_schema` (read-only) |
| **Reference/production-style DB** `postgres` | **ABSENT** — 0 tables | `information_schema` (read-only) |

**I1 is therefore correctly described as "implemented in the repository, present in disposable test databases only, and not deployed to Demo Lab, QA or production."** The existence of the migration in Git is not evidence that I1 is live anywhere, and no persistent environment was migrated by this verification.

## 10. Tests independently executed

| Suite | Command (abbreviated) | Result |
|---|---|---|
| I1 API behaviour (8) + I1 migration contract (9) | `pytest tests/unit/api/test_v3_insight_endpoints.py tests/unit/data/test_i1_insight_migration.py -q` | **17 passed**, exit 0 — independently reproduces the implementing agent's "17 passed" (the suite is 9 DDL-contract + 8 API-behaviour tests) |
| Full unit suite at HEAD `5bd5e29` | `pytest tests/unit -q --junitxml=…` | **2,808 tests: 4 failed, 0 errors, 3 skipped** (250 s) |
| Full unit suite at pre-I1 `e48ee55` | same, in a `/tmp` clone checked out at `5633798^` | **2,791 tests: 4 failed, 0 errors, 3 skipped** (246 s) |
| Delta attributable to I1 | — | **+17 tests, +0 failures** |

The 4 failures are **identical at both commits** and are therefore pre-existing, not introduced by I1 (list in §12). The I1 migration is the newest migration, yet `test_migration_ordering_is_unchanged` fails both before and after it — I1 did not cause it. No test was fixed.

**Limitation of the repository's own I1 tests (recorded, not a defect):** the migration contract suite asserts **DDL text** (substring matching of the SQL file), not live schema behaviour; the API suite runs the real router with an **in-memory repository double** that mirrors the real SQL's scoping semantics. Neither exercises PostgreSQL, so neither would detect an RLS predicate error or a broken repository query. This verification closed that gap with §5 probes 3–8.

## 11. Evidence index (artefacts outside the repository)

| Evidence | Location |
|---|---|
| Migration applied verbatim + idempotency log | `/tmp/reapply.log` (I1 clone) |
| 35-case RLS/constraint matrix output | `/tmp/i1_rls_results.txt`, harness `/tmp/i1_rls_verify.sh` |
| Real-repository probe output (19 pass / 1 fail) | `/tmp/i1_repo_results.txt`, probe `/tmp/i1_repo_probe.py` |
| Principal/authorization probe output | `/tmp/i1_principal_results.txt`, probe `/tmp/i1_principal_probe.py` |
| Naming/leakage/follow-up searches | `/tmp/i1_search_results.txt`, `/tmp/i1_followup_results.txt` |
| Unit-suite JUnit XML (HEAD and pre-I1) | `/tmp/head.xml`, `/tmp/prei1.xml` |
| Root-cause demonstration (`coalesce($1,$2)` resolves to `text`) | live `PREPARE`/`pg_prepared_statements` output in this session; reproduced by F-02 |

## 12. Failures and limitations

**Pre-existing test failures (identical at `e48ee55` and `5bd5e29` — not caused by I1, not fixed):**

1. `tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered`
2. `tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered`
3. `tests/unit/api/test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained`
4. `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`

**Limitations of this verification:**

1. **No live end-to-end HTTP test with real authentication.** The backend was not running and authentication depends on the Supabase/GoTrue stack. API behaviour was verified by mounting the **real router** with real dependency injection (the same technique the I1 suite uses) rather than over HTTP against a running server; the data/RLS layers were verified live against PostgreSQL. A true end-to-end run against a running backend with real JWTs remains outstanding for a later stage.
2. **The RLS verification used the auditor's own disposable database**, built from the repository DDL, not Demo Lab/QA/production (which correctly do not carry the migration).
3. **The implementing agent's own RLS claim** ("applied and RLS-verified on the disposable `carbontally_test` clone") is *not* relied on: the RLS conclusions above come from the auditor's freshly created clone.
4. Field-level schema was judged against D2 §7.5 (see §13) — not against a prescribed field list, because none is ratified.

## 13. Field-level schema judgement (D2 §7.5)

D2 deliberately defers the exact shape of Layer 1, so the absence of a prescribed field list is **not** a defect. Judging only whether the chosen fields are the minimum technically necessary without introducing unratified product semantics:

| Field | Judgement |
|---|---|
| `id`, `organization_id`, `created_by`, `created_at`, `updated_at` | Required — identity, tenancy, creator-private principal and persistence timestamps. `organization_id` is required by §9.3/§9.6; `created_by` is required by §9.2. |
| `title` (nullable) | Acceptable technical label for listing. Not a product decision; no status semantics. |
| `role` with values `user` / `insight` | Author-kind, defensible as the minimum needed to represent a persisted message (`insight` is unused in I1 — no LLM exists). It is **not** answer status, which §11.6 defers; the migration comment says so explicitly. One consequence is recorded as F-03. |
| `content` | Required. |
| `ordinal` (1-based, unique per conversation) | Required to satisfy the ordering/retrieval aspect of §24.2; no product semantics. |
| No status/retention/billing/AI-interaction/model-provider columns | Correct — those belong to §11.6/I3/I4/I7/I8. |

**No field introduces a substantive product decision unsupported by D2.** One item is worth PO attention: `updated_at` exists (and is touched by `add_message`) but there is no UPDATE surface in I1, so it is currently a write-only-on-insert-plus-touch field. This is a technical observation, not a defect.

## 14. Findings

Ordered by significance. None of the three is a *ratified I1 requirement* failure; the materiality reasoning is stated so the PO can disagree.

### F-01 — Internal-staff identity widens the organisation scope of the Insight surface (deviation requiring PO disposition)

* **Observed (live, by mounting the real router):** a principal that is **both** CarbonTally internal staff (`is_staff=True`, `entity_id IS NULL`) **and** an active organisation member passes `require_org_member()` and then `ensure_org_access()`'s internal-staff early return, so it may act on **any** organisation: `GET /conversations?organization_id=<other org>` → **200**, `POST /conversations` naming another organisation → **201**, and the row was confirmed written with the other organisation's id.
* **Bounded by:** the creator-private predicate. That principal can read only conversations it created; a same-org member reading the staff principal's conversation receives **404** (verified). No customer's conversation content is exposed to staff, and nothing is misattributed to a customer user (`created_by` is always the caller).
* **Control cases (also live):** an ordinary org member → own org 200, other org **403**; internal staff **without** org membership → **403** everywhere; Processing Entity staff → **403** everywhere (the D20 entity-staff denial works).
* **Why it matters:** D2 §9.1 ratifies the first surface as the **customer user** in the customer workspace, and §10.2 states staff support access to customer Insight conversations is **DEFERRED** and "must be an explicit, named capability, not a by-product of staff identity". This org-scope widening *is* a by-product of staff identity on a new surface. It is inherited platform behaviour (the D20 any-org rule is ratified elsewhere), and D2 does not address D20 for Insight.
* **Recorded, not fixed** (D2 §24.4: a requirement belonging to I2–I8 is recorded, not implemented). **PO disposition required:** confirm that the platform-wide internal-staff rule is intended to apply to the Insight surface, or restate the §10.2 boundary as an explicit denial for Insight endpoints.
* **Test coverage:** the I1 suite contains **no** staff-principal test, so this behaviour is untested by the implementation's own suite.

### F-02 — `InsightRepository.save()` cannot execute (defect; no caller)

* **Observed (live, real code):** `await repo.save(conversation)` raises `asyncpg.exceptions.DatatypeMismatchError: column "created_at" is of type timestamp with time zone but expression is of type text`.
* **Root cause (independently demonstrated at SQL level):** the statement uses `coalesce($5, $6)` for `created_at`/`updated_at`. PostgreSQL resolves `coalesce(param, param)` on untyped parameters to **`text`** (shown by `PREPARE … SELECT coalesce($1,$2)` → `parameter_types = {text,text}`), and the resulting text expression cannot be assigned to `timestamptz`. The same failure occurs when the exact INSERT is prepared directly, with no Python involved.
* **Impact:** currently **nil at runtime** — `save()` has **no caller** anywhere in the repository (verified by search), the five I1 routes use only the explicit I1 methods, and `AbstractRepository.save()` is not exercised by the I1 test suite. It is a genuine defect in delivered I1 code: any future caller of the generic repository contract would fail at runtime. `delete()` and `get()` are unaffected in their declared behaviour.
* **Secondary observation:** `save()` is also the only *unscoped write* path (insert-or-update by `id` with no organisation argument); it should not be wired to a request path without org/creator scoping (see F-04).
* **Recorded, not fixed** (read-only verification). Suggested fix for the PO/engineering: cast inside the expression (`coalesce($5, $6::timestamptz)`) or pass one resolved timestamp — to be taken as an I1 remediation decision, not as an implementation by this verification.

### F-03 — RLS does not constrain message author-kind: a client can fabricate `role='insight'` rows

* **Observed (live):** under `SET LOCAL ROLE authenticated` (i.e. the Supabase/PostgREST client path), U1 successfully inserted a message into **its own** conversation with `role='insight'`. The `GRANT SELECT, INSERT … TO authenticated` plus the INSERT policy allow it; only the FastAPI layer refuses it (422).
* **Bounded by:** the same creator-private and organisation predicates — the fabricated row must be in the caller's own conversation, in the caller's own organisation, and `created_by` must be the caller. No cross-tenant or cross-principal effect.
* **Why it matters:** D2 §6.3 assigns the system actor semantics to the Insight side, and D2 §8.7 (D-11) makes authorization a server-side, deny-by-default concern; the database is the last line. Today I1 has no LLM, so the practical impact is limited to rows that are indistinguishable from a future system-authored message. Before I3/I4 depend on author-kind (or on an answer-state vocabulary that §11.6 defers), the boundary should be closed at the policy level (e.g. restrict client INSERT to `role = 'user'`, or constrain the column), so the API check is not the only enforcement.
* **Recorded, not fixed.**

### Observations (informational)

* **F-04** — `AbstractRepository.get(id)` reads a conversation **without** organisation scoping (verified live). It is documented in-code as internal/service-only and **has no caller**; and the API's only conversation read (`get_conversation`) is org-scoped. Together with F-02, the generic contract surface is not tenant-scoped and should either remain unused or be made explicitly internal before I3/I4 build tools on it.
* **F-05** — The backend writes with `service_role`, which **bypasses RLS by design** (confirmed live: `service_role` sees every organisation's rows). This is the platform-wide pattern and not an I1 deviation, but it means **code-level scoping is the only boundary on the backend path** — verified correct for every I1 read (org scope in SQL; creator predicate in the API). Any future Insight tool (I3) must reuse this repository's scoping rather than issuing raw SQL; this is the single most important invariant to carry forward.
* **F-06** — The repository's I1 test suite is fake-repo API tests plus DDL-text assertions (see §10). It has no live-schema RLS test, no repository-against-database test and no staff-principal test. The durable suite would be materially stronger with a live RLS test in the disposable-database harness; this verification supplied one ad hoc, but ad hoc evidence is not durable regression protection.
* **F-07** — Consistency with the implementing agent's report: the report's "17 passed" and its pre-existing-failure list are **independently reproduced**; its claims that the migration is disposable-environment-only and that `get()` is unused are **confirmed**; its statement that "I1 grants no staff exception — every principal, including CarbonTally staff, is creator-scoped" is **true at the conversation level** but should be read together with F-01 (staff retain the organisation-scope bypass). The report makes **no claim** that `save()` executes, so F-02 is new information rather than a contradiction.

## 15. Verdict

> ## **PASS**

**Rule applied (from the brief):** PASS requires all ratified I1 requirements to be independently verified with sufficient evidence, with **no material I1 defect and no unauthorised scope leakage**.

**Why PASS:**

* All thirteen I1 scope items (§24.2/§24.5/§24.6, including the three the brief emphasises — explicit RLS posture, organisation scoping, and creator-private visibility that must be enforceable) were verified with **live** evidence, not by reading claims: the migration was applied by the auditor to a fresh disposable database and probed in 35 behavioural cases, the real repository was driven against PostgreSQL, and the real router was mounted with principal shapes the I1 suite omits.
* The two binding security properties hold **in two independent layers**: organisation scope is enforced in the database (RLS) *and* in SQL; creator-private visibility is enforced in the database *and* in the API with 404 no-disclosure semantics. Possession of a conversation id confers nothing (live-proved for a same-org non-creator, a cross-org principal, and across message reads and writes).
* No unauthorised I2–I8 implementation, no human-messaging coupling, no `ask_*` naming, and no change to `public.ai_content_history` was found; I1's footprint is 9 files and 1,244 added lines, with no frontend, configuration or deployment changes.
* No new test failures were introduced (full unit suite delta: +17 tests, +0 failures).

**Materiality test applied to the findings:** F-02 has **zero runtime impact** because the method has no caller and no route, schema or deployed behaviour depends on it — it is a defect in a delivered class, not a failure of an I1 requirement or of the ratified persistence behaviour. F-01 exposes **no** conversation content across principals or tenants, does not misattribute content to a customer, and stems from a ratified platform-wide rule (D20) that D2 did not restate for Insight; it is a boundary question for the PO, not a demonstrated failure of an I1 requirement. F-03 requires a direct client-side (PostgREST) write of a row that remains inside the caller's own conversation and organisation, and only the reserved author-kind value is unenforced; the API denies it. On that reasoning the PASS bar is met.

**Explicit scope of this verdict — in the brief's own terms:**

* This verdict covers **only** the ratified I1 persistence foundation.
* **I1 IS NOT CLOSED.** Closure is a PO action and requires the PO to disposition F-01, F-02 and F-03 (and note F-04–F-06).
* **I2 IS NOT AUTHORISED**, and no later stage is authorised, evaluated or progressed by this report.
* If the PO reads D2 §10.2 as binding at the organisation-scope level for this surface, **F-01 should be treated as a scope deviation requiring remediation before I2 is considered** — the auditor's PASS does not pre-empt that reading.

## 16. Closure boundary — exactly what remains for PO closure

1. **Disposition F-01** (internal-staff organisation-scope reach on the Insight surface): confirm D20's any-org rule applies to Insight, or restate §10.2 as an explicit denial for Insight routes.
2. **Disposition F-02** (`InsightRepository.save()` defect): remediate (or consciously remove/retire the method from the contract) in an authorised I1 remediation step; do not leave it as latent breakage for a future caller.
3. **Disposition F-03** (author-kind not enforced at the policy level): decide whether the client INSERT path must be constrained to `role='user'` before I3/I4 depend on author-kind.
4. **Accept F-04/F-05 as carry-forward invariants** for I3 tooling (repository-level scoping must be reused; `get()`/`save()` are not tenant-scoped).
5. **Accept F-06** and add a durable live-schema RLS test plus a staff-principal test to the repository suite (currently the only live RLS evidence is the auditor's ad hoc probe recorded in §7).
6. **Deployment decision (outside this brief):** decide when/whether the migration is applied to Demo Lab, QA or production. As of this verification it is applied **nowhere persistent**, and this report makes no claim that I1 is live.
7. **Authorise I2 separately** (D2 §24.4) — nothing in this verification authorises it.

---

*Verification performed read-only. No application code, migration, schema, configuration, test, fixture, deployment environment or production data was modified; no defect was fixed; no persistent database was migrated; `public.ai_content_history` was left untouched; no other repository was modified. The only repository change is this report.*
