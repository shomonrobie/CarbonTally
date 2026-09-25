"""P17-L — the canonical governed capability projection (pure, no I/O).

`P17-DECISION-03 §6` requires ONE canonical projection shared by the customer and
investor surfaces, and `§18.3` requires the gates `AG-1`…`AG-8` to be automated.
The route-level suite (`tests/unit/api/test_p17l_capability_truth_surface.py`)
closes the branches a payload can close; this suite closes the branches that
belong to the projection itself:

* the governed dimensions of a requirement identity are *derived*, never guessed
  (an unrecognised code raises rather than inventing a scope or a category);
* the rollup is *derived from the rows* — a value outside the frozen four-way
  split is a governance finding, not a rendering choice;
* `§8` capability ≠ result is structural: `result_presence` is always null;
* the guards that make `AG-3`/`AG-4`/`AG-7` enforceable actually fire;
* the module declares no vocabulary of its own (`§5`, `F-2`) — it is a
  projection, not a second capability configuration file.
"""
from __future__ import annotations

import pathlib
from typing import Any

import pytest

from domain import capability_catalogue as cc
from domain.disclosure import (
    CARBONTALLY_CAPABILITIES,
    REQUIREMENT_CLASSES,
    SCOPE2_METHODS,
    DisclosureViolation,
)
from domain.disclosure_projection import UNSUPPORTED_CAPABILITIES

_ROLLUP = {
    "SUPPORTED": 4,
    "PARTIALLY_SUPPORTED": 6,
    "FUTURE": 3,
    "MISSING_CAPABILITY": 2,
}

_M1_IMAGE = {
    "GP-S3-CAT-01": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-02": "MISSING_CAPABILITY",
    "GP-S3-CAT-03": "SUPPORTED",
    "GP-S3-CAT-04": "SUPPORTED",
    "GP-S3-CAT-05": "SUPPORTED",
    "GP-S3-CAT-06": "SUPPORTED",
    "GP-S3-CAT-07": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-08": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-09": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-10": "MISSING_CAPABILITY",
    "GP-S3-CAT-11": "FUTURE",
    "GP-S3-CAT-12": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-13": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-14": "FUTURE",
    "GP-S3-CAT-15": "FUTURE",
}


def _row(code: str, capability: str, **overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "requirement_code": code,
        "title": f"Requirement {code}",
        "description": "Bounded scope. Prerequisite: the named prerequisite.",
        "requirement_class": "REQUIRED" if code.startswith(("GP-S1", "GP-S2")) else "CONDITIONAL",
        "carbontally_capability": capability,
        "source_locator": "GHG Protocol Corporate Standard (2004 revised edition)",
        "authoritative_text_ref": "verified 2026-09-12 (source tier 1)",
        "source_tier": 1,
        "official_identifier": None,
        "identifier_status": "UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION",
        "framework_code": "GHG_PROTOCOL",
        "framework_version_label": "Corporate Accounting and Reporting Standard (2004 revised edition)",
    }
    row.update(overrides)
    return row


def _rows() -> list[dict[str, Any]]:
    rows = [
        _row("GP-S1", "SUPPORTED"),
        _row("GP-S2-LB", "SUPPORTED"),
        _row("GP-S2-MB", "MISSING_CAPABILITY"),
    ]
    rows.extend(_row(code, capability) for code, capability in _M1_IMAGE.items())
    return rows


def _payload() -> dict[str, Any]:
    return cc.project_capability_catalogue(
        framework={"code": "GHG_PROTOCOL", "name": "GHG Protocol Corporate Standard"},
        framework_version={"version_label": "x", "status": "IN_FORCE", "source_tier": 1},
        requirement_rows=_rows(),
    )


# ===========================================================================
# §5 / F-2 — no second configuration file: the vocabulary is imported
# ===========================================================================
def test_the_module_declares_no_second_capability_vocabulary() -> None:
    """§5 / `F-2` — this is a projection, not a capability configuration file."""
    assert set(cc._CAPABILITY_EXPLANATION) == set(CARBONTALLY_CAPABILITIES)
    assert set(cc.ROLLUP_KEYS) <= set(CARBONTALLY_CAPABILITIES)
    assert set(cc.SCOPES) == {"Scope 1", "Scope 2", "Scope 3"}
    assert set(cc._SCOPE2_METHOD_BY_SUFFIX.values()) <= set(SCOPE2_METHODS)
    # No module-level tuple re-declares the governed vocabulary.
    for name, value in vars(cc).items():
        if name == "CARBONTALLY_CAPABILITIES":
            continue  # the imported governed constant itself, not a re-declaration
        if isinstance(value, tuple) and len(value) == len(CARBONTALLY_CAPABILITIES):
            assert set(value) != set(CARBONTALLY_CAPABILITIES), name


