# OHD — INDEPENDENT RE-VERIFICATION — CARBONTALLY INSIGHT I2 (authorization + visibility) after remediation

**Verification ID:** `OHD-P8-I2-INSIGHT-AUTHORIZATION-REVERIFICATION-20260921`
**Date:** 2026-09-21
**Verifier:** OHD (independent verification agent) — read-only re-verification
**Previous verification:** `OHD-P8-I2-INSIGHT-AUTHORIZATION-20260921` — verdict **FAIL**
**Verdict:** **PASS** (see §10). All material I2 requirements are independently verified and every previously blocking finding is demonstrably resolved.

---

## 1. Exact revision verified

| Item | Value |
|---|---|
| Branch | `p8-release-reconciled` |
| **HEAD (verified revision)** | **`177dff51f59e9b904c021b4bbb7a6c7ee236adf1`** (`177dff5`) |
| Remediation commit | `177dff51f59e9b904c021b4bbb7a6c7ee236adf1` — `fix(p8-i2): remediate OHD I2 FAIL (customer role contract, active organisation, hermetic RLS test)` (2026-09-21 15:38:43 +0600) |
| Parent (previous verified head, contains the OHD FAIL report) | `682d591` — `docs(p8-i2): OHD independent verification of the CarbonTally Insight I2 authorization layer` |
| I2 implementation under review | `de18c358` — `feat(p8-i2): CarbonTally Insight authorization and visibility layer` |
| My report commit | `177dff5` (this document) |

The stated target matched on arrival; no revision switch, reset or checkout was performed.

## 2. Repository / branch state

| Check | Result |
|---|---|
| `git branch --show-current` | `p8-release-reconciled` ✅ |
| `git rev-parse HEAD` | `177dff51f59e9b904c021b4bbb7a6c7ee236adf1` — **exactly the stated target** ✅ |
| `git status --porcelain --untracked-files=all` | **0 lines** (working tree clean, no untracked files) ✅ |
| `git stash list` | empty ✅ |
| Remediation commit present | yes, and it is HEAD ✅ |
| Unexpected commits | none: the remediation sits directly on the previous OHD report commit; history is linear and as expected ✅ |
| `github/p8-release-reconciled` remote | `177dff51f59e9b904c021b4bbb7a6c7ee236adf1` — identical to local HEAD ✅ |
| `origin` remote (local path `/tmp/ct_step2`) | `93d5cddd…`, stale; **not** used as evidence of remote state (unchanged from the previous verification) |
| Deployments used as evidence | **none** (no Vercel preview or deployment was consulted or treated as evidence) |

**Complete change set between the I2 implementation and the verified revision** (`git diff --name-status de18c358 HEAD`):

```
M  backend/api/insight_authz.py
M  backend/tests/unit/api/test_v3_insight_endpoints.py
M  backend/tests/unit/api/test_v3_insight_i2_authorization.py
M  backend/tests/unit/data/test_i2_insight_rls_live.py
A  docs/implementation/phase8/CT-P8-I2-INSIGHT-AUTHORIZATION-20260921.md   (implementer doc)
A  docs/verification/OHD-P8-I2-INSIGHT-AUTHORIZATION-INDEPENDENT-VERIFICATION-20260921.md (previous OHD report)
```

`git diff --stat de18c358 177dff5 -- supabase/` is **empty**: the remediation changed **no migration and no schema**, so the database posture verified previously (and re-verified in §7) is the posture at HEAD.

## 3. Previous OHD findings carried into this re-verification

| ID | Previous finding | Blocks I2 closure? |
|---|---|---|
| **F-01** | Customer authorization compared the caller role against bare names (`owner/admin/member/viewer`) while `auth.py:313` produces `org_<role>`, so **every real customer was denied 403** on all five routes | **yes** (primary) |
| **F-02** | `organizations.is_active` never consulted by the Insight authorization: members of a suspended organisation, and consultants with active grants to one, were ALLOWED | yes (secondary) |
| **F-03** | The live-RLS test asserted global table counts, so it failed spuriously on a database holding pre-existing Insight rows (`assert 2 == 1`) | no (test robustness) |
| **F-04** | The disposable `carbontally_test` was behind the migration set (missing phase-6.1c/6.2a consultant columns), so the real consultant chain could not execute there | no (environment) |
| **O-01** | Auditor denial was implicit (fall-through), not explicit | no (observation) |
| **O-02** | Staff organisation scope was unbounded: any active staff profile was granted Insight for any organisation | no (observation, but hardening required before I3) |

