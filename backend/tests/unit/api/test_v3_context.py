"""Phase 3 / P1-B regression — ``GET /api/v3/me/context`` (fail-closed routing).

Required behaviour:

* staff (CarbonTally internal) -> /ops
* Processing Entity staff   -> /pe (dedicated PE application shell)
* consultant                -> /consultant
* customer org member  -> /home
* genuinely new user   -> /onboarding (SERVER decision, never on error)
* unauthenticated      -> 401
* resolution failure   -> 500 (never "new user")
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException
from starlette.testclient import TestClient

from api.dependencies import get_repositories
from api.v3_context import me_context
from auth import AuthUser
from tests.unit.api.fakes import (
    consultant_user,
    entity_operator_user,
    member_user,
    org_owner_user,
    staff_user,
)


def _org_member():
    return member_user("org-a", "u-member", "member@carbontally.test")


def test_staff_resolves_ops(client, user_provider):
    user_provider.set_user(staff_user(user_id="u-staff", role_name="operator"))
    response = client.get("/api/v3/me/context")
    assert response.status_code == 200
    body = response.json()
    assert body["actor_type"] == "staff"
    assert body["destination"] == "/ops"
    assert body["primary_workspace"] == "ops"


def test_entity_staff_resolves_pe(client, user_provider):
    user_provider.set_user(entity_operator_user("entity-a", user_id="u-entity"))
    response = client.get("/api/v3/me/context")
    assert response.status_code == 200
    body = response.json()
    assert body["actor_type"] == "entity_staff"
    # V1.2 — PE staff land in the dedicated PE application shell, NOT /ops.
    assert body["destination"] == "/pe"
    assert body["primary_workspace"] == "pe"
    assert body["workspaces"] == ["pe"]
    assert body["staff"]["entity_id"] == "entity-a"


def test_consultant_resolves_consultant(client, user_provider, world):
    world.consultants.seed_profile("firm-1", "u-consultant", company_name="Acme Consultants")
    world.consultants.seed_firm_member("firm-1", "u-consultant", role="consultant")
    user_provider.set_user(consultant_user("u-consultant", "consultant@carbontally.test"))
    response = client.get("/api/v3/me/context")
    assert response.status_code == 200
    body = response.json()
    assert body["actor_type"] == "consultant"
    assert body["destination"] == "/consultant"
    assert body["consultant"]["firm_id"] == "firm-1"
    assert body["consultant"]["role"] == "consultant"


def test_org_member_resolves_home(client, user_provider):
    user_provider.set_user(_org_member())
    response = client.get("/api/v3/me/context")
    assert response.status_code == 200
    body = response.json()
    assert body["actor_type"] == "customer"
    assert body["destination"] == "/home"
    assert body["organization"]["id"] == "org-a"
    assert body["organization"]["name"]  # seeded organisation name is resolved


def test_org_owner_resolves_home(client, user_provider):
    user_provider.set_user(org_owner_user("org-a", "u-owner", "owner@carbontally.test"))
    response = client.get("/api/v3/me/context")
    assert response.status_code == 200
    assert response.json()["destination"] == "/home"


def test_genuinely_new_user_resolves_onboarding(client, user_provider):
    """Authenticated with NO org/staff/consultant relationship -> onboarding."""
    user_provider.set_user(consultant_user("u-new", "new@carbontally.test"))
    response = client.get("/api/v3/me/context")
    assert response.status_code == 200
    body = response.json()
    assert body["actor_type"] == "new_user"
    assert body["destination"] == "/onboarding"


def test_unauthenticated_returns_401(client, user_provider):
    user_provider.set_unauthenticated()
    response = client.get("/api/v3/me/context")
    assert response.status_code == 401


def test_resolution_failure_is_500_never_new_user(app, world, user_provider):
    """A database failure must fail closed (500), never classify as new user."""

    class _BoomConsultants:
        async def get_profile_by_user(self, user_id):  # pragma: no cover
            raise RuntimeError("db down")

    class _BoomBundle:
        consultants = _BoomConsultants()

    async def boom_repos():
        return _BoomBundle()

    user_provider.set_user(_org_member())
    app.dependency_overrides[get_repositories] = boom_repos
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/api/v3/me/context")
    assert response.status_code == 500
    assert "onboarding" not in response.text.lower()


def test_me_context_never_turns_db_failure_into_new_user():
    """Direct async guard: a resolver exception propagates (fail-closed)."""

    class _BoomConsultants:
        # P6-1B: canonical resolution is membership-first
        # (get_active_memberships_by_user), so the failure must surface there.
        async def get_active_memberships_by_user(self, user_id):  # pragma: no cover
            raise RuntimeError("db down")

    class _BoomBundle:
        consultants = _BoomConsultants()

    user = AuthUser(user_id="u-1", email="u@carbontally.test", role="user", role_name="user")
    with pytest.raises(RuntimeError):
        asyncio.run(me_context(user, _BoomBundle()))