def test_every_capability_value_has_a_governed_explanation() -> None:
    for value in CARBONTALLY_CAPABILITIES:
        explanation = cc.capability_explanation(value)
        assert explanation and explanation[0].isupper()


def test_an_unknown_capability_has_no_explanation() -> None:
    with pytest.raises(DisclosureViolation):
        cc.capability_explanation("PARTIAL")


def test_the_glossary_covers_the_governed_vocabulary_in_order() -> None:
    glossary = cc.capability_glossary()
    assert [entry["value"] for entry in glossary] == list(CARBONTALLY_CAPABILITIES)


# ===========================================================================
# Governed dimensions are derived from the catalogue identity, never guessed
# ===========================================================================
def test_scope1_and_scope2_dimensions_are_derived() -> None:
    assert cc.dimensions_for_requirement_code("GP-S1") == {
        "scope": "Scope 1",
        "scope2_method": None,
        "scope3_category": None,
    }
    assert cc.dimensions_for_requirement_code("GP-S2-LB")["scope2_method"] == "LOCATION_BASED"
    assert cc.dimensions_for_requirement_code("GP-S2-MB")["scope2_method"] == "MARKET_BASED"


@pytest.mark.parametrize("category", list(range(1, 16)))
def test_every_scope3_category_is_derived(category: int) -> None:
    dimensions = cc.dimensions_for_requirement_code(f"GP-S3-CAT-{category:02d}")
    assert dimensions["scope"] == "Scope 3"
    assert dimensions["scope3_category"] == category
    assert dimensions["scope2_method"] is None


@pytest.mark.parametrize(
    "code", ["", "GP-S4", "GP-S2-XX", "GP-S3-CAT-16", "GP-S3-CAT-00", "cat-1", "S3-1"]
)
def test_an_unrecognised_requirement_identity_raises(code: str) -> None:
    with pytest.raises(DisclosureViolation):
        cc.dimensions_for_requirement_code(code)


def test_the_governed_taxonomy_size_is_fifteen() -> None:
    assert cc.SCOPE3_CATEGORY_COUNT == 15


# ===========================================================================
# AG-1 — the projection is the exact governed image
# ===========================================================================
def test_ag_1_the_projection_is_the_exact_m1_image() -> None:
    by_code = {item["requirement_code"]: item for item in _payload()["requirements"]}
    for code, capability in _M1_IMAGE.items():
        assert by_code[code]["carbontally_capability"] == capability, code


def test_ag_1_every_projected_value_is_governed() -> None:
    for item in _payload()["requirements"]:
        assert item["carbontally_capability"] in CARBONTALLY_CAPABILITIES
        assert item["requirement_class"] in REQUIREMENT_CLASSES
        assert item["requirement_class_expression"] in REQUIREMENT_CLASSES


def test_a_row_outside_the_vocabulary_is_refused_not_rendered() -> None:
    rows = _rows()
    rows[0] = _row("GP-S1", "PARTIAL")
    with pytest.raises(DisclosureViolation):
        cc.project_capability_catalogue(
            framework={}, framework_version={}, requirement_rows=rows
        )


def test_a_row_with_an_unknown_class_is_refused_not_rendered() -> None:
    rows = _rows()
    rows[0] = _row("GP-S1", "SUPPORTED", requirement_class="PROBABLY")
    with pytest.raises(DisclosureViolation):
        cc.project_capability_catalogue(
            framework={}, framework_version={}, requirement_rows=rows
        )


# ===========================================================================
# AG-2 — governed, distinct outcomes
# ===========================================================================
def test_ag_2_not_supported_and_future_remain_distinct() -> None:
    by_code = {item["requirement_code"]: item for item in _payload()["requirements"]}
    assert by_code["GP-S3-CAT-02"]["requirement_class_expression"] == "NOT_SUPPORTED"
    assert by_code["GP-S3-CAT-11"]["requirement_class_expression"] == "FUTURE"
    assert by_code["GP-S3-CAT-11"]["requirement_class_expression"] != by_code["GP-S3-CAT-02"][
        "requirement_class_expression"
    ]


def test_ag_2_a_capability_never_becomes_an_applicability_outcome() -> None:
    outcomes = {
        item["requirement_class_expression"] for item in _payload()["requirements"]
    }
    assert "NOT_APPLICABLE" not in outcomes
    assert "UNDETERMINED" not in outcomes



