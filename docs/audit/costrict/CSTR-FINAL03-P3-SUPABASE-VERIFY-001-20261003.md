# CSTR-FINAL03-P3-SUPABASE-VERIFY-001 — Independent Verification of the Production Supabase Migration, Schema, RLS and Data Preservation

## 1. Task ID

**CSTR-FINAL03-P3-SUPABASE-VERIFY-001** — independent verification of the production Supabase migration
executed by Cline under **CT-FINAL03-P3-SUPABASE-001**, claimed as:

> *CT-FINAL03-P3-SUPABASE-001 — IMPLEMENTED — PRODUCTION SUPABASE MIGRATIONS APPLIED AND DATA/RLS PRESERVATION VERIFIED — READY FOR INDEPENDENT VERIFICATION*

## 2. Verification role

**CoStrict** — independent verification agent, **not** the implementation agent. This verification was
performed **read-only against production**. Every production query ran in a session that executed
`SET default_transaction_read_only = on` first (verified in-session: `default_transaction_read_only = on`,
see §17). No migration, table, policy, grant, RLS setting, row, storage object, worker, environment
variable, secret, Render/Vercel configuration or repository file was modified; nothing was repaired;
nothing was committed or pushed. No secret, token, JWT, service-role key or credential-bearing DSN is
printed in this report.

**Evidence labels used throughout**

* **[I]** — independently verified by CoStrict in this pass (production query, frozen-release object, or local computation).
* **[C]** — stated by Cline and **not** independently reproducible.
* **[E]** — expected migration effect (documented by the ratified scope or the frozen migration files).
* **[O]** — operational observation.
* **[L]** — limitation / not determinable by this method.

---

## 3. Production target identity

| Field | Value | Basis |
|---|---|---|
| Project ref | `pvwiojoyaqywtydzcpbg` — **present in the connection username** (`…: True`, checked in-process; the username itself is never printed) | [I] |
| Endpoint kind / region | Supavisor **pooler**, host region segment **`eu-west-2`**, port **5432** | [I] |
| Database / role at SQL level | `current_database()` = **`postgres`**, `current_user` = **`postgres`** (the pooler maps the tenant user) | [I] |
| Server version | **PostgreSQL 17.6** (`aarch64-unknown-linux-gnu`, server_version_num 170006) | [I] |
| Recovery state | `pg_is_in_recovery()` = **f** (primary) | [I] |
| Supabase roles present | `anon`, `authenticated`, `service_role` all present | [I] |
| RLS is a real control | `anon.rolbypassrls = f`, `authenticated.rolbypassrls = f` | [I] |
| Backend trust model | `service_role.rolbypassrls = t` (documented backend bypass) | [I] |
| Schema fingerprint match to the ratified baseline | 2 organisations (same ids/names), 7,049 factors, 71→98 applied migrations, `documents` bucket 58 objects — the recorded production pre-state | [I] |

**Target confirmed.** The database queried is the intended CarbonTally production project. The wrong-target
risk is excluded by the identity of the retained data (the exact two production organisations, the exact
owner accounts, the 7,049-factor library) plus the migration-history tip.

---

## 4. Frozen release SHA

```
375a48dc1b9e9cfd74090bbf747554ae997acb59   (branch p8-release-reconciled)
```

Previously independently verified by `CSTR-FINAL03-P2-RECON-VERIFY-001` (release SHA and scope confirmed).
The repository state was **not altered** by this verification: `HEAD` is still this SHA (§16).

---

## 5. Migration-history verification

Live production query, `supabase_migrations.schema_migrations` [I]:

| Check | Result |
|---|---|
| Applied migrations | **98** |
| Tip | **`20261029000000`** (`ct_final_03_staff_workload_rls`) |
| Duplicate versions | **0** |
| Versions newer than the tip | **0** |
| Applied versions vs the **frozen release's own migration set** (`git ls-tree -r <SHA> -- supabase/migrations`) | **98 vs 98, set-identical** |
| Local files not applied (pending) | **NONE** |
| Applied but not in the release | **NONE** |
| The five-file tail, in order (DB order review) | `20261025000000` → `20261026000000` → `20261027000000` → `20261028000000` → `20261029000000` — **exact match** |
| FINAL-03 migration versions present | `20261028000000` ★, `20261029000000` ★ (both present) |

The +27 delta (71 → 98) is confirmed by the pre-migration restore-point dump, whose archived
`schema_migrations` COPY block contains **71** rows [I], and the post-state holds 98 [I].

