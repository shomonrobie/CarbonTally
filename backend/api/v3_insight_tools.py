"""CarbonTally Insight I3 — controlled read-only tool surface (HTTP).

Authorization: PO I3 Tool Catalogue Ratification Decision Record (2026-09-21).
Four ratified tools only; no LLM, no provider, no mutation, no arbitrary query.

Every route carries the I2 gate (``require_insight_user``) at the router, and every
invocation additionally resolves the caller's scope through
``authorize_insight_scope`` — the surface cannot widen the closed I1/I2 boundary.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.dependencies import RepositoryBundle, get_repositories
from api.insight_authz import require_insight_user
from auth import AuthUser
from domain.insight_tool import TOOL_CONTRACT_VERSION
from services.insight_rate_limit import (
    RateLimitDecision,
    acquire_execution_leases,
    check_request_rates,
    rate_limited_error,
    release_execution_leases,
)
from services.insight_tools import classify_intent, invoke_tool, registry_payload

router = APIRouter(
    prefix="/api/v3/insight/tools",
    tags=["V3 — CarbonTally Insight (I3 tools)"],
    dependencies=[Depends(require_insight_user)],
)


class ToolInvokeIn(BaseModel):
    """A tool invocation: the authorized organisation scope + tool + bounded input."""

    organization_id: str = Field(..., min_length=1)
    tool: str = Field(..., min_length=1, max_length=128)
    input: dict[str, Any] = Field(default_factory=dict)


class IntentIn(BaseModel):
    """A deterministic routing request (no answer generation)."""

    utterance: str = Field(..., min_length=1, max_length=2000)


@router.get("")
async def list_tools() -> dict:
    """The ratified I3 registry (definitions only; executes nothing)."""
    return {"contract_version": TOOL_CONTRACT_VERSION, "tools": registry_payload()}


@router.post("/invoke")
async def invoke(
    payload: ToolInvokeIn,
    current_user: AuthUser = Depends(require_insight_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Deterministic read-only execution: validate → I2 authorize → read → status.

    Phase 8 I8-A — this route is a second customer-facing Insight execution path,
    so it carries the *same* rate limit as ``POST /api/v3/insight/interactions``.
    The limit cannot be bypassed by switching routes.
    """
    rate_decision = await check_request_rates(
        repos=repos,
        user_id=current_user.user_id,
        organization_id=payload.organization_id,
    )
    if not rate_decision.allowed:
        raise rate_limited_error(rate_decision)
    lease = await acquire_execution_leases(
        repos=repos,
        user_id=current_user.user_id,
        organization_id=payload.organization_id,
    )
    if not lease.acquired:
        raise rate_limited_error(
            RateLimitDecision(
                allowed=False,
                scope=lease.scope,
                limit=lease.max_concurrent,
                capacity=lease.max_concurrent,
                remaining=0,
                retry_after_seconds=lease.retry_after_seconds,
            )
        )
    try:
        result = await invoke_tool(
            tool_name=payload.tool,
            current_user=current_user,
            repos=repos,
            organization_id=payload.organization_id,
            tool_input=payload.input,
        )
    finally:
        await release_execution_leases(repos=repos, lease=lease)
    return result.as_dict()


@router.post("/intent")
async def classify(payload: IntentIn) -> dict:
    """Deterministic intent classification (routes to one of the four tools, or refuses)."""
    return {"contract_version": TOOL_CONTRACT_VERSION, **classify_intent(payload.utterance)}
