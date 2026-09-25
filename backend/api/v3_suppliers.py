"""V3 suppliers surface (V3 new capability).

Organisation-scoped supplier records (``suppliers``).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.accounting_context_auth import ensure_record_owner_authorized
from api.audit_helpers import record_acting_for_attribution
from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_repositories,
)
from auth import AuthUser, require_org_member, require_org_admin

router = APIRouter(prefix="/api/v3/suppliers", tags=["V3 — Suppliers"])


class SupplierCreate(BaseModel):
    organization_id: str
    name: str
    type: Optional[str] = None
    supplier_type: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    country: Optional[str] = None
    vat_number: Optional[str] = None
    metadata: dict = {}


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_suppliers(
    organization_id: str,
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    return {
        "suppliers": await repos.suppliers.search_for_org(
            organization_id,
            search=search,
            category_id=category_id,
            status=status,
            limit=limit,
            offset=offset,
        )
    }


@router.post("", status_code=201)
async def create_supplier(
    payload: SupplierCreate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, payload.organization_id)
    # P17-IMPLEMENT-03 — persist acting-for attribution on the supplier write.
    #
    # The SUPPLIER'S ORGANIZATION is the authority: resolve_record_owner_authorized
    # re-authorises the actor against the data-owning organization (not against
    # anything the client supplied), and the acting-for value is taken from that
    # server-resolved context. A forged acting_for_organization_id in the payload
    # is impossible here because SupplierCreate has no such field and nothing from
    # the request body reaches the attribution.
    context = await ensure_record_owner_authorized(
        current_user, repos, payload.organization_id
    )
    supplier = await repos.suppliers.create(
        org_id=payload.organization_id,
        name=payload.name,
        type_=payload.type,
        supplier_type=payload.supplier_type,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        country=payload.country,
        vat_number=payload.vat_number,
        metadata=payload.metadata,
        created_by=current_user.user_id,
        provenance=context.provenance_columns(),
    )
    await record_acting_for_attribution(
        repos,
        carrier="supplier",
        record_id=str(getattr(supplier, "id", "")),
        actor=current_user.user_id,
        actor_organization_id=context.actor_organization_id,
        acting_for_organization_id=context.acting_for_organization_id,
        owner_organization_id=payload.organization_id,
    )
    return supplier


@router.get("/{supplier_id}")
async def get_supplier(
    supplier_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    supplier = await repos.suppliers.get(supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="supplier not found")
    ensure_org_access(current_user, supplier.organization_id)
    return supplier


@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: str,
    payload: SupplierUpdate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    supplier = await repos.suppliers.get(supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="supplier not found")
    ensure_org_access(current_user, supplier.organization_id)
    result = await repos.suppliers.update(
        supplier_id, payload.name, payload.contact_email, payload.is_active
    )
    if result is None:
        raise HTTPException(status_code=404, detail="supplier not found")
    return result


@router.delete("/{supplier_id}", status_code=204)
async def remove_supplier(
    supplier_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    supplier = await repos.suppliers.get(supplier_id)
    if supplier is not None:
        ensure_org_access(current_user, supplier.organization_id)
    await repos.suppliers.remove(supplier_id)
