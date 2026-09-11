"""P6-2F — deterministic synthetic E2E fixtures.

Everything is created against the in-memory world (no database, no production
data, no real billing provider). The scenario is resettable by constructing a
fresh ``InMemoryWorld`` (every test gets an isolated ``world`` fixture).

The identities/relationships reuse the EXISTING authorization model — no new
production roles, capabilities or grants are invented for testing.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from domain.billing import BillingPlan, Subscription
from domain.staff import StaffProfile, StaffRole
from services.billing import BillingService

# --- stable synthetic identities -------------------------------------------------
ORG_A = "org-a"
ORG_B = "org-b"
FIRM_A = "firm-a"
FIRM_B = "firm-b"
CLIENT_A = "client-a"              # engagement: firm-a  <->  org-a  (ACTIVE)
CLIENT_B = "client-b"              # engagement: firm-b  <->  org-b  (ACTIVE)
CLIENT_A_SUSPENDED = "client-a-susp"  # engagement: firm-a <-> org-a (SUSPENDED)


def seed_firm(
    world,
    *,
    firm_id: str = FIRM_A,
    user_id: str = "u-firm-a",
    company: str = "Firm A",
    role: str = "manager",
    is_active: bool = True,
    **flags,
) -> str:
    """Seed a consultant firm profile + one active member (capabilities opt-in)."""
    world.consultants.seed_profile(firm_id, user_id, company, is_active=is_active)
    world.consultants.seed_firm_member(
        firm_id,
        user_id,
        role=role,
        is_active=is_active,
        can_manage_clients=flags.get("can_manage_clients", True),
        can_submit=flags.get("can_submit", True),
        can_extract=flags.get("can_extract", True),
        can_map=flags.get("can_map", True),
        can_validate=flags.get("can_validate", True),
        can_calculate=flags.get("can_calculate", True),
    )
    return firm_id


def seed_engagement(
    world,
    *,
    client_id: str = CLIENT_A,
    firm_id: str = FIRM_A,
    org_id: str = ORG_A,
    status: str = "active",
):
    """Seed a consultant-client grant (the authoritative relationship)."""
    return world.consultants.seed_client(
        client_id, firm_id, org_id, "Client Org", status=status,
        relationship_origin="consultant_created_customer",
    )


def seed_item(
    world,
    *,
    org_id: str = ORG_A,
    status: str = "pending",
    item_id: str | None = None,
    file_name: str = "invoice.pdf",
):
    """Seed a processing item under an organisation batch."""
    return world.manual_extraction.seed_item(
        item_id or f"item-{uuid.uuid4().hex[:8]}", org_id, file_name, status=status
    )


def seed_entitlement(world, org_id: str = ORG_A, *, credits: int = 500) -> None:
    """Seed a synthetic subscription + credits (no real billing provider)."""
    key = f"sub-{uuid.uuid4().hex[:8]}"
    asyncio.run(
        world.billing_plans.create(
            BillingPlan(
                id=str(uuid.uuid4()),
                plan_code="professional",
                name="Professional",
                price=149,
                currency="GBP",
                included_credits=credits,
                version=1,
                is_active=True,
                features={},
                effective_from=datetime.now(timezone.utc),
            ),
            created_by="admin-1",
        )
    )
    asyncio.run(
        world.billing_subscriptions.upsert_active(
            Subscription(
                id=str(uuid.uuid4()),
                organization_id=org_id,
                plan_code="professional",
                plan_version=1,
                billing_mode="CREDIT",
                lifecycle_status="active",
                current_period_start=datetime.now(timezone.utc),
                current_period_end=datetime.now(timezone.utc),
                idempotency_key=key,
            ),
            created_by="admin-1",
        )
    )
    asyncio.run(
        BillingService(world.bundle()).grant_credits(
            org_id, credits, source="plan_included", reason="monthly",
            idempotency_key=f"{key}-grant",
        )
    )


def seed_internal_staff(
    world, *, user_id: str, permissions: dict, role_id: str | None = None,
    entity_id: str | None = None,
) -> str:
    """Seed a CarbonTally internal staff profile with a real permission role."""
    role_id = role_id or f"role-{user_id}"
    world.staff.seed_role(StaffRole(id=role_id, name=role_id, permissions=dict(permissions)))
    world.staff.seed_profile(
        StaffProfile(
            id=f"sp-{user_id}", user_id=user_id, first_name=user_id, last_name="One",
            email=f"{user_id}@carbontally.test", role_id=role_id, entity_id=entity_id,
        )
    )
    return role_id


def seed_standard_scenario(world) -> None:
    """The representative two-organisation / two-firm baseline (ALLOW + DENY)."""
    seed_firm(world, firm_id=FIRM_A, user_id="u-firm-a", company="Firm A")
    seed_firm(world, firm_id=FIRM_B, user_id="u-firm-b", company="Firm B")
    seed_engagement(world, client_id=CLIENT_A, firm_id=FIRM_A, org_id=ORG_A, status="active")
    seed_engagement(world, client_id=CLIENT_B, firm_id=FIRM_B, org_id=ORG_B, status="active")
    seed_engagement(world, client_id=CLIENT_A_SUSPENDED, firm_id=FIRM_A, org_id=ORG_A, status="suspended")
    seed_internal_staff(world, user_id="u-qc", permissions={"can_qc": True})
    seed_internal_staff(world, user_id="u-ops", permissions={"can_manage_staff": True})
    seed_internal_staff(world, user_id="u-review", permissions={"can_review": True})
    seed_entitlement(world, ORG_A)
