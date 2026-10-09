"""Manual Processing — subscription entitlement + routing decision (pure domain).

Covers the ratified business rule at the domain layer (no HTTP, no database):

    manual_processing_effective = subscription_entitled AND governance_enabled

plus the plan-derived entitlement resolution and the processor (routing
destination) most-specific-wins resolution.
"""
from __future__ import annotations

from domain.billing import BillingPlan
from domain.manual_processing import (
    OUTCOME_NOT_ENABLED,
    OUTCOME_NOT_ENTITLED,
    OUTCOME_NO_PROCESSOR,
    OUTCOME_ROUTABLE,
    EffectiveManualProcessing,
    ManualProcessingProcessor,
    OrgContext,
    entitlement_from_plan,
    resolve_processor,
    resolve_routing,
)


def _plan(*, features=None, assisted: bool = False, code: str = "pro", version: int = 1):
    return BillingPlan(
        id="plan-1",
        plan_code=code,
        name="Pro",
        price=0,
        features=features if features is not None else {},
        assisted_processing_available=assisted,
        version=version,
    )


def _governance(enabled: bool, scope_type=None, scope_id=None):
    return EffectiveManualProcessing(
        enabled=enabled,
        source_level="explicit" if scope_type else "default",
        source_scope_type=scope_type,
        source_scope_id=scope_id,
    )


def _processor(scope_type: str, scope_id: str, *, pe: str = "pe-1", active: bool = True):
    return ManualProcessingProcessor(
        scope_type=scope_type,
        scope_id=scope_id,
        processing_entity_id=pe,
        active=active,
    )


class TestPlanEntitlement:
    """Subscription entitlement is derived from the EXISTING commercial model."""

    def test_no_plan_is_not_entitled(self) -> None:
        decision = entitlement_from_plan(None)
        assert decision.entitled is False
        assert decision.source == "none"

    def test_explicit_feature_flag_grants_entitlement(self) -> None:
        decision = entitlement_from_plan(
            _plan(
                features={"manual_processing": {"enabled": True}},
                code="business",
                version=3,
            )
        )
        assert decision.entitled is True
        assert decision.source == "feature"
        assert decision.plan_code == "business"
        assert decision.plan_version == 3

    def test_explicit_feature_flag_can_withhold_entitlement(self) -> None:
        """An explicit ``false`` wins over an otherwise assisted-capable plan."""
        decision = entitlement_from_plan(
            _plan(features={"manual_processing": {"enabled": False}}, assisted=True)
        )
        assert decision.entitled is False
        assert decision.source == "feature"

    def test_assisted_processing_plan_column_grants_entitlement(self) -> None:
        decision = entitlement_from_plan(_plan(assisted=True, code="business"))
        assert decision.entitled is True
        assert decision.source == "assisted_processing_available"

    def test_plan_without_the_capability_is_not_entitled(self) -> None:
        decision = entitlement_from_plan(_plan(features={"reports": True}, assisted=False))
        assert decision.entitled is False
        assert decision.source == "none"


class TestEffectiveRouting:
    """``effective = entitled AND enabled`` — the subscription is the FIRST gate."""

    def test_entitled_enabled_and_configured_is_routable(self) -> None:
        decision = resolve_routing(
            entitlement_from_plan(_plan(assisted=True)),
            _governance(True, "organization", "org-a"),
            _processor("organization", "org-a"),
        )
        assert decision.effective is True
        assert decision.configured is True
        assert decision.outcome == OUTCOME_ROUTABLE
        assert decision.processing_entity_id == "pe-1"

    def test_not_entitled_denies_even_with_an_enabled_grant(self) -> None:
        """A stale enabled grant can NEVER bypass the subscription requirement."""
        decision = resolve_routing(
            entitlement_from_plan(_plan(assisted=False)),
            _governance(True, "organization", "org-a"),
            _processor("organization", "org-a"),
        )
        assert decision.entitled is False
        assert decision.enabled is True
        assert decision.effective is False
        assert decision.outcome == OUTCOME_NOT_ENTITLED
        assert decision.processing_entity_id is None

    def test_entitled_but_grant_disabled_is_denied(self) -> None:
        decision = resolve_routing(
            entitlement_from_plan(_plan(assisted=True)),
            _governance(False, "organization", "org-a"),
            _processor("organization", "org-a"),
        )
        assert decision.effective is False
        assert decision.outcome == OUTCOME_NOT_ENABLED

    def test_entitled_and_enabled_without_a_processor_is_configuration_state(self) -> None:
        decision = resolve_routing(
            entitlement_from_plan(_plan(assisted=True)),
            _governance(True, "organization", "org-a"),
            None,
        )
        assert decision.effective is True
        assert decision.configured is False
        assert decision.outcome == OUTCOME_NO_PROCESSOR
        assert decision.processing_entity_id is None

    def test_inactive_processor_is_not_a_destination(self) -> None:
        decision = resolve_routing(
            entitlement_from_plan(_plan(assisted=True)),
            _governance(True, "organization", "org-a"),
            _processor("organization", "org-a", active=False),
        )
        assert decision.outcome == OUTCOME_NO_PROCESSOR


class TestProcessorPrecedence:
    """The processor uses the SAME FIN-06 most-specific-wins precedence."""

    def test_consultant_client_overrides_the_firm_and_the_organization(self) -> None:
        context = OrgContext(
            "org-a", consultant_client_id="cc-1", consultant_firm_id="firm-1"
        )
        resolved = resolve_processor(
            [
                _processor("organization", "org-a", pe="pe-org"),
                _processor("consultant_firm", "firm-1", pe="pe-firm"),
                _processor("consultant_client", "cc-1", pe="pe-client"),
            ],
            context,
        )
        assert resolved.processing_entity_id == "pe-client"

    def test_firm_overrides_the_organization(self) -> None:
        context = OrgContext(
            "org-a", consultant_client_id=None, consultant_firm_id="firm-1"
        )
        resolved = resolve_processor(
            [
                _processor("organization", "org-a", pe="pe-org"),
                _processor("consultant_firm", "firm-1", pe="pe-firm"),
            ],
            context,
        )
        assert resolved.processing_entity_id == "pe-firm"

    def test_organization_is_the_default_scope(self) -> None:
        resolved = resolve_processor(
            [_processor("organization", "org-a", pe="pe-org")], OrgContext("org-a")
        )
        assert resolved.processing_entity_id == "pe-org"

    def test_no_configuration_returns_none(self) -> None:
        assert resolve_processor([], OrgContext("org-a")) is None
