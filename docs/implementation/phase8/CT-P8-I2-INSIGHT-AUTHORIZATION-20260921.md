# CT-P8-I2 — CarbonTally Insight Authorization and Visibility Layer

**Authorization:** `CT-P8-INSIGHT-I2-I8-MASTER-20260921-001` (bounded I1 hardening + I2 only)
**Implementation date:** 2026-09-21
**Branch:** `p8-release-reconciled`
**Starting SHA:** `66adfb5fb45e1945b65202544f74364b83e9df79` (OHD I1 verification, verdict PASS)
**Implementation commit:** `de18c358b35b4378c8a2b8edce257c8c440e8cec`
**Remediation commit:** see §12 (this addendum); baseline for remediation `682d591` (OHD I2 FAIL)
**Verdict (original implementation):** OHD returned **FAIL** (`OHD-P8-I2-INSIGHT-AUTHORIZATION-20260921`) — I2 was NOT verified and NOT closed; I3 remains unauthorised.
**Verdict after remediation:** `I2 REMEDIATED — READY FOR OHD RE-VERIFICATION` (§12). Remediation is **not** independent verification.

## 1. Authoritative specification

* `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` — §8 (authorization boundary; stored references are not grants; order of operations), §9.1/§9.2/§9.5/§9.6 (creator-private visibility; four customer roles), §10 (consultant/staff/auditor/PE boundaries), §23.2 (I2 = "Apply the ratified creator-private visibility model; complete authorization coverage; ALLOW and DENY verification"), §24.2–§24.6.
* PO decision (2026-09-21) — ratified Insight access model: customers (own organisation), consultants (existing consultant→customer relationship), authorized CarbonTally staff/admin (internal intelligence within existing staff/admin permissions); **no** auditor, **no** PE, **no** public access; the public FAQ assistant remains separate.
* OHD I1 independent verification (`66adfb5`) findings F-01…F-07.

## 2. I1 hardening — finding dispositions

**F-01 — staff cross-organization scope → RESOLVED (narrow, Insight-specific).**
Staff scope is no longer inherited from organisation membership or from a generic org-access helper: `authorize_insight_scope` resolves *internal staff* first, from the existing staff authorization chain (`staff_profiles` ACTIVE + `staff_roles.permissions`, via `resolve_staff_context`), and only then falls through to customer → consultant → deny. `ensure_org_access` is no longer called anywhere on the Insight surface. No platform-wide rule changed — `ensure_org_access` and every other endpoint behave exactly as before. Staff also remain creator-private, so no cross-principal conversation content is exposed. Evidence: `backend/api/insight_authz.py`; tests `test_internal_staff_gets_internal_scope_from_an_active_staff_profile`, `test_staff_shaped_identity_without_an_active_profile_gains_no_staff_scope`, `test_staff_remain_creator_private_on_the_insight_surface`, `test_pe_staff_profile_is_denied_even_if_the_identity_flags_disagree`.

**F-02 — `save()` could not execute (`DatatypeMismatchError`) → RESOLVED (types only, no semantics).**
Every parameter is now cast explicitly to the ratified I1 column type (`$1::uuid`, `$2::uuid`, `$3::uuid`, `$4::text`, `coalesce($5::timestamptz, $6::timestamptz)`, `coalesce($7::timestamptz, $6::timestamptz)`). The repository API was **not** redesigned; `save()` remains internal/service-only (documented in-method) and is still unrouted. Evidence: `backend/data/insight.py`; `test_save_statement_casts_every_parameter_explicitly`.

**F-03 — a client could forge `role='insight'` → RESOLVED (minimum policy change).**
New migration `20261002000000_p8_i2_insight_authorization.sql` replaces the single insert policy with the identical organisation + creator + parent-conversation predicate **plus `role = 'user'`**, so the reserved author kind can only be written by the service-role backend (future I4). No table, column, index, grant or other policy changed; no I3/I4 audit semantics were introduced. Evidence: migration; independent **live** regression `test_client_may_persist_only_human_authored_messages` (real RLS, disposable DB); contract test `test_i2_insert_policy_pins_the_author_kind_to_human_messages`.

**F-04 — unscoped (unused) `get()` → RESOLVED (narrow, convention-consistent).**
`InsightRepository.get(id, *, organization_id)` now requires the organisation scope — the same shape the repository already uses for `ActivityClarificationsRepository.get(id, *, organization_id=…)`. No unscoped conversation read remains, so a future caller cannot silently become an authorization bypass. Callers re-verified: the method has none (the API uses `get_conversation`). Evidence: `test_get_requires_an_organization_scope`, `test_repository_has_no_unscoped_conversation_read`.

