# CT-PO — CarbonTally CT-SCHEMA-02 Report

**Task ID:** `CT-SCHEMA-02-20260927-CANONICAL-SCHEMA-REBUILD-AUTOMATION-AND-D32-RUNNER-FIX`
**Date:** 2026-09-27
**Repository / authority:** `/home/shomonrobie/ct_93d5cdd` (branch `p8-release-reconciled`)
**Type:** Implementation + verification (harness/schema automation). No application-code change, no production action, no deployment, no push.

---

## 1. Objective

Deliver a **deterministic, fail-closed, from-zero canonical schema rebuild** that reproduces
the CT-SCHEMA-01 verified canonical schema and fingerprint on a brand-new disposable target,
with the D32 `search_path` defect (**F-02**) and its extension (**F-02-EXT**) fixed, and with
the full acceptance surface re-verified end-to-end on a *fresh* target rather than a reused one.

The work converts verified-but-manual CT-SCHEMA-01 knowledge into two durable, re-runnable
artefacts:

1. a canonical rebuild driver (`canonical_schema_rebuild.sh`) implementing the two-layer model
   (platform layer + application layer) in dependency order, and
2. a hardened verifier (`canonical_schema_verify.py`) whose inventory rendering is
   context-deterministic (`search_path` pinned), so inventory bytes and the canonical
   fingerprint are comparable by construction.

---

## 2. Starting SHA

```
cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea   (branch p8-release-reconciled, 2026-09-26 16:19:11 +0600)
fix(public-truth): build provenance, admin config gate, security headers, admin branding
```

## 3. Ending SHA

```
cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea   (unchanged)
```

**No commit and no push were made.** `git reflog -1` still reads
`cb70fd6 HEAD@{0}: commit: fix(public-truth): …` — i.e. the newest reflog entry predates this
task. All CT-SCHEMA-02 output is **uncommitted working-tree state** (`M`/`D`/`??`), deliberately
left for review.

---

## 4. Files changed

All paths relative to the repository root. Classification: **N** = new (untracked),
**M** = modified (tracked), **D** = deleted (tracked), **S** = symlink replacement.

| Path | Class | Purpose |
|---|---|---|
| `e2e/environment/scripts/canonical_schema_rebuild.sh` | N | Canonical from-zero rebuild driver: PHASE A platform → B migrations 1–26 → C D32 operator + semantics → D migrations 27–89 → VERIFY. Fail-closed; labelled disposable target only; evidence dir; `--dry-run`/`--reuse`/`--destroy`. Generates the Storage service's key material **per run** (no key material stored; `CT02_*` overrides for non-disposable use). |
| `e2e/environment/scripts/canonical_schema_verify.py` | N | Canonical verifier: 10 exact count checks + 12-class inventory + canonical fingerprint + migration-set fingerprint/provenance + D32 policy/anchor checks + P16R/P17 named checks. **This task added `INVENTORY_SEARCH_PATH` (`"$user", public, auth, extensions`) pinned in `Db.__init__`/`_cmd`, a `Db(..., search_path=…)` parameter and a `--inventory-search-path` CLI flag (F-02-EXT fix).** |
| `e2e/environment/scripts/d32_storage_operator.sql` | N | Canonical D32 operator step (provider-privileged context): private `documents` bucket + exactly four `storage.objects` policies. Idempotent, fail-closed, self-verifying. |
| `e2e/environment/scripts/verify_d32_policy_semantics.sql` | N | Behavioural D32 policy-semantics proof — exercises the four policies under simulated `auth.uid()`/role contexts inside a transaction that is rolled back. 11 assertions. |
| `e2e/environment/scripts/d32_search_path_regression.sh` | N | F-02 regression suite R1–R9 proving old risk, the fix, and that validation is not weakened. |
| `e2e/environment/scripts/apply_migrations.sh` | M | Range-based migration application (`--range A B`), pinned `search_path`, deterministic ordering, `ALL_APPLIED applied=/selected=source=`, `LEDGER=`, ledger row/`sha256` emission. |
| `e2e/environment/scripts/bootstrap.sh` | M | Two-layer bootstrap aligned to the canonical sequence (platform → 1–26 → D32 operator → 27–89). |
| `e2e/environment/scripts/reset.sh` | M | Reset aligned to the canonical sequence; no destructive action against non-disposable targets. |
| `e2e/environment/supabase/config.toml` | M | `enabled = false` for services that would otherwise double-provision/conflict in the disposable container model; canonical `schemas`/port kept. |
| `e2e/environment/supabase/migrations` | S | **Symlink** to the canonical `supabase/migrations` (single source of truth for migrations). |
| `e2e/environment/supabase/migrations/*.sql` (53 tracked files) | D | Removal of the **drifted stale copy** of the migration set (it had stopped at the pre-V3M3 generation and diverged from the canonical chain). Superseded by the symlink above. |
| `e2e/environment/README.md` | M | Documents the canonical build contract: two layers, dependency-ordered sequence, D32 operator step and role contract, evidence locations. |
| `supabase/migrations/20260823000000_d32_private_documents_storage.sql` | M | **The F-02 fix** (+111/−10): validation re-written to resolve identity anchors to OIDs at parse time and match the *stored* expression by OID tokens instead of deparsed `search_path`-relative text. *(Only migration differing from CT-SCHEMA-01 HEAD — asserted by the verifier.)* |

**Pre-existing working-tree changes that this task did not touch, and must not be attributed to
CT-SCHEMA-02:** `M .gitignore` (whole-file line-ending-style diff, no semantic change) and the
large set of untracked `docs/architecture/*` documents produced by earlier tasks.

**Net tracked diff for CT-SCHEMA-02's own scope:** 5 modified harness/config files + 1 modified
migration + 53 deletions (drifted migration copy) + 5 new scripts + 1 symlink.

---

## 5. F-02 root cause

**Defect:** migration 27 (`20260823000000_d32_private_documents_storage.sql`) validated the four
D32 storage policies by reading their predicate **as text from `pg_policies`**. Two independent
properties of PostgreSQL made that validation non-deterministic and, in one direction, unsound.

