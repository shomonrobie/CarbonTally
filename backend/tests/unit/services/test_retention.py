"""N3 — configurable retention: policy normalisation + enforcement safety tests.

Verifies that no duration is invented, unset values are never enforced, and
audit/evidence tables are excluded from the eligible domain set.
"""
from __future__ import annotations

from services.retention import _ELIGIBLE_DOMAINS, build_policy, enforce_retention


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
    # be weakened by retention. Only documents are eligible today.
    assert set(_ELIGIBLE_DOMAINS) == {"document_retention_days"}


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
