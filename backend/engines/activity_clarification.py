"""041 — first-class ACTIVITY CLARIFICATION (source evidence vs user adjudication).

CarbonTally must not guess when the extracted activity evidence is insufficient to
determine the semantic activity/factor family (PO decision, F-039-1). This module is
the clarification layer that sits *around* the existing selection boundary:

    extracted activity ──► retrieval candidates ──► select_factor()
                                                       │
                        sufficient ────────────────────┤
                        clarification_required ────────┘
                                 │
                        user supplies SEMANTIC clarification
                                 │
                    policy_input = original activity + clarification
                                 │
                        select_factor() AGAIN (never a factor-ID bypass)

It is deliberately storage-agnostic: it produces the clarification record and the
re-run outcome. Persistence (the authorized table), RLS, HTTP endpoints and the D19 UI
are the follow-up specified in the 041 report; nothing here writes to a database and
nothing here selects a factor by identifier.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from engines.factor_selection_policy import (
    activity_of,
    family_of,
    request_tokens,
    select_factor,
    treatment_route,
)

GENERIC_ACTIVITY_TOKENS = frozenset(
    {"waste", "fuel", "fuels", "energy", "gas", "oil", "oils", "electricity", "power",
     "material", "materials", "transport", "travel", "heat", "steam"}
)
_ROUTE_LABELS = {
    "landfill": "Landfill", "recycl": "Recycling", "closed-loop": "Closed-loop recycling",
    "closed loop": "Closed-loop recycling", "open-loop": "Open-loop recycling",
    "open loop": "Open-loop recycling", "compost": "Composting", "incinerat": "Incineration",
    "energy recovery": "Incineration with energy recovery", "anaerob": "Anaerobic digestion",
    "digest": "Anaerobic digestion",
}
_FAMILY_LABELS = {
    "waste disposal": "Waste treatment / disposal", "material use": "Material use",
    "fuels": "Fuel combustion", "bioenergy": "Biofuel", "water supply": "Water supply",
    "wtt- fuels": "Upstream (WTT) fuel",
}
_VARIANT_LABELS = {
    "mineral": "100% mineral", "biofuel blend": "average biofuel blend",
    "development fuel": "development fuel", "biodiesel": "biodiesel", "hvo": "HVO",
    "off-road": "off-road", "bioethanol": "bioethanol",
}
DECLINED = "i_dont_know"
_DECLINE_TERMS = (DECLINED, "i dont know", "i don't know", "unknown", "no idea")


@dataclass(frozen=True)
class ClarificationOption:
    """A semantic choice derived from the REAL eligible candidate groups."""

    id: str  # stable semantic key — never an emission-factor id
    label: str
    semantic_term: str  # fed back into the policy as evidence
    detail: str = ""


@dataclass(frozen=True)
class ActivityEvidence:
    activity: str
    unit: Optional[str] = None
    verdict: str = "sufficient"  # sufficient | clarification_required | insufficient_evidence
    reason: str = ""
    options: tuple = ()
    policy_status: str = ""
    selected_factor_id: Optional[str] = None


@dataclass(frozen=True)
class ClarificationRecord:
    """The adjudication event — kept separate from source document evidence."""

    clarification_id: str
    activity_key: str
    original_activity: str
    clarification: str
    clarification_type: str
    status: str
    outcome_status: str
    policy_input: str
    actor_id: Optional[str] = None
    actor_scope: Optional[str] = None
    created_at: str = ""
    selected_factor_id: Optional[str] = None
    selected_factor_name: Optional[str] = None
    factor_set: Optional[str] = None
    factor_source: Optional[str] = None
    reporting_year: Optional[int] = None
    unit: Optional[str] = None
    scope: Optional[str] = None
    eligible_group_count: int = 0
    notes: tuple = field(default_factory=tuple)


def _now(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat()


def _option(group: tuple) -> ClarificationOption:
    family, route, variant = (list(group) + ["", "", ""])[:3]
    parts = [_FAMILY_LABELS.get(family, (family or "activity").title())]
    if variant:
        parts.append(_VARIANT_LABELS.get(variant, variant))
    if route:
        parts.append(_ROUTE_LABELS.get(route, str(route).title()))
    term = (
        _ROUTE_LABELS.get(route, route) if route
        else _VARIANT_LABELS.get(variant, variant) if variant
        else _FAMILY_LABELS.get(family, family or "activity")
    )
    return ClarificationOption(
        id="|".join(str(p) for p in (family, route, variant)),
        label=" · ".join(p for p in parts if p),
        semantic_term=str(term),
        detail=f"family={family or '-'} route={route or '-'} variant={variant or '-'}",
    )


def _groups_from_candidates(candidates: Sequence[Any]) -> tuple:
    seen: list = []
    for factor in candidates:
        key = (family_of(factor), treatment_route(activity_of(factor)) or "", "")
        if key not in seen:
            seen.append(key)
    return tuple(seen)


def assess_activity_evidence(
    activity: str,
    candidates: Sequence[Any],
    *,
    unit: Optional[str] = None,
    scope: Optional[str] = None,
    preferred_unit: Optional[str] = None,
) -> ActivityEvidence:
    """Decide whether the extracted activity can be resolved deterministically."""
    decision = select_factor(
        candidates, activity=activity, unit=unit, scope=scope, preferred_unit=preferred_unit
    )
    tokens = request_tokens(activity)
    generic = bool(tokens) and tokens <= GENERIC_ACTIVITY_TOKENS

    if decision.status == "selected" and decision.factor is not None:
        return ActivityEvidence(
            activity=activity, unit=unit, verdict="sufficient", reason=decision.reason,
            policy_status=decision.status,
            selected_factor_id=getattr(decision.factor, "id", None),
        )

    groups = decision.groups or _groups_from_candidates(candidates)
    options = tuple(_option(g) for g in groups)
    if decision.status == "ambiguous":
        return ActivityEvidence(
            activity=activity, unit=unit, verdict="clarification_required",
            reason=decision.reason or "multiple materially different candidates",
            options=options, policy_status=decision.status,
        )
    if generic:
        return ActivityEvidence(
            activity=activity, unit=unit, verdict="insufficient_evidence",
            reason=("the extracted activity names only a general category, so the intended "
                    "activity/factor family cannot be established"),
            options=options, policy_status=decision.status,
        )
    if decision.status == "not_applicable":
        # The policy abstains because the request is outside its semantic classes
        # (e.g. water). That is NOT an ambiguity: clarification is not required and
        # the existing behaviour stays in force.
        return ActivityEvidence(
            activity=activity, unit=unit, verdict="not_required",
            reason="outside the factor-selection policy's semantic classes",
            policy_status=decision.status,
        )
    return ActivityEvidence(
        activity=activity, unit=unit, verdict="clarification_required",
        reason=decision.reason or "no eligible candidate for the stated activity",
        options=options, policy_status=decision.status,
    )


def resolve_clarification(
    activity: str,
    clarification: str,
    candidates: Sequence[Any],
    *,
    unit: Optional[str] = None,
    scope: Optional[str] = None,
    preferred_unit: Optional[str] = None,
    activity_key: str = "",
    actor_id: Optional[str] = None,
    actor_scope: Optional[str] = None,
    now: Optional[datetime] = None,
) -> tuple:
    """Re-run the EXISTING policy with the clarification added as evidence.

    Returns ``(record, factor_or_None)``. The original activity is never mutated and
    the clarification is never treated as a factor choice: only the combined text
    enters ``select_factor``.
    """
    text = clarification.strip()
    term = "" if text.casefold() in _DECLINE_TERMS else text
    policy_input = " ".join(p for p in (activity.strip(), term) if p).strip()
    decision = select_factor(
        candidates, activity=policy_input, unit=unit, scope=scope, preferred_unit=preferred_unit
    )
    factor = decision.factor if decision.status == "selected" else None
    record = ClarificationRecord(
        clarification_id=str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"{activity_key}::{activity}::{clarification}")
        ),
        activity_key=activity_key,
        original_activity=activity,
        clarification=clarification,
        clarification_type="semantic_activity",
        status="clarification_supplied",
        outcome_status=decision.status,
        policy_input=policy_input,
        actor_id=actor_id,
        actor_scope=actor_scope,
        created_at=_now(now),
        selected_factor_id=getattr(factor, "id", None),
        selected_factor_name=(str(getattr(factor, "activity_type", "")) or None) if factor else None,
        factor_set=getattr(factor, "factor_set", None),
        factor_source=getattr(factor, "factor_source", None),
        reporting_year=getattr(factor, "reporting_year", None),
        unit=getattr(factor, "unit", None),
        scope=getattr(factor, "scope", None),
        eligible_group_count=len(decision.eligible),
        notes=tuple(decision.groups) if decision.status == "ambiguous" else (),
    )
    return record, factor


def decline_clarification(
    activity: str,
    *,
    activity_key: str = "",
    actor_id: Optional[str] = None,
    actor_scope: Optional[str] = None,
    now: Optional[datetime] = None,
) -> ClarificationRecord:
    """The safe unresolved path — no factor is chosen and nothing is calculated."""
    return ClarificationRecord(
        clarification_id=str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"{activity_key}::{activity}::{DECLINED}")
        ),
        activity_key=activity_key,
        original_activity=activity,
        clarification=DECLINED,
        clarification_type="declined",
        status="declined",
        outcome_status="unresolved_declined",
        policy_input=activity.strip(),
        actor_id=actor_id,
        actor_scope=actor_scope,
        created_at=_now(now),
    )
