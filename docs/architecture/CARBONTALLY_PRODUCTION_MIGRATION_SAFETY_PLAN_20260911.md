# CarbonTally — Production Migration Preparation & Safety Plan

**Prompt Ref:** `CT-PROD-MIGRATION-PREP-20260911-001` · **Date:** 2026-09-11 · **Mode:** READ-ONLY
**Repository:** CarbonTally · branch `main` · **HEAD/Release-1:** `daad396523ac693352cc2f4ebb7fc58814a9e60b` (unchanged)
**Production:** project `CarbonTally` · ref `pvwiojoyaqywtydzcpbg` · org `pfurlzwxdtvyljnahlnx` · active
**Predecessors:** `CT-PROD-SUPABASE-RECON-20260911-001` · `-002` · Deployment Readiness 20260911

> This operation **prepared and safety-checked** a migration plan. **No migration was applied, no DDL/DML
> was executed, nothing in production was modified, and no migration file or application code was
> changed.** Every production interaction was an HTTP **GET**.

---

## 1. Current production state (accepted unchanged from RECON-002)

| Fact | Value |
|---|---|
| production active | **yes** (API host resolves; GoTrue `v2.196.0`) |
| effective schema | **≈ migrations 1–21** (through `20260810050000_v3m6_entity_rls`) |
| migrations not represented | **≈32 of 53** |
| Release-1 migrations applied | **none demonstrated** (10 proven absent; 7 unprobeable) |
| `documents` bucket | **absent** (`NoSuchBucket`) |
| D37 `billing_*` family | **absent** (7 tables) |
| `work_item_assignments` | **absent**; legacy `processing_assignments` present |
| DPQ durability columns | **absent** (19 columns) |
| emission factors | **7 049 rows present** → no load required |
| `emission_factors` exposure | anonymous SELECT confirmed (`DR-16`) |
| migration history table | **unreadable through the current GET-only method** |
| RLS/grant inventory | **incomplete** |
| backups/PITR/rollback | **not verified** |

No conclusion above was silently changed.

---

## 2. Objective A — migration-history access (still `UNKNOWN`)

**No safe read-only method exists in this environment.**

| Candidate | Verdict |
|---|---|
| `supabase migration list --linked` | **PROHIBITED** — creates a temporary login role (a mutation). Not run. |
| Direct `psql` → `select * from supabase_migrations.schema_migrations` | **Impossible** — no DB credential/session exists (no password, no `.pgpass`, no CLI token; the only DB-capable credential is the prohibited write-capable service key). |
| PostgREST (publishable key) | **Impossible** — the `supabase_migrations` schema is not exposed. |
| Inference from application behaviour | **Prohibited by §3** — and not used. |

**`PRODUCTION MIGRATION HISTORY = UNKNOWN`.** Consequently the plan below is built from the **effective
schema delta**, with a mandatory history read as runbook step 0 once a read-only credential exists.

---

## 3. Migration inventory and the exact delta

### 3.1 Inventory summary (all 53 repository migrations, mechanical risk scan)

| Band | Migrations | Notes |
|---|---|---|
| 1–8 | `init_schema` + `rc2_*` | base schema, constraints, indexes, RLS, functions, triggers |
| 9–16 | `add_*` (batches, factors, snapshots, logs, events, aliases, DPQ cols, new-table RLS) | all **applied** (object-evidenced) except #16 (RLS/grants only) |
| 17–21 | `v3m1`, `v3m2`, `v3m3`, `v3m5`, `v3m6` | **applied** (17–20 evidenced; 21 RLS-only) |
| **22–53** | **the delta** | **not represented in production** |

### 3.2 History delta vs effective schema delta (Objective C)

* **Migration-history delta:** `UNKNOWN` (history unreadable). **Not asserted.**
* **Effective schema delta (the operative answer):** **migrations 22 → 53 = 32 files.**
* Are any of the 32 already effectively represented? **No.** Every probed discriminator from
  migrations 23, 24, 26, 28, 30–32, 36 and all 10 provable Release-1 migrations is **absent**
  (`42703`/`PGRST205`). The remaining migrations in the band are index/function/trigger/RLS-only and sit
  between proven-absent neighbours; **none can be shown to be applied**.
* **Reverse drift:** none identified. PostgREST hints referenced `processing_assignments`,
  `typing_status`, `conversation_participants` and `staff_profiles` — **all four are created by
  repository migrations**, so they are base-schema tables, not production-only objects.
* **Therefore: effective schema delta = history delta = migrations 22 → 53.** The 32 are **not**
  reducible — each is either provably absent or unprovable, and none may be skipped. (Answer to §5's
  "do not simply say apply all 32": the investigation supports applying all 32, in order; it is **not**
  a shortcut.)

### 3.3 The delta — exact ordered execution set (Objective B)