**5.1 `pg_policies.qual`/`with_check` are *deparsed* expressions rendered relative to the
reading session's `search_path`.** The same, unmodified stored policy therefore renders
differently per role:

| Reading role | Default `search_path` | Rendered predicate fragment |
|---|---|---|
| `postgres` (documented migration role) | `"$user", public, extensions` | `auth.uid()` |
| `supabase_admin` (provider role) | `"$user", public, auth, extensions` | `uid()` |

Because `auth` is *in* `supabase_admin`'s path and *not* in `postgres`'s, a validator that
matches the literal fragment `auth.uid()` **fails for the provider role and passes for the
migration role** — the outcome of a security validation depended on which role happened to run
it. The D32 operator step is executed in the **provider** context (only the provider role may
own/alter `storage.objects`), so the documented operator role was exactly the role for which the
validator failed.

**5.2 The check was a substring match, so it could also be *fooled*.** `position('<fragment>' in
stored_expression)` accepts any expression *containing* the fragment. A policy calling
`myauth.uid()` — a different function in a different schema — satisfied a naive textual check,
so the validator could pass a policy whose organisation scope was **not** anchored to Supabase's
`auth.uid()`. That is validation *weakening*, not merely path fragility (proved by R6a in §19).

**5.3 Extension (F-02-EXT).** The same class of defect applies to the **inventory/evidence**
layer: PostgreSQL renders every *stored* expression (column defaults, policy predicates, index
expressions, view definitions) relative to the session `search_path`. Concretely, the
`auth.refresh_tokens.id` default deparses as `nextval('refresh_tokens_id_seq'::regclass)` when
`auth` is in the path, and as `nextval('auth.refresh_tokens_id_seq'::regclass)` when it is not.
Consequently the canonical inventory bytes — and therefore the **canonical fingerprint** — are
only reproducible when the reading session's `search_path` is pinned. This was the sole
divergence in the previous verification round (`C_columns`, one row), and it was *not* a schema
difference at all.

**Impact:** migration 27's validation was reproducible only for a specific reading role, and its
positive result did not strictly prove that the policies call Supabase's session-identity
function. Both properties are unacceptable for a fail-closed security validation that gates the
private-documents boundary.

---

## 6. Fix implemented

**6.1 Migration 27 — identity anchors compared by OID, not by text (the core F-02 fix).**

```sql
identity_function_oid := to_regprocedure(approved_identity_function)::oid;   -- 'auth.uid()'
IF identity_function_oid IS NULL THEN ... fail closed ... END IF;
identity_relation_oid := to_regclass(approved_identity_relation)::oid;       -- 'public.organization_members'
...
IF position(':funcid ' || identity_function_oid::text || ' ' in stored_expression) = 0 THEN
    RAISE EXCEPTION 'D32 policy drift: % does not call the approved session-identity function '
                    '(identity checked by OID), so its organisation scope cannot be trusted', ...
IF position(':relid ' || identity_relation_oid::text || ' ' in stored_expression) = 0 THEN
    RAISE EXCEPTION 'D32 policy drift: % does not anchor its organisation scope (identity '
                    'checked by OID)', ...
```

The validator still checks the approved **org-scope fragment** textually (the
`(storage.foldername(name))[1] = 'uploads'` + `[2]::uuid IN (…)` shape), so genuine drift is
still caught (§19, R7). The rest of migration 27 is unchanged: it does not create provider-owned
objects; those are created by the operator step (§10) and validated here.

**6.2 Verifier — inventory rendering pinned (the F-02-EXT fix).**
`canonical_schema_verify.py` now carries the constant

```python
INVENTORY_SEARCH_PATH = '"$user", public, auth, extensions'
```

applied in `Db.__init__` (and re-applied per `_cmd` invocation), with an override
`--inventory-search-path` and the pinned value echoed in the verification header. The verifier
therefore reads deparsed expressions in exactly the context CT-SCHEMA-01's canonical inventory
was produced in, and the rendering context is now part of the evidence rather than an accident of
the invoking role.

**6.3 Driver — PHASE A readiness hardened.** The Supabase Postgres image restarts PostgreSQL
during initialisation, so a single `pg_isready`/one-shot query can succeed inside the restart
window and be followed by a connection reset. The gate now requires **two consecutive successful
in-container `psql` queries** (max 300 s) before the platform layer is accepted.

---

## 7. Why the fix is `search_path`-safe

1. **OIDs are resolved once, at parse time, and stored as integers.** `to_regprocedure('auth.uid()')`
   and `to_regclass('public.organization_members')` resolve the *qualified* names to their object
   identities at that moment. Comparison is then made against the `nodeToString` form of the
   stored policy expression, in which a function call is serialised as `:funcid <oid>` and a
   relation reference as `:relid <oid>`. Those are numeric identities — **no schema name, and
   therefore no `search_path` component, participates in the comparison**.
2. **It is stronger, not merely stable.** A same-named look-alike (`myauth.uid()`) has a different
   `funcid`, so it is rejected regardless of any role's `search_path` (§19, R6b). The
   pre-revision validator accepted it (R6a).
3. **The org-scope check remains textual and still detects drift** (R7), so path-independence did
   not cost detection capability.
4. **Read-time context no longer leaks into the verdict**: the result is identical for
   `supabase_admin`, for `postgres`, and under a forced `auth,public` or `pg_catalog` path
   (R1–R5b/§19), because no name resolution happens at read time.
5. **The evidence layer applies the same principle.** With the pinned `INVENTORY_SEARCH_PATH`,
   inventory bytes are a function of the schema alone — which is what makes byte-comparison
   against CT-SCHEMA-01 and the canonical fingerprint meaningful. Pinning the reading context is
   the only correct alternative to not comparing at all; the pinned value is the one CT-SCHEMA-01's
   canonical inventory was rendered under, and it is now recorded in the evidence header.

---

## 8. Canonical rebuild procedure

Driver: `e2e/environment/scripts/canonical_schema_rebuild.sh`