**F-05 — `service_role` bypasses RLS → DOCUMENTED AS A BINDING CARRIED INVARIANT (nothing changed).**
Supabase semantics were not touched. Invariant: *application/domain authorization remains the authoritative boundary for backend service-role access*; every I3 controlled tool MUST reuse the scoped repository surface (organisation-scoped SQL + creator predicate) and MUST NOT issue raw SQL. The I2 migration alters no grant. Evidence: `test_f05_service_role_posture_is_unchanged_by_i2`; invariant I-6 (§7).

**F-06 — no durable live-RLS coverage → RESOLVED.**
New `backend/tests/unit/data/test_i2_insight_rls_live.py` runs the REAL policies against a REAL database. It is skipped unless `INSIGHT_RLS_TEST_DSN` is set, refuses any database whose name looks persistent (`demo`/`qa`/`investor`/`prod`/`live`, and the main application databases) mirroring the F-046-1 guard, and performs no destructive setup (one transaction, own fixtures, rollback). Coverage: author-kind integrity (F-03), creator-private visibility, cross-organisation read/write denial, service-role author-kind write. Evidence: 4 live tests PASS (§6).

**F-07 — consistency with the I1 implementation report → ACCEPTED.**
I1's verified claims are unchanged. F-01's disposition is superseded by the newer PO decision; the I1 statement "I1 grants no staff exception — every principal is creator-scoped" remains true *at the conversation level* and is preserved by I2.

## 3. I2 implementation scope

`backend/api/insight_authz.py` is the **single authorization entry point** for the
Insight surface. It creates **no** customer-access model of its own; it reuses the
platform's authoritative relationships:

| Scope | Authoritative source reused | Resolver |
| --- | --- | --- |
| Customer | `organization_members` (ACTIVE, ACTIVE organisation) — already resolved per request by `auth.get_current_user`, which filters `is_active = TRUE` | `authorize_insight_scope` |
| Consultant | `consultant_clients` **ACTIVE** grant (D15), the single source of the consultant→customer relationship | `api.consultant_auth.ensure_consultant_org_access` (called, not reimplemented) |
| Internal staff/admin | `staff_profiles` (ACTIVE) + `staff_roles.permissions` via `staff_profiles.role_id`; `entity_id IS NULL` = CarbonTally internal | `api.operations_auth.resolve_staff_context` (public alias added over `_resolve_context`) |

Evaluation order is scope-before-role (AGENTS.md §7 / D20): **PE staff → internal
staff → customer → consultant → deny**. A staff-shaped identity with no ACTIVE
staff profile gains no staff scope and falls through to the ordinary rules, so
staff access is never a side effect of membership.

**Consultant path (no parallel model):** the grant check *is* the existing
`ensure_consultant_org_access`, which resolves the caller's active firm membership
(`consultant_firm_members`) and then requires an ACTIVE `consultant_clients` row for
the requested organisation; the organisation id always comes from the request scope
being authorized, never from a consultant-supplied bypass. `pending`/`rejected`/
`suspended`/`ended`/`inactive` grants confer no access. Revoking the grant ends
access on the next read (D2 §8.8).

**Staff/admin path:** authorization requires an ACTIVE `staff_profiles` row; the
row's `entity_id` decides internal vs PE. `staff_roles.permissions` are carried on
the access object **for the later controlled-tool layer only** — I2 grants no data
scope by itself, and staff remain creator-private on conversations. The PO's
staff/admin data topics (customer usage/activity/subscriptions/billing/storage/
service utilisation/workflow patterns) are I3 tool scope, and their "within existing
staff/admin permissions" restriction is recorded as binding invariant I-5 (§7). The
PO constraint "Insight may recommend but must not independently perform consequential
subscription, billing, permission, calculation, deletion or configuration changes"
is recorded as invariant I-7 for I3 tool design.

**Visibility:** creator-private for **every** persona, including staff
(`visibility_created_by` returns the concrete principal id; there is no
"see-everything" mode to pass). Each conversation read re-resolves from the database
by (authorized organisation, creator) and returns **404** otherwise, so a stored
conversation id is never a grant.

## 4. Authorization matrix