Flags: **DM** data mutation · **DES** destructive · **RLS** security change · **GR** grants ·
**FN/TR** function/trigger · **REF** reference-data insert · **IDEM** idempotent · **NONIDEM** apply once.

| Order | Migration | Production status | Main changes | DM | DES | RLS | GR | FN/TR | REF | IDEM | Dep. | Recommendation |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|
| 22 | `20260821000000_d20_d15_active_consultant_grant` | implied NOT_APPLIED | active-consultant grant helper + EXECUTE grants | – | – | – | yes | fn | – | yes | 17–21 | apply; verify helper |
| 23 | `20260821010000_d21_white_label_branding` | **NOT_APPLIED** | `organizations.white_label_enabled` | – | – | – | – | – | – | yes | 1–21 | apply; column-only |
| 24 | `20260821020000_d22_processing_work_assignment` | **NOT_APPLIED** | `processing_assignments.entity_id`, `.manual_extraction_batch_id` + 3 FK | – | – | yes | – | – | – | yes | 18 | apply; FK refs must be consistent |
| 25 | `20260822000000_p9_rls_recursion_fix` | implied NOT_APPLIED | replaces recursive RLS helper fns/policies | – | – | **yes** | – | fn | – | yes | 21 | apply; **re-verify isolation at once** |
| 26 | `20260822010000_d27_d19_customer_lifecycle` | **NOT_APPLIED** | `organizations.customer_type`; client lifecycle cols; **3 new tables** + RLS | – | – | yes | – | fn | – | yes | 1–21 | apply; verify new-table RLS |
| 27 | `20260823000000_d32_private_documents_storage` | **NOT_APPLIED** | private-bucket flip + `storage.objects` RLS + **4 UNGUARDED `CREATE POLICY`** | – | – | **yes** | – | – | – | **NONIDEM** | – | apply **once**; bucket first |
| 28 | `20260823010000_d33_evidence_traceability` | **NOT_APPLIED** | snapshot `source_item_id/source_file/source_page`; item `file_id`; evidence fn | – | – | – | – | fn | – | yes | 11 | apply; column-only |
| 29 | `20260824010000_d35_self_service_onboarding` | implied NOT_APPLIED | `auth.users`→`public.users` sync trigger+fn (INSERT is **inside the function**) | – | – | – | – | tr+fn | – | yes | 1–21 | apply; verify trigger |
| 30 | `20260824020000_d37_0_billing_security_and_configurable_subscription` | **NOT_APPLIED** | **billing tables** + RLS/grants + seed plans/config | **yes** | – | **yes** | **yes** | – | **yes** | yes | 1–21 | apply; seed is `ON CONFLICT DO NOTHING` |
| 31 | `20260824030000_d37_master_commercial_billing` | **NOT_APPLIED** | orders/ledger/payments/config + **v2 plan versions** in a `DO` block | **yes** | – | yes | yes | – | **yes** | **NONIDEM** | 30 | apply **exactly once**, straight after 30 |
| 32 | `20260825000000_v3m7_vehicles` | **NOT_APPLIED** | `vehicles` table + RLS + trigger + grants | – | – | yes | yes | tr+fn | – | yes | 1–21 | apply; verify RLS |
| 33 | `20260828000000_v3m8_messaging_unique_participants` | implied NOT_APPLIED | **`DELETE` duplicate `conversation_participants`** + UNIQUE constraint | **yes** | **yes** | – | – | – | – | yes | 1–21 | apply after **counting duplicates** (expect 0) |
| 34 | `20260828010000_v3m8_system_admin_role_model` | implied NOT_APPLIED | guarded `UPDATE staff_roles`; **`DELETE` stray test role + profile (id-scoped)** | **yes** | **yes** | – | – | – | – | yes | 1–21 | apply after confirming the id is absent |
| 35 | `20260828020000_v3m8_pe_manager_role` | implied NOT_APPLIED | inserts `pe_manager` into `staff_roles` | – | – | – | – | – | **yes** | **NONIDEM** | 1–21 | apply once; pre-check for an existing row |
| 36 | `20260829000000_v3m9_durable_automatic_processing` | **NOT_APPLIED** | **19 DPQ columns** (+ indexes) | – | – | – | – | – | – | yes | 15 | apply; additive |
| 37 | `20260831000000_v3m10_org_membership_unique` | implied NOT_APPLIED | UNIQUE index on `organization_members(organization_id,user_id)` | – | – | – | – | – | – | yes | 1–21 | apply after **counting duplicate memberships** (expect 0) |
| 38 | `20260831010000_v3m11_operational_indexes` | implied NOT_APPLIED | 4 operational indexes | – | – | – | – | – | – | yes | – | apply; additive |

