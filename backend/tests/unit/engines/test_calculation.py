"""Unit tests for engines.calculation."""
from __future__ import annotations

import dataclasses
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import pytest

from core.exceptions import UnitMismatchError, ValidationFailedError
from domain.audit import AuditEntry
from domain.calculation import (
    CalculationMethodology,
    CalculationSnapshot,
    EmissionLog,
)
from domain.factor import EmissionFactor
from domain.matching import MatchResult
from domain.workflow import CalculationCompleted, CalculationRequested, DomainEvent
from engines.calculation import (
    DEFAULT_ALGORITHM_VERSION,
    CalculationEngine,
    CalculationRequest,
)
from infra.event_bus import EventBus

_NATURAL_GAS = "Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]"


def make_factor(**kwargs: Any) -> EmissionFactor:
    return EmissionFactor(
        id=str(kwargs.get("id") or f"f-{uuid.uuid4().hex[:12]}"),
        reporting_year=int(kwargs.get("year", 2025)),
        activity_type=str(kwargs.get("activity_type") or _NATURAL_GAS),
        co2e_multiplier=Decimal(str(kwargs.get("multiplier") or "0.18400")),
        unit=str(kwargs.get("unit") or "kWh"),
        scope=str(kwargs.get("scope") or "Scope 1"),
        factor_source=str(kwargs.get("factor_source") or "DEFRA-DESNZ"),
        factor_set=str(kwargs.get("factor_set") or "DEFRA-2025"),
        country=str(kwargs.get("country") or "GB"),
        provider_key=str(kwargs.get("provider") or "defra"),
        import_batch_id=kwargs.get("import_batch_id"),
        natural_key=(
            "2025",
            str(kwargs.get("activity_type") or _NATURAL_GAS),
            "GB",
            "kWh",
            "Scope 1",
        ),
    )


def make_request(**kwargs: Any) -> CalculationRequest:
    def take(name: str, default: Any) -> Any:
        return kwargs.pop(name, default)

    return CalculationRequest(
        match_request_id=str(take("match_request_id", "match-1")),
        organization_id=str(take("organization_id", "org-1")),
        factor=take("factor", make_factor()),
        quantity=Decimal(str(take("quantity", "100"))),
        quantity_unit=str(take("quantity_unit", "kWh")),
        date=take("date", date(2025, 6, 1)),
        reporting_year=int(take("year", 2025)),
        activity=str(take("activity", "Natural gas")),
        activity_type=str(take("activity_type", _NATURAL_GAS)),
        scope=take("scope", None),
        methodology=str(take("methodology", "direct_multiply")),
        source_file=take("source_file", None),
        source_page=take("source_page", None),
        log_id=take("log_id", None),
        asset_id=take("asset_id", None),
        facility_id=take("facility_id", None),
    )


class _MemorySink:
    """In-memory CalculationSink for unit tests."""

    def __init__(self) -> None:
        self.snapshots: dict[str, CalculationSnapshot] = {}
        self.logs: dict[str, EmissionLog] = {}
        self.fail_snapshot = False

    async def save_snapshot(
        self,
        snapshot: CalculationSnapshot,
        *,
        activity: str,
        activity_type: str,
        factor_source: Optional[str] = None,
        factor_set: Optional[str] = None,
        import_batch_id: Optional[str] = None,
        calculated_by: Optional[str] = None,
    ) -> CalculationSnapshot:
        if self.fail_snapshot:
            raise RuntimeError("snapshot persistence failed")
        stored = dataclasses.replace(snapshot)
        self.snapshots[stored.id] = stored
        return stored

    async def create(
        self,
        org_id: str,
        factor_id: str,
        quantity: Decimal,
        unit: str,
        scope: Optional[str],
        date: date,
        asset_id: Optional[str],
        facility_id: Optional[str],
        snapshot_id: str,
    ) -> EmissionLog:
        log = EmissionLog(
            id=f"log-{snapshot_id}",
            organization_id=org_id,
            factor_id=factor_id,
            quantity=quantity,
            date=date,
            unit=unit,
            scope=scope,
            asset_id=asset_id,
            facility_id=facility_id,
            snapshot_id=snapshot_id,
            calculated_kg_co2e=Decimal("0"),
        )
        self.logs[log.id] = log
        return log

    async def save(self, entity: EmissionLog) -> EmissionLog:
        self.logs[entity.id] = entity
        return entity


