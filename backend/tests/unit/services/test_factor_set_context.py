"""031 — effective factor-set context (constrains factor matching; no jurisdiction in the mapper).

Locks the PO decision that DEFRA/UK is the default set while other sets stay selectable: the mapping
stage must pass the *effective* (country, provider) into the matching pipeline instead of a literal.
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from types import SimpleNamespace

from domain.automatic_processing import AutomaticProcessingJob
from domain.matching import MatchResult
from services import automatic_processing as ap

ORG = "00000000-0000-4000-8000-000000000001"
FACTOR = SimpleNamespace(
    id="factor-1", activity_type="Diesel (average biofuel blend)", unit="litres", scope="scope_1"
)


class _RecordingMatcher:
    def __init__(self) -> None:
        self.requests: list = []

    async def match(self, request):
        self.requests.append(request)
        return MatchResult(status="matched", factor=FACTOR, confidence=1.0,
                           methodology="keyword_search", stages_executed=("keyword_search",))


class _Recorder:
    async def save_mapped_data(self, *a, **k):
        return None

    async def advance_stage(self, *a, **k):
        return None

    async def mark_blocked(self, *a, **k):
        return None

    async def mark_failed(self, *a, **k):
        return None


def _job(metadata):
    return AutomaticProcessingJob(
        id=str(uuid.uuid4()),
        organization_id=ORG,
        file_name="invoice.pdf",
        file_url="uploads/org-1/invoice.pdf",
        file_type="PDF",
        stage="mapping",
        status="processing",
        metadata=metadata,
        source_item_id=None,
        extracted_data={"date": "2026-05-08", "line_items": [
            {"activity": "Diesel", "quantity": 10.0, "unit": "litres",
             "line_number": 1, "source_line": "Diesel supply 10 L"},
        ]},
    )


def _service(matcher):
    recorder = _Recorder()
    repos = SimpleNamespace(
        processing=recorder, manual_extraction=recorder,
        factors=SimpleNamespace(get=lambda *a, **k: None,
                                find_by_activity=None),
        customer_factors=SimpleNamespace(get=lambda *a, **k: None),
        evidence_line_items=None, logs=None, notifications=None,
    )
    return ap.AutomaticProcessingService(repos, matching_engine=matcher)


# -- the context helper ------------------------------------------------------
def test_default_factor_set_is_defra_uk() -> None:
    assert ap.factor_set_context(None) == ("GB", "defra")
    assert ap.factor_set_context({}) == ("GB", "defra")
    assert ap.factor_set_context({"factor_country": "  ", "factor_provider": ""}) == (
        "GB", "defra",
    )


def test_default_provider_uses_the_index_provider_key_vocabulary() -> None:
    """G-1 regression — the default provider must speak the factor index's vocabulary.

    ``EmissionFactor.provider_key`` is sourced from ``import_batches.provider_key`` (``defra`` /
    ``seai``), whereas ``factor_source`` is the presentation label (``DEFRA-DESNZ``).
    ``FactorSearchIndex.keyword_search`` filters candidates by STRICT equality on
    ``provider_key``, so a default written in the label vocabulary silently drops every candidate
    and the real pipeline reports ``no_match`` for exactly the requests the direct
    ``POST /api/v2/factor-match`` probe matches.
    """
    assert ap.DEFAULT_FACTOR_PROVIDER == "defra"
    assert ap.DEFAULT_FACTOR_PROVIDER != "DEFRA-DESNZ"  # the factor_source label, never the filter


def test_document_level_override_selects_another_factor_set() -> None:
    # e.g. an Irish document selecting the SEAI set — data-driven, not hard-coded to two sets.
    assert ap.factor_set_context({"factor_country": "IE", "factor_provider": "SEAI"}) == (
        "IE", "SEAI",
    )
    assert ap.factor_set_context({"factor_provider": "SEAI"}) == ("GB", "SEAI")
    assert ap.factor_set_context({"factor_country": "IE"}) == ("IE", "defra")


def test_non_mapping_metadata_is_tolerated() -> None:
    assert ap.factor_set_context("not-a-dict") == ("GB", "defra")


# -- the matching pipeline receives the effective context --------------------
async def test_mapping_request_carries_the_effective_factor_set() -> None:
    matcher = _RecordingMatcher()
    service = _service(matcher)
    assert await service._map(_job({"mime": "application/pdf"}), "token") == "validating"
    assert len(matcher.requests) == 1
    request = matcher.requests[0]
    assert request.country == "GB"
    assert request.preferred_provider == "defra"


async def test_mapping_request_honours_a_document_override() -> None:
    matcher = _RecordingMatcher()
    service = _service(matcher)
    await service._map(
        _job({"factor_country": "IE", "factor_provider": "SEAI"}), "token"
    )
    request = matcher.requests[0]
    assert request.country == "IE"
    assert request.preferred_provider == "SEAI"


def test_no_jurisdiction_is_derived_from_activity_text() -> None:
    # The context is explicit selection only: metadata keys, never activity keywords.
    assert ap.factor_set_context({"activity": "Irish diesel", "supplier": "SEAI Fuels"}) == (
        "GB", "defra",
    )


# -- the default provider must be usable by the REAL matcher (G-1) -----------
def _gas_factors(activity: str = "Fuels > Gas fuels > Natural gas (kg CO2e)") -> list:
    """The two DEFRA gas kWh bases, carrying the index's real ``provider_key`` vocabulary."""
    from domain.factor import EmissionFactor

    return [
        EmissionFactor(
            id=factor_id,
            reporting_year=2025,
            activity_type=f"{activity} [{unit}]",
            co2e_multiplier=Decimal(multiplier),
            unit=unit,
            scope="Scope 1",
            factor_source="DEFRA-DESNZ",
            factor_set="DEFRA-2025",
            country="GB",
            provider_key="defra",
            natural_key=("2025", f"{activity} [{unit}]", "GB", unit, "Scope 1"),
        )
        for factor_id, unit, multiplier in (
            ("f-gross", "kWh (Gross CV)", "0.18494"),
            ("f-net", "kWh (Net CV)", "0.20489"),
        )
    ]


async def test_pipeline_default_provider_reaches_the_real_matcher() -> None:
    """G-1 regression: a gas ``kWh`` request built with the pipeline default still matches.

    Runs the REAL engine over the REAL index with factors carrying ``provider_key='defra'`` — the
    same strict provider filter that emptied the candidate set in the live pipeline — and pins the
    historical label as the *defect* case (labels are not provider keys).
    """
    from domain.matching import MatchRequest, MatchingPipelineConfig
    from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline
    from infra.search_index import FactorSearchIndex

    index = FactorSearchIndex()
    index.load(_gas_factors())
    config = MatchingPipelineConfig()
    engine = FactorMatchingEngine(index, build_matching_pipeline(config), config=config)

    def _request(provider):
        return MatchRequest(
            id=str(uuid.uuid4()), activity="Natural gas", country="GB", reporting_year=2025,
            unit="kWh", organization_id=ORG, preferred_provider=provider, max_stages=6,
        )

    matched = await engine.match(_request(ap.DEFAULT_FACTOR_PROVIDER))
    assert matched.status == "matched", matched.stages_executed
    assert matched.factor is not None and matched.factor.id == "f-net"
    assert matched.confidence == 1.0
    assert matched.methodology == "calorific_basis"

    # the historical label is not a provider key → every candidate is filtered out (the defect)
    assert (await engine.match(_request("DEFRA-DESNZ"))).status == "no_match"
