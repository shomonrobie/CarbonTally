"""Phase 8 B4 — narrative overlay + DM-6 drill-down API (in-memory).

Locks: A1 (requirement-bound, Owner/Admin authoring), A3 (non-empty, no length
cap), D15 (no authoring on an APPROVED/FINAL version), P3 (no calculation reach),
and the ratified **DM-6** drill-down matrix at the HTTP boundary.
"""
from __future__ import annotations

from typing import Any, Optional

import pytest
from starlette.testclient import TestClient

from api.dependencies import get_current_user, get_pool, get_repositories
from api.router import create_app
from auth import AuthUser
from tests.unit.api.fakes import (
    admin_user,
    consultant_user,
    member_user,
    org_owner_user,
)
from tests.unit.api.route_paths import flatten_router_paths

ORG = "org-a"
RV = "rv-1"
REQ = "req-1"

CONTRACT_PATHS = {
    "/api/v3/reports/{report_id}/disclosure/narrative",
    "/api/v3/reports/{report_id}/disclosure/narrative/{requirement_version_id}",
}


def _entry_row(kind: str = "CUSTOMER_COMMENTARY", body: str = "Existing note") -> dict:
    return {
        "id": "ne-1",
        "organization_id": ORG,
        "report_version_id": RV,
        "requirement_version_id": REQ,
        "disclosure_value_id": "dv-1",
        "narrative_kind": kind,
        "body": body,
        "state": "DRAFT",
        "authored_by": "u-owner",
        "authored_at": None,
        "updated_by": None,
        "updated_at": None,
        "created_at": None,
    }


def _audit_row(action: str) -> dict:
    """Minimal ``audit_trail`` row as ``AuditRepository.record`` materialises it."""
    return {
        "id": "audit-1",
        "action_type": action,
        "table_name": "test",
        "record_id": "11111111-1111-4111-8111-111111111111",
        "performed_by": "11111111-1111-4111-8111-111111111111",
        "performed_at": None,
        "old_data": None,
        "new_data": None,
        "changes": None,
        "ip_address": None,
        "metadata": None,
    }


class _State(dict):
    pass


class _FakeConn:
    def __init__(self, state: _State) -> None:
        self._s = state
        self.writes: list[tuple[str, tuple]] = []
        #: Alias used by the audit route (A10 assertions read ``calls``).
        self.calls = self.writes

    async def fetchrow(self, query: str, *args: Any) -> Optional[Any]:
        q = " ".join(query.split())
        if "JOIN public.report_generation_queue" in q:
            return self._s.get("context")
        if q.startswith("INSERT INTO public.disclosure_narrative_entries"):
            self.writes.append(("narrative_upsert", args))
            return _entry_row(str(args[4]), str(args[5]))
        if "FROM public.disclosure_values" in q and "WHERE id = $1" in q:
            return self._s.get("value")
        if q.startswith("INSERT INTO public.audit_trail"):
            self.calls.append(("audit", args))
            return _audit_row(str(args[0]))
        raise AssertionError(f"unexpected fetchrow: {q[:90]}")

    async def fetch(self, query: str, *args: Any) -> list[dict]:
        q = " ".join(query.split())
        if "FROM public.disclosure_narrative_entries" in q:
            return list(self._s.get("entries", []))
        if "LEFT JOIN public.disclosure_value_evidence" in q:
            return list(self._s.get("value_lines", []))
        if "FROM public.disclosure_values" in q:
            return list(self._s.get("values", []))
        raise AssertionError(f"unexpected fetch: {q[:90]}")

    async def execute(self, query: str, *args: Any) -> str:
        return "OK"


class _Acquire:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    async def __aenter__(self) -> _FakeConn:
        return self._conn

    async def __aexit__(self, *exc: Any) -> bool:
        return False


class _FakePool:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    def acquire(self) -> _Acquire:
        return _Acquire(self._conn)


class _Reports:
    async def get_full(self, report_id: str) -> Optional[dict]:
        return {"id": report_id, "organization_id": ORG}


class _ReportVersions:
    async def get_current(self, report_id: str) -> Optional[dict]:
        return {"id": RV}


class _Repos:
    def __init__(self) -> None:
        self.reports = _Reports()
        self.report_versions = _ReportVersions()


