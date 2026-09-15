"""Phase 8 B3 — disclosure API surface (in-memory, no database access).

Verifies the contract §12.2 routes, the **server-side** authorization boundary
(organisation member read / Owner-Admin write; Processing-Entity and internal
staff denied) and the meaningful-4xx requirement for absent catalogue rows.
The development database is never opened.
"""
from __future__ import annotations

from typing import Any, Optional

import pytest
from starlette.testclient import TestClient

from api.dependencies import get_current_user, get_pool, get_repositories
from api.router import create_app
from auth import AuthUser
from tests.unit.api.fakes import admin_user, member_user, org_owner_user
from tests.unit.api.route_paths import flatten_router_paths

ORG = "org-a"

CONTRACT_PATHS = {
    "/api/v3/reports/{report_id}/disclosure",
    "/api/v3/reports/{report_id}/disclosure/{value_id}/lines",
    "/api/v3/reports/{report_id}/disclosure/project",
    "/api/v3/reports/{report_id}/intensity",
    "/api/v3/organizations/{organization_id}/applicability",
}


# ---------------------------------------------------------------------------
# In-memory pool / repositories (no database)
# ---------------------------------------------------------------------------
class _State(dict):
    """Canned responses keyed by logical name."""


class _FakeConn:
    def __init__(self, state: _State) -> None:
        self._s = state

    async def fetchrow(self, query: str, *args: Any) -> Optional[dict]:
        q = " ".join(query.split())
        if "FROM public.disclosure_values" in q and "WHERE id = $1" in q:
            return self._s.get("value")
        if "INSERT INTO public.disclosure_intensity_ratios" in q:
            return self._s.get("selection")
        raise AssertionError(f"unexpected fetchrow: {q[:90]}")

    async def fetch(self, query: str, *args: Any) -> list[dict]:
        q = " ".join(query.split())
        if "LEFT JOIN public.disclosure_value_evidence" in q:
            return list(self._s.get("value_lines", []))
        if "FROM public.disclosure_values" in q:
            return list(self._s.get("values", []))
        if "FROM public.disclosure_intensity_denominator_types" in q:
            return list(self._s.get("catalogue", []))
        if "FROM public.disclosure_intensity_ratios r" in q:
            return list(self._s.get("selected", []))
        if "FROM public.disclosure_applicability_assessments" in q:
            return list(self._s.get("assessments", []))
        raise AssertionError(f"unexpected fetch: {q[:90]}")

    async def execute(self, query: str, *args: Any) -> str:  # pragma: no cover - unused
        return "OK"


class _Acquire:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    async def __aenter__(self) -> _FakeConn:
        return self._conn

    async def __aexit__(self, *exc: Any) -> bool:
        return False


class _FakePool:
    def __init__(self, state: _State) -> None:
        self._conn = _FakeConn(state)

    def acquire(self) -> _Acquire:
        return _Acquire(self._conn)


class _Reports:
    def __init__(self, organization_id: Optional[str]) -> None:
        self._org = organization_id

    async def get_full(self, report_id: str) -> Optional[dict]:
        if self._org is None:
            return None
        return {"id": report_id, "organization_id": self._org}


class _ReportVersions:
    def __init__(self, version_id: Optional[str] = "rv-1") -> None:
        self._version_id = version_id

    async def get_current(self, report_id: str) -> Optional[dict]:
        return {"id": self._version_id} if self._version_id else None


class _Repos:
    def __init__(self, organization_id: Optional[str] = ORG, version_id: Optional[str] = "rv-1") -> None:
        self.reports = _Reports(organization_id)
        self.report_versions = _ReportVersions(version_id)


def _pe_staff() -> AuthUser:
    return AuthUser(
        user_id="u-pe",
        email="pe@carbontally.test",
        role="pe_staff",
        role_name="pe_staff",
        is_staff=True,
        entity_id="entity-1",
    )


@pytest.fixture
def b3_client():
    """Client with auth/repos/pool overrides; the state dict is mutable per test."""
    state = _State()
    app = create_app()
    holder: dict[str, Any] = {"user": admin_user()}
    repos = _Repos()

    async def _user() -> AuthUser:
        return holder["user"]

    async def _repos() -> _Repos:
        return repos

    async def _pool() -> _FakePool:
        return _FakePool(state)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_repositories] = _repos
    app.dependency_overrides[get_pool] = _pool
    client = TestClient(app)
    client.b3_state = state  # type: ignore[attr-defined]
    client.b3_holder = holder  # type: ignore[attr-defined]
    return client


# ---------------------------------------------------------------------------
# Route contract
# ---------------------------------------------------------------------------
def test_contract_routes_are_registered(b3_client: TestClient) -> None:
    paths = flatten_router_paths(b3_client.app)
    missing = CONTRACT_PATHS - paths
    assert not missing, f"contract §12.2 routes missing: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Authorization — DENY
# ---------------------------------------------------------------------------
def test_internal_staff_cannot_read_disclosures(b3_client: TestClient) -> None:
    b3_client.b3_holder["user"] = admin_user()
    response = b3_client.get(f"/api/v3/reports/rep-1/disclosure")
    assert response.status_code == 403


def test_processing_entity_staff_cannot_read_disclosures(b3_client: TestClient) -> None:
    b3_client.b3_holder["user"] = _pe_staff()
    response = b3_client.get(f"/api/v3/reports/rep-1/disclosure")
    assert response.status_code == 403


def test_member_cannot_run_projection(b3_client: TestClient) -> None:
    b3_client.b3_holder["user"] = member_user(ORG, "u-member", "member@carbontally.test")
    response = b3_client.post("/api/v3/reports/rep-1/disclosure/project", json={})
    assert response.status_code == 403
    assert "owner/admin" in response.json()["error"]["message"].lower()


