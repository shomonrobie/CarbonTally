"""Integration tests for infra.search_index + EmissionFactorsRepository.

Seeds factors through the repository, builds the index from the repository's
full factor set, and verifies natural-key and keyword lookups against the real
data. Rows created here are removed afterwards so the suite stays clean.
"""
from __future__ import annotations

from decimal import Decimal

import asyncpg
import pytest

from data.emission_factors import EmissionFactorsRepository
from domain.factor import EmissionFactor
from infra.search_index import FactorSearchIndex
from tests.integration.conftest import new_id

pytestmark = pytest.mark.asyncio


def _factor(activity_type: str, **kwargs: object) -> EmissionFactor:
    year = 2025
    return EmissionFactor(
        id=str(kwargs.get("id") or new_id()),
        reporting_year=year,
        activity_type=activity_type,
        co2e_multiplier=Decimal(str(kwargs.get("multiplier") or "2.52000")),
        unit="litres",
        scope="Scope 1",
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
        provider_key="defra",
        natural_key=("2025", activity_type, "GB", "litres", "Scope 1"),
    )


async def test_index_loads_from_real_repository_data(pool: asyncpg.Pool) -> None:
    repo = EmissionFactorsRepository(pool)
    marker = new_id()
    factor_a = _factor(f"Fuels > Liquid fuels > Diesel P3 {marker} (net CV)")
    factor_b = _factor(f"Fuels > Gaseous fuels > Natural gas P3 {marker}")
    try:
        await repo.save(factor_a)
        await repo.save(factor_b)

        index = await FactorSearchIndex.from_repository(repo)
        assert len(index) >= 2

        # Exact natural-key lookup against the seeded rows.
        assert index.exact_natural_key(factor_a.natural_key) is not None
        assert index.exact_natural_key(factor_b.natural_key) is not None

        # Keyword search finds both seeded factors (all query tokens present).
        results = index.keyword_search(f"diesel {marker}")
        assert any(f.id == factor_a.id for f, _ in results)
        results = index.keyword_search(f"natural gas {marker}")
        assert any(f.id == factor_b.id for f, _ in results)

        # Unit filtering narrows to the seeded row.
        narrowed = index.keyword_search(f"diesel {marker}", unit="litres")
        assert any(f.id == factor_a.id for f, _ in narrowed)
    finally:
        await repo.delete(factor_a.id)
        await repo.delete(factor_b.id)


async def test_exact_natural_key_miss_returns_none(pool: asyncpg.Pool) -> None:
    repo = EmissionFactorsRepository(pool)
    index = await FactorSearchIndex.from_repository(repo)
    assert (
        index.exact_natural_key(
            ("2025", "Phase 3 > Definitely missing", "GB", "litres", "Scope 1")
        )
        is None
    )
