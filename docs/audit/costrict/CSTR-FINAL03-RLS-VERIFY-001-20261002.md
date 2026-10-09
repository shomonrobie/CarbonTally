# CSTR-FINAL03-RLS-VERIFY-001 — FINAL-03 RLS Security Remediation: Independent Verification

## 1. Task ID

**CSTR-FINAL03-RLS-VERIFY-001** — independent verification of the FINAL-03 RLS security remediation (Migration 1 + Migration 2, combined).

## 2. Verification date

2026-10-02

## 3. Investigator

**CoStrict** — independent verifier. **Not** the implementation agent. This verification was performed read-only; no implementation artefact was created, edited, committed, pushed, deployed or applied to any non-disposable environment.

## 4. Scope

### Verified (combined intended remediation)

| Artefact | File | Size | Statement executed |
|---|---|---|---|
| Migration 1 (43 tables) | `supabase/migrations/20261028000000_ct_final_03_rls_security_remediation.sql` | 312 lines | `ALTER TABLE public.<t> ENABLE ROW LEVEL SECURITY` (single `EXECUTE format(…)`) |
| Migration 2 (1 table) | `supabase/migrations/20261029000000_ct_final_03_staff_workload_rls.sql` | 222 lines | `ALTER TABLE public.<t> ENABLE ROW LEVEL SECURITY` (single `EXECUTE format(…)`) |

Covered: migration governance (presence, ordering, additivity, disjointness, no historical edits); the exact 44-table target set; per-table RLS/FORCE/policy state; policy preservation for the two enable-only tables; role-by-role authorisation behaviour (anon / authenticated / service_role); data-preservation; browser/API reachability of the 23 identified call sites; the `staff_workload` residual closure; the Prisma contradiction; idempotence; wrong-target safety; and the regression test surface.

### Explicitly out of scope (per the authorisation)

- **Production was not contacted** (no Supabase production connection, no Render, no Vercel, no deploy, no migration application to production).
- No application code, migration, RLS state, policy, grant/revoke, table, or data was modified; no commit or push.
- No remediation was implemented; the FINAL-03 RLS decision was not changed; FINAL-03 was not closed; P2/P5/P6 was not started.

## 5. Environment(s)

| Environment | Role in verification | Contacted |
|---|---|---|
| `postgresql://postgres:postgres@127.0.0.1:54426/ct_f03_rls_verify` | Primary disposable target — full CarbonTally schema (135 public tables), the 44-table post-remediation state | Yes (local) |
| `postgresql://…/ct_f03_sw_verify` | Secondary disposable target for the `staff_workload` residual | Yes (local) |
| `postgresql://…/ct_local_93d5cdd` | Source/disposable baseline (schema reference) | Yes (local) |
| `ct_cstr_wt_20261002b` (created by this verification) | Empty scratch DB for the wrong-target guards | Yes (local, disposable) |
| `postgres` | catalogue queries (DB inventory) | Yes (local) |
| Production Supabase / Render / Vercel | **not contacted** | **No** |

The local cluster is the repository's isolated disposable environment (`backend/.env`: *"ISOLATED LOCAL ENV for 93d5cdd … Disposable database on the local cluster; no production endpoint is referenced"*). **Important environment property (a known constraint, not a discrepancy): the local cluster enables RLS on all 135 of its public tables**, so enablement is a no-op locally (see §15 and §17).

## 6. Migration verification (governance)

