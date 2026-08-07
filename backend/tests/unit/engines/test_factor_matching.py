"""Unit tests for engines.factor_matching (engine + pipeline builder)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import pytest

from domain.audit import AuditEntry, AuditQuery
from domain.factor import EmissionFactor
from domain.matching import MatchRequest, MatchingPipelineConfig
from domain.workflow import DomainEvent, FactorMatched, FactorNotFound
from engines.factor_matching import (
    FactorMatchingEngine,
    build_matching_pipeline,
)
from engines.matching_stages import ExactMatchStage, SemanticMatchStage
from infra.event_bus import EventBus
from infra.search_index import FactorSearchIndex


def make_factor(
    activity_type: str,
    **kwargs: Any,
) -> EmissionFactor:
    year = int(kwargs.get("year", 2025))
    unit = kwargs.get("unit")
    scope = kwargs.get("scope")
    country = str(kwargs.get("country") or "GB")
    provider = str(kwargs.get("provider") or "defra")
    return EmissionFactor(
        id=str(kwargs.get("id") or f"f-{uuid.uuid4().hex[:12]}"),
        reporting_year=year,
        activity_type=activity_type,
        co2e_multiplier=Decimal(str(kwargs.get("multiplier") or "0.18400")),
        unit=str(unit) if unit is not None else None,
        scope=str(scope) if scope is not None else None,
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country=country,
        provider_key=provider,
        natural_key=(
            str(year),
            activity_type,
            country,
            str(unit) if unit is not None else "",
            str(scope) if scope is not None else "",
        ),
    )


def make_index(factors: list[EmissionFactor]) -> FactorSearchIndex:
    index = FactorSearchIndex()
    index.load(factors)
    return index


def make_request(**kwargs: Any) -> MatchRequest:
    return MatchRequest(
        id=str(kwargs.get("id") or "req-1"),
        activity=str(kwargs.get("activity") or "Natural gas"),
        country=str(kwargs.get("country") or "GB"),
        reporting_year=int(kwargs.get("year", 2025)),
        unit=kwargs.get("unit"),
        scope=kwargs.get("scope"),
        organization_id=kwargs.get("organization_id"),
        preferred_provider=kwargs.get("provider"),
        max_stages=int(kwargs.get("max_stages", 6)),
    )


def make_engine(
    factors: list[EmissionFactor],
    *,
    config: Optional[MatchingPipelineConfig] = None,
    event_bus: Optional[EventBus] = None,
    audit_logger: Any = None,
) -> FactorMatchingEngine:
    stages = build_matching_pipeline(config or MatchingPipelineConfig())
    return FactorMatchingEngine(
        make_index(factors),
        stages,
        config=config,
        event_bus=event_bus,
        audit_logger=audit_logger,
    )


_NATURAL_GAS = "Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]"
_DIESEL = "Fuels > Liquid fuels > Diesel (net CV) [litres]"


class TestPipelineBuilder:
    def test_builds_default_stage_order(self) -> None:
        config = MatchingPipelineConfig()
        stages = build_matching_pipeline(config)
        assert [s.name for s in stages] == [
            "exact_match",
            "natural_key",
            "alias_match",
            "keyword_search",
            "fuzzy_match",
        ]

    def test_unknown_stage_raises(self) -> None:
        config = MatchingPipelineConfig(stages=("teleport_match",))
        with pytest.raises(ValueError, match="unknown matching stage"):
            build_matching_pipeline(config)

    def test_custom_stage_order(self) -> None:
        config = MatchingPipelineConfig(stages=("keyword_search", "exact_match"))
        stages = build_matching_pipeline(config)
        assert [s.name for s in stages] == ["keyword_search", "exact_match"]

    def test_semantic_enabled_propagates(self) -> None:
        config = MatchingPipelineConfig(
            stages=("semantic_match",), semantic_enabled=True
        )
        stages = build_matching_pipeline(config)
        assert isinstance(stages[0], SemanticMatchStage)


class TestEngineMatchFlow:
    async def test_exact_match_short_circuits(self) -> None:
        factor = make_factor(_NATURAL_GAS)
        engine = make_engine([factor])
        result = await engine.match(make_request(activity=_NATURAL_GAS))
        assert result.status == "matched"
        assert result.methodology == "exact_match"
        assert result.confidence == 1.0
        assert result.stages_executed == ("exact_match",)
        assert result.factor is not None
        assert result.factor.id == factor.id
        assert result.provider == "defra"

    async def test_natural_key_match(self) -> None:
        factor = make_factor(_DIESEL, unit="litres", scope="Scope 1")
        # In the default pipeline exact_match legitimately subsumes the natural
        # key; run the natural-key stage on its own to verify it end to end.
        config = MatchingPipelineConfig(stages=("natural_key",))
        engine = make_engine([factor], config=config)
        result = await engine.match(
            make_request(
                activity=_DIESEL, unit="litres", scope="Scope 1", year=2025
            )
        )
        assert result.status == "matched"
        assert result.methodology == "natural_key"

    async def test_keyword_fallback_after_exact_miss(self) -> None:
        engine = make_engine([make_factor(_NATURAL_GAS)])
        # "Natural gas" is a token subset of the factor activity but not exact.
        result = await engine.match(make_request(activity="Natural gas"))
        assert result.status == "matched"
        assert result.methodology == "keyword_search"
        assert 0.0 < result.confidence <= 1.0

    async def test_no_match_returns_suggestions(self) -> None:
        engine = make_engine([make_factor(_NATURAL_GAS)])
        result = await engine.match(
            make_request(activity="Petrol (unleaded)", id="req-nomatch")
        )
        assert result.status == "no_match"
        assert result.factor is None
        assert result.stages_executed == (
            "exact_match",
            "natural_key",
            "alias_match",
            "keyword_search",
            "fuzzy_match",
        )
        assert result.request_id == "req-nomatch"

    async def test_ambiguous_exact_returns_ambiguous(self) -> None:
        engine = make_engine(
            [
                make_factor(_NATURAL_GAS, unit="kWh"),
                make_factor(_NATURAL_GAS, unit="therms"),
            ]
        )
        result = await engine.match(make_request(activity=_NATURAL_GAS))
        assert result.status == "ambiguous"
        assert result.factor is None
        assert len(result.suggestions) >= 1

    async def test_max_stages_limits_pipeline(self) -> None:
        engine = make_engine([make_factor(_NATURAL_GAS)])
        result = await engine.match(
            make_request(activity="Natural gas", max_stages=1)
        )
        # Only exact_match runs; it misses, so the result is no_match.
        assert result.status == "no_match"
        assert result.stages_executed == ("exact_match",)

    async def test_empty_stages_raise(self) -> None:
        with pytest.raises(ValueError, match="stages"):
            FactorMatchingEngine(make_index([make_factor(_NATURAL_GAS)]), [])


class TestEngineSideEffects:
    async def test_publishes_factor_matched_event(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []

        async def capture(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(FactorMatched, capture)
        factor = make_factor(_NATURAL_GAS)
        engine = make_engine([factor], event_bus=bus)
        result = await engine.match(
            make_request(activity=_NATURAL_GAS, id="req-event")
        )
        await bus.drain()
        assert result.status == "matched"
        assert len(received) == 1
        event = received[0]
        assert isinstance(event, FactorMatched)
        assert event.request_id == "req-event"
        assert event.factor_id == factor.id
        assert event.confidence == 1.0
        assert event.correlation_id == "req-event"

    async def test_publishes_factor_not_found_event(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []

        async def capture(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(FactorNotFound, capture)
        engine = make_engine([make_factor(_NATURAL_GAS)], event_bus=bus)
        result = await engine.match(
            make_request(activity="Petrol (unleaded)", id="req-nf")
        )
        await bus.drain()
        assert result.status == "no_match"
        assert len(received) == 1
        event = received[0]
        assert isinstance(event, FactorNotFound)
        assert event.request_id == "req-nf"
        assert event.activity == "Petrol (unleaded)"

    async def test_audits_match_outcome(self) -> None:
        sink = _MemorySink()
        engine = make_engine([make_factor(_NATURAL_GAS)], audit_logger=sink)
        result = await engine.match(
            make_request(activity=_NATURAL_GAS, id="req-audit")
        )
        assert result.status == "matched"
        assert len(sink.entries) == 1
        entry = sink.entries[0]
        assert entry.action == "factor_match:matched"
        assert entry.entity_type == "factor_match"
        assert entry.entity_id == "req-audit"
        assert entry.actor == "matching_engine"
        assert entry.correlation_id == "req-audit"
        assert entry.after is not None
        assert entry.after["status"] == "matched"

    async def test_failing_event_bus_does_not_break_match(self) -> None:
        class _BrokenBus:
            async def publish(self, event: DomainEvent) -> int:
                raise RuntimeError("bus down")

        engine = make_engine(
            [make_factor(_NATURAL_GAS)],
            event_bus=_BrokenBus(),  # type: ignore[arg-type]
        )
        result = await engine.match(make_request(activity=_NATURAL_GAS))
        assert result.status == "matched"


class _MemorySink:
    """In-memory audit sink for the engine audit test."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    async def record(self, entry: AuditEntry) -> AuditEntry:
        self.entries.append(entry)
        return entry

    async def query(self, filters: AuditQuery) -> list[AuditEntry]:
        result = self.entries
        if filters.correlation_id is not None:
            result = [e for e in result if e.correlation_id == filters.correlation_id]
        return result[: filters.limit]

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
        return await self.record(entry)


