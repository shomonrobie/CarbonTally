"""V1.2 dual-origin workflow transition tests (CT-QC-001..005).

Pure tests over the canonical work-item state machine
(domain.partners.ITEM_STATUS_FLOW): internal work never enters PE stages, PE
work must pass PE Review → PE QC → CarbonTally QC, CarbonTally QC is required
before customer approval on the canonical paths, and historical early-QC
statuses keep their original meaning.
"""
from __future__ import annotations

from domain.partners import (
    ITEM_STATUS_FLOW,
    WORKFLOW_STAGE_STATUSES,
    can_transition_item_status,
)


def test_internal_path_skips_pe_stages() -> None:
    # calculated → review (internal) → reviewed → ct_qc → ct_qc_approved →
    # customer_review (no PE stage in the chain).
    assert can_transition_item_status("calculated", "reviewed")
    assert can_transition_item_status("reviewed", "ct_qc")
    assert can_transition_item_status("ct_qc", "ct_qc_approved")
    assert can_transition_item_status("ct_qc_approved", "customer_review")
    # Internal work must never be forced into PE stages.
    assert can_transition_item_status("calculated", "reviewed")
    assert not can_transition_item_status("reviewed", "pe_review")
    assert not can_transition_item_status("ct_qc_approved", "pe_qc")


def test_pe_path_reaches_carbontally_qc() -> None:
    # calculated → pe_review → pe_reviewed → pe_qc → pe_qc_approved → ct_qc.
    assert can_transition_item_status("calculated", "pe_review")
    assert can_transition_item_status("pe_review", "pe_reviewed")
    assert can_transition_item_status("pe_reviewed", "pe_qc")
    assert can_transition_item_status("pe_qc", "pe_qc_approved")
    assert can_transition_item_status("pe_qc_approved", "ct_qc")
    # PE Review cannot jump straight to customer approval.
    assert not can_transition_item_status("pe_reviewed", "customer_review")
    assert not can_transition_item_status("pe_qc_approved", "customer_review")


def test_customer_approval_requires_ct_qc_gate_on_canonical_path() -> None:
    # On the canonical internal path the only route into customer_review after
    # calculated is through ct_qc_approved (or the legacy direct transition).
    assert can_transition_item_status("ct_qc_approved", "customer_review")
    # V1.2 — CT QC approval releases the item to the customer decision surface:
    # customers approve/reject from ct_qc_approved (guard is server-side).
    assert can_transition_item_status("ct_qc_approved", "approved")
    assert can_transition_item_status("ct_qc_approved", "rejected")
    # PE work cannot bypass: pe_reviewed / pe_qc_approved have no direct path.
    assert "customer_review" not in ITEM_STATUS_FLOW["pe_reviewed"]
    assert "customer_review" not in ITEM_STATUS_FLOW["pe_qc_approved"]
    assert "customer_review" not in ITEM_STATUS_FLOW["pe_qc"]
    # ... and cannot jump straight to a customer decision either.
    assert "approved" not in ITEM_STATUS_FLOW["pe_qc_approved"]
    assert "rejected" not in ITEM_STATUS_FLOW["pe_qc_approved"]


def test_rejection_rework_loops_preserved() -> None:
    assert can_transition_item_status("pe_review", "pe_review_rejected")
    assert can_transition_item_status("pe_review_rejected", "mapping")
    assert can_transition_item_status("pe_qc", "pe_qc_rejected")
    assert can_transition_item_status("pe_qc_rejected", "extracting")
    assert can_transition_item_status("ct_qc", "ct_qc_rejected")
    assert can_transition_item_status("ct_qc_rejected", "mapping")
    assert can_transition_item_status("customer_review", "rejected")
    assert can_transition_item_status("rejected", "mapping")


def test_historical_early_qc_statuses_retain_meaning() -> None:
    # Legacy early extraction-QC markers remain valid and lead to mapping, and
    # are NOT silently reinterpreted as CarbonTally QC (ct_qc) statuses.
    assert can_transition_item_status("extracted", "qc_approved")
    assert can_transition_item_status("qc_approved", "mapping")
    assert can_transition_item_status("qc_rejected", "extracting")
    assert "qc_approved" in WORKFLOW_STAGE_STATUSES["qc"]
    assert "ct_qc" not in ITEM_STATUS_FLOW["qc_approved"]
