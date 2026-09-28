#!/usr/bin/env bash
# P6-2F — reset the ISOLATED E2E environment (resettable requirement).
#
# CT-SCHEMA-02: the reset follows the canonical two-layer order (see
# bootstrap.sh and ../README.md). `supabase db reset` is NOT used to apply
# migrations — it would apply an unreviewed chain through the CLI. The platform
# schema is re-provisioned by the stack itself and the canonical sequence is
# applied explicitly, so a reset can never produce a schema that the canonical
# procedure would not.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_DIR="$(cd "$HERE/.." && pwd)"
cd "$ENV_DIR"

export E2E_DB_HOST="${E2E_DB_HOST:-127.0.0.1}"
export E2E_DB_PORT="${E2E_DB_PORT:-55326}"
export E2E_DB_NAME="${E2E_DB_NAME:-postgres}"
export E2E_DB_USER="${E2E_DB_USER:-postgres}"
export E2E_DB_PASSWORD="${E2E_DB_PASSWORD:-postgres}"
PROVIDER_ROLE="${E2E_PROVIDER_ROLE:-supabase_admin}"

echo "== resetting ISOLATED E2E database (project carbontally_e2e) =="
echo "   LAYER 1: platform reset (auth/storage only — no application migrations)"
# `supabase db reset` drops and recreates the database and re-provisions the
# platform; the CLI project has application migrations disabled. A failure here
# is fatal: it means the platform layer is not available.
supabase db reset --no-seed

echo "   LAYER 2: migrations 1-26"
bash "$HERE/apply_migrations.sh" --from 1 --to 26 --expect-count 26 --require-storage

echo "   LAYER 2: D32 operator step (provider context)"
PGPASSWORD="$E2E_DB_PASSWORD" psql -h "$E2E_DB_HOST" -p "$E2E_DB_PORT" \
  -U "$PROVIDER_ROLE" -d "$E2E_DB_NAME" -X -q -v ON_ERROR_STOP=1 \
  -f "$HERE/d32_storage_operator.sql"

echo "   LAYER 2: migrations 27-89"
bash "$HERE/apply_migrations.sh" --from 27 --to 89 --expect-count 63 --require-storage

echo "   LAYER 2: canonical migration-set verification"
python3 "$HERE/canonical_schema_verify.py" --migration-set-only

# Re-apply the E2E-only privilege baseline: the CLI applies migrations as a role
# whose objects do not carry `authenticated` DML grants, so PostgREST would
# answer 42501 before RLS could decide. Neither step changes RLS.
PGPASSWORD="$E2E_DB_PASSWORD" psql -h "$E2E_DB_HOST" -p "$E2E_DB_PORT" -U "$PROVIDER_ROLE" -d "$E2E_DB_NAME" -q \
  -f "$HERE/grant_service_role.sql" || echo "WARN: service_role grants step failed"
PGPASSWORD="$E2E_DB_PASSWORD" psql -h "$E2E_DB_HOST" -p "$E2E_DB_PORT" -U "$PROVIDER_ROLE" -d "$E2E_DB_NAME" -q \
  -f "$HERE/grant_authenticated.sql" || echo "WARN: authenticated grants step failed"
bash "$HERE/capture_env.sh"
echo "RESET DONE (synthetic fixtures must be re-seeded: seed_e2e.py + seed_lifecycle_fixtures.py)."