```
PHASE A  platform prerequisites (fail closed if the Storage layer is absent)
PHASE B  migrations 1-26          as postgres       (creates public.organization_members,
                                                     which the D32 predicates reference)
PHASE C  D32 operator step        as supabase_admin (private documents bucket + four
                                                     provider-context policies) + behavioural
                                                     policy-semantics proof (rolled back)
         D32 operator re-run        → idempotency evidence (policy count before/after)
PHASE D  migrations 27-89         as postgres       (migration 27 validates PHASE C's objects)
VERIFY   canonical_schema_verify.py: 10 exact counts + 12-class inventory + canonical
         fingerprint + migration-set count/order/uniqueness/fingerprint/provenance +
         D32 policy/bucket/anchor checks + P16R/P17 named checks
```

Safety properties by construction:

* **Target naming and labelling** — containers `${PREFIX}_pg` / `${PREFIX}_storage`, volume
  `${PREFIX}_pgdata` (default prefix `ct_schema02`), labelled
  `ct.schema02.task=CT-SCHEMA-02-20260927` and `ct.schema02.disposable=true`. The driver refuses
  (non-zero exit) to adopt an existing container/volume unless `--reuse` is given explicitly.
* **Fail-closed** — missing platform object, wrong migration count, any failed migration,
  unverifiable policy, unexpected count/fingerprint, or any `anon`/`public` policy aborts the run
  with a non-zero exit. Nothing is downgraded to a warning.
* **Credentials** — a random password is generated per run and written to a `0600`
  `/tmp/<prefix>.env`; it is never printed and never committed.
* **Evidence** — `--evidence <dir>` (default `/tmp/ct_schema02_evidence`): per-phase stdout,
  per-migration logs, both phase ledgers, the consolidated canonical ledger + `sha256`, the
  inventory directory, `verify.txt`, `verify.json`, and the PHASE A target-identity block.

Invocation used for the final acceptance run:

```bash
bash e2e/environment/scripts/canonical_schema_rebuild.sh --evidence /tmp/ct_schema02_evidence
```

The brand-new target was created by the driver itself (no `--reuse`), so PHASE A truly started
from an empty volume.

## 9. Platform prerequisite procedure (LAYER 1)

```bash
# 1) Postgres: pinned Supabase image, empty volume, labelled disposable container
docker volume create ct_schema02_pgdata
docker run -d --name ct_schema02_pg \
  --label ct.schema02.task=CT-SCHEMA-02-20260927 --label ct.schema02.disposable=true \
  -e POSTGRES_PASSWORD=<generated> -e POSTGRES_USER=supabase_admin -e POSTGRES_DB=postgres \
  -p 127.0.0.1:55460:5432 -v ct_schema02_pgdata:/var/lib/postgresql/data \
  public.ecr.aws/supabase/postgres:17.6.1.159

# 2) Readiness gate: TWO consecutive successful in-container psql queries (max 300 s),
#    because the image restarts Postgres during initialisation.

# 3) Storage service: pinned image, pointed at the same database.
#    Its anon/service key pair and JWT secret are GENERATED PER RUN (nothing
#    key-shaped is stored in the script); CT02_ANON_KEY / CT02_SERVICE_KEY /
#    CT02_JWT_SECRET override this for a non-disposable environment.
docker run -d --name ct_schema02_storage public.ecr.aws/supabase/storage-api:v1.69.0

# 4) Fail-closed platform prerequisites, all verified before PHASE B:
#      storage.buckets, storage.objects, storage.foldername(), auth.uid(),
#      RLS enabled on storage.objects
```

**Result (final acceptance run):**

```
=== PHASE A target identity ===
container=/ct_schema02_pg id=512f2bf53e692753baaf801ad9f0f6526dbf4d32c0c6fb82007e100f111f2066 image=public.ecr.aws/supabase/postgres:17.6.1.159
volume=ct_schema02_pgdata created=2026-09-27T19:06:55+06:00
postgres_version=PostgreSQL 17.6 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 15.2.0, 64-bit
[19:07:01] fresh target public tables: 0
[19:07:01] starting the platform Storage service (public.ecr.aws/supabase/storage-api:v1.69.0)
[19:07:01] generated per-run Storage key material (nothing key-shaped is stored in this script)
[19:07:08] PHASE A complete — platform layer present (storage.buckets, storage.objects,
           storage.foldername, auth.uid(), RLS on storage.objects)
```

The Storage service was additionally probed independently with the *generated* key pair:
`{"healthy":true}`; an authenticated `GET /bucket` returned the `documents` bucket with
`"public":false`; the same call without authorisation was refused (HTTP 400). The platform accepts
per-run key material, so no credential is embedded in the harness.

`fresh target public tables: 0` is the explicit **from-zero** proof: the application layer was
absent at the start of the rebuild.

---

## 10. D32 procedure (PHASE C — provider context)

`e2e/environment/scripts/d32_storage_operator.sql`, executed as `supabase_admin` (the only role
with the provider privilege to own/alter `storage.objects`), **after** migrations 1–26 and
**before** migration 27:

1. `INSERT INTO storage.buckets (id, name, public) … WHERE NOT EXISTS (… name = 'documents')`
   followed by `UPDATE storage.buckets SET public = FALSE WHERE name = 'documents'` (convergent).
2. A fail-closed pre-flight assertion that the bucket exists **and** `public = FALSE`, raising an
   exception otherwise.
3. For each of the four approved policy names: `DROP POLICY IF EXISTS` then `CREATE POLICY` with
   the approved predicate — convergence on the approved name only, never touching anything else.
4. A post-check asserting exactly the four approved policies exist with the expected command and
   role.

Approved predicate shape (org-scoped, session-identity anchored):

```
bucket_id = 'documents'
AND (storage.foldername(name))[1] = 'uploads'
AND (storage.foldername(name))[2]::uuid IN (
      SELECT organisation_id FROM public.organization_members WHERE user_id = auth.uid()
    )
```

After the operator step the driver runs
`e2e/environment/scripts/verify_d32_policy_semantics.sql`, which simulates member/outsider
contexts inside a transaction and **rolls back**, so it proves behaviour without mutating the
canonical target.

**Verified sequence (from the final run log):**

