"""Canonical scheduled-reporting repository (CT-IMPLEMENT-03 / PD-2).

Persistence for the CT-SCHEMA-02/CT-IMPLEMENT-02 canonical schedule tables —
``report_schedule_definitions`` and ``report_schedule_runs``. It is **not** the
retired ``report_schedules`` table and must never be pointed at one: PD-2
forbids recreating the legacy name, and ``services.report_schedule_runner``
executes only against these tables.

The repository is also the canonical ``ScheduleStore`` implementation. That is
deliberate: the runner's persistence contract is exactly this module's
read/claim/finish/record quartet, and the schema's own constraints supply the
guarantees the runner documents —

* ``UNIQUE (schedule_id, scheduled_for)`` → ``open_run`` returns ``None`` for an
  already-executed due slot (the idempotency proof, not a Python-side guess);
* ``BEFORE UPDATE/DELETE`` guard → ``finish_run`` can only move a ``running``
  run to its terminal state, once;
* ``is_active OR paused_at IS NOT NULL`` → pausing always stamps ``paused_at``.

Due selection reads the persisted ``next_run_at`` (never in-memory state), so a
restart resumes from the database. No business rule lives here: frequency
vocabulary, retry arithmetic and next-occurrence maths stay in
``domain.report_schedule``.
"""
from __future__ import annotations

from datetime import datetime, time
from typing import Any, Mapping, Optional, Sequence

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb

#: Every column of ``report_schedule_definitions`` this application uses.
_DEFINITION_COLUMNS = """
    id, organization_id, name, report_type, reporting_year, period_start,
    period_end, recipients, frequency, run_time, timezone, is_active, paused_at,
    created_by, created_at, updated_at, next_run_at, last_run_at, last_result,
    last_error, failure_count, retry_policy
"""

#: Every column of ``report_schedule_runs`` this application uses.
_RUN_COLUMNS = """
    id, schedule_id, organization_id, scheduled_for, attempt, status,
    started_at, finished_at, report_id, report_version_id, result_summary,
    error_code, error_message
"""

#: Statuses a run may be *moved to* by :meth:`ReportSchedulesRepository.finish_run`.
_TERMINAL_RUN_STATUSES = ("succeeded", "failed", "skipped")


def _as_time(value: Any) -> Optional[time]:
    """Coerce a ``time`` column (``datetime.time`` or ``'HH:MM:SS'``) to ``time``."""
    if value is None:
        return None
    if isinstance(value, time):
        return value
    parts = (str(value).split(":") + ["0", "0"])[:3]
    return time(int(parts[0]), int(parts[1]))


def _row_to_definition(row: Any) -> dict:
    """Map one definition row to the canonical dict form.

    JSONB is decoded (``recipients`` as a list, ``retry_policy`` as an object)
    and datetimes are left as ``datetime`` objects, because this is the shape
    ``domain.report_schedule.ScheduleDefinition.from_row`` consumes. The API
    layer (``api.v3_reports``) owns JSON shaping — no presentation logic here.
    """
    r = dict(row)
    return {
        "id": str(r["id"]),
        "organization_id": str(r["organization_id"]),
        "name": str(r["name"]),
        "report_type": str(r["report_type"]),
        "reporting_year": int(r["reporting_year"]),
        "period_start": r.get("period_start"),
        "period_end": r.get("period_end"),
        "recipients": loads_jsonb(r.get("recipients")) or [],
        "frequency": str(r["frequency"]),
        "run_time": _as_time(r.get("run_time")),
        "timezone": str(r["timezone"]),
        "is_active": bool(r.get("is_active", True)),
        "paused_at": r.get("paused_at"),
        "created_by": str(r["created_by"]) if r.get("created_by") else None,
        "created_at": r.get("created_at"),
        "updated_at": r.get("updated_at"),
        "next_run_at": r.get("next_run_at"),
        "last_run_at": r.get("last_run_at"),
        "last_result": r.get("last_result"),
        "last_error": r.get("last_error"),
        "failure_count": int(r.get("failure_count") or 0),
        "retry_policy": loads_jsonb(r.get("retry_policy")) or {},
    }


