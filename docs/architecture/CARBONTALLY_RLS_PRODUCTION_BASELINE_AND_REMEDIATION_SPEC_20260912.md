---
Document Type: Security Discovery & Remediation Specification (READ-ONLY — no changes made)
Project: CarbonTally
Prompt ID: CT-SEC-RLS-PRODUCTION-BASELINE-AND-REMEDIATION-SPEC-20260912-001
Predecessor: CT-SEC-RLS-PRODUCTION-ACTIVATION-20260912-001 (PO-ratified security checkpoint)
Status: SPECIFICATION ONLY — no implementation, no migration, no policy/grant/RLS change
Created: 2026-09-12
Supersedes: the UNVERIFIED production baseline in the predecessor report
---

# CarbonTally — RLS Production Baseline & Remediation Specification

## 1. Executive Conclusion

**The production Supabase baseline is now VERIFIED.** It was obtained read-only
via the linked Supabase CLI (`supabase db dump --linked --schema public`,
schema-only, no data). The production project is `pvwiojoyaqywtydzcpbg`
(ACTIVE_HEALTHY, eu-west-2).

The result is materially worse than the predecessor discovery could establish,
and it inverts the risk model:

> **Production `anon` holds `GRANT ALL` on 104 of 104 tables. RLS is enabled on
> only 7 of 104 tables. Therefore 97 of 104 tables (93%) are readable *and
> writable* by the anonymous role through PostgREST using the public anon key
> that ships in the frontend bundle.**

The ~153 Advisor findings are therefore **not** 153 cosmetic notices, and they
are **not** 153 distinct vulnerabilities. They are two
development-posture artefacts amplified by one privilege-model defect:

| Advisor-facing artefact | Verified production count | Nature |
|---|---|---|
| "Policy Exists RLS Disabled" | **50 tables** | dev posture — policies created, RLS never enabled |
| "RLS Disabled in Public" (policyless) | **47 tables** | dev posture — no RLS *and* no policy |
| Total tables with RLS disabled | **97 of 104** | the real number that matters |

**Root cause (now evidenced, not hypothesised).** The RLS-enablement floor is a
bulk `DO` loop at the end of
`supabase/migrations/00000000000000_init_schema.sql:2319-2324`. That loop was
introduced by commit `dbe72aa` into a migration **already recorded as applied in
production**. Editing an applied migration never re-executes it, so production
never ran the bulk enable. The only RLS enablements that reached production are
the seven per-table `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` statements
inside *other*, later-applied migrations — and the arithmetic matches exactly
(4 + 1 + 1 + 1 = **7**). The RC1/RC2 schema storeys that underlie production
contain **zero** RLS enablement
(`database/rc1/001_rc1_schema.sql`: 0; `database/rc2/00000000000000_init_schema.sql`: 0).

**Recommended immediate action.** A single, small, low-risk, independently
authorizable step should precede the whole programme: revoke the blanket
`anon`/`authenticated` grants (§8, RLS-4A). It does not require any RLS change
and closes the anonymous exposure. The remainder of the programme
(RLS-4 → RLS-5 → RLS-3 → RLS-2 → RLS-1 → verification) proceeds as ratified.

**Nothing was changed.** No DDL, DML, policy, grant, RLS, config, code, or
production state was modified.

---

## 2. Production Baseline

**Source of truth:** `supabase db dump --linked --schema public` (schema only —
*no* `--data-only`; no row data was read). Dump written outside the repository to
`/tmp/prod_public_schema.sql` (232,366 bytes, 6,331 lines). Every figure below is
read directly from that dump unless labelled otherwise.

### 2.1 Tables (Part A.1)

| Metric | Production (VERIFIED) | Local dev DB (VERIFIED, for contrast) |
|---|---|---|
| Public tables | **104** | 116 |
| RLS enabled | **7** | 116 |
| RLS disabled | **97** | 0 |
| `FORCE ROW LEVEL SECURITY` | **0** | 0 |
| Table owner | `postgres` (all 104) | `postgres` (all 116) |

**Tables with RLS ENABLED (7):**

```text
calculation_snapshots   customer_factors   domain_events
factor_aliases          import_batches     issues
processing_entities
```

These seven are exactly the tables carrying a per-table `ENABLE ROW LEVEL
SECURITY` inside an applied migration:
`20260807070000_add_new_table_rls.sql` (4),
`20260810000000_v3m1_processing_entities.sql` (1),
`20260810020000_v3m3_customer_factors.sql` (1),
`20260810040000_v3m5_issues.sql` (1).

### 2.2 Policies (Part A.2)

| Metric | Production | Local |
|---|---|---|
| `CREATE POLICY` statements | **179** | 174 |
| Tables with ≥1 policy | **55** | 58 |
| Policies targeting `authenticated` | **179 (100%)** | 174 |
| Policies targeting `anon` | **0** | 0 |
| Restrictive policies | **0** (all permissive) | 0 |

**No policy in production faces `anon`.** This is the single most important
structural fact in the whole baseline: RLS, where it is on, is a complete
deny-all for the anonymous role, and the only thing standing between `anon`
and the tenant database is `relrowsecurity`.

### 2.3 Grants (Part A.3)

| Grantee | Table privileges in production |
|---|---|
| `anon` | **`GRANT ALL` on 104 / 104 tables** |
| `authenticated` | `ALL` on 96 tables; `SELECT,INSERT,UPDATE,DELETE` (no `TRUNCATE`) on 8 |
| `service_role` | `ALL` on all tables |
| Schema `USAGE` | granted to `postgres`, `anon`, `authenticated`, `service_role` |

**`emission_factors` specifically:** RLS **disabled**, **0 policies**, and
explicit `GRANT ALL ... TO "anon"` and `GRANT ALL ... TO "authenticated"`.
The predecessor's empirically observed anonymous read of 7,049 rows is hereby
confirmed as a *privilege + RLS-state* consequence, not a policy anomaly.

> **Effective production exposure: `anon` ALL + RLS disabled on 97 tables.**
> This includes `organizations`, `organization_members`, `users`,
> `password_reset_tokens`, `audit_trail`, `system_settings`, `login_history`,
> `staff_roles`, `emissions_logs`, `messages`, `customer_documents`,
> `organization_files`, and `report_versions`.

**Evidence limitation — column privileges (Part A.3, partial):** a `pg_dump`
schema dump does **not** emit column-level ACLs or *default* privileges.
Production column-level grants are therefore **UNVERIFIED**. The table-level
`GRANT ALL` statements above are explicit and VERIFIED (they are non-default, so
`pg_dump` emitted them).

### 2.4 Functions (Part A.4)

| Metric | Production | Local |
|---|---|---|
| Public functions | **7** | 21 |
| `SECURITY DEFINER` | 7 | 17 |
| `search_path` pinned | all `SECURITY DEFINER` (none mutable) | same |
| Functions with `EXECUTE` granted to **`anon`** | **7 of 7** | 17 (via `PUBLIC` default) |
| `REVOKE ... FROM PUBLIC` | 2 only (`anonymise_user`, `is_entity_member`) | — |

Production function inventory with `anon` `EXECUTE`:

```text
anonymise_user            is_entity_member        is_org_active
is_org_admin_or_owner     is_org_consultant       is_org_member
set_updated_at
```

`anonymise_user(p_user_id, p_actor_id, p_reason)` is a `SECURITY DEFINER`
**data-mutating** function whose `EXECUTE` is explicitly granted to `anon`. Its
internal authorization guard was **not** fully evaluated in this pass and is
flagged in §6 (F-6) and §13 as a required review item — it is **not** declared
safe or unsafe here.

Note production **lacks** the `is_consultant_firm_*` helper family, because
`20260822000000_p9_rls_recursion_fix.sql` is not applied (see §5).

### 2.5 Production migration state (Part A.5)

Obtained read-only via `supabase migration list --linked`.

| Metric | Value |
|---|---|
| Migrations recorded applied in production | **21** (through `20260810050000`) |
| Repository migration files | **55** |
| Repository migrations **NOT** applied | **34** |
| Remote-only migration records (in prod, absent locally) | **0** |
| History consistency | consistent — no orphan production migration records |

Applied: `00000000000000`, `20260800000000` … `20260807070000`, `20260810000000`,
`20260810010000`, `20260810020000`, `20260810040000`, `20260810050000`.

### 2.6 Table inventory divergence

12 repository tables do not exist in production:

```text
billing_commercial_config    billing_credit_ledger      billing_idempotency_keys
billing_orders               billing_payment_records    billing_plans
billing_storage_usage        consultant_custom_domains  consultant_senders
data_discovery_requests      vehicles                   work_item_assignments
```

0 production tables are absent from the repository. Production is a strict
subset.

---

## 3. Verified vs Unverified Evidence

### VERIFIED (production, read directly)

* Table list, `relrowsecurity`, `relforcerowsecurity`, owner — all 104 tables.
* All 179 policies: table, name, command, role, `USING`, `WITH CHECK`, permissiveness.
* Table-level `GRANT`/`REVOKE` statements (explicit, non-default ACLs).
* Function list, `SECURITY DEFINER` flags, `search_path`, function `EXECUTE` grantees.
* Migration history (21 applied / 34 outstanding), 0 orphan records.
* Absence of the RLS-enablement floor in `database/rc1` and `database/rc2`.
* Presence of the RLS-enablement floor in commit `dbe72aa`
  (`supabase/migrations/00000000000000_init_schema.sql`).
* Local dev DB state (116 tables, 116 RLS-enabled, 174 policies, 0 recursive policies).

### INFERRED (high confidence, not directly observed)

* **Live exploitability of the `anon` exposure.** The *capability* is verified
  (grants + RLS state). Live exploitation was **not** attempted, because it would
  read or mutate production data. PostgREST behaviour is used only as
  **supporting evidence**: the predecessor reconciliation *did* observe `anon`
  returning 7,049 rows from `emission_factors`, and `frontend/src/supabaseClient.js`
  constructs the client with the **public** anon key. PostgREST exposes the
  `public` schema (`supabase/config.toml`: `schemas = ["public","graphql_public"]`).
* **Default privileges on production tables.** `pg_dump` does not emit defaults;
  the explicit `GRANT ALL` statements above are non-default and therefore
  authoritative, but any *additional* default privileges are not enumerable from
  the dump.
* **Realtime cross-tenant broadcast.** `postgres_changes` honours RLS for the
  subscriber. With RLS disabled on all seven subscribed tables, a subscriber
  would receive other tenants' row changes. Mechanically inferred from the
  verified RLS-disabled state; not dynamically tested.
* **Drift mechanism** (applied-migration edit in `dbe72aa`). The *state* is
  verified and the arithmetic matches exactly; the causal history is inferred
  from `git log -S`.

### UNVERIFIED

* Production **column-level** privileges.
* Production **`ALTER DEFAULT PRIVILEGES`** entries.
* `anonymise_user` internal authorization guard.
* Actual production **row counts / data volumes** (no data was read — deliberate
  privacy constraint).
* The exact Supabase **Advisor export** (never present in the repository).

> **UNVERIFIED — the Supabase Advisor export itself was not available; the
> Advisor-facing counts in §1 are derived from verified catalog state, not from
> the Advisor report.**

---

## 4. Actual Production Risk Classification

Classification is by *data sensitivity × access path × verified privilege*, not
by lint severity.

| Class | Basis | Tables | Examples |
|---|---|---|---|
| **CRITICAL** | `anon` ALL + RLS disabled + credential/identity/audit content | 8 | `password_reset_tokens`, `users`, `organization_members`, `login_history`, `user_invitations`, `pending_invites`, `audit_trail`, `system_settings` |
| **CRITICAL** | `anon` ALL + RLS disabled + tenant/customer content | 39 | `organizations`, `emissions_logs`, `messages`, `conversations`, `customer_documents`, `organization_files`, `customer_factors`, `facilities`, `assets`, `suppliers`, `issues`, `calculation_snapshots`*, `report_versions` |
| **HIGH** | `anon` ALL + RLS disabled + internal operational data | 30 | `processing_*`, `qc_*`, `staff_*`, `sla_*`, `queue_settings`, `beta_users`, `notification_delivery`, `email_logs` |
| **HIGH** | `anon` ALL + RLS disabled + cross-tenant Realtime broadcast | 7 (overlap) | `notifications`, `customer_documents`, `customer_verifications`, `activity_feed`, `messages`, `manual_review_queue`, `staff_workload` |
| **MEDIUM** | `anon` ALL + RLS disabled + low-sensitivity / reference | 20 | `units`, `roles`, `glossary`, `document_types`, `activity_categories`, `emission_factors`, `typing_status`, `user_presence` |
| **SAFE (RLS on + no anon policy)** | RLS blocks the granted privileges | **7** | `calculation_snapshots`, `customer_factors`, `domain_events`, `factor_aliases`, `import_batches`, `issues`, `processing_entities` |
| **UNKNOWN** | Requires column/default-privilege data | — | column-level grants |

\* `calculation_snapshots` and `issues` are RLS-enabled and therefore SAFE for
`anon`; they appear above only inside the tenant-content family.

**Application compatibility note (important):** the direct-client surface is
narrower than the predecessor report assumed — see §7. The frontend performs
**no direct table CRUD**; it uses Supabase only for **auth** and **Realtime**.
The PostgREST table exposure is therefore currently *latent* rather than
exercised by the product — which lowers the probability of accidental
cross-tenant access through the app, but does **not** reduce the exposure,
because the anon key is public and the database is reachable directly.

---

## 5. Migration Drift Reconciliation (Part C)

### 5.1 The 21 applied / 34 outstanding

Full outstanding list with RLS/security relevance (statement counts = occurrences
of `ROW LEVEL SECURITY`, `CREATE POLICY`, `GRANT`, or `REVOKE`):