**Migration-content integrity [I]/[L].** `supabase_migrations.schema_migrations` stores only
`(version, name, statements)`; it carries **no file digest**, so the *bytes* applied cannot be read back
from the server. The content claim is instead verified by (a) exact version/name correspondence with the
frozen release files, (b) the observed schema/RLS/policy/column outcome matching those files' defined
effects (44 enablements, four new factor columns, 16 new tables, 33 new policies), and (c) the
previously verified frozen release itself. Recorded as a stated limitation rather than an asserted byte proof.

---

## 6. Schema verification

| Metric | Cline POST | CoStrict measured | Verdict |
|---|---|---|---|
| `public` base tables (`relkind='r'`) | 150 | **150** | ✅ |
| RLS-enabled tables | 147 | **147** | ✅ |
| RLS-disabled tables | 3 | **3** | ✅ |
| `public` policies | 231 | **231** | ✅ |
| FORCE RLS tables | 0 | **0** | ✅ |
| Policies referencing `anon`/`public` | 0 | **0** | ✅ |
| `public` functions / indexes / triggers | 68 / 411 / 95 | **68 / 411 / 95** | ✅ |
| `backup*` tables | present | **1** (`backup_jobs`) | ✅ |

**Identity of the three RLS-disabled tables [I]** — `business_hours`, `emission_factors`, `sla_definitions`
(exactly the Class-A set, each with **0 policies**). This is verified by *table identity*, not just by count.

**Additive-only result [I]:** the sixteen documented new tables all exist and are all RLS-enabled:
`activity_clarifications`, `backup_jobs`, `carbontally_insight_conversations`,
`carbontally_insight_interactions`, `carbontally_insight_messages`, `carbontally_insight_tool_calls`,
`contractual_instruments`, `estimation_records`, `insight_concurrency_leases`,
`insight_rate_limit_buckets`, `instrument_allocations`, `report_schedule_definitions`,
`report_schedule_runs`, `report_share_access_events`, `report_shares`, `scope3_categories`.

**No table was lost [I]:** the ratified pre-migration baseline's 47-table RLS-disabled set
(`03-schema-drift-and-rls.txt`) equals **exactly** the 44 FINAL-03 targets ∪ {`emission_factors`,
`business_hours`, `sla_definitions`} — 47 = 44 + 3, with `targets − baseline = ∅`; all 44 targets and all
3 Class-A tables are present live. 134 + 16 = 150 tables, consistent with the measured tally.

---

## 7. RLS verification — the 44 FINAL-03 targets

**Method [I]:** the target list was derived **from the frozen migration files themselves** (regex-extracted
`group_a` (41), `group_b` (2) and M2 `fail_closed` (1) arrays at SHA `375a48d…`), then each table was
queried live on production.

| Group | Tables | Expected | Measured live | Verdict |
|---|---|---|---|---|
| A — fail-closed | 41 | RLS on, **0** policies | **41/41 RLS on, 0 policies** | ✅ |
| B — enable-only | 2 | RLS on, retained policies | **2/2 RLS on — 3 + 1 policies** | ✅ |
| `staff_workload` | 1 | RLS on, **0** policies | **RLS on, 0 policies** | ✅ |
| **Total** | **44** | 44 RLS on, 4 policies | **44/44 RLS on, 0 FORCE RLS, 4 policies** | ✅ |
| Class A | 3 | untouched (RLS off, 0 policies) | `business_hours` (off,0) · `emission_factors` (off,0) · `sla_definitions` (off,0) | ✅ |

**Group B retained policies (live definitions) [I]**

| Table | Policy | CMD | Roles | USING / WITH CHECK |
|---|---|---|---|---|
| `conversation_participants` | `conversation_participants_entity_select` | SELECT | `{authenticated}` | `can_view_entity_conversation(conversation_id)` |
| `conversation_participants` | `conversation_participants_select` | SELECT | `{authenticated}` | `can_view_conversation_participants(conversation_id)` |
| `conversation_participants` | `conversation_participants_update_own` | UPDATE | `{authenticated}` | `is_conversation_participant(conversation_id)` / `(user_id = auth.uid())` |
| `manual_extraction_items` | `manual_extraction_items_entity_select` | SELECT | `{authenticated}` | `((work_item_effective_entity(id) IS NOT NULL) AND is_entity_member(work_item_effective_entity(id)))` |

**FORCE RLS [I]:** `relforcerowsecurity = true` on **0** public base tables — the FINAL-03 decision to leave
FORCE off (so `service_role` keeps working) is intact on every one of the 44 targets and everywhere else.

