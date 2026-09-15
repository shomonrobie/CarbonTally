"""Phase 8-X X1 — operational health domain tests (pure; no database).

Covers the bounded first-release logic: M1 queue visibility classification and M2
worker-liveness classification. These are the rules the API and worker rely on, so the
tests lock the honest-edge cases (unknowns stay unknown, completed work never inflates
the backlog age, an unclaimed job is never "stuck").
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from domain.operational_health import (
    HEARTBEAT_HEALTHY,
    HEARTBEAT_STALE,
    HEARTBEAT_UNKNOWN,
    OperationalHealthViolation,
    classify_worker_liveness,
    is_retry_exhausted,
    is_stuck,
    seconds_since,
    stage_distribution,
    summarise_queue,
)

NOW = datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc)


def _ago(seconds: int) -> datetime:
    return NOW - timedelta(seconds=seconds)


# ---------------------------------------------------------------------------
# seconds_since
# ---------------------------------------------------------------------------


def test_seconds_since_measures_elapsed_time() -> None:
    assert seconds_since(_ago(90), now=NOW) == 90


def test_seconds_since_is_none_when_unknown() -> None:
    assert seconds_since(None, now=NOW) is None


def test_seconds_since_clamps_future_timestamps_to_zero() -> None:
    assert seconds_since(NOW + timedelta(seconds=30), now=NOW) == 0


def test_seconds_since_rejects_unparseable_values() -> None:
    """A malformed tick must raise, never be silently treated as 'no tick'."""
    with pytest.raises(OperationalHealthViolation):
        seconds_since("not-a-timestamp", now=NOW)


def test_seconds_since_accepts_an_iso_string() -> None:
    """The heartbeat is read back from a JSONB payload, so ISO strings are valid.

    (This case was found by the X1 integration suite: passing the persisted string
    straight to the classifier previously raised instead of classifying.)
    """
    assert seconds_since("2026-09-14T11:58:30+00:00", now=NOW) == 90
    assert seconds_since("2026-09-14T11:58:30Z", now=NOW) == 90
    assert classify_worker_liveness("2026-09-14T11:58:30+00:00", now=NOW)["state"] == HEARTBEAT_HEALTHY


# ---------------------------------------------------------------------------
# M1 — stuck claims and retry exhaustion
# ---------------------------------------------------------------------------


def test_unclaimed_job_is_never_stuck() -> None:
    row = {"lock_token": None, "locked_at": _ago(10_000)}
    assert is_stuck(row, now=NOW, stale_after_seconds=300) is False


def test_claim_held_past_the_window_is_stuck() -> None:
    row = {"lock_token": "t-1", "locked_at": _ago(400)}
    assert is_stuck(row, now=NOW, stale_after_seconds=300) is True


def test_claim_within_the_window_is_not_stuck() -> None:
    row = {"lock_token": "t-1", "locked_at": _ago(120)}
    assert is_stuck(row, now=NOW, stale_after_seconds=300) is False


def test_retry_exhaustion_requires_both_counters() -> None:
    assert is_retry_exhausted({"attempt_count": 5, "max_attempts": 5}) is True
    assert is_retry_exhausted({"attempt_count": 6, "max_attempts": 5}) is True
    assert is_retry_exhausted({"attempt_count": 4, "max_attempts": 5}) is False
    assert is_retry_exhausted({"attempt_count": None, "max_attempts": 5}) is False
    assert is_retry_exhausted({}) is False


def test_stage_distribution_groups_missing_stage_as_unknown() -> None:
    rows = [{"stage": "queued"}, {"stage": "queued"}, {"stage": "review"}, {"stage": None}]
    assert stage_distribution(rows) == {"UNKNOWN": 1, "queued": 2, "review": 1}


# ---------------------------------------------------------------------------
# M1 — the queue summary
# ---------------------------------------------------------------------------


def test_summary_counts_open_work_and_ignores_completed_age() -> None:
    rows = [
        {"stage": "queued", "created_at": _ago(3_600)},
        {"stage": "review", "created_at": _ago(600)},
        # An old COMPLETED job must not inflate the backlog age.
        {"stage": "completed", "created_at": _ago(999_999)},
    ]
    summary = summarise_queue(rows, now=NOW, stale_after_seconds=300)
    assert summary["total_jobs"] == 3
    assert summary["open_jobs"] == 2
    assert summary["oldest_waiting_age_seconds"] == 3_600


def test_summary_reports_stuck_exhausted_and_error_counts() -> None:
    rows = [
        {"stage": "extracting", "lock_token": "t", "locked_at": _ago(900), "workflow_error_count": 2},
        {"stage": "queued", "attempt_count": 3, "max_attempts": 3, "last_error": "boom"},
        {"stage": "queued"},
    ]
    summary = summarise_queue(rows, now=NOW, stale_after_seconds=300)
    assert summary["stuck_claims"] == 1
    assert summary["retry_exhausted"] == 1
    assert summary["jobs_with_last_error"] == 1
    assert summary["workflow_error_count"] == 2


def test_summary_uses_ingested_at_when_present() -> None:
    rows = [{"stage": "mapping", "ingested_at": _ago(120), "created_at": _ago(99_999)}]
    summary = summarise_queue(rows, now=NOW)
    assert summary["oldest_waiting_age_seconds"] == 120


def test_summary_is_honest_when_there_is_no_waiting_work() -> None:
    summary = summarise_queue([], now=NOW)
    assert summary["total_jobs"] == 0
    assert summary["open_jobs"] == 0
    assert summary["oldest_waiting_age_seconds"] is None


def test_summary_rejects_a_non_positive_window() -> None:
    with pytest.raises(OperationalHealthViolation):
        summarise_queue([], now=NOW, stale_after_seconds=0)


# ---------------------------------------------------------------------------
# M2 — worker liveness
# ---------------------------------------------------------------------------


def test_no_tick_is_reported_as_unknown_never_healthy() -> None:
    liveness = classify_worker_liveness(None, now=NOW, stale_after_seconds=300)
    assert liveness["state"] == HEARTBEAT_UNKNOWN
    assert liveness["last_tick"] is None
    assert liveness["age_seconds"] is None


def test_recent_tick_is_healthy() -> None:
    liveness = classify_worker_liveness(_ago(30), now=NOW, stale_after_seconds=300)
    assert liveness["state"] == HEARTBEAT_HEALTHY
    assert liveness["age_seconds"] == 30


def test_old_tick_is_stale() -> None:
    liveness = classify_worker_liveness(_ago(900), now=NOW, stale_after_seconds=300)
    assert liveness["state"] == HEARTBEAT_STALE


def test_liveness_never_raises_an_alert_or_acts() -> None:
    """X1 reports; it does not alert. Alerting is X2 (PX-6 recipients/thresholds)."""
    liveness = classify_worker_liveness(_ago(9_999), now=NOW)
    assert set(liveness) == {"state", "last_tick", "age_seconds", "stale_after_seconds"}

