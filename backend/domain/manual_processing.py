"""FIN-06 — Manual Processing governance (domain policy).

The PO decision: **Manual Processing is OFF by default** and only CarbonTally
Admin may enable it, with the scope vocabulary

    organization | consultant_firm | consultant_client

and the precedence **most-specific-wins**:

    consultant_client  >  consultant_firm  >  organization  >  platform default

Absence of an explicit governance row for the most specific applicable scope
means the request is **denied** (fail closed). A more specific ``enabled=False``
row therefore overrides a broader ``enabled=True`` row, and vice versa a specific
``True`` enables work inside an otherwise-off scope.

This module is deliberately pure: it contains no database access and no HTTP
concerns, so the precedence model is unit-testable in isolation. The repository
(``data.manual_processing``) supplies the rows; the API layer supplies the
CarbonTally-Admin authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

#: Ratified scope vocabulary (mirrors the migration CHECK constraint).
SCOPE_ORGANIZATION = "organization"
SCOPE_CONSULTANT_FIRM = "consultant_firm"
SCOPE_CONSULTANT_CLIENT = "consultant_client"

SCOPE_TYPES: tuple[str, ...] = (
    SCOPE_ORGANIZATION,
    SCOPE_CONSULTANT_FIRM,
    SCOPE_CONSULTANT_CLIENT,
)

#: Most-specific first — the FIRST matching scope with an explicit row wins.
SCOPE_PRECEDENCE: tuple[str, ...] = (
    SCOPE_CONSULTANT_CLIENT,
    SCOPE_CONSULTANT_FIRM,
    SCOPE_ORGANIZATION,
)

#: The platform default when no explicit row matches.
DEFAULT_ENABLED = False


@dataclass(frozen=True, slots=True)
class ManualProcessingGrant:
    """One explicit governance row (``manual_processing_grants``)."""

    scope_type: str
    scope_id: str
    enabled: bool
    reason: Optional[str] = None
    set_by: Optional[str] = None
    set_at: Optional[object] = None


@dataclass(frozen=True, slots=True)
class EffectiveManualProcessing:
    """The resolved governance answer for one organisation context."""

    enabled: bool
    #: ``explicit`` (a governance row decided it) or ``default`` (nothing matched).
    source_level: str
    source_scope_type: Optional[str] = None
    source_scope_id: Optional[str] = None
    #: Present because the platform default is fail-closed by decision.
    default_off: bool = True


@dataclass(frozen=True, slots=True)
class OrgContext:
    """The organisations's relationship context used for scope resolution.

    ``consultant_client_id``/``consultant_firm_id`` are populated only when the
    organisation is reached through an ACTIVE consultant-client grant; they are
    never trusted from the client (the API resolves them server-side).
    """

    organization_id: str
    consultant_client_id: Optional[str] = None
    consultant_firm_id: Optional[str] = None


def scope_targets(context: OrgContext) -> dict[str, str]:
    """Return the scope-id candidate for each applicable scope type."""
    targets: dict[str, str] = {}
    if context.consultant_client_id:
        targets[SCOPE_CONSULTANT_CLIENT] = context.consultant_client_id
    if context.consultant_firm_id:
        targets[SCOPE_CONSULTANT_FIRM] = context.consultant_firm_id
    if context.organization_id:
        targets[SCOPE_ORGANIZATION] = context.organization_id
    return targets


def resolve_effective(
    grants: Iterable[ManualProcessingGrant], context: OrgContext
) -> EffectiveManualProcessing:
    """Resolve the effective governance value by most-specific-wins precedence."""
    by_scope: dict[tuple[str, str], ManualProcessingGrant] = {
        (g.scope_type, g.scope_id): g for g in grants
    }
    targets = scope_targets(context)
    for scope_type in SCOPE_PRECEDENCE:
        scope_id = targets.get(scope_type)
        if not scope_id:
            continue
        grant = by_scope.get((scope_type, scope_id))
        if grant is not None:
            return EffectiveManualProcessing(
                enabled=bool(grant.enabled),
                source_level="explicit",
                source_scope_type=scope_type,
                source_scope_id=scope_id,
            )
    return EffectiveManualProcessing(
        enabled=DEFAULT_ENABLED,
        source_level="default",
        source_scope_type=None,
        source_scope_id=None,
    )


def is_scope_type_valid(scope_type: str) -> bool:
    return scope_type in SCOPE_TYPES
