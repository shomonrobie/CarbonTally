# CarbonTally P6-2F — Isolated E2E Environment

This directory provisions a **dedicated, isolated Supabase stack** for the P6-2F
UI/UX + E2E security acceptance gate (`PO-PHASE6-F-ENV-20260910`).

> **Never reuse the investor/demo instance.** The demo project is
> `carbon_ledger` (API `127.0.0.1:54425`, DB `127.0.0.1:54426`). This
> environment is project **`carbontally_e2e`** (API `127.0.0.1:55325`, DB
> `127.0.0.1:55326`) — separate containers, separate database, separate data.

## CT-SCHEMA-02 — the canonical two-layer rebuild model

CT-SCHEMA-01 verified that the 89-file migration chain reproduces the canonical
application schema **from zero**, and established that it is a *two-layer*
artifact: the chain needs a Supabase platform layer (auth + Storage) that no
CarbonTally migration creates, and exactly one operator step that needs provider
privilege. The canonical sequence is:

```
LAYER 1  PLATFORM      Supabase Storage service provisions storage.*
                       (bare PostgreSQL has no storage.objects — F-01)
   |
LAYER 2  migrations 1-26          creates public.organization_members, which the
   |                              approved storage predicates reference (F-03)
   |
   D32 OPERATOR STEP              private `documents` bucket + the four approved
   |                              provider-context policies on storage.objects
   |                              (provider privilege; cannot be a migration)
   |
   migrations 27-89               migration 27 validates what the operator created
   |
   VERIFICATION                   migration set, inventory, fingerprint, D32, P17/P16R
```

Two contracts make this reliable:

| Contract | Migration role | Provider role |
|---|---|---|
| Role | `postgres` (ordinary, no ownership of provider objects — PO decision Route C) | `supabase_admin` locally, or the Supabase dashboard storage-policy editor |
| Used for | migrations 1-26 and 27-89 | the D32 operator step only |
| `search_path` | pinned explicitly (`"$user", public, extensions`) and verified before the first file runs | n/a |

Migration `20260823000000_d32_private_documents_storage.sql` (revision
`P8-D17-D32-STORAGE-POLICY-VALIDATION-DETERMINISM-001`) validates the four
policies **search_path-independently**: it pins its own evaluation context and
asserts the identity of `auth.uid()` and `public.organization_members` **by
OID**, so a rebuild can no longer pass or fail because of the caller's session
`search_path`, and a look-alike `myauth.uid()` cannot satisfy the check.

## Layout

```
e2e/environment/
  supabase/config.toml          isolated project_id + remapped ports;
                                [db.migrations] enabled = false (the CLI must not
                                apply the application chain — see below)
  supabase/migrations           SYMLINK to ../../../supabase/migrations
  scripts/apply_migrations.sh   canonical migration runner (--from/--to/--expect-count,
                                pinned search_path, independent ledger, fail-closed)
  scripts/d32_storage_operator.sql   the D32 operator step (idempotent, fail-closed)
  scripts/verify_d32_policy_semantics.sql  behavioural proof of the four policies
                                (runs as `authenticated`; always rolled back)
  scripts/d32_search_path_regression.sh    reproduces F-02 and proves the fix
  scripts/canonical_schema_rebuild.sh      from-zero rebuild driver (PHASE A-D)
  scripts/canonical_schema_verify.py       canonical inventory/fingerprint verifier
  scripts/capture_env.sh        writes .env.e2e from `supabase status -o env` (gitignored)
  scripts/bootstrap.sh          platform + canonical sequence + env + fixtures
  scripts/reset.sh              same, from a reset database
  scripts/teardown.sh           stop + remove the isolated stack (disposable)
```

`supabase/migrations` in this directory is a **symlink** to the canonical
`supabase/migrations`. It used to be a 53-file copy that had drifted from the
canonical set (including a pre-revision D32); that copy is gone, so the harness
cannot silently apply a different chain from the one that was verified.

## Ports (no overlap with the demo instance)

| Service | Demo | **Isolated E2E** |
|---|---|---|
| API / PostgREST / Auth | 54425 | **55325** |
| Postgres | 54426 | **55326** |
| Studio | 54423 | **55323** |
| Inbucket (email) | 54424 | **55324** |
| Shadow DB | 54420 | **55320** |
| Pooler | 54429 | **55329** |

## Bring-up

```bash
bash e2e/environment/scripts/bootstrap.sh      # platform + canonical schema + env + fixtures
```

`bootstrap.sh` prints the target URL/DB and both roles before doing anything, so
destructive steps are always against the isolated instance.

## Reset / teardown

```bash
bash e2e/environment/scripts/reset.sh          # reset DB + re-apply canonical sequence
bash e2e/environment/scripts/teardown.sh       # stop + remove the isolated stack
```

## From-zero rebuild on a brand-new disposable target (no Supabase CLI)

`canonical_schema_rebuild.sh` builds the canonical schema on a fresh disposable
PostgreSQL/Supabase-compatible target using the real platform images (the same
images the CLI stack uses) and verifies it against the CT-SCHEMA-01 canonical
inventory and fingerprint:

```bash
bash e2e/environment/scripts/canonical_schema_rebuild.sh            # PHASE A-D + VERIFY
bash e2e/environment/scripts/canonical_schema_rebuild.sh --destroy  # …and clean up
```

It fails loudly if the platform Storage layer is absent, if the migration count
is not 26 + 63, if any migration fails, if the D32 operator step is not
idempotent, if the D32 semantics proof fails, or if the final inventory or
migration-set fingerprint differs from the recorded canonical values.

### Reproducibility (CT-RELEASE-04)

Everything the rebuild needs is repository-controlled: a clean checkout of the
commit that carries this section can execute

```bash
bash e2e/environment/scripts/canonical_schema_rebuild.sh --profile ct-implement-02
```

and reproduce the canonical 92-migration environment. No untracked file, ignored
file, developer-specific path, second worktree or manually prepared SQL is
required. The provenance check in `canonical_schema_verify.py` is **HEAD-scoped**:
a migration file — including the authorised D32 revision — may differ from `HEAD`
only while `HEAD` does not yet contain it, so a clean checkout (where nothing can
differ from `HEAD`) satisfies it as well.

`scripts/fixtures/d32_pre_revision_ct_schema_01.sql` is a byte-identical copy of
the CT-SCHEMA-01-verified D32 file as it stood **before** the
P8-D17-D32-STORAGE-POLICY-VALIDATION-DETERMINISM-001 revision (sha256
`45d9eb87…5421798`, git blob `66a8ddf`). It is **not** a migration — the runner
only ever reads `supabase/migrations` — and exists solely so
`d32_search_path_regression.sh` can reproduce F-02 without depending on git
history. That script asserts the fixture's hash and that it differs from the
current migration before it runs.

## Notes

* The Supabase CLI is used for **platform provisioning only**
  (`[db.migrations] enabled = false`). Historically the CLI applied a copy of the
  migration chain and `apply_migrations.sh` then finished the sequence as
  `supabase_admin`, because the pre-revision D32 issued ownership-sensitive DDL
  on `storage.objects`. That revision is obsolete: D32 now validates the
  provider-context policies, the migration role is `postgres`, and only the
  narrow operator step runs with provider privilege. The helper and this README
  were stale and have been corrected.
* `.env.e2e` is gitignored. It contains the CLI's **local-dev** keys (shared
  defaults for local Supabase, never production credentials).
* No production data, credentials, payments or entitlements are used.
