"""Phase 8 B2 — pure materialisation-derivation tests (contract §11, §20.1).

No database, no I/O: these exercise the normative eligibility, derivation,
canonical-``payload_hash``, ordinal-gap and divergence rules of
:mod:`domain.line_items` as functions. The runtime/DB acceptance tests live in
``tests/integration/test_evidence_line_items_b2_runtime.py``.
"""
from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from domain.line_items import (
    ACTION_DIVERGENCE,
    ACTION_INSERT,
    ACTION_SKIP_EXISTS,
    INELIGIBLE_LINE_COUNT,
    MATERIALISATION_BACKFILL,
    MATERIALISATION_FORWARD,
    UNKNOWN_EXTRACTION_METHOD,
    canonical_payload,
    compute_payload_hash,
    decide_ordinals,
    derive_line_candidates,
    parse_decimal,
)

# --- §11.1 eligibility ------------------------------------------------------


def test_eligibility_requires_a_line_items_array() -> None:
    for payload in (
        None,
        {},  # flat record — ineligible, and never fabricated from
        {"line_items": None},
        {"line_items": {}},
        {"line_items": "a,b"},
        {"activity": "Natural gas", "quantity": 10, "unit": "kWh"},
    ):
        result = derive_line_candidates(payload)
        assert result.eligible is False
        assert result.line_count == INELIGIBLE_LINE_COUNT
        assert result.candidates == ()
        assert result.materialisable == 0


def test_empty_line_items_array_is_eligible_but_yields_no_rows() -> None:
    result = derive_line_candidates({"line_items": []})
    assert result.eligible is True
    assert result.line_count == 0
    assert result.skipped_no_lines == 1
    assert result.candidates == ()


def test_flat_record_never_falls_back_to_a_synthetic_line() -> None:
    """Manufacturing granularity is explicitly prohibited (§11.4)."""
    result = derive_line_candidates(
        {"activity": "Diesel", "quantity": 500, "unit": "litres", "page_count": 8}
    )
    assert result.candidates == ()
    assert result.eligible is False


# --- §11.2 derivation -------------------------------------------------------


def test_recognised_key_extraction_and_raw_mapping() -> None:
    result = derive_line_candidates(
        {
            "line_items": [
                {
                    "activity": "Grid electricity",
                    "description": "Half-hourly supply",
                    "quantity": "1234.50",
                    "unit": "kWh",
                    "amount": 99.5,
                    "supplier": "Octopus",
                    "invoice_number": "INV-1",
                    "unrecognised": "ignored",
                }
            ]
        }
    )
    assert result.line_count == 1
    (line,) = result.candidates
    assert line.line_number == 1
    assert line.raw_description == "Grid electricity"  # activity wins
    assert line.raw_quantity == Decimal("1234.50")
    assert line.raw_unit == "kWh"
    assert line.source_page is None  # NEVER page_count (F-B2-7 / B2-D4)
    assert line.row_reference is None  # B2-D8
    assert line.extraction_method_override is None


def test_raw_description_falls_back_to_description_then_item() -> None:
    assert (
        derive_line_candidates({"line_items": [{"description": "Desc"}]})
        .candidates[0]
        .raw_description
        == "Desc"
    )
    assert (
        derive_line_candidates({"line_items": [{"item": "Item name"}]})
        .candidates[0]
        .raw_description
        == "Item name"
    )
    assert (
        derive_line_candidates({"line_items": [{"quantity": 1, "unit": "kg"}]})
        .candidates[0]
        .raw_description
        is None
    )


def test_non_numeric_quantity_and_blank_unit_stay_null() -> None:
    (line,) = derive_line_candidates(
        {"line_items": [{"activity": "Waste", "quantity": "n/a", "unit": "   "}]}
    ).candidates
    assert line.raw_quantity is None
    assert line.raw_unit is None
    assert parse_decimal("100.00") == Decimal("100.00")
    assert parse_decimal(True) is None and parse_decimal("") is None


def test_payload_hash_is_key_order_independent_and_recognised_key_only() -> None:
    first = {"quantity": 100, "unit": "kWh", "noise": "x", "page": 3}
    second = {"unit": "kWh", "quantity": 100}
    assert compute_payload_hash(first) == compute_payload_hash(second)
    assert canonical_payload(first) == {"quantity": "100", "unit": "kWh"}
    assert compute_payload_hash({"quantity": 101}) != compute_payload_hash(
        {"quantity": 100}
    )


def test_number_normalisation_prevents_false_divergence() -> None:
    for value in (100, 100.0, "100", "100.0", "100.00", Decimal("100.00")):
        assert canonical_payload({"quantity": value}) == {"quantity": "100"}
        assert compute_payload_hash({"quantity": value}) == compute_payload_hash(
            {"quantity": 100}
        )



def test_non_scalar_values_are_omitted_from_the_hash() -> None:
    assert compute_payload_hash({"quantity": {"nested": 1}, "unit": "kWh"}) == (
        compute_payload_hash({"unit": "kWh"})
    )
    # the element is still materialisable because a recognised key carries a value
    (line,) = derive_line_candidates(
        {"line_items": [{"quantity": {"nested": 1}, "unit": "kWh"}]}
    ).candidates
    assert line.raw_quantity is None


