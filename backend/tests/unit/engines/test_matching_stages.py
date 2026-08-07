"""Unit tests for engines.matching_stages."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

import pytest

from domain.factor import EmissionFactor
from domain.matching import FactorAlias, MatchRequest
from engines.matching_stages import (
    AliasMatchStage,
    ExactMatchStage,
    FuzzyMatchStage,
    KeywordSearchStage,
    NaturalKeyStage,
    RepositoryAliasResolver,
    SemanticMatchStage,
)
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
    )


_NATURAL_GAS = "Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]"


class TestExactMatchStage:
    async def test_exact_single_match(self) -> None:
        stage = ExactMatchStage()
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(
            make_request(activity=_NATURAL_GAS), index
        )
        assert result.matched is True
        assert result.confidence == 1.0
        assert result.is_definitive is True
        assert result.provider == "defra"

    async def test_exact_case_insensitive(self) -> None:
        stage = ExactMatchStage()
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(
            make_request(activity=_NATURAL_GAS.upper()), index
        )
        assert result.matched is True

    async def test_exact_no_match(self) -> None:
        stage = ExactMatchStage()
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(make_request(activity="Diesel"), index)
        assert result.matched is False

    async def test_exact_ambiguous_without_unit(self) -> None:
        stage = ExactMatchStage()
        index = make_index(
            [
                make_factor(_NATURAL_GAS, unit="kWh"),
                make_factor(_NATURAL_GAS, unit="therms"),
            ]
        )
        result = await stage.execute(make_request(activity=_NATURAL_GAS), index)
        assert result.matched is False
        assert result.score == 1.0
        assert "ambiguous" in result.reason

    async def test_unit_filter_resolves_ambiguity(self) -> None:
        stage = ExactMatchStage()
        index = make_index(
            [
                make_factor(_NATURAL_GAS, unit="kWh"),
                make_factor(_NATURAL_GAS, unit="therms"),
            ]
        )
        result = await stage.execute(
            make_request(activity=_NATURAL_GAS, unit="kWh"), index
        )
        assert result.matched is True
        assert result.factor is not None
        assert result.factor.unit == "kWh"


class TestNaturalKeyStage:
    async def test_natural_key_hit(self) -> None:
        stage = NaturalKeyStage()
        factor = make_factor(_NATURAL_GAS, unit="kWh", scope="Scope 1")
        index = make_index([factor])
        result = await stage.execute(
            make_request(
                activity=_NATURAL_GAS, unit="kWh", scope="Scope 1", year=2025
            ),
            index,
        )
        assert result.matched is True
        assert result.confidence == 1.0
        assert result.is_definitive is True

    async def test_natural_key_miss(self) -> None:
        stage = NaturalKeyStage()
        index = make_index([make_factor(_NATURAL_GAS, unit="kWh")])
        result = await stage.execute(
            make_request(activity=_NATURAL_GAS, unit="tonnes"), index
        )
        assert result.matched is False

    async def test_natural_key_null_unit_scope(self) -> None:
        stage = NaturalKeyStage()
        factor = make_factor("Electricity", unit=None, scope=None)
        index = make_index([factor])
        result = await stage.execute(
            make_request(activity="Electricity", unit=None, scope=None), index
        )
        assert result.matched is True


class TestKeywordSearchStage:
    async def test_full_token_match(self) -> None:
        stage = KeywordSearchStage(min_confidence=0.80)
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(
            make_request(activity="Natural gas"), index
        )
        assert result.matched is True
        assert result.score >= 0.80
        assert result.is_definitive is False

    async def test_below_threshold_is_not_matched(self) -> None:
        stage = KeywordSearchStage(min_confidence=0.80)
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(
            make_request(activity="Natural gaz"), index
        )
        assert result.matched is False

    async def test_unit_filter_limits_retrieval(self) -> None:
        stage = KeywordSearchStage(min_confidence=0.80)
        index = make_index(
            [
                make_factor(_NATURAL_GAS, unit="kWh"),
                make_factor("Diesel (net CV)", unit="litres"),
            ]
        )
        result = await stage.execute(
            make_request(activity="Natural gas", unit="kWh"), index
        )
        assert result.matched is True
        assert result.factor is not None
        assert result.factor.unit == "kWh"

    def test_min_confidence_validation(self) -> None:
        with pytest.raises(ValueError):
            KeywordSearchStage(min_confidence=1.5)


class TestAliasMatchStage:
    async def _resolver(self, target: Optional[str]) -> Any:
        async def resolve(
            alias_text: str, organization_id: Optional[str]
        ) -> Optional[str]:
            return target

        return resolve

    async def test_alias_match_is_definitive(self) -> None:
        resolver = await self._resolver(_NATURAL_GAS)
        stage = AliasMatchStage(resolver)
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(make_request(activity="NG"), index)
        assert result.matched is True
        assert result.confidence == 1.0
        assert result.is_definitive is True
        assert result.reason == "alias match"

    async def test_unresolved_alias(self) -> None:
        resolver = await self._resolver(None)
        stage = AliasMatchStage(resolver)
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(make_request(activity="NG"), index)
        assert result.matched is False

    async def test_no_resolver_configured(self) -> None:
        stage = AliasMatchStage()
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(make_request(activity="NG"), index)
        assert result.matched is False
        assert "resolver" in result.reason

    async def test_repository_alias_resolver_adapts_repo(self) -> None:
        alias_obj = FactorAlias(
            id="a-1",
            organization_id="org-1",
            alias_text="NG",
            target_activity_type=_NATURAL_GAS,
            target_provider_key="defra",
            created_at=datetime(2025, 6, 1),
        )

        class _StubRepo:
            async def find_by_alias(
                self, alias_text: str, org_id: Optional[str]
            ) -> Optional[FactorAlias]:
                if alias_text == "NG" and org_id == "org-1":
                    return alias_obj
                return None

        resolver = RepositoryAliasResolver(_StubRepo())  # type: ignore[arg-type]
        stage = AliasMatchStage(resolver)
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(
            make_request(activity="NG", organization_id="org-1"), index
        )
        assert result.matched is True

    async def test_repository_alias_resolver_global_fallback(self) -> None:
        alias_obj = FactorAlias(
            id="a-2",
            organization_id=None,
            alias_text="NG",
            target_activity_type=_NATURAL_GAS,
            target_provider_key="defra",
        )

        class _StubRepo:
            async def find_by_alias(
                self, alias_text: str, org_id: Optional[str]
            ) -> Optional[FactorAlias]:
                if org_id is None:
                    return alias_obj
                return None

        resolver = RepositoryAliasResolver(_StubRepo())  # type: ignore[arg-type]
        stage = AliasMatchStage(resolver)
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(
            make_request(activity="NG", organization_id=None), index
        )
        assert result.matched is True


class TestFuzzyMatchStage:
    async def test_high_similarity_matches(self) -> None:
        stage = FuzzyMatchStage(threshold=0.85)
        index = make_index([make_factor(_NATURAL_GAS)])
        # A near-identical query (extra trailing space) scores above threshold.
        result = await stage.execute(
            make_request(activity="Fuels > Gas fuels > Natural gas (kg CO2e) [kWh] "),
            index,
        )
        assert result.matched is True
        assert 0.85 <= result.confidence <= 1.0

    async def test_low_similarity_does_not_match(self) -> None:
        stage = FuzzyMatchStage(threshold=0.85)
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(
            make_request(activity="Electricity grid losses"), index
        )
        assert result.matched is False

    def test_threshold_validation(self) -> None:
        with pytest.raises(ValueError):
            FuzzyMatchStage(threshold=1.5)


class TestSemanticMatchStage:
    async def test_disabled_does_not_match(self) -> None:
        stage = SemanticMatchStage(enabled=False)
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(make_request(activity="NG"), index)
        assert result.matched is False
        assert "disabled" in result.reason

    async def test_enabled_without_scorer_does_not_match(self) -> None:
        stage = SemanticMatchStage(enabled=True)
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(make_request(activity="NG"), index)
        assert result.matched is False
        assert "not configured" in result.reason

    async def test_enabled_with_scorer_matches(self) -> None:
        def scorer(activity: str, factor_activity: str) -> float:
            return 0.95 if factor_activity == _NATURAL_GAS else 0.1

        stage = SemanticMatchStage(enabled=True, scorer=scorer)
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(make_request(activity="natural gas"), index)
        assert result.matched is True
        assert result.confidence == 0.95

    async def test_enabled_with_scorer_below_threshold(self) -> None:
        def scorer(activity: str, factor_activity: str) -> float:
            return 0.5

        stage = SemanticMatchStage(enabled=True, min_confidence=0.70, scorer=scorer)
        index = make_index([make_factor(_NATURAL_GAS)])
        result = await stage.execute(make_request(activity="natural gas"), index)
        assert result.matched is False


