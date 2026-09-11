"""Harness self-tests: read-only database QA modules (spec §8, §9)."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_harness.core.config import TargetEnv
from qa_harness.core.status import ToolUnavailable
from qa_harness.db.constraints import ConstraintAudit
from qa_harness.db.indexes import IndexAudit
from qa_harness.db.integrity import IntegrityAudit, IntegrityRule, build_standard_rules
from qa_harness.db.migrations import MigrationAudit, MigrationRecord
from qa_harness.db.rls import RlsAudit, RlsExpectation, build_standard_expectations
from qa_harness.db.schema_inventory import SchemaInventory, TableInfo


def _probed() -> dict:
    return {
        "organizations": TableInfo(name="organizations", columns={"id"}, rls_enabled=True, row_count=10),
        "users": TableInfo(name="users", columns={"id"}, rls_enabled=True, row_count=10),
        "organization_files": TableInfo(name="organization_files", columns={"id"}, rls_enabled=False, row_count=100),
    }


def test_schema_missing_tables() -> None:
    inventory = SchemaInventory(expected_tables=["organizations", "vehicles", "not_there"])
    missing = inventory.missing_tables(_probed())
    assert missing == ["vehicles", "not_there"]


def test_schema_missing_columns() -> None:
    inventory = SchemaInventory(key_columns={"organizations": ["id", "name"]})
    missing = inventory.missing_columns(_probed())
    assert missing == {"organizations": ["name"]}


def test_schema_tables_without_rls() -> None:
    inventory = SchemaInventory(expected_tables=["organizations", "organization_files"])
    assert inventory.tables_without_rls(_probed()) == ["organization_files"]


def test_rls_expectations_documented() -> None:
    expectations = build_standard_expectations()
    assert expectations
    kinds = {e.expected for e in expectations}
    assert kinds <= {"ALLOW", "DENY", "PO DECISION REQUIRED"}


def test_rls_classify() -> None:
    audit = RlsAudit(expectations=[])
    expectation = RlsExpectation(id="X", actor="a", action="read",
                                 resource="r", expected="DENY")
    audit.classify(expectation, actual_denied=True)
    assert expectation.status == "PASS"
    audit.classify(expectation, actual_denied=False)
    assert expectation.status == "FAIL"


def test_integrity_rule_render() -> None:
    rule = IntegrityRule(id="T1", name="x", description="y", table="t",
                         sql="SELECT id FROM {table} LIMIT 1;")
    assert rule.render({"table": "organizations"}).startswith("SELECT")


def test_standard_integrity_rules_cover_documented_areas() -> None:
    rules = build_standard_rules()
    ids = {r.id for r in rules}
    assert "INT-ORPHAN-1" in ids
    assert any("conversation_participants" in r.table for r in rules)
    assert any("calculation_snapshots" in r.table for r in rules)
    assert any("emissions_logs" in r.table for r in rules)


def test_integrity_audit_run_with_fake_connection() -> None:
    class FakeCursor:
        def __init__(self, result):
            self._result = result

        def execute(self, sql):  # noqa: ANN001
            pass

        def fetchall(self):
            return self._result

        def close(self):
            pass

    class FakeConnection:
        def cursor(self):
            return FakeCursor([(5,)])

    rule = build_standard_rules()[0]
    audit = IntegrityAudit(FakeConnection(), rules=[rule])
    results = audit.run()
    assert results[rule.id] == 5  # count_only rule reads row[0] of the count

    class FailingCursor(FakeCursor):
        def execute(self, sql):  # noqa: ANN001
            raise RuntimeError("table does not exist")

    class FailingConnection:
        def cursor(self):
            return FailingCursor([])

    audit2 = IntegrityAudit(FailingConnection(), rules=[rule])
    assert audit2.run()[rule.id] == -1  # -1 = rule could not run


def test_migration_audit_parses_repo(tmp_path: Path) -> None:
    (tmp_path / "20260810000000_v3m1_processing_entities.sql").write_text("-- x")
    (tmp_path / "20260811000000_v3m2_not_a_migration.sql").write_text("-- x")
    (tmp_path / "readme.txt").write_text("-- x")
    audit = MigrationAudit(migrations_dir=tmp_path)
    records = audit.repo_migrations()
    assert len(records) == 2
    assert records[0].version == "20260810000000"
    assert records[1].name == "v3m2_not_a_migration"


def test_migration_not_applied_and_summary(tmp_path: Path) -> None:
    (tmp_path / "20260810000000_a.sql").write_text("-- x")
    (tmp_path / "20260811000000_b.sql").write_text("-- x")
    audit = MigrationAudit(migrations_dir=tmp_path)
    pending = audit.not_applied(["20260810000000"])
    assert [r.filename for r in pending] == ["20260811000000_b.sql"]
    summary = audit.summary(applied=["20260810000000"])
    assert summary["pending_count"] == 1
    assert summary["repo_migrations"] == 2


def test_index_audit_missing() -> None:
    audit = IndexAudit()
    probed = {
        "messages": TableInfo(name="messages", indexes=["idx_messages_conversation"]),
    }
    missing = audit.missing_indexes(probed)
    assert all(exp.table != "messages" or exp.column != "conversation_id" for exp in missing)


def test_constraint_audit_violations() -> None:
    audit = ConstraintAudit()
    probed = {
        "vehicles": TableInfo(name="vehicles", primary_key=["id"]),
        "conversation_participants": TableInfo(
            name="conversation_participants",
            primary_key=["id"],
            unique_constraints=[["conversation_id", "user_id"]],
        ),
    }
    violations = audit.violations(probed)
    # vehicles exists, PKs present and the unique pair is present → no violations.
    assert violations == []
    # A table with no PK is flagged.
    probed2 = {
        "vehicles": TableInfo(name="vehicles", primary_key=["id"]),
        "conversation_participants": TableInfo(name="conversation_participants"),
    }
    pk_violations = [v for v in audit.violations(probed2) if v.kind == "pk"]
    assert any(v.table == "conversation_participants" for v in pk_violations)


# --------------------------------------------------------------------------- #
# DSN resolution (V1.2 calibration) — never guesses, never leaks
# --------------------------------------------------------------------------- #

from qa_harness.scripts.run_db import _resolve_dsn  # noqa: E402

LOCAL = TargetEnv(
    name="local", postgres_dsn_env="DATABASE_URL",
    postgres_host="127.0.0.1", postgres_port=54426, postgres_db="postgres",
)


def test_resolve_dsn_none_raises_clear_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    with pytest.raises(ToolUnavailable) as exc:
        _resolve_dsn(LOCAL)
    assert "SUPABASE_DB_URL / DATABASE_URL" in str(exc.value)
    assert "POSTGRES_PASSWORD" in str(exc.value)


def test_resolve_dsn_supabase_alias_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://u:p@h:1/db")
    monkeypatch.setenv("DATABASE_URL", "postgresql://wrong:wrong@h:2/db")
    assert _resolve_dsn(LOCAL) == "postgresql://u:p@h:1/db"


def test_resolve_dsn_dsn_env_second(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h:2/db")
    assert _resolve_dsn(LOCAL) == "postgresql://u:p@h:2/db"


def test_resolve_dsn_structured_from_local_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_PASSWORD", "local-secret-123")
    dsn = _resolve_dsn(LOCAL)
    # built from environments.yaml defaults — password URL-encoded
    assert dsn == "postgresql://postgres:local-secret-123@127.0.0.1:54426/postgres"


def test_resolve_dsn_structured_with_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_PASSWORD", "s3cret with spaces!")
    monkeypatch.setenv("POSTGRES_USER", "carbon")
    monkeypatch.setenv("POSTGRES_HOST", "10.0.0.5")
    monkeypatch.setenv("POSTGRES_PORT", "55443")
    monkeypatch.setenv("POSTGRES_DB", "carbon_ledger")
    dsn = _resolve_dsn(LOCAL)
    assert dsn == "postgresql://carbon:s3cret%20with%20spaces%21@10.0.0.5:55443/carbon_ledger"


def test_resolve_dsn_respects_env_specific_dsn_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    staging = TargetEnv(name="staging", postgres_dsn_env="STAGING_DATABASE_URL")
    monkeypatch.setenv("STAGING_DATABASE_URL", "postgresql://s:p@h:3/db")
    assert _resolve_dsn(staging) == "postgresql://s:p@h:3/db"
    with pytest.raises(ToolUnavailable):
        monkeypatch.delenv("STAGING_DATABASE_URL", raising=False)
        _resolve_dsn(staging)


# --------------------------------------------------------------------------- #
# Supabase-status auto-discovery (local only, opt-in, no secret leakage)
# --------------------------------------------------------------------------- #

from qa_harness.scripts.run_db import (  # noqa: E402
    _dsn_from_supabase_status,
    _resolve_connection,
)

_STATUS_JSON = '{"DB_URL":"postgresql://postgres:postgres@127.0.0.1:54426/postgres",' \
               '"SERVICE_ROLE_KEY":"should-never-leak"}'

QACONFIG = type(
    "QaConfig", (), {"raw": {"qa_config.yaml": {"database": {"allow_supabase_status_discovery": True}}}}
)()


class _FakeProc:
    returncode = 0
    stdout = _STATUS_JSON


def _stub_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _name: "/usr/local/bin/supabase")
    monkeypatch.setattr("subprocess.run", lambda *a, **k: _FakeProc())


def test_discovery_local_extracts_db_url_only(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_subprocess(monkeypatch)
    assert _dsn_from_supabase_status(LOCAL, QACONFIG) == \
        "postgresql://postgres:postgres@127.0.0.1:54426/postgres"


def test_discovery_never_for_non_local_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_subprocess(monkeypatch)
    staging = TargetEnv(name="staging", postgres_dsn_env="STAGING_DATABASE_URL")
    assert _dsn_from_supabase_status(staging, QACONFIG) is None


def test_discovery_gated_by_config_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_subprocess(monkeypatch)
    off_config = type("QaConfig", (), {"raw": {"qa_config.yaml": {"database": {}}}})()
    assert _dsn_from_supabase_status(LOCAL, off_config) is None
    assert _dsn_from_supabase_status(LOCAL, None) is None


def test_discovery_falls_back_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    # CLI missing
    monkeypatch.setattr("shutil.which", lambda _name: None)
    assert _dsn_from_supabase_status(LOCAL, QACONFIG) is None
    # CLI errors
    _stub_subprocess(monkeypatch)

    class _BadProc:
        returncode = 1
        stdout = "boom"

    monkeypatch.setattr("subprocess.run", lambda *a, **k: _BadProc())
    assert _dsn_from_supabase_status(LOCAL, QACONFIG) is None


def test_resolve_connection_prefers_environment_over_discovery(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_subprocess(monkeypatch)
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:envpw@h:4/db")
    dsn, source = _resolve_connection(LOCAL, QACONFIG)
    assert dsn == "postgresql://u:envpw@h:4/db"
    assert source == "environment"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    dsn, source = _resolve_connection(LOCAL, QACONFIG)
    assert dsn == "postgresql://postgres:postgres@127.0.0.1:54426/postgres"
    assert source == "local supabase status discovery"
    with pytest.raises(ToolUnavailable):
        monkeypatch.setattr("shutil.which", lambda _name: None)
        _resolve_connection(LOCAL, QACONFIG)

