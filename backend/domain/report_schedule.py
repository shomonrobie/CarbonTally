"""Canonical scheduled-reporting domain model (CT-IMPLEMENT-02, PD-2).

Ratified PO decision **PD-2**: implement canonical scheduled reporting — do not
retire it, and do not recreate the retired legacy ``report_schedules`` table. The
schema half of PD-2 is
``supabase/migrations/20261023000000_ct02_scheduled_reporting.sql``
(``report_schedule_definitions`` + ``report_schedule_runs``); this is the **pure**
half — the frequency vocabulary, the run/outcome vocabulary, retry semantics and
due-time arithmetic. It performs no I/O: the repository persists, the runner
orchestrates, the API authorizes and audits.

Every constant mirrors a constraint the database itself enforces, so the two can
never drift silently:

======================  =====================================================
:data:`FREQUENCIES`     ``report_schedule_definitions_frequency_check``
:data:`RUN_STATUSES`    ``report_schedule_runs_status_check``
:data:`SCHEDULE_RESULTS` ``report_schedule_definitions_result_check``
:data:`DEFAULT_RETRY_POLICY` the ``retry_policy`` column default
:data:`MAX_ATTEMPTS_BOUNDS`  ``…_retry_policy_check`` / ``…_attempt_check``
======================  =====================================================

``daily`` is deliberately **not** canonical: the legacy
``GET /api/reports/schedule/frequencies`` surface advertises it, but the canonical
frequency CHECK rejects it. The legacy advertisement is a recorded mismatch, not a
licence to widen the model.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# ---------------------------------------------------------------------------
# Frequency vocabulary (canonical — exactly the four the schema accepts)
# ---------------------------------------------------------------------------
WEEKLY = "weekly"
MONTHLY = "monthly"
QUARTERLY = "quarterly"
ANNUAL = "annual"

#: Every accepted ``report_schedule_definitions.frequency`` value.
FREQUENCIES: tuple[str, ...] = (WEEKLY, MONTHLY, QUARTERLY, ANNUAL)

#: Advertised by the retired ``/schedule/frequencies`` surface, rejected by the
#: canonical CHECK. Kept explicit so the mismatch stays visible in code.
LEGACY_UNSUPPORTED_FREQUENCIES: tuple[str, ...] = ("daily",)

#: Calendar months advanced per frequency (``weekly`` advances by 7 days).
_MONTHS_PER_FREQUENCY: dict[str, int] = {MONTHLY: 1, QUARTERLY: 3, ANNUAL: 12}

# ---------------------------------------------------------------------------
# Execution vocabulary
# ---------------------------------------------------------------------------
RUNNING = "running"
SUCCEEDED = "succeeded"
FAILED = "failed"
SKIPPED = "skipped"

#: Every accepted ``report_schedule_runs.status`` value.
RUN_STATUSES: tuple[str, ...] = (RUNNING, SUCCEEDED, FAILED, SKIPPED)

#: Terminal run states — a run leaves ``RUNNING`` at most once.
TERMINAL_RUN_STATUSES: tuple[str, ...] = (SUCCEEDED, FAILED, SKIPPED)

#: Every accepted ``report_schedule_definitions.last_result`` value.
SCHEDULE_RESULTS: tuple[str, ...] = (SUCCEEDED, FAILED, SKIPPED)

# ---------------------------------------------------------------------------
# Configuration defaults (identical to the migration's column defaults)
# ---------------------------------------------------------------------------
DEFAULT_RUN_TIME = time(7, 0)
DEFAULT_TIMEZONE = "Europe/London"

#: Bounded retry policy the runner applies when a run fails.
DEFAULT_RETRY_POLICY: Mapping[str, Any] = {
    "max_attempts": 3,
    "backoff_minutes": [5, 30, 120],
}

MIN_ATTEMPTS = 1
MAX_ATTEMPTS = 10
MAX_ATTEMPTS_BOUNDS: tuple[int, int] = (MIN_ATTEMPTS, MAX_ATTEMPTS)


class ScheduleConfigurationError(ValueError):
    """A schedule configuration the canonical schema would also reject."""



# ---------------------------------------------------------------------------
# Validation — mirrors the database constraints exactly
# ---------------------------------------------------------------------------
def validate_frequency(frequency: object) -> str:
    """Return ``frequency`` when canonical, else raise.

    ``daily`` gets an explicit message because it is the value the retired
    surface advertised.
    """
    if not isinstance(frequency, str) or frequency not in FREQUENCIES:
        extra = (
            f" {frequency!r} was advertised by the retired /schedule/frequencies "
            f"surface; it is not a canonical frequency."
            if frequency in LEGACY_UNSUPPORTED_FREQUENCIES
            else ""
        )
        raise ScheduleConfigurationError(
            f"unsupported schedule frequency {frequency!r}; canonical frequencies "
            f"are {', '.join(FREQUENCIES)}.{extra}"
        )
    return frequency


def validate_timezone(name: object) -> str:
    """Return ``name`` when it is a real IANA timezone, else raise."""
    if not isinstance(name, str) or not name:
        raise ScheduleConfigurationError("a schedule requires an IANA timezone")
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, KeyError) as exc:
        raise ScheduleConfigurationError(
            f"{name!r} is not a known IANA timezone; a schedule must run in a real "
            f"timezone, never in an implied one."
        ) from exc
    return name


def resolve_retry_policy(policy: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    """Normalise and validate a retry policy (``None`` ⇒ the canonical default)."""
    if policy is None:
        policy = DEFAULT_RETRY_POLICY
    if not isinstance(policy, Mapping):
        raise ScheduleConfigurationError("retry_policy must be a JSON object")
    if "max_attempts" not in policy:
        raise ScheduleConfigurationError("retry_policy must define max_attempts")
    try:
        attempts = int(policy["max_attempts"])
    except (TypeError, ValueError) as exc:
        raise ScheduleConfigurationError("retry_policy.max_attempts must be an integer") from exc
    if not MIN_ATTEMPTS <= attempts <= MAX_ATTEMPTS:
        raise ScheduleConfigurationError(
            f"retry_policy.max_attempts must be between {MIN_ATTEMPTS} and {MAX_ATTEMPTS}"
        )
    raw_backoff = policy.get("backoff_minutes", ())
    if isinstance(raw_backoff, (str, bytes)) or not isinstance(raw_backoff, Sequence):
        raise ScheduleConfigurationError("retry_policy.backoff_minutes must be a list")
    backoff: list[int] = []
    for value in raw_backoff:
        try:
            minutes = int(value)
        except (TypeError, ValueError) as exc:
            raise ScheduleConfigurationError(
                "retry_policy.backoff_minutes must contain whole minutes"
            ) from exc
        if minutes < 0:
            raise ScheduleConfigurationError("retry_policy.backoff_minutes cannot be negative")
        backoff.append(minutes)
    return {"max_attempts": attempts, "backoff_minutes": backoff}


# ---------------------------------------------------------------------------
# Attempt / retry semantics
# ---------------------------------------------------------------------------
def attempt_number(failure_count: int) -> int:
    """The attempt number a run takes after ``failure_count`` failures.

    The first ever run of a due slot is attempt 1; a retry after one failure is
    attempt 2. Mirrors ``report_schedule_runs.attempt`` (CHECK 1..10).
    """
    return max(int(failure_count), 0) + 1


def max_attempts(policy: Optional[Mapping[str, Any]]) -> int:
    return int(resolve_retry_policy(policy)["max_attempts"])


def can_retry(policy: Optional[Mapping[str, Any]], failure_count: int) -> bool:
    """Whether another attempt is permitted after ``failure_count`` failures."""
    return attempt_number(failure_count) <= max_attempts(policy)


def backoff_delta(policy: Optional[Mapping[str, Any]], failure_count: int) -> timedelta:
    """Delay before the next attempt, after ``failure_count`` consecutive failures.

    ``backoff_minutes`` is applied in order; the last value repeats when a policy
    declares fewer intervals than it allows attempts.
    """
    backoff = resolve_retry_policy(policy)["backoff_minutes"]
    if not backoff:
        return timedelta(0)
    index = min(max(int(failure_count), 1), len(backoff)) - 1
    return timedelta(minutes=backoff[index])


# ---------------------------------------------------------------------------
# Due-time arithmetic
# ---------------------------------------------------------------------------
def _add_months(moment: datetime, months: int) -> datetime:
    """``moment`` advanced by whole calendar months, clamping the day."""
    index = moment.month - 1 + months
    year = moment.year + index // 12
    month = index % 12 + 1
    day = min(moment.day, calendar.monthrange(year, month)[1])
    return moment.replace(year=year, month=month, day=day)


def _due_instant(day: date, run_time: time, tz: ZoneInfo) -> datetime:
    """``day`` at ``run_time`` in ``tz`` as an aware UTC instant."""
    return datetime.combine(day, run_time, tzinfo=tz).astimezone(timezone.utc)


def _advance(anchor: date, frequency: str) -> date:
    if frequency == WEEKLY:
        return anchor + timedelta(days=7)
    return _add_months(datetime.combine(anchor, time(0, 0)), _MONTHS_PER_FREQUENCY[frequency]).date()


def next_occurrence(
    frequency: str,
    run_time: time,
    timezone_name: str,
    after: datetime,
    *,
    from_date: Optional[date] = None,
) -> datetime:
    """The next due time strictly after ``after``, returned in UTC.

    ``after`` must be timezone-aware. ``from_date`` anchors the period being
    advanced (a schedule created mid-period becomes due at its next period
    boundary rather than immediately); it defaults to ``after`` in the schedule's
    own timezone.
    """
    validate_frequency(frequency)
    tz = ZoneInfo(validate_timezone(timezone_name))
    if after.tzinfo is None:
        raise ScheduleConfigurationError("a due-time calculation requires an aware timestamp")
    anchor = from_date or after.astimezone(tz).date()
    candidate = _due_instant(anchor, run_time, tz)
    # The anchor may sit on/after the reference instant (a mid-period creation, or
    # a DST shift); advance period by period until the due time really is future.
    guard = 0
    while candidate <= after and guard < 256:
        candidate = _due_instant(_advance(candidate.astimezone(tz).date(), frequency), run_time, tz)
        guard += 1
    return candidate


def is_due(next_run_at: Optional[datetime], now: datetime) -> bool:
    """Whether a schedule's persisted due time has arrived.

    The due time is read from the database (``next_run_at``), never inferred from
    in-memory state, so a restart resumes from the persisted row.
    """
    if next_run_at is None:
        return False
    if next_run_at.tzinfo is None or now.tzinfo is None:
        raise ScheduleConfigurationError("due-time comparison requires aware timestamps")
    return next_run_at <= now


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ScheduleDefinition:
    """The canonical fields of one ``report_schedule_definitions`` row."""

    id: str
    organization_id: str
    name: str
    report_type: str
    reporting_year: int
    frequency: str
    run_time: time
    timezone: str
    next_run_at: Optional[datetime]
    failure_count: int = 0
    retry_policy: Mapping[str, Any] = field(default_factory=lambda: dict(DEFAULT_RETRY_POLICY))
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    recipients: tuple[Any, ...] = ()
    is_active: bool = True

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "ScheduleDefinition":
        """Build from a database row, applying the canonical defaults."""
        run_time = row.get("run_time") or DEFAULT_RUN_TIME
        if isinstance(run_time, str):  # REST returns 'HH:MM:SS'
            parts = (run_time.split(":") + ["0", "0"])[:3]
            run_time = time(int(parts[0]), int(parts[1]))
        recipients = row.get("recipients") or ()
        return cls(
            id=str(row["id"]),
            organization_id=str(row["organization_id"]),
            name=str(row.get("name") or ""),
            report_type=str(row.get("report_type") or "annual"),
            reporting_year=int(row.get("reporting_year") or 0),
            frequency=str(row.get("frequency") or ""),
            run_time=run_time,
            timezone=str(row.get("timezone") or DEFAULT_TIMEZONE),
            next_run_at=row.get("next_run_at"),
            failure_count=int(row.get("failure_count") or 0),
            # Resolve rather than reference: a value object must own its policy, so
            # a caller can never mutate the module-level canonical default (and a
            # malformed stored policy is surfaced instead of silently defaulted).
            retry_policy=resolve_retry_policy(row.get("retry_policy")),
            period_start=row.get("period_start"),
            period_end=row.get("period_end"),
            recipients=tuple(recipients) if isinstance(recipients, Sequence) else (),
            is_active=bool(row.get("is_active", True)),
        )

    def resolved_retry_policy(self) -> dict[str, Any]:
        """This schedule's retry policy, normalised and validated."""
        return resolve_retry_policy(self.retry_policy)


@dataclass(frozen=True)
class ProducedReport:
    """What the report engine produced for one due slot.

    ``report_id`` (``report_generation_queue``) and ``report_version_id``
    (``report_versions``) are the canonical artefacts. A producer that cannot name
    them has not produced a report, so the run is recorded as a failure rather
    than as a success carrying nothing.
    """

    report_id: str
    report_version_id: Optional[str] = None
    result_summary: Optional[Mapping[str, Any]] = None

