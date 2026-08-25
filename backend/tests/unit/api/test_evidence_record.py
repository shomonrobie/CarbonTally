"""D33.1 — evidence-record / technical provenance tests.

Covers:
- evidence-completeness classification (COMPLETE / PARTIAL / UNAVAILABLE),
- honest source-location precision (never fabricated),
- the evidence-record builder (original vs derived sections, stable IDs),
- evidence-access audit writes (ids only, never URLs),
- export evidence_status,
- authorization (own-org only, cross-org denied).
"""
from __future__ import annotations

from types import SimpleNamespace

from domain.evidence import (
    build_evidence_record,
    classify_evidence_completeness,
    source_location_precision,
)
from tests.unit.api.fakes import member_user


# ---------------------------------------------------------------------------
# Evidence completeness (pure)
# ---------------------------------------------------------------------------


def test_completeness_complete_with_page():
    status, reason = classify_evidence_completeness(
        has_document=True, has_item=True, has_calculation=True,
        has_factor=True, has_page=True,
    )
    assert status == "COMPLETE"


def test_completeness_partial_without_page():
    status, reason = classify_evidence_completeness(
        has_document=True, has_item=True, has_calculation=True,
        has_factor=True, has_page=False,
    )
    assert status == "PARTIAL"
    assert "page" in reason.lower()


def test_completeness_partial_incomplete_chain():
    status, _ = classify_evidence_completeness(
        has_document=True, has_item=True, has_calculation=True,
        has_factor=False, has_page=False,
    )
    assert status == "PARTIAL"


def test_completeness_unavailable():
    status, _ = classify_evidence_completeness(
        has_document=False, has_item=False, has_calculation=False,
        has_factor=False, has_page=False,
    )
    assert status == "UNAVAILABLE"


# ---------------------------------------------------------------------------
# Source-location precision (pure)
# ---------------------------------------------------------------------------


def test_source_location_no_fabrication():
    loc = source_location_precision(has_document=True, page=None, has_item=False)
    assert loc["display"] == "Source document available; exact source location not available."
    assert loc["page"] is None
    assert loc["sheet"] is None


def test_source_location_line_but_no_page():
    loc = source_location_precision(has_document=True, page=None, has_item=True)
    assert loc["display"] == "Source line available; page/location not available."
    assert loc["line_available"] is True

def _fixture_objects():
    emission = SimpleNamespace(
        id="log-a", organization_id="org-a", snapshot_id="snap-a",
        date="2025-01-31", calculated_kg_co2e="0.140", scope="Scope 2", unit="kWh",
    )
    snapshot = {
        "id": "snap-a", "activity": "Electricity", "activity_type": "Electricity",
        "quantity": "500", "quantity_unit": "kWh", "co2e_multiplier": "0.00028",
        "co2e_kg": "0.140", "scope": "Scope 2", "factor_source": "DEFRA-DESNZ",
        "factor_set": "DEFRA-2025", "methodology": "direct_multiply",
        "algorithm_version": "1.0", "content_hash": "h", "calculated_at": None,
        "calculated_by": "org-a", "request_id": "r1", "factor_id": "f1",
        "customer_factor_id": None, "source_item_id": "item-a",
        "source_file": "INV-10482.pdf", "source_page": 2,
    }
    item = SimpleNamespace(
        id="item-a", file_name="INV-10482.pdf", file_url="uploads/org-a/i.pdf",
        file_id="file-a", page_count=3, document_type="utility", status="approved",
        extracted_data={"activity": "Electricity", "quantity": "500", "unit": "kWh",
                        "supplier": "UK Grid Power Ltd", "date": "2025-01-31",
                        "invoice_number": "INV-10482"},
        mapped_data={"activity_type": "Electricity"},
        mapped_facility_id=None, mapped_asset_id=None, mapped_supplier_id=None,
        extracted_by="u-a", extracted_at=None,
    )
    file_row = SimpleNamespace(
        id="file-a", organization_id="org-a", name="INV-10482.pdf",
        path="uploads/org-a/i.pdf", file_type="PDF", size_bytes=1024,
        uploaded_by="u-a", uploaded_at=None, metadata={"data_type": "utility"},
    )
    factor = SimpleNamespace(
        id="f1", reporting_year=2025, activity_type="Electricity",
        co2e_multiplier="0.00028", unit="kWh", scope="Scope 2",
        factor_source="DEFRA-DESNZ", factor_set="DEFRA-2025", country="GB",
    )
    return emission, snapshot, item, file_row, factor