| 39 | `20260831020000_audit_activity_immutability` | implied NOT_APPLIED | drops/replaces 10 audit policies + guard fn | – | – | **yes** | – | fn | – | mostly (all DROPs `IF EXISTS`) | 5/16 | apply; **audit semantics change — verify** |
| 40 | `20260831030000_tenant_org_id_not_null` | implied NOT_APPLIED | `assets.organization_id SET NOT NULL` | – | – | – | – | – | – | yes | – | **requires 0 NULL rows in production `assets`** |
| 41 | `20260831040000_consultant_revocation_roles` | implied NOT_APPLIED | revocation role vocabulary + fn + grants | – | – | yes | yes | fn | yes | yes | – | apply; verify vocabulary |
| 42 | `20260902020000_v1_2_dual_origin_workflow` | **NOT_APPLIED** | 6 item columns + 2 FK + 2 CHECK | – | – | – | – | – | – | yes | 24 | apply; additive |
| 43 | `20260902030000_phase5_work_item_assignments` | **NOT_APPLIED** | **new table** `work_item_assignments` + unique idx + 6 CHECK + 2 FK + RLS | – | – | yes | – | – | – | yes | 24, 36 | apply; verify RLS |
| 44 | `20260902040000_phase5_pe_operational_messaging` | **NOT_APPLIED** | conversations/messages columns + **backfill UPDATE** + `SET NOT NULL` on `conversation_kind` | **yes** | – | yes | – | fn | – | yes | 33 | apply; NOT NULL on a fresh column |
| 45 | `20260902050000_phase5_notification_event_key` | **NOT_APPLIED** | `notifications.event_key`/`actor_domain` + UNIQUE idx | – | – | – | – | – | – | yes | – | apply; UNIQUE on a **new** column |
| 46 | `20260903010000_ws4_gate3_4a_item_assignment_foundation` | implied NOT_APPLIED | assignment foundation fns + policies + grants | – | – | yes | yes | fn | – | yes | 43 | apply after 43 |
| 47 | `20260905000000_gate4_actor_provenance` | **NOT_APPLIED** | `calculation_snapshots.performed_by` + FK | – | – | – | – | – | – | yes | 11 | apply; additive |
| 48 | `20260905010000_gate5_t1_automation_provenance` | **NOT_APPLIED** | 3 automation provenance columns | – | – | – | – | – | – | yes | – | apply; additive |
| 49 | `20260905020000_gate5_t6_automation_write_once_guard` | implied NOT_APPLIED | write-once guard fn + trigger | – | – | – | – | fn+tr | – | yes | 48 | apply; verify trigger |
| 50 | `20260906010000_gate6_w1_automation_extracted_output` | **NOT_APPLIED** | `automation_extracted_data` + fn + trigger | – | – | – | – | fn+tr | – | yes | 36, 48 | apply |
| 51 | `20260906090000_p6_1c_consultant_engagement` | **NOT_APPLIED** | 4 engagement columns + 2 CHECK | – | – | – | – | – | – | yes | 1–21 | apply; additive |
| 52 | `20260906100000_p6_2a_consultant_processing_permissions` | **NOT_APPLIED** | 6 `can_*` capability columns | – | – | – | – | – | – | yes | 1–21 | apply; additive |
| 53 | `20260910120000_p6_2d_consultant_provenance` | **NOT_APPLIED** | `consultant_firm_id`, `processing_mode`, provenance cols + FK + CHECK | – | – | – | – | – | – | yes | 42 | apply; additive |

**Ordering is strict `22 → 53`.** Every dependency listed above is satisfied by applying in this order.

### 3.4 Mechanical risk totals for the delta (32 files)

`unconditional DROP` **0** (every DROP carries `IF EXISTS`) · `ALTER … TYPE` **0** · `RENAME` **0** ·
`enum change` **0** · `SET NOT NULL` **2** (one on a freshly added column) · `data mutation`
**8 statements across 6 files** · `RLS/security change` **12 files** · `GRANT/REVOKE` **6 files** ·
`function/trigger` **11 files** · `reference-data insert` **4 files** · `non-idempotent on re-run`
**3 files (27, 31, 35)**.


---

## 4. Objective D — per-migration production risk review