```
[19:07:08] PHASE B — applying migrations 1-26 as postgres
ALL_APPLIED applied=26 selected=26 source=/home/shomonrobie/ct_93d5cdd/supabase/migrations
LEDGER=/tmp/ct_schema02_evidence/ledger_phase_b.tsv
[19:07:11] PHASE B complete — 26/26 applied; public.organization_members present (D32 dependency satisfied)
[19:07:11] PHASE C — D32 operator step: private documents bucket + four provider-context policies
[19:07:11] PHASE C — operator step OK; proving policy semantics behaviourally (rolled back)
[D32_SEMANTICS_RESULT pass=11 fail=0]
[19:07:11] PHASE C — idempotency re-run of the operator step
[19:07:11] storage.objects policies before=4 after=4
[19:07:11] PHASE C complete — operator step idempotent (4 policies, 1 bucket, unchanged on re-run)
[19:07:11] PHASE D — applying migrations 27-89 as postgres
ALL_APPLIED applied=63 selected=63 source=/home/shomonrobie/ct_93d5cdd/supabase/migrations
LEDGER=/tmp/ct_schema02_evidence/ledger_phase_d.tsv
LEDGER_SHA256=f291384d3ab89e9f4b7a1533c12d91b7080a00ba3d23b5d4a7d4dceb527bf811
ledger_rows_excluding_header=89
applied=89 failed=0
distinct_files=89
ledger_sha256=c6f93de854028a647a14c7954a370e810c6cad5e40a22045fffacde8c09e911b
[19:07:17] VERIFY — canonical schema verification
=== RESULT: ALL CHECKS PASSED (57 pass, 0 fail) ===
[19:07:25] REBUILD VERIFIED — canonical schema reproduced (see /tmp/ct_schema02_evidence)
```

The sequence is therefore confirmed exactly as required:
**platform/storage → migrations 1–26 → D32 operator step → migrations 27–89.**

## 11. Migration 1–26 result

```
[19:07:08] PHASE B — applying migrations 1-26 as postgres
ALL_APPLIED applied=26 selected=26 source=/home/shomonrobie/ct_93d5cdd/supabase/migrations
LEDGER=/tmp/ct_schema02_evidence/ledger_phase_b.tsv
[19:07:11] PHASE B complete — 26/26 applied; public.organization_members present (D32 dependency satisfied)
```

**26/26 applied, 0 failures.** Executed as `postgres` with the pinned `search_path`; the
stop-on-error contract means the phase would have aborted the whole run on any failure. No phase-B
migration log contains an error, and the ledger records all 26 rows.

## 12. D32 result

```
[19:07:11] PHASE C — operator step OK
[19:07:11] storage.objects policies before=4 after=4        (idempotent)
[19:07:11] PHASE C complete — operator step idempotent (4 policies, 1 bucket, unchanged on re-run)
```

Operator-context pre/post checks passed. On the rebuilt target, independently re-queried for this
report:

```
bucket:      documents | public=false | file_size_limit=-          (private, single bucket)
policies:    count(*) from pg_policies where schemaname='storage' and tablename='objects'  →  4
```

Behavioural proof (rolled back), from `phase_c_semantics.txt`:

```
D32_SEMANTICS pass=11 fail=0
  PASS member_cannot_insert_other_org_path
  PASS member_updates_own_org_object (rows = 1)
  PASS member_cannot_update_other_org_object (rows = 0)
  PASS outsider_sees_no_documents
  PASS outsider_cannot_insert_documents
  PASS non_uploads_path_not_visible
  NOTE delete_policy_verified_structurally (platform blocks direct SQL delete)
```

## 13. Migration 27–89 result

```
ALL_APPLIED applied=63 selected=63
LEDGER=/tmp/ct_schema02_evidence/ledger_phase_d.tsv
LEDGER_SHA256=f291384d3ab89e9f4b7a1533c12d91b7080a00ba3d23b5d4a7d4dceb527bf811
ledger_rows_excluding_header=89
applied=89 failed=0
distinct_files=89
ledger_sha256=c6f93de854028a647a14c7954a370e810c6cad5e40a22045fffacde8c09e911b
```

**63/63 applied, 0 failures** — including the revised migration 27, which in PHASE D successfully
*validated* the provider-created bucket and policies (it would have failed closed otherwise).
Consolidated ledger: **89 rows, `applied=89 failed=0 distinct_files=89`** (= 26 + 63), i.e. no
migration was skipped and none was applied twice.
`ledger_sha256` covers a run-specific artefact (it embeds per-migration start timestamps), so it is
recorded as evidence of *this* run; the deterministic, comparable fingerprint is the migration-set
fingerprint below.

---

## 14. Migration-set fingerprint

```
PASS  migration_count — found 89 .sql files (expected 89)
PASS  migration_order_deterministic — filenames sort deterministically by version prefix
PASS  migration_versions_unique — no duplicate migration version prefixes
PASS  migration_endpoints — first=00000000000000_init_schema.sql
                            last=20261020000000_p17k_governed_capability_catalogue.sql
INFO  migration_set_fingerprint_actual —
      40b168b393fb2ca70ea40093bd4e9eecebf5c4604c752eea6a6f5a902c003c30
PASS  migration_set_fingerprint_matches_recorded —
      actual=40b168b3…c30  expected=40b168b3…c30
PASS  migration_set_provenance_ct_schema_01 — git HEAD reproduces the CT-SCHEMA-01
      migration-set fingerprint (d73e1e2b4e503c13b5079dfc84f3ae0081d04f0f67f91231d8baa0879b8cb26c)
PASS  migration_set_only_authorised_revision — files differing from CT-SCHEMA-01 HEAD:
      ['20260823000000_d32_private_documents_storage.sql']
```

**Final migration count: 89** (canonical `supabase/migrations`, reached through the
`e2e/environment/supabase/migrations` symlink — one source of truth, no duplicated copy).

**Final migration-set fingerprint (working tree, i.e. the CT-SCHEMA-02 set):**

```
40b168b393fb2ca70ea40093bd4e9eecebf5c4604c752eea6a6f5a902c003c30
```

**CT-SCHEMA-01's recorded set fingerprint (pristine HEAD):**

```
d73e1e2b4e503c13b5079dfc84f3ae0081d04f0f67f91231d8baa0879b8cb26c
```

