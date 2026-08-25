"""D30 — reporting endpoint + metric tests.

Covers:
- pure metric helpers (stage distribution, completion ratio)
- customer dashboard composition + organisation isolation
- consultant portfolio (ACTIVE grants only; ended counted not detailed)
- internal staff permission gates (platform / review / QC)
- processing-entity isolation (own entity only)
"""
from __future__ import annotations

import pytest

from data.reporting import STAGE_BY_STATUS, completed_ratio, stage_distribution
from tests.unit.api.fakes import (
    consultant_user,
    entity_operator_user,
    member_user,
    staff_user,
)


def _row(status: str):
    return {"status": status}


# ---------------------------------------------------------------------------
# Pure metric helpers
# ---------------------------------------------------------------------------


def test_stage_distribution_buckets_statuses():
    rows = [
        _row("pending"),          # source
        _row("extracting"),       # extraction
        _row("extracted"),        # extraction
        _row("mapping"),          # mapping
        _row("mapped"),           # mapping
        _row("validating"),       # validation
        _row("validated"),        # validation
        _row("calculating"),      # calculation
        _row("calculated"),       # calculation
        _row("customer_review"),  # review
        _row("approved"),         # approval
        _row("qc_approved"),      # qc
    ]
    counts = stage_distribution(rows)
    assert counts["source"] == 1
    assert counts["extraction"] == 2
    assert counts["mapping"] == 2
    assert counts["validation"] == 2
    assert counts["calculation"] == 2
    assert counts["review"] == 1
    assert counts["approval"] == 1
    assert counts["qc"] == 1
    assert sum(counts.values()) == 12


def test_stage_distribution_unknown_status_defaults_to_source():
    counts = stage_distribution([_row("mystery_status")])
    assert counts["source"] == 1
    assert counts["extraction"] == 0


def test_completed_ratio_uses_approval_and_qc():
    counts = {"source": 1, "extraction": 1, "mapping": 1, "approval": 1, "qc": 1}
    assert completed_ratio(counts) == 40.0
    assert completed_ratio({"source": 2}) == 0.0
    assert completed_ratio({}) == 0.0


def test_every_known_stage_status_is_mapped():
    for status in ("pending", "extracting", "extracted", "mapping", "mapped",
                   "validating", "validated", "calculating", "calculated",
                   "customer_review", "approved", "rejected",
                   "qc_approved", "qc_rejected"):
        assert status in STAGE_BY_STATUS


# ---------------------------------------------------------------------------
# Customer dashboard (org-scoped)
# ---------------------------------------------------------------------------


def _seed_staff(world, user_id, permissions, entity_id=None):
    from domain.staff import StaffProfile, StaffRole

    world.staff.seed_role(
        StaffRole(id="role-x", name="x", permissions=permissions)
    )
    world.staff.seed_profile(
        StaffProfile(
            id=f"sp-{user_id}",
            user_id=user_id,
            first_name="A",
            last_name="B",
            email=f"{user_id}@carbontally.test",
            role_id="role-x",
            entity_id=entity_id,
            is_active=True,
        )
    )


def test_customer_dashboard_composes_aggregates(client, world, user_provider):
    world.reporting.emissions_summary_result = {
        "total_kg": 183.0, "row_count": 1,
        "by_scope": [{"scope": "Scope 1", "kg": 183.0, "rows": 1}],
        "by_month": [{"month": "2025-06", "kg": 183.0, "rows": 1}],
    }
    world.reporting.document_summary_result = {
        "total_documents": 4, "processing_by_status": {"completed": 2, "pending": 2},
        "processed": 2, "pending": 2, "requiring_attention": 1,
    }
    world.reporting.processing_summary_result = {
        "batches": {"total": 2, "by_status": {"open": 2}},
        "items": {"total": 4, "by_stage": {"source": 1, "approval": 3},
                  "mapped": 3, "unmapped": 1, "complete_pct": 75.0},
    }
    world.reporting.issues_summary_result = {"by_status": {"open": 1}, "open": 1, "sla_breached_open": 0}
    world.reporting.report_summary_result = {"completed": 1, "pending": 1}

    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.get("/api/v3/reporting/customer-dashboard?organization_id=org-a")
    assert resp.status_code == 200
    data = resp.json()
    assert data["emissions"]["total_kg"] == 183.0
    assert data["documents"]["processed"] == 2
    assert data["processing"]["items"]["complete_pct"] == 75.0
    assert data["reports"]["ready"] == 1
    assert data["attention"]["open_issues"] == 1
    assert data["attention"]["documents_requiring_attention"] == 1
    assert data["attention"]["unmapped_items"] == 1


def test_customer_dashboard_denies_other_organization(client, world, user_provider):
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.get("/api/v3/reporting/customer-dashboard?organization_id=org-b")
    assert resp.status_code == 403


