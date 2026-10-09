"""CT-CONSULTANT-PLATFORM-FULL-IMPLEMENTATION-03 — CarbonTally Admin consultant
commercial DECISION surface (PO-1).

PO-1 makes a product-mode change a REQUEST a firm submits and CarbonTally
DECIDES. A consultant can never write ``consultant_profiles.commercial_mode``
(there is no such route anywhere); the ONLY writer is the admin decision route
in this module. The surface records the decision (approve/reject + note +
effective date) and, when an EARLIER transition is explicitly approved
(``apply_now``), applies the mode to the firm's profile.

Admin authority is re-checked server-side via the existing ``require_admin``
gate (the same legacy staff-admin check ``/api/v2/admin/*`` uses); the frontend
is never the security boundary. No new permission vocabulary and no second
subscription model are introduced — entitlement stays CarbonTally-controlled.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from api.dependencies import RepositoryBundle, get_repositories, require_admin
from domain.audit import AuditEntry
from domain.consultant_entitlement import PRODUCT_MODES

router = APIRouter(
    prefix="/api/v3/admin/consultants",
    tags=["V3 — Admin: Consultant Commercial (PO-1)"],
)


class ModeDecisionBody(BaseModel):
    """PO-1 — the CarbonTally Admin decision on a firm's mode-change request."""

    model_config = ConfigDict(extra="forbid")

    decision: str  # approve | reject
    decision_note: Optional[str] = None
    #: The billing/renewal boundary the change becomes effective at. When
    #: ``apply_now`` is set, an EARLIER transition is approved and this defaults
    #: to now.
    effective_at: Optional[datetime] = None
    apply_now: bool = False


async def _audit(
    repos: RepositoryBundle,
    *,
    entity_id: str,
    action: str,
    actor: str,
    after: Optional[dict] = None,
) -> None:
    """Append-only audit for the admin commercial decision (never blocks)."""
    try:
        await repos.audit.record(
            AuditEntry(
                id="",
                correlation_id="",
                entity_type="consultant_mode_change_request",
                entity_id=entity_id,
                action=action,
                actor=actor or "",
                occurred_at=datetime.now(timezone.utc),
                changed_fields={"after": after},
                before=None,
                after=after,
            )
        )
    except Exception:  # noqa: BLE001 — audit never breaks the decision
        pass


@router.get("/mode-change-requests")
async def list_pending_mode_change_requests(
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The CarbonTally Admin queue: every firm's UNDECIDED mode-change request."""
    return {"requests": await repos.consultants.list_pending_mode_change_requests()}


@router.post("/mode-change-requests/{request_id}/decision")
async def decide_mode_change_request(
    request_id: str,
    payload: ModeDecisionBody,
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """PO-1 — CarbonTally Admin approves/rejects a firm's mode-change request.

    * reject  -> the request is ``rejected``; the firm's mode is untouched.
    * approve -> the request is ``approved`` at ``effective_at`` (the
      billing/renewal boundary). When ``apply_now`` is set, CarbonTally approves
      an EARLIER transition and the mode is applied to the firm immediately.
    """
    request = await repos.consultants.get_mode_change_request(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="mode-change request not found")
    if (request.get("status") or "requested") != "requested":
        raise HTTPException(
            status_code=409, detail="this request has already been decided"
        )
    decision = (payload.decision or "").strip().lower()
    if decision not in ("approve", "reject"):
        raise HTTPException(status_code=422, detail="decision must be approve or reject")

    firm_id = request.get("firm_id")
    if decision == "reject":
        updated = await repos.consultants.decide_mode_change_request(
            request_id,
            status="rejected",
            decided_by=current_user.user_id,
            decision_note=payload.decision_note,
        )
        if updated is None:
            # Lost the atomic race — another admin decision landed first.
            raise HTTPException(
                status_code=409, detail="this request has already been decided"
            )
        await _audit(
            repos,
            entity_id=request_id,
            action="admin.mode_change_rejected",
            actor=current_user.user_id,
            after={"status": "rejected", "decision_note": payload.decision_note},
        )
        return {"request": updated, "applied_mode": None}

    target = request.get("requested_mode")
    if target not in PRODUCT_MODES:
        raise HTTPException(
            status_code=422, detail="requested_mode is not a valid product mode"
        )

    effective_at = payload.effective_at
    applied_mode = None
    if payload.apply_now:
        # PO-1 — CarbonTally may approve an earlier (immediate) transition.
        applied_mode = await repos.consultants.set_commercial_mode(firm_id, target)
        effective_at = effective_at or datetime.now(timezone.utc)

    updated = await repos.consultants.decide_mode_change_request(
        request_id,
        status="approved",
        decided_by=current_user.user_id,
        decision_note=payload.decision_note,
        effective_at=effective_at,
    )
    if updated is None:
        # Lost the atomic race — another admin decision landed first.
        raise HTTPException(
            status_code=409, detail="this request has already been decided"
        )
    await _audit(
        repos,
        entity_id=request_id,
        action="admin.mode_change_approved",
        actor=current_user.user_id,
        after={
            "status": "approved",
            "requested_mode": target,
            "apply_now": payload.apply_now,
            "applied_mode": applied_mode,
        },
    )
    return {"request": updated, "applied_mode": applied_mode}
