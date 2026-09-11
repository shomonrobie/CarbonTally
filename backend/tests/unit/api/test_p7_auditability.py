"""Phase 7 — Auditor / Assurance API tests (authorization + shape).

Covers the auditability surface added by Phase 7:
- org-scoped audit activity / readiness / evidence package authorization
  (owner/admin ALLOW; member DENY; PE staff DENY; cross-tenant DENY;
  internal staff ALLOW)
- the ops audit console's new taxonomy investigation filters
- the entity-scoped activity surface's scope enforcement

All tests run in memory over the shared fakes; the database is never opened.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from domain.audit import (
    CAT_AUTH,
    CAT_CALCULATION,
    ORIGIN_SYSTEM,
    AuditEntry,
)
from tests.unit.api.fakes import (
    entity_operator_user,
    member_user,
    org_admin_user,
    org_owner_user,
    staff_user,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_staff(world, user_id, permissions, entity_id=None):
    from domain.staff import StaffProfile, StaffRole

    world.staff.seed_role(StaffRole(id=f"role-{user_id}", name="x", permissions=permissions))
    world.staff.seed_profile(
        StaffProfile(
            id=f"sp-{user_id}",
            user_id=user_id,
            first_name="A",
            last_name="B",
            email=f"{user_id}@carbontally.test",
            role_id=f"role-{user_id}",
            entity_id=entity_id,
            is_active=True,
        )
    )


def _seed_audit(world, entries):
    for e in entries:
        asyncio.run(world.audit.record(e))


def _entry(i, *, action, category=None, origin=None, org=None, actor="u-1"):
    return AuditEntry(
        id=f"audit-{i}",
        correlation_id="corr-1",
        entity_type="manual_extraction_item",
        entity_id=f"ent-{i}",
        action=action,
        actor=actor,
        occurred_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        category=category,
        origin=origin,
        organization_id=org,
    )


# ---------------------------------------------------------------------------
# Org-scoped audit activity — authorization
# ---------------------------------------------------------------------------


def test_audit_activity_org_admin_allowed(client, world, user_provider):
    world.reporting.audit_activity_result = {
        "organization_id": "org-a",
        "total": 1,
        "events": [{"action": "document:uploaded", "category": "document"}],
    }
    user_provider.set_user(org_admin_user("org-a", "u-a", "a@example.test"))
    resp = client.get("/api/v3/reporting/audit-activity?organization_id=org-a")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["events"][0]["action"] == "document:uploaded"


def test_audit_activity_org_owner_allowed(client, world, user_provider):
    user_provider.set_user(org_owner_user("org-a", "u-o", "o@example.test"))
    assert client.get(
        "/api/v3/reporting/audit-activity?organization_id=org-a"
    ).status_code == 200


def test_audit_activity_member_denied(client, world, user_provider):
    """Member (not owner/admin) must not read org audit records."""
    user_provider.set_user(member_user("org-a", "u-m", "m@example.test"))
    assert client.get(
        "/api/v3/reporting/audit-activity?organization_id=org-a"
    ).status_code == 403


def test_audit_activity_cross_tenant_denied(client, world, user_provider):
    """An org admin of A cannot read B's audit activity."""
    user_provider.set_user(org_admin_user("org-a", "u-a", "a@example.test"))
    assert client.get(
        "/api/v3/reporting/audit-activity?organization_id=org-b"
    ).status_code == 403


def test_audit_activity_internal_staff_allowed(client, world, user_provider):
    _seed_staff(world, "u-admin", {"can_manage_staff": True, "can_view_all": True})
    user_provider.set_user(
        staff_user("u-admin", permissions={"can_manage_staff": True, "can_view_all": True})
    )
    assert client.get(
        "/api/v3/reporting/audit-activity?organization_id=org-a"
    ).status_code == 200


def test_audit_activity_pe_staff_denied(client, world, user_provider):
    """Processing Entity staff must never gain customer-organisation audit access."""
    _seed_staff(world, "u-entity-op", {"can_view_all": True}, entity_id="ent-a")
    user_provider.set_user(entity_operator_user("ent-a"))
    assert client.get(
        "/api/v3/reporting/audit-activity?organization_id=org-a"
    ).status_code == 403


def test_audit_activity_anonymous_denied(client, world, user_provider):
    user_provider.set_unauthenticated()
    assert client.get(
        "/api/v3/reporting/audit-activity?organization_id=org-a"
    ).status_code == 401


# ---------------------------------------------------------------------------
# Audit readiness
# ---------------------------------------------------------------------------


