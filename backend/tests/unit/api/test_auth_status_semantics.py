"""WS3 / API-0001 — authentication status semantics regression tests.

The audit found that a *missing* Authorization header returned HTTP 403
"Not authenticated" (Starlette ``HTTPBearer`` auto-error) instead of the
standard HTTP 401 + ``WWW-Authenticate`` challenge.

Approved remediation (backend/auth.py):
* ``HTTPBearer(auto_error=False)`` — missing credentials reach
  ``get_current_user`` as ``None`` instead of being short-circuited to 403.
* ``get_current_user`` raises 401 + ``WWW-Authenticate: Bearer`` for missing
  credentials.
* Invalid credentials remain 401 (existing behaviour).
* Authenticated-but-insufficient-permission remains 403 (existing behaviour).

These tests run entirely in memory (no Supabase required): the missing-credential
path raises before any external call.
"""
from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from auth import get_current_user, security
from tests.unit.api.fakes import member_user


def test_httpbearer_auto_error_is_disabled() -> None:
    """Missing Authorization header must NOT be short-circuited to 403."""
    assert getattr(security, "auto_error", True) is False


def _missing_credentials_error() -> HTTPException:
    """Resolve get_current_user(None) to its HTTPException (memory-only path)."""
    try:
        asyncio.run(get_current_user(None))
    except HTTPException as exc:
        return exc
    except Exception as exc:  # noqa: BLE001 — any other exception is a regression
        raise AssertionError(
            f"expected HTTPException, got {type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError("expected HTTPException")


def test_missing_credentials_returns_401_with_www_authenticate() -> None:
    """get_current_user(None) → 401 + WWW-Authenticate: Bearer (no 403)."""
    exc = _missing_credentials_error()
    assert exc.status_code == 401
    assert "Not authenticated" in str(exc.detail)
    assert exc.headers == {"WWW-Authenticate": "Bearer"}


def test_missing_credentials_are_not_500() -> None:
    """The None-credentials path must raise 401 before touching Supabase."""
    exc = _missing_credentials_error()
    assert exc.status_code == 401


def test_authenticated_but_insufficient_permission_returns_403(
    app, client, user_provider
) -> None:
    """A valid non-admin user hitting an admin-only route still gets 403."""
    user_provider.set_user(member_user("org-a", "member-1", "member@test"))
    resp = client.get("/api/v3/admin/review-queue")
    assert resp.status_code == 403

