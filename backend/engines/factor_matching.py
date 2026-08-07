"""Factor Matching Engine (Backend v2.1 §7, §11, CT-ARCH-004/006/014).

Orchestrates the matching pipeline: it runs the configured stages in order over
the :class:`domain.matching.FactorSearch` index and produces a
:class:`domain.matching.MatchResult`. The engine:

* never performs calculations (CT-ARCH-004),
* returns every match with its confidence score, matching method and provider
  (CT-ARCH-006), and
* records each outcome through the event bus and audit logger when wired
  (CT-ARCH-014 explainability).

The event bus is used fire-and-forget for the published outcome events (§4.2);
audit entries are awaited best-effort and never break the match.

Dependency rules: this module imports from ``core`` (logging), ``domain``
(matching contracts and events), ``infra`` (event bus, audit logger) and the
matching stages. It is stateless per request — the composition root creates a
new engine per request (DI graph §4.1).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Callable, Optional, Sequence

from core.logging import get_logger
from domain.matching import (
    FactorSearch,
    MatchRequest,
    MatchResult,
    MatchingPipelineConfig,
    MatchingStage,
    Suggestion,
)
from domain.workflow import DomainEvent, FactorMatched, FactorNotFound
from engines.matching_stages import (
    AliasMatchStage,
    AliasResolver,
    ExactMatchStage,
    FuzzyMatchStage,
    KeywordSearchStage,
    NaturalKeyStage,
    SemanticMatchStage,
)
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus

logger = get_logger(__name__)


class FactorMatchingEngine:
    """Runs the matching pipeline against a search index.

    Args:
        index: The factor search index (Phase 3 ``FactorSearchIndex``).
        stages: Ordered matching stages (see :func:`build_matching_pipeline`).
        config: Pipeline tuning; defaults to :class:`MatchingPipelineConfig`.
        event_bus: Optional bus that receives ``FactorMatched``/``FactorNotFound``
            outcome events (fire-and-forget).
        audit_logger: Optional logger that records every match outcome.
    """

    def __init__(
        self,
        index: FactorSearch,
        stages: Sequence[MatchingStage],
        *,
        config: Optional[MatchingPipelineConfig] = None,
        event_bus: Optional[EventBus] = None,
        audit_logger: Optional[AuditLogger] = None,
    ) -> None:
        if not stages:
            raise ValueError("stages must not be empty")
        self._index = index
        self._stages = list(stages)
        self._config = config or MatchingPipelineConfig()
        self._event_bus = event_bus
        self._audit_logger = audit_logger

    @property
    def stages(self) -> tuple[str, ...]:
        """The configured stage names, in execution order."""
        return tuple(stage.name for stage in self._stages)

    @property
    def config(self) -> MatchingPipelineConfig:
        """The pipeline tuning in effect."""
        return self._config

    async def match(self, request: MatchRequest) -> MatchResult:
        """Run the pipeline and produce the final :class:`MatchResult`."""
        stages_executed: list[str] = []
        for stage in self._stages[: request.max_stages]:
            stage_result = await stage.execute(request, self._index)
            stages_executed.append(stage.name)
            if stage_result.matched:
                outcome = MatchResult(
                    status="matched",
                    factor=stage_result.factor,
                    confidence=stage_result.confidence,
                    methodology=stage_result.stage_name,
                    provider=stage_result.provider,
                    stages_executed=tuple(stages_executed),
                    request_id=request.id,
                )
                return await self._finalize(request, outcome)
            if stage_result.score >= 1.0:
                suggestions = await self._suggestions(request)
                outcome = MatchResult(
                    status="ambiguous",
                    suggestions=tuple(suggestions),
                    stages_executed=tuple(stages_executed),
                    request_id=request.id,
                )
                return await self._finalize(request, outcome)
        suggestions = await self._suggestions(request)
        outcome = MatchResult.no_match(
            suggestions=suggestions,
            stages_executed=stages_executed,
            request_id=request.id,
        )
        return await self._finalize(request, outcome)

    async def _suggestions(self, request: MatchRequest) -> list[Suggestion]:
        """Collect ranked candidates for a no-match/ambiguous result."""
        results = self._index.keyword_search(
            request.activity,
            unit=request.unit,
            country=request.country,
            provider=request.preferred_provider,
            limit=self._config.max_suggestions,
        )
        return [
            Suggestion(
                factor=factor,
                score=score,
                reason="retrieved candidate",
                stage="keyword_search",
            )
            for factor, score in results
            if score > 0.0
        ]

    async def _finalize(
        self, request: MatchRequest, outcome: MatchResult
    ) -> MatchResult:
        """Publish the outcome event and audit entry, then return the result."""
        await self._publish_event(request, outcome)
        await self._audit(request, outcome)
        return outcome

    async def _publish_event(
        self, request: MatchRequest, outcome: MatchResult
    ) -> None:
        """Publish ``FactorMatched``/``FactorNotFound`` on the bus (fire-and-forget)."""
        if self._event_bus is None:
            return
        event: Optional[DomainEvent] = None
        occurred_at = datetime.now(timezone.utc)
        if outcome.status == "matched":
            event = FactorMatched(
                event_id=str(uuid.uuid4()),
                occurred_at=occurred_at,
                correlation_id=request.id,
                request_id=request.id,
                factor_id=(
                    outcome.factor.id if outcome.factor is not None else ""
                ),
                confidence=outcome.confidence,
            )
        elif outcome.status == "no_match":
            event = FactorNotFound(
                event_id=str(uuid.uuid4()),
                occurred_at=occurred_at,
                correlation_id=request.id,
                request_id=request.id,
                activity=request.activity,
                unit=request.unit,
            )
        if event is not None:
            try:
                await self._event_bus.publish(event)
            except Exception:  # noqa: BLE001 - side effects must not break the match
                logger.exception(
                    "failed to publish %s for request %s",
                    type(event).__name__,
                    request.id,
                )

    async def _audit(self, request: MatchRequest, outcome: MatchResult) -> None:
        """Record the match outcome through the audit logger (best-effort)."""
        if self._audit_logger is None:
            return
        try:
            await self._audit_logger.log_action(
                action=f"factor_match:{outcome.status}",
                entity_type="factor_match",
                entity_id=request.id,
                correlation_id=request.id,
                actor="matching_engine",
                after={
                    "status": outcome.status,
                    "factor_id": (
                        outcome.factor.id if outcome.factor is not None else None
                    ),
                    "confidence": outcome.confidence,
                    "methodology": outcome.methodology,
                    "stages_executed": list(outcome.stages_executed),
                },
            )
        except Exception:  # noqa: BLE001 - audit must not break the match
            logger.exception(
                "failed to audit match result for request %s", request.id
            )


def build_matching_pipeline(
    config: MatchingPipelineConfig,
    *,
    alias_resolver: Optional[AliasResolver] = None,
) -> list[MatchingStage]:
    """Build the ordered matching stages declared by ``config.stages``.

    Args:
        config: The pipeline configuration (stage order + thresholds).
        alias_resolver: Optional alias resolver for :class:`AliasMatchStage`
            (e.g. a :class:`RepositoryAliasResolver`).

    Returns:
        One stage instance per configured stage name, in order.

    Raises:
        ValueError: When ``config.stages`` names an unregistered stage.
    """
    builders: dict[str, Callable[[], MatchingStage]] = {
        "exact_match": lambda: ExactMatchStage(),
        "natural_key": lambda: NaturalKeyStage(),
        "alias_match": lambda: AliasMatchStage(alias_resolver),
        "keyword_search": lambda: KeywordSearchStage(
            min_confidence=config.keyword_min_confidence
        ),
        "fuzzy_match": lambda: FuzzyMatchStage(threshold=config.fuzzy_threshold),
        "semantic_match": lambda: SemanticMatchStage(
            enabled=config.semantic_enabled,
            min_confidence=config.semantic_min_confidence,
        ),
    }
    stages: list[MatchingStage] = []
    for name in config.stages:
        builder = builders.get(name)
        if builder is None:
            raise ValueError(f"unknown matching stage {name!r}")
        stages.append(builder())
    return stages

