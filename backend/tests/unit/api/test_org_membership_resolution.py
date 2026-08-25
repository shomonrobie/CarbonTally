"""D29 / F1 — GET /api/organizations/members/user/{id} regression tests.

Covers the D28 P1 finding: the endpoint returned HTTP 500 for any user without
an `organization_members` row because supabase-py 2.9.0 returns None (not an
APIResponse) for an empty ``maybe_single`` result.

These tests are DB-free: the endpoint's `get_supabase_client()` is
monkeypatched with an in-memory fake that reproduces the real client's
None-on-empty behaviour.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from routes.organizations.members import get_organization_by_user


class _Result:
    def __init__(self, data):
        self.data = data


class _Query:
    """Minimal supabase-py query-builder fake (select/eq/maybe_single/execute)."""

    def __init__(self, table, rows):
        self.table = table
        self.rows = rows
        self.filters = []
        self.raise_on_execute = None

    def select(self, *cols):
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def maybe_single(self):
        return self

    def execute(self):
        if self.raise_on_execute is not None:
            raise self.raise_on_execute
        rows = self.rows
        for key, value in self.filters:
            rows = [r for r in rows if r.get(key) == value]
        if not rows:
            # Reproduces supabase-py 2.9.0: empty maybe_single -> None
            return None
        return _Result(rows[0])


class _FakeSupabase:
    def __init__(self, fail: Exception | None = None):
        self.members = [
            ("u-owner", "org-a", "owner", True),
            ("u-member", "org-a", "member", True),
            ("u-inactive", "org-a", "member", False),
            ("u-other-org", "org-b", "admin", True),
        ]
        self.orgs = [
            {"id": "org-a", "name": "Org A"},
            {"id": "org-b", "name": "Org B"},
        ]
        self.fail = fail

    def from_(self, table):
        if table == "organization_members":
            q = _Query(
                table,
                [
                    {"user_id": uid, "organization_id": org, "role": role, "is_active": active}
                    for uid, org, role, active in self.members
                ],
            )
        elif table == "organizations":
            q = _Query(table, self.orgs)
        else:
            raise AssertionError(f"unexpected table {table}")
        q.raise_on_execute = self.fail
        return q


def _user(user_id: str):
    return SimpleNamespace(user_id=user_id)


@pytest.mark.asyncio
async def test_active_member_resolves_own_organization(monkeypatch):
    fake = _FakeSupabase()
    monkeypatch.setattr("routes.organizations.members.get_supabase_client", lambda: fake)
    result = await get_organization_by_user("u-owner", _user("u-owner"))
    assert result["mode"] == "single"
    assert result["primary_organization"]["id"] == "org-a"
    assert result["primary_role"] == "owner"
    assert result["organizations"][0]["is_primary"] is True


@pytest.mark.asyncio
async def test_non_member_returns_404_not_500(monkeypatch):
    # D28 defect: this used to raise AttributeError -> HTTP 500.
    fake = _FakeSupabase()
    monkeypatch.setattr("routes.organizations.members.get_supabase_client", lambda: fake)
    with pytest.raises(HTTPException) as exc:
        await get_organization_by_user("u-nobody", _user("u-nobody"))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_consultant_and_staff_identities_return_404(monkeypatch):
    # Consultants/internal staff/entity staff have no organization_members row.
    fake = _FakeSupabase()
    monkeypatch.setattr("routes.organizations.members.get_supabase_client", lambda: fake)
    for identity in ("u-consultant", "u-operator", "u-reviewer", "u-entity-staff"):
        with pytest.raises(HTTPException) as exc:
            await get_organization_by_user(identity, _user(identity))
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_cannot_resolve_another_users_membership(monkeypatch):
    # No cross-organization information disclosure.
    fake = _FakeSupabase()
    monkeypatch.setattr("routes.organizations.members.get_supabase_client", lambda: fake)
    with pytest.raises(HTTPException) as exc:
        await get_organization_by_user("u-member", _user("u-owner"))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_inactive_membership_returns_404(monkeypatch):
    fake = _FakeSupabase()
    monkeypatch.setattr("routes.organizations.members.get_supabase_client", lambda: fake)
    with pytest.raises(HTTPException) as exc:
        await get_organization_by_user("u-inactive", _user("u-inactive"))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_membership_with_missing_org_returns_404(monkeypatch):
    fake = _FakeSupabase()
    fake.members.append(("u-orphan", "org-missing", "admin", True))
    monkeypatch.setattr("routes.organizations.members.get_supabase_client", lambda: fake)
    with pytest.raises(HTTPException) as exc:
        await get_organization_by_user("u-orphan", _user("u-orphan"))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_query_failure_returns_500_without_leaking_details(monkeypatch):
    fake = _FakeSupabase(fail=RuntimeError("secret internal detail"))
    monkeypatch.setattr("routes.organizations.members.get_supabase_client", lambda: fake)
    with pytest.raises(HTTPException) as exc:
        await get_organization_by_user("u-owner", _user("u-owner"))
    assert exc.value.status_code == 500
    assert "secret internal detail" not in str(exc.value.detail)


@pytest.mark.asyncio
async def test_member_sees_only_their_own_organization(monkeypatch):
    # A member of org-a never receives org-b data.
    fake = _FakeSupabase()
    monkeypatch.setattr("routes.organizations.members.get_supabase_client", lambda: fake)
    result = await get_organization_by_user("u-member", _user("u-member"))
    assert result["primary_organization"]["id"] == "org-a"
    assert "org-b" not in str(result["organizations"])