**Policy-count arithmetic [I]:** 231 total − 33 on the 16 new tables = **198 policies on pre-existing
tables**, exactly the ratified pre-migration baseline count; and the **name sets** of policies on
pre-existing tables are **identical** pre vs post (198 vs 198; `PRE − POST = ∅`, `POST − PRE = ∅`, using
the pre-apply capture file as the pre-state data source — the comparison itself is CoStrict's). No policy was
dropped, renamed or added on any pre-existing table.

---

## 8. Policy security verification

| Check | Result | Basis |
|---|---|---|
| Policies referencing `anon` or `public` anywhere in `public` | **0** | [I] |
| Policies on the 41 fail-closed Group-A tables | **0** (so no broad `authenticated` policy exists on them) | [I] |
| Policies on `staff_workload` | **0** | [I] |
| Policies on the 44 targets | **4**, all `{authenticated}`, all Group-B retained names | [I] |
| Policies on the 16 new tables | 33, all on the new tables only; **0** reference `anon` | [I] |
| Retained Group-B policies unchanged | names, CMD and roles match the pre-apply capture; definitions are the ratified expressions | [I] |
| `anon` can bypass RLS | **No** (`rolbypassrls = false`) | [I] |
| `service_role` retains its intended bypass | **Yes** (`rolbypassrls = true`, unchanged) | [I] |
| Storage policies | the four `d32_documents_*` policies on `storage.objects`, all `{authenticated}`; no `anon` policy | [I] |

**No anonymous/public policy was introduced, and no broad authenticated policy was introduced on any
fail-closed table.**

---

## 9. The three remaining RLS-disabled tables

Verified by identity and state [I]: `emission_factors`, `business_hours`, `sla_definitions` remain
RLS-disabled with zero policies. **Not enabled, not altered, no policy created, no grant touched** — the
Class-A decision is preserved exactly.

---

## 10. Emission-factor data preservation (critical)

Independent method (**strongest available, no production mutation**): the pre-migration state was read from
Cline's pre-apply logical dump (`/tmp/ct_p3_restore_point/retained_footprint_pre_p3.dump`, archive
timestamp **2026-10-03 04:22:31 +06**, sha256 **`523f47126794eaee087c51cf65d2668df6731835c0172667b7a4d78c70fe1fcb`** —
matches the report [I]) by streaming its COPY blocks with `pg_restore` (no database involved); the
post-migration state was read live from production.

| Check | PRE (dump) | POST (live) | Verdict |
|---|---|---|---|
| `emission_factors` row count | **7,049** | **7,049** | ✅ |
| PRE column set (COPY header) | 13 columns — `id, reporting_year, activity_type, co2e_multiplier, created_at, updated_at, unit, scope, factor_source, factor_set, country, region_deprecated, import_batch_id` | live table = those 13 **+** `scope2_method`, `scope3_category_hint`, `factor_type`, `gas_coverage` (ordinals 14–17) | ✅ additive |
| The four new columns existed PRE? | **No** | added by the applied set | ✅ [E] |
| **13-column row set, canonicalised and sorted** | sha256 **`e02284727206bfea7b9c1e2effb24e6e2a1274b85d75df687a4f89c34137b268`** (7,049 rows) | sha256 **`e02284727206bfea7b9c1e2effb24e6e2a1274b85d75df687a4f89c34137b268`** (7,049 rows) | ✅ **byte-identical, `diff = 0`** |
| Duplicate factor rows | 0 | 0 | ✅ |
| Rows added / removed | — | 0 / 0 | ✅ |

**My digest differs from the sha256 reported by Cline (`795ea7c4…`) because I used my own canonical
serialisation (field separator `U+001F`, NULL sentinel `∅`, rows sorted, SHA-256 over the joined text). The
verification claim does not depend on digest equality with the report — it depends on the PRE and POST digests
being produced by the *same* CoStrict method and being equal, which they are.**

**Root cause of the whole-row fingerprint change (D-1) confirmed [I]/[E]:** the frozen migration
`20261010000000_p17a_accounting_dimensions_and_factor_governance.sql:197-207` contains
`ALTER TABLE public.emission_factors ADD COLUMN IF NOT EXISTS` for exactly the four new columns (plus
guarded `CHECK` constraints and column comments), and its own comment states *"No factor row is created,
changed, deleted or given a fabricated multiplier"*. The whole-row `f::text` hash therefore necessarily
changed while all pre-existing values stayed identical — **explained, not data loss**. The new columns
exist and are NULL on all retained rows (no fabrication).

---

## 11. Organisation / account preservation