| Migration | RLS/GRANT stmts | Classification |
|---|---|---|
| `20260821000000_d20_d15_active_consultant_grant` | 3 | **A** — consultant grant model; prerequisite to consultant policies |
| `20260821010000_d21_white_label_branding` | 0 | **B** — branding; independent of RLS |
| `20260821020000_d22_processing_work_assignment` | 3 | **A** — assignment/scope |
| **`20260822000000_p9_rls_recursion_fix`** | **8** | **A — HARD PREREQUISITE** (see §5.2) |
| `20260822010000_d27_d19_customer_lifecycle` | 8 | **A** — 3 new tables + RLS |
| `20260823000000_d32_private_documents_storage` | 5 | **A** — `storage.objects` RLS; **NONIDEM** (4 unguarded `CREATE POLICY`) — apply once |
| `20260823010000_d33_evidence_traceability` | 0 | **C** — additive |
| `20260824010000_d35_self_service_onboarding` | 0 | **B** — onboarding; product decision |
| `20260824020000_d37_0_billing_security_and_configurable_subscription` | 14 | **B** — billing schema + RLS + GRANT; **DML (seeds)**; separate review |
| `20260824030000_d37_master_commercial_billing` | 6 | **B** — billing; **DML** |
| `20260825000000_v3m7_vehicles` | 8 | **C** — new table + RLS/grants, self-contained |
| `20260828000000_v3m8_messaging_unique_participants` | 0 | **C** |
| `20260828010000_v3m8_system_admin_role_model` | 0 | **B** — role model change |
| `20260828020000_v3m8_pe_manager_role` | 0 | **B** — role model change |
| `20260829000000_v3m9_durable_automatic_processing` | 0 | **B** — durable processing |
| `20260831000000_v3m10_org_membership_unique` | 0 | **A** — membership uniqueness, affects `organization_members` |
| `20260831010000_v3m11_operational_indexes` | 0 | **C** — indexes (performance lints) |
| `20260831020000_audit_activity_immutability` | 2 | **A** — immutability RLS |
| **`20260831030000_tenant_org_id_not_null`** | 0 | **A — HARD PREREQUISITE** (see §5.2) |
| `20260831040000_consultant_revocation_roles` | 6 | **A** — consultant policies |
| `20260902020000_v1_2_dual_origin_workflow` | 0 | **C** |
| `20260902030000_phase5_work_item_assignments` | 1 | **C** — new table + RLS |
| `20260902040000_phase5_pe_operational_messaging` | 3 | **A** — messaging scope |
| `20260902050000_phase5_notification_event_key` | 0 | **C** |
| `20260903010000_ws4_gate3_4a_item_assignment_foundation` | 5 | **A** — assignment/scope |
| `20260905000000_gate4_actor_provenance` | 0 | **C** |
| `20260905010000_gate5_t1_automation_provenance` | 0 | **C** |
| `20260905020000_gate5_t6_automation_write_once_guard` | 0 | **C** |
| `20260906010000_gate6_w1_automation_extracted_output` | 0 | **C** |
| `20260906090000_p6_1c_consultant_engagement` | 2 | **A** — consultant engagement |
| `20260906100000_p6_2a_consultant_processing_permissions` | 0 | **B** — permissions |
| `20260910120000_p6_2d_consultant_provenance` | 1 | **A** — consultant provenance |
| `20260912000000_p7_audit_immutability_and_indexes` | 0 | **A** — Phase 7 audit immutability |
| `20260913000000_p8_report_lifecycle_status` | 0 | **C / D** — additive; **no RLS change** (verified in source and in predecessor discovery) |

Class key: **A** must apply before RLS activation · **B** must NOT be applied
automatically (separate review; several carry DML/role/product changes) ·
**C** safe and independent · **D** already reflected despite history discrepancy ·
**E** unknown/insufficient evidence.

**D instances: 0.** Production's 7-table RLS enablement is fully explained by
applied migrations, so no "silently applied" migration is evidenced.

### 5.2 Hard prerequisites demonstrated by production evidence

Two findings make these **mandatory before any RLS enablement on the affected
tables** — not optional:

**(i) `20260822000000_p9_rls_recursion_fix` is NOT applied, and production still
carries the recursive policies — VERIFIED.** Four production policies embed
inline self-referential subqueries on their own table:

```text
organization_members      om_insert_admin
organization_members      om_select_self_or_admin
organization_members      om_update_admin
consultant_firm_members   cfm_select_self_or_team_admin
```

These are the exact pre-fix forms repaired on 2026-08-22 locally. Today they are
inert (RLS is off on both tables). **Enabling RLS on `organization_members` or
`consultant_firm_members` before applying this migration will reproduce the
original P1 defect: infinite recursion on every direct authenticated read.**
Production also lacks the `is_consultant_firm_member` /
`is_consultant_firm_revoker` / `is_consultant_team_admin` helpers the fix
introduces (verified: production has 7 functions; the helpers are absent), so the
policies cannot simply be enabled as-is.

**(ii) `20260831030000_tenant_org_id_not_null` is NOT applied.** The RC1 file
records the reason RLS alone is insufficient: *"NULL `organization_id` rows fall
outside every tenant-equality policy (tenancy hole)"*
(`database/rc1/004_rc1_rls.sql`, header). Enabling tenant RLS while nullable
`organization_id` rows exist leaves those rows outside every predicate — a
tenancy hole that RLS will *not* close.

### 5.3 Dependency ordering (specification only — nothing applied)

```text
1. 20260807070000 / 20260810000000 / 20260810020000 / 20260810040000  (ALREADY APPLIED)
2. 20260821000000 d20_d15_active_consultant_grant        -> consultant model
3. 20260821020000 d22_processing_work_assignment
4. 20260822000000 p9_rls_recursion_fix                   -> HARD PREREQUISITE (recursion)
5. 20260831000000 v3m10_org_membership_unique
6. 20260831020000 audit_activity_immutability
7. 20260831030000 tenant_org_id_not_null                 -> HARD PREREQUISITE (tenancy hole)
8. 20260831040000 consultant_revocation_roles
9. 20260902040000 phase5_pe_operational_messaging
10. 20260903010000 ws4_gate3_4a_item_assignment_foundation
11. 20260906090000 p6_1c_consultant_engagement
12. 20260910120000 p6_2d_consultant_provenance
13. 20260912000000 p7_audit_immutability_and_indexes
14. 20260822010000 d27_d19_customer_lifecycle            (RLS + 3 new tables)
15. 20260823000000 d32_private_documents_storage         (storage RLS; NONIDEM — once)
16. 20260825000000 v3m7_vehicles | 20260902030000 phase5_work_item_assignments
17. 20260824020000 d37_0_billing_* | 20260824030000 d37_master_*   (SEPARATE REVIEW — DML)
18. remaining class-C migrations in timestamp order
```

**Do not apply 2–15 as part of the RLS activation migration.** They are separate
product/security migrations requiring their own authorization; this ordering
expresses *dependency*, not a batched release.

---

## 6. F-1 … F-9 Disposition (Part B)

