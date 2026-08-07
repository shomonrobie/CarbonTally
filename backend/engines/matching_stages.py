"""Concrete matching stages (Backend v2.1 §7, §11, CT-ARCH-006).

Each stage implements :class:`domain.matching.MatchingStage` — one step of the
matching pipeline with a single responsibility. Stages are stateless (built
fresh per pipeline) and never perform calculations (CT-ARCH-004); they only
match a :class:`domain.matching.MatchRequest` against the search index and
return a :class:`domain.matching.StageResult`.

Priority follows CT-ARCH-006: exact, natural-key, alias, keyword, fuzzy, then
semantic (AI ranking — future).

Dependency rules: this module imports from ``core`` (logging), the ``domain``
package (matching contracts) and, for the alias repository adapter, the
repository layer. It contains no business policy beyond per-stage matching
mechanics — pipeline order and thresholds live in ``MatchingPipelineConfig``
and the engine.
"""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Awaitable, Callable, Optional

from core.logging import get_logger
from data.factor_aliases import FactorAliasesRepository
from domain.factor import EmissionFactor
from domain.matching import FactorSearch, MatchRequest, MatchingStage, StageResult

logger = get_logger(__name__)

#: Resolves an activity alias to its target activity type (or ``None``).
AliasResolver = Callable[[str, Optional[str]], Awaitable[Optional[str]]]


class RepositoryAliasResolver:
    """Adapter turning ``FactorAliasesRepository`` into an :data:`AliasResolver`.

    Org-scoped aliases are checked first, then global aliases (the repository's
    ``find_by_alias`` contract).
    """

    def __init__(self, repository: FactorAliasesRepository) -> None:
        if repository is None:
            raise ValueError("repository must not be None")
        self._repository = repository

    async def __call__(
        self, alias_text: str, organization_id: Optional[str]
    ) -> Optional[str]:
        alias = await self._repository.find_by_alias(alias_text, organization_id)
        return alias.target_activity_type if alias is not None else None


#: Retrieval breadth used by stages that need to inspect exact activity matches.
_LARGE_LIMIT = 500


def _exact_activity_matches(
    request: MatchRequest, index: FactorSearch, activity: str
) -> list[EmissionFactor]:
    """Return factors whose activity type equals ``activity`` (case-insensitive)."""
    results = index.keyword_search(
        activity,
        unit=request.unit,
        country=request.country,
        provider=request.preferred_provider,
        limit=_LARGE_LIMIT,
    )
    needle = activity.casefold()
    return [factor for factor, _score in results if factor.activity_type.casefold() == needle]


class ExactMatchStage(MatchingStage):
    """Highest-priority stage: the request activity equals a factor's activity type."""

    @property
    def name(self) -> str:
        return "exact_match"

    async def execute(self, request: MatchRequest, index: FactorSearch) -> StageResult:
        exact = _exact_activity_matches(request, index, request.activity)
        if len(exact) == 1:
            factor = exact[0]
            return StageResult(
                stage_name=self.name,
                matched=True,
                factor=factor,
                confidence=1.0,
                score=1.0,
                reason="exact activity match",
                provider=factor.provider_key,
                is_definitive=True,
            )
        if len(exact) > 1:
            return StageResult(
                stage_name=self.name,
                matched=False,
                confidence=0.0,
                score=1.0,
                reason=f"exact activity match is ambiguous ({len(exact)} candidates)",
            )
        return StageResult(
            stage_name=self.name,
            matched=False,
            reason="no exact activity match",
        )


class NaturalKeyStage(MatchingStage):
    """Matches the RC2 natural key ``(year, activity, country, unit, scope)``."""

    @property
    def name(self) -> str:
        return "natural_key"

    async def execute(self, request: MatchRequest, index: FactorSearch) -> StageResult:
        key = (
            str(request.reporting_year),
            request.activity,
            request.country,
            request.unit or "",
            request.scope or "",
        )
        factor = index.exact_natural_key(key)
        if factor is not None:
            return StageResult(
                stage_name=self.name,
                matched=True,
                factor=factor,
                confidence=1.0,
                score=1.0,
                reason="natural-key match",
                provider=factor.provider_key,
                is_definitive=True,
            )
        return StageResult(
            stage_name=self.name,
            matched=False,
            reason="no natural-key match",
        )


class KeywordSearchStage(MatchingStage):
    """Token-overlap retrieval above a minimum confidence (CT-ARCH-006 keyword)."""

    def __init__(self, min_confidence: float = 0.80) -> None:
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be in [0, 1]")
        self._min_confidence = min_confidence

    @property
    def name(self) -> str:
        return "keyword_search"

    @property
    def min_confidence(self) -> float:
        """The confidence floor below which a keyword match is not accepted."""
        return self._min_confidence

    async def execute(self, request: MatchRequest, index: FactorSearch) -> StageResult:
        results = index.keyword_search(
            request.activity,
            unit=request.unit,
            country=request.country,
            provider=request.preferred_provider,
            limit=1,
        )
        if results:
            factor, score = results[0]
            if score >= self._min_confidence:
                return StageResult(
                    stage_name=self.name,
                    matched=True,
                    factor=factor,
                    confidence=score,
                    score=score,
                    reason="keyword match",
                    provider=factor.provider_key,
                    is_definitive=False,
                )
        return StageResult(
            stage_name=self.name,
            matched=False,
            reason="no keyword match above threshold",
        )


