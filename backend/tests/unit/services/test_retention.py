"""N3 — configurable retention: policy normalisation + enforcement safety tests.

Verifies that no duration is invented, unset values are never enforced, and
audit/evidence tables are excluded from the eligible domain set.
"""
from __future__ import annotations

from services.retention import (
    _ELIGIBLE_DOMAINS,
    build_policy,
    enforce_retention,
    telemetry_excluded_tables,
)


def test_build_policy_keeps_configured_days_only() -> None:
    policy = build_policy({"document_retention_days": 730, "audit_log_retention_days": None})
    assert policy["document_retention_days"] == 730
    # audit domain is not eligible for enforcement at all.
    assert "audit_log_retention_days" not in policy


def test_build_policy_never_invents_values() -> None:
    assert build_policy({})["document_retention_days"] is None
    assert build_policy({"document_retention_days": None})["document_retention_days"] is None
    # negative values are treated as unconfigured (never enforced).
    assert build_policy({"document_retention_days": -30})["document_retention_days"] is None


def test_audit_and_evidence_domains_are_excluded_from_enforcement() -> None:
    # Security invariant: auditability and the immutable evidence model must not
    # be weakened by retention.
    #
    # Step 2 closure / POD-6 — corrected stale expectation: the eligible set is
    # documents **plus** the Phase 8-X X2 telemetry domain (PO decision `PX-7`),
    # which the implementation already carries. The invariant this test exists to
    # protect is unchanged: no audit/evidence/backup domain is ever eligible, and
    # the telemetry rule may never purge a business/evidence/audit table.
    assert set(_ELIGIBLE_DOMAINS) == {
        "document_retention_days",
        "operational_telemetry_retention_days",
    }
    for excluded_domain in (
        "audit_log_retention_days",
        "data_retention_days",
        "backup_retention_days",
    ):
        assert excluded_domain not in _ELIGIBLE_DOMAINS
    for excluded_table in (
        "audit_trail",
        "evidence_line_items",
        "calculation_snapshots",
        "report_versions",
    ):
        assert excluded_table in telemetry_excluded_tables()


async def test_enforce_retention_dry_run_default() -> None:
    class _Repos:
        class _Files:
            async def expire_documents_older_than(self, cutoff, *, dry_run=True):
                return {"eligible": 3, "applied": 0}

        class _Settings:
            async def get_retention(self):
                return {"document_retention_days": 730, "audit_log_retention_days": None}

        files = _Files()
        settings = _Settings()

    report = await enforce_retention(_Repos(), dry_run=True)
    assert report["dry_run"] is True
    assert report["policy"]["document_retention_days"] == 730
    assert report["domains"]["document_retention_days"]["applied"] == 0
    assert report["domains"]["document_retention_days"]["eligible"] == 3
