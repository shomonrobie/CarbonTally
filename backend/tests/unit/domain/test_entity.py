"""Unit tests for the Processing Entity domain (V3 ADR-V3-001)."""

from __future__ import annotations

import pytest

from domain.entity import ENTITY_STATUSES, ProcessingEntity


class TestProcessingEntity:
    def test_valid_entity(self) -> None:
        entity = ProcessingEntity(id="pe-1", name="Babui Limited")
        assert entity.status == "active"
        assert entity.id == "pe-1"

    def test_rejects_empty_id(self) -> None:
        with pytest.raises(ValueError):
            ProcessingEntity(id="", name="Babui")

    def test_rejects_empty_name(self) -> None:
        with pytest.raises(ValueError):
            ProcessingEntity(id="pe-1", name="")

    def test_rejects_unknown_status(self) -> None:
        with pytest.raises(ValueError):
            ProcessingEntity(id="pe-1", name="Babui", status="bogus")

    def test_immutable(self) -> None:
        entity = ProcessingEntity(id="pe-1", name="Babui")
        with pytest.raises(AttributeError):
            entity.name = "Changed"  # type: ignore[misc]

    def test_lifecycle_transitions(self) -> None:
        entity = ProcessingEntity(id="pe-1", name="Babui")
        assert entity.can_transition_to("suspended")
        assert entity.can_transition_to("terminated")
        # terminated is terminal — no transitions out
        terminated = ProcessingEntity(id="pe-1", name="Babui", status="terminated")
        assert not terminated.can_transition_to("active")

    def test_statuses_vocabulary(self) -> None:
        assert set(ENTITY_STATUSES) == {
            "active", "remediation", "suspended", "terminated"
        }
