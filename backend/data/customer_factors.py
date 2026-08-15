"""Customer-factors repository (V3, ADR-V3-002 — DECIDED).

Persistence for the V3M-3 ``customer_factors`` table. Reads are org-scoped and
respect the V3M-3 RLS surface at the database level (the repository itself uses
the service-role pool and therefore always filters by ``organization_id`` in
code — never across tenants).

Approval authority (D-cf-3) is an API/service concern; this repository only
persists status transitions.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.customer_factor import CustomerFactor

_FACTOR_COLUMNS = """
    id, organization_id, name, description, activity_type, co2e_multiplier,
    unit, scope, country, reporting_year, factor_source, status, version,
    metadata, created_at, updated_at, created_by, updated_by
"""




def _row_to_customer_factor(row: Any) -> CustomerFactor:
    """Map a ``customer_factors`` row to the domain object (V3M-3)."""
    r = dict(row)
    return CustomerFactor(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        name=str(r["name"]),
        description=str(r["description"]) if r.get("description") else None,
        activity_type=str(r["activity_type"]),
        co2e_multiplier=Decimal(str(r["co2e_multiplier"])),
        unit=str(r["unit"]) if r.get("unit") else None,
        scope=str(r["scope"]) if r.get("scope") else None,
        country=str(r["country"]),
        reporting_year=int(r["reporting_year"]),
        factor_source=str(r["factor_source"]),
        status=str(r["status"]),
        version=int(r["version"]),
        metadata=loads_jsonb(r.get("metadata")) or {},
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
        created_by=str(r["created_by"]) if r.get("created_by") else None,
        updated_by=str(r["updated_by"]) if r.get("updated_by") else None,
    )


class CustomerFactorsRepository(AbstractRepository[CustomerFactor]):
    """Org-scoped customer-owned factor persistence."""

    async def get(self, id: str) -> Optional[CustomerFactor]:
        """Return the customer factor with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_FACTOR_COLUMNS} FROM public.customer_factors WHERE id = $1",
            id,
        )
        return _row_to_customer_factor(row) if row is not None else None

    async def get_org_factors(self, org_id: str) -> list[CustomerFactor]:
        """Return every customer factor for ``org_id``, newest version last."""
        rows = await self._fetch_all(
            f"SELECT {_FACTOR_COLUMNS} FROM public.customer_factors "
            "WHERE organization_id = $1 ORDER BY activity_type, version, id",
            org_id,
        )
        return [_row_to_customer_factor(r) for r in rows]

    async def get_active_for_org(self, org_id: str) -> list[CustomerFactor]:
        """Return ACTIVE customer factors for ``org_id`` (matching candidates).

        D-cf-5: only approved (``status = 'active'``) customer factors are
        eligible to be matched ahead of CarbonTally-managed factors.
        """
        rows = await self._fetch_all(
            f"SELECT {_FACTOR_COLUMNS} FROM public.customer_factors "
            "WHERE organization_id = $1 AND status = 'active' "
            "ORDER BY activity_type, version, id",
            org_id,
        )
        return [_row_to_customer_factor(r) for r in rows]

    async def save(self, entity: CustomerFactor) -> CustomerFactor:
        """Insert or update a customer factor (version family respected)."""
        now = datetime.now(timezone.utc)
        row = await self._fetch_one(
            f"""
            INSERT INTO public.customer_factors (
                id, organization_id, name, description, activity_type,
                co2e_multiplier, unit, scope, country, reporting_year,
                factor_source, status, version, metadata,
                created_at, updated_at, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                      $14::jsonb, $15, $16, $17, $18)
            ON CONFLICT (id)
            DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                activity_type = EXCLUDED.activity_type,
                co2e_multiplier = EXCLUDED.co2e_multiplier,
                unit = EXCLUDED.unit,
                scope = EXCLUDED.scope,
                country = EXCLUDED.country,
                reporting_year = EXCLUDED.reporting_year,
                status = EXCLUDED.status,
                version = EXCLUDED.version,
                metadata = EXCLUDED.metadata,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            RETURNING {_FACTOR_COLUMNS}
            """,
            entity.id,
            entity.organization_id,
            entity.name,
            entity.description,
            entity.activity_type,
            entity.co2e_multiplier,
            entity.unit,
            entity.scope,
            entity.country,
            entity.reporting_year,
            entity.factor_source,
            entity.status,
            entity.version,
            dumps_jsonb(entity.metadata),
            entity.created_at or now,
            now,
            entity.created_by,
            entity.updated_by,
        )
        if row is None:
            raise RuntimeError("customer factor upsert returned no row")
        return _row_to_customer_factor(row)

    async def update_status(
        self, id: str, status: str, *, updated_by: Optional[str] = None
    ) -> CustomerFactor:
        """Soft-deactivate / approve a customer factor (authority enforced by
        the API/service layer, mirroring D-cf-3)."""
        row = await self._fetch_one(
            f"""
            UPDATE public.customer_factors
            SET status = $2, updated_at = NOW(), updated_by = $3
            WHERE id = $1
            RETURNING {_FACTOR_COLUMNS}
            """,
            id,
            status,
            updated_by,
        )
        if row is None:
            raise RuntimeError(f"customer factor {id!r} does not exist")
        return _row_to_customer_factor(row)

    async def delete(self, id: str) -> None:
        """Hard-delete is NOT permitted for customer factors (V3M-3 has no
        DELETE policy; soft-deactivate via status)."""
        raise NotImplementedError(
            "customer_factors are never hard-deleted; use update_status"
        )