# ===========================================================================
# AG-3 — no Axis-A token is renderable, and the guard actually fires
# ===========================================================================
def test_ag_3_no_axis_a_token_is_renderable() -> None:
    cc.assert_no_axis_a_status_token(_payload())


def test_ag_3_the_scan_distinguishes_a_governed_value_from_the_internal_token() -> None:
    """`PARTIALLY_SUPPORTED` must never be mistaken for the internal `PARTIAL`."""
    assert cc.AXIS_A_STATUS_PATTERN.search("PARTIALLY_SUPPORTED") is None
    assert cc.AXIS_A_STATUS_PATTERN.search("PARTIAL") is not None
    assert cc.AXIS_A_STATUS_PATTERN.search("DEFERRED") is not None
    assert cc.AXIS_A_STATUS_PATTERN.search("NOT_IMPLEMENTED") is not None


@pytest.mark.parametrize("token", ["PARTIAL", "DEFERRED", "NOT_IMPLEMENTED", "deferred"])
def test_ag_3_the_guard_refuses_an_injected_token(token: str) -> None:
    payload = _payload()
    payload["requirements"][0]["capability_detail"] = f"status: {token}"
    with pytest.raises(DisclosureViolation):
        cc.assert_no_axis_a_status_token(payload)


def test_the_axis_a_scan_runs_inside_the_projection() -> None:
    """A projection cannot return an Axis-A token even if a caller forgets."""
    source = pathlib.Path(cc.__file__).read_text()
    assert "assert_no_axis_a_status_token(payload)" in source
    assert "assert_no_placeholder_or_figure(payload)" in source
    assert "assert_no_forbidden_field(payload)" in source


# ===========================================================================
# AG-4 — no placeholder, no figure; absence renders as absence
# ===========================================================================
def test_ag_4_no_placeholder_or_figure_is_renderable() -> None:
    cc.assert_no_placeholder_or_figure(_payload())


@pytest.mark.parametrize(
    "injected", ["N/A", "not applicable", "excluded", "coming soon", "0 tCO2e", "12 tCO2e"]
)
def test_ag_4_the_guard_refuses_an_injected_placeholder_or_figure(injected: str) -> None:
    payload = _payload()
    payload["requirements"][0]["capability_detail"] = injected
    with pytest.raises(DisclosureViolation):
        cc.assert_no_placeholder_or_figure(payload)


def test_the_governed_not_applicable_value_is_not_the_phrase_not_applicable() -> None:
    """`NOT_APPLICABLE_TO_PRODUCT` is a governed value, not a placeholder."""
    cc.assert_no_placeholder_or_figure({"value": "NOT_APPLICABLE_TO_PRODUCT"})


# ===========================================================================
# AG-7 — the four-way rollup, derived and never a total
# ===========================================================================
def test_ag_7_the_rollup_is_the_frozen_four_way_split() -> None:
    assert cc.scope3_capability_rollup(_rows()) == _ROLLUP
    assert set(_ROLLUP) == set(cc.ROLLUP_KEYS)


def _with_category(code: str, capability: str) -> list[dict[str, Any]]:
    """`_rows()` with one Scope 3 category's capability replaced."""
    rows = _rows()
    replaced = False
    for index, row in enumerate(rows):
        if row["requirement_code"] == code:
            rows[index] = _row(code, capability)
            replaced = True
    assert replaced, code
    return rows


def test_ag_7_the_rollup_is_derived_from_the_rows() -> None:
    """Moving one category between buckets moves the rollup with it."""
    rollup = cc.scope3_capability_rollup(_with_category("GP-S3-CAT-11", "PARTIALLY_SUPPORTED"))
    assert rollup["FUTURE"] == 2
    assert rollup["PARTIALLY_SUPPORTED"] == 7


def test_ag_7_a_scope3_value_outside_the_four_way_split_is_refused() -> None:
    with pytest.raises(DisclosureViolation):
        cc.scope3_capability_rollup(_with_category("GP-S3-CAT-11", "NOT_APPLICABLE_TO_PRODUCT"))


def test_ag_7_the_rollup_counts_only_scope3_categories() -> None:
    assert sum(cc.scope3_capability_rollup(_rows()).values()) == 15
    assert cc.scope3_capability_rollup([_row("GP-S1", "SUPPORTED")]) == {
        "SUPPORTED": 0,
        "PARTIALLY_SUPPORTED": 0,
        "FUTURE": 0,
        "MISSING_CAPABILITY": 0,
    }


def test_ag_7_no_total_or_coverage_field_exists() -> None:
    cc.assert_no_forbidden_field(_payload())