| # | Principal / request | Decision | Enforcement point |
| --- | --- | --- | --- |
| 1 | Customer user (owner/admin/member/viewer), own organisation | **ALLOW** (creator-private) | org membership scope + creator filter/RLS |
| 2 | Customer user naming another organisation | **DENY 403** | `authorize_insight_scope` scope mismatch |
| 3 | Customer user reading another customer's conversation (same org) | **DENY 404** | `conversation_is_visible` + RLS creator predicate |
| 4 | Consultant with ACTIVE grant for the organisation | **ALLOW** (creator-private) | `ensure_consultant_org_access` |
| 5 | Consultant without an ACTIVE grant (incl. `ended`) | **DENY 403** | same resolver |
| 6 | Consultant naming an unassigned customer in the request | **DENY 403** | request scope authorized server-side |
| 7 | Consultant for two authorized customers | **ALLOW** for both (separate conversations) | per-request grant resolution |
| 8 | Internal staff/admin with ACTIVE staff profile | **ALLOW** (internal scope, creator-private) | `resolve_staff_context` (`entity_id IS NULL`) |
| 9 | Staff-shaped identity with no ACTIVE staff profile | Falls through to customer/consultant rules | `resolve_staff_context` returns `None` |
| 10 | Processing Entity staff (flag or profile `entity_id`) | **DENY 403** | router gate + scope resolver |
| 11 | Auditor persona (no membership) | **DENY 403** | no auditor authorization source exists (D2 §10.3) |
| 12 | Public / unauthenticated | **DENY 401** + `WWW-Authenticate: Bearer` | router gate |
| 13 | Customer role outside `owner/admin/member/viewer` | **DENY 403** (deny-by-default) | role check |
| 14 | Revoked membership or revoked consultant grant | **DENY** on the next read | live re-resolution (D2 §8.8) |
| 15 | Client forging `role='insight'` (API or direct DB) | **DENY 422 (API)** / **RLS rejection (DB)** | policy `role = 'user'` (F-03) |

## 5. Files, migrations, tests

**Created**

* `backend/api/insight_authz.py` — I2 authorization/visibility layer (single entry point)
* `supabase/migrations/20261002000000_p8_i2_insight_authorization.sql` — F-03 author-kind integrity (one policy replacement)
* `backend/tests/unit/api/test_v3_insight_i2_authorization.py` — authorization matrix (Part J items 1–15)
* `backend/tests/unit/data/test_i2_insight_authorization_contracts.py` — F-02/F-03/F-04/F-05 contracts + migration minimality
* `backend/tests/unit/data/test_i2_insight_rls_live.py` — live-schema RLS regression (F-06)
* this report

**Modified**

* `backend/api/v3_insight.py` — router gate `require_insight_user` + per-request `authorize_insight_scope`; `ensure_org_access`/`require_org_member` removed from the Insight surface
* `backend/api/operations_auth.py` — additive public alias `resolve_staff_context` (no behaviour change)
* `backend/data/insight.py` — F-02 explicit casts; F-04 organisation-scoped `get()`
* `backend/tests/unit/api/test_v3_insight_endpoints.py` — I1 bundle gains the staff/consultant stub surfaces the I2 gate resolves
* `backend/tests/unit/data/test_i1_insight_migration.py` — ordering assertion updated to the intended post-I2 state (scope-before-role change; no I1 security assertion was weakened)

**Migration:** `20261002000000_p8_i2_insight_authorization.sql` — repository file created; applied **only** to the disposable `carbontally_test` database for test execution. **Not** applied to Demo Lab, QA or production (§8).

**Tests executed (Cline, implementation-time evidence — not independent verification):**

| Suite | Command | Result |
| --- | --- | --- |
| I1 + I2 unit/contract suite | `pytest tests/unit/api/test_v3_insight_endpoints.py tests/unit/api/test_v3_insight_i2_authorization.py tests/unit/data/test_i1_insight_migration.py tests/unit/data/test_i2_insight_authorization_contracts.py tests/unit/data/test_i2_insight_rls_live.py -q` | **46 passed, 4 skipped** (live tests skipped without a DSN), exit 0 |
| Live RLS regression (disposable `carbontally_test`) | `INSIGHT_RLS_TEST_DSN=…carbontally_test pytest tests/unit/data/test_i2_insight_rls_live.py -q` | **4 passed**, exit 0 |
| Full backend unit suite | `pytest tests/unit -q` | see §6 |

