# CT-FINAL-03 — RLS SECURITY REMEDIATION: IMPLEMENTATION & VERIFICATION MANIFEST

**Document** `10-final-03-rls-remediation-implementation-and-verification-20261002.md`
**Date** 2026-10-02
**Author** Cline (implementation). **NOT independent verification** — CoStrict verification is a separate, later step.
**Authority** Owner implementation authorisation of 2026-10-02, implementing package `08`
(`08-final-03-p2-p5-p6-rls-decision-package-20261002.md`) and package `09`
(`09-final-03-r1-r2-r3-remediation-decision-20261002.md`).
**Objective implemented** RLS on a security-first / least-privilege / fail-closed model, with **no known
unnecessary RLS-disabled table left behind** (§1.5). The old `149 / 149 / 271` baseline was explicitly
**not** an objective (package `09` §6.0).

**STATUS: `FINAL-03 RLS SECURITY REMEDIATION — SINGLE RESIDUAL CLOSED — READY FOR INDEPENDENT VERIFICATION`**

> **Third pass (2026-10-02, residual closure).** The owner has taken the recorded hygiene option for the
> single remaining residual: `public.staff_workload` is RLS-enabled fail-closed with **zero** policies, by
> the *additive* follow-up migration `20261029000000_ct_final_03_staff_workload_rls.sql` (§1.5, §2.5).
> The already-accepted 43-table artefact `20261028000000_…` is **byte-for-byte unchanged** — the residual
> was closed by *adding* a migration, not by editing one (governance rationale: that file's own header and
> §1.5 below). Nothing else changed: no policy created/dropped/altered, no grant, no data, no schema, no
> production contact, no deploy, no P5/P6, no commit and no push.

---

## 0. What was implemented (one paragraph)

Two additive, security-only migrations enable RLS on **44** tables and create, drop or alter **no** policy:
`20261028000000_ct_final_03_rls_security_remediation.sql` (43 tables — 41 fail-closed with **zero**
policies, 2 enable-only with their existing policies kept untouched) and its residual-closure follow-up
`20261029000000_ct_final_03_staff_workload_rls.sql` (`staff_workload` — fail-closed, **zero** policies,
§1.5). Neither changes a grant, a row, or the schema, and both are proven at the database level to be a
true before/after fix (authenticated/anon access closed, `service_role` backend access preserved). The 23
direct browser/PostgREST call sites from package `09` are all resolved (8 removed as dead or
unauthorised, 12 re-pointed to admin-gated or session-authenticated backend endpoints, 3 retained because
their existing policies already cover them). Four small backend endpoints were completed/added to receive
the moved calls. A focused static + live RLS test suite was added and passes.

---

## 1. Migration manifest

| Item | Value |
|---|---|
| File (1) | `supabase/migrations/20261028000000_ct_final_03_rls_security_remediation.sql` — the 43-table artefact (unchanged since it was accepted) |
| File (2) | `supabase/migrations/20261029000000_ct_final_03_staff_workload_rls.sql` — the additive residual closure for `staff_workload` (full manifest in §1.5) |
| File (1) size | 312 lines |
| File (2) size | 222 lines |
| Ordering | File (1) sorts directly after the previous head, `20261027000000_ct_backup_02_backup_sets_and_verification.sql`; File (2) sorts directly after File (1). Both orderings are asserted by tests, and File (2)'s target set is asserted **disjoint** from File (1)'s |
| Statement executed | exactly one form: `ALTER TABLE public.<t> ENABLE ROW LEVEL SECURITY` (a single `EXECUTE format(…)` inside one `DO` block) |
| Policies created | **0** |
| Policies dropped/altered | **0** |
| Policies retained | **4** (all pre-existing, untouched) |
| Grants / default privileges / FORCE RLS / functions / storage | untouched |
| Data statements (INSERT/UPDATE/DELETE/TRUNCATE/DROP) | **none** |
| Idempotent | yes — re-run verified as a no-op (exit 0, identical counts) |
| Rollback | documented in the file header: the exact inverse is `ALTER TABLE … DISABLE ROW LEVEL SECURITY` per table, **owner-authorised reversal only**, requiring a new migration + written risk acceptance |

### 1.1 Group A — fail-closed: RLS enabled, ZERO policies (41 tables)

| Source | Tables |
|---|---|
| §3 CRITICAL (R-1/R-2/R-3) — 4 | `system_settings`, `staff_roles`, `password_reset_tokens`, `beta_access_codes` |
| §5 remaining Class-C — 9 | `beta_users`, `email_logs`, `notifications`, `review_audit_trail`, `waitlist`, `audit_trail`, `consultant_billing`, `consultant_tasks`, `login_history` |
| §6 Class-D (D-6 "enable now") — 9 | `conversation_activity_log`, `message_activity_log`, `report_comments`, `report_versions`, `staff_activity_log`, `typing_status`, `user_activity_log`, `user_presence`, `verification_logs` |
| §8 Class-B "free enablement" — 19 | `approval_decisions`, `approval_requests`, `dashboard_metrics`, `notification_delivery`, `processing_assignments`, `processing_audit_trail`, `processing_steps`, `processing_time_log`, `qc_checklists`, `qc_checks`, `qc_errors`, `queue_settings`, `reassignment_history`, `review_assignment_history`, `sla_compliance`, `staff_daily_performance`, `staff_performance`, `team_performance`, `verification_activity_log` |