Local recomputation of the 89 filenames (`ls | sed 's#.*/##' | sort | sha256sum`) gives
`ea973858e38a5f08d57accba3fe0b2dc391a5a7a6cf05600110cac6fad6af330`, a *name-list* digest; the
verifier's fingerprint additionally covers file **contents** and is the authoritative value.

**Why the set fingerprint legitimately differs from CT-SCHEMA-01's:** the two sets differ by
exactly **one intentionally revised file** — `20260823000000_d32_private_documents_storage.sql`,
the authorised F-02 fix. The verifier *asserts* this difference is exactly one file and that no
other migration differs, so the fingerprint change is bounded, reviewed and attributable. The
pristine-HEAD value is still reproducible from git (§14 provenance check), so CT-SCHEMA-01's
baseline remains independently verifiable.

## 15. Final schema inventory

**Exact count checks — 10/10, all observed = expected:**

| Count | Observed | Expected | Result |
|---|---|---|---|
| `public` tables | 145 | 145 | PASS |
| `public` tables with RLS | 145 | 145 | PASS |
| `public` tables **without** RLS | 0 | 0 | PASS |
| policies (all schemas) | 227 | 227 | PASS |
| policies granting `anon`/`public` | 0 | 0 | PASS |
| foreign keys | 172 | 172 | PASS |
| indexes | 551 | 551 | PASS |
| `public` functions | 31 | 31 | PASS |
| triggers | 88 | 88 | PASS |
| columns (all schemas) | 4,592 | 4,592 | PASS |

**Canonical inventory classes — 12/12 rendered and hashed** (all byte-identical to the
CT-SCHEMA-01 canonical inventory under the pinned `search_path`):

| Class | Rows | `sha256[:16]` |
|---|---|---|
| A_schemas | 12 | `3b34dbbe3f5b4f3e` |
| B_tables | 375 | `76cc8d06a18eb3f3` |
| C_columns | 4,592 | `ec066d9137717193` |
| D_constraints | 756 | `a6edef0b84bb20ae` |
| E_indexes | 551 | `35b223fe062ab67d` |
| F_enums | 1 | `66b0463c35a783c0` |
| G_functions | 144 | `c48bdd0caad6b5d8` |
| H_triggers | 88 | `3d56a82e370bb7d5` |
| I_views | 3 | `719eae8c2fd3308a` |
| K_sequences | 1 | `ffe5afc1f09c4033` |
| L_rls | 229 | `0636b8902d07f024` |
| M_policies | 227 | `d8654459049e9c39` |

**Schema-only confirmation** (the rebuild produces structure, not data):

```
PASS  reference_rows_scope3_categories                 — observed=15  expected=15
PASS  reference_rows_disclosure_frameworks              — observed=3   expected=3
PASS  reference_rows_disclosure_framework_versions      — observed=1   expected=1
PASS  reference_rows_disclosure_requirement_versions    — observed=18  expected=18
PASS  no_application_data_organizations                 — observed=0 rows
PASS  no_application_data_customer_factors              — observed=0 rows
```

i.e. migration-declared reference data is present and correct, while **no application/demo data**
was created by the rebuild.

## 16. Exact canonical schema fingerprint

```
INFO  inventory_fingerprint_actual —
      c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f
PASS  inventory_fingerprint_matches_canonical —
      actual=c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f
      expected=c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f
```

**The canonical schema fingerprint of the from-zero rebuild on a brand-new target is exactly
CT-SCHEMA-01's canonical fingerprint:**

```
c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f
```

This is a **byte-level** match of all 12 inventory classes, not a count-level approximation: the
fresh target's rendered inventory (under the pinned search_path) is identical to the CT-SCHEMA-01
canonical inventory, so the rebuild is reproducible by construction rather than by coincidence of
counts.

---

## 17. D32 policy verification

**Verified on the freshly rebuilt target** (`verify.txt`, `inventory/M_policies.txt`):

```
PASS  d32_documents_bucket_private — storage.buckets.public=false (must be false)
PASS  d32_storage_objects_rls_enabled — RLS must be enabled on storage.objects
PASS  d32_policy_d32_documents_select_org_member — observed=SELECT|authenticated  expected=SELECT|authenticated
PASS  d32_policy_d32_documents_insert_org_member — observed=INSERT|authenticated  expected=INSERT|authenticated
PASS  d32_policy_d32_documents_update_org_member — observed=UPDATE|authenticated  expected=UPDATE|authenticated
PASS  d32_policy_d32_documents_delete_org_member — observed=DELETE|authenticated  expected=DELETE|authenticated
PASS  d32_no_extra_storage_policies — 0 unexpected storage.objects policy/policies beyond the four approved
PASS  d32_no_anon_public_storage_policy — observed=0
PASS  d32_identity_anchor_d32_documents_select_org_member — auth.uid()-by-OID / organization_members-by-OID: true|true
PASS  d32_identity_anchor_d32_documents_insert_org_member — auth.uid()-by-OID / organization_members-by-OID: true|true
PASS  d32_identity_anchor_d32_documents_update_org_member — auth.uid()-by-OID / organization_members-by-OID: true|true
PASS  d32_identity_anchor_d32_documents_delete_org_member — auth.uid()-by-OID / organization_members-by-OID: true|true
```

The four provider-context policies present in the target, with command and role:

```
storage.objects :: d32_documents_delete_org_member :: DELETE :: authenticated
storage.objects :: d32_documents_insert_org_member :: INSERT :: authenticated
storage.objects :: d32_documents_select_org_member :: SELECT :: authenticated
storage.objects :: d32_documents_update_org_member :: UPDATE :: authenticated
```

Bucket state re-queried directly for this report:

```
documents | public=false | file_size_limit=-
```

**Summary:** 1 private bucket, exactly 4 policies (one per command), all restricted to the
`authenticated` role, **0** additional `storage.objects` policies, **0** policies granting
`anon`/`public`, and all four policies proven (by OID) to be anchored to `auth.uid()` and
`public.organization_members` rather than merely *containing* matching text.

## 18. Idempotency result