class AliasMatchStage(MatchingStage):
    """Resolves an organisation/global alias to a factor activity (CT-ARCH-006)."""

    def __init__(self, resolver: Optional[AliasResolver] = None) -> None:
        self._resolver = resolver

    @property
    def name(self) -> str:
        return "alias_match"

    async def execute(self, request: MatchRequest, index: FactorSearch) -> StageResult:
        if self._resolver is None:
            return StageResult(
                stage_name=self.name,
                matched=False,
                reason="no alias resolver configured",
            )
        target = await self._resolver(request.activity, request.organization_id)
        if target is None:
            return StageResult(
                stage_name=self.name,
                matched=False,
                reason="no alias resolves the activity",
            )
        exact = _exact_activity_matches(request, index, target)
        if len(exact) == 1:
            factor = exact[0]
            return StageResult(
                stage_name=self.name,
                matched=True,
                factor=factor,
                confidence=1.0,
                score=1.0,
                reason="alias match",
                provider=factor.provider_key,
                is_definitive=True,
            )
        if len(exact) > 1:
            return StageResult(
                stage_name=self.name,
                matched=False,
                confidence=0.0,
                score=1.0,
                reason=f"alias target is ambiguous ({len(exact)} candidates)",
            )
        return StageResult(
            stage_name=self.name,
            matched=False,
            reason="alias target not found in index",
        )


class FuzzyMatchStage(MatchingStage):
    """String-similarity fallback above a threshold (CT-ARCH-006 fuzzy)."""

    def __init__(self, threshold: float = 0.85) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be in [0, 1]")
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "fuzzy_match"

    @property
    def threshold(self) -> float:
        """The similarity floor below which a fuzzy match is not accepted."""
        return self._threshold

    async def execute(self, request: MatchRequest, index: FactorSearch) -> StageResult:
        results = index.keyword_search(
            request.activity,
            unit=request.unit,
            country=request.country,
            provider=request.preferred_provider,
            limit=200,
        )
        best: Optional[tuple[EmissionFactor, float]] = None
        query = request.activity.casefold()
        for factor, _score in results:
            ratio = SequenceMatcher(None, query, factor.activity_type.casefold()).ratio()
            if best is None or ratio > best[1]:
                best = (factor, ratio)
        if best is not None and best[1] >= self._threshold:
            factor, ratio = best
            return StageResult(
                stage_name=self.name,
                matched=True,
                factor=factor,
                confidence=ratio,
                score=ratio,
                reason="fuzzy match",
                provider=factor.provider_key,
                is_definitive=False,
            )
        return StageResult(
            stage_name=self.name,
            matched=False,
            reason="no fuzzy match above threshold",
        )


#: Semantic (embedding) similarity function between two activity strings.
SemanticScorer = Callable[[str, str], float]


class SemanticMatchStage(MatchingStage):
    """Semantic (AI/embedding) matching — the future AI ranking step (CT-ARCH-006).

    The stage is an extension point: it is inert unless enabled **and** supplied
    with a :data:`SemanticScorer`. ``MatchingPipelineConfig.semantic_enabled``
    defaults to ``False`` and no LLM/embedding client exists before the AI
    phases, so the pipeline builder constructs the stage without a scorer.
    """

    def __init__(
        self,
        enabled: bool = False,
        min_confidence: float = 0.70,
        scorer: Optional[SemanticScorer] = None,
    ) -> None:
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be in [0, 1]")
        self._enabled = enabled
        self._min_confidence = min_confidence
        self._scorer = scorer

    @property
    def name(self) -> str:
        return "semantic_match"

    async def execute(self, request: MatchRequest, index: FactorSearch) -> StageResult:
        if not self._enabled:
            return StageResult(
                stage_name=self.name,
                matched=False,
                reason="semantic matching is disabled",
            )
        if self._scorer is None:
            return StageResult(
                stage_name=self.name,
                matched=False,
                reason="semantic matching is not configured (no scorer)",
            )
        results = index.keyword_search(
            request.activity,
            unit=request.unit,
            country=request.country,
            provider=request.preferred_provider,
            limit=200,
        )
        best: Optional[tuple[EmissionFactor, float]] = None
        for factor, _score in results:
            similarity = self._scorer(request.activity, factor.activity_type)
            if best is None or similarity > best[1]:
                best = (factor, similarity)
        if best is not None and best[1] >= self._min_confidence:
            factor, similarity = best
            return StageResult(
                stage_name=self.name,
                matched=True,
                factor=factor,
                confidence=similarity,
                score=similarity,
                reason="semantic match",
                provider=factor.provider_key,
                is_definitive=False,
            )
        return StageResult(
            stage_name=self.name,
            matched=False,
            reason="no semantic match above threshold",
        )


