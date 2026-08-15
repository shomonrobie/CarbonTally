"""Factor-matching domain objects (Backend v2.1 §9, ADR-10, §16 matching).

``MatchingStage`` is the contract every matching stage implements;
``FactorSearch`` is the domain-facing contract of the search index (implemented
by ``infra.search_index`` in Phase 3). Pure Python, immutable frozen dataclasses.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol

from domain.factor import EmissionFactor


class FactorSearch(Protocol):
    """Contract for the factor search index used by matching stages.

    Implemented by ``infra.search_index.FactorSearchIndex`` (Phase 3).
    """

    def exact_natural_key(self, key: tuple[str, ...]) -> Optional[EmissionFactor]: ...

    def keyword_search(
        self,
        query: str,
        unit: Optional[str] = None,
        country: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 10,
    ) -> list[tuple[EmissionFactor, float]]: ...


class MatchingStage(ABC):
    """Contract for one stage of the matching pipeline.

    Concrete stages (Phase 4: exact, natural-key, alias, keyword, fuzzy,
    semantic) implement :meth:`execute`.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stage's unique name (e.g. ``keyword_search``)."""

    @abstractmethod
    async def execute(self, request: MatchRequest, index: FactorSearch) -> StageResult:
        """Run this stage against ``request`` using ``index``."""


@dataclass(frozen=True, slots=True)
class MatchRequest:
    """A request to match a consumption activity to an emission factor."""

    id: str
    activity: str
    country: str
    reporting_year: int
    unit: Optional[str] = None
    scope: Optional[str] = None
    organization_id: Optional[str] = None
    preferred_provider: Optional[str] = None
    max_stages: int = 6

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id must not be empty")
        if not self.activity:
            raise ValueError("activity must not be empty")
        if not (1990 <= self.reporting_year <= 2100):
            raise ValueError(
                f"reporting_year {self.reporting_year} outside supported range 1990-2100"
            )
        if self.max_stages < 1:
            raise ValueError("max_stages must be >= 1")


@dataclass(frozen=True, slots=True)
class StageResult:
    """The outcome of a single matching stage."""

    stage_name: str
    matched: bool
    factor: Optional[EmissionFactor] = None
    confidence: float = 0.0
    score: float = 0.0
    reason: str = ""
    provider: Optional[str] = None
    is_definitive: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be in [0, 1]")
        if self.matched and self.factor is None:
            raise ValueError("a matching stage must return the factor it matched")
        if not self.matched and self.factor is not None:
            raise ValueError("a non-matching stage must not return a factor")


@dataclass(frozen=True, slots=True)
class Suggestion:
    """An alternative factor offered to the customer for manual selection."""

    factor: EmissionFactor
    score: float
    reason: str
    stage: str


@dataclass(frozen=True, slots=True)
class MatchResult:
    """The final outcome of a matching pipeline run.

    V3 (D-cf-5): a match may resolve to a CarbonTally-managed factor
    (``factor_kind='emission_factor'``) or an approved customer factor
    (``factor_kind='customer_factor'`` + ``customer_factor_id``). Exactly one
    source applies per match.
    """

    status: str
    factor: Optional[EmissionFactor] = None
    confidence: float = 0.0
    methodology: str = ""
    provider: Optional[str] = None
    stages_executed: tuple[str, ...] = ()
    suggestions: tuple[Suggestion, ...] = ()
    processing_time_ms: int = 0
    request_id: str = ""
    factor_kind: str = "emission_factor"
    customer_factor_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status not in ("matched", "no_match", "ambiguous"):
            raise ValueError(
                f"status {self.status!r} must be 'matched', 'no_match' or 'ambiguous'"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if self.status == "matched" and self.factor is None and not self.customer_factor_id:
            raise ValueError(
                "a matched result must include the factor or customer_factor_id"
            )
        if self.factor_kind not in ("emission_factor", "customer_factor"):
            raise ValueError(
                f"factor_kind {self.factor_kind!r} must be 'emission_factor' or 'customer_factor'"
            )
        if self.factor_kind == "customer_factor" and self.status == "matched" and not self.customer_factor_id:
            raise ValueError(
                "a customer-factor match must carry customer_factor_id"
            )
        if self.factor_kind == "emission_factor" and self.customer_factor_id:
            raise ValueError(
                "an emission-factor match must not carry customer_factor_id"
            )

    @staticmethod
    def no_match(
        suggestions: list[Suggestion],
        stages_executed: list[str],
        request_id: str = "",
    ) -> MatchResult:
        """Build a ``no_match`` result carrying manual-selection suggestions."""
        return MatchResult(
            status="no_match",
            suggestions=tuple(suggestions),
            stages_executed=tuple(stages_executed),
            request_id=request_id,
        )


@dataclass(frozen=True, slots=True)
class FactorAlias:
    """A customer-supplied synonym mapping to a factor activity type.

    Mirrors the RC2 ``factor_aliases`` table.
    """

    id: str
    organization_id: Optional[str]
    alias_text: str
    target_activity_type: str
    target_provider_key: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class MatchingPipelineConfig:
    """Tuning parameters for the matching pipeline."""

    stages: tuple[str, ...] = (
        "exact_match",
        "natural_key",
        "alias_match",
        "keyword_search",
        "fuzzy_match",
    )
    fuzzy_threshold: float = 0.85
    keyword_min_confidence: float = 0.80
    semantic_enabled: bool = False
    semantic_min_confidence: float = 0.70
    max_suggestions: int = 10
    prefer_provider: Optional[str] = None
    restrict_country: Optional[str] = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.fuzzy_threshold <= 1.0:
            raise ValueError("fuzzy_threshold must be in [0, 1]")
        if not 0.0 <= self.keyword_min_confidence <= 1.0:
            raise ValueError("keyword_min_confidence must be in [0, 1]")
        if not 0.0 <= self.semantic_min_confidence <= 1.0:
            raise ValueError("semantic_min_confidence must be in [0, 1]")
        if self.max_suggestions < 1:
            raise ValueError("max_suggestions must be >= 1")

