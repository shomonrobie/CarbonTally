"""P17-IMPLEMENT-06 — contractual instrument repository (trusted data access).

Asserts the properties that make this repository trustworthy:

* every tenant-scoped read carries the ``organization_id`` predicate **in SQL**,
  so a foreign instrument is indistinguishable from an absent one;
* row mapping preserves database values exactly;
* a missing / cross-tenant instrument fails closed (``None``);
* the allocation write is idempotent and never decides DC-09 itself;
* an instrument cannot be deleted through the application.

The pool is a recording stand-in for asyncpg (as in the existing repository
tests, e.g. ``test_i4_repository_sql_and_jsonb.py``); no database is opened.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional

import pytest

from data.contractual_instruments import (
    ContractualInstrumentsRepository,
    _row_to_allocation,
    _row_to_instrument,
)
from domain.contractual_instruments import (
    INSTRUMENT_TYPES,
    ContractualInstrument,
    InstrumentAllocation,
)

_ORG = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_OTHER = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
_INSTRUMENT_ID = "11111111-1111-4111-8111-111111111111"
_SNAPSHOT_ID = "22222222-2222-4222-8222-222222222222"


class _FakeConn:
    def __init__(self, one: Any = None, many: Optional[list[Any]] = None) -> None:
        self._one = one
        self._many = many if many is not None else []
        self.calls: list[tuple[str, tuple]] = []

    async def fetchrow(self, query: str, *args: Any) -> Any:
        self.calls.append((query, args))
        return self._one

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        self.calls.append((query, args))
        return self._many


class _Acquire:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    async def __aenter__(self) -> _FakeConn:
        return self._conn

    async def __aexit__(self, *exc: Any) -> bool:
        return False


class _FakePool:
    def __init__(self, one: Any = None, many: Optional[list[Any]] = None) -> None:
        self.conn = _FakeConn(one, many)

    def acquire(self) -> _Acquire:
        return _Acquire(self.conn)


def _instrument_row(**over: Any) -> dict:
    row = {
        "id": _INSTRUMENT_ID,
        "organization_id": _ORG,
        "instrument_type": INSTRUMENT_TYPES[0],
        "identifier": "GO-2025-0001",
        "issuer": "Green Issuer",
        "source_facility": "Northwind Wind Farm",
        "geography": "GB",
        "vintage_year": 2025,
        "quantity": Decimal("1000"),
        "unit": "kWh",
        "valid_from": date(2025, 1, 1),
        "valid_to": date(2025, 12, 31),
        "retirement_status": "active",
    }
    row.update(over)
    return row


def _allocation_row(**over: Any) -> dict:
    row = {
        "id": "33333333-3333-4333-8333-333333333333",
        "organization_id": _ORG,
        "instrument_id": _INSTRUMENT_ID,
        "calculation_snapshot_id": _SNAPSHOT_ID,
        "emissions_log_id": None,
        "allocated_quantity": Decimal("100"),
        "allocated_unit": "kWh",
        "allocation_period_start": date(2025, 6, 1),
        "allocation_period_end": date(2025, 6, 1),
        "claim_reference": "scope2:req-1",
    }
    row.update(over)
    return row


def _allocation(**over: Any) -> InstrumentAllocation:
    base = dict(
        organization_id=_ORG,
        instrument_id=_INSTRUMENT_ID,
        allocated_quantity=Decimal("100"),
        allocated_unit="kWh",
        allocation_period_start=date(2025, 6, 1),
        allocation_period_end=date(2025, 6, 1),
        calculation_snapshot_id=_SNAPSHOT_ID,
    )
    base.update(over)
    return InstrumentAllocation(**base)


# ---------------------------------------------------------------------------
# Row mapping — database values preserved exactly
# ---------------------------------------------------------------------------
def test_row_mapping_preserves_database_values() -> None:
    instrument = _row_to_instrument(_instrument_row())
    assert instrument.id == _INSTRUMENT_ID
    assert instrument.organization_id == _ORG
    assert instrument.identifier == "GO-2025-0001"
    assert instrument.geography == "GB"
    assert instrument.quantity == Decimal("1000")
    assert instrument.unit == "kWh"
    assert instrument.vintage_year == 2025
    assert instrument.retirement_status == "active"
    assert instrument.valid_from == date(2025, 1, 1)
    assert instrument.valid_to == date(2025, 12, 31)


def test_allocation_row_mapping_preserves_values_and_null_log_id() -> None:
    allocation = _row_to_allocation(_allocation_row())
    assert allocation.organization_id == _ORG
    assert allocation.instrument_id == _INSTRUMENT_ID
    assert allocation.calculation_snapshot_id == _SNAPSHOT_ID
    assert allocation.emissions_log_id is None
    assert allocation.allocated_quantity == Decimal("100")
    assert allocation.claim_reference == "scope2:req-1"


# ---------------------------------------------------------------------------
# Tenant scoping — the predicate is in SQL, not a post-load assertion
# ---------------------------------------------------------------------------
async def test_get_for_organization_scopes_the_query_by_tenant() -> None:
    pool = _FakePool(one=_instrument_row())
    repo = ContractualInstrumentsRepository(pool)  # type: ignore[arg-type]
    found = await repo.get_for_organization(_INSTRUMENT_ID, _ORG)
    assert found is not None
    query, args = pool.conn.calls[-1]
    assert "organization_id = $2" in query, "tenant predicate missing from SQL"
    assert args == (_INSTRUMENT_ID, _ORG)


async def test_get_for_organization_is_none_when_the_row_is_absent() -> None:
    """Absent and cross-tenant are the same outcome: fail closed."""
    pool = _FakePool(one=None)
    repo = ContractualInstrumentsRepository(pool)  # type: ignore[arg-type]
    assert await repo.get_for_organization(_INSTRUMENT_ID, _OTHER) is None
    query, args = pool.conn.calls[-1]
    assert "AND organization_id = $2" in query
    assert args[1] == _OTHER


async def test_list_allocations_scopes_by_instrument_and_tenant() -> None:
    pool = _FakePool(many=[_allocation_row()])
    repo = ContractualInstrumentsRepository(pool)  # type: ignore[arg-type]
    allocations = await repo.list_allocations(_INSTRUMENT_ID, _ORG)
    assert len(allocations) == 1
    query, args = pool.conn.calls[-1]
    assert "instrument_id = $1 AND organization_id = $2" in query
    assert args == (_INSTRUMENT_ID, _ORG)


# ---------------------------------------------------------------------------
# Allocation write — idempotent, never decides DC-09 itself
# ---------------------------------------------------------------------------
async def test_record_allocation_is_idempotent_via_on_conflict_do_nothing() -> None:
    pool = _FakePool(one={"id": "44444444-4444-4444-8444-444444444444"})
    repo = ContractualInstrumentsRepository(pool)  # type: ignore[arg-type]
    new_id = await repo.record_allocation(_allocation())
    assert new_id == "44444444-4444-4444-8444-444444444444"
    query, args = pool.conn.calls[-1]
    assert "ON CONFLICT ON CONSTRAINT instrument_allocations_unique" in query
    assert "DO NOTHING" in query
    assert args[0] == _ORG and args[1] == _INSTRUMENT_ID


async def test_record_allocation_returns_none_when_already_recorded() -> None:
    """No row returned by ``DO NOTHING`` means the claim already existed."""
    pool = _FakePool(one=None)
    repo = ContractualInstrumentsRepository(pool)  # type: ignore[arg-type]
    assert await repo.record_allocation(_allocation()) is None


async def test_find_allocation_for_request_keys_on_the_request_identity() -> None:
    pool = _FakePool(one={"id": "55555555-5555-4555-8555-555555555555"})
    repo = ContractualInstrumentsRepository(pool)  # type: ignore[arg-type]
    found = await repo.find_allocation_for_request(
        instrument_id=_INSTRUMENT_ID,
        organization_id=_ORG,
        period_start=date(2025, 6, 1),
        period_end=date(2025, 6, 1),
        request_id="req-1",
    )
    assert found == "55555555-5555-4555-8555-555555555555"
    query, args = pool.conn.calls[-1]
    assert "s.request_id = $5" in query
    assert args == (_INSTRUMENT_ID, _ORG, date(2025, 6, 1), date(2025, 6, 1), "req-1")


# ---------------------------------------------------------------------------
# Provenance: an instrument is evidence, not a deletable record
# ---------------------------------------------------------------------------
async def test_delete_is_refused() -> None:
    repo = ContractualInstrumentsRepository(_FakePool())  # type: ignore[arg-type]
    with pytest.raises(NotImplementedError):
        await repo.delete(_INSTRUMENT_ID)


async def test_save_requires_the_row_identity() -> None:
    repo = ContractualInstrumentsRepository(_FakePool())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must carry its id"):
        await repo.save(
            ContractualInstrument(
                organization_id=_ORG,
                instrument_type=INSTRUMENT_TYPES[0],
                identifier="GO-1",
                geography="GB",
                quantity=Decimal("1000"),
                unit="kWh",
            )
        )


def test_domain_instrument_id_defaults_to_none_for_existing_callers() -> None:
    """The additive ``id`` field must not disturb pre-existing construction."""
    instrument = ContractualInstrument(
        organization_id=_ORG,
        instrument_type=INSTRUMENT_TYPES[0],
        identifier="GO-1",
        geography="GB",
        quantity=Decimal("1000"),
        unit="kWh",
    )
    assert instrument.id is None