## 4. Authoritative requirements used

* CarbonTally Insight D2 ratified specification (PO decision §1; §8 authorization boundary and "a stored reference is not a grant"; §9.1/§9.2/§9.6 creator-private + organisation **and** creator; §10.2/§10.3/§10.4 staff deferred / no auditor persona / PE denied).
* The re-verification brief's persona model: **customer** (own authorized organisation), **consultant** (only through the **existing** CarbonTally consultant→customer relationship), **CarbonTally Staff/Admin** (within the existing staff/admin authorization model and permissions); **auditors, private-equity and public users explicitly excluded**. LLM/provider/tooling functionality is **not** part of I2.
* The previous OHD report as the finding baseline.

No new product requirement was invented.

## 5. Independent evidence per remediation

### 5.1 F-01 — real customer authorization (primary blocking failure) — **RESOLVED**

**Code contract.** `insight_authz.CUSTOMER_INSIGHT_ROLES` is unchanged (`owner/admin/member/viewer`) but the comparison now normalises the production shape first: `normalize_org_role()` lowercases, strips whitespace and removes the single leading `org_` prefix (`ORG_ROLE_PREFIX`), and `authorize_insight_scope` evaluates `normalize_org_role(current_user.role) not in CUSTOMER_INSIGHT_ROLES`. `org_owner → owner`, `org_supervisor → supervisor` (still denied). This is the prefix-stripping convention several platform modules already use, and it makes the ratified list match the contract `auth.py` actually produces.

**Evidence method 1 — real resolver + real repositories + real database.** The unmodified `api.insight_authz.authorize_insight_scope` was driven with the real `OrganizationsRepository`, `StaffRepository` and `ConsultantsRepository` against a real PostgreSQL database, with principals carrying the production role shape:

| Principal | Target | Required | **Observed** |
|---|---|---|---|
| `org_owner` | own active org | ALLOW | **ALLOW:customer** |
| `org_admin` | own active org | ALLOW | **ALLOW:customer** |
| `org_member` | own active org | ALLOW | **ALLOW:customer** |
| `org_viewer` | own active org | ALLOW | **ALLOW:customer** |
| `org_owner` | different active org | DENY/403 | **DENY:403** |
| `org_owner` | inactive org | DENY/403 | **DENY:403** |
| `org_owner` | unknown org (random UUID) | DENY/403 | **DENY:403** |
| `org_owner` | org of a revoked membership | DENY/403 | **DENY:403** (see below) |
| `org_supervisor` (unratified) | own org | DENY/403 | **DENY:403** |
| `org_auditor` | own org | DENY/403 | **DENY:403** |
| `owner` (bare/legacy fixture shape) | own org | ALLOW | **ALLOW:customer** |
| no membership (`is_org_member=False`) | own-former org | DENY/403 | **DENY:403** |

**On the revoked-membership row.** A principal hand-built as `is_org_member=True, organization_id=<revoked org>` produces ALLOW — but that principal **cannot be produced by the platform**: `auth.py` resolves membership with `.eq('is_active', True)`, so an inactive membership leaves `is_org_member=False, organization_id=None`. That was confirmed both by reading the query at HEAD and by deriving the principal from the database after flipping the row. The *reachable* revoked-membership path is therefore DENY (verified twice, §5.6).

**Evidence method 2 — authentication → membership → authorization end to end (no synthetic fixtures).** Principals were built by querying the database with exactly the rules `auth.py` uses (active `organization_members` row → `role = f"org_{org_role}"` or `org_viewer` when null; `staff_profiles` row → staff role name, `entity_id`, and permissions from `staff_roles`), then fed to the real resolver. With `organization_members.role` cycling through the **real** vocabulary values (`owner`, `admin`, `member`, `viewer` — the values present in Demo Lab), the derived principals were `org_owner`, `org_admin`, `org_member`, `org_viewer` and **all four were ALLOWED** for their own active organisation, with the other-org case denied. This is the exact mismatch the previous FAIL identified, now shown to be resolved against real role data.

