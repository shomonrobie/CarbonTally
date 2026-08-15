"""DEFRA regression tests: SEAI must not change DEFRA matching/calculation.

Uses the backend matching + calculation engines (from ``backend/``) with real
factor rows from the isolated test database: a DEFRA GB diesel factor and the
imported SEAI IE diesel factor. Country selection must keep GB and IE apart.
"""
from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from src.providers.seai import analyze_workbook, load_to_db, map_all  # noqa: E402

from domain.calculation import CalculationSnapshot, EmissionLog  # noqa: E402
from domain.factor import EmissionFactor  # noqa: E402
from domain.matching import MatchRequest, MatchingPipelineConfig  # noqa: E402
from engines.calculation import (  # noqa: E402
    CalculationEngine,
    CalculationRequest,
)
from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline  # noqa: E402
from infra.search_index import FactorSearchIndex  # noqa: E402

FALLBACK_DEFRA_DIESEL = {
    "reporting_year": 2025,
    "activity_type": "Fuels > Liquid fuels > Diesel (net CV) [litres]",
    "co2e_multiplier": Decimal("2.52000"),
    "unit": "litres",
    "scope": "Scope 1",
    "factor_source": "DEFRA-DESNZ",
    "factor_set": "DEFRA-2025",
    "country": "GB",
    "provider_key": "defra",
}


def _backend_factor(row: tuple, provider_key: str) -> EmissionFactor:
    (
        activity_type, multiplier, unit, scope, source, factor_set,
        country, year, batch_id,
    ) = row
    return EmissionFactor(
        id="f-" + provider_key + "-" + activity_type[:16].replace(" ", "_"),
        reporting_year=year,
        activity_type=activity_type,
        co2e_multiplier=Decimal(str(multiplier)),
        unit=unit,
        scope=scope,
        factor_source=source,
        factor_set=factor_set,
        country=country,
        provider_key=provider_key,
        natural_key=(str(year), activity_type, country, unit or "", scope or ""),
    )

@pytest.fixture(scope="module")
def seai_and_defra_diesel(db_conn, db_url, seai_data):
    """Return ``(seai_diesel, defra_diesel)`` backend factors from the DB."""
    factors, skipped = map_all(list(seai_data.rows))
    load_to_db(factors, skipped, db_url, source_checksum=seai_data.meta.file_sha256)

    seai = None
    defra = None
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT activity_type, co2e_multiplier, unit, scope, factor_source, "
            "factor_set, country, reporting_year, import_batch_id "
            "FROM public.emission_factors "
            "WHERE country = 'IE' AND factor_source = 'SEAI' "
            "AND activity_type ILIKE 'Fuels > Liquid fuels > Diesel /%' "
            "AND unit = 'litres'"
        )
        row = cur.fetchone()
        assert row is not None, "SEAI diesel factor not found in test DB"
        seai = _backend_factor(row, "seai")

        cur.execute(
            "SELECT activity_type, co2e_multiplier, unit, scope, factor_source, "
            "factor_set, country, reporting_year, import_batch_id "
            "FROM public.emission_factors "
            "WHERE country = 'GB' AND unit = 'litres' "
            "AND (activity_type ILIKE '%Diesel%' OR activity_type ILIKE '%diesel%') "
            "ORDER BY activity_type LIMIT 1"
        )
        row = cur.fetchone()
        if row is not None:
            defra = _backend_factor(row, "defra")
    if defra is None:
        defra = EmissionFactor(
            id="f-defra-fallback-diesel",
            natural_key=(
                str(FALLBACK_DEFRA_DIESEL["reporting_year"]),
                FALLBACK_DEFRA_DIESEL["activity_type"],
                "GB", "litres", "Scope 1",
            ),
            **FALLBACK_DEFRA_DIESEL,
        )
    return seai, defra


