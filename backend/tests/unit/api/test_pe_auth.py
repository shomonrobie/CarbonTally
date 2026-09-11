"""Unit tests for the Processing Entity authorization model (Phase 3 / PE-ROLE-001).

The stored staff-role vocabulary is the LEGACY representation that must remain
compatible; this module's mapping moves the canonical model toward the frozen
PE role vocabulary (Data Entry Operator / Reviewer / QC Specialist / Admin)
without any database migration.
"""
from __future__ import annotations

from api.pe_auth import (
    CAP_COMMUNICATE,
    CAP_MANAGE_TEAM,
    CAP_PROCESS,
    CAP_QC,
    CAP_READ_WORK,
    CAP_REVIEW,
    PE_FROZEN_ROLE_LABELS,
    PE_ROLE_CAPABILITIES,
    PEContext,
)


def test_frozen_role_labels_for_all_legacy_keys() -> None:
    # Every legacy PE staff role key maps to a frozen PE-ROLE-001 label.
    assert PE_FROZEN_ROLE_LABELS["operator"] == "Data Entry Operator"
    assert PE_FROZEN_ROLE_LABELS["reviewer"] == "Reviewer"
    assert PE_FROZEN_ROLE_LABELS["qc_specialist"] == "QC Specialist"
    assert PE_FROZEN_ROLE_LABELS["pe_manager"] == "Admin"


def test_role_separation_capabilities() -> None:
    # PE-ROLE-001: PE roles never grant Customer/Consultant/Ops/Admin domains.
    for caps in PE_ROLE_CAPABILITIES.values():
        assert not (caps & {"customer_admin", "ops_admin", "system_admin"})
        assert CAP_READ_WORK in caps
    # Data Entry Operator can process but cannot manage the team.
    assert CAP_PROCESS in PE_ROLE_CAPABILITIES["operator"]
    assert CAP_MANAGE_TEAM not in PE_ROLE_CAPABILITIES["operator"]
    assert CAP_REVIEW not in PE_ROLE_CAPABILITIES["operator"]
    assert CAP_QC not in PE_ROLE_CAPABILITIES["operator"]
    # Reviewer can review but cannot process or manage the team.
    assert CAP_REVIEW in PE_ROLE_CAPABILITIES["reviewer"]
    assert CAP_PROCESS not in PE_ROLE_CAPABILITIES["reviewer"]
    # QC Specialist can QC but cannot process/manage the team.
    assert CAP_QC in PE_ROLE_CAPABILITIES["qc_specialist"]
    assert CAP_MANAGE_TEAM not in PE_ROLE_CAPABILITIES["qc_specialist"]
    # Admin (pe_manager) may process/review/qc/manage the team but is still a
    # PE-domain capability set — never CarbonTally Admin.
    assert CAP_MANAGE_TEAM in PE_ROLE_CAPABILITIES["pe_manager"]
    assert CAP_PROCESS in PE_ROLE_CAPABILITIES["pe_manager"]
    assert "system_admin" not in PE_ROLE_CAPABILITIES["pe_manager"]


def test_context_can_uses_frozen_capabilities() -> None:
    ctx = PEContext(
        entity_id="pe-1",
        entity={"id": "pe-1", "name": "PE", "status": "active"},
        staff=None,  # type: ignore[arg-type]  # not needed for capability checks
        role_key="operator",
        role_label="Data Entry Operator",
        capabilities=PE_ROLE_CAPABILITIES["operator"],
    )
    assert ctx.can(CAP_READ_WORK)
    assert ctx.can(CAP_PROCESS)
    assert ctx.can(CAP_COMMUNICATE)
    assert not ctx.can(CAP_REVIEW)
    assert not ctx.can(CAP_QC)
    assert not ctx.can(CAP_MANAGE_TEAM)


def test_admin_context_review_and_qc() -> None:
    ctx = PEContext(
        entity_id="pe-1",
        entity={"id": "pe-1", "name": "PE", "status": "active"},
        staff=None,  # type: ignore[arg-type]
        role_key="pe_manager",
        role_label="Admin",
        capabilities=PE_ROLE_CAPABILITIES["pe_manager"],
    )
    assert ctx.can(CAP_REVIEW)
    assert ctx.can(CAP_QC)
    assert ctx.can(CAP_MANAGE_TEAM)