| Item | Expected | Measured live | Verdict |
|---|---|---|---|
| `organizations` rows | 2 | **2** | ✅ |
| `0c0aa358-eaed-492c-9a8b-f7fabe6531ac` | Babui Technologies UK Limited, active | **present, same id, name unchanged, `is_active=t`** | ✅ |
| `8ae45e55-afa9-42f1-b4f9-f0225f9b98cd` | Faria Green Company UK LTD, active | **present, same id, name unchanged, `is_active=t`** | ✅ |
| `auth.users` (owner-created accounts) | 2 | **2** | ✅ |
| `40b9f3f6-040d-4cc5-9bb1-82ae10115421` | present, confirmed, not banned | **present, `email_confirmed_at` set, `banned_until` null** | ✅ |
| `ab7a9f50-8f16-4eb4-a229-40fa3a87c3e4` | present, confirmed, not banned | **present, `email_confirmed_at` set, `banned_until` null** | ✅ |
| Demo-domain users | 0 | **0** | ✅ |
| `organization_members` rows | 2 | **2** | ✅ |
| `02534fcc-87c5-45ea-8be8-17def8d9fcbe` | owner, org 0c0aa358, active | **identical** (`role=owner`, `is_active=t`, created 2026-09-17 07:24:56.588538+00) | ✅ |
| `61cd9d4d-aed3-4ca7-a2b4-798e89564206` | owner, org 8ae45e55, active | **identical** (`role=owner`, `is_active=t`, created 2026-09-17 15:24:27.744541+00) | ✅ |

**One time-bound observation [O]:** both accounts' `last_sign_in_at` now show **2026-10-03 ~05:37–05:38 UTC**
(vs 2026-09-26 / 2026-09-24 at baseline), and `auth.sessions` / `auth.refresh_tokens` now hold **28 / 51**
vs the reported 26 / 48. These are **auth-service activity metadata**, advanced by a live sign-in after the
migration — they are not identity, membership or business data, and their identity fields are unchanged.
Cline's "unchanged" statement was correct at his measurement time and is time-bound, not contradicted.

---

## 12. Organisation-linked data preservation and the ±1 reconciliation

**Authoritative PRE state:** the pre-apply dump (above). **POST state:** live production [I].

| Table | PRE (dump) | POST (live) | Verdict |
|---|---|---|---|
| `evidence_line_items` | 74 | **74** | ✅ |
| `document_processing_queue` | 11 | **11** | ✅ |
| `organization_files` | 11 | **11** | ✅ |
| `organization_members` | 2 | **2** | ✅ |
| `manual_extraction_batches` | 2 | **2** | ✅ |
| `conversations` | 1 | **1** | ✅ |
| `messages` | 1 | **1** | ✅ |
| **Total** | **102** | **102** | ✅ |

**Finding F-1 (INFORMATIONAL — documentation arithmetic, now settled): the brief's baseline total of "101"
is inconsistent with its own seven components, which sum to 102.** The ratified decision package itself
already flagged this: §B.3 prints the component table with **total 102** and states *"`02-preservation-org-linked-counts.txt`
cites **101** for the same set → a **±1 reconciliation** to settle by one re-measure at cutover"*. This
verification **is** that re-measure: every one of the seven components matches the baseline exactly, and the
correct total is **102**. **No data discrepancy exists** — the mismatch is in the earlier citation, and no
row was lost, added or altered (see §13 for the single worker-driven metadata change).

**Byte-level retained-row comparison [I]:** every retained table's pre-migration column list was taken from
the dump's `COPY public.<t> (<cols>) FROM stdin;` header, the same columns were selected from production, and
both row sets were canonicalised and compared. `organizations` (68 cols), `organization_members` (7),
`evidence_line_items` (14), `organization_files` (26), `manual_extraction_batches` (30), `conversations` (20)
and `messages` (23) are **identical**; `document_processing_queue` (79 cols, 11 rows) is identical **except
lease metadata on one row** (§13).

**The only pre-existing-table write in the batch [I]/[E]:** `20261026000000_ct_backup_01_backup_jobs.sql:181`
contains `UPDATE public.staff_roles SET permissions = permissions || '{"can_manage_backups": true}' … WHERE name IN ('admin','system_admin')`.
On production, `staff_roles` contains a single row (`pe_manager`, permissions
`{can_review, can_process, can_view_all}`) — **the UPDATE therefore matched zero rows and was a no-op in
production**. This is stronger than the implementation report's phrasing: no retained row of any kind was
modified by the batch.

---

## 13. D-3 — automatic-processing-worker activity (independent investigation)

**Method [I]:** full 79-column per-row comparison of the pre-apply dump's `document_processing_queue` COPY
data against live production, with boolean canonicalisation (`t/f` = `true/false`), followed by a
column-by-column diff.