def test_evidence_record_structure_and_origins():
    emission, snapshot, item, file_row, factor = _fixture_objects()
    rec = build_evidence_record(
        emission=emission, snapshot=snapshot, item=item,
        file_row=file_row, factor=factor, customer_factor=None,
    )
    assert rec["completeness"] == "COMPLETE"  # document + line + page + calc + factor
    sections = rec["sections"]
    assert sections["source_document"]["origin"] == "original"
    assert sections["extraction"]["origin"] == "original"
    assert sections["mapping"]["origin"] == "derived"
    assert sections["emission_factor"]["origin"] == "derived"
    assert sections["calculation"]["origin"] == "derived"
    assert sections["result"]["origin"] == "derived"

    sd = sections["source_document"]["fields"]
    assert sd["document_name"] == "INV-10482.pdf"
    assert sd["invoice_reference"] == "INV-10482"
    assert sd["supplier"] == "UK Grid Power Ltd"

    ex = sections["extraction"]["fields"]
    assert ex["original_value"] == "500 kWh"

    ff = sections["emission_factor"]["fields"]
    assert ff["factor_source"] == "DEFRA-DESNZ"
    assert ff["factor_set"] == "DEFRA-2025"
    assert ff["reporting_year"] == 2025

    cf = sections["calculation"]["fields"]
    assert cf["formula"] == "500 kWh × 0.00028 = 0.140 kg CO₂e"

    td = rec["technical_details"]
    assert td["emission_log_id"] == "log-a"
    assert td["calculation_snapshot_id"] == "snap-a"
    assert td["manual_extraction_item_id"] == "item-a"
    assert td["organization_file_id"] == "file-a"
    assert td["emission_factor_id"] == "f1"

    assert rec["source_location"]["page"] == 2
    assert "page 2" in rec["source_location"]["precision"]


def test_evidence_record_honest_when_no_page():
    emission, snapshot, item, file_row, factor = _fixture_objects()
    snapshot = dict(snapshot, source_page=None)
    rec = build_evidence_record(
        emission=emission, snapshot=snapshot, item=item,
        file_row=file_row, factor=factor, customer_factor=None,
    )
    assert rec["completeness"] == "PARTIAL"
    assert rec["source_location"]["page"] is None
    assert "page/location not available" in rec["source_location"]["display"]


def test_source_location_excel_row_cell():
    loc = source_location_precision(
        has_document=True, page=None, has_item=True, sheet="Sheet1", row="12", column="B"
    )
    assert "row 12" in loc["precision"]
    assert "column B" in loc["precision"]
    assert "sheet Sheet1" in loc["precision"]


# ---------------------------------------------------------------------------
# API: evidence record + audit
# ---------------------------------------------------------------------------


def _install_chain(world, org_id="org-a"):
    """Wire in-memory lineage fakes for the evidence/reverse endpoints."""

    async def logs_get(log_id: str):
        return SimpleNamespace(
            id="log-a", organization_id=org_id, snapshot_id="snap-a",
            date="2025-01-31", quantity="500", unit="kWh",
            calculated_kg_co2e="0.140", scope="Scope 2", asset_id=None,
            created_at=None,
        )

    async def logs_get_snapshot(snapshot_id: str):
        return {
            "id": "snap-a", "organization_id": org_id,
            "activity": "Electricity", "activity_type": "Electricity",
            "quantity": "500", "quantity_unit": "kWh", "co2e_multiplier": "0.00028",
            "co2e_kg": "0.140", "scope": "Scope 2", "date": "2025-01-31",
            "reporting_year": 2025, "factor_source": "DEFRA-DESNZ",
            "factor_set": "DEFRA-2025", "methodology": "direct_multiply",
            "algorithm_version": "1.0", "content_hash": "h",
            "calculated_at": "2025-06-01T00:00:00", "calculated_by": org_id,
            "request_id": "r1", "factor_id": "f1", "customer_factor_id": None,
            "source_item_id": "item-a", "source_file": "INV-10482.pdf",
            "source_page": 2,
        }

    async def items_get(item_id: str):
        return SimpleNamespace(
            id="item-a", file_name="INV-10482.pdf",
            file_url="uploads/org-a/i.pdf", file_id="file-a", page_count=3,
            document_type="utility", status="approved",
            extracted_data={"activity": "Electricity", "quantity": "500",
                            "unit": "kWh", "supplier": "UK Grid Power Ltd",
                            "date": "2025-01-31", "invoice_number": "INV-10482"},
            mapped_data={"activity_type": "Electricity"},
            mapped_facility_id=None, mapped_asset_id=None, mapped_supplier_id=None,
            extracted_by="u-a", extracted_at=None, calculated_emissions_kg_co2e=0.140,
        )

    async def files_get(file_id: str):
        return SimpleNamespace(
            id="file-a", organization_id=org_id, name="INV-10482.pdf",
            path="uploads/org-a/i.pdf", file_type="PDF", size_bytes=1024,
            uploaded_by="u-a", uploaded_at=None, metadata={"data_type": "utility"},
        )

    async def factors_get(factor_id: str):
        return SimpleNamespace(
            id="f1", reporting_year=2025, activity_type="Electricity",
            co2e_multiplier="0.00028", unit="kWh", scope="Scope 2",
            factor_source="DEFRA-DESNZ", factor_set="DEFRA-2025", country="GB",
        )

    world.logs.get = logs_get  # type: ignore[method-assign]
    world.logs.get_snapshot = logs_get_snapshot  # type: ignore[method-assign]
    world.manual_extraction.get_item = items_get  # type: ignore[method-assign]
    world.files.get = files_get  # type: ignore[method-assign]
    world.files.get_by_path = files_get  # type: ignore[method-assign]
    world.factors.get = factors_get  # type: ignore[method-assign]


