#!/usr/bin/env python3
"""DEMO-T1 — write the release's environment file for the local Demo Lab.

The file is written **outside the repository** (``<state dir>/backend.env``) because
it contains the lab's service key and JWT secret. It points the release at:

* ``DATABASE_URL``  → the lab database (release schema, lab data only)
* ``SUPABASE_URL``  → the lab gateway (``/rest/v1`` → lab DB, ``/auth/v1`` → local stack GoTrue)

Usage::

    python3 tools/demo_lab/lab_env.py --write     # write and print the path
    set -a; . "$(python3 tools/demo_lab/lab_env.py --write)"; set +a
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402

ENV_PATH = lab.STATE_DIR / "backend.env"


def render() -> str:
    keys = lab.stack_env()
    return "\n".join([
        "# DEMO-T1 local Demo Lab environment — GENERATED, LOCAL ONLY, DO NOT COMMIT",
        f"# lab database : {lab.LAB_DB}",
        f"# lab gateway  : http://127.0.0.1:{lab.GATEWAY_PORT}",
        "",
        f"DATABASE_URL=postgresql://{lab.STACK_DB_USER}:{lab.STACK_DB_PASSWORD}"
        f"@127.0.0.1:{lab.STACK_DB_PORT}/{lab.LAB_DB}",
        f"SUPABASE_URL=http://127.0.0.1:{lab.GATEWAY_PORT}",
        f"SUPABASE_SERVICE_KEY={keys['service_key']}",
        f"SUPABASE_ANON_KEY={keys['anon_key']}",
        f"SUPABASE_JWT_SECRET={keys['jwt_secret']}",
        "TESSERACT_CMD=",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the Demo Lab backend env file")
    parser.add_argument("--write", action="store_true",
                        help="write the file (default) and print its path")
    parser.parse_args()
    lab.ensure_dirs()
    ENV_PATH.write_text(render())
    ENV_PATH.chmod(0o600)
    print(ENV_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
