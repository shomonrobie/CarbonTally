#!/usr/bin/env bash
# P6-2F — reset the ISOLATED E2E environment (resettable requirement).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_DIR="$(cd "$HERE/.." && pwd)"
cd "$ENV_DIR"

echo "== resetting ISOLATED E2E database (project carbontally_e2e) =="
supabase db reset --no-seed || true
bash "$HERE/apply_migrations.sh" 20260823000000_d32_private_documents_storage.sql
# Re-apply the E2E-only privilege baseline: the CLI applies migrations as a role
# whose objects do not carry `authenticated` DML grants, so PostgREST would
# answer 42501 before RLS could decide. Neither step changes RLS.
PGPASSWORD=postgres psql -h 127.0.0.1 -p 55326 -U supabase_admin -d postgres -q \
  -f "$HERE/grant_service_role.sql" || echo "WARN: service_role grants step failed"
PGPASSWORD=postgres psql -h 127.0.0.1 -p 55326 -U supabase_admin -d postgres -q \
  -f "$HERE/grant_authenticated.sql" || echo "WARN: authenticated grants step failed"
bash "$HERE/capture_env.sh"
echo "RESET DONE (synthetic fixtures must be re-seeded: seed_e2e.py + seed_lifecycle_fixtures.py)."

