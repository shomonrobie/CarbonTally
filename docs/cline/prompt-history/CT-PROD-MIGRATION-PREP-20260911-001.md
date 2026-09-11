# CT-PROD-MIGRATION-PREP-20260911-001

**Prompt Ref:** `CT-PROD-MIGRATION-PREP-20260911-001` · **Datetime:** 2026-09-11
**Response Ref:** `CT-PROD-MIGRATION-PREP-20260911-001-R1`
**Mode:** READ-ONLY migration preparation & safety gate (no migration applied)
**Repository:** CarbonTally · branch `main` · **HEAD/Release-1** `daad396523ac693352cc2f4ebb7fc58814a9e60b`
**Primary artifact:** `docs/architecture/CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md`
**Final verdict:** `NOT READY — SAFETY PREREQUISITES MISSING`

---

## 1. Prompt (faithful summary)

The PO reviewed `CT-PROD-SUPABASE-RECON-20260911-002` and authorized **ONE bounded, READ-ONLY
operation**: prepare and safety-check the production migration plan and establish whether production is
safe to modify. Prohibited: applying migrations, `supabase db push`, migration up/down, any DDL/DML/
GRANT/REVOKE, RLS/Auth/storage/bucket changes, loading factors, creating users/organisations/
subscriptions, modifying production configuration, Render/Vercel deploys, commit, push, and any change
to application code, migration files or E2E fixtures. The production **service key remained
prohibited**. Objectives: (A) establish migration history safely; (B) build the exact migration delta
over all 53 migrations; (C) distinguish history delta from effective schema delta; (D) per-migration
production risk review; (E) billing schema compatibility incl. `usage_tracking.usage_month`; (F)
read-only DR-16 investigation; (G) backup/PITR readiness; (H) execution runbook. Required outputs: the
safety-plan report, this prompt-history record, Q1–Q10 answers, one mandated verdict, and the exact
18-line no-change checklist.

---

## 2. Files inspected

`supabase/migrations/**` (all **53** files — every one mechanically scanned, and the 32-file delta read
object-by-object), `backend/data/billing.py`, `backend/services/billing.py`, `backend/domain/billing.py`,
`supabase/config.toml`, `e2e/environment/supabase/config.toml`, plus Git metadata and the three prior
production documents (`DEPLOYMENT_READINESS`, `SUPABASE_RECONCILIATION` Parts 1 & 2).

## 3. Commands run (all read-only)

```
git branch --show-current · git rev-parse HEAD · git log -1 --oneline
git status --porcelain=v1 · git diff --cached --name-only
git ls-tree -r --name-only HEAD -- supabase/migrations               (53)
git show --name-only --diff-filter=A HEAD -- supabase/migrations     (17)
git status --porcelain=v1 -- supabase/migrations                     (0)
git ls-files | grep -iE 'backup|restore|\.dump$'
per-file risk scan over all 53 migrations: DROP / ALTER..TYPE / SET NOT NULL / UNIQUE / FK / CHECK /
  INSERT / UPDATE / DELETE / CREATE POLICY + ENABLE RLS / GRANT + REVOKE / CREATE FUNCTION /
  CREATE TRIGGER / IF NOT EXISTS + OR REPLACE / RENAME
guarded-vs-unguarded DROP scan (delta) ; enum + rename scan (all 53)
exact data-mutation statement extraction (delta)
grep usage_tracking and 'ON CONFLICT' across backend/{data,services,domain}/billing.py
grep for ENABLE RLS / CREATE POLICY / GRANT referencing emission_factors (all 53)
grep backup|pitr in both config.toml files and in docs
```

**Production queries:** none were required in this operation beyond the GET probes already recorded in
RECON-002. **No write verb, DDL or DML was issued at any point**, and `supabase migration list --linked`
was **not run** (it creates a temporary login role).

## 4. Evidence / findings

**Objective A — migration history: `UNKNOWN`.** No safe read-only method exists: the CLI command is
prohibited (creates a temporary login role), no DB credential/session exists, and PostgREST does not
expose the `supabase_migrations` schema. Application-behaviour inference is prohibited and was not used.

**Objectives B/C — the delta.** Effective schema delta = **migrations 22 → 53 = 32 files**. No
discriminator from that band is present in production (10 Release-1 migrations proven absent; all other
probes absent), and **no reverse drift** was found — the PostgREST hints `processing_assignments`,
`typing_status`, `conversation_participants`, `staff_profiles` are all repository-created base tables.
The **history delta remains `UNKNOWN`** and is **not** asserted.

**Objective D — risk scan (32 delta files).** unconditional DROP **0** · `ALTER … TYPE` **0** · RENAME
**0** · enum change **0** · `SET NOT NULL` **2** (one on a freshly added column) · data mutation **8
statements in 6 files** · RLS/security changes **12 files** · GRANT/REVOKE **6 files** · function/trigger
**11 files** · reference-data inserts **4 files** · **non-idempotent: 27, 31, 35**.

Data-mutating statements, exactly:

