"""V3 vehicles surface (D17 organisation master data).

Organisation-scoped fleet master data with the same authorization posture as
facilities/assets:

* list / get   — org member (``require_org_member`` + ``ensure_org_access``)
* create/update/remove — org admin (``require_org_admin`` + org access)

RLS (migration 20260825000000_v3m7_vehicles.sql) is the authoritative boundary:
SELECT = org member OR authorised consultant; INSERT/UPDATE/DELETE = org member.
This module never bypasses RLS.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_repositories,
)
from auth import AuthUser, require_org_admin, require_org_member
from pydantic import BaseModel

router = APIRouter(prefix="/api/v3/vehicles", tags=["V3 — Vehicles"])


class VehicleCreate(BaseModel):
    organization_id: str
    name: str
    registration: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    fuel_type: Optional[str] = None
    vehicle_type: Optional[str] = None
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    metadata: dict = {}


class VehicleUpdate(BaseModel):
    name: Optional[str] = None
    registration: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    fuel_type: Optional[str] = None
    vehicle_type: Optional[str] = None
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


@router.get("")
async def list_vehicles(
    organization_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    return {"vehicles": await repos.tenant.list_vehicles(organization_id)}


@router.get("/{vehicle_id}")
async def get_vehicle(
    vehicle_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    vehicle = await repos.tenant.get_vehicle(vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=404, detail="vehicle not found")
    ensure_org_access(current_user, vehicle.organization_id)
    return vehicle


@router.post("", status_code=201)
async def add_vehicle(
    payload: VehicleCreate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, payload.organization_id)
    return await repos.tenant.add_vehicle(
        payload.organization_id,
        payload.name.strip(),
        payload.registration,
        payload.make,
        payload.model,
        payload.fuel_type,
        payload.vehicle_type,
        payload.capacity,
        payload.capacity_unit,
        payload.metadata,
    )


@router.put("/{vehicle_id}")
async def update_vehicle(
    vehicle_id: str,
    payload: VehicleUpdate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    existing = await repos.tenant.get_vehicle(vehicle_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="vehicle not found")
    ensure_org_access(current_user, existing.organization_id)
    updated = await repos.tenant.update_vehicle(
        vehicle_id,
        name=payload.name.strip() if payload.name is not None else None,
        registration=payload.registration,
        make=payload.make,
        model=payload.model,
        fuel_type=payload.fuel_type,
        vehicle_type=payload.vehicle_type,
        capacity=payload.capacity,
        capacity_unit=payload.capacity_unit,
        is_active=payload.is_active,
        metadata=payload.metadata,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="vehicle not found")
    return updated


@router.delete("/{vehicle_id}", status_code=204)
async def remove_vehicle(
    vehicle_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    vehicle = await repos.tenant.get_vehicle(vehicle_id)
    if vehicle is not None:
        ensure_org_access(current_user, vehicle.organization_id)
    await repos.tenant.remove_vehicle(vehicle_id)