| # | Finding | Production disposition | Evidence |
|---|---|---|---|
| **F-1** | `organization_members.om_update_self` self-role escalation | **VERIFIED production vulnerability (policy), currently masked AND amplified.** Policy text identical to local: `USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid())` — no `role` constraint. RLS is **disabled** on `organization_members`, so today the predicate is inert and the exposure is the broader one (any authenticated user may read/update any row given `authenticated` `ALL`). Once RLS is enabled, the narrow escalation (a member setting their own `role`) becomes reachable. **Must be fixed in RLS-5 before RLS-1.** | dump policy text; RLS=False |
| **F-2** | `organizations_org_update` over-broad member update | **VERIFIED production vulnerability (policy).** `USING is_org_member(id) WITH CHECK is_org_member(id)` — no owner/admin predicate. Same masking/amplification logic as F-1. | dump policy text; RLS=False |
| **F-3** | Anonymous read of `emission_factors` | **VERIFIED — and materially broader than reported.** Not just readable: `anon` has explicit `GRANT ALL` on it and RLS is disabled, so anonymous **write** capability is also granted. Product requirement status is **REQUIRES PO DECISION** (§13 Q4). | dump: RLS=False, 0 policies, `GRANT ALL TO anon` |
| **F-4** | Broad `anon` SELECT grants | **VERIFIED — escalated to the primary finding.** Not merely `SELECT`: `anon` holds `GRANT ALL` on **104/104** tables and RLS is disabled on **97**. Anonymous read **and write** capability on 93% of the production database. | dump grant matrix |
| **F-5** | `anon`/`authenticated` `TRUNCATE` | **VERIFIED (privilege), not reachable via PostgREST.** `anon` has `ALL` (incl. `TRUNCATE`) on all 104 tables. `TRUNCATE` is not gated by RLS and is not exposed as a PostgREST verb, so exploitation requires direct DB access — defence-in-depth, not an API exposure. Note `authenticated` retains `TRUNCATE` on 96 tables (the 8 explicit-grant tables correctly exclude it). | dump grants |
| **F-6** | `PUBLIC`/`anon` EXECUTE on `SECURITY DEFINER` helpers | **VERIFIED — `anon` `EXECUTE` on all 7 production functions**, including the data-mutating `anonymise_user` and trigger function `set_updated_at`. Only 2 functions have `REVOKE ... FROM PUBLIC`. Impact of the helper family is a limited existence oracle; **`anonymise_user` requires dedicated review (UNVERIFIED guard)**. **REQUIRES PO/SECURITY DECISION** on which functions are intentional RPCs (§13 Q5). | dump function ACLs |
| **F-9** | `users_update_self` over-broad self-update | **VERIFIED policy present in production** (`USING/WITH CHECK id = auth.uid()`); RLS disabled on `users`. Production `users` **column set not enumerated in this pass** — precise exploitability **UNVERIFIED**; column-level privileges also UNVERIFIED. | dump policy text |
| **NEW — recursion** | Pre-fix recursive policies still in production | **VERIFIED.** 4 policies with inline self-reference; p9 fix not applied. Highest-priority prerequisite. | dump policy bodies; migration list |
| **NEW — Realtime** | Cross-tenant `postgres_changes` broadcast | **INFERRED (high confidence)** from verified RLS-disabled state on all 7 subscribed tables. | dump RLS flags; `lib/realtime/manager.js` |
| **NEW — process** | Applied migration edited after being applied | **VERIFIED.** Bulk-RLS loop introduced in `dbe72aa` into an already-applied `init_schema`; RC1/RC2 copies contain no enablement. | `git log -S`; file greps |
| **RLS deny-all tables (58 local / 47 prod)** | Special requirement F | **Classification below (§6.1).** Production: 47 tables with no RLS and no policy; 2 with RLS and no policy. | dump |

**No inference has been promoted to a production fact.** Live exploitation of
F-1/F-3/F-4 was **not tested**.

### 6.1 Classification of the policy-less tables (Special requirement F)

Ratified direction is *not* to add policies to all of them. Production has
**47** RLS-disabled/no-policy tables plus **2** RLS-enabled/no-policy tables.

| Classification | Tables |
|---|---|
| **Intentionally service-only** (backend-only; no client policy needed) | `audit_trail`, `processing_audit_trail`, `processing_assignments`, `processing_steps`, `processing_time_log`, `qc_checks`, `qc_checklists`, `qc_errors`, `queue_settings`, `sla_compliance`, `sla_definitions`, `staff_activity_log`, `staff_daily_performance`, `staff_performance`, `staff_roles`, `staff_workload`, `team_performance`, `system_settings`, `notification_delivery`, `email_logs`, `dashboard_metrics`, `reassignment_history`, `review_assignment_history`, `review_audit_trail`, `verification_activity_log`, `verification_logs`, `conversation_activity_log`, `message_activity_log`, `user_activity_log`, `typing_status`, `user_presence`, `business_hours`, `beta_access_codes`, `beta_users`, `waitlist`, `login_history`, `password_reset_tokens`, `report_versions`, `report_comments`, `import_batches`†, `domain_events`† |
| **Intentionally authenticated-readable (reference)** | `emission_factors`, `factor_aliases`†, `units`, `roles`, `glossary`, `document_types`, `activity_categories`, `product_categories`, `supplier_categories`, `document_type_categories`, `email_templates`, `notification_templates` |
| **Tenant-scoped (policy should exist; currently missing)** | `approval_decisions`, `approval_requests`, `manual_extraction_items`, `conversation_participants` |
| **Direct-client-required** | **none** — no frontend table CRUD exists (§7) |
| **Legacy/unused** | **not assessed** — requires product input |
| **Unknown** | `consultant_billing`, `consultant_tasks`, `customer_subscriptions` |

† RLS already enabled.

---

## 7. Direct-Client Dependency Inventory

Complete inventory of frontend ↔ Supabase direct dependencies (grep of
`frontend/src/**`):

### 7.1 Table CRUD via PostgREST — **NONE**

`frontend/src/context/RealtimeContext.jsx:276` records that
`supabase.from('notifications')` reads/writes were **removed** because of "RLS
deny-by-default". No other `supabase.from(...)` call exists. All data access is
backend-mediated through the FastAPI API (`api.js`). This is a significant
simplification: **the RLS-activation compatibility risk is concentrated in
Realtime and auth, not in table CRUD.**

### 7.2 Auth (`supabase.auth.*`) — expected, RLS-independent

| File | Operation |
|---|---|
| `Login.js` | `getSession`, `onAuthStateChange`, `signUp`, `signInWithPassword`, `signInWithOAuth` |
| `BetaLogin.jsx` | `getSession`, `signInWithPassword`, `signOut` |
| `AuthCallback.js` | `getSession` (×2) |
| `OnboardingWizard.jsx` | `updateUser` |
| plus `OrganizationMetadata.jsx`, `hooks/useNotifications.js`, `hooks/useManualEntry.js`, `hooks/useDocumentLogging.js`, `DocumentStatus.jsx`, `lib/realtime/manager.js` | `getSession` |

Auth is unaffected by RLS (GoTrue/`auth` schema).

### 7.3 Realtime (`postgres_changes`) — **RLS-dependent**