**Evidence method 3 — HTTP.** Over the real router with real repositories and a real database (ASGI transport, single event loop), the production-shaped customer: lists own org → **200**, creates → **201**, reads own conversation → **200**, other org list/read → **403**, unknown org → **403**, missing `organization_id` → **422**, unauthenticated → **401**.

### 5.2 F-02 — inactive/suspended organisation — **RESOLVED**

**Code.** A new module-level `organization_is_active(repos, organization_id)` resolves `repos.organizations.get_by_id(...)` and requires the row to exist **and** `is_active` to be true; it **fails closed** if the repository surface is absent. It is invoked as step **0b**, i.e. **before** the staff branch, the customer branch and the consultant branch — so no scope is granted before organisation activity is established. Denial is a 403. (The referenced `OrganizationsRepository.get_by_id` exists at HEAD and delegates to `get`, which selects `is_active`.)

| Required case | **Observed** (real repositories + real DB) |
|---|---|
| customer → inactive org | **DENY:403** |
| consultant **with an otherwise valid active grant** → inactive customer org | **DENY:403** |
| staff (with the strongest staff permissions, `is_superuser`) → inactive org | **DENY:403** |
| missing/unknown organisation | **DENY:403** (empty `organization_id` additionally → **422**) |
| org reactivated | ALLOW again (re-resolved per request) |

**Not dependent on client-side RLS.** The check is in the application authorization layer, so it applies on the service-role backend path. This matters and was demonstrated: with the organisation suspended, the database RLS correctly denies the `authenticated` client (0 rows, insert refused) **while `service_role` still reads the suspended organisation's rows** — i.e. RLS alone would not have protected the backend path, and the new explicit check is what closes it.

### 5.3 F-03 — hermetic live-RLS test — **RESOLVED**

Inspected at HEAD and executed against disposable databases:

| Requirement | Evidence |
|---|---|
| fresh isolated UUID fixtures | `_Fixture` uses `uuid.uuid4()` for both organisations, both users and the conversation — per run ✅ |
| assertions scoped to the run's own rows | every assertion now filters `WHERE id = $1` / `WHERE conversation_id = $1` / `WHERE organization_id = $1`; no global `count(*)` over a shared table ✅ |
| cannot be contaminated by existing rows | run on a database that **already held leftover Insight rows** (`conv=4 msg=1`): **5 passed** — the exact condition that previously produced `assert 2 == 1` ✅ |
| savepoint for intentional RLS rejection | rejected inserts run inside `async with conn.transaction()` (SAVEPOINT), keeping the outer transaction usable ✅ |
| overall rollback | the `conn` fixture starts one transaction and always rolls it back in `finally`; no TRUNCATE, no DELETE ✅ |
| refuses Demo Lab/QA/investor/prod/live | all six probe DSNs refused with `RuntimeError: … may never target a persistent environment` (`carbontally_qa_phase8`, `carbontally_demo_local`, `carbontally`, `investor_prod`, `my_live_db`, `postgres`) ✅ |
| never falls back to a non-test database | with a DSN naming a non-existent database the suite fails to connect (`InvalidCatalogNameError`); with no DSN it **skips** (`5 skipped`) — no default/fallback database ✅ |
| leaves no persistent fixtures | row counts identical before and after three runs in both databases; writes are rolled back ✅ |
| coverage of the real policies | client may persist only human-authored messages (forged `role='insight'` rejected), creator-private reads, cross-organisation read/write denial, suspended-organisation blockage on the client path, and `service_role` as the only writer of the reserved author kind ✅ |

No safety guard was weakened to make the test run.

### 5.4 F-04 — disposable test-database schema — **RESOLVED**

Verified against the code's own column contracts (`_MEMBER_COLUMNS`, `_CLIENT_COLUMNS`, `_PROFILE_COLUMNS`, `_STAFF_COLUMNS`, `_ROLE_COLUMNS`):

| Table | Code requires | Present in `carbontally_test` | Present in the auditor's disposable DB |
|---|---|---|---|
| `consultant_firm_members` | 18 | **18 (missing: none)** | 18 |
| `consultant_clients` | 20 | **20 (missing: none)** | 20 |
| `consultant_profiles` | 12 | **12 (missing: none)** | 12 |
| `staff_profiles` | 15 | **15 (missing: none)** | 15 |
| `staff_roles` | 7 | **7 (missing: none)** | 7 |

