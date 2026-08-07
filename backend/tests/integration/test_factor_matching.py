"""Integration tests for the Phase 4 Factor Matching Engine.

Seeds emission factors and aliases through the real repositories, builds the
search index from the repository, and verifies the full matching pipeline over
real data — including the prep-pack completion criterion of 20 pipeline
queries with correct factors, confidence ranges and configurable pipelines.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

import asyncpg
import pytest

from data.audit import AuditRepository
from data.emission_factors import EmissionFactorsRepository
from data.events import EventsRepository
from data.factor_aliases import FactorAliasesRepository
from domain.audit import AuditQuery
from domain.factor import EmissionFactor
from domain.matching import FactorAlias, MatchRequest, MatchingPipelineConfig
from domain.workflow import FactorMatched
from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline
from engines.matching_stages import RepositoryAliasResolver
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus
from infra.search_index import FactorSearchIndex
from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio

#: Unique marker so seeded rows never collide with other test files.
_MARKER = f"p4-{new_id()[:6]}"

ACTIVITY_GAS = f"Fuels > Gas fuels > Natural gas {_MARKER} (kg CO2e) [kWh]"
ACTIVITY_DIESEL = f"Fuels > Liquid fuels > Diesel {_MARKER} (net CV) [litres]"
ACTIVITY_DIESEL_GROSS = f"Fuels > Liquid fuels > Diesel {_MARKER} (gross CV) [litres]"
ACTIVITY_PETROL = f"Fuels > Liquid fuels > Petrol {_MARKER} (net CV) [litres]"
ACTIVITY_ELECTRICITY = f"Electricity (T&D losses) {_MARKER}"


def _factor(
    activity: str,
    *,
    unit: Optional[str] = "kWh",
    scope: str = "Scope 1",
    country: str = "GB",
) -> EmissionFactor:
    return EmissionFactor(
        id=new_id(),
        reporting_year=2025,
        activity_type=activity,
        co2e_multiplier=Decimal("0.18400"),
        unit=unit,
        scope=scope,
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country=country,
        provider_key="defra",
        natural_key=(
            "2025", activity, country, unit or "", scope,
        ),
    )


class _Seeded:
    def __init__(
        self,
        pool: asyncpg.Pool,
        factor_repo: EmissionFactorsRepository,
        alias_repo: FactorAliasesRepository,
        index: FactorSearchIndex,
        resolver: RepositoryAliasResolver,
        factor_ids: list[str],
        alias_ids: list[str],
        org_id: str,
    ) -> None:
        self.pool = pool
        self.factor_repo = factor_repo
        self.alias_repo = alias_repo
        self.index = index
        self.resolver = resolver
        self.factor_ids = factor_ids
        self.alias_ids = alias_ids
        self.org_id = org_id


@pytest.fixture(scope="session")
async def seeded(pool: asyncpg.Pool) -> Any:
    factor_repo = EmissionFactorsRepository(pool)
    alias_repo = FactorAliasesRepository(pool)

    factors = [
        _factor(ACTIVITY_GAS, unit="kWh", scope="Scope 1", country="GB"),
        _factor(ACTIVITY_GAS, unit="kWh", scope="Scope 1", country="IE"),
        _factor(ACTIVITY_DIESEL, unit="litres", scope="Scope 1", country="GB"),
        _factor(ACTIVITY_DIESEL_GROSS, unit="litres", scope="Scope 1", country="GB"),
        _factor(ACTIVITY_PETROL, unit="litres", scope="Scope 1", country="GB"),
        _factor(ACTIVITY_ELECTRICITY, unit="kWh", scope="Scope 2", country="GB"),
    ]
    factor_ids: list[str] = []
    for factor in factors:
        await factor_repo.save(factor)
        factor_ids.append(factor.id)

    org_id = await make_org(pool, name="P4 Matching Org")
    org_alias = FactorAlias(
        id=new_id(),
        organization_id=org_id,
        alias_text="NG",
        target_activity_type=ACTIVITY_GAS,
        target_provider_key="defra",
        created_at=datetime.now(),
    )
    global_alias = FactorAlias(
        id=new_id(),
        organization_id=None,
        alias_text="DieselNet",
        target_activity_type=ACTIVITY_DIESEL,
        target_provider_key="defra",
        created_at=datetime.now(),
    )
    await alias_repo.save(org_alias)
    await alias_repo.save(global_alias)

    index = await FactorSearchIndex.from_repository(factor_repo)
    resolver = RepositoryAliasResolver(alias_repo)

    ctx = _Seeded(
        pool=pool,
        factor_repo=factor_repo,
        alias_repo=alias_repo,
        index=index,
        resolver=resolver,
        factor_ids=factor_ids,
        alias_ids=[org_alias.id, global_alias.id],
        org_id=org_id,
    )
    try:
        yield ctx
    finally:
        for factor_id in factor_ids:
            await factor_repo.delete(factor_id)
        for alias_id in [org_alias.id, global_alias.id]:
            await alias_repo.delete(alias_id)


def _engine(
    ctx: _Seeded,
    *,
    config: Optional[MatchingPipelineConfig] = None,
    event_bus: Optional[EventBus] = None,
    audit_logger: Optional[AuditLogger] = None,
) -> FactorMatchingEngine:
    stages = build_matching_pipeline(
        config or MatchingPipelineConfig(), alias_resolver=ctx.resolver
    )
    return FactorMatchingEngine(
        ctx.index,
        stages,
        config=config,
        event_bus=event_bus,
        audit_logger=audit_logger,
    )


def _request(
    activity: str,
    *,
    country: str = "GB",
    unit: Optional[str] = None,
    scope: Optional[str] = None,
    organization_id: Optional[str] = None,
    max_stages: int = 6,
) -> MatchRequest:
    return MatchRequest(
        id=new_id(),
        activity=activity,
        country=country,
        reporting_year=2025,
        unit=unit,
        scope=scope,
        organization_id=organization_id,
        max_stages=max_stages,
    )


# ---------------------------------------------------------------------------
# The prep-pack completion criterion: 20 pipeline queries over real data.
# Each case: (activity, expected_status, expected_method, request kwargs,
# config kwargs, expected factor country, id).
# ---------------------------------------------------------------------------

_QUERIES = [
    pytest.param(ACTIVITY_GAS, "matched", "exact_match", {"unit": "kWh"}, None, "GB", "q01-exact-gas"),
    pytest.param(ACTIVITY_GAS.upper(), "matched", "exact_match", {"unit": "kWh"}, None, "GB", "q02-exact-case-insensitive"),
    pytest.param(ACTIVITY_GAS, "matched", "exact_match", {"country": "IE", "unit": "kWh"}, None, "IE", "q03-exact-gas-ie"),
    pytest.param(ACTIVITY_DIESEL, "matched", "exact_match", {"unit": "litres"}, None, "GB", "q04-exact-diesel"),
    pytest.param(ACTIVITY_ELECTRICITY, "matched", "exact_match", {"unit": "kWh", "scope": "Scope 2"}, None, "GB", "q05-exact-electricity"),
    pytest.param(f"Natural gas {_MARKER}", "matched", "keyword_search", {}, None, "GB", "q06-keyword-gas"),
    pytest.param(f"Natural gas {_MARKER}", "matched", "keyword_search", {"unit": "kWh"}, None, "GB", "q07-keyword-gas-kwh"),
    pytest.param(f"Natural gas {_MARKER}", "no_match", None, {"unit": "litres"}, None, None, "q08-keyword-unit-miss"),
    pytest.param(f"Diesel {_MARKER}", "matched", "keyword_search", {"unit": "litres"}, None, "GB", "q09-keyword-diesel"),
    pytest.param("NG", "matched", "alias_match", {"organization_id": "org-a"}, None, "GB", "q10-alias-org-scoped"),
    pytest.param("NG", "no_match", None, {"organization_id": "org-b"}, None, None, "q11-alias-other-org"),
    pytest.param("DieselNet", "matched", "alias_match", {}, None, "GB", "q12-alias-global"),
    pytest.param(f"Petrol (unleaded) {_MARKER}", "no_match", None, {"unit": "litres"}, None, None, "q13-no-match-suggestions"),
    pytest.param(ACTIVITY_GAS + " 2x", "matched", "fuzzy_match", {"unit": "kWh"}, {"stages": ("fuzzy_match",)}, "GB", "q14-fuzzy-gas"),
    pytest.param(f"Natural gas {_MARKER} xyz", "no_match", None, {}, {"stages": ("keyword_search",), "keyword_min_confidence": 0.99}, None, "q15-keyword-threshold"),
    pytest.param(f"Natural gas {_MARKER}", "matched", "keyword_search", {}, {"stages": ("keyword_search",)}, "GB", "q16-keyword-only-pipeline"),
    pytest.param(ACTIVITY_DIESEL, "matched", "natural_key", {"unit": "litres", "scope": "Scope 1"}, {"stages": ("natural_key",)}, "GB", "q17-natural-key-only"),
    pytest.param(ACTIVITY_DIESEL_GROSS, "matched", "exact_match", {"unit": "litres"}, None, "GB", "q18-exact-diesel-gross"),
    pytest.param(f"Petrol {_MARKER}", "matched", "keyword_search", {"unit": "litres"}, None, "GB", "q19-keyword-petrol"),
    pytest.param("Renewable energy certificates", "no_match", None, {}, None, None, "q20-no-match-no-suggestions"),
]


@pytest.mark.parametrize(
    "activity,expected_status,expected_method,req_kwargs,config_kwargs,expected_country,query_id",
    _QUERIES,
)
async def test_pipeline_query(
    activity: str,
    expected_status: str,
    expected_method: Optional[str],
    req_kwargs: dict[str, Any],
    config_kwargs: Optional[dict[str, Any]],
    expected_country: Optional[str],
    query_id: str,
    seeded: Any,
) -> None:
    config = (
        MatchingPipelineConfig(**config_kwargs)
        if config_kwargs is not None
        else MatchingPipelineConfig()
    )
    engine = _engine(seeded, config=config)
    organization_id = req_kwargs.get("organization_id")
    if organization_id == "org-a":
        organization_id = seeded.org_id
    elif organization_id == "org-b":
        organization_id = new_id()
    request = _request(
        activity,
        country=str(req_kwargs.get("country") or "GB"),
        unit=req_kwargs.get("unit"),
        scope=req_kwargs.get("scope"),
        organization_id=organization_id,
    )
    result = await engine.match(request)
    assert result.status == expected_status, query_id
    if expected_method is not None:
        assert result.methodology == expected_method, query_id
    if result.status == "matched":
        assert result.factor is not None
        assert 0.0 <= result.confidence <= 1.0
        if expected_country is not None:
            assert result.factor.country == expected_country
    if result.status == "no_match":
        assert 0.0 <= result.confidence <= 1.0


async def test_no_match_suggestions_are_ranked_candidates(seeded: Any) -> None:
    engine = _engine(seeded)
    request = _request(f"Petrol (unleaded) {_MARKER}", unit="litres")
    result = await engine.match(request)
    assert result.status == "no_match"
    assert result.suggestions, "expected ranked candidate suggestions"
    assert all(0.0 < s.score <= 1.0 for s in result.suggestions)


async def test_no_match_without_candidates_has_no_suggestions(seeded: Any) -> None:
    engine = _engine(seeded)
    request = _request("Renewable energy certificates")
    result = await engine.match(request)
    assert result.status == "no_match"
    assert result.suggestions == ()


async def test_max_stages_limits_executed_pipeline(seeded: Any) -> None:
    engine = _engine(seeded)
    request = _request(f"Natural gas {_MARKER}", max_stages=1)
    result = await engine.match(request)
    # Only exact_match runs; "Natural gas <marker>" is not an exact activity.
    assert result.status == "no_match"
    assert result.stages_executed == ("exact_match",)


async def test_engine_publishes_and_persists_factor_matched(seeded: Any) -> None:
    events_repo = EventsRepository(seeded.pool)
    bus = EventBus()

    async def persist(event: Any) -> None:
        await events_repo.store(event)

    bus.subscribe(FactorMatched, persist)
    engine = _engine(seeded, event_bus=bus)
    request = _request(ACTIVITY_GAS, unit="kWh")
    result = await engine.match(request)
    await bus.drain()

    assert result.status == "matched"
    stored = await events_repo.get_by_correlation(request.id)
    assert len(stored) == 1
    event = stored[0]
    assert isinstance(event, FactorMatched)
    assert event.request_id == request.id
    assert event.factor_id is not None
    assert event.confidence == 1.0


async def test_engine_audits_every_outcome(seeded: Any) -> None:
    logger = AuditLogger(AuditRepository(seeded.pool))
    engine = _engine(seeded, audit_logger=logger)
    request = _request(ACTIVITY_DIESEL, unit="litres")
    result = await engine.match(request)
    assert result.status == "matched"

    entries = await logger.query(AuditQuery(correlation_id=request.id))
    assert len(entries) == 1
    assert entries[0].action == "factor_match:matched"
    assert entries[0].entity_type == "factor_match"
    assert entries[0].actor == "matching_engine"
    assert entries[0].after is not None
    assert entries[0].after["methodology"] == "exact_match"


