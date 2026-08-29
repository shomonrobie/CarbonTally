"""Phase C — Security / Factor Lifecycle regression tests.

Covers the CL-42..CL-47 acceptance contracts:

* CL-42  Viewer upload is denied with 403 BEFORE any storage/DB write;
         owner/admin/member keep 201.
* CL-43  Customer-factor lifecycle: duplicate family/version is a clean 409
         (never a 500); factor version is representable; an approved factor can
         receive a new version (draft N+1); create with an explicit version.
* CL-44  Approved customer factors appear in mapping-options on both the
         customer surface and the ops surface, labelled with the source.
* CL-47  Spend/GBP activities return an actionable ``spend_suggestion`` instead
         of a silent empty factor list.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal

from auth import AuthUser
from domain.customer_factor import CustomerFactor
from tests.unit.api.fakes import (
    InMemoryWorld,
    member_user,
    org_owner_user,
    staff_user,
)


def _viewer_user(org_id: str = "org-a", user_id: str = "viewer-1") -> AuthUser:
    """A read-only organisation Viewer (CL-42 — the read-only org role)."""
    return AuthUser(
        user_id=user_id,
        email="viewer@test",
        role="org_viewer",
        role_name="org_viewer",
        organization_id=org_id,
        is_org_member=True,
    )


def _customer_factor(
    *,
    factor_id: str,
    org_id: str = "org-a",
    activity_type: str = "Electricity",
    unit: str = "kWh",
    scope: str = "Scope 2",
    status: str = "draft",
    version: int = 1,
    name: str = "Customer Electricity Factor",
    co2e: str = "0.31",
) -> CustomerFactor:
    return CustomerFactor(
        id=factor_id,
        organization_id=org_id,
        name=name,
        activity_type=activity_type,
        co2e_multiplier=Decimal(co2e),
        unit=unit,
        scope=scope,
        country="GB",
        reporting_year=2025,
        status=status,
        version=version,
        created_by="member-1",
    )


async def _seed_batch_with_item_async(world: InMemoryWorld):
    batch = await world.manual_extraction.create_batch("org-a", "Phase C batch")
    item = await world.manual_extraction.create_item(
        batch.id,
        file_name="invoice-2025.pdf",
        file_url="storage/docs/invoice-2025.pdf",
        document_type="invoice",
        status="pending",
    )
    return batch, item


def _seed_batch_with_item(world: InMemoryWorld):
    return asyncio.run(_seed_batch_with_item_async(world))


# ---------------------------------------------------------------------------
# CL-42 — Viewer upload deny
# ---------------------------------------------------------------------------


class TestCl42ViewerUploadDenied:
    def test_viewer_upload_is_403_before_any_write(self, world, client, user_provider) -> None:
        user_provider.set_user(_viewer_user())
        resp = client.post(
            "/api/v3/uploads",
            data={"organization_id": "org-a", "data_type": "utility"},
            files={"file": ("viewer_upload.pdf", b"sample pdf bytes", "application/pdf")},
        )
        assert resp.status_code == 403
        # The API's uniform error envelope (ErrorResponse) carries the reason.
        assert "read-only" in resp.json()["error"]["message"].lower()
        # No storage record was created — the deny happens before any write.
        assert world.files._by_id == {}

    def test_owner_upload_remains_201(self, world, client, user_provider, monkeypatch) -> None:
        class _StorageBucket:
            def upload(self, path, content, **kwargs):
                return None

        class _Storage:
            def from_(self, bucket):
                return _StorageBucket()

        class _Client:
            storage = _Storage()

        import api.v3_documents as docs

        monkeypatch.setattr(docs, "get_service_client", lambda: _Client())
        monkeypatch.setattr(docs, "storage_signed_url", lambda path: f"https://signed/{path}")
        user_provider.set_user(org_owner_user("org-a", "owner-1", "owner@test"))
        resp = client.post(
            "/api/v3/uploads",
            data={"organization_id": "org-a", "data_type": "utility"},
            files={"file": ("owner_upload.pdf", b"sample pdf bytes", "application/pdf")},
        )
        assert resp.status_code == 201
        assert world.files._by_id, "owner upload must create the organisation_files row"


# ---------------------------------------------------------------------------
# CL-43 — customer-factor lifecycle
# ---------------------------------------------------------------------------


class TestCl43FactorLifecycle:
    def test_duplicate_family_returns_409_not_500(self, world, client, user_provider) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        payload = {
            "organization_id": "org-a",
            "name": "My Electricity Factor",
            "activity_type": "Electricity",
            "co2e_multiplier": "0.31",
            "reporting_year": 2025,
            "unit": "kWh",
            "scope": "Scope 2",
        }
        assert client.post("/api/v3/customer-factors", json=payload).status_code == 201
        # Same family + same resolved version (1) -> clean 409, never a 500.
        resp = client.post("/api/v3/customer-factors", json=payload)
        assert resp.status_code == 409
        assert "already exists" in resp.json()["error"]["message"]

    def test_approved_factor_can_receive_new_version(self, world, client, user_provider) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        base = {
            "organization_id": "org-a",
            "name": "My Electricity Factor",
            "activity_type": "Electricity",
            "co2e_multiplier": "0.31",
            "reporting_year": 2025,
            "unit": "kWh",
            "scope": "Scope 2",
        }
        v1 = client.post("/api/v3/customer-factors", json=base).json()
        assert v1["version"] == 1
        # Approve v1 (owner may self-approve — PO Decision).
        user_provider.set_user(org_owner_user("org-a", "owner-1", "owner@test"))
        assert client.post(f"/api/v3/customer-factors/{v1['id']}/approve").status_code == 200
        # D-cf-4 — a NEW version is a draft N+1, never an edit of the active row.
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        v2 = client.post(
            "/api/v3/customer-factors",
            json={**base, "name": "My Electricity Factor v2", "co2e_multiplier": "0.29"},
        )
        assert v2.status_code == 201
        body = v2.json()
        assert body["version"] == 2
        assert body["status"] == "draft"
        assert body["id"] != v1["id"]
        # The active v1 row is untouched.
        active = client.get(f"/api/v3/customer-factors/{v1['id']}").json()
        assert active["version"] == 1
        assert active["status"] == "active"

    def test_explicit_existing_version_is_409(self, world, client, user_provider) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        base = {
            "organization_id": "org-a",
            "name": "F",
            "activity_type": "Electricity",
            "co2e_multiplier": "0.31",
            "reporting_year": 2025,
            "unit": "kWh",
            "scope": "Scope 2",
        }
        assert client.post("/api/v3/customer-factors", json=base).status_code == 201
        resp = client.post("/api/v3/customer-factors", json={**base, "version": 1})
        assert resp.status_code == 409

    def test_explicit_fresh_version_creates_with_that_version(self, world, client, user_provider) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        base = {
            "organization_id": "org-a",
            "name": "Explicit",
            "activity_type": "Water",
            "co2e_multiplier": "0.10",
            "reporting_year": 2025,
            "unit": "m3",
            "scope": "Scope 3",
        }
        resp = client.post("/api/v3/customer-factors", json={**base, "version": 7})
        assert resp.status_code == 201
        assert resp.json()["version"] == 7


# ---------------------------------------------------------------------------
# CL-44 / CL-47 — mapping-options carry approved customer factors + spend guidance
# ---------------------------------------------------------------------------


class TestCl44MappingOptionsCustomerFactors:
    def test_ops_mapping_options_include_approved_customer_factors(
        self, world, client, user_provider
    ) -> None:
        from tests.unit.api.test_v3_operations import _seed_ops_world

        _seed_ops_world(world)
        _batch, item = _seed_batch_with_item(world)
        asyncio.run(
            world.customer_factors.save(
                _customer_factor(factor_id="cf-active", status="active", version=1)
            )
        )
        user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
        resp = client.get(f"/api/v3/ops/items/{item.id}/mapping-options")
        assert resp.status_code == 200
        body = resp.json()
        customer = [f for f in body["customer_factors"] if f["id"] == "cf-active"]
        assert customer, "approved customer factor must appear in mapping-options"
        assert customer[0]["factor_kind"] == "customer_factor"
        # With an approved customer factor available the reason must be absent.
        assert body["no_factors_reason"] is None

    def test_customer_mapping_options_include_approved_customer_factors(
        self, world, client, user_provider
    ) -> None:
        _batch, item = _seed_batch_with_item(world)
        asyncio.run(
            world.customer_factors.save(
                _customer_factor(factor_id="cf-active", status="active", version=1)
            )
        )
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.get(f"/api/v3/processing/items/{item.id}/mapping-options")
        assert resp.status_code == 200
        body = resp.json()
        assert any(f["id"] == "cf-active" for f in body["customer_factors"])
        assert body["no_factors_reason"] is None

    def test_draft_customer_factors_do_not_appear_in_mapping_options(
        self, world, client, user_provider
    ) -> None:
        _batch, item = _seed_batch_with_item(world)
        asyncio.run(
            world.customer_factors.save(
                _customer_factor(factor_id="cf-draft", status="draft", version=1)
            )
        )
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.get(f"/api/v3/processing/items/{item.id}/mapping-options")
        assert resp.status_code == 200
        assert resp.json()["customer_factors"] == []

    def test_spend_activity_returns_actionable_suggestion(self, world, client, user_provider) -> None:
        batch, item = _seed_batch_with_item(world)
        asyncio.run(
            world.manual_extraction.save_extracted_data(
                item.id,
                {
                    "supplier": "SpendCo",
                    "activity": "Purchased goods",
                    "quantity": "12500",
                    "unit": "GBP",
                    "amount": "12500",
                },
                "member-1",
            )
        )
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.get(f"/api/v3/processing/items/{item.id}/mapping-options")
        assert resp.status_code == 200
        body = resp.json()
        assert body["factors"] == []
        assert body["customer_factors"] == []
        # CL-47 — never a silent empty list: the response explains the supported
        # spend workflow (create an approved customer factor in the currency unit).
        assert body["no_factors_reason"]
        assert body["spend_suggestion"] is not None
        assert body["spend_suggestion"]["kind"] == "spend_based"
        assert body["spend_suggestion"]["unit"] == "GBP"
        assert body["spend_suggestion"]["action"] == "create_customer_factor"

    def test_unrelated_customer_factor_does_not_mask_spend_dead_end(
        self, world, client, user_provider
    ) -> None:
        """CL-47 — an approved Diesel factor must not hide a spend dead-end.

        The org owns an approved Diesel/litres factor; the item is a Purchased
        goods/GBP spend activity. The picker still shows the customer factor,
        but the spend guidance must still fire (no factor covers THIS activity).
        """
        _batch, item = _seed_batch_with_item(world)
        asyncio.run(
            world.customer_factors.save(
                _customer_factor(
                    factor_id="cf-diesel",
                    activity_type="Diesel",
                    unit="litres",
                    scope="Scope 1",
                    status="active",
                    version=1,
                )
            )
        )
        asyncio.run(
            world.manual_extraction.save_extracted_data(
                item.id,
                {
                    "supplier": "SpendCo",
                    "activity": "Purchased goods",
                    "quantity": "12500",
                    "unit": "GBP",
                    "amount": "12500",
                },
                "member-1",
            )
        )
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.get(f"/api/v3/processing/items/{item.id}/mapping-options")
        assert resp.status_code == 200
        body = resp.json()
        assert any(f["id"] == "cf-diesel" for f in body["customer_factors"])
        assert body["spend_suggestion"] is not None
        assert body["spend_suggestion"]["kind"] == "spend_based"

