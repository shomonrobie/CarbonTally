"""CarbonTally Insight I4 — interaction API (authorized I4 stage).

Authorization: PO I4 Implementation Authorization (2026-09-21); PO Q7 (Layer-2
lifecycle), Q9 (interaction/tool-call correlation), Q11 (truthful
provider-unavailable behaviour), Q8 (creator-private visibility only).

Minimum surface required by the Master Specification (§30 API design, §31 error
boundary): run one authorized interaction, read one interaction, list the
caller's own interactions. No new personas, permissions, tools or endpoints.

Every route is attached to the Insight router dependencies (``require_insight_user``)
and re-authorizes through the closed I2 boundary inside the service, so an
unauthenticated, PE, auditor or cross-organisation caller is denied before any
Layer-2 evidence is written.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import RepositoryBundle, get_repositories
from api.insight_authz import require_insight_user
from auth import AuthUser
from domain.insight_interaction import MAX_IDEMPOTENCY_KEY_LENGTH, MAX_QUESTION_LENGTH
from services.insight_interactions import (
    NARRATION_MODES,
    NARRATION_OPTIONAL,
    get_interaction_outcome,
    list_interaction_outcomes,
    narration_client,
    run_interaction,
)

router = APIRouter(
    prefix="/api/v3/insight",
    tags=["V3 — CarbonTally Insight"],
    dependencies=[Depends(require_insight_user)],
)


class InteractionCreateIn(BaseModel):
    organization_id: str = Field(..., min_length=1)
    conversation_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_LENGTH)
    idempotency_key: Optional[str] = Field(
        default=None, max_length=MAX_IDEMPOTENCY_KEY_LENGTH
    )
    #: ``none`` | ``optional`` | ``required`` — see PO Q11/Q14.
    narration: str = Field(default=NARRATION_OPTIONAL)


@router.post("/interactions", status_code=status.HTTP_201_CREATED)
async def create_interaction(
    payload: InteractionCreateIn,
    current_user: AuthUser = Depends(require_insight_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Run one authorized I4 interaction and return its persisted outcome."""
    if payload.narration not in NARRATION_MODES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="narration must be one of: " + ", ".join(NARRATION_MODES),
        )
    outcome = await run_interaction(
        current_user=current_user,
        repos=repos,
        organization_id=payload.organization_id,
        conversation_id=payload.conversation_id,
        question=payload.question,
        idempotency_key=payload.idempotency_key,
        narration=payload.narration,
        llm_client=narration_client(),
    )
    return outcome.as_dict()


@router.get("/interactions")
async def list_interactions(
    organization_id: str = Query(..., min_length=1),
    conversation_id: Optional[str] = Query(default=None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_insight_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """List the caller's own interactions (creator-private)."""
    return await list_interaction_outcomes(
        current_user=current_user,
        repos=repos,
        organization_id=organization_id,
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )


@router.get("/interactions/{interaction_id}")
async def get_interaction(
    interaction_id: str,
    organization_id: str = Query(..., min_length=1),
    current_user: AuthUser = Depends(require_insight_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Read one interaction (creator-private; existence is not disclosed)."""
    return await get_interaction_outcome(
        current_user=current_user,
        repos=repos,
        organization_id=organization_id,
        interaction_id=interaction_id,
    )
