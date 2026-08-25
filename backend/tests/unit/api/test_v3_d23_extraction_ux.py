"""V3 D23 — realistic end-to-end extraction: multi-line extraction/validation/
calculation + upload→extraction enqueue semantics.

Covers the D23 hardening:
* multi-line extraction (``extracted_data.line_items``) validates per line and
  calculates each mapped line (summed result; per-line emissions persisted)
* legacy single-line extraction/validation/calculation still works
* the upload→extraction bridge creates a reusable "Uploads" batch + item
  (repository-level semantics; the storage path is exercised live)
* entity staff can calculate multi-line work through their own workspace
"""
from __future__ import annotations

import asyncio

from domain.entity import ProcessingEntity
from domain.partners import ManualExtractionItem
from domain.staff import StaffProfile, StaffRole
from engines.processing_workflow import (
    has_blocking_findings,
    validate_processing_item,
)
from tests.unit.api.fakes import entity_operator_user, staff_user

# ---------------------------------------------------------------------------
# Seeding helpers
# ---------------------------------------------------------------------------


def _seed_ops_world(world) -> None:
    world.staff.seed_role(
        StaffRole(id="role-operator", name="operator", permissions={"can_process": True})
    )
    world.staff.seed_role(
        StaffRole(
            id="role-manager",
            name="manager",
            permissions={
                "can_manage_staff": True,
                "can_process": True,
                "can_review": True,
                "can_view_all": True,
            },
        )
    )
    world.staff.seed_role(
        StaffRole(id="role-reviewer", name="reviewer", permissions={"can_review": True})
    )
    asyncio.run(world.entities.save(ProcessingEntity(id="entity-1", name="Entity A", status="active")))
    profiles = [
        StaffProfile(
            id="sp-op", user_id="u-op", first_name="Op", last_name="One",
            email="op@carbontally.test", role_id="role-operator", entity_id=None,
        ),
        StaffProfile(
            id="sp-rev", user_id="u-rev", first_name="Rev", last_name="One",
            email="rev@carbontally.test", role_id="role-reviewer", entity_id=None,
        ),
        StaffProfile(
            id="sp-ent1", user_id="u-ent1", first_name="Ent", last_name="A",
            email="enta@entity.test", role_id="role-operator", entity_id="entity-1",
        ),
    ]
    for profile in profiles:
        world.staff.seed_profile(profile)


def _multi_line_item(world, entity_id: str | None = None) -> ManualExtractionItem:
    """A multi-line electricity+gas invoice item in an assignable batch."""
    batch = asyncio.run(
        world.manual_extraction.create_batch(
            "org-a", "D23 multi-line", created_by="u-op"
        )
    )
    if entity_id:
        asyncio.run(
            world.manual_extraction.update_batch(
                batch.id, status="in_progress", assigned_to=None,
                assigned_by="u-op", entity_id=entity_id,
            )
        )
    else:
        asyncio.run(
            world.manual_extraction.update_batch(
                batch.id, status="in_progress", assigned_to="u-op", assigned_by="u-op"
            )
        )
    item = asyncio.run(
        world.manual_extraction.create_item(
            batch.id, "d23-invoice.pdf", "https://files.test/d23.pdf", 2
        )
    )
    item = asyncio.run(
        world.manual_extraction.update_item(
            item.id,
            {
                "supplier": "ACME Utilities",
                "invoice_number": "INV-2025-001",
                "invoice_date": "2025-06-01",
                "currency": "GBP",
                "line_items": [
                    {"description": "Electricity", "activity": "Electricity", "quantity": "1000", "unit": "kWh", "amount": "120.00"},
                    {"description": "Natural gas", "activity": "Natural gas", "quantity": "500", "unit": "kWh", "amount": "40.00"},
                ],
            },
            None,
            None,
            "u-op",
        )
    )
    return item


def _map_lines(world, item: ManualExtractionItem) -> ManualExtractionItem:
    return asyncio.run(
        world.manual_extraction.update_item(
            item.id,
            item.extracted_data,
            {
                "line_items": [
                    {"activity_type": "Electricity", "factor_id": "factor-defra-gas"},
                    {"activity_type": "Natural gas", "factor_id": "factor-defra-gas"},
                ]
            },
            None,
            "u-op",
        )
    )


