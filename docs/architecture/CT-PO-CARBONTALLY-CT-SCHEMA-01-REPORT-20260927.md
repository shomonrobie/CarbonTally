# CT-PO — CT-SCHEMA-01 Report: Canonical Schema From Zero

**Verdict:** `CT_SCHEMA_01_CANONICAL_SCHEMA_VERIFIED` *(with recorded environment/runner preconditions;
conservative alternative reading `CT_SCHEMA_01_PARTIAL_WITH_REMAINING_UNKNOWN` — see §12)*

**Task ID:** `CT-SCHEMA-01-20260927-CANONICAL-SCHEMA-FROM-ZERO-VERIFICATION`
**Type:** READ-ONLY verification with one brand-new disposable target; that target was the only thing
created or mutated. No production contact, no Git mutation, no source/migration change.
**Date:** 2026-09-27 · **Duration:** approximately 16:19–16:55 local (Asia/Dhaka).

**Companion documents (produced by this task):**
1. `CT-PO-CARBONTALLY-CANONICAL-SCHEMA-FROM-ZERO-VERIFICATION-20260927.md`
2. `CT-PO-CARBONTALLY-SCHEMA-CODE-MISMATCH-REGISTER-20260927.md`
3. `CT-PO-CARBONTALLY-CANONICAL-SCHEMA-FEATURE-SUPPORT-MATRIX-20260927.md`
4. `CT-PO-CARBONTALLY-SCHEMA-COMPARISON-MATRIX-20260927.md`
5. this report

---

## 1. Task identity and authority

| Field | Value |
|---|---|
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD (verified at start and at end) | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| Working tree | **unchanged by this task** — 51 porcelain entries before and after (pre-existing ` M .gitignore` plus pre-existing untracked files); the five deliverables are new untracked documents |
| Historical repository (evidence only) | `/home/shomonrobie/carbon_tally` @ `20b7a928bb73fdfacf8271ff537a8fd245f62c79` (branch `main`) — **not** merged, not modified |
| Production | **never contacted** |
| Git operations performed | `rev-parse`, `status`, `ls-files`-class reads only. No commit, push, merge, rebase, checkout, reset |

## 2. Disposable verification target