def test_evidence_endpoint_returns_record_and_audits(client, world, user_provider, monkeypatch):
    import api.v3_emissions as v3_emissions

    _install_chain(world)
    monkeypatch.setattr(
        "services.storage.storage_signed_url", lambda *a, **k: "https://signed/x"
    )
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.get("/api/v3/emissions/log-a/evidence")
    assert resp.status_code == 200
    data = resp.json()
    rec = data["evidence_record"]
    assert rec["completeness"] == "COMPLETE"
    assert rec["sections"]["extraction"]["origin"] == "original"
    assert rec["sections"]["calculation"]["origin"] == "derived"
    assert rec["sections"]["calculation"]["fields"]["formula"].startswith("500 kWh")
    assert rec["technical_details"]["emission_log_id"] == "log-a"
    assert rec["technical_details"]["organization_file_id"] == "file-a"

    # audit written — ids only, no URLs/secrets
    entries = [e for e in world.audit._entries if e.action == "evidence.access"]
    assert len(entries) == 1
    assert entries[0].entity_id == "log-a"
    assert entries[0].changed_fields["snapshot_id"] == "snap-a"
    assert entries[0].changed_fields["source_file_id"] == "file-a"
    text = repr(entries[0].changed_fields).lower()
    assert "signed" not in text and "token" not in text


def test_evidence_record_cross_org_denied_no_audit(client, world, user_provider, monkeypatch):
    import api.v3_emissions as v3_emissions

    _install_chain(world)
    monkeypatch.setattr(
        "services.storage.storage_signed_url", lambda *a, **k: "https://signed/x"
    )
    user_provider.set_user(member_user("org-b", "u-b", "b@example.test"))
    resp = client.get("/api/v3/emissions/log-a/evidence")
    assert resp.status_code == 403
    assert all(e.action != "evidence.access" for e in world.audit._entries)


def test_reverse_endpoint_audits(client, world, user_provider):
    _install_chain(world)

    async def logs_list_for_file(file_id: str):
        return [
            {"id": "log-a", "organization_id": "org-a", "snapshot_id": "snap-a",
             "start_date": "2025-01-01", "end_date": "2025-01-31",
             "calculated_kg_co2e": "0.140", "scope": "Scope 2",
             "source_file": "INV-10482.pdf"},
        ]

    world.logs.list_for_file = logs_list_for_file  # type: ignore[method-assign]
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.get("/api/v3/documents/file-a/emissions")
    assert resp.status_code == 200
    entries = [e for e in world.audit._entries if e.action == "evidence.reverse_lookup"]
    assert len(entries) == 1
    assert entries[0].entity_id == "file-a"
    assert entries[0].changed_fields["emissions_returned"] == 1


# ---------------------------------------------------------------------------
# Export evidence_status
# ---------------------------------------------------------------------------


def test_export_evidence_status_logic():
    from data.exports import _evidence_status

    assert _evidence_status({"source_item_id": "i1", "source_file": "a.pdf", "source_page": 2}) == "COMPLETE"
    assert _evidence_status({"source_item_id": "i1", "source_file": "a.pdf", "source_page": None}) == "PARTIAL"
    assert _evidence_status({"source_item_id": "i1", "source_file": None, "source_page": None}) == "PARTIAL"
    assert _evidence_status({"source_item_id": None, "source_file": None, "source_page": None}) == "UNAVAILABLE"
