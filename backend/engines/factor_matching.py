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
from typing import Any, Callable, Optional, Protocol, Sequence

from core.logging import get_logger
from core.units import (
    select_basis_factor,
    source_calorific_basis,
    split_qualified_unit,
)
from domain.customer_factor import CustomerFactor
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
from engines.factor_selection_policy import select_factor as select_factor_policy
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus

logger = get_logger(__name__)


class CustomerFactorLookup(Protocol):
    """The customer-factor candidate surface consumed by the matching engine.

    Satisfied structurally by ``CustomerFactorsRepository.get_active_for_org``.
    D-cf-5: only approved (``status='active'``) customer factors are eligible
    to be matched ahead of CarbonTally-managed factors.
    """

    async def get_active_for_org(self, org_id: str) -> list[CustomerFactor]: ...


class FactorMatchingEngine:
    """Runs the matching pipeline against a search index.

    Args:
        index: The factor search index (Phase 3 ``FactorSearchIndex``).
        stages: Ordered matching stages (see :func:`build_matching_pipeline`).
        config: Pipeline tuning; defaults to :class:`MatchingPipelineConfig`.
        event_bus: Optional bus that receives ``FactorMatched``/``FactorNotFound``
            outcome events (fire-and-forget).
        audit_logger: Optional logger that records every match outcome.
        customer_factor_lookup: Optional source of approved customer factors
            (D-cf-5 — checked before the CarbonTally pipeline when the request
            carries an ``organization_id``).
    """

    def __init__(
        self,
        index: FactorSearch,
        stages: Sequence[MatchingStage],
        *,
        config: Optional[MatchingPipelineConfig] = None,
        event_bus: Optional[EventBus] = None,
        audit_logger: Optional[AuditLogger] = None,
        customer_factor_lookup: Optional[CustomerFactorLookup] = None,
    ) -> None:
        if not stages:
            raise ValueError("stages must not be empty")
        self._index = index
        self._stages = list(stages)
        self._config = config or MatchingPipelineConfig()
        self._event_bus = event_bus
        self._audit_logger = audit_logger
        self._customer_factor_lookup = customer_factor_lookup

    @property
    def stages(self) -> tuple[str, ...]:
        """The configured stage names, in execution order."""
        return tuple(stage.name for stage in self._stages)

    @property
    def config(self) -> MatchingPipelineConfig:
        """The pipeline tuning in effect."""
        return self._config

    async def match(self, request: MatchRequest) -> MatchResult:
        """Run the pipeline and produce the final :class:`MatchResult`.

        D-cf-5 precedence: an approved customer factor for the request's
        organisation (exact activity match) is resolved first; only when none
        exists does the CarbonTally pipeline run.
        """
        customer_result = await self._match_customer_factor(request)
        if customer_result is not None:
            return await self._finalize(request, customer_result)

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
                return await self._finalize(
                    request, await self._apply_selection_policy(request, outcome)
                )
            if stage_result.score >= 1.0:
                suggestions = await self._suggestions(request)
                outcome = MatchResult(
                    status="ambiguous",
                    suggestions=tuple(suggestions),
                    stages_executed=tuple(stages_executed),
                    request_id=request.id,
                )
                return await self._finalize(request, outcome)
        basis_factor = self._discover_calorific_basis(request)
        if basis_factor is not None:
            stages_executed.append("calorific_basis")
            outcome = MatchResult(
                status="matched",
                factor=basis_factor,
                confidence=1.0,
                methodology="calorific_basis",
                provider=getattr(basis_factor, "provider_key", None),
                stages_executed=tuple(stages_executed),
                request_id=request.id,
            )
            return await self._finalize(
                request, await self._apply_selection_policy(request, outcome)
            )
        suggestions = await self._suggestions(request)
        outcome = MatchResult.no_match(
            suggestions=suggestions,
            stages_executed=stages_executed,
            request_id=request.id,
        )
        return await self._finalize(request, outcome)

    async def _match_customer_factor(
        self, request: MatchRequest
    ) -> Optional[MatchResult]:
        """Resolve an approved customer factor (D-cf-5) ahead of the pipeline.

        Returns ``None`` when the request is not org-scoped, no lookup is
        configured, or no exact customer-factor candidate exists. A definitive
        single candidate yields ``matched``; multiple candidates yield
        ``ambiguous``.
        """
        if self._customer_factor_lookup is None or not request.organization_id:
            return None
        candidates = await self._customer_factor_lookup.get_active_for_org(
            request.organization_id
        )
        needle = request.activity.casefold()
        exact = [
            factor
            for factor in candidates
            if factor.activity_type.casefold() == needle
            and factor.country == request.country
        ]
        if not exact:
            return None
        if len(exact) > 1:
            return MatchResult(
                status="ambiguous",
                factor_kind="customer_factor",
                suggestions=tuple(),
                stages_executed=("customer_factor",),
                request_id=request.id,
            )
        chosen = exact[0]
        return MatchResult(
            status="matched",
            confidence=1.0,
            methodology="customer_factor",
            provider=None,
            stages_executed=("customer_factor",),
            request_id=request.id,
            factor_kind="customer_factor",
            customer_factor_id=chosen.id,
        )

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

    async def _apply_selection_policy(
        self, request: MatchRequest, outcome: MatchResult
    ) -> MatchResult:
        """PO D-FS-1…D-FS-6 — deterministic semantic eligibility and preference.

        Runs at the factor-selection boundary (the engine) over the EXISTING
        candidate list, so the semantic decision is explicit and deterministic
        rather than a lexical side-effect. It only ever *corrects* a match whose
        factor the policy excludes/outranks, or downgrades such a match to
        ``ambiguous``; it never fabricates a match, and it leaves a match whose
        factor the policy also considers eligible completely untouched.
        """
        current = getattr(outcome, "factor", None)
        if outcome.status != "matched" or current is None:
            return outcome
        results = self._index.keyword_search(
            request.activity,
            unit=None,
            country=request.country,
            provider=request.preferred_provider,
            limit=max(int(self._config.max_suggestions), 25),
        )
        candidates = [factor for factor, score in results if score > 0.0]
        current_id = getattr(current, "id", None)
        if not any(getattr(f, "id", None) == current_id for f in candidates):
            candidates.append(current)
        decision = select_factor_policy(
            candidates,
            activity=request.activity,
            unit=request.unit,
            scope=request.scope,
            preferred_unit=getattr(current, "unit", None),
        )
        eligible_ids = {getattr(f, "id", None) for f in decision.eligible}
        if decision.status == "selected" and decision.factor is not None:
            winner = decision.factor
            if getattr(winner, "id", None) == current_id or current_id in eligible_ids:
                return outcome
            return MatchResult(
                status="matched",
                factor=winner,
                confidence=1.0,
                methodology="selection_policy",
                provider=getattr(winner, "provider_key", None),
                stages_executed=tuple(list(outcome.stages_executed) + ["selection_policy"]),
                request_id=request.id,
            )
        if decision.status == "ambiguous" and current_id not in eligible_ids:
            suggestions = await self._suggestions(request)
            return MatchResult(
                status="ambiguous",
                suggestions=tuple(suggestions),
                stages_executed=tuple(list(outcome.stages_executed) + ["selection_policy"]),
                request_id=request.id,
            )
        return outcome

    def _discover_calorific_basis(self, request: MatchRequest) -> Optional[Any]:
        """D-A post-stage calorific-basis discovery (natural gas).

        The staged pipeline compares ``request.unit`` verbatim, so an
        unqualified ``kWh`` request can never reach the qualified
        ``kWh (Gross CV)`` / ``kWh (Net CV)`` factors. This step re-queries the
        EXISTING index with the request's base unit (``split_qualified_unit``)
        and lets :func:`core.units.select_basis_factor` decide the basis from
        the retrieved candidates — a deterministic policy, never enumeration
        order.

        It is deliberately inert unless the candidates offer more than one
        distinct qualifier of the same base unit, so electricity, water,
        diesel, waste and unrelated activities are structurally unaffected; a
        request that is already qualified has nothing to discover and returns
        ``None``. Gross/Net remain methodological bases, never conversions.
        """
        base_unit, qualifier = split_qualified_unit(request.unit or "")
        if not base_unit or qualifier:
            return None
        # Natural-gas scope gate (the oracle showed that without it an
        # unrelated/undetected activity - "Power consumption kWh" - could be
        # redirected to a CNG basis factor). The calorific-basis policy only
        # ever applies to a request that actually names a gas.
        if "gas" not in (request.activity or "").casefold():
            return None
        # ``FactorSearchIndex.keyword_search`` applies a STRICT unit filter, so a
        # base-unit re-query would return nothing (verified: unit="kWh" -> []).
        # Candidate retrieval is therefore activity-based (``unit=None``) and unit
        # compatibility is enforced by ``select_basis_factor`` itself, which only
        # accepts candidates sharing the request's base unit.
        results = self._index.keyword_search(
            request.activity,
            unit=None,
            country=request.country,
            provider=request.preferred_provider,
            limit=max(int(self._config.max_suggestions), 25),
        )
        candidates = [
            factor
            for factor, score in results
            if score > 0.0
            and split_qualified_unit(getattr(factor, "unit", "") or "")[0]
            == base_unit
        ]
        return select_basis_factor(
            candidates,
            source_basis=source_calorific_basis(request.activity),
        )

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
                    outcome.factor.id
                    if outcome.factor is not None
                    else (outcome.customer_factor_id or "")
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
                    "factor_kind": outcome.factor_kind,
                    "customer_factor_id": outcome.customer_factor_id,
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

