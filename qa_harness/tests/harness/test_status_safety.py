"""Harness self-tests: run status vocabulary + read-only safety (spec §33, §36)."""

from __future__ import annotations

import pytest

from qa_harness.core.safety import (
    BLOCKED_SAFE_MUTATION_NOT_AVAILABLE,
    GuardMode,
    MutationNotAvailable,
    ReadOnlyGuard,
)
from qa_harness.core.status import (
    CheckResult,
    ModuleResult,
    RunStatus,
    ToolUnavailable,
)


def test_run_status_vocabulary() -> None:
    assert RunStatus.TOOL_UNAVAILABLE.value == "SKIPPED — TOOL UNAVAILABLE"
    assert RunStatus.MUTATION_NOT_AVAILABLE.value == "BLOCKED — SAFE MUTATION NOT AVAILABLE"
    assert BLOCKED_SAFE_MUTATION_NOT_AVAILABLE in RunStatus.MUTATION_NOT_AVAILABLE.value


def test_tool_unavailable() -> None:
    exc = ToolUnavailable("playwright", "pip install playwright")
    assert exc.tool == "playwright"
    assert "playwright" in str(exc)


def test_check_result_envelope() -> None:
    check = CheckResult(name="x", status=RunStatus.PASS)
    assert check.to_dict()["status"] == "PASS"


def test_module_result_mark_skipped() -> None:
    module = ModuleResult(module="db")
    module.mark_skipped("psycopg2")
    assert module.status == RunStatus.TOOL_UNAVAILABLE
    assert module.skipped_reason == "psycopg2"
    # No checks were recorded, so per-check counts stay empty.
    assert module.summary_counts()[RunStatus.TOOL_UNAVAILABLE.value] == 0


def test_guard_defaults_to_read_only() -> None:
    guard = ReadOnlyGuard()
    assert guard.mode == GuardMode.READ_ONLY
    with pytest.raises(MutationNotAvailable):
        guard.require_read_only()


def test_guard_blocks_write_outside_mutation() -> None:
    guard = ReadOnlyGuard(mode=GuardMode.MUTATION)
    with pytest.raises(MutationNotAvailable):
        guard.require_read_only()  # no active mutation scope


def test_guard_mutation_lifecycle() -> None:
    guard = ReadOnlyGuard(mode=GuardMode.MUTATION)
    declaration = guard.declare_mutation("QA-MUT-001", "isolated QA record")
    assert declaration.tag == "qa_harness_"
    guard.record_created("org-abc")
    assert guard.created_ids == {"org-abc"}
    guard.require_read_only()  # passes inside an active scope
    guard.finish_mutation(cleanup_verified=True)
    assert declaration.cleanup_verified is True


def test_guard_rejects_declare_in_read_only() -> None:
    guard = ReadOnlyGuard()
    with pytest.raises(MutationNotAvailable):
        guard.declare_mutation("QA-MUT-002", "should be blocked")