| Risk | Object (migration) | Potential production impact | Could existing production data cause failure? | Required precondition | Post-migration verification |
|---|---|---|---|---|---|
| **DELETE (dedupe)** | `conversation_participants` (33) | removes rows where `a.created_at < b.created_at` for the same (conversation_id,user_id) | Only if duplicates exist. The file header says an audit found none — **that audit was on the dev DB, not production** | count duplicates; expect **0** | row count unchanged; UNIQUE constraint present |
| **DELETE (cleanup)** | `staff_profiles`, `staff_roles` (34) | removes one stray test role + its profile | Only if id `56f5fa09-30d8-43a7-a5be-fdb3fbc93519` exists (unlikely; **no-op if absent**) | confirm the id is absent | id absent afterwards |
| **UPDATE (backfill)** | `conversations.conversation_kind` (44) | sets `'org'` where NULL | No — the column is **created in the same migration**, so it starts NULL and is then backfilled | none | no NULL `conversation_kind` |
| **UPDATE (guarded)** | `staff_roles.permissions` (34) | adds `can_manage_billing` to `system_admin` | No — guarded by `IS DISTINCT FROM 'true'` | a `system_admin` row should exist (no-op if not) | `system_admin` carries the flag |
| **INSERT (reference)** | `billing_plans`, `billing_commercial_config` (30) | seeds 4 plans + commercial config | No — `ON CONFLICT (plan_code, version) DO NOTHING` | none | 4+ plans and config keys present |
| **INSERT (reference, unguarded)** | `billing_plans` v2 (31) | closes the open version and mints a new one | Not on first run; **re-running mints v3+** | apply exactly once | one open version per `plan_code` |
| **INSERT (reference, unguarded)** | `staff_roles.pe_manager` (35) | adds the PE-manager role | Fails if the row already exists | pre-check for an existing `pe_manager` | role present exactly once |
| **SET NOT NULL** | `assets.organization_id` (40) | fails if any NULL exists | **YES — if production `assets` holds tenantless rows** | count NULLs; expect **0** | column is `NOT NULL` |
| **SET NOT NULL** | `conversations.conversation_kind` (44) | fails if NULLs remain | No — fresh column, backfilled in-file | none | column `NOT NULL`, default `'org'` |
| **UNIQUE index** | `organization_members` (37) | fails if duplicate memberships exist | **YES — if duplicate (org,user) memberships exist** | count duplicates; expect **0** | unique index exists |
| **UNIQUE constraints** | `conversation_participants` (33), `notifications.event_key` (45), `work_item_assignments` (43) | constraint creation fails on duplicates | Only (33) can realistically collide with existing rows | duplicate counts = 0 | constraints present |
| **FK additions** | (24), (47), (43), (42/53), (32), (26) | FK validation fails on orphaned values | **Possible** in principle — but the new columns are NULL for existing rows, so validation passes | verify no invalid references | `pg_constraint` present |
| **CHECK constraints** | (24, 26, 42, 43, 51, 53) | validation fails on violating rows | Low — constraints fall mainly on **new** NULL columns (NULL passes a CHECK) | none | constraints present |
| **RLS replacement** | `p9` (25), `audit_activity_immutability` (39) | policies dropped then recreated → a brief window of altered restriction; could **weaken** isolation if a policy is not recreated | Not data-dependent | apply inside a transaction; immediately re-run the negative isolation matrix | every tenant table still blocks cross-tenant access |
| **RLS additions** | `storage.objects` (27), `vehicles` (32), 3 `d27` tables (26), `work_item_assignments` (43) | a new table **without** RLS enabled is a security hole | No | confirm `ENABLE ROW LEVEL SECURITY` ran for each new table | `relrowsecurity = true` for each |
| **Unguarded `CREATE POLICY`** | `storage.objects` (27) | a second application fails ("policy already exists") | No | apply once | 4 policies present |
| **GRANT/REVOKE** | (22, 30, 31, 32, 41, 46) | privilege changes could over- or under-permit | No | review each GRANT after application | expected grants present; **no `anon` write** |
| **Function/trigger replacement** | (22, 25, 26, 28, 29, 32, 41, 44, 46, 49, 50) | behaviour changes in audit/provenance/automation | No | apply in order | each function/trigger exists and is active |
| **New-object assumptions** | (26), (32), (43) | none — `CREATE TABLE IF NOT EXISTS` on **new** tables | No | none | tables + RLS present |

**No migration was fixed or altered.** Every risk above is a precondition for the *execution* operation.


---

## 5. Objective E — billing schema compatibility

| Item | Release-1 expectation (repository-authoritative) | Evidence | Production |
|---|---|---|---|
| `usage_tracking` table | exists | `00000000000000_init_schema.sql:1480` | **present** (base schema) |
| `usage_tracking.usage_month` | **`DATE`** | `init_schema.sql:1484` → `usage_month DATE` | **`DATE`** (base schema applied); definitive confirmation needs a DB session |
| `usage_tracking.usage_date` | `DATE` | `init_schema.sql:1483` | same |
| `usage_tracking` uniqueness | **`UNIQUE (organization_id, usage_month)`** | `init_schema.sql:1492` | same (base schema) |
| D6 write path | `INSERT INTO usage_tracking (organization_id, usage_date, usage_month, ai_files_processed) VALUES ($1, $2::timestamptz, date_trunc('month',$2::timestamptz)::date, $3)` | `backend/data/billing.py:851-857` | Release-1 code |
| `ON CONFLICT` used? | **NO** — no `ON CONFLICT` exists anywhere in the billing code | `grep -rn 'on conflict' backend/{data,services,domain}/billing.py` → **no matches**; the only `usage_tracking` statements are `data/billing.py:851` (INSERT) and `services/billing.py:202` (SELECT) | Release-1 code |
| Billing tables required | `customer_subscriptions` (init), `billing_plans`, `billing_commercial_config`, `billing_credit_ledger`, `billing_orders`, `billing_payment_records`, `billing_storage_usage`, `billing_idempotency_keys` | migrations 30, 31 | only `customer_subscriptions` + `usage_tracking` present; the **7 `billing_*` tables absent** |
| Seed idempotency | plans + config seeded **in-migration** | 30 (`ON CONFLICT … DO NOTHING`), 31 (versioned `DO` block) | n/a (not applied) |
| Allowances / entitlement | `billing_credit_ledger`, `billing_commercial_config` | 30, 31 | **absent** |