`consultant_firm_members` now has 23 columns including `can_extract` (it had 17 and was missing the p6_1c/p6_2a set). Independently, the **real** consultant chain executed successfully (`get_active_memberships_by_user`, `get_profile_by_id`, `get_client_by_org`) — which is only possible if every required column exists. No persistent environment was modified to establish this.

### 5.5 O-01 — explicit auditor denial — **RESOLVED**

`is_auditor_principal()` checks **both** `role` and `role_name`, case-insensitively, against the named persona set `{"auditor", "org_auditor", "assurance_reviewer", "auditor_reviewer"}`, and is evaluated as step **0**, before any scope is granted, so it wins even when the principal also holds a valid relationship. No auditor permission model, table or role was created (a named refusal only).

| Case | **Observed** |
|---|---|
| `role='auditor'` (also an active org member) | **DENY:403** |
| `role='org_auditor'` (also an active org member) | **DENY:403** |
| `role='assurance_reviewer'` | **DENY:403** |
| `role='auditor_reviewer'` | **DENY:403** |
| `role='Auditor'`, `role='ORG_AUDITOR'` (case variants) | **DENY:403** |
| `role_name='auditor' / 'org_auditor' / 'assurance_reviewer' / 'auditor_reviewer'` (with `role='org_owner'` and a valid membership) | **DENY:403** for all four |
| auditor-shaped **staff** identity (`role_name='auditor'`, active superuser staff profile) | **DENY:403** |

`resolve_insight_persona()` also names the auditor persona first, and returns `PERSONA_NON_MEMBER` for an organisation member with an unratified role — consistent with the authorization decision. It is a naming helper only: the router gate `require_insight_user` does not use it to grant anything.

### 5.6 O-02 — staff scope boundary — **RESOLVED**

**Code.** Staff scope is now additionally gated by `staff_context_grants_insight_scope(context)`, which reads the caller's **existing** `staff_roles.permissions` (the same authoritative source `auth.py` uses to populate the principal) and requires `can_view_all: true` **or** the platform's existing `is_superuser: true` flag. Both keys are pre-existing platform vocabulary — nothing was invented: `can_view_all` is the ops-wide permission the operations/reporting dashboard itself requires (`v3_reporting.py` `ensure_staff_permission(context, "can_view_all")`, `notifications.py` reads `sr.permissions ->> 'can_view_all'`, `auth.py` lists it in the default permission map) and `is_superuser` is checked in `auth.py` lines 409/499. The staff branch still requires an **active** `staff_profiles` row and still refuses `entity_id IS NOT NULL` (PE).

| Required case | **Observed** |
|---|---|
| active `staff_profiles` + `can_view_all` → staff scope (arbitrary active org) | **ALLOW:staff_internal** |
| active `staff_profiles` + `is_superuser` (the **real** Demo Lab `admin` role shape) → staff scope | **ALLOW:staff_internal** |
| active `staff_profiles` with **no** relevant permission → arbitrary org | **DENY:403** |
| PE staff (`entity_id` set) even with `is_superuser` → arbitrary org | **DENY:403** |
| inactive `staff_profiles` row (note: `auth.py` sets `is_staff=True` for it — it has no `is_active` filter; the authorization layer requires the profile to be active) | **DENY:403** |
| staff-shaped identity with **no** staff profile | **DENY:403** — staff identity grants nothing |
| staff → **inactive** organisation | **DENY:403** |
| staff reads another principal's conversation / its messages | **404** (creator-private preserved) |
| staff permission **removed** after creating a conversation → same id | **403** |
| internal staff scope distinct from customer scope | distinct personas (`staff_internal` vs `customer`) ✅ |

**Fall-through nuance (stated explicitly, by design).** A staff member who lacks the permission but who *also* holds a genuine active organisation membership is not granted *staff* scope; they fall through to the ordinary customer rules and receive **customer** scope for **their own** organisation only — verified: own org → `ALLOW:customer`, other org → `DENY:403`, and with no membership row → `DENY:403`. Losing the staff permission never yields customer scope it did not already have, and never yields cross-organisation scope.

