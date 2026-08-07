"""Unit tests for domain.matching."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from domain.factor import EmissionFactor
from domain.matching import (
    FactorAlias,
    FactorSearch,
    MatchRequest,
    MatchResult,
    MatchingPipelineConfig,
    MatchingStage,
    StageResult,
    Suggestion,
)


def make_factor() -> EmissionFactor:
    return EmissionFactor(
        id="f-1",
        reporting_year=2025,
        activity_type="Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]",
        co2e_multiplier=Decimal("0.184"),
        unit="kWh",
        scope="Scope 1",
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
        provider_key="defra",
    )


class TestMatchRequest:
    def test_constructs(self) -> None:
        req = MatchRequest(
            id="mr-1", activity="natural gas", country="GB", reporting_year=2025
        )
        assert req.max_stages == 6

    def test_is_immutable(self) -> None:
        req = MatchRequest(
            id="mr-1", activity="natural gas", country="GB", reporting_year=2025
        )
        with pytest.raises(FrozenInstanceError):
            req.activity = "diesel"  # type: ignore[misc]

    def test_rejects_empty_activity(self) -> None:
        with pytest.raises(ValueError):
            MatchRequest(id="mr-1", activity="", country="GB", reporting_year=2025)

    def test_rejects_max_stages_below_one(self) -> None:
        with pytest.raises(ValueError):
            MatchRequest(
                id="mr-1", activity="gas", country="GB", reporting_year=2025, max_stages=0
            )

    def test_rejects_implausible_year(self) -> None:
        with pytest.raises(ValueError):
            MatchRequest(id="mr-1", activity="gas", country="GB", reporting_year=1899)


class TestStageResult:
    def test_matched_requires_factor(self) -> None:
        with pytest.raises(ValueError):
            StageResult(stage_name="exact", matched=True)

    def test_unmatched_must_not_have_factor(self) -> None:
        with pytest.raises(ValueError):
            StageResult(stage_name="exact", matched=False, factor=make_factor())

    def test_confidence_range(self) -> None:
        with pytest.raises(ValueError):
            StageResult(stage_name="exact", matched=False, confidence=1.5)

    def test_score_range(self) -> None:
        with pytest.raises(ValueError):
            StageResult(stage_name="exact", matched=False, score=-0.1)

    def test_matched(self) -> None:
        result = StageResult(
            stage_name="exact",
            matched=True,
            factor=make_factor(),
            confidence=1.0,
            score=1.0,
            reason="exact activity match",
            provider="defra",
            is_definitive=True,
        )
        assert result.provider == "defra"
        assert result.is_definitive is True


class TestMatchResult:
    def test_no_match_helper(self) -> None:
        suggestion = Suggestion(factor=make_factor(), score=0.9, reason="similar", stage="fuzzy")
        result = MatchResult.no_match(
            suggestions=[suggestion],
            stages_executed=["exact", "fuzzy"],
            request_id="mr-1",
        )
        assert result.status == "no_match"
        assert result.factor is None
        assert result.suggestions == (suggestion,)
        assert result.stages_executed == ("exact", "fuzzy")
        assert result.request_id == "mr-1"

    def test_matched_must_include_factor(self) -> None:
        with pytest.raises(ValueError):
            MatchResult(status="matched")

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValueError):
            MatchResult(status="weird")

    def test_is_immutable(self) -> None:
        result = MatchResult.no_match([], ["exact"])
        with pytest.raises(FrozenInstanceError):
            result.status = "matched"  # type: ignore[misc]


class TestFactorAlias:
    def test_constructs(self) -> None:
        alias = FactorAlias(
            id="a-1",
            organization_id="org-1",
            alias_text="NG",
            target_activity_type="Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]",
            target_provider_key="defra",
            created_by="user-1",
            created_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
        )
        assert alias.alias_text == "NG"


class TestMatchingPipelineConfig:
    def test_defaults(self) -> None:
        config = MatchingPipelineConfig()
        assert config.fuzzy_threshold == 0.85
        assert config.semantic_enabled is False
        assert config.stages[0] == "exact_match"

    def test_threshold_range(self) -> None:
        with pytest.raises(ValueError):
            MatchingPipelineConfig(fuzzy_threshold=1.5)

    def test_max_suggestions_range(self) -> None:
        with pytest.raises(ValueError):
            MatchingPipelineConfig(max_suggestions=0)


class TestMatchingStageContract:
    """MatchingStage/FactorSearch are typable contracts used by Phase 4 stages."""

    def test_protocol_shape(self) -> None:
        # Structural check: a class with the required methods satisfies the
        # FactorSearch protocol at runtime via isinstance.
        assert hasattr(FactorSearch, "exact_natural_key")
        assert hasattr(FactorSearch, "keyword_search")

    def test_stage_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            MatchingStage()  # type: ignore[abstract]