The live run independently reproduces the F-03 boundary in the database: a client
insert of `role='user'` succeeds, a client insert of `role='insight'` is refused by
RLS, the creator sees their conversation while a same-organisation peer and a
cross-organisation principal see none, and the service-role backend remains the only
writer of the reserved author kind.

## 6. New regression coverage added (F-06)

`test_i2_insight_rls_live.py` (live, disposable DB): author-kind integrity;
creator-private visibility; cross-organisation read denial; cross-organisation write
denial; service-role author-kind write. It is durable (re-runnable), self-guarding
(refuses persistent databases) and non-destructive (transactional, rolled back).

`test_v3_insight_i2_authorization.py` (in-memory, API): organisation isolation;
cross-org read/write denial; creator-private visibility; consultant grant
ALLOW/DENY/multi-customer/unassigned-denial/revocation; staff/admin scope and
staff-without-profile fall-through; PE, auditor and unauthenticated denial;
conversation-id guessing; scope-parameter expansion; author-kind integrity;
router-level gate presence.

`test_i2_insight_authorization_contracts.py` (repo/DDL): F-02 casts, F-03 policy
predicate, F-04 scoped `get`, F-05 untouched grant posture, migration minimality.

### 6.1 Full-suite regression baseline

`cd backend && python -m pytest tests/unit --tb=no -p no:warnings`
→ **4 failed, 2830 passed, 7 skipped in 256.78s** (collected = 2,841).

| Baseline | Collected | Failures |
| --- | --- | --- |
| pre-I1 (`e48ee55`) | 2,791 | 4 |
| I1 HEAD (`66adfb5`) | 2,808 | 4 |
| I2 (this work) | 2,841 | 4 — the **same pre-existing** failures |

The four failures are unchanged in identity: `test_review_sla_surfaces.py`
(3 tests) and `test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`
(1 test — an exact migration-count expectation of 71 that already failed with 75
migrations *before* I1 and now sees 77 because the I2 migration was added). They are
**not** fixed by this work, are **not** attributed to I2, and are left to their own
workstreams as instructed. **Delta: +33 tests, +0 new failures.** Of the 7 skips, 4
are the new live-RLS tests (no disposable DSN supplied in this run).

## 7. Security invariants (binding, carried forward)

| # | Invariant |
| --- | --- |
| I-1 | Every Insight read is re-authorized from the authenticated principal and the request's organisation scope; nothing is inherited from a previous request or a stored id. |
| I-2 | A conversation is visible only to the principal that created it, within the organisation the current request authorizes (D2 §9.2/§9.6). No shared, team, admin or staff "read anyone's conversation" mode exists. |
| I-3 | Stored references and conversation ids are never grants (D2 §8.4). |
| I-4 | Authorization precedes data access: authorization → scope resolution → RLS/domain controls → (future) controlled tool execution (D2 §8.5). The LLM is never an authorization mechanism and no prompt content can expand scope. |
| I-5 | Staff/admin Insight data scope is limited by the caller's existing staff/admin permissions (`staff_roles.permissions`); I2 grants no data scope, and the I3 tool layer must enforce it. |
| I-6 | `service_role` bypasses RLS by platform design, so **application-layer scoping is the boundary** on the backend path: I3 tools must reuse the scoped repository surface and must never issue raw SQL (OHD F-05). |
| I-7 | Insight may recommend but must never independently perform consequential subscription, billing, permission, calculation, deletion or configuration changes (PO decision). |
| I-8 | Author-kind integrity: only the backend may write the reserved `insight` author kind; authenticated clients may write `user` messages only (F-03). |
| I-9 | Revocation is live: ending membership (or a consultant grant) ends access to existing conversations on the next request (D2 §8.8). |

## 8. Environment / deployment boundary

* Repository migration created: `20261002000000_p8_i2_insight_authorization.sql`.
* Applied **only** to the **disposable** `carbontally_test` database (test execution).
* **No** migration was applied to the **Demo Lab** (`carbontally_demo_local`), **QA**
  (`carbontally_qa_phase8`) or **production**; no deployment was performed.
* The live RLS test module refuses to run against any persistent-sounding database.
* The I1 migration likewise remains unapplied to persistent environments.

## 9. Explicit exclusions (not implemented)

