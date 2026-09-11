"""Phase 7 — canonical audit taxonomy + evidence-readiness tests (pure).

These are pure-Python unit tests: no database, no HTTP. They pin the
classifications the audit ledger and the readiness indicator rely on.
"""
from __future__ import annotations

import pytest

from data.reporting import (
    AUDIT_READINESS_LABEL,
    audit_readiness_from_counts,
)
from domain.audit import (
    ACTOR_SYSTEM,
    CAT_ADMIN,
    CAT_AUTH,
    CAT_CALCULATION,
    CAT_DOCUMENT,
    CAT_EVIDENCE,
    CAT_EXTRACTION,
    CAT_MAPPING,
    CAT_REPORT,
    CAT_SECURITY,
    CAT_SYSTEM,
    CAT_VALIDATION,
    CAT_WORKFLOW,
    ORIGIN_HUMAN,
    ORIGIN_SYSTEM,
    AuditQuery,
    classify_action,
    classify_origin,
)


# ---------------------------------------------------------------------------
# classify_action
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "action,expected",
    [
        # Generic documented lifecycle heads.
        ("session:login", CAT_AUTH),
        ("login:success", CAT_AUTH),
        ("logout", CAT_AUTH),
        ("access:denied", CAT_SECURITY),
        ("document:uploaded", CAT_DOCUMENT),
        ("extraction:completed", CAT_EXTRACTION),
        ("mapping:updated", CAT_MAPPING),
        ("validation:failed", CAT_VALIDATION),
        ("calculation:completed", CAT_CALCULATION),
        ("verify:snapshot", CAT_CALCULATION),
        ("evidence:inspected", CAT_EVIDENCE),
        ("review:completed", CAT_WORKFLOW),
        ("qc:approved", CAT_WORKFLOW),
        ("report:generated", CAT_REPORT),
        ("staff:role_changed", CAT_ADMIN),
        ("organization:created", CAT_ADMIN),
        # Real V3 action heads observed in backend/api/*.py.
        ("pe_calculate:applied", CAT_CALCULATION),
        ("ops_calculate:applied", CAT_CALCULATION),
        ("pe_validate:blocked", CAT_VALIDATION),
        ("ops_map:applied", CAT_MAPPING),
        ("pe_review:approved", CAT_WORKFLOW),
        ("pe_qc:approved", CAT_WORKFLOW),
        ("org_item_extraction:edited", CAT_EXTRACTION),
        ("processing_entity:created", CAT_ADMIN),
        ("factor_alias:created", CAT_MAPPING),
        ("whitelabel.domain.created", CAT_ADMIN),
        ("plan.created", CAT_ADMIN),
        ("discovery.requested", CAT_DOCUMENT),
        ("reassigned", CAT_WORKFLOW),
    ],
)
def test_classify_action_maps_known_heads(action, expected):
    assert classify_action(action) == expected


def test_classify_action_normalises_case_and_dashes():
    assert classify_action("Document-Uploaded") == CAT_DOCUMENT
    assert classify_action("  SESSION:LOGIN  ") == CAT_AUTH


def test_classify_action_unknown_is_system_not_guessed():
    assert classify_action("zzz:whatever") == CAT_SYSTEM
    assert classify_action("") == CAT_SYSTEM
    assert classify_action(None) == CAT_SYSTEM


def test_classify_action_handles_underscored_head():
    assert classify_action("manual_extraction:synced") == "extraction"


# ---------------------------------------------------------------------------
# classify_origin
# ---------------------------------------------------------------------------


def test_classify_origin_human_for_real_actor():
    assert classify_origin("11111111-1111-4111-8111-111111111111") == ORIGIN_HUMAN


def test_classify_origin_system_for_machine_labels():
    assert classify_origin("system") == ORIGIN_SYSTEM
    assert classify_origin("automatic_pipeline") == ORIGIN_SYSTEM
    assert classify_origin(None) == ORIGIN_SYSTEM
    assert classify_origin("x", ACTOR_SYSTEM) == ORIGIN_SYSTEM


def test_classify_origin_machine_zero_uuid_marker():
    assert classify_origin("00000000-0000-0000-0000-000000000000") == ORIGIN_SYSTEM


# ---------------------------------------------------------------------------
# AuditQuery validation
# ---------------------------------------------------------------------------


def test_audit_query_accepts_phase7_filters():
    q = AuditQuery(category=CAT_AUTH, origin=ORIGIN_SYSTEM, outcome="failure")
    assert q.category == CAT_AUTH
    assert q.origin == ORIGIN_SYSTEM
    assert q.outcome == "failure"
    assert q.organization_id is None


def test_audit_query_rejects_invalid_taxonomy_values():
    with pytest.raises(ValueError):
        AuditQuery(category="not-a-category")
    with pytest.raises(ValueError):
        AuditQuery(origin="sometimes")
    with pytest.raises(ValueError):
        AuditQuery(outcome="maybe")


# ---------------------------------------------------------------------------
# Evidence readiness (pure)
# ---------------------------------------------------------------------------


def test_readiness_is_labelled_and_never_assurance():
    result = audit_readiness_from_counts(
        calculations_total=10,
        calculations_with_source=10,
        evidence_complete=10,
        evidence_partial=0,
        evidence_unavailable=0,
        open_issues=0,
        awaiting_review=0,
        reports_ready=1,
        documents=3,
    )
    assert result["label"] == AUDIT_READINESS_LABEL
    assert result["label"] == "AUDIT EVIDENCE READINESS"
    assert result["not_assurance"] is True
    # Never claim verification/assurance words.
    text = (result["label"] + " " + result["notice"]).lower()
    assert "assured" not in text
    assert "certified" not in text
    assert result["status"] == "evidence_present"
    assert result["evidence_coverage_pct"] == 100.0
    assert result["gaps"] == []


def test_readiness_reports_gaps_honestly():
    result = audit_readiness_from_counts(
        calculations_total=4,
        calculations_with_source=2,
        evidence_complete=2,
        evidence_partial=1,
        evidence_unavailable=1,
        open_issues=2,
        awaiting_review=1,
        reports_ready=0,
        documents=1,
    )
    assert result["status"] == "gaps_to_review"
    assert result["evidence_coverage_pct"] == 50.0
    assert len(result["gaps"]) >= 3
    assert result["components"]["evidence_unavailable"] == 1


def test_readiness_no_evidence_yet():
    result = audit_readiness_from_counts(
        calculations_total=0,
        calculations_with_source=0,
        evidence_complete=0,
        evidence_partial=0,
        evidence_unavailable=0,
        open_issues=0,
        awaiting_review=0,
        reports_ready=0,
        documents=0,
    )
    assert result["status"] == "no_evidence_yet"
    assert result["evidence_coverage_pct"] == 0.0
