"""V3 processing workflow (Phase 3) — route registration + workflow rules.

Covers the full pipeline surfaces (dashboard, status, batch progress,
extraction, mapping, validation, calculation, customer review, workspace,
queues) and the pure item-validation engine rules.
"""
from __future__ import annotations

from domain.partners import (
    ITEM_STATUS_FLOW,
    ManualExtractionItem,
    can_transition_item_status,
)
from engines.processing_workflow import (
    has_blocking_findings,
    validate_processing_item,
)
from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/processing/dashboard",
    "/api/v3/processing/status",
    "/api/v3/processing/batches/{batch_id}/progress",
    "/api/v3/processing/batches/{batch_id}/start",
    "/api/v3/processing/batches/{batch_id}/complete",
    "/api/v3/processing/batches/{batch_id}/cancel",
    "/api/v3/processing/items/{item_id}/start",
    "/api/v3/processing/items/{item_id}/extract",
    "/api/v3/processing/items/{item_id}/map",
    "/api/v3/processing/items/{item_id}/validate",
    "/api/v3/processing/items/{item_id}/calculate",
    "/api/v3/processing/items/{item_id}/customer-review",
    "/api/v3/processing/items/{item_id}/workspace",
    "/api/v3/processing/items/{item_id}/mapping-options",
    "/api/v3/processing/next-item",
    "/api/v3/processing/queue",
    "/api/v3/processing/customer-review",
    "/api/v3/processing/issues",
)


def test_v3_processing_workflow_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    missing = [
        fragment
        for fragment in EXPECTED_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"missing V3 processing-workflow routes: {missing}"


def _item(**overrides) -> ManualExtractionItem:
    base = dict(
        id="item-1",
        batch_id="batch-1",
        file_name="invoice.pdf",
        file_url="https://cdn.example/invoice.pdf",
        page_count=2,
        document_type="invoice",
        status="mapped",
        extracted_data={
            "supplier": "ACME Energy",
            "date": "2026-01-15",
            "activity": "Electricity",
            "quantity": "12000",
            "unit": "kWh",
        },
        mapped_data={"factor_id": "f-1", "activity_type": "Electricity"},
        emission_factor_used="f-1",
    )
    base.update(overrides)
    return ManualExtractionItem(**base)


def test_validation_passes_for_complete_item() -> None:
    findings = validate_processing_item(_item())
    assert findings == []
    assert not has_blocking_findings(findings)


def test_validation_flags_missing_extraction_fields() -> None:
    data = dict(_item().extracted_data or {})
    data["supplier"] = ""
    data["date"] = None
    findings = validate_processing_item(_item(extracted_data=data))
    codes = {f.code for f in findings}
    assert "EXTRACTION_MISSING_FIELD" in codes
    assert {f.field for f in findings if f.code == "EXTRACTION_MISSING_FIELD"} == {
        "supplier",
        "date",
    }


def test_validation_flags_missing_invalid_and_negative_quantity() -> None:
    base = _item().extracted_data or {}
    missing = _item(extracted_data={**base, "quantity": None})
    invalid = _item(extracted_data={**base, "quantity": "abc"})
    negative = _item(extracted_data={**base, "quantity": "-5"})
    assert any(f.code == "INVALID_QUANTITY" for f in validate_processing_item(missing))
    assert any(f.code == "INVALID_QUANTITY" for f in validate_processing_item(invalid))
    assert any(f.code == "NEGATIVE_QUANTITY" for f in validate_processing_item(negative))


def test_validation_flags_missing_unit() -> None:
    base = _item().extracted_data or {}
    item = _item(extracted_data={**base, "unit": ""})
    assert any(f.code == "MISSING_UNIT" for f in validate_processing_item(item))


def test_validation_requires_mapping_and_factor() -> None:
    no_mapping = _item(mapped_data=None, emission_factor_used=None)
    no_factor = _item(emission_factor_used=None)
    findings = validate_processing_item(no_mapping)
    assert any(f.code == "MAPPING_MISSING" for f in findings)
    assert any(f.code == "FACTOR_MISSING" for f in findings)
    assert has_blocking_findings(findings)
    assert not any(
        f.code in ("MAPPING_MISSING", "FACTOR_MISSING")
        for f in validate_processing_item(no_factor)
    )


def test_validation_flags_negative_calculation_result() -> None:
    item = _item(calculated_emissions_kg_co2e=-1.0)
    findings = validate_processing_item(item)
    assert any(f.code == "NEGATIVE_RESULT" for f in findings)


def test_extraction_only_validation_skips_mapping_rules() -> None:
    item = _item(mapped_data=None, emission_factor_used=None)
    findings = validate_processing_item(item, require_mapping=False)
    assert not any(f.code in ("MAPPING_MISSING", "FACTOR_MISSING") for f in findings)


def test_transition_table_covers_core_pipeline() -> None:
    assert can_transition_item_status("pending", "extracting")
    assert can_transition_item_status("pending", "extracted")
    assert can_transition_item_status("extracted", "mapped")
    assert can_transition_item_status("mapped", "validated")
    # The V3 state machine advances through the in-flight working status first
    # (claimed via /items/{id}/start): validated -> calculating -> calculated.
    assert can_transition_item_status("validated", "calculating")
    assert can_transition_item_status("calculating", "calculated")
    assert can_transition_item_status("calculated", "customer_review")
    assert can_transition_item_status("calculated", "approved")
    assert can_transition_item_status("customer_review", "rejected")
    assert can_transition_item_status("rejected", "mapping")
    assert not can_transition_item_status("pending", "approved")
    assert not can_transition_item_status("extracted", "calculated")
    assert not can_transition_item_status(None, "approved")


def test_transition_table_is_a_complete_state_machine() -> None:
    for status, targets in ITEM_STATUS_FLOW.items():
        assert status in ITEM_STATUS_FLOW
        for target in targets:
            assert can_transition_item_status(status, target)


