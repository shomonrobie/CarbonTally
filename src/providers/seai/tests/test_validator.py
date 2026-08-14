"""Unit tests: SEAI validator (approved gate rules).

The validator must pass on the canonical 20/8 mapping and fail on any of the
approved rule violations (mutations of the canonical data).
"""
from __future__ import annotations

import copy
from decimal import Decimal

import pytest

from src.providers.seai import analyze_workbook, map_all, validate
from src.providers.seai.models import FACTOR_SOURCE, FACTOR_SET, SeaiFactor
from src.providers.seai.validator import (
    ELECTRICITY_CONSUMPTION,
    ELECTRICITY_GROSS_SUPPLY,
)



@pytest.fixture(scope="session")
def canonical(seai_data):
    factors, skipped = map_all(list(seai_data.rows))
    return seai_data, factors, skipped


def test_canonical_mapping_passes(canonical):
    _, factors, skipped = canonical
    report = validate(factors, skipped)
    assert report.ok, [i.message for i in report.issues]
    assert report.errors == 0


def test_remove_one_factor_fails(canonical):
    _, factors, skipped = canonical
    report = validate(factors[:-1], skipped)
    assert not report.ok
    assert any("expected 20 imported" in i.message for i in report.issues)


def test_add_extra_factor_fails(canonical):
    _, factors, skipped = canonical
    extra = copy.deepcopy(factors[0])
    extra.activity_type = "Fuels > Liquid fuels > Fake (kg CO2) [litres]"
    extra.source_name = "Fake"
    report = validate(factors + [extra], skipped)
    assert not report.ok
    assert any("expected 20 imported" in i.message for i in report.issues)


def test_missing_skip_row_fails(canonical):
    _, factors, skipped = canonical
    report = validate(factors, skipped[:-1])
    assert not report.ok
    assert any("expected 8 skipped" in i.message for i in report.issues)


def test_missing_electricity_pair_fails(canonical):
    _, factors, skipped = canonical
    trimmed = [f for f in factors if f.activity_type != ELECTRICITY_GROSS_SUPPLY]
    report = validate(trimmed, skipped)
    assert not report.ok
    assert any("gross electricity supply" in i.message for i in report.issues)


def test_electricity_consumption_required(canonical):
    _, factors, skipped = canonical
    trimmed = [f for f in factors if f.activity_type != ELECTRICITY_CONSUMPTION]
    report = validate(trimmed, skipped)
    assert not report.ok
    assert any("electricity consumption factor missing" in i.message for i in report.issues)


def test_removing_biodiesel_me_fails(canonical):
    _, factors, skipped = canonical
    trimmed = [f for f in factors if f.source_name != "Biodiesel ME"]
    report = validate(trimmed, skipped)
    assert not report.ok
    assert any("Biodiesel ME" in i.message for i in report.issues)


def test_gcv_must_be_skipped(canonical):
    _, factors, skipped = canonical
    report = validate(factors, [s for s in skipped if s.name != "Natural gas (GCV)"])
    assert not report.ok
    assert any("Natural gas (GCV) must be skipped" in i.message for i in report.issues)


def test_wrong_country_fails(canonical):
    _, factors, skipped = canonical
    mutated = [copy.deepcopy(f) for f in factors]
    mutated[0].country = "GB"
    report = validate(mutated, skipped)
    assert not report.ok
    assert any("country" in i.message for i in report.issues)


def test_negative_multiplier_fails(canonical):
    _, factors, skipped = canonical
    mutated = [copy.deepcopy(f) for f in factors]
    mutated[0].co2e_multiplier = Decimal("-1.0")
    report = validate(mutated, skipped)
    assert not report.ok
    assert any("negative multiplier" in i.message for i in report.issues)


def test_unsupported_unit_fails(canonical):
    _, factors, skipped = canonical
    mutated = [copy.deepcopy(f) for f in factors]
    mutated[0].unit = "m3"
    report = validate(mutated, skipped)
    assert not report.ok
    assert any("unsupported unit" in i.message for i in report.issues)


def test_duplicate_natural_key_fails(canonical):
    _, factors, skipped = canonical
    dup = copy.deepcopy(factors[0])
    report = validate(factors + [dup], skipped)
    assert not report.ok
    assert report.duplicates
    assert any("duplicate natural key" in i.message for i in report.issues)


def test_skip_reason_counts_enforced(canonical):
    _, factors, skipped = canonical
    report = validate(factors, skipped)
    assert report.ok
    reasons = [s.reason for s in skipped]
    assert reasons.count("no_factor_value") == 7
    assert reasons.count("non_canonical_basis") == 1


def test_factor_source_and_set_fields(canonical):
    _, factors, _ = canonical
    for f in factors:
        assert f.factor_source == FACTOR_SOURCE
        assert f.factor_set == FACTOR_SET
