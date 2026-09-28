#!/usr/bin/env bash
# P6-2F — bring up the ISOLATED E2E environment (project carbontally_e2e).
#
# CT-SCHEMA-02: the environment is built in the canonical TWO-LAYER order:
#
#   LAYER 1  platform      `supabase start` — provisions auth/storage (the real
#                          Storage service creates storage.*). Application
#                          migrations are DISABLED for this CLI project
#                          (supabase/config.toml `[db.migrations] enabled = false`)
#                          so the CLI can never apply a divergent migration copy.
#   LAYER 2  application   `apply_migrations.sh` 1-26 -> D32 operator step
#                          (provider context) -> `apply_migrations.sh` 27-89
#                          -> migration-set verification
#
# Safety: prints the target before doing anything destructive; the isolated
# project uses ports 553xx and never touches the demo instance (544xx).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_DIR="$(cd "$HERE/.." && pwd)"
cd "$ENV_DIR"

export E2E_DB_HOST="${E2E_DB_HOST:-127.0.0.1}"
export E2E_DB_PORT="${E2E_DB_PORT:-55326}"
export E2E_DB_NAME="${E2E_DB_NAME:-postgres}"
export E2E_DB_USER="${E2E_DB_USER:-postgres}"
export E2E_DB_PASSWORD="${E2E_DB_PASSWORD:-postgres}"

echo "== P6-2F isolated E2E bootstrap =="
echo "   project_id : $(grep -m1 '^project_id' supabase/config.toml | cut -d'\"' -f2)"
echo "   api port   : $(grep -m1 -A3 '^\[api\]' supabase/config.toml | grep -m1 '^port' | tr -dc '0-9')"
echo "   db port    : $(awk '/^\[db\]/{f=1} f&&/^port/{print; exit}' supabase/config.toml | tr -dc '0-9')"
echo "   migration role : $E2E_DB_USER (pinned search_path; no provider privilege)"
echo "   provider role  : ${E2E_PROVIDER_ROLE:-supabase_admin} (D32 operator step only)"
echo "   (demo instance is carbon_ledger on 544xx — NOT touched)"

echo "== LAYER 1: starting the platform stack (auth/storage; no application migrations) =="
supabase start

echo "== LAYER 2: migrations 1-26 (creates public.organization_members) =="
bash "$HERE/apply_migrations.sh" --from 1 --to 26 --expect-count 26 --require-storage

echo "== LAYER 2: D32 operator step — private documents bucket + four provider-context policies =="
PGPASSWORD="$E2E_DB_PASSWORD" psql -h "$E2E_DB_HOST" -p "$E2E_DB_PORT" \
  -U "${E2E_PROVIDER_ROLE:-supabase_admin}" -d "$E2E_DB_NAME" -X -q -v ON_ERROR_STOP=1 \
  -f "$HERE/d32_storage_operator.sql"

echo "== LAYER 2: migrations 27-89 (migration 27 validates the step above) =="
bash "$HERE/apply_migrations.sh" --from 27 --to 89 --expect-count 63 --require-storage

echo "== LAYER 2: canonical migration-set verification =="
python3 "$HERE/canonical_schema_verify.py" --migration-set-only

echo "== granting service_role table privileges (isolated env only) =="
PGPASSWORD="$E2E_DB_PASSWORD" psql -h "$E2E_DB_HOST" -p "$E2E_DB_PORT" \
  -U "${E2E_PROVIDER_ROLE:-supabase_admin}" -d "$E2E_DB_NAME" -q \
  -f "$HERE/grant_service_role.sql" || echo "WARN: grants step failed"

echo "== restoring authenticated table privileges from the schema's own RLS surface =="
PGPASSWORD="$E2E_DB_PASSWORD" psql -h "$E2E_DB_HOST" -p "$E2E_DB_PORT" \
  -U "${E2E_PROVIDER_ROLE:-supabase_admin}" -d "$E2E_DB_NAME" -q \
  -f "$HERE/grant_authenticated.sql" || echo "WARN: authenticated grants step failed"

echo "== capturing environment =="
bash "$HERE/capture_env.sh"

echo "== seeding synthetic P6-2F fixtures + personas =="
python3 "$HERE/seed_e2e.py"

echo "== seeding lifecycle-state + D6 entitlement fixtures =="
python3 "$HERE/seed_lifecycle_fixtures.py"

echo "DONE. Next: start the app servers (backend/frontend) against this environment."


