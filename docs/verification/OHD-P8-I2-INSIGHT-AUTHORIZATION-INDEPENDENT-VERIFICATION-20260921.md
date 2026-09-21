# OHD — INDEPENDENT VERIFICATION — CARBONTALLY INSIGHT I2 (authorization + bounded I1 hardening)

**Verification ID:** `OHD-P8-I2-INSIGHT-AUTHORIZATION-20260921`
**Date:** 2026-09-21
**Verifier:** OHD (independent verification agent) — read-only verification
**Verdict:** **FAIL** (see §18). I1 hardening F-01…F-06 are verified; the I2 authorization layer is largely correct, but **one material ratified I2 requirement is demonstrably not satisfied** (customer Insight for the customer's own authorized organisation) and one required matrix row (inactive organization → DENY) is not enforced on the backend path. **I2 is NOT closed and I3 is NOT authorised.**

---

## 1. Baseline

| Item | Value |
|---|---|
| Branch | `p8-release-reconciled` |
| HEAD | `ad49f5703f47d6acdc7962b1322fdbb1ff56356a` — `docs(p8-i2): CT-P8-I2 Insight authorization implementation report` |
| Implementation commit | `de18c358b35b4378c8a2b8edce257c8c440e8cec` — `feat(p8-i2): CarbonTally Insight authorization and visibility layer` (parent: `66adfb5`, the I1 OHD verification) |
| Remote alignment | `github/p8-release-reconciled` = `ad49f5703f47d6acdc7962b1322fdbb1ff56356a` — **identical** |
| Working tree | **clean** — `git status --porcelain --untracked-files=all` = 0 lines; `git stash list` = 0 |
| Other remote | `origin` is a local path and is **not** used as evidence of remote state |

Both expected SHAs exist and carry the stated content. HEAD is the report commit, so the implementation commit is its parent, not HEAD.

**I2 change footprint** (`de18c358`, 10 files, +1,275 / −56):

| File | Δ |
|---|---|
| `backend/api/insight_authz.py` | +241 (new authorization layer) |
| `backend/api/operations_auth.py` | +13 (additive public alias only) |
| `backend/api/v3_insight.py` | +91/−… (routes re-wired) |
| `backend/data/insight.py` | +47/−… (I1 hardening F-02/F-04) |
| `backend/tests/unit/api/test_v3_insight_i2_authorization.py` | +464 (new) |
| `backend/tests/unit/data/test_i2_insight_rls_live.py` | +222 (new) |
| `backend/tests/unit/data/test_i2_insight_authorization_contracts.py` | +142 (new) |
| `backend/tests/unit/api/test_v3_insight_endpoints.py` | ±27 (harness updated for the I2 bundle) |
| `backend/tests/unit/data/test_i1_insight_migration.py` | +7/−… (ordering assertion updated) |
| `supabase/migrations/20261002000000_p8_i2_insight_authorization.sql` | +77 (new) |

No frontend, configuration, dependency or deployment file was touched.

## 2. Governing decisions used

* `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` — §8 (authorization boundary; a stored reference is not a grant), §9.1/§9.2/§9.6 (creator-private; organisation **and** creator), §10.2 (staff Insight deferred), §10.3 (no auditor persona exists), §10.4 (PE receive no Insight capability), §24.1–§24.6.
* The later PO decision restated in the brief: customer Insight for the customer's authorized organisation; consultant Insight **only** through the existing consultant→customer authorization; Staff/Admin internal Insight within existing staff/admin permissions; **no** auditor, PE or public Insight; LLM is never the authorization boundary; access is read-oriented; recommendations do not constitute automatic consequential actions.
* Superseded `ask_*` terminology was not revived (verified: no `ask_*` object exists — §13).

## 3. Method

Everything below was derived from the repository, PostgreSQL and the code's own runtime behaviour. The implementing agent's report (`docs/implementation/phase8/…I2…`) was read only to compare claims, never as evidence.

1. Source trace of the migration, `insight_authz.py`, all five routes, the repository hardening, and the three new test modules.
2. Auditor-built disposable database `ct_i2_verify_20260921` (template copy of the disposable `carbontally_test`, **Insight objects dropped**, then `20261001000000` and `20261002000000` applied **verbatim** from the repository, then re-applied for idempotency).
3. Live DB-boundary probe under `SET LOCAL ROLE authenticated` with simulated `request.jwt.claims` (the mechanism `auth.uid()` reads), plus `service_role` and `anon` cases.
4. Real-repository probe: `InsightRepository` imported unmodified from HEAD, driven over asyncpg.
5. **Real-relationship authorization probe**: the real `api.insight_authz.authorize_insight_scope` driven with the real `ConsultantsRepository` / `StaffRepository` reading real `consultant_clients`, `consultant_firm_members`, `consultant_profiles`, `staff_profiles`, `staff_roles` rows. No fake authorization data, no re-implemented resolver.
6. Router probe with production-shaped principals, plus an every-read revocation sequence.
7. Test execution: the I2/I1 suites, the live-RLS suite (with and without DSN), and the **full unit suite at three commits** (`e48ee55`, `5bd5e29`, `ad49f57`).
8. Leakage, naming and read-vs-action scans.

**Environment discipline:** Demo Lab, QA and production were only *read*. No persistent environment was migrated. No application code, migration, schema, configuration, test, fixture or data outside the auditor's own disposable databases was modified. No defect was fixed. The only repository change is this report.

## 4. I1 hardening verification (F-01 … F-06)

| Finding | Independent result | Evidence |
|---|---|---|
| **F-01** staff cross-org scope not a by-product of organization membership | **VERIFIED** | Staff scope is now resolved **explicitly** from the existing chain (`resolve_staff_context` → ACTIVE `staff_profiles` row, permissions from `staff_roles.permissions`, `entity_id IS NULL` = internal) and is evaluated **before** the customer branch. Live with real tables: internal staff (active profile, **no** organisation membership) → `ALLOW:staff_internal` for an arbitrary customer org; the same principal who is *also* an org member → still `ALLOW:staff_internal` (scope is the staff profile, not the membership); a staff-shaped identity with **no** active profile → `DENY:403` (no staff scope); inactive profile → `DENY:403`. |
| **F-01** platform-wide behaviour not globally changed | **VERIFIED** | The only shared-file change is a **13-line additive alias** in `operations_auth.py` (`resolve_staff_context` delegating to the pre-existing `_resolve_context`). `auth.py`, `api/dependencies.py`, `consultant_auth.py` are **untouched**. Full unit suite shows **no new failures** (identical 4 pre-existing failures at all three commits — §14). |
| **F-02** `save()` SQL/type defect corrected | **VERIFIED (fixed)** | SQL now casts every parameter: `$1::uuid, $2::uuid, $3::uuid, $4::text, coalesce($5::timestamptz, $6::timestamptz), coalesce($7::timestamptz, $6::timestamptz)`. The untyped `coalesce($5,$6)` form survives **only in the docstring prose** (line 136); an AST-based scan of every SQL string in the module finds **no** untyped `coalesce($N,$M)`. Live against real PostgreSQL: `save()` executes on the **update** branch (title persisted, `created_at` round-trips as a datetime) **and** on the **insert** branch. The rest of the method (single insert-or-update, technical fields only) is unchanged. |
| **F-03** author-kind integrity at the DB/RLS boundary | **VERIFIED (fixed)** | Migration `20261002000000` replaces exactly one policy (`ci_messages_conversation_creator_insert`) and adds `AND role = 'user'` to the existing WITH CHECK, keeping `is_org_member(organization_id)`, `created_by = auth.uid()` and the parent-conversation creator `EXISTS`. Live: as `authenticated`, a `role='user'` insert in the caller's own conversation is **ALLOWED**; the same insert with `role='insight'` is **DENIED** by RLS (`violates row-level security policy`); as `service_role` (the backend) a `role='insight'` insert is **ALLOWED**. Policy text read back from `pg_policies` matches the file. |
| **F-03** I1 policies not weakened | **VERIFIED** | The complete `pg_policies` snapshot before/after applying the I2 migration in the auditor's DB differs by **exactly one policy and exactly one predicate** (`role = 'user'` added). **No grant changes**, **no RLS-flag changes**, no table/column/index/constraint change; re-applying the migration leaves exactly one such policy (idempotent). |
| **F-04** scoped repository `get()` | **VERIFIED (fixed)** | Signature is now `async def get(self, id: str, *, organization_id: str)` — **keyword-only and required** — delegating to `get_conversation`. Live: own org → the conversation; another org → `None`; calling `get(id)` without the scope raises `TypeError`. All callers searched: the API uses only `get_conversation`, `create_conversation`, `list_conversations`, `count_conversations`, `add_message`, `list_messages` — **no caller of `get()`**, and no unscoped SELECT remains in the module (every Insight SELECT filters `organization_id`; every INSERT supplies it). |
| **F-05** service-role invariant | **VERIFIED (carried invariant)** | Still true and unchanged: `service_role` bypasses RLS — live, it wrote the reserved `role='insight'` row and it still reads rows belonging to a **suspended** organisation while the authenticated path sees none. Application-layer authorization now runs **before** data access on all five routes (`require_insight_user` → `authorize_insight_scope` → repository). Enforceability by the current architecture: yes for the I1/I2 surface — every repository method the API calls is organisation-scoped and creator-filtered, and the one unscoped write path (`save()`) is documented internal-only with no caller. It remains a **design invariant for I3**, not a structural guarantee (see §13/O-02). |
| **F-06** durable live-RLS testing | **VERIFIED** | `tests/unit/data/test_i2_insight_rls_live.py` exists and: uses a **real** database; runs inside **one transaction that is always rolled back** (no TRUNCATE, no deletes); refuses a DSN that omits the scope or names a persistent database (independently exercised: DSN = `carbontally_qa_phase8` and `carbontally_demo_local` both raise `RuntimeError: … may never target a persistent environment`); **skips** when the DSN is unset (verified: 4 skipped); and tests the real policies (author-kind forgery, creator-private reads, cross-organisation read/write, service_role author kind). Independently executed against a clean disposable DB: **4 passed**. |

## 5. I2 authorization architecture

`backend/api/insight_authz.py` is the single entry point. Actual evaluation order (read from code and confirmed by behaviour):

**unauthenticated → PE (`is_entity_staff`) → internal staff (`resolve_staff_context`) → customer (own organisation) → consultant (`ensure_consultant_org_access`) → deny**

* the router carries `dependencies=[Depends(require_insight_user)]`, so the surface is deny-by-default by construction and PE is refused before any scope resolution;
* staff is resolved from the **staff profile**, not from membership, and is evaluated before the customer branch — which is what closes OHD F-01;
* the customer branch compares the **requested** organisation against the principal's own organisation (the URL/parameter is never the boundary);
* consultant falls through to the platform's D15 resolver, which requires an ACTIVE `consultant_clients` grant for the firm profile;
* denial is a **uniform 403** with a non-disclosing detail (verified: all five routes return `403 {"detail": "CarbonTally Insight access denied"}` for an unauthorized principal).

The reported order in the implementation report matches the code, and the code's order is correct for the platform's identity model **except** for the customer-role predicate (F-01 below), which does not match the role vocabulary the platform's own resolver produces.

## 6. Customer authorization

| Check | Result | Evidence |
|---|---|---|
| Active organisation membership required | PASS | Authorization requires `is_org_member`; a principal without an active `organization_members` row is denied (403). `auth.py` resolves membership with `.eq('is_active', True)`. |
| Organisation must be **active** | **FAIL** | See finding **F-02**: `authorize_insight_scope` never consults `organizations.is_active`; a member of a **suspended** organisation is `ALLOW:customer` (live, real tables), and the backend pool bypasses the RLS suspension predicate. |
| Revoked membership loses access | PASS | Live: revoked principal → 403; and the specific case of a principal whose membership was revoked **and** who presents an old conversation id → 403. |
| Access re-resolved on subsequent reads | PASS | Both resolvers read the database on every request; live sequences (revocation, restoration, ending a grant) flip the outcome on the **same** conversation id. |
| Cannot query another organisation by supplying its id | PASS | 403 on list/create/read-by-id when naming another organisation; the scope always comes from the server-side relationship. |
| Conversation ids cannot bypass organisation authorization | PASS | 403 at the authorization step for an unauthorized organisation; **404** (no existence disclosure) for another principal's conversation inside an authorised organisation. |
| **Customer may use Insight for its own authorized organisation** | **FAIL** | With the production role shape (`org_owner` / `org_admin` / `org_member` / `org_viewer`, which is what `auth.py` produces) every route returns **403**. See finding **F-01**. Only test-fixture-shaped roles (`owner`, `member`) are allowed. |

## 7. Consultant → customer authorization (critical requirement)

Source of truth: the **existing** `consultant_clients` relationship via the **existing** `api.consultant_auth.ensure_consultant_org_access` (D15). I2 does not recreate consultant permissions (no new table, no new grant model, no parallel resolver — verified by reading the module and the migration).

Independently executed against **real relationship rows** (`consultant_profiles` + `consultant_firm_members` + `consultant_clients`), driving the real resolver:

| Case | Expected | Observed |
|---|---|---|
| Consultant A → **Customer A** with an ACTIVE grant | ALLOW | **ALLOW:consultant** |
| Consultant A → Customer B with **no** grant | DENY | **DENY:403** |
| Consultant A → Customer A after the grant is **ENDED** (revocation) | DENY | **DENY:403** |
| Consultant with an **inactive firm membership** | DENY | **DENY:403** |
| Grant restored → re-checked per request | ALLOW | **ALLOW:consultant** |
| Self-declared `consultant` role with no firm membership | DENY | **DENY:403** |

Router-level every-read sequence (real router, mutable grant state): create while authorized → **201**; read back → **200**; **revoke** → the *same* conversation id → **403**; list → **403**; append → **403**; restore → **200**. Consultant reading **another user's** conversation inside an authorized customer org → **404** (creator-private holds). No bypass by customer id, conversation id or request parameter was found.

## 8. Staff / Admin authorization

Existing authorization source: `staff_profiles` (ACTIVE) → `staff_roles.permissions`, via the shared `resolve_staff_context`/`_resolve_context` — the same chain the ops surface uses; `entity_id IS NULL` = CarbonTally internal.

| Case | Expected | Observed |
|---|---|---|
| Internal staff, ACTIVE profile, arbitrary customer org | ALLOW (staff scope) | **ALLOW:staff_internal** |
| Internal staff who is also an ordinary org member | staff scope, not customer scope | **ALLOW:staff_internal** |
| Staff-**shaped** identity with no ACTIVE staff profile | no staff scope | **DENY:403** |
| INACTIVE staff profile, no other relationship | DENY | **DENY:403** |
| PE staff (`entity_id` set) | DENY | **DENY:403** |
| Auditor | DENY | **DENY:403** (no auditor persona exists — §9) |
| Creator-private behaviour for staff | preserved | staff reading another principal's conversation → **404**; listing its messages → **404** |

**Authorized now vs. deferred to I3:** what is authorised today is *organisation scope* plus *creator-private visibility* — i.e. a staff member may open/use Insight conversations for any organisation **that they themselves created**. `staff_permissions` is resolved and carried on the access object but **grants nothing by itself** ("carried for the later controlled-tool layer"). No customer-data permission, no cross-user conversation visibility and no internal data scope is implemented. That is consistent with the PO decision only insofar as "within their existing staff/admin permissions" is **not yet enforced anywhere**; the module states this is a binding I3 invariant (see O-02).

## 9. Denied personas

| Persona | Result | Evidence |
|---|---|---|
| Auditor | **DENY** | No auditor role/persona/table exists in the platform (searched migrations + backend); an `auditor`/`org_auditor` role with no relationship → 403. `PERSONA_AUDITOR` is enumerated in the decision table but is never assigned by any resolver — denial is by absence of an authorization relationship, not by an explicit auditor check (O-01). |
| PE staff | **DENY** | Denied twice: `require_insight_user` (router) and the `entity_id IS NOT NULL` branch; live 403 for list and create. |
| Public / unauthenticated | **DENY** | 401 (`Authentication required`) with no principal; `anon` role has no privilege on either table (live). |
| Revoked user | **DENY** | 403 (no active membership; falls through). |
| Revoked consultant grant | **DENY** | 403 after `status='ended'`; same conversation id no longer readable. |
| Inactive organisation | **DENY expected — actual ALLOW** | Finding **F-02**. |
| Unknown/unsupported customer role | **DENY** | 403 for `org_auditor`, `public`, `guest`, `""`. (Note: because of F-01 this is currently true for *every* customer role.) |
| Any principal, forged author kind | **DENY** | API 422 and, independently, database RLS rejection for `role='insight'`. |

No unauthorized data was returned in any case: unauthorized organisations yield 403 before any query; other principals' conversations inside an authorized organisation yield 404 and — verified at the database layer — **zero rows**, so no content is disclosed.

## 10. RLS / database verification

**Exact disposable environment:** `ct_i2_verify_20260921`, created as a template copy of the disposable `carbontally_test`, `carbontally_insight_*` dropped, then `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql` and `supabase/migrations/20261002000000_p8_i2_insight_authorization.sql` applied **verbatim** from the repository (both exit 0), then re-applied (idempotent). Nothing was applied to Demo Lab, QA or production.

Live outcomes (18/18 expected results):

| Check | Result |
|---|---|
| `authenticated` inserts `role='user'` in its own conversation | ALLOWED |
| `authenticated` forges `role='insight'` | **DENIED** (RLS) |
| `service_role` writes `role='insight'` | ALLOWED (backend-only author) |
| Only the backend-authored `insight` row exists | 1 |
| Same-org **non-creator** appends to another's conversation | DENIED |
| Cross-org principal appends | DENIED |
| Forged `created_by` | DENIED |
| Message `organization_id` contradicting the conversation | DENIED |
| Creator reads own conversation / same-org non-creator / cross-org principal | 1 / 0 / 0 |
| Same-org non-creator reads messages / creator reads own messages | 0 / 2 (its own `user` row + the backend `insight` row) |
| Client `UPDATE` / `DELETE` | DENIED (no privilege) |
| `anon` SELECT | DENIED |
| Member of a **suspended** organisation (authenticated path) | 0 rows / insert DENIED (the RLS suspension predicate works) |
| `service_role` on the suspended organisation | still sees the row (RLS bypass — see F-02) |
| Policy inventory | 4 policies (`ci_conversations_creator_select`, `ci_conversations_creator_insert`, `ci_messages_conversation_creator_select`, `ci_messages_conversation_creator_insert`), all `TO authenticated`, no anon policy |

`public.is_org_member(uuid)` is `SECURITY DEFINER, STABLE`, testing active membership of an **active** organisation — which is why the authenticated path honours suspension while the service-role backend path does not.

## 11. Every-read re-authorization

Verified paths (all five routes re-resolve authorization **per request** from the principal's current relationships, then scope the query):

| Sequence | Outcome |
|---|---|
| Consultant: create while authorized → read/lists OK → **revoke** → same conversation id | 201 → 200 → **403** |
| Consultant: append after revoke | **403** |
| Consultant: restore grant → same id | **200** |
| Customer: own conversation, own org | 200 |
| Customer: own conversation id + **other** organisation parameter | **403** |
| Customer: list another organisation | **403** |
| Customer: `organization_id` omitted | **422** (no implicit scope) |
| Customer with membership revoked: list / old conversation id | **403** / **403** |
| Unauthorized principal, all five routes | uniform **403**, no data |
| Any principal: conversation belonging to an unauthorized organisation | **403** |
| Any principal: another principal's conversation **within** an authorized organisation | **404**, and 0 rows at the database layer |

## 12. Creator-private model

Preserved for **every** persona: `visibility_created_by(access)` always returns the concrete principal id, and `conversation_is_visible` requires **both** organisation and creator equality. Verified outcomes: creator → 200; same-org other principal → 404 (and 0 rows live); **consultant** authorized for the customer org → 404 on a customer user's conversation; **internal staff** → 404 on another principal's conversation and on its messages. No organisation-wide sharing mode, no team/admin/staff "see-everything" path exists. The only exception surface is each principal's **own** conversations.

## 13. Read-vs-action boundary

No consequential action is implemented on the Insight surface. The router exposes exactly five persistence routes (create/list/read conversation, append/list messages); a scan of both Insight modules for subscription/billing/permission/calculation/approval/rejection/deletion/configuration operations found only **prose** describing what is deferred or prohibited. `InsightRepository.delete()` still raises `NotImplementedError`. Recommendations and any execution of consequential changes remain unimplemented, as required.

## 14. Independent test results

| Suite | Result |
|---|---|
| I1 migration (9) + I2 contracts (7) + I1 endpoints (8) + I2 authorization (22) + live RLS (4) | **50 collected: 46 passed, 0 failed, 4 skipped** (skips are the live-RLS tests without a DSN) — independently reproduces the implementing agent's "46 passed" |
| Live RLS suite **with** `INSIGHT_RLS_TEST_DSN` → clean disposable DB | **4 passed**, 0 failed |
| Live RLS suite **without** DSN | 4 skipped (safe default) |
| Live RLS suite with a QA / Demo Lab DSN | **refused** (`RuntimeError`) — guard works |
| Full unit suite @ `ad49f57` (I2) | **2,841 tests, 4 failures, 0 errors, 7 skipped** |
| Full unit suite @ `5bd5e29` (I1) | 2,808 tests, 4 failures, 0 errors, 3 skipped |
| Full unit suite @ `e48ee55` (pre-I1) | 2,791 tests, 4 failures, 0 errors, 3 skipped |
| Delta attributable to I2 | **+33 tests, +0 failures**, +4 skips (the new live-RLS module) |

The **same four** tests fail at all three commits — `tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered`, `…::test_canonical_ops_review_assign_registered`, `…::test_admin_legacy_compat_surface_retained`, and `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`. They are **pre-existing** and were **not** fixed.

Note on the I2 test modules' nature: the 22 authorization tests and 8 endpoint tests run the **real router and the real authorization module** with in-memory repository doubles; the 7 contract tests are **static** (DDL-text, AST and signature assertions); only the 4 live-RLS tests touch a real database. That is why the customer-role defect in §6 is invisible to the suite — every test builds its principal with a bare role (`owner`/`admin`/`member`/`viewer`), a shape the production auth layer never produces.

## 15. Security test matrix (independent results)

| Principal | Target | Expected | **Observed** |
|---|---|---|---|
| Customer (production shape `org_owner`) | Own org | ALLOW | **DENY 403 — FAIL (F-01)** |
| Customer (test-fixture shape `owner`) | Own org | ALLOW | ALLOW 200 |
| Customer | Other org | DENY | DENY 403 |
| Consultant | Authorized customer | ALLOW | ALLOW 200 / 201 |
| Consultant | Unauthorized customer | DENY | DENY 403 |
| Consultant | Authorized customer after grant revocation | DENY | DENY 403 |
| Staff/Admin | Authorized internal scope | ALLOW | ALLOW 200 (`staff_internal`) |
| Staff-shaped identity without a valid staff profile | Staff scope | DENY | DENY 403 (no staff scope) |
| Auditor | Insight | DENY | DENY 403 |
| PE | Insight | DENY | DENY 403 |
| Public (unauthenticated) | Insight | DENY | 401 |
| Any principal | Forged author kind (`role='insight'`) | DENY | 422 (API) **and** RLS denial (DB) |
| Any principal | Conversation id from an unauthorized scope | DENY | 403 (other org) / 404 + 0 rows (other principal) |
| Any principal | Scope expansion via request parameters | DENY | 403 (other org, other-org parameter, omitted parameter → 422) |
| Member of an **inactive** organization | Own org | DENY | **ALLOW — FAIL (F-02)** |

## 16. I2–I8 leakage scan

| Later stage | Result |
|---|---|
| I3 — data tools, tool registry, intent classification, natural-language retrieval, tool calls | **None** (0 files for `insight_tool`, `tool_registry`, `intent_classif`; the words "tools"/"tool layer" appear only in prose) |
| I4 — AI interaction records, canonical AI audit events, model/provider attribution | **None** (0 files; no `ai_interaction`, no provider/model columns) |
| I5 — context/memory layer | **None** (0 files) |
| I6 — Insight frontend | **None** — the only `insight` string in `frontend/src`+`admin/src` is the pre-existing admin Analytics subtitle word "insights" |
| I7 — retention, deletion, privacy, export | **None** — `delete()` still refuses; no retention/export concept |
| I8 — billing/allowances, provider implementation, provider hardening | **None** — 0 files; no `insight_billing`/`insight_provider` |
| LLM API calls | **None on the Insight surface.** `backend/infra/llm_client.py` exists but was added by `c5eadec` ("Phase 7: Document Processing and AI Extraction"), is used by the **document-processing** pipeline, and is **not imported by any Insight module**. |
| RAG / LangChain / embeddings / vector store | **None** |
| Unrestricted database access | **None new** — the Insight repository remains the only access path, every SELECT is organisation-scoped and every INSERT supplies `organization_id` |
| `ask_*` implementation | **None** — only the I1 test asserting their absence |
| `public.ai_content_history` | **Untouched** — the only I2 mention is a non-scope comment |
| Migration ordering | Valid — `20261002000000` is the latest of 77 migrations, immediately after the I1 migration |

## 17. Findings

### F-01 (I2) — Every real customer is denied Insight (material; the primary cause of the FAIL verdict)

* **Severity / materiality: HIGH.** The governing product decision is "Customer users may use Insight for data belonging to their authorized CarbonTally organization". Against the **real** identity model this is not satisfied: every customer organisation member receives **403** on all five routes.
* **Evidence.** `backend/auth.py:313` sets an org member's role as `f"org_{org_role}"` (or `"org_viewer"` when the org role is null). Live Demo Lab data shows `organization_members.role ∈ {owner, admin, member, viewer}`, so a real principal's `AuthUser.role` is always **`org_owner` / `org_admin` / `org_member` / `org_viewer`**. `backend/api/insight_authz.py:59` defines `CUSTOMER_INSIGHT_ROLES = ("owner", "admin", "member", "viewer")` and line 180 compares `(current_user.role or "").lower() not in CUSTOMER_INSIGHT_ROLES` → the predicate is **never true**, so the customer branch always denies. There is exactly **one** non-test `AuthUser` construction in the backend, and no normalization strips the prefix.
* **Independent observations.** Router probe: `org_owner`/`org_admin`/`org_member`/`org_viewer` → 403; `owner`/`member` → 200. Real-table probe: `org_owner` → `DENY:403`, `org_member` → `DENY:403`, `owner` → `ALLOW:customer`. All 22 I2 authorization tests pass because they build principals with bare roles.
* **Platform convention confirms the mismatch.** The neighbouring platform code handles both forms: `_ORG_AUDIT_ROLES = frozenset({"owner", "admin", "org_owner", "org_admin"})` (`api/dependencies.py:233`, used by `ensure_org_audit_access`); other modules strip the prefix (`api/v3_disclosure.py:104`, `api/v3_reports.py:576`, `domain/disclosure_narrative.py:77`, `domain/disclosure_exposure.py:103`).
* **Security direction:** **fail-closed** — no unauthorized access is granted by this defect; the impact is that the ratified customer capability is inoperative and the I2 suite cannot detect it.
* **Affected requirement:** brief §7 and the security matrix row "Customer / Own org / ALLOW"; PO decision §1 (customer Insight); D2 §9.1/§9.5.
* **Recommended disposition (not performed — verification only):** accept both role forms (as `_ORG_AUDIT_ROLES` does) or strip the `org_` prefix before comparison, and add a test that builds the principal the way `auth.py` does (`role="org_member"`) so the production shape is covered.

### F-02 (I2) — Organization activity (tenant suspension) is not enforced on the Insight backend path

* **Severity / materiality: MEDIUM.** The brief's matrix requires "Inactive organization → DENY". The API authorization never consults `organizations.is_active`: live, a member of a **suspended** organisation is `ALLOW:customer` and a consultant with an active grant to a suspended organisation is `ALLOW:consultant`.
* **Evidence.** `insight_authz.authorize_insight_scope` reads only `current_user.is_org_member`/`organization_id` (customer), the staff profile, or the consultant grant — no organisation-activity check; `RepositoryBundle.organizations`/`tenant` exist but are not used by the Insight layer. The database **does** enforce suspension (`is_org_member` requires an active organisation) — live, the authenticated path sees 0 rows and cannot create — but the backend uses the **service-role** pool, which bypasses RLS (live: `service_role` still saw the suspended organisation's conversation). So the suspension predicate does not protect the Insight data path.
* **Context (relevant to disposition):** a platform-wide scan finds **no** API-layer tenant-activity check anywhere; the shared D20 helper `ensure_org_access` (used by other business surfaces, and by I1) likewise does not check it. So Insight is *consistent with the platform* while not meeting the stated expectation.
* **Affected requirement:** brief §10 (inactive organization DENY) and §7 (organization must be active); D2 §8.7 deny-by-default, tenant-suspension intent (`organizations.is_active` is documented as the "RLS suspend predicate").
* **Recommended disposition:** PO decision — either declare tenant suspension to be an RLS-only control (and document that the service-role backend path is exempt), or add the organisation-activity check to the Insight authorization step (and consider the platform-wide gap separately).

### F-03 (I2) — The durable live-RLS test is not hermetic against pre-existing rows

* **Severity: LOW (test robustness, not authorization).** The live-RLS assertions use **global** counts (`count(*) … WHERE role='insight' == 1`, `count(*) FROM …conversations == 1`). Independently observed: with one pre-existing committed `insight` row in the disposable database, `test_service_role_writes_the_reserved_author_kind` failed (`assert 2 == 1`); on a clean disposable database the same suite passes 4/4. The documented target `carbontally_test` is currently empty, so the documented command passes today — but the test will fail spuriously once that database accumulates Insight rows.
* **Affected requirement:** F-06's purpose (durable regression protection).
* **Recommended disposition:** scope the assertions to the test's own `conversation_id`/seed rows, as the other three tests largely do.

### F-04 (I2) — The disposable test database is behind the migration set (environment, not I2)

* **Severity: INFORMATIONAL, but blocking for live consultant-path testing.** `carbontally_test` lacks the phase-6.1c/6.2a columns: `consultant_firm_members` has 17 columns (missing `can_extract`, `can_map`, `can_validate`, `can_calculate`, `can_confirm_automation`, `can_submit`) and `consultant_clients` misses `relationship_origin`, `engagement_requested_at`, `engagement_decided_by`, `engagement_decided_at`, whereas the fully migrated Demo Lab has 23/24. Consequence: the **real** consultant chain raises `UndefinedColumnError` on that database (the repository's `_MEMBER_COLUMNS`/`_CLIENT_COLUMNS` select those columns), which is why the verifier had to apply `20260906090000_p6_1c_consultant_engagement.sql` and `20260906100000_p6_2a_consultant_processing_permissions.sql` to the auditor's own clone to exercise the consultant path with real tables.
* **Affected requirement:** none in I2; it affects the ability to run live consultant-path tests, and it means the live-RLS module's "real database" coverage is limited to the Insight tables (which are complete there).
* **Recommended disposition:** refresh the disposable test database (or document that it is partial), and consider a full-schema from-scratch application in CI.

### Observations (informational)

* **O-01 — Auditor denial is implicit.** `PERSONA_AUDITOR` is enumerated in `PERSONA_DECISIONS` but never assigned by `resolve_insight_persona` or `authorize_insight_scope`; auditors are denied only because no auditor persona/relationship exists (consistent with D2 §10.3). If an auditor identity is later modelled as a **staff role**, the staff branch would grant it staff scope. Worth an explicit exclusion before such a persona is introduced.
* **O-02 — Staff organisation scope is currently unbounded.** Any internal staff member with an ACTIVE profile may act on **any** organisation, and `staff_permissions` is carried but unused. This is stated in-code as an I3 binding invariant ("data scope is enforced at the controlled-tool layer"). Today it grants no cross-principal data (creator-private holds for staff), but the I3 tool layer must enforce the permission dimension — the I2 architecture provides it a resolved `staff_permissions` map, which is the right seam, yet nothing structurally prevents an I3 tool from ignoring it.
* **O-03 — `service_role` remains the only writer of `role='insight'`** and the RLS bypass is the platform's normal backend posture; the code-level scoping verified in §5–§12 is therefore the *only* boundary on the backend path. This is the invariant I3 tooling must reuse (no raw SQL).
* **O-04 — Consistency with the implementing agent's report.** Independently reproduced: "17 I1/I2 endpoint+migration tests" (my focused run: 46 passed + 4 skipped = 50 collected), the pre-existing failure list, the 46-passed claim, the F-02 cast change, the F-03 policy text, the F-04 signature, and the F-06 guard behaviour. Not reproduced/aligned: the report's implication that customer authorization works end-to-end (it does not against the production role shape — F-01), and the claim that "PE staff denied, internal staff operational-only" is accurate but silent on the unbounded staff organisation scope (O-02).

## 18. Verdict

> ## **FAIL**

**Rule applied (from the brief):** FAIL — a material I2 requirement or security invariant is demonstrably not satisfied.

**Why FAIL, and why not PARTIAL or BLOCKED:**

* A **material ratified requirement is demonstrably unsatisfied**: customer users may not use Insight for their own authorized organisation, because the customer-role predicate cannot match the role vocabulary the platform's own authentication layer produces. This is not a documentation gap or an unverifiable claim — it was reproduced three independent ways (router probe with production-shaped principals, the real resolver against real relationship rows, and code/data tracing), and it affects 100% of real customer organisation members (fail-closed). The brief's security matrix row "Customer / Own org / ALLOW" is therefore **not** met.
* A required matrix row is also unmet for **inactive organisations** (F-02).
* **PARTIAL was not used** because the shortfall is not "evidence could not be established" — the evidence is conclusive and negative. **BLOCKED was not used** because all required evidence was obtainable safely (real database, real resolvers, full test runs, guard verification).
* The verdict is **not** a rejection of the I2 work as a whole: the I1 hardening F-01…F-06 is verified, the consultant→customer chain reuses the existing relationship correctly, staff/PE/auditor/public/unknown-role denial is correct, RLS author-kind integrity is real at the database boundary, creator-private visibility and every-read re-authorization hold, and no I3–I8 leakage exists. The FAIL is driven by the customer-authorization defect (F-01), reinforced by F-02.

**Explicit scope of this verdict:** this verdict covers **only** I2 and the bounded I1 hardening. **I2 IS NOT CLOSED. I3 IS NOT AUTHORISED** by this report, and no later stage was implemented, evaluated or progressed. No defect was fixed (per §19 of the brief): F-01/F-02/F-03 are recorded for disposition, not remediated.

## 19. Limitations

1. **No live end-to-end HTTP test with real JWTs.** Authentication depends on the Supabase/GoTrue stack, which is not running; the router was therefore exercised by mounting the **real** router and **real** authorization module with real dependency injection (the same technique the repository's own I2 tests use) while the data and RLS layers were exercised against real PostgreSQL. The customer-role defect in F-01 is nevertheless conclusive, because it is a pure string-vocabulary mismatch between two committed code paths (`auth.py` and `insight_authz.py`), demonstrated both by direct resolver calls and by the router.
2. **RLS verification used the auditor's own disposable database** built from the repository DDL, not Demo Lab/QA/production (which correctly do not carry the Insight migration).
3. **The consultant path was exercised with the real resolver and real tables on the auditor's clone**, after applying two phase-6.x migrations that the disposable test database was missing (F-04). No fake authorization data was used.
4. **Staff/consultant/customer relationships in the live probes were seeded by the auditor** in its own disposable database; they are real rows in the real tables with the real column semantics, but the POPULATION is synthetic.
5. The `staff_permissions` dimension is not exercised because no I2 code path consumes it (O-02).

## 20. Closure boundary — what the PO must decide before I2 can be closed and I3 authorised

1. **Remediate or explicitly accept F-01** (customer authorization must work for the production role shape). This is the blocking item: until it is resolved, the ratified customer capability is inoperative, and the I2 test suite cannot detect a regression in it.
2. **Decide F-02** (tenant suspension): confirm that organisation activity must be enforced on the Insight backend path (and remediate), or ratify suspension as an RLS-only control and document the service-role exemption.
3. **Accept or remediate F-03** (live-RLS test hermeticity) so the durable regression test remains trustworthy as `carbontally_test` accumulates data.
4. **Accept F-04** (stale disposable test database) and decide whether to refresh it / add a from-scratch full-migration CI path, so live consultant-path testing is possible.
5. **Disposition O-01/O-02** before I3: an explicit auditor exclusion if an auditor persona is ever introduced, and the I3 tool-level permission model for staff organisation scope (with `staff_permissions` as the seam).
6. **Re-verify after remediation**: the customer path, the tenant-activity decision, and a suite case that constructs the principal exactly as `auth.py` does. Closure should not be inferred from a green suite that only exercises bare-role fixtures.
7. **Authorise I3 separately** (D2 §24.4). Nothing in this verification authorises I3, and no later-stage implementation was found (§16).

---

*Verification performed read-only. No application code, migration, schema, configuration, test, fixture or data outside the auditor's own disposable databases was modified; no defect was fixed; no persistent environment was migrated; `public.ai_content_history` was left untouched; no other repository was modified. The only repository change is this report.*
