"""V1.2 processing-origin + CarbonTally QC separation tests (CT-QC-001..005).

Covers the pure processing-origin model and the authorization invariants that
keep CarbonTally QC an internal CarbonTally control (never a PE capability).
"""
from __future__ import annotations

from auth import ADMIN_ROLE_NAMES
from domain.processing_origin import (
    ORIGIN_CARBONTALLY_INTERNAL,
    ORIGIN_PROCESSING_ENTITY,
    processing_origin_for_batch,
    processing_origin_label,
)
from api.pe_auth import PE_ROLE_CAPABILITIES


def test_batch_origin_internal_when_no_entity() -> None:
    assert (
        processing_origin_for_batch(None) == ORIGIN_CARBONTALLY_INTERNAL
    )


def test_batch_origin_processing_entity_when_assigned() -> None:
    assert (
        processing_origin_for_batch("pe-1") == ORIGIN_PROCESSING_ENTITY
    )


def test_origin_labels_human_readable() -> None:
    assert processing_origin_label(ORIGIN_CARBONTALLY_INTERNAL) == (
        "CarbonTally internal processing"
    )
    assert processing_origin_label(ORIGIN_PROCESSING_ENTITY) == (
        "Processing Entity processing"
    )
    assert processing_origin_label("unknown") == "unknown"


def test_pe_qc_capability_never_grants_carbontally_admin() -> None:
    # CT-QC-003/§7 — a PE QC Specialist's "qc" capability is a PE-domain
    # capability. It must never appear in CarbonTally's internal admin role
    # vocabulary (the gate for the /api/v3/qc CarbonTally QC surface).
    assert "qc" not in ADMIN_ROLE_NAMES
    for role_key, caps in PE_ROLE_CAPABILITIES.items():
        assert not (caps & {"admin", "system_admin"})
        assert not (caps & {"can_review", "can_process"})


def test_all_pe_roles_keep_qc_outside_ops_permission_namespace() -> None:
    # ops (CarbonTally internal) gates use staff permissions like
    # can_review/can_process; PE capability names must not overlap them.
    pe_caps = {c for caps in PE_ROLE_CAPABILITIES.values() for c in caps}
    assert not (pe_caps & {"can_review", "can_process", "can_manage_team"})
