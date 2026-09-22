"""Phase 8 — deterministic bounded query planner (no LLM, no database, no SQL).

Authorization: PO Insight Discovery-Aggregation-Provenance package (2026-09-22)
under the D-01 rule that the model must never become a query engine. The planner
is pure regex parsing: these tests pin its four outcomes, its deterministic
extraction rules, and the fact that it never fabricates a parameter.
"""
from __future__ import annotations

import pytest

from services import insight_query_planner as planner


# --------------------------------------------------------------------------
# Period extraction
# --------------------------------------------------------------------------
def test_single_iso_date_is_a_one_day_period():
    assert planner.parse_period("what happened on 2024-02-02?") == ("2024-02-02", "2024-02-02")


def test_iso_date_range_is_normalised_to_ascending_order():
    assert planner.parse_period("from 2024-03-01 to 2024-01-01") == ("2024-01-01", "2024-03-01")


def test_iso_month_is_the_calendar_month():
    assert planner.parse_period("2024-02 totals") == ("2024-02-01", "2024-02-29")


def test_month_name_and_year_is_the_calendar_month():
    assert planner.parse_period("in february 2024") == ("2024-02-01", "2024-02-29")
    assert planner.parse_period("for december 2023") == ("2023-12-01", "2023-12-31")


def test_bare_year_is_the_calendar_year():
    assert planner.parse_period("by month for 2023") == ("2023-01-01", "2023-12-31")


def test_no_period_is_reported_as_missing():
    assert planner.parse_period("show me the totals") == (None, None)


# --------------------------------------------------------------------------
# Amount / tolerance extraction
# --------------------------------------------------------------------------
def test_amount_before_the_unit_and_after_the_unit():
    assert planner.extract_amount("which calculation was 20000 kg co2e")[0] == "20000"
    assert planner.extract_amount("co2e of 20,000")[0] == "20000"


def test_approximate_word_is_recorded_but_never_converted_into_a_tolerance():
    amount, approximate, tolerance_kg, tolerance_pct = planner.extract_amount(
        "approximately 20000 kg co2e"
    )
    assert amount == "20000"
    assert approximate is True
    assert tolerance_kg is None and tolerance_pct is None


def test_explicit_tolerances_are_extracted():
    assert planner.extract_amount("20000 kg co2e within 100 kg")[2] == "100"
    assert planner.extract_amount("20000 kg co2e plus or minus 5%")[3] == "5"


# --------------------------------------------------------------------------
# Scope / activity / dimension extraction
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text,expected",
    [("scope 1 emissions", "Scope 1"), ("scope 3", "Scope 3"), ("outside of scopes", "Outside of Scopes")],
)
def test_scope_extraction_uses_the_canonical_vocabulary(text, expected):
    assert planner.extract_scope(text) == (expected, False)


def test_an_invalid_scope_is_reported_as_invalid_not_dropped():
    assert planner.extract_scope("scope 9") == (None, True)


def test_activity_is_only_taken_from_a_quoted_or_labelled_term():
    assert planner.extract_activity('show me the "diesel" record') == "diesel"
    assert planner.extract_activity("activity: diesel") == "diesel"
    assert planner.extract_activity("the diesel thing") is None


@pytest.mark.parametrize(
    "text,expected",
    [
        ("emissions by facility for 2024", "facility"),
        ("total per month in 2024", "month"),
        ("breakdown by scope for 2024", "scope"),
        ("grouped by supplier in 2024", "supplier"),
        ("emissions by assets in 2024", "asset"),
        ("total by activity in 2024", "activity"),
        ("no grouping word here", None),
    ],
)
def test_dimension_detection(text, expected):
    assert planner.detect_dimension(text) == expected


# --------------------------------------------------------------------------
# The four planning outcomes
# --------------------------------------------------------------------------
def test_discovery_plan_is_produced_from_typed_filters():
    plan = planner.plan_question("which calculation was 20000 kg co2e on 2024-02-02?")
    assert plan["status"] == "planned"
    assert plan["tool"] == "insight_discovery"
    assert plan["operation"] == "discovery"
    assert plan["tool_input"] == {
        "start_date": "2024-02-02",
        "end_date": "2024-02-02",
        "co2e_kg": "20000",
    }


def test_discovery_plan_carries_an_explicit_tolerance_when_stated():
    plan = planner.plan_question("approximately 20000 kg co2e within 500 in 2024")
    assert plan["status"] == "planned"
    assert plan["tool_input"]["co2e_tolerance_kg"] == "500"
    assert plan["tool_input"]["co2e_approx"] is True


def test_approximate_amount_without_a_determinable_tolerance_is_a_clarification():
    plan = planner.plan_question("approximately 20000 kg co2e in 2024")
    assert plan["status"] == "clarification"
    assert plan["reason"] == "amount_tolerance_required"
    assert plan["tool"] is None
    assert plan["tool_input"] == {}


def test_an_invalid_scope_is_an_invalid_outcome_not_a_guess():
    plan = planner.plan_question("scope 9 emissions in 2024")
    assert plan["status"] == "invalid"
    assert plan["reason"] == "invalid_scope"


def test_aggregation_requires_an_explicit_period():
    planned = planner.plan_question("emissions by facility in 2024")
    assert planned["status"] == "planned"
    assert planned["tool"] == "insight_aggregation"
    assert planned["tool_input"] == {
        "group_by": "facility",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
    }
    unclear = planner.plan_question("emissions by facility")
    assert unclear["status"] == "clarification"
    assert unclear["reason"] == "period_required"


def test_provenance_requires_an_explicit_dimension_and_group_key():
    planned = planner.plan_question("which calculations make up scope 1 in february 2024?")
    assert planned["status"] == "planned"
    assert planned["tool"] == "insight_aggregate_provenance"
    assert planned["tool_input"] == {
        "group_by": "scope",
        "group_key": "Scope 1",
        "start_date": "2024-02-01",
        "end_date": "2024-02-29",
    }
    unclear = planner.plan_question("which calculations make up the facility total in 2024?")
    assert unclear["status"] == "clarification"
    assert unclear["reason"] == "group_key_required"


def test_an_unrecognised_question_falls_back_to_the_existing_classifier():
    plan = planner.plan_question("what is the summary of my report?")
    assert plan["status"] == "unsupported"
    assert plan["tool"] is None


def test_reporting_year_is_an_explicit_filter_not_a_calendar_period():
    plan = planner.plan_question("which calculation has reporting year 2023?")
    assert plan["status"] == "planned"
    assert plan["tool_input"] == {"reporting_year": "2023"}


def test_planning_is_deterministic():
    question = "which calculation was 20000 kg co2e on 2024-02-02?"
    assert planner.plan_question(question) == planner.plan_question(question)


def test_the_planner_never_emits_an_unknown_plan_field():
    for question in (
        "which calculation was 20000 kg co2e on 2024-02-02?",
        "emissions by facility in 2024",
        "which calculations make up scope 1 in february 2024?",
        "scope 9 emissions in 2024",
        "what is the report summary?",
    ):
        plan = planner.plan_question(question)
        assert set(plan) == {"status", "tool", "tool_input", "operation", "reason"}
        assert plan["status"] in ("planned", "clarification", "unsupported", "invalid")
        if plan["status"] == "planned":
            assert plan["tool"] in (
                "insight_discovery",
                "insight_aggregation",
                "insight_aggregate_provenance",
            )
            assert isinstance(plan["tool_input"], dict) and plan["tool_input"]
