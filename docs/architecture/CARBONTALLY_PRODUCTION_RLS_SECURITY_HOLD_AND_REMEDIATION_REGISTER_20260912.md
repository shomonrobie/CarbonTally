---
Document Type: Security Hold & Remediation Register (project control — DOCUMENTATION ONLY)
Project: CarbonTally
Prompt ID: CT-SEC-RLS-HOLD-REGISTER-20260912-001
Status: **RLS PRODUCTION SECURITY REMEDIATION — DEFERRED / NOT YET AUTHORIZED**
Created: 2026-09-12
Authoritative technical source: `docs/architecture/CARBONTALLY_RLS_PRODUCTION_BASELINE_AND_REMEDIATION_SPEC_20260912.md`
---

# CarbonTally — Production RLS Security Hold & Remediation Register

> **This register is a project-control document, not a technical specification.**
> It duplicates no specification. The authoritative technical detail remains the
> OHD baseline & remediation specification named above; this register exists so
> that the verified findings, the agreed remediation direction, the open PO
> decisions and the explicit non-authorization state survive phases, sessions
> and handovers.

---

## 1. Purpose

This register preserves the **verified production RLS/security posture** of
CarbonTally and the **agreed remediation direction**, while remediation
implementation is **intentionally deferred** to a later, separately authorized
security/release gate.

It exists because:

* the production RLS findings were established by independent discovery and are
  material;
* the project's current sequencing priority is product delivery (Phase 8, then
  the bounded Phase 8-X Operational Intelligence work), not security
  remediation;
* the findings, prerequisites, remediation sequence and open PO decisions are
  detailed enough to be **forgotten or mis-remembered** across sessions if not
  recorded in one stable place;
* implementation must not begin accidentally, incidentally, or as a side effect
  of unrelated work.

**What this register is for**

* durable preservation of verified findings;
* durable preservation of the proposed remediation sequence and prerequisites;
* explicit recording of the current hold state;
* explicit recording of the conditions under which the work reopens;
* a controlled handover artefact for a future PO/engineering/security owner.

**What this register is not**

* it is **not** an implementation authorization;
* it is **not** a substitute for the technical specification;
* it is **not** an audit, certification, or compliance attestation of any kind.

---

## 2. Current Status

```text
RLS PRODUCTION SECURITY REMEDIATION — DEFERRED / NOT YET AUTHORIZED
```

| Attribute | State |
|---|---|
| Discovery performed | **YES** — independently, read-only |
| Discovery accepted as a genuine production security concern | **YES** (accepted as a discovery/security checkpoint) |
| Remediation authorized | **NO** |
| Remediation implemented | **NO** |
| Production changes made by the discovery | **NONE** |
| Production changes made by this register | **NONE** |
| RLS-4A-1 (Anonymous Access Containment) | **NOT AUTHORIZED / NOT IMPLEMENTED** |
| RLS-4A-2 (Authenticated Grant Hardening) | **NOT AUTHORIZED / NOT IMPLEMENTED** |
| RLS-5 / RLS-3 / RLS-2 / RLS-1 | **NOT AUTHORIZED / NOT IMPLEMENTED** |
| Outstanding migration backlog applied | **NO** |
| `FORCE ROW LEVEL SECURITY` | **DEFERRED** (pre-existing ratified position) |

The discovery has been accepted as a **real production security concern**. That
acceptance is a statement about the *findings*, not an authorization to change
anything. Remediation implementation remains unauthorized pending the reopening
condition defined in §10.

---

## 3. Why the Work Is Deferred

The current project sequencing decision is:

1. **Complete the ratified Phase 8 product capabilities.**
2. **Complete the subsequently bounded Phase 8-X — Operational Intelligence
   work.**
3. **Reopen the RLS security remediation gate.**
4. **Begin the separately authorized RLS remediation sequence.**
5. **Independently verify the resulting production security posture.**

**RLS remediation is a cross-cutting production security / release gate.**
It is *not* a product phase, and **no Phase 9 is created, implied or assigned by
this register.** The remediation sequence is a security workstream that must
clear before production security posture can be considered settled; it sits
alongside, not inside, the product roadmap.

**Why sequencing it after Phase 8 / Phase 8-X is a deliberate choice**

* The remediation groups must be authored against the **then-current** schema.
  Phase 8 and Phase 8-X both add tables, migrations and access paths; authoring
  RLS remediation now would guarantee rework and re-verification.