### 5.1 NEW RISK — `DR-19`: the D6 monthly charge cannot be written twice in one calendar month

`usage_tracking` is **UNIQUE on `(organization_id, usage_month)`**, while
`backend/data/billing.py:851` performs a **plain `INSERT` with no `ON CONFLICT`**. Once the Release-1
backend is deployed:

* the **first** approval in a calendar month for an organisation inserts a row and succeeds;
* **any second approval in the same month for the same organisation raises a unique violation
  (`23505`)** → the D6 charge path errors.

This is a **pre-existing correctness risk in Release-1 application code**, **not** caused by any
migration, and it is **not fixed here** (out of scope). It is recorded because it becomes reachable the
moment the delta is applied and the backend is deployed. Recommend a read-only post-migration check of
`usage_tracking` behaviour and a separate decision on the fix (e.g. an upsert that accumulates
`ai_files_processed`). **`DR-19` is a billing-path first-customer blocker, not a migration blocker.**

**No billing row was created and no billing transaction was performed.**

---

## 6. Objective F — DR-16 investigation (read-only)

| Question | Finding |
|---|---|
| Anonymous SELECT possible today? | **YES — confirmed.** `GET /rest/v1/emission_factors?select=id&limit=1` → `200` with row data; `Prefer: count=exact` → `206`, `content-range: 0-0/7049`. All **7 049** rows are exposed. |
| Is authenticated SELECT expected? | Yes — the factor library must be readable by authenticated application users (factor matching/mapping). |
| Is the table likely RLS-protected? | **Almost certainly NOT.** A repository-wide scan found **no `ENABLE ROW LEVEL SECURITY` and no `CREATE POLICY` and no `GRANT`/`REVOKE` referencing `emission_factors`** in any of the 53 migrations. If RLS were enabled with no policy, `anon` would receive **0 rows** (as it does for every other tenant table). Because it receives **7 049**, the most probable explanation is that **RLS is disabled on this table in production**. |
| Evidence of anonymous **write** capability? | **None obtained.** No write verb was issued (prohibited). However, **if** RLS is disabled *and* Supabase's default `anon` table privileges are present, `INSERT`/`UPDATE`/`DELETE` would also be possible. This cannot be excluded, and it **cannot be tested within the read-only boundary**. |
| Which Release-1 migration/policy should govern it? | **None exists.** No migration in the Release-1 set grants or restricts access to `emission_factors`; the table originates in `00000000000000_init_schema.sql` (which also does not enable RLS on it). |
| Comparison with other tables | Every other probed tenant table (`organizations`, `organization_members`, `notifications`, `conversations`, `usage_tracking`, `customer_subscriptions`, `manual_extraction_items`, `suppliers`, `facilities`, `factor_aliases`, `activity_categories`, `document_types`) returns `200 []` to anon → RLS-enforced. **`emission_factors` is the sole exception.** |

### Classification (per §8)

> **`CONFIRMED SELECT exposure — RLS almost certainly DISABLED (no repository policy exists), and anonymous WRITE capability CANNOT BE EXCLUDED but is UNTESTED.`**

This is *not* "SELECT exposure only" in the strong sense (that would require positive evidence that
writes are denied) and *not* "confirmed writable" (no write was tested). It is the evidence-supported
middle classification, and it is a **P1 security item** requiring Supabase-console or read-only-DB
verification. **No policy was created, altered or dropped.**


---

## 7. Objective G — backup / PITR readiness

**`UNKNOWN — requires Supabase console verification`.**

