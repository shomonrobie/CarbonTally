#!/usr/bin/env bash
# P6-2F — tear down the ISOLATED E2E environment (disposable requirement).
# Stops ONLY the carbontally_e2e project's containers.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_DIR="$(cd "$HERE/.." && pwd)"
cd "$ENV_DIR"
echo "== stopping ISOLATED E2E stack (carbontally_e2e) =="
supabase stop
echo "TEARDOWN DONE (demo instance untouched)."