def test_customer_dashboard_denies_entity_staff(client, world, user_provider):
    _seed_staff(world, "u-ent", {"can_process": True}, entity_id="ent-x")
    user_provider.set_user(staff_user("u-ent", permissions={"can_process": True}, entity_id="ent-x"))
    resp = client.get("/api/v3/reporting/customer-dashboard?organization_id=org-a")
    assert resp.status_code == 403


def test_customer_dashboard_requires_authentication(client, user_provider):
    user_provider.set_unauthenticated()
    resp = client.get("/api/v3/reporting/customer-dashboard?organization_id=org-a")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Consultant portfolio (active grants only)
# ---------------------------------------------------------------------------


def test_consultant_portfolio_excludes_ended_clients_from_detail(client, world, user_provider):
    world.consultants.seed_profile("firm-1", "u-cons", "Acme Consultants")
    world.consultants.seed_firm_member("firm-1", "u-cons", role="manager")
    world.consultants.seed_client("client-a", "firm-1", "org-a", "ACME LTD", status="active")
    world.consultants.seed_client("client-b", "firm-1", "org-b", "Old Client", status="ended")
    world.reporting.portfolio_result = [
        {"client_id": "client-a", "organization_id": "org-a", "client_name": "ACME LTD",
         "client_industry": "Retail", "status": "active", "documents": 4, "items": 3,
         "open_issues": 1, "ready_reports": 2},
        {"client_id": "client-b", "organization_id": "org-b", "client_name": "Old Client",
         "client_industry": None, "status": "ended", "documents": 0, "items": 0,
         "open_issues": 0, "ready_reports": 0},
    ]
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    resp = client.get("/api/v3/reporting/consultant-portfolio")
    assert resp.status_code == 200
    data = resp.json()
    # Ended relationship counted but never detailed (D15).
    assert data["portfolio"]["active"] == 1
    assert data["portfolio"]["ended"] == 1
    assert len(data["clients"]) == 1
    assert data["clients"][0]["client_name"] == "ACME LTD"


def test_consultant_portfolio_requires_consultant(client, world, user_provider):
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.get("/api/v3/reporting/consultant-portfolio")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Internal operations / review / QC reporting (staff permission gates)
# ---------------------------------------------------------------------------


def test_platform_reporting_allows_internal_staff_with_can_view_all(client, world, user_provider):
    _seed_staff(world, "u-op", {"can_view_all": True, "can_process": True})
    world.reporting.platform_result = {"platform": {"organizations": 2}}
    user_provider.set_user(staff_user("u-op", permissions={"can_view_all": True, "can_process": True}))
    resp = client.get("/api/v3/ops/reporting/platform")
    assert resp.status_code == 200
    assert resp.json()["platform"]["organizations"] == 2


def test_platform_reporting_denies_entity_staff(client, world, user_provider):
    _seed_staff(world, "u-ent", {"can_view_all": True}, entity_id="ent-x")
    user_provider.set_user(staff_user("u-ent", permissions={"can_view_all": True}, entity_id="ent-x"))
    resp = client.get("/api/v3/ops/reporting/platform")
    assert resp.status_code == 403


def test_review_reporting_requires_can_review(client, world, user_provider):
    _seed_staff(world, "u-rev", {"can_review": True})
    user_provider.set_user(staff_user("u-rev", permissions={"can_review": True}))
    resp = client.get("/api/v3/ops/reporting/review")
    assert resp.status_code == 200

    # operator without can_review is denied
    _seed_staff(world, "u-op", {"can_process": True})
    user_provider.set_user(staff_user("u-op", permissions={"can_process": True}))
    assert client.get("/api/v3/ops/reporting/review").status_code == 403


def test_qc_reporting_requires_can_review(client, world, user_provider):
    _seed_staff(world, "u-qc", {"can_review": True})
    user_provider.set_user(staff_user("u-qc", permissions={"can_review": True}))
    resp = client.get("/api/v3/ops/reporting/qc")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Processing Entity performance (own entity only)
# ---------------------------------------------------------------------------


def test_entity_performance_own_entity_allowed(client, world, user_provider):
    _seed_staff(world, "u-ent", {"can_process": True}, entity_id="ent-x")
    world.reporting.entity_performance_result = {"items": {"total": 3}}
    user_provider.set_user(entity_operator_user("ent-x", "u-ent"))
    resp = client.get("/api/v3/ops/entities/ent-x/performance")
    assert resp.status_code == 200
    assert resp.json()["items"]["total"] == 3


def test_entity_performance_other_entity_denied(client, world, user_provider):
    _seed_staff(world, "u-ent", {"can_process": True}, entity_id="ent-x")
    user_provider.set_user(entity_operator_user("ent-x", "u-ent"))
    resp = client.get("/api/v3/ops/entities/ent-y/performance")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# D31 — customer trend + member activity
