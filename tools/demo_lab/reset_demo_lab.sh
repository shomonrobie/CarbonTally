#!/usr/bin/env bash
# DEMO-T1 — remove the local Demo Lab (LAB ONLY).
#
#   ./tools/demo_lab/reset_demo_lab.sh              # lab DB + lab containers
#   ./tools/demo_lab/reset_demo_lab.sh --purge-state # also local credentials/evidence
#
# It never touches the developer's Supabase stack databases, the investor demo
# dataset, production, or Render. The only stack-side action is deleting the
# lab's own auth users (identified by the lab e-mail domain), because the lab
# authenticates through the local stack's GoTrue.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../.." && pwd)"
STATE_DIR="${DEMO_LAB_STATE_DIR:-$HOME/ct_local_env/demo_lab}"
PY="${PYTHON:-python3}"

cd "${REPO_ROOT}"
echo "== removing the local Demo Lab (lab resources only) =="

read -r -d '' PYCODE <<'PY' || true
import sys
sys.path.insert(0, "tools/demo_lab")
import lab

# 1. lab auth users (namespaced by the lab e-mail domain) in the local stack GoTrue
try:
    keys = lab.stack_env()
    headers = {"apikey": keys["service_key"], "Authorization": f"Bearer {keys['service_key']}"}
    status, payload, _raw = lab.http_json(
        f"http://127.0.0.1:{lab.GATEWAY_PORT}/auth/v1/admin/users?per_page=1000", headers=headers)
    removed = 0
    if status == 200 and isinstance(payload, dict):
        for user in payload.get("users", []):
            if str(user.get("email", "")).endswith(lab.EMAIL_DOMAIN):
                code, _p, _r = lab.http_json(
                    f"http://127.0.0.1:{lab.GATEWAY_PORT}/auth/v1/admin/users/{user['id']}",
                    method="DELETE", headers=headers)
                removed += int(code in (200, 204))
    print(f"lab auth users removed: {removed}")
except Exception as exc:  # noqa: BLE001 — reset must report, not crash
    print(f"could not remove lab auth users: {exc}")

# 2. lab containers
import subprocess
for name in lab.LAB_CONTAINERS:
    subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    print(f"container removed (if present): {name}")

# 3. lab database (only the lab's own database is dropped)
result = lab.psql(f'DROP DATABASE IF EXISTS "{lab.LAB_DB}" WITH (FORCE)', db="postgres")
print("lab database dropped:" , "ok" if result.returncode == 0 else result.stderr[:200])
PY

"${PY}" - <<< "${PYCODE}"

if [[ "${1:-}" == "--purge-state" ]]; then
  rm -rf "${STATE_DIR}"
  echo "local state purged: ${STATE_DIR}"
else
  echo "local state kept: ${STATE_DIR} (use --purge-state to delete credentials/evidence)"
fi