| Question | Independent finding |
|---|---|
| Was the table modified during/after the migration window? | **Yes** — 1 of 11 rows. |
| Any row inserted/deleted? | **No** — 11 rows before and after, **identical id sets** (0 only-PRE, 0 only-POST). |
| Which columns changed? | **Only `lock_token`, `locked_at`, `updated_at`** on row `c50ad7ac-4132-461b-b434-9be194d726d4` — every other column of every row is identical. |
| PRE → POST values | `lock_token`: `worker::b6261600…` → **`worker::244a11d3c6af426a9d8bca3b6263ff9e`**; `locked_at`: `2026-10-02 13:16:40.336216+00` → **`2026-10-03 05:44:04.850846+00`**; `updated_at`: `2026-10-02 13:16:40.385205+00` → **`2026-10-03 05:44:04.920616+00`**. |
| Does any migration reference the table? | **No** — all 98 frozen migration files were scanned for the string `document_processing_queue`; **zero matches**. |
| Business-state columns | `status = processing`, `stage = extracting`, `attempt_count = 0`, `max_attempts = 3`, `workflow_error_count = 0`, `last_error = "attempt interrupted: worker cancelled or shutting down (extr…)"`, `pipeline_version = v3-auto-1.1` — **unchanged**; the row still refers to the same document. |
| Preservation-critical data altered? | **No.** The queue still holds 11 rows; no business payload column changed. |

**Critical timing observation [I]:** the new lease timestamp is **2026-10-03 05:44:04 UTC** — i.e.
**more than an hour after** Cline's migration window (`~22:23 UTC` on 2026-10-02) and **after** his own
measurements, and the new `worker::244a11d3…` token differs from the last token Cline observed
(`worker::cb64c9db…`). The external writer is therefore **still active now**, independently corroborating
that the writer is an application worker (lock-token format `worker::<uuid4hex>` is generated by the
CarbonTally worker code, not by SQL) and that its activity is **not** migration-induced.

The migration window was therefore **not write-quiescent**; that is an accurate operational observation
about a live environment, not a migration defect, and it caused **no preservation-critical data loss or
unauthorised mutation**.

**Classification: D-3 — NON-BLOCKING / OPERATIONAL OBSERVATION.**

---

## 14. Storage preservation

