"""DEMO-T1 — shared local Demo Lab configuration and helpers (LOCAL ONLY).

This module is the single place that knows the local Demo Lab's names, ports and
paths. It contains **no secrets**: a lab JWT secret and per-actor credentials are
generated on first use and stored outside the repository, under
``<state dir>/credentials.local.json`` (mode 0600).

Boundary: this tooling only ever talks to the LOCAL disposable infrastructure it
creates (a dedicated PostgreSQL database inside the developer's local Supabase
cluster and three local containers). It never contacts production, Render or any
hosted Supabase project.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import pathlib
import secrets
import subprocess
import time
import urllib.error
import urllib.request
import uuid

# --- identity of this lab -------------------------------------------------

LAB_ID = "carbontally_demo_lab"
LAB_NAMESPACE = "demo-lab-t1"
LAB_DB = "carbontally_demo_local"
EMAIL_DOMAIN = "demo-lab.carbontally.local"

#: Host port of the lab's own API gateway (auth + rest), bound to localhost only.
GATEWAY_PORT = 54430
#: The release backend port used when the lab is exercised through HTTP.
BACKEND_PORT = 8070

#: Containers created by this tooling (all prefixed, all disposable).
POSTGREST_CONTAINER = f"{LAB_ID}_postgrest"
GATEWAY_CONTAINER = f"{LAB_ID}_gateway"
#: DEMO-T3-IMP-001 (Scope A) — lab-owned storage API (documents + artefacts).
STORAGE_CONTAINER = f"{LAB_ID}_storage"
LAB_CONTAINERS = (POSTGREST_CONTAINER, STORAGE_CONTAINER, GATEWAY_CONTAINER)

#: The developer's LOCAL Supabase stack (source of the cluster only — never mutated).
STACK_DB_CONTAINER = "supabase_db_carbon_ledger"
STACK_AUTH_CONTAINER = "supabase_auth_carbon_ledger"
STACK_STORAGE_CONTAINER = "supabase_storage_carbon_ledger"
STACK_NETWORK = "supabase_network_carbon_ledger"
STACK_DB_PORT = 54426
STACK_DB_USER = "postgres"
STACK_DB_PASSWORD = "postgres"

IMAGES = {
    "postgrest": "public.ecr.aws/supabase/postgrest:v14.5",
    "storage": "public.ecr.aws/supabase/storage-api:v1.69.0",
    "gateway": "nginx:alpine",
}

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"
MANIFEST_PATH = pathlib.Path(__file__).resolve().parent / "manifest.json"

#: Local-only state (credentials, generated config, evidence). Outside the repo.
STATE_DIR = pathlib.Path(
    os.environ.get("DEMO_LAB_STATE_DIR", str(pathlib.Path.home() / "ct_local_env" / "demo_lab"))
)
CREDENTIALS_PATH = STATE_DIR / "credentials.local.json"
GENERATED_DIR = STATE_DIR / "generated"
EVIDENCE_DIR = STATE_DIR / "evidence"


def ensure_dirs() -> None:
    for path in (STATE_DIR, GENERATED_DIR, EVIDENCE_DIR):
        path.mkdir(parents=True, exist_ok=True)


# --- local state ----------------------------------------------------------


def load_state() -> dict:
    ensure_dirs()
    if CREDENTIALS_PATH.exists():
        return json.loads(CREDENTIALS_PATH.read_text())
    return {}


def save_state(state: dict) -> None:
    ensure_dirs()
    CREDENTIALS_PATH.write_text(json.dumps(state, indent=1, sort_keys=True))
    os.chmod(CREDENTIALS_PATH, 0o600)


def lab_secret() -> str:
    """A lab-specific JWT secret, generated once and kept outside the repo."""
    state = load_state()
    if not state.get("jwt_secret"):
        state["jwt_secret"] = secrets.token_hex(32)
        save_state(state)
    return state["jwt_secret"]


def stack_env() -> dict:
    """Local stack keys (service/anon/JWT secret) — read, never printed.

    They are cached in the local state file (outside the repo, mode 0600) so the
    lab never has to call the CLI again and no secret ever reaches the repository.
    """
    state = load_state()
    if state.get("stack_jwt_secret") and state.get("stack_service_key"):
        return {"jwt_secret": state["stack_jwt_secret"],
                "service_key": state["stack_service_key"],
                "anon_key": state.get("stack_anon_key", "")}
    result = run(["supabase", "status", "-o", "env"], timeout=120,
                 cwd=str(REPO_ROOT))
    values: dict[str, str] = {}
    for line in (result.stdout + result.stderr).splitlines():
        if "=" in line and not line.startswith(" "):
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip('"')
    if not values.get("SERVICE_ROLE_KEY") or not values.get("JWT_SECRET"):
        raise RuntimeError("could not read the local Supabase stack credentials "
                           "(`supabase status -o env` failed)")
    state.update({"stack_jwt_secret": values["JWT_SECRET"],
                  "stack_service_key": values.get("SERVICE_ROLE_KEY", ""),
                  "stack_anon_key": values.get("ANON_KEY", "")})
    save_state(state)
    return {"jwt_secret": state["stack_jwt_secret"],
            "service_key": state["stack_service_key"],
            "anon_key": state["stack_anon_key"]}


def demo_password() -> str:
    """A lab-specific synthetic password (never a production credential)."""
    state = load_state()
    if not state.get("demo_password"):
        state["demo_password"] = "Lab-" + secrets.token_urlsafe(18)
        save_state(state)
    return state["demo_password"]


def deterministic_uuid(key: str) -> str:
    """Stable UUID for a lab entity, so provisioning is idempotent."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"carbontally/{LAB_NAMESPACE}/{key}"))


