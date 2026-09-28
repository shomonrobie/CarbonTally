"""Canonical scheduled-report producer (CT-IMPLEMENT-03 / PD-2).

The runner's ``ReportProducer`` for real deployment: it turns one due schedule
slot into a **canonical report** — a ``report_generation_queue`` row completed by
``engines.report_generation.ReportGenerationEngine`` plus a ``report_versions``
snapshot — instead of a spinner or a claim.

It adds no reporting logic of its own. The generation sequence is exactly the one
the V3 reporting surface already uses
(``api.v3_reports.generate_report``): create the queue row (QUEUED), mark it
GENERATING, run the authoritative engine with that row id, then record the
version snapshot. That is deliberate: a scheduled report and a user-requested
report must be the same artefact, produced by the same engine, so a schedule can
never bypass validation, provenance or the version lifecycle.

Outcome discipline (the runner's contract):

* a produced ``ProducedReport`` must name the canonical ``report_id`` — the
  runner records a produced-in-nothing run as a *failure*, never a success;
* an engine failure is re-raised so the runner records ``failed`` with a real
  error code and applies the retry policy;
* this producer never returns ``None``. A "skip" is a product decision (which
  conditions make a scheduled report not worth producing) and none is ratified,
  so nothing is silently skipped.  ← see CT-IMPLEMENT-03 report §PO gates.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from core.logging import get_logger
from domain.report import ReportRequest
from domain.report_schedule import ProducedReport, ScheduleDefinition

logger = get_logger(__name__)


class CanonicalReportProducer:
    """Produces the canonical report/version for one due schedule slot.

    Args:
        repos: The repository bundle (``reports`` + ``report_versions``).
        engine: The authoritative ``ReportGenerationEngine``.
        clock: Optional aware-time source (injectable for tests).
    """

    def __init__(self, repos: Any, engine: Any) -> None:
        if repos is None or engine is None:
            raise ValueError("CanonicalReportProducer requires repos and engine")
        self._repos = repos
        self._engine = engine

    async def __call__(
        self, schedule: ScheduleDefinition, *, scheduled_for: datetime
    ) -> Optional[ProducedReport]:
        """Generate the report for ``schedule``'s due slot.

        Commits to a report for the schedule's configured ``reporting_year`` and
        period; the slot time is recorded on the run row by the runner, and is
        carried into the version's change summary so the produced artefact says
        which slot produced it.
        """
        report_type = schedule.report_type
        options: dict[str, Any] = {
            "scheduled": True,
            "schedule_id": schedule.id,
            "scheduled_for": scheduled_for.isoformat(),
        }
        if schedule.period_start is not None:
            options["period_start"] = schedule.period_start.isoformat()
        if schedule.period_end is not None:
            options["period_end"] = schedule.period_end.isoformat()

        request_row = await self._repos.reports.create_generation_request(
            schedule.organization_id,
            report_type,
            schedule.reporting_year,
            None,
            created_by=None,
            report_name=(
                f"{schedule.name or 'Scheduled report'} "
                f"({report_type} {schedule.reporting_year})"
            ),
        )
        request = ReportRequest(
            organization_id=schedule.organization_id,
            report_type=report_type,
            reporting_year=schedule.reporting_year,
            template_id=None,
            options=options,
        )

        try:
            await self._repos.reports.mark_generating(request_row.id)
            result = await self._engine.generate(request, report_id=request_row.id)
        except Exception as exc:  # noqa: BLE001 — persist the real failure, re-raise
            # The queue row must not be left claiming to be generating while the
            # run row says failed: the persisted state has to agree.
            try:
                await self._repos.reports.mark_failed(
                    request_row.id, error_log=str(exc), user_id=None
                )
            except Exception:  # noqa: BLE001 — never mask the original failure
                logger.exception(
                    "scheduled report %s: could not mark queue row %s failed",
                    schedule.id,
                    request_row.id,
                )
            raise

        content = result.content.to_dict()
        version = await self._repos.report_versions.create(
            report_id=result.report.id,
            version_number=await self._repos.report_versions.next_version_number(
                result.report.id
            ),
            content=content,
            file_url=result.report.storage_url,
            file_name=f"report-{result.report.id}.json",
            created_by=None,
            change_summary=(
                f"Scheduled {report_type} report for {schedule.reporting_year} "
                f"(schedule {schedule.id}, due slot {scheduled_for.isoformat()})"
            ),
            is_current=True,
        )
        return ProducedReport(
            report_id=str(result.report.id),
            report_version_id=str(version["id"]),
            result_summary={
                "report_type": report_type,
                "reporting_year": schedule.reporting_year,
                "version_number": version["version_number"],
                "page_count": int((content or {}).get("page_count") or 0),
            },
        )