@pytest.mark.parametrize(
    "field",
    [
        "scope3_coverage",
        "total_emissions",
        "completeness_score",
        "materiality_assessment",
        "assurance_opinion",
        "category_applicability",
        "architecture_status",
    ],
)
def test_ag_7_the_guard_refuses_a_forbidden_field(field: str) -> None:
    payload = _payload()
    payload[field] = 1
    with pytest.raises(DisclosureViolation):
        cc.assert_no_forbidden_field(payload)



# ===========================================================================
# AG-6 / CS-2 — one governed value per requirement, no per-surface variant
# ===========================================================================
def test_ag_6_each_requirement_appears_exactly_once() -> None:
    codes = [item["requirement_code"] for item in _payload()["requirements"]]
    assert len(codes) == len(set(codes))
    assert len(codes) == 18


def test_ag_6_no_per_surface_variant_field_is_produced() -> None:
    item = _payload()["requirements"][0]
    for variant in ("investor_capability", "customer_capability", "surface"):
        assert variant not in item


def test_the_projection_is_deterministic() -> None:
    """The same rows produce the same statement, every time (CS-2 by construction)."""
    assert _payload() == _payload()


# ===========================================================================
# AG-8 / §12 — provenance, or an explicit unresolved marker
# ===========================================================================
def test_ag_8_provenance_is_carried_through_verbatim() -> None:
    item = _payload()["requirements"][0]
    assert item["provenance"] == {
        "source_locator": "GHG Protocol Corporate Standard (2004 revised edition)",
        "authoritative_text_ref": "verified 2026-09-12 (source tier 1)",
        "source_tier": 1,
        "official_identifier": None,
        "identifier_status": "UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION",
    }


def test_ag_8_an_unresolved_identifier_is_never_invented() -> None:
    for item in _payload()["requirements"]:
        provenance = item["provenance"]
        assert provenance["identifier_status"] in (
            "RESOLVED",
            "UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION",
        )
        if provenance["identifier_status"] != "RESOLVED":
            assert provenance["official_identifier"] is None


def test_ag_8_the_framework_version_is_reported_as_recorded() -> None:
    payload = cc.project_capability_catalogue(
        framework={"code": "GHG_PROTOCOL", "name": "Standard", "publisher": "WRI & WBCSD"},
        framework_version={
            "version_label": "Corporate Accounting and Reporting Standard (2004 revised edition)",
            "status": "IN_FORCE",
            "source_tier": 1,
            "source_url": "https://ghgprotocol.org/corporate-standard",
            "authoritative_source_date": None,
        },
        requirement_rows=_rows(),
    )
    assert payload["framework"]["publisher"] == "WRI & WBCSD"
    # An absent authority date is null — never a guessed date.
    assert payload["framework_version"]["authoritative_source_date"] is None


# ===========================================================================
# §8 — product capability ≠ result presence (structural, not presentational)
# ===========================================================================
def test_result_presence_is_never_a_product_level_fact() -> None:
    payload = _payload()
    assert payload["result_presence_note"]
    for item in payload["requirements"]:
        assert item["result_presence"] is None


def test_no_result_field_is_derived_from_capability() -> None:
    """A supported requirement still carries no result (absence ≠ zero)."""
    supported = [i for i in _payload()["requirements"] if i["supported"] is True]
    assert supported
    assert all(item["result_presence"] is None for item in supported)


def test_supported_uses_the_governed_unsupported_set() -> None:
    for item in _payload()["requirements"]:
        assert item["supported"] is (
            item["carbontally_capability"] not in UNSUPPORTED_CAPABILITIES
        )


# ===========================================================================
# Lookup helpers (used by the surfaces and their tests)
# ===========================================================================
def test_capability_lookup_helpers() -> None:
    payload = _payload()
    assert cc.capability_for_scope3(payload, 5)["requirement_code"] == "GP-S3-CAT-05"
    assert cc.capability_for_scope3(payload, 16) is None
    assert (
        cc.capability_for_scope2(payload, "LOCATION_BASED")["carbontally_capability"]
        == "SUPPORTED"
    )
    assert (
        cc.capability_for_scope2(payload, "MARKET_BASED")["carbontally_capability"]
        != "SUPPORTED"
    )
    with pytest.raises(DisclosureViolation):
        cc.capability_for_scope2(payload, "GUESSED")


def test_an_empty_catalogue_projects_an_empty_statement() -> None:
    payload = cc.project_capability_catalogue(
        framework={}, framework_version={}, requirement_rows=[]
    )
    assert payload["requirements"] == []
    assert sum(payload["scope3_capability_rollup"].values()) == 0

