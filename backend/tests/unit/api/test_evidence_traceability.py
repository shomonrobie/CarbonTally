"""D33 — evidence traceability tests.

Covers the authoritative lineage chain:
- ``CalculationSnapshot`` carries ``source_item_id`` / ``source_file`` /
  ``source_page`` (the exact extraction source).
- ``GET /api/v3/emissions/{log_id}/evidence`` — emission -> calculation ->
  extraction item -> source document (org member only; cross-org denied).
- ``GET /api/v3/documents/{file_id}/emissions`` — reverse document -> emissions.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from domain.calculation import CalculationSnapshot
from tests.unit.api.fakes import member_user


def _log(org_id: str = "org-a", snapshot_id: str = "snap-a") -> SimpleNamespace:
    return SimpleNamespace(
        id="log-a",
        organization_id=org_id,
        snapshot_id=snapshot_id,
        date="2025-01-01",
        quantity="12500",
        unit="kWh",
        calculated_kg_co2e="2212.50",
        scope="Scope 2",
        asset_id=None,
        created_at=None,
    )


def _snapshot(org_id: str = "org-a") -> dict:
    return {
        "id": "snap-a",
        "organization_id": org_id,
        "activity": "Electricity",
        "activity_type": "Electricity",
        "quantity": "12500",
        "quantity_unit": "kWh",
        "co2e_multiplier": "0.177",
        "co2e_kg": "2212.50",
        "scope": "Scope 2",
        "date": "2025-01-31",
        "reporting_year": 2025,
        "factor_source": "DEFRA-DESNZ",
        "factor_set": "2024",
        "methodology": "direct_multiply",
        "algorithm_version": "1.0",
        "content_hash": "h",
        "calculated_at": "2025-06-01T00:00:00",
        "calculated_by": "org-a",
        "factor_id": None,
        "customer_factor_id": None,
        "source_item_id": "item-a",
        "source_file": "Electricity_Invoice_Jan25.pdf",
        "source_page": 1,
    }


def _install_chain(world, *, org_id="org-a") -> None:
    """Wire the in-memory lineage fakes for the evidence endpoints."""

    async def logs_get(log_id: str):
        return _log(org_id)

    async def logs_get_snapshot(snapshot_id: str):
        return _snapshot(org_id)

    async def items_get(item_id: str):
        return SimpleNamespace(
            id=item_id,
            file_name="Electricity_Invoice_Jan25.pdf",
            file_url="uploads/org-a/2025/01/electricity-jan25.pdf",
            file_id="file-a",
            page_count=2,
            document_type="utility",
            status="approved",
            extracted_data={"activity": "Electricity", "quantity": "12500", "unit": "kWh"},
            mapped_data={"activity_type": "Electricity"},
            calculated_emissions_kg_co2e=2212.50,
        )

    async def files_get(file_id: str):
        return SimpleNamespace(
            id=file_id,
            organization_id=org_id,
            name="Electricity_Invoice_Jan25.pdf",
            path="uploads/org-a/2025/01/electricity-jan25.pdf",
            file_type="PDF",
            size_bytes=1024,
            uploaded_by="u-a",
            uploaded_at=None,
            metadata={"data_type": "utility"},
        )

    world.logs.get = logs_get  # type: ignore[method-assign]
    world.logs.get_snapshot = logs_get_snapshot  # type: ignore[method-assign]
    world.manual_extraction.get_item = items_get  # type: ignore[method-assign]
    world.files.get = files_get  # type: ignore[method-assign]
    world.files.get_by_path = files_get  # type: ignore[method-assign]


def test_snapshot_domain_carries_source_item():
    snap = CalculationSnapshot(
        id="s1",
        match_request_id="m1",
        organization_id="org-a",
        factor_id="f1",
        quantity="1",
        quantity_unit="kWh",
        co2e_multiplier="1",
        co2e_kg="1",
        scope="Scope 1",
        date="2025-01-01",
        reporting_year=2025,
        methodology="direct_multiply",
        algorithm_version="1.0",
        created_at="2025-01-02",
        source_file="invoice.pdf",
        source_page=3,
        source_item_id="item-1",
    )
    assert snap.source_item_id == "item-1"
    assert snap.source_file == "invoice.pdf"
    assert snap.source_page == 3


# ---------------------------------------------------------------------------
# Emission -> evidence
# ---------------------------------------------------------------------------


def test_emission_evidence_org_member(client, world, user_provider, monkeypatch):
    import api.v3_emissions as v3_emissions

    _install_chain(world)
    monkeypatch.setattr(
        "services.storage.storage_signed_url", lambda *a, **k: "https://signed/x"
    )
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.get("/api/v3/emissions/log-a/evidence")
    assert resp.status_code == 200
    data = resp.json()
    assert data["evidence"]["source_item_id"] == "item-a"
    assert data["source_document"]["name"] == "Electricity_Invoice_Jan25.pdf"
    assert data["source_item"]["extracted_data"]["activity"] == "Electricity"
    assert data["source_document"]["signed_url"] == "https://signed/x"


def test_emission_evidence_cross_org_denied(client, world, user_provider, monkeypatch):
    import api.v3_emissions as v3_emissions

    _install_chain(world)
    monkeypatch.setattr(
        "services.storage.storage_signed_url", lambda *a, **k: "https://signed/x"
    )
    user_provider.set_user(member_user("org-b", "u-b", "b@example.test"))
    assert client.get("/api/v3/emissions/log-a/evidence").status_code == 403


def test_emission_evidence_unknown_log_404(client, world, user_provider, monkeypatch):
    import api.v3_emissions as v3_emissions

    async def logs_get(log_id: str):
        return None

    world.logs.get = logs_get  # type: ignore[method-assign]
    monkeypatch.setattr(
        "services.storage.storage_signed_url", lambda *a, **k: "https://signed/x"
    )
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    assert client.get("/api/v3/emissions/nope/evidence").status_code == 404


# ---------------------------------------------------------------------------
# Reverse document -> emissions
# ---------------------------------------------------------------------------


def test_document_emissions_reverse_lookup(client, world, user_provider):
    _install_chain(world)

    async def logs_list_for_file(file_id: str):
        return [
            {
                "id": "log-a",
                "organization_id": "org-a",
                "snapshot_id": "snap-a",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "calculated_kg_co2e": "2212.50",
                "scope": "Scope 2",
                "source_file": "Electricity_Invoice_Jan25.pdf",
            }
        ]

    world.logs.list_for_file = logs_list_for_file  # type: ignore[method-assign]
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.get("/api/v3/documents/file-a/emissions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["document_name"] == "Electricity_Invoice_Jan25.pdf"
    assert len(data["emissions"]) == 1
    assert data["emissions"][0]["snapshot_id"] == "snap-a"


def test_document_emissions_cross_org_denied(client, world, user_provider):
    _install_chain(world)

    async def logs_list_for_file(file_id: str):
        return []

    world.logs.list_for_file = logs_list_for_file  # type: ignore[method-assign]
    user_provider.set_user(member_user("org-b", "u-b", "b@example.test"))
    assert client.get("/api/v3/documents/file-a/emissions").status_code == 403

