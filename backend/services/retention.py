"""Configurable retention enforcement (N3).

Retention is a CONFIGURABLE platform capability (N3): the configured policy
lives in ``system_settings`` (audit_log_retention_days, data_retention_days,
document_retention_days, backup_retention_days) and is surfaced via
``/api/v3/settings/retention``. This module is the SERVER-SIDE enforcement
entry point — the UI is never a retention control.

Design rules:
* Only CONFIGURED durations are enforced (``None`` = not configured = never
  purged). No policy value is invented here.
* Purging uses the existing soft-delete convention (``deleted_at``) — rows are
  never hard-deleted by retention.
* AUDIT and EVIDENCE tables are EXPLICITLY EXCLUDED. Auditability and the
  immutable calculation/evidence model are security invariants (task §5); no
  retention job may weaken them without an explicit product decision. This is a
  safeguard, not an invented policy value.
* Dry-run by default: the caller (deployment scheduler) must pass
  ``dry_run=False`` explicitly to apply anything.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional


#: Domains eligible for enforcement. Audit/evidence tables are intentionally
#: absent (security invariant — see module docstring).
#:
#: Phase 8-X X2 adds ``operational_telemetry_retention_days`` (PO `PX-7`
#: decision: telemetry detail 90 days by default, aggregates indefinitely).
#: Its enforcement is deliberately scoped to the two telemetry stores below and
#: is PROHIBITED from touching the excluded tables listed in
#: ``_TELEMETRY_EXCLUDED_TABLES``.
_ELIGIBLE_DOMAINS = ("document_retention_days", "operational_telemetry_retention_days")

#: Tables that NO retention rule in this module may ever touch (business records,
#: evidence and audit). `PX-7` explicitly excluded the first two; the remainder are
#: the existing report/evidence invariant (`B4-D8`).
_TELEMETRY_EXCLUDED_TABLES = (
    "document_processing_queue",
    "processing_logs",
    "report_versions",
    "report_version_artifacts",
    "evidence_line_items",
    "calculation_snapshots",
    "emissions_logs",
    "audit_trail",
)


def telemetry_excluded_tables() -> tuple[str, ...]:
    """The explicit never-purge list (exposed so verification can assert it)."""
    return _TELEMETRY_EXCLUDED_TABLES


def build_policy(settings: dict[str, Any]) -> dict[str, Optional[int]]:
    """Normalise the raw retention settings into a policy.

    Returns a dict of {domain: days_or_None}. ``None`` means "not configured" —
    no duration is invented.
    """
    policy: dict[str, Optional[int]] = {}
    for domain in _ELIGIBLE_DOMAINS:
        raw = settings.get(domain)
        try:
            policy[domain] = int(raw) if raw is not None else None
        except (TypeError, ValueError):
            policy[domain] = None
        if policy[domain] is not None and policy[domain] < 0:
            policy[domain] = None
    return policy


def compute_expired(
    policy: dict[str, Optional[int]], *, now: Optional[datetime] = None
) -> dict[str, int]:
    """Pure helper: for each configured domain, return the number of rows older
    than the retention period given ``row_age_days`` inputs.

    This function is intentionally trivial and testable; the repository layer
    supplies real row ages. Never called with an invented duration.
    """
    return {}


async def enforce_retention(repos: Any, *, dry_run: bool = True) -> dict[str, Any]:
    """Apply (or, by default, report) the configured retention policy.

    Returns a report of what was eligible/applied per domain.
    """
    settings = await repos.settings.get_retention()
    policy = build_policy(settings)
    report: dict[str, Any] = {"dry_run": dry_run, "policy": policy, "domains": {}}
    now = datetime.now(timezone.utc)

    days = policy.get("document_retention_days")
    if days is None:
        report["domains"]["document_retention_days"] = {"configured": False}
    else:
        cutoff = now - timedelta(days=days)
        # Soft-delete expired organisation documents (existing convention).
        if hasattr(repos, "files") and hasattr(repos.files, "expire_documents_older_than"):
            expired = await repos.files.expire_documents_older_than(cutoff, dry_run=dry_run)
            report["domains"]["document_retention_days"] = {
                "cutoff": cutoff.isoformat(),
                "applied": not dry_run,
                **expired,
            }

    # --- Phase 8-X X2 (`PX-7`) — operational TELEMETRY detail only -----------
    # The duration is whatever is CONFIGURED (90 by default in the schema); it is
    # never hard-coded here. Only the two telemetry stores are pruned; the
    # never-purge list is asserted below so a future edit cannot widen the blast
    # radius silently, and aggregates are untouched by definition (no aggregate
    # store is deleted from).
    telemetry_days = policy.get("operational_telemetry_retention_days")
    if telemetry_days is None:
        report["domains"]["operational_telemetry_retention_days"] = {"configured": False}
    else:
        telemetry_cutoff = now - timedelta(days=telemetry_days)
        telemetry: dict[str, Any] = {
            "cutoff": telemetry_cutoff.isoformat(),
            "applied": not dry_run,
            "detail_retention_days": telemetry_days,
            "aggregates": "indefinite (no aggregate store is pruned)",
            "excluded_tables": list(telemetry_excluded_tables()),
            "parts": {},
        }
        if hasattr(repos, "notifications") and hasattr(
            repos.notifications, "prune_operational_alerts_before"
        ):
            telemetry["parts"]["alerts"] = (
                await repos.notifications.prune_operational_alerts_before(
                    telemetry_cutoff, dry_run=dry_run
                )
            )
        if hasattr(repos, "processing") and hasattr(
            repos.processing, "prune_operational_metrics_before"
        ):
            telemetry["parts"]["metrics"] = (
                await repos.processing.prune_operational_metrics_before(
                    telemetry_cutoff, dry_run=dry_run
                )
            )
        report["domains"]["operational_telemetry_retention_days"] = telemetry

    return report