# ---------------------------------------------------------------------------
# 1. Multi-line validation (engine)
# ---------------------------------------------------------------------------


def test_multi_line_validation_accepts_valid_lines(world) -> None:
    _seed_ops_world(world)
    item = _multi_line_item(world)
    item = _map_lines(world, item)
    findings = validate_processing_item(item)
    assert not has_blocking_findings(findings)


def test_multi_line_validation_flags_missing_fields(world) -> None:
    _seed_ops_world(world)
    item = _multi_line_item(world)
    item = asyncio.run(
        world.manual_extraction.update_item(
            item.id,
            {
                "supplier": "ACME Utilities",
                "invoice_date": "2025-06-01",
                "line_items": [
                    {"description": "Gas", "activity": "", "quantity": "x", "unit": ""},
                    {"description": "Elec", "activity": "Electricity", "quantity": "-5", "unit": "kWh"},
                ],
            },
            None,
            None,
            "u-op",
        )
    )
    findings = validate_processing_item(item)
    assert has_blocking_findings(findings)
    codes = {f.code for f in findings}
    assert "EXTRACTION_MISSING_FIELD" in codes
    assert "INVALID_QUANTITY" in codes
    assert "NEGATIVE_QUANTITY" in codes
    assert "MISSING_UNIT" in codes
    assert "MAPPING_MISSING" in codes or "FACTOR_MISSING" in codes


def test_multi_line_validation_requires_every_line_factor(world) -> None:
    _seed_ops_world(world)
    item = _multi_line_item(world)
    item = asyncio.run(
        world.manual_extraction.update_item(
            item.id,
            item.extracted_data,
            {"line_items": [{"activity_type": "Electricity", "factor_id": "factor-defra-gas"}]},
            None,
            "u-op",
        )
    )
    findings = validate_processing_item(item)
    assert any(f.code == "FACTOR_MISSING" for f in findings)


# ---------------------------------------------------------------------------
# 2. Multi-line calculation (internal operator + entity)
# ---------------------------------------------------------------------------


def test_internal_operator_multi_line_calculate(client, world, user_provider) -> None:
    _seed_ops_world(world)
    item = _multi_line_item(world)
    # API flow: start/extract (multi-line), map (per-line factors), validate,
    # start calculation, calculate.
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    assert client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "extraction"}).status_code == 200
    extracted = client.post(
        f"/api/v3/ops/items/{item.id}/extract",
        json={
            "extracted_data": {
                "supplier": "ACME Utilities",
                "invoice_number": "INV-2025-001",
                "invoice_date": "2025-06-01",
                "currency": "GBP",
                "line_items": [
                    {"description": "Electricity", "activity": "Electricity", "quantity": "1000", "unit": "kWh", "amount": "120.00"},
                    {"description": "Natural gas", "activity": "Natural gas", "quantity": "500", "unit": "kWh", "amount": "40.00"},
                ],
            }
        },
    )
    assert extracted.status_code == 200, extracted.text
    mapped = client.post(
        f"/api/v3/ops/items/{item.id}/map",
        json={
            "mapped_data": {
                "line_items": [
                    {"activity_type": "Electricity", "factor_id": "factor-defra-gas"},
                    {"activity_type": "Natural gas", "factor_id": "factor-defra-gas"},
                ]
            }
        },
    )
    assert mapped.status_code == 200, mapped.text
    assert mapped.json()["item"]["status"] == "mapped"
    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))
    assert client.post(f"/api/v3/ops/items/{item.id}/validate").status_code == 200
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    assert client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "calculation"}).status_code == 200
    response = client.post(f"/api/v3/ops/items/{item.id}/calculate", json={})
    assert response.status_code == 200, response.text
    body = response.json()
    # 1000 * 0.183 + 500 * 0.183 = 274.5
    assert abs(float(body["result"]["co2e_kg"]) - 274.5) < 0.01
    assert body["result"]["multi_line"] is True
    assert body["item"]["status"] == "calculated"
    lines = body["item"]["mapped_data"]["line_items"]
    assert len(lines) == 2
    assert all(l.get("emissions_kg") is not None for l in lines)


