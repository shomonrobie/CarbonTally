"""Phase 3 / P1-A regression — Supabase service-role client lifecycle (FD leak).

The P1-A defect: ``auth.get_supabase_client()`` created a NEW service-role
client per call, so repeated authenticated requests leaked file descriptors
until the process hit its FD limit and every request 500'd with
``[Errno 24] Too many open files``.

These tests encode the required behaviour:

* one process-wide client is created regardless of how many times the client
  is requested (no new client per request, no FD growth);
* configuration errors fail closed with HTTP 500;
* the admin surface reuses the same singleton.
"""

from __future__ import annotations

import os

import pytest
from fastapi import HTTPException

import auth
import database
import infra.supabase


class _FakeServiceClient:
    """Stand-in for ``create_client`` that never opens sockets/FDs."""

    instances = 0

    def __init__(self) -> None:
        type(self).instances += 1


@pytest.fixture(autouse=True)
def _client_fixture(monkeypatch):
    infra.supabase._client = None
    _FakeServiceClient.instances = 0
    monkeypatch.setattr(auth, "SUPABASE_URL", "http://127.0.0.1:54425")
    monkeypatch.setattr(auth, "SUPABASE_SERVICE_KEY", "test-service-key")
    monkeypatch.setattr(database, "SUPABASE_URL", "http://127.0.0.1:54425")
    monkeypatch.setattr(database, "SUPABASE_SERVICE_KEY", "test-service-key")
    monkeypatch.setattr(infra.supabase, "create_service_client", _FakeServiceClient)
    yield
    infra.supabase._client = None
    _FakeServiceClient.instances = 0


def test_repeated_calls_create_exactly_one_client():
    """Repeated authenticated-request pattern must not create new clients."""
    first = auth.get_supabase_client()
    for _ in range(300):
        assert auth.get_supabase_client() is first
    assert _FakeServiceClient.instances == 1


def test_no_fd_growth_from_repeated_calls():
    """Repeated client access does not continuously grow open file descriptors."""
    fd_dir = "/proc/self/fd"
    if not os.path.isdir(fd_dir):  # pragma: no cover - Linux-only assertion
        pytest.skip("requires /proc/self/fd")
    before = len(os.listdir(fd_dir))
    first = auth.get_supabase_client()
    for _ in range(300):
        assert auth.get_supabase_client() is first
    after = len(os.listdir(fd_dir))
    assert after <= before + 2, f"FD count grew from {before} to {after}"


def test_missing_config_fails_closed_with_500(monkeypatch):
    monkeypatch.setattr(auth, "SUPABASE_URL", "")
    with pytest.raises(HTTPException) as exc:
        auth.get_supabase_client()
    assert exc.value.status_code == 500


def test_create_client_failure_fails_closed_with_500(monkeypatch):
    def _boom():
        raise RuntimeError("supabase down")

    monkeypatch.setattr(infra.supabase, "create_service_client", _boom)
    infra.supabase._client = None
    with pytest.raises(HTTPException) as exc:
        auth.get_supabase_client()
    assert exc.value.status_code == 500


def test_reset_recreates_client():
    first = auth.get_supabase_client()
    infra.supabase.reset_service_client()
    second = auth.get_supabase_client()
    assert first is not second
    assert _FakeServiceClient.instances == 2


def test_admin_surface_reuses_the_same_singleton():
    service_client = auth.get_supabase_client()
    admin_client = database.get_supabase_admin()
    assert admin_client is service_client
    assert _FakeServiceClient.instances == 1
