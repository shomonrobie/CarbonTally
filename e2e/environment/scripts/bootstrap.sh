#!/usr/bin/env bash
# P6-2F — bring up the ISOLATED E2E environment (project carbontally_e2e).
#
# Safety: prints the target before doing anything destructive; the isolated
# project uses ports 553xx and never touches the demo instance (544xx).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_DIR="$(cd "$HERE/.." && pwd)"
cd "$ENV_DIR"

echo "== P6-2F isolated E2E bootstrap =="
echo "   project_id : $(grep -m1 '^project_id' supabase/config.toml | cut -d'\"' -f2)"
echo "   api port   : $(grep -m1 -A3 '^\[api\]' supabase/config.toml | grep -m1 '^port' | tr -dc '0-9')"
echo "   db port    : $(awk '/^\[db\]/{f=1} f&&/^port/{print; exit}' supabase/config.toml | tr -dc '0-9')"
echo "   (demo instance is carbon_ledger on 544xx — NOT touched)"

echo "== starting stack =="
supabase start

echo "== applying migrations (CLI) =="
supabase db reset --no-seed || true

# The D32 storage-RLS migration needs the storage-object owner role; the CLI
# applies with `postgres`. Finish from that migration onward as supabase_admin.
echo "== finishing migrations as supabase_admin =="
bash "$HERE/apply_migrations.sh" 20260823000000_d32_private_documents_storage.sql

echo "== granting service_role table privileges (isolated env only) =="
PGPASSWORD=postgres psql -h 127.0.0.1 -p 55326 -U supabase_admin -d postgres -q \
  -f "$HERE/grant_service_role.sql" || echo "WARN: grants step failed"

echo "== restoring authenticated table privileges from the schema's own RLS surface =="
PGPASSWORD=postgres psql -h 127.0.0.1 -p 55326 -U supabase_admin -d postgres -q \
  -f "$HERE/grant_authenticated.sql" || echo "WARN: authenticated grants step failed"

echo "== capturing environment =="
bash "$HERE/capture_env.sh"

echo "== seeding synthetic P6-2F fixtures + personas =="
python3 "$HERE/seed_e2e.py"

echo "== seeding lifecycle-state + D6 entitlement fixtures =="
python3 "$HERE/seed_lifecycle_fixtures.py"

echo "DONE. Next: start the app servers (backend/frontend) against this environment."