I2 implemented the authorization/visibility layer **only**. Not implemented: I3
controlled tools, tool registry, intent classification, natural-language data
querying; I4 AI interaction records and canonical AI audit events; I5 context/memory;
I6 user interface; I7 retention/privacy/deletion/export; I8 providers, provider
adapters, billing/allowance, production hardening. Also **not** implemented: any LLM
or provider integration; RAG/embeddings/LangChain; automatic subscription, billing,
permission, calculation, deletion or configuration changes; report redesign; consultant
natural-language question answering (I3+); reuse of `public.ai_content_history`; any
`ask_*` insight architecture; auditor/PE/public access.

## 10. Known limitations

1. The consultant grant check performs one repository lookup per request (resolver
   reuse rather than caching); correctness over latency at this stage.
2. `staff_permissions` is carried on `InsightAccess` but not yet consumed — it is the
   I3 input, and I5/I-5 remains to be enforced at tool level.
3. The live RLS test requires an explicit `INSIGHT_RLS_TEST_DSN`; CI must provide a
   disposable database or the test skips (it never falls back to a persistent one).
4. The PO's staff/admin "internal intelligence" topics are authorized but have no
   data surface yet (I3); I2 establishes only the boundary they must use.
5. `save()` remains an internal-only insert-or-update path; it is explicitly
   documented as not-for-request-use pending the I3/I4 write model.

## 11. Verification boundary

`READY FOR INDEPENDENT OHD I2 VERIFICATION`.

Cline's tests are implementation evidence, not independent verification. I2 is **not**
verified, **not** closed, and **no** later stage was started. The next step is
independent OHD verification of this commit, then PO closure of I2 before any I3
authorization.

---

# 12. OHD I2 FAIL — remediation addendum

**OHD verification:** `OHD-P8-I2-INSIGHT-AUTHORIZATION-20260921`, report commit
`682d5913d572cffc0226844f03cfcf76b2353a38`, implementation under review
`de18c358b35b4378c8a2b8edce257c8c440e8cec`.
**OHD verdict:** **FAIL** — I1 hardening F-01…F-06 verified; I2 authorization largely
correct; but one material ratified requirement failed (customer own-org ALLOW) and one
required matrix row was unenforced (inactive organisation → DENY). I2 NOT closed, I3
NOT authorised.
**Remediation baseline:** `682d591` (branch `p8-release-reconciled`).

## 12.1 F-01 — every real customer was denied (root cause and fix)

**Root cause (confirmed in code).** `auth.py:313` builds the authenticated
organisation-member principal as

```python
role = f"org_{org_role}" if org_role else "org_viewer"
role_name = role
```

so the production role strings are `org_owner` / `org_admin` / `org_member` /
`org_viewer`. `insight_authz` compared against the **bare** forms (`owner`, `admin`,
`member`, `viewer`), so the customer branch never matched and every legitimate
customer received 403 on all five routes.

**Fix (narrowest Insight-specific correction; no global auth change).**
`normalize_org_role()` strips the platform's `org_` prefix (case-insensitively) before
the ratified-role check, so **both** the canonical production form and the bare form
resolve to the same ratified role. `role_name` is left as the platform sets it; no
resolver, middleware or platform authorization code was modified. `auth.py`,
`api/dependencies.py`, `api/operations_auth.py` (beyond the earlier additive alias) and
`api/consultant_auth.py` are **untouched** by the remediation.

**Regression protection.** The I2 test suite now constructs principals **exactly as
`auth.py` does** (`role = role_name = "org_<role>"`): the customer matrix is
parametrised over `org_owner`, `org_admin`, `org_member`, `org_viewer`, and
`test_role_normalization_accepts_production_and_bare_forms` pins the contract. This is
the specific defect class that must not recur.

## 12.2 F-02 — inactive organisation is now DENIED

**Decision applied (PO):** an organisation must be **ACTIVE** for Insight access —
customer **and** consultant.

**Implementation.** `authorize_insight_scope` performs
`organization_is_active(repos, organization_id)` (via the existing
`repositories.organizations.get_by_id(...).is_active`) **before** any scope branch, and
fails closed when the organisation is missing, inactive, or the repository surface is
unavailable. Applied uniformly to every persona (customer, consultant, staff) — the
narrowest rule that satisfies the decision and cannot be gamed by persona choice.

**Why the backend needed an explicit check.** `public.is_org_member()` itself requires
an ACTIVE organisation, so the RLS layer already blocks the client path for a suspended
organisation (live-verified: 0 rows). The backend uses `service_role` (BYPASSRLS), so
the application check is the control on that path.