| Check | PRE | POST (live) | Verdict |
|---|---|---|---|
| `documents` bucket exists | yes | **`documents`** present (only bucket) | ✅ |
| Bucket remains private | `public = f` | **`public = f`** | ✅ |
| Objects in `documents` | 58 | **58** | ✅ |
| Objects in all buckets | 58 | **58** | ✅ |
| `file_size_limit` | **2,097,152** (confirmed from the pre-apply dump's `storage.buckets` COPY row) | **10,485,760** | ⚠ **intended (D-2)** — the two authorised bucket-alignment migrations raise the ceiling to 10 MiB |
| Object-level exposure | — | `storage.objects` RLS enabled; its only policies are the four `d32_documents_*` policies granted to `{authenticated}`; **no `anon` policy, no public policy** | ✅ |

No object was uploaded, deleted, renamed or modified by this verification, and no unexpected public
exposure exists.

---

## 15. O-1 — `anon` grants investigation

| Check | Independent finding |
|---|---|
| Which tables carry `anon` DML grants | **Exactly three**: `activity_clarifications`, `insight_concurrency_leases`, `insight_rate_limit_buckets` — 4 privileges each = **12 grant rows**, and these are the **only** `anon` grants in `public` | [I] |
| RLS state of those tables | all three **RLS-enabled**; `activity_clarifications` has 4 policies (all `{authenticated}`), the other two have **0 policies** | [I] |
| Any anonymous policy anywhere? | **0** policies reference `anon`/`public` in the whole `public` schema | [I] |
| Can `anon` actually read protected data? | Live probe inside a read-only transaction: `SET LOCAL ROLE anon; SELECT count(*) FROM public.activity_clarifications;` → **`anon`, 0 rows** | [I] |
| Can `anon` write? | Catalog-deterministic: with RLS enabled and **no permissive policy applicable to `anon`**, PostgreSQL denies all INSERT/UPDATE/DELETE. **No write probe was attempted** (a write attempt is outside the read-only boundary) | [I]/[L] |
| Grant counts (public schema) | `anon 12`, `authenticated 509`, `service_role 1041`, `postgres 1050` — exactly the reported post-migration figures | [I] |

**Evidence limitation stated honestly [L]:** all three tables are currently **empty (0 rows)**, so the
0-row `anon` probe is *consistent with* RLS filtering but is not by itself discriminating (an empty table
returns 0 rows for any role). The conclusive evidence is the catalog state — RLS enabled with **no
permissive policy for `anon`** — which PostgreSQL enforces deterministically. **No actual anonymous access
was demonstrated**, and the grants are inert.

**Classification: O-1 — NON-BLOCKING SECURITY HARDENING OBSERVATION** (an owner decision on a future
`REVOKE`-hardening migration; **not** performed and **not** performed here).

---

## 16. Backup / PITR status, deployment boundary, repository state

**Backup / PITR [I]/[L]:** SQL-visible evidence shows `archive_mode = on` with the platform's
`/usr/bin/admin-mgr wal-push` archive command and `wal_level = logical` — i.e. the platform's WAL archive
mechanism is active at the instance level. **Whether project-level managed backups / PITR are enabled is a
Supabase control-plane property that is not observable through SQL**, so Cline's "no managed backup/PITR"
statement is **[C]**, not independently confirmed (and not contradicted). This is the previously accepted
**B2′** infrastructure limitation with owner decision **P4** open; nothing was enabled, configured or
changed by this verification. The pre-apply logical dump (sha256 `523f4712…` [I]) remains the only
pre-migration restore point and lives in `/tmp` (not durable — [E]).

**Deployment boundary [I]/[L]:**
* Repository: `HEAD` is still the frozen release SHA `375a48dc1b9e9cfd74090bbf747554ae997acb59` on
  `p8-release-reconciled`; no new commit, tag or push; the only tracked modifications are the two
  **pre-existing** ones (`.gitignore`, `frontend/App_.js`, mtimes 2026-09-23 / 2026-09-28, untouched).
* The only repository artefact added by the P3 task is its report
  (`docs/audit/cline/CT-FINAL03-P3-SUPABASE-001-20261003.md`, mtime 2026-10-03 04:40:20).
* No file in the repository was written after 04:45 (verified by a write-window scan) other than this
  verification's own report.
* Render / Vercel deployment state and service restarts are **not observable from this host** — that part of
  the boundary rests on Cline's confirmation [C]; no deploy tooling was invoked by this verification [I].

---

## 17. Tests / checks performed

All production checks were **read-only**, each in a session whose first statement was
`SET default_transaction_read_only = on` (re-verified in-session: **`on`**). The Supavisor pooler does not
forward `PGOPTIONS`, so the setting was applied **in-session**; unlike the implementation pass, **no
destructive DDL probe was attempted** — enforcement is asserted from the session setting plus the absence of
any write statement in any query.

| # | Check | Result |
|---|---|---|
| 1 | Session read-only enforcement | `SHOW default_transaction_read_only` → **on** [I] |
| 2 | Target identity (ref in username, pooler region, port, DB, version, recovery) | as §3 [I] |
| 3 | Migration history (count/tip/duplicates/tail/pending/applied-not-local) | as §5 [I] |
| 4 | Schema inventory (tables, RLS on/off, policies, FORCE, functions, indexes, triggers, backup tables) | as §6 [I] |
| 5 | Identity of the 3 RLS-disabled tables | exactly the Class-A set [I] |
| 6 | 44 FINAL-03 targets × (exists, RLS, FORCE, policies) + summary | 44/44 RLS-on, 0 FORCE, 4 policies [I] |
| 7 | Group-B policy definitions (name, cmd, roles, USING, WITH CHECK) | as §7 [I] |
| 8 | Policy name-set comparison pre vs post on pre-existing tables | 198 = 198, no drop/rename/add [I] |
| 9 | `anon`/`public` policy count | 0 [I] |
| 10 | Class-A tables: RLS off + 0 policies | ✅ [I] |
| 11 | 16 new tables present, RLS on, anon policies 0 | ✅ [I] |
| 12 | `emission_factors` count + full 13-column PRE vs POST comparison (dump-driven) | 7,049 / identical digests [I] |
| 13 | `emission_factors` column inventory (17 = 13 + 4) and the adding migration | ✅ [I] |
| 14 | Per-table PRE vs POST row counts for the 7 org-linked tables + factors + orgs + members + storage.buckets | all identical [I] |
| 15 | Full 79-column PRE vs POST comparison of `document_processing_queue` | 1 row, lease metadata only [I] |
| 16 | Migration-source scan of all 98 migration files for `document_processing_queue` | 0 references [I] |
| 17 | Organisations / accounts / memberships / demo users / sessions / tokens | as §11 [I] |
| 18 | Storage: bucket privacy, object counts, object policies | as §14 [I] |
| 19 | `anon` grants inventory + live anon SELECT probe under RLS | 12 grants / 0 rows [I] |
| 20 | Role attributes (`anon`/`authenticated` not BYPASSRLS; `service_role` BYPASSRLS) | ✅ [I] |
| 21 | WAL/archive settings; repo state; write-window scan | as §16 [I] |

**Skipped / not performed (by boundary):** any write, DDL or migration; any worker start/stop; any Render or
Vercel action; any storage mutation; any live application/browser acceptance; any change to O-1 grants;
`supabase` CLI was not run.

---

## 18. Findings

| ID | Class | Finding | Evidence |
|---|---|---|---|
| **F-1** | **INFORMATIONAL** (documentation) | The baseline "101 org-linked" figure is inconsistent with its own components (sum = **102**). The ratified package §B.3 already flagged the ±1 for settlement at cutover; this re-measure settles it: **102**, matching production on all seven components. **No data discrepancy.** | §12 [I] |
| **F-2** | **NON-BLOCKING / OPERATIONAL** | D-3 confirmed as a live **external** application worker: 1 of 11 queue rows, only `lock_token`/`locked_at`/`updated_at` changed; no row inserted/deleted; no migration references the table; and a **new re-lease at 2026-10-03 05:44:04 UTC** shows the worker is still active **after** the migration window. The migration window was not write-quiescent. No preservation-critical data lost or altered. | §13 [I] |
| **F-3** | **NON-BLOCKING SECURITY HARDENING OBSERVATION** | O-1: `anon` holds 12 inert DML grants on three new RLS-enabled tables; **0** `anon`/`public` policies exist; the live `anon` probe returns 0 rows; fail-closed is guaranteed by catalog state (no permissive policy for `anon`). **No actual anonymous access demonstrated.** Owner decision required for any `REVOKE`-hardening migration — not performed. | §15 [I] |
| **F-4** | INFORMATIONAL (expected) | D-1: whole-row factor fingerprint change is fully explained — the applied `20261010000000_p17a…` adds exactly four columns to `emission_factors`; the 13-column row set is **byte-identical** (my canonical sha256 `e0228472…` on both sides, 7,049 rows, `diff = 0`); no factor row created/changed/deleted. | §10 [I] |
| **F-5** | INFORMATIONAL (intended) | D-2: `documents.file_size_limit` 2,097,152 → 10,485,760 is the authorised Storage Step-2 alignment; `public = false` unchanged; 58/58 objects intact. PRE value independently confirmed from the pre-apply dump. | §14 [I] |
| **F-6** | INFORMATIONAL (auth activity) | `last_sign_in_at` advanced to 2026-10-03 ~05:37–05:38 UTC and `auth.sessions`/`refresh_tokens` are 28/51 (reported 26/48). Auth-service metadata advanced by live sign-ins; identities, confirmations and memberships unchanged. Cline's "unchanged" figures were time-bound, not wrong. | §11 [I] |
| **F-7** | INFORMATIONAL | The batch's single pre-existing-table write (`UPDATE public.staff_roles … WHERE name IN ('admin','system_admin')`) matched **zero rows** on production (only `pe_manager` exists) → **no retained row was modified at all** by the batch. | §12 [I] |
| **F-8** | FINAL-03 / governance note | The release's independent RLS/R1 verification reports were **excluded** from the frozen release by the PO's closed-enumeration reading (previously recorded as N-7 in `CSTR-FINAL03-P2-RECON-VERIFY-001`). Unchanged by this task; a PO decision if a self-defending release is wanted. | prior report [I] |
| **F-9** | LIMITATION | Managed backup/PITR state is not SQL-observable; `archive_mode=on` with the platform WAL-push is visible. B2′ accepted limitation (P4 open). No change attempted. | §16 [I]/[L] |
| **F-10** | LIMITATION | Migration **file bytes** cannot be read back from `supabase_migrations`; content integrity is evidenced by exact version/name correspondence with the frozen release plus the observed outcome matching those files' defined effects. | §5 [I]/[L] |
| **F-11** | LIMITATION | Render/Vercel deployment state and worker restarts are not observable from this host; that boundary rests on Cline's confirmation. | §16 [C]/[L] |

**BLOCKING findings: NONE.**

---

## 19. Limitations

1. **No server-side migration content digest** (F-10): the applied bytes were not verifiable from the
   database; correspondence is by version/name plus outcome.
2. **Backup/PITR not SQL-observable** (F-9): the B2′ limitation stands as recorded; not independently
   re-confirmed and not changed.
3. **Anon write denial is catalog-inferred**, not write-tested (deliberate: no production writes) (F-3).
4. **The anon SELECT probe is non-discriminating because the three tables are empty** (F-3).
5. **The pre-migration comparison data source is the P3 pre-apply dump and the pre-apply policy capture**
   — both produced by the implementation pass. The *comparisons* are CoStrict's, but the captures are not
   independently created; the surviving independent pre-state records (the ratified evidence pack of
   2026-10-02: 47-table RLS list, 7,049 factors, 198 policies, 58 objects, 71 migrations, component counts)
   were used to cross-check them, and they agree in every case.
6. **The worker (D-3) is still active**: values observed now differ from those recorded in the
   implementation report, so the report's D-3 numbers are time-bound snapshots. The row is not frozen.
7. **Auth activity metadata** advanced after the migration (F-6); such values cannot be "preserved" by
   nature.
8. **`staff_roles` PRE state is not in the dump** (not part of the retained footprint); the no-op finding is
   established from the live single-row state plus the migration's WHERE clause.
9. **No live application/browser acceptance** was performed (out of scope); the schema has not been exercised
   by a freshly deployed application.
10. **The 3 RLS-disabled Class-A tables remain a recorded security posture decision**, unchanged by the
    migration and untouched here.

---

## 20. Final verdict

All conditions of the acceptance criteria were independently met:

| # | Condition | Result |
|---|---|---|
| 1 | Correct production project verified | ✅ `pvwiojoyaqywtydzcpbg` (in username), pooler `eu-west-2`, PG 17.6, production data identity |
| 2 | Migration count/tip/order correct | ✅ 98 applied, tip `20261029000000`, 0 duplicates, 0 newer |
| 3 | 27 intended migrations applied | ✅ 71 (PRE, from the pre-apply dump) → 98; **set-identical** to the frozen release's migration files; 0 pending; 0 unexpected |
| 4 | Schema result independently verified | ✅ 150 tables / 68 functions / 411 indexes / 95 triggers / 1 `backup*` table |
| 5 | 150 public tables verified | ✅ |
| 6 | 147 RLS-enabled / 3 RLS-disabled verified | ✅ |
| 7 | Remaining RLS-disabled tables are exactly the three Class-A tables | ✅ `business_hours`, `emission_factors`, `sla_definitions` (0 policies each) |
| 8 | All 44 FINAL-03 RLS targets verified | ✅ 44/44 RLS-on (targets extracted from the frozen migrations) |
| 9 | Fail-closed policy state verified | ✅ 41 Group-A tables + `staff_workload` = 0 policies; 0 anon/public policies |
| 10 | Group B policies preserved | ✅ 3 + 1 retained policies, correct CMD/roles/expressions; legacy policy name set unchanged (198 = 198) |
| 11 | `staff_workload` verified RLS + zero policies | ✅ |
| 12 | FORCE RLS remains 0 | ✅ 0 tables with `relforcerowsecurity` |
| 13 | Anonymous/public policy count is 0 | ✅ and a live `anon` probe sees 0 rows |
| 14 | Emission-factor count remains 7,049 | ✅ |
| 15 | Original emission-factor data verified preserved | ✅ 13-column row set byte-identical PRE vs POST (identical canonical sha256, `diff = 0`), 0 duplicates, 4 new columns additive |
| 16 | Two organisations preserved | ✅ same ids, names, active flags |
| 17 | Two owner-created accounts preserved | ✅ same ids, confirmed, not banned |
| 18 | Organization memberships preserved | ✅ 2 rows, ids/roles/orgs unchanged |
| 19 | Org-linked baseline preserved (accounting for worker-only lease changes) | ✅ **102** per-table exact match (the "101" citation is a documentation artefact — F-1); only 1 queue row's lease metadata changed, worker-driven (F-2) |
| 20 | 58 storage objects preserved | ✅ 58/58, bucket still private, no anon policy |
| 21 | D-3 causes no unexplained data loss or unauthorised mutation | ✅ 11/11 rows, ids identical, lease metadata only, no migration reference |
| 22 | O-1 does not permit actual anonymous access | ✅ fail-closed; 0 anon policies; live probe 0 rows; inert grants only |
| 23 | No unexpected production change discovered | ✅ all deltas are additive/intended (16 tables, 33 policies, 4 columns, RLS enablement, bucket ceiling) and the residual changes are the live worker and auth activity |
| 24 | No production remediation was required during verification | ✅ none performed, none needed |

> **CSTR-FINAL03-P3-SUPABASE-VERIFY-001 — INDEPENDENTLY VERIFIED — PRODUCTION MIGRATION, SCHEMA, RLS AND PRESERVATION ACCEPTED**

**READY FOR PO AUTHORIZATION OF MANUAL RENDER AND VERCEL DEPLOYMENT**

Explicit boundary of this verdict: it verifies the **production database migration, schema, RLS configuration
and data preservation** only. It does **not** authorize or perform any Render/Vercel deployment, worker
start, environment/secret change, O-1 grant remediation, backup configuration change, or live application
acceptance, and it does **not** declare FINAL-03 cutover acceptance. The next decision belongs to the Product
Owner.