| Table | Actor | Expected policy | Works today with RLS on? | RLS now (prod) |
|---|---|---|---|---|
| `notifications` | customer / consultant / staff | self-or-org scoped | **No** — deny-all (0 policies) | **disabled** |
| `customer_documents` | customer | org member | Yes (`_tenant_select`) | **disabled** |
| `customer_verifications` | customer | org member | Yes | **disabled** |
| `activity_feed` | customer | org member | Yes | **disabled** |
| `messages` | customer / consultant / PE | participant/tenant | Yes | **disabled** |
| `manual_review_queue` | internal staff | internal only | Yes | **disabled** |
| `staff_workload` | internal staff | internal only | **No** — 0 policies | **disabled** |

**Consequence:** with RLS disabled, RLS-aware Realtime currently has **no**
row filter for these seven tables — a subscriber receives changes for **all
tenants**. `notifications` and `staff_workload` additionally have no policy at
all, so enabling RLS without adding a policy will silently break their realtime
UI (the same failure that caused the earlier `notifications` removal).

**Recommendation (not implemented):** direct Realtime usage on
`customer_documents`, `customer_verifications`, `activity_feed` and `messages`
is a candidate for backend mediation, since the backend already bypasses RLS and
can enforce scope explicitly. No frontend redesign is proposed here.

---

## 8. Exact RLS Remediation Groups (Part D)

The ratified order **RLS-4 → RLS-5 → RLS-3 → RLS-2 → RLS-1 → verification** is
preserved. **No dependency change is required**; production evidence *adds* two
mandatory prerequisites (§5.2) that are already satisfied by placing the p9
recursion fix inside RLS-4/RLS-5 and the tenancy-hole fix inside RLS-1's
preconditions. One step is split out as **RLS-4A** because production evidence
shows it is independently deliverable and closes the largest exposure without any
RLS change.

---

### RLS-4A — Anonymous grant reduction (EMERGENCY-CAPABLE, INDEPENDENT)

1. **Affected:** all 104 public tables; roles `anon`, `authenticated`.
2. **Current production state:** `anon` `GRANT ALL` on 104/104; `authenticated`
   `ALL` on 96.
3. **Desired state:** `anon` has **no** table privileges (and no schema usage
   beyond what auth requires); `authenticated` retains only `SELECT,INSERT,
   UPDATE,DELETE` (no `TRUNCATE`/`REFERENCES`/`TRIGGER`), matching the 8 tables
   that already follow the explicit-grant convention.
4. **Required SQL operation types:** `REVOKE` only. No `ENABLE`, no policy change.
5. **Dependencies:** none. Safe to run first, independently.
6. **Ordering:** may execute before RLS-4; does not alter the group sequence.
7. **Positive tests:** authenticated reads/writes of its own tenant data still
   succeed; backend unchanged (BYPASSRLS).
8. **Negative tests:** `anon` `SELECT`/`INSERT`/`UPDATE`/`DELETE` on every table
   → denial; `anon` `TRUNCATE` → denial.
9. **Direct PostgREST tests:** anon key against a sample of tables → 401/403 or
   0 rows, **not** data.
10. **Backend regression:** full domain smoke (auth, ledger, calculation, QC,
    reports, imports, messaging, billing, AI).
11. **Rollback:** re-`GRANT` (documented, reversible) — but note that reverting
    re-opens the exposure.
12. **Verification evidence:** `information_schema.role_table_grants` for `anon`
    = empty on all `public` tables, re-read from production (not inferred).
13. **Stop condition:** if any production client path is found to depend on the
    `anon` role for table access, halt and escalate.

---

### RLS-4 — Function / SECURITY DEFINER / privilege hardening

1. **Affected:** 7 public functions (`anonymise_user`, `is_entity_member`,
   `is_org_active`, `is_org_admin_or_owner`, `is_org_consultant`, `is_org_member`,
   `set_updated_at`); all `public` tables (`TRUNCATE`/`TRIGGER`/`REFERENCES`).
2. **Current production state:** `anon` `EXECUTE` on all 7 functions; only 2 have
   `REVOKE ... FROM PUBLIC`; `search_path` pinned on all `SECURITY DEFINER`
   functions (no hardening needed there); `anon` holds `TRUNCATE` on all tables.
3. **Desired state:** `EXECUTE` limited to the roles that legitimately need it
   (policy-internal helpers: no `anon`, keep `authenticated` only if policy
   evaluation requires it; intentional RPCs: explicitly allowed); `TRUNCATE`
   revoked from `anon`/`authenticated`.
4. **Required SQL operation types:** `REVOKE EXECUTE ON FUNCTION`, `GRANT EXECUTE
   ON FUNCTION`, `REVOKE TRUNCATE/TRIGGER/REFERENCES ON TABLE`, and — as part of
   the p9 prerequisite — `CREATE OR REPLACE FUNCTION` for the three consultant
   helpers (from the unapplied migration, applied under its own authorization).
5. **Dependencies:** none for the `REVOKE`s; the p9 migration carries its own
   policy DROP/CREATE (see RLS-5).
6. **Ordering:** first.
7. **Positive tests:** policy evaluation still succeeds for `authenticated` on
   `organization_members`, `consultant_clients`, `organizations`, `issues`.
8. **Negative tests:** `anon` RPC call to every helper → denial; `anon`
   `TRUNCATE` → denial.
9. **Direct PostgREST tests:** `POST /rest/v1/rpc/<helper>` with anon key → denial.
10. **Backend regression:** the 73-test ops/auth unit suites + RLS integration
    suite (11 assertions).
11. **Rollback:** re-`GRANT EXECUTE`.
12. **Verification evidence:** `pg_proc.proacl` for the 7 functions; recursive
    check confirming 0 self-referential policies.
13. **Stop condition:** any function identified as a required **public** RPC must
    be explicitly allowlisted by the PO before the `REVOKE`.

---

### RLS-5 — Policy correctness (defects + recursion)

1. **Affected policies:** `om_update_self` (F-1), `organizations_org_update`
   (F-2), `users_update_self` (F-9), plus the four recursive policies
   (`om_insert_admin`, `om_select_self_or_admin`, `om_update_admin`,
   `cfm_select_self_or_team_admin`), plus `om_insert_admin`/`om_update_admin`/
   `om_select_self_or_admin` and the `cc_*` set recreated by the p9 migration.
2. **Current production state:** defective and recursive forms present, RLS
   disabled on the affected tables.
3. **Desired state:** the p9 recursion fix applied; `om_update_self` restricted so
   a member cannot alter `role` (either constrain the `WITH CHECK`, drop the
   policy in favour of an admin-only path, or add a column-level restriction);
   `organizations_org_update` requires `is_org_admin_or_owner(id)`;
   `users_update_self` column-restricted to agreed profile columns.
4. **Required SQL operation types:** `DROP POLICY`, `CREATE POLICY`,
   `ALTER POLICY`, `CREATE OR REPLACE FUNCTION` (p9 helpers), and `REVOKE
   UPDATE (role) ON organization_members` if the column-level path is chosen.
5. **Dependencies:** RLS-4A and RLS-4 complete; the p9 migration is part of this
   group.
6. **Ordering:** second.
7. **Positive tests:** owner/admin can change roles and edit the organisation;
   a member can still update their own permitted profile fields.