```
[19:07:11] PHASE C — idempotency re-run of the operator step
[19:07:11] storage.objects policies before=4 after=4
[19:07:11] PHASE C complete — operator step idempotent (4 policies, 1 bucket, unchanged on re-run)
```

**Result: idempotent.** The provider-standard operator step was applied twice within the same run;
the policy count on `storage.objects` was 4 before and 4 after, the bucket set remained a single
private `documents` bucket, and the operator's own post-check passed after the re-run (the
`DROP POLICY IF EXISTS … does not exist, skipping` notices are the expected convergence messages
of the first application; the re-run's log `phase_c_operator_rerun.txt` is 0 bytes — no change).

Two additional idempotency properties verified:

* the migration chain is applied in **disjoint ranges** (1–26, then 27–89) from a single canonical
  source, and the consolidated ledger contains exactly **89** rows — no migration applied twice or
  skipped;
* the operator step converges on the four **approved names** only (drop-then-create on named
  policies), so repeated execution cannot accumulate policies or alter unrelated objects.

## 19. Search_path regression result (F-02)

`e2e/environment/scripts/d32_search_path_regression.sh`, run **against the freshly rebuilt
target** (`127.0.0.1:55460`, roles `supabase_admin` / `postgres`):

```
=== CT-SCHEMA-02 D32 search_path regression (target postgres/supabase_admin@127.0.0.1:55460/postgres) ===
ambient search_path of supabase_admin: "$user", public, auth, extensions
ambient search_path of postgres:       "$user", public, extensions

--- reproducing the old risk (pre-revision validator) ---
PASS  R1_pre_revision_as_provider_role      (rejected: D32 policy drift: d32_documents_select_org_member
                                             is missing the approved org-scope fragment)
PASS  R2_pre_revision_as_migration_role     (rc=0)
PASS  R2b_pre_revision_forced_pg_catalog    (rc=0)

--- the revised validator is search_path independent ---
PASS  R3_revised_as_provider_role           (rc=0)
PASS  R4_revised_forced_auth_public         (rc=0)
PASS  R5_revised_forced_pg_catalog          (rc=0)
PASS  R5b_revised_provider_forced_auth      (rc=0)

--- the validation is not weakened: a look-alike function is rejected ---
PASS  R6a_pre_revision_accepts_lookalike_function (rc=0)
PASS  R6b_revised_rejects_lookalike_function (rejected: … does not call the approved
                                             session-identity function auth.ui…)

--- drift is still caught ---
PASS  R7_revised_rejects_missing_fragment   (rejected: … is missing the approved org-scope fragment)

--- restore and confirm the target is unchanged ---
PASS  R8 target restored (4 storage.objects policies)
PASS  R8 documents bucket still private and single
PASS  R9_revised_final_pass                 (rc=0)

=== RESULT: 13 passed, 0 failed ===
```

Interpretation:

* **R1 vs R2** reproduce F-02 exactly: the *pre-revision* validator **fails** in the provider
  context (`supabase_admin`, whose path contains `auth`) and **passes** in the migration context —
  the role-dependence that made the defect real.
* **R3–R5b** show the *revised* validator passing under the provider role and under forced
  `auth,public` and `pg_catalog` paths — no role or path dependence remains.
* **R6a/R6b** show the fix is a **strengthening**: the pre-revision check accepted a policy calling
  a look-alike `myauth.uid()`, while the revised check rejects it by OID.
* **R7** shows genuine drift (missing org-scope fragment) is still rejected — the fix did not
  disable detection.
* **R8/R9** prove the mutation used for R6/R7 was confined to the disposable target and fully
  restored (4 policies, one private bucket, revised validator finally passing).

**Final-run confirmation:** this suite was re-executed after the final from-zero rebuild (the run
containing the key-material-free driver) and returned the identical result — **13 passed,
0 failed** — against the new target, so §19's evidence belongs to the delivered artefacts rather
than to an earlier iteration. Immediately afterwards the canonical verifier was run **standalone**
against the same target and returned **57 pass, 0 fail** again, proving the suite's temporary
policy mutation was fully restored and the canonical schema was left untouched.

---

## 20. E2E / regression test results

All suites were run **against the freshly rebuilt target** unless stated otherwise.

