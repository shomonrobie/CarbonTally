"""Phase 8 P1 — row-candidate detection for multi-line PDF text layers (`P1-B`).

Regression lock for `CT-STEP2-P1-ROWCANDIDATE-FIX-023`. The production forensic
(`CT-STEP2-P1-PDF-PRODUCTION-FORENSIC-022`) proved that ``multi_fuel.pdf`` carries five
genuine activity rows in its text layer while the detector reported only **two**
candidates — the two ``kWh`` rows — because the unit gate could not express ``L``,
``t`` or ``m³``. These tests lock the corrected behaviour:

* five genuine table rows -> five addressable candidates (order preserved);
* every candidate keeps its quantity and unit;
* invoice furniture, prose and page-2 testing text never become candidates;
* a unit-less or single-number line is never promoted to a candidate;
* page semantics and the ``shadow`` rollout default are unchanged by the fix.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from services import extraction_fidelity as p1

#: Verbatim text layer of the production regression oracle ``multi_fuel.pdf``
#: (read with ``pdfplumber`` when this task was executed). Page 1 is 544 chars of
#: real text; page 2 is the testing footer.
MULTI_FUEL_PAGE_1 = (
    "Pure Energy PLC\n"
    "967 Renewable Road\n"
    "Liverpool\n"
    "IV47 7UK\n"
    "UK\n"
    "FUEL INVOICE\n"
    "Ref No.: PWR/2026/8130\n"
    "Date: May 08, 2026\n"
    "Buyer: Power Power & Co\n"
    "Period: Apr 01, 2026 – Apr 30, 2026\n"
    "ID: multi_fuel\n"
    "Description Qty Unit Rate Subtotal\n"
    "Gas usage 5,362.2000 kWh €0.0670 €359.2700\n"
    "Diesel supply 4,434.4000 L €1.6190 €7,179.2900\n"
    "Waste disposal 60 t €105.8140 €6,348.8400\n"
    "Water supply 163.2000 m³ €2.0130 €328.5200\n"
    "Power consumption 24,620.5000 kWh €0.1710 €4,210.1100\n"
    "Subtotal: €18,426.0300\n"
    "Sales Tax: €3,685.2000\n"
    "Net Payable: €22,111.2300\n"
    "Terms: Net 30 days.\n"
)
MULTI_FUEL_PAGE_2 = "For testing purposes only\n"
MULTI_FUEL = MULTI_FUEL_PAGE_1 + "\f" + MULTI_FUEL_PAGE_2

#: The five genuine activity rows, in source order.
ORACLE_ROWS = (
    ("Gas usage 5,362.2000 kWh €0.0670 €359.2700", 5362.2, "kwh"),
    ("Diesel supply 4,434.4000 L €1.6190 €7,179.2900", 4434.4, "l"),
    ("Waste disposal 60 t €105.8140 €6,348.8400", 60.0, "t"),
    ("Water supply 163.2000 m³ €2.0130 €328.5200", 163.2, "m3"),
    ("Power consumption 24,620.5000 kWh €0.1710 €4,210.1100", 24620.5, "kwh"),
)

SINGLE_LINE = "Acme Water Ltd\nInvoice 1234\nElectricity supply 12,500 kWh 2,340.00\n"

STANDARD_TABLE = (
    "Acme Water Ltd\n"
    "Invoice 1234\n"
    "Electricity supply 12,500 kWh 2,340.00\n"
    "Natural gas 4,000 kWh 320.00\n"
    "Water supply 300 m3 450.00\n"
    "Total due 3,110.00\n"
)

#: Layout/typography variation: tab-separated columns and a row whose unit column is
#: absent (no unit token, so it is *not* a row candidate).
VARIED_TABLE = (
    "Description\tQty\tUnit\tRate\tSubtotal\n"
    "Gas   usage\t5,362.2000   kWh  0.0670  359.2700\n"
    "Standing charge 45 45.0000\n"
)

OCR_MARKED = (
    "[page 1]\n"
    "Acme Fuels Ltd\n"
    "Diesel supply 4,434.4000 L €1.6190 €7,179.2900\n"
    "[page 2]\n"
    "Waste disposal 60 t €105.8140 €6,348.8400\n"
)

CORPUS_DIR = Path(
    os.environ.get(
        "CARBONTALLY_SYNTHETIC_DOCS",
        str(
            Path.home()
            / "carbon_tally_synthetic_documents"
            / "output_all_variations"
            / "documents"
        ),
    )
)
MULTI_FUEL_PDF = CORPUS_DIR / "multi_fuel.pdf"


def _candidates(text: str) -> int:
    return p1.classify(text, method="pdf_text", page_count=1).candidate_lines


def _items(text: str):
    items, _coverage = p1.build_line_items(text, method="pdf_text", page_count=1)
    return items


# -- Test 1: the production oracle (5 rows in -> 5 candidates) ----------------
def test_multi_fuel_text_layer_yields_five_candidates() -> None:
    assert _candidates(MULTI_FUEL) == 5


def test_multi_fuel_is_multi_line_suspect_again() -> None:
    judgement = p1.classify(MULTI_FUEL, method="pdf_text", page_count=2)
    assert judgement.multi_line_suspect is True
    assert "5 candidate source lines" in judgement.reasons


@pytest.mark.skipif(not MULTI_FUEL_PDF.exists(), reason="synthetic corpus not present")
def test_production_oracle_pdf_yields_five_candidates() -> None:
    pdfplumber = pytest.importorskip("pdfplumber")
    with pdfplumber.open(MULTI_FUEL_PDF) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        page_count = len(pdf.pages)
    judgement = p1.classify(text, method="pdf_text", page_count=page_count)
    assert judgement.candidate_lines == 5, judgement.reasons
    items, _coverage = p1.build_line_items(
        text, method="pdf_text", page_count=page_count
    )
    assert len(items) == 5


# -- Test 2: source order preserved ------------------------------------------
def test_candidate_order_follows_the_source_table() -> None:
    items = _items(MULTI_FUEL)
    assert [item["source_line"] for item in items] == [row for row, _q, _u in ORACLE_ROWS]
    assert [item["line_number"] for item in items] == [1, 2, 3, 4, 5]


def test_candidate_descriptions_follow_the_source_order() -> None:
    found = p1.find_source_lines(MULTI_FUEL_PAGE_1)
    assert len(found) == 5
    assert [line["description"].split()[0] for line in found] == [
        "Gas",
        "Diesel",
        "Waste",
        "Water",
        "Power",
    ]


# -- Test 3: every candidate retains quantity and unit -----------------------
@pytest.mark.parametrize(("raw", "quantity", "unit"), ORACLE_ROWS)
def test_candidate_retains_quantity_and_unit(
    raw: str, quantity: float, unit: str
) -> None:
    items = _items(MULTI_FUEL)
    match = [item for item in items if item["source_line"] == raw]
    assert len(match) == 1, f"{raw!r} is not an addressable candidate"
    assert match[0]["quantity"] == quantity
    assert match[0]["unit"] == unit


@pytest.mark.parametrize(("raw", "quantity", "unit"), ORACLE_ROWS)
def test_find_source_lines_reports_the_unit_hint(
    raw: str, quantity: float, unit: str
) -> None:
    found = p1.find_source_lines(raw)
    assert len(found) == 1
    assert found[0]["quantity"] == quantity
    assert found[0]["unit_hint"] == unit


def test_unit_hint_covers_short_symbolic_units() -> None:
    # `L`, `t` and `m³` are the units the pre-fix gate could not express.
    assert (
        p1.find_source_lines("Diesel supply 4,434.4000 L €1.6190 €7,179.2900")[0][
            "unit_hint"
        ]
        == "l"
    )
    assert (
        p1.find_source_lines("Waste disposal 60 t €105.8140 €6,348.8400")[0]["unit_hint"]
        == "t"
    )
    assert (
        p1.find_source_lines("Water supply 163.2000 m³ €2.0130 €328.5200")[0][
            "unit_hint"
        ]
        == "m3"
    )


# -- Test 4: invoice furniture, prose and testing text are never candidates ---
@pytest.mark.parametrize(
    "line",
    [
        "Description Qty Unit Rate Subtotal",
        "Subtotal: €18,426.0300",
        "Sales Tax: €3,685.2000",
        "Net Payable: €22,111.2300",
        "Ref No.: PWR/2026/8130",
        "Date: May 08, 2026",
        "Period: Apr 01, 2026 – Apr 30, 2026",
        "Buyer: Power Power & Co",
        "967 Renewable Road",
        "IV47 7UK",
        "Pure Energy PLC",
        "FUEL INVOICE",
        "Terms: Net 30 days.",
        "For testing purposes only",
    ],
)
def test_furniture_and_prose_are_rejected(line: str) -> None:
    assert p1.find_source_lines(line) == []


def test_only_the_five_activity_rows_are_candidates_in_the_oracle_document() -> None:
    hits = [
        raw
        for page in (MULTI_FUEL_PAGE_1, MULTI_FUEL_PAGE_2)
        for raw in page.splitlines()
        if p1.find_source_lines(raw)
    ]
    assert hits == [row for row, _q, _u in ORACLE_ROWS]


# -- Test 5: single-line documents stay single-candidate ---------------------
def test_single_line_document_remains_one_candidate() -> None:
    assert _candidates(SINGLE_LINE) == 1
    items = _items(SINGLE_LINE)
    assert len(items) == 1
    assert items[0]["quantity"] == 12500.0
    assert items[0]["unit"] == "kwh"


# -- Test 6: existing standard multi-line fixtures remain correct ------------
def test_standard_three_row_table_is_unchanged() -> None:
    assert _candidates(STANDARD_TABLE) == 3
    items = _items(STANDARD_TABLE)
    assert [item["quantity"] for item in items] == [12500.0, 4000.0, 300.0]
    assert [item["unit"] for item in items] == ["kwh", "kwh", "m3"]


# -- Test 7: difficult/edge fixtures — no new candidates are fabricated ------
def test_row_without_a_unit_column_is_not_a_candidate() -> None:
    assert _candidates(VARIED_TABLE) == 1
    items = _items(VARIED_TABLE)
    assert len(items) == 1
    assert items[0]["quantity"] == 5362.2
    assert items[0]["unit"] == "kwh"


def test_whitespace_variation_does_not_change_the_result() -> None:
    spaced = "Gas   usage\t5,362.2000   kWh  0.0670  359.2700"
    found = p1.find_source_lines(spaced)
    assert len(found) == 1
    assert found[0]["quantity"] == 5362.2
    assert found[0]["unit_hint"] == "kwh"


def test_number_without_a_unit_is_not_a_candidate() -> None:
    assert p1.find_source_lines("Electricity 12,500 2,340.00") == []


def test_payable_is_furniture_regardless_of_currency() -> None:
    # The oracle's amounts are in `€`; a `£`-denominated payable line must not become a
    # candidate either (it otherwise satisfies the currency-token gate).
    assert p1.find_source_lines("Net Payable: £22,111.23") == []
    assert p1.find_source_lines("Amount payable £4,120.00") == []
    assert p1.find_source_lines("Net Payable: €22,111.2300") == []


# -- Test 8: OCR/text-layer parity for the shared detector -------------------
def test_ocr_marker_text_is_counted_per_page_with_marker_basis() -> None:
    judgement = p1.classify(OCR_MARKED, method="ocr", page_count=2)
    assert judgement.candidate_lines == 2
    assert judgement.page_basis == "marker"
    items, coverage = p1.build_line_items(OCR_MARKED, method="ocr", page_count=2)
    assert [item["page"] for item in items] == [1, 2]
    assert {item["page_trust"] for item in items} == {"lower"}
    assert coverage["page_basis"] == "marker"


def test_short_units_are_recognised_on_an_ocr_text_layer_too() -> None:
    found = p1.find_source_lines("Diesel supply 4,434.4000 L €1.6190 €7,179.2900")
    assert found[0]["quantity"] == 4434.4


# -- Test 9: the shadow rollout is untouched by this fix ---------------------
def test_shadow_remains_the_effective_mode() -> None:
    assert p1.shape_mode(env={}) == p1.MODE_SHADOW
    assert p1.shape_mode(env={p1.SHAPE_MODE_ENV: p1.MODE_ENABLED}) == p1.MODE_SHADOW
    assert p1.rollout_status(env={})["effective_mode"] == p1.MODE_SHADOW
    assert p1.rollout_status(env={})["in_rollout"] is False


def test_coverage_block_records_candidates_without_rewriting_output() -> None:
    judgement = p1.classify(MULTI_FUEL, method="pdf_text", page_count=2)
    coverage = judgement.as_coverage()
    assert coverage["candidate_lines"] == 5
    assert coverage["multi_line_min_lines"] == p1.MULTI_LINE_MIN_LINES
    assert {"candidate_lines", "page_basis", "page_resolution", "clipped"} <= set(coverage)


# -- Test 11: the quantity column comes from the table structure -------------
def test_reference_code_is_not_mistaken_for_the_quantity() -> None:
    # Corpus evidence (`border_decorative_fuel.pdf`): the reference code sits two
    # columns left of the unit, so the quantity must be read from the column that is
    # adjacent to the unit column — not from the first number on the row.
    found = p1.find_source_lines("Diesel delivery - REF-89015 3,900 L $1.61 $6,294.60")
    assert len(found) == 1
    assert found[0]["quantity"] == 3900.0
    assert found[0]["unit_hint"] == "l"


def test_quantity_is_the_column_left_of_the_unit_column() -> None:
    found = p1.find_source_lines("Recycling services 53 t $158.86 $8,419.53")
    assert found[0]["quantity"] == 53.0
    assert found[0]["unit_hint"] == "t"


# -- Test 10: no fabricated candidate from unrelated prose -------------------
@pytest.mark.parametrize(
    "line",
    [
        "We reviewed the site t 12 times during the audit",
        "Please note l 3 outstanding items remain",
        "Cover page only",
        "This document was produced by the synthetic corpus generator",
        "For testing purposes only",
    ],
)
def test_unrelated_prose_never_becomes_a_candidate(line: str) -> None:
    assert p1.find_source_lines(line) == []