```
30  INSERT INTO billing_plans              (seeded; ON CONFLICT (plan_code, version) DO NOTHING)
30  INSERT INTO billing_commercial_config  (seeded)
31  DO block: UPDATE billing_plans SET effective_to ; 2 x INSERT INTO billing_plans
                                           (mints new versions -> NOT re-runnable)
33  DELETE FROM conversation_participants a USING b WHERE a.created_at < b.created_at  (row deletion)
34  UPDATE staff_roles SET permissions ... WHERE name='system_admin' AND ... IS DISTINCT FROM 'true'
34  DELETE FROM staff_profiles WHERE role_id='56f5fa09-...' AND email='m34e3cb22-0@t.test'
34  DELETE FROM staff_roles    WHERE id='56f5fa09-...'                                 (id-scoped cleanup)
35  INSERT INTO staff_roles (pe_manager)                                               (bare insert)
44  UPDATE conversations SET conversation_kind='org' WHERE conversation_kind IS NULL   (new-column backfill)
```

(`29`'s `INSERT INTO public.users` is **inside a trigger function**, not a backfill.)

Precondition-gated: **40** (`assets.organization_id SET NOT NULL` → needs 0 NULLs) · **37** (UNIQUE
memberships → 0 duplicates) · **33** (0 duplicate participants) · **27** (needs the `documents` bucket;
`CREATE POLICY` unguarded) · **34/35** (absent test-role id / absent `pe_manager`) · **30+31** (apply
once, together).

**Objective E — billing.** `usage_tracking` is created at `00000000000000_init_schema.sql:1480` with
**`usage_month DATE`** and **`UNIQUE (organization_id, usage_month)`**, matching the Release-1
expectation and the `date_trunc(...)::date` fix at `backend/data/billing.py:851`. **NEW RISK `DR-19`:**
that write is a plain `INSERT` with **no `ON CONFLICT`**, so a **second approval in the same calendar
month for the same organisation raises `23505`**. No `ON CONFLICT` exists anywhere in the billing code
(`data/billing.py:851` writes; `services/billing.py:202` reads). The 7 `billing_*` tables remain absent
(migrations 30/31 unapplied).

**Objective F — DR-16 classified:** **`CONFIRMED SELECT exposure (7 049 rows); RLS almost certainly
DISABLED (no ENABLE ROW LEVEL SECURITY, no CREATE POLICY, no GRANT/REVOKE referencing emission_factors
anywhere in the 53 migrations); anonymous WRITE capability UNTESTED and cannot be excluded`** — every
other probed table returns `[]` to anon. No write test was attempted.

**Objective G — backup/PITR: `UNKNOWN — requires Supabase console verification`.** No backup/PITR
configuration exists in the repository; the only artefacts are **local development** dumps
(`backups/**`, `backend/carbon_tally_backup*.sql`, `local_backups/**`); no restore procedure; no rehearsal
evidence; snapshot creation is not provably read-only, so it is reported as a **prerequisite**.

**Objective H — runbook** prepared (§8 of the plan): Step 0 read-only credential, **Step 1 backup
confirmation as a hard gate**, Step 3 six precondition counts, Step 4 strict block ordering `22 → 53`
(`27` once; `30–31` together, once), per-block verification, schema/RLS/billing/storage checks,
application smoke tests, stop criteria, and §8.1's six outstanding read-only items.


## 5. Decisions

1. **Refused** `supabase migration list --linked` (creates a temporary login role).
2. **Refused** the service key; issued **no** write-verb, DDL or DML statement.
3. **Refused** to infer migration history from application behaviour (explicitly prohibited).
4. Built the delta from the **effective schema** (object-evidenced) while keeping the **history delta
   `UNKNOWN`** — reported separately, never conflated.
5. Retained every prior conclusion unchanged (including the DR-02 downgrade and DR-16/17/18).
6. Recorded **DR-19** (D6 monthly-charge correctness) because it was discovered while inspecting the
   billing write path — **without fixing it** (out of scope).

## 6. Risks

* **`DR-20` (P0):** a 32-migration **forward-only** delta with **no rollback path** and **unverified
  backup/PITR** — the dominant risk of the execution operation.
* **`DR-21` (P0):** recorded history, the RLS/policy/grant inventory and the six precondition counts
  cannot be obtained with the current access.
* **`DR-08` (P1):** the `documents` bucket is absent and is a **dependency of migration 27**.
* **`DR-19` (P1):** the second same-month approval fails on the D6 charge path once deployed.
* **`DR-16` (P1):** anonymous read of the factor table, with anonymous write not excludable.
* **`DR-13`:** no down-migrations — a partially applied delta is unrecoverable by tooling.

## 7. Stop-condition confirmation

**No stop condition was triggered while producing this plan** — the operation was read-only by
construction (no DB session, no write verb, no migration executed). Where the plan required information
that cannot be obtained within the boundary (migration history, RLS/grants, precondition counts,
backup/PITR), the result was reported as **`UNKNOWN` / prerequisite** — **not guessed and not worked
around**. The verdict itself stops before modification: **production is not to be modified on this
authorization.**

## 8. Final verdict

> ## `NOT READY — SAFETY PREREQUISITES MISSING`

**Answers:** Q1 delta established for **effective schema** (22 → 53, 32 files) but **history `UNKNOWN`** ·
Q2 **all 32, in order** · Q3 **none unsafe; six precondition-gated** · Q4 **yes — 6 files / 8 statements**
· Q5 **yes — 12 files, incl. 2 policy replacements** · Q6 **confirmed SELECT; RLS almost certainly off;
write UNTESTED** · Q7 **not verified (`UNKNOWN`)** · Q8 **no safe rollback established** · Q9 **not safe to
modify yet** · Q10 **only a prerequisite operation may be authorized; no migration execution**.

See `docs/architecture/CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md`.

