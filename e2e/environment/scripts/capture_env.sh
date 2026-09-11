#!/usr/bin/env bash
# Capture the isolated environment's connection settings into .env.e2e.
# LOCAL-DEV keys only (Supabase CLI shared defaults); never production.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_DIR="$(cd "$HERE/.." && pwd)"
OUT="$ENV_DIR/.env.e2e"

cd "$ENV_DIR"
raw="$(supabase status -o env 2>/dev/null)"

get() { printf '%s\n' "$raw" | sed -n "s/^$1=\"\{0,1\}\([^\"]*\)\"\{0,1\}$/\1/p" | head -1; }

API_URL="$(get API_URL)"
DB_URL="$(get DB_URL)"
ANON_KEY="$(get ANON_KEY)"
SERVICE_ROLE_KEY="$(get SERVICE_ROLE_KEY)"
JWT_SECRET="$(get JWT_SECRET)"
STUDIO_URL="$(get STUDIO_URL)"
INBUCKET_URL="$(get INBUCKET_URL)"

cat > "$OUT" <<EOF
# P6-2F isolated E2E environment (project carbontally_e2e). Gitignored.
E2E_ENV_ID=carbontally_e2e
E2E_SUPABASE_URL=$API_URL
E2E_DB_URL=$DB_URL
E2E_ANON_KEY=$ANON_KEY
E2E_SERVICE_ROLE_KEY=$SERVICE_ROLE_KEY
E2E_JWT_SECRET=$JWT_SECRET
E2E_STUDIO_URL=$STUDIO_URL
E2E_INBUCKET_URL=$INBUCKET_URL
E2E_API_URL=http://127.0.0.1:8051
EOF
echo "wrote $OUT"
echo "  API_URL=$API_URL"
echo "  DB_URL=$DB_URL"
