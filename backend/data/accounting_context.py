"""P17 accounting-context repository (acting-for persistence + CAMS dimensions).

Task: ``P17-IMPLEMENT-02-20260925-API-ACTING-FOR-WRITE-PATHS``.

Responsibilities, and deliberately nothing else: read the organisation summary
fields the accounting context needs; resolve an active organisation membership
role; read the Scope 3 category vocabulary; **persist acting-for attribution**
onto the P17 write-path carriers; read that attribution back; read the eight CAMS
dimensions for one calculation snapshot.

Design notes:

* **No new audit model.** Attribution is written onto the columns added by
  ``20261010000000_p17a``; the audit ledger remains ``AuditRepository`` /
  ``audit_trail``, which now carries the same two values.
* **Table names are never interpolated from caller input.** ``ACTING_FOR_CARRIERS``
  is a closed allowlist mapping a logical carrier name to physical column names,
  so an acting-for write cannot become an injection vector and cannot touch a
  table the architecture did not name.
* **Ownership is never written.** ``organization_id`` is never updated here —
  acting-for is context, and this repository can only set the context columns.
"""
from __future__ import annotations

from typing import Optional

from data.base import AbstractRepository

__all__ = [
    "ACTING_FOR_CARRIERS",
    "AccountingContextRepository",
    "STANDARD_ACTOR_COLUMN",
    "STANDARD_ACTING_FOR_COLUMN",
]

STANDARD_ACTOR_COLUMN = "actor_organization_id"
STANDARD_ACTING_FOR_COLUMN = "acting_for_organization_id"

#: The nine ARCH-04 §10.3 write-path carriers, mapped to their P17 columns.
#: ``owner`` is documented and is never written by this module. Keyed by a stable
#: LOGICAL name so the API never accepts a raw table name.
ACTING_FOR_CARRIERS: dict[str, dict[str, Optional[str]]] = {
    "calculation_snapshot": {
        "table": "calculation_snapshots",
        "owner": "organization_id",
        "actor": "performed_by_organization_id",
        "acting_for": STANDARD_ACTING_FOR_COLUMN,
    },
    "emissions_log": {
        "table": "emissions_logs",
        "owner": "organization_id",
        "actor": "performed_by_organization_id",
        "acting_for": STANDARD_ACTING_FOR_COLUMN,
    },
    "evidence_line_item": {
        "table": "evidence_line_items",
        "owner": "organization_id",
        "actor": "contributed_by_organization_id",
        "acting_for": STANDARD_ACTING_FOR_COLUMN,
    },
    "customer_document": {
        "table": "customer_documents",
        "owner": "organization_id",
        "actor": STANDARD_ACTOR_COLUMN,
        "acting_for": STANDARD_ACTING_FOR_COLUMN,
    },
    "supplier": {
        "table": "suppliers",
        "owner": "organization_id",
        "actor": STANDARD_ACTOR_COLUMN,
        "acting_for": STANDARD_ACTING_FOR_COLUMN,
    },
    "review_audit_trail": {
        "table": "review_audit_trail",
        "owner": None,
        "actor": STANDARD_ACTOR_COLUMN,
        "acting_for": STANDARD_ACTING_FOR_COLUMN,
    },
    "review_assignment_history": {
        "table": "review_assignment_history",
        "owner": None,
        "actor": STANDARD_ACTOR_COLUMN,
        "acting_for": STANDARD_ACTING_FOR_COLUMN,
    },
    "report_version": {
        "table": "report_versions",
        "owner": None,
        "actor": "prepared_by_organization_id",
        "acting_for": STANDARD_ACTING_FOR_COLUMN,
    },
    "audit_entry": {
        "table": "audit_trail",
        "owner": None,
        "actor": STANDARD_ACTOR_COLUMN,
        "acting_for": STANDARD_ACTING_FOR_COLUMN,
    },
}


