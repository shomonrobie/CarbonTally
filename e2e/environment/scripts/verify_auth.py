#!/usr/bin/env python3
"""P6-2F — prove REAL Supabase authentication against the isolated environment.

Creates (or reuses) a synthetic auth user via the GoTrue admin API and signs in
with the password grant using the anon key — the exact mechanism the browser
uses. No identity is faked; no `get_current_user` override is involved.

Usage:  python verify_auth.py [email] [password]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import urllib.error
import urllib.request

ENV_FILE = Path(__file__).resolve().parents[1] / ".env.e2e"


def load_env() -> dict:
    out = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip()
    return out


def req(url: str, method: str, headers: dict, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def main() -> int:
    env = load_env()
    sb = env["E2E_SUPABASE_URL"].strip('"')
    anon = env["E2E_ANON_KEY"].strip('"')
    service = env["E2E_SERVICE_ROLE_KEY"].strip('"')

    email = sys.argv[1] if len(sys.argv) > 1 else "p6f-probe-owner@e2e.carbontally.local"
    password = sys.argv[2] if len(sys.argv) > 2 else "CarbonTally-E2E-Local-2026!"

    print(f"environment : {env.get('E2E_ENV_ID')} ({sb})")

    # 1. health
    status, _ = req(f"{sb}/auth/v1/health", "GET", {"apikey": anon})
    print(f"auth health : {status}")

    # 2. create user (idempotent)
    status, body = req(
        f"{sb}/auth/v1/admin/users",
        "POST",
        {"apikey": anon, "Authorization": f"Bearer {service}", "Content-Type": "application/json"},
        {"email": email, "password": password, "email_confirm": True,
         "user_metadata": {"p6f": True, "namespace": "p6_2f_e2e"}},
    )
    print(f"create user : {status} {'(exists)' if status in (409, 422) else ''}")

    # 3. sign in with password (the real browser mechanism)
    status, body = req(
        f"{sb}/auth/v1/token?grant_type=password",
        "POST",
        {"apikey": anon, "Content-Type": "application/json"},
        {"email": email, "password": password},
    )
    print(f"sign-in     : {status}")
    if status != 200 or "access_token" not in body:
        print("REAL AUTH: FAIL")
        print(json.dumps(body)[:300])
        return 1
    token = body["access_token"]
    claims = json.loads(
        __import__("base64").urlsafe_b64decode(token.split(".")[1] + "===").decode()
    )
    print(f"  role      : {claims.get('role')}")
    print(f"  sub       : {claims.get('sub')}")
    print(f"  aud       : {claims.get('aud')}")
    print(f"  token len : {len(token)}")
    print("REAL AUTH: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