* Phase 8 deliverables sit on top of an **unapplied-migration backlog** (§7), so
  the baseline will move regardless.
* 12 tables currently exist in the repository but **not** in production (§4.3);
  the production baseline will change as those features deploy.
* The remediation is **not blocked on additional discovery** — only on
  authorization and on a settled schema to remediate.

**Why the hold does not resolve the exposure**

Deferral is a **sequencing** decision, not a statement that the exposure is
acceptable, mitigated, or low risk. §4 and §5 record the verified posture
unchanged. The hold state is deliberately explicit so that deferral cannot later
be misread as dismissal.

---

## 4. Verified Production Baseline

All figures below are **VERIFIED** unless labelled otherwise. Source of truth is
the OHD baseline & remediation specification, derived from a read-only
schema-only production dump (`supabase db dump --linked --schema public`) plus
`supabase migration list --linked`. **No row data was read.**

### 4.1 Production project and migration state

| Item | Value | Status |
|---|---|---|
| Production project ref | `pvwiojoyaqywtydzcpbg` (name: CarbonTally, region eu-west-2) | VERIFIED |
| Project status | `ACTIVE_HEALTHY` | VERIFIED |
| Migrations recorded applied | **21** (through `20260810050000`) | VERIFIED |
| Repository migration files | **55** | VERIFIED |
| Repository migrations **not** applied | **34** | VERIFIED |
| Remote-only migration records (orphans) | **0** | VERIFIED |

### 4.2 RLS and policy posture

| Metric | Production | Local dev (contrast) | Status |
|---|---|---|---|
| Public tables | **104** | 116 | VERIFIED |
| RLS **enabled** | **7** | 116 | VERIFIED |
| RLS **disabled** | **97** | 0 | VERIFIED |
| `FORCE ROW LEVEL SECURITY` | **0** | 0 | VERIFIED |
| Table owner | `postgres` (all) | `postgres` (all) | VERIFIED |
| `CREATE POLICY` statements | **179** | 174 | VERIFIED |
| Tables with ≥1 policy | **55** | 58 | VERIFIED |
| Policies targeting `authenticated` | **179 (100%)** | 174 | VERIFIED |
| Policies targeting `anon` | **0** | 0 | VERIFIED |
| Restrictive policies | **0 (all permissive)** | 0 | VERIFIED |

**Tables with RLS enabled (7):** `calculation_snapshots`, `customer_factors`,
`domain_events`, `factor_aliases`, `import_batches`, `issues`,
`processing_entities`.

**Policy / RLS combinations (production):**

| Combination | Count |
|---|---|
| Policy exists + RLS disabled | **50** |
| RLS disabled + no policy | **47** |
| RLS enabled + no policy | **2** |
| RLS enabled + policy | **5** |

**No production policy faces `anon`.** Where RLS is enabled, it is a complete
deny-all for the anonymous role; the only barrier between `anon` and the tenant
database is `relrowsecurity`.

### 4.3 Grants

| Grantee | Production table privileges | Status |
|---|---|---|
| `anon` | **`GRANT ALL` on 104 / 104 tables** | VERIFIED |
| `authenticated` | `ALL` on 96 tables; `SELECT,INSERT,UPDATE,DELETE` (no `TRUNCATE`) on 8 | VERIFIED |
| `service_role` | `ALL` on all tables | VERIFIED |
| Schema `USAGE` | granted to `postgres`, `anon`, `authenticated`, `service_role` | VERIFIED |
| Column-level privileges | — | **UNVERIFIED** (a schema dump does not emit column ACLs) |
| `ALTER DEFAULT PRIVILEGES` entries | — | **UNVERIFIED** |

**Effective production exposure: `anon` `ALL` + RLS disabled on 97 of 104 tables.**
Affected sensitive tables include (non-exhaustive): `organizations`,
`organization_members`, `users`, `password_reset_tokens`, `audit_trail`,
`system_settings`, `login_history`, `staff_roles`, `emissions_logs`, `messages`,
`conversations`, `customer_documents`, `organization_files`, `customer_factors`,
`facilities`, `assets`, `suppliers`, `issues`, `report_versions`.

**Tables in the repository but absent from production (12):**
`billing_commercial_config`, `billing_credit_ledger`,
`billing_idempotency_keys`, `billing_orders`, `billing_payment_records`,
`billing_plans`, `billing_storage_usage`, `consultant_custom_domains`,
`consultant_senders`, `data_discovery_requests`, `vehicles`,
`work_item_assignments`. Zero production tables are absent from the repository —
production is a strict subset.

