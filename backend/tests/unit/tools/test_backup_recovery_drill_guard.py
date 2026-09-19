"""Workstream F — the recovery drill must never point at a database whose data matters.

``tools/backup_recovery_drill.py`` creates, populates and (by default) drops a target
database, so a mis-pointed run is destructive. The guard is the F-046-1-style invariant: a
disposable name is ``ct_*`` or the dedicated test database, and anything that looks like a
persistent environment (qa/demo/investor/prod/live) is refused BEFORE any SQL runs.
"""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

_TOOL = pathlib.Path(__file__).resolve().parents[4] / "tools" / "backup_recovery_drill.py"


def _drill():
    spec = importlib.util.spec_from_file_location("ct_backup_drill_tool", _TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_the_drill_tool_exists_at_the_documented_path() -> None:
    assert _TOOL.is_file(), f"missing recovery-drill tool at {_TOOL}"


def test_disposable_names_are_accepted() -> None:
    drill = _drill()
    assert drill.assert_disposable("ct_step2_070", "source") == "ct_step2_070"
    assert drill.assert_disposable("ct_f0391_065", "target") == "ct_f0391_065"
    # the dedicated disposable test database is allowed by its own name
    assert drill.assert_disposable("carbontally_test", "source") == "carbontally_test"


@pytest.mark.parametrize("name", [
    "ct_demo_clone",          # 'demo' in a disposable-looking name
    "ct_investor_seed",
    "ct_prod_restore",
    "ct_live_check",
    "ct_qa_snapshot",
    "postgres",               # not disposable at all
    "carbontally_prod",
])
def test_persistent_or_ambiguous_names_are_refused(name: str) -> None:
    drill = _drill()
    with pytest.raises(SystemExit):
        drill.assert_disposable(name, "source")
    with pytest.raises(SystemExit):
        drill.assert_disposable(name, "target")
