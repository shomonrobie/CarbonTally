# CT-FINAL03-P3-SUPABASE-001 — Apply Frozen FINAL-03 Migrations to Production Supabase

**Task ID:** `CT-FINAL03-P3-SUPABASE-001`
**Date:** 2026-10-03 (local, UTC+06) · **Executed by:** Cline (implementation agent)
**Scope:** Production Supabase schema migration + verification **only**. Database migration only — no application deployment.
**Report line:** `CT-FINAL03-P3-SUPABASE-001 — IMPLEMENTED — PRODUCTION SUPABASE MIGRATIONS APPLIED AND DATA/RLS PRESERVATION VERIFIED — READY FOR INDEPENDENT VERIFICATION`

> **Read this first (§12 note + §16 D-1).** All 27 frozen migrations applied cleanly and **all retained
> production data is preserved**. The recorded `emission_factors` **whole-row** fingerprint necessarily
> *changed* because two of the authorised migrations **add four columns** to that table (row text includes
> new columns). The 7,049 factor rows are **byte-identical on every one of the 13 pre-migration columns**
> (proven below: identical sorted sha256, `diff = 0`). The count is exactly 7,049 before and after.

---

## 1. Task

Apply the authorised, frozen FINAL-03 migration chain to the existing production Supabase project
`pvwiojoyaqywtydzcpbg`, in place, additively, without destroying any retained production data, and verify
schema / RLS / data / migration-history preservation afterwards.

**Explicitly out of scope and NOT performed:** Render deploy, Vercel deploy, production worker start-up,
production environment/secret changes, email or billing configuration, live application/browser
acceptance, `db reset`, database drop/recreate, truncation, local/demo import, arbitrary cleanup SQL.

**No application worker was started by this task** (see §19 and discrepancy **D-3** — a *pre-existing,
external* production writer was observed in the migration window).

---

## 2. Frozen release (authorised input)

| Field | Value |
| --- | --- |
| Release SHA | `375a48dc1b9e9cfd74090bbf747554ae997acb59` |
| Branch | `p8-release-reconciled` |
| Remote / remote branch | `github` / `github/p8-release-reconciled` |
| Independent verification | `CSTR-FINAL03-P2-RECON-VERIFY-001` — RELEASE SHA AND AUTHORIZED SCOPE CONFIRMED |
| Migration files in release | 98 (`supabase/migrations/*.sql`), all verified present at this SHA |

**Migration-file integrity (all 27 applied files).** For every file, the working-tree sha256 equals the
sha256 of the same blob at the frozen SHA (`git show 375a48dc…:supabase/migrations/<file>`), i.e. the
files applied were the frozen artefacts and were not modified. The two FINAL-03 RLS files match the
independently verified hashes exactly:

| Migration | SHA256 |
| --- | --- |
| `20261028000000_ct_final_03_rls_security_remediation.sql` | `ca461c9c5be712b8c5bfaaa8200e2a3be83c5fb55990c3e118446b86904ecb15` |
| `20261029000000_ct_final_03_staff_workload_rls.sql` | `0775fa68388a5e697965b7500284a653df4a96336218ea5b2abbb2b98f7b1cb3` |

Representative digests of the other applied files (worktree = frozen-HEAD, all `MATCH`):
`20261025000000 = d24b08fb62a95dd2…`, `20261026000000 = b75da97887a0b13e…`,
`20261027000000 = 500202973db24f77…`; full 27-file list in **Appendix A**.

---

## 3. Production Supabase target identity (secrets redacted)

| Field | Value |
| --- | --- |
| Project ref | `pvwiojoyaqywtydzcpbg` (CarbonTally) |
| Organisation ref | `pfurlzwxdtvyljnahlnx` |
| Region / engine | `eu-west-2` · PostgreSQL **17.6** (`aarch64-unknown-linux-gnu`) |
| Endpoint used | Supavisor pooler `aws-1-eu-west-2.pooler.supabase.com:5432` (**session** mode) |
| Database / role | `postgres` / `postgres.<project-ref>` |
| Credential source | `SUPABASE_LIVE_POSTGRES_DATABASE_URL` from `backend/.env` |
| Credential handling | Parsed in memory into `PG*` env / CLI argument; **never printed, logged or written to any artefact**. Passwords, tokens, JWTs, service-role keys and complete credential-bearing DSNs are redacted in this report. |

**Read-only enforcement proof.** Every baseline/verification psql session began with
`SET default_transaction_read_only = on` (the pooler does not forward `PGOPTIONS`, so the setting was
applied in-session and re-verified: `enforced_ro = on`). Enforcement was **proved**, not assumed:

```
create table public.__p3_readonly_probe(x int);
ERROR:  cannot execute CREATE TABLE in a read-only transaction
```

Toolchain: `supabase` CLI **2.115.0** (`db push`), `psql` **18.6**, `pg_dump`/`pg_restore` **18.6**.

**Wrong-target guard.** The production pre-state matched the established FINAL-03 baseline exactly
(§4/§5), including the two retained organisations and the 71-applied/27-pending migration delta — so the
target was the intended project, not a local or demo database.

---

## 4. Pre-migration schema baseline (measured 2026-10-03 04:22–04:23 local / 22:22–22:23 UTC)

| Metric | Pre-migration (measured) | Established baseline (FINAL-03 evidence pack) | Match |
| --- | --- | --- | --- |
| `public` base tables | **134** | 134 | ✅ |
| RLS-enabled tables | **87** | 87 | ✅ |
| RLS-disabled tables | **47** | 47 | ✅ |
| `public` policies | **198** | 198 | ✅ |
| `public` functions | 55 | — | recorded |
| `public` triggers (non-internal) | 81 | — | recorded |
| `public` indexes | 315 | — | recorded |
| Applied migrations | **71** | 71 | ✅ |
| Latest applied migration | **`20260927000000`** | `20260927000000` | ✅ |
| `backup*` tables | **none** | none | ✅ |
| RLS-disabled set | the recorded 47-table list (incl. `system_settings`, `staff_roles`, `emission_factors`, `staff_workload`, `conversation_participants`, `manual_extraction_items`, …) | same | ✅ |
| Grants (public schema) | `authenticated` 477 · `service_role` 938 · `postgres` 938 · `anon` none | 477/938/938 | ✅ |
| Policies referencing `anon`/`public` | **0** | — | recorded |
| `anon`/`authenticated` `BYPASSRLS` | `false` / `false` (so RLS enablement is a real control) | — | ✅ |
| `service_role`/`postgres` `BYPASSRLS` | `true` / `true` (documented backend trust model) | — | ✅ |