### 4.4 Function / `EXECUTE` posture

| Item | Value | Status |
|---|---|---|
| Public functions in production | **7** | VERIFIED |
| `SECURITY DEFINER` functions | 7 | VERIFIED |
| `search_path` pinned on `SECURITY DEFINER` functions | all (none mutable) | VERIFIED |
| Functions with `EXECUTE` granted to **`anon`** | **7 of 7** | VERIFIED |
| Functions with `REVOKE ... FROM PUBLIC` | 2 only (`anonymise_user`, `is_entity_member`) | VERIFIED |

Production functions with `anon` `EXECUTE`: `anonymise_user`, `is_entity_member`,
`is_org_active`, `is_org_admin_or_owner`, `is_org_consultant`, `is_org_member`,
`set_updated_at`.

Production **lacks** the `is_consultant_firm_member` /
`is_consultant_firm_revoker` / `is_consultant_team_admin` helper family, because
`20260822000000_p9_rls_recursion_fix.sql` is not applied.

`anonymise_user` is a `SECURITY DEFINER` **data-mutating** function whose
`EXECUTE` is granted to `anon`. Its internal authorization guard was **not**
fully evaluated during discovery, and is **UNVERIFIED**.

### 4.5 Migration drift

Production is **21 applied / 34 outstanding**, with **0 orphan migration
records**. Two drift findings are material:

**(a) Root cause — an already-applied migration was edited (VERIFIED state,
evidenced mechanism).** The RLS-enablement floor is a bulk `DO` loop at
`supabase/migrations/00000000000000_init_schema.sql` (lines 2319–2324). That loop
was introduced by commit **`dbe72aa`** ("checkpoint: verified V2.1 and V3
database foundation") into a migration **already recorded as applied** in
production. Editing an applied migration never re-executes it, so production
never ran the bulk enable. The underlying storeys contain **zero** RLS
enablement (`database/rc1/001_rc1_schema.sql`: 0;
`database/rc2/00000000000000_init_schema.sql`: 0). The only enablements that
reached production are the seven per-table `ENABLE ROW LEVEL SECURITY` statements
inside *other*, later-applied migrations — and the arithmetic matches exactly
(4 + 1 + 1 + 1 = **7**).

**(b) Recursion defect still present (VERIFIED).** Four production policies embed
inline self-referential subqueries on their own table:

```text
organization_members      om_insert_admin
organization_members      om_select_self_or_admin
organization_members      om_update_admin
consultant_firm_members   cfm_select_self_or_team_admin
```

These are the pre-fix forms. They are currently inert because RLS is disabled on
both tables.

### 4.6 Realtime implication

The frontend subscribes to `postgres_changes` on: `notifications`,
`customer_documents`, `customer_verifications`, `activity_feed`, `messages`,
`manual_review_queue`, `staff_workload`. Supabase Realtime honours RLS for the
subscribing role; **all seven of these tables have RLS disabled in production**,
so Realtime currently applies no row filter for them. This is classified
**INFERRED (high confidence)** from the verified RLS-disabled state; it was not
dynamically tested.

### 4.7 Tenant `organization_id` prerequisite

`20260831030000_tenant_org_id_not_null` is **not applied**. The RC1 security file
records why RLS alone is insufficient: *"NULL `organization_id` rows fall outside
every tenant-equality policy (tenancy hole)"*
(`database/rc1/004_rc1_rls.sql`, header). Enabling tenant RLS while nullable
`organization_id` rows exist leaves those rows outside every predicate.

### 4.8 Evidence limitations (carried forward unchanged)

1. The **Supabase Advisor export** was never present; the Advisor-facing counts
   quoted in the source report are derived from verified catalog state.
2. Production **column-level** and **default** privileges are **UNVERIFIED**.
3. **Live exploitation was not attempted** (it would read or write production
   data). Capability is VERIFIED; exploitation is INFERRED, with the predecessor
   reconciliation's empirically observed anonymous read of 7,049
   `emission_factors` rows as supporting evidence only.
4. Production **row counts / data volumes** were deliberately not read.
5. Realtime cross-tenant broadcast is mechanically inferred, not tested.
6. `anonymise_user`'s internal authorization guard is **UNVERIFIED**.
7. The 12 production-missing tables were identified from the schema dump; their
   *feature* impact was not assessed.

---

## 5. Security Findings

Severity and status are carried forward **exactly as recorded in the source
report**. Findings were established from verified catalog state; where
exploitability was not demonstrated, it is stated as such. Nothing in this
register upgrades an inference into a demonstrated exploit.

| ID | Finding | Classification | Current status |
|---|---|---|---|
| **F-4** | **Broad anonymous grant exposure** — `anon` holds `GRANT ALL` on 104/104 tables, with RLS disabled on 97. Anonymous read *and write* capability on ~93% of the production database. | **CRITICAL** (primary finding) | VERIFIED (capability). Exploitation INFERRED, not attempted. |
| **NEW** | **Anonymous access to credential/identity/audit tables** — `password_reset_tokens`, `users`, `organization_members`, `login_history`, `user_invitations`, `pending_invites`, `audit_trail`, `system_settings` all sit inside the anonymous-ALL + RLS-disabled set. | **CRITICAL** | VERIFIED (capability). |
| **F-3** | **`emission_factors` exposure** — RLS disabled, 0 policies, explicit `GRANT ALL` to `anon` and `authenticated`. Broader than first reported: the grant covers writes as well as reads. Public/private intent is an open PO question. | **HIGH** / **REQUIRES PO DECISION** | VERIFIED (grant + RLS state). |
| **NEW** | **Recursive / pre-fix RLS policies in production** — four policies with inline self-reference; the recursion fix is not applied. Inert today; **would break direct authenticated reads the moment RLS is enabled**. | **HIGH (prerequisite)** | VERIFIED. |
| **F-1** | **`organization_members.om_update_self` role-escalation concern** — policy is `USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid())`, with no constraint on `role`. | **HIGH** | VERIFIED as a production policy. Masked *and* amplified by RLS being disabled. |
| **F-2** | **`organizations` update authorization concern** — `organizations_org_update` uses `USING/WITH CHECK is_org_member(id)` with no owner/admin predicate. | **MEDIUM-HIGH** | VERIFIED as a production policy. |
| **F-6** | **`SECURITY DEFINER` / function `EXECUTE` exposure** — `anon` has `EXECUTE` on all 7 production functions, including the data-mutating `anonymise_user` and the trigger function `set_updated_at`. Only 2 functions have `REVOKE ... FROM PUBLIC`. | **MEDIUM** (defence-in-depth) | VERIFIED as a privilege. |
| **F-5** | **Anonymous / authenticated `TRUNCATE` privilege** — `anon` holds `TRUNCATE` on all 104 tables; `authenticated` on 96. `TRUNCATE` is not gated by RLS. **Not reachable through PostgREST**, so exploitation requires direct database access. | **MEDIUM** (hygiene) | VERIFIED as a privilege. |
| **F-9** | **`users_update_self` concern** — policy `USING/WITH CHECK id = auth.uid()` with no column restriction; production `users` column set was not enumerated. | **UNVERIFIED** | VERIFIED as a policy; exploitability **UNVERIFIED**. |
| **NEW** | **Realtime tenant-isolation concern** — all seven `postgres_changes`-subscribed tables have RLS disabled, so Realtime applies no row filter. | **INFERRED (high confidence)** | Not dynamically tested. |
| **NEW** | **Process defect — edited already-applied migration** — the RLS-enablement floor was added to `init_schema` after it was applied. This is the root cause of the entire finding set. | **PROCESS / GOVERNANCE** | VERIFIED. |

### 5.1 Severity distribution (as recorded, unchanged)

```text
CRITICAL            2 findings
HIGH / prereq       3 findings
MEDIUM-HIGH         1 finding
MEDIUM (hygiene)    2 findings
UNVERIFIED          1 finding
INFERRED            1 finding
PROCESS             1 finding
```

### 5.2 What is **not** claimed

* No claim that the exposure has been exploited.
* No claim that any specific tenant's data has been accessed or altered.
* No claim of regulatory non-compliance. **This register makes no GDPR,
  UK GDPR, Irish data-protection, or any other compliance statement, and asserts
  no certification, audit or assurance status.** Those are separate questions
  requiring separate, qualified assessment.
* No claim that the 153-report Advisor finding count maps one-to-one to
  vulnerabilities. The verified underlying reality is **97 tables with RLS
  disabled** and **`anon` ALL on 104 tables**.

---

## 6. Proposed Remediation Sequence

The proposed sequencing is:

```text
RLS-4A  →  RLS-5  →  RLS-3  →  RLS-2  →  RLS-1  →  verification
```

with **RLS-4A split into two bounded sub-steps**:

### RLS-4A-1 — Anonymous Access Containment

* **Scope:** the `anon` half of RLS-4A — revoke `anon` table privileges across
  the `public` schema.
* **Operation types:** `REVOKE` only. No `ENABLE`, no policy change.
* **Rationale:** closes the anonymous exposure without any RLS change, and is
  independently deliverable.
* **Status:** **NOT AUTHORIZED — NOT IMPLEMENTED.**

### RLS-4A-2 — Authenticated Grant Hardening

* **Scope:** the `authenticated` half of RLS-4A — reduce `authenticated` from
  `ALL` to `SELECT,INSERT,UPDATE,DELETE` (dropping `TRUNCATE` / `REFERENCES` /
  `TRIGGER`), matching the 8 tables that already follow the explicit-grant
  convention.
* **Operation types:** `REVOKE` only.
* **Status:** **NOT AUTHORIZED — NOT IMPLEMENTED.**

The remainder of the sequence, as recorded in the source report:

| Group | Scope (summary) |
|---|---|
| **RLS-5** | Policy correctness — F-1, F-2, F-9 corrections plus the recursion-fix policy rewrites |
| **RLS-3** | Reference / static tables — enable RLS; keep authenticated read; no `anon` access |
| **RLS-2** | Operational / control-plane tables — enable RLS; service-only unless tenant-scoped |
| **RLS-1** | Critical tenant / customer tables — enable RLS with corrected org/consultant/entity predicates |
| **verification** | Full negative matrix against production; record a drift baseline |

Each group is a **separately authorized** change with its own verification gate.
No batched release. `DISABLE ROW LEVEL SECURITY` is **not** an acceptable
rollback (pre-existing ratified position).

### 6.1 Sequence discrepancy requiring PO confirmation

The source specification's full sequence additionally contains **RLS-4
(Function / `SECURITY DEFINER` / privilege hardening)** positioned between
RLS-4A and RLS-5, and assigns to it:

* the `anon` `EXECUTE` revocation (F-6), and
* the `TRUNCATE` / `REFERENCES` / `TRIGGER` revocation (F-5).

**RLS-4 is absent from the sequence recorded in the PO instruction for this
register.** This register records the PO-stated sequence as the register's
sequence and flags the omission rather than resolving it: if RLS-4 is genuinely
dropped, F-5 and F-6 must be **explicitly reassigned** to RLS-4A-1 / RLS-4A-2,
otherwise they are lost. This requires PO confirmation (§8, D-13). It is recorded
here so the question cannot be missed at handover.

---

## 7. Known Prerequisites

Two prerequisites were demonstrated by production evidence and are **mandatory
before any RLS enablement on the affected tables** — not optional.

### 7.1 `20260822000000_p9_rls_recursion_fix` — HARD PREREQUISITE

* **State:** **NOT APPLIED** in production.
* **Consequence if ignored:** enabling RLS on `organization_members`,
  `consultant_firm_members` or `consultant_clients` while the four pre-fix
  recursive policies remain will reproduce the original defect — **infinite
  recursion on every direct authenticated read**.
* Production also lacks the three consultant helper functions the fix
  introduces, so those policies cannot simply be enabled as-is.

### 7.2 `20260831030000_tenant_org_id_not_null` — HARD PREREQUISITE

* **State:** **NOT APPLIED** in production.
* **Consequence if ignored:** rows with `NULL organization_id` fall outside every
  tenant-equality policy — a tenancy hole that RLS will not close.

### 7.3 Additional dependency-class migrations

Consultant-scope correctness also depends on `20260821000000`,
`20260831000000` (`v3m10_org_membership_unique`),
`20260831020000` (`audit_activity_immutability`), `20260831040000`,
`20260902040000`, `20260903010000`, `20260906090000`, `20260910120000`,
`20260912000000`, `20260822010000`, and `20260823000000`
(`d32_private_documents_storage`, which is **non-idempotent** — four unguarded
`CREATE POLICY` statements — and must be applied once).

### 7.4 Batching prohibition

> **Outstanding migrations must NOT be blindly applied as a batch.**

Several carry **DML** or other potentially material changes and require separate
review. In particular `20260824020000_d37_0_billing_security_and_configurable_subscription`
and `20260824030000_d37_master_commercial_billing` carry DML. Migrations that
change role models (`v3m8_system_admin_role_model`, `v3m8_pe_manager_role`) or
introduce durable processing (`v3m9_durable_automatic_processing`) are
product/security decisions, not mechanical applies.

Prerequisites are to be applied **individually, each under its own
authorization, each separately verified** — not folded into the RLS activation.

---

## 8. PO Decisions Still Required

Carried forward from the source report. **These decisions have not been made and
are not made by this register.**

| # | Decision | Why it blocks |
|---|---|---|
| **Q1 / D-1** | Authorize **anonymous grant containment** (RLS-4A-1) as an independent step? | 97 tables are anonymously accessible; the fix needs no RLS change |
| **Q2 / D-2** | Accept the status of the **12 production-missing tables** (7 billing, 2 consultant, `vehicles`, `work_item_assignments`, `data_discovery_requests`)? | determines whether Phase 8 / billing features are deployable |
| **Q3 / D-3** | Adjudicate the **34-migration backlog**: apply in dependency order, or freeze the difference? | drift grows with every new migration |
| **Q4 / D-4** | Is public / anonymous access to **`emission_factors`** a product requirement? | decides whether its exposure is a defect or a documented intentional exception (default proposed: authenticated-only) |
| **Q5 / D-5** | Which of the 7 functions are **intentional public RPCs** vs policy-internal? | `EXECUTE` revocation cannot be applied blindly (F-6) |
| **Q6 / D-6** | **Who may change an organization member's role**, and by what path? | required before RLS-5 can be specified (F-1) |
| **Q7 / D-7** | **`users_update_self` — which columns** may a user update? Requires production column enumeration. | required before RLS-5 (F-9) |
| **Q8 / D-8** | Should direct **Realtime** access on tenant tables be replaced by backend mediation? | determines whether `notifications` / `staff_workload` need new policies |
| **Q9 / D-9** | Is a **tenant `organization_id` nullability** remediation acceptable? | the tenancy hole persists otherwise (§7.2) |
| **Q10 / D-10** | Authorize a **dedicated read-only production DB role** for future verification? | the current mechanism provisions a transient login role per invocation (§9.4) |
| **Q11 / D-11** | Confirm **`FORCE RLS`** remains deferred? | re-affirm after activation |
| **Q12 / D-12** | Review **`anonymise_user` `EXECUTE` to `anon`**. | potential unauthenticated data-mutation surface |
| **D-13** | **Confirm whether RLS-4 remains in the sequence** (see §6.1), or explicitly reassign F-5 and F-6. | prevents silent loss of the function/`EXECUTE` hardening |

---

## 9. Explicit Non-Actions

**As of this register:**

* **RLS-4A-1 is NOT implemented.**
* **RLS-4A-2 is NOT implemented.**
* **No RLS remediation has been applied** — not RLS-5, not RLS-3, not RLS-2, not
  RLS-1, and not group verification.
* **No RLS enablement or disablement** has been performed anywhere.
* **No production grants have been changed** — no `GRANT` or `REVOKE` applied.
* **No production policies have been created, altered or dropped.**
* **No production functions have been created, altered or revoked.**
* **No Supabase or production configuration has been modified.**
* **No outstanding migration batch has been applied** as part of this task, and
  no migration has been created or modified.
* **No application code, database schema, RLS policy, test, or other
  documentation has been modified** by this task beyond the two documents named
  in §12.4.
* **No production data has been read or written.**

### 9.1 The hold is explicit and deliberate

This section exists so that a future reader cannot infer, from the presence of a
detailed remediation plan, that any part of it has been executed. **The plan is
comprehensive precisely because it is deferred.** Presence of a specification is
not evidence of implementation.

### 9.2 What a future reader must not assume

* Do not assume RLS-4A-1 was applied as a "quick fix" at some earlier point.
* Do not assume the production baseline in §4 is still current — it is a
  point-in-time snapshot dated 2026-09-12 and **must be re-verified** before
  remediation is authored.
* Do not assume the 34-migration backlog has been adjudicated.
* Do not assume any PO decision in §8 has been made.

### 9.3 Verification evidence required when work resumes

* A fresh production catalog read-back (tables, `relrowsecurity`,
  `relforcerowsecurity`, policies, grants, function ACLs) and migration state.
* The full negative authorization matrix executed against production, with
  **zero** cross-tenant rows.
* Independent verification of each authorized step before the next begins.

### 9.4 Discovery-mechanism disclosure (for D-10)

The read-only discovery used the linked Supabase CLI
(`supabase migration list --linked`, `supabase db dump --linked --schema public`).
Both print `Initialising login role...` and use the CLI's Management-API session
to provision a **transient** login role for the read. No schema, data, policy,
grant, migration, or configuration was modified. This is disclosed because it is
technically a tool-managed, transient production action rather than a purely
read-only connection; a dedicated read-only role (D-10) would remove the
ambiguity.

---

## 10. Reopening Condition

> **The security gate requires explicit Product Owner authorization before any
> implementation resumes.**

Reopening conditions:

1. Phase 8 product capabilities are complete (or the PO elects to sequence
   remediation earlier).
2. Phase 8-X Operational Intelligence work is complete or explicitly parked.
3. The PO **explicitly reopens** the RLS security remediation gate.
4. The production baseline is **re-verified** (the §4 snapshot may be stale).
5. Each remediation step is **separately bounded and separately authorized**.
6. The first authorized step (expected to be RLS-4A-1) is **independently
   verified** before the next step begins.

**RLS-4A-1 is not automatically authorized by this register, by the passage of
time, by completion of Phase 8 or Phase 8-X, or by any other event.** Only an
explicit PO authorization opens the gate.

**Emergency exception:** if the anonymous exposure is observed to be *exercised*
(i.e. evidence of actual access or alteration of production data), the PO should
be informed immediately so that containment can be separately authorized ahead
of the normal sequence. This register does not pre-authorize any such action.

---

## 11. Relationship to Phase 8 and Phase 8-X

| Workstream | Nature | Relationship to RLS remediation |
|---|---|---|
| **Phase 8** | The **active product-development roadmap** (ratified). | Unchanged. RLS remediation does **not** replace, redefine, or gate Phase 8 delivery, and this register does not modify the Phase 8 roadmap. |
| **Phase 8-X — Operational Intelligence** | The bounded **Operational Intelligence extension/workstream** (subsequently defined). | Unchanged. RLS remediation is **not** part of Phase 8-X, and Phase 8-X is **not** part of RLS remediation. |
| **RLS remediation** | A **cross-cutting production security / release gate** (`RLS-4A → RLS-5 → RLS-3 → RLS-2 → RLS-1 → verification`). | Independent security workstream. Not a product phase. **No Phase 9 is created or implied.** |

**Explicit disambiguations:**

* **Infrastructure / runtime operational intelligence must not be confused with
  RLS remediation.** They are unrelated: one is product/runtime visibility, the
  other is database-level access control.
* **RLS remediation is not a Phase 8-X deliverable**, and Phase 8-X deliverables
  are not a prerequisite for RLS remediation beyond the shared
  then-current-schema question (§3).
* **No new Phase 9 exists.** The remediation sequence is a security workstream
  and is deliberately not numbered as a product phase.

**Historical naming note (for handover accuracy).** An earlier working document
for the operational-intelligence workstream exists under the filename
`docs/architecture/CARBONTALLY_PHASE9_SYSTEM_RUNTIME_AND_OPERATIONAL_INTELLIGENCE_BASELINE_20260912.md`.
Its `Phase 9` identifier was **never PO-ratified**, is explicitly marked
unobtained within that document, and is **historical working terminology only**.
That document does **not** create a Phase 9, and it must not be read as doing so.
The bounded workstream is now referred to as **Phase 8-X — Operational
Intelligence**. Its baseline is otherwise unaffected by this register.

---

## 12. Source and Lineage

### 12.1 Authoritative technical source

| Document | Role |
|---|---|
| `docs/architecture/CARBONTALLY_RLS_PRODUCTION_BASELINE_AND_REMEDIATION_SPEC_20260912.md` | **Authoritative.** Contains the full production baseline, evidence classification, finding dispositions, remediation groups with per-group SQL operation types, test matrix, rollout procedure, rollback strategy and stop conditions. **This register duplicates none of that detail.** |

### 12.2 Related production / security documentation

| Document | Role |
|---|---|
| `docs/architecture/CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md` | Predecessor read-only reconciliation; first recorded the `emission_factors` exposure and the `UNKNOWN` production RLS state. |
| `docs/architecture/CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md` | Migration-by-migration production status and risk classification; source of the batching prohibition (§7.4). |
| `docs/architecture/CARBONTALLY_PRODUCTION_READINESS_AUDIT_20260911.md` | Production readiness position (records the verified **local/dev** RLS boundary — 116 tables / 175 policies — which is *not* production state). |
| `docs/architecture/CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md` | Authentication / access model. |
| `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` | Architecture source of truth. |
| `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` | PO-ratified product roadmap; terminates at Phase 8 (no Phase 9/10). |
| `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` | Actor/workspace/access model; §39/§39.1 record the historical RLS recursion defect and its fix (historical implementation lineage only — not product phase terminology). |
| `AGENTS.md` | Project governance: RLS policy rules, database change policy, tenant isolation, security boundary principles. |

### 12.3 Schema, migration and code evidence

| Artefact | Role |
|---|---|
| `database/rc1/004_rc1_rls.sql`, `database/rc2/004_rc2_rls.sql` | RC RLS storeys; record the tenancy-hole warning and the "never DISABLE RLS" guidance. |
| `supabase/migrations/00000000000000_init_schema.sql` (lines 2319–2324) | The bulk RLS-enablement loop; introduced by `dbe72aa` into an already-applied migration (§4.5a). |
| `supabase/migrations/20260822000000_p9_rls_recursion_fix.sql` | Hard prerequisite (§7.1). |
| `supabase/migrations/20260831030000_tenant_org_id_not_null.sql` | Hard prerequisite (§7.2). |
| `backend/infra/supabase.py` | Backend privileged access path (`postgres` / `service_role`, both `BYPASSRLS`) — the reason enabling RLS is low-risk to the backend. |
| `frontend/src/lib/realtime/manager.js` | Realtime subscription inventory (§4.6). |

### 12.4 Documents created by this task

| Document | Purpose |
|---|---|
| `docs/architecture/CARBONTALLY_PRODUCTION_RLS_SECURITY_HOLD_AND_REMEDIATION_REGISTER_20260912.md` | This register. |
| `docs/ohd/reports/CT-SEC-RLS-HOLD-REGISTER-20260912-001.md` | Mandatory task report. |

### 12.5 Lineage summary

```text
CT-SEC-RLS-PRODUCTION-ACTIVATION-20260912-001   (discovery; INCONCLUSIVE — PO review required)
        ↓
PO-ratified as a discovery/security checkpoint
        ↓
CT-SEC-RLS-PRODUCTION-BASELINE-AND-REMEDIATION-SPEC-20260912-001
        (production baseline VERIFIED; remediation specification produced)
        ↓
CT-SEC-RLS-HOLD-REGISTER-20260912-001           (this register; remediation DEFERRED,
                                                 NOT AUTHORIZED, gate controlled)
```

---

## 13. Project-Control Status Summary

| Field | Value |
|---|---|
| Discovery | **COMPLETE** (read-only, independently performed) |
| Production baseline | **VERIFIED** on 2026-09-12 (point-in-time; requires re-verification on reopening) |
| Findings accepted | **YES** — as a genuine production security concern |
| Remediation authorized | **NO** |
| Remediation implemented | **NO** |
| Remediation status | **DEFERRED / NOT YET AUTHORIZED** |
| RLS-4A-1 | **NOT AUTHORIZED / NOT IMPLEMENTED** |
| RLS-4A-2 | **NOT AUTHORIZED / NOT IMPLEMENTED** |
| Outstanding migration backlog | **NOT APPLIED / NOT ADJUDICATED** |
| `FORCE RLS` | **DEFERRED** (pre-existing ratified position) |
| Open PO decisions | **13** (§8) |
| Hard prerequisites | **2** (§7.1, §7.2) |
| Sequence discrepancy | **1** (§6.1 — RLS-4) |
| Reopening trigger | **Explicit PO authorization only** (§10) |
| Owner | **Product Owner** (authorization); engineering/security to implement once authorized |
| Next action | **None.** Await Phase 8 → Phase 8-X → explicit gate reopening. |

---

**END OF REGISTER**

> **Status line for handover:** Production RLS security remediation is
> **DEFERRED / NOT YET AUTHORIZED**. The verified production exposure recorded in
> §4 and §5 remains **unremediated**. No part of the remediation sequence in §6
> has been implemented. Reopening requires explicit Product Owner authorization
> (§10).