**Class-B rationale (authorisation §8 requires the exact list and rationale).** Each of the 19 was
verified in this pass to have **zero browser references of any kind** — no `from('<table>')` and no
realtime `table: '<table>'` in `admin/src` or `frontend/src` — and no authenticated write path; every
current writer is the `service_role` backend or a migration. Enabling RLS is therefore free: there is no
legitimate direct PostgREST access to break, and the class-B re-classification gate ("re-classify when
the owning feature ships") is unaffected because a future feature would flow through a backend endpoint,
which RLS does not impede.

### 1.2 Group B — enable only, policies preserved (2 tables)

| Table | Retained policies (4 total, untouched) |
|---|---|
| `conversation_participants` | `conversation_participants_select`, `conversation_participants_update_own`, `conversation_participants_entity_select` |
| `manual_extraction_items` | `manual_extraction_items_entity_select` |

### 1.3 Deliberately NOT in this migration

| Item | Why |
|---|---|
| `emission_factors`, `business_hours`, `sla_definitions` (Class A) | Containment / config: `authenticated` holds no privileges on `emission_factors`; the other two are tenant-agnostic, row-less configuration. Authorisation §7: do not add RLS merely to improve a count. |
| `staff_workload` | **CLOSED by File (2)** — RLS enabled fail-closed, zero policies (§1.5, §2.5). Phase 1 recorded it as the single residual under package `09` §6.0's recorded option *"RLS + 0 policies (free)"*; the owner (2026-10-02, third pass) chose that option rather than accept-and-gate. |
| `service_role` = ALL on the 47 | The deliberate backend trust model (package `09` I-3/I-4), not a defect. |

### 1.4 Guards and post-conditions built into the migration

Refuses to run (`RAISE EXCEPTION`) when: the approved-set definition has been edited (41/2/4 arithmetic);
`conversation_participants` or `manual_extraction_items` is absent (wrong-target check); `anon` /
`authenticated` hold `BYPASSRLS` (enforcement would be theatre); a Group-A table already carries a policy
(an unrecognised grant path); the retained policy family has changed. It proves after enablement that
every present approved table is RLS-enabled, the **total policy count in `public` is unchanged** (delta
0), the retained policy family is byte-for-byte identical, and no approved table carries FORCE ROW LEVEL
SECURITY (package 08 D-11 remains deferred), and the two enable-only tables keep their policies
byte-for-byte. File (2)'s own guards and post-conditions are listed in §1.5.

---

### 1.5 File (2) — the residual closure for `staff_workload` (full manifest)

| Item | Value |
|---|---|
| Authority | Owner implementation authorisation (2026-10-02, third pass): *"enable RLS on `public.staff_workload` using the same fail-closed model … Do not weaken or create a policy merely to preserve legacy behaviour."* |
| File | `supabase/migrations/20261029000000_ct_final_03_staff_workload_rls.sql` |
| Why a separate file (governance) | `AGENTS.md` §66 requires a migration for every schema change and the repository states **no rule permitting an already-created migration to be edited**. File (1) is the artefact **accepted for independent verification in principle**; editing it would change accepted bytes. The authorisation's default is therefore "do **not** modify the already-created migration — add the change safely according to the repository's migration rules", which is what this additive file does. There is **no duplicate and no conflict**: `staff_workload` is not in File (1)'s approved set (41 + 2 = 43), neither file creates or drops a policy, and the two table sets are asserted **disjoint** |
| Statement executed | exactly one form, as in File (1): `ALTER TABLE public.<t> ENABLE ROW LEVEL SECURITY` (a single `EXECUTE format(…)` inside one `DO` block) — one table |
| Tables | `staff_workload` only — RLS enabled, **ZERO** policies |
| Policies created / dropped / altered | **0 / 0 / 0** |
| Grants, default privileges, FORCE RLS, functions, triggers, storage, schema, columns, indexes | untouched |
| Data statements (INSERT/UPDATE/DELETE/TRUNCATE/DROP) | **none** |
| Guards | (0) set-arithmetic (exactly 1 target); (1) **wrong-target**: `public.staff_workload` absent → `RAISE EXCEPTION`; (2) `anon`/`authenticated` must not hold `BYPASSRLS` (or the enablement would be theatre); (3) the table must carry **no** policy before enablement (an existing policy is an unrecognised grant path to review) |
| Post-conditions | the table **is** RLS-enabled; it carries **0** policies; the total `public` policy count is **unchanged** (delta 0); `FORCE ROW LEVEL SECURITY` is still off |
| Idempotent | yes — re-run verified as a no-op (exit 0; `rls_enabled_before=t`, `policies 218 → 218`) |
| Rollback | documented in the file header: the exact inverse is `ALTER TABLE public.staff_workload DISABLE ROW LEVEL SECURITY;` — **owner-authorised reversal only**, requiring a new migration + written risk acceptance |
| Deliberate difference from File (1) | File (1) *skips* absent approved tables with a `NOTICE` (RLS-4B precedent, so a partial clone cannot be broken). File (2) has exactly one target, so absence means "not a CarbonTally database" and it **fails loudly rather than silently no-opping on a security control**. The table is created by `00000000000000_init_schema.sql:1253`, so every database built from this repo's migration chain has it |
| A target where the table is *already* RLS-enabled | accepted: the enablement is then a no-op and the post-conditions still have to hold (stated in the file header, because the local dev cluster enables RLS on all 135 of its public tables — see §2.5) |

**Browser paths — the phase-1 deletion stands; nothing is weakened or worked around**

* The only browser *read* of the table was already deleted in phase 1 (`admin/src/pages/admin/WorkHub.jsx`;
  it selected `assigned_reviews`, `in_progress_reviews`, `last_updated`, which exist nowhere — package `09`
  §4.7). It is **not** restored; only its explanatory comment was updated to state the new RLS state.
* One inert realtime subscription registration remains: `frontend/src/lib/realtime/manager.js:243-251`
  (`channel.on('postgres_changes', { event: 'UPDATE', table: Tables.STAFF_WORKLOAD, filter: 'staff_id=eq.…' })`,
  with `Tables.STAFF_WORKLOAD = 'staff_workload'` at `frontend/src/lib/realtime/types.js:60`). With RLS
  enabled and **zero** policies it can deliver no row to `anon`/`authenticated`. Per the authorisation it
  is left exactly as it is — no policy is created to preserve it — and it is recorded here as a
  knowingly-inert browser path. It carried nothing meaningful before either: the table holds 0 rows in
  every environment inspected, and the local cluster already had RLS enabled on it.
* Current readers/writers are the `service_role` backend only (`backend/utils/staff_workload.py`;
  `backend/routes/admin/{workload,reviews,staff,dashboard,assignments}.py`), which `BYPASSRLS` leaves
  unaffected — verified live in §2.5.

---

## 2. Verification results (local disposable environment only)

**Environment used** — the repository's isolated local cluster (`backend/.env`: *"ISOLATED LOCAL ENV
for 93d5cdd … Disposable database on the local cluster; no production endpoint is referenced"*).
The migration was applied **only** to a scratch clone (`CREATE DATABASE ct_f03_rls_verify TEMPLATE
ct_local_93d5cdd`) after RLS was deliberately disabled on the 43 tables to reproduce the measured
pre-remediation baseline. **Production, Render, Vercel and the production Supabase project were not
contacted.** The clone and all probes are disposable; no row was created, changed or deleted anywhere
(the test suite asserts this independently — §5).

**Residual-closure pass (third pass).** File (2) was verified on a **second, freshly created** disposable
clone — `CREATE DATABASE ct_f03_sw_verify TEMPLATE ct_local_93d5cdd` — into which File (1) and then File (2)
were applied in chain order (both exit 0). Because the local cluster is *not* in production's RLS
pre-state (it enables RLS on all **135** of its public tables, whereas production has RLS off on these 44 —
packages `08`/`09`), the pre-state was reproduced exactly as in the first pass: RLS was deliberately
**disabled** on the 44 tables (the 43 approved + `staff_workload`) in the clone, leaving `91 of 135`
enabled. That yields the true production pre-state for the residual, including
`staff_workload rls_on=false, policies=0` with `authenticated` holding SELECT/INSERT/UPDATE/DELETE grants
(§2.5). This is stated explicitly because it is the one thing a verifier must not mistake for a
discrepancy: **the local cluster is a fully-RLS-enabled local environment, not a copy of production.**

### 2.1 Before / after enforcement (database level, role-played identities)

`SET LOCAL ROLE <role>` (+ `request.jwt.claims` where a subject matters) — the same mechanism PostgREST
uses. `N rows returned` pre-state = the live exposure; `0 rows returned` post-state = RLS deny-all.

| Table | PRE `authenticated` | PRE `anon` | POST `authenticated` | POST `anon` |
|---|---|---|---|---|
| `system_settings` | **1 row returned** | DENIED | 0 rows returned | DENIED |
| `staff_roles` | **3 rows returned** | DENIED | 0 rows returned | DENIED |
| `password_reset_tokens` | 0 rows returned | DENIED | 0 rows returned | DENIED |
| `beta_access_codes` | 0 rows returned | DENIED | 0 rows returned | DENIED |
| `audit_trail` | 0 rows returned | DENIED | 0 rows returned | DENIED |
| `beta_users`, `email_logs`, `notifications`, `waitlist`, `login_history`, `consultant_billing`, `consultant_tasks`, `review_audit_trail` | 0 rows returned (reachable — grant held) | DENIED | 0 rows returned | DENIED |

The PRE column is the exposure package `09` describes: `system_settings` (**R-1**: the production email
provider/sender row) and `staff_roles` (**R-2**: the permission catalogue) were readable *and writable*
by any authenticated JWT — confirmed here with real row counts, not inferred.

### 2.2 Writes after enablement (all fail closed)

| Probe | Result |
|---|---|
| `authenticated` INSERT into `beta_users` | `ERROR: new row violates row-level security policy for table "beta_users"` |
| `authenticated` INSERT into `review_audit_trail` | `ERROR: new row violates row-level security policy for table "review_audit_trail"` |
| `authenticated` INSERT into `password_reset_tokens` | refused |
| `authenticated` UPDATE `system_settings` / `staff_roles` / `consultant_billing` | `UPDATE 0` |
| `authenticated` DELETE `audit_trail` / `login_history` / `consultant_tasks` / `notifications` / `email_logs` | `DELETE 0` |
| `anon` INSERT `waitlist` | `ERROR: permission denied for table waitlist` |
| `anon` UPDATE `beta_access_codes` | refused |

### 2.3 Backend access preserved (`service_role`)

| Probe | Result |
|---|---|
| `service_role` SELECT `system_settings` | 1 (unchanged) |
| `service_role` SELECT `manual_extraction_items` | 1 (unchanged) |
| `service_role` SELECT `conversation_participants` | 0 (unchanged) |

### 2.4 Migration mechanics

| Check | Result |
|---|---|
| First application | `begin → DO → commit`, exit 0; `NOTICE: CT-FINAL-03: approved=43, present=43, absent_skipped=0, enabled_before=0, enabled_after=43, statements_run=43, policies_before=218, policies_after=218 (delta 0), fail-closed tables=41 (0 policies), retained-policy tables=2 carrying 4 policies…` |
| RLS state after | `43/43` approved tables RLS-enabled |
| Policy count | `218 → 218` (delta **0**) — no policy created or dropped |
| Policies on the fail-closed group | `0` |
| Retained policies | exactly `conversation_participants_entity_select, conversation_participants_select, conversation_participants_update_own, manual_extraction_items_entity_select` |
| FORCE ROW LEVEL SECURITY | `0` tables (untouched) |
| Idempotency (re-run) | exit 0; `enabled_before=43`, policy count still 218, `43/43` enabled — true no-op |
| Data preserved | `system_settings=1`, `manual_extraction_items=1` (retained rows intact) |
| Static scan of the file | no `DELETE`/`TRUNCATE`/`DROP`/`GRANT`/`REVOKE`/`INSERT`/`UPDATE` statement; the only DDL is the single `ALTER TABLE … ENABLE ROW LEVEL SECURITY` |

---

### 2.5 Residual closure: `staff_workload` — before / after with a real row present

The **same** probe script was run before and after File (2) on the disposable clone, with a synthetic row
seeded inside a transaction that is **always rolled back** — so "0 rows" can never be confused with "the
table happens to be empty", and the only variable between the two runs is RLS.

```
-- /tmp/f03_sw_probe.sql (throw-away; every write is rolled back at the end)
BEGIN;
INSERT INTO public.users …; INSERT INTO public.staff_profiles …; INSERT INTO public.staff_workload …;  -- 1 row
SAVEPOINT s_auth; SET LOCAL ROLE authenticated;
  SELECT set_config('request.jwt.claims', json_build_object('sub','…','role','authenticated')::text, true);
  SELECT count(*) FROM public.staff_workload;
  UPDATE public.staff_workload SET workload_score = 999;
  DELETE FROM public.staff_workload;
  INSERT INTO public.staff_workload (staff_id, assigned_tasks) VALUES ('…', 1);
ROLLBACK TO SAVEPOINT s_auth;
SAVEPOINT s_anon; SET LOCAL ROLE anon; SELECT count(*) …; INSERT …; UPDATE …; DELETE …; ROLLBACK TO SAVEPOINT s_anon;
SAVEPOINT s_svc;  SET LOCAL ROLE service_role; SELECT count(*) …; UPDATE … SET workload_score = workload_score;
ROLLBACK TO SAVEPOINT s_svc;
RESET ROLE; SELECT 'AFTER PROBES (owner): rows = '||count(*)||' max(workload_score) = '||max(workload_score) FROM public.staff_workload;
ROLLBACK;
```

| Probe (the row exists in **both** runs) | PRE — RLS **off** (production pre-state) | POST — RLS **on, 0 policies** |
|---|---|---|
| `authenticated` `SELECT count(*)` | **1** (fully exposed) | **0** |
| `authenticated` `UPDATE …` | **UPDATE 1** | **UPDATE 0** |
| `authenticated` `DELETE FROM …` | **DELETE 1** | **DELETE 0** |
| `authenticated` `INSERT …` | **INSERT 0 1** (accepted) | `ERROR: new row violates row-level security policy for table "staff_workload"` |
| `anon` `SELECT` | `ERROR: permission denied for table staff_workload` (no grant — `anon` is contained by grants, not by RLS) | same |
| `service_role` `SELECT` / `UPDATE` | 1 / `UPDATE 1` | **1 / `UPDATE 1` — backend preserved** |
| owner view at the end of the transaction | 1 row, `workload_score` = 1 | 1 row, `workload_score` = 1 (nothing mutated) |
| after `ROLLBACK` | 0 rows | 0 rows — the probe row never existed outside the transaction |

Pre-state facts captured on the clone before File (2): `rls_on=false force_rls=false policies=0 rows=0`;
grants `authenticated SELECT=true INSERT=true UPDATE=true DELETE=true`, `anon SELECT=false`; totals
`rls_enabled_tables=91 of 135 | policies_in_public=218`.

### 2.6 Residual-closure migration mechanics

| Check | Result |
|---|---|
| File (1) re-application on the clone (unchanged artefact, chained first) | exit 0; `NOTICE: approved=43, present=43, absent_skipped=0, enabled_before=0, enabled_after=43, statements_run=43, policies_before=218, policies_after=218 (delta 0) …` |
| File (2) first application | exit 0; `NOTICE: … pre-enable grant/RLS state on public.staff_workload — rls_on=f, force_rls=f, policies=0, authenticated SELECT/INSERT/UPDATE/DELETE=t, anon SELECT=f`; then `targets=1, rls_enabled_before=f, rls_enabled_after=t, policies_on_target=0, policies_before=218, policies_after=218 (delta 0), force_rls=off` |
| RLS state after | the 44 target tables **44/44** RLS-enabled; clone total back to **135/135** |
| Policy count | `218 → 218` (delta **0**) — no policy created, dropped or altered by either file |
| Policies on `staff_workload` | **0** (fail-closed) |
| FORCE ROW LEVEL SECURITY | **0** tables (untouched) |
| Idempotency (re-run of File (2)) | exit 0; `rls_enabled_before=t, rls_enabled_after=t, policies 218 → 218` — true no-op |
| Data preserved | `staff_workload` = 0 rows before and after; the probe row existed only inside a rolled-back transaction; the **source** database `ct_local_93d5cdd` re-checked unchanged (`135/135`, `218` policies, `staff_workload rls=true rows=0`) |
| Static scan of File (2) | no `DELETE`/`TRUNCATE`/`DROP`/`GRANT`/`REVOKE`/`INSERT`/`UPDATE` statement; the only DDL is the single `ALTER TABLE … ENABLE ROW LEVEL SECURITY` |
| No production contact | the local cluster `127.0.0.1:54426` only; nothing deployed; nothing committed (§7.2) |
| Wrong-target guard (target absent) | verified on a throw-away clone with `staff_workload` dropped: `ERROR: CT-FINAL-03 residual precondition failed: public.staff_workload is absent — refusing to no-op on a security control (wrong target?)` — the transaction aborted, **nothing was applied**, and the clone was dropped afterwards. This is the deliberate difference from File (1)'s skip-absent behaviour (§1.5) |
| Policy-drift guard (policy pre-existing) | not exercised (no policy exists on the table anywhere it was inspected, so the guard's `RAISE` path could not be reached without creating one — which the authorisation forbids); it is the same construct as File (1)'s Group-A drift guard, which File (1)'s own tests cover |

---

## 3. Browser / PostgREST call-site remediation — all 23 sites

`Action` legend: **REMOVED** = deleted (dead, unauthorised, or duplicating a backend-owned record);
**RE-POINTED** = now calls a backend endpoint; **UNCHANGED** = retained because the existing policy
already covers it (the enable-only group).

| # | Site (as filed in package `09`) | Table | Action | Destination / reason |
|---|---|---|---|---|
| 1 | `admin/src/pages/admin/Settings.js:67-71` | `system_settings` | **RE-POINTED** | `GET /api/v3/settings/upload-policy` + `GET /api/v3/settings/retention` (both `require_admin()`) |
| 2 | `admin/src/pages/admin/Settings.js:117-131` (`createDefaultSettings`) | `system_settings` | **REMOVED** | Targeted non-existent columns (`settings_json`, `max_file_size_mb`, …); defaults are backend-owned (`backend/data/settings.py`) and must not be browser-seeded |
| 3 | `admin/src/pages/admin/Settings.js:155-182` (save) | `system_settings` | **RE-POINTED** | `PUT /api/v3/settings/upload-policy` + `PUT /api/v3/settings/retention`, only for the limits the backend genuinely persists |
| 4 | `admin/src/pages/admin/BetaManagement.js:35` | `waitlist` | **RE-POINTED** | `GET /api/waitlist/` (now `require_admin()`) |
| 5 | `admin/src/pages/admin/BetaManagement.js:58` | `email_logs` | **RE-POINTED** | `GET /api/admin/logs/email?type=beta_invite&limit=100` (existing, `require_admin()`) |
| 6 | `admin/src/pages/admin/BetaManagement.js:99` | `beta_access_codes` | **RE-POINTED** | `GET /api/admin/beta/codes?email=…&limit=1` (existing, `require_admin()`) |
| 7 | `admin/src/pages/admin/WorkHub.jsx:194` | `notifications` | **REMOVED** | Dead: selects `user_id`, the table exposes `recipient_id`/`recipient_type` → PostgREST error, discarded by destructuring. `/api/v3/notifications` remains authoritative |
| 8 | `admin/src/pages/admin/WorkHub.jsx:250` | `staff_workload` | **REMOVED** | Dead: selects `assigned_reviews`, `in_progress_reviews`, `last_updated`, which exist nowhere (package `09` §6.0.1) |
| 9-13 | `admin/src/services/reviewService.js:40,68,123,184` (4 INSERTs) | `review_audit_trail` | **REMOVED** | Audit records must not be manufactured by an authenticated browser; no server-side authorisation existed for these writes |
| 14 | `admin/src/services/reviewService.js:137` | `review_audit_trail` | **RE-POINTED** | `GET /api/admin/reviews/history/audit` (existing, `require_admin()`) |
| 15 | `frontend/src/BetaLogin.jsx:72-76` | `beta_users` | **RE-POINTED** | `GET /api/beta/me` (session-authenticated; replaces the beta-access-list read) |
| 16 | `frontend/src/BetaLogin.jsx:135-139` | `beta_users` | **RE-POINTED** | `GET /api/beta/me` |
| 17 | `frontend/src/BetaSignup.jsx:35-39` | `beta_access_codes` | **RE-POINTED** | existing session-free `GET /api/admin/beta/codes/validate/{code}` (no token material returned) |
| 18 | `frontend/src/BetaSignup.jsx:83-87` | `beta_users` | **REMOVED** | Duplicated backend-owned data; the same condition is already handled by the `signUp()` "User already registered" branch |
| 19 | `frontend/src/BetaSignup.jsx:120-126` | `beta_access_codes` (mark used) | **RE-POINTED** | `POST /api/beta/redeem` (session identity used; no client-supplied email) |
| 20 | `frontend/src/BetaSignup.jsx:129-136` | `beta_users` (insert) | **RE-POINTED** | `POST /api/beta/redeem` — the self-grant path is gone: no client-supplied `user_id`/`access_level` |
| 21 | `frontend/src/BetaSignup.jsx:139-145` | `waitlist` (activate) | **RE-POINTED** | `POST /api/beta/redeem` (server-side, keyed to the verified session email) |
| 22 | `frontend/src/lib/realtime/manager.js:397-408` | `conversation_participants` | **UNCHANGED** | Legitimate own-membership read; covered by `conversation_participants_select` |
| 23 | `frontend/src/components/chat/ChatWidget.jsx:40-44` | `conversation_participants` | **UNCHANGED** | Legitimate own-membership read; covered by the existing policy |
| 24 | `frontend/src/components/chat/ChatWindow.jsx:108-115` | `conversation_participants` | **UNCHANGED** | Legitimate membership read; covered by the existing policy |

*(Rows 9–13 are the five elements of one block — four INSERT sites plus one SELECT — giving 23 total
sites across 10 tables, matching package `09` §4 / R-6.)*

**Net effect** — 8 sites removed, 12 re-pointed (of which three `BetaSignup` writes were consolidated
into one new endpoint call), 3 unchanged. Post-change verification of the source tree: the only remaining
`from('<protected table>')` occurrences in `admin/src` + `frontend/src` are the three
`conversation_participants` reads above, plus one comment in `RealtimeContext.jsx` recording that the old
`notifications` read is gone.

### 3.1 Backend endpoints completed or added (the minimum required to receive the moved calls)

| Endpoint | Status | Auth model |
|---|---|---|
| `GET /api/waitlist/` | **completed** (was a `pass` stub) | `require_admin()` — server-side listing with `status` / `search` filters |
| `POST /api/waitlist/` | **completed** (was a `pass` stub) | public by design (landing-page signup); server-side `service_role` write, upsert on email |
| `GET /api/beta/me` | **new** (`backend/routes/beta_access.py`) | `require_auth()` — answers only about the caller's own session email |
| `POST /api/beta/redeem` | **new** (`backend/routes/beta_access.py`) | `require_auth()` — redeems the caller's own code: marks it used, provisions their `beta_users` row (`access_level` is a server constant), activates their waitlist entry; rejects a code issued to a different address |

Both new endpoints take **identity from the session only** — no client-supplied `email`, `user_id` or
`access_level` — which is what removes the self-grant vector recorded in package `09` §4.2. They are
registered in `backend/routes/__init__.py` and `backend/main.py`; the app's OpenAPI surface confirms
`/api/beta/me`, `/api/beta/redeem` and `/api/waitlist/` are served (623 paths in total; import exit 0).

### 3.2 Support module added to the admin bundle

`admin/src/services/adminApi.js` — a small shared authenticated fetch helper mirroring the existing
`factorAdminService.js` pattern (bearer token from the Supabase session, JSON headers, error surfaced
with `.status` / `.raw`). The browser never reaches a protected table directly; the authorization
decision is always the backend's.

---

## 4. Tests added and run

### 4.1 New focused suite

`backend/tests/integration/test_final_03_rls_remediation_live.py` — static + live, ~830 lines (601 before
the residual-closure additions). The
approved table groups are **parsed out of the migration**, so the test cannot drift from the artefact it
verifies; the live half refuses any non-disposable target and creates its fixtures inside a transaction
that is **always rolled back**.

| Class | Tests |
|---|---|
| Static (no DB) | ordering after the previous head; approved-set arithmetic (41/2/4); Class A untouched; `staff_workload` **not** in the 43-table artefact's groups (still documented there) because it is closed by File (2); no data/destructive/GRANT/REVOKE/CREATE-POLICY statement (comments and string literals stripped first); the only executed DDL is enablement; rollback + non-scope documentation present |
| Static — File (2) (no DB) | File (2) sorts directly after File (1); its declared target set is exactly `['staff_workload']` and is **disjoint** from File (1)'s groups (no duplicate/conflicting migration); no data/destructive/GRANT/REVOKE/CREATE-POLICY statement; the only executed DDL is enablement; rollback + non-scope **and the separate-file governance rationale** (`AGENTS.md`, the accepted artefact name) documented |
| Live — structure | RLS enabled on every approved table; zero policies on the fail-closed group; retained policy family intact (and no `anon`, no bare `USING (true)`); no broad authenticated policy on any approved table; FORCE RLS untouched; `anon`/`authenticated` do not hold BYPASSRLS |
| Live — enforcement | `anon` denied on all 41 fail-closed tables; `authenticated` denied on all 41; 13 write probes (INSERT/UPDATE/DELETE) all refused; the token/settings/staff/audit/billing/telemetry table set stays denied; `service_role` backend paths still work |
| Live — retention semantics | `conversation_participants` **positive** cases (org member of the conversation's org; the participant themselves), **negative** cases (unrelated authenticated user), **cross-tenant** case (org A member cannot see org B), **anon** case, **positive** own-row UPDATE, **negative** UPDATE on another conversation, **negative** direct INSERT (server-authoritative write model); `manual_extraction_items` negative cases + backend positive + entity-staff positive (precondition derived from the policy's own `is_entity_member` predicate, skipped with an explicit reason when not constructible); the single retained policy asserted |
| Live — data safety (last) | a row-count fingerprint of `system_settings`, `manual_extraction_items`, `manual_extraction_batches`, `organizations`, `users`, `emission_factors`, `staff_workload` taken before any probe, re-asserted after — proving the verification mutated nothing |
| Live — residual closure (`staff_workload`) | RLS-enabled with **zero** policies and no FORCE RLS; `anon` + `authenticated` denied on SELECT; **row-level** proof — a probe row is seeded inside a transaction that is always rolled back, and `authenticated`/`anon` still get `SELECT 0` / `UPDATE 0` / `DELETE 0` and an `INSERT` refused with `InsufficientPrivilegeError` (a valid `staff_profiles` parent exists, so a constraint cannot be the cause) while `service_role` still reads and updates it |
| Live — [previous phases, unchanged] | enforcement/token/staff/audit/billing/telemetry denials; `service_role` backend paths; `conversation_participants` positive/negative/cross-tenant cases; `manual_extraction_items` retention semantics |

**Result — 30 passed, 1 skipped, 0 failed** (0.72 s; 31 collected). The previous pass reported 21 passed /
1 skipped; the increase is the six new static assertions plus the four new live `staff_workload` tests.

```
FINAL_03_RLS_TEST_DSN=postgresql://postgres:postgres@127.0.0.1:54426/ct_f03_sw_verify \
  python -m pytest tests/integration/test_final_03_rls_remediation_live.py -q -rs
→ 30 passed, 1 skipped
→ SKIPPED [1] … : no entity-allocated manual_extraction_batch here — positive case not constructible
```

Static half alone (no `FINAL_03_RLS_TEST_DSN`, so the live half self-skips): **12 passed, 19 skipped**,
exit 0 — it therefore also runs in any CI environment with no database.

The one skip is by design and reported as such: *"no entity-allocated manual_extraction_batch here —
positive case not constructible"*. In this clone the single retained `manual_extraction_batch` has
`entity_id IS NULL`, so no authenticated user can legitimately see its item (the retained policy requires
`entity_id IS NOT NULL`). That is the fail-closed behaviour asserted by the negative cases; the positive
branch runs automatically on any target that holds an entity-allocated batch (production holds the 14
retained rows package `09` §5.3 records).

### 4.2 Regression checks

| Check | Command | Result |
|---|---|---|
| Route unit suite | `pytest tests/unit/routes -q` | **25 passed**, exit 0 |
| Route unit suite — **re-run in the residual-closure pass** | `pytest tests/unit/routes -q` | **25 passed**, exit 0 (unchanged by this pass) |
| Syntax of the file changed in the residual-closure pass | `node -e "@babel/parser.parse('admin/src/pages/admin/WorkHub.jsx')"` | `PARSE OK` |
| `tests/test_all_endpoints.py` (re-run in this pass) | `pytest tests/test_all_endpoints.py -q` | **exit 5 — no tests collected**: it is a standalone script module, not a pytest module, so it is *not* claimed as a regression here |
| Whole app imports with every router (incl. the new one) | `python -c "import main; main.app.openapi()"` | exit 0; 623 OpenAPI paths; `/api/beta/me`, `/api/beta/redeem`, `/api/waitlist/` present |
| Python syntax of the changed/new backend files | `python -m py_compile …` | OK |
| Syntax of every changed front-end file (7 files) | Babel parse with the repo's `babel-preset-react-app` | all OK |
| Legacy endpoint scripts referencing `/api/waitlist/` (`tests/test_all_endpoints.py`, `test_api.py`, `test_api_simple.py`) | inspected | their expectations (`POST` public → 200; `GET` admin → 200) are satisfied *better* than before, when both handlers returned `null` |

### 4.3 Regression-suite scope (stated honestly)

`pytest tests/unit` (the full unit suite) was run twice in the residual-closure pass with a 25-minute cap.
Run 1 executed every test and printed the complete **short test summary: 9 failures**, then the process was
stopped by the cap before the totals line — so **no pass count is claimed**. Run 2 (`-x`) was stopped once
the same failures had been reproduced individually. The 9 failures were triaged, and **none is caused by
this change-set** (which adds one migration, one comment and test additions — no runtime code):

| # | Failing test | Cause | Pre-existing? |
|---|---|---|---|
| 1 | `tests/unit/backup/test_jobs.py::TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain` | asserts `names[-1] == 20261027000000_ct_backup_02_…` | **Yes** — recomputed **excluding** this pass's file: `names[-1]` is `20261028000000_…` (the phase-1 FINAL-03 migration), so the assertion was already false (`False` with **and** without the new file) |
| 2 | `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | asserts `names[-1] == 20261007000000_p8_insight_data_quality_reproducibility.sql` | **Yes** — already false without the new file (same recomputation) |
| 3 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | asserts `len(names) == 71` | **Yes** — the chain holds **97** migrations without the new file (98 with it); it was already 97 ≠ 71 |
| 4 | `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | asserts the set of migrations later than the i1 migration equals one of four fixed lists ending at `20261008000000_…` | **Yes** — the later set already contains the P16/P17/backup migrations, which are not in those lists |
| 5 | `tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | asserts every migration after the P16 baseline belongs to the P17 family | **Yes** — the P8/P16/STEP2/BACKUP/phase-1 FINAL-03 migrations that were already in the tree are not P17 family members |
| 6-8 | `tests/unit/engines/test_extraction_suggestions.py::{test_suggest_parses_clean_invoice, test_suggest_missing_fields_leave_unresolved, test_suggest_no_fabrication_on_garbage}` | `extraction_evidence` dict is non-empty where the test expects `{}` (engine behaviour) | **Yes** — unrelated module; no file in this change-set touches it |
| 9 | `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` | `body["verification_delivered"] is False` but was `True` (discovery route behaviour) | **Yes** — unrelated module; no file in this change-set touches it |

**Conclusion (stated plainly):** the full unit suite does **not** pass in this working tree, but the
failure set is **entirely pre-existing**. Failures 1-5 are "the newest migration in the chain" guard
snapshots from earlier phases that every subsequent phase (STEP2, BACKUP-01/02, phase-1 FINAL-03, and now
this pass) has invalidated; failures 6-9 are unrelated engine/route behaviours. Fixing the guards would
mean editing tests outside this authorisation, so they are **flagged for the owner** (§7.1) rather than
touched. The claimed evidence for this pass is therefore: the focused static+live RLS suite
(**30 passed / 1 skipped**, and **12 passed / 19 skipped** as static-only), `tests/unit/routes`
(**25 passed**), the Babel parse of the changed file, and the live before/after database evidence in §2.5.

---

## 5. Security invariants (§10 of the authorisation) — status

| # | Invariant | Status | Evidence |
|---|---|---|---|
| 1 | Anonymous users cannot directly access protected tables | **met** | `anon` denied on all **42** fail-closed tables (41 + the residual `staff_workload`) + write probes refused |
| 2 | Authenticated users cannot directly access protected tables unless an explicit least-privilege policy is required | **met** | `authenticated` gets 0 rows on all **42** — including the residual, proven against a real seeded row (§2.5) — and the only authenticated policies anywhere on the approved set are the 4 retained ones |
| 3 | No authenticated user can modify settings / staff permissions / password-reset tokens / beta credentials / audit trails / billing / login telemetry / consultant records | **met** | 13 write probes refused (RLS violation / `UPDATE 0` / `DELETE 0`) plus the residual-closure row-level write probes (`UPDATE 0`, `DELETE 0`, INSERT refused) |
| 4 | Service-role backend paths continue to function | **met** | `service_role` reads succeed on every probed table; `service_role` keeps BYPASSRLS; no grant changed |
| 5 | Legitimate tenant/consultant/customer access continues through the application API | **met** | all re-pointed calls go to existing backend endpoints (`/api/v3/settings/*`, `/api/admin/logs/email`, `/api/admin/beta/codes`, `/api/admin/reviews/history/audit`) plus the two session-authenticated beta endpoints; no backend route was changed in its authorization model |
| 6 | `manual_extraction_items` and `conversation_participants` policy semantics remain intact | **met** | retained policy family asserted unchanged (names, roles, `cmd`); positive/negative/cross-tenant cases exercised |
| 7 | No cross-tenant access is introduced | **met** | no policy was created at all; the cross-tenant negative case is exercised (org A member vs org B conversation); consultant tables now return 0 rows to everyone but `service_role` |
| 8 | No policy uses a client-controlled field as the sole security boundary | **met** | no policy was created; the two new endpoints derive identity from the session only (no client `email`/`user_id`/`access_level`), and `redeem` additionally binds the code to the address it was issued to |
| 9 | No broad `FOR ALL TO authenticated USING (true)` policy | **met** | asserted for every approved table; the policy count is unchanged (delta 0) |
| 10 | No secrets or token material become browser-readable | **met** | `password_reset_tokens` and `beta_access_codes` now deny all browser roles; the beta validation endpoint returns code metadata only — never `magic_token` |

---

## 6. Production-data preservation (§12) — status

| Requirement | Status |
|---|---|
| No production rows deleted / no truncate / no organization reset | **met** — no data statement exists in the migration or anywhere in this change-set; the only DB writes performed in verification were inside rolled-back savepoints in a disposable clone |
| The two retained owner/test organizations and accounts and their data untouched | **met** — nothing in the change-set addresses `organizations`, `organization_members` or `users`; the fingerprint test covers `organizations`/`users` row counts |
| The 7,049 emission factors untouched | **met** — `emission_factors` is Class A and is deliberately not in the migration; its row count is in the fingerprint |
| Local/demo data untouched | **met** — verification ran against `TEMPLATE` clones; the source database (`ct_local_93d5cdd`) and the demo lab were never written to, and the source was re-checked unchanged after the residual-closure pass (`135/135` RLS, `218` policies, `staff_workload` 0 rows) |
| Residual-closure pass introduced no data change | **met** — `staff_workload` held 0 rows before and after; the only writes anywhere were inside transactions that were rolled back (the probe row is created and destroyed in one transaction, asserted by the fingerprint test) |

**Retained-data reachability** (the point of the enable-only group): the 14 retained
`manual_extraction_items` rows stay reachable to their entity staff through
`manual_extraction_items_entity_select` and to the backend through `service_role` — never world-readable.
The conversation membership row stays reachable through the three existing policies.

---

## 7. Residuals, deliberate non-actions and limitations

### 7.1 Residual decision list (nothing hidden)

| Item | State | What is needed from the owner |
|---|---|---|
| `staff_workload` | **CLOSED — no residual** (RLS enabled fail-closed, zero policies, by File (2) on 2026-10-02) | none. The owner took package `09` §6.0's recorded hygiene option; there is **no** remaining RLS-disabled table in this change-set's scope and no waiver is outstanding |
| Legacy admin surfaces (`/admin/settings`, `/admin/beta-management`, `/admin/work-hub`) | re-pointed, not retired | a decision on whether these legacy pages are retired outright (package `09` §6.4 lists "whether the legacy Settings.js / BetaManagement.js / Waitlist admin pages are retired" as an owner decision) |
| Inert realtime subscription for `staff_workload` (`frontend/src/lib/realtime/manager.js:243-251`) | left exactly as it is (no policy created to preserve it) | none required for security; if the owner later wants the dead registration removed, that is a front-end cleanup, not an RLS decision |
| Five pre-existing migration-chain guard tests (`test_the_backup_migrations_are_the_newest_in_the_chain`, `test_i2_migration_is_the_latest_and_scoped_to_one_policy`, `test_migration_ordering_is_unchanged`, `test_i1_migration_is_the_latest_migration`, `test_p17_does_not_reuse_or_edit_a_historical_timestamp`) | **fail on any new migration and were already failing before this pass** (§4.3 — proven by recomputing each assertion with this pass's file excluded) | an owner/verification item: they are "the newest migration" snapshots from earlier phases that STEP2, BACKUP-01/02 and the phase-1 FINAL-03 migration already invalidated. Deliberately **not** touched here (editing them is outside this authorisation); they will need updating at freeze/P2. Four further failures (`test_extraction_suggestions` ×3, `test_v3_discovery` ×1) are unrelated pre-existing engine/route behaviours |
| `waitlist` invite flow (`/api/waitlist/invite` called by the admin page) | untouched | it is not a table path and was already calling a non-existent endpoint; unchanged by this change-set (documented, not invented) |
| D-1 freeze ratification, D-3 step-7 gate, D-4/P5 backup credentials + key escrow, D-5/P6 identities | untouched | standing owner decisions; explicitly out of this authorisation |

### 7.2 What was NOT done (hard-stop compliance)

* **No** production contact: no production Supabase change, no migration applied outside the disposable
  local clone, **no** Render deploy, **no** Vercel deploy.
* **No** P5 or P6 execution; no production secret was configured or read.
* **No** commit and **no** push (nothing was committed; `git status` remains as the owner left it plus
  these working-tree changes).
* **No** historical migration was modified; **no** new phase started.
* **No** migration applied anywhere except the two disposable local clones (`ct_f03_rls_verify` in the
  first pass, `ct_f03_sw_verify` in this one) — no production Supabase project was contacted, and no
  production secret was read or written.
* **The accepted 43-table artefact is byte-for-byte unchanged.** The single residual was closed by
  **adding** a migration, not by editing one (`AGENTS.md` §66 states no rule permitting an edit of an
  already-created migration; and editing an artefact already accepted for verification would invalidate
  that acceptance). The two files are disjoint and neither creates, drops or alters a policy.
* **No policy was created, dropped, altered or weakened anywhere** — not even to preserve the legacy
  `staff_workload` browser behaviour, which the authorisation explicitly forbade; the phase-1 deletion of
  the dead browser read is preserved and the inert realtime registration was left untouched rather than
  given a policy.
* **No** backend authentication model redesign: no change to `auth.py`, no new role, no change to how
  the backend authenticates or to `service_role` usage. No backend runtime code changed in this pass at
  all.
* **No** policy was created, dropped or weakened; `emission_factors` was not given RLS; the count was not
  bent to any baseline (the residual closure is a security decision, not a count exercise: 44 tables are
  now RLS-enabled, and Class A remains deliberately untouched).

### 7.3 Limitations a verifier should re-check

1. The live half was executed against a **local clone**; production's exact table set (150 tables vs the
   clone's 135) means the class-B/D tables that are absent locally were not exercised by the live tests.
   The migration skips absent tables and asserts on present ones, so behaviour is environment-safe — but
   the verifier should run the suite against a full clone of production.
2. The `manual_extraction_items` entity-staff **positive** case self-skipped locally (§4.1); production
   data makes it runnable.
3. The full unit suite did not finish in this session (§4.3).
4. `waitlist` POST is intentionally unauthenticated (a public waitlist signup); this preserves the legacy
   behaviour but is a deliberate, documented public write path.
5. Beta self-signup: when Supabase requires e-mail confirmation, `signUp()` returns no session and the
   redemption call cannot be authenticated, so the code is not marked used at that moment. The account is
   still created and the beta gate is decided server-side; the code can be redeemed once a session exists
   (or an admin can provision from the existing admin endpoints). This is documented in the code.
6. **Residual closure:** the inert realtime `staff_workload` registration
   (`frontend/src/lib/realtime/manager.js:243-251`) could not be exercised end-to-end here (that needs a
   live Supabase Realtime connection). Its inertness follows directly from *RLS enabled + zero policies*
   — Postgres change-feed rows are filtered by RLS for `anon`/`authenticated` — and is inspectable at the
   cited lines; it is recorded rather than fixed because the authorisation forbids creating a policy to
   preserve legacy behaviour and forbids scope beyond `staff_workload`.
7. **Local vs production RLS state:** the local cluster enables RLS on all 135 of its public tables, so the
   pre-state had to be reproduced by disabling RLS on the 44 tables in the disposable clone (§2). On
   production the residual is genuinely RLS-**off** today (packages `08`/`09`), which is the state the PRE
   column of §2.5 reproduces; the verifier should re-confirm the production pre-state with a read-only
   inspection if they want it from the live system rather than from the recorded packages.

---

## 8. Exact file manifest

### Added

| File | Purpose |
|---|---|
| `supabase/migrations/20261028000000_ct_final_03_rls_security_remediation.sql` | the 43-table artefact (RLS enablement only) |
| `supabase/migrations/20261029000000_ct_final_03_staff_workload_rls.sql` | **added in the residual-closure pass**: RLS enablement only on `staff_workload` (fail-closed, zero policies) — §1.5 |
| `backend/routes/beta_access.py` | self-service beta endpoints (`GET /api/beta/me`, `POST /api/beta/redeem`) |
| `admin/src/services/adminApi.js` | shared authenticated admin→backend fetch helper |
| `backend/tests/integration/test_final_03_rls_remediation_live.py` | the focused static + live RLS suite |
| `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/10-final-03-rls-remediation-implementation-and-verification-20261002.md` | this manifest |

### Modified

| File | Change |
|---|---|
| `backend/routes/waitlist.py` | both `pass` stubs implemented (public POST signup; `require_admin()` GET listing) |
| `backend/routes/__init__.py` | export `beta_access` |
| `backend/main.py` | import + `include_router(beta_access.router)` |
| `admin/src/pages/admin/Settings.js` | 3 `system_settings` sites resolved (1 read + 1 write re-pointed to `/api/v3/settings/*`; the default-seeding insert deleted) |
| `admin/src/pages/admin/BetaManagement.js` | 3 sites re-pointed (waitlist, email logs, beta codes) |
| `admin/src/pages/admin/WorkHub.jsx` | 2 dead sites deleted (`notifications`, `staff_workload`); **residual-closure pass:** the explanatory comment for the `staff_workload` deletion updated to state that the table is now RLS-enabled (no functional change; the deletion stands) |
| `backend/tests/integration/test_final_03_rls_remediation_live.py` | **residual-closure pass:** +6 static assertions (File (2) ordering, target-set/disjointness, statement safety, single-DDL, rollback/non-scope/governance) and +4 live tests (RLS + zero policies, `anon`/`authenticated` denial, the row-level enforcement proof, `service_role` preservation); the 43-table residual assertion renamed to state it is not in that artefact; `staff_workload` added to the data-preservation fingerprint |
| `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/10-…md` | **residual-closure pass:** this document (§1.5, §2.5, §2.6, §4, §5, §7, §8, §9 updated) |
| `admin/src/services/reviewService.js` | 4 unauthorised audit INSERTs deleted; audit read re-pointed |
| `frontend/src/BetaSignup.jsx` | 5 sites resolved (validate re-pointed; pre-check deleted; 3 writes consolidated into `POST /api/beta/redeem`) |
| `frontend/src/BetaLogin.jsx` | 2 beta-status reads re-pointed to `GET /api/beta/me` |

**Not touched:** `backend/auth.py`, `backend/database.py`, the 43-table artefact
`20261028000000_ct_final_03_rls_security_remediation.sql` (**byte-for-byte unchanged**), any other existing
migration, any `.env`, any production configuration, `frontend/src/components/chat/*`,
`frontend/src/lib/realtime/*` (the inert `staff_workload` registration is left exactly as it was),
`admin/src/App.js` (no route removed), `emission_factors`.

---

## 9. Statement of completion

Implementation and local verification are complete, including the residual closure that this pass was
authorised to make. The authorisation's hard stop is respected: nothing was applied to production, nothing
was deployed, no secrets were configured, P5/P6 were not executed, and nothing was committed or pushed. The
switch from "accept-and-gate the residual" to "enable RLS on `staff_workload`" was implemented as a
**new, additive** migration so the accepted artefact did not change — and the residual's before/after
enforcement is proven against a real row, not an empty table. This document is a Cline implementation
report — it is **not** independent verification.

**`FINAL-03 RLS SECURITY REMEDIATION — SINGLE RESIDUAL CLOSED — READY FOR INDEPENDENT VERIFICATION`**