**FINAL-03 RLS pre-conditions (all satisfied, so the migration's own guards could not trip):**

* Group A (41 tables): **zero** policies on every one (no "unrecognised grant path").
* Group B: `conversation_participants` = 3 policies, `manual_extraction_items` = 1 policy — exactly the
  4 retained policy names the migration requires
  (`conversation_participants_entity_select`, `conversation_participants_select`,
  `conversation_participants_update_own`, `manual_extraction_items_entity_select`).
* Both Group B tables exist; `staff_workload` exists with 0 policies; Class A
  (`emission_factors`, `business_hours`, `sla_definitions`) present and untouched.

---

## 5. Pre-migration data preservation baseline (measured, read-only)

| Preservation metric | Pre-migration (measured) | Established baseline | Match |
| --- | --- | --- | --- |
| `emission_factors` rows | **7,049** | 7,049 | ✅ |
| `emission_factors` whole-row fingerprint `md5(string_agg(md5(f::text),'' order by md5(f::text)))` | **`021087a43be5db7469ec6d16ae542235`** | `021087a43be5db7469ec6d16ae542235` | ✅ |
| `organizations` rows | **2** | 2 | ✅ |
| — `0c0aa358-eaed-492c-9a8b-f7fabe6531ac` | Babui Technologies UK Limited · `is_active=t` · created 2026-09-17 07:24:56.588538+00 | identical | ✅ |
| — `8ae45e55-afa9-42f1-b4f9-f0225f9b98cd` | Faria Green Company UK LTD · `is_active=t` · created 2026-09-17 15:24:27.744541+00 | identical | ✅ |
| `auth.users` | **2** | 2 | ✅ |
| — `40b9f3f6-040d-4cc5-9bb1-82ae10115421` | `sho***@gmail.com` · confirmed 2026-08-18 12:12:57.715426+00 · last sign-in 2026-09-26 13:45:03.745723+00 · not banned | identical | ✅ |
| — `ab7a9f50-8f16-4eb4-a229-40fa3a87c3e4` | `far***@gmail.com` · confirmed 2026-09-17 15:23:23.730471+00 · last sign-in 2026-09-24 05:15:52.152694+00 · not banned | identical | ✅ |
| `auth.sessions` / `auth.refresh_tokens` | 26 / 48 | 26 / 48 | ✅ |
| Demo-domain users (`@demo.carbontally.local`) | **0** | 0 | ✅ |
| `organization_members` | **2** | 2 | ✅ |
| — `02534fcc-87c5-45ea-8be8-17def8d9fcbe` | user `40b9f3f6…` @ org `0c0aa358…` · role=owner · active | identical | ✅ |
| — `61cd9d4d-aed3-4ca7-a2b4-798e89564206` | user `ab7a9f50…` @ org `8ae45e55…` · role=owner · active | identical | ✅ |
| Org-linked rows (total) | **101** | 101 | ✅ |
| — `evidence_line_items` | 74 | 74 | ✅ |
| — `document_processing_queue` | 11 | 11 | ✅ |
| — `organization_files` | 11 | 11 | ✅ |
| — `organization_members` | 2 | 2 | ✅ |
| — `manual_extraction_batches` | 2 | 2 | ✅ |
| — `conversations` | 1 | 1 | ✅ |
| — `messages` | 1 | 1 | ✅ |
| `storage.objects` in bucket `documents` (total objects) | **58** (58) | 58 | ✅ |
| `storage.buckets` `documents` row | `public=f` · `file_size_limit=2097152` | `public=f` · limit 2,097,152 | ✅ |

**Restore point taken immediately before the apply** (no platform backup/PITR is available — see **L-1**):
a local logical `pg_dump` (`--format=custom`) of the retained footprint (`organizations`,
`organization_members`, `evidence_line_items`, `document_processing_queue`, `organization_files`,
`manual_extraction_batches`, `conversations`, `messages`, `emission_factors`,
`supabase_migrations.schema_migrations`, `storage.buckets`):

* path (outside the repository, not part of the release): `/tmp/ct_p3_restore_point/retained_footprint_pre_p3.dump`
* size **389,139 bytes** · sha256 **`523f47126794eaee087c51cf65d2668df6731835c0172667b7a4d78c70fe1fcb`**
* created 2026-10-03 **04:22:31 +06** (= 2026-10-02 22:22:31 UTC), i.e. before the first migration was applied.

---

## 6. Migration list and order (the 27 applied files, canonical filename order)

| # | Migration | # | Migration |
| --- | --- | --- | --- |
| 1 | `20260928000000_p8_fs_activity_clarifications.sql` | 15 | `20261012000000_p17d_scope3_category_taxonomy.sql` |
| 2 | `20260929000000_p8_fs_activity_clarifications_fks.sql` | 16 | `20261013000000_p17h_estimation_and_assumption_records.sql` |
| 3 | `20260930000000_p8_fs_adjudication_lifecycle.sql` | 17 | `20261014000000_p17_10_product_contract_reporting_dimensions.sql` |
| 4 | `20260931000000_p8_fs_adjudication_context_lineage.sql` | 18 | `20261020000000_p17k_governed_capability_catalogue.sql` |
| 5 | `20261001000000_p8_i1_insight_persistence.sql` | 19 | `20261021000000_ct02_audit_ledger_hardening.sql` |
| 6 | `20261002000000_p8_i2_insight_authorization.sql` | 20 | `20261022000000_ct02_report_sharing.sql` |
| 7 | `20261003000000_p8_i4_insight_interactions.sql` | 21 | `20261023000000_ct02_scheduled_reporting.sql` |
| 8 | `20261005000000_p8_insight_discovery_aggregation_rate_limit.sql` | 22 | `20261024000000_ct_final_01_documents_bucket_size_limit.sql` |
| 9 | `20261006000000_p8_insight_temporal_comparison.sql` | 23 | `20261025000000_ct_step2_documents_bucket_size_alignment.sql` |
| 10 | `20261007000000_p8_insight_data_quality_reproducibility.sql` | 24 | `20261026000000_ct_backup_01_backup_jobs.sql` |
| 11 | `20261008000000_p16r5_result_reportability_lifecycle.sql` | 25 | `20261027000000_ct_backup_02_backup_sets_and_verification.sql` |
| 12 | `20261009000000_p16r7_calculation_request_idempotency.sql` | 26 | `20261028000000_ct_final_03_rls_security_remediation.sql` |
| 13 | `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` | 27 | `20261029000000_ct_final_03_staff_workload_rls.sql` |
| 14 | `20261011000000_p17c_contractual_instruments_and_allocations.sql` | | |

**Delta derivation.** Production held 71 applied migrations (max `20260927000000`); the release contains
98. The 27 files above are exactly the local files whose versions are **not** in production history
(`comm` on version lists): **27 pending**, **0 applied-but-not-local**, and **no local file below the
remote tip was skipped** — the pending set is a pure tail, so `--include-all` was neither needed nor used.

**Pre-apply destructive-statement scan of the 27 files (independent scan; no migration file was modified):**

* **No** `TRUNCATE public.*`, **no** `DELETE FROM public.*`, **no** unconditional `DROP TABLE`/`DROP COLUMN`.
* `DROP CONSTRAINT IF EXISTS` + re-`ADD CONSTRAINT` only on `organizations` (guarded by new NULL columns).
* DML present, all benign and previously documented: `UPDATE public.activity_clarifications` (table
  created earlier in the same batch), `UPDATE public.staff_roles` (capability grant
  `{"can_manage_backups": true}` for `admin`/`system_admin`), reference-data `INSERT`s
  (`scope3_categories`, `disclosure_framework_versions`, `disclosure_requirement_versions`), and the two
  bucket-alignment files' `UPDATE storage.buckets` (see §14 / **D-2**).
* **No `CONCURRENTLY`** anywhere in the set → every file is fully transactional.
* **No pending migration references `document_processing_queue`** (relevant to **D-3**).

---

## 7. Migration execution — result for every migration

**Mechanism (the approved Supabase production migration path, per cutover runbook step 5):**

```
supabase db push --skip-vault --yes --db-url <SUPABASE_LIVE_POSTGRES_DATABASE_URL>
```

* cwd = repository root (so `supabase/migrations/**` is the frozen set), `--db-url` = the **production**
  `SUPABASE_LIVE_POSTGRES_DATABASE_URL` (never the local `DATABASE_URL`, which points at `127.0.0.1`).
* `--skip-vault` — no vault/config-derived change is pushed; **nothing but migrations** was touched.
* `--dry-run` was executed first and reported exactly the 27 expected files in order (no extra, no
  missing).
* Migration history was managed by the CLI against `supabase_migrations.schema_migrations`; the CLI
  records a version only after that migration's transaction commits, so no migration can be marked
  applied without executing. No `db reset`, no manual history insert, no bypass of migration tracking.

**Result: 27/27 applied, exit 0, zero errors.** Console excerpt (verbatim; the `[Y/n]` prompt was
auto-answered by `--yes`):

```
Connecting to remote database...
Do you want to push these migrations to the remote database?
 • 20260928000000_p8_fs_activity_clarifications.sql
 • 20260929000000_p8_fs_activity_clarifications_fks.sql
 … (all 27, in the order of §6) …
 • 20261029000000_ct_final_03_staff_workload_rls.sql
 [Y/n] y
Applying migration 20260928000000_p8_fs_activity_clarifications.sql...
Applying migration 20260929000000_p8_fs_activity_clarifications_fks.sql...
 … one line per migration, no error line …
Applying migration 20261029000000_ct_final_03_staff_workload_rls.sql...
Finished supabase db push.
```

| # | Migration | Result |
| --- | --- | --- |
| 1–27 | every file in §6 | **APPLIED — SUCCESS** (each printed `Applying migration …`; no failure, no partial application, no abort; final line `Finished supabase db push.`) |

No STOP condition was triggered: no unexpected conflict, no schema mismatch, no destructive operation, no
migration failure. The two FINAL-03 RLS migrations' own fail-closed guards (wrong-target check,
`anon`/`authenticated`-BYPASSRLS check, fail-closed-drift check, retained-policy-family check) all passed,
and their post-conditions (all approved tables RLS-enabled, `public` policy count delta = 0, retained
policy family byte-identical, no FORCE RLS) held — otherwise they would have raised and aborted the push.

