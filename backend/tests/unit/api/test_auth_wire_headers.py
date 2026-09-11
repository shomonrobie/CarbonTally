"""RV-1 — wire-level ``WWW-Authenticate`` regression tests.

OHD re-verification found the API returned HTTP 401 correctly, but the
``WWW-Authenticate: Bearer`` challenge was stripped by the global HTTP
exception handlers (backend/main.py composition root and
backend/api/router.py ``create_app()``): the handlers rebuilt the JSON
response without forwarding ``exc.headers``.

These tests exercise the real HTTP application (TestClient → routing → real
``auth.get_current_user`` dependency → exception handler → wire response) and
assert on the actual ``response.headers`` — NOT merely on ``exc.headers``.

The missing-credentials path short-circuits inside ``get_current_user`` before
any Supabase call, so no external service is required.
"""
from __future__ import annotations

import starlette.testclient
from starlette.testclient import TestClient

from api.router import create_app
from tests.unit.api.fakes import member_user


def _get_no_auth(client: starlette.testclient.TestClient) -> starlette.testclient.Response:
    """Request a protected route with no Authorization header."""
    return client.get("/api/v3/ops/organizations")


def test_missing_credentials_wire_401_challenge_v21_app() -> None:
    """Real dependency chain (create_app): 401 + WWW-Authenticate: Bearer on the wire."""
    app = create_app()  # no dependency overrides → real get_current_user
    with TestClient(app) as client:
        resp = _get_no_auth(client)
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate") == "Bearer"
    # existing envelope structure unchanged
    body = resp.json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"] == "Not authenticated"
    assert isinstance(body["request_id"], str)


def test_missing_credentials_wire_401_challenge_composition_root() -> None:
    """Production composition root (main.app): 401 + WWW-Authenticate: Bearer on the wire.

    ``main.app`` is the app OHD actually probed (``uvicorn main:app``). The
    TestClient is used without the context manager so Starlette does not run
    the startup event (which would start the background processing worker).
    """
    import main  # noqa: PLC0415 — production composition root

    with TestClient(main.app) as client:
        resp = _get_no_auth(client)
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate") == "Bearer"
    # legacy envelope structure unchanged
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == 401
    assert body["error"]["message"] == "Not authenticated"
    assert body["error"]["path"] == "/api/v3/ops/organizations"


def test_invalid_credentials_remain_wire_401(app, client, user_provider) -> None:
    """Invalid credentials (401 raised by the auth layer) stay 401 on the wire."""
    user_provider.set_unauthenticated()
    resp = client.get("/api/v3/admin/review-queue")
    assert resp.status_code == 401


def test_insufficient_permission_remains_wire_403_no_challenge(
    app, client, user_provider
) -> None:
    """Authenticated-but-insufficient-permission stays 403 (and no Bearer challenge)."""
    user_provider.set_user(member_user("org-a", "member-1", "member@test"))
    resp = client.get("/api/v3/admin/review-queue")
    assert resp.status_code == 403
    assert "WWW-Authenticate" not in resp.headers
