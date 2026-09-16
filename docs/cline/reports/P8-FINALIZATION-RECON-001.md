# P8-FINALIZATION-RECON-001 — FINALIZATION MASTER RECONNAISSANCE

**Task ID:** `P8-FINALIZATION-RECON-001`
**Type:** READ-ONLY reconnaissance and decision preparation. **No implementation authorization.**
**Timestamp (report written):** `2026-09-16T07:04:41Z`
**Authoritative worktree:** `/home/shomonrobie/carbon_tally_p8_release`
**Executor:** Cline (implementation/forensics agent)
**Production:** **NOT contacted, NOT queried, NOT modified.** No production credential was used.

> Environment note: the local sandbox wall clock and the repository commit timeline differ. Every
> claim below is pinned to a **commit SHA**, a **file + line**, or a **read-only SQL result**, not to
> elapsed time.

---

## 1. Task ID

`P8-FINALIZATION-RECON-001` — finalization master reconnaissance for the remaining Phase 8 items:
`P8-FIN-02/D-7`, `FIN-01c`, `FIN-05`, `FIN-06`, `D-4`, `D-11`, `D-14`, `D-15`, `D-16`, `D-17`,
migration drift prevention.

Scope discipline: this report determines **what is implemented, what is merely documented, what is
unresolved, what needs a PO decision, and what verification each item requires**. It authorizes
nothing.

---

## 2. Timestamp

`2026-09-16T07:04:41Z` (UTC, sandbox clock). All repository and database evidence was gathered in
this session from the release checkout identified below.

---

## 3. Exact release HEAD