8. **Negative tests:** **member/viewer cannot set their own `role` to
   `owner`/`admin`** (Special Requirement A); **viewer/member cannot mutate
   `organizations`** (Special Requirement B); no infinite recursion on
   `organization_members`/`consultant_firm_members` direct reads.
9. **Direct PostgREST tests:** `PATCH /rest/v1/organization_members?user_id=eq.<self>`
   with `{"role":"owner"}` → denial; `PATCH /rest/v1/organizations?id=eq.<own>`
   as viewer → denial.
10. **Backend regression:** membership management endpoints, consultant
    engagement, entity scope suites.
11. **Rollback:** restore prior policy definitions (forward-fix preferred).
12. **Verification evidence:** policy `pg_get_expr` output on production showing
    the constraint; 0 recursive policies.
13. **Stop condition:** if no safe way to constrain self-update exists without
    changing the membership architecture, halt → **PO DECISION** (Q6).

---

### RLS-3 — Reference / static tables

1. **Affected:** `emission_factors`, `factor_aliases`, `units`, `roles`,
   `glossary`, `document_types`, `document_type_categories`,
   `activity_categories`, `product_categories`, `supplier_categories`,
   `email_templates`, `notification_templates`.
2. **Current production state:** `emission_factors` RLS disabled / 0 policies /
   `anon` ALL (F-3). `factor_aliases` RLS enabled. Others RLS disabled.
3. **Desired state:** `ENABLE ROW LEVEL SECURITY` where off; keep
   `authenticated` read (`USING (true)`); **`anon` no access** — satisfies
   Special Requirement C ("reference data may remain authenticated-readable
   where explicitly intended") and D (unless the PO rules `emission_factors` is
   intentionally public).
4. **Required SQL operation types:** `ENABLE RLS`; `CREATE POLICY` (`SELECT TO
   authenticated`); `REVOKE` from `anon` (covered by RLS-4A).
5. **Dependencies:** RLS-4A.
6. **Ordering:** third.
7. **Positive tests:** authenticated reads reference data.
8. **Negative tests:** `anon` read → 0 rows; tenant-user cross-tenant reads
   unaffected.
9. **Direct PostgREST tests:** anon key → `200 []` (as already observed for every
   table except `emission_factors`).
10. **Backend regression:** factor matching, calculation, imports.
11. **Rollback:** policy drop; **not** `DISABLE RLS`.
12. **Verification evidence:** `relrowsecurity = true` for each table, re-read
    from production.
13. **Stop condition:** if the PO rules `emission_factors` must be publicly
    readable as a product requirement, halt this group's item and record a
    documented intentional exception.

---

### RLS-2 — Operational / control-plane tables

1. **Affected:** `processing_*`, `qc_*`, `staff_*`, `sla_*`, `queue_settings`,
   `system_settings`, `login_history`, `password_reset_tokens`, `audit_trail`,
   `audit_logs`, `report_comments`, `report_versions`, `notification_delivery`,
   `email_logs`, `activity_logs`, `document_activity_log`, `user_activity_log`,
   `message_activity_log`, `conversation_activity_log`, `verification_*`,
   `beta_*`, `waitlist`, `dashboard_metrics`, `team_performance`,
   `reassignment_history`, `review_*`, `typing_status`, `user_presence`,
   `business_hours`, `consultant_billing`, `consultant_tasks`,
   `customer_subscriptions`, `approval_*`.
2. **Current production state:** RLS disabled (33 of these), 0 policies on most.
3. **Desired state:** `ENABLE RLS`; **service-only** (no `authenticated` policy)
   except where the classification in §6.1 says tenant-scoped, in which case add
   the appropriate org/entity predicate.
4. **Required SQL operation types:** `ENABLE RLS`; `CREATE POLICY` only for the
   tenant-scoped subset; `REVOKE` from `anon`.
5. **Dependencies:** RLS-4A, RLS-4, RLS-5 (for the recursion and tenancy fixes).
6. **Ordering:** fourth.
7. **Positive tests:** internal staff surfaces still function via backend.
8. **Negative tests:** `anon` → 0 rows; authenticated non-staff → 0 rows on
   staff/QC/audit tables; customer → 0 rows on internal tables.
9. **Direct PostgREST tests:** authenticated non-staff and anon → empty/denied on
   every table in the group.
10. **Backend regression:** ops dashboard, QC, SLA, notifications, audit exports.
11. **Rollback:** policy drop; forward-fix preferred.
12. **Verification evidence:** per-table `relrowsecurity` from production.
13. **Stop condition:** any table found to be required by a client path must be
    reclassified **before** enablement.

---

### RLS-1 — Critical tenant / customer tables

1. **Affected:** `organizations`, `organization_members`, `organization_metadata`,
   `users`, `emissions_logs`, `messages`, `conversations`,
   `conversation_participants`, `customer_documents`, `customer_communication`,
   `customer_review_log`, `customer_verifications`, `organization_files`,
   `customer_factors`, `facilities`, `assets`, `suppliers`, `issues`,
   `calculation_snapshots`, `manual_extraction_batches`,
   `manual_extraction_items`, `manual_review_queue`, `processing_queue`,
   `processing_logs`, `document_processing_queue`, `upload_batches`,
   `report_generation_queue`, `report_templates`, `ai_content_history`,
   `activity_feed`, `user_feedback`, `user_invitations`, `pending_invites`,
   `draft_entries`, `export_history`, `usage_tracking`, `consultant_clients`,
   `consultant_firm_members`, `consultant_profiles`, `staff_profiles`,
   `notifications`, `staff_workload`, `notification_templates` (scope-dependent).
2. **Current production state:** RLS disabled on all but `issues`,
   `processing_entities`, `customer_factors`, `calculation_snapshots`; `anon`
   ALL; policies present but inert.
3. **Desired state:** RLS enabled everywhere in the group; existing
   org/consultant/entity predicates active and **corrected**; `anon` no access;
   `notifications` and `staff_workload` given policies **before** enablement if
   Realtime is to keep working.
4. **Required SQL operation types:** `ENABLE RLS`; `CREATE POLICY` (incl. the two
   missing deny-by-default tables); `DROP POLICY`/`CREATE POLICY` for corrections;
   `REVOKE` from `anon` (RLS-4A).
5. **Dependencies:** **RLS-4A, RLS-4, RLS-5 mandatory**; the p9 recursion fix and
   `tenant_org_id_not_null` prerequisites (§5.2) resolved; RLS-3 and RLS-2
   complete.
6. **Ordering:** fifth.
7. **Positive tests:** each actor family reads/writes exactly its own scope
   (customer, consultant, PE/entity, internal staff).
8. **Negative tests:** the full §10 matrix — Customer A→B, Consultant A→B and
   A→B's client, PE A→B, entity→internal, viewer→write, member→admin, and the
   Special Requirement A/B entitlement tests.
9. **Direct PostgREST tests:** real JWTs per actor family; cross-tenant probes
   must return 0 rows / denial, never data.
10. **Backend regression:** every domain in §10.
11. **Rollback:** policy drop / forward-fix. **`DISABLE ROW LEVEL SECURITY` is
    explicitly not an acceptable rollback** (ratified decision 7) because
    `anon`/`authenticated` retain their grants until RLS-4A is complete.
