"""Phase 8 — bounded Insight aggregation and aggregate→provenance.

Authorization: PO Insight Discovery-Aggregation-Provenance package (2026-09-22).

Aggregation is CO₂e-only (kg CO₂e): a summed raw quantity across mixed units is
never exposed. Provenance returns a bounded, organisation-scoped set of the
calculation snapshots behind one aggregate cell, with an explicit truncation flag
and the existing reference kinds so the shared Source Evidence Viewer remains the
only evidence destination.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from api import v3_insight_tools
from api.dependencies import get_repositories
from auth import AuthUser, get_current_user
from tests.unit.api.insight_analytics_fakes import (
    InsightLogsFake,
    provenance_row,
    snapshot_row,
)
from tests.unit.api.insight_limit_fakes import InsightLimitsFake

ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BASE = "/api/v3/insight/tools"
PERIOD = {"start_date": "2024-01-01", "end_date": "2024-12-31"}


class _Orgs:
    async def get_by_id(self, organization_id):
        return SimpleNamespace(id=organization_id, is_active=True)


class _NoneRepo:
    async def get_by_user(self, user_id):
        return None

    async def get_active_memberships_by_user(self, user_id):
        return []


def _auth_user(organization_id=ORG_A):
    return AuthUser(
        user_id=ALICE,
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
    state = {"user": _auth_user()}

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


def _invoke(api, tool, payload, org=ORG_A):
    return api.client.post(
        f"{BASE}/invoke", json={"organization_id": org, "tool": tool, "input": payload}
    )


def _seed(api, groups=None, totals=(3, "2000.75")):
    api.logs.groups = (
        groups
        if groups is not None
        else [
            {"group_key": "Scope 1", "row_count": 2, "co2e_kg": Decimal("1500.5")},
            {"group_key": "Scope 2", "row_count": 1, "co2e_kg": Decimal("500.25")},
        ]
    )
    api.logs.totals = {"rows": totals[0], "co2e": Decimal(totals[1])}


# --------------------------------------------------------------------------
# Aggregation: every authorized dimension
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "dimension",
    ["scope", "month", "year", "activity", "supplier", "facility", "asset"],
)
def test_every_authorized_dimension_is_accepted(api, dimension):
    _seed(api)
    body = _invoke(api, "insight_aggregation", {"group_by": dimension, **PERIOD}).json()
    assert body["status"] == "success"
    assert body["data"]["group_by"] == dimension
    assert body["data"]["basis"].startswith("kg CO2e")
    assert api.logs.method_calls("aggregate_groups")[0]["dimension"] == dimension


def test_groups_are_ordered_bounded_and_labelled(api):
    _seed(
        api,
        groups=[
            {"group_key": "facility-1", "row_count": 2, "co2e_kg": Decimal("1500")},
            {"group_key": "none", "row_count": 1, "co2e_kg": Decimal("500")},
        ],
    )
    api.logs.labels = {"facility-1": "Birmingham Head Office"}
    body = _invoke(api, "insight_aggregation", {"group_by": "facility", **PERIOD}).json()
    assert [g["key"] for g in body["data"]["groups"]] == ["facility-1", "none"]
    assert body["data"]["groups"][0]["label"] == "Birmingham Head Office"
    assert body["data"]["groups"][0]["co2e_kg"] == "1500"
    assert body["data"]["group_count"] == 2
    assert body["data"]["groups_truncated"] is False


def test_group_list_truncation_is_flagged_and_the_total_stays_complete(api):
    _seed(
        api,
        groups=[
            {"group_key": f"g{index}", "row_count": 1, "co2e_kg": Decimal("10")}
            for index in range(4)
        ],
    )
    body = _invoke(
        api, "insight_aggregation", {"group_by": "scope", "limit": 2, **PERIOD}
    ).json()
    assert body["data"]["group_count"] == 2
    assert body["data"]["groups_truncated"] is True
    assert body["data"]["total_is_complete"] is False  # never presented as the whole total
    assert body["truncated"] is True
    # The period total still comes from the existing organization-scoped aggregate.
    assert body["data"]["total_co2e_kg"] == "2000.75"
    assert body["data"]["row_count"] == 3


def test_no_rows_in_period_is_no_data(api):
    _seed(api, groups=[], totals=(0, "0"))
    body = _invoke(api, "insight_aggregation", {"group_by": "scope", **PERIOD}).json()
    assert body["status"] == "no_data"
    assert body["reason"] == "no_rows_in_period"


def test_a_genuine_zero_total_is_reported_as_zero_not_as_success(api):
    _seed(
        api,
        groups=[{"group_key": "Scope 1", "row_count": 2, "co2e_kg": Decimal("0")}],
        totals=(2, "0"),
    )
    body = _invoke(api, "insight_aggregation", {"group_by": "scope", **PERIOD}).json()
    assert body["status"] == "success"
    assert body["reason"] == "zero_total"


def test_no_mixed_unit_quantity_total_is_ever_returned(api):
    _seed(api)
    body = _invoke(api, "insight_aggregation", {"group_by": "activity", **PERIOD}).json()
    assert "quantity" not in body["data"]
    assert all("quantity" not in group for group in body["data"]["groups"])


@pytest.mark.parametrize(
    "payload,reason",
    [
        ({"group_by": "scope_code", **PERIOD}, "unsupported_group_by"),
        # A missing/empty required input is refused by the closed I3 input check
        # before the handler runs; a malformed value reaches the handler.
        ({"group_by": "", **PERIOD}, "missing_required_parameter"),
        ({"group_by": "scope"}, "missing_required_parameter"),
        (
            {"group_by": "scope", "start_date": "not-a-date", "end_date": "2024-12-31"},
            "invalid_date",
        ),
        (
            {"group_by": "scope", "start_date": "2024-12-31", "end_date": "2024-01-01"},
            "invalid_date_range",
        ),
        ({"group_by": "scope", "limit": "51", **PERIOD}, "invalid_number"),
        ({"group_by": "scope", "sql": "1=1", **PERIOD}, "unknown_parameter"),
    ],
)
def test_aggregation_rejects_unsupported_dimensions_and_bad_periods(api, payload, reason):
    body = _invoke(api, "insight_aggregation", payload).json()
    assert body["status"] == "invalid_input"
    assert body["reason"] == reason
    assert api.logs.calls == []


def test_aggregation_is_organisation_scoped(api):
    _seed(api)
    _invoke(api, "insight_aggregation", {"group_by": "scope", **PERIOD}, org=ORG_A)
    assert api.logs.method_calls("aggregate_groups")[0]["org"] == ORG_A
    assert api.logs.method_calls("aggregate")[0]["org"] == ORG_A


def test_aggregation_declares_its_provenance_tool_and_carries_no_references(api):
    _seed(api)
    body = _invoke(api, "insight_aggregation", {"group_by": "scope", **PERIOD}).json()
    assert body["data"]["provenance_tool"] == "insight_aggregate_provenance"
    # An aggregate cell is a total, not a record: it carries no references.
    assert body["references"] == []


# --------------------------------------------------------------------------
# Aggregate → provenance
# --------------------------------------------------------------------------
def test_provenance_returns_the_bounded_contributing_snapshots(api):
    api.logs.group_snapshots = [provenance_row("s1"), provenance_row("s2", co2e="500")]
    body = _invoke(
        api,
        "insight_aggregate_provenance",
        {"group_by": "scope", "group_key": "Scope 1", **PERIOD},
    ).json()
    assert body["status"] == "success"
    assert [s["id"] for s in body["data"]["snapshots"]] == ["s1", "s2"]
    assert body["data"]["snapshot_count"] == 2
    assert body["data"]["snapshot_count_capped"] is False
    assert body["data"]["basis"].startswith("calculation_snapshots")
    # Identifiers first: every contributing record is an existing reference kind,
    # so the shared Source Evidence Viewer remains the only evidence destination.
    # Order is deterministic (snapshot ids, then the deduplicated evidence lines).
    assert body["references"] == [
        {"kind": "calculation_snapshot", "id": "s1"},
        {"kind": "calculation_snapshot", "id": "s2"},
        {"kind": "evidence_line_item", "id": "line-1"},
    ]


def test_provenance_reports_truncation_instead_of_a_false_complete_set(api):
    api.logs.group_snapshots = [provenance_row(f"s{index}") for index in range(4)]
    body = _invoke(
        api,
        "insight_aggregate_provenance",
        {"group_by": "scope", "group_key": "Scope 1", "limit": 2, **PERIOD},
    ).json()
    assert body["data"]["snapshot_count"] == 2
    assert body["data"]["snapshot_count_capped"] is True
    assert body["truncated"] is True
    assert api.logs.method_calls("count_group_snapshots")[0]["cap"] == 3


def test_provenance_without_contributing_snapshots_is_no_data(api):
    api.logs.group_snapshots = []
    body = _invoke(
        api,
        "insight_aggregate_provenance",
        {"group_by": "scope", "group_key": "Scope 3", **PERIOD},
    ).json()
    assert body["status"] == "no_data"
    assert body["reason"] == "no_contributing_snapshots"


def test_provenance_exposes_no_raw_content(api):
    api.logs.group_snapshots = [provenance_row("s1")]
    body = _invoke(
        api,
        "insight_aggregate_provenance",
        {"group_by": "scope", "group_key": "Scope 1", **PERIOD},
    ).json()
    snapshot = body["data"]["snapshots"][0]
    assert set(snapshot) == {
        "id", "date", "activity_type", "scope", "co2e_kg", "source_line_item_id",
    }
    for forbidden in ("source_file", "source_page", "raw_description", "signed_url", "content"):
        assert forbidden not in snapshot


@pytest.mark.parametrize(
    "payload,reason",
    [
        (
            {
                "group_by": "scope",
                "start_date": PERIOD["start_date"],
                "end_date": PERIOD["end_date"],
            },
            "missing_required_parameter",
        ),
        ({"group_by": "nope", "group_key": "x", **PERIOD}, "unsupported_group_by"),
        ({"group_by": "scope", "group_key": "x", "limit": "101", **PERIOD}, "invalid_number"),
        ({"group_by": "scope", "group_key": "x"}, "missing_required_parameter"),
        (
            {"group_by": "scope", "group_key": "x", "start_date": "nope", "end_date": "2024-12-31"},
            "invalid_date",
        ),
    ],
)
def test_provenance_rejects_invalid_requests(api, payload, reason):
    body = _invoke(api, "insight_aggregate_provenance", payload).json()
    assert body["status"] == "invalid_input"
    assert body["reason"] == reason
    assert api.logs.calls == []


def test_provenance_is_organisation_scoped_and_denied_cross_tenant(api):
    api.logs.group_snapshots = [provenance_row("s1")]
    _invoke(
        api,
        "insight_aggregate_provenance",
        {"group_by": "scope", "group_key": "Scope 1", **PERIOD},
        org=ORG_A,
    )
    assert api.logs.method_calls("list_group_snapshots")[0]["org"] == ORG_A
    api.state["user"] = _auth_user(organization_id=ORG_B)
    denied = _invoke(
        api,
        "insight_aggregate_provenance",
        {"group_by": "scope", "group_key": "Scope 1", **PERIOD},
        org=ORG_A,
    ).json()
    assert denied["status"] == "not_authorized"


def test_provenance_is_deterministic_for_identical_requests(api):
    api.logs.group_snapshots = [provenance_row("s1"), provenance_row("s2")]
    payload = {"group_by": "scope", "group_key": "Scope 1", **PERIOD}
    first = _invoke(api, "insight_aggregate_provenance", payload).json()
    second = _invoke(api, "insight_aggregate_provenance", payload).json()
    assert first["data"] == second["data"]
    assert first["references"] == second["references"]
