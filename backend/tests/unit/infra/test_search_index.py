"""Unit tests for infra.search_index."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from domain.factor import EmissionFactor
from infra.search_index import (
    FactorSearchIndex,
    get_search_index,
    reset_search_index,
)


def _factor(
    activity_type: str,
    **kwargs: Any,
) -> EmissionFactor:
    factor_id = str(kwargs.get("id") or f"f-{abs(hash(activity_type))}")
    year = int(kwargs.get("year", 2025))
    unit = kwargs.get("unit")
    scope = kwargs.get("scope")
    country = str(kwargs.get("country") or "GB")
    provider = str(kwargs.get("provider") or "defra")
    return EmissionFactor(
        id=factor_id,
        reporting_year=year,
        activity_type=activity_type,
        co2e_multiplier=Decimal(str(kwargs.get("multiplier") or "2.50000")),
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


_FACTORS = [
    _factor("Fuels > Liquid fuels > Diesel (net CV)", id="f-diesel-net", unit="litres", scope="Scope 1"),
    _factor("Fuels > Liquid fuels > Diesel (gross CV)", id="f-diesel-gross", unit="tonnes", scope="Scope 1"),
    _factor("Fuels > Liquid fuels > Petrol (net CV)", id="f-petrol", unit="litres", scope="Scope 1", country="IE"),
    _factor("Fuels > Gaseous fuels > Natural gas", id="f-gas", unit="kWh", scope="Scope 1"),
    _factor("Electricity (T&D losses)", id="f-electricity", unit="kWh", scope="Scope 2", provider="defra"),
]


class TestExactNaturalKey:
    def test_hit(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        target = _FACTORS[0]
        found = index.exact_natural_key(target.natural_key)
        assert found is not None
        assert found.id == target.id

    def test_miss(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        assert index.exact_natural_key(("2025", "nonexistent", "GB", "", "")) is None

    def test_blank_natural_key_is_ignored(self) -> None:
        index = FactorSearchIndex()
        bare = EmissionFactor(
            id="f-bare",
            reporting_year=2025,
            activity_type="Bare activity",
            co2e_multiplier=Decimal("1.50000"),
        )
        index.add(bare)
        assert bare.natural_key == ()
        assert index.exact_natural_key(bare.natural_key) is None
        assert index.keyword_search("Bare activity")[0][0].id == "f-bare"


class TestKeywordSearch:
    def test_token_coverage_ranking(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        results = index.keyword_search("Diesel net CV")
        assert results
        top_factor, top_score = results[0]
        assert top_factor.id == "f-diesel-net"
        assert top_score == 1.0

    def test_scores_are_descending(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        results = index.keyword_search("Diesel net CV")
        scores = [score for _, score in results]
        assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
        assert max(scores) == 1.0

    def test_unit_filter(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        results = index.keyword_search("Diesel", unit="tonnes")
        assert [f.id for f, _ in results] == ["f-diesel-gross"]

    def test_country_filter(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        results = index.keyword_search("Petrol", country="IE")
        assert [f.id for f, _ in results] == ["f-petrol"]

    def test_provider_filter(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        results = index.keyword_search("electricity", provider="defra")
        assert [f.id for f, _ in results] == ["f-electricity"]
        assert index.keyword_search("electricity", provider="seai") == []

    def test_limit(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        assert len(index.keyword_search("diesel", limit=1)) == 1
        with pytest.raises(ValueError):
            index.keyword_search("diesel", limit=0)

    def test_empty_query_returns_nothing(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        assert index.keyword_search("") == []
        assert index.keyword_search("!!!") == []

    def test_empty_index_returns_nothing(self) -> None:
        index = FactorSearchIndex()
        assert index.keyword_search("diesel") == []

    def test_case_insensitive(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        assert index.keyword_search("DIESEL NET")[0][0].id == "f-diesel-net"


class TestMutation:
    def test_add_and_replace_by_id(self) -> None:
        index = FactorSearchIndex()
        original = _FACTORS[0]
        index.add(original)
        replacement = _factor(original.activity_type, id=original.id, multiplier="9.90000")
        index.add(replacement)
        assert len(index) == 1
        assert index.get(original.id) is replacement

    def test_remove(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        assert index.remove("f-diesel-net") is True
        assert index.remove("f-diesel-net") is False
        assert len(index) == len(_FACTORS) - 1
        assert index.exact_natural_key(_FACTORS[0].natural_key) is None

    def test_load_replaces_contents(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        subset = _FACTORS[:2]
        index.load(subset)
        assert len(index) == 2
        assert index.get("f-diesel-net") is not None
        assert index.get("f-gas") is None

    def test_rebuild_is_load(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        index.rebuild([])
        assert len(index) == 0

    def test_get_len_snapshot(self) -> None:
        index = FactorSearchIndex()
        index.load(_FACTORS)
        assert len(index) == len(_FACTORS)
        assert index.get("f-gas") is not None
        assert [f.id for f in index.snapshot()] == [f.id for f in _FACTORS]

    def test_default_limit_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            FactorSearchIndex(default_limit=0)


class TestFromRepository:
    class _StubSource:
        def __init__(self, factors: list[EmissionFactor]) -> None:
            self._factors = factors

        async def load_all_for_index(self) -> list[EmissionFactor]:
            return self._factors

    async def test_loads_from_source(self) -> None:
        index = await FactorSearchIndex.from_repository(self._StubSource(_FACTORS))
        assert len(index) == len(_FACTORS)
        assert index.exact_natural_key(_FACTORS[0].natural_key) is not None
        assert index.keyword_search("diesel net")[0][0].id == "f-diesel-net"


class TestSingleton:
    def test_get_search_index_is_singleton(self) -> None:
        reset_search_index()
        try:
            assert get_search_index() is get_search_index()
        finally:
            reset_search_index()

    def test_reset_search_index_replaces(self) -> None:
        reset_search_index()
        try:
            first = get_search_index()
            reset_search_index()
            second = get_search_index()
            assert first is not second
        finally:
            reset_search_index()