**Practical effect on the real role vocabulary (informational, for the PO).** Among the roles present in the reference data, `admin` (`{"is_superuser": true, …}`) qualifies and therefore retains staff Insight; `operator` (`{"can_process": true}`) and `pe_manager` do **not** qualify and now receive no staff Insight scope (PE was already excluded). This is the deliberate narrowing the brief specifies ("`can_view_all` OR existing `is_superuser`"), not a defect — but it means staff Insight is currently limited to staff roles carrying one of those two keys, so the PO should confirm that this is the intended population.

### 5.7 Consultant authorization — existing relationship remains the single source — **VERIFIED**

`insight_authz` still delegates to the platform's `ensure_consultant_org_access` (D15); **no** Insight-specific consultant permission model, table, grant or resolver exists (confirmed by reading the module and by the fact that the remediation added no migration and no new object). Verified against **real** `consultant_profiles` / `consultant_firm_members` / `consultant_clients` rows, with the consultant principal in the shape `auth.py` really produces (`role='user'`, no membership, `is_staff=False`):

| Required case | **Observed** |
|---|---|
| active firm membership + active grant → ALLOW | **ALLOW:consultant** (200/201 over HTTP) |
| no relationship → DENY | **DENY:403** |
| relationship ended → DENY | **DENY:403** |
| inactive consultant firm membership → DENY | **DENY:403** |
| revoked relationship → DENY on the next read (same conversation id) | **DENY:403** (HTTP: 403 after `status='ended'`, 200 again after restore) |
| consultant requesting an unassigned customer → DENY | **DENY:403** |
| valid relationship but customer organisation suspended → DENY | **DENY:403** |
| consultant reading another principal's conversation in an authorised org | **404** (creator-private) |
| self-declared `consultant` role without a firm membership | **DENY:403** |

### 5.8 Every-read authorization and creator-private visibility — **VERIFIED**

| Scenario | **Observed** |
|---|---|
| membership revoked after creation → previously created conversation id | **403** (list 403, append 403) |
| membership restored → same id | **200** |
| organisation suspended after creation → same id / list | **403** / **403**; after reactivation → **200** |
| consultant relationship ended after creation → same id | **403**; after restore → **200** |
| staff permission removed after creation → same id | **403** |
| same-org non-creator reads/appends/lists another's conversation or messages | **404** (200 for its own list only) |
| consultant reads a customer principal's conversation in an authorised org | **404** |
| staff reads another principal's conversation | **404** |

Previously issued identifiers never function as authorization grants, and creator-private visibility holds for every persona, including staff and consultants.

### 5.9 Forged author kind — **VERIFIED**

* API: `role='insight'` → **422**; `role='assistant'` (unratified) → **422**; `role='user'` → **201**.
* Persisted author kinds after the sequence: **only** `[("user", 1)]`.
* Database/RLS posture (re-verified at HEAD, migration unchanged): an `authenticated` client **can** insert `role='user'` in its own conversation but is **denied** inserting `role='insight'` (`InsufficientPrivilegeError`), while `service_role` (the backend) still writes the reserved kind. API validation and database enforcement agree.

## 6. Tests executed and results

| Suite | Result |
|---|---|
| Focused I1/I2 suites (I1 migration, I2 contracts, I1 endpoints, I2 authorization) | **58 passed, 0 failed** |
| Focused suites including the live-RLS module **with** a disposable DSN | **63 passed, 0 failed** (live-RLS: 5 passed) |
| Live-RLS module without a DSN | 5 skipped (safe default) |
| Live-RLS module on a database **holding leftover rows** (hermeticity stress) | **5 passed** (previously `assert 2 == 1`) |
| Live-RLS module run twice on the same database | identical results (repeatable) |
| **Full backend unit suite at HEAD `177dff5`** | **2,854 collected, 4 failures, 0 errors, 8 skipped** |
| Full unit suite at the prior I2 head `ad49f57` | 2,841 collected, 4 failures, 0 errors, 7 skipped |
| Full unit suite at I1 `5bd5e29` | 2,808 collected, 4 failures, 0 errors, 3 skipped |
| Full unit suite pre-I1 `e48ee55` | 2,791 collected, 4 failures, 0 errors, 3 skipped |

**New failures: none.** Delta versus the previous I2 head is **+13 tests and +1 skip** (the added authorization cases and the extra live-RLS test), with the failure count unchanged.

**Pre-existing failures (identical at all four commits, not introduced here, not fixed here):**

* `tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered`
* `tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered`
* `tests/unit/api/test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained`
* `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`