def test_member_cannot_select_intensity(b3_client: TestClient) -> None:
    b3_client.b3_holder["user"] = member_user(ORG, "u-member", "member@carbontally.test")
    response = b3_client.post(
        "/api/v3/reports/rep-1/intensity",
        json={"denominator_type_id": "dt-1", "selection_basis": "because"},
    )
    assert response.status_code == 403


def test_member_cannot_create_applicability(b3_client: TestClient) -> None:
    b3_client.b3_holder["user"] = member_user(ORG, "u-member", "member@carbontally.test")
    response = b3_client.post(
        f"/api/v3/organizations/{ORG}/applicability",
        json={
            "framework_version_id": "fv-1",
            "reporting_year": 2025,
            "reporting_period_start": "2025-01-01",
            "reporting_period_end": "2025-12-31",
            "assessed_status": "APPLIES",
            "basis": "Turnover above the threshold per filed accounts",
        },
    )
    assert response.status_code == 403


def test_foreign_org_member_cannot_read(b3_client: TestClient) -> None:
    b3_client.b3_holder["user"] = member_user("org-other", "u-x", "x@carbontally.test")
    response = b3_client.get("/api/v3/reports/rep-1/disclosure")
    assert response.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Authorization — ALLOW + meaningful 4xx
# ---------------------------------------------------------------------------
def test_owner_can_read_disclosure_set(b3_client: TestClient) -> None:
    b3_client.b3_holder["user"] = org_owner_user(ORG, "u-owner", "owner@carbontally.test")
    b3_client.b3_state["values"] = [
        {"id": "v-1", "value_status": "RESOLVED"},
        {"id": "v-2", "value_status": "UNRESOLVED"},
    ]
    response = b3_client.get("/api/v3/reports/rep-1/disclosure")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert body["count_by_status"] == {"RESOLVED": 1, "UNRESOLVED": 1}


def test_unknown_report_is_404(b3_client: TestClient) -> None:
    app = b3_client.app

    async def _no_report() -> _Repos:
        return _Repos(organization_id=None)

    app.dependency_overrides[get_repositories] = _no_report
    b3_client.b3_holder["user"] = org_owner_user(ORG, "u-owner", "owner@carbontally.test")
    response = b3_client.get("/api/v3/reports/missing/disclosure")
    assert response.status_code == 404
    assert "not found" in response.json()["error"]["message"].lower()


def test_unknown_denominator_is_a_meaningful_404(b3_client: TestClient) -> None:
    """An absent catalogue row must not surface a raw database error."""
    b3_client.b3_holder["user"] = org_owner_user(ORG, "u-owner", "owner@carbontally.test")
    b3_client.b3_state["catalogue"] = []
    response = b3_client.post(
        "/api/v3/reports/rep-1/intensity",
        json={"denominator_type_id": "does-not-exist", "selection_basis": "chosen"},
    )
    assert response.status_code == 404
    detail = response.json()["error"]["message"]
    assert "controlled" in detail.lower() and "catalogue" in detail.lower()


def test_owner_can_select_a_catalogue_denominator(b3_client: TestClient) -> None:
    b3_client.b3_holder["user"] = org_owner_user(ORG, "u-owner", "owner@carbontally.test")
    b3_client.b3_state["catalogue"] = [
        {"id": "dt-1", "code": "NET_REVENUE", "name": "Net revenue / turnover", "is_active": True}
    ]
    b3_client.b3_state["selection"] = {
        "id": "sel-1",
        "denominator_type_id": "dt-1",
        "ratio_value": "2.5",
        "selection_source": "CUSTOMER_CONFIRMED",
    }
    response = b3_client.post(
        "/api/v3/reports/rep-1/intensity",
        json={
            "denominator_type_id": "dt-1",
            "selection_basis": "Customer confirmed net revenue for the period",
            "denominator_value": 100,
            "denominator_unit": "GBP",
            "numerator_value": 250,
            "selection_source": "CUSTOMER_CONFIRMED",
        },
    )
    assert response.status_code == 200
    assert response.json()["selection"]["ratio_value"] == "2.5"


def test_blank_selection_basis_is_400(b3_client: TestClient) -> None:
    b3_client.b3_holder["user"] = org_owner_user(ORG, "u-owner", "owner@carbontally.test")
    b3_client.b3_state["catalogue"] = [{"id": "dt-1", "code": "NET_REVENUE", "is_active": True}]
    response = b3_client.post(
        "/api/v3/reports/rep-1/intensity",
        json={"denominator_type_id": "dt-1", "selection_basis": "   "},
    )
    assert response.status_code == 422 or response.status_code == 400


def test_applicability_basis_may_not_assert_a_legal_determination(b3_client: TestClient) -> None:
    b3_client.b3_holder["user"] = org_owner_user(ORG, "u-owner", "owner@carbontally.test")
    response = b3_client.post(
        f"/api/v3/organizations/{ORG}/applicability",
        json={
            "framework_version_id": "fv-1",
            "reporting_year": 2025,
            "reporting_period_start": "2025-01-01",
            "reporting_period_end": "2025-12-31",
            "assessed_status": "APPLIES",
            "basis": "The organisation is legally required to report",
        },
    )
    assert response.status_code == 400
    assert "legal determination" in response.json()["error"]["message"].lower()


def test_applicability_list_returns_assessments_and_no_legal_claim(b3_client: TestClient) -> None:
    b3_client.b3_holder["user"] = org_owner_user(ORG, "u-owner", "owner@carbontally.test")
    b3_client.b3_state["assessments"] = [{"id": "a-1", "assessed_status": "UNDETERMINED"}]
    response = b3_client.get(f"/api/v3/organizations/{ORG}/applicability")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["legal_determination"] is False