def test_entity_staff_multi_line_calculate(client, world, user_provider) -> None:
    _seed_ops_world(world)
    item = _multi_line_item(world, entity_id="entity-1")
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    assert client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{item.id}/start",
        json={"stage": "extraction"},
    ).status_code == 200
    assert client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{item.id}/extract",
        json={
            "extracted_data": {
                "supplier": "ACME Utilities",
                "invoice_date": "2025-06-01",
                "currency": "GBP",
                "line_items": [
                    {"description": "Electricity", "activity": "Electricity", "quantity": "1000", "unit": "kWh", "amount": "120.00"},
                    {"description": "Natural gas", "activity": "Natural gas", "quantity": "500", "unit": "kWh", "amount": "40.00"},
                ],
            }
        },
    ).status_code == 200
    assert client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{item.id}/map",
        json={
            "mapped_data": {
                "line_items": [
                    {"activity_type": "Electricity", "factor_id": "factor-defra-gas"},
                    {"activity_type": "Natural gas", "factor_id": "factor-defra-gas"},
                ]
            }
        },
    ).status_code == 200
    # CarbonTally's validation gate reviews the entity's output (D22), then the
    # entity calculates.
    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))
    assert client.post(f"/api/v3/ops/items/{item.id}/validate").status_code == 200
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    assert client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{item.id}/start",
        json={"stage": "calculation"},
    ).status_code == 200
    response = client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{item.id}/calculate",
        json={},
    )
    assert response.status_code == 200, response.text
    assert abs(float(response.json()["result"]["co2e_kg"]) - 274.5) < 0.01
    assert response.json()["item"]["status"] == "calculated"


def test_entity_mapping_options_endpoint(client, world, user_provider) -> None:
    _seed_ops_world(world)
    item = _multi_line_item(world, entity_id="entity-1")
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    response = client.get(
        f"/api/v3/ops/entities/entity-1/extraction/items/{item.id}/mapping-options"
    )
    assert response.status_code == 200
    assert "factors" in response.json()
    assert "facilities" in response.json()
    user_provider.set_user(entity_operator_user("entity-2", "u-ent2"))
    assert (
        client.get(
            f"/api/v3/ops/entities/entity-2/extraction/items/{item.id}/mapping-options"
        ).status_code
        == 403
    )


# ---------------------------------------------------------------------------
# 3. Legacy single-line still works
# ---------------------------------------------------------------------------


def test_single_line_validation_still_works(world) -> None:
    _seed_ops_world(world)
    batch = asyncio.run(
        world.manual_extraction.create_batch("org-a", "single", created_by="u-op")
    )
    asyncio.run(
        world.manual_extraction.update_batch(
            batch.id, status="in_progress", assigned_to="u-op", assigned_by="u-op"
        )
    )
    item = asyncio.run(
        world.manual_extraction.create_item(
            batch.id, "single.pdf", "https://files.test/single.pdf", 1
        )
    )
    item = asyncio.run(
        world.manual_extraction.update_item(
            item.id,
            {
                "supplier": "S",
                "date": "2025-06-01",
                "activity": "Natural gas",
                "quantity": "1000",
                "unit": "kWh",
            },
            None,
            None,
            "u-op",
        )
    )
    findings = validate_processing_item(item, require_mapping=False)
    assert not has_blocking_findings(findings)


# ---------------------------------------------------------------------------
# 4. Upload→extraction enqueue semantics (repository-level)
# ---------------------------------------------------------------------------


def test_upload_enqueue_reuses_uploads_batch_and_creates_item(world) -> None:
    _seed_ops_world(world)
    batch = asyncio.run(
        world.manual_extraction.create_batch(
            org_id="org-a",
            batch_name="Uploads",
            total_documents=1,
            total_pages=1,
            total_cost=0.0,
            currency="GBP",
            batch_description="Auto-created from document uploads",
            price_per_page=None,
            created_by="u-op",
        )
    )
    item = asyncio.run(
        world.manual_extraction.create_item(
            batch.id, "invoice.pdf", "https://storage/invoice.pdf", 2, "pdf", "pending"
        )
    )
    assert item.batch_id == batch.id
    assert item.status == "pending"
    assert item.page_count == 2

