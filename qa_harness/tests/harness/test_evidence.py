"""Harness self-tests: evidence path generation (spec §26, §35)."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_harness.core.evidence import EvidenceStore, KINDS, sanitize_token
from qa_harness.evidence.registry import EvidenceRegistry


def test_sanitize_token() -> None:
    assert sanitize_token("Customer Admin") == "Customer_Admin"
    assert sanitize_token("pe-manager-1.demo") == "pe-manager-1.demo"
    assert sanitize_token("/////") == "unnamed"


def test_path_generation(tmp_path: Path) -> None:
    store = EvidenceStore(base_dir=tmp_path)
    path = store.path("screenshots", "20260824T150000_abc123", "consultant",
                      "dashboard", route="/consultant", ext="png")
    assert path.parent == tmp_path / "screenshots"
    assert "20260824T150000_abc123" in path.name
    assert "consultant" in path.name
    assert path.suffix == ".png"


def test_collision_never_overwrites(tmp_path: Path) -> None:
    store = EvidenceStore(base_dir=tmp_path)
    first = store.write("api", "run1", "operator", "response", '{"ok":true}')
    second = store.write("api", "run1", "operator", "response", '{"ok":false}')
    assert first != second
    assert first.read_text(encoding="utf-8") == '{"ok":true}'
    assert second.read_text(encoding="utf-8") == '{"ok":false}'


def test_unknown_kind_raises(tmp_path: Path) -> None:
    store = EvidenceStore(base_dir=tmp_path)
    with pytest.raises(ValueError):
        store.path("nope", "run", "role", "name")


def test_all_kinds_exist(tmp_path: Path) -> None:
    store = EvidenceStore(base_dir=tmp_path)
    for kind in KINDS:
        assert (tmp_path / kind).is_dir()


def test_registry_records(tmp_path: Path) -> None:
    store = EvidenceStore(base_dir=tmp_path)
    registry = EvidenceRegistry(store=store)
    path = store.path("console", "run1", "viewer", "log", ext="txt")
    registry.record("console", path, role="viewer", route="/home", run_id="run1")
    items = registry.by_kind("console")
    assert len(items) == 1
    # Registry stores paths relative to the evidence root.
    assert items[0].path == path.relative_to(tmp_path).as_posix()
    assert items[0].role == "viewer"