# ---------------------------------------------------------------------------


def test_emissions_trend_returns_zero_filled_months(client, world, user_provider):
    world.reporting.emissions_trend_result = {
        "organization_id": "org-a",
        "months": [{"month": "2025-08", "kg": 0.0, "rows": 0},
                   {"month": "2025-09", "kg": 183.0, "rows": 1}],
    }
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.get("/api/v3/reporting/emissions-trend?organization_id=org-a&months=12")
    assert resp.status_code == 200
    assert resp.json()["months"][1]["kg"] == 183.0


def test_emissions_trend_denies_cross_org(client, world, user_provider):
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    assert client.get("/api/v3/reporting/emissions-trend?organization_id=org-b").status_code == 403


def test_emissions_trend_denies_entity_staff(client, world, user_provider):
    _seed_staff(world, "u-ent", {"can_process": True}, entity_id="ent-x")
    user_provider.set_user(staff_user("u-ent", permissions={"can_process": True}, entity_id="ent-x"))
    assert client.get("/api/v3/reporting/emissions-trend?organization_id=org-a").status_code == 403


def test_member_activity_returns_members(client, world, user_provider):
    world.reporting.member_activity_result = [
        {"user_id": "u-a", "name": "A Member", "documents_uploaded": 2,
         "issues_created": 1, "issues_resolved": 0, "extraction_batches": 1, "emissions_rows": 0},
    ]
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.get("/api/v3/reporting/member-activity?organization_id=org-a")
    assert resp.status_code == 200
    assert resp.json()["members"][0]["name"] == "A Member"


def test_member_activity_denies_cross_org(client, world, user_provider):
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    assert client.get("/api/v3/reporting/member-activity?organization_id=org-b").status_code == 403


# ---------------------------------------------------------------------------
# D31 — consultant client drill-down (ACTIVE grants only)
# ---------------------------------------------------------------------------


def _seed_consultant(world, user_id="u-cons"):
    world.consultants.seed_profile("firm-1", user_id, "Acme Consultants")
    world.consultants.seed_firm_member("firm-1", user_id, role="manager")
    world.consultants.seed_client("client-a", "firm-1", "org-a", "ACME LTD", status="active")
    world.consultants.seed_client("client-b", "firm-1", "org-b", "Old Client", status="ended")
    return consultant_user(user_id, "cons@example.test")


def test_consultant_client_detail_own_active_client(client, world, user_provider):
    _seed_consultant(world)
    world.reporting.consultant_client_detail_result = {
        "client_id": "client-a", "organization_id": "org-a", "client_name": "ACME LTD",
        "client_industry": "Retail", "status": "active", "documents": 4,
        "items": {"total": 3, "completed": 1, "by_stage": {"mapping": 3}},
        "issues": {"total": 2, "open": 1},
        "reports": {"ready": 1},
        "emissions": {"total_kg": 100.0, "rows": 1, "by_scope": []},
    }
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    resp = client.get("/api/v3/reporting/consultant-client/client-a")
    assert resp.status_code == 200
    assert resp.json()["client_name"] == "ACME LTD"
    assert resp.json()["items"]["by_stage"]["mapping"] == 3


def test_consultant_client_detail_unknown_client_404(client, world, user_provider):
    _seed_consultant(world)
    world.reporting.consultant_client_detail_result = None
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    assert client.get("/api/v3/reporting/consultant-client/client-zzz").status_code == 404


def test_consultant_client_detail_ended_client_403(client, world, user_provider):
    _seed_consultant(world)
    world.reporting.consultant_client_detail_result = {
        "client_id": "client-b", "organization_id": "org-b", "client_name": "Old Client",
        "client_industry": None, "status": "ended", "documents": 0,
        "items": {"total": 0, "completed": 0, "by_stage": {}},
        "issues": {"total": 0, "open": 0},
        "reports": {"ready": 0},
        "emissions": {"total_kg": 0.0, "rows": 0, "by_scope": []},
    }
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    assert client.get("/api/v3/reporting/consultant-client/client-b").status_code == 403


def test_consultant_client_detail_requires_consultant(client, world, user_provider):
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    assert client.get("/api/v3/reporting/consultant-client/client-a").status_code == 403


# ---------------------------------------------------------------------------
# D31 — ops queue aging + admin audit
# ---------------------------------------------------------------------------


def test_queue_aging_allows_internal_staff(client, world, user_provider):
    _seed_staff(world, "u-op", {"can_view_all": True, "can_process": True})
    world.reporting.queue_aging_result = {
        "batches": {"total": 3, "open": 2, "aging": {"0-1d": 2}},
        "items": {"total": 4, "aging": {"3-7d": 1}, "internal": 3, "entity": 1},
    }
    user_provider.set_user(staff_user("u-op", permissions={"can_view_all": True, "can_process": True}))
    resp = client.get("/api/v3/ops/reporting/aging")
    assert resp.status_code == 200
    assert resp.json()["batches"]["open"] == 2