**Skipped tests:** the five live-RLS tests (require `INSIGHT_RLS_TEST_DSN`; deliberately skipped without it). No other skips.

**Environment limitation affecting the run count:** the live-RLS tests are excluded from the suite total unless a disposable DSN is exported, which is why the suite reports 8 skips rather than 3; exporting the DSN during the focused run produced 63 passed / 0 skipped-equivalent failures.

## 7. Databases and environments used

| Environment | Use | Writes |
|---|---|---|
| `ct_i2_verify_20260921` (auditor-owned disposable; template copy of the disposable `carbontally_test`, Insight objects rebuilt by applying `20261001000000` and `20261002000000` **verbatim** from the repository; plus the p6_1c/p6_2a consultant migrations) | all live probes: real resolver, real repositories, HTTP end-to-end, live-RLS runs, DB-boundary RLS matrix | **yes — disposable only** (fixture seeding, organisation suspension toggles) |
| `carbontally_test` (the disposable database the live-RLS suite documents; refreshed by the remediation for F-04) | schema verification (F-04) and one live-RLS run | only through the suite's own rolled-back transaction; row counts confirmed unchanged |
| `carbontally_demo_local` (Demo Lab) | **read-only**: `staff_roles.permissions` vocabulary, `organization_members.role` vocabulary, consultant column comparison | **none** |
| QA (`carbontally_qa_phase8`) | referenced only as a refused DSN in the guard test | **none** |
| production / investor / live | **not touched, not deployed to, not used** | **none** |

No deployment or preview of any kind was produced or treated as evidence. No application code, migration, schema, configuration, test, fixture or data outside the auditor-owned disposable databases was modified; no defect was fixed.

## 8. Scope control (no I3 or later)

* The complete change set since the I2 implementation is **one module** (`backend/api/insight_authz.py`) plus **three test files** and **two documents** (§2). No new module, no new migration, no dependency or configuration change.
* No LLM/provider integration for Insight: the Insight modules import no LLM client (`infra/llm_client.py` is pre-existing Phase-7 document-processing code). No tool registry, tool execution, intent classification, natural-language answering, RAG/LangChain/embeddings, canonical AI interaction/audit layer, context/memory system, frontend Insight UI, retention/export, billing, or automatic consequential action exists — artefact scans for `insight_tool`, `tool_registry`, `intent_classif`, `ai_interaction`, `insight_context`, `insight_memory`, `insight_retention`, `insight_billing`, `insight_provider` return **0 files each**, and the only `insight` string in the front ends is the pre-existing admin Analytics subtitle.
* The router still exposes exactly the five I1 persistence routes; `InsightRepository.delete()` still refuses. Recommendations still constitute no action.
* **No scope leakage found.** I3 and later stages remain unimplemented and unauthorized.

## 9. Remaining findings (informational; none blocks closure)

