"""F-039-1 — activity-clarification API (F-048-2 / 052).

The HTTP half of authorised activity clarification. The user expresses **meaning**
("Landfill", "Waste oils", "Mineral diesel", …); the server re-enters the existing
factor-selection policy and whatever it returns is what gets recorded.

Reused, not reinvented:

* authentication — ``auth.get_current_user`` (the existing AuthUser dependency);
* authorisation — ``api.dependencies.ensure_processing_org_access``, the existing
  org-scoped processing gate: CarbonTally internal staff pass, Processing Entity
  staff are denied, organisation members pass for **their own** organisation only,
  and a consultant passes only with an ACTIVE client grant. Request bodies cannot
  change that outcome;
* factor selection — ``engines.activity_clarification`` (which calls the frozen
  ``factor_selection_policy.select_factor``). No selection logic lives here;
* persistence — ``data.activity_clarifications.ActivityClarificationsRepository``.

Two safety properties are structural rather than advisory:

* the request models are ``extra="forbid"``, so a body carrying
  ``selected_factor_id`` / ``factor_set`` / ``factor_source`` / ``reporting_year`` /
  ``outcome_status`` / ``actor_id`` is **rejected** (422) instead of being silently
  accepted as authoritative;
* the submitted clarification is validated against the engine's **own** eligible
  semantic options, so a client cannot name an arbitrary activity to steer the
  policy, and the response never offers a factor id as the user's choice.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from api.dependencies import (
    RepositoryBundle,
    ensure_processing_org_access,
    get_matching_engine,
    get_repositories,
)
from auth import AuthUser, get_current_user
from domain.matching import MatchRequest
from engines.activity_clarification import assess_family_conflict
from engines.factor_matching import FactorMatchingEngine

router = APIRouter(
    prefix="/api/v3/activity-clarifications",
    tags=["V3 — Activity Clarification"],
)


# ===========================================================================
# Schemas — the client may supply *meaning* only (Part C)
# ===========================================================================


class ClarificationOptionOut(BaseModel):
    """One semantic choice. ``id`` is a semantic key, never an emission-factor id."""

    id: str
    label: str
    semantic_term: str
    detail: str = ""


class ClarificationStateOut(BaseModel):
    """Whether clarification is required for an activity context, and why."""

    activity: str
    verdict: str
    reason: str = ""
    policy_status: str = ""
    clarification_required: bool
    options: list[ClarificationOptionOut] = Field(default_factory=list)


class ClarificationSubmitIn(BaseModel):
    """A semantic clarification. Factor metadata is rejected outright."""

    model_config = ConfigDict(extra="forbid")

    organization_id: str
    activity: str
    clarification: str
    activity_key: str = ""
    #: Policy INPUTS (scoping evidence already visible to the user), never the answer.
    unit: Optional[str] = None
    scope: Optional[str] = None
    country: str = "GB"
    reporting_year: Optional[int] = None


class ClarificationDeclineIn(BaseModel):
    """The explicit "I don't know" path."""

    model_config = ConfigDict(extra="forbid")

    organization_id: str
    activity: str
    activity_key: str = ""


class ClarificationResultOut(BaseModel):
    """Server-generated adjudication state — including the policy's own result."""

    activity_key: str
    original_activity: str
    clarification: str
    clarification_type: str
    policy_input: str
    outcome_status: str
    resolved: bool
    selected_factor_id: Optional[str] = None
    selected_factor_name: Optional[str] = None
    factor_set: Optional[str] = None
    factor_source: Optional[str] = None
    reporting_year: Optional[int] = None
    unit: Optional[str] = None
    scope: Optional[str] = None
    eligible_group_count: int = 0
    actor_id: Optional[str] = None
    actor_scope: Optional[str] = None
    created_at: str = ""


# ===========================================================================
# Internal helpers
# ===========================================================================

#: Verdicts for which a clarification submission is meaningful. The
#: deterministic and no-candidate outcomes are NOT adjudication requests, so a
#: submission against them is refused instead of forcing a row.
_SUBMITTABLE_VERDICTS = frozenset({"clarification_required", "policy_ambiguous"})


def _actor_scope(current_user: AuthUser) -> str:
    """Server-derived actor scope — never taken from the request body."""
    if current_user.is_internal_staff:
        return "internal_staff"
    if current_user.is_entity_staff:
        return "processing_entity"
    if current_user.is_org_member:
        return "organization_member"
    return "consultant"


async def _candidates(
    matching_engine: FactorMatchingEngine,
    *,
    organization_id: str,
    activity: str,
    unit: Optional[str],
    scope: Optional[str],
    country: str,
    reporting_year: Optional[int],
) -> list:
    """The REAL eligible candidates — from the existing matching engine accessor."""
    request = MatchRequest(
        id=f"clarification:{organization_id}",
        activity=activity,
        country=country or "GB",
        reporting_year=int(reporting_year or datetime.now(timezone.utc).year),
        unit=unit,
        scope=scope,
        organization_id=organization_id,
    )
    return list(matching_engine.clarification_candidates(request))


def _validate_semantic_choice(clarification: str, options: tuple) -> None:
    """Accept only a choice the engine itself offered (no invented semantics)."""
    text = (clarification or "").strip().casefold()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="clarification must not be empty",
        )
    allowed = set()
    for option in options:
        for value in (
            getattr(option, "semantic_term", ""),
            getattr(option, "label", ""),
            getattr(option, "id", ""),
        ):
            if value:
                allowed.add(str(value).strip().casefold())
    if text not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="clarification must be one of the available semantic options",
        )


