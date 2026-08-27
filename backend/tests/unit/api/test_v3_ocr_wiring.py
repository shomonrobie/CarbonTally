"""V3 OCR wiring tests.

Covers the deterministic OCR/extraction bridge added to the V3 document
surface:

- ``api.v3_documents._extract_document_text`` — the best-effort text/OCR
  helper (PDF text, scanned-PDF OCR fallback, image OCR, failure safety).
- ``POST /api/v3/uploads/{file_id}/ocr`` — org-scoped re-run endpoint that
  persists the extraction summary on ``organization_files.metadata``.
- the item-workspace surfaces expose ``source.ocr_text`` for human review.

The helper is unit-tested with mocked OCR primitives (no tesseract needed);
the endpoint/workspace wiring is tested through the in-memory world.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest import mock

from api import v3_documents
from domain.operations import OrganizationFile
from domain.partners import ManualExtractionItem
from domain.staff import StaffProfile, StaffRole
from tests.unit.api.fakes import member_user, staff_user


def _seed_ops_staff(world) -> None:
    world.staff.seed_role(
        StaffRole(id="role-operator", name="operator", permissions={"can_process": True})
    )
    world.staff.seed_profile(
        StaffProfile(
            id="sp-op", user_id="u-op", first_name="Op", last_name="One",
            email="op@carbontally.test", role_id="role-operator", entity_id=None,
            is_active=True,
        )
    )


def _file_row(file_id="file-1", org_id="org-a", metadata=None) -> OrganizationFile:
    return OrganizationFile(
        id=file_id,
        organization_id=org_id,
        name="invoice.pdf",
        path=f"uploads/{org_id}/2026/01/invoice.pdf",
        size_bytes=100,
        file_type="PDF",
        mime_type="application/pdf",
        bucket="documents",
        status="uploaded",
        uploaded_by="u-a",
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# _extract_document_text (helper)
# ---------------------------------------------------------------------------


def test_helper_pdf_uses_direct_text(monkeypatch):
    class _FakeExtractor:
        def _extract_text_direct(self, content):
            return "Electricity supply invoice 12500 kWh consumption period"

        def _extract_text_ocr(self, content):
            raise AssertionError("OCR must not run when direct text succeeds")

        def _get_page_count(self, content):
            return 2

    monkeypatch.setattr("pdf_engine.PDFExtractor", lambda: _FakeExtractor())
    out = v3_documents._extract_document_text(b"pdf", "bill.pdf", "application/pdf")
    assert out["status"] == "ok"
    assert out["method"] == "pdf_text"
    assert "12500 kWh" in out["text"]
    assert out["page_count"] == 2


def test_helper_scanned_pdf_falls_back_to_ocr(monkeypatch):
    class _FakeExtractor:
        def _extract_text_direct(self, content):
            return ""  # digital layer empty -> scanned

        def _extract_text_ocr(self, content):
            return "\n[page 1]\nElectricity 12500 kWh supply\n"

        def _get_page_count(self, content):
            return 1

    monkeypatch.setattr("pdf_engine.PDFExtractor", lambda: _FakeExtractor())
    out = v3_documents._extract_document_text(b"scan", "scan.pdf", "application/pdf")
    assert out["status"] == "ok"
    assert out["method"] == "tesseract_ocr"
    assert "12500 kWh" in out["text"]


def test_helper_image_uses_image_text(monkeypatch):
    class _FakeExtractor:
        def extract_image_text(self, content):
            return "Invoice 15/01/2025 Electricity 12500 kWh"

    monkeypatch.setattr("pdf_engine.PDFExtractor", lambda: _FakeExtractor())
    out = v3_documents._extract_document_text(b"img", "bill.png", "image/png")
    assert out["status"] == "ok"
    assert out["method"] == "tesseract_ocr"
    assert out["page_count"] == 1


def test_helper_unsupported_type():
    out = v3_documents._extract_document_text(b"x", "notes.txt", "text/plain")
    assert out["status"] == "unsupported"
# ---------------------------------------------------------------------------
# POST /api/v3/uploads/{file_id}/ocr
# ---------------------------------------------------------------------------


def test_ocr_endpoint_persists_and_returns_summary(world, client, user_provider, monkeypatch):
    world.files.add_file(_file_row())
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    monkeypatch.setattr(v3_documents, "_extract_document_text", lambda *a, **k: {
        "status": "ok", "method": "tesseract_ocr", "text": "Electricity 12500 kWh",
        "page_count": 1, "detail": None,
    })
    fake_client = mock.Mock()
    fake_client.storage.from_.return_value.download.return_value = b"pdf-bytes"
    monkeypatch.setattr(v3_documents, "get_service_client", lambda: fake_client)

    resp = client.post("/api/v3/uploads/file-1/ocr")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ocr"]["status"] == "ok"
    assert body["ocr"]["text"] == "Electricity 12500 kWh"

    stored = asyncio.run(world.files.get("file-1"))
    assert stored.metadata["ocr"]["text"] == "Electricity 12500 kWh"


def test_ocr_endpoint_denies_foreign_org(world, client, user_provider, monkeypatch):
    world.files.add_file(_file_row(org_id="org-b"))
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    monkeypatch.setattr(v3_documents, "_extract_document_text", lambda *a, **k: {"status": "ok"})
    resp = client.post("/api/v3/uploads/file-1/ocr")
    assert resp.status_code == 403


def test_ocr_endpoint_missing_document_404(world, client, user_provider):
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.post("/api/v3/uploads/does-not-exist/ocr")
    assert resp.status_code == 404


def test_ocr_endpoint_storage_missing_404(world, client, user_provider, monkeypatch):
    world.files.add_file(_file_row())
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    fake_client = mock.Mock()
    fake_client.storage.from_.return_value.download.side_effect = RuntimeError("no object")
    monkeypatch.setattr(v3_documents, "get_service_client", lambda: fake_client)
    resp = client.post("/api/v3/uploads/file-1/ocr")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Workspace surfaces OCR text (ops + customer processing)
# ---------------------------------------------------------------------------


def test_ops_workspace_surfaces_ocr_text(world, client, user_provider):
    _seed_ops_staff(world)
    batch = asyncio.run(
        world.manual_extraction.create_batch(
            org_id="org-a", batch_name="Uploads", total_documents=1, total_pages=1,
            total_cost=0.0, currency="GBP",
            batch_description="Auto-created from document uploads",
            price_per_page=None, created_by="u-op",
        )
    )
    item = asyncio.run(
        world.manual_extraction.create_item(
            batch.id, "invoice.pdf", "uploads/org-a/invoice.pdf", 1, "pdf", "pending",
            file_id="file-1",
        )
    )
    world.files.add_file(
        _file_row(metadata={"ocr": {"status": "ok", "text": "Electricity 12500 kWh", "method": "pdf_text"}})
    )
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    resp = client.get(f"/api/v3/ops/items/{item.id}/workspace")
    assert resp.status_code == 200
    assert resp.json()["source"]["ocr_text"] == "Electricity 12500 kWh"


def test_customer_workspace_surfaces_ocr_text(world, client, user_provider):
    batch = asyncio.run(
        world.manual_extraction.create_batch(
            org_id="org-a", batch_name="Uploads", total_documents=1, total_pages=1,
            total_cost=0.0, currency="GBP",
            batch_description="Auto-created from document uploads",
            price_per_page=None, created_by="u-a",
        )
    )
    item = asyncio.run(
        world.manual_extraction.create_item(
            batch.id, "invoice.pdf", "uploads/org-a/invoice.pdf", 1, "pdf", "pending",
            file_id="file-1",
        )
    )
    world.files.add_file(
        _file_row(metadata={"ocr": {"status": "ok", "text": "Gas 38.5 tonnes", "method": "tesseract_ocr"}})
    )
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.get(f"/api/v3/processing/items/{item.id}/workspace")
    assert resp.status_code == 200
    assert resp.json()["source"]["ocr_text"] == "Gas 38.5 tonnes"


def test_workspace_surfaces_ocr_suggestions(world, client, user_provider):
    """Suggested fields are surfaced separately from confirmed extracted_data."""
    _seed_ops_staff(world)
    batch = asyncio.run(
        world.manual_extraction.create_batch(
            org_id="org-a", batch_name="Uploads", total_documents=1, total_pages=1,
            total_cost=0.0, currency="GBP",
            batch_description="Auto-created from document uploads",
            price_per_page=None, created_by="u-op",
        )
    )
    item = asyncio.run(
        world.manual_extraction.create_item(
            batch.id, "invoice.pdf", "uploads/org-a/invoice.pdf", 1, "pdf", "pending",
            file_id="file-1",
        )
    )
    world.files.add_file(
        _file_row(metadata={"ocr": {
            "status": "ok", "text": "Electricity 12500 kWh",
            "suggested_data": {"quantity": 12500.0, "unit": "kWh", "activity": "Electricity"},
            "unresolved": [],
        }})
    )
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    resp = client.get(f"/api/v3/ops/items/{item.id}/workspace")
    assert resp.status_code == 200
    body = resp.json()
    # Three-way distinction:
    assert body["source"]["ocr_text"] == "Electricity 12500 kWh"   # reference text
    assert body["source"]["ocr_suggestions"]["quantity"] == 12500.0  # suggestions
    assert body["data"]["extracted_data"] == {}                      # NOT confirmed yet


def test_ocr_rerun_does_not_overwrite_human_extracted_data(world, client, user_provider, monkeypatch):
    """A later OCR run must never overwrite human-confirmed extracted_data."""
    _seed_ops_staff(world)
    batch = asyncio.run(
        world.manual_extraction.create_batch(
            org_id="org-a", batch_name="Uploads", total_documents=1, total_pages=1,
            total_cost=0.0, currency="GBP",
            batch_description="Auto-created from document uploads",
            price_per_page=None, created_by="u-op",
        )
    )
    item = asyncio.run(
        world.manual_extraction.create_item(
            batch.id, "invoice.pdf", "uploads/org-a/invoice.pdf", 1, "pdf", "pending",
            file_id="file-1",
        )
    )
    # Human confirms extracted data.
    asyncio.run(
        world.manual_extraction.save_extracted_data(
            item.id, {"quantity": 99.0, "unit": "kWh", "activity": "Electricity",
                      "supplier": "Human Corrected Ltd", "date": "2026-01-01"}, "u-op"
        )
    )
    world.files.add_file(_file_row(metadata={"data_type": "utility"}))
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))

    monkeypatch.setattr(v3_documents, "_extract_document_text", lambda *a, **k: {
        "status": "ok", "method": "tesseract_ocr", "text": "OCR garbage 5000",
        "suggested_data": {"quantity": 5000.0}, "unresolved": [], "detail": None,
    })
    fake_client = mock.Mock()
    fake_client.storage.from_.return_value.download.return_value = b"pdf-bytes"
    monkeypatch.setattr(v3_documents, "get_service_client", lambda: fake_client)

    resp = client.post("/api/v3/uploads/file-1/ocr")
    assert resp.status_code == 200

    stored = asyncio.run(world.manual_extraction.get_item(item.id))
    # Human data and status untouched by the OCR re-run.
    assert stored.extracted_data["quantity"] == 99.0
    assert stored.extracted_data["supplier"] == "Human Corrected Ltd"
    assert stored.status == "extracted"


def test_upload_ocr_persists_suggestions(world, client, user_provider, monkeypatch):
    """Inline upload OCR persists suggested_data but never auto-approves."""
    _seed_ops_staff(world)
    batch = asyncio.run(
        world.manual_extraction.create_batch(
            org_id="org-a", batch_name="Uploads", total_documents=1, total_pages=1,
            total_cost=0.0, currency="GBP",
            batch_description="Auto-created from document uploads",
            price_per_page=None, created_by="u-op",
        )
    )
    item = asyncio.run(
        world.manual_extraction.create_item(
            batch.id, "invoice.pdf", "uploads/org-a/invoice.pdf", 1, "pdf", "pending",
            file_id="file-1",
        )
    )
    world.files.add_file(_file_row())
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    monkeypatch.setattr(v3_documents, "_extract_document_text", lambda *a, **k: {
        "status": "ok", "method": "pdf_text", "text": "Electricity 12500 kWh",
        "suggested_data": {"quantity": 12500.0, "unit": "kWh"},
        "unresolved": ["supplier"], "detail": None,
    })
    fake_client = mock.Mock()
    fake_client.storage.from_.return_value.download.return_value = b"pdf-bytes"
    monkeypatch.setattr(v3_documents, "get_service_client", lambda: fake_client)

    resp = client.post("/api/v3/uploads/file-1/ocr")
    assert resp.status_code == 200
    stored = asyncio.run(world.files.get("file-1"))
    ocr = stored.metadata["ocr"]
    assert ocr["suggested_data"]["quantity"] == 12500.0
    assert "supplier" in ocr["unresolved"]
    # The suggestion never advances the item automatically — it stays pending
    # with NO extracted_data until a human confirms via the /extract endpoint.
    stored_item = asyncio.run(world.manual_extraction.get_item(item.id))
    assert stored_item.status == "pending"
    assert stored_item.extracted_data is None




def test_helper_never_raises(monkeypatch):
    def _boom(self, *a, **k):
        raise RuntimeError("engine exploded")

    monkeypatch.setattr("pdf_engine.PDFExtractor", lambda: SimpleNamespace(
        _extract_text_direct=_boom, _extract_text_ocr=_boom,
        _get_page_count=_boom, extract_image_text=_boom,
    ))
    out = v3_documents._extract_document_text(b"x", "bad.pdf", "application/pdf")
    assert out["status"] == "error"
    assert "engine exploded" in out["detail"]