def _pe_staff() -> AuthUser:
    return AuthUser(
        user_id="u-pe", email="pe@carbontally.test", role="pe_staff", role_name="pe_staff",
        is_staff=True, entity_id="entity-1",
    )


@pytest.fixture
def b4n_client():
    state = _State(
        context={"organization_id": ORG, "report_id": "rep-1", "status": "DRAFT", "reporting_year": 2025},
        values=[{"id": "dv-1", "requirement_version_id": REQ, "effective_class": "REQUIRED", "value_status": "RESOLVED"}],
        value={
            "id": "dv-1", "organization_id": ORG, "report_version_id": RV,
            "requirement_version_id": REQ, "effective_class": "REQUIRED", "value_status": "RESOLVED",
        },
        value_lines=[
            {
                "disclosure_value_id": "dv-1", "id": "line-1", "line_number": 1,
                "description": "Diesel", "amount": 10, "unit": "litres",
                "document_id": "doc-1", "storage_path": "org/doc-1.pdf",
            }
        ],
        entries=[_entry_row()],
    )
    app = create_app()
    holder: dict[str, Any] = {"user": org_owner_user(ORG, "u-owner", "owner@carbontally.test")}
    conn = _FakeConn(state)

    async def _user() -> AuthUser:
        return holder["user"]

    async def _repos() -> _Repos:
        return _Repos()

    async def _pool() -> _FakePool:
        return _FakePool(conn)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_repositories] = _repos
    app.dependency_overrides[get_pool] = _pool
    client = TestClient(app)
    client.b4n_state = state  # type: ignore[attr-defined]
    client.b4n_holder = holder  # type: ignore[attr-defined]
    client.b4n_conn = conn  # type: ignore[attr-defined]
    return client


def test_narrative_routes_registered(b4n_client: TestClient) -> None:
    missing = CONTRACT_PATHS - flatten_router_paths(b4n_client.app)
    assert not missing, f"B4 narrative routes missing: {sorted(missing)}"