def _row_to_run(row: Any) -> dict:
    """Map one run row to its canonical dict form (JSONB decoded)."""
    r = dict(row)
    return {
        "id": str(r["id"]),
        "schedule_id": str(r["schedule_id"]),
        "organization_id": str(r["organization_id"]),
        "scheduled_for": r.get("scheduled_for"),
        "attempt": int(r["attempt"]),
        "status": str(r["status"]),
        "started_at": r.get("started_at"),
        "finished_at": r.get("finished_at"),
        "report_id": str(r["report_id"]) if r.get("report_id") else None,
        "report_version_id": (
            str(r["report_version_id"]) if r.get("report_version_id") else None
        ),
        "result_summary": loads_jsonb(r.get("result_summary")),
        "error_code": r.get("error_code"),
        "error_message": r.get("error_message"),
    }


class ReportSchedulesRepository(AbstractRepository[dict]):
    """Persistence for the canonical schedule definition/run tables.

    Implements the runner's ``ScheduleStore`` protocol structurally
    (``due_schedules`` / ``open_run`` / ``finish_run`` / ``record_outcome``).
    """

    # ------------------------------------------------------------------
    # Definitions
    # ------------------------------------------------------------------
    async def create(
        self,
        *,
        organization_id: str,
        name: str,
        report_type: str,
        reporting_year: int,
        frequency: str,
        run_time: time,
        timezone_name: str,
        recipients: Sequence[Any],
        next_run_at: datetime,
        created_by: str,
        period_start: Any = None,
        period_end: Any = None,
        retry_policy: Optional[Mapping[str, Any]] = None,
        is_active: bool = True,
    ) -> dict:
        """Insert one schedule definition and return the stored row.

        ``next_run_at`` is required for an active schedule — the schema's
        ``ct02_report_schedule_validate`` trigger refuses an active schedule
        without a due time, because such a schedule could never become due.
        """
        row = await self._fetch_one(
            f"""
            INSERT INTO public.report_schedule_definitions (
                organization_id, name, report_type, reporting_year,
                period_start, period_end, recipients, frequency, run_time,
                timezone, is_active, created_by, next_run_at, retry_policy
            ) VALUES (
                $1::uuid, $2, $3, $4,
                $5::date, $6::date, $7::jsonb, $8, $9,
                $10, $11, $12::uuid, $13,
                COALESCE($14::jsonb,
                         '{{"max_attempts": 3, "backoff_minutes": [5, 30, 120]}}'::jsonb)
            )
            RETURNING {_DEFINITION_COLUMNS}
            """,
            organization_id,
            name,
            report_type,
            int(reporting_year),
            period_start,
            period_end,
            dumps_jsonb(list(recipients)),
            frequency,
            run_time,
            timezone_name,
            bool(is_active),
            created_by,
            next_run_at,
            dumps_jsonb(dict(retry_policy)) if retry_policy is not None else None,
        )
        if row is None:
            raise RuntimeError("report schedule insert returned no row")
        return _row_to_definition(row)

    async def get(self, id: str) -> Optional[dict]:
        """Return one schedule definition, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_DEFINITION_COLUMNS} FROM public.report_schedule_definitions "
            "WHERE id = $1::uuid",
            id,
        )
        return _row_to_definition(row) if row is not None else None

    async def get_for_org(self, id: str, organization_id: str) -> Optional[dict]:
        """Return one schedule definition **scoped to its organisation**.

        Tenant isolation is part of the read itself, so a schedule id from
        another organisation resolves to ``None`` rather than to a row the caller
        must then be trusted to filter.
        """
        row = await self._fetch_one(
            f"SELECT {_DEFINITION_COLUMNS} FROM public.report_schedule_definitions "
            "WHERE id = $1::uuid AND organization_id = $2::uuid",
            id,
            organization_id,
        )
        return _row_to_definition(row) if row is not None else None

    async def list_for_org(
        self,
        organization_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = None,
    ) -> list[dict]:
        """List an organisation's schedules, newest first."""
        args: list[Any] = [organization_id]
        where = "organization_id = $1::uuid"
        if is_active is not None:
            args.append(bool(is_active))
            where += f" AND is_active = ${len(args)}"
        args.append(int(limit))
        limit_placeholder = f"${len(args)}"
        args.append(int(offset))
        offset_placeholder = f"${len(args)}"
        rows = await self._fetch_all(
            f"""
            SELECT {_DEFINITION_COLUMNS} FROM public.report_schedule_definitions
            WHERE {where}
            ORDER BY created_at DESC, id
            LIMIT {limit_placeholder} OFFSET {offset_placeholder}
            """,
            *args,
        )
        return [_row_to_definition(r) for r in rows]

    async def count_for_org(self, organization_id: str) -> int:
        """Number of schedules belonging to an organisation."""
        row = await self._fetch_one(
            "SELECT COUNT(*)::int AS n FROM public.report_schedule_definitions "
            "WHERE organization_id = $1::uuid",
            organization_id,
        )
        return int(row["n"]) if row is not None else 0

    async def set_active(
        self,
        id: str,
        *,
        is_active: bool,
        next_run_at: Optional[datetime],
        paused_at: Optional[datetime],
    ) -> Optional[dict]:
        """Pause (``is_active=False`` + ``paused_at``) or resume a schedule.

        Resuming clears ``paused_at`` and re-stamps ``next_run_at`` from the
        supplied domain-computed due time, so the schema's
        ``is_active OR paused_at IS NOT NULL`` invariant holds in both
        directions. Returns ``None`` when the schedule does not exist.
        """
        row = await self._fetch_one(
            f"""
            UPDATE public.report_schedule_definitions
               SET is_active = $2,
                   next_run_at = $3,
                   paused_at = $4,
                   updated_at = NOW()
             WHERE id = $1::uuid
            RETURNING {_DEFINITION_COLUMNS}
            """,
            id,
            bool(is_active),
            next_run_at,
            paused_at,
        )
        return _row_to_definition(row) if row is not None else None

    async def delete(self, id: str) -> bool:
        """Delete one schedule definition; ``True`` when a row was removed.

        ``report_schedule_runs`` rows cascade with the definition (the schema
        declares ``ON DELETE CASCADE``). The delete is audited by the caller —
        PD-2 requires create/change/deletion auditing.
        """
        status = await self._execute(
            "DELETE FROM public.report_schedule_definitions WHERE id = $1::uuid", id
        )
        return status.upper().startswith("DELETE 1")

    # ------------------------------------------------------------------
    # ScheduleStore — the runner's persistence contract
    # ------------------------------------------------------------------
    async def due_schedules(
        self, now: datetime, limit: int
    ) -> Sequence[Mapping[str, Any]]:
        """Schedules whose persisted ``next_run_at`` has arrived.

        Ordered by due time so an overdue backlog is worked oldest-first, and
        bounded by ``limit`` so one tick can never become unbounded work.
        """
        rows = await self._fetch_all(
            f"""
            SELECT {_DEFINITION_COLUMNS} FROM public.report_schedule_definitions
             WHERE is_active
               AND next_run_at IS NOT NULL
               AND next_run_at <= $1
             ORDER BY next_run_at, id
             LIMIT $2
            """,
            now,
            int(limit),
        )
        return [_row_to_definition(r) for r in rows]

    async def open_run(
        self,
        schedule: Any,
        *,
        scheduled_for: datetime,
        attempt: int,
    ) -> Optional[str]:
        """Claim a due slot by inserting the run row, or return ``None``.

        ``ON CONFLICT (schedule_id, scheduled_for) DO NOTHING`` is the idempotency
        mechanism itself: the table's UNIQUE constraint decides whether this due
        slot has already been executed, so a repeated (or concurrent) tick for the
        same slot can never create a second run or a duplicate report.
        """
        row = await self._fetch_one(
            """
            INSERT INTO public.report_schedule_runs (
                schedule_id, organization_id, scheduled_for, attempt, status
            ) VALUES ($1::uuid, $2::uuid, $3, $4, 'running')
            ON CONFLICT (schedule_id, scheduled_for) DO NOTHING
            RETURNING id
            """,
            schedule.id,
            schedule.organization_id,
            scheduled_for,
            int(attempt),
        )
        return str(row["id"]) if row is not None else None

    async def finish_run(
        self,
        run_id: str,
        *,
        status: str,
        report_id: Optional[str] = None,
        report_version_id: Optional[str] = None,
        result_summary: Optional[Mapping[str, Any]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Move a ``running`` run to its terminal state, exactly once.

        The ``status = 'running'`` predicate plus the schema's run guard mean a
        second call (or a call on an already-terminal run) changes nothing and
        raises nothing: run history is append-only.
        """
        if status not in _TERMINAL_RUN_STATUSES:
            raise ValueError(
                f"finish_run accepts a terminal status only, got {status!r}"
            )
        await self._execute(
            """
            UPDATE public.report_schedule_runs
               SET status = $2,
                   finished_at = NOW(),
                   report_id = $3::uuid,
                   report_version_id = $4::uuid,
                   result_summary = $5::jsonb,
                   error_code = $6,
                   error_message = $7
             WHERE id = $1::uuid AND status = 'running'
            """,
            run_id,
            status,
            report_id,
            report_version_id,
            dumps_jsonb(dict(result_summary)) if result_summary else None,
            error_code,
            error_message,
        )

    async def record_outcome(
        self,
        schedule: Any,
        *,
        next_run_at: datetime,
        last_result: str,
        failure_count: int,
        is_active: bool,
        last_error: Optional[str] = None,
        paused_at: Optional[datetime] = None,
    ) -> None:
        """Persist the schedule's own execution/retry state.

        ``paused_at`` is written verbatim, so pausing stamps it and every other
        outcome clears it — the schema's ``is_active OR paused_at IS NOT NULL``
        CHECK depends on that.
        """
        await self._execute(
            """
            UPDATE public.report_schedule_definitions
               SET next_run_at = $2,
                   last_result = $3,
                   failure_count = $4,
                   is_active = $5,
                   last_error = $6,
                   paused_at = $7,
                   updated_at = NOW()
             WHERE id = $1::uuid
            """,
            schedule.id,
            next_run_at,
            last_result,
            int(failure_count),
            bool(is_active),
            last_error,
            paused_at,
        )

    # ------------------------------------------------------------------
    # Runs
    # ------------------------------------------------------------------
    async def list_runs(self, schedule_id: str, *, limit: int = 50) -> list[dict]:
        """Execution history for one schedule, newest due slot first."""
        rows = await self._fetch_all(
            f"""
            SELECT {_RUN_COLUMNS} FROM public.report_schedule_runs
             WHERE schedule_id = $1::uuid
             ORDER BY scheduled_for DESC, id
             LIMIT $2
            """,
            schedule_id,
            int(limit),
        )
        return [_row_to_run(r) for r in rows]

    async def get_run(self, run_id: str) -> Optional[dict]:
        """Return one run row, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_RUN_COLUMNS} FROM public.report_schedule_runs "
            "WHERE id = $1::uuid",
            run_id,
        )
        return _row_to_run(row) if row is not None else None

    async def has_runs(self, schedule_id: str) -> bool:
        """Whether a schedule has any execution history.

        The schema makes run history append-only (``ct02_report_schedule_run_guard``
        refuses DELETE for every role), while ``report_schedule_definitions``
        cascades on delete. A schedule that has run therefore **cannot** be
        deleted without breaching the guard, so callers must ask this first
        rather than discovering it as a raw database error.
        """
        row = await self._fetch_one(
            "SELECT EXISTS (SELECT 1 FROM public.report_schedule_runs"
            " WHERE schedule_id = $1::uuid) AS present",
            schedule_id,
        )
        return bool(row["present"]) if row is not None else False

    # ------------------------------------------------------------------
    # AbstractRepository contract
    # ------------------------------------------------------------------
    async def save(self, entity: dict) -> dict:
        """Unused: schedules are written through the explicit methods above."""
        raise NotImplementedError(
            "use ReportSchedulesRepository.create/set_active for schedule writes"
        )