def _match(engine, activity: str, country: str, unit: str, scope: str) -> Any:
    request = MatchRequest(
        id=f"req-{country}-{activity[:8]}",
        activity=activity,
        country=country,
        reporting_year=2025,
        unit=unit,
        scope=scope,
        organization_id="org-test",
        max_stages=6,
    )
    return engine.match(request)


def test_country_selection_prevents_gb_ie_confusion(seai_and_defra_diesel):
    seai, defra = seai_and_defra_diesel
    assert seai.country == "IE" and defra.country == "GB"
    index = FactorSearchIndex()
    index.load([seai, defra])
    stages = build_matching_pipeline(MatchingPipelineConfig())
    engine = FactorMatchingEngine(index, stages)

    # The same user activity resolves to the correct factor per country.
    gb = _match(engine, "Diesel", "GB", "litres", "Scope 1")
    assert gb.status == "matched"
    assert gb.factor.country == "GB"
    assert gb.factor.factor_source == "DEFRA-DESNZ"

    ie = _match(engine, "Diesel", "IE", "litres", "Scope 1")
    assert ie.status == "matched"
    assert ie.factor.country == "IE"
    assert ie.factor.factor_source == "SEAI"
    assert ie.factor.activity_type == seai.activity_type


def test_defra_gb_matching_still_works(seai_and_defra_diesel):
    seai, defra = seai_and_defra_diesel
    index = FactorSearchIndex()
    index.load([seai, defra])
    engine = FactorMatchingEngine(index, build_matching_pipeline(MatchingPipelineConfig()))

    result = _match(engine, "Diesel", "GB", "litres", "Scope 1")
    assert result.status == "matched"
    assert result.factor.country == "GB"
    assert result.factor.provider_key == "defra"


class _FakeSink:
    """Minimal in-memory CalculationSink."""

    def __init__(self) -> None:
        self.snapshots: list[CalculationSnapshot] = []
        self.logs: list[EmissionLog] = []

    async def save_snapshot(self, snapshot, *, activity, activity_type,
                            factor_source=None, factor_set=None,
                            import_batch_id=None, calculated_by=None,
                            factor_kind=None, customer_factor_id=None):
        self.snapshots.append(snapshot)
        return snapshot

    async def create(self, org_id, factor_id, quantity, unit, scope, date,
                     asset_id, facility_id, snapshot_id):
        log = EmissionLog(
            id="log-1", organization_id=org_id, factor_id=factor_id,
            quantity=quantity, date=date, unit=unit, scope=scope,
            snapshot_id=snapshot_id,
        )
        self.logs.append(log)
        return log

    async def save(self, entity: EmissionLog) -> EmissionLog:
        for i, log in enumerate(self.logs):
            if log.id == entity.id:
                self.logs[i] = entity
                return entity
        self.logs.append(entity)
        return entity


def test_calculation_with_seai_factor_unchanged(seai_and_defra_diesel):
    seai, _ = seai_and_defra_diesel
    engine = CalculationEngine(_FakeSink())
    request = CalculationRequest(
        match_request_id="req-calc-1",
        organization_id="org-test",
        factor=seai,
        quantity=Decimal("100"),
        quantity_unit="litres",
        date=date(2025, 6, 1),
        reporting_year=2025,
        activity="Diesel / gasoil (100% petroleum)",
        activity_type=seai.activity_type,
        scope="Scope 1",
    )
    result = engine.calculate(request)
    assert float(result.co2e_kg) == pytest.approx(268.2327, abs=1e-6)
    assert result.snapshot.factor_id == seai.id
    assert engine.verify(result.snapshot).match


def test_domain_calculation_contract_unchanged(seai_and_defra_diesel):
    """Domain-level arithmetic (quantity x multiplier) is unchanged."""
    seai, _ = seai_and_defra_diesel
    assert float(seai.calculate_emissions(Decimal("1000"), "litres")) == pytest.approx(
        float(seai.co2e_multiplier * Decimal("1000")), abs=1e-6
    )