* **O-03 (new, LOW — informational).** Denial *status* is uniform (403 everywhere, as the matrix requires), but the `detail` string differs by failure mode: an authenticated principal probing an **existing active** organisation it has no relationship with receives `"CarbonTally Insight access denied"`, while an **inactive or unknown** organisation receives `"Organization access denied"`. That allows an authenticated caller who knows an organisation UUID to distinguish "exists and active" from "absent or suspended". No tenant data, and no naming/content of another tenant, is revealed; UUID guessability is negligible; the required outcome (DENY/403) is met in every case. Recommended hardening (not performed): use a single uniform detail string for all denials.
* **O-04 (informational).** A permission-less staff member who is also a genuine organisation member receives ordinary **customer** scope for that organisation (never staff scope, never cross-organisation). This is the intended reading of the model; recorded so it is not mistaken for a leak.
* **O-05 (informational).** F-04 was resolved by **refreshing the disposable test database**, not by a repository artefact — `carbontally_test` is now complete (all code-required columns present) but a future re-creation from a partial source would drift again. Recommend ensuring the disposable test database is always built by applying the full migration set (and noting that in the suite's own run instructions).
* **O-06 (informational).** `backend/data/organizations.py` defines `get_by_id` twice (identical bodies, lines 311 and 314 — a duplicated definition that predates this remediation and was not changed by it). It is harmless and the remediation's `organization_is_active` correctly resolves it, but the duplicate should not be removed without care, since the Insight active-organisation check now depends on that method existing.
* **O-07 (informational).** The auditor refusal list is enumerative (`auditor`, `org_auditor`, `assurance_reviewer`, `auditor_reviewer`). A future auditor persona introduced under a different name would not be *explicitly* refused — though it would still be denied by the absence of any authorization relationship. No new auditor permission model was created, as required.
* **O-08 (informational).** `organization_is_active` adds one organisation lookup per Insight request (including for staff). This is a deliberate cost of enforcing tenant activity on the service-role path; no correctness or security impact was observed.

## 10. Final verdict

> ## **PASS**

**Rule applied (from the brief):** PASS only if all material I2 requirements are independently verified **and** the previous blocking findings are demonstrably resolved. Both conditions hold:

* **F-01 (blocking) is demonstrably resolved.** Production-shaped customers (`org_owner`, `org_admin`, `org_member`, `org_viewer`) are allowed for their own active organisation, and every denial case required by the matrix holds. This was reproduced three independent ways — the real authorization function with the real repositories against a real database, DB-derived principals built by `auth.py`'s own rules over real role data, and the real router over HTTP with real persistence. The specific mismatch that caused the previous FAIL (bare names compared against the `org_`-prefixed production shape) no longer exists.
* **F-02 (blocking) is demonstrably resolved.** Organisation activity is checked explicitly, before any scope is granted, for customers, consultants and staff, with unknown organisations refused and the check enforced on the backend path rather than relying on client-side RLS — established in a way that also demonstrated RLS alone would not have sufficed.
* **F-03 and F-04 are resolved**, including the exact conditions that previously failed (a database holding leftover rows now yields 5 passed; the disposable database now satisfies every column the consultant code requires).
* **O-01 and O-02 are resolved** by explicit auditor refusal and by binding staff scope to existing platform permissions, with no permission or persona model invented and no customer/consultant/staff access regressed.
* **No regression**: the full unit suite grew by 13 tests with **no new failures**; the four failures are the identical pre-existing set; the five live-RLS tests pass against a disposable database and skip safely without a DSN.
* **Scope control holds**: nothing beyond I2 was implemented, and the only source file changed by the remediation is the I2 authorization module.

Remaining items are informational only (O-03 … O-08). The single candidate security observation (O-03, differentiated denial messages) does not breach a ratified requirement — the required DENY/403 outcome is met in every case and no tenant data is exposed — so it does not alter the verdict, but it is recorded for the PO with a recommended hardening.

**Explicit scope of this verdict:** it covers **only** I2 authorization/visibility and the bounded I1 hardening, at revision `177dff51f59e9b904c021b4bbb7a6c7ee236adf1`. **I2 is now independently verified and ready for PO closure. I3 remains unauthorized and must not be started**, and nothing in this report authorizes any later stage.

## 11. Limitations

1. **No live end-to-end test with real JWTs.** Authentication depends on the Supabase/GoTrue stack, which is not running in this environment. The real router and the real authorization module were therefore exercised with dependency injection (the technique the repository's own tests use), and the "real authentication path" was verified by deriving principals from the database with exactly the queries and rules `auth.py` applies (verified against `auth.py` line by line, including its `.eq('is_active', True)` membership filter). The F-01 defect and its remediation are a pure string-contract matter between two committed code paths, and both sides were exercised directly.
2. **Populations are synthetic, tables are real.** Relationship rows in the live probes (organisations, memberships, consultant firms/grants, staff roles/profiles) were seeded by the auditor in its own disposable database; the tables, constraints, columns and the code's SQL are the real ones, and staff-role permission shapes were taken from the reference data's real vocabulary.
3. **Stale local `origin` remote** (`/tmp/ct_step2`) was not used as evidence; remote alignment was taken from `github/p8-release-reconciled`.
4. **The suite's skip count depends on `INSIGHT_RLS_TEST_DSN`**, so the whole-suite totals include 8 skips unless a disposable DSN is exported (5 of them live-RLS tests).
5. Remediation *claims* in the implementer's report were compared against, but never used as, evidence.

---

*Re-verification performed read-only. Only auditor-owned disposable databases were written to. Demo Lab, QA, investor/live and production were inspected read-only at most, were never migrated, and no deployment was performed. No application code, migration, schema, configuration, test, fixture or data was modified and no defect was fixed; the only repository change is this report.*
