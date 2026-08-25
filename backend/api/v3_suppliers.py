"""V3 suppliers surface (V3 new capability).

Organisation-scoped supplier records (``suppliers``).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

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
    return await repos.suppliers.create(
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
    )


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