| Check | Result | Evidence |
|---|---|---|
| Migration 1 exists | **PASS** | 312-line file present |
| Migration 2 exists | **PASS** | 222-line file present |
| Migration 2 sorts after Migration 1 | **PASS** | `ls` ordering: `…20261028000000…` then `…20261029000000…`; asserted by `test_residual_migration_sorts_immediately_after_the_artefact` |
| Migration 2 targets only `public.staff_workload` | **PASS** | `fail_closed text[] := ARRAY['staff_workload']` (M2:104); arithmetic guard requires exactly 1 target (M2:117-120) |
| Migration 2 is additive & disjoint from Migration 1 | **PASS** | `staff_workload ∉ group_a ∪ group_b` (M1:96-150); asserted by `test_residual_target_set_is_exactly_the_one_table` (`… == [RESIDUAL_TABLE]` and `not set(residual) & (set(group_a)|set(group_b))`) |
| No historical migration modified | **PASS** | `git status --porcelain -- supabase/migrations` shows **only** new untracked files (`?? 20261025…, 20261026…, 20261027…, 20261028…, 20261029…`); **no `M` (modified) entry** — every pre-existing migration is unchanged |
| Migration 2 contains no data mutation | **PASS** | forbidden-token scan (`TRUNCATE, DELETE FROM, DROP …, INSERT INTO, UPDATE public., CREATE/ALTER POLICY, GRANT, REVOKE, ALTER DEFAULT PRIVILEGES, DISABLE/FORCE ROW LEVEL SECURITY`) — `test_residual_migration_contains_no_data_or_destructive_statement` passes; manual read confirms |
| Migration 2 contains no GRANT / REVOKE / policy create+drop / FORCE RLS / function / schema / index / constraint / table create+drop | **PASS** | the only `EXECUTE` line is the enablement (M2:179); `test_residual_only_executed_ddl_is_enablement` asserts `executed == ["EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);"]` |
| Migration 1 same statement-safety properties | **PASS** | only `EXECUTE` = enablement (M1:258); `test_the_only_executed_ddl_is_enablement`, `test_migration_contains_no_data_or_destructive_statement` pass |
| Repo rule "schema changes have a migration" | **PASS** | both changes are delivered as migrations (`AGENTS.md` §66 cited in M2 header:13-18) |

**Governance limitation:** Migration 1's *byte-level* immutability cannot be proven from VCS history because both migrations are **uncommitted** (untracked) working-tree files — there is no committed baseline to diff against. Additivity/disjointness is instead verified **structurally** (M2 touches exactly `staff_workload`; `staff_workload` is in neither M1 group; M1's internal arithmetic is 41/2/4 and unchanged) and by the focused test suite. No evidence of an edit to M1 was found.

## 7. Exact 44-table target verification