# --- tokens (Supabase-compatible HS256, lab secret only) ------------------


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def mint_token(user_id: str, email: str, secret: str, role: str = "authenticated",
               expires_in: int = 3600, extra_claims: dict | None = None) -> str:
    """Mint a Supabase-compatible HS256 JWT for the lab.

    ``aud`` is deliberately omitted: the release validates locally-minted tokens
    through its documented manual HS256 path, and PyJWT rejects a mismatched
    audience.
    """
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + expires_in,
    }
    if extra_claims:
        payload.update(extra_claims)
    signing_input = ".".join(
        [_b64(json.dumps(header, separators=(",", ":")).encode()),
         _b64(json.dumps(payload, separators=(",", ":")).encode())]
    )
    signature = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64(signature)}"




# --- docker / psql / http helpers ----------------------------------------


def run(cmd: list[str], *, check: bool = False, timeout: int = 300,
        stdin_text: str | None = None, cwd: str | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                            input=stdin_text, cwd=cwd)
    if check and result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(cmd)}\n{result.stderr}")
    return result


def psql(sql: str, *, db: str = LAB_DB, check: bool = False) -> subprocess.CompletedProcess:
    return run(
        ["docker", "exec", "-i", STACK_DB_CONTAINER, "psql", "-v", "ON_ERROR_STOP=0",
         "-U", STACK_DB_USER, "-d", db, "-t", "-A", "-c", sql],
        check=check,
    )


def psql_scalar(sql: str, *, db: str = LAB_DB) -> str:
    result = psql(sql, db=db)
    return result.stdout.strip()


def database_exists(db: str = LAB_DB) -> bool:
    return psql_scalar(
        f"SELECT 1 FROM pg_database WHERE datname='{db}'", db="postgres") == "1"