| Item | Value |
|---|---|
| Worktree | `/home/shomonrobie/carbon_tally_p8_release` |
| Branch | `p8-release-reconciled` |
| **HEAD (release commit)** | **`2a34557fa14c9e96166d7287565ad7cf33337e0b`** |
| Parent | `2f56562ad797c5c2f1b73da7380e45199584e016` (published `origin/main` tip) |
| **Tree SHA** | **`59c9a25798d6d49145b9b6927ebcf77532f25f3f`** |
| Remote `refs/heads/p8-release-reconciled` | `2a34557fa14c9e96166d7287565ad7cf33337e0b` (matches HEAD) |
| Remote `refs/heads/main` | `2f56562ad797c5c2f1b73da7380e45199584e016` (unchanged; equals the release commit's parent) |
| History | `2a34557 → 2f56562 → 1db97ba (RLS-4B) → ae5d3bd (B2 provenance) → …` — published history **plus exactly one** evidence commit |

**Divergence note (structural, not a defect):** this checkout is a **single-branch clone**
(`remote.origin.fetch` = `+refs/heads/p8-release-reconciled:refs/remotes/origin/p8-release-reconciled`),
so `origin/main` is **not** a resolvable local ref here. It was verified two ways instead:
(a) `git ls-remote origin refs/heads/main` → `2f56562…`; (b) blob-SHA comparison of the release
tree's backend files against the published `origin/main` tree → **identical** (see §5.3).

---

## 4. Repository cleanliness verification

| Check | Result |
|---|---|
| `git status --porcelain` | **0 lines — pristine** |
| Staged | none |
| Untracked | none (the clone carries only tracked release content) |
| Local-only material from the previous worktree | **absent by construction**; the old worktree was not opened or modified |
| Local dev env files | `.env`, `.env.local`, `.env.test` copied during provisioning (git-ignored → status stays clean); `.env.production` and demo-credential files deliberately **not** copied |

---

## 5. Current-state findings

### 5.1 Release tree contents (verified in this checkout)

| Item | Result |
|---|---|
| Migration files | **69** |
| `20260925000000_p8_rls_4b_group1_enablement.sql` (RLS-4B) | present |
| B2 evidence-line provenance | present: `backend/data/evidence_line_items.py`, `backend/api/v3_disclosure.py`, `backend/data/disclosure.py`, `backend/domain/disclosure.py`, `calculation_snapshots.source_line_item_id` handling in `backend/data/emissions_logs.py` |
| Report / frozen-artefact stack | present: `backend/domain/report_artefact.py`, `backend/services/report_artefact_storage.py`, `backend/domain/report_lifecycle.py` |
| FIN-01a (legacy OnboardingWizard retired) + FIN-01b (org-member chat identity projection) | present, incl. `frontend/src/components/chat/__tests__/chat-identity.test.jsx` |
| N1 / server-side messaging API | present: `backend/api/v3_messaging.py` |
| Manual-processing containment | present: `backend/api/processing_mode.py` |
| Curated Phase 8 evidence | `docs/cline/reports` **60**, `docs/architecture` **276** (recursive), `docs/ohd/reports` **5**, plus `CARBONTALLY_AUDIT_FINDING_VERIFICATION.md` |
| Production planning records | migration-safety plan, backup architecture, RLS baseline spec, RLS hold register — all present |
| Test suites | **202** backend `test_*.py` files; **28** frontend test files |
| CI workflows | **none** (`.github/workflows` contains no workflow files) |
| Pre-commit configuration | **none** (`.pre-commit-config.yaml` absent) |

### 5.2 Database evidence used (read-only)

Local, non-production cluster `127.0.0.1:54426`; `SELECT`-only queries, no writes, no DDL:

| Database | Role in this reconnaissance |
|---|---|
| `postgres` (canonical local) | live schema / policy / privilege inspection |
| `ct_p8_rehearsal_20260915` | disposable clone built by the release migration chain (68 migrations at build time; RLS-4B not included), used to check bucket/privilege state |

> `.env` in the release tree still points at `127.0.0.1:54326`, which is not listening; the reachable
> cluster is `54426`. This is an environment fact, not an authorization.

### 5.3 Published-baseline comparison and contradictions (reported, not resolved)

| # | Finding | Source of truth |
|---|---|---|
| **C-1** | The RLS-4B migration header claims the legacy frontend writes non-existent columns `organizations.created_by`, `organization_members.joined_at`, `conversations.is_group`, **`messages.organization_id`**. Live schema: `conversations.is_group` **absent** ✓; `organizations.created_by` **absent** ✓; `organization_members.joined_at` **absent** ✓; **`messages.organization_id` PRESENT** ✗. | Current release schema (migrations + live DB) is authoritative; the migration **comment** is stale for `messages.organization_id`. Consequence: the legacy message insert fails for a *different* reason than the comment states (see §6.4). |
| **C-2** | Historical programme record describes production as "~97/104 tables RLS-**disabled**, `anon` `GRANT ALL`". The release tree's `00000000000000_init_schema.sql` contains an **"RLS ENABLEMENT (All tables)"** loop (~line 2320) that enables RLS on every `public` table. Schema-as-migrated is therefore RLS-**enabled** with **zero policies** on reference/legacy tables (`emission_factors`, `beta_users`, `beta_access_codes`, `waitlist`) → fail-closed for client roles. | Live local DBs corroborate the migration (`emission_factors rls=true, policies=0`). **Production remains UNVERIFIED**; the historical measurement may reflect out-of-band production state. This is precisely what **D-15** must settle. |
| **C-3** | The release tree has **no CI at all** (no `.github/workflows` entries), whereas an earlier worktree carried `playwright.yml`. | Release tree is authoritative for the release; the drift-gate baseline is therefore "no gate exists" (§16). |

---

## 6. D-7 findings — chat participant-write path (`P8-FIN-02`)

### 6.1 Frontend trace

| Question | Finding |
|---|---|
| Which UI initiates it | The **legacy chat widget** `frontend/src/components/chat/ChatWidget.jsx`, mounted from the legacy shell `frontend/src/App.js` (~lines 1651, 1847). The "start a conversation with support" flow is `handleStartConversation(staffId)` at `ChatWidget.jsx:212-294`. |
| Where conversations are created | `ChatWidget.jsx:250-260` — direct browser insert into `conversations` with `organization_id`, `created_by`, **`is_group`**, `created_at`, `updated_at`. |
| Where participants are inserted | `ChatWidget.jsx:265-280` — direct browser insert into `conversation_participants`: two rows (`conversation_id`, `user_id`, `joined_at`, `is_active`) for the current user and the selected staff user. |
| Participant update/delete | `conversation_participants` is **read** at `ChatWidget.jsx:41,218,229` and `ChatWindow.jsx:109,214`; no browser update/delete of participants exists. |
| Messages | `ChatWindow.jsx:238-241` inserts `messages` (`conversation_id`, `sender_id`, `receiver_id`, `content`, `is_read`, `created_at`) — **no `organization_id`**; read-marking updates at `ChatWidget.jsx:319`, `ChatWindow.jsx:91,146`; `conversations.updated_at` touch at `ChatWindow.jsx:246-249`. |
| Is `is_group` still written? | **Yes — `ChatWidget.jsx:255`. The column does not exist** → the conversation insert fails before participants are attempted. |
| Does the target directory depend on FIN-01c? | **Yes.** The counterparty list comes from `ChatWidget.jsx:198-201`, a direct `users` peer read (`id,email,full_name,avatar_url,raw_user_meta_data … raw_user_meta_data->>is_staff='true'`) — the **single remaining direct `users` read in the entire frontend** and the FIN-01c subject (§11). |

### 6.2 Backend — existing N1 / server-side messaging API

`backend/api/v3_messaging.py`, prefix `/api/v3/messaging`:

| Endpoint | Authorization |
|---|---|
| `POST /conversations` | `_authorize_org_actor` → `org_member` \| `consultant` (ACTIVE grant) \| `staff` (internal, `entity_id IS NULL`, `can_manage_staff`) else **403** |
| `GET /conversations?organization_id=` | same gate |
| `GET /conversations/{id}/messages` | conversation's org + same gate |
| `POST /conversations/{id}/messages` | same gate; persists with the conversation's `organization_id` |
| `POST /conversations/{id}/read` | same gate |
| `GET/POST /entity-conversations`, `…/messages`, `…/read` | `_resolve_entity_actor` → active PE member or internal ops with `can_manage_staff`; PE↔customer is impossible by construction |

*Models:* `ConversationCreate{organization_id, subject(≤300)}`, `MessageSend{content(≤20000)}`, both `extra="forbid"`.
*Participant creation behaviour:* `create_conversation` inserts the conversation and adds **only the creator** (`add_participant(..., metadata={"participant_role": role})`). **No endpoint or parameter adds a counterparty participant.**
*Repository behaviour* (`backend/data/messaging.py`): `create_conversation` inserts `(organization_id, subject, status='open', created_by, created_at, updated_at)` — **schema-aligned, no `is_group`**; `add_participant` inserts `(conversation_id, user_id, is_active, metadata, created_at, updated_at)` with `ON CONFLICT (conversation_id,user_id) DO UPDATE`; `send_message` inserts `(conversation_id, sender_id, organization_id, content, is_read)` — **supplies `organization_id`**; all writes use the **service role** (RLS-bypassing, server-authorized).
*Audit:* entity (PE) conversations write `pe_msg:conversation_created` / `pe_msg:message_sent` through `repos.audit.record`. **Org/customer/consultant support conversations write no audit entry today.**
*Error handling:* explicit 403 (`_authorize_org_actor`), 404 (unknown/entity-less conversation), 422 (invalid entity context), 409 (closed conversation).

### 6.3 Database / RLS — live evidence (read-only)

| Table | Relevant columns | Policies present | Missing |
|---|---|---|---|
| `conversations` | id, organization_id, staff_id, customer_id, subject, status, last_message_at, **created_by**, closed_by/at, is_urgent, priority, created_at/updated_at, read_by, unread_count, participant_count, conversation_kind (NOT NULL, default `'org'`), processing_entity_id, context. **No `is_group`.** | SELECT (`is_org_member OR is_org_consultant`), SELECT (entity), **INSERT** (`WITH CHECK is_org_member(organization_id)`), UPDATE, DELETE | — |
| `conversation_participants` | id, conversation_id, user_id, joined_at, last_read_at, is_active, metadata, created_at, updated_at | SELECT (`can_view_conversation_participants`), SELECT (entity), UPDATE (`USING is_conversation_participant` / `WITH CHECK user_id = auth.uid()`) | **NO INSERT policy, NO DELETE policy** |
| `messages` | id, conversation_id, sender_id, receiver_id, **organization_id**, subject, content, is_read, …, created_at/updated_at | SELECT (tenant/entity), **INSERT** (`WITH CHECK is_org_member(organization_id)`), UPDATE, DELETE | — |
| Triggers | only `trg_set_updated_at_*` on all three tables | — | **no trigger populates `messages.organization_id`** |
| Grants | `authenticated` holds SELECT/INSERT/UPDATE/DELETE on all three; `anon` holds **no** INSERT on `conversations` | — | — |
| Policy origin | `supabase/migrations/20260822010000_d27_d19_customer_lifecycle.sql` | — | — |

### 6.4 Explicit verification: are browser-side participant writes authorized?

**No.** Three independent, individually sufficient blockers exist in the release tree:

1. The browser `conversations` insert sends **`is_group`, which does not exist** → rejected (unknown column) before any RLS evaluation.
2. Even if (1) were removed, `conversation_participants` has **no INSERT policy** while RLS is enabled → the participant insert is **deny-all** for `authenticated`.
3. `ChatWindow`'s `messages` insert omits `organization_id`; `messages_tenant_insert` requires `is_org_member(organization_id)` on the new row, and `messages.organization_id` is nullable with **no populating trigger** → evaluation against `NULL` **denies** the insert. (This refines C-1: the column exists; the UI simply never supplies it.)

The legacy chat write path is therefore **non-functional end-to-end**, independently of FIN-01c.

### 6.5 Decision preparation — two architectural choices (neither selected)

**Option A — repair browser-side writes**

| Aspect | Detail |
|---|---|
| Schema alignment | Remove/replace `is_group` in `ChatWidget`; supply `organization_id` (or add a `BEFORE INSERT` trigger) for `messages`. |
| Required RLS policies | New `conversation_participants` INSERT policy with a participant-scoped `WITH CHECK` (self-insert for `auth.uid()`, and/or org-scoped addition of others); a DELETE policy if participant removal is a supported action. |
| Required grants | None — `authenticated` already holds INSERT; but those grants become **live**, so the effective client-write surface expands. |
| Security implications | A mis-scoped `WITH CHECK` would permit **adding arbitrary users to arbitrary conversations** (cross-tenant/cross-role). Requires negative tests: stranger-add, cross-tenant add, PE add, viewer-add. Business rules would live in the client. |

**Option B — route participant creation through the existing server-side N1 API**

| Aspect | Detail |
|---|---|
| Required frontend changes | Replace the three direct Supabase writes (`ChatWidget` conversation + participants, `ChatWindow` messages) with the existing `/api/v3/messaging/*` client calls (`frontend/src/v3/api.js` ~1164-1186) and keep Realtime subscription for live updates. |
| Is existing server authorization sufficient? | **Yes in substance** — `_authorize_org_actor` already covers org members, active-grant consultants and authorised internal staff, and excludes PE. |
| Are API changes required? | **Yes — one bounded gap.** `POST /conversations` cannot name a counterparty. Either (a) add an optional `participant_user_id`/counterparty field to `ConversationCreate`, validated server-side against the org/invitee policy, or (b) add a bounded `POST /conversations/{id}/participants` reusing `add_participant`. **No schema change and no RLS expansion is required.** |
| Additional gap to close | Org/support conversations currently write **no audit entry** (entity conversations do); an audit hook should accompany the change. |
| Security implications | Writes remain service-role and server-validated; the browser gains **no** new write privilege; tenant scoping stays in one place. |

**Recommendation — labelled as a recommendation requiring explicit PO authorization (this is not an authorization):** **Option B.** The server-side path is already schema-aligned (no `is_group`), already authorized and tenant-scoped, satisfies the existing `messages` policy by supplying `organization_id`, and requires only a small, testable API addition plus an audit hook. Option A would require inventing new client-write policies on a table that currently has none — a larger security surface for the same functional result.

---

## 7. D-4 findings — `emission_factors` security posture

### 7.1 Complete usage trace

| Surface | Finding |
|---|---|
| Backend repository | `backend/data/emission_factors.py` — full server-side lifecycle: SELECT (~26, 270, 306), **INSERT** (~193, 283), **UPDATE** (~249), **DELETE** (~326). Used via `RepositoryBundle` (`backend/api/dependencies.py:42`). |
| Backend reporting/exports | `backend/data/exports.py:88` and `backend/data/reporting.py:1171` `LEFT JOIN public.emission_factors` for factor provenance in emissions/report output. |
| Backend engines | `backend/engines/validation.py` (factor-existence validation), `backend/engines/calculation.py:524`, `backend/engines/benchmarking.py`, `backend/core/units.py` (unit vocabulary), `backend/engines/report_generation.py` (read-only aggregation). |
| Legacy API route | `backend/routes/reference.py:61-63` — server-side read of `emission_factors.activity_type` for the reference vocabulary (the old `defra_conversion_factors` table no longer exists, PGRST205). |
| Admin control plane | `backend/routes/admin/defra.py` — admin CRUD over factors: `GET /factors`, `GET /factors/{id}`, `POST /factors`, `POST /factors/bulk`, `PUT /factors/{id}`, `DELETE /factors/{id}`, `GET /years`, `GET /activities`, `GET /validate` (admin app page `admin/src/pages/admin/DefraFactors.js`). |
| **Frontend / public website / admin client** | **ZERO direct references.** `grep -rn 'emission_factors' frontend/src admin/src` → **no matches**. No browser surface reads or writes the table. |
| Anonymous product surface | **None found.** No public/visitor page, no anon-key query, no Edge function reads factors client-side. |
| Service-role usage | Yes — the backend accesses it through the service client (`infra.supabase.get_service_client`), which **bypasses RLS**, so all legitimate access is service-role/API-mediated. |

### 7.2 Live security state (read-only, canonical local DB)

| Aspect | Value |
|---|---|
| RLS enabled | **true** (enabled by the generic "RLS ENABLEMENT (All tables)" loop in `00000000000000_init_schema.sql`, ~line 2320) |
| Policies | **0** → fail-closed for RLS-bound roles |
| `anon` privileges | `SELECT` **true**, `TRUNCATE` **true**, `REFERENCES`, `TRIGGER`; `INSERT` false |
| `authenticated` privileges | `INSERT` **true**, `UPDATE` **true**, `DELETE` **true**, plus non-DML (`TRUNCATE`/`REFERENCES`/`TRIGGER`/`MAINTAIN`) |
| Default privileges on `public` (as recorded by `20260922000000_p8_rls_4a2…`) | `{postgres=arwdDxtm, anon=Dxtm, authenticated=Dxtm, service_role=Dxtm}` — future tables inherit `Dxtm` for `anon`/`authenticated` |
| Migrations touching the table's privileges/RLS | **none** — three migrations explicitly **exclude** it: `20260920000000_p8_rls_anon_grant_containment.sql` (lines 13-14, 52, 70), `20260922000000_p8_rls_4a2_authenticated_grant_hardening.sql` (lines 41, 46), and RLS-4B (exclusion list) |

### 7.3 Assessment

* **No legitimate product surface requires anonymous access**, and **none requires authenticated *client* access** either: every consumer is server-side (API/service-role) or admin-plane.
* Because RLS is enabled with zero policies, anon/authenticated cannot actually read or write rows today; the residual exposure is the **privilege surface** itself (`anon` holding `TRUNCATE`/`REFERENCES`/`TRIGGER`; `authenticated` holding DML + non-DML on a table they can never legitimately touch), plus the **non-durable** default ACL that re-grants `Dxtm` to `anon` on future tables.
* `TRUNCATE` is **not** subject to RLS, so `anon` holding it is a genuine least-privilege defect even though it is not reachable through PostgREST.
* Production posture for this table is **UNVERIFIED** (see C-2).

### 7.4 Recommendation prepared for PO consideration (not adopted, not authorized)

> **`emission_factors` is internal / server-side reference data and must not be anonymously accessible;
> neither `anon` nor `authenticated` should hold any privilege on it.**

Basis: no client-side consumer exists anywhere in the release tree; all access is service-role
(RLS-bypassing) or admin-plane; RLS is already enabled with zero policies, so removing the privileges
removes the *only* remaining exposure. Nothing in the product breaks.

**Minimum bounded change set if this recommendation is adopted later** (one small, REVOKE-only migration
numbered **above `20260925000000`**, e.g. `20260926…_p8_rls_4b_d4_emission_factors_containment.sql`):

1. `REVOKE ALL ON TABLE public.emission_factors FROM anon;` (removes `SELECT`, `TRUNCATE`, `REFERENCES`, `TRIGGER`).
2. `REVOKE ALL ON TABLE public.emission_factors FROM authenticated;` followed, if desired for defence in
   depth, by an explicit `GRANT SELECT … TO authenticated` **plus** a read policy — or simply leave it
   fully revoked, since no client reads it.
3. `ALTER DEFAULT PRIVILEGES … REVOKE` parity for the same role/table class **only if** the default-ACL
   hardening migration (`20260923000000`) is not already in force; otherwise no change is required.
4. No `ENABLE`/`FORCE RLS` change (RLS is already enabled; `FORCE` remains deferred by RLS decision `D-11`).
5. No data change, no policy creation, no column, index or function change.

**Regression tests required to prove the intended posture** (to be added only under separate authorization):

| Test | Assertion |
|---|---|
| Privilege census | `has_table_privilege('anon','public.emission_factors', x) = false` for SELECT/INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER; same for `authenticated` per the ruling |
| Default-ACL durability | creating a scratch table in a transaction does **not** re-grant `Dxtm` to `anon`/`authenticated` (rollback afterwards) |
| RLS posture parity | `relrowsecurity = true`, `relforcerowsecurity = false` (unchanged), policy count unchanged |
| Functional non-regression | factor lookup/EF-E selection, emissions calculation, report provenance and admin factor CRUD still pass through the **service role** (API/runtime suites) |
| Negative isolation | anon-key PostgREST read of `emission_factors` returns no data/permission error |

---

## 8. D-11 findings — `report-artifacts` storage

### 8.1 Implementation trace

| Question | Finding |
|---|---|
| Expected bucket name | `report-artifacts` — single constant `backend/domain/report_artefact.py:24` (`ARTEFACT_BUCKET`); `ARTEFACT_CONTENT_TYPE = "application/pdf"` (line 27) |
| Migration / schema references | `supabase/migrations/20260919000000_p8_b4_frozen_artefact.sql` — table `report_version_artifacts`, `storage_bucket varchar(63) NOT NULL DEFAULT 'report-artifacts'`, `CHECK (storage_bucket = 'report-artifacts')`, append-only grants, RLS member-read / admin-insert |
| Object key format | Derived by CHECK from the row: `{organization_id}/{report_id}/{report_version_id}.pdf` (migration lines 69-71); the Python layer derives it too and never accepts it |
| Integrity requirement | `content_sha256 char(64)` constrained to lowercase hex SHA-256 (`~ '^[0-9a-f]{64}$'`), `byte_size > 0`; immutability via the append-only record + the version's `FINAL` state (PO `B4-D7`) |
| Append-only / immutability | `UNIQUE (report_version_id)`; UPDATE/DELETE are **not granted** to `authenticated` and no such policy exists |
| Backend adapter | `backend/services/report_artefact_storage.py` — `SupabaseReportArtefactStorage` (`storage.from_('report-artifacts')`, upload with `upsert=false`, `create_signed_url` TTL 300 s, `exists()` best-effort) plus `InMemoryReportArtefactStorage` for tests; `get_report_artefact_storage()` process-wide |
| Provider assumptions | Supabase Storage (private bucket), service-role client; no external storage path exists (forbidden by PO ruling) |
| Does the application create the bucket? | **No.** No `create_bucket`/`get_bucket`/`list_buckets` call anywhere in `backend/`. The migration itself states "No storage object is created by this migration." |
| Do tests use a mock? | **Yes** — `InMemoryReportArtefactStorage` is used by `backend/tests/integration/test_disclosure_b4_finalisation_runtime.py` and `backend/tests/unit/api/test_v3_disclosure_finalisation_api.py`; the real-storage path is therefore **not verified** |
| Does production code verify bucket existence? | **No.** `exists()` is implemented but not called anywhere; failure would surface only as an upload error at finalisation time |
| Is the bucket represented in configuration? | **No** — no reference in `.env*` templates, YAML, shell scripts or IaC (`grep` over the release tree: only the constant, the migration and docs) |
| Live bucket state | Canonical local DB **and** the rehearsal clone each contain **only** the `documents` bucket (private). **No `report-artifacts` bucket exists in any reachable environment.** |

### 8.2 Consequence

B4 finalisation is mandated to **fail** if the immutable PDF cannot be produced and stored, so in any
environment lacking the bucket the ratified finalisation path cannot complete. This is a genuine
functional gap, not documentation drift.

### 8.3 Two bounded options (neither selected)

**Option A — operational provisioning**

| Aspect | Assessment |
|---|---|
| Implementation impact | **No code or migration change.** A documented operator step: create a **private** bucket named `report-artifacts` in each environment (local QA/clone, staging, production) via the Supabase dashboard/CLI, with no public URL access. |
| Deployment impact | Must be completed **before** the first finalisation in any environment; must be part of the release runbook and environment checklist. Easy to forget → needs a checklist gate. |
| Security implications | Operator-controlled; private by default; must be created with `public = false` and no anon policy. Risk: human variance (name typo, accidental public flag) — the name is enforced by the schema CHECK, so a typo fails loudly at finalisation. |
| Repeatability | Manual, per environment; not reproducible from the repository; drift is possible and invisible until finalisation is attempted (no code verifies existence). |
| Verification required | Post-provision evidence: bucket exists, `public=false`, list of buckets; then one end-to-end finalisation on a disposable environment proving upload + SHA-256 row + signed-URL download works with the real adapter. |

**Option B — migration-managed provisioning**

| Aspect | Assessment |
|---|---|
| Implementation impact | One additive migration (numbered **above `20260925000000`**) that inserts the bucket row (`storage.buckets`, `public = false`) idempotently, plus optionally storage-object policies if the design requires them. |
| Deployment impact | Provisioning travels with the migration ledger → identical in every environment; cannot be forgotten; ordering must be respected (bucket before any finalisation). |
| Security implications | Bucket created with `public = false`, no anon grants, no public URL; deterministic and reviewable in one place. Requires the migration runner to have rights on the `storage` schema (Supabase service/owner role) — currently unproven in this environment. |
| Repeatability | Fully deterministic and idempotent (`INSERT … ON CONFLICT DO NOTHING`), reproducible from the repository. |
| Verification required | Migration `rc=0` twice; bucket present and private; **plus** the same real-adapter end-to-end finalisation test; plus evidence that the migration does not alter existing buckets/policies (`documents` unchanged). |

**Open question for the PO (not decided here):** whether CarbonTally's policy is that *runtime resources*
(buckets) may be created by migrations at all — the historical precedent (`documents` bucket) was
operational, while `20260823000000_d32_private_documents_storage.sql` only flipped `public = false` on an
already-provisioned bucket. Choosing B therefore also ratifies a new provisioning convention.

---

## 9. FIN-05 findings — beta / waitlist / pre-launch surfaces

### 9.1 Actual surfaces

| Layer | Finding |
|---|---|
| Database tables | `beta_access_codes`, `beta_users`, `waitlist` (all created in `00000000000000_init_schema.sql`, lines 375-419) |
| RLS / policies (live) | All three: **RLS enabled, 0 policies** → fail-closed for `anon`/`authenticated`; `anon` holds `SELECT`+`Dxtm`, `authenticated` holds DML grants |
| RLS-4B coverage | **Explicitly excluded** — `20260925000000_p8_rls_4b_group1_enablement.sql` lines 45-49 name "the legacy `beta_users` / `beta_access_codes` / `waitlist` flows" as non-scope |
| Row data (canonical local) | `beta_users` **0**, `beta_access_codes` **0**, `waitlist` **0** — nothing to preserve locally (production unknown) |
| Backend APIs | `backend/routes/admin/beta.py` — 10 endpoints (codes: list/create/update-status/delete/validate; users: list/create/update-access/delete/stats); `backend/routes/waitlist.py` — **stubs only** (`POST /` → `pass`, `GET /` → `pass`); the admin UI additionally calls `/api/waitlist/invite`, `/unsubscribe`, `/resubscribe`, which **do not exist anywhere in the backend** → 404 |
| Frontend surfaces | `frontend/src/BetaSignup.jsx` (direct Supabase reads/writes on `beta_access_codes`, `beta_users`, `waitlist`); `frontend/src/BetaLogin.jsx` (direct `beta_users` reads); `frontend/src/services/emailService.js` → `POST /api/waitlist` (stub) |
| Routes registered | **Yes, still live**: `frontend/src/App.js:1976-1977` → `/beta/signup`, `/beta-login`, listed among public paths (~line 1879) |
| Admin surface | `admin/src/pages/admin/BetaManagement.js`, routed at `/admin/beta-management` (`admin/src/App.js:76`) — reads `waitlist`/`beta_access_codes` client-side and calls the non-existent waitlist endpoints |
| Landing page | `frontend/src/LandingPage.jsx` — "Pre-launch commercial homepage. Replaces the beta/waitlist landing page." **No waitlist form.** `frontend/src/public/ContactPage.jsx` — "no signup or waitlist form". `AppHeader.jsx` — "No beta, waitlist or free-trial CTA." |
| Live dependency | **None functional.** Every write path is either RLS-denied (direct Supabase under zero policies), a stub (`pass`), or a non-existent backend route. No customer workflow can succeed through these surfaces today. |

**Dormancy verdict:** the database objects and the *public beta routes/components* still exist and remain
reachable, but the flows are **non-functional** — they are dormant-but-present, with dead backend calls in
the admin UI.

### 9.2 Two options (neither selected; the product decision is the PO's)

**Option A — retain temporarily**

| Aspect | Requirements if retained |
|---|---|
| Governance | Written decision record for *why* the surfaces remain, an owner and a review date; explicit acknowledgement that the flows are currently non-functional |
| Retention | Retention period for any retained rows, expressed through the N3 configurable-retention control plane or the PO's retention schedule — **do not invent a duration** |
| Grants / RLS | Either (a) leave fail-closed (RLS with zero policies) and accept dead surfaces, or (b) authorise a bounded policy/grant set that re-enables only the intended flows (a new security change with its own gate) |
| Data protection | `anonymise_user` already scrubs `beta_users.email` (`20260804000000_rc2_functions.sql:183`), so erasure remains covered |
| Verification | RLS/policy census, route inventory, and a test proving erasure/retention behaviour on these tables |

**Option B — retire**

| Aspect | Requirements if retired |
|---|---|
| Destructive? | The **rows** are the only irreplaceable part. Locally all three tables are **empty (0 rows)**; **production counts are UNVERIFIED**, so retirement must be preceded by a count and (if non-zero) an export/archive decision. |
| Migration / preservation decisions | (1) `DROP TABLE` (irreversible) vs revoke-and-keep (reversible); (2) archive production rows first?; (3) do historical beta records carry contractual/compliance weight (PO/legal)? |
| Code removal scope | `backend/routes/admin/beta.py` (+ registration), `backend/routes/waitlist.py` (+ `backend/routes/__init__.py`), `frontend/src/BetaSignup.jsx`, `frontend/src/BetaLogin.jsx`, the two `App.js` routes and the public-path entry, the `emailService.js` waitlist calls, `admin/src/pages/admin/BetaManagement.js` + its route, and the dead `/api/waitlist/invite|unsubscribe|resubscribe` callers |
| Sequencing | A destructive migration must **not** be bundled into the production catch-up window; it belongs in a later separately-authorized step after backup/PITR confirmation (D-16) |
| Verification | Route/component inventory after removal; API 404 behaviour; table/RLS census; `grep` gate proving no live references remain; test-suite update |

---

## 10. FIN-06 findings — Manual Processing Governance

> **The intended product direction is treated as a requirement to be represented, not as a legal claim.**
> Nothing here asserts that the UK Data (Use and Access) Act 2025 mandates this exact product
> configuration. The legal driver is context; the control surface below is a **product decision**.

### 10.1 Current implementation (verified)

| Aspect | Finding |
|---|---|
| Manual-processing API | `backend/api/v3_manual_extraction.py`, prefix `/api/v3/manual-extraction`: `POST /batches`, `GET /batches`, `GET /batches/{id}`, `POST /batches/{id}/items`, `GET /batches/{id}/items`, `PUT /items/{item_id}` — guarded by `require_org_member()` + `ensure_org_access(...)`. **No enablement gate exists: any organisation member (and internal staff via the documented bypass) can create and manage manual batches today.** |
| Workflow actions | `backend/api/v3_processing_workflow.py`: `/batches/{id}/start|complete|cancel`, `/items/{id}/start|extract|map|validate|consultant-review|consultant-submit|calculate|customer-review` |
| Consultant capability gate | `_STAGE_PERMISSION` (~line 90): `source\|extraction → extract`, `mapping → map`, `validation → validate`, `calculation → calculate`, `review → submit`, resolved via `backend/api/consultant_auth.py::CONSULTANT_PERMISSIONS` against real columns |
| Capability columns | `consultant_firm_members.can_extract / can_map / can_validate / can_calculate / can_confirm_automation / can_submit` — added by `20260906100000_p6_2a_consultant_processing_permissions.sql`, all **`NOT NULL DEFAULT false`** |
| **Who can grant them today** | **Nobody through the application.** `add_team_member` (`backend/api/v3_consultants.py`) deliberately creates members with **all `can_*` flags FALSE** ("no permission flag is grantable through this endpoint"); the only other writer is `set_firm_member_active` (`backend/data/consultants.py:334-354`), which flips `is_active` only. Consultant firms therefore **cannot self-enable processing capability**, and **CarbonTally admin cannot enable it either** — only direct SQL/service-role can. |
| Default posture | **Effectively OFF.** Additionally, manual work is forced through CT-QC before customer-facing actions (`backend/api/processing_mode.py`: `item_is_automatic` + `ensure_manual_ct_qc_prerequisite` → 403) |
| Automatic-processing interaction | `item_is_automatic` treats work as automatic only with a durable job **and** machine production evidence (`automation_extracted_data` or the zero-UUID `extracted_by`); everything else is **manual** (fail-closed). Canonical `processing_mode` (`automatic`/`manual`) is recorded write-once by `record_consultant_provenance` (`backend/data/manual_extraction.py:678-720`) |
| Organisation / consultant model | `organizations` (975 local rows), `consultant_profiles`, `consultant_firm_members` (54), `consultant_clients` (917; status vocabulary incl. `active`/`onboarding`/`inactive`) |
| Existing system settings | `system_settings(id, setting_key UNIQUE, setting_value JSONB, setting_type, description, is_editable, updated_by, updated_at, …)` — **2 rows locally**; **no enforcement code reads it**; used only by the legacy admin router `backend/routes/admin/settings.py` (`/api/admin/settings/*`), which validates a handful of keys and has no history table |
| Existing admin architecture | `admin/src/pages/admin/*` (Settings.js, DefraFactors.js, BetaManagement.js, Users.js, Organizations.js, …) + `backend/routes/admin/*` (settings, defra, staff, permissions, audit, logs, …); v3 admin surfaces in `backend/api/admin_*.py`. **No manual-processing governance page or endpoint exists.** |
| Audit logging | Infrastructure exists: `domain.audit.AuditEntry` + `repos.audit.record(...)`, already used by `v3_processing_workflow.py`, `v3_operations.py`, `v3_consultants.py` (firm-member mutations record the server-authoritative actor) and `v3_messaging.py` (PE paths). Append-only immutability is enforced by migrations `20260831020000` + `20260912000000`. |
| Entitlement / subscription | `backend/services/billing.py::ensure_processing_entitlement` and `charge_processing` read `customer_subscriptions`, which has **0 rows locally** (known entitlement gap) → billing is **not** a usable enablement lever today |
| Jobs / pipelines | `document_processing_queue` with durable `stage`, `locked_at`, `lock_token`, `attempt_count` and per-stage outputs (migration `20260829000000`, currently **pending in production**); worker/service in `backend/services/automatic_processing.py` |

### 10.2 Configuration-model analysis

| Requirement dimension | Can an existing structure represent it safely? | Notes |
|---|---|---|
| Default **OFF** | Yes (already true) | Capability flags default false; the manual API has no gate but is org-member scoped |
| Enablement by **CarbonTally Admin only** | **No existing mechanism** | Needs a new privileged control (endpoint + permission) and a data home; `system_settings` is the only generic config store and no enforcement code reads it |
| Scope: individual **Organisation** | Partly | `organizations` is the natural key; a scope row per organisation is representable |
| Scope: **Consultant** (firm) | Partly | `consultant_profiles` is the natural key |
| Scope: individual **Consultant Client** | Partly | `consultant_clients` row id is the natural key |
| Scope: **selected / all** consultant clients | Needs a model | "all clients of firm X" is derivable; "selected subset" needs either a per-grant row per client or an exclusion/override model |
| **Precedence** (org vs firm vs client) | **Needs an explicit rule** | With overlapping scopes the effective answer must be deterministic and documented (e.g. most-specific-wins vs any-grant-wins); the current code has no such resolution layer |
| Inheritance / overrides | Needs a rule | Firm-level grant inherited by clients vs per-client override |
| Relationship changes / revocation | Partly | `consultant_clients.status` lifecycle already exists; effective permission must be recomputed per request (no stale caching) |
| **Existing jobs** vs **new jobs** | Needs a rule | Items carry write-once `processing_mode` + provenance; batches have `status`; queue rows carry `stage`/`locked_at`. Whether disabling the capability blocks in-flight/manual batches mid-flight (or only new batches/items) is a PO rule |
| **Queued / in-progress** jobs | Needs a rule | Same as above; automatic queue is separate (`document_processing_queue`) |
| Auditability | Yes (infrastructure exists) | `AuditEntry`/`repos.audit.record` is already used for security-sensitive mutations and is append-only by migration |
| Cache invalidation | Needs a decision | If resolved per request from the DB (recommended), no cache exists to invalidate; any cache must be explicitly bounded |
| Fail-safe behaviour | Needs a rule | Recommendation shape: on error/ambiguity, **deny** (fail-closed), consistent with `processing_mode`'s existing fail-closed posture |

**Sufficiency verdict:** the **existing structures cannot fully represent** the governance requirement.
`system_settings` can *store* opaque configuration, but there is no enforcement code, no scope/precedence
resolver, no admin authorisation surface, and no audit for such changes. A dedicated configuration model is
therefore required — either a new bounded table (e.g. `manual_processing_grants` with `scope_type`
(`organization` | `consultant_firm` | `consultant_client` | `consultant_client_set`), `scope_id`,
`enabled`, `granted_by`, `granted_at`, `revoked_at`, `reason`) **or** a versioned JSON document in
`system_settings` **plus** a new resolver service. The choice is a PO/architecture decision (see §20).

### 10.3 Proposed policy model (proposal only — not implemented, not authorized)

```text
EFFECTIVE_MANUAL_PROCESSING(actor, organization, item_or_batch)
  = DENY                                    if no grant matches            (default OFF, fail-closed)
  = DENY                                    if any matching grant is revoked/expired
  = ALLOW                                   if an explicit grant matches the most specific scope
  with precedence (most specific wins):
      consultant_client (explicit)  >  consultant_client_set (selected)  >
      consultant_firm (all clients) >  organization (self-service)      >  platform default (DENY)
  AND ALLOW only when actor capability holds:
      consultant path  → the actor's firm member row has the stage capability flag
      organisation path→ the member's role is Owner/Admin (per existing role vocabulary)
  AND writes are audited: grant/revoke (actor, scope, before/after) and every DENY that blocks an action
  AND automatic processing is unaffected (this governance governs MANUAL processing only)
```

Rules requiring PO confirmation are listed in §20 (items **PO-F1 … PO-F9**).

---

## 11. FIN-01c status — staff/support projection

| Question | Finding |
|---|---|
| Remaining direct `users` reads | **Exactly one**, in the whole frontend: `frontend/src/components/chat/ChatWidget.jsx:199` |
| Exact file/component | `ChatWidget.jsx`, `fetchStaffMembers()` (lines 195-210): `supabase.from('users').select('id, email, full_name, avatar_url, raw_user_meta_data').eq('raw_user_meta_data->>is_staff','true')` |
| Customer-facing? | **Yes** — it is the counterparty picker used by the customer-facing chat widget ("start a conversation with support"). |
| Staff/admin-facing? | The *targets* are internal staff; the *caller* is an authenticated customer user. |
| Accuracy defect | The selected columns `full_name`, `avatar_url`, `raw_user_meta_data` **do not exist** on `users` (confirmed live and against migrations) → the read cannot be served as written. |
| Does it affect Phase 8 completion? | **No.** No Phase 8 acceptance criterion (B1–B4, S1–S7, RLS-4A/4B, X1–X7) depends on the legacy chat widget's staff picker. |
| Is it required for P8-FIN-02? | **Not for the write-path fix**; **yes for end-to-end usability** of the legacy "start a conversation" flow. If D-7 is implemented as Option B (server-side), the counterparty projection should be resolved by that same server endpoint rather than a second client read. |

**Recommendation (not an authorization):** keep FIN-01c as a **separate future task**, but bind it to the
D-7 decision — if the PO authorises D-7 Option B, include the counterparty projection in that same bounded
deliverable (server-side, org/staff scoped, no client `users` read); otherwise FIN-01c remains deferred and
the legacy chat picker stays non-functional. The optional FIN-01b **static guard hardening** (a
source-level assertion covering *all* chat components, not only the rendered `ChatWindow`/`ChatList`
paths) should be folded into that task; it is non-blocking.

---

## 12. D-15 findings — production ACL verification (READ-ONLY planning)

**Status: NOT VERIFIED. Production was not contacted. No read-only production access is currently authorised.**

| Aspect | Requirement |
|---|---|
| Required access | A **read-only** production path: either the PO-authorised dedicated read-only role (RLS register decision **`D-10`**) or an out-of-band read-only credential; verification must run inside `BEGIN TRANSACTION READ ONLY` (the pattern used by `tools/p2_census/…`, which also refuses production-looking DSNs unless explicitly allowed) |
| Exact checks | 1. `supabase_migrations.schema_migrations` — applied versions and count (record expectation: **21**). 2. `pg_class.relrowsecurity` census over `public` (+ `relforcerowsecurity`). 3. `pg_policies` inventory (names, commands, `USING`/`WITH CHECK`). 4. Privilege census for `anon`/`authenticated`/`service_role` via `role_table_grants` **and** `has_table_privilege()` for `TRUNCATE`, `REFERENCES`, `TRIGGER`, `MAINTAIN` and DML. 5. `pg_default_acl` for `public`. 6. **Precondition counts**: `assets.organization_id IS NULL`; duplicate `organization_members(organization_id,user_id)`; duplicate `conversation_participants(conversation_id,user_id)`; `staff_roles` id `56f5fa09-…` absent; `staff_roles` name `pe_manager` absent; `billing_plans` count; `documents` bucket exists; **`report-artifacts` bucket existence**. 7. `emission_factors` RLS/policy/privilege state (D-4). 8. Row counts for `beta_users`/`beta_access_codes`/`waitlist` (FIN-05). 9. `storage.buckets` listing with `public` flags. |
| Expected evidence artefact | Signed-off census report: environment, timestamp, connected role, exact SQL, raw result sets, before-values for every metric a later migration changes, plus the `pg_default_acl` snapshot |
| Security-sensitive masking | Never print connection strings/passwords, JWTs, anon/service keys or signed URLs. Mask PII in any row sample (report counts/shapes, not values). Evidence enters the repository only if free of secrets/PII. |
| Explicitly not claimed | That PITR is enabled; that any privilege is safe; that RLS is enabled in production; or that the historical "97/104 disabled / `anon` `GRANT ALL`" record is current (see C-2). |

---

## 13. D-16 findings — backup / PITR + restoration rehearsal

**Status: NOT VERIFIED. No production backup or restore evidence exists in this repository.**

| Aspect | Requirement / finding |
|---|---|
| What must be verified in the provider | That automated backups/PITR are **enabled** for the production project, the retention window, the latest restorable point, and the owner able to perform a restore. `CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md` and `CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md` §7/§8 make this **HARD GATE Step 1**: "do not proceed if this cannot be confirmed". |
| Is PITR enabled? | **UNKNOWN** — must be confirmed in the provider console by the PO/ops. **Not asserted here.** |
| Application-side status | Backup **code** exists and is independently verified: `backend/backup/{service,catalog,artifact,crypto,settings,storage}.py`, with `CARBONTALLY_PRODUCTION_BACKUP_P1_1_N1_INDEPENDENT_VERIFICATION_20260911.md` → **`N1 VERIFIED — PASS`** (91 + 16 checks). This is *implementation* evidence, **not** evidence that production backups exist. |
| Acceptable restore evidence | A **timed, documented restore** into an **isolated/disposable** environment: (a) restore completes and schema/row counts on hot tables reconcile; (b) RLS/privilege posture re-verified after restore; (c) measured duration recorded against the recovery objective; (d) storage-object expectations stated (a database backup is **not** an object backup). |
| Required rehearsal environment | A disposable clone — never production, never the investor demo, never persistent QA. F-046-1 applies to any destructive harness use: the integration `pool` fixture refuses `qa`/`demo`/`investor`/`prod`/`live` names **before** any `TRUNCATE`. |
| Rollback / recovery evidence | The migration safety plan §10 records the rollback reality: a Git revert does **not** reverse a DB migration; backend/frontend rollbacks are separate operations. The restore path is therefore the real recovery mechanism and must be demonstrated **before** D-17. |
| Explicitly not claimed | That any rehearsal has occurred. The records state plainly: "Has rollback been rehearsed? **NO** evidence of any rehearsal". |

---

## 14. D-14 planning findings — production migration window (planning only, no execution)

### 14.1 Recalculated baseline and delta

| Metric | Value | Basis |
|---|---|---|
| Repository migration set (release tree) | **69** files, strictly ordered by filename | `ls supabase/migrations/*.sql` → 69 |
| Production applied (as recorded) | **21** | Programme records (`CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md` §3.1: bands 1–8 init/rc2, 9–16 add_*, 17–21 v3m1/v3m2/v3m3/v3m5/v3m6). **UNVERIFIED — production not contacted.** |
| **Pending (delta)** | **48 files** (positions **22 → 69**) | 69 − 21. The earlier "47 pending" figure predates the release tree's RLS-4B migration; the release figure is **48**, with RLS-4B last by filename. |
| Local canonical DB | 46 applied (newest `20260903010000`) | Read-only `supabase_migrations.schema_migrations` — the *local* environment is itself behind |

### 14.2 Ordered delta (22 → 69) with risk markers

Legend: `RLS` enables/alters row security · `POLICY` creates/drops policies · `GRANT` touches privileges ·
`STORAGE` touches storage · `QUEUE` touches the processing queue/automation.

```text
22 20260821000000_d20_d15_active_consultant_grant                      GRANT
23 20260821010000_d21_white_label_branding
24 20260821020000_d22_processing_work_assignment                        POLICY
25 20260822000000_p9_rls_recursion_fix                                  POLICY
26 20260822010000_d27_d19_customer_lifecycle                            RLS POLICY
27 20260823000000_d32_private_documents_storage                         RLS POLICY STORAGE
28 20260823010000_d33_evidence_traceability
29 20260824010000_d35_self_service_onboarding
30 20260824020000_d37_0_billing_security_and_configurable_subscription  RLS POLICY GRANT
31 20260824030000_d37_master_commercial_billing                         RLS GRANT
32 20260825000000_v3m7_vehicles                                         RLS POLICY GRANT
33 20260828000000_v3m8_messaging_unique_participants
34 20260828010000_v3m8_system_admin_role_model
35 20260828020000_v3m8_pe_manager_role
36 20260829000000_v3m9_durable_automatic_processing                     QUEUE
37 20260831000000_v3m10_org_membership_unique
38 20260831010000_v3m11_operational_indexes
39 20260831020000_audit_activity_immutability                           POLICY
40 20260831030000_tenant_org_id_not_null
41 20260831040000_consultant_revocation_roles                           POLICY GRANT
42 20260902020000_v1_2_dual_origin_workflow
43 20260902030000_phase5_work_item_assignments                          RLS
44 20260902040000_phase5_pe_operational_messaging                       POLICY
45 20260902050000_phase5_notification_event_key
46 20260903010000_ws4_gate3_4a_item_assignment_foundation               POLICY GRANT
47 20260905000000_gate4_actor_provenance
48 20260905010000_gate5_t1_automation_provenance                        QUEUE
49 20260905020000_gate5_t6_automation_write_once_guard                  QUEUE
50 20260906010000_gate6_w1_automation_extracted_output                  QUEUE
51 20260906090000_p6_1c_consultant_engagement                           POLICY
52 20260906100000_p6_2a_consultant_processing_permissions               (capability columns)
53 20260910120000_p6_2d_consultant_provenance
54 20260912000000_p7_audit_immutability_and_indexes
55 20260913000000_p8_report_lifecycle_status
56 20260914000000_p8_b1_disclosure_model_foundation                     RLS POLICY GRANT
57 20260915000000_p8_b1_correction_privileges_and_evidence_idempotency   GRANT
58 20260916000000_p8_b2_evidence_line_items                             RLS POLICY GRANT
59 20260916010000_p8_b2_provenance_line_links
60 20260917000000_p8_b3_intensity_catalogue                             RLS POLICY
61 20260917010000_p8_b3_intensity_ratios                                RLS POLICY GRANT
62 20260918000000_p8_b4_narrative_overlay                               RLS POLICY GRANT
63 20260919000000_p8_b4_frozen_artefact                                 RLS POLICY GRANT STORAGE
64 20260920000000_p8_rls_anon_grant_containment
65 20260921000000_p8_s2_is_current_single_valued
66 20260922000000_p8_rls_4a2_authenticated_grant_hardening
67 20260923000000_p8_rls_4a1b_anon_default_privilege_hardening           GRANT
68 20260924000000_p8x_x2_operational_telemetry_retention                QUEUE
69 20260925000000_p8_rls_4b_group1_enablement                           RLS QUEUE
```

**Ordering is strict.** RLS-4B deliberately sorts last: it activates policy families (re)written by earlier
pending migrations (`20260821000000`, `20260822000000`, `20260831020000`, `20260831040000`) and the RLS-4A
containment trio (`20260920000000`, `20260922000000`, `20260923000000`). Enabling RLS earlier would enforce
superseded predicate text.

### 14.3 Security / operational implications of the delta

| Implication | Detail |
|---|---|
| Security-sensitive migrations | **24 of the 48** touch RLS, policies or privileges: 22, 24, 25, 26, 27, 30, 31, 32, 39, 41, 43, 44, 46, 51, 56, 57, 58, 60, 61, 62, 63, 64, 66, 67, 69 — plus the final RLS-4B activation. The plan's stop criterion "RLS would become weaker" applies to each. |
| Worker / automatic-processing controls | Migrations 36, 48, 49, 50 supply the durable queue columns and write-once automation guards that the worker code already expects (`stage`, `locked_at`, `attempt_count`, `automation_extracted_data`). The **worker must be drained before DDL and restarted afterwards**, and duplicate-calculation prevention re-verified. |
| Storage implications | 27 flips `documents` to private and creates 4 `CREATE POLICY` statements (**non-idempotent — apply once**); 63 constrains `report_version_artifacts` to the `report-artifacts` bucket, which **does not exist anywhere reachable** → **D-11 must be closed before** the reporting path can work. |
| Non-idempotent files | The 2026-09-11 review flagged 27/31/35 as apply-once; **that list must be re-derived for the current 48-file delta** as an evidence step, not assumed. |
| Precondition counts | Required before execution (see §12 D-15 checks 6–9), since several migrations add `SET NOT NULL`/`UNIQUE`/FK constraints. |
| Expected verification steps | Per-block object checks (`information_schema`, `pg_constraint`, `pg_indexes`, `pg_proc`, `pg_trigger`); RLS/privilege census parity; negative isolation matrix; storage checks; application smoke tests; a post-migration evidence artefact. |

---

## 15. D-17 status — production migration authorization

**D-17 is a TERMINAL PO AUTHORIZATION GATE. It is NOT authorised, NOT granted, and NOT implied by anything in
this report.**

* The programme record is explicit: production is **NOT AUTHORISED, NOT TOUCHED** (G0-D open).
* D-17 becomes meaningful only after: D-15 (verified production state) → D-16 (backup/PITR + rehearsal evidence) → D-14 (frozen window plan over the frozen migration set, with an evidenced clone rehearsal).
* No part of this reconnaissance authorises, prepares for, or initiates a production migration, deployment, or production connection.
* Any implementation work authorized *after* this report (D-7/D-4/D-11/FIN-05/FIN-06) would add **further** migrations numbered above `20260925000000`, changing the delta again — so the migration set must be frozen **before** D-14/D-17.

---

## 16. Migration drift-gate findings

| Question | Finding |
|---|---|
| Existing mechanism comparing production ledger ↔ repository set? | **None in the release tree.** No script, no CI job, no release gate. |
| CI hard-fail gate? | **No CI exists at all** — `.github/workflows` has no workflow files in the release tree. |
| Pre-commit gate? | **None** (`.pre-commit-config.yaml` absent). |
| Historical gate? | `CARBONTALLY_PRODUCTION_PRECOMMIT_GATE_20260911.md` §5 documents a one-off review and classifies the then-unknown live state as `REPOSITORY_ONLY`, explicitly "not a commit blocker but **a deployment blocker**" — i.e. the risk was identified in prose only; nothing enforces it, which is precisely how the current 48-migration drift arose. |
| Reusable primitives already present | `qa_harness/db/migrations.py` (migration discovery/application helpers, with `qa_harness/tests/harness/test_run_db_runner.py`); `backend/backup/settings.py` already knows the `supabase_migrations` schema; `tools/p2_census/…` demonstrates the safe read-only, production-refusing pattern. |

### 16.1 Bounded proposal (design only — not implemented)

1. **Deterministic comparison.** A read-only script (e.g. `tools/migration_drift/check_migrations.py`) that:
   reads the repository migration filenames (ordered, duplicates/out-of-order detected) and the target
   database's `supabase_migrations.schema_migrations`, then reports three disjoint sets — **applied**,
   **pending** (in repository order), **unexpected** (ledger entries absent from the repository) — plus
   ordering/duplicate/skipped-version anomalies. Read-only transaction; refuses production-looking DSNs
   unless `CARBONTALLY_MIGRATION_DRIFT_ALLOW=non-production` (mirroring the existing census tool).
2. **Release blocking.** A CI job (the release tree currently has no CI, so this establishes the first
   workflow) that runs the comparison on `main`/release branches with the **staging** credential and **fails**
   the check when `pending > 0` for a database the release targets. Because production credentials must never
   live in CI, the production-side comparison runs through an explicitly authorised operator step.
3. **Emergency override.** A single documented, time-boxed escape hatch: an env flag
   (`CARBONTALLY_MIGRATION_DRIFT_OVERRIDE=<ticket-id>`) that downgrades the failure to a warning **only**
   when a ticket id is supplied, and **always** writes the override into the evidence artefact. Overrides are
   reviewable after the fact; the flag never suppresses the evidence.
4. **Evidence artefact.** Machine-readable output (JSON + short Markdown) recording Git SHA, commit date,
   repository count, ledger count, pending list in order, unexpected list, preconditions checked, override id
   (if any), and the exact SQL used — stored with the release evidence for each deployment.
5. **Operator workflow.** Documented order: (a) run the check pre-deploy; (b) if pending > 0, either apply the
   migrations (under the authorised window) or block the deploy; (c) attach the artefact to the release;
   (d) post-deploy, re-run to prove parity. The gate's purpose is exactly to make "application code deployed
   while the ledger stayed frozen" impossible to do silently.

---

## 17. Dependency graph

```text
PRODUCT DECISIONS (PO)                    TECHNICAL IMPLEMENTATION            SECURITY VERIFICATION        PRODUCTION OPERATIONAL GATES     FINAL PO CLOSURE
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
PO-D1  D-7 fix strategy (A or B)  ──►  WP-1 D-7 implementation ──────────►  VP-1 D-7 RLS/write-path  ─┐
PO-D2  FIN-01c in/out of scope    ──►  WP-2 FIN-01c (bind to WP-1 if B) ─►  VP-2 FIN-01c guard       ─┤
PO-D3  D-4 posture ruling         ──►  WP-3 D-4 revocation migration ────►  VP-3 D-4 privilege census ┤
PO-D4  D-11 option (A or B)       ──►  WP-4 bucket provisioning ─────────►  VP-4 real-adapter e2e     ─┤──► PO CLOSURE (per item)
PO-D5  FIN-05 retain/retire       ──►  WP-5 FIN-05 action ───────────────►  VP-5 FIN-05 census/tests  ─┤
PO-D6  FIN-06 policy model        ──►  WP-6 FIN-06 implementation ───────►  VP-6 governance matrix    ─┘
                                       WP-7 drift gate (independent) ────►  VP-7 gate fault-injection ─┐
                                                                                                          │
  PRODUCT DECISION ──► IMPLEMENTATION ──► INDEPENDENT VERIFICATION ──► (migration-set FREEZE) ──────────► │
                                                                                                          ▼
PO-D7  read-only production access  ──────────────────────────────────► D-15 production ACL/ledger census ─┐
PO-D8  PITR + rehearsal authority   ──────────────────────────────────► D-16 restore evidence ────────────┤
      (evidenced clone rehearsal over the FROZEN set) ─────────────────► VP-8 rehearsal evidence ──────────┤
                                                                                                          ▼
PO-D9  migration window approval    ──────────────────────────────────► D-14 window plan ──► PO-D10 D-17 AUTHORIZATION ──► EXECUTION ──► VP-9 post-migration evidence ──► PO CLOSURE
```

**Independence**

| Item | Independently executable? | Hard dependencies |
|---|---|---|
| D-7 (WP-1) | Yes, after PO-D1 | FIN-01c only for end-to-end usability |
| FIN-01c (WP-2) | Yes, after PO-D2 | None (binds to WP-1 if Option B chosen) |
| D-4 (WP-3) | Yes, after PO-D3 | None (no application dependency — verified) |
| D-11 (WP-4) | Yes, after PO-D4 | None; but must precede any production reporting smoke test |
| FIN-05 (WP-5) | Yes, after PO-D5 | Retirement path depends on D-16 if destructive |
| FIN-06 (WP-6) | Yes, after PO-D6 | Adds migrations → must precede the migration-set freeze |
| Drift gate (WP-7) | Yes (no PO decision needed beyond strictness) | Should precede any further deployment |
| D-15 | Needs PO-D7 (read-only access) | None |
| D-16 | Needs PO-D8 (provider access) | None, but feeds D-17 |
| D-14 | Needs D-15 + D-16 + frozen set | After all implementation work |
| D-17 | Terminal | After D-14/D-15/D-16 |

**Explicit answers to common dependency questions**

* **Does D-7 depend on FIN-01c?** No for the write path; yes for end-to-end usability of the legacy widget.
* **Is FIN-01c required for Phase 8 closure?** No — recommend a separate future task (bound to D-7 if Option B).
* **Do FIN-05 / FIN-06 affect the production migration?** Yes as **potential new migrations** — they must be decided *before* the migration set is frozen, or the 48-file delta changes again.
* **Are D-4 / D-11 / D-16 prerequisites for production?** D-16 **yes, hard** (Step-1 gate). D-11 **yes for production reporting functionality** (not for the DDL itself). D-4 **no** for the delta (RLS-4B excludes it) but **yes** for RLS steps 3–5 and full security closure.
* **Relationship D-14 / D-15 / D-17?** D-15 + D-16 + an evidenced rehearsal are **inputs**; D-14 is the **plan**; D-17 is the **terminal authorisation**. Sequential, not parallel.
* **Must a rehearsal precede D-17?** **Yes** — and the existing `ct_p8_rehearsal_20260915` clone is **not** sufficient evidence as it stands (no published evidence artefact, and it was built from the 68-migration set **before** RLS-4B).
* **Does any pending migration depend on an unresolved PO decision?** The existing 69-file set does **not** (RLS-4B explicitly excludes the open items). But **D-4, D-7 and FIN-05/FIN-06 each add migrations**, so the *final* set is decision-dependent — hence freeze after one decision batch.

---

## 18. Master decision register

| ID | Item | Current state | Decision required? | Proposed bounded action | Dependency | Verification |
|---|---|---|---|---|---|---|
| **D-7** | Chat participant writes (`P8-FIN-02`) | Browser path **non-functional**: `conversations.insert` sends non-existent `is_group`; `conversation_participants` has **no INSERT policy**; `messages` insert omits `organization_id` (policy denies NULL). Server API exists but cannot name a counterparty. | **YES** — Option A (repair browser writes + new policies) vs Option B (route through N1 API + bounded API addition) | A = schema alignment + participant INSERT/DELETE policy + negative tests; B = frontend rewiring to `/api/v3/messaging/*`, optional counterparty field/endpoint, plus audit hook for org conversations. No schema/RLS expansion needed for B. | PO-D1; FIN-01c for usability | RLS ALLOW/DENY matrix (participant/non-participant/cross-tenant/PE), write-path red-green, audit-entry assertions |
| **D-4** | `emission_factors` posture | RLS enabled, **0 policies**; `anon` holds SELECT/TRUNCATE/REFERENCES/TRIGGER; `authenticated` holds DML + non-DML; **zero client-side usage**; excluded from RLS-4A-1/4A-2/4B | **YES** — ratify "internal/server-side; not anonymously accessible" | One REVOKE-only migration > `20260925000000` (+ optional default-ACL parity); no policy, no data change | PO-D3 | `has_table_privilege` census, default-ACL durability test, RLS parity, functional non-regression via service role, anon-key negative read |
| **D-11** | `report-artifacts` bucket | Mandated by schema CHECK + PO `B4-D5/D6/D7`; adapter present; **bucket absent in every reachable environment**; no code creates or verifies it; tests use the in-memory adapter | **YES** — Option A (operational provisioning) vs Option B (migration-managed provisioning) | A = documented operator step + checklist gate; B = additive idempotent bucket migration (+ policies if required) | PO-D4 | Bucket exists & private; real-adapter e2e finalisation (upload + SHA-256 row + signed URL ≤300 s); `documents` untouched (B) |
| **FIN-05** | Beta / waitlist surfaces | Tables exist (RLS on, 0 policies), **0 rows locally**; admin beta API exists; waitlist API is a **stub**; admin calls to `/invite`, `/unsubscribe`, `/resubscribe` **do not exist**; `/beta/signup` and `/beta-login` still registered; LandingPage pre-launch, no waitlist form | **YES** — retain temporarily vs retire | Retain = decision record + retention via N3 + optional bounded policy set; Retire = code/route removal + (destructive) table disposition **after** backup confirmation | PO-D5; destructive path needs D-16 | Route/API inventory, `grep` gate for remaining references, RLS/table census, erasure behaviour test |
| **FIN-06** | Manual processing governance | **No governance control exists.** Flags `can_extract`…`can_submit` exist, default **false**, and **no application path can grant them**; manual-extraction API is org-member scoped with **no enablement gate**; `system_settings` exists but is read by no enforcement code; audit infrastructure exists | **YES — largest decision block** (default posture, admin enablement, scope vocabulary, precedence, new/existing jobs, auditability, storage home) | New bounded configuration model + resolver + CarbonTally-admin-only enablement surface + audit; enforcement wired into manual batch/stage actions; fail-closed | PO-D6 | Default-OFF proof; scope precedence matrix; grant/revoke audit rows; relationship-change recomputation; new/existing-job rules; no self-enablement negative tests |
| **FIN-01c** | Staff/support projection | **Exactly one** direct `users` read remains (`ChatWidget.jsx:199`) and it selects non-existent columns; customer-facing picker; not required by any Phase 8 acceptance criterion | **YES (scope only)** — in or out of finalization | Recommend: separate future task, bound to D-7 Option B (server-side projection); fold in FIN-01b static guard hardening | PO-D2 | Static guard over all chat components; projection contract test; no client `users` read |

| **D-15** | Production ACL verification | **NOT VERIFIED.** No read-only production access authorised | **YES** — authorise read-only production access (RLS `D-10`) | Run the §12 census read-only and publish the masked evidence artefact | PO-D7 | Census completeness, precondition counts, no secrets/PII in evidence |
| **D-16** | Restoration / PITR | **NOT VERIFIED.** Backup code verified (N1 PASS) but **no** provider backup confirmation and **no** rehearsal evidence | **YES** — authorise provider verification + timed rehearsal | Confirm backups/PITR in the provider; timed restore into a disposable clone; record duration, counts, RLS parity; document rollback reality | PO-D8 | Restore evidence artefact; post-restore RLS/privilege verification; measured duration vs objective |
| **D-14** | Migration window | Runbook exists but is **stale** (written for a 32-file delta); release delta now **48 files (22→69)** | **YES** — window, operator, controls, rollback authority | Update the runbook to the frozen 48-file delta; blocks; stop criteria; worker drain/restart; evidence plan | D-15 + D-16 + frozen set | Block object checks; precondition counts; RLS census parity; smoke tests; drift-gate artefact |
| **D-17** | Production migration authorization | **NOT AUTHORISED, NOT GRANTED** | **YES — terminal** | None until D-14/D-15/D-16 evidence exists | All production gates | Post-migration evidence + independent verification (§19 VP-9) |
| **WP-8** | Migration drift gate | **No CI, no gate, no pre-commit hook** in the release tree; primitives exist (`qa_harness/db/migrations.py`; `p2_census` read-only pattern) | Partly — strictness/override policy | Bounded read-only comparison tool + CI/release gate + override + evidence artefact + operator workflow (§16.1) | Independent (PO strictness only) | Fault-injection test (repository ahead of ledger ⇒ fail); evidence-artefact completeness |

---

## 19. Recommended implementation sequence

> Every implementation step below is **proposal only** and requires its own PO authorisation. Nothing here
> is authorised by this report.

**Wave 0 — decisions (no code)**
1. PO decision batch: `PO-D1` (D-7 strategy), `PO-D2` (FIN-01c scope), `PO-D3` (D-4), `PO-D4` (D-11), `PO-D5` (FIN-05), `PO-D6` (FIN-06), plus drift-gate strictness (`PO-D11`) — taken **together** so the migration set can be frozen once.

**Wave 1 — implementation, smallest and least coupled first (each independently verified)**
2. **WP-4 / D-11** — bucket provisioning per the chosen option → VP-4 (real-adapter end-to-end finalisation). *Unblocks the ratified reporting path.*
3. **WP-7 / WP-8** — migration drift gate → VP-7. *Should land before any further deployment.*
4. **WP-3 / D-4** — REVOKE-only containment migration → VP-3 (privilege census + default-ACL durability + non-regression).
5. **WP-1 / D-7** — per the chosen option (A: policies + schema alignment; B: frontend rewiring + bounded API addition + audit hook) → VP-1 (RLS ALLOW/DENY matrix, red/green).
6. **WP-2 / FIN-01c** — only if `PO-D2` places it in scope; otherwise deferred and folded into a later D-7-adjacent task → VP-2.
7. **WP-6 / FIN-06** — configuration model + resolver + admin enablement + audit + enforcement → VP-6. **Must complete before the freeze**, because it adds migrations.
8. **WP-5 / FIN-05** — retain actions or retirement; any destructive part is **sequenced after D-16** → VP-5.

**Wave 2 — production preparation (no production writes)**
9. `PO-D7` → **D-15** read-only production census, published as a masked evidence artefact.
10. `PO-D8` → **D-16** provider backup/PITR confirmation + timed restore rehearsal into a disposable clone.
11. **VP-8** — evidenced clone rehearsal of the **frozen** migration set (re-run of the deterministic replay, with published evidence and `rc=0`×2 for idempotent files); re-derive the non-idempotent file list for the current delta.
12. `PO-D9` → **D-14** frozen window plan (blocks, stop criteria, worker drain/restart, rollback authority, evidence plan).

**Wave 3 — production execution (only after D-17)**
13. Execute 22 → 69 in the frozen order with checkpoint verification, then the security/storage/smoke verifications, then worker recovery.
14. **VP-9** — post-migration evidence + independent verification.
15. **PO closure** per item (PO acts; agents do not self-close).

---

## 20. Explicit list of unresolved PO decisions

### Product decisions
* **PO-D1 — D-7 strategy:** Option A (repair browser writes; requires a new `conversation_participants` INSERT policy and schema alignment) or Option B (route through the N1 server API; requires a bounded API addition + audit hook). *Recommendation: B (not an authorization).*
* **PO-D2 — FIN-01c scope:** in Phase 8 finalization, or a separate future task? *Recommendation: separate, bound to D-7 Option B.*
* **PO-D3 — D-4:** ratify that `emission_factors` is internal/server-side and must not be anonymously accessible (and whether `authenticated` retains any privilege).
* **PO-D4 — D-11:** operational provisioning (A) vs migration-managed provisioning (B) — including whether migrations may create runtime resources at all.
* **PO-D5 — FIN-05:** retain temporarily (retention period expressed in the N3 control plane) or retire (dropping tables is irreversible; production row counts unverified).
* **PO-D6 — FIN-06:** the governance requirement itself. Sub-decisions requiring explicit confirmation (business rules, not implementation choices):
  * **PO-F1** — authoritative definition of "Manual Processing" (which entry points are governed: consultant manual extraction/mapping/validation/calculation, organisation self-service manual batches, or both).
  * **PO-F2** — default posture (stated intent: **OFF**) and whether it is global-by-default with explicit grants only.
  * **PO-F3** — enablement authority: which CarbonTally role may enable (System Admin only? Staff Admin? under which permission flag) and whether any self-service path may ever exist.
  * **PO-F4** — scope vocabulary and granularity: organisation, consultant firm, individual consultant client, selected clients, all clients.
  * **PO-F5** — precedence/inheritance when multiple scopes match (most-specific-wins vs any-grant-wins) and whether a narrow scope can *deny* what a broader grant allows.
  * **PO-F6** — behaviour for **existing/new/queued/in-progress** work: does disabling stop in-flight manual batches, block only new batches/items, or allow started work to complete?
  * **PO-F7** — relationship changes/revocation: immediate effect on in-flight work, and whether revocation records an audit event with actor + reason.
  * **PO-F8** — auditability: what must be recorded (grant, revoke, denied attempt, scope change) and the audit-trail retention.
  * **PO-F9** — configuration home: dedicated table vs versioned document in `system_settings` (determines migration footprint and resolver design).
* **PO-D11 — drift-gate strictness:** hard-fail on pending migrations vs warn, plus the emergency-override policy.

### Technical implementation (authorization, not a product decision)
* **PO-D12** — authorization to implement the items above (WP-1…WP-6) individually, with tests, and to add migrations numbered above `20260925000000`.

### Security verification
* **PO-D7 — read-only production access:** authorise the read-only production credential/role (RLS register decision `D-10`) plus masking rules for the published evidence.
* **PO-D13** — authorization for independent security verification of D-4/D-7 outcomes (ALLOW **and** DENY cases) as a gate separate from implementation.

### Production operational gates
* **PO-D8 — D-16:** authorise provider backup/PITR confirmation and a timed restore rehearsal into a disposable environment; accept the recorded duration/rollback reality.
* **PO-D9 — D-14:** approve the maintenance window, operator, worker/API controls, block plan and rollback authority.
* **PO-D10 — D-17:** the terminal authorization to apply production migrations. **Not granted; not requested by this report.**

### Final PO closure
* **PO-D14** — accept (or reject) each verified item after independent verification; agents do not self-close.

---

## 21. Explicit list of things NOT verified

1. **Production schema/ledger state** — no production connection was made; "21 applied / 48 pending" is **recorded, not measured**.
2. **Production RLS/privilege posture** — including whether the historical "97/104 RLS-disabled, `anon` `GRANT ALL`" record is current (contradicted at migration level by the "enable all tables" loop ⇒ C-2).
3. **Production backups / PITR** — enabled state, retention and latest restorable point are **unknown**.
4. **Any restoration or rollback rehearsal** — none evidenced; no timed restore exists.
5. **`report-artifacts` bucket in production** — unknown; the bucket is absent in every environment reachable from here.
6. **Real-storage finalisation path** — B4 tests use the in-memory adapter; the real Supabase Storage upload/signed-URL path is **unverified**.
7. **Production row counts** for `beta_users` / `beta_access_codes` / `waitlist` (local counts are 0 and prove nothing about production).
8. **End-to-end behaviour of the legacy chat widget** — inferred from code + live schema/RLS; not exercised in a browser.
9. **FIN-06 product intent** — the product meaning of "Manual Processing" is **not** inferable from code (see PO-F1).
10. **Any legal conclusion** — no claim is made about what the UK Data (Use and Access) Act 2025 requires; that driver was not independently verified.
11. **Migration idempotency for the current 48-file delta** — the historical apply-once list (27/31/35) was **not** re-derived here.
12. **`storage`-schema write rights** required by D-11 Option B — not tested.
13. **The previous worktree's uncommitted material** — deliberately untouched and not assessed; the release tree is the reference.

---

## 22. Explicit list of things NOT changed

* **No source code changed** — backend, frontend, admin, engines, services, repositories all untouched.
* **No migrations** added, edited, reordered or applied; no change under `supabase/migrations/`.
* **No schema, RLS, policy, privilege, default-privilege or storage change**; no bucket created or modified; no table created, altered or dropped.
* **No database data changed** — all database access was read-only `SELECT` against **local, non-production** databases.
* **No production connection, query, migration or deployment** of any kind.
* **No test** added, edited, skipped or deleted.
* **No commit, push, tag, branch move, rebase, reset, clean, stash, merge or checkout**; the only repository write in this task is **this report file** (untracked, uncommitted, unpushed).
* **No change to the previous worktree** (`/home/shomonrobie/carbon_tally`), which remains as it was.
* **No item is self-closed**; all closure verdicts remain PO acts.

---

**Report complete. No implementation authorization is contained in or implied by this document. STOP.**