**Tests.** customer → suspended org: DENY (list, create); suspension takes effect on the
**next read** and restoration returns access; consultant with a valid grant → suspended
customer org: DENY; unknown organisation id: DENY. Live RLS test
`test_suspended_organisation_is_blocked_for_the_client_path` confirms RLS and the
application rule agree.

## 12.3 F-03 — live-RLS test made hermetic

`backend/tests/unit/data/test_i2_insight_rls_live.py` was hard-coded to fixed UUIDs and
used table-wide `count(*)`, so a second run (or any leftover object in the disposable
database) could perturb it. It is now hermetic:

* **fresh UUIDs per run** for both organisations, both users and the conversation — no id
  can collide with, or be counted from, another run's rows;
* **every assertion is scoped to this run's own row** (`WHERE conversation_id = $1` /
  `WHERE organization_id = $1`) instead of counting shared tables;
* one transaction per test, **always rolled back**; no TRUNCATE, no DELETE;
* the DSN guard is unchanged and fail-closed: it refuses any database whose name looks
  persistent (`demo`, `qa`, `investor`, `prod`, `live`) or is a main application database,
  and it **skips** (never falls back) when no DSN is set;
* the intentional RLS rejection runs inside a `SAVEPOINT`, so the surrounding assertion
  transaction stays usable and no ordering coupling remains.

## 12.4 F-04 — disposable test database refreshed

`carbontally_test` predated the consultant engagement/permission migrations, so the
consultant relationship could not be exercised there. Bounded refresh performed **only**
on that disposable database:

| Migration applied | Effect (verified via `information_schema.columns`) |
| --- | --- |
| `20260906090000_p6_1c_consultant_engagement.sql` | `consultant_clients`: **20 → 24** columns (`relationship_origin`, `engagement_requested_at`, `engagement_decided_by`, `engagement_decided_at`) |
| `20260906100000_p6_2a_consultant_processing_permissions.sql` | `consultant_firm_members`: **17 → 23** columns; `can_*` processing flags now **10** |

Both are additive `ADD COLUMN IF NOT EXISTS` + guarded `DO` blocks, applied with
`ON_ERROR_STOP=1` (exit 0 each). No persistent database was touched, no migration file was
modified, and no rows were deleted. The live RLS suite re-ran green afterwards (5 passed).
Live consultant-resolution testing against the current schema is therefore now possible
for OHD; consultant authorization here is covered by the API suite, which drives the
**real** `ensure_consultant_org_access` resolver.

## 12.5 O-01 — auditor denial is now explicit

`is_auditor_principal()` refuses an auditor/assurance-reviewer identity **by name**
(`auditor`, `org_auditor`, `assurance_reviewer`, `auditor_reviewer` — matched on `role`
**and** `role_name`, case-insensitively) and is checked **first** in both
`resolve_insight_persona` and `authorize_insight_scope`, so the refusal is a named
decision rather than a by-product of the absence of a relationship. No auditor role,
table, permission model or invitation model was created (D2 §10.3). A parametrised test
covers all three real spellings, asserting persona `auditor`, `403`, and no writes.

## 12.6 O-02 — staff scope is bounded by existing staff permissions

**Authoritative source (existing, unchanged):** `resolve_staff_context` → ACTIVE
`staff_profiles`; permissions from `staff_roles.permissions` via `staff_profiles.role_id`;
`entity_id IS NULL` = internal staff.

**New bound:** those permissions must actually grant ops-wide customer visibility — the
platform's existing **`can_view_all`** (the permission the operations dashboard itself
requires, `api/v3_operations.py:629`) or the platform's `is_superuser` flag. Staff
identity alone now grants **nothing**.