12. **Verification evidence:** per-table `relrowsecurity` from production; policy
    inventory; the executed negative matrix with **zero** cross-tenant rows.
13. **Stop condition:** **any** observed cross-tenant ALLOW → immediate halt,
    roll back the last group only, and escalate as a security incident.

---

### RLS-6 — Production activation & verification

1. **Affected:** the whole `public` schema.
2. **Current state:** 97/104 tables unprotected.
3. **Desired state:** `relrowsecurity = true` on every application table;
   `FORCE RLS` still **deferred**; `anon` with no table privileges; the full
   negative matrix passing with zero cross-tenant rows.
4. **Required SQL operation types:** verification `SELECT`s only (this group
   authors no DDL of its own beyond final reconciliation).
5. **Dependencies:** RLS-1 … RLS-5.
6. **Ordering:** last, then continuous drift detection.
7. **Positive tests:** `run_acceptance.py`, `run_p6f_acceptance.py` in the e2e
   environment; production smoke of every domain.
8. **Negative tests:** the complete matrix re-run **against production**.
9. **Direct PostgREST tests:** anon and per-role JWT probes.
10. **Backend regression:** full backend suite in `backend/.venv`.
11. **Rollback:** per-group forward-fix.
12. **Verification evidence:** production catalog read-back + the executed matrix
    + a recorded baseline for drift detection (reuse the audit-swarm
    `db_collector.py` `db_rls` packet, which already reports
    `tables_with_rls_disabled`).
13. **Stop condition:** any table reaching RLS-enabled with zero policies and a
    live client dependency → halt.

---

## 9. Exact Migration Ordering

```text
STEP 0 (optional, independent, recommended first)
  RLS-4A  revoke anon/authenticated blanket grants        [REVOKE only]

STEP 1  RLS-4   function ACL + TRUNCATE hardening
                (+ apply 20260822000000_p9_rls_recursion_fix helpers)
STEP 2  RLS-5   policy correctness: F-1, F-2, F-9 + apply the p9 policy rewrites
STEP 3  RLS-3   reference tables: ENABLE RLS + authenticated-only read policy
STEP 4  RLS-2   operational/control-plane: ENABLE RLS + service-only
STEP 5  RLS-1   tenant/customer: ENABLE RLS + corrected tenant/entity policies
STEP 6  RLS-6   verification + drift baseline
```

Mandatory cross-cutting prerequisites (satisfied by the above, listed for the
implementation agent):

```text
P1  20260822000000_p9_rls_recursion_fix        -> before any RLS enablement on
                                                  organization_members,
                                                  consultant_firm_members,
                                                  consultant_clients
P2  20260831030000_tenant_org_id_not_null      -> before RLS-1 (tenancy hole)
P3  20260831000000_v3m10_org_membership_unique -> before RLS-1
P4  20260821000000 / 20260831040000 / 20260906090000 / 20260910120000
                                               -> consultant scope correctness
P5  20260823000000_d32_private_documents_storage -> storage RLS; NONIDEM (apply once)
```

Each step is its own authorized migration with its own verification gate. **No
batched release.**

---

## 10. Required Test Matrix

| Class | Test | Expected |
|---|---|---|
| Anonymous | `anon` `SELECT` on every group table | 0 rows / denial |
| Anonymous | `anon` `INSERT`/`UPDATE`/`DELETE` (not executed; capability test only) | denial |
| Anonymous | `anon` `EXECUTE` on each function | denial |
| Tenancy | Customer A → Customer B rows (read *and* write) | denial |
| Tenancy | NULL-`organization_id` rows excluded from every tenant predicate | no orphan rows |
| Consultant | Consultant A → Consultant B's client | denial |
| Consultant | Inactive/reactivated grant (D15) | 403 → 200 |
| PE/entity | PE A → PE B work; entity staff → internal/customer/consultant surfaces | denial |
| Role | Viewer → write; Member → admin operation | denial |
| **Special A** | Member/viewer `PATCH` own `organization_members.role` → `owner`/`admin` | **denial** |
| **Special A** | Owner/admin role management via the authorized path | **allow** |
| **Special B** | Viewer/member mutate `organizations` via PostgREST | **denial** |
| **Special C** | `anon` reaches no tenant/customer/business-sensitive data | 0 rows |
| **Special D** | `anon` on `emission_factors` | 0 rows (unless PO rules it public) |
| **Special E** | Allowlisted public RPCs only | allow; all others denial |
| Recursion | Direct authenticated read of `organization_members`, `consultant_firm_members`, `consultant_clients` | no recursion error |
| Realtime | Subscriber receives only its own tenant's changes | no cross-tenant events |
| Positive | Each actor family reads/writes its own scope per domain | correct scope |
| Backend | Full domain smoke: auth, onboarding, org/entity access, ledger, calculations, factors, evidence, QC, reports, versions, imports, queues, workers, notifications, activity, messaging, billing/usage, AI/Insight, admin | unchanged |
| Structural | `relrowsecurity = true` for every application table | true |
| Structural | 0 policies with inline self-reference | 0 |
| Regression | `test_v3m1_v3m2_processing_entities.py`, `test_v3m5_issues.py`, `test_v3m3_customer_factors.py`, `tests/e2e/test_p6_2f_invariants.py` | pass |
| Acceptance | `e2e/environment/scripts/run_acceptance.py` | pass |

**Every unexpected ALLOW is a security finding.**

---

## 11. Production Rollout Procedure

1. **Capture a pre-change baseline** — production catalog read-back (tables,
   `relrowsecurity`, policies, grants, function ACLs) and migration state.
2. **Authorize and apply RLS-4A** (independent; closes the anonymous exposure).
   Verify by re-reading `information_schema.role_table_grants` from production.
3. **Apply prerequisites P1–P5** under their own authorizations, each verified
   separately. Do **not** batch with RLS enablement.
4. **RLS-4 → RLS-5 → RLS-3 → RLS-2 → RLS-1**, one group per authorized change,
   with the group's test matrix run against production before the next group.
5. **RLS-6 verification** — full matrix with zero cross-tenant rows; record the
   baseline for drift detection.
6. **Continuous drift detection** — re-run the `db_rls` collector on a schedule;
   alarm on any table regressing to `relrowsecurity = false`.
7. **Never** combine with the outstanding `20260824020000`/`20260824030000`
   billing migrations (they carry DML and require separate review).
8. **`FORCE ROW LEVEL SECURITY` remains deferred** (ratified decision 6; no
   practical effect while `postgres` holds `BYPASSRLS` and owns every table).

**Process control (new, from §5.2):** never edit a migration that is already
recorded as applied. Any post-application change to `00000000000000_init_schema`
is unenforceable in production — this is the root cause of the entire finding set.

---

## 12. Recovery / Rollback Strategy

* **Never** `ALTER TABLE ... DISABLE ROW LEVEL SECURITY` (ratified decision 7).
  Until RLS-4A completes, disabling RLS converts a functional failure into an
  anonymous data exposure.
* **Per-group forward-fix only.** Each group is independently revertible by
  restoring its prior policy set / re-granting the revoked privilege.
