"""P17-C contractual-instrument repository (P17-IMPLEMENT-06).

The trusted data-access layer for
``public.contractual_instruments`` / ``public.instrument_allocations``.

Why this module exists
----------------------
The P17-C schema and ``domain.contractual_instruments`` were implemented in
IMPLEMENT-MASTER-01, and IMPLEMENT-05 built the market-based Scope 2 calculation
on top of the domain. Neither had a repository, so the market-based HTTP path
failed closed: the only place an instrument could have come from was the request
body, and a **client-supplied organisation id must never decide an accounting
entitlement**.

Division of responsibility — this repository only retrieves and stores:

* **This module** loads rows and maps them to domain objects, and scopes every
  read by the caller's **authorized** organization.
* **The domain** (``domain.scope2`` / ``domain.contractual_instruments``) decides
  eligibility: active status, geography, vintage, method/energy compatibility and
  the DC-09 quantity rule.

No eligibility rule is duplicated here, and no organization identity is ever taken
from request input.

Tenant isolation is enforced twice over:

1. every read below is an explicit SQL predicate on ``organization_id``, so a row
   belonging to another tenant is **indistinguishable from a row that does not
   exist** — the stronger of the two failure modes, since it does not confirm the
   existence of another tenant's instrument;
2. the database independently forbids a cross-tenant claim: ``instrument_allocations``
   carries the composite foreign key
   ``(instrument_id, organization_id) -> contractual_instruments(id, organization_id)``.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from data.base import AbstractRepository
from domain.contractual_instruments import ContractualInstrument, InstrumentAllocation

#: Explicit column list — never ``SELECT *`` — so the mapping below is auditable
#: and a future column addition cannot silently change the projection.
_INSTRUMENT_COLUMNS = """
    id, organization_id, instrument_type, identifier, issuer, source_facility,
    geography, vintage_year, quantity, unit, valid_from, valid_to,
    retirement_status
"""

_ALLOCATION_COLUMNS = """
    id, organization_id, instrument_id, calculation_snapshot_id, emissions_log_id,
    allocated_quantity, allocated_unit, allocation_period_start,
    allocation_period_end, claim_reference