# -- A1/P3/D15 authoring boundary -------------------------------------------
def test_owner_can_author_narrative(b4n_client: TestClient) -> None:
    response = b4n_client.put(
        f"/api/v3/reports/rep-1/disclosure/narrative/{REQ}",
        json={"body": "We report operational control boundaries here."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["requirement_version_id"] == REQ
    assert body["state"] == "DRAFT"
    assert b4n_client.b4n_conn.writes[0][0] == "narrative_upsert"


@pytest.mark.parametrize(
    "user_factory",
    [
        lambda: member_user(ORG, "u-m", "m@carbontally.test"),
        lambda: consultant_user("u-c", "c@carbontally.test"),
        lambda: admin_user(),
        _pe_staff,
    ],
)
def test_non_owner_roles_cannot_author(b4n_client: TestClient, user_factory) -> None:
    b4n_client.b4n_holder["user"] = user_factory()
    response = b4n_client.put(
        f"/api/v3/reports/rep-1/disclosure/narrative/{REQ}", json={"body": "x"}
    )
    assert response.status_code == 403
    assert b4n_client.b4n_conn.writes == []


def test_authoring_refused_on_approved_version(b4n_client: TestClient) -> None:
    b4n_client.b4n_state["context"]["status"] = "APPROVED"
    response = b4n_client.put(
        f"/api/v3/reports/rep-1/disclosure/narrative/{REQ}", json={"body": "late edit"}
    )
    assert response.status_code == 409
    assert b4n_client.b4n_conn.writes == []


def test_requirement_must_belong_to_the_report(b4n_client: TestClient) -> None:
    response = b4n_client.put(
        "/api/v3/reports/rep-1/disclosure/narrative/req-other", json={"body": "x"}
    )
    assert response.status_code == 409
    assert "A1" in response.json()["error"]["message"]


def test_empty_body_is_rejected(b4n_client: TestClient) -> None:
    response = b4n_client.put(
        f"/api/v3/reports/rep-1/disclosure/narrative/{REQ}", json={"body": "   "}
    )
    assert response.status_code == 409


def test_unknown_kind_is_rejected(b4n_client: TestClient) -> None:
    response = b4n_client.put(
        f"/api/v3/reports/rep-1/disclosure/narrative/{REQ}",
        json={"body": "x", "narrative_kind": "FREE_FORM_ESSAY"},
    )
    assert response.status_code == 409


def test_long_body_is_accepted_no_arbitrary_limit(b4n_client: TestClient) -> None:
    response = b4n_client.put(
        f"/api/v3/reports/rep-1/disclosure/narrative/{REQ}", json={"body": "x" * 20000}
    )
    assert response.status_code == 200


def test_member_can_read_narrative(b4n_client: TestClient) -> None:
    b4n_client.b4n_holder["user"] = member_user(ORG, "u-m", "m@carbontally.test")
    response = b4n_client.get("/api/v3/reports/rep-1/disclosure/narrative")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["authoring_allowed"] is True


def test_pe_staff_cannot_read_narrative(b4n_client: TestClient) -> None:
    b4n_client.b4n_holder["user"] = _pe_staff()
    assert b4n_client.get("/api/v3/reports/rep-1/disclosure/narrative").status_code == 403


# -- DM-6 drill-down ---------------------------------------------------------
def test_owner_drilldown_is_full(b4n_client: TestClient) -> None:
    response = b4n_client.get("/api/v3/reports/rep-1/disclosure/dv-1/lines")
    assert response.status_code == 200
    body = response.json()
    assert body["drill_down_depth"] == "FULL"
    assert body["lines"][0]["document_id"] == "doc-1"


def test_viewer_drilldown_is_controlled(b4n_client: TestClient) -> None:
    b4n_client.b4n_holder["user"] = member_user(ORG, "u-m", "m@carbontally.test")
    response = b4n_client.get("/api/v3/reports/rep-1/disclosure/dv-1/lines")
    assert response.status_code == 200
    line = response.json()["lines"][0]
    assert line["amount"] == 10
    assert "document_id" not in line
    assert "storage_path" not in line


def test_consultant_drilldown_is_bounded_at_the_domain_layer(b4n_client: TestClient) -> None:
    """DM-6: consultants are BOUNDED.

    The BOUNDED projection is enforced by the ratified `DM-6` matrix (see
    ``tests/unit/domain/test_disclosure_exposure.py``). At this HTTP boundary a
    non-member consultant is stopped by the **B3 organisation-member gate**
    (``require_org_member``) *before* any drill-down decision — that boundary is
    unchanged and is not widened by B4. A consultant reaches client data through
    the consultant operating surface (AGENTS.md §10–§11), not by being treated as
    an organisation member here.
    """
    b4n_client.b4n_holder["user"] = consultant_user("u-c", "c@carbontally.test")
    response = b4n_client.get("/api/v3/reports/rep-1/disclosure/dv-1/lines")
    assert response.status_code == 403
    # No line data (and no field names) leaked in the denial.
    assert "document_id" not in response.text
    assert "storage_path" not in response.text


def test_processing_entity_drilldown_is_denied(b4n_client: TestClient) -> None:
    b4n_client.b4n_holder["user"] = _pe_staff()
    assert b4n_client.get("/api/v3/reports/rep-1/disclosure/dv-1/lines").status_code == 403


def test_internal_staff_drilldown_is_denied(b4n_client: TestClient) -> None:
    b4n_client.b4n_holder["user"] = admin_user()
    assert b4n_client.get("/api/v3/reports/rep-1/disclosure/dv-1/lines").status_code == 403


# ---------------------------------------------------------------------------
# A10 — narrative writes are audited without duplicating the prose
# ---------------------------------------------------------------------------
def test_narrative_write_is_audited_without_the_body(b4n_client: TestClient) -> None:
    secret_body = "Boundary note that must not be duplicated into the audit trail"
    response = b4n_client.put(
        f"/api/v3/reports/rep-1/disclosure/narrative/{REQ}", json={"body": secret_body}
    )
    assert response.status_code == 200
    audits = [c for c in b4n_client.b4n_conn.calls if c[0] == "audit"]
    assert audits, "the narrative write must be audited"
    payload = str(audits[0][1])
    assert secret_body not in payload, "the audit must not duplicate the narrative body"
    assert REQ in payload, "the audit must record the requirement binding"
