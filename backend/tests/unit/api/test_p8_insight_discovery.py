"""Phase 8 — bounded Insight discovery (dimensions, outcomes, tenant isolation).

Authorization: PO Insight Discovery-Aggregation-Provenance package (2026-09-22).

Exercised through the real I3 HTTP surface with an in-memory repository double, so
the test covers validation → I2 authorization → bounded query → result shape.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from api import v3_insight_tools
from api.dependencies import get_repositories
from auth import AuthUser, get_current_user
from tests.unit.api.insight_analytics_fakes import InsightLogsFake, snapshot_row
from tests.unit.api.insight_limit_fakes import InsightLimitsFake

ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BASE = "/api/v3/insight/tools"
TOOL = "insight_discovery"


class _Orgs:
    async def get_by_id(self, organization_id):
        return SimpleNamespace(id=organization_id, is_active=True)


class _NoneRepo:
    async def get_by_user(self, user_id):
        return None

    async def get_active_memberships_by_user(self, user_id):
        return []


def _user(user_id=ALICE, organization_id=ORG_A):
    return AuthUser(
        user_id=user_id,
        email="alice@example.test",
        role="org_owner",
        role_name="org_owner",
        organization_id=organization_id,
        is_org_member=True,
    )


@pytest.fixture()
def api():
    logs = InsightLogsFake()
    app = FastAPI()
    app.include_router(v3_insight_tools.router)
    state = {"user": _user()}

    async def _current_user():
        return state["user"]

    async def _repositories():
        return SimpleNamespace(
            organizations=_Orgs(),
            staff=_NoneRepo(),
            consultants=_NoneRepo(),
            logs=logs,
            insight=None,
            insight_limits=InsightLimitsFake(),
        )

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_repositories] = _repositories
    return SimpleNamespace(client=TestClient(app), logs=logs, state=state)


def _discover(api, payload, org=ORG_A):
    return api.client.post(
        f"{BASE}/invoke", json={"organization_id": org, "tool": TOOL, "input": payload}
    )


# --------------------------------------------------------------------------
# Outcomes: zero / one / multiple
# --------------------------------------------------------------------------
def test_zero_matches_is_no_data(api):
    api.logs.snapshots.append(snapshot_row("s1", organization_id=ORG_A, co2e="100"))
    body = _discover(api, {"co2e_kg": "99999"}).json()
    assert body["status"] == "no_data"
    assert body["reason"] == "no_matches"
    assert body["data"] == {}


def test_exactly_one_match_is_success(api):
    api.logs.snapshots.append(snapshot_row("s1", organization_id=ORG_A))
    body = _discover(api, {"co2e_kg": "20000"}).json()
    assert body["status"] == "success"
    assert body["reason"] is None
    assert body["data"]["match_count"] == 1
    assert body["data"]["match_count_capped"] is False
    assert [c["id"] for c in body["data"]["candidates"]] == ["s1"]
    assert body["references"] == [
        {"kind": "calculation_snapshot", "id": "s1"},
        {"kind": "evidence_line_item", "id": "line-1"},
    ]


def test_several_matches_are_reported_as_such_not_as_success(api):
    for index in range(3):
        api.logs.snapshots.append(snapshot_row(f"s{index}", organization_id=ORG_A))
    body = _discover(api, {"start_date": "2024-02-01", "end_date": "2024-02-29"}).json()
    assert body["status"] == "success"
    assert body["reason"] == "multiple_matches"
    assert body["data"]["match_count"] == 3
    assert len(body["data"]["candidates"]) == 3


def test_match_count_is_capped_and_flagged_beyond_the_bound(api):
    for index in range(5):
        api.logs.snapshots.append(snapshot_row(f"s{index}", organization_id=ORG_A))
    body = _discover(
        api, {"start_date": "2024-01-01", "end_date": "2024-12-31", "limit": 2}
    ).json()
    assert body["reason"] == "multiple_matches"
    assert body["data"]["match_count"] == 3  # bounded by limit + 1, never a full count
    assert body["data"]["match_count_capped"] is True
    assert body["truncated"] is True
    assert len(body["data"]["candidates"]) == 2


# --------------------------------------------------------------------------
# Dimension coverage
# --------------------------------------------------------------------------
def test_date_single_day_is_inclusive(api):
    api.logs.snapshots.append(snapshot_row("s1", organization_id=ORG_A, date_value="2024-02-02"))
    api.logs.snapshots.append(snapshot_row("s2", organization_id=ORG_A, date_value="2024-02-03"))
    body = _discover(api, {"start_date": "2024-02-02", "end_date": "2024-02-02"}).json()
    assert [c["id"] for c in body["data"]["candidates"]] == ["s1"]


def test_date_range_and_reporting_year_are_distinct_filters(api):
    api.logs.snapshots.append(
        snapshot_row("s1", organization_id=ORG_A, date_value="2024-02-02", reporting_year=2024)
    )
    api.logs.snapshots.append(
        snapshot_row("s2", organization_id=ORG_A, date_value="2023-02-02", reporting_year=2023)
    )
    ranged = _discover(api, {"start_date": "2024-01-01", "end_date": "2024-12-31"}).json()
    assert [c["id"] for c in ranged["data"]["candidates"]] == ["s1"]
    yearly = _discover(api, {"reporting_year": "2023"}).json()
    assert [c["id"] for c in yearly["data"]["candidates"]] == ["s2"]


def test_scope_activity_supplier_facility_and_asset_filters(api):
    api.logs.snapshots.append(
        snapshot_row(
            "s1", organization_id=ORG_A, activity_type="diesel", scope="Scope 1", supplier_id="sup-1"
        )
    )
    api.logs.snapshots.append(
        snapshot_row(
            "s2", organization_id=ORG_A, activity_type="electricity", scope="Scope 2", supplier_id=None
        )
    )

    def candidates(payload):
        return [c["id"] for c in _discover(api, payload).json()["data"]["candidates"]]

    assert candidates({"scope": "1"}) == ["s1"]
    assert candidates({"activity": "diesel"}) == ["s1"]
    assert candidates({"supplier_id": "sup-1"}) == ["s1"]
    assert candidates({"facility_id": "facility-1"}) == ["s1", "s2"]
    assert candidates({"asset_id": "asset-1"}) == ["s1", "s2"]


def test_supplier_dimension_is_honest_when_no_emission_carries_a_supplier(api):
    """The known supplier-data limitation stays visible as ``no_data``, not a guess."""
    api.logs.snapshots.append(snapshot_row("s1", organization_id=ORG_A, supplier_id=None))
    body = _discover(api, {"supplier_id": "sup-absent"}).json()
    assert body["status"] == "no_data"
    assert body["reason"] == "no_matches"
    assert api.logs.method_calls("search_snapshots")[0]["filters"] == {"supplier_id": "sup-absent"}


# --------------------------------------------------------------------------
# Amount matching and tolerance
# --------------------------------------------------------------------------
def test_exact_amount_uses_zero_tolerance(api):
    api.logs.snapshots.append(snapshot_row("s1", organization_id=ORG_A, co2e="20000"))
    api.logs.snapshots.append(snapshot_row("s2", organization_id=ORG_A, co2e="20001"))
    body = _discover(api, {"co2e_kg": "20000"}).json()
    assert [c["id"] for c in body["data"]["candidates"]] == ["s1"]


def test_explicit_absolute_and_relative_tolerances_widen_the_match(api):
    api.logs.snapshots.append(snapshot_row("s1", organization_id=ORG_A, co2e="20001"))
    absolute = _discover(api, {"co2e_kg": "20000", "co2e_tolerance_kg": "100"}).json()
    assert [c["id"] for c in absolute["data"]["candidates"]] == ["s1"]
    relative = _discover(api, {"co2e_kg": "20000", "co2e_tolerance_pct": "1"}).json()
    assert [c["id"] for c in relative["data"]["candidates"]] == ["s1"]


def test_approximate_amount_without_tolerance_is_refused_not_guessed(api):
    api.logs.snapshots.append(snapshot_row("s1", organization_id=ORG_A))
    body = _discover(api, {"co2e_kg": "20000", "co2e_approx": True}).json()
    assert body["status"] == "invalid_input"
    assert body["reason"] == "amount_tolerance_required"
    assert api.logs.method_calls("search_snapshots") == []


def test_conflicting_tolerances_are_refused(api):
    body = _discover(
        api, {"co2e_kg": "20000", "co2e_tolerance_kg": "10", "co2e_tolerance_pct": "5"}
    ).json()
    assert body["status"] == "invalid_input"
    assert body["reason"] == "conflicting_tolerance"


# --------------------------------------------------------------------------
# Invalid input and tenant isolation
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "payload,reason",
    [
        ({}, "no_discovery_filters"),
        ({"start_date": "yesterday"}, "invalid_date"),
        ({"start_date": "2024-03-01", "end_date": "2024-01-01"}, "invalid_date_range"),
        ({"start_date": "2000-01-01", "end_date": "2024-01-01"}, "period_too_long"),
        ({"reporting_year": "nope"}, "invalid_number"),
        ({"co2e_kg": "-5"}, "negative_amount"),
        ({"scope": "Scope 9"}, "invalid_scope"),
        ({"activity": "ab"}, "activity_term_too_short"),
        ({"supplier_id": "x", "plant": "y"}, "unknown_parameter"),
        ({"limit": "0"}, "invalid_number"),
        ({"limit": "9999"}, "invalid_number"),
    ],
)
def test_invalid_parameters_are_refused(api, payload, reason):
    body = _discover(api, payload).json()
    assert body["status"] == "invalid_input"
    assert body["reason"] == reason
    assert api.logs.calls == []


def test_the_query_is_always_the_callers_own_organisation(api):
    api.logs.snapshots.append(snapshot_row("other", organization_id=ORG_B))
    body = _discover(api, {"reporting_year": "2024"}, org=ORG_A).json()
    assert body["status"] == "no_data"
    assert api.logs.method_calls("search_snapshots")[0]["org"] == ORG_A


def test_a_foreign_organisation_request_is_denied_before_any_query(api):
    api.state["user"] = _user(user_id=ALICE, organization_id=ORG_B)
    body = _discover(api, {"reporting_year": "2024"}, org=ORG_A).json()
    assert body["status"] == "not_authorized"
    assert api.logs.calls == []


def test_discovery_is_deterministic_for_identical_requests(api):
    api.logs.snapshots.append(snapshot_row("s1", organization_id=ORG_A))
    first = _discover(api, {"reporting_year": "2024"}).json()
    second = _discover(api, {"reporting_year": "2024"}).json()
    assert first["data"] == second["data"]
    assert first["references"] == second["references"]