"""


def _row_to_instrument(row: Any) -> ContractualInstrument:
    """Map a ``contractual_instruments`` row to the domain object.

    Values are passed through unchanged: the domain's ``__post_init__`` validates
    instrument type and quantity, so a malformed row surfaces as a domain error
    rather than being silently coerced. The surrogate ``id`` is carried so the row
    can be correlated back when recording an allocation.
    """
    return ContractualInstrument(
        id=str(row["id"]),
        organization_id=str(row["organization_id"]),
        instrument_type=row["instrument_type"],
        identifier=row["identifier"],
        issuer=row["issuer"],
        source_facility=row["source_facility"],
        geography=row["geography"],
        vintage_year=row["vintage_year"],
        quantity=Decimal(row["quantity"]),
        unit=row["unit"],
        valid_from=row["valid_from"],
        valid_to=row["valid_to"],
        retirement_status=row["retirement_status"],
    )


def _row_to_allocation(row: Any) -> InstrumentAllocation:
    """Map an ``instrument_allocations`` row to the domain object."""
    return InstrumentAllocation(
        organization_id=str(row["organization_id"]),
        instrument_id=str(row["instrument_id"]),
        allocated_quantity=Decimal(row["allocated_quantity"]),
        allocated_unit=row["allocated_unit"],
        allocation_period_start=row["allocation_period_start"],
        allocation_period_end=row["allocation_period_end"],
        calculation_snapshot_id=(
            str(row["calculation_snapshot_id"])
            if row["calculation_snapshot_id"] is not None
            else None
        ),
        emissions_log_id=(
            str(row["emissions_log_id"])
            if row["emissions_log_id"] is not None
            else None
        ),
        claim_reference=row["claim_reference"],
    )


class ContractualInstrumentsRepository(AbstractRepository[ContractualInstrument]):
    """Trusted read/write surface for P17-C contractual instruments."""

    # ------------------------------------------------------------------
    # Instrument reads
    # ------------------------------------------------------------------
    async def get(self, id: str) -> Optional[ContractualInstrument]:
        """Return the instrument with ``id`` regardless of tenant.

        Internal/administrative use only. The API path must call
        :meth:`get_for_organization`, which is tenant-scoped.
        """
        row = await self._fetch_one(
            f"SELECT {_INSTRUMENT_COLUMNS} FROM public.contractual_instruments "
            "WHERE id = $1",
            id,
        )
        return _row_to_instrument(row) if row is not None else None

    async def get_for_organization(
        self, instrument_id: str, organization_id: str
    ) -> Optional[ContractualInstrument]:
        """Return the instrument **only when it belongs to ``organization_id``**.

        This is the trusted loader for the market-based Scope 2 path. The tenant
        predicate is part of the query, not a post-load assertion, so another
        tenant's instrument is indistinguishable from one that does not exist —
        the caller learns nothing about instruments it is not entitled to see.

        Returns ``None`` when the instrument does not exist **or** belongs to
        another tenant. Both cases fail closed at the call site.
        """
        row = await self._fetch_one(
            f"SELECT {_INSTRUMENT_COLUMNS} FROM public.contractual_instruments "
            "WHERE id = $1 AND organization_id = $2",
            instrument_id,
            organization_id,
        )
        return _row_to_instrument(row) if row is not None else None

    async def list_for_organization(
        self, organization_id: str
    ) -> list[ContractualInstrument]:
        """Every instrument claimed by the organization, deterministically ordered."""
        rows = await self._fetch_all(
            f"SELECT {_INSTRUMENT_COLUMNS} FROM public.contractual_instruments "
            "WHERE organization_id = $1 ORDER BY identifier, id",
            organization_id,
        )
        return [_row_to_instrument(r) for r in rows]

    # ------------------------------------------------------------------
    # Allocation reads
    # ------------------------------------------------------------------
    async def list_allocations(
        self, instrument_id: str, organization_id: str
    ) -> list[InstrumentAllocation]:
        """Allocations already recorded against this instrument for this tenant.

        Tenant-scoped on both ``instrument_id`` and ``organization_id``: a
        cross-tenant or wrong-instrument allocation can never be loaded into the
        DC-09 sum, so the quantity guard cannot be defeated by supplying a foreign
        instrument reference. The database's composite foreign key enforces the
        same invariant independently.
        """
        rows = await self._fetch_all(
            f"SELECT {_ALLOCATION_COLUMNS} FROM public.instrument_allocations "
            "WHERE instrument_id = $1 AND organization_id = $2 "
            "ORDER BY allocation_period_start, id",
            instrument_id,
            organization_id,
        )
        return [_row_to_allocation(r) for r in rows]

    async def find_allocation_for_request(
        self,
        *,
        instrument_id: str,
        organization_id: str,
        period_start: Any,
        period_end: Any,
        request_id: str,
    ) -> Optional[str]:
        """Return the id of an allocation already recording this request.

        The idempotency anchor is the **calculation request identity**
        (``calculation_snapshots.request_id``), not the snapshot id: a re-run of
        an identical request produces a new snapshot id, so keying on the snapshot
        alone would let the same claim be recorded twice.
        """
        row = await self._fetch_one(
            """
            SELECT a.id
              FROM public.instrument_allocations a
              JOIN public.calculation_snapshots s ON s.id = a.calculation_snapshot_id
             WHERE a.instrument_id = $1
               AND a.organization_id = $2
               AND a.allocation_period_start = $3
               AND a.allocation_period_end = $4
               AND s.request_id = $5
             LIMIT 1
            """,
            instrument_id,
            organization_id,
            period_start,
            period_end,
            request_id,
        )
        return str(row["id"]) if row is not None else None

    # ------------------------------------------------------------------
    # Allocation write
    # ------------------------------------------------------------------
    async def record_allocation(
        self, allocation: InstrumentAllocation
    ) -> Optional[str]:
        """Record the claim, idempotently. Returns the new id, or ``None``.

        ``None`` means an allocation for this instrument, period and snapshot was
        already recorded, so nothing new was written — the caller must not treat
        that as a new claim.

        The insert happens **after** the calculation has been persisted, so
        ``calculation_snapshot_id`` always references a real snapshot (the FK is
        ``ON DELETE RESTRICT``). DC-09 remains the authority on quantity: this
        method records what the service already validated and does not itself
        decide whether the claim is permitted.
        """
        row = await self._fetch_one(
            """
            INSERT INTO public.instrument_allocations (
                organization_id, instrument_id, calculation_snapshot_id,
                emissions_log_id, allocated_quantity, allocated_unit,
                allocation_period_start, allocation_period_end, claim_reference
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT ON CONSTRAINT instrument_allocations_unique DO NOTHING
            RETURNING id
            """,
            allocation.organization_id,
            allocation.instrument_id,
            allocation.calculation_snapshot_id,
            allocation.emissions_log_id,
            allocation.allocated_quantity,
            allocation.allocated_unit,
            allocation.allocation_period_start,
            allocation.allocation_period_end,
            allocation.claim_reference,
        )
        return str(row["id"]) if row is not None else None

    # ------------------------------------------------------------------
    # AbstractRepository
    # ------------------------------------------------------------------
    async def save(self, entity: ContractualInstrument) -> ContractualInstrument:
        """Upsert an instrument by id and return the stored state."""
        if entity.id is None:
            raise ValueError("an instrument must carry its id to be saved")
        row = await self._fetch_one(
            f"""
            INSERT INTO public.contractual_instruments (
                id, organization_id, instrument_type, identifier, issuer,
                source_facility, geography, vintage_year, quantity, unit,
                valid_from, valid_to, retirement_status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT (id) DO UPDATE SET
                instrument_type = EXCLUDED.instrument_type,
                identifier = EXCLUDED.identifier,
                issuer = EXCLUDED.issuer,
                source_facility = EXCLUDED.source_facility,
                geography = EXCLUDED.geography,
                vintage_year = EXCLUDED.vintage_year,
                quantity = EXCLUDED.quantity,
                unit = EXCLUDED.unit,
                valid_from = EXCLUDED.valid_from,
                valid_to = EXCLUDED.valid_to,
                retirement_status = EXCLUDED.retirement_status,
                updated_at = NOW()
            RETURNING {_INSTRUMENT_COLUMNS}
            """,
            entity.id,
            entity.organization_id,
            entity.instrument_type,
            entity.identifier,
            entity.issuer,
            entity.source_facility,
            entity.geography,
            entity.vintage_year,
            entity.quantity,
            entity.unit,
            entity.valid_from,
            entity.valid_to,
            entity.retirement_status,
        )
        if row is None:
            raise RuntimeError("contractual instruments upsert returned no row")
        return _row_to_instrument(row)

    async def delete(self, id: str) -> None:
        """Refuse deletion: an instrument is accounting evidence.

        A claimed instrument backs a market-based figure. Deleting it would leave
        a persisted emissions result whose claim can no longer be evidenced, so
        removal is not an application operation — an instrument is retired by
        setting ``retirement_status``, not by deleting the row.
        """
        raise NotImplementedError(
            "contractual instruments are accounting evidence and must not be "
            "deleted; retire the instrument instead"
        )