Reconstructed from the migration files (not from Cline's report).

- **Group A — fail-closed, 0 policies (41):** `system_settings`, `staff_roles`, `password_reset_tokens`, `beta_access_codes`, `beta_users`, `email_logs`, `notifications`, `review_audit_trail`, `waitlist`, `audit_trail`, `consultant_billing`, `consultant_tasks`, `login_history`, `conversation_activity_log`, `message_activity_log`, `report_comments`, `report_versions`, `staff_activity_log`, `typing_status`, `user_activity_log`, `user_presence`, `verification_logs`, `approval_decisions`, `approval_requests`, `dashboard_metrics`, `notification_delivery`, `processing_assignments`, `processing_audit_trail`, `processing_steps`, `processing_time_log`, `qc_checklists`, `qc_checks`, `qc_errors`, `queue_settings`, `reassignment_history`, `review_assignment_history`, `sla_compliance`, `staff_daily_performance`, `staff_performance`, `team_performance`, `verification_activity_log`.
  - M1 arithmetic guard (M1:178-185) requires `len(group_a)=41`, `len(group_b)=2`, `len(retained_policies)=4`; `test_approved_set_arithmetic` asserts 41/2/4.
- **Group B — enable-only, policies preserved (2):** `conversation_participants`, `manual_extraction_items`.
- **Migration 2 target (1):** `staff_workload`.
- **Total = 44.** `test_class_a_tables_are_not_touched` confirms `emission_factors`, `business_hours`, `sla_definitions` are **not** in the set (Class A, deliberately excluded).

All 44 present in `ct_f03_rls_verify` (**44/44**).

## 8. RLS state (per target)

Measured in `ct_f03_rls_verify` (migration-produced schema):

| Group | n | present | RLS enabled | FORCE RLS | policies |
|---|---|---|---|---|---|
| A | 41 | 41/41 | **41/41** | 0 | **0 per table** |
| B | 2 | 2/2 | 2/2 | 0 | `conversation_participants`=3, `manual_extraction_items`=1 |
| M2 | 1 | 1/1 | 1/1 | 0 | `staff_workload`=**0** |

`anon`/`authenticated` do **not** hold `BYPASSRLS`; `service_role` does. Total policies in `public` = **218**. Asserted live by `test_rls_enabled_on_every_approved_table`, `test_zero_policies_on_the_fail_closed_group`, `test_force_row_level_security_untouched`, `test_anon_and_authenticated_do_not_bypass_rls`.

## 9. Policy state

- **Fail-closed group:** exactly **0** policies on each of the 41 (verified per-table, §8).
- **Retained family (4), definitions read directly** (not merely counted):

| Policy | Table | Cmd | Roles | USING | WITH CHECK |
|---|---|---|---|---|---|
| `conversation_participants_entity_select` | conversation_participants | SELECT | `{authenticated}` | `can_view_entity_conversation(conversation_id)` | — |
| `conversation_participants_select` | conversation_participants | SELECT | `{authenticated}` | `can_view_conversation_participants(conversation_id)` | — |
| `conversation_participants_update_own` | conversation_participants | UPDATE | `{authenticated}` | `is_conversation_participant(conversation_id)` | `user_id = auth.uid()` |
| `manual_extraction_items_entity_select` | manual_extraction_items | SELECT | `{authenticated}` | `(work_item_effective_entity(id) IS NOT NULL) AND is_entity_member(work_item_effective_entity(id))` | — |

- No policy grants `anon`; none is a bare `USING (true)`. Asserted by `test_retained_policy_family_is_intact`, `test_no_broad_authenticated_policy_on_any_approved_table`, `test_manual_extraction_items_policy_is_the_only_one`.
- **The migration creates/drops no policy.** Live: re-running both migrations (idempotence, §15) produced `policies 218 → 218 (delta 0)` per-file.

## 10. Authorization test results

Executed **independently** (my own probes, not only the implementation's tests), via `SET LOCAL ROLE` + `request.jwt.claims`, all read-only or inside a rolled-back transaction, on `ct_f03_rls_verify`.

| Probe | Result |
|---|---|
| `anon` SELECT `system_settings` | `ERROR: permission denied for table system_settings` (contained by grants — no `anon` privilege) |
| `anon` SELECT `staff_workload` | `ERROR: permission denied for table staff_workload` |
| `anon` INSERT `waitlist` | `ERROR: permission denied for table waitlist` |
| `authenticated` SELECT `system_settings` / `staff_roles` / `password_reset_tokens` / `beta_access_codes` / `waitlist` / `staff_workload` | **0 rows** each (RLS fail-closed) |
| `authenticated` INSERT `beta_users` | `ERROR: new row violates row-level security policy for table "beta_users"` |
| `authenticated` UPDATE `system_settings` | `UPDATE 0` |
| `authenticated` DELETE `audit_trail` | `DELETE 0` |
| `service_role` SELECT `system_settings` etc. | allowed (BYPASSRLS) |

`staff_workload` **row-level proof** (a real row seeded as owner inside a transaction that was **rolled back**):
`authenticated` → SELECT `0`, UPDATE `0`, DELETE `0`, INSERT → `ERROR: new row violates row-level security policy for table "staff_workload"`; `service_role` → SELECT `1`, UPDATE `1`; owner after probes → `1` row, `workload_score=7` (unmutated); after `ROLLBACK` → 0 rows.
This reproduces the implementation's §2.5 claim with independent evidence, and matches the focused suite's `test_residual_table_enforces_denial_against_a_real_row`.

## 11. Data-preservation results

- **No DML in either migration** (static scan + tests; §6) — the migrations cannot delete/alter rows.
- **Disposable fingerprint unchanged** across the idempotence run on `ct_f03_rls_verify`: `policies 218`; `organizations=25`, `users=658`, `emission_factors=0`, `staff_workload=0` — identical before and after (§15).
- Live suite `test_no_data_was_mutated_by_the_verification` passes (retained-row fingerprint `system_settings=1`, `manual_extraction_items=1`, + `organizations`, `users`, `emission_factors`, `staff_workload` unchanged).
- **Production identity/emission-factor preservation — NOT independently demonstrable locally (evidence gap, §17).** The two retained owner/test organisations (`0c0aa358-eaed-492c-9a8b-f7fabe6531ac`, `8ae45e55-afa9-42f1-b4f9-f0225f9b98cd` — *Babui Technologies UK Limited*, *Faria Green Company UK LTD*) and the `emission_factors = 7049` library recorded in the preservation baseline (`docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/02-preservation-assessment-entities.txt:1-31`) are **present in no local database** (all databases searched). They exist only on production, which was not contacted. Their preservation is therefore supported **by mechanism** (the migration contains no DML), not by a local row-level check.

## 12. Browser / API reachability results

| Check | Result |
|---|---|
| `admin/src` direct `.from('<protected table>')` for the 9 protected tables | **0 occurrences** — all previously-identified admin direct accesses are removed/re-pointed |
| `frontend/src` direct `.from('<protected table>')` | Only 3 `conversation_participants` reads remain (`frontend/src/lib/realtime/manager.js:397-399`, `frontend/src/components/chat/ChatWindow.jsx:108-110`, `frontend/src/components/chat/ChatWidget.jsx:40-42`) — the intended "UNCHANGED" sites covered by the retained policies; plus a comment in `frontend/src/context/RealtimeContext.jsx:275-277` |
| `staff_workload` direct browser read | **removed** — `admin/src/pages/admin/WorkHub.jsx:247-256` sets `const staffWorkload = []` with an explanatory comment; no `from('staff_workload')` anywhere in `admin/src`/`frontend/src` |
| `staff_workload` realtime subscription | present but **inert under RLS**: `frontend/src/lib/realtime/manager.js:243-251` (`event: 'UPDATE'`, filter `staff_id=eq.<id>`), constant `Types.STAFF_WORKLOAD='staff_workload'` (`frontend/src/lib/realtime/types.js:60`); RLS on + 0 policies ⇒ no row is delivered to `anon`/`authenticated` |
| New/completed receiving endpoints | **present**: `backend/routes/beta_access.py` (`GET /api/beta/me`, `POST /api/beta/redeem`), `backend/routes/waitlist.py` (`POST /` public server-side write, `GET /` `require_admin()`), `admin/src/services/adminApi.js` |
| Residual (pre-existing, not FINAL-03) | `admin/src/components/StaffReviewQueue.jsx:96-99` still calls `GET /api/admin/reviews/staff/workload`, which is **not defined** in `backend/routes/admin/reviews.py` (prefix `/api/admin/reviews`; its routes are `/queue`, `/{review_id}`, `…/assign`, `…/complete`, `…/reject`, `/my-queue`, `/queue/priority`, `/queue/reorder`, `/queue/stats/detailed`, `/queue/escalate`, `/queue/sla-monitor`) → **404**. It never reaches any table; recorded as a residual (see §18). |

## 13. `staff_workload` verification

| Property | Result |
|---|---|
| Table exists | Yes (created by `00000000000000_init_schema.sql:1253-1266`) |
| RLS enabled | **Yes** (`relrowsecurity = true`) |
| FORCE RLS | **Off** |
| Policies | **0** |
| `anon` table privilege | **None** (`has_table_privilege('anon',…,'SELECT') = f`; probe → permission denied) |
| `authenticated` can retrieve rows | **No** (SELECT `0`; row-level proof with a real row: SELECT/UPDATE/DELETE `0`, INSERT refused) |
| service-role / backend access preserved | **Yes** (`service_role` SELECT `1`, UPDATE `1` on the seeded row) |
| Application data changed by the migration | **None** (0 rows before/after; no DML in the file) |

Backend references (from `CSTR-FT03-STAFF-WORKLOAD-001-…md`): broken `assigned_reviews`/`in_progress_reviews`/`last_updated` reads/writes; missing `(staff_id,date)` unique constraint (so the `on_conflict='staff_id,date'` upsert cannot work); UI-orphaned workload endpoints; `AdminAssignment` path discarding `workload_score`. **Effect on the RLS verdict: none** — the table is fail-closed with no browser path, carries 0 rows, and the backend (service_role) is unaffected. These are pre-existing application defects, outside this change-set, and were **not** repaired.

## 14. Prisma contradiction verification

**Reproduced and confirmed (not reconciled, not modified).** `prisma/schema.prisma:2971-2987` declares `@@unique([staff_id, date])` and `@@index([staff_id, date], map: "idx_staff_workload_staff_date")`, plus column defaults (`assigned_tasks @default(0)` etc.). The migration-produced schema contains **neither**: in both `ct_local_93d5cdd` and `ct_f03_rls_verify`, `staff_workload` has only the primary-key index `staff_workload_pkey` and **no** unique constraint. No `src/`/`shared/` code references Prisma. **Effect on the RLS remediation: none** — the contradiction concerns constraints/indexes, not RLS or security, and Prisma is not a runtime path.

## 15. Idempotence and wrong-target results

**Idempotence** (both migrations re-applied to the disposable `ct_f03_rls_verify`):

```
M1 NOTICE: approved=43, present=43, absent_skipped=0, enabled_before=43, enabled_after=43,
           statements_run=43, policies_before=218, policies_after=218 (delta 0), …
M2 NOTICE: targets=1, rls_enabled_before=t, rls_enabled_after=t, policies_on_target=0,
           policies_before=218, policies_after=218 (delta 0), force_rls=off …
M2 re-run: identical NOTICE (no-op)
```

- No duplicate policy; policy count 218 → 218; no error from already-enabled RLS; fingerprint unchanged (§11). **PASS.**
- Note (§5): because the local cluster pre-enables RLS on all 135 public tables, `enabled_before=43` here — the enablement is a no-op locally and the *disabled → enabled transition* is not observable in this environment (see §17).

**Wrong-target safety** (empty scratch DB `ct_cstr_wt_20261002b`, `-v ON_ERROR_STOP=1`):

```
M1 → ERROR: CT-FINAL-03 precondition failed: conversation_participants / manual_extraction_items
           must exist (retained-data target check)
M2 → ERROR: CT-FINAL-03 residual precondition failed: public.staff_workload is absent —
           refusing to no-op on a security control (wrong target?)
tables left in scratch DB public schema: 0
```

Both guards **fail loudly** and leave the database **unchanged** (0 tables). **PASS.**

## 16. Regression-test results

### Focused FINAL-03 suite — `backend/tests/integration/test_final_03_rls_remediation_live.py`

| Invocation | Result |
|---|---|
| `FINAL_03_RLS_TEST_DSN=postgresql://postgres:postgres@127.0.0.1:54426/ct_f03_rls_verify python -m pytest tests/integration/test_final_03_rls_remediation_live.py -q` | **30 passed, 1 skipped** in 0.57s |
| same file, **no DSN** (static half only) | **12 passed, 19 skipped** |

Skip reason: `test_manual_extraction_items_retained_rows_and_entity_isolation:791` — *"no entity-allocated manual_extraction_batch here — positive case not constructible"* (target data condition, not a failure).

### Wider unit suite — `python -m pytest tests/unit -o addopts="" -q --tb=no`

**9 failed, 4765 passed, 8 skipped** (412s).

Classification (**PRE-EXISTING** vs **INTRODUCED BY THIS REMEDIATION**):

| # | Failing test | Class | Why |
|---|---|---|---|
| 1 | `tests/unit/backup/test_jobs.py::TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain` | **INTRODUCED (non-security)** | Asserts `names[-1] == 20261027000000_ct_backup_02_…`; FINAL-03's `…20261028000000…`/`…20261029000000…` are now last. Without the two FINAL-03 files the test passes. |
| 2 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | **PRE-EXISTING** | Asserts `len(names) == 71`; the repo holds **98** migration files (p16/p17/ct02/backup migrations already present before FINAL-03). Fails with or without FINAL-03. |
| 3 | `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | **PRE-EXISTING** | Requires the only migrations after I1 to be a fixed small list; many later migrations predate FINAL-03. |
| 4 | `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | **PRE-EXISTING** | Asserts `names[-1] == "20261007000000_…"`; already superseded by 2026-10-08+ migrations before FINAL-03. |
| 5 | `tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | **PRE-EXISTING** | Requires every migration with stamp > P16 baseline to be in the P17 set; ct02/step2/backup (`20261021…`–`20261027…`) already violate this before FINAL-03. |
| 6–8 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice` / `…_missing_fields_leave_unresolved` / `…_no_fabrication_on_garbage` | **PRE-EXISTING / unrelated** | Extraction-suggestion engine behaviour; no relation to migrations or RLS. |
| 9 | `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` | **PRE-EXISTING / unrelated** | Asserts `verification_delivered is False` but the local env has email delivery configured (`body['verification_delivered'] == True`); environment-dependent, and `api/v3_discovery.py` is a *separate* working-tree modification, not part of FINAL-03. |

No failing test asserts a FINAL-03 property. **No FINAL-03-relevant test fails.** No failures were repaired.

## 17. Limitations

1. **RLS disabled → enabled transition not observable locally.** The local cluster enables RLS on **all 135** public tables (no event trigger — a setup default), so migration enablement is a no-op here and `enabled_before=43`. The remediation's *effect* is therefore established by (a) static analysis — the only executable DDL is `ALTER TABLE … ENABLE ROW LEVEL SECURITY` on the exact 41/2/1 targets, and (b) the post-state match + idempotence, **not** by observing a live flip from `rls_off`. The implementation report states the pre-state was reproduced on a clone by deliberately disabling RLS; this verifier **did not** disable RLS (governance boundary) and so does not independently attest the off→on flip.
2. **PostgREST HTTP path not exercised.** `backend/.env` points `SUPABASE_URL` at an unroutable host, so no HTTP PostgREST call was possible; authorisation was verified at the DB layer (the same role+RLS mechanism PostgREST uses).
3. **Production not contacted** (mandated). Consequently the specific production identities and the `emission_factors=7049` library are verified only by *mechanism* (no DML), not by local row comparison.
4. **Migration 1 immutability not byte-provable via VCS** (both migrations are uncommitted/untracked); verified structurally (§6).
5. **Wrong-target tested only against an empty schema** (the deterministic, safe case). The functional-absence guard for Migration 2 cannot be tested on a real CarbonTally schema without dropping the table (forbidden).
6. **Full integration suite not run** (some tests require external services; out of the disposable scope). Focused + static + full unit suites were run.
7. **Environment-driven failure** (#9 above) is expected to differ across environments.

## 18. Residual findings

| ID | Finding | Material to the RLS remediation? | Owner action required |
|---|---|---|---|
| **R1** | **One introduced test regression**: `tests/unit/backup/test_jobs.py::test_the_backup_migrations_are_the_newest_in_the_chain` fails because FINAL-03 adds newer migrations. A stale hard-coded "newest migration" assertion (the same anti-pattern explicitly avoided in `tests/unit/api/test_storage_management_step2.py:863-875`). | **No** — non-security, no functional effect; does not affect migration correctness, RLS state, policies, or scope. | Yes (test-expectation update at the FINAL-03 gate) — **not** performed here (read-only boundary). |
| **R2** | 8 pre-existing/unrelated unit failures (rows 2–9, §16). | No | Not part of FINAL-03. |
| **R3** | Inert realtime registration for `staff_workload` (`frontend/src/lib/realtime/manager.js:243-251`) left in place by design. | No | Documented; optional cleanup later. |
| **R4** | Stale endpoint reference `GET /api/admin/reviews/staff/workload` (`admin/src/components/StaffReviewQueue.jsx:97`) has **no** matching route (404) — pre-existing, unrelated to FINAL-03; does not reach any table. | No | Not part of FINAL-03; noted for the owner. |
| **R5** | Prisma model declares a `(staff_id, date)` unique constraint + `idx_staff_workload_staff_date` that the migration-produced schema does not create. | No | Outside FINAL-03. |
| **R6** | Production identity / emission-factor preservation verified by mechanism only (§11). | No (mechanism guarantee) | None; production is out of scope. |

## 19. Final verdict

All security acceptance criteria are established by independent evidence:

- **A. Migration integrity** — both migrations present, correctly ordered, additive, disjoint, statement-safe; no historical migration modified. ✅
- **B. Exact scope** — the intended **44-table** set is implemented exactly (41 fail-closed + 2 policy-preserving + `staff_workload`); Class A untouched. ✅
- **C. Security posture** — the fail-closed tables are genuinely inaccessible to `anon` and `authenticated` (0 rows / refused writes, independently reproduced); the backend `service_role` is unaffected. ✅
- **D. Policy preservation** — `conversation_participants` (3) and `manual_extraction_items` (1) retain their exact intended policies, definitions verified; no policy created/dropped/altered (218→218). ✅
- **E. `staff_workload`** — RLS enabled, 0 policies, fail-closed, `anon` privilege-none, `authenticated` no rows, service-role compatible, no browser path exposing data. ✅
- **F. No unintended mutation** — no DML in either migration; disposable fingerprint and live retained-row assertions unchanged. ✅
- **G. Regression** — the FINAL-03 focused suite passes (30 passed / 1 skipped live; 12 passed / 19 skipped static-only); the wider unit suite's 9 failures are honestly classified: **8 pre-existing/unrelated** and **1 introduced, non-security, stale "newest-migration" assertion (R1)**. No FINAL-03-relevant test fails. ✅ (with R1 recorded)
- **H. Governance** — no production/deploy/commit action occurred. ✅

The single introduced failure (R1) is a stale test expectation in an unrelated suite, with no effect on the security remediation's correctness, scope or enforcement; it is recorded as a residual for resolution at the gate. On the evidence, the security remediation itself is verified.

**FINAL-03 RLS SECURITY REMEDIATION — INDEPENDENTLY VERIFIED — READY FOR FINAL-03 GATE REVIEW**

> If the PO's reading of acceptance criterion **G** requires **zero** introduced test failures, then residual **R1** alone would place the change-set at *NOT VERIFIED — MATERIAL FINDINGS REQUIRE RESOLUTION* pending a test-expectation update; the RLS remediation itself is unaffected either way. This verifier's materiality judgement is that R1 is **not** material to the RLS remediation.