| Item | Finding |
|---|---|
| Supabase backup configuration | **No backup configuration exists anywhere in the repository.** No `backup`/`pitr` keys in `supabase/config.toml` or `e2e/environment/supabase/config.toml`. |
| PITR enablement | **UNKNOWN** — Supabase plan-dependent, configured in the console, not readable from here. |
| Recovery / restore procedure | **NOT DEFINED** in the repository. The only "backup" material is **local development** material: `backups/*.dump`, `backups/seed.sql`, `backups/00000000000000_init_schema.sql`, `backend/carbon_tally_backup*.sql`, `local_backups/**`, plus a tracked `docs/audit/cline/CARBONTALLY_DEVELOPMENT_DATABASE_BACKUP_REPORT.md`. **None of it is a production backup.** |
| Snapshot creation | **Not performed** — creating a snapshot is not provably read-only, so per §9 it is reported as a **prerequisite** instead. |
| Can recovery be independently verified? | **NO** — no read-only API exposes backup/PITR status. |
| Has rollback been rehearsed? | **NO** evidence of any rehearsal. |

**This is the single most important precondition for the migration operation**, because the delta is
**forward-only** (§10) and ~32 migrations deep.

---

## 8. Objective H — proposed execution runbook (NOT EXECUTED)

**Step 0 — obtain a genuinely read-only DB credential** (read-only role, or the project password
supplied out-of-band) and complete the **read-only reconciliation** that is still outstanding:
`supabase_migrations.schema_migrations`, per-table RLS flags/policies, grants, and the exact
precondition counts in §8.1.

**Step 1 — backup / recovery confirmation (HARD GATE).** Confirm in the Supabase console that
backups/PITR are enabled and note the recovery point; record the restore procedure and the owner.
**Do not proceed if this cannot be confirmed.**

**Step 2 — production health confirmation.** `/health` (FastAPI) and `/auth/v1/health` (GoTrue) OK;
confirm no in-flight maintenance.

**Step 3 — precondition counts (must all be as expected).**
| Check | Expected | Purpose |
|---|---|---|
| `select count(*) from assets where organization_id is null` | **0** | gate for migration 40 |
| duplicate `organization_members(organization_id,user_id)` | **0** | gate for 37 |
| duplicate `conversation_participants(conversation_id,user_id)` | **0** | gate for 33 |
| `staff_roles` row id `56f5fa09-30d8-43a7-a5be-fdb3fbc93519` | **absent** | gate for 34 |
| `staff_roles` row named `pe_manager` | **absent** | gate for 35 |
| `billing_plans` row count | **0** | confirms 30/31 not previously applied |
| `documents` bucket exists | **yes (created beforehand)** | gate for 27 |

**Step 4 — apply the delta in exact order 22 → 53**, in **blocks**, each in a transaction:
`22–26` · `27` (bucket-dependent, once) · `28–29` · `30–31` (together, once) · `32–36` · `37–40`
(precondition-gated) · `41–46` · `47–53`.
*Never re-run 27, 31 or 35. Never apply a migration out of order.*

**Step 5 — per-block verification.** After each block: confirm the objects from §3.3 exist
(`information_schema.columns`, `pg_constraint`, `pg_indexes`, `pg_proc`, `pg_trigger`).

**Step 6 — critical schema checks.** `usage_tracking.usage_month` is `date`; `notifications.event_key`
is unique; `organization_members` unique index; `assets.organization_id` NOT NULL;
`work_item_assignments` present; the 7 `billing_*` tables present; DPQ durability columns present; all
10 Release-1 provable columns now present.

**Step 7 — RLS / security checks.** RLS enabled (`relrowsecurity = true`) on **every** new table and on
every tenant table; re-run the negative isolation matrix (Customer A→B, Client A→B, Consultant A→B,
Consultant A→B's client, PE A→B, PE→prohibited document, Viewer→write, Member→admin, Staff→Staff Admin,
Staff Admin→System Admin, Customer/PE→internal ops); **verify no `anon` capability anywhere**, and resolve
`DR-16`.

**Step 8 — billing checks.** The 7 `billing_*` tables and their constraints; `billing_plans` seeded;
`billing_commercial_config` seeded; `/api/v3/commercial/entitlement/{org}` fail-closed behaviour; and
**the `DR-19` monthly-charge behaviour**.

**Step 9 — storage checks.** `documents` bucket exists and is **private**; the 4 `d32` storage policies
exist; signed-URL access works through the API only.

**Step 10 — application smoke tests** (only after the backend is deployed in a **separate** operation):
health, auth, one organisation read, one upload→extract→map→calculate→approve path on a scratch record,
and the accompanying D11 notification and D6 charge.

**Step 11 — stop / abort criteria:** see §9.

**Step 12 — post-migration validation** and **rollback/recovery**: see §10.

### 8.1 Read-only items still outstanding before execution (must be closed)

1. `supabase_migrations.schema_migrations` contents (history).
2. Per-table RLS flags, policy definitions, `USING`/`WITH CHECK` expressions.
3. Grants/privileges for `anon`, `authenticated`, `service_role`.
4. The §8 Step-3 precondition counts (production data).
5. `emission_factors` RLS state and anonymous write capability (`DR-16`).
6. Backup/PITR status (§7).


