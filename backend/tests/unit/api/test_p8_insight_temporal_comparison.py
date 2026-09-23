"""Phase 8 P2 — bounded Insight temporal comparison (capability family 11).

Authorization: PO P2 implementation authorization (2026-09-22), bounded by the P1
capability coverage matrix (family 11 / package P2).

What these tests pin:

* the comparison formula is the authorized one and nothing else:
  ``absolute = period_B - period_A`` and
  ``percentage = ((B - A) / A) * 100`` only when ``A != 0``;
* a zero baseline returns the absolute difference plus an explicit
  "percentage not computable" result — never a division by zero, never an
  invented percentage, and never a new I4 answer state;
* both periods stay explicitly bounded, organisation-scoped and bounded in
  output, and the two period totals stay complete even when the optional group
  list truncates;
* the LLM layer receives only the deterministic values (and no causal claim).

LIMITATION (stated, not hidden): the SQL itself is not executed here. The
comparison reuses the already-verified aggregation statements
(``aggregate``/``aggregate_groups``/``group_labels``) and adds no new SQL, so the
database-level verification stays an integration task (F-046-1).
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
from domain.insight_query import (
    MAX_AGGREGATE_GROUPS,
    MAX_PERIOD_DAYS,
    PERCENTAGE_BASIS_PERIOD_A,
    PERCENTAGE_BASIS_ZERO,
    TEMPORAL_COMPARISON_DIMENSIONS,
    TOOL_INSIGHT_TEMPORAL_COMPARISON,
    compare_totals,
    order_comparison_keys,
    validate_comparison_dimension,
    validate_comparison_periods,
)
from services.insight_query_planner import (
    REASON_COMPARISON_PERIODS_REQUIRED,
    STATUS_CLARIFICATION,
    STATUS_INVALID,
    STATUS_PLANNED,
    plan_question,
)
from services.insight_tools import TOOL_REGISTRY, invoke_tool
from tests.unit.api.insight_analytics_fakes import InsightLogsFake
from tests.unit.api.insight_limit_fakes import InsightLimitsFake

ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BASE = "/api/v3/insight/tools"

#: 2026-01 vs 2025-01 — the canonical two-period comparison used throughout.
PERIOD_A = ("2026-01-01", "2026-01-31")
PERIOD_B = ("2025-01-01", "2025-01-31")
COMPARISON_INPUT = {
    "period_a_start": PERIOD_A[0],
    "period_a_end": PERIOD_A[1],
    "period_b_start": PERIOD_B[0],
    "period_b_end": PERIOD_B[1],
}


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


class _Repos:
    """The repository bundle the tool layer needs for a comparison."""

    def __init__(self, logs=None, limits=None):
        self.logs = logs or InsightLogsFake()
        self.limits = limits or InsightLimitsFake()
        # The limiter resolves its store as ``repos.insight_limits``.
        self.insight_limits = self.limits
        self.organizations = _Orgs()
        self.memberships = _NoneRepo()
        self.staff = _NoneRepo()


def _client(repos, organization_id=ORG_A):
    app = FastAPI()
    app.include_router(v3_insight_tools.router)
    app.dependency_overrides[get_repositories] = lambda: repos
    app.dependency_overrides[get_current_user] = lambda: _auth_user(organization_id)
    return TestClient(app)


def _logs_a_100_b_150() -> InsightLogsFake:
    logs = InsightLogsFake()
    logs.set_period(*PERIOD_A, rows=4, co2e="100")
    logs.set_period(*PERIOD_B, rows=6, co2e="150")
    return logs


async def _invoke(logs, tool_input=None, organization_id=ORG_A, user=None, repos=None):
    return await invoke_tool(
        tool_name=TOOL_INSIGHT_TEMPORAL_COMPARISON,
        current_user=user or _auth_user(organization_id),
        repos=repos or _Repos(logs),
        organization_id=organization_id,
        tool_input=tool_input if tool_input is not None else dict(COMPARISON_INPUT),
    )


# --------------------------------------------------------------------------
# 1. The pure contract — the formula, the zero baseline and the ordering
# --------------------------------------------------------------------------
def test_absolute_change_is_period_b_minus_period_a() -> None:
    delta = compare_totals(Decimal("100"), Decimal("150"))
    assert delta.absolute_change == Decimal("50")
    assert delta.direction == "increase"


def test_negative_change_is_reported_as_a_decrease() -> None:
    delta = compare_totals(Decimal("150"), Decimal("100"))
    assert delta.absolute_change == Decimal("-50")
    assert delta.direction == "decrease"


def test_no_change_is_reported_truthfully() -> None:
    delta = compare_totals(Decimal("100"), Decimal("100"))
    assert delta.absolute_change == Decimal("0")
    assert delta.direction == "no_change"
    assert delta.percentage_change == Decimal("0.000000")


def test_percentage_change_uses_the_authorized_formula() -> None:
    delta = compare_totals(Decimal("100"), Decimal("150"))
    assert delta.percentage_change == Decimal("50.000000")
    assert delta.percentage_change_available is True
    assert delta.percentage_basis == PERCENTAGE_BASIS_PERIOD_A


def test_half_up_quantisation_is_deterministic() -> None:
    # 1/3 → 33.333333% (six decimal places, ROUND_HALF_UP), stable on repeat.
    first = compare_totals(Decimal("3"), Decimal("4"))
    second = compare_totals(Decimal("3"), Decimal("4"))
    assert first.percentage_change == Decimal("33.333333")
    assert first == second


def test_zero_baseline_never_divides_by_zero_and_never_invents_a_percentage() -> None:
    delta = compare_totals(Decimal("0"), Decimal("150"))
    assert delta.absolute_change == Decimal("150")
    assert delta.percentage_change is None
    assert delta.percentage_change_available is False
    assert delta.percentage_basis == PERCENTAGE_BASIS_ZERO
    assert delta.direction == "increase"


def test_both_periods_zero_is_a_zero_baseline_not_a_fabricated_value() -> None:
    delta = compare_totals(Decimal("0"), Decimal("0"))
    assert delta.absolute_change == Decimal("0")
    assert delta.percentage_change is None
    assert delta.percentage_change_available is False
    assert delta.direction == "no_change"


def test_ordering_is_symmetric_and_ties_break_on_the_group_key() -> None:
    rows_a = [
        {"group_key": "b", "co2e_kg": Decimal("10")},
        {"group_key": "a", "co2e_kg": Decimal("10")},
    ]
    rows_b = [{"group_key": "b", "co2e_kg": Decimal("90")}]
    forward = order_comparison_keys(rows_a, rows_b)
    swapped = order_comparison_keys(rows_b, rows_a)
    assert forward == ["b", "a"]
    assert forward == swapped


def test_only_the_closed_comparison_dimensions_are_accepted() -> None:
    assert set(TEMPORAL_COMPARISON_DIMENSIONS) == {"scope", "activity", "facility", "asset"}
    for allowed in TEMPORAL_COMPARISON_DIMENSIONS:
        assert validate_comparison_dimension(allowed) is None
    # An omitted dimension means "overall totals" and is valid.
    assert validate_comparison_dimension(None) is None
    assert validate_comparison_dimension("") is None
    for refused in ("month", "year", "supplier", "scope; DROP TABLE", "total"):
        assert validate_comparison_dimension(refused) == "unsupported_group_by"


def test_comparison_periods_require_all_four_bounds() -> None:
    assert validate_comparison_periods(*PERIOD_A, *PERIOD_B)[4] is None
    _, _, _, _, reason = validate_comparison_periods(PERIOD_A[0], PERIOD_A[1], "", PERIOD_B[1])
    assert reason == "missing_period"


def test_comparison_periods_reject_reversed_and_unparseable_bounds() -> None:
    _, _, _, _, reversed_reason = validate_comparison_periods(
        "2026-01-31", "2026-01-01", *PERIOD_B
    )
    assert reversed_reason == "invalid_date_range"
    _, _, _, _, bad_reason = validate_comparison_periods(
        "last month", "2026-01-31", *PERIOD_B
    )
    assert bad_reason == "invalid_date"


# --------------------------------------------------------------------------
# 2. The tool — overall comparison, empty periods and the zero baseline
# --------------------------------------------------------------------------
async def test_overall_comparison_returns_both_totals_and_the_deltas() -> None:
    result = await _invoke(_logs_a_100_b_150())
    assert result.status == "success"
    assert result.tool == TOOL_INSIGHT_TEMPORAL_COMPARISON
    assert result.references == ()
    data = result.data
    assert data["group_by"] is None
    assert data["period_a"] == {
        "start_date": PERIOD_A[0],
        "end_date": PERIOD_A[1],
        "total_co2e_kg": "100",
        "row_count": 4,
    }
    assert data["period_b"]["total_co2e_kg"] == "150"
    assert data["absolute_change_kg"] == "50"
    assert data["percentage_change"] == "50.000000"
    assert data["percentage_change_available"] is True
    assert data["direction"] == "increase"
    assert data["empty_periods"] == []
    assert data["groups"] == []
    assert data["groups_truncated"] is False
    assert data["provenance_tool"] == "insight_aggregate_provenance"
    assert "kg CO2e" in data["basis"]


async def test_both_periods_empty_is_no_data_not_a_zero_versus_zero_result() -> None:
    logs = InsightLogsFake()
    logs.set_period(*PERIOD_A, rows=0, co2e="0")
    logs.set_period(*PERIOD_B, rows=0, co2e="0")
    result = await _invoke(logs)
    assert result.status == "no_data"
    assert result.reason == "no_rows_in_periods"


async def test_empty_period_a_still_reports_the_absolute_change_without_a_percentage() -> None:
    logs = InsightLogsFake()
    logs.set_period(*PERIOD_A, rows=0, co2e="0")
    logs.set_period(*PERIOD_B, rows=3, co2e="150")
    result = await _invoke(logs)
    assert result.status == "success"
    assert result.data["empty_periods"] == ["period_a"]
    assert result.data["absolute_change_kg"] == "150"
    assert result.data["percentage_change"] is None
    assert result.data["percentage_change_available"] is False
    assert result.data["percentage_basis"] == PERCENTAGE_BASIS_ZERO


async def test_empty_period_b_is_an_honest_minus_one_hundred_percent() -> None:
    logs = InsightLogsFake()
    logs.set_period(*PERIOD_A, rows=3, co2e="150")
    logs.set_period(*PERIOD_B, rows=0, co2e="0")
    result = await _invoke(logs)
    assert result.status == "success"
    assert result.data["empty_periods"] == ["period_b"]
    assert result.data["absolute_change_kg"] == "-150"
    assert result.data["percentage_change"] == "-100.000000"
    assert result.data["direction"] == "decrease"


async def test_records_present_but_both_totals_zero_is_the_zero_total_convention() -> None:
    logs = InsightLogsFake()
    logs.set_period(*PERIOD_A, rows=2, co2e="0")
    logs.set_period(*PERIOD_B, rows=5, co2e="0")
    result = await _invoke(logs)
    assert result.status == "success"
    assert result.reason == "zero_total"
    assert result.data["percentage_change"] is None
    assert result.data["percentage_basis"] == PERCENTAGE_BASIS_ZERO
    assert result.data["empty_periods"] == []


async def test_comparison_is_bounded_and_invalid_inputs_are_refused() -> None:
    logs = _logs_a_100_b_150()
    # An over-long period (beyond the ten-year bound) is a rejection, not a read.
    too_long = dict(COMPARISON_INPUT)
    too_long["period_a_start"] = "2000-01-01"
    result = await _invoke(logs, too_long)
    assert result.status == "invalid_input"
    assert result.reason == "period_too_long"

    # A reversed period, a non-date and a missing bound are all rejections.
    assert (
        await _invoke(
            logs,
            {**COMPARISON_INPUT, "period_b_start": "2025-02-01", "period_b_end": "2025-01-01"},
        )
    ).reason == "invalid_date_range"
    assert (await _invoke(logs, {**COMPARISON_INPUT, "period_a_end": "soon"})).reason == "invalid_date"
    missing = {k: v for k, v in COMPARISON_INPUT.items() if k != "period_b_start"}
    assert (await _invoke(logs, missing)).status == "invalid_input"

    # A dimension the comparison contract cannot express is refused.
    assert (await _invoke(logs, {**COMPARISON_INPUT, "group_by": "month"})).reason == (
        "unsupported_group_by"
    )
    assert (await _invoke(logs, {**COMPARISON_INPUT, "group_by": "supplier"})).reason == (
        "unsupported_group_by"
    )


async def test_single_day_periods_are_inclusive_boundaries() -> None:
    logs = InsightLogsFake()
    logs.set_period("2026-01-01", "2026-01-01", rows=1, co2e="10")
    logs.set_period("2025-01-01", "2025-01-01", rows=1, co2e="20")
    result = await _invoke(
        logs,
        {
            "period_a_start": "2026-01-01",
            "period_a_end": "2026-01-01",
            "period_b_start": "2025-01-01",
            "period_b_end": "2025-01-01",
        },
    )
    assert result.status == "success"
    assert result.data["period_a"]["end_date"] == result.data["period_a"]["start_date"]
    assert result.data["absolute_change_kg"] == "10"


async def test_identical_requests_produce_identical_results() -> None:
    first = await _invoke(_logs_a_100_b_150())
    second = await _invoke(_logs_a_100_b_150())
    assert first.as_dict() == second.as_dict()


# --------------------------------------------------------------------------
# 3. Grouped comparison — union semantics, deterministic order and the bound
# --------------------------------------------------------------------------
def _grouped_logs() -> InsightLogsFake:
    logs = InsightLogsFake()
    logs.set_period(*PERIOD_A, rows=3, co2e="100")
    logs.set_period(*PERIOD_B, rows=3, co2e="150")
    logs.set_period_groups(
        *PERIOD_A,
        [
            {"group_key": "Scope 1", "row_count": 2, "co2e_kg": Decimal("40")},
            {"group_key": "Scope 2", "row_count": 1, "co2e_kg": Decimal("60")},
        ],
    )
    logs.set_period_groups(
        *PERIOD_B,
        [{"group_key": "Scope 1", "row_count": 2, "co2e_kg": Decimal("90")}],
    )
    return logs


async def test_grouped_comparison_reports_both_periods_for_every_group() -> None:
    result = await _invoke(_grouped_logs(), {**COMPARISON_INPUT, "group_by": "scope"})
    assert result.status == "success"
    data = result.data
    assert data["group_by"] == "scope"
    assert data["group_count"] == 2
    # Largest of the two period totals first (Scope 1 has 90), then the key.
    assert [g["key"] for g in data["groups"]] == ["Scope 1", "Scope 2"]
    scope1 = data["groups"][0]
    assert scope1["period_a_co2e_kg"] == "40"
    assert scope1["period_b_co2e_kg"] == "90"
    assert scope1["absolute_change_kg"] == "50"
    assert scope1["percentage_change"] == "125.000000"
    # A group present in only one period keeps the other side's authoritative
    # zero and exposes the row counts that make the absence visible.
    scope2 = data["groups"][1]
    assert scope2["period_a_co2e_kg"] == "60"
    assert scope2["period_b_co2e_kg"] == "0"
    assert scope2["period_b_row_count"] == 0
    assert scope2["percentage_change"] == "-100.000000"


async def test_grouped_comparison_labels_only_come_from_the_organisation_catalogue() -> None:
    logs = _grouped_logs()
    logs.labels = {"Scope 1": "Scope 1 (labelled)"}
    result = await _invoke(logs, {**COMPARISON_INPUT, "group_by": "scope"})
    assert result.data["groups"][0]["label"] == "Scope 1 (labelled)"
    # No catalogue row ⇒ no invented label.
    assert result.data["groups"][1]["label"] is None


async def test_grouped_comparison_truncates_honestly_within_the_shared_bound() -> None:
    logs = InsightLogsFake()
    logs.set_period(*PERIOD_A, rows=60, co2e="600")
    logs.set_period(*PERIOD_B, rows=60, co2e="600")
    logs.set_period_groups(
        *PERIOD_A,
        [
            {"group_key": f"g{i:03d}", "row_count": 1, "co2e_kg": Decimal(str(1000 - i))}
            for i in range(MAX_AGGREGATE_GROUPS + 5)
        ],
    )
    result = await _invoke(logs, {**COMPARISON_INPUT, "group_by": "scope"})
    assert result.status == "success"
    assert result.data["group_count"] == MAX_AGGREGATE_GROUPS
    assert result.data["groups_truncated"] is True
    assert result.truncated is True
    # The period totals stay complete because they come from the aggregate, not
    # from the (truncated) group list.
    assert result.data["period_a"]["total_co2e_kg"] == "600"


async def test_a_limit_above_the_shared_bound_is_refused() -> None:
    result = await _invoke(
        _grouped_logs(),
        {**COMPARISON_INPUT, "group_by": "scope", "limit": MAX_AGGREGATE_GROUPS + 1},
    )
    assert result.status == "invalid_input"
    assert result.reason == "invalid_number"


async def test_a_group_with_a_zero_baseline_reports_no_percentage() -> None:
    logs = InsightLogsFake()
    logs.set_period(*PERIOD_A, rows=1, co2e="0")
    logs.set_period(*PERIOD_B, rows=1, co2e="25")
    logs.set_period_groups(*PERIOD_A, [])
    logs.set_period_groups(
        *PERIOD_B, [{"group_key": "Scope 1", "row_count": 1, "co2e_kg": Decimal("25")}]
    )
    result = await _invoke(logs, {**COMPARISON_INPUT, "group_by": "scope"})
    group = result.data["groups"][0]
    assert group["absolute_change_kg"] == "25"
    assert group["percentage_change"] is None
    assert group["percentage_basis"] == PERCENTAGE_BASIS_ZERO


# --------------------------------------------------------------------------
# 4. Evidence: traceability, the single viewer and no raw content
# --------------------------------------------------------------------------
def test_comparison_output_exposes_only_allowlisted_fields() -> None:
    definition = TOOL_REGISTRY[TOOL_INSIGHT_TEMPORAL_COMPARISON]
    assert set(definition.output_fields) == {
        "group_by",
        "period_a",
        "period_b",
        "absolute_change_kg",
        "percentage_change",
        "percentage_change_available",
        "percentage_basis",
        "direction",
        "groups",
        "group_count",
        "groups_truncated",
        "empty_periods",
        "comparison_dimensions",
        "basis",
        "provenance_tool",
    }
    # No reference kind is returned and no new kind is introduced anywhere.
    assert definition.reference_kinds == ()
    assert definition.read_only is True


async def test_comparison_output_carries_no_raw_content_or_signed_url() -> None:
    result = await _invoke(_grouped_logs(), {**COMPARISON_INPUT, "group_by": "scope"})
    dumped = repr(result.as_dict()).lower()
    # No raw source material, no storage handle and no signed location may appear.
    for forbidden in (
        "signed",
        "https://",
        "http://",
        "storage",
        "bucket",
        "object_key",
        "source_file",
        "source_page",
        "content_hash",
        "ocr",
        "extracted_text",
        "raw_text",
    ):
        assert forbidden not in dumped, forbidden
    # The structural guarantee behind that check: no group or period block may
    # carry a key outside the declared output allowlist.
    allowed_group_keys = {
        "key",
        "label",
        "period_a_co2e_kg",
        "period_b_co2e_kg",
        "period_a_row_count",
        "period_b_row_count",
        "absolute_change_kg",
        "percentage_change",
        "percentage_change_available",
        "percentage_basis",
        "direction",
    }
    allowed_period_keys = {"start_date", "end_date", "total_co2e_kg", "row_count"}
    for group in result.data["groups"]:
        assert set(group) == allowed_group_keys
    assert set(result.data["period_a"]) == allowed_period_keys
    assert set(result.data["period_b"]) == allowed_period_keys


async def test_comparison_result_names_the_existing_provenance_path() -> None:
    logs = _grouped_logs()
    logs.group_snapshots = [
        {
            "id": "snap-1",
            "date": "2026-01-05",
            "activity_type": "diesel",
            "scope": "Scope 1",
            "co2e_kg": Decimal("40"),
            "source_line_item_id": "line-7",
        }
    ]
    result = await _invoke(logs, {**COMPARISON_INPUT, "group_by": "scope"})
    # The comparison itself returns no references: contributing calculation
    # records stay reachable through the already-verified provenance tool, which
    # the result names together with the period bounds it needs.
    assert result.references == ()
    assert result.data["provenance_tool"] == "insight_aggregate_provenance"
    assert result.data["period_a"]["start_date"] == PERIOD_A[0]
    assert result.data["groups"][0]["key"] == "Scope 1"
    provenance = await invoke_tool(
        tool_name="insight_aggregate_provenance",
        current_user=_auth_user(),
        repos=_Repos(logs),
        organization_id=ORG_A,
        tool_input={
            "group_by": "scope",
            "group_key": "Scope 1",
            "start_date": PERIOD_A[0],
            "end_date": PERIOD_A[1],
        },
    )
    assert provenance.status == "success"
    assert provenance.references[0].kind == "calculation_snapshot"
    assert provenance.references[0].id == "snap-1"


# --------------------------------------------------------------------------
# 5. Security: organisation scoping and the closed input surface
# --------------------------------------------------------------------------
def test_comparison_route_is_organisation_scoped_and_rate_limited() -> None:
    repos = _Repos(_logs_a_100_b_150())
    client = _client(repos)
    response = client.post(
        f"{BASE}/invoke",
        json={
            "organization_id": ORG_A,
            "tool": TOOL_INSIGHT_TEMPORAL_COMPARISON,
            "input": COMPARISON_INPUT,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["absolute_change_kg"] == "50"
    # The request consumed the shared allowance: the comparison is subject to the
    # already-closed INS-01 limiter and cannot bypass it.
    assert repos.limits.consumed


def test_cross_tenant_comparison_is_denied() -> None:
    repos = _Repos(_logs_a_100_b_150())
    # A user authorised for ORG_B cannot obtain ORG_A's comparison.
    client = _client(repos, organization_id=ORG_B)
    response = client.post(
        f"{BASE}/invoke",
        json={
            "organization_id": ORG_A,
            "tool": TOOL_INSIGHT_TEMPORAL_COMPARISON,
            "input": COMPARISON_INPUT,
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "not_authorized"


def test_an_unknown_organisation_is_denied() -> None:
    repos = _Repos(_logs_a_100_b_150())
    client = _client(repos)
    response = client.post(
        f"{BASE}/invoke",
        json={
            "organization_id": "99999999-9999-4999-8999-999999999999",
            "tool": TOOL_INSIGHT_TEMPORAL_COMPARISON,
            "input": COMPARISON_INPUT,
        },
    )
    assert response.json()["status"] == "not_authorized"


def test_arbitrary_sql_and_arbitrary_columns_are_refused() -> None:
    repos = _Repos(_logs_a_100_b_150())
    client = _client(repos)
    for hostile in (
        {"group_by": "scope; DROP TABLE emissions_logs"},
        {"group_by": "1=1"},
        {"group_by": "scope, (SELECT 1)"},
    ):
        body = client.post(
            f"{BASE}/invoke",
            json={
                "organization_id": ORG_A,
                "tool": TOOL_INSIGHT_TEMPORAL_COMPARISON,
                "input": {**COMPARISON_INPUT, **hostile},
            },
        ).json()
        assert body["status"] == "invalid_input"
        assert body["reason"] == "unsupported_group_by"
    # An unaccepted parameter (an arbitrary column name) is refused outright.
    body = client.post(
        f"{BASE}/invoke",
        json={
            "organization_id": ORG_A,
            "tool": TOOL_INSIGHT_TEMPORAL_COMPARISON,
            "input": {**COMPARISON_INPUT, "select": "emissions_logs.*"},
        },
    ).json()
    assert body["status"] == "invalid_input"
    assert body["reason"] == "unknown_parameter"


def test_an_exhausted_allowance_answers_429() -> None:
    repos = _Repos(_logs_a_100_b_150())
    repos.limits.drain("user", ALICE)
    client = _client(repos)
    response = client.post(
        f"{BASE}/invoke",
        json={
            "organization_id": ORG_A,
            "tool": TOOL_INSIGHT_TEMPORAL_COMPARISON,
            "input": COMPARISON_INPUT,
        },
    )
    assert response.status_code == 429
    assert "Retry-After" in response.headers


# --------------------------------------------------------------------------
# 6. Failure path, closed vocabularies and the LLM boundary
# --------------------------------------------------------------------------
class _BrokenLogs(InsightLogsFake):
    async def aggregate(self, org_id: str, period, group_by: str):  # type: ignore[override]
        raise RuntimeError("simulated repository failure")


async def test_a_repository_failure_fails_closed_without_leaking_internals() -> None:
    result = await _invoke(_BrokenLogs())
    assert result.status == "error"
    assert result.reason == "internal_error"
    assert "simulated repository failure" not in repr(result.as_dict())
    assert result.data == {}


def test_the_tool_uses_the_closed_status_and_answer_vocabularies() -> None:
    from domain.insight_interaction import (
        ALLOWED_TOOL_STATUSES,
        TOOL_ARGUMENT_ALLOWLIST,
        AnswerStatus,
    )
    from domain.insight_tool import ToolStatus

    definition = TOOL_REGISTRY[TOOL_INSIGHT_TEMPORAL_COMPARISON]
    assert set(definition.statuses) <= set(ALLOWED_TOOL_STATUSES)
    assert set(definition.statuses) <= {s.value for s in ToolStatus}
    # The I4 answer vocabulary is untouched by this package: still fifteen states.
    assert len(list(AnswerStatus)) == 15
    assert "multiple_matches" in {s.value for s in AnswerStatus}
    # The comparison's bounded arguments are persistable; nothing else is.
    assert TOOL_ARGUMENT_ALLOWLIST[TOOL_INSIGHT_TEMPORAL_COMPARISON] == (
        "period_a_start",
        "period_a_end",
        "period_b_start",
        "period_b_end",
        "group_by",
        "limit",
    )


def test_the_catalogue_gained_exactly_one_tool() -> None:
    """The catalogue is exactly the authorized I3 set (an exact count, not a subset).

    Ten tools: the four PO-ratified read-only tools, the three Phase 8 analytics
    tools, the P2 temporal-comparison tool and the two P3 quality/reproducibility
    tools. P2 added exactly one tool; the later PO P3 implementation authorization
    (2026-09-23) added exactly two more, which is why this pin is ten rather than
    eight (MIG-1 + catalogue-pin remediation). The assertion stays an *exact*
    count so an accidental addition or removal still fails.
    """
    assert len(TOOL_REGISTRY) == 10
    assert TOOL_INSIGHT_TEMPORAL_COMPARISON in TOOL_REGISTRY


async def test_the_narration_context_carries_only_deterministic_values() -> None:
    from services.insight_interactions import _bounded_context

    result = await _invoke(_logs_a_100_b_150())
    context = _bounded_context(result.as_dict())
    # The provider layer is handed the deterministic figures, not a task to
    # compute them: the absolute change and the percentage are already decided.
    assert "50" in context
    assert "50.000000" in context
    for causal in ("cause", "because", "attribut", "why", "due to", "variance"):
        assert causal not in context.lower(), causal


async def test_the_narration_context_never_carries_a_zero_baseline_percentage() -> None:
    from services.insight_interactions import _bounded_context

    logs = InsightLogsFake()
    logs.set_period(*PERIOD_A, rows=0, co2e="0")
    logs.set_period(*PERIOD_B, rows=3, co2e="150")
    result = await _invoke(logs)
    context = _bounded_context(result.as_dict())
    # No percentage was computed, so the provider cannot narrate one.
    assert result.data["percentage_change"] is None
    assert "zero_baseline" in context
    assert "infinity" not in context.lower()
    assert "100%" not in context


# --------------------------------------------------------------------------
# 7. The planner boundary — bounded, deterministic, no new date vocabulary
# --------------------------------------------------------------------------
def test_the_planner_maps_two_explicit_months_onto_the_comparison_contract() -> None:
    plan = plan_question("compare january 2026 with january 2025")
    assert plan["status"] == STATUS_PLANNED
    assert plan["tool"] == TOOL_INSIGHT_TEMPORAL_COMPARISON
    assert plan["operation"] == "temporal_comparison"
    assert plan["tool_input"] == COMPARISON_INPUT


def test_the_planner_maps_two_explicit_years_and_an_iso_month() -> None:
    assert plan_question("compare 2024 and 2025")["tool_input"] == {
        "period_a_start": "2024-01-01",
        "period_a_end": "2024-12-31",
        "period_b_start": "2025-01-01",
        "period_b_end": "2025-12-31",
    }
    assert plan_question("comparison of 2025-01 versus 2024-01")["tool_input"] == {
        "period_a_start": "2025-01-01",
        "period_a_end": "2025-01-31",
        "period_b_start": "2024-01-01",
        "period_b_end": "2024-01-31",
    }


def test_the_planner_carries_a_supported_dimension_and_refuses_the_others() -> None:
    planned = plan_question("compare february 2026 with february 2025 by facility")
    assert planned["tool_input"]["group_by"] == "facility"
    refused = plan_question("compare january 2026 with january 2025 by supplier")
    assert refused["status"] == STATUS_INVALID
    assert refused["reason"] == "unsupported_group_by"
    refused_month = plan_question("compare january 2026 with january 2025 by month")
    assert refused_month["reason"] == "unsupported_group_by"


def test_a_comparison_without_two_periods_is_a_clarification() -> None:
    plan = plan_question("compare our emissions")
    assert plan["status"] == STATUS_CLARIFICATION
    assert plan["reason"] == REASON_COMPARISON_PERIODS_REQUIRED
    # A single explicit period is not enough to invent a baseline.
    single = plan_question("compare january 2026")
    assert single["status"] == STATUS_CLARIFICATION
    assert single["reason"] == REASON_COMPARISON_PERIODS_REQUIRED
    # Repeating the same period collapses to one, so equality cannot masquerade
    # as a two-period comparison.
    repeated = plan_question("compare january 2026 with january 2026")
    assert repeated["status"] == STATUS_CLARIFICATION


def test_the_planner_does_not_interpret_comparative_direction() -> None:
    # Directional framing is deliberately not understood: the baseline is always
    # the first-mentioned period, so an unsupported phrasing stays unsupported
    # rather than being silently reversed.
    plan = plan_question("is this month higher than last month?")
    assert plan["status"] == "unsupported"
    assert plan["tool"] is None


def test_existing_planning_behaviour_is_unchanged_for_other_questions() -> None:
    # A plain aggregation question is untouched by the comparison branch.
    plan = plan_question("emissions by facility for 2024")
    assert plan["status"] == STATUS_PLANNED
    assert plan["tool"] == "insight_aggregation"
    assert plan["tool_input"]["group_by"] == "facility"
    assert plan_question("emissions by scope for 2024")["tool"] == "insight_aggregation"
    assert plan_question("which calculation was 20000 kg co2e on 2024-02-02?")["tool"] == (
        "insight_discovery"
    )
    provenance = plan_question(
        "which calculations make up scope 1 for 2024-01-01 to 2024-12-31"
    )
    assert provenance["tool"] == "insight_aggregate_provenance"
    # A neutral comparison word always routes to the comparison contract: an
    # under-specified comparison is a clarification rather than a silent
    # single-period aggregation.
    under_specified = plan_question("compare by facility 2024")
    assert under_specified["status"] == STATUS_CLARIFICATION
    assert under_specified["reason"] == REASON_COMPARISON_PERIODS_REQUIRED
