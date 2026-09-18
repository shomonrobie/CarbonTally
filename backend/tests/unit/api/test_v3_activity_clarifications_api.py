"""F-048-2/052 — activity-clarification API: authorization + anti-bypass.

The app under test is the REAL router over the REAL authorization code path
(``ensure_processing_org_access``) and the REAL clarification engine. Only the
transport dependencies FastAPI requires are substituted, through the project's
standard ``dependency_overrides`` mechanism:

* ``get_current_user`` → an authenticated ``AuthUser``, or the real 401 shape for
  an unauthenticated request (the endpoints declare ``Depends(get_current_user)``,
  so an anonymous request cannot reach the handler);
* ``get_repositories`` → a bundle whose ``clarifications`` member is the REAL
  repository over a capturing fake pool, so persistence (and the exact SQL
  parameters reaching the database) is genuinely exercised;
* ``get_matching_engine`` → a stub engine returning the scenario's candidates.

**No authorization function is mocked** — ``ensure_processing_org_access`` runs for
real, which is what makes the cross-tenant and unauthenticated cases meaningful.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from api.dependencies import get_matching_engine, get_repositories
from api.v3_activity_clarifications import router
from auth import AuthUser, get_current_user
from data.activity_clarifications import ActivityClarificationsRepository

ORG_A = "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa"
ORG_B = "bbbbbbbb-2222-4222-8222-bbbbbbbbbbbb"
USER = "cccccccc-3333-4333-8333-cccccccccccc"


class _FakeConn:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.queries: list[str] = []
        self.params: list[tuple] = []

    async def fetchrow(self, query, *args):
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        return self.rows.pop(0) if self.rows else None

    async def fetch(self, query, *args):
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        row = self.rows.pop(0) if self.rows else None
        return [] if row is None else list(row)

    async def execute(self, query, *args):
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        return "OK"


class _Acquire:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *exc):
        return False


class _Pool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _Acquire(self._conn)


class _Engine:
    """Stub matching engine — returns the scenario's candidates."""

    def __init__(self, candidates=()):
        self._candidates = list(candidates)

    def clarification_candidates(self, request):
        return list(self._candidates)


def _client(*, user=None, candidates=(), rows=()):
    conn = _FakeConn(rows)
    bundle = SimpleNamespace(
        clarifications=ActivityClarificationsRepository(_Pool(conn))  # type: ignore[arg-type]
    )
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_repositories] = lambda: bundle
    app.dependency_overrides[get_matching_engine] = lambda: _Engine(candidates)
    if user is None:

        def _unauthenticated():
            raise HTTPException(status_code=401, detail="Not authenticated")

        app.dependency_overrides[get_current_user] = _unauthenticated
    else:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app), conn


def _member(org: str = ORG_A) -> AuthUser:
    return AuthUser(
        user_id=USER,
        email="member@example.com",
        role="member",
        organization_id=org,
        is_org_member=True,
    )


def _declined_row(**over):
    row = {
        "activity_key": "k1",
        "original_activity": "Waste",
        "clarification": "i_dont_know",
        "clarification_type": "declined",
        "policy_input": "Waste",
        "outcome_status": "unresolved_declined",
        "selected_factor_id": None,
        "selected_factor_name": None,
        "factor_set": None,
        "factor_source": None,
        "reporting_year": None,
        "unit": None,
        "scope": None,
        "eligible_group_count": 0,
        "actor_id": USER,
        "actor_scope": "organization_member",
        "created_at": "2026-09-18T00:00:00+00:00",
    }
    row.update(over)
    return row


# ---------------------------------------------------------------------------
# Authentication / authorization (Parts D, I.1–I.7)
# ---------------------------------------------------------------------------


def test_unauthenticated_requests_are_denied() -> None:
    client, conn = _client(user=None)
    assert client.get(
        "/api/v3/activity-clarifications/options",
        params={"organization_id": ORG_A, "activity": "Waste"},
    ).status_code == 401
    assert client.post(
        "/api/v3/activity-clarifications/clarifications",
        json={"organization_id": ORG_A, "activity": "Waste", "clarification": "Landfill"},
    ).status_code == 401
    assert client.post(
        "/api/v3/activity-clarifications/decline",
        json={"organization_id": ORG_A, "activity": "Waste"},
    ).status_code == 401
    assert conn.params == []  # nothing reached persistence


def test_member_cannot_reach_another_organisation() -> None:
    client, conn = _client(user=_member(ORG_A))
    assert client.get(
        "/api/v3/activity-clarifications/options",
        params={"organization_id": ORG_B, "activity": "Waste"},
    ).status_code == 403
    assert client.post(
        "/api/v3/activity-clarifications/clarifications",
        json={"organization_id": ORG_B, "activity": "Waste", "clarification": "Landfill"},
    ).status_code == 403
    assert client.post(
        "/api/v3/activity-clarifications/decline",
        json={"organization_id": ORG_B, "activity": "Waste"},
    ).status_code == 403
    assert conn.params == []


