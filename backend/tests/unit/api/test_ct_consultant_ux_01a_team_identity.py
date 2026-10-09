"""CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A — human-readable team identity.

UX-11/AC-14: a firm admin adds a team member by EMAIL (an existing CarbonTally
user), never by an internal user id. The backend resolves the email to an
EXISTING identity server-side; an unknown email is refused (no silent
provisioning) and the manage_team permission still governs the write.

In-memory; the auth-directory lookup is monkeypatched (no network/DB).
"""
from __future__ import annotations

import importlib

import pytest

from tests.unit.api.fakes import consultant_user


def _seed_firm(world, user_id="u-cons", *, can_manage_team=True, firm="firm-1"):
    world.consultants.seed_profile(firm, user_id, "Acme Consultants", is_active=True)
    world.consultants.seed_firm_member(firm, user_id, role="manager", can_manage_team=can_manage_team)
    return consultant_user(user_id, "cons@example.test")


@pytest.fixture
def resolver(monkeypatch):
    """Patch the email->identity resolver with a deterministic directory."""
    module = importlib.import_module("api.v3_consultants")
    directory = {"jane@firm.test": "u-jane"}

    async def _fake_resolve(email: str):
        return directory.get(email)

    monkeypatch.setattr(module, "_resolve_owner_identity_by_email", _fake_resolve)
    return directory


def test_add_member_by_email_resolves_existing_identity(client, world, user_provider, resolver) -> None:
    user = _seed_firm(world, user_id="u-cons", can_manage_team=True)
    user_provider.set_user(user)

    resp = client.post(
        "/api/v3/consultants/me/team",
        json={"email": "jane@firm.test", "role": "consultant"},
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    # The email is resolved to the existing identity; the member starts with no caps.
    assert created["user_id"] == "u-jane"
    assert created["can_manage_team"] is False


def test_add_member_email_is_case_insensitive(client, world, user_provider, resolver) -> None:
    user = _seed_firm(world, user_id="u-cons", can_manage_team=True)
    user_provider.set_user(user)

    resp = client.post(
        "/api/v3/consultants/me/team",
        json={"email": "Jane@Firm.test", "role": "consultant"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["user_id"] == "u-jane"


def test_add_member_unknown_email_refused_without_provisioning(client, world, user_provider, resolver) -> None:
    user = _seed_firm(world, user_id="u-cons", can_manage_team=True)
    user_provider.set_user(user)

    resp = client.post(
        "/api/v3/consultants/me/team",
        json={"email": "nobody@firm.test", "role": "consultant"},
    )
    assert resp.status_code == 404, resp.text


def test_add_member_requires_an_identifier(client, world, user_provider, resolver) -> None:
    user = _seed_firm(world, user_id="u-cons", can_manage_team=True)
    user_provider.set_user(user)

    resp = client.post("/api/v3/consultants/me/team", json={"role": "consultant"})
    assert resp.status_code == 422, resp.text


def test_add_member_email_path_still_requires_manage_team(client, world, user_provider, resolver) -> None:
    """The email convenience must NOT weaken the manage_team authorization."""
    user = _seed_firm(world, user_id="u-limited", can_manage_team=False)
    user_provider.set_user(user)

    resp = client.post(
        "/api/v3/consultants/me/team",
        json={"email": "jane@firm.test", "role": "consultant"},
    )
    assert resp.status_code == 403, resp.text


def test_add_member_email_matching_self_rejected(client, world, user_provider, monkeypatch) -> None:
    """A resolver returning the caller's own id must not add the caller."""
    module = importlib.import_module("api.v3_consultants")

    async def _self_resolve(_email: str):
        return "u-cons"

    monkeypatch.setattr(module, "_resolve_owner_identity_by_email", _self_resolve)
    user = _seed_firm(world, user_id="u-cons", can_manage_team=True)
    user_provider.set_user(user)

    resp = client.post(
        "/api/v3/consultants/me/team",
        json={"email": "me@firm.test", "role": "manager"},
    )
    assert resp.status_code == 422, resp.text
