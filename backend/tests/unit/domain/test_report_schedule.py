"""Unit tests for the canonical scheduled-reporting domain (CT-IMPLEMENT-02, PD-2).

The vocabulary asserted here mirrors the CHECK constraints in
``supabase/migrations/20261023000000_ct02_scheduled_reporting.sql``: if the
migration and this module ever disagree, one of these tests fails.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import pytest

from domain.report_schedule import (
    ANNUAL,
    DEFAULT_RETRY_POLICY,
    DEFAULT_RUN_TIME,
    DEFAULT_TIMEZONE,
    FREQUENCIES,
    LEGACY_UNSUPPORTED_FREQUENCIES,
    MAX_ATTEMPTS,
    MIN_ATTEMPTS,
    MONTHLY,
    QUARTERLY,
    RUN_STATUSES,
    SCHEDULE_RESULTS,
    TERMINAL_RUN_STATUSES,
    WEEKLY,
    ProducedReport,
    ScheduleConfigurationError,
    ScheduleDefinition,
    attempt_number,
    backoff_delta,
    can_retry,
    is_due,
    next_occurrence,
    resolve_retry_policy,
    validate_frequency,
    validate_timezone,
)


def test_frequency_vocabulary_matches_schema_check() -> None:
    # report_schedule_definitions_frequency_check: weekly|monthly|quarterly|annual
    assert FREQUENCIES == (WEEKLY, MONTHLY, QUARTERLY, ANNUAL)
    assert "daily" not in FREQUENCIES


def test_run_and_result_vocabulary_matches_schema_checks() -> None:
    assert RUN_STATUSES == ("running", "succeeded", "failed", "skipped")
    assert TERMINAL_RUN_STATUSES == ("succeeded", "failed", "skipped")
    # report_schedule_definitions_result_check excludes 'running'
    assert SCHEDULE_RESULTS == ("succeeded", "failed", "skipped")


def test_default_retry_policy_matches_column_default() -> None:
    assert resolve_retry_policy(None) == {
        "max_attempts": 3,
        "backoff_minutes": [5, 30, 120],
    }
    assert DEFAULT_RETRY_POLICY["max_attempts"] == 3
    assert (MIN_ATTEMPTS, MAX_ATTEMPTS) == (1, 10)


@pytest.mark.parametrize("frequency", FREQUENCIES)
def test_validate_frequency_accepts_canonical(frequency: str) -> None:
    assert validate_frequency(frequency) == frequency


def test_validate_frequency_rejects_daily_and_names_the_retired_surface() -> None:
    with pytest.raises(ScheduleConfigurationError) as excinfo:
        validate_frequency("daily")
    message = str(excinfo.value)
    assert "daily" in message
    assert "/schedule/frequencies" in message
    assert LEGACY_UNSUPPORTED_FREQUENCIES == ("daily",)


def test_validate_timezone_requires_a_real_iana_zone() -> None:
    assert validate_timezone(DEFAULT_TIMEZONE) == "Europe/London"
    assert validate_timezone("UTC") == "UTC"
    with pytest.raises(ScheduleConfigurationError):
        validate_timezone("Mars/Olympus")
    with pytest.raises(ScheduleConfigurationError):
        validate_timezone("")


@pytest.mark.parametrize(
    "policy",
    [
        {"max_attempts": 0},
        {"max_attempts": 11},
        {"max_attempts": "many"},
        {"backoff_minutes": [5]},
        {"max_attempts": 3, "backoff_minutes": "5,30"},
        {"max_attempts": 3, "backoff_minutes": [-1]},
        {"max_attempts": 3, "backoff_minutes": ["soon"]},
        "not-an-object",
    ],
)
def test_resolve_retry_policy_rejects_malformed(policy: object) -> None:
    with pytest.raises(ScheduleConfigurationError):
        resolve_retry_policy(policy)  # type: ignore[arg-type]


def test_resolve_retry_policy_accepts_explicit_policy() -> None:
    assert resolve_retry_policy({"max_attempts": 2, "backoff_minutes": [10]}) == {
        "max_attempts": 2,
        "backoff_minutes": [10],
    }


def test_attempt_and_retry_semantics() -> None:
    assert attempt_number(0) == 1
    assert attempt_number(2) == 3
    assert attempt_number(-5) == 1  # a failure counter is never negative
    assert can_retry(None, 0) is True
    assert can_retry(None, 2) is True
    assert can_retry(None, 3) is False  # max_attempts reached
    assert backoff_delta(None, 1) == timedelta(minutes=5)
    assert backoff_delta(None, 2) == timedelta(minutes=30)
    assert backoff_delta(None, 3) == timedelta(minutes=120)
    # Fewer intervals than attempts: the last interval repeats, never overruns.
    assert backoff_delta(None, 9) == timedelta(minutes=120)
    assert backoff_delta({"max_attempts": 1, "backoff_minutes": []}, 1) == timedelta(0)



def test_next_occurrence_is_strictly_future_and_period_anchored() -> None:
    reference = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert next_occurrence(WEEKLY, DEFAULT_RUN_TIME, "Europe/London", reference) == datetime(
        2026, 1, 8, 7, 0, tzinfo=timezone.utc
    )
    # Monthly is anchored on the schedule's own day (the persisted next_run_at is
    # authoritative), not on calendar month starts.
    assert next_occurrence(MONTHLY, DEFAULT_RUN_TIME, "Europe/London", reference) == datetime(
        2026, 2, 1, 7, 0, tzinfo=timezone.utc
    )
    mid_period = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    assert next_occurrence(MONTHLY, DEFAULT_RUN_TIME, "Europe/London", mid_period) == datetime(
        2026, 2, 15, 7, 0, tzinfo=timezone.utc
    )
    assert next_occurrence(QUARTERLY, DEFAULT_RUN_TIME, "Europe/London", reference) == datetime(
        2026, 4, 1, 6, 0, tzinfo=timezone.utc  # BST: 07:00 local == 06:00Z
    )
    assert next_occurrence(ANNUAL, DEFAULT_RUN_TIME, "Europe/London", reference) == datetime(
        2027, 1, 1, 7, 0, tzinfo=timezone.utc
    )


def test_next_occurrence_honours_an_explicit_anchor_date() -> None:
    reference = datetime(2026, 1, 20, 12, 0, tzinfo=timezone.utc)
    # Anchored on the 1st, the next monthly due time after the 20th is 1 February.
    assert next_occurrence(
        MONTHLY, DEFAULT_RUN_TIME, "Europe/London", reference, from_date=date(2026, 1, 1)
    ) == datetime(2026, 2, 1, 7, 0, tzinfo=timezone.utc)


def test_next_occurrence_handles_dst_transition() -> None:
    # 2026-03-29 is the Europe/London spring transition; local 07:00 is preserved.
    reference = datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc)
    due = next_occurrence(WEEKLY, DEFAULT_RUN_TIME, "Europe/London", reference)
    assert due == datetime(2026, 4, 1, 6, 0, tzinfo=timezone.utc)
    assert due > reference


def test_next_occurrence_rejects_bad_inputs() -> None:
    with pytest.raises(ScheduleConfigurationError):
        next_occurrence("daily", DEFAULT_RUN_TIME, "Europe/London", datetime.now(timezone.utc))
    with pytest.raises(ScheduleConfigurationError):
        next_occurrence(WEEKLY, DEFAULT_RUN_TIME, "Nope/Nope", datetime.now(timezone.utc))
    with pytest.raises(ScheduleConfigurationError):
        next_occurrence(WEEKLY, DEFAULT_RUN_TIME, "Europe/London", datetime(2026, 1, 1))


def test_is_due_reads_the_persisted_due_time_only() -> None:
    now = datetime(2026, 1, 1, 7, 0, tzinfo=timezone.utc)
    assert is_due(None, now) is False
    assert is_due(datetime(2026, 1, 1, 6, 59, tzinfo=timezone.utc), now) is True
    assert is_due(now, now) is True
    assert is_due(datetime(2026, 1, 1, 7, 1, tzinfo=timezone.utc), now) is False
    with pytest.raises(ScheduleConfigurationError):
        is_due(datetime(2026, 1, 1, 6, 0), now)


def test_schedule_definition_from_row_applies_canonical_defaults() -> None:
    definition = ScheduleDefinition.from_row(
        {
            "id": "11111111-1111-4111-8111-111111111111",
            "organization_id": "22222222-2222-4222-8222-222222222222",
            "name": "Monthly pack",
            "frequency": "monthly",
            "reporting_year": 2026,
            "run_time": "07:00:00",  # the REST path returns a string
            "recipients": [{"email": "owner@example.com"}],
            "next_run_at": datetime(2026, 2, 1, 7, 0, tzinfo=timezone.utc),
        }
    )
    assert definition.run_time == time(7, 0)
    assert definition.timezone == DEFAULT_TIMEZONE
    assert definition.report_type == "annual"
    assert definition.resolved_retry_policy() == resolve_retry_policy(None)
    assert definition.recipients == ({"email": "owner@example.com"},)
    assert definition.is_active is True
    assert definition.period_start is None


def test_schedule_definition_defaults_are_not_shared_between_instances() -> None:
    row = {
        "id": "a", "organization_id": "o", "name": "n", "frequency": "weekly",
        "reporting_year": 2026, "run_time": time(7, 0), "timezone": "UTC",
        "next_run_at": None,
    }
    first = ScheduleDefinition.from_row(dict(row))
    second = ScheduleDefinition.from_row(dict(row, id="b"))
    assert first.retry_policy is not second.retry_policy


def test_produced_report_names_the_canonical_artefacts() -> None:
    produced = ProducedReport(report_id="r1", report_version_id="v1", result_summary={"rows": 3})
    assert produced.report_id == "r1"
    assert produced.report_version_id == "v1"
    assert ProducedReport(report_id="r2").report_version_id is None