**Resulting scope.** With `can_view_all`/`is_superuser`: internal-staff scope for any
**active** organisation, still creator-private (the PO decision authorises staff *use* for
internal intelligence, not reading other principals' conversations). Without it: no staff
scope at all; because the platform sets a staff principal's `role` to the *staff* role
name rather than `org_<role>`, such a principal gains no customer scope from membership
either — **deny-by-default**, recorded as a deliberate limitation (§12.11) rather than an
invented fallback. No global staff model was redesigned and no new permission invented.

## 12.7 Consultant authorization — preserved, not regressed

Unchanged by the remediation: `consultant_clients` with `status = 'active'` remains the
single authoritative consultant→customer relationship, resolved by the pre-existing
`api.consultant_auth.ensure_consultant_org_access` (called, not reimplemented). No parallel
relationship exists. The only added condition is the organisation-active check (F-02),
applied **on top of** a valid grant: an ended or absent grant still DENIES, an inactive
firm membership still DENIES, revocation still takes effect on the next read, and an active
grant no longer suffices for a **suspended** customer organisation. API tests cover active
grant / no grant / `ended` grant / multiple authorized customers / unassigned customer
named in the request / revocation.

## 12.8 Tests and regression (remediation)

| Suite | Result |
| --- | --- |
| Focused I1+I2 unit/contract (5 modules) | **58 passed, 5 skipped**, exit 0 |
| Live RLS (disposable `carbontally_test`, hermetic) | **5 passed**, exit 0 |
| Full backend unit suite (`pytest tests/unit --tb=no`) | **4 failed, 2842 passed, 8 skipped in 250.02s** (collected 2,854) |

Regression comparison: pre-I1 2,791 / 4 failures · I1 HEAD 2,808 / 4 failures · I2
implementation 2,841 / 4 failures / 7 skipped · **I2 remediated 2,854 / 4 failures / 8
skipped**. **Delta: +13 tests, +0 new failures.** The 4 failures are the same pre-existing
ones (`test_review_sla_surfaces.py` ×3 and the D17 exact migration-count assertion); none
was fixed and none is attributed to this work. The extra skip is the new live
suspended-organisation test (no DSN in the full-suite run).

**Every-read re-authorization re-verified after remediation:** suspension, membership
revocation and consultant-grant revocation each end access on the next read; restoration
returns it; conversation ids and request parameters cannot expand authorization; no
authorization result is cached across requests.

## 12.9 Files changed by the remediation

* `backend/api/insight_authz.py` — role normalisation (F-01), organisation-active check
  (F-02), explicit auditor refusal (O-01), staff-scope permission binding (O-02)
* `backend/tests/unit/api/test_v3_insight_i2_authorization.py` — production role shapes,
  suspended-organisation cases, staff-permission cases, explicit auditor cases, role
  contract
* `backend/tests/unit/api/test_v3_insight_endpoints.py` — I1 bundle gains the
  organisation-active stub surface
* `backend/tests/unit/data/test_i2_insight_rls_live.py` — hermetic rewrite (F-03) + the
  suspended-organisation RLS case
* this report (this addendum)

No migration was added by the remediation (the I2 migration `20261002000000` is unchanged);
no repository file outside this list was modified, and OHD's verification report was not
touched.

## 12.10 Environment boundaries (remediation)

* **Disposable:** `carbontally_test` — I2 migration re-verified, p6_1c/p6_2a applied
  (F-04), hermetic live RLS suite run. Fixtures are rolled back; no fixture rows persist.
* **Demo Lab (`carbontally_demo_local`): untouched.** **QA (`carbontally_qa_phase8`):
  untouched.** **Production: untouched.** No deployment was performed.

## 12.11 Remaining limitations (post-remediation)

1. A staff principal **with** the ops permission has internal scope over any active
   organisation but remains creator-private; **data-level** staff scope ("within their
   existing staff/admin permissions") is fully enforceable only at the I3 tool layer
   (invariant I-5) — no customer data surface exists yet.
2. A staff principal **without** the ops permission receives no Insight scope at all
   (deny-by-default). If the PO wants such staff to retain customer-workspace Insight for
   their own organisation, the organisation role must be resolved separately from the
   staff role — a product decision, not invented here.
3. The auditor refusal is a role-name vocabulary check because CarbonTally has no auditor
   identity source (D2 §10.3); if an auditor model is ever ratified, this check must be
   re-pointed at it.
4. `can_view_all` / `is_superuser` are the only existing permissions used; a narrower or
   differently shaped staff Insight permission would be a new permission decision.
5. Consultant live-resolver testing is now *possible* in the refreshed disposable database
   (F-04), but this remediation exercised consultant authorization through the API suite
   rather than adding a new live resolver test.

## 12.12 Status

`I2 REMEDIATED — READY FOR OHD RE-VERIFICATION`.

I2 remains **NOT verified** and **NOT closed**; I3 is **not** authorised and was not
started. No LLM/provider, tools, context, UI, audit-interaction, retention or billing work
exists. This addendum is implementation evidence, not independent verification.
