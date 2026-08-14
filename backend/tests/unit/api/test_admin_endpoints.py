"""Phase 10.4 — admin endpoint contract tests.

Covers the admin surface (imports, providers, audit, aliases): authorized
access, unauthorized/org isolation, response structure, no accidental database
mutation on read-only endpoints, and CRUD/validation behaviour.
"""
from __future__ import annotations

import asyncio

import pytest

from tests.unit.api.fakes import member_user, seed_audit_entry


# ===========================================================================
# Admin imports
# ===========================================================================


def test_imports_list_authorized_admin(client):
    response = client.get("/api/v2/admin/imports", params={"provider": "defra"})
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "defra"
    assert body["total"] == 2
    assert body["batches"][0]["id"] == "batch-defra-2025"
    assert body["batches"][0]["is_active"] is True
    assert body["batches"][0]["rows_imported"] == 7029


def test_imports_list_requires_admin(client, user_provider):
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v2/admin/imports", params={"provider": "defra"})
    assert response.status_code == 403


def test_imports_list_requires_authenticated(client, user_provider):
    user_provider.set_unauthenticated()
    response = client.get("/api/v2/admin/imports", params={"provider": "defra"})
    assert response.status_code == 401


def test_imports_list_paging(client):
    response = client.get(
        "/api/v2/admin/imports", params={"provider": "defra", "limit": 1, "offset": 1}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["batches"]) == 1
    assert body["batches"][0]["id"] == "batch-defra-2024"


