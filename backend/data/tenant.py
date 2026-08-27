"""Tenant write surface repository (V3 legacy-capability reimplementation).

Complements ``data.organizations.OrganizationsRepository`` (which owns the
read side for members/facilities/assets) with the create/update/remove methods
the legacy routes exposed for organisation members, facilities and assets.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.operations import AssetDetail, FacilityDetail, MemberRecord, VehicleDetail

_FACILITY_COLUMNS = (
    "id, organization_id, name, postcode, country, type, is_active, "
    "created_at, updated_at, metadata"
)

_ASSET_COLUMNS = (
    "id, organization_id, facility_id, name, type, description, "
    "serial_number, is_active, created_at, metadata"
)

_VEHICLE_COLUMNS = (
    "id, organization_id, name, registration, make, model, fuel_type, "
    "vehicle_type, capacity, capacity_unit, is_active, created_at, "
    "updated_at, metadata"
)

_MEMBER_COLUMNS = (
    "id, organization_id, user_id, role, is_active, created_at, updated_at"
)


def _row_to_member(row: Any) -> MemberRecord:
    r = dict(row)
    return MemberRecord(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        user_id=str(r["user_id"]),
        role=str(r["role"]),
        is_active=bool(r.get("is_active", True)),
        joined_at=r.get("created_at"),
        last_active=r.get("updated_at"),
    )


def _row_to_facility(row: Any) -> FacilityDetail:
    r = dict(row)
    return FacilityDetail(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        name=str(r["name"]),
        postcode=r.get("postcode"),
        country=str(r.get("country") or "GB"),
        type=r.get("type"),
        is_active=bool(r.get("is_active", True)),
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
        metadata=loads_jsonb(r.get("metadata")) or {},
    )


def _row_to_asset(row: Any) -> AssetDetail:
    r = dict(row)
    return AssetDetail(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        facility_id=r.get("facility_id"),
        name=str(r["name"]),
        type=r.get("type"),
        description=r.get("description"),
        serial_number=r.get("serial_number"),
        is_active=bool(r.get("is_active", True)),
        created_at=r.get("created_at"),
        metadata=loads_jsonb(r.get("metadata")) or {},
    )


def _row_to_vehicle(row: Any) -> VehicleDetail:
    r = dict(row)
    return VehicleDetail(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        name=str(r["name"]),
        registration=r.get("registration"),
        make=r.get("make"),
        model=r.get("model"),
        fuel_type=r.get("fuel_type"),
        vehicle_type=r.get("vehicle_type"),
        capacity=float(r["capacity"]) if r.get("capacity") is not None else None,
        capacity_unit=r.get("capacity_unit"),
        is_active=bool(r.get("is_active", True)),
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
        metadata=loads_jsonb(r.get("metadata")) or {},
    )


class TenantRepository(AbstractRepository[dict]):
    """Create/update/remove for members, facilities and assets."""

    # -- members -----------------------------------------------------------
    async def get_member_by_user(self, org_id: str, user_id: str) -> Optional[MemberRecord]:
        row = await self._fetch_one(
            f"SELECT {_MEMBER_COLUMNS} FROM public.organization_members "
            "WHERE organization_id = $1 AND user_id = $2 LIMIT 1",
            org_id,
            user_id,
        )
        return _row_to_member(row) if row is not None else None

    async def add_member(self, org_id: str, user_id: str, role: str) -> MemberRecord:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.organization_members (
                organization_id, user_id, role, is_active, created_at
            ) VALUES ($1, $2, $3, TRUE, NOW())
            RETURNING {_MEMBER_COLUMNS}
            """,
            org_id,
            user_id,
            role,
        )
        if row is None:
            raise RuntimeError("organization_members insert returned no row")
        return _row_to_member(row)

    async def update_member(self, member_id: str, role: Optional[str], is_active: Optional[bool]) -> Optional[MemberRecord]:
        sets, args = ["updated_at = NOW()"], [member_id]
        if role is not None:
            sets.append(f"role = ${len(args) + 1}")
            args.append(role)
        if is_active is not None:
            sets.append(f"is_active = ${len(args) + 1}")
            args.append(is_active)
        row = await self._fetch_one(
            f"UPDATE public.organization_members SET {', '.join(sets)} "
            f"WHERE id = $1 RETURNING {_MEMBER_COLUMNS}",
            *args,
        )
        return _row_to_member(row) if row is not None else None

    async def remove_member(self, member_id: str) -> None:
        await self._execute(
            "UPDATE public.organization_members SET is_active = FALSE WHERE id = $1",
            member_id,
        )

    # -- facilities --------------------------------------------------------
    async def get_facility(self, facility_id: str) -> Optional[FacilityDetail]:
        row = await self._fetch_one(
            f"SELECT {_FACILITY_COLUMNS} FROM public.facilities WHERE id = $1",
            facility_id,
        )
        return _row_to_facility(row) if row is not None else None

    async def add_facility(
        self,
        org_id: str,
        name: str,
        postcode: Optional[str],
        country: str,
        type_: Optional[str],
        metadata: dict,
    ) -> FacilityDetail:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.facilities (
                organization_id, name, postcode, country, type, is_active,
                created_at, updated_at, metadata
            ) VALUES ($1, $2, $3, $4, $5, TRUE, NOW(), NOW(), $6)
            RETURNING {_FACILITY_COLUMNS}
            """,
            org_id,
            name,
            postcode,
            country,
            type_,
            dumps_jsonb(metadata),
        )
        if row is None:
            raise RuntimeError("facilities insert returned no row")
        return _row_to_facility(row)

    async def update_facility(
        self, facility_id: str, name: Optional[str], is_active: Optional[bool]
    ) -> Optional[FacilityDetail]:
        sets, args = ["updated_at = NOW()"], [facility_id]
        if name is not None:
            sets.append(f"name = ${len(args) + 1}")
            args.append(name)
        if is_active is not None:
            sets.append(f"is_active = ${len(args) + 1}")
            args.append(is_active)
        row = await self._fetch_one(
            f"UPDATE public.facilities SET {', '.join(sets)} "
            f"WHERE id = $1 RETURNING {_FACILITY_COLUMNS}",
            *args,
        )
        return _row_to_facility(row) if row is not None else None

    async def remove_facility(self, facility_id: str) -> None:
        await self._execute(
            "UPDATE public.facilities SET is_active = FALSE WHERE id = $1",
            facility_id,
        )

    # -- assets ------------------------------------------------------------
    async def get_asset(self, asset_id: str) -> Optional[AssetDetail]:
        row = await self._fetch_one(
            f"SELECT {_ASSET_COLUMNS} FROM public.assets WHERE id = $1",
            asset_id,
        )
        return _row_to_asset(row) if row is not None else None

    async def add_asset(
        self,
        org_id: str,
        facility_id: Optional[str],
        name: str,
        type_: Optional[str],
        metadata: dict,
    ) -> AssetDetail:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.assets (
                organization_id, facility_id, name, type, is_active,
                created_at, metadata
            ) VALUES ($1, $2, $3, $4, TRUE, NOW(), $5)
            RETURNING {_ASSET_COLUMNS}
            """,
            org_id,
            facility_id,
            name,
            type_,
            dumps_jsonb(metadata),
        )
        if row is None:
            raise RuntimeError("assets insert returned no row")
        return _row_to_asset(row)

    async def update_asset(
        self, asset_id: str, name: Optional[str], is_active: Optional[bool]
    ) -> Optional[AssetDetail]:
        sets, args = [], [asset_id]
        if name is not None:
            sets.append(f"name = ${len(args) + 1}")
            args.append(name)
        if is_active is not None:
            sets.append(f"is_active = ${len(args) + 1}")
            args.append(is_active)
        sets.append("updated_at = NOW()")
        row = await self._fetch_one(
            f"UPDATE public.assets SET {', '.join(sets)} "
            f"WHERE id = $1 RETURNING {_ASSET_COLUMNS}",
            *args,
        )
        return _row_to_asset(row) if row is not None else None

    async def remove_asset(self, asset_id: str) -> None:
        await self._execute(
            "UPDATE public.assets SET is_active = FALSE WHERE id = $1",
            asset_id,
        )

    # -- vehicles (D17) -----------------------------------------------------
    async def list_vehicles(self, org_id: str) -> list[VehicleDetail]:
        rows = await self._fetch_all(
            f"SELECT {_VEHICLE_COLUMNS} FROM public.vehicles "
            "WHERE organization_id = $1 ORDER BY name, id",
            org_id,
        )
        return [_row_to_vehicle(r) for r in rows]

    async def get_vehicle(self, vehicle_id: str) -> Optional[VehicleDetail]:
        row = await self._fetch_one(
            f"SELECT {_VEHICLE_COLUMNS} FROM public.vehicles WHERE id = $1",
            vehicle_id,
        )
        return _row_to_vehicle(row) if row is not None else None

    async def add_vehicle(
        self,
        org_id: str,
        name: str,
        registration: Optional[str],
        make: Optional[str],
        model: Optional[str],
        fuel_type: Optional[str],
        vehicle_type: Optional[str],
        capacity: Optional[float],
        capacity_unit: Optional[str],
        metadata: dict,
    ) -> VehicleDetail:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.vehicles (
                organization_id, name, registration, make, model, fuel_type,
                vehicle_type, capacity, capacity_unit, is_active,
                created_at, updated_at, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, TRUE, NOW(), NOW(), $10)
            RETURNING {_VEHICLE_COLUMNS}
            """,
            org_id,
            name,
            registration,
            make,
            model,
            fuel_type,
            vehicle_type,
            capacity,
            capacity_unit,
            dumps_jsonb(metadata),
        )
        if row is None:
            raise RuntimeError("vehicles insert returned no row")
        return _row_to_vehicle(row)

    async def update_vehicle(
        self,
        vehicle_id: str,
        name: Optional[str] = None,
        registration: Optional[str] = None,
        make: Optional[str] = None,
        model: Optional[str] = None,
        fuel_type: Optional[str] = None,
        vehicle_type: Optional[str] = None,
        capacity: Optional[float] = None,
        capacity_unit: Optional[str] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[VehicleDetail]:
        sets, args = ["updated_at = NOW()"], [vehicle_id]

        def add(col: str, value: Any) -> None:
            sets.append(f"{col} = ${len(args) + 1}")
            args.append(value)

        if name is not None:
            add("name", name)
        if registration is not None:
            add("registration", registration)
        if make is not None:
            add("make", make)
        if model is not None:
            add("model", model)
        if fuel_type is not None:
            add("fuel_type", fuel_type)
        if vehicle_type is not None:
            add("vehicle_type", vehicle_type)
        if capacity is not None:
            add("capacity", capacity)
        if capacity_unit is not None:
            add("capacity_unit", capacity_unit)
        if is_active is not None:
            add("is_active", is_active)
        if metadata is not None:
            add("metadata", dumps_jsonb(metadata))
        if len(sets) == 1:
            return await self.get_vehicle(vehicle_id)
        row = await self._fetch_one(
            f"UPDATE public.vehicles SET {', '.join(sets)} "
            f"WHERE id = $1 RETURNING {_VEHICLE_COLUMNS}",
            *args,
        )
        return _row_to_vehicle(row) if row is not None else None

    async def remove_vehicle(self, vehicle_id: str) -> None:
        await self._execute(
            "UPDATE public.vehicles SET is_active = FALSE WHERE id = $1",
            vehicle_id,
        )

    # AbstractRepository contract (this repository is method-driven).
    async def get(self, id: str):
        return None

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        return None