* **RLS-4A rollback** = re-`GRANT` (reversible, but re-opens the exposure —
  hence the recommendation to treat re-granting as a deliberate, documented act).
* **Emergency containment** if a live cross-tenant ALLOW is observed:
  1. revoke the affected table's `anon`/`authenticated` DML grants;
  2. re-apply the last known-good policy set for that table;
  3. escalate as a security incident; preserve evidence before remediation.
* **Prerequisite failure** (e.g. p9 recursion reproduced): stop, re-apply the p9
  migration, re-run the recursion check, then resume.
* **No destructive operation** is proposed anywhere in this specification.

---

## 13. Stop Conditions

1. Any observed **cross-tenant ALLOW** during or after a group → halt immediately.
2. **Recursion** reproduced on `organization_members` / `consultant_firm_members`
   → halt; the p9 prerequisite is not effective.
3. A table reaching **RLS-enabled with zero policies** while a live client
   dependency exists → halt (silent zero-row breakage).
4. **`anonymise_user`** `EXECUTE` to `anon` cannot be shown to be safe → halt
   RLS-4 and escalate.
5. `emission_factors` public readability turns out to be a **product
   requirement** → halt Special D and record an intentional exception.
6. Constraining `om_update_self` (F-1) would require changing the membership
   architecture → halt → **PO DECISION**.
7. Any step requiring **authentication/authorization architecture** change → halt.
8. Any migration with **destructive or broad** consequences → halt.
9. Production **column-level privileges** prove to differ materially from the
   table-level picture → re-baseline before proceeding.
10. A required **public RPC** is identified among the 7 functions → halt RLS-4's
    `REVOKE` for that function pending PO allowlisting.

---

## 14. Remaining PO / Security Decisions

| # | Decision | Why it blocks |
|---|---|---|
| Q1 | **Authorize RLS-4A now** (revoke blanket `anon` grants) as an independent, emergency-capable step? | 97 tables are anonymously writable; the fix needs no RLS change |
| Q2 | Accept the **unaudited status** of 12 tables missing from production (7 billing, 2 consultant, `vehicles`, `work_item_assignments`, `data_discovery_requests`)? | determines whether Phase-8/billing features are actually deployable |
| Q3 | Adjudicate the **34-migration backlog**: apply (in the §5.3 order) or freeze the difference? | productive drift grows with every new migration |
| Q4 | Is **public/anonymous access to `emission_factors`** a product requirement? | decides Special D (default proposed: authenticated-only) |
| Q5 | Which of the 7 functions are **intentional public RPCs** vs policy-internal? | `REVOKE` cannot be applied blindly (Special E) |
| Q6 | Who may change a member's **role**, and by what path (F-1)? | needed before RLS-5 can be specified |
| Q7 | `users_update_self` — which columns may a user update (F-9)? Requires production column enumeration. | needed before RLS-5 |
| Q8 | Should direct **Realtime** access on tenant tables be replaced by backend mediation? | determines whether `notifications`/`staff_workload` need new policies |
| Q9 | Is a **`tenant_org_id_not_null`** remediation acceptable now? | tenancy hole persists otherwise (§5.2) |
| Q10 | Authorize a **read-only production DB role** for future verification (avoids reliance on the CLI's temporary login role)? | current mechanism provisions a transient login role per invocation |
| Q11 | Confirm **`FORCE RLS`** stays deferred | ratified as deferred; re-affirm after activation |
| Q12 | Review **`anonymise_user` EXECUTE to `anon`** | potential unauthenticated data-mutation surface |

**Mechanism disclosure (for Q10):** `supabase db dump --linked` and
`supabase migration list --linked` both print `Initialising login role...` and use
the CLI's Management-API session to provision a **transient** login role for the
read. No schema, data, policy, grant, or configuration was modified, and no
migration was applied. This is disclosed because it is technically a
tool-managed, transient production action rather than a purely read-only
connection; a dedicated read-only role (Q10) would remove the ambiguity.

---

## 15. Task Completion Report

### Files created / modified

| Path | Change |
|---|---|
| `docs/architecture/CARBONTALLY_RLS_PRODUCTION_BASELINE_AND_REMEDIATION_SPEC_20260912.md` | **CREATED** (this document) |

Outside the repository (ephemeral, not version-controlled, contains **no row
data**):

| Path | Purpose |
|---|---|
| `/tmp/prod_public_schema.sql` | production `public` schema dump (schema-only) |
| `/tmp/analyze_rls.py`, `/tmp/analyze2..5.py` | read-only analysis scripts |

No application code, SQL migration, policy, grant, RLS setting, Supabase
configuration, test, or documentation other than the file above was modified.

### State changes

* **Database state changed: NO.** All local inspection used
  `default_transaction_read_only = on`; no local DDL/DML was issued.
* **Production state changed: NO.** Only read-only operations were performed
  (`projects list`, `migration list --linked`, schema-only `db dump`). No
  migration was applied, no policy/grant/RLS/config was altered, and no row data
  was read or written. The CLI's transient login-role provisioning is disclosed
  in §14.

### Git

* **Current HEAD:** `19e4f01c176eee5870f3c15038b6e7c68b23281c`
  (`feat: implement Phase 8 report lifecycle foundation`), branch `main`.
* **Worktree status:** **208 modified / 52 untracked** — identical before and
  after this task. All pre-existing work preserved exactly; no staging, no
  commit, no push, no reset/clean/stash.
* The new specification is **uncommitted** by instruction.

### Evidence limitations

1. The Supabase **Advisor export** was not available; Advisor-facing counts are
   derived from verified catalog state.
2. Production **column-level** and **default** privileges are UNVERIFIED
   (`pg_dump` does not emit them).
3. Live exploitation of the `anon` exposure was **not** attempted (would read or
   mutate production data) — capability is VERIFIED, exploitation is INFERRED
   with the predecessor's `emission_factors` read as supporting evidence.
4. Production **row counts / data volumes** were deliberately not read.
5. `anonymise_user`'s internal authorization guard was not fully evaluated.
6. Realtime cross-tenant broadcast is mechanically inferred, not dynamically
   tested.
7. The 12 production-missing tables were identified from the schema dump; their
   *feature* impact was not assessed.
8. No e2e/local re-verification was run for this task (discovery only).

---

## 16. Final Verdict

**RLS PRODUCTION BASELINE VERIFIED — IMPLEMENTATION SPEC READY FOR PO AUTHORIZATION**

Production catalog metadata was successfully obtained read-only, the drift
root cause is evidenced, all seven known findings plus three new ones are
dispositioned, and the bounded remediation specification is complete and
dependency-ordered. The remaining items are **PO/security decisions**, not
evidentiary gaps. Because the verified exposure is an anonymous
read-write capability on 97 of 104 production tables, **authorization of RLS-4A
(revoke-only, no RLS change) is recommended as an immediate, independently
authorizable first step**, ahead of the ratified
RLS-4 → RLS-5 → RLS-3 → RLS-2 → RLS-1 → verification sequence.

**No implementation. No migration. No policy change. No grant change. No RLS
change. No production change. No commit. No push.**