| Field | Value |
|---|---|
| SCHEMA-DB-ID | `CT-SCHEMA-01-TARGET-A` |
| Container | `ct_schema01_pg` — id `65ec22a681965668f8dca1b5f3ae26c5329bf1a81a90ccfd4b49aad8633316f6` |
| Volume | `ct_schema01_pgdata` (created 2026-09-27T16:30:17+06:00) |
| Image | `public.ecr.aws/supabase/postgres:17.6.1.159` — `sha256:86a2e078779e5bdccda1f6f6c5063aa9779a322d1fface5fb408d051909b230f` |
| PostgreSQL | 17.6 (matches the local Supabase stack's 17.6.1.x line) |
| Database / role | `postgres`; provider role `supabase_admin`, migration role `postgres` (non-superuser) |
| Port | `127.0.0.1:55450` |
| Platform sidecar | `ct_schema01_storage` (`storage-api:v1.69.0`) — platform provisioning only |
| Baseline | **0 `public` tables, 0 application rows, 5 extensions, 29 roles, 12 schemas** |
| Earlier instance | `CT-SCHEMA-01-TARGET-0` (id `17e10418744411783fe514355746786b32f943055ec30bc46657080bf7799c3c`) used for the bare-platform and role-sensitivity probes, then **destroyed with its volume** by this task (the only destruction performed); evidence archived |
| Isolation | No pre-existing database, container, volume or backup was touched, reset, truncated or deleted |

## 3. Migration count and execution result

| Measure | Value |
|---|---|
| Migration files (recounted) | **89** |
| Migration-set fingerprint | `d73e1e2b4e503c13b5079dfc84f3ae0081d04f0f67f91231d8baa0879b8cb26c` |
| Applied | **89** (26 before the operator interlude + 63 after) |
| Failed (canonical run) | **0** |
| Skipped / duplicates | **0 / 0** |
| Independent apply ledger | `/tmp/ledger_final.tsv` — `sha256 11bfc796f5a9e727d83c8fb69f96e3971927187127c4e8a747dae3b45444bedd` (89 rows, 89 `APPLIED`) |
| `supabase_migrations` ledger | not populated (no CLI apply performed — limitation) |
| First / last applied | `00000000000000_init_schema.sql` / `20261020000000_p17k_governed_capability_catalogue.sql` |

**Two execution failures were found and are the substantive discoveries of this task** (each reproduced):

1. **`F-01` (S1)** — on a bare Supabase Postgres baseline the chain stops at **27/89**
   (`20260823000000_d32_private_documents_storage.sql`): `ERROR: relation "storage.buckets" does not exist`.
   The platform `storage` layer (provisioned by storage-api, not by any migration) must exist first.
2. **`F-02` (S1)** — with storage provisioned, the same migration **still fails when applied as
   `supabase_admin`**: `D32 policy drift: d32_documents_select_org_member is missing the approved
   org-scope fragment "auth.uid()"`. Root cause: the migration validates the *deparsed* predicate text,
   and PostgreSQL deparses `auth.uid()` unqualified when `auth` is in the session `search_path`
   (`supabase_admin` has it; `postgres` does not). It **passes** as `postgres`. The repository's own
   `e2e/environment/scripts/apply_migrations.sh` prescribes `supabase_admin` for exactly this migration —
   the two documented mechanisms contradict each other, and the helper's ownership rationale is stale
   (the current D32 revision issues no ownership-sensitive DDL).
3. **`F-03` (S2)** — the D32 operator step (private bucket + four provider-context policies) **cannot
   precede migration 1**, because the approved predicates reference `public.organization_members`
   (created by migration 1). Correct order: platform → migrations ≥ 1 → operator policies → migrations 27–89.

The successful canonical run used exactly that order, as the non-superuser `postgres` role.

## 4. Complete schema inventory summary (after 89/89)

| Class | Count |
|---|---|
| `public` tables (application) | **145** |
| Tables all schemas | 375 (145 `public`, 10 `storage`, 5 `auth`, 2 `vault`, 2 `extensions`, rest catalog) |
| Columns (all schemas) | 4 592 |
| Constraints | 756 → 223 PK, 172 FK, 109 UNIQUE, 252 CHECK (620 in `public`) |
| Indexes | 551 |
| Enums / custom types | 1 (`storage.buckettype`, platform); **application schema declares 0 enums** |
| Functions (`public` / all non-catalog) | 31 / 144 |
| Triggers (non-internal) | 88 |
| Views / materialised views | 3 (all platform) / 0 |
| RLS-enabled `public` tables | **145 / 145 (100 %)** |
| RLS policies | 227 (`SELECT` 93, `INSERT` 46, `UPDATE` 43, `DELETE` 37, `ALL` 4) |
| Policies granting `anon`/`public` | **0** |
| Grants to `anon`/`authenticated`/`service_role`/`public` | 1 646 |
| Application rows | **0** (organisations 0, emission_factors 0, customer_factors 0) |
| Migration-declared reference rows | `scope3_categories` 15, `disclosure_frameworks` 3, `disclosure_framework_versions` 1, `disclosure_requirement_versions` 18 |
| **Inventory fingerprint** | **`c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f`** |

**Declared-object completeness across all 89 migrations:** 145/145 tables, 167/167 `ADD COLUMN`
declarations, 187/188 indexes and 80/81 policies (the two differences are objects **explicitly dropped by
later migrations in the same chain** — supersessions, not gaps), 31/31 functions → **100 % reconciled**.

## 5. Code / schema compatibility

| Measure | Value |
|---|---|
| High-precision code references to `public.<object>` | 159 unique identifiers |
| Client-style references (`.table/.from/.from_`) | 54 unique identifiers |
| Canonical tables with no code reference (grep level) | 0 |
| Code references absent from the canonical schema | 20 raw hits → **4 genuine**, 9 test fixtures, 7 regex artefacts |
| Genuine code↔schema mismatches | **4 (all S2)** — `defra_conversion_factors`, `report_history`, `report_schedules`, `notification_delivery_log` |

The four genuine mismatches are **legacy route surfaces** referenced by durable backend code, created by
no migration and present in **no** environment (flagship, demo_local, qa_phase8, canonical). The
from-zero rebuild neither causes nor cures them; they are code drift.

## 6. P17 / P16R compatibility

| Item | Result |
|---|---|
| P17-A (`20261010000000`) | All declared columns/indexes/constraints present; **no `accounting_dimensions` table exists by design** (dimensions are columns on results) |
| P17-C (`20261011000000`) | `contractual_instruments` (20 cols, RLS, 4 policies), `instrument_allocations` (12 cols, RLS, 4 policies), `p17_instrument_over_allocated()` — all present |
| P17-D (`20261012000000`) | `scope3_categories` present **with 15 category rows** |
| P17-H (`20261013000000`) | `estimation_records` (14 cols, RLS, 4 policies) + 4 diagnostic functions — all present; no separate `assumption_records` table by design |
| P17-10 (`20261014000000`) | `scope3_method`, `transaction_provider` + 4 indexes present |
| P17-K (`20261020000000`) | Creates **no schema object**; seeds reference data — `disclosure_framework_versions` 1 row, `disclosure_requirement_versions` **18 rows** present |
| P16-R5 (`20261008000000`) | `reportability_status`, invalidation/supersession columns + 2 indexes present |
| P16-R7 (`20261009000000`) | `uq_calc_snapshots_request_id` present |
| Automated check | 105 parsed declarations → **104 confirmed present, 1 parser artefact, 0 real absences** |

## 7. FIEW impact

| Measure | Value |
|---|---|
| FIEW rows examined | **57 / 57** |
| Rows whose schema blocker is removed by the clean rebuild | **57** (all 31 FIEW-cited tables and 27 FIEW-cited columns present in the canonical schema) |
| Rows promoted to a higher truth state by this task | **0** |
| Rows still runtime-unverified | **57** |
| Rows that stay `DOCUMENTED_ONLY` regardless of schema | 1 (`FIEW-056`, P17-K reference data) |
| Rows additionally dependent on the platform storage policies | 1 lineage (`FIEW-024`/`025` evidence-document paths) |
| Discrepancy recorded | P17-K seeded **18** rows in the canonical rebuild vs **55** observed in a disposable clone (open question, not a defect) |

## 8. Existing-database comparison

| Database | `public` tables | Canonical objects missing | Canonical-only extras | Status |
|---|---|---|---|---|
| `postgres` (flagship) | 116 | 29 | 0 | `OUTDATED` (ledger 46 rows, max `20260903010000`) |
| `carbontally_demo_local` | 141 | 4 | 0 | `OUTDATED` |
| `carbontally_qa_phase8` | 133 | 12 | 0 | `OUTDATED` |
| `carbontally_test` | 117 | 28 | 0 | `OUTDATED` |
| `ct_p17k_20260926` (disposable) | **145** | **0** | **0** | `CANONICAL (identical)` |
| `ct_d17d32_chain` | 0 | 145 | 0 | empty scratch |
| **Canonical rebuild** | **145** | — | — | reference |
| `ct_local_93d5cdd` | not reachable read-only | — | — | `UNKNOWN` |

Canonical is a **strict superset** of every durable database; the most advanced disposable clone is
**table-for-table identical** to it. No durable environment currently carries the canonical schema.

## 9. Blockers, unknowns and limitations

**Blockers (all reproduced with evidence):** `F-01` platform storage layer required before migration 27
(S1) · `F-02` migration 27 fails as the repository's own documented apply role `supabase_admin` because of
`search_path`-dependent deparsed-text validation (S1) · `F-03` D32 operator provisioning cannot precede
migration 1 (S2).

**Mismatch register (17 entries):** S1 = 2 · S2 = 6 · S3 = 3 · S4/INFO = 6. Details in
`CT-PO-CARBONTALLY-SCHEMA-CODE-MISMATCH-REGISTER-20260927.md`.

**Unknowns:** no CLI-ledger run performed · no Supabase-CLI-managed (`supabase start`) run performed ·
runtime behaviour untested · whether the four legacy mismatches correspond to registered routes ·
`ct_local_93d5cdd` comparison unavailable.

**Limitations:** migrations applied as the non-superuser `postgres` role only (privilege behaviour under
other roles probed only for migration 27) · no application code executed · D32 policies created from the
migration header definitions rather than the dashboard mechanism · no `supabase_migrations` ledger ·
rebuilt schema contains no application data · the disposable target remains running (labelled, isolated,
schema-only) for follow-up verification · fingerprints are valid for the recorded image digest.

**Explicit non-claims:** no feature is claimed to work; no workflow, route, RLS-enforcement or report is
claimed to function; no acceptance verdict is given; production is untouched; the 57 FIEW downgrades are
**not** reversed by this report.

## 10. Recommended next steps

1. Resolve `F-02` (make the D32 validation `search_path`-independent, **or** correct the harness role and
   the stale ownership rationale) — an implementation task, not this read-only task.
2. Encode the canonical two-layer, four-step from-zero procedure (platform → migrations ≥ 1 → operator
   storage policies → migrations 27–89) as a runbook/automation; it must fail loudly if the platform
   storage layer is absent.
3. Apply the chain to a **declared durable** environment (all current durable databases are 4–29 canonical
   objects behind) and treat that environment — not a clone — as the schema of record.
4. Run the E2E gate against the rebuilt schema to begin moving FIEW rows beyond `SCHEMA`, with independent
   verification for any promotion.
5. Resolve the four legacy code↔schema mismatches (live route audit, then add migration or remove code).
6. Commission independent verification of this task (fresh disposable clone → same ledger arithmetic and
   same inventory fingerprint).

## 11. Final hand-back

| Item | Value |
|---|---|
| **Verdict** | `CT_SCHEMA_01_CANONICAL_SCHEMA_VERIFIED` *(with the recorded preconditions; conservative alternative `CT_SCHEMA_01_PARTIAL_WITH_REMAINING_UNKNOWN`)* |
| HEAD SHA | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| Branch | `p8-release-reconciled` |
| Migration count | **89** |
| Applied count | **89** (ledger 89/89, 0 failed, 0 skipped, 0 duplicates) |
| Clean rebuild success/failure | **Success** on a fresh empty application database with the standard Supabase platform baseline; **fails at 27/89** on a bare Supabase Postgres baseline (F-01) and **fails at 27/89** as `supabase_admin` (F-02) |
| Disposable DB identity | `CT-SCHEMA-01-TARGET-A` — container `ct_schema01_pg`, volume `ct_schema01_pgdata`, PostgreSQL 17.6, image `public.ecr.aws/supabase/postgres:17.6.1.159` |
| Schema object counts | 145 `public` tables (145/145 RLS) · 227 policies · 172 FKs · 551 indexes · 4 592 columns · 31 functions · 88 triggers · 756 constraints; fingerprint `c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f` |
| Mismatch counts | **S1 = 2 · S2 = 6 · S3 = 3 · S4/INFO = 6** (17 registered) |
| FIEW rows whose schema blocker is removed | **57** |
| FIEW rows remaining runtime-unverified | **57** (0 promoted) |
| Existing DB comparison summary | flagship 116/145 (−29) · demo_local 141/145 (−4) · qa_phase8 133/145 (−12) · test 117/145 (−28) · `ct_p17k_20260926` 145/145 (identical) · `ct_local_93d5cdd` unknown; **0 extras anywhere** |
| Can the 89-migration chain be treated as the canonical schema source? | **Yes** — it is ordered, executable from zero, produces the complete intended application schema (100 % declared-object reconciliation), reproduces the most advanced environment exactly, and is a strict superset of every durable database. It is **not** a bare-Postgres-only chain: it requires the Supabase platform layer and one operator step, and migration 27 is role/`search_path` sensitive |
| **Exact next task recommendation** | **`CT-SCHEMA-02-20260927-CANONICAL-SCHEMA-REBUILD-AUTOMATION-AND-D32-RUNNER-FIX`** — (a) fix the D32 `search_path`/role validation contradiction and align `e2e/environment/scripts/apply_migrations.sh`; (b) implement the documented two-layer from-zero procedure with a hard failure when the platform storage layer is absent; (c) apply it to a declared durable environment; (d) record the resulting ledger + fingerprint as the schema of record |

**No implementation. No production contact. No Git mutation.** This task created and mutated only the
labelled disposable target in §2 and wrote only the five documentation files listed on its cover.

<!--CTEOF-->