# ---------------------------------------------------------------------------
# Anti-bypass: the body cannot carry authority (Parts C, I.8–I.14)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,value",
    [
        ("selected_factor_id", "11111111-2222-4333-8444-555555555555"),
        ("selected_factor_name", "Landfill of waste"),
        ("factor_set", "DEFRA 2024"),
        ("factor_source", "customer"),
        ("outcome_status", "selected"),
        ("actor_id", "99999999-9999-4999-8999-999999999999"),
    ],
)
def test_submitted_factor_metadata_is_rejected(field: str, value) -> None:
    """The *answer* cannot be supplied by the client.

    ``unit`` / ``scope`` / ``country`` / ``reporting_year`` are deliberately NOT in
    this list: they are policy INPUTS (scoping evidence for candidate lookup), which
    is why they are accepted — but the values *recorded* as the adjudication's factor
    metadata are always the server-selected factor's own, never the request's.
    """
    client, conn = _client(user=_member(), rows=[_declined_row()])
    body = {"organization_id": ORG_A, "activity": "Waste", "clarification": "Landfill"}
    body[field] = value
    assert client.post(
        "/api/v3/activity-clarifications/clarifications", json=body
    ).status_code == 422
    assert conn.params == []


def test_decline_cannot_be_told_it_succeeded_and_rejects_extras() -> None:
    client, conn = _client(user=_member(), rows=[_declined_row()])
    for extra in (
        {"outcome_status": "selected"},
        {"unit": "kg"},
        {"selected_factor_id": None},
    ):
        body = {"organization_id": ORG_A, "activity": "Waste", **extra}
        assert client.post(
            "/api/v3/activity-clarifications/decline", json=body
        ).status_code == 422
    assert conn.params == []


# ---------------------------------------------------------------------------
# Decline semantics + provenance (Parts G, H, I.18–I.20)
# ---------------------------------------------------------------------------


def test_decline_persists_unresolved_declined_without_a_factor() -> None:
    client, conn = _client(user=_member(), rows=[_declined_row()])
    response = client.post(
        "/api/v3/activity-clarifications/decline",
        json={"organization_id": ORG_A, "activity": "Waste", "activity_key": "k1"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["outcome_status"] == "unresolved_declined"
    assert body["selected_factor_id"] is None
    assert body["resolved"] is False
    assert body["actor_id"] == USER  # server-derived, never client-supplied
    assert body["actor_scope"] == "organization_member"
    assert body["clarification_type"] == "declined"

    params = conn.params[0]
    assert params[3] == ORG_A  # organisation from the authorised context
    assert params[4] == "Waste"  # original extracted evidence preserved
    assert params[6] == "i_dont_know"  # the user's statement, kept separate


def test_decline_retry_returns_the_stored_adjudication() -> None:
    client, conn = _client(user=_member(), rows=[None, _declined_row()])
    response = client.post(
        "/api/v3/activity-clarifications/decline",
        json={"organization_id": ORG_A, "activity": "Waste", "activity_key": "k1"},
    )
    assert response.status_code == 201
    assert response.json()["outcome_status"] == "unresolved_declined"
    assert (
        "ON CONFLICT ON CONSTRAINT activity_clarifications_unique DO NOTHING"
        in conn.queries[0]
    )
    assert "activity_key = $2" in conn.queries[1]  # re-read of the stored row


def test_decline_repeated_returns_the_same_state() -> None:
    client, _conn = _client(
        user=_member(), rows=[_declined_row(), _declined_row(), _declined_row()]
    )
    payload = {"organization_id": ORG_A, "activity": "Waste", "activity_key": "k1"}
    first = client.post("/api/v3/activity-clarifications/decline", json=payload)
    second = client.post("/api/v3/activity-clarifications/decline", json=payload)
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()


# ---------------------------------------------------------------------------
# Options / not-required behaviour (Part E)
# ---------------------------------------------------------------------------


def test_options_reports_state_without_offering_factor_ids() -> None:
    client, _conn = _client(user=_member(), candidates=[])
    response = client.get(
        "/api/v3/activity-clarifications/options",
        params={"organization_id": ORG_A, "activity": "Waste"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"]
    assert body["clarification_required"] is False  # no eligible candidates → no prompt
    assert body["options"] == []  # options are never invented
    assert "selected_factor_id" not in body


def test_clarification_is_not_adjudicated_when_the_engine_does_not_ask() -> None:
    client, conn = _client(user=_member(), candidates=[])
    response = client.post(
        "/api/v3/activity-clarifications/clarifications",
        json={"organization_id": ORG_A, "activity": "Waste", "clarification": "Landfill"},
    )
    assert response.status_code == 409
    assert conn.params == []  # nothing persisted, nothing guessed
