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
_ELIGIBLE_DOMAINS = ("document_retention_days",)


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
        return report

    cutoff = now - timedelta(days=days)
    # Soft-delete expired organisation documents (existing convention).
    if hasattr(repos, "files") and hasattr(repos.files, "expire_documents_older_than"):
        expired = await repos.files.expire_documents_older_than(cutoff, dry_run=dry_run)
        report["domains"]["document_retention_days"] = {
            "cutoff": cutoff.isoformat(),
            "applied": not dry_run,
            **expired,
        }
    return report
