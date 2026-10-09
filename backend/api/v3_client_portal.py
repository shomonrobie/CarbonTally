"""CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — Plane C client portal API (F-7/F-8).

The binding client portal route family is ``/portal/:clientId/*`` (PO-8 A). This
router is the API behind it: ``/api/v3/portal/{client_id}/...``. Every route
resolves the server-authoritative :class:`ClientPortalContext` first, so the
client cannot change clientId, Organisation or tenant through the URL, and the
CLIENT ACCESS PROFILE is enforced server-side on every read and write (MUST-2).

Explicitly ABSENT (PO-9 / NB-3, verified by a route-absence test):
  * no factor-mapping editor, factor search or mapping write;
  * no recalculation trigger;
  * no user invitation / user management (PO-2 / MUST-4);
  * no plan / invoice / subscription / upgrade surface (PO-5 / MUST-5);
  * no access-profile, branding or relationship control other than the OQ-1
    REQUEST endpoints below.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from api.client_portal_auth import (
    ClientPortalContext,
    ensure_client_operation,
    portal_capabilities,
    require_client_portal_context,
)
from api.dependencies import RepositoryBundle, get_repositories
from domain.audit import AuditEntry
from domain.relationship_access import OP_COMMENT, OP_READ_DATA

router = APIRouter(prefix="/api/v3/portal", tags=["V3 — Client Portal (Plane C)"])


class RelationshipRequestBody(BaseModel):
    """OQ-1 / OQ-3 — a NON-destructive request, or an explicit confirmation."""

    model_config = ConfigDict(extra="ignore")

    request_type: str  # change_consultant | end_relationship
    reason: Optional[str] = None
    confirmed: bool = False


class AnnotationBody(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str


def _context_body(context: ClientPortalContext) -> dict:
    return {
        "organization": {
            "id": context.organization_id,
            "name": context.organization_name,
        },
        "consultant": {
            "firm_id": context.firm_id,
            "firm_name": context.firm_name,
        },
        "brand": context.brand.to_dict(),
        "mode": context.mode,
        "profile": context.profile,
        "state": context.state,
        "retained_read_only": context.retained_read_only,
        "capabilities": portal_capabilities(context),
    }


@router.get("/{client_id}/context")
async def portal_context(
    context: ClientPortalContext = Depends(require_client_portal_context),
):
    """The plane's context + the profile CEILING matrix (§11.2 MUST-2)."""
    ensure_client_operation(context, OP_READ_DATA)
    return _context_body(context)


@router.get("/{client_id}/organization")
async def portal_organization(
    context: ClientPortalContext = Depends(require_client_portal_context),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Organisation-scoped data only (MUST-7) — never another client's data."""
    ensure_client_operation(context, OP_READ_DATA)
    organization = await repos.organizations.get(context.organization_id)
    return {
        "organization": {
            "id": context.organization_id,
            "name": context.organization_name,
            "country": getattr(organization, "country", None),
            "is_active": bool(getattr(organization, "is_active", True)),
        },
        "read_only": context.is_retained,
    }


async def _audit(repos: RepositoryBundle, **fields) -> None:
    from datetime import datetime, timezone

    try:
        await repos.audit.record(
            AuditEntry(
                id="",
                correlation_id="",
                occurred_at=datetime.now(timezone.utc),
                changed_fields={},
                before=None,
                after=None,
                **fields,
            )
        )
    except Exception:  # noqa: BLE001 — audit never breaks the client action
        pass


@router.post("/{client_id}/annotations", status_code=201)
async def portal_annotation(
    payload: AnnotationBody,
    context: ClientPortalContext = Depends(require_client_portal_context),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """A client "comment / respond to a query" write (§8.2, OP_COMMENT).

    Permitted in READ_ONLY / COLLABORATIVE / MANAGED while the link is ACTIVE;
    DENIED for a RETAINED relationship (PA-3: no messaging-send after
    termination) and for OFF. A retained client therefore cannot write here even
    though they can still read their history.
    """
    ensure_client_operation(context, OP_COMMENT)
    await _audit(
        repos,
        entity_type="consultant_client_annotation",
        entity_id=context.organization_id,
        action="portal.annotation.created",
        actor=str(getattr(context.relationship, "created_by", None) or ""),
    )
    return {"status": "recorded", "organization_id": context.organization_id}


@router.post("/{client_id}/relationship-requests", status_code=201)
async def portal_relationship_request(
    payload: RelationshipRequestBody,
    context: ClientPortalContext = Depends(require_client_portal_context),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """OQ-1 / OQ-3 — a client-initiated CHANGE or END REQUEST (non-destructive).

    Not an immediate operation: it records an authenticated, authorised,
    auditable REQUEST. For a profile with no portal access (OFF), the same
    request is submitted through the CarbonTally support path — this endpoint is
    unreachable for that client by construction (no plane).
    """
    # Only an ACTIVE relationship can be changed/ended by the client; a retained
    # (already-ended) relationship has nothing to request here.
    if context.state != "active":
        raise HTTPException(
            status_code=409,
            detail=(
                "This engagement has already ended; contact CarbonTally support "
                "to reconnect."
            ),
        )
    if payload.request_type not in ("change_consultant", "end_relationship"):
        raise HTTPException(
            status_code=422,
            detail="request_type must be change_consultant or end_relationship",
        )
    if not payload.confirmed:
        # T-1: no single-click termination — an explicit confirmation is required.
        raise HTTPException(
            status_code=428,
            detail="Explicit confirmation is required to submit this request",
        )
    record = await repos.consultants.create_relationship_request(
        organization_id=context.organization_id,
        consultant_id=context.firm_id,
        request_type=payload.request_type,
        initiated_by=None,
        initiated_capacity="client",
        reason=payload.reason,
        contact_email=None,
    )
    await _audit(
        repos,
        entity_type="consultant_relationship_request",
        entity_id=str(record.get("id") or context.organization_id),
        action=f"portal.relationship.{payload.request_type}_requested",
        actor="",
    )
    return {"request": record}
