"""P17-IMPLEMENT-04 — canonical accounting write pipeline (engine level).

Exercises the REAL pipeline: ``CalculationEngine.calculate()`` →
``sink.save_snapshot`` → ``_persist_log`` → ``sink.create``/``sink.save``.

These are not helper-only tests. The sink is an in-memory stand-in for the
repository (as in the existing engine tests), but the code under test is the
actual production engine and the actual accounting-dimension validation, so the
guarantees asserted here are the ones the next Scope 2 task will inherit.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Optional

import pytest

from core.exceptions import (
    BoundaryAmbiguityError,
    Scope2MethodRequiredError,
    Scope3CategoryRequiredError,
)
from domain.accounting_dimensions import AccountingDimensions
from domain.calculation import CalculationSnapshot, EmissionLog
from domain.factor import EmissionFactor
from engines.calculation import CalculationEngine, CalculationRequest

_ACTIVITY = "Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]"
_ORG = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_FIRM = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
_OTHER = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def make_factor(**kwargs: Any) -> EmissionFactor:
    return EmissionFactor(
        id=str(kwargs.get("id") or f"f-{uuid.uuid4().hex[:12]}"),
        reporting_year=int(kwargs.get("year", 2025)),
        activity_type=str(kwargs.get("activity_type") or _ACTIVITY),
        co2e_multiplier=Decimal(str(kwargs.get("multiplier") or "0.18400")),
        unit=str(kwargs.get("unit") or "kWh"),
        scope=str(kwargs.get("scope") or "Scope 1"),
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
        provider_key="defra",
        import_batch_id=None,
        natural_key=("2025", _ACTIVITY, "GB", "kWh", "Scope 1"),
    )


class _RecordingSink:
    """In-memory ``CalculationSink`` that retains the objects it was handed."""

    def __init__(self) -> None:
        self.snapshots: list[CalculationSnapshot] = []
        self.created: list[EmissionLog] = []
        self.saved: list[EmissionLog] = []

    async def save_snapshot(self, snapshot: CalculationSnapshot, **kwargs: Any):
        self.snapshots.append(snapshot)
        return snapshot

    async def create(
        self,
        org_id: str,
        factor_id: Optional[str],
        quantity: Decimal,
        unit: str,
        scope: Optional[str],
        date: Any,
        asset_id: Optional[str],
        facility_id: Optional[str],
        snapshot_id: str,
        supplier_id: Optional[str] = None,
        accounting_dimensions: Optional[AccountingDimensions] = None,
    ) -> EmissionLog:
        log = EmissionLog(
            id=f"log-{len(self.created)}",
            organization_id=org_id,
            factor_id=factor_id,
            quantity=quantity,
            date=date,
            unit=unit,
            scope=scope,
            asset_id=asset_id,
            facility_id=facility_id,
            snapshot_id=snapshot_id,
        )
        self.created.append(log)
        return log

    async def save(self, entity: EmissionLog) -> EmissionLog:
        self.saved.append(entity)
        return entity


def make_request(**kwargs: Any) -> CalculationRequest:
    def take(name: str, default: Any) -> Any:
        return kwargs.pop(name, default)

    return CalculationRequest(
        match_request_id=str(take("match_request_id", "match-1")),
        organization_id=str(take("organization_id", _ORG)),
        factor=take("factor", make_factor()),
        quantity=Decimal(str(take("quantity", "100"))),
        quantity_unit=str(take("quantity_unit", "kWh")),
        date=take("date", date(2025, 6, 1)),
        reporting_year=int(take("year", 2025)),
        activity=str(take("activity", "Natural gas")),
        activity_type=str(take("activity_type", _ACTIVITY)),
        scope=take("scope", None),
        accounting_dimensions=take("accounting_dimensions", None),
    )


# ---------------------------------------------------------------------------
# 1. Canonical write — dimensions reach the snapshot AND the log, identically
# ---------------------------------------------------------------------------
async def test_scope2_write_persists_identity_on_snapshot_and_log() -> None:
    sink = _RecordingSink()
    engine = CalculationEngine(sink)  # type: ignore[arg-type]
    dims = AccountingDimensions(
        scope2_method="LOCATION_BASED",
        energy_type="electricity",
        data_quality="primary_supplier",
        performed_by_organization_id=_FIRM,
        acting_for_organization_id=_ORG,
    )
    result = await engine.calculate(
        make_request(scope="Scope 2", accounting_dimensions=dims)
    )

    assert sink.snapshots and sink.saved, "canonical write did not run"
    snapshot = sink.snapshots[-1]
    log = sink.saved[-1]

    # The snapshot carries the identity...
    assert snapshot.accounting_dimensions is not None
    assert snapshot.accounting_dimensions.scope2_method == "LOCATION_BASED"
    assert snapshot.accounting_dimensions.energy_type == "electricity"
    assert snapshot.accounting_dimensions.data_quality == "primary_supplier"
    assert snapshot.accounting_dimensions.acting_for_organization_id == _ORG
    assert snapshot.accounting_dimensions.performed_by_organization_id == _FIRM

    # ...and the emissions log carries the SAME identity (Phase 4 / Phase 11).
    assert (
        log.accounting_dimensions.as_columns()
        == snapshot.accounting_dimensions.as_columns()
    )

    # The log is linked to the authoritative snapshot, and they agree on owner.
    assert log.snapshot_id == snapshot.id
    assert log.organization_id == snapshot.organization_id == _ORG

    # The returned result exposes the stored snapshot.
    assert result.snapshot.accounting_dimensions.scope2_method == "LOCATION_BASED"


async def test_scope3_write_persists_category_on_snapshot_and_log() -> None:
    sink = _RecordingSink()
    engine = CalculationEngine(sink)  # type: ignore[arg-type]
    dims = AccountingDimensions(
        scope3_category=3,
        acting_for_organization_id=_ORG,
        performed_by_organization_id=_ORG,
    )
    await engine.calculate(make_request(scope="Scope 3", accounting_dimensions=dims))
    snapshot = sink.snapshots[-1]
    log = sink.saved[-1]
    assert snapshot.accounting_dimensions.scope3_category == 3
    assert log.accounting_dimensions.scope3_category == 3
    assert (
        log.accounting_dimensions.as_columns()
        == snapshot.accounting_dimensions.as_columns()
    )


async def test_dc04_transport_boundary_is_persisted_for_category_4() -> None:
    sink = _RecordingSink()
    engine = CalculationEngine(sink)  # type: ignore[arg-type]
    dims = AccountingDimensions(scope3_category=4, transport_boundary="upstream")
    await engine.calculate(make_request(scope="Scope 3", accounting_dimensions=dims))
    assert sink.snapshots[-1].accounting_dimensions.transport_boundary == "upstream"


# ---------------------------------------------------------------------------
# 2. Refusal happens BEFORE any write (no partial accounting result)
# ---------------------------------------------------------------------------
async def test_scope2_without_method_is_refused_with_nothing_written() -> None:
    sink = _RecordingSink()
    engine = CalculationEngine(sink)  # type: ignore[arg-type]
    with pytest.raises(Scope2MethodRequiredError):
        await engine.calculate(make_request(scope="Scope 2"))
    assert sink.snapshots == []
    assert sink.created == []
    assert sink.saved == []


async def test_scope3_without_category_is_refused_with_nothing_written() -> None:
    sink = _RecordingSink()
    engine = CalculationEngine(sink)  # type: ignore[arg-type]
    with pytest.raises(Scope3CategoryRequiredError):
        await engine.calculate(make_request(scope="Scope 3"))
    assert sink.snapshots == []
    assert sink.saved == []


async def test_scope1_may_not_carry_scope2_method() -> None:
    sink = _RecordingSink()
    engine = CalculationEngine(sink)  # type: ignore[arg-type]
    with pytest.raises(Exception) as excinfo:
        await engine.calculate(
            make_request(
                scope="Scope 1",
                accounting_dimensions=AccountingDimensions(
                    scope2_method="MARKET_BASED"
                ),
            )
        )
    assert excinfo.value.code == "ACCOUNTING_DIMENSION_INVALID"
    assert sink.snapshots == []


async def test_dc04_transport_boundary_with_wrong_category_is_refused() -> None:
    sink = _RecordingSink()
    engine = CalculationEngine(sink)  # type: ignore[arg-type]
    with pytest.raises(BoundaryAmbiguityError):
        await engine.calculate(
            make_request(
                scope="Scope 3",
                accounting_dimensions=AccountingDimensions(
                    scope3_category=1, transport_boundary="upstream"
                ),
            )
        )
    assert sink.snapshots == []


async def test_dc05_waste_origin_with_wrong_category_is_refused() -> None:
    sink = _RecordingSink()
    engine = CalculationEngine(sink)  # type: ignore[arg-type]
    with pytest.raises(BoundaryAmbiguityError):
        await engine.calculate(
            make_request(
                scope="Scope 3",
                accounting_dimensions=AccountingDimensions(
                    scope3_category=4, waste_origin="operations"
                ),
            )
        )
    assert sink.snapshots == []


# ---------------------------------------------------------------------------
# 3. P16 preservation — no dimensions means NULL, and hashes are unchanged
# ---------------------------------------------------------------------------
async def test_scope1_without_dimensions_still_calculates() -> None:
    sink = _RecordingSink()
    engine = CalculationEngine(sink)  # type: ignore[arg-type]
    await engine.calculate(make_request(scope="Scope 1"))
    assert sink.snapshots[-1].accounting_dimensions is None
    assert sink.saved[-1].accounting_dimensions is None


async def test_content_hash_is_identical_with_and_without_dimensions() -> None:
    """P16 snapshot identity/idempotency must not depend on P17 dimensions."""
    plain = _RecordingSink()
    with_dims = _RecordingSink()
    # The SAME factor instance: P16 snapshot identity must depend on the
    # calculation inputs, and P17 dimensions must not be among them.
    factor = make_factor()

    await CalculationEngine(plain).calculate(  # type: ignore[arg-type]
        make_request(scope="Scope 1", match_request_id="match-same", factor=factor)
    )
    await CalculationEngine(with_dims).calculate(  # type: ignore[arg-type]
        make_request(
            scope="Scope 1",
            match_request_id="match-same",
            factor=factor,
            accounting_dimensions=AccountingDimensions(data_quality="modelled"),
        )
    )
    assert (
        plain.snapshots[-1].content_hash == with_dims.snapshots[-1].content_hash
    ), "P17 dimensions must not change the P16 content hash"


async def test_unknown_dimensions_are_left_null_never_guessed() -> None:
    sink = _RecordingSink()
    engine = CalculationEngine(sink)  # type: ignore[arg-type]
    await engine.calculate(
        make_request(
            scope="Scope 3",
            accounting_dimensions=AccountingDimensions(scope3_category=11),
        )
    )
    columns = sink.snapshots[-1].accounting_dimensions.as_columns()
    # Only the supplied category is set; every other dimension stays NULL.
    assert columns["scope3_category"] == 11
    for name in (
        "scope2_method",
        "energy_type",
        "data_quality",
        "facility_id",
        "transport_boundary",
        "waste_origin",
        "source_snapshot_id",
        "performed_by_organization_id",
        "acting_for_organization_id",
    ):
        assert columns[name] is None, f"{name} was fabricated"


# ---------------------------------------------------------------------------
# 4. Cross-record consistency guard (Phase 4 / Phase 11)
# ---------------------------------------------------------------------------
def _snapshot(**over: Any) -> CalculationSnapshot:
    base: dict[str, Any] = dict(
        id="snap-1",
        match_request_id="match-1",
        organization_id=_ORG,
        factor_id=None,
        quantity=Decimal("1"),
        quantity_unit="kWh",
        co2e_multiplier=Decimal("1"),
        co2e_kg=Decimal("1"),
        scope="Scope 2",
        date=date(2025, 6, 1),
        reporting_year=2025,
        methodology="direct_multiply",
        algorithm_version="v1",
        created_at=date(2025, 6, 1),
    )
    base.update(over)
    return CalculationSnapshot(**base)


def _log(**over: Any) -> EmissionLog:
    base: dict[str, Any] = dict(
        id="log-1",
        organization_id=_ORG,
        factor_id=None,
        quantity=Decimal("1"),
        date=date(2025, 6, 1),
        snapshot_id="snap-1",
    )
    base.update(over)
    return EmissionLog(**base)


def test_log_attributed_to_a_different_owner_than_its_snapshot_is_refused() -> None:
    guard = CalculationEngine._assert_log_matches_snapshot
    with pytest.raises(ValueError, match="does not match snapshot organization"):
        guard(_snapshot(), _log(organization_id=_OTHER))


def test_log_with_a_different_acting_for_than_its_snapshot_is_refused() -> None:
    guard = CalculationEngine._assert_log_matches_snapshot
    snapshot = _snapshot(
        accounting_dimensions=AccountingDimensions(
            scope2_method="LOCATION_BASED", acting_for_organization_id=_ORG
        )
    )
    log = _log(
        accounting_dimensions=AccountingDimensions(
            scope2_method="LOCATION_BASED", acting_for_organization_id=_OTHER
        )
    )
    with pytest.raises(ValueError, match="acting_for_organization_id"):
        guard(snapshot, log)


def test_matching_log_and_snapshot_are_accepted() -> None:
    guard = CalculationEngine._assert_log_matches_snapshot
    dims = AccountingDimensions(
        scope2_method="MARKET_BASED",
        acting_for_organization_id=_ORG,
        performed_by_organization_id=_FIRM,
    )
    guard(_snapshot(accounting_dimensions=dims), _log(accounting_dimensions=dims))