---

## 9. Migration stop criteria (hard STOP conditions)

If **any** of the following is observed at any point, **stop immediately and do not continue**:

1. **Migration history conflicts** with the expected state (recorded history contradicts the effective
   schema established in RECON-002) → stop and re-plan.
2. **A migration would drop or rename production data.** (The delta contains **no** unconditional DROP,
   no `ALTER TYPE` and no RENAME — any such statement found at execution time is a stop.)
3. **Existing production data violates a new constraint** — in particular any non-zero result in the
   §8 Step-3 precondition counts (NULL `assets.organization_id`, duplicate memberships, duplicate
   conversation participants).
4. **A migration is non-idempotent** and has already been applied (27, 31, 35).
5. **Backup / PITR cannot be confirmed** (§7). *This is the primary gate.*
6. **RLS would become weaker** — a table left without RLS, a policy not recreated after a
   `DROP POLICY`, or any new `anon` capability.
7. **The billing migration has unexpected data effects** (e.g. `billing_plans` unexpectedly populated,
   or the versioned `DO` block would mint an unintended version).
8. **A migration requires manual production data transformation** that has not been authorised.
9. **Any destination-object collision** is detected before application (a delta object already exists
   with a different structure).
10. **`emission_factors` anonymous write capability is confirmed and unresolved** (`DR-16`).

**Issues discovered under these criteria are to be documented, not resolved, by this operation.**

---

## 10. Rollback / recovery reality (Objective H.12)

| Layer | Rollback | Truth |
|---|---|---|
| Git | revert `daad396` | **does NOT reverse any database migration** |
| Backend (Render) | redeploy previous build | loses the D6 billing fix; separate operation |
| Frontend (Vercel) | instant rollback | unrelated to schema |
| **Migrations** | **NO DOWN-MIGRATIONS EXIST** | the 32 migrations are **forward-only**; `DROP … IF EXISTS` guards exist for indexes/policies/functions, but there is **no down script for any migration**, and later migrations depend on earlier ones → **a partially applied delta cannot be rolled back by the tooling** |
| Billing | ledger is append-only | reversals must go through the commercial API, never ad-hoc SQL |
| **Data** | restore from backup/PITR | **PITR status `UNKNOWN`** (§7) → **data rollback currently UNVERIFIED** |

**True database rollback is therefore impossible with the current tooling.** The only recovery path is
a **verified backup/PITR restore**, which is why Step 1 is a hard gate. A Git revert must never be
presented as reversing a migration.

---

## 11. Blocker matrix (migration-preparation view)

| ID | Finding after this operation | Severity | Blocks migration? | Blocks deployment? | Blocks first customer? |
|---|---|---|---|---|---|
| **DR-20 (NEW)** | **Backup/PITR/restore `UNKNOWN`; no rollback path for a 32-migration forward-only delta** | **P0** | **YES (hard gate)** | YES | YES |
| **DR-21 (NEW)** | **Read-only DB reconciliation still outstanding** — recorded history, RLS flags/policies, grants and the six §8 Step-3 precondition counts | **P0** | **YES** | YES | YES |
| **DR-19 (NEW)** | D6 charge cannot be written twice per month (UNIQUE + plain INSERT, no `ON CONFLICT`) | **P1 (correctness)** | No | YES | YES (billing path) |
| **DR-16** | `emission_factors` anonymous SELECT confirmed; RLS almost certainly disabled; anonymous write untested | **P1 (security)** | No | No | YES |
| DR-01 / DR-17 / DR-18 | Confirmed large schema delta — **now fully characterised and correctly ordered** | **P0/P1** | YES | YES | YES |
| DR-02 | **Downgraded** — factors present (7 049); residual = repository packaging of the DEFRA source | P2/P3 | No | No | No |
| DR-08 | `documents` bucket absent — also a **migration-27 dependency** | **P1** | **YES (blocks 27)** | YES | YES |
| DR-04 / DR-05 / DR-09 | secrets/env · frontend build config · OCR binaries | P0/P1 | No | YES | YES |
| DR-13 | Forward-only migrations / no rollback | **P1** | YES (raises risk) | YES | YES |
| DR-03 | History ≠ schema | P1 | YES | YES | YES |
| DR-06 / 07 / 12 / 02b / 14 | frontend fallbacks · CORS · seed hygiene · repo hygiene · P6-2F evidence | P2/P3/E | No | No | No |

**Delta quality:** the plan itself is **technically sound and completely characterised** — 0
unconditional drops, 0 `ALTER TYPE`, 0 renames, 0 enum changes, every DROP `IF EXISTS`, only 3
non-idempotent files, and **every** data-mutating statement identified with a precondition. **The
blockers are safety prerequisites, not plan defects.**


