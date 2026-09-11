"""run_db runner regression tests — the cursor/connection bug (V1.2 first run).

The live first run crashed with:

    'psycopg2.extensions.cursor' object has no attribute 'cursor'

because run_db passed a **cursor** to collectors that expect a **connection**
(SchemaProbe._fetch / IntegrityAudit.run call ``connection.cursor()``). These
tests pin the corrected wiring: collectors get a connection, a collection
failure is a HARNESS_RUNTIME_ERROR (never an application finding), and no
evidence is written from a failed/partial collection.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

from qa_harness.core.config import TargetEnv
from qa_harness.core.evidence import EvidenceStore
from qa_harness.core.findings import FindingClassification
from qa_harness.core.run_context import RunContext
from qa_harness.db.schema_inventory import EXPECTED_TABLES
from qa_harness.evidence.registry import EvidenceRegistry
from qa_harness.findings.store import FindingStore
from qa_harness.scripts import run_db as run_db_module

ENV = TargetEnv(name="local", api_url="http://localhost:8050")


def _args() -> argparse.Namespace:
    return argparse.Namespace(env="local", read_only=True)


class FakeCursor:
    """Mimics psycopg2 cursor. Deliberately has NO ``cursor()`` method —
    passing this to a collector (the historical bug) must fail loudly."""

    def __init__(self, row_source: Any) -> None:
        self._row_source = row_source
        self._rows: List[Tuple[Any, ...]] = []
        self.executed: List[str] = []

    def execute(self, sql: str, params: Optional[List[Any]] = None) -> None:
        self.executed.append(sql)
        self._rows = self._row_source(sql, params or [])

    def fetchall(self) -> List[Tuple[Any, ...]]:
        return self._rows

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self, row_source: Any) -> None:
        self._row_source = row_source
        self.closed = False
        self._cursors: List[FakeCursor] = []

    def cursor(self) -> FakeCursor:
        cur = FakeCursor(self._row_source)
        self._cursors.append(cur)
        return cur

    def close(self) -> None:
        self.closed = True

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class FakePsycopg2:
    def __init__(self, row_source: Any) -> None:
        self._row_source = row_source
        self.connections: List[FakeConnection] = []

    def connect(self, dsn: str, **kwargs: Any) -> FakeConnection:
        conn = FakeConnection(self._row_source)
        self.connections.append(conn)
        return conn


def _all_tables_row_source(sql: str, params: List[Any]) -> List[Tuple[Any, ...]]:
    """Realistic read-only results: every expected table present, all
    documented PKs / composite uniques / the facilities check / all expected
    indexes present, RLS enabled everywhere → zero findings."""
    if "information_schema.tables" in sql and "table_schema = 'public'" in sql:
        return [(t,) for t in EXPECTED_TABLES]
    if "information_schema.columns" in sql:
        from qa_harness.db.schema_inventory import KEY_TABLE_COLUMNS
        return [(table, column, "text")
                for table, columns in KEY_TABLE_COLUMNS.items()
                for column in columns]
    if "constraint_type = 'UNIQUE'" in sql:
        return [
            ("conversation_participants", "u_cp", "conversation_id"),
            ("conversation_participants", "u_cp", "user_id"),
            ("organization_members", "u_om", "organization_id"),
            ("organization_members", "u_om", "user_id"),
            ("consultant_clients", "u_cc", "consultant_id"),
            ("consultant_clients", "u_cc", "organization_id"),
        ]
    if "pg_get_constraintdef" in sql:
        return [("facilities",
                 "CHECK (((postcode IS NOT NULL) OR (eircode IS NOT NULL)))")]
    if "pg_indexes" in sql:
        from qa_harness.db.indexes import build_expected_indexes
        return [(exp.table, f"idx_{exp.table}_{exp.column}") for exp in build_expected_indexes()]
    if "constraint_type = 'PRIMARY KEY'" in sql:
        pks = [
            ("conversation_participants", "id"),
            ("emissions_logs", "id"),
            ("calculation_snapshots", "id"),
            ("organization_files", "id"),
        ]
        return [(t, c) for t, c in pks]
    if "relrowsecurity" in sql:
        return [(t, True, False) for t in EXPECTED_TABLES]
    if "supabase_migrations" in sql:
        from qa_harness.db.migrations import MigrationAudit
        return [(r.version,) for r in MigrationAudit().repo_migrations()]
    return []


def _patch(monkeypatch: pytest.MonkeyPatch, row_source: Any) -> FakePsycopg2:
    fake = FakePsycopg2(row_source)
    monkeypatch.setattr(run_db_module, "psycopg2", fake)
    monkeypatch.setattr(run_db_module, "_PSYCOPG2", True)
    monkeypatch.setattr(run_db_module, "_resolve_connection",
                        lambda env=None, config=None: ("postgresql://qa", "test"))
    return fake


def _ctx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> RunContext:
    monkeypatch.setenv("CARBON_TALLY_DEMO_PASSWORD", "demo-pass-2026!")
    return RunContext(
        env=ENV, env_name="local", git_sha="abc1234",
        store=FindingStore(tmp_path / "findings"),
        evidence=EvidenceStore(tmp_path / "evidence"),
        registry=EvidenceRegistry(EvidenceStore(tmp_path / "evidence2")),
    )


def _db_evidence_files(ctx: RunContext) -> List[Path]:
    base = ctx.evidence.base_dir / "db"
    if not base.exists():
        return []
    return sorted(base.glob("*.json"))


def test_run_db_passes_connection_not_cursor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: a cursor (which has no ``.cursor()``) must NEVER reach the
    collectors. With the corrected wiring the run completes; the historical
    wiring raised AttributeError."""
    _patch(monkeypatch, _all_tables_row_source)
    ctx = _ctx(tmp_path, monkeypatch)
    assert run_db_module.run_db(_args(), ctx=ctx) == run_db_module.EXIT_OK
    assert ctx.raw_findings() == []
    # evidence written from the completed collection
    names = {p.name for p in _db_evidence_files(ctx)}
    assert names == {
        f"{ctx.run_id}_db_unnamed_db_schema.json",
        f"{ctx.run_id}_db_unnamed_db_rls.json",
        f"{ctx.run_id}_db_unnamed_db_integrity.json",
        f"{ctx.run_id}_db_unnamed_db_indexes.json",
        f"{ctx.run_id}_db_unnamed_db_constraints.json",
        f"{ctx.run_id}_db_unnamed_db_migrations.json",
    }
    assert ctx.checks_executed > 0


