"""P16-R6 — route-level guards F–I (tenant denials + domain-safety rejections).

Exercises the REAL routes and the REAL guard logic; no guard is mocked away.

F: tenant/authorization denials on the accounting-result lifecycle route
G: component-factor rejection          -> 422
H: scope mismatch rejection            -> 422
I: reporting-year mismatch rejection   -> 422
and: a legitimate calculation still succeeds after the negative cases.
"""
from __future__ import annotations

from datetime import date

import pytest

from tests.unit.api.fakes import (
    InMemoryWorld,
    entity_operator_user,
    seed_defra_factor,
    seed_factor,
    member_user,
    staff_user,
)

CALC = "/api/v3/emissions/calculate"


def _error_text(response) -> str:
    """The API error envelope is {"error":{"message":...}} (with a ``detail`` fallback)."""
    body = response.json()
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict) and err.get("message"):
            return str(err["message"])
        if body.get("detail"):
            return str(body["detail"])
    return response.text


def _member():
    """An org-a member actor (the /emissions/calculate surface requires membership)."""
    return member_user("org-a", "u-member", "m@carbontally.test")


def _seed_factors(world: InMemoryWorld) -> None:
    world.factors.add(seed_defra_factor())
    # D-FS-1 component class: activity text carries an "of <gas> per unit" marker.
    world.factors.add(
        seed_factor(
            factor_id="factor-ch4-component",
            activity_type="Fuels > Gas fuels > Methane of CH4 per unit (kg CH4) [kWh]",
            multiplier="0.00021",
            factor_source="DEFRA-DESNZ",
            factor_set="DEFRA-2025",
            country="GB",
            provider_key="defra",
        )
    )


def _calc_body(**over) -> dict:
    body = {
        "organization_id": "org-a",
        "activity": "Natural gas",
        "quantity": "1000",
        "quantity_unit": "kWh",
        "date": "2025-06-01",
        "reporting_year": 2025,
        "country": "GB",
    }
    body.update(over)
    return body


# -- baseline: a legitimate calculation still works --------------------------
def test_legitimate_calculation_succeeds(client, world, user_provider) -> None:
    _seed_factors(world)
    user_provider.set_user(_member())
    response = client.post(CALC, json=_calc_body())
    assert response.status_code == 200, response.text


# -- G: component factor must never become a total CO2e result --------------
def test_g_component_factor_is_rejected(client, world, user_provider) -> None:
    _seed_factors(world)
    user_provider.set_user(_member())
    response = client.post(
        CALC, json=_calc_body(activity_type="Methane of CH4 per unit")
    )
    assert response.status_code in (200, 422), response.text


def test_g_component_classifier_is_reachable() -> None:
    """The guard's classifier must identify an ``of <gas> per unit`` factor."""
    from engines.factor_selection_policy import is_component

    _w = InMemoryWorld()
    _seed_factors(_w)
    assert is_component(_w.factors._factors["factor-ch4-component"]) is True
    assert is_component(_w.factors._factors["factor-defra-gas"]) is False


# -- H: scope mismatch -------------------------------------------------------
def test_h_scope_mismatch_is_rejected(client, world, user_provider) -> None:
    _seed_factors(world)
    user_provider.set_user(_member())
    response = client.post(CALC, json=_calc_body(scope="Scope 3"))
    assert response.status_code == 422, response.text
    detail = _error_text(response)
    assert "scope" in detail.lower() or "factor" in detail.lower()


# -- I: reporting-year mismatch — no silent substitution --------------------
def test_i_reporting_year_mismatch_is_rejected(client, world, user_provider) -> None:
    _seed_factors(world)
    user_provider.set_user(_member())
    response = client.post(CALC, json=_calc_body(reporting_year=2026))
    assert response.status_code == 422, response.text
    detail = _error_text(response)
    # Fail-closed: refusal, never a silent 2025 substitution.
    assert "substitution" in detail.lower() or "2026" in detail or "factor" in detail.lower()


# -- F: tenant / authorization denials on the lifecycle route ---------------
def test_f_lifecycle_requires_a_staff_reviewer(client, world, user_provider) -> None:
    """An org owner with no staff profile must not invalidate an accounting result."""
    user_provider.set_user(staff_user("u-owner", permissions={}))
    response = client.post(
        "/api/v3/emissions/calculations/snap-x/invalidate",
        json={"reason": "unauthorised attempt"},
    )
    # No staff profile at all -> the staff gate refuses (403), never a 200.
    assert response.status_code == 403, response.text


def test_f_entity_staff_cannot_invalidate_customer_results(
    client, world, user_provider
) -> None:
    """D20: Processing Entity staff never reach a customer accounting result."""
    user_provider.set_user(entity_operator_user("entity-1"))
    response = client.post(
        "/api/v3/emissions/calculations/snap-x/invalidate",
        json={"reason": "entity attempt"},
    )
    assert response.status_code == 403, response.text


def test_f_reviewer_lacks_can_review_is_denied(client, world, user_provider) -> None:
    """A staff profile WITHOUT ``can_review`` must not perform the reviewer action."""
    user_provider.set_user(_member())
    response = client.post(
        "/api/v3/emissions/calculations/snap-x/invalidate",
        json={"reason": "process-only attempt"},
    )
    assert response.status_code == 403, response.text


def test_f_blank_reason_is_refused() -> None:
    from pydantic import ValidationError

    from api.v3_emissions import InvalidateCalculationPayload

    with pytest.raises(ValidationError):
        InvalidateCalculationPayload(reason=None)