def test_ordinal_gaps_are_preserved_when_elements_are_skipped() -> None:
    result = derive_line_candidates(
        {
            "line_items": [
                {"activity": "line one", "quantity": 1, "unit": "kg"},
                "not-an-object",  # malformed → gap at ordinal 2
                {"activity": "line three", "quantity": 3, "unit": "kg"},
                {},  # empty → gap at ordinal 4
                {"activity": "line five"},  # ordinal stays 5
            ]
        }
    )
    assert [c.line_number for c in result.candidates] == [1, 3, 5]
    assert result.skipped_malformed == 1
    assert result.skipped_empty == 1
    assert result.skipped_no_lines == 0


def test_identical_duplicate_elements_stay_distinct_ordinals() -> None:
    line = {"activity": "Same", "quantity": 5, "unit": "kg"}
    result = derive_line_candidates({"line_items": [dict(line), dict(line)]})
    assert [c.line_number for c in result.candidates] == [1, 2]
    # never merged: same hash, distinct ordinals
    assert result.candidates[0].payload_hash == result.candidates[1].payload_hash


# --- §11.7 declared per-line interface (no producer today) ------------------


def test_per_line_optional_keys_are_read_when_genuine() -> None:
    (line,) = derive_line_candidates(
        {
            "line_items": [
                {
                    "activity": "Boiler gas",
                    "quantity": 10,
                    "unit": "kWh",
                    "page": 2,
                    "line_reference": "INV-123/2/3",
                    "extraction_method": "csv",
                }
            ]
        }
    ).candidates
    assert line.source_page == 2
    assert line.row_reference == "INV-123/2/3"
    assert line.extraction_method_override == "csv"


def test_malformed_per_line_keys_are_ignored_not_errors() -> None:
    (line,) = derive_line_candidates(
        {
            "line_items": [
                {
                    "activity": "x",
                    "quantity": 1,
                    "unit": "kg",
                    "page": 0,  # out of domain
                    "line_reference": "   ",  # blank
                    "extraction_method": 5,  # wrong type
                }
            ]
        }
    ).candidates
    assert line.source_page is None
    assert line.row_reference is None
    assert line.extraction_method_override is None


def test_per_line_keys_do_not_change_the_payload_hash() -> None:
    base = {"activity": "x", "quantity": 1, "unit": "kg"}
    assert compute_payload_hash(base) == compute_payload_hash(
        {**base, "page": 9, "line_reference": "ref", "extraction_method": "csv"}
    )


# --- §11.3 rerun decisions (B2-D2) -----------------------------------------


def test_decide_ordinals_insert_skip_and_divergence() -> None:
    candidates = derive_line_candidates(
        {
            "line_items": [
                {"activity": "a", "quantity": 1, "unit": "kg"},  # ordinal 1
                {"activity": "b", "quantity": 2, "unit": "kg"},  # ordinal 2
                {"activity": "c", "quantity": 3, "unit": "kg"},  # ordinal 3
            ]
        }
    ).candidates
    existing = {
        1: ("line-1", candidates[0].payload_hash),  # identical → no write
        2: ("line-2", "0" * 64),  # changed payload → DIVERGENCE
        # 3 absent → INSERT
    }
    decisions = {d.line_number: d for d in decide_ordinals(candidates, existing)}
    assert decisions[1].action == ACTION_SKIP_EXISTS
    assert decisions[1].line_id == "line-1"
    assert decisions[2].action == ACTION_DIVERGENCE
    assert decisions[2].line_id == "line-2"
    assert decisions[2].stored_hash == "0" * 64
    assert decisions[2].current_hash == candidates[1].payload_hash
    assert decisions[3].action == ACTION_INSERT


def test_decide_ordinals_never_touches_ordinals_without_a_candidate() -> None:
    candidates = derive_line_candidates(
        {"line_items": [{"activity": "a", "quantity": 1, "unit": "kg"}]}
    ).candidates
    assert [d.line_number for d in decide_ordinals(candidates, {})] == [1]
    # a stored ordinal with no current candidate is left alone (immutability):
    # a shorter/corrected array never deletes or renumbers a stored row.
    decisions = decide_ordinals(candidates, {1: ("l1", candidates[0].payload_hash)})
    assert [d.line_number for d in decisions] == [1]


def test_materialisation_kind_and_method_vocabulary() -> None:
    assert MATERIALISATION_FORWARD == "FORWARD"
    assert MATERIALISATION_BACKFILL == "BACKFILL"
    assert UNKNOWN_EXTRACTION_METHOD == "unknown"


def test_module_reads_no_extraction_engine_and_no_mapped_data() -> None:
    """§22.2 — the derivation module cannot re-extract or read mapped data."""
    raw = (
        Path(__file__).resolve().parents[3] / "domain" / "line_items.py"
    ).read_text(encoding="utf-8")
    # Only executable code is inspected: the module docstring legitimately
    # *describes* the prohibition, so docstrings and comments are removed first.
    code = re.sub(r'"""(.*?)"""', "", raw, flags=re.S)
    code = "\n".join(line.split("#", 1)[0] for line in code.splitlines())
    for forbidden in (
        "mapped_data",
        "automatic_extraction",
        "ai_document_extraction",
        "extraction_suggestions",
        "tesseract",
        "openai",
        "requests",
    ):
        assert forbidden not in code.lower(), forbidden