def test_audit_readiness_never_assurance(client, world, user_provider):
    world.reporting.audit_readiness_result = {
        "label": "AUDIT EVIDENCE READINESS",
        "status": "gaps_to_review",
        "not_assurance": True,
        "evidence_coverage_pct": 50.0,
        "components": {"calculations_total": 4},
        "gaps": ["1 calculation(s) have no source-item lineage (evidence chain unavailable)."],
    }
    user_provider.set_user(org_admin_user("org-a", "u-a", "a@example.test"))
    resp = client.get("/api/v3/reporting/audit-readiness?organization_id=org-a")
    assert resp.status_code == 200
    body = resp.json()
    assert body["not_assurance"] is True
    assert body["label"] == "AUDIT EVIDENCE READINESS"
    assert "assured" not in body["label"].lower()


def test_audit_readiness_member_denied(client, world, user_provider):
    user_provider.set_user(member_user("org-a", "u-m", "m@example.test"))
    assert client.get(
        "/api/v3/reporting/audit-readiness?organization_id=org-a"
    ).status_code == 403


# ---------------------------------------------------------------------------
# Evidence package
# ---------------------------------------------------------------------------


def test_audit_package_owner_allowed_and_hashed(client, world, user_provider):
    world.reporting.audit_package_result = {
        "package": {
            "document_type": "carbontally_audit_evidence_package",
            "not_assurance": True,
        },
        "integrity": {"algorithm": "sha256", "package_hash": "abc123"},
    }
    user_provider.set_user(org_owner_user("org-a", "u-o", "o@example.test"))
    resp = client.get("/api/v3/exports/audit-package.json?organization_id=org-a")
    assert resp.status_code == 200
    body = resp.json()
    assert body["integrity"]["package_hash"] == "abc123"
    assert body["package"]["not_assurance"] is True


def test_audit_package_member_denied(client, world, user_provider):
    user_provider.set_user(member_user("org-a", "u-m", "m@example.test"))
    assert client.get(
        "/api/v3/exports/audit-package.json?organization_id=org-a"
    ).status_code == 403


def test_audit_package_pe_staff_denied(client, world, user_provider):
    _seed_staff(world, "u-entity-op", {"can_view_all": True}, entity_id="ent-a")
    user_provider.set_user(entity_operator_user("ent-a"))
    assert client.get(
        "/api/v3/exports/audit-package.json?organization_id=org-a"
    ).status_code == 403


# ---------------------------------------------------------------------------
# Ops audit console — taxonomy investigation filters
# ---------------------------------------------------------------------------


def _staff_admin(world, user_provider):
    _seed_staff(world, "u-admin", {"can_manage_staff": True, "can_view_all": True})
    user_provider.set_user(
        staff_user("u-admin", permissions={"can_manage_staff": True, "can_view_all": True})
    )


def test_ops_audit_category_filter(client, world, user_provider):
    _seed_audit(
        world,
        [
            _entry(1, action="session:login", category=CAT_AUTH, origin=ORIGIN_SYSTEM),
            _entry(2, action="calculation:completed", category=CAT_CALCULATION),
            _entry(3, action="logout", category=CAT_AUTH),
        ],
    )
    _staff_admin(world, user_provider)
    resp = client.get("/api/v3/ops/reporting/audit?category=authentication")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert all(e["category"] == "authentication" for e in body["entries"])


def test_ops_audit_origin_filter(client, world, user_provider):
    _seed_audit(
        world,
        [
            _entry(1, action="calculation:completed", category=CAT_CALCULATION,
                   origin=ORIGIN_SYSTEM, actor="system"),
            _entry(2, action="calculation:completed", category=CAT_CALCULATION,
                   origin="human", actor="u-9"),
        ],
    )
    _staff_admin(world, user_provider)
    resp = client.get("/api/v3/ops/reporting/audit?origin=system")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["entries"][0]["origin"] == "system"


def test_ops_audit_invalid_category_is_422(client, world, user_provider):
    _staff_admin(world, user_provider)
    resp = client.get("/api/v3/ops/reporting/audit?category=not-a-real-category")
    assert resp.status_code == 422


def test_ops_audit_invalid_timestamp_is_422(client, world, user_provider):
    _staff_admin(world, user_provider)
    resp = client.get("/api/v3/ops/reporting/audit?since=nonsense")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Entity-scoped activity — scope enforcement
# ---------------------------------------------------------------------------


def test_entity_audit_internal_staff_allowed(client, world, user_provider):
    _seed_staff(world, "u-admin", {"can_manage_staff": True, "can_view_all": True})
    user_provider.set_user(
        staff_user("u-admin", permissions={"can_manage_staff": True, "can_view_all": True})
    )
    resp = client.get("/api/v3/ops/entities/ent-a/audit-activity")
    assert resp.status_code == 200


def test_entity_audit_foreign_entity_denied(client, world, user_provider):
    _seed_staff(world, "u-entity-op", {"can_view_all": True}, entity_id="ent-a")
    user_provider.set_user(entity_operator_user("ent-a"))
    resp = client.get("/api/v3/ops/entities/ent-b/audit-activity")
    assert resp.status_code == 403