class _AuditSink:
    """In-memory audit sink recording ``log_action`` calls."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    async def log_action(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        correlation_id: str,
        actor: Optional[str] = None,
        changed_fields: Optional[dict[str, Any]] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        before: Any = None,
        after: Any = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor or "system",
            occurred_at=datetime.now(timezone.utc),
            changed_fields=dict(changed_fields or {}),
            reason=reason,
            ip_address=ip_address,
            before=before,
            after=after,
        )
        self.entries.append(entry)
        return entry


class TestCalculationRequest:
    def test_constructs(self) -> None:
        request = make_request()
        assert request.match_request_id == "match-1"
        assert request.methodology == "direct_multiply"

    def test_default_methodology_is_direct_multiply(self) -> None:
        assert make_request().methodology == "direct_multiply"

    def test_rejects_empty_match_request_id(self) -> None:
        with pytest.raises(ValueError, match="match_request_id"):
            make_request(match_request_id="")

    def test_rejects_empty_organization(self) -> None:
        with pytest.raises(ValueError, match="organization_id"):
            make_request(organization_id="")

    def test_rejects_negative_quantity(self) -> None:
        with pytest.raises(ValueError, match="quantity"):
            make_request(quantity="-1")

    def test_rejects_empty_unit(self) -> None:
        with pytest.raises(ValueError, match="quantity_unit"):
            make_request(quantity_unit="")

    def test_rejects_implausible_year(self) -> None:
        with pytest.raises(ValueError, match="reporting_year"):
            make_request(year=1899)

    def test_rejects_unknown_methodology(self) -> None:
        with pytest.raises(ValidationFailedError, match="methodology"):
            make_request(methodology="teleport")

    def test_from_match_result_builds_request(self) -> None:
        factor = make_factor()
        match = MatchResult(
            status="matched",
            factor=factor,
            confidence=1.0,
            methodology="exact_match",
            request_id="match-9",
        )
        request = CalculationRequest.from_match_result(
            match,
            organization_id="org-1",
            quantity=Decimal("100"),
            quantity_unit="kWh",
            date=date(2025, 6, 1),
            reporting_year=2025,
            activity="Natural gas",
            activity_type=_NATURAL_GAS,
        )
        assert request.match_request_id == "match-9"
        assert request.factor is factor

    def test_from_match_result_rejects_no_match(self) -> None:
        match = MatchResult.no_match([], ["keyword_search"], request_id="match-0")
        with pytest.raises(ValidationFailedError, match="matched factor"):
            CalculationRequest.from_match_result(
                match,
                organization_id="org-1",
                quantity=Decimal("100"),
                quantity_unit="kWh",
                date=date(2025, 6, 1),
                reporting_year=2025,
                activity="Natural gas",
                activity_type=_NATURAL_GAS,
            )


class TestCalculationEngine:
    async def test_calculate_produces_correct_co2e(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink)
        result = await engine.calculate(make_request())
        assert result.co2e_kg == Decimal("18.400000")
        assert result.co2e_tonnes == Decimal("0.018400")
        assert result.methodology == CalculationMethodology.DIRECT_MULTIPLY
        assert result.factor_used.unit == "kWh"

    async def test_calculate_rounds_to_result_precision(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink)
        factor = make_factor(multiplier="0.18456789")
        result = await engine.calculate(
            make_request(factor=factor, quantity="100")
        )
        assert result.co2e_kg == Decimal("18.456789")

    async def test_snapshot_fields_populated(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink)
        request = make_request(scope="Scope 1")
        result = await engine.calculate(request)
        snapshot = result.snapshot
        assert snapshot.match_request_id == "match-1"
        assert snapshot.organization_id == "org-1"
        assert snapshot.factor_id == request.factor.id
        assert snapshot.quantity == Decimal("100")
        assert snapshot.quantity_unit == "kWh"
        assert snapshot.co2e_multiplier == request.factor.co2e_multiplier
        assert snapshot.co2e_kg == Decimal("18.400000")
        assert snapshot.scope == "Scope 1"
        assert snapshot.date == date(2025, 6, 1)
        assert snapshot.reporting_year == 2025
        assert snapshot.methodology == "direct_multiply"
        assert snapshot.algorithm_version == DEFAULT_ALGORITHM_VERSION
        assert len(snapshot.content_hash) == 64

    async def test_calculate_persists_snapshot(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink)
        result = await engine.calculate(make_request())
        stored = sink.snapshots.get(result.snapshot.id)
        assert stored is not None
        assert stored.co2e_kg == result.co2e_kg

    async def test_calculate_creates_log_when_no_log_id(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink)
        result = await engine.calculate(make_request())
        log = sink.logs.get(f"log-{result.snapshot.id}")
        assert log is not None
        assert log.calculated_kg_co2e == Decimal("18.400000")
        assert log.snapshot_id == result.snapshot.id
        assert log.organization_id == "org-1"
        assert log.unit == "kWh"

    async def test_calculate_updates_existing_log(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink)
        existing = EmissionLog(
            id="log-existing",
            organization_id="org-1",
            factor_id="f-1",
            quantity=Decimal("100"),
            date=date(2025, 6, 1),
            unit="kWh",
            scope="Scope 1",
            snapshot_id=None,
            calculated_kg_co2e=Decimal("0"),
        )
        sink.logs["log-existing"] = existing
        result = await engine.calculate(make_request(log_id="log-existing"))
        updated = sink.logs["log-existing"]
        assert updated.calculated_kg_co2e == result.co2e_kg
        assert updated.snapshot_id == result.snapshot.id
        assert updated.factor_id == result.factor_used.id

    async def test_unit_mismatch_raises(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink)
        with pytest.raises(UnitMismatchError):
            await engine.calculate(make_request(quantity_unit="litres"))
        assert sink.snapshots == {}

    async def test_negative_quantity_raises(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink)
        with pytest.raises(ValueError):
            await engine.calculate(make_request(quantity="-5"))
        assert sink.snapshots == {}

    async def test_snapshot_persistence_failure_propagates(self) -> None:
        sink = _MemorySink()
        sink.fail_snapshot = True
        engine = CalculationEngine(sink)
        with pytest.raises(RuntimeError, match="snapshot persistence failed"):
            await engine.calculate(make_request())

    async def test_custom_algorithm_version(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink, algorithm_version="2.1.0")
        assert engine.algorithm_version == "2.1.0"
        result = await engine.calculate(make_request())
        assert result.snapshot.algorithm_version == "2.1.0"


class TestVerification:
    async def test_verify_matches_computed_snapshot(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink)
        result = await engine.calculate(make_request())
        verification = engine.verify(result.snapshot)
        assert verification.match is True
        assert verification.discrepancy is None
        assert verification.tampered is False

    async def test_verify_detects_tampered_hash(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink)
        result = await engine.calculate(make_request())
        snapshot = dataclasses.replace(
            result.snapshot, content_hash="0" * 64
        )
        verification = engine.verify(snapshot)
        assert verification.tampered is True

    async def test_verify_detects_incorrect_result(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink)
        result = await engine.calculate(make_request())
        snapshot = dataclasses.replace(result.snapshot, co2e_kg=Decimal("99"))
        verification = engine.verify(snapshot)
        assert verification.match is False
        assert verification.discrepancy is not None
        assert verification.discrepancy == Decimal("18.400000") - Decimal("99")


class TestEngineSideEffects:
    async def test_publishes_requested_and_completed_events(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []

        async def capture(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(None, capture)
        sink = _MemorySink()
        engine = CalculationEngine(sink, event_bus=bus)
        result = await engine.calculate(
            make_request(match_request_id="match-evt")
        )
        await bus.drain()

        events = [type(e).__name__ for e in received]
        assert events == ["CalculationRequested", "CalculationCompleted"]
        requested = received[0]
        assert isinstance(requested, CalculationRequested)
        assert requested.match_request_id == "match-evt"
        assert requested.organization_id == "org-1"
        assert requested.correlation_id == "match-evt"
        completed = received[1]
        assert isinstance(completed, CalculationCompleted)
        assert completed.snapshot_id == result.snapshot.id
        assert completed.co2e_kg == result.co2e_kg

    async def test_audits_calculation(self) -> None:
        sink = _MemorySink()
        audit = _AuditSink()
        engine = CalculationEngine(sink, audit_logger=audit)  # type: ignore[arg-type]
        result = await engine.calculate(
            make_request(match_request_id="match-audit")
        )
        assert result.co2e_kg == Decimal("18.400000")
        assert len(audit.entries) == 1
        entry = audit.entries[0]
        assert entry.action == "calculation:completed"
        assert entry.entity_type == "calculation_snapshot"
        assert entry.entity_id == result.snapshot.id
        assert entry.correlation_id == "match-audit"
        assert entry.actor == "calculation_engine"
        assert entry.after is not None
        assert entry.after["co2e_kg"] == "18.400000"

    async def test_failing_event_bus_does_not_break_calculation(self) -> None:
        class _BrokenBus:
            async def publish(self, event: DomainEvent) -> int:
                raise RuntimeError("bus down")

        sink = _MemorySink()
        engine = CalculationEngine(
            sink, event_bus=_BrokenBus()  # type: ignore[arg-type]
        )
        result = await engine.calculate(make_request())
        assert result.co2e_kg == Decimal("18.400000")
        assert len(sink.snapshots) == 1

    async def test_no_side_effects_when_unwired(self) -> None:
        sink = _MemorySink()
        engine = CalculationEngine(sink)
        result = await engine.calculate(make_request())
        assert result.co2e_kg == Decimal("18.400000")



