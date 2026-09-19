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
from engines.activity_clarification import (
    assess_family_conflict,
    decline_clarification as decline_clarification_record,
    resolve_clarification,
)
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
    """A semantic clarification. Factor metadata and evidence values are rejected.

    ``unit``/``scope`` are deliberately absent (F4): the authoritative values come
    from the persisted extraction line, so a client cannot steer selection by
    supplying them — with ``extra="forbid"`` any attempt is a 422.
    """

    model_config = ConfigDict(extra="forbid")

    organization_id: str
    activity: str
    clarification: str
    #: Lookup key for the persisted extraction item; the server re-derives the
    #: organisation, provenance and authoritative unit/scope from it (F2).
    item_id: Optional[str] = None
    activity_key: str = ""
    #: Matching scope only — not the recorded answer (see the docstring above).
    country: str = "GB"
    reporting_year: Optional[int] = None


class ClarificationDeclineIn(BaseModel):
    """The explicit "I don't know" path."""

    model_config = ConfigDict(extra="forbid")

    organization_id: str
    activity: str
    item_id: Optional[str] = None
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


async def _item_evidence(
    repos: RepositoryBundle,
    *,
    organization_id: str,
    item_id: Optional[str],
    activity: str,
) -> dict:
    """Server-derived provenance + authoritative evidence for a persisted item (F2).

    Returns an empty dict when no item is supplied — provenance then stays NULL and no
    unit/scope is invented. Raises 404 for an unknown item, and 403 when the item
    belongs to another organisation: provenance fields can never be used to cross a
    tenant boundary (D-039-1-F).
    """
    if not item_id:
        return {}
    ctx = await repos.clarifications.resolve_evidence(item_id, activity)
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="extraction item not found"
        )
    derived = ctx.get("organization_id")
    if derived and derived != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="extraction item belongs to another organisation",
        )
    return ctx


def _validate_semantic_choice(
    clarification: str,
    options: tuple,
    activity: str = "",
    candidates: Sequence[Any] = (),
    *,
    unit: Optional[str] = None,
    scope: Optional[str] = None,
) -> None:
    """Accept the engine's own offered options, or semantics it can still resolve.

    Two acceptance paths, both server-derived — the request can never name a factor:

    1. the submission matches one of the semantic options the engine offered for
       this activity (``semantic_term`` / ``label`` / ``id``);
    2. otherwise the existing policy is re-run with it, and the submission is
       accepted only when that produces a genuine selection from the server-side
       candidate set (e.g. the engine offers the family-level "Fuel combustion"
       option but also resolves the more specific "Waste oils").

    Anything else — arbitrary text that neither was offered nor resolves through
    the policy — is refused, so a client cannot steer the selection by inventing
    semantics. If an offered option leaves the policy unresolved, that is a
    legitimate "still ambiguous" outcome and is persisted as unresolved.
    """
    text = (clarification or "").strip().casefold()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="clarification must not be empty",
        )
    offered = set()
    for option in options:
        for value in (
            getattr(option, "semantic_term", ""),
            getattr(option, "label", ""),
            getattr(option, "id", ""),
        ):
            if value:
                offered.add(str(value).strip().casefold())
    if text in offered:
        return
    from engines.activity_clarification import resolve_clarification

    _record, factor = resolve_clarification(
        activity, clarification, candidates, unit=unit, scope=scope
    )
    if factor is None:
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
    evidence = await _item_evidence(
        repos,
        organization_id=payload.organization_id,
        item_id=payload.item_id,
        activity=payload.activity,
    )
    # F4: the authoritative unit/scope come from the persisted extraction line (None when
    # no single line matches) — never from the request body.
    unit = evidence.get("unit")
    scope = evidence.get("scope")
    context_key = payload.item_id or payload.activity_key or (
        f"{payload.organization_id}:{payload.activity}"
    )
    candidates = await _candidates(
        matching_engine,
        organization_id=payload.organization_id,
        activity=payload.activity,
        unit=unit,
        scope=scope,
        country=payload.country,
        reporting_year=payload.reporting_year,
    )
    assessment = assess_family_conflict(payload.activity, candidates, unit=unit, scope=scope)
    if assessment.verdict not in _SUBMITTABLE_VERDICTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "clarification is not required for this activity "
                f"(verdict: {assessment.verdict})"
            ),
        )
    _validate_semantic_choice(
        payload.clarification,
        assessment.options,
        payload.activity,
        candidates,
        unit=unit,
        scope=scope,
    )
    record, _factor = resolve_clarification(
        payload.activity,
        payload.clarification,
        candidates,
        unit=unit,
        scope=scope,
        activity_key=context_key,
        actor_id=current_user.user_id,
        actor_scope=_actor_scope(current_user),
    )
    stored = await repos.clarifications.apply_versioned(
        record,
        organization_id=payload.organization_id,
        actor_id=current_user.user_id,
        item_id=evidence.get("item_key"),
        batch_key=evidence.get("batch_key"),
        source_evidence_ref=evidence.get("source_evidence_ref"),
        context_key=context_key,
        evidence_signature=(
            repos.clarifications.evidence_signature(payload.activity, unit, scope)
            if evidence
            else None
        ),
        evidence_context=evidence.get("evidence_context"),
    )
    return _result_out({"record": stored, "resolved": bool(stored.get("selected_factor_id"))})


@router.post(
    "/decline",
    response_model=ClarificationResultOut,
    status_code=status.HTTP_201_CREATED,
)
async def decline_clarification(
    payload: ClarificationDeclineIn,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
    matching_engine: FactorMatchingEngine = Depends(get_matching_engine),
) -> ClarificationResultOut:
    """The explicit "I don't know" path — only where clarification actually applies.

    F3: the SAME assessment the clarification path uses gates the decline. A decline is
    refused (409, no write) when the activity is deterministic/not-required, so a
    meaningless ``unresolved_declined`` cannot be manufactured for it.
    """
    await ensure_processing_org_access(current_user, repos, payload.organization_id)
    evidence = await _item_evidence(
        repos,
        organization_id=payload.organization_id,
        item_id=payload.item_id,
        activity=payload.activity,
    )
    unit = evidence.get("unit")
    scope = evidence.get("scope")
    context_key = payload.item_id or payload.activity_key or (
        f"{payload.organization_id}:{payload.activity}"
    )
    candidates = await _candidates(
        matching_engine,
        organization_id=payload.organization_id,
        activity=payload.activity,
        unit=unit,
        scope=scope,
        country="GB",
        reporting_year=None,
    )
    assessment = assess_family_conflict(payload.activity, candidates, unit=unit, scope=scope)
    if assessment.verdict not in _SUBMITTABLE_VERDICTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "decline is only available where clarification is required "
                f"(verdict: {assessment.verdict})"
            ),
        )
    record = decline_clarification_record(
        payload.activity,
        activity_key=context_key,
        actor_id=current_user.user_id,
        actor_scope=_actor_scope(current_user),
    )
    stored = await repos.clarifications.apply_versioned(
        record,
        organization_id=payload.organization_id,
        actor_id=current_user.user_id,
        item_id=evidence.get("item_key"),
        batch_key=evidence.get("batch_key"),
        source_evidence_ref=evidence.get("source_evidence_ref"),
        context_key=context_key,
        evidence_signature=(
            repos.clarifications.evidence_signature(payload.activity, unit, scope)
            if evidence
            else None
        ),
        evidence_context=evidence.get("evidence_context"),
    )
    return _result_out({"record": stored, "resolved": False})
