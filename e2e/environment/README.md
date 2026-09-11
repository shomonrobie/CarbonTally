# CarbonTally P6-2F — Isolated E2E Environment

This directory provisions a **dedicated, isolated Supabase stack** for the P6-2F
UI/UX + E2E security acceptance gate (`PO-PHASE6-F-ENV-20260910`).

> **Never reuse the investor/demo instance.** The demo project is
> `carbon_ledger` (API `127.0.0.1:54425`, DB `127.0.0.1:54426`). This
> environment is project **`carbontally_e2e`** (API `127.0.0.1:55325`, DB
> `127.0.0.1:55326`) — separate containers, separate database, separate data.

## Layout

```
e2e/environment/
  supabase/config.toml          isolated project_id + remapped ports
  supabase/migrations/          copy of supabase/migrations (53 files)
  scripts/apply_migrations.sh   applies migrations from a filename onward (supabase_admin)
  scripts/capture_env.sh        writes .env.e2e from `supabase status -o env` (gitignored)
  scripts/bootstrap.sh          start stack + migrate + capture env
  scripts/reset.sh              drop + re-migrate (resettable)
  scripts/teardown.sh           stop + remove the isolated stack (disposable)
```

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
bash e2e/environment/scripts/bootstrap.sh      # start + migrate + capture env
```

`bootstrap.sh` prints the target URL/DB before doing anything, so destructive
steps are always against the isolated instance.

## Reset / teardown

```bash
bash e2e/environment/scripts/reset.sh          # drop + re-apply migrations
bash e2e/environment/scripts/teardown.sh       # stop + remove the isolated stack
```

## Notes

* Migrations are applied by the Supabase CLI as the `postgres` role; the D32
  storage-RLS migration needs `supabase_admin` (which owns `storage.objects`),
  so `apply_migrations.sh` finishes the sequence with that role. This is an
  **environment** workaround only — no migration file was changed.
* `.env.e2e` is gitignored. It contains the CLI's **local-dev** keys (shared
  defaults for local Supabase, never production credentials).
* No production data, credentials, payments or entitlements are used.
