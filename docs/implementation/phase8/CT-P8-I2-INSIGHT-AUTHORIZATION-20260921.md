# CT-P8-I2 — CarbonTally Insight Authorization and Visibility Layer

**Authorization:** `CT-P8-INSIGHT-I2-I8-MASTER-20260921-001` (bounded I1 hardening + I2 only)
**Implementation date:** 2026-09-21
**Branch:** `p8-release-reconciled`
**Starting SHA:** `66adfb5fb45e1945b65202544f74364b83e9df79` (OHD I1 verification, verdict PASS)
**Implementation commit:** `de18c358b35b4378c8a2b8edce257c8c440e8cec`
**Verdict:** `READY FOR INDEPENDENT OHD I2 VERIFICATION` — I2 is **not** independently verified and **not** closed by this report.

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