def test_imports_active_batch(client):
    response = client.get(
        "/api/v2/admin/imports/active",
        params={"provider": "seai", "reporting_year": 2025},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["batch"]["id"] == "batch-seai-2025"
    assert body["batch"]["provider_key"] == "seai"
    assert body["batch"]["rows_imported"] == 20


def test_imports_active_batch_none(client):
    response = client.get(
        "/api/v2/admin/imports/active",
        params={"provider": "defra", "reporting_year": 2023},
    )
    assert response.status_code == 200
    assert response.json()["batch"] is None


def test_imports_get_by_id(client):
    response = client.get("/api/v2/admin/imports/batch-seai-2025")
    assert response.status_code == 200
    assert response.json()["id"] == "batch-seai-2025"


def test_imports_get_by_id_unknown(client):
    response = client.get("/api/v2/admin/imports/no-such-batch")
    assert response.status_code == 404


def test_imports_read_only_no_mutation(world, client):
    before = len(world.imports._batches)
    client.get("/api/v2/admin/imports", params={"provider": "defra"})
    client.get("/api/v2/admin/imports/active", params={"provider": "defra", "reporting_year": 2025})
    client.get("/api/v2/admin/imports/batch-defra-2025")
    assert len(world.imports._batches) == before


# ===========================================================================
# Admin providers
# ===========================================================================


def test_providers_listing_implemented_and_deferred(client):
    response = client.get("/api/v2/admin/providers")
    assert response.status_code == 200
    by_key = {p["key"]: p for p in response.json()["providers"]}
    assert set(by_key) == {"seai", "defra", "epa", "ademe", "ipcc"}
    assert by_key["seai"]["implemented"] is True
    assert by_key["defra"]["implemented"] is True
    # Deferred providers are never reported as implemented (Phase 10 boundary).
    for key in ("epa", "ademe", "ipcc"):
        assert by_key[key]["implemented"] is False
        assert by_key[key]["status"] == "deferred"


def test_providers_listing_attaches_live_state(client):
    response = client.get("/api/v2/admin/providers")
    by_key = {p["key"]: p for p in response.json()["providers"]}
    assert by_key["defra"]["factor_count"] == 1  # seeded factors
    assert by_key["defra"]["active_batches"][0]["id"] == "batch-defra-2025"
    assert by_key["seai"]["factor_count"] == 1


def test_provider_by_key(client):
    response = client.get("/api/v2/admin/providers/seai")
    assert response.status_code == 200
    body = response.json()
    assert body["implemented"] is True
    assert body["country_codes"] == ["IE"]


def test_provider_unknown_key(client):
    response = client.get("/api/v2/admin/providers/nasa")
    assert response.status_code == 404


def test_providers_requires_admin(client, user_provider):
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v2/admin/providers")
    assert response.status_code == 403


# ===========================================================================
# Admin audit
# ===========================================================================


@pytest.fixture
def audit_seeded(world):
    asyncio.run(
        world.audit.record(
            seed_audit_entry(
                action="report:generated",
                entity_type="report",
                entity_id="report-1",
                correlation_id="corr-1",
                actor="admin-1",
            )
        )
    )
    asyncio.run(
        world.audit.record(
            seed_audit_entry(
                action="factor_alias:created",
                entity_type="factor_alias",
                entity_id="alias-x",
                correlation_id="corr-2",
                actor="admin-1",
            )
        )
    )
    return world


def test_audit_query_by_action(client, audit_seeded):
    response = client.get("/api/v2/admin/audit", params={"action": "report:generated"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["entries"][0]["action"] == "report:generated"
    assert body["entries"][0]["entity_type"] == "report"


def test_audit_query_requires_admin(client, audit_seeded, user_provider):
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v2/admin/audit", params={"action": "report:generated"})
    assert response.status_code == 403


def test_audit_by_correlation(client, audit_seeded):
    response = client.get("/api/v2/admin/audit/correlation/corr-1")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["entries"][0]["correlation_id"] == "corr-1"


def test_audit_entry_by_id(client, audit_seeded):
    entries = client.get("/api/v2/admin/audit").json()["entries"]
    entry_id = entries[0]["id"]
    response = client.get(f"/api/v2/admin/audit/{entry_id}")
    assert response.status_code == 200
    assert response.json()["id"] == entry_id


def test_audit_entry_unknown(client):
    response = client.get("/api/v2/admin/audit/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_audit_export_csv(client, audit_seeded):
    response = client.get("/api/v2/admin/audit/export", params={"action": "report:generated"})
    assert response.status_code == 200
    body = response.json()
    assert body["content_type"] == "text/csv"
    assert "correlation_id" in body["csv"]
    assert "report:generated" in body["csv"]


# ===========================================================================
# Admin aliases
# ===========================================================================


def test_aliases_list_global(client):
    response = client.get("/api/v2/admin/aliases")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["aliases"][0]["alias_text"] == "NG"
    assert body["aliases"][0]["organization_id"] is None


def test_aliases_list_org_scoped(client):
    response = client.get("/api/v2/admin/aliases", params={"organization_id": "org-a"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["aliases"][0]["alias_text"] == "GasNet"
    assert body["aliases"][0]["organization_id"] == "org-a"


def test_aliases_list_requires_admin(client, user_provider):
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v2/admin/aliases")
    assert response.status_code == 403


def test_alias_create_global(client, world):
    response = client.post(
        "/api/v2/admin/aliases",
        json={
            "alias_text": "Petrol",
            "target_activity_type": "Fuels > Liquid fuels > Petrol (kg CO2e) [litres]",
            "target_provider_key": "defra",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["alias_text"] == "Petrol"
    assert body["organization_id"] is None
    assert body["created_by"] == "admin-1"

    listed = client.get("/api/v2/admin/aliases").json()
    assert listed["total"] == 2

    # The write is recorded through the existing audit repository.
    audit_actions = [e.action for e in world.audit._entries]
    assert "factor_alias:created" in audit_actions


def test_alias_create_org_scoped(client):
    response = client.post(
        "/api/v2/admin/aliases",
        json={
            "alias_text": "DieselNet",
            "target_activity_type": "Fuels > Liquid fuels > Diesel (kg CO2e) [litres]",
            "target_provider_key": "defra",
            "organization_id": "org-b",
        },
    )
    assert response.status_code == 201
    assert response.json()["organization_id"] == "org-b"


def test_alias_create_missing_fields(client):
    response = client.post("/api/v2/admin/aliases", json={"alias_text": "Petrol"})
    assert response.status_code == 422


def test_alias_update(client, world):
    response = client.put(
        "/api/v2/admin/aliases/alias-ng",
        json={"alias_text": "Natural Gas (NG)"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["alias_text"] == "Natural Gas (NG)"
    assert "factor_alias:updated" in [e.action for e in world.audit._entries]


def test_alias_update_empty_payload(client):
    response = client.put("/api/v2/admin/aliases/alias-ng", json={})
    assert response.status_code == 422


def test_alias_update_unknown(client):
    response = client.put("/api/v2/admin/aliases/no-such-alias", json={"alias_text": "X"})
    assert response.status_code == 404


def test_alias_delete(client, world):
    response = client.delete("/api/v2/admin/aliases/alias-a1")
    assert response.status_code == 204
    assert "factor_alias:deleted" in [e.action for e in world.audit._entries]
    listed = client.get("/api/v2/admin/aliases", params={"organization_id": "org-a"}).json()
    assert listed["total"] == 0


def test_alias_delete_unknown(client):
    response = client.delete("/api/v2/admin/aliases/no-such-alias")
    assert response.status_code == 404


