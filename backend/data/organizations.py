"""Organisations repository (Backend v2.1 §10).

Persistence for the RC2 ``organizations`` aggregate and its child structures
(members, metadata, facilities, assets).
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository
from domain.organization import (
    Asset,
    Facility,
    Organization,
    OrganizationMember,
    OrganizationMetadata,
)

_ORG_COLUMNS = "id, name, country, is_active, created_at"

_MEMBER_COLUMNS = "id, organization_id, user_id, role, is_active, created_at"

_METADATA_COLUMNS = """
    total_floor_area_sqm, occupied_floor_area_sqm, average_employees,
    annual_revenue, industry_sector
"""

_FACILITY_COLUMNS = """
    id, organization_id, name, address_line1, address_line2, city, county,
    postcode
"""

_ASSET_COLUMNS = "id, facility_id, organization_id, name, type AS asset_type"


def _row_to_org(row: Any) -> Organization:
    r = dict(row)
    return Organization(
        id=str(r["id"]),
        name=str(r["name"]),
        country=str(r.get("country") or "GB"),
        is_active=bool(r["is_active"]),
        created_at=r["created_at"],
    )


def _row_to_member(row: Any) -> OrganizationMember:
    r = dict(row)
    return OrganizationMember(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        user_id=str(r["user_id"]),
        role=str(r["role"]),
        is_active=bool(r.get("is_active", True)),
        created_at=r.get("created_at"),
    )


def _row_to_metadata(row: Any) -> OrganizationMetadata:
    r = dict(row)
    return OrganizationMetadata(
        total_floor_area_sqm=_as_float(r.get("total_floor_area_sqm")),
        occupied_floor_area_sqm=_as_float(r.get("occupied_floor_area_sqm")),
        fte_count=_as_int(r.get("average_employees")),
        annual_revenue_gbp=_as_float(r.get("annual_revenue")),
        sector=r.get("industry_sector"),
    )


def _row_to_facility(row: Any) -> Facility:
    r = dict(row)
    parts = [
        str(r.get(col) or "")
        for col in ("address_line1", "address_line2", "city", "county")
    ]
    return Facility(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        name=str(r["name"]),
        address=", ".join(p for p in parts if p),
        postcode=r.get("postcode"),
    )


def _row_to_asset(row: Any) -> Asset:
    r = dict(row)
    return Asset(
        id=str(r["id"]),
        facility_id=str(r["facility_id"]),
        organization_id=str(r["organization_id"]) if r.get("organization_id") else "",
        name=str(r["name"]),
        asset_type=str(r.get("asset_type") or "other"),
    )


def _as_float(value: Any) -> Optional[float]:
    return float(value) if value is not None else None


def _as_int(value: Any) -> Optional[int]:
    return int(value) if value is not None else None

class OrganizationsRepository(AbstractRepository[Organization]):
    """CRUD and lookup for organisations and their child structures."""

    async def get_by_id(self, org_id: str) -> Optional[Organization]:
        """Return the organisation with ``org_id``, or ``None``."""
        return await self.get(org_id)

    async def get_members(self, org_id: str) -> list[OrganizationMember]:
        """Return every member of the organisation with their roles."""
        rows = await self._fetch_all(
            f"""
            SELECT {_MEMBER_COLUMNS} FROM public.organization_members
            WHERE organization_id = $1
            ORDER BY created_at, id
            """,
            org_id,
        )
        return [_row_to_member(r) for r in rows]

    async def get_metadata(self, org_id: str) -> Optional[OrganizationMetadata]:
        """Return the organisation's metadata, or ``None`` when absent."""
        row = await self._fetch_one(
            f"""
            SELECT {_METADATA_COLUMNS} FROM public.organization_metadata
            WHERE organization_id = $1
            LIMIT 1
            """,
            org_id,
        )
        return _row_to_metadata(row) if row is not None else None

    async def get_facilities(self, org_id: str) -> list[Facility]:
        """Return every facility belonging to the organisation."""
        rows = await self._fetch_all(
            f"""
            SELECT {_FACILITY_COLUMNS} FROM public.facilities
            WHERE organization_id = $1
            ORDER BY name, id
            """,
            org_id,
        )
        return [_row_to_facility(r) for r in rows]

    async def get_assets(self, org_id: str) -> list[Asset]:
        """Return every asset belonging to the organisation."""
        rows = await self._fetch_all(
            f"""
            SELECT {_ASSET_COLUMNS} FROM public.assets
            WHERE organization_id = $1
            ORDER BY name, id
            """,
            org_id,
        )
        return [_row_to_asset(r) for r in rows]

    async def get(self, id: str) -> Optional[Organization]:
        """Return the organisation with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_ORG_COLUMNS} FROM public.organizations WHERE id = $1",
            id,
        )
        return _row_to_org(row) if row is not None else None

    async def save(self, entity: Organization) -> Organization:
        """Upsert an organisation by id and return the stored state."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.organizations (id, name, country, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, NOW(), NOW())
            ON CONFLICT (id)
            DO UPDATE SET
                name = EXCLUDED.name,
                country = EXCLUDED.country,
                is_active = EXCLUDED.is_active,
                updated_at = NOW()
            RETURNING {_ORG_COLUMNS}
            """,
            entity.id,
            entity.name,
            entity.country,
            entity.is_active,
        )
        if row is None:
            raise RuntimeError("organization upsert returned no row")
        return _row_to_org(row)

    async def delete(self, id: str) -> None:
        """Delete an organisation (cascades to its child rows)."""
        await self._execute(
            "DELETE FROM public.organizations WHERE id = $1", id
        )

    async def update_metadata(
        self, org_id: str, data: OrganizationMetadata
    ) -> OrganizationMetadata:
        """Upsert the organisation's metadata row and return the stored state."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.organization_metadata (
                organization_id, total_floor_area_sqm, occupied_floor_area_sqm,
                average_employees, annual_revenue, industry_sector,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
            ON CONFLICT (organization_id)
            DO UPDATE SET
                total_floor_area_sqm = EXCLUDED.total_floor_area_sqm,
                occupied_floor_area_sqm = EXCLUDED.occupied_floor_area_sqm,
                average_employees = EXCLUDED.average_employees,
                annual_revenue = EXCLUDED.annual_revenue,
                industry_sector = EXCLUDED.industry_sector,
                updated_at = NOW()
            RETURNING {_METADATA_COLUMNS}
            """,
            org_id,
            data.total_floor_area_sqm,
            data.occupied_floor_area_sqm,
            data.fte_count,
            data.annual_revenue_gbp,
            data.sector,
        )
        if row is None:
            raise RuntimeError("organization metadata upsert returned no row")
        return _row_to_metadata(row)

