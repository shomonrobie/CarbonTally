"""F2 regression tests — legacy upload batch endpoints are organisation-scoped.

The PE security audit (P2/F2) found that:
- ``GET /api/batches/{batch_id}/progress`` had NO authorisation check at all;
- ``GET /api/batches/stats?organization_id=...`` filtered by the supplied org
  without verifying the caller belongs to it.

These tests are DB-free: ``routes.upload.get_supabase_client`` is monkeypatched
with an in-memory fake and ``auth.get_current_user`` is overridden per test.
"""
from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth import get_current_user
from routes.upload import router as upload_router


class _Result:
    def __init__(self, data):
        self.data = data


class _Query:
    """Minimal supabase-py query-builder fake (select/eq/in_/maybe_single/execute)."""

    def __init__(self, rows):
        self.rows = list(rows)
        self.filters = []
        self.in_filters = []
        self.single = False

    def select(self, *cols):
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def in_(self, key, values):
        self.in_filters.append((key, values))
        return self

    def maybe_single(self):
        self.single = True
        return self

    def execute(self):
        rows = self.rows
        for key, value in self.filters:
            rows = [r for r in rows if r.get(key) == value]
        for key, values in self.in_filters:
            rows = [r for r in rows if r.get(key) in values]
        if self.single:
            return _Result(rows[0]) if rows else None
        return _Result(rows)


class _FakeSupabase:
    def __init__(self, batches, members):
        self.batches = batches
        self.members = members

    def from_(self, table):
        if table == "upload_batches":
            return _Query(self.batches)
        if table == "organization_members":
            return _Query(self.members)
        raise AssertionError(f"unexpected table {table}")


def _make_app(monkeypatch, user, fake):
    from routes import upload as upload_module

    monkeypatch.setattr(upload_module, "get_supabase_client", lambda: fake)

    app = FastAPI()
    app.include_router(upload_router)

    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override
    return app


def _batch(batch_id="batch-1", org_id="org-a"):
    return {
        "id": batch_id,
        "organization_id": org_id,
        "total_files": 2,
        "processed_files": 1,
        "status": "in_progress",
        "created_at": "2026-08-01T00:00:00Z",
    }


def _member(user_id="u-owner", org_id="org-a"):
    return {"id": f"m-{user_id}", "organization_id": org_id, "user_id": user_id}


def test_batch_progress_denied_for_non_member(monkeypatch):
    user = SimpleNamespace(user_id="u-intruder", is_admin=False)
    fake = _FakeSupabase(
        batches=[_batch()],
        members=[_member("u-owner")],
    )
    app = _make_app(monkeypatch, user, fake)
    with TestClient(app) as client:
        resp = client.get("/api/batches/batch-1/progress")
    assert resp.status_code == 403


def test_batch_progress_allowed_for_member(monkeypatch):
    user = SimpleNamespace(user_id="u-owner", is_admin=False)
    fake = _FakeSupabase(
        batches=[_batch()],
        members=[_member("u-owner")],
    )
    app = _make_app(monkeypatch, user, fake)
    with TestClient(app) as client:
        resp = client.get("/api/batches/batch-1/progress")
    assert resp.status_code == 200
    assert resp.json()["data"]["percentage"] == 50.0


def test_batch_progress_allowed_for_admin(monkeypatch):
    user = SimpleNamespace(user_id="u-admin", is_admin=True)
    fake = _FakeSupabase(batches=[_batch()], members=[])
    app = _make_app(monkeypatch, user, fake)
    with TestClient(app) as client:
        resp = client.get("/api/batches/batch-1/progress")
    assert resp.status_code == 200


def test_batch_stats_foreign_org_denied(monkeypatch):
    """An explicit organization_id must belong to the caller (unless admin)."""
    user = SimpleNamespace(user_id="u-intruder", is_admin=False)
    fake = _FakeSupabase(
        batches=[_batch(org_id="org-a")],
        members=[_member("u-owner", "org-a")],
    )
    app = _make_app(monkeypatch, user, fake)
    with TestClient(app) as client:
        resp = client.get("/api/batches/stats?organization_id=org-a")
    assert resp.status_code == 403


def test_batch_stats_own_org_allowed(monkeypatch):
    user = SimpleNamespace(user_id="u-owner", is_admin=False)
    fake = _FakeSupabase(
        batches=[_batch(org_id="org-a")],
        members=[_member("u-owner", "org-a")],
    )
    app = _make_app(monkeypatch, user, fake)
    with TestClient(app) as client:
        resp = client.get("/api/batches/stats?organization_id=org-a")
    assert resp.status_code == 200
    assert resp.json()["data"]["total_batches"] == 1


def test_batch_stats_admin_any_org_allowed(monkeypatch):
    user = SimpleNamespace(user_id="u-admin", is_admin=True)
    fake = _FakeSupabase(batches=[_batch(org_id="org-b")], members=[])
    app = _make_app(monkeypatch, user, fake)
    with TestClient(app) as client:
        resp = client.get("/api/batches/stats?organization_id=org-b")
    assert resp.status_code == 200
    assert resp.json()["data"]["total_batches"] == 1
