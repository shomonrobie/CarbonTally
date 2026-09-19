#!/usr/bin/env bash
# DEMO-T1 — bring up the local Demo Lab and verify it end to end.
#
#   ./tools/demo_lab/run_demo_lab.sh            # stack + provision + verify
#   ./tools/demo_lab/run_demo_lab.sh --backend  # also start the release backend
#
# Everything is LOCAL: a dedicated database inside the developer's local Supabase
# cluster, two local containers, and localhost-only ports. Nothing contacts
# production, Render or any hosted Supabase project.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../.." && pwd)"
STATE_DIR="${DEMO_LAB_STATE_DIR:-$HOME/ct_local_env/demo_lab}"
BACKEND_PORT="${DEMO_LAB_BACKEND_PORT:-8070}"
PY="${PYTHON:-python3}"

echo "== DEMO-T1 local Demo Lab =="
echo "repo:      ${REPO_ROOT}"
echo "state dir: ${STATE_DIR} (credentials live here, never in the repo)"

cd "${REPO_ROOT}"

echo "── 1/4 stack (database + local REST/Auth gateway)"
"${PY}" tools/demo_lab/stack.py

echo "── 2/4 provision synthetic identities (idempotent)"
"${PY}" tools/demo_lab/provision.py

echo "── 3/4 environment file (outside the repo)"
ENV_FILE="$("${PY}" tools/demo_lab/lab_env.py --write)"
chmod 600 "${ENV_FILE}"
echo "     ${ENV_FILE}"

if [[ "${1:-}" == "--backend" ]]; then
  echo "── 3b/4 starting the release backend on 127.0.0.1:${BACKEND_PORT}"
  pkill -f "uvicorn main:app --host 127.0.0.1 --port ${BACKEND_PORT}" 2>/dev/null || true
  (
    cd "${REPO_ROOT}/backend"
    set -a; . "${ENV_FILE}"; set +a
    nohup .venv/bin/uvicorn main:app --host 127.0.0.1 --port "${BACKEND_PORT}" \
      > "${STATE_DIR}/backend.log" 2>&1 &
  )
  for _ in $(seq 1 40); do
    if curl -sf -o /dev/null "http://127.0.0.1:${BACKEND_PORT}/health"; then break; fi
    sleep 1
  done
  echo "     backend: http://127.0.0.1:${BACKEND_PORT} (log: ${STATE_DIR}/backend.log)"
fi

echo "── 4/4 verify identities, authorization and isolation (server-side)"
"${PY}" tools/demo_lab/verify.py

echo
echo "Demo Lab ready."
echo "  gateway : http://127.0.0.1:54430  (/auth/v1, /rest/v1)"
echo "  database: carbontally_demo_local on 127.0.0.1:54426"
echo "  actors  : ${STATE_DIR}/credentials.local.json"
echo "  evidence: ${STATE_DIR}/evidence/"
