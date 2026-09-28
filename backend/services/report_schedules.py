"""Canonical scheduled-reporting service (CT-IMPLEMENT-03 / PD-2).

The application layer between the API routes and the canonical persistence
(``data.report_schedules``) + domain (``domain.report_schedule``). It owns
exactly three responsibilities:

1. **Validation** — a schedule is validated against the canonical vocabulary
   (the same values the database's CHECK constraints accept) *before* it is
   written, so a caller receives a described 4xx rather than a raw constraint
   violation, and an invalid frequency can never be persisted.
2. **Due-time computation** — ``next_run_at`` is computed through
   ``domain.report_schedule.next_occurrence`` in the schedule's own timezone.
   There is no second copy of that arithmetic here.
3. **Auditing** — create / pause / resume / delete and every run outcome append
   to the canonical ``audit_trail``. PD-2 requires create/change/deletion
   auditing; this module supplies the human actions and
   :func:`build_audit_sink` supplies the runner's outcomes. Both use
   ``correlation_id = schedule id``, as the migration's table comment requires.

Nothing here talks to a database client type directly — it consumes the
repository through its declared methods, so the legacy compatibility routes and
the canonical ``/api/v3`` routes share one implementation rather than two.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone
from typing import Any, Awaitable, Callable, Mapping, Optional, Sequence

from core.logging import get_logger
from domain.audit import (
    ACTOR_ORG_USER,
    ACTOR_SYSTEM,
    CAT_REPORT,
    ORIGIN_HUMAN,
    ORIGIN_SYSTEM,
    OUTCOME_FAILURE,
    OUTCOME_SUCCESS,
    AuditEntry,
)
from domain.report_schedule import (
    FREQUENCIES,
    SCHEDULE_REPORT_TYPES,
    ScheduleConfigurationError,
    next_occurrence as domain_next_occurrence,
    resolve_retry_policy,
    validate_frequency as domain_validate_frequency,
    validate_timezone as domain_validate_timezone,
)

logger = get_logger(__name__)

#: Audit actions for schedule lifecycle changes (all classify to CAT_REPORT).
AUDIT_SCHEDULE_CREATED = "report_schedule_created"
AUDIT_SCHEDULE_PAUSED = "report_schedule_paused"
AUDIT_SCHEDULE_RESUMED = "report_schedule_resumed"
AUDIT_SCHEDULE_DELETED = "report_schedule_deleted"
AUDIT_SCHEDULE_RUN_SUCCEEDED = "report_schedule_run_succeeded"
AUDIT_SCHEDULE_RUN_FAILED = "report_schedule_run_failed"
AUDIT_SCHEDULE_RUN_SKIPPED = "report_schedule_run_skipped"
AUDIT_SCHEDULE_SLOT_DEDUPLICATED = "report_schedule_run_slot_deduplicated"

#: Entity/table name recorded on every schedule audit entry.
ENTITY_SCHEDULE = "report_schedule_definitions"

#: Human-readable labels for the canonical frequencies (presentation only).
FREQUENCY_LABELS: Mapping[str, str] = {
    "weekly": "Weekly",
    "monthly": "Monthly",
    "quarterly": "Quarterly",
    "annual": "Annual",
}


class ScheduleValidationError(ValueError):
    """A schedule request the canonical model (and the database) rejects."""

    def __init__(self, message: str, *, field: Optional[str] = None) -> None:
        super().__init__(message)
        self.field = field


class ScheduleInUseError(ScheduleValidationError):
    """The schedule has execution history and therefore cannot be deleted.

    The canonical schema makes a run append-only (``DELETE`` is refused for every
    role) and deletes a definition's runs by cascade, so deleting a schedule that
    has run would breach the guard. The supported action is to pause it.
    """


def canonical_frequencies() -> list[dict[str, str]]:
    """The canonical frequency vocabulary, for the API to advertise.

    Exactly the four values ``report_schedule_definitions_frequency_check``
    accepts. ``daily`` is deliberately absent — the database rejects it, so
    advertising it would be an invitation to a constraint violation.
    """
    return [
        {"value": value, "label": FREQUENCY_LABELS.get(value, value.title())}
        for value in FREQUENCIES
    ]


def classify_recipient(value: str) -> tuple[Optional[str], Optional[str]]:
    """Split one recipient string into ``(user_id, email)``.

    A value containing ``@`` is an email address (normalised to lower case, which
    the schema's ``report_shares_email_normalised_check``-style normalisation
    requires for share recipients and keeps consistent here); anything else is
    treated as a user id. At least one of the two is always returned, so the
    schema's "recipient is explicit" requirement can never be satisfied by an
    empty value.
    """
    text = (value or "").strip()
    if not text:
        raise ScheduleValidationError(
            "a recipient must be a user id or an email address", field="recipients"
        )
    if "@" in text:
        return None, text.lower()
    return text, None


def normalise_recipients(values: Sequence[Any]) -> list[dict[str, Optional[str]]]:
    """Normalise a recipient list into explicit recipient objects.

    Each element becomes ``{"user_id": …, "email": …}`` with at least one of the
    two populated, which is the shape the schedule's ``recipients`` column
    comment describes ("each element names an authenticated user and/or an
    address"). An empty list is refused: a schedule with nobody to send to would
    execute and deliver nothing, which is not a working schedule.
    """
    if not values:
        raise ScheduleValidationError(
            "a schedule requires at least one recipient", field="recipients"
        )
    recipients: list[dict[str, Optional[str]]] = []
    for value in values:
        if isinstance(value, Mapping):
            user_id = value.get("user_id") or None
            email = value.get("email") or None
            if not user_id and not email:
                raise ScheduleValidationError(
                    "a recipient must name a user id or an email address",
                    field="recipients",
                )
            recipients.append(
                {
                    "user_id": str(user_id) if user_id else None,
                    "email": str(email).lower() if email else None,
                }
            )
            continue
        user_id, email = classify_recipient(str(value))
        recipients.append({"user_id": user_id, "email": email})
    return recipients


def validate_frequency(value: object) -> str:
    """Canonical frequency validation, expressed as a schedule-request error.

    The domain raises :class:`ScheduleConfigurationError` (shared with the
    runner, where a stored configuration is at fault). At the request boundary the
    same condition is a *request* error, so it is translated here with a field
    name the API can report.
    """
    try:
        return domain_validate_frequency(value)
    except ScheduleConfigurationError as exc:
        raise ScheduleValidationError(str(exc), field="frequency") from exc


def validate_timezone(name: object) -> str:
    """IANA timezone validation, expressed as a schedule-request error."""
    try:
        return domain_validate_timezone(name)
    except ScheduleConfigurationError as exc:
        raise ScheduleValidationError(str(exc), field="timezone") from exc


def validate_report_type(report_type: object) -> str:
    """Return ``report_type`` when the canonical engine supports it, else raise."""
    if not isinstance(report_type, str) or report_type not in SCHEDULE_REPORT_TYPES:
        raise ScheduleValidationError(
            f"unsupported schedule report_type {report_type!r}; a schedule may only "
            f"drive a report the engine actually produces "
            f"({', '.join(SCHEDULE_REPORT_TYPES)})",
            field="report_type",
        )
    return report_type


def validate_name(name: object) -> str:
    """Return a non-blank schedule name, else raise (mirrors the name CHECK)."""
    if not isinstance(name, str) or not name.strip():
        raise ScheduleValidationError("a schedule requires a name", field="name")
    return name.strip()


def validate_reporting_year(year: object) -> int:
    """Return an in-range reporting year, else raise (mirrors the year CHECK)."""
    try:
        value = int(year)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ScheduleValidationError(
            "reporting_year must be a whole year", field="reporting_year"
        ) from exc
    if not 1990 <= value <= 2100:
        raise ScheduleValidationError(
            "reporting_year must be between 1990 and 2100", field="reporting_year"
        )
    return value


def validate_period(
    period_start: Optional[date], period_end: Optional[date]
) -> tuple[Optional[date], Optional[date]]:
    """Validate an optional reporting period (mirrors the period-order CHECK)."""
    if period_start is not None and period_end is not None and period_end < period_start:
        raise ScheduleValidationError(
            "period_end must not precede period_start", field="period_end"
        )
    return period_start, period_end


def validate_run_time(value: object) -> time:
    """Return the schedule's local run time, else raise."""
    if isinstance(value, time):
        return value
    if isinstance(value, str) and value.strip():
        parts = (value.strip().split(":") + ["0", "0"])[:3]
        try:
            return time(int(parts[0]), int(parts[1]))
        except (TypeError, ValueError) as exc:
            raise ScheduleValidationError(
                "run_time must be a local time of day (HH:MM)", field="run_time"
            ) from exc
    raise ScheduleValidationError(
        "run_time must be a local time of day (HH:MM)", field="run_time"
    )


def next_due_at(
    frequency: str,
    run_time: time,
    timezone_name: str,
    after: datetime,
) -> datetime:
    """The next due instant (UTC) strictly after ``after``.

    Delegates to the canonical domain arithmetic — the same function the runner
    uses to advance a slot — so a created schedule's first due time and its later
    occurrences cannot diverge. ``after`` must be timezone-aware.
    """
    validate_frequency(frequency)
    validate_timezone(timezone_name)
    try:
        return domain_next_occurrence(frequency, run_time, timezone_name, after)
    except ScheduleConfigurationError as exc:
        raise ScheduleValidationError(str(exc), field="run_time") from exc


def resolve_policy(policy: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    """Retry-policy validation, expressed as a schedule-request error."""
    try:
        return resolve_retry_policy(policy)
    except ScheduleConfigurationError as exc:
        raise ScheduleValidationError(str(exc), field="retry_policy") from exc


def _iso(value: Any) -> Optional[str]:
    """ISO-8601 for datetime/date columns, verbatim for anything else."""
    return value.isoformat() if getattr(value, "isoformat", None) else value


def shape_schedule(row: Mapping[str, Any]) -> dict:
    """JSON-ready shape of one schedule definition (no raw database types).

    Shared by the canonical ``/api/v3`` surface and the legacy compatibility
    surface, so both describe the same persisted row identically.
    """
    run_time = row.get("run_time")
    return {
        "id": str(row["id"]),
        "organization_id": str(row["organization_id"]),
        "name": row.get("name"),
        "report_type": row.get("report_type"),
        "reporting_year": row.get("reporting_year"),
        "period_start": _iso(row.get("period_start")),
        "period_end": _iso(row.get("period_end")),
        "frequency": row.get("frequency"),
        "run_time": (
            run_time.strftime("%H:%M") if isinstance(run_time, time) else run_time
        ),
        "timezone": row.get("timezone"),
        "recipients": list(row.get("recipients") or []),
        "is_active": bool(row.get("is_active", True)),
        "paused_at": _iso(row.get("paused_at")),
        "next_run_at": _iso(row.get("next_run_at")),
        "last_run_at": _iso(row.get("last_run_at")),
        "last_result": row.get("last_result"),
        "last_error": row.get("last_error"),
        "failure_count": int(row.get("failure_count") or 0),
        "retry_policy": dict(row.get("retry_policy") or {}),
        "created_by": row.get("created_by"),
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
    }


def shape_run(row: Mapping[str, Any]) -> dict:
    """JSON-ready shape of one run row (real outcome, canonical artefacts)."""
    return {
        "id": str(row["id"]),
        "schedule_id": str(row["schedule_id"]),
        "scheduled_for": _iso(row.get("scheduled_for")),
        "attempt": row.get("attempt"),
        "status": row.get("status"),
        "started_at": _iso(row.get("started_at")),
        "finished_at": _iso(row.get("finished_at")),
        "report_id": row.get("report_id"),
        "report_version_id": row.get("report_version_id"),
        "result_summary": row.get("result_summary"),
        "error_code": row.get("error_code"),
        "error_message": row.get("error_message"),
    }


def build_audit_sink(repos: Any) -> Callable[[str, Mapping[str, Any]], Awaitable[None]]:
    """The runner's audit sink, bound to the canonical ``audit_trail``.

    ``correlation_id`` is the schedule id, as the PD-2 migration's table comment
    requires. The entry is written by the **system** (the scheduler acted, not a
    person), classified ``CAT_REPORT``, and carries only identifiers and states —
    never report narratives or document content. Best-effort by design: the
    runner already treats an audit failure as non-fatal, and this closure keeps
    that behaviour explicit rather than relying on it implicitly.
    """
    audit = repos.audit

    async def _sink(action: str, payload: Mapping[str, Any]) -> None:
        organization_id = payload.get("organization_id")
        schedule_id = str(payload.get("report_schedule_id") or payload.get("correlation_id") or "")
        stored = {
            key: value
            for key, value in payload.items()
            if key not in {"organization_id", "report_schedule_id", "actor", "actor_type"}
        }
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=str(payload.get("correlation_id") or schedule_id),
            entity_type=ENTITY_SCHEDULE,
            entity_id=schedule_id,
            action=action,
            actor=str(payload.get("actor") or ACTOR_SYSTEM),
            occurred_at=datetime.now(timezone.utc),
            changed_fields=stored,
            reason=f"report schedule {action}",
            actor_type=str(payload.get("actor_type") or ACTOR_SYSTEM),
            origin=ORIGIN_SYSTEM,
            outcome=(OUTCOME_FAILURE if action.endswith("_failed") else OUTCOME_SUCCESS),
            organization_id=str(organization_id) if organization_id else None,
            category=CAT_REPORT,
        )
        await audit.record(entry)

    return _sink


class ReportScheduleService:
    """Canonical create/read/pause/resume/delete for report schedules.

    Args:
        repos: The request repository bundle (``report_schedules`` plus the
            ``audit`` sink; the report/version repositories are used by the
            producer, not here).
        clock: Optional aware-time source, injectable so due-time arithmetic is
            deterministic in tests. Defaults to ``datetime.now(timezone.utc)``.
    """

    def __init__(
        self, repos: Any, *, clock: Optional[Callable[[], datetime]] = None
    ) -> None:
        self._repos = repos
        self._schedules = repos.report_schedules
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    async def list_schedules(
        self,
        organization_id: str,
        *,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """A page of an organisation's schedules plus the total count."""
        items = await self._schedules.list_for_org(
            organization_id, limit=limit, offset=offset, is_active=is_active
        )
        return {
            "schedules": items,
            "total": await self._schedules.count_for_org(organization_id),
            "limit": limit,
            "offset": offset,
            "frequencies": canonical_frequencies(),
        }

    async def get(self, organization_id: str, schedule_id: str) -> Optional[dict]:
        """One schedule **scoped to the caller's organisation**, or ``None``."""
        return await self._schedules.get_for_org(schedule_id, organization_id)

    async def runs(
        self, organization_id: str, schedule_id: str, *, limit: int = 50
    ) -> Optional[list[dict]]:
        """Execution history, or ``None`` when the schedule is not in the org."""
        schedule = await self._schedules.get_for_org(schedule_id, organization_id)
        if schedule is None:
            return None
        return await self._schedules.list_runs(schedule_id, limit=limit)

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    async def create(
        self,
        organization_id: str,
        *,
        actor: str,
        name: object,
        report_type: object,
        reporting_year: object,
        frequency: object,
        run_time: object,
        recipients: Sequence[Any],
        timezone_name: object = "Europe/London",
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        retry_policy: Optional[Mapping[str, Any]] = None,
        is_active: bool = True,
    ) -> dict:
        """Validate and persist one schedule, then audit its creation.

        Validation happens before any write, against the canonical vocabulary the
        database itself enforces, so an invalid frequency (``daily``, say) is
        refused with an explanation instead of reaching a CHECK constraint.
        Raises :class:`ScheduleValidationError` for anything the canonical model
        rejects.
        """
        validated_name = validate_name(name)
        validated_type = validate_report_type(report_type)
        validated_year = validate_reporting_year(reporting_year)
        validated_frequency = validate_frequency(frequency)
        validated_timezone = validate_timezone(timezone_name)
        validated_time = validate_run_time(run_time)
        validated_recipients = normalise_recipients(recipients)
        validated_start, validated_end = validate_period(period_start, period_end)
        policy = resolve_policy(retry_policy)

        now = self._clock()
        next_run_at = next_due_at(
            validated_frequency,
            validated_time,
            validated_timezone,
            now,
        )
        row = await self._schedules.create(
            organization_id=organization_id,
            name=validated_name,
            report_type=validated_type,
            reporting_year=validated_year,
            frequency=validated_frequency,
            run_time=validated_time,
            timezone_name=validated_timezone,
            recipients=validated_recipients,
            next_run_at=next_run_at,
            created_by=actor,
            period_start=validated_start,
            period_end=validated_end,
            retry_policy=policy,
            is_active=is_active,
        )
        await self._audit(
            AUDIT_SCHEDULE_CREATED,
            organization_id=organization_id,
            schedule_id=row["id"],
            actor=actor,
            after={
                "name": validated_name,
                "report_type": validated_type,
                "reporting_year": validated_year,
                "frequency": validated_frequency,
                "timezone": validated_timezone,
                "run_time": validated_time.strftime("%H:%M"),
                "recipient_count": len(validated_recipients),
                "next_run_at": next_run_at.isoformat(),
                "is_active": bool(is_active),
            },
        )
        return row

    async def pause(
        self, organization_id: str, schedule_id: str, *, actor: str
    ) -> Optional[dict]:
        """Pause a schedule (``is_active = false`` + ``paused_at``).

        The persisted ``next_run_at`` is preserved: pausing suspends execution
        without destroying the due time the schedule had reached. Returns
        ``None`` when the schedule is not in the caller's organisation.
        """
        schedule = await self._schedules.get_for_org(schedule_id, organization_id)
        if schedule is None:
            return None
        row = await self._schedules.set_active(
            schedule_id,
            is_active=False,
            next_run_at=schedule.get("next_run_at"),
            paused_at=self._clock(),
        )
        if row is not None:
            await self._audit(
                AUDIT_SCHEDULE_PAUSED,
                organization_id=organization_id,
                schedule_id=schedule_id,
                actor=actor,
                changed={"is_active": False},
                before={"is_active": schedule.get("is_active")},
                after={"is_active": False},
            )
        return row

    async def resume(
        self, organization_id: str, schedule_id: str, *, actor: str
    ) -> Optional[dict]:
        """Resume a paused schedule and re-establish a real due time.

        A future ``next_run_at`` is kept as-is (a pause is not a rescheduling). A
        past or absent due time is recomputed to the next occurrence in the
        schedule's own timezone, so resuming an overdue schedule does not fire
        immediately as a catch-up burst — it becomes due at its next real
        period boundary. Returns ``None`` when the schedule is not in the
        caller's organisation.
        """
        schedule = await self._schedules.get_for_org(schedule_id, organization_id)
        if schedule is None:
            return None
        now = self._clock()
        stored_due = schedule.get("next_run_at")
        if stored_due is not None and stored_due > now:
            next_run_at = stored_due
        else:
            next_run_at = next_due_at(
                schedule["frequency"],
                validate_run_time(schedule["run_time"]),
                schedule["timezone"],
                now,
            )
        row = await self._schedules.set_active(
            schedule_id, is_active=True, next_run_at=next_run_at, paused_at=None
        )
        if row is not None:
            await self._audit(
                AUDIT_SCHEDULE_RESUMED,
                organization_id=organization_id,
                schedule_id=schedule_id,
                actor=actor,
                changed={"is_active": True, "next_run_at": next_run_at.isoformat()},
                before={"is_active": False},
                after={"is_active": True},
            )
        return row

    async def delete(
        self, organization_id: str, schedule_id: str, *, actor: str
    ) -> bool:
        """Delete a schedule (audited); ``False`` when it is not in the org.

        A schedule that has **executed** is refused with
        :class:`ScheduleInUseError` rather than producing a raw database error: its
        run history is immutable by design, so the supported action is to pause it.
        """
        schedule = await self._schedules.get_for_org(schedule_id, organization_id)
        if schedule is None:
            return False
        if await self._schedules.has_runs(schedule_id):
            raise ScheduleInUseError(
                "this schedule has execution history, which is immutable; pause it "
                "instead of deleting it",
                field="schedule_id",
            )
        deleted = await self._schedules.delete(schedule_id)
        if deleted:
            await self._audit(
                AUDIT_SCHEDULE_DELETED,
                organization_id=organization_id,
                schedule_id=schedule_id,
                actor=actor,
                before={
                    "name": schedule.get("name"),
                    "frequency": schedule.get("frequency"),
                    "is_active": schedule.get("is_active"),
                },
            )
        return deleted

    # ------------------------------------------------------------------
    # Auditing
    # ------------------------------------------------------------------
    async def _audit(
        self,
        action: str,
        *,
        organization_id: str,
        schedule_id: str,
        actor: str,
        changed: Optional[Mapping[str, Any]] = None,
        before: Optional[Mapping[str, Any]] = None,
        after: Optional[Mapping[str, Any]] = None,
        outcome: str = OUTCOME_SUCCESS,
    ) -> None:
        """Append one schedule lifecycle event to the canonical audit trail.

        ``correlation_id = schedule id`` (the PD-2 migration's requirement), the
        actor is the real person who acted, and only field names/states are
        stored. Best-effort: an audit failure is logged and never breaks the
        already-persisted change.
        """
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=schedule_id,
            entity_type=ENTITY_SCHEDULE,
            entity_id=schedule_id,
            action=action,
            actor=actor,
            occurred_at=self._clock(),
            changed_fields=dict(changed or {}),
            reason=f"report schedule {action}",
            before=dict(before) if before else None,
            after=dict(after) if after else None,
            actor_type=ACTOR_ORG_USER,
            origin=ORIGIN_HUMAN,
            outcome=outcome,
            organization_id=organization_id,
            # The actor is a member of the organisation they acted on, so the
            # dedicated column and the metadata mirror both carry it (the
            # established P17-IMPLEMENT-02 pattern for this ledger).
            actor_organization_id=organization_id,
            category=CAT_REPORT,
        )
        try:
            await self._repos.audit.record(entry)
        except Exception:  # noqa: BLE001 — audit must never break the operation
            logger.exception(
                "report schedule audit (%s) failed for %s", action, schedule_id
            )