def test_queue_aging_denies_entity_staff(client, world, user_provider):
    _seed_staff(world, "u-ent", {"can_view_all": True}, entity_id="ent-x")
    user_provider.set_user(staff_user("u-ent", permissions={"can_view_all": True}, entity_id="ent-x"))
    assert client.get("/api/v3/ops/reporting/aging").status_code == 403


def test_queue_aging_requires_can_view_all(client, world, user_provider):
    _seed_staff(world, "u-min", {"can_process": True})
    user_provider.set_user(staff_user("u-min", permissions={"can_process": True}))
    assert client.get("/api/v3/ops/reporting/aging").status_code == 403


def test_audit_reporting_admin_only(client, world, user_provider):
    _seed_staff(world, "u-admin", {"can_manage_staff": True, "can_view_all": True})
    user_provider.set_user(staff_user("u-admin", permissions={"can_manage_staff": True, "can_view_all": True}))
    resp = client.get("/api/v3/ops/reporting/audit?limit=50")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    # operator without can_manage_staff is denied
    _seed_staff(world, "u-op", {"can_process": True, "can_view_all": True})
    user_provider.set_user(staff_user("u-op", permissions={"can_process": True, "can_view_all": True}))
    assert client.get("/api/v3/ops/reporting/audit").status_code == 403


def test_audit_reporting_denies_entity_staff(client, world, user_provider):
    _seed_staff(world, "u-ent", {"can_manage_staff": True}, entity_id="ent-x")
    user_provider.set_user(staff_user("u-ent", permissions={"can_manage_staff": True}, entity_id="ent-x"))
    assert client.get("/api/v3/ops/reporting/audit").status_code == 403


# ---------------------------------------------------------------------------
# D31 — extended review / QC / entity payloads
# ---------------------------------------------------------------------------


def test_review_reporting_includes_workload_and_issues(client, world, user_provider):
    _seed_staff(world, "u-rev", {"can_review": True})
    world.reporting.review_result = {
        "by_status": {"pending": 1},
        "aging": {"0-3d": 1},
        "sla_breached": 0,
        "workload": [{"name": "Rev One", "reviewer_id": "sp-u-rev", "assigned": 1,
                      "completed": 0, "pending": 1, "overdue": 0}],
        "issues": {"by_type": {"exception": 4}, "by_status": {"open": 4}, "by_month": [], "blocking": None},
    }
    user_provider.set_user(staff_user("u-rev", permissions={"can_review": True}))
    resp = client.get("/api/v3/ops/reporting/review")
    assert resp.status_code == 200
    assert resp.json()["workload"][0]["name"] == "Rev One"
    assert resp.json()["issues"]["by_type"]["exception"] == 4


def test_qc_reporting_includes_processor_performance(client, world, user_provider):
    _seed_staff(world, "u-qc", {"can_review": True})
    world.reporting.qc_result = {
        "outcomes": {"qc_approved": 2},
        "by_scope": [],
        "avg_quality_score": 95.0,
        "quality_scored_items": 2,
        "processor_performance": [
            {"scope": "internal", "completed": 2, "rejected": 0, "avg_quality": 95.0,
             "scored": 2, "sample_size": 2, "rejection_rate_pct": 0.0},
        ],
        "recurring_quality": {"supported": False, "source": "qc_errors", "note": "not populated"},
    }
    user_provider.set_user(staff_user("u-qc", permissions={"can_review": True}))
    resp = client.get("/api/v3/ops/reporting/qc")
    assert resp.status_code == 200
    assert resp.json()["processor_performance"][0]["sample_size"] == 2
    assert resp.json()["recurring_quality"]["supported"] is False


def test_entity_performance_includes_sla_and_quality(client, world, user_provider):
    _seed_staff(world, "u-ent", {"can_process": True}, entity_id="ent-x")
    world.reporting.entity_performance_result = {
        "batches": {"total": 2, "by_status": {"open": 2}, "sla_breached": 1, "overdue": 1},
        "items": {"total": 3, "by_stage": {"source": 3}, "complete_pct": 0.0},
        "quality": {"completed": 2, "rejected": 1, "rejection_rate_pct": 50.0,
                    "avg_quality": 88.0, "scored": 2, "sample_size": 2},
        "staff": [],
    }
    user_provider.set_user(entity_operator_user("ent-x", "u-ent"))
    resp = client.get("/api/v3/ops/entities/ent-x/performance")
    assert resp.status_code == 200
    assert resp.json()["batches"]["sla_breached"] == 1
    assert resp.json()["quality"]["rejection_rate_pct"] == 50.0

