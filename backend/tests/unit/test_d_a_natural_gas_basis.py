"""034 D-A — natural-gas calorific-basis selection (Gross / Net / factor-set default).

The PO rule: an explicit source declaration selects that basis; an unqualified natural-gas energy
quantity uses the factor set's documented default basis = Net/NCV. Gross and Net are METHODOLOGICAL
bases, not unit aliases — they choose between two authoritative factors and never convert a quantity.
`select_basis_factor` is deliberately inert unless the candidate set offers more than one distinct
qualifier of the same base unit, so electricity/water/diesel/waste selection cannot be affected.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from core.units import (
    DEFAULT_CALORIFIC_BASIS,
    normalize_unit,
    resolve_unit_for_factor,
    select_basis_factor,
    source_calorific_basis,
    unit_matches_with_qualifier,
)

GROSS = SimpleNamespace(id="fff-gross", unit="kWh (Gross CV)")
NET = SimpleNamespace(id="aaa-net", unit="kWh (Net CV)")


def _candidates(*factors):
    return list(factors)


# -- source-basis detection (explicit evidence only) -------------------------
@pytest.mark.parametrize(
    "evidence", ["Gross CV", "gross cv", "GCV", "Gross calorific value", "billed on GCV basis"]
)
def test_explicit_gross_declarations_are_detected(evidence: str) -> None:
    assert source_calorific_basis(evidence) == "gross"


@pytest.mark.parametrize(
    "evidence", ["Net CV", "net cv", "NCV", "Net calorific value", "metered NCV"]
)
def test_explicit_net_declarations_are_detected(evidence: str) -> None:
    assert source_calorific_basis(evidence) == "net"


@pytest.mark.parametrize(
    "evidence",
    [None, "", "Power consumption 24,620.5000 kWh", "gross tonnage of waste", "net weight 60 t",
     "net payable €22,111.23", "Gross CV and Net CV both stated"],
)
def test_basis_is_never_inferred_from_unrelated_words(evidence) -> None:
    # Unrelated "gross"/"net" prose must yield None so the caller uses the default basis.
    assert source_calorific_basis(evidence) is None


def test_default_basis_is_net_for_the_supported_factor_sets() -> None:
    assert DEFAULT_CALORIFIC_BASIS == "net"


# -- deterministic basis selection ------------------------------------------
def test_unqualified_kwh_selects_net_cv_by_default() -> None:
    selected = select_basis_factor(_candidates(GROSS, NET), source_basis=None)
    assert selected is NET and selected.unit == "kWh (Net CV)"


def test_explicit_gross_selects_the_gross_candidate() -> None:
    selected = select_basis_factor(
        _candidates(GROSS, NET), source_basis=source_calorific_basis("Gross CV")
    )
    assert selected is GROSS


def test_explicit_net_selects_the_net_candidate() -> None:
    selected = select_basis_factor(
        _candidates(GROSS, NET), source_basis=source_calorific_basis("NCV")
    )
    assert selected is NET


def test_gcv_and_ncv_select_the_same_way_as_their_long_forms() -> None:
    assert select_basis_factor(_candidates(GROSS, NET), source_basis=source_calorific_basis("GCV")) is GROSS
    assert select_basis_factor(
        _candidates(GROSS, NET), source_basis=source_calorific_basis("Net calorific value")
    ) is NET


def test_enumeration_order_never_decides_the_selected_factor() -> None:
    # both orderings, plus an id-ordering that contradicts the presentation order
    forward = select_basis_factor(_candidates(GROSS, NET))
    backward = select_basis_factor(_candidates(NET, GROSS))
    assert forward is NET and backward is NET
    assert forward.id == backward.id


def test_single_qualifier_or_unqualified_sets_are_left_alone() -> None:
    # not a Gross/Net choice -> the helper must not select anything (no other family affected)
    assert select_basis_factor(_candidates(GROSS)) is None
    assert select_basis_factor(_candidates(SimpleNamespace(id="f1", unit="kWh"))) is None
    assert select_basis_factor([]) is None
    assert select_basis_factor(_candidates(SimpleNamespace(id="f2", unit="litres"))) is None


# -- 027 protections and existing compatibility are untouched ---------------
def test_gross_and_net_are_not_unit_conversions() -> None:
    # the qualifier rule treats them as the same BASE unit (compatible input) ...
    assert unit_matches_with_qualifier("kWh", "kWh (Gross CV)") is True
    assert unit_matches_with_qualifier("kWh", "kWh (Net CV)") is True
    # ... but resolution never rewrites one basis into the other, and normalization keeps them distinct
    assert resolve_unit_for_factor("kWh (Gross CV)", "kWh (Net CV)") == "kWh (Gross CV)"
    assert normalize_unit("kWh (Gross CV)") != normalize_unit("kWh (Net CV)")
    assert normalize_unit("kWh (Gross CV)") == "kWh (Gross CV)"


def test_plain_kwh_and_alias_handling_is_unchanged() -> None:
    assert resolve_unit_for_factor("kWh", "kWh") == "kWh"
    assert resolve_unit_for_factor("kwh", "kWh") == "kWh"
    assert resolve_unit_for_factor("L", "litres") == "litres"
    assert resolve_unit_for_factor("m3", "cubic metres") == "cubic metres"
