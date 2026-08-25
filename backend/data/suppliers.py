"""Suppliers repository (V3 new capability).

Persistence for the RC2 ``suppliers`` table (organisation-scoped supplier
records with emissions factors).
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.partners import Supplier

_SUPPLIER_COLUMNS = (
    "id, organization_id, name, type, supplier_category_id, contact_name, "
    "contact_email, contact_phone, country, vat_number, website, supplier_type, "
    "annual_emissions, supplier_rating, is_certified, is_active, created_at, "
    "updated_at, metadata"
)


def _row_to_supplier(row: Any) -> Supplier:
    r = dict(row)
    return Supplier(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        name=str(r["name"]),
        type=r.get("type"),
        supplier_category_id=r.get("supplier_category_id"),
        contact_name=r.get("contact_name"),
        contact_email=r.get("contact_email"),
        contact_phone=r.get("contact_phone"),
        country=r.get("country"),
        vat_number=r.get("vat_number"),
        website=r.get("website"),
        supplier_type=r.get("supplier_type"),
        annual_emissions=r.get("annual_emissions"),
        supplier_rating=r.get("supplier_rating"),
        is_certified=bool(r.get("is_certified", False)),
        is_active=bool(r.get("is_active", True)),
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
        metadata=loads_jsonb(r.get("metadata")) or {},
    )


class SuppliersRepository(AbstractRepository[Supplier]):
    """CRUD for organisation-scoped suppliers."""

    async def create(
        self,
        org_id: str,
        name: str,
        type_: Optional[str],
        supplier_type: Optional[str],
        contact_name: Optional[str],
        contact_email: Optional[str],
        contact_phone: Optional[str],
        country: Optional[str],
        vat_number: Optional[str],
        metadata: Optional[dict],
        created_by: Optional[str],
    ) -> Supplier:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.suppliers (
                organization_id, name, type, supplier_type, contact_name,
                contact_email, contact_phone, country, vat_number, is_active,
                created_at, created_by, updated_at, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, TRUE, NOW(), $10, NOW(), $11)
            RETURNING {_SUPPLIER_COLUMNS}
            """,
            org_id,
            name,
            type_,
            supplier_type,
            contact_name,
            contact_email,
            contact_phone,
            country,
            vat_number,
            created_by,
            dumps_jsonb(metadata or {}),
        )
        if row is None:
            raise RuntimeError("suppliers insert returned no row")
        return _row_to_supplier(row)

    async def get(self, supplier_id: str) -> Optional[Supplier]:
        row = await self._fetch_one(
            f"SELECT {_SUPPLIER_COLUMNS} FROM public.suppliers WHERE id = $1",
            supplier_id,
        )
        return _row_to_supplier(row) if row is not None else None

    async def list_for_org(self, org_id: str) -> list[Supplier]:
        rows = await self._fetch_all(
            f"SELECT {_SUPPLIER_COLUMNS} FROM public.suppliers "
            "WHERE organization_id = $1 AND is_active = TRUE ORDER BY name",
            org_id,
        )
        return [_row_to_supplier(r) for r in rows]

    async def search_for_org(
        self,
        org_id: str,
        *,
        search: Optional[str] = None,
        category_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Supplier]:
        """Org-scoped supplier search/filter over real columns (read-only).

        ``status`` filters the real ``is_active`` flag (``active``/``inactive``);
        ``category_id`` filters ``supplier_category_id``; ``search`` is an
        ILIKE match on name / contact_email / contact_name.
        """
        query = (
            f"SELECT {_SUPPLIER_COLUMNS} FROM public.suppliers "
            "WHERE organization_id = $1"
        )
        args: list[Any] = [org_id]
        if status == "active":
            query += " AND is_active = TRUE"
        elif status == "inactive":
            query += " AND is_active = FALSE"
        if category_id is not None:
            args.append(category_id)
            query += f" AND supplier_category_id = ${len(args)}"
        if search:
            args.append(f"%{search}%")
            query += (
                f" AND (name ILIKE ${len(args)} "
                f"OR contact_email ILIKE ${len(args)} "
                f"OR contact_name ILIKE ${len(args)})"
            )
        query += " ORDER BY name"
        query += f" LIMIT {int(limit)} OFFSET {int(offset)}"
        rows = await self._fetch_all(query, *args)
        return [_row_to_supplier(r) for r in rows]

    async def update(
        self,
        supplier_id: str,
        name: Optional[str],
        contact_email: Optional[str],
        is_active: Optional[bool],
    ) -> Optional[Supplier]:
        sets, args = ["updated_at = NOW()"], [supplier_id]
        if name is not None:
            sets.append(f"name = ${len(args) + 1}")
            args.append(name)
        if contact_email is not None:
            sets.append(f"contact_email = ${len(args) + 1}")
            args.append(contact_email)
        if is_active is not None:
            sets.append(f"is_active = ${len(args) + 1}")
            args.append(is_active)
        row = await self._fetch_one(
            f"UPDATE public.suppliers SET {', '.join(sets)} "
            f"WHERE id = $1 RETURNING {_SUPPLIER_COLUMNS}",
            *args,
        )
        return _row_to_supplier(row) if row is not None else None

    async def remove(self, supplier_id: str) -> None:
        await self._execute(
            "UPDATE public.suppliers SET is_active = FALSE WHERE id = $1",
            supplier_id,
        )

    async def save(self, entity: Supplier) -> Supplier:
        return entity

    async def delete(self, id: str) -> None:
        return None
