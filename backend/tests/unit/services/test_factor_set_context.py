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
    assert ap.factor_set_context(None) == ("GB", "DEFRA-DESNZ")
    assert ap.factor_set_context({}) == ("GB", "DEFRA-DESNZ")
    assert ap.factor_set_context({"factor_country": "  ", "factor_provider": ""}) == (
        "GB", "DEFRA-DESNZ",
    )


def test_document_level_override_selects_another_factor_set() -> None:
    # e.g. an Irish document selecting the SEAI set — data-driven, not hard-coded to two sets.
    assert ap.factor_set_context({"factor_country": "IE", "factor_provider": "SEAI"}) == (
        "IE", "SEAI",
    )
    assert ap.factor_set_context({"factor_provider": "SEAI"}) == ("GB", "SEAI")
    assert ap.factor_set_context({"factor_country": "IE"}) == ("IE", "DEFRA-DESNZ")


def test_non_mapping_metadata_is_tolerated() -> None:
    assert ap.factor_set_context("not-a-dict") == ("GB", "DEFRA-DESNZ")


# -- the matching pipeline receives the effective context --------------------
async def test_mapping_request_carries_the_effective_factor_set() -> None:
    matcher = _RecordingMatcher()
    service = _service(matcher)
    assert await service._map(_job({"mime": "application/pdf"}), "token") == "validating"
    assert len(matcher.requests) == 1
    request = matcher.requests[0]
    assert request.country == "GB"
    assert request.preferred_provider == "DEFRA-DESNZ"


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
        "GB", "DEFRA-DESNZ",
    )