def _option_out(option) -> ClarificationOptionOut:
    return ClarificationOptionOut(
        id=str(getattr(option, "id", "")),
        label=str(getattr(option, "label", "")),
        semantic_term=str(getattr(option, "semantic_term", "")),
        detail=str(getattr(option, "detail", "") or ""),
    )


def _result_out(outcome: dict) -> ClarificationResultOut:
    """Map the persisted row to the response — factor data is the server's own."""
    record = dict(outcome.get("record") or {})
    selected = record.get("selected_factor_id")
    return ClarificationResultOut(
        activity_key=record.get("activity_key") or "",
        original_activity=record.get("original_activity") or "",
        clarification=record.get("clarification") or "",
        clarification_type=record.get("clarification_type") or "",
        policy_input=record.get("policy_input") or "",
        outcome_status=record.get("outcome_status") or "",
        resolved=bool(selected) and bool(outcome.get("resolved")),
        selected_factor_id=str(selected) if selected else None,
        selected_factor_name=record.get("selected_factor_name"),
        factor_set=record.get("factor_set"),
        factor_source=record.get("factor_source"),
        reporting_year=record.get("reporting_year"),
        unit=record.get("unit"),
        scope=record.get("scope"),
        eligible_group_count=int(record.get("eligible_group_count") or 0),
        actor_id=str(record["actor_id"]) if record.get("actor_id") else None,
        actor_scope=record.get("actor_scope"),
        created_at=str(record.get("created_at") or ""),
    )


# ===========================================================================
# Endpoints
# ===========================================================================


@router.get("/options", response_model=ClarificationStateOut)
async def get_clarification_options(
    organization_id: str = Query(..., description="organisation the activity belongs to"),
    activity: str = Query(..., description="the extracted activity under review"),
    unit: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    country: str = Query("GB"),
    reporting_year: Optional[int] = Query(None),
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
    matching_engine: FactorMatchingEngine = Depends(get_matching_engine),
) -> ClarificationStateOut:
    """Report whether this activity needs clarification, and the semantic choices.

    The organisation is authorised server-side; the verdict comes from the existing
    clarification engine, and the options are the engine's own eligible semantic
    groups. No factor id is ever offered as the user's choice.
    """
    await ensure_processing_org_access(current_user, repos, organization_id)
    candidates = await _candidates(
        matching_engine,
        organization_id=organization_id,
        activity=activity,
        unit=unit,
        scope=scope,
        country=country,
        reporting_year=reporting_year,
    )
    assessment = assess_family_conflict(activity, candidates, unit=unit, scope=scope)
    return ClarificationStateOut(
        activity=activity,
        verdict=assessment.verdict,
        reason=assessment.reason,
        policy_status=assessment.policy_status,
        clarification_required=assessment.verdict == "clarification_required",
        options=[_option_out(option) for option in assessment.options],
    )


@router.post(
    "/clarifications",
    response_model=ClarificationResultOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_clarification(
    payload: ClarificationSubmitIn,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
    matching_engine: FactorMatchingEngine = Depends(get_matching_engine),
) -> ClarificationResultOut:
    """Adjudicate an ambiguous activity from the user's *semantic* statement.

    Flow (Part F): authenticate → authorise the organisation server-side → load the
    real candidates → validate the chosen semantics against the engine's own options
    → re-enter the existing policy → persist the engine's record → return the
    server-generated state. A factor id is never accepted or returned as a choice.
    """
    await ensure_processing_org_access(current_user, repos, payload.organization_id)
    candidates = await _candidates(
        matching_engine,
        organization_id=payload.organization_id,
        activity=payload.activity,
        unit=payload.unit,
        scope=payload.scope,
        country=payload.country,
        reporting_year=payload.reporting_year,
    )
    assessment = assess_family_conflict(
        payload.activity, candidates, unit=payload.unit, scope=payload.scope
    )
    if assessment.verdict not in _SUBMITTABLE_VERDICTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "clarification is not required for this activity "
                f"(verdict: {assessment.verdict})"
            ),
        )
    _validate_semantic_choice(payload.clarification, assessment.options)
    outcome = await repos.clarifications.apply_clarification(
        payload.activity,
        payload.clarification,
        candidates,
        organization_id=payload.organization_id,
        actor_id=current_user.user_id,
        actor_scope=_actor_scope(current_user),
        activity_key=payload.activity_key
        or f"{payload.organization_id}:{payload.activity}",
        unit=payload.unit,
        scope=payload.scope,
    )
    return _result_out(outcome)


@router.post(
    "/decline",
    response_model=ClarificationResultOut,
    status_code=status.HTTP_201_CREATED,
)
async def decline_clarification(
    payload: ClarificationDeclineIn,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> ClarificationResultOut:
    """The explicit "I don't know" path: ``unresolved_declined``, no factor, no guess."""
    await ensure_processing_org_access(current_user, repos, payload.organization_id)
    outcome = await repos.clarifications.apply_decline(
        payload.activity,
        organization_id=payload.organization_id,
        actor_id=current_user.user_id,
        actor_scope=_actor_scope(current_user),
        activity_key=payload.activity_key
        or f"{payload.organization_id}:{payload.activity}",
    )
    return _result_out(outcome)