**Timeline (local, UTC+06):** dry-run 04:21:47 → restore-point dump 04:22:31 → apply window ~04:23:0x
→ `Finished supabase db push.` 04:23:54 → post-migration checks 04:25:02.

---

## 8. Post-migration schema state (measured immediately after the apply)

| Metric | PRE | POST | Delta | Interpretation |
| --- | --- | --- | --- | --- |
| `public` base tables | 134 | **150** | **+16** | exactly the 16 documented additive tables (§6) |
| RLS-enabled tables | 87 | **147** | +60 | 44 FINAL-03 enablements + 16 new tables, all RLS-on |
| RLS-disabled tables | 47 | **3** | −44 | only Class A remains disabled (§9) |
| `public` policies | 198 | **231** | +33 | all 33 new policies live on the 16 new tables; **none removed** |
| `public` functions | 55 | 68 | +13 | additive (new tables' helper functions) |
| `public` triggers (non-internal) | 81 | 95 | +14 | additive (append-only guards) |
| `public` indexes | 315 | 411 | +96 | additive |

**Table-set reconciliation (`comm` of table names).** Tables present PRE but **missing POST: none**.
Tables added POST (16): `activity_clarifications`, `backup_jobs`, `carbontally_insight_conversations`,
`carbontally_insight_interactions`, `carbontally_insight_messages`, `carbontally_insight_tool_calls`,
`contractual_instruments`, `estimation_records`, `insight_concurrency_leases`,
`insight_rate_limit_buckets`, `instrument_allocations`, `report_schedule_definitions`,
`report_schedule_runs`, `report_share_access_events`, `report_shares`, `scope3_categories` — matching the
pre-migration conflict analysis exactly.

**BACKUP-01/02 pre-start gate (runbook step 6) — satisfied.** `public.backup_jobs` now exists with the
verification/single-flight column set and all expected indexes:

```
backup_jobs_pkey · backup_jobs_single_flight_idx · backup_jobs_backup_set_idx
backup_jobs_verification_idx · backup_jobs_expiry_idx · backup_jobs_history_idx · backup_jobs_idempotency_key_idx
```

**Note on the withdrawn `149 / 149 / 271` legacy expectation (D-4):** that figure is neither the measured
state nor an objective (PO-ratified; the QA-only P8 RLS lineage is production-prohibited). The
production-specific expectation was *current objects + additive objects*; the measured result
(150 tables / 147 RLS-enabled / 231 policies) is consistent with that derivation.

---

## 9. Post-migration RLS state

**Result: all 44 FINAL-03 remediation targets are RLS-enabled; fail-closed targets carry zero policies;
Group B kept exactly its retained policies; Class A was not modified.**

| Group | Tables | Expected | Measured POST |
| --- | --- | --- | --- |
| Group A — fail-closed | 41 | RLS on, **0** policies | **41/41 RLS-on, 0 policies** ✅ |
| Group B — enable-only | 2 | RLS on, 3 + 1 retained policies | **2/2 RLS-on, 3 + 1 policies** ✅ |
| `staff_workload` | 1 | RLS on, **0** policies | **RLS-on, 0 policies** ✅ |
| **Total targets** | **44** | 44 RLS-on, 4 policies total | **44/44 RLS-on, 4 policies total** ✅ |
| Class A | 3 | untouched (RLS off, 0 policies) | `emission_factors` (f,0) · `business_hours` (f,0) · `sla_definitions` (f,0) ✅ |

Post-migration RLS totals: **147 RLS-enabled / 3 RLS-disabled** (the 3 disabled being exactly Class A);
**`relforcerowsecurity` = false on every target** (no `FORCE ROW LEVEL SECURITY`); **0 policies reference
`anon` or `public`**.

Group B retained policies (unchanged, definitions captured as a new baseline):
`conversation_participants_entity_select` (SELECT, `{authenticated}`),
`conversation_participants_select` (SELECT, `{authenticated}`),
`conversation_participants_update_own` (UPDATE, `{authenticated}`,
`USING is_conversation_participant(conversation_id)` / `WITH CHECK user_id = auth.uid()`),
`manual_extraction_items_entity_select` (SELECT, `{authenticated}`).

**SQL-level proof that FINAL-03 could not have altered policies or grants.** Auditing the two frozen
files' executable statements: the only statement they execute is
`EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t)`; there is **no**
`CREATE POLICY` / `DROP POLICY` / `ALTER POLICY` / `GRANT` / `REVOKE` / `INSERT` / `UPDATE` / `DELETE`
statement in either body (the files' own guards and post-conditions enforce policy-count delta = 0).

---

## 10. Post-migration policy inventory summary

| Check | Result |
| --- | --- |
| `public` policies PRE → POST | **198 → 231** (+33) |
| Policies present PRE but **missing POST** | **none** (no policy was dropped) |
| Policies added POST | 33, all on the 16 newly created tables (e.g. `activity_clarifications` 4; `contractual_instruments`/`estimation_records`/`instrument_allocations` 4 each; `carbontally_insight_*` 2 each; `report_shares`/`report_schedule_definitions` 3 each; `report_schedule_runs`/`report_share_access_events`/`scope3_categories` 1 each) |
| Policies referencing `anon` or `public` | **0** (PRE and POST) |
| Policies on the 44 FINAL-03 targets | **4** — exactly the Group B retained family |
| Policies on Group A fail-closed tables | **0** |
| Policies on `staff_workload` | **0** |
| Policy count delta attributable to FINAL-03 | **0** (all +33 come from the 16 new tables) |

---

## 11. Post-migration data preservation results

**Method (strongest available, byte-level).** The pre-migration state was captured as a physical
`pg_dump` (restore point, §5) immediately before the apply. For every retained table the pre-migration
column list was read from the dump's own `COPY public.<t> (<cols>) FROM stdin;` header, the same column
list was selected from live production afterwards, both row sets were sorted, and the **sha256 of each
sorted row set** was compared. Identical sha256 ⇒ every retained row is byte-for-byte unchanged on the
pre-migration column set (a new column added by a migration is excluded by construction, so it cannot
mask or fake a change).

| Retained table | PRE cols | PRE rows | POST rows | Sorted-row sha256 PRE = POST | `diff` | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `organizations` | 68 | 2 | 2 | `40575ce489e02c8e78e2339aef450d4a352f659f9d2bf50a128bf940e7867cfd` | 0 | **IDENTICAL** ✅ |
| `organization_members` | 7 | 2 | 2 | `e6a0572aa39b0d925544a63cbe7cc0b5ebe5f0c499ef49156bb0fc89f1bce6e3` | 0 | **IDENTICAL** ✅ |
| `evidence_line_items` | 14 | 74 | 74 | `899261459f2b06c9191e10adc3085ab7d294863f92b661fa7009a3bbd6f1ca23` | 0 | **IDENTICAL** ✅ |
| `organization_files` | 26 | 11 | 11 | `04c9f2f8c5e763af116813407316c02c48f7a1ddfedfe6a91658fd901b1537df` | 0 | **IDENTICAL** ✅ |
| `manual_extraction_batches` | 30 | 2 | 2 | `fad7f7c8932b0106e260b369359072c58385c464a5b5dbbcde6818f949b6b52a` | 0 | **IDENTICAL** ✅ |
| `conversations` | 20 | 1 | 1 | `562a3fdde1b218abc33716b44ba60204f9b65fcbd25fbf0b4b38b7fd70d4750c` | 0 | **IDENTICAL** ✅ |
| `messages` | 23 | 1 | 1 | `32731550208bb2f8b4a4778c2728131abed0fca58d5cbf2e335e09f4159c1b9a` | 0 | **IDENTICAL** ✅ |
| `document_processing_queue` | 79 | 11 | 11 | PRE `efdf073ed1c186c9a105f53340ad1f90a8d154d396ea598fe7c34ff7e57672ad` / POST `3ecc8d5f60a5947e91c632f316b678f3b08327d75c5d9415d2f0bbb2b70b78c9` | 4 (2 rows) | **row count + identity preserved; 2 rows advanced by an external worker — see D-3** |

| Preservation metric | PRE | POST | Verdict |
| --- | --- | --- | --- |
| Org-linked rows total (7 tables) | 101 | **101** (74/11/11/2/2/1/1) | ✅ unchanged |
| `organizations` (ids/names/active/created_at) | 2 | **2** — same ids, same names, `is_active=t`, same timestamps | ✅ byte-identical |
| `auth.users` | 2 | **2** — same ids, same e-mails, same confirmation/last-sign-in timestamps, not banned | ✅ unchanged |
| `auth.sessions` / `auth.refresh_tokens` | 26 / 48 | **26 / 48** | ✅ unchanged |
| Demo-domain users | 0 | **0** | ✅ no demo import |
| `organization_members` (ids/org/user/role/active) | 2 | **2** — same rows | ✅ byte-identical |
| `storage.objects` (bucket `documents`) | 58 | **58** | ✅ unchanged |

**No deletion, no count decrease, no identity change, no storage loss.**

---

## 12. Emission-factor count and fingerprint comparison

| Metric | PRE | POST | Verdict |
| --- | --- | --- | --- |
| `emission_factors` row count | **7,049** | **7,049** | ✅ exact match |
| Whole-row fingerprint `md5(string_agg(md5(f::text),'' order by md5(f::text)))` | `021087a43be5db7469ec6d16ae542235` | `9dbc60575b4fc70bff66b87848514014` | **changed — explained, see below** |
| **Original 13-column row set** (sorted COPY text, both from the pre-migration dump and live production) | sha256 `795ea7c43571b632286a2af546989ba5c7189e25be7a7af545bd950a235886a9` (7,049 rows) | sha256 `795ea7c43571b632286a2af546989ba5c7189e25be7a7af545bd950a235886a9` (7,049 rows) | ✅ **byte-identical, `diff = 0`** |

**Why the whole-row fingerprint changed (fully explained, not data loss).** The apply **added four
columns** to `public.emission_factors` — `scope2_method`, `scope3_category_hint`, `factor_type`,
`gas_coverage` (columns 14–17; added by `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql`
and the factor-governance work) — and attached/updated column comments. Because `f::text` renders the
*whole* row, any added column changes the hash **even though not one pre-existing value changed**. The
13-column comparison above proves the 7,049 factor rows are unchanged byte-for-byte.

**No factor row was inserted, deleted, or updated:** the count is exact, the original-column row set is
byte-identical, and the pre-apply scan found no `DELETE`/`TRUNCATE`/`UPDATE` against `emission_factors`
(only `ADD COLUMN IF NOT EXISTS`, `COMMENT`, and two *referencing* FKs from other tables).

**New whole-row fingerprint baseline (post-migration): `9dbc60575b4fc70bff66b87848514014`** — the value
future changes should be compared against (the pre-migration `021087a4…` is no longer reproducible by
design).

---

## 13. Organisation / account preservation results

* `0c0aa358-eaed-492c-9a8b-f7fabe6531ac` — **Babui Technologies UK Limited** — present, `is_active=t`,
  created 2026-09-17 07:24:56.588538+00 (unchanged), row byte-identical. ✅
* `8ae45e55-afa9-42f1-b4f9-f0225f9b98cd` — **Faria Green Company UK LTD** — present, `is_active=t`,
  created 2026-09-17 15:24:27.744541+00 (unchanged), row byte-identical. ✅
* `40b9f3f6-040d-4cc5-9bb1-82ae10115421` — present in `auth.users`, e-mail confirmed, **not banned**,
  last sign-in 2026-09-26 13:45:03.745723+00 (unchanged). ✅
* `ab7a9f50-8f16-4eb4-a229-40fa3a87c3e4` — present in `auth.users`, e-mail confirmed, **not banned**,
  last sign-in 2026-09-24 05:15:52.152694+00 (unchanged). ✅
* Membership relationship intact and byte-identical: `40b9f3f6… → 0c0aa358…` (owner) and
  `ab7a9f50… → 8ae45e55…` (owner); exactly **2** `organization_members` rows.

The migration set touched `public.organizations` only **additively** (`ADD COLUMN IF NOT EXISTS
consolidation_approach / organization_type` + NULL-safe `CHECK` constraints), which is confirmed by the
byte-identical 68-column comparison in §11.

---

## 14. Storage-object preservation result

| Check | PRE | POST | Verdict |
| --- | --- | --- | --- |
| `storage.objects` in bucket `documents` | **58** | **58** | ✅ no object lost/added |
| `storage.objects` (all buckets) | 58 | **58** | ✅ |
| `storage.buckets` row `documents` | `public=f` · `file_size_limit=2097152` | `public=f` · **`file_size_limit=10485760`** | ⚠ **intended metadata change — D-2** |

No object was moved, rewritten or deleted; the bucket row itself was **not** recreated. The bucket row's
`file_size_limit` was raised to **10,485,760 B (10 MiB)** by the two *authorised* bucket-alignment
migrations (`20261024000000_ct_final_01_documents_bucket_size_limit.sql`,
`20261025000000_ct_step2_documents_bucket_size_alignment.sql`), which is exactly the ratified Storage
Step 2I / CT-FINAL-01 alignment (runbook step 11 target: private `documents` bucket with the
10,485,760-byte ceiling). `public = FALSE` was re-asserted and is unchanged.

---

## 15. Migration-history result

| Check | Result |
| --- | --- |
| Applied migrations PRE → POST | **71 → 98** (+27) |
| Latest applied version | `20260927000000` → **`20261029000000`** |
| Pending local files after the apply | **0** of 98 |
| Applied-but-not-local versions | **none** |
| Duplicate versions in `supabase_migrations.schema_migrations` | **0** |
| Ordering | canonical filename (version) order preserved; the CLI applied the tail strictly in order |
| Skipped migrations | **none** |
| Falsely marked applied (recorded without executing) | **none** — the CLI records a version only after that migration's transaction commits, and each migration logged `Applying migration …` |
| Unexpected migrations applied | **none** — the applied tail equals the frozen 27 exactly |

Final migration tip: **`20261029000000_ct_final_03_staff_workload_rls`**.

---

## 16. Discrepancies

| ID | Severity | Discrepancy | Assessment / disposition |
| --- | --- | --- | --- |
| **D-1** | Info (expected) | `emission_factors` **whole-row** fingerprint changed (`021087a4…` → `9dbc6057…`) | **Fully explained, not data loss.** Four columns were added to the table by the authorised set, so `f::text` differs by construction. The 7,049 rows are **byte-identical on all 13 pre-migration columns** (identical sorted sha256, `diff = 0`); count exact. See §12. |
| **D-2** | Info (intended) | `storage.buckets.documents.file_size_limit` 2,097,152 → **10,485,760** | **Intended** by the two authorised bucket-alignment migrations (ratified 10 MiB cap; runbook step 11). `public=FALSE` re-asserted; **no object changed** (58/58). See §14. |
| **D-3** | **Attention — verifier to note** | During the migration window an **external, pre-existing production writer** re-attempted one `document_processing_queue` row: `updated_at` 2026-10-02 **13:16:40** → **22:27:45** → **22:32:46** UTC; `lock_token` `worker::b6261600…` → `worker::a5754a68…` → `worker::cb64c9db…`; `locked_at` moved with it. | **Not caused by the migration:** no pending migration references `document_processing_queue` (verified), and a lock token of the form `worker::<uuid4hex>` is generated by the CarbonTally application (`backend/workers/automatic_processing.py:136`), not by a migration. The row is still present (`processing`/`extracting`, same document, same error text), the queue still holds **11** rows, and only lease/attempt metadata advanced. **Consequence:** the migration window was **not write-quiesced**; production has (or had) a live automatic-processing worker writing to the queue. Recorded so the independent verifier does not mis-attribute this diff to the migration. |
| **D-4** | Info (PO-ratified) | Legacy expectation `149 tables / 149 RLS-enabled / 271 policies` not reached | Not an objective (PO-ratified; the QA-only P8 RLS lineage is production-prohibited). Measured: **150 / 147 / 231**. See §8. |
| **D-5** | Info | `anon` holds DML grants on 3 newly created tables (all RLS fail-closed) | See **O-1**. |
| **D-6** | Info | Pre-existing working-tree changes (`.gitignore`, `frontend/App_.js`) still show as modified after this task | Pre-existing (mtimes 2026-09-23 / 2026-09-28, i.e. before this session) and **untouched by P3**; HEAD is still the frozen SHA. See **L-8**. |

### 16.1 Observations for the verifier

* **O-1 (security nuance, fail-closed).** Supabase's default privileges granted `anon` the four DML
  privileges on three **newly created** tables: `activity_clarifications`, `insight_concurrency_leases`,
  `insight_rate_limit_buckets` (12 `(table, privilege)` grants). **All three are RLS-enabled**
  (`activity_clarifications` 4 policies, all `{authenticated}`; the other two **0 policies**), and **0
  policies anywhere reference `anon`/`public`** → every `anon` read/write is **denied** by RLS
  (fail-closed). `activity_clarifications` additionally had `TRUNCATE/TRIGGER/REFERENCES/MAINTAIN`
  revoked from `anon` by `20260928000000`. This is the migration-defined state, not drift; whether to add a
  `REVOKE`-hardening migration (the D-4/R-5 register class) is **for the owner/verifier**, not decided
  here. Post-migration grants: `authenticated` 509, `service_role` 1041, `postgres` 1050, `anon` 12.
* **O-2 (fallback path unused).** Because `supabase db push --db-url` worked end-to-end, the alternative
  "reviewed SQL application path" (per-file psql + history insert) was **not** used, so no manual
  migration-history manipulation occurred.

---

## 17. Limitations

* **L-1 — No platform restore point available.** The recorded B2′ gap stands (0 managed backups, PITR
  disabled, `backup.retention_days=0`, owner decision **P4** still open), so no database-level restore
  point could be created. **Mitigation taken:** a local logical `pg_dump` of the retained footprint
  immediately before the apply (§5, sha256 `523f4712…`), plus a verified additive-only migration set.
  This is a mitigation, not a substitute for a managed backup/PITR capability.
* **L-2 — `--db-url` appears in the CLI process argument list** for the duration of the push (same host,
  single user, no multi-user exposure). The DSN was never printed, logged, echoed or written into any
  artefact, and it is redacted everywhere in this report. The flag is the documented CLI mechanism for a
  project that is not linked in the local `supabase/.temp`.
* **L-3 — Group B policy *definitions* were not captured pre-migration on production** (only names, CMD
  and roles). Their integrity is evidenced instead by (a) the migration's own retained-policy-family guard
  and policy-count-delta-0 post-condition, (b) the SQL audit proving the files execute only
  `ALTER TABLE … ENABLE ROW LEVEL SECURITY`, and (c) no lost/renamed policy in the name/CMD/roles diff.
  Current definitions are captured as a new baseline (md5 of the 4 retained definitions =
  `3e60016d86251ec803a335978195ef40`).
* **L-4 — The migration window was not write-quiesced** (external automatic-processing worker active —
  D-3). The retained tables were nonetheless verified byte-identical apart from that worker's lease
  metadata.
* **L-5 — Cline cannot confer acceptance.** This report is implementation evidence only; an independent
  CoStrict verification of the production migration / schema / RLS / preservation result is required.
* **L-6 — Application layer not deployed or verified.** Render and Vercel were **not** deployed, the
  production worker was **not** started by this task, and no browser/E2E acceptance was performed. The
  post-migration schema has therefore **not** been exercised by a freshly deployed application here.
* **L-7 — The restore-point dump lives in `/tmp`** (outside the repository, deliberately not committed
  because it contains production data). It is not part of the release and does not survive a reboot.
* **L-8 — Repository state:** HEAD remains `375a48dc1b9e9cfd74090bbf747554ae997acb59` on
  `p8-release-reconciled`; no commit, tag or push was made by P3; the only repository artefact added by
  this task is this report. Two pre-existing tracked modifications (`.gitignore`, `frontend/App_.js`)
  remain in the working tree and were not touched (D-6).

---

## 18. Confirmation — no Render / Vercel deployment

**Confirmed: no deployment of any kind occurred in this task.**
No Render deploy, no Vercel deploy, no production service restart, no production environment-variable or
secret change, no email/SMTP or billing configuration change, no DNS change. The only production system
touched was the **database schema/data** described above.

## 19. Confirmation — no application worker was started

**Confirmed: this task started no worker, service or scheduled process.**
No backup worker, no background worker, no automatic-processing worker, no API/`uvicorn` process and no
cron job was started by this task on any host. (An **external, pre-existing** production writer was
*observed* writing `document_processing_queue` during the window — recorded as **D-3**; it was not
started, stopped or altered here.) The BACKUP-01/02 pre-start gate is now *satisfied* for any future
authorised worker start (`public.backup_jobs` exists with its indexes — §8), but no start was performed.

---

## 20. Final verdict

> **CT-FINAL03-P3-SUPABASE-001 — IMPLEMENTED — PRODUCTION SUPABASE MIGRATIONS APPLIED AND DATA/RLS PRESERVATION VERIFIED — READY FOR INDEPENDENT VERIFICATION**

Basis (all conditions met):

* **27/27 intended migrations applied successfully** — canonical order, no skip, no duplicate, no
  unexpected migration, no false history entry; final tip `20261029000000` (§6/§7/§15).
* **No destructive operation** — the set contains no `TRUNCATE`/`DELETE`/unconditional `DROP`; no table
  lost (`comm` = empty); no policy lost (§6/§8/§10).
* **No `db reset`, no manual schema rewrite, no local/demo import** — migration tracking used throughout;
  0 demo-domain users (§5/§7).
* **Required production data preserved** — 101 org-linked rows, 2 organisations (same ids/names), 2
  owner-created accounts, 2 `organization_members` rows, 58 storage objects: count-identical **and**
  byte-identical on the pre-migration column sets (§11/§13/§14).
* **7,049 emission factors remain intact** — exact count; the 13 original columns are **byte-identical**
  (`diff = 0`, sorted sha256 `795ea7c4…` on both sides). *Qualified by design:* the **whole-row**
  fingerprint necessarily changed because four columns were added by the authorised set (**D-1**); this is
  recorded explicitly rather than reported as a match (§12).
* **FINAL-03 RLS state correct** — 44/44 targets RLS-enabled (41 fail-closed with 0 policies; Group B with
  its 3+1 retained policies; `staff_workload` with 0 policies), 0 FORCE RLS, 0 `anon`/`public` policies,
  Class A untouched (§9).
* **Migration history correct** (§15).
* **No blocking discrepancy.** D-1/D-2/D-4/D-5/D-6 are explained/expected; **D-3** is an external-writer
  observation the verifier must know about, but it is **not** a migration defect and caused no data loss.

**This is an implementation result, not an acceptance.** Per the task boundary, the next step is
**independent CoStrict verification** of the production Supabase migration, schema, RLS and
data-preservation result. Render and Vercel remain **not deployed** and **not authorised** by this task.

---

## Appendix A — the 27 applied migrations, frozen-SHA integrity

For every file, `sha256(worktree) == sha256(git show 375a48dc…:supabase/migrations/<file>)` → `MATCH`.
Digests below are the first 16 hex characters of the file's full sha256.

| Version | Result | worktree | frozen HEAD |
| --- | --- | --- | --- |
| 20260928000000 | MATCH | `20e2743b4bd5abec` | `20e2743b4bd5abec` |
| 20260929000000 | MATCH | `631eab47f03308e0` | `631eab47f03308e0` |
| 20260930000000 | MATCH | `60326f04e792480e` | `60326f04e792480e` |
| 20260931000000 | MATCH | `9b90424e7ef47b85` | `9b90424e7ef47b85` |
| 20261001000000 | MATCH | `1695a59a9900c14a` | `1695a59a9900c14a` |
| 20261002000000 | MATCH | `310dc0456fd72141` | `310dc0456fd72141` |
| 20261003000000 | MATCH | `5ec1fc92b545e904` | `5ec1fc92b545e904` |
| 20261005000000 | MATCH | `5b1058daacdbdd7b` | `5b1058daacdbdd7b` |
| 20261006000000 | MATCH | `4bf8888d1b47e091` | `4bf8888d1b47e091` |
| 20261007000000 | MATCH | `a8c8bab139b53b10` | `a8c8bab139b53b10` |
| 20261008000000 | MATCH | `94499f4e15a457ef` | `94499f4e15a457ef` |
| 20261009000000 | MATCH | `3808e10aa7449a5f` | `3808e10aa7449a5f` |
| 20261010000000 | MATCH | `e6865ff6c137dda2` | `e6865ff6c137dda2` |
| 20261011000000 | MATCH | `09a5e95687f53a29` | `09a5e95687f53a29` |
| 20261012000000 | MATCH | `41dbb59e8ea283f5` | `41dbb59e8ea283f5` |
| 20261013000000 | MATCH | `028a5b91ab483d1a` | `028a5b91ab483d1a` |
| 20261014000000 | MATCH | `aef13370890f4f76` | `aef13370890f4f76` |
| 20261020000000 | MATCH | `c28d478f283c506f` | `c28d478f283c506f` |
| 20261021000000 | MATCH | `68ed11826a778d3d` | `68ed11826a778d3d` |
| 20261022000000 | MATCH | `9847078d01bd0c58` | `9847078d01bd0c58` |
| 20261023000000 | MATCH | `05fb521ae9238c39` | `05fb521ae9238c39` |
| 20261024000000 | MATCH | `d88d78537c74874b` | `d88d78537c74874b` |
| 20261025000000 | MATCH | `d24b08fb62a95dd2` | `d24b08fb62a95dd2` |
| 20261026000000 | MATCH | `b75da97887a0b13e` | `b75da97887a0b13e` |
| 20261027000000 | MATCH | `500202973db24f77` | `500202973db24f77` |
| **20261028000000** (FINAL-03 RLS) | MATCH | `ca461c9c5be712b8` | `ca461c9c5be712b8` |
| **20261029000000** (FINAL-03 RLS) | MATCH | `0775fa68388a5e69` | `0775fa68388a5e69` |

Full sha256 of the two FINAL-03 files (must equal the independently verified values):
`ca461c9c5be712b8c5bfaaa8200e2a3be83c5fb55990c3e118446b86904ecb15` and
`0775fa68388a5e697965b7500284a653df4a96336218ea5b2abbb2b98f7b1cb3` — **exact match**.

## Appendix B — evidence artefacts (all outside the repository, under `/tmp`)

| Artefact | Content |
| --- | --- |
| `/tmp/p3_pre_baseline.txt`, `/tmp/p3_pre_baseline_2.txt` | pre-migration schema/data/RLS baseline (read-only; `enforced_ro=on`) |
| `/tmp/p3_pre_migrations.txt`, `/tmp/p3_pre_tables_rls.txt`, `/tmp/p3_pre_policies.txt` | pre-migration migration list / RLS state / policy inventory |
| `/tmp/p3_guard_pre.txt` | pre-apply FINAL-03 guard pre-conditions (Group A/B policy families, BYPASSRLS) |
| `/tmp/p3_push_help.txt` | `supabase db push --help` (CLI 2.115.0 flags) |
| `/tmp/p3_dryrun.txt` | dry-run: exactly the 27 expected migrations, in order |
| `/tmp/ct_p3_restore_point/retained_footprint_pre_p3.dump` | pre-apply restore point, sha256 `523f47126794eaee087c51cf65d2668df6731835c0172667b7a4d78c70fe1fcb` |
| `/tmp/p3_apply.txt` | the apply log (27 × `Applying migration …` + `Finished supabase db push.`), DSN redacted |
| `/tmp/p3_post_a.txt`, `/tmp/p3_post_b.txt` | post-migration schema/data/RLS/policy/44-target verification |
| `/tmp/p3_post_migrations.txt`, `/tmp/p3_post_tables_rls.txt`, `/tmp/p3_post_policies.txt` | post-migration inventories |
| `/tmp/p3_factors_cmp_result.txt` | 7,049-row byte-identical factors proof (13 pre-migration columns) |
| `/tmp/p3_retained_cmp_result.txt` | per-table byte-identical retained-data proof |
| `/tmp/p3_dpq_diff_raw.txt` | the two `document_processing_queue` row diffs (D-3) |
| `/tmp/p3_dpq_live.txt`, `/tmp/p3_activity.txt`, `/tmp/p3_worker_attr.txt` | external-worker attribution evidence (D-3) |
| `/tmp/p3_anon.txt` | `anon` grant / RLS fail-closed analysis (O-1) |
| `/tmp/p3_groubb_defs.txt` | retained Group B policy definitions + definition md5 `3e60016d86251ec803a335978195ef40` |
| `/tmp/p3_integrity.txt` | 27-file frozen-SHA integrity table (Appendix A) |
| `/tmp/p3_final_mig_check.txt`, `/tmp/p3_diffs.txt`, `/tmp/p3_rls_counts.txt` | post-apply delta checks (pending = 0, table/policy/migration set diffs, RLS counts) |

**No credential, token, JWT, service-role key or complete DSN appears in this report or in any evidence
artefact produced for it.**

---

## Appendix C — exact commands used (redacted)

```sh
# read-only baseline (same wrapper used for every verification query)
SET default_transaction_read_only = on;      # enforced in-session; proved by a failing CREATE TABLE probe

# pre-apply plan
supabase db push --dry-run --skip-vault --yes --db-url <SUPABASE_LIVE_POSTGRES_DATABASE_URL>

# restore point (local, outside the repo)
pg_dump --format=custom --no-owner --no-privileges \
  --table=public.organizations --table=public.organization_members \
  --table=public.evidence_line_items --table=public.document_processing_queue \
  --table=public.organization_files --table=public.manual_extraction_batches \
  --table=public.conversations --table=public.messages --table=public.emission_factors \
  --table=supabase_migrations.schema_migrations --table=storage.buckets \
  -f /tmp/ct_p3_restore_point/retained_footprint_pre_p3.dump

# APPLY (cwd = repository root)
supabase db push --skip-vault --yes --db-url <SUPABASE_LIVE_POSTGRES_DATABASE_URL>

# post-apply verification: schema/RLS/policy/data counts (read-only, §8–§15),
# per-table byte-level PRE vs POST comparison (§11), factors 13-column comparison (§12).
```

**Not run:** `supabase db reset`, `supabase link`, any `DROP`/`TRUNCATE`/`DELETE`, any application
`deploy`, any worker start, any production configuration change.
