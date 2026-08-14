"""Admin factor-alias endpoints (prep-pack Phase 10.3, aliases; §20.2).

Exposes the existing :class:`data.factor_aliases.FactorAliasesRepository` — the
single RC2 ``factor_aliases`` table is used; no second alias store is created.

Organisation ownership is preserved: ``organization_id = NULL`` aliases are
global; a non-NULL value scopes the alias to one organisation. The endpoint is
staff/admin-only, so organisation-scoped alias data is never reachable by
unauthorised users. Write operations record an audit entry through the existing
``AuditRepository`` (audit framework reuse).
"""
from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from api.contracts import (
    FactorAliasCreate,
    FactorAliasListOut,
    FactorAliasOut,
    FactorAliasUpdate,
    factor_alias_out,
)
from api.dependencies import (
    AuditContext,
    RepositoryBundle,
    get_audit_context,
    get_repositories,
    require_admin,
)
from domain.audit import AuditEntry
from domain.matching import FactorAlias

router = APIRouter(prefix="/api/v2/admin/aliases", tags=["Admin Aliases"])


@router.get("", response_model=FactorAliasListOut)
async def list_aliases(
    org_id: Optional[str] = Query(
        default=None, alias="organization_id", description="Scope listing to one organisation"
    ),
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> FactorAliasListOut:
    """List global aliases, or the aliases of one organisation when scoped."""
    if org_id:
        aliases = await repos.aliases.get_org_aliases(org_id)
    else:
        aliases = await repos.aliases.get_global_aliases()
    return FactorAliasListOut(total=len(aliases), aliases=[factor_alias_out(a) for a in aliases])


@router.post("", response_model=FactorAliasOut, status_code=status.HTTP_201_CREATED)
async def create_alias(
    payload: FactorAliasCreate,
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
) -> FactorAliasOut:
    """Create a global or organisation-scoped alias."""
    alias = FactorAlias(
        id=str(uuid.uuid4()),
        organization_id=payload.organization_id,
        alias_text=payload.alias_text.strip(),
        target_activity_type=payload.target_activity_type,
        target_provider_key=payload.target_provider_key,
        created_by=current_user.user_id,
        created_at=datetime.now(timezone.utc),
    )
    stored = await repos.aliases.save(alias)
    await _record_alias_audit(
        repos,
        audit,
        action="factor_alias:created",
        alias=stored,
        after={"alias_text": stored.alias_text, "organization_id": stored.organization_id},
    )
    return factor_alias_out(stored)


@router.put("/{alias_id}", response_model=FactorAliasOut)
async def update_alias(
    alias_id: str,
    payload: FactorAliasUpdate,
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
) -> FactorAliasOut:
    """Update one alias (404 when unknown)."""
    existing = await repos.aliases.get(alias_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"alias {alias_id} not found")
    updated = replace(
        existing,
        alias_text=payload.alias_text if payload.alias_text is not None else existing.alias_text,
        target_activity_type=(
            payload.target_activity_type
            if payload.target_activity_type is not None
            else existing.target_activity_type
        ),
        target_provider_key=(
            payload.target_provider_key
            if payload.target_provider_key is not None
            else existing.target_provider_key
        ),
        organization_id=(
            payload.organization_id if payload.organization_id is not None else existing.organization_id
        ),
    )
    stored = await repos.aliases.save(updated)
    await _record_alias_audit(
        repos,
        audit,
        action="factor_alias:updated",
        alias=stored,
        after={"alias_text": stored.alias_text, "organization_id": stored.organization_id},
    )
    return factor_alias_out(stored)


@router.delete("/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alias(
    alias_id: str,
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
) -> Response:
    """Delete one alias (404 when unknown)."""
    existing = await repos.aliases.get(alias_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"alias {alias_id} not found")
    await repos.aliases.delete(alias_id)
    await _record_alias_audit(
        repos,
        audit,
        action="factor_alias:deleted",
        alias=existing,
        before={"alias_text": existing.alias_text, "organization_id": existing.organization_id},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _record_alias_audit(
    repos: RepositoryBundle,
    audit: AuditContext,
    *,
    action: str,
    alias: FactorAlias,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
) -> None:
    """Record alias writes through the existing audit repository (best-effort)."""
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id=audit.correlation_id,
        entity_type="factor_alias",
        entity_id=alias.id,
        action=action,
        actor=audit.actor,
        occurred_at=datetime.now(timezone.utc),
        changed_fields={"alias_text": alias.alias_text},
        ip_address=audit.ip_address or None,
        before=before,
        after=after,
    )
    await repos.audit.record(entry)