class AccountingContextRepository(AbstractRepository[dict]):
    """Read/write surface for the P17 accounting context."""

    # ------------------------------------------------------------------
    # Organisation reads
    # ------------------------------------------------------------------
    async def get_organization_summary(self, organization_id: str) -> Optional[dict]:
        """Return the P17 organisation summary, or ``None`` when it is absent.

        ``organization_type`` is ``None`` for every pre-existing row; callers
        treat that as ``CUSTOMER`` (the migration's documented default), so no
        historical row changes meaning.
        """
        row = await self._fetch_one(
            """
            SELECT id, name, organization_type, consolidation_approach, is_active
              FROM public.organizations
             WHERE id = $1::uuid
             LIMIT 1
            """,
            organization_id,
        )
        if row is None:
            return None
        r = dict(row)
        return {
            "id": str(r["id"]),
            "name": r.get("name"),
            "organization_type": r.get("organization_type") or "CUSTOMER",
            "consolidation_approach": r.get("consolidation_approach"),
            "is_active": bool(r.get("is_active", True)),
        }

    async def list_active_member_roles(self, user_id: str) -> dict[str, str]:
        """Return ``{organization_id: role}`` for the user's ACTIVE memberships.

        Reuses ``organization_members`` (the existing authorisation surface) with
        the same active-membership predicate the RLS helper
        ``public.is_org_member`` uses. Membership is never inferred from any
        other column.
        """
        rows = await self._fetch_all(
            """
            SELECT organization_id, role
              FROM public.organization_members
             WHERE user_id = $1::uuid
               AND coalesce(is_active, true) = true
            """,
            user_id,
        )
        return {str(r["organization_id"]): (r.get("role") or "member") for r in rows}

    # ------------------------------------------------------------------
    # Reference data
    # ------------------------------------------------------------------
    async def list_scope3_categories(self) -> list[dict]:
        """Return the 15-category reference vocabulary, ordered by category."""
        rows = await self._fetch_all(
            """
            SELECT category, slug, name, is_downstream, description
              FROM public.scope3_categories
             ORDER BY category
            """
        )
        return [
            {
                "category": int(r["category"]),
                "slug": r["slug"],
                "name": r["name"],
                "is_downstream": bool(r["is_downstream"]),
                "description": r.get("description"),
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # CAMS dimensions
    # ------------------------------------------------------------------
    async def get_snapshot_dimensions(self, snapshot_id: str) -> Optional[dict]:
        """Return the eight CAMS dimensions persisted for one calculation snapshot."""
        row = await self._fetch_one(
            """
            SELECT id, organization_id, scope, scope2_method, scope3_category,
                   energy_type, data_quality, facility_id, transport_boundary,
                   waste_origin, source_snapshot_id, reportability_status,
                   performed_by_organization_id, acting_for_organization_id
              FROM public.calculation_snapshots
             WHERE id = $1::uuid
             LIMIT 1
            """,
            snapshot_id,
        )
        if row is None:
            return None
        r = dict(row)
        return {
            "calculation_snapshot_id": str(r["id"]),
            "organization_id": str(r["organization_id"]),
            "scope": r.get("scope"),
            "scope2_method": r.get("scope2_method"),
            "scope3_category": (
                int(r["scope3_category"]) if r.get("scope3_category") else None
            ),
            "energy_type": r.get("energy_type"),
            "data_quality": r.get("data_quality"),
            "facility_id": str(r["facility_id"]) if r.get("facility_id") else None,
            "transport_boundary": r.get("transport_boundary"),
            "waste_origin": r.get("waste_origin"),
            "source_snapshot_id": (
                str(r["source_snapshot_id"]) if r.get("source_snapshot_id") else None
            ),
            "reportability_status": r.get("reportability_status"),
            "performed_by_organization_id": (
                str(r["performed_by_organization_id"])
                if r.get("performed_by_organization_id")
                else None
            ),
            "acting_for_organization_id": (
                str(r["acting_for_organization_id"])
                if r.get("acting_for_organization_id")
                else None
            ),
        }

    # ------------------------------------------------------------------
    # Acting-for persistence
    # ------------------------------------------------------------------
    async def persist_acting_for(
        self,
        *,
        carrier: str,
        record_id: str,
        actor_organization_id: Optional[str],
        acting_for_organization_id: str,
    ) -> Optional[dict]:
        """Persist acting-for attribution on one write-path carrier.

        Returns the stored attribution, or ``None`` when no row matched (the
        caller turns that into a 404 rather than reporting a silent success).

        ``carrier`` must be a key of :data:`ACTING_FOR_CARRIERS`; the table and
        column names come from that allowlist, never from the caller.
        """
        spec = ACTING_FOR_CARRIERS.get(carrier)
        if spec is None:
            raise ValueError(f"unknown acting-for carrier: {carrier!r}")
        # Identifiers come from the closed allowlist above, so this f-string
        # cannot be influenced by request input.
        query = (
            f"UPDATE public.{spec['table']} "
            f"SET {spec['actor']} = NULLIF($2, '')::uuid, "
            f"    {spec['acting_for']} = NULLIF($3, '')::uuid "
            f"WHERE id = $1::uuid "
            f"RETURNING id, {spec['actor']} AS actor_organization_id, "
            f"          {spec['acting_for']} AS acting_for_organization_id"
        )
        row = await self._fetch_one(
            query, record_id, actor_organization_id, acting_for_organization_id
        )
        if row is None:
            return None
        r = dict(row)
        return {
            "carrier": carrier,
            "record_id": str(r["id"]),
            "actor_organization_id": (
                str(r["actor_organization_id"])
                if r.get("actor_organization_id")
                else None
            ),
            "acting_for_organization_id": (
                str(r["acting_for_organization_id"])
                if r.get("acting_for_organization_id")
                else None
            ),
        }

    async def get_acting_for_attribution(
        self, *, carrier: str, record_id: str
    ) -> Optional[dict]:
        """Read persisted acting-for attribution for one record.

        Also returns the OWNER column when the carrier has one, so a caller can
        see the distinction between the tenant that OWNS the data and the
        organisation the actor was operating FOR.
        """
        spec = ACTING_FOR_CARRIERS.get(carrier)
        if spec is None:
            raise ValueError(f"unknown acting-for carrier: {carrier!r}")
        owner_select = (
            f", {spec['owner']} AS owner_organization_id"
            if spec.get("owner")
            else ", NULL::uuid AS owner_organization_id"
        )
        row = await self._fetch_one(
            f"SELECT id, {spec['actor']} AS actor_organization_id, "
            f"       {spec['acting_for']} AS acting_for_organization_id"
            f"{owner_select} "
            f"  FROM public.{spec['table']} WHERE id = $1::uuid LIMIT 1",
            record_id,
        )
        if row is None:
            return None
        r = dict(row)
        return {
            "carrier": carrier,
            "record_id": str(r["id"]),
            "owner_organization_id": (
                str(r["owner_organization_id"])
                if r.get("owner_organization_id")
                else None
            ),
            "actor_organization_id": (
                str(r["actor_organization_id"])
                if r.get("actor_organization_id")
                else None
            ),
            "acting_for_organization_id": (
                str(r["acting_for_organization_id"])
                if r.get("acting_for_organization_id")
                else None
            ),
            "attribution_persisted": r.get("acting_for_organization_id") is not None,
        }

    # ------------------------------------------------------------------
    # AbstractRepository contract
    # ------------------------------------------------------------------
    async def get(self, id: str) -> Optional[dict]:
        """Return a carrier record's attribution by ``<carrier>:<record_id>``.

        Provided so the class honours the repository contract; the typed methods
        above are the intended surface.
        """
        carrier, _, record_id = id.partition(":")
        if not record_id:
            return None
        return await self.get_acting_for_attribution(
            carrier=carrier, record_id=record_id
        )

    async def save(self, entity: dict) -> dict:
        """Persist acting-for attribution from a mapping."""
        result = await self.persist_acting_for(
            carrier=str(entity["carrier"]),
            record_id=str(entity["record_id"]),
            actor_organization_id=entity.get("actor_organization_id"),
            acting_for_organization_id=str(entity["acting_for_organization_id"]),
        )
        if result is None:
            raise KeyError(f"no record for carrier {entity.get('carrier')!r}")
        return result

    async def delete(self, id: str) -> None:
        """Not supported: attribution is provenance and is never deleted.

        Acting-for is part of the audit record. Removing it would destroy the
        answer to "who was this operation performed for?", so deletion is
        deliberately unavailable rather than silently implemented.
        """
        raise NotImplementedError(
            "acting-for attribution is provenance and must not be deleted"
        )