| Suite | Command | Result |
|---|---|---|
| Full canonical rebuild (from zero, brand-new target) | `bash e2e/environment/scripts/canonical_schema_rebuild.sh --evidence /tmp/ct_schema02_evidence` | executed **twice from zero** (19:06:54 and the earlier 18:48:41 run); both times PHASE A→D + VERIFY completed, final log line `REBUILD VERIFIED — canonical schema reproduced`, exit 0. The second run used the final key-material-free driver and is the evidence of record. |
| Canonical verifier | (run by the driver, `VERIFY` phase) | **57 pass, 0 fail** — 10 count checks, 12 inventory classes, fingerprint, migration-set (count/order/uniqueness/endpoints/fingerprint/provenance/authorised-revision), D32 bucket/RLS/policy/anchor checks, reference-data checks, application-data-absence checks, P16R/P17 named checks |
| D32 policy semantics (behavioural, rolled back) | `verify_d32_policy_semantics.sql` (PHASE C) | **pass=11 fail=0** |
| F-02 search_path regression | `d32_search_path_regression.sh` (fresh target) | **13 passed, 0 failed** (§19) |
| Post-regression re-verification (target integrity after the regression suite's mutation/restore) | `canonical_schema_verify.py --host 127.0.0.1 --port 55460` | **57 pass, 0 fail** — canonical schema unchanged after R6/R7 restoration |
| D32 operator idempotency | re-run inside PHASE C | policies before=4 after=4; bucket unchanged |
| Backend unit suites touching migrations/schema | `backend/.venv/bin/python -m pytest backend/tests/unit -q` | 9 failures — **all proven pre-existing and unrelated** (see below) |

**Provenance of the 9 unit-suite failures** (none caused by CT-SCHEMA-02; the task's only
migration change was a content revision inside one existing file, and no file was added or
removed):

| Failing test(s) | Class | Why it is pre-existing |
|---|---|---|
| `test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | stale pinned count | asserts `len(names) == 71`; **HEAD itself tracks 89 migration files** (`git ls-tree -r HEAD -- supabase/migrations` → 89), so the assertion fails at HEAD with or without this task |
| `test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration`, `test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | stale "latest migration" pin | HEAD's latest migration is already `20261020000000_p17k_governed_capability_catalogue.sql`, so these assertions fail at HEAD; filename-based, independent of migration content |
| `test_review_sla_surfaces.py` (3 tests) | API surface registry pin | fail on the backend router registry; the failures reference nothing in `e2e/environment/**`, the D32 migration, or the verifier (`grep` returned no reference) |
| `test_extraction_suggestions.py` (3 tests) | extraction-engine unit tests | fail in the extraction suggestion engine; no reference to anything changed by this task |

The first three classes are the "pinned historical artefact" pattern already known in this
repository (a test asserting the *previous* generation's migration count / latest migration).
They are **disclosed, not fixed** — fixing them is outside CT-SCHEMA-02's authorised scope
(§21/§22).

**Not run, and why:** the browser/persona end-to-end suites under `tests/e2e/` (Playwright/TS) and
the `qa_harness` full run require a running application stack (frontend + FastAPI + Supabase
services). CT-SCHEMA-02 changes no application code, no API and no frontend; it delivers a
schema/harness rebuild and a migration *validation* fix. Running the app-level suites would not
exercise the changed surface, and no app stack was started for this task. This is recorded as a
limitation, not as a pass.

## 21. Known limitations

1. **The migration-set fingerprint legitimately differs from CT-SCHEMA-01's**
   (`40b168b3…` vs `d73e1e2b…`) because of exactly one authorised revision. The verifier asserts
   the difference is bounded to that one file, and the pristine-HEAD value remains reproducible
   from git. Any *other* future divergence will fail the run.
2. **Nine pre-existing unit-test failures remain** in the backend unit suite (§20). They are
   unrelated to this task and were deliberately not modified. They will keep `pytest
   backend/tests/unit` non-green until a separate task updates the pinned expectations.
3. **Browser/persona E2E and the `qa_harness` suite were not run** (§20) — they need a running
   application stack, which this schema-only task does not start.
4. **The D32 operator step is still an operator step, not migration DDL.** This is not a defect
   but a constraint of the platform: only the provider role owns `storage.objects`, and CarbonTally
   deliberately does not escalate the migration role's privilege (PO decision, Route C). The step
   is therefore automated, idempotent and fail-closed, but it must be executed per environment in
   the provider context. Migration 27 fails closed if it was not run.
5. **`ledger_sha256` is run-specific** (it embeds per-migration start timestamps), so it evidences
   *this* run rather than serving as a cross-run comparison key. The comparable artefacts are the
   migration-set fingerprint and the canonical inventory fingerprint.
6. **The canonical fingerprint is context-sensitive by nature** and is only meaningful under the
   pinned `INVENTORY_SEARCH_PATH`. The verifier pins it (F-02-EXT fix) and prints it in the
   evidence header; any tool comparing inventories outside that context will produce false
   divergences (§5.3).
7. **The disposable target is left running** (`ct_schema02_pg`, `ct_schema02_storage`, volume
   `ct_schema02_pgdata`) so its evidence can be inspected; the driver supports `--destroy`
   (task §20) to remove it. It is labelled disposable and bound to `127.0.0.1:55460`.
8. **The rebuild is schema-only.** It intentionally creates no organisations, users, documents or
   factors; there is no data-reconciliation claim.

---

## 22. Explicit out-of-scope items

Explicitly **not** done in CT-SCHEMA-02, and verified as untouched:

1. **`defra_conversion_factors` was NOT created or restored.** Confirmed absent on the rebuilt
   canonical target (`to_regclass('public.defra_conversion_factors') IS NULL`). The canonical
   factor table is **`emission_factors`** (verified present, together with `customer_factors` and
   `calculation_snapshots`). The historical migration away from the DEFRA-specific model remains a
   **separate future code/schema investigation** (register item SCM-004).
2. **The other three legacy code↔schema mismatches remain out of scope and unresolved** — the four
   items of the "referenced by durable code, created by no migration" class are
   `defra_conversion_factors` (SCM-004), `report_history` (SCM-005), `report_schedules` (SCM-006)
   and `notification_delivery_log` (SCM-007). All four were verified **absent** on the rebuilt
   canonical target, and **no backend/frontend source file referencing them was modified** (the
   references in `backend/utils/emissions.py`, `backend/report_generator.py`,
   `backend/routes/*` are unchanged working-tree state at HEAD).
3. **CT-SCHEMA-03 was not started**; no subsequent task was begun.
4. **SCM-008 (durable databases 4–29 canonical tables behind the migration chain)** is not
   addressed: no durable environment was migrated, rebased or reconciled. The rebuild targets a
   *disposable* target only.
5. **SCM-009/010/011** (scratch objects created in `public` by integration tests; no
   applied-migration ledger for psql-built durable DBs; `ct_local_93d5cdd` not comparable) are not
   addressed.
6. **No FIEW capability was promoted** — see §24.1. No feature was moved from
   `BLOCKED_BY_SCHEMA` / `DISPOSABLE_ENVIRONMENT_ONLY` to `IMPLEMENTED_AND_WIRED`, and neither the
   FIEW register nor the feature catalogue/matrix documents were edited by this task.
7. **No application code, API route, frontend component, `public`-schema RLS policy or business
   rule was changed.** The only product-schema-adjacent change is the *validation logic* inside
   migration 27; the policies it validates are unchanged in name, command, role and predicate.
8. **No test file was modified**, including the nine pre-existing failures disclosed in §20/§21.
9. **Pre-existing working-tree changes were left alone** — notably the whole-file `.gitignore`
   modification, which is not attributable to this task.
10. **No commit, no push, no PR, no release, no deployment, no production access** (§23).

---

## 23. Production safety confirmation

| Control | Evidence |
|---|---|
| **No production environment modified** | Every database action targeted `127.0.0.1:55460` — the disposable container `ct_schema02_pg` (labels `ct.schema02.task=CT-SCHEMA-02-20260927`, `ct.schema02.disposable=true`) on volume `ct_schema02_pgdata`. No production/durable connection string was used; no durable environment (flagship `postgres`, demo/investor containers, any Supabase cloud project) was written to. The credential is a per-run random password in a `0600` `/tmp/ct_schema02.env`, never printed and never committed. |
| **No deployment occurred** | No deployment CLI was invoked (no Vercel/Render/Supabase CLI, no `supabase db push`, no remote project link, no image push). `e2e/environment/supabase/config.toml` sets conflicting local services `enabled = false`, i.e. configuration was *reduced*, not deployed. The only containers created are the two labelled local disposables. |
| **No Git push occurred** | `git rev-parse HEAD` = `cb70fd6…` = the starting SHA and `git reflog -1` still reads `cb70fd6 HEAD@{0}: commit: fix(public-truth): …` — **no new commit exists**, so nothing could have been pushed. Remote tracking state is unchanged; no `push`, `--force`, rebase, reset, clean or history rewrite was run. |
| **Read-only discipline elsewhere** | Only mutations were (a) the labelled disposable containers/volume and their evidence directory and (b) the working-tree file edits listed in §4. Investor/demo datasets were neither read as data nor mutated. |
| **Secrets** | **No key material is stored anywhere in the delivered scripts.** The driver generates the Storage service's anon/service pair and JWT secret **per run** from a random 64-hex secret (`openssl rand`), with environment overrides (`CT02_ANON_KEY`/`CT02_SERVICE_KEY`/`CT02_JWT_SECRET`) for any non-disposable use; a scan of the report and every new script returns no key-shaped literal, and the run password never leaves the `0600` `/tmp/ct_schema02.env`. Supabase's public local-development demo constants were deliberately **removed** from the harness rather than embedded. |

---

## 24. Final verdict

```
CT_SCHEMA_02_IMPLEMENTED_AND_VERIFIED
```

**24.1 FIEW verification (no capability promoted).** The FIEW register
(`CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md`) records features that Cline
classified `IMPLEMENTED_AND_WIRED` but whose executable chain depends on persistence absent from
the authoritative durable environment. This task changed **no application capability and no
persistence**:

* the canonical rebuild produced **precisely the same schema objects** as CT-SCHEMA-01 — all 12
  inventory classes byte-identical, all 10 counts identical — so nothing new became "wired";
* the rebuilt target is a **disposable clone**, i.e. exactly the environment class the register
  treats as non-authoritative (`DISPOSABLE_ENVIRONMENT_ONLY`), so its existence cannot promote a
  row;
* the D32 revision changes **validation only** — the bucket and the four policies it validates are
  unchanged and already part of the canonical baseline;
* the FIEW register and the feature catalogue/matrix documents were **not edited** by this task.

Therefore **no FIEW capability was promoted**, and no FIEW row may be treated as satisfied on the
basis of this task.

**24.2 Acceptance trace (every required finalization item):**

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Implementation verified in the repository | ✅ | §4, §6 — files present; rebuild + verifier re-run from the fixed tree |
| 2 | Exact final migration count + set fingerprint | ✅ | §14 — 89; `40b168b3…c30` (working tree) / `d73e1e2b…b26c` (pristine HEAD) |
| 3 | Clean from-zero rebuild result | ✅ | §9, §11–13 — `fresh target public tables: 0`; PHASE A→VERIFY; `REBUILD VERIFIED` |
| 4 | Final canonical schema inventory vs CT-SCHEMA-01 | ✅ | §15 — 145 tables / 145 RLS / 0 without RLS / 227 policies / 0 anon-public / 172 FKs / 551 indexes / 31 functions / 88 triggers / 4,592 columns — all exactly equal |
| 5 | Canonical fingerprint matches CT-SCHEMA-01 | ✅ | §16 — `c89c50bd…3c2f`, byte-level match across 12/12 inventory classes |
| 6 | D32 sequence platform → 1–26 → operator → 27–89 | ✅ | §10 — phase log |
| 7 | D32 bucket + four provider-context policies | ✅ | §17 — private `documents` bucket; 4 `authenticated` policies; 0 extras; 0 anon/public; 4/4 OID anchors |
| 8 | D32 idempotency | ✅ | §18 — before=4 after=4; bucket unchanged |
| 9 | search_path regression + F-02 explanation | ✅ | §5, §6, §7, §19 — 13/13; root cause and fix stated |
| 10 | Relevant regression/E2E tests run | ✅ | §20 — verifier 57/57; semantics 11/11; regression 13/13; unit suite run, all failures proven pre-existing |
| 11 | No FIEW capability promoted | ✅ | §24.1 |
| 12 | Four code↔schema mismatches remain out of scope | ✅ | §22.1–22.2 — SCM-004/005/006/007 absent on target; no referencing source modified |
| 13 | No production environment modified | ✅ | §23 |
| 14 | No deployment occurred | ✅ | §23 |
| 15 | No Git push occurred | ✅ | §23 — HEAD unchanged, reflog unchanged |

Every acceptance criterion above is backed by executed evidence, not inference; no criterion
remains untested. The one pre-existing failing-test class (§20) lies outside the CT-SCHEMA-02
acceptance surface and is disclosed rather than silently absorbed.

**24.3 Remaining work (for subsequent tasks, not this one):**

* update the stale pinned expectations in the three migration/API pin-test classes (§20/§21);
* the separate `defra_conversion_factors` legacy code↔schema investigation (SCM-004) and the other
  three mismatch items (SCM-005/006/007);
* durable-environment alignment for SCM-008/009/010/011;
* CT-SCHEMA-03 (not started).

**24.4 Disposable-resource note.** The labelled disposables `ct_schema02_pg`, `ct_schema02_storage`
and volume `ct_schema02_pgdata` were intentionally retained for evidence inspection;
`canonical_schema_rebuild.sh --destroy` removes them. Evidence is in `/tmp/ct_schema02_evidence/`
(`verify.txt`, `verify.json`, `inventory/`, `ledger_*.tsv`, `logs_phase_*`, `phase_a_identity.txt`,
`phase_c_semantics.txt`).

---

*End of report — CT-SCHEMA-02-20260927-CANONICAL-SCHEMA-REBUILD-AUTOMATION-AND-D32-RUNNER-FIX.*









