# CarbonTally — RC2 Production Hardening — Repair Release Notes

**Bundle:** `database/rc2/*` — 7 migration files + this manifest
**Target:** PostgreSQL 16 (Supabase), schema `public`
**Precursor:** baseline `supabase/migrations/00000000000000_init_schema.sql` already applied
**Scope:** REPAIR of the CarbonTally RC1 hardening release. The RC2 audit fixed
the critical/high exposures in the RC1 package while preserving the approved
RC1 design intentions that were sound.

All "tag" references (C#, H#, K#, L#, I#) are the audit finding identifiers from
the **CarbonTally RC1 — Independent Database Audit** report. The RC2 naming
convention restates RC1's numbering (e.g. `C3`, `H1`) so the fix-trace is greppable.

---

## 1. The RC2 package at a glance

| File | What it does | Audit focuses |
|------|--------------|---------------|
| `001_rc2_schema.sql` | Renames, new columns, legacy column merges, region retirement | R1–R3, C1–C10, C4, C7 |
| `002_rc2_constraints.sql` | FK set, CHECK vocabulary, unique-index rebuilds, password-token keys | F1, H2, H4, K1–K8, L2, L3 |
| `003_rc2_indexes.sql` | Index hardening + extension ensure (non-transactional) | I1–I5, H5, L3-support |
| `004_rc2_rls.sql` | RLS allow-storey on the deny-by-default floor | C2, C4, C5, C6 |
| `005_rc2_functions.sql` | `set_updated_at()`, `anonymise_user()` | C3, H1, F1/F2 |
| `006_rc2_triggers.sql` | `trg_set_updated_at_<table>` maintenance triggers | §7 checklist |
| `007_rc2_verification.sql` | Read-only post-migration verification suite | all __sections__ |

---

## 2. The critical / high repairs (and why they matter)

### C3 — `anonymise_user()` privilege escalation (Critical) → fixed in `005`
**Root cause:** the effective actor was derived from a **caller-supplied**
`p_actor_id` (`v_actor := coalesce(p_actor_id, auth.uid())`). Because the function
is `SECURITY DEFINER` and `authenticated` held `EXECUTE` (for self-service), **any**
authenticated user could call `anonymise_user(any_victim_id, any_active_staff_id)` and
erase a row that was not theirs — cross-tenant / mass erasure.

**Fix:** authority derives from the **session only** (`auth.uid()`). A caller-supplied
`p_actor_id` that does not match `auth.uid()` under a real session now `RAISE`s
(anti-spoof). `p_actor_id` is retained only as an advisory/audit tag. The `EXECUTE
TO authenticated` grant is preserved (self-service path is now safe because the
function rejects any mismatch).

### H1 — hash resolution for the erasure marker email (Critical) → fixed in `005`
**Root cause:** the baseline installs `pgcrypto` **`WITH SCHEMA extensions`**, so
`sha256` is reachable only as `extensions.sha256`. RC1 called bare `sha256(...)`
with `search_path = public`, which cannot resolve.

**Fix:** `encode(extensions.sha256(p_user_id::text::bytea), 'hex')`.

### H2 — broken `emissions_logs_unit_fkey` predicate (High) → fixed in `002`
**Root cause:** the FK joined `emissions_logs.unit` to `units.code` on a predicate
that can never hold for present-day `unit` content — a logically dead constraint
that traps valid emissions rows on write.

**Fix:** the FK was **dropped** and is **intentionally not re-created** (`unit` is
treated as free text). `007 §3a` asserts it is gone.

### H4 — `customer_subscriptions.status` CHECK too narrow for Stripe (High) → fixed in `002`
The CHECK accepted only 6 states; Stripe can report `incomplete`,
`incomplete_expired`, and `unpaid`. The constraint was **widened** the 9-value
list (extended-comprise, so pre-existing rows are preserved).

### H5 — planner-limiting filtered index (High) → fixed in `003`
A partial index was reconstructed to match the application filter predicates
so the query planner uses it (avoiding an accidental full-flag/perf regression).

---

## 3. Deployment order

Run strictly in the listed order. `007` is the gate before application smoke tests.

1. `001_rc2_schema.sql` — transactional. Must apply clean first; every later file
   references the final names it produces.
2. `002_rc2_constraints.sql` — transactional. `VALIDATE CONSTRAINT` sub-steps
   **lock** momentarily; run during the agreed low-traffic window.
3. `003_rc2_indexes.sql` — **NON-transactional.** `CREATE INDEX CONCURRENTLY`
   cannot run inside a transaction. Run **statement-by-statement**, and **never
   wrap this file in a transaction-forcing runner** (e.g. `psql --single-transaction`
   or Drizzle/Prisma transaction wrappers). A failed build leaves an **INVALID**
   index: drop it (`DROP INDEX CONCURRENTLY`) and re-run only that statement.
4. `004_rc2_rls.sql` — transactional. Requires `003`'s `pgcrypto`? No — RLS helpers
   do not need `sha256`; they need only the baseline. Order kept here for
   convention (RLS before functions on the consultant helpers).
5. `005_rc2_functions.sql` — transactional. `extensions.sha256` requires
   `pgcrypto` (ensured in `003`). Run after `003`.
6. `006_rc2_triggers.sql` — transactional. Requires `005`'s `set_updated_at()`.
   Captured `NOTICE` lines list exactly which tables got a trigger; save them to
   compare against `007 §7`.
7. `007_rc2_verification.sql` — **read-only**, re-runnable at any time. Run after
   `006` and again after application smoke tests.

---

## 4. Non-transactional cautions

- `003_rc2_indexes.sql` is the **only** non-transactional file. See §3.
- Everything else runs inside `BEGIN … COMMIT` (single transaction each file).
- `001` may contain `DROP COLUMN` branches that are **data-destructive by design**
  (merging duplicate legacy columns). Confirm the staging data audit (Gate 2)
  cleared those columns before applying.
- `005`'s `anonymise_user()` is **irreversible by design** — its acceptance
  evidence is the Gate 5 staging rehearsal, not a rollback.

---

## 5. Per-file rollback

| File | Rollback |
|------|----------|
| `001` | Re-run using the matching baseline restore / reverse-DDL fragment (documented per R/C block). Columns renamed cannot be auto-renamed; treat as fix-forward. |
| `002` | Recreate `emissions_logs_unit_fkey` if the team later reverts H2; `DROP CONSTRAINT … ; ADD CONSTRAINT …` for widened checks; `DROP INDEX …; CREATE UNIQUE INDEX …` for rebuilt uniques. |
| `003` | `DROP INDEX CONCURRENTLY <name>` per index. A failed build leaves an INVALID index — drop and re-run the statement. |
| `004` | Drop the policies by name (each `DROP POLICY IF EXISTS …`), keep baseline RLS enablement (restores deny-by-default). Drop the four helper functions. No pre-existing policy was dropped. |
| `005` | `DROP FUNCTION IF EXISTS public.anonymise_user(uuid, uuid, text);` and `DROP FUNCTION IF EXISTS public.set_updated_at();` (drop `set_updated_at` only after `006` triggers are removed). |
| `006` | `DROP TRIGGER IF EXISTS trg_set_updated_at_<table> ON public.<table>;` per installed table, or simply re-run (idempotent). |
| `007` | n/a — read-only, nothing to roll back. |

**General principle:** prefer **fix-forward** over rollback. The only irreversible
object is `anonymise_user`'s erasure (by design).

---

## 6. Post-deploy verification

1. Capture `007`'s `RAISE NOTICE` summary — all check-gates must read OK.
2. Confirm the **FK inventory** reports **10** validated FKs and no
   `emissions_logs_unit_fkey`.
3. Confirm the **003 index count** is **21** (18 RC1 + 3 RC2 additions).
4. Confirm `anonymise_user` guard behaviour on **staging**: an authenticated
   self-service call works only for `auth.uid() = p_user_id`; a mismatched
   `p_actor_id` raises; the service-role runbook path still works.
5. **Gate 4 (RLS penetration matrix):** exercise the `_tenant_*` / role /
   consultant policies against the `authenticated` role before app sign-off.
6. **Gate 5 (erasure rehearsal):** stage a full `anonymise_user` run + residual-PII
   scan. This is the acceptance evidence for `005`.
7. **Gate 1 reconciliation:** the pre-existing Supabase indexes and any
   pre-existing policies/views surface as explicit reconciliation records, not
   RC2 failures.

---

## 7. Integrity of the RC2 package

- **Idempotence:** every mutating file is `DROP … IF EXISTS` / `CREATE OR REPLACE` /
  `CREATE … IF NOT EXISTS`. Re-runs are safe.
- **Single source of truth:** RC2 files were written against the **baseline init
  file** (not against RC1's guessed inventory), so object/constraint/policy names
  match the database exactly.
- **`007` asserts the RC2 state**, not RC1's expectations: 10 FKs, the H2 drop,
  21 indexes, the widened `customer_subscriptions` vocabulary, 4 RLS helpers,
  6 functions, generative RLS gap checks.

---

*End of 008_rc2_release_notes.md*