def table_count(db: str = LAB_DB) -> int:
    value = psql_scalar(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'", db=db)
    return int(value or 0)


def container_state(name: str) -> str:
    result = run(["docker", "inspect", "-f", "{{.State.Status}}", name])
    return result.stdout.strip() if result.returncode == 0 else "absent"


def container_up(name: str) -> bool:
    return container_state(name) == "running"


def http_json(url: str, *, method: str = "GET", headers: dict | None = None,
              body: dict | None = None, timeout: int = 20) -> tuple[int, dict | list | None, str]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method,
                                     headers={"Content-Type": "application/json",
                                              **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode()
            status = response.status
    except urllib.error.HTTPError as exc:  # expected for 4xx/5xx probes
        raw = exc.read().decode()
        status = exc.code
    except Exception as exc:  # noqa: BLE001 — network failure is a probe result
        return 0, None, str(exc)
    try:
        return status, json.loads(raw), raw
    except json.JSONDecodeError:
        return status, None, raw


#: Supabase's platform bootstrap creates these auth helpers/types; GoTrue's own
#: migrations *reference* them (e.g. ``auth.code_challenge_method``) but never
#: create them, so the lab copies them from the local stack (READ-ONLY there).
AUTH_HELPER_FUNCTIONS = ("uid", "role", "email", "jwt", "jwt_claim")


def stack_auth_enum_ddl(db: str = "postgres") -> list[str]:
    """``CREATE TYPE auth.<name> AS ENUM (…)`` statements read from the local stack."""
    sql = (
        "SELECT 'CREATE TYPE auth.' || t.typname || ' AS ENUM (' || "
        "string_agg('''' || e.enumlabel || '''', ',' ORDER BY e.enumsortorder) || ')' "
        "FROM pg_type t JOIN pg_enum e ON e.enumtypid = t.oid "
        "JOIN pg_namespace n ON n.oid = t.typnamespace "
        "WHERE n.nspname = 'auth' GROUP BY t.typname ORDER BY t.typname")
    result = psql(sql, db=db)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def stack_auth_helper_function_ddl(db: str = "postgres") -> list[str]:
    """``CREATE OR REPLACE FUNCTION auth.…`` definitions read from the local stack."""
    names = ",".join(f"'{name}'" for name in AUTH_HELPER_FUNCTIONS)
    sql = ("SELECT pg_get_functiondef(p.oid) FROM pg_proc p "
           "JOIN pg_namespace n ON n.oid = p.pronamespace "
           f"WHERE n.nspname = 'auth' AND p.proname IN ({names})")
    result = psql(sql, db=db)
    statements: list[str] = []
    current: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("CREATE OR REPLACE FUNCTION"):
            if current:
                statements.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        statements.append("\n".join(current))
    return [statement for statement in statements if statement.strip().endswith("$function$")]


def wait_for(url: str, *, expect_in: tuple[int, ...], attempts: int = 40,
             delay: float = 1.5) -> int:
    """Poll ``url`` until it answers with an expected status (or give up)."""
    last = 0
    for _ in range(attempts):
        status, _payload, _raw = http_json(url)
        last = status
        if status in expect_in:
            return status
        time.sleep(delay)
    return last

def service_key(secret: str | None = None) -> str:
    """The stack's service_role key (authoritative — accepted by every tier)."""
    if secret is None:
        try:
            return stack_env()["service_key"]
        except Exception:  # noqa: BLE001 — fall back to a lab-signed key
            return mint_token("service-role", "service@local", lab_secret(),
                              role="service_role", expires_in=60 * 60 * 24 * 365)
    return mint_token("service-role", "service@local", secret,
                      role="service_role", expires_in=60 * 60 * 24 * 365)


def anon_key(secret: str | None = None) -> str:
    """The stack's anon key (authoritative), or a lab-signed equivalent."""
    if secret is None:
        try:
            return stack_env()["anon_key"]
        except Exception:  # noqa: BLE001
            return mint_token("anon", "anon@local", lab_secret(), role="anon",
                              expires_in=60 * 60 * 24 * 365)
    return mint_token("anon", "anon@local", secret, role="anon",
                      expires_in=60 * 60 * 24 * 365)


def session_secret() -> str:
    """The JWT secret the release must validate session tokens with.

    The lab delegates authentication to the local stack's GoTrue, so tokens carry
    the stack's signature and the release's ``SUPABASE_JWT_SECRET`` must match it.
    """
    try:
        return stack_env()["jwt_secret"]
    except Exception:  # noqa: BLE001
        return lab_secret()
