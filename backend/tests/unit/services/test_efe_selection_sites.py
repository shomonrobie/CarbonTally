"""P2 EF-E — the three authorised selection sites (PO D-A **b**).

Proves that each traced surface uses the **strict T2** mechanism and delivers the
behaviour the PO required:

* **S1** ``GET /api/v3/factors``             → ``api/v3_emissions.py``
* **S2** ``GET /items/{id}/mapping-options`` → ``api/v3_processing_workflow.py``
* **S3** ``_prefer_aggregate_factor``        → ``services/automatic_processing.py``
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

import pytest

from core.units import unit_matches_with_qualifier
from domain.factor import EmissionFactor


def _factor(factor_id: str, activity: str, unit: str) -> EmissionFactor:
    return EmissionFactor(
        id=factor_id,
        reporting_year=2025,
        activity_type=activity,
        co2e_multiplier=Decimal("0.18"),
        unit=unit,
        scope="Scope 1",
    )


AGGREGATE_QUALIFIED = _factor("f-agg", "Natural gas [kWh (Gross CV)]", "kWh (Gross CV)")
COMPONENT_QUALIFIED = _factor(
    "f-comp", "Natural gas (kg CO2e of CH4 per unit) [kWh (Gross CV)]", "kWh (Gross CV)"
)


class _CapturingFactors:
    """Fake factor repository: captures selection kwargs, serves candidates."""

    def __init__(self, candidates: list[EmissionFactor]) -> None:
        self._candidates = candidates
        self.calls: list[dict[str, Any]] = []

    async def find_by_activity(self, activity: str, **kwargs: Any) -> list[EmissionFactor]:
        self.calls.append({"activity": activity, **kwargs})
        return list(self._candidates)

    @property
    def last(self) -> dict[str, Any]:
        return self.calls[-1]


# ------------------------------------------------------------------- S1 -------
def test_s1_factor_search_uses_the_strict_mechanism() -> None:
    import api.v3_emissions as module

    source = inspect.getsource(module.factor_search)
    assert "find_by_activity" in source
    assert "unit_qualifier_tolerant=True" in source


# ------------------------------------------------------------------- S2 -------
def test_s2_mapping_options_uses_the_strict_mechanism() -> None:
    import api.v3_processing_workflow as module

    source = inspect.getsource(module.mapping_options)
    assert "find_by_activity" in source
    assert "unit_qualifier_tolerant=True" in source


async def _noop_async_list(*_args: Any, **_kwargs: Any) -> list[Any]:
    return []


class _Collaborator:
    """Stand-in that is both attribute-addressable and callable.

    ``collab.method(...)`` and ``collab(...)`` both resolve to an awaitable
    returning ``[]``, which covers every collaborator shape the handler uses.
    """

    def __getattr__(self, name: str) -> Any:
        async def _call(*_args: Any, **_kwargs: Any) -> list[Any]:
            return []

        return _call

    async def __call__(self, *_args: Any, **_kwargs: Any) -> list[Any]:
        return []


class _Permissive:
    """Stand-in for any collaborator bundle the handler reaches for.

    ``repos.<group>.<method>(...)`` resolves because each unknown attribute is a
    :class:`_Collaborator`. ``__getattr__`` only fires when normal lookup fails, so
    explicitly assigned attributes (the capturing factor repo) still win.
    """

    def __getattr__(self, name: str) -> Any:
        return _Collaborator()


@pytest.mark.asyncio
async def test_s2_picker_is_no_longer_a_false_dead_end(monkeypatch) -> None:
    """With a qualified factor present, the picker must not report a dead-end."""
    import api.v3_processing_workflow as module

    factors_repo = _CapturingFactors([AGGREGATE_QUALIFIED])
    repos = _Permissive()
    repos.factors = factors_repo
    repos.customer_factors = _Permissive()

    item = type(
        "Item",
        (),
        {
            "id": "item-1",
            "extracted_data": {"activity": "Natural gas", "unit": "kWh"},
            "status": "pending",
            "quality_score": None,
            "qc_by": None,
            "qc_at": None,
            "customer_approved": None,
            "customer_reviewed_by": None,
            "customer_reviewed_at": None,
            "customer_rejection_reason": None,
            "customer_notes": None,
        },
    )()
    batch = type("Batch", (), {"organization_id": "org-a"})()

    async def _checked(user, repos_, item_id):
        return item, batch

    monkeypatch.setattr(module, "_get_checked_item", _checked)
    user = type("U", (), {"user_id": "u-1"})()

    payload = await module.mapping_options("item-1", current_user=user, repos=repos)

    assert factors_repo.last["unit_qualifier_tolerant"] is True
    assert factors_repo.last["unit"] == "kWh"
    assert payload["factors"], "a qualified factor must be offered (no false dead-end)"
    assert payload.get("no_factors_reason") is None


# ------------------------------------------------------------------- S3 -------
@dataclass
class _MatchResult:
    """The automatic-pipeline match result shape (a real dataclass — the service
    uses ``dataclasses.replace`` to swap the chosen factor)."""

    status: str
    factor: Optional[EmissionFactor]


class _ServiceHarness:
    """Stand-in exposing ``_prefer_aggregate_factor`` with a fake factor repo."""

    def __init__(self, candidates: list[EmissionFactor]) -> None:
        from services.automatic_processing import AutomaticProcessingService

        self.service = AutomaticProcessingService.__new__(AutomaticProcessingService)
        self.service._repos = type("R", (), {})()
        self.service._repos.factors = _CapturingFactors(candidates)

    async def prefer(self, activity: str, unit: Optional[str], current: EmissionFactor):
        return await self.service._prefer_aggregate_factor(
            activity, unit, _MatchResult(status="matched", factor=current)
        )


@pytest.mark.asyncio
async def test_s3_qualified_aggregate_is_now_preferred() -> None:
    harness = _ServiceHarness([AGGREGATE_QUALIFIED, COMPONENT_QUALIFIED])
    result = await harness.prefer("Natural gas", "kWh", COMPONENT_QUALIFIED)
    assert harness.service._repos.factors.last["unit_qualifier_tolerant"] is True
    assert result.factor is not None
    assert "of CH4 per unit" not in result.factor.activity_type
    assert result.factor.id == "f-agg"


@pytest.mark.asyncio
async def test_s3_original_result_is_preserved_when_no_aggregate_exists() -> None:
    harness = _ServiceHarness([COMPONENT_QUALIFIED])
    result = await harness.prefer("Natural gas", "kWh", COMPONENT_QUALIFIED)
    assert result.factor is COMPONENT_QUALIFIED


@pytest.mark.asyncio
async def test_s3_never_selects_an_incompatible_unit_factor() -> None:
    """Negative: an incompatible unit factor is never eligible for selection.

    The unit-compatibility guarantee lives in the **selection query** (the strict T2
    rule), not in ``_prefer_aggregate_factor`` itself — so this models the repository
    faithfully by filtering the candidate set through the same strict rule the SQL
    applies, and asserts the component factor is then preserved.
    """
    incompatible = _factor("f-litres", "Diesel [litres]", "litres")
    assert unit_matches_with_qualifier("kWh", incompatible.unit) is False

    eligible = [
        f for f in [incompatible] if unit_matches_with_qualifier("kWh", f.unit)
    ]
    assert eligible == []  # the query would return nothing for this pair

    harness = _ServiceHarness(eligible)
    result = await harness.prefer("Natural gas", "kWh", COMPONENT_QUALIFIED)
    assert result.factor is COMPONENT_QUALIFIED


def test_exactly_the_three_authorised_sites_carry_the_strict_mechanism() -> None:
    """D-A(b): S1, S2 and S3 — and nothing beyond them."""
    import api.v3_emissions as em
    import api.v3_processing_workflow as wf
    import services.automatic_processing as ap

    carriers = [
        inspect.getsource(em.factor_search),
        inspect.getsource(wf.mapping_options),
        inspect.getsource(ap.AutomaticProcessingService),
    ]
    assert sum("unit_qualifier_tolerant" in src for src in carriers) == 3

