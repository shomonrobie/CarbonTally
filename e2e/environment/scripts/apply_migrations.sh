#!/usr/bin/env bash
# P6-2F E2E environment — apply migrations from a given filename onward.
#
# `supabase db reset` applies migrations as the `postgres` role, which does not
# own `storage.objects`; the D32 storage-RLS migration therefore needs the
# `supabase_admin` role. This helper applies the remaining migrations with that
# role (isolated environment ONLY — never the demo instance).
#
# Usage: apply_migrations.sh <start_filename>
set -u
START="${1:-}"
HOST="${E2E_DB_HOST:-127.0.0.1}"
PORT="${E2E_DB_PORT:-55326}"
USER="${E2E_DB_USER:-supabase_admin}"
DB="${E2E_DB_NAME:-postgres}"
export PGPASSWORD="${E2E_DB_PASSWORD:-postgres}"

DIR="$(cd "$(dirname "$0")/../supabase/migrations" && pwd)"
cd "$DIR"

applied=0 skipped=0
for f in $(ls -1 *.sql | sort); do
  if [ -n "$START" ] && [[ "$f" < "$START" ]]; then
    skipped=$((skipped+1))
    continue
  fi
  echo "== applying $f"
  if ! psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -v ON_ERROR_STOP=1 -q -f "$f" >/tmp/e2e_mig_one.log 2>&1; then
    echo "FAILED: $f"
    tail -5 /tmp/e2e_mig_one.log
    exit 1
  fi
  applied=$((applied+1))
done
echo "APPLIED=$applied SKIPPED=$skipped"
echo "ALL_APPLIED"
