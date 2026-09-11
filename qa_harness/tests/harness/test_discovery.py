"""ResourceDiscovery self-tests — no live database (mocked psycopg2)."""

from __future__ import annotations

from typing import Any, List, Tuple

import pytest

from qa_harness.db import discovery as discovery_module
from qa_harness.db.discovery import ResourceDiscovery


class FakeCursor:
    def __init__(self, row: Any) -> None:
        self._row = row
        self.executed: List[Tuple[str, Tuple[Any, ...]]] = []

    def execute(self, sql: str, params: Tuple[Any, ...]) -> None:
        self.executed.append((sql, params))

    def fetchone(self) -> Any:
        return self._row

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self, row: Any) -> None:
        self._row = row
        self.closed = False
        self.cursors: List[FakeCursor] = []

    def cursor(self) -> FakeCursor:
        cur = FakeCursor(self._row)
        self.cursors.append(cur)
        return cur

    def close(self) -> None:
        self.closed = True


class FakePsycopg2:
    def __init__(self, row: Any, *, fail: bool = False) -> None:
        self._row = row
        self._fail = fail

    def connect(self, dsn: str, **kwargs: Any) -> FakeConnection:
        if self._fail:
            raise RuntimeError("connection refused")
        return FakeConnection(self._row)


def _patch_psycopg2(monkeypatch: pytest.MonkeyPatch, row: Any,
                    *, fail: bool = False) -> None:
    monkeypatch.setattr(discovery_module, "psycopg2", FakePsycopg2(row, fail=fail))
    monkeypatch.setattr(discovery_module, "_PSYCOPG2", True)


def test_conversation_id_for_returns_scalar(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_psycopg2(monkeypatch, ("conv-123",))
    discovery = ResourceDiscovery("postgresql://qa")
    assert discovery.conversation_id_for("owner.demo0001@demo.carbontally.local") == "conv-123"
    discovery.close()


def test_missing_table_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenCursor(FakeCursor):
        def execute(self, sql: str, params: Tuple[Any, ...]) -> None:
            raise discovery_module.psycopg2.ProgrammingError(
                'relation "conversations" does not exist')

    class BrokenConnection(FakeConnection):
        def cursor(self) -> FakeCursor:
            return BrokenCursor(None)

    class BrokenPsycopg2(FakePsycopg2):
        def connect(self, dsn: str, **kwargs: Any) -> FakeConnection:
            return BrokenConnection(None)

    monkeypatch.setattr(discovery_module, "psycopg2", BrokenPsycopg2(None))
    monkeypatch.setattr(discovery_module, "_PSYCOPG2", True)
    discovery = ResourceDiscovery("postgresql://qa")
    assert discovery.conversation_id_for("owner.demo0001@demo.carbontally.local") is None


def test_unreachable_db_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_psycopg2(monkeypatch, None, fail=True)
    discovery = ResourceDiscovery("postgresql://qa")
    assert discovery.conversation_id_for_org("org-1") is None


def test_missing_driver_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(discovery_module, "_PSYCOPG2", False)
    discovery = ResourceDiscovery("postgresql://qa")
    assert discovery.conversation_id_for("x@y.z") is None


def test_results_are_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakePsycopg2(("conv-1",))
    monkeypatch.setattr(discovery_module, "psycopg2", fake)
    monkeypatch.setattr(discovery_module, "_PSYCOPG2", True)
    discovery = ResourceDiscovery("postgresql://qa")
    assert discovery.conversation_id_for("a@b.c") == "conv-1"
    assert discovery.conversation_id_for("a@b.c") == "conv-1"
    # Only ONE cursor should ever have been created (second call cached).
    assert discovery._conn is not None
    assert len(discovery._conn.cursors) == 1
    discovery.close()


def test_close_closes_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_psycopg2(monkeypatch, ("conv-1",))
    discovery = ResourceDiscovery("postgresql://qa")
    discovery.conversation_id_for("a@b.c")
    conn = discovery._conn
    discovery.close()
    assert conn is not None and conn.closed is True
    assert discovery._conn is None


def test_context_manager_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_psycopg2(monkeypatch, ("conv-1",))
    with ResourceDiscovery("postgresql://qa") as discovery:
        discovery.conversation_id_for("a@b.c")
        conn = discovery._conn
    assert conn is not None and conn.closed is True


def test_other_org_query_uses_distinct(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_psycopg2(monkeypatch, ("conv-other",))
    discovery = ResourceDiscovery("postgresql://qa")
    assert discovery.conversation_id_for_other_org("org-a") == "conv-other"
    discovery.close()