def test_run_db_schema_evidence_has_tables(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, _all_tables_row_source)
    ctx = _ctx(tmp_path, monkeypatch)
    run_db_module.run_db(_args(), ctx=ctx)
    schema = next(p for p in _db_evidence_files(ctx) if p.name.endswith("_db_schema.json"))
    payload = json.loads(schema.read_text())
    assert payload["tables_probed"] == len(EXPECTED_TABLES)
    assert payload["missing_tables"] == []
    assert "organizations" in payload["tables"]


def test_collection_failure_is_harness_runtime_error_not_app_finding(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(sql: str, params: List[Any]) -> List[Tuple[Any, ...]]:
        if "information_schema.tables" in sql:
            raise RuntimeError("relation does not exist")
        return []

    _patch(monkeypatch, boom)
    ctx = _ctx(tmp_path, monkeypatch)
    code = run_db_module.run_db(_args(), ctx=ctx)
    assert code == run_db_module.EXIT_FAIL
    findings = ctx.raw_findings()
    # exactly one finding, classified as a harness/tool failure
    assert len(findings) == 1
    assert findings[0].classification == FindingClassification.HARNESS_RUNTIME_ERROR
    assert "harness/tool" in findings[0].title.lower()
    # NO evidence is written from a failed collection
    assert _db_evidence_files(ctx) == []


def test_cursor_object_as_connection_still_fails_loudly() -> None:
    """Pin the exact historical failure mode: if a cursor is ever passed to a
    collector again, it must raise (so tests catch the regression) rather than
    silently producing bogus schema data."""
    from qa_harness.db.schema_inventory import SchemaProbe

    cursor = FakeCursor(_all_tables_row_source)
    probe = SchemaProbe(cursor)  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        probe.probe()


def test_connection_is_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _patch(monkeypatch, _all_tables_row_source)
    ctx = _ctx(tmp_path, monkeypatch)
    run_db_module.run_db(_args(), ctx=ctx)
    assert fake.connections and all(c.closed for c in fake.connections)


def test_probe_groups_composite_uniques_and_keeps_check_definitions() -> None:
    """Regression for the two latent probe defects found during calibration:
    multi-column UNIQUE rows must be grouped into ONE entry per constraint
    (a flattened per-column list can never match a unique_pair rule), and
    CHECK rows must carry the constraint DEFINITION, not just the name."""
    from qa_harness.db.schema_inventory import SchemaProbe

    def rows(sql: str, params: List[Any]) -> List[Tuple[Any, ...]]:
        if "information_schema.tables" in sql:
            return [("conversation_participants",), ("facilities",)]
        if "constraint_type = 'UNIQUE'" in sql:
            return [
                ("conversation_participants", "u_cp", "conversation_id"),
                ("conversation_participants", "u_cp", "user_id"),
            ]
        if "pg_get_constraintdef" in sql:
            return [("facilities", "CHECK (((postcode IS NOT NULL) OR (eircode IS NOT NULL)))")]
        return []

    conn = FakeConnection(rows)
    probed = SchemaProbe(conn).probe()
    assert probed["conversation_participants"].unique_constraints == [
        ["conversation_id", "user_id"],
    ]
    assert any("postcode" in c for c in probed["facilities"].check_constraints)