---

## 12. Required final decision (§12)

**Q1 — Can the exact production migration delta now be established?**
**YES for the effective-schema delta; NO for the history delta.** The **effective schema delta is
migrations 22 → 53 (32 files)**, fully enumerated, ordered and characterised. The **migration-history
delta remains `UNKNOWN`** (no read-only access to `supabase_migrations.schema_migrations`).

**Q2 — Which migrations must be executed?**
**All 32, in order 22 → 53** (§3.3). None can be shown to be already applied and none may be skipped.
Notably: 27 (bucket-dependent, once), 30+31 (billing, together, once), 33/34 (data deletes),
37/40 (data-precondition-gated), 42–46 and 47–53 (Release-1 workflow/provenance).

**Q3 — Are any migrations unsafe or require preconditions?**
**None is intrinsically unsafe**, but **six require verified preconditions**: 27 (bucket must exist),
30–31 (apply once, together), 33 (duplicate count 0), 34 (stray role id absent), 35 (`pe_manager`
absent; bare INSERT), 37 (duplicate memberships 0), 40 (`assets.organization_id` NULLs = 0).

**Q4 — Does any migration modify production data?**
**YES — 6 files / 8 statements:** 30 and 31 (reference-data inserts: plans, commercial config),
33 (`DELETE` duplicate conversation participants), 34 (`DELETE` stray test role + profile; guarded
`UPDATE` of `staff_roles`), 35 (`INSERT` `pe_manager` role), 44 (`UPDATE` backfill of a brand-new
column). No `UPDATE`/`DELETE` targets pre-existing business data other than 33 and 34.

**Q5 — Does any migration alter RLS/security semantics?**
**YES — 12 files.** Most are additive (enable RLS on new tables; add policies); **25 (`p9`) and 39
(audit immutability) replace existing policies/functions**, and 27 adds unguarded storage policies;
6 files contain `GRANT`/`REVOKE`. **None is expected to weaken isolation, but each must be verified
immediately after application.**

**Q6 — Is `emission_factors` exposure SELECT-only, potentially writable, or UNKNOWN?**
**`CONFIRMED SELECT exposure; RLS almost certainly disabled; anonymous write capability UNTESTED and
cannot be excluded.`** No repository migration enables RLS or defines any policy for this table, and it
is the only probed table that returns rows to the anonymous role.

**Q7 — Is backup/PITR verified?**
**NO — `UNKNOWN`, requires Supabase console verification.** No backup/PITR configuration or restore
procedure exists in the repository, and no read-only API exposes it.

**Q8 — Is a safe recovery/rollback strategy established?**
**NO.** Migrations are **forward-only with no down-scripts**; a Git revert does not reverse database
state; a partially applied delta is **not recoverable by tooling**; the only recovery path is a
backup/PITR restore whose existence is unverified.

**Q9 — Is production safe to modify?**
**NOT YET.** The *plan* is sound, but **backup/rollback verification (DR-20)** and the **read-only
reconciliation incl. precondition counts (DR-21)** are missing, and the `documents` bucket — a migration
dependency — does not exist.

**Q10 — Can the Product Owner authorize a separate migration-execution operation?**
**Not yet.** The PO may authorize a **prerequisite operation** (read-only DB reconciliation + backup/PITR
confirmation + `documents` bucket creation + `DR-16` verification), after which a **separate**
migration-execution operation can be considered. **No migration may be applied under this
authorization.**

---

## 13. Mandatory no-change confirmation

```text
Repository source modified: NO
Tests modified: NO
Migrations modified: NO
Git commit created: NO
Git push performed: NO
Production database altered: NO
Production migrations applied: NO
Production data created: NO
Emission-factor data loaded: NO
Demo data migrated: NO
Production users created: NO
Production organisations created: NO
Production subscriptions created: NO
Production storage modified: NO
Production RLS modified: NO
Production Auth modified: NO
Production deployment performed: NO
Secrets changed: NO
```

*Only documentation files were written (this plan and the matching prompt-history record). No migration,
DDL, DML, GRANT, storage, Auth or configuration action was taken. Every production interaction was a
read-only HTTP GET.*

---

## FINAL VERDICT

## `NOT READY — SAFETY PREREQUISITES MISSING`

The migration plan is **complete, correctly ordered and risk-reviewed**; the blockers are **safety
prerequisites**, not plan defects: **backup/PITR and rollback unverified (DR-20)**, **read-only
reconciliation and precondition counts outstanding (DR-21)**, the **`documents` bucket absent
(DR-08 blocks migration 27)**, and the **`emission_factors` exposure (DR-16)** unresolved. Once these
are closed, a **separately authorized** migration-execution operation can be proposed. Also recorded for
the record: **`DR-19`** (D6 monthly-charge correctness risk in Release-1 code, not a migration defect).

