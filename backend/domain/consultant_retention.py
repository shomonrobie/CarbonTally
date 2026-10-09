"""CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — consultant relationship retention
policy (OQ-2, now BINDING; PO-10; AGENTS.md §42).

The Product Owner has decided:

    default retention period = 7 YEARS after relationship termination,
    configurable by CarbonTally Admin, with retained read-only access permitted
    while the policy allows and a legal hold overriding normal deletion.

§24 requires ONE authoritative policy source — the period is NOT hard-coded
into scattered business logic. This module is the *resolver*: it turns the
stored ``system_settings`` JSONB into a ``RetentionPolicy`` and DERIVES the
expiry of a retained relationship. It performs no I/O and deletes nothing.

This task deliberately does NOT implement automated deletion (see the migration
note ``auto_delete_enabled: false``): the policy/state model is implemented and
the remaining deletion-execution gap is documented rather than invented.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

#: The authoritative setting key (public.system_settings.setting_key).
RETENTION_SETTING_KEY = "consultant_relationship_retention"

#: The ratified default retention period, in years (OQ-2 / PO decision).
DEFAULT_RETENTION_YEARS = 7


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """The resolved consultant-relationship retention policy."""

    years: int = DEFAULT_RETENTION_YEARS
    retained_read_only: bool = True
    legal_hold_blocks_deletion: bool = True
    auto_delete_enabled: bool = False

    def expires_at(self, ended_at: Optional[datetime]) -> Optional[datetime]:
        """When retained access to a relationship that ended at ``ended_at`` ends.

        Returns ``None`` when there is no ended-at timestamp (nothing to
        expire) — callers must treat that as "no expiry known", never as
        "no retention".
        """
        if ended_at is None:
            return None
        return ended_at + timedelta(days=365 * self.years)

    def is_retained(self, ended_at: Optional[datetime], now: Optional[datetime] = None) -> bool:
        """Whether a relationship that ended at ``ended_at`` is still retained.

        A relationship that ended recently is retained; one whose retention has
        elapsed is NOT (S-EXPIRED, §15.1) unless a legal hold applies — the hold
        check belongs to the caller, which owns the hold state.
        """
        expiry = self.expires_at(ended_at)
        if expiry is None:
            return False
        return (now or datetime.now(timezone.utc)) < expiry


def resolve_retention_policy(setting_value: Optional[Any]) -> RetentionPolicy:
    """Resolve the stored setting JSONB into a policy — FAIL SAFE.

    An absent/malformed setting resolves to the ratified 7-year default (the
    policy the PO decided), never to "no retention" and never to "delete now".
    """
    data = setting_value if isinstance(setting_value, dict) else {}
    raw_years = data.get("years", DEFAULT_RETENTION_YEARS)
    try:
        years = int(raw_years)
    except (TypeError, ValueError):
        years = DEFAULT_RETENTION_YEARS
    if years <= 0:
        years = DEFAULT_RETENTION_YEARS
    return RetentionPolicy(
        years=years,
        retained_read_only=bool(data.get("retained_read_only", True)),
        legal_hold_blocks_deletion=bool(data.get("legal_hold_blocks_deletion", True)),
        auto_delete_enabled=bool(data.get("auto_delete_enabled", False)),
    )
