"""WS1 / DB-0001 — audit/activity immutability migration regression tests.

Deterministic tests that read the migration file (the canonical definition of
the RLS change) and verify the invariants the audit backlog required:

* UPDATE/DELETE tenant policies are dropped (IF EXISTS, idempotent) on the
  immutable historical tables: audit_logs, activity_logs, document_activity_log.
* activity_feed mutation stays possible for UX but is row-owner scoped
  (``user_id = auth.uid()``), preserving tenant isolation.
* No tables are dropped and the V3 ``audit_trail`` is untouched.

They run with zero external dependencies and no database connection.
"""
from __future__ import annotations

from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[4] / "supabase" / "migrations"
MIGRATION = MIGRATIONS_DIR / "20260831020000_audit_activity_immutability.sql"


def _read() -> str:
    assert MIGRATION.exists(), f"migration file missing: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def _normalize(sql: str) -> str:
    return " ".join(sql.split()).lower()


def test_drops_update_and_delete_on_immutable_audit_logs() -> None:
    sql = _normalize(_read())
    assert "drop policy if exists audit_logs_tenant_update" in sql
    assert "drop policy if exists audit_logs_tenant_delete" in sql


def test_drops_update_and_delete_on_immutable_activity_logs() -> None:
    sql = _normalize(_read())
    assert "drop policy if exists activity_logs_tenant_update" in sql
    assert "drop policy if exists activity_logs_tenant_delete" in sql


def test_drops_update_and_delete_on_document_activity_log() -> None:
    sql = _normalize(_read())
    assert "drop policy if exists document_activity_log_tenant_update" in sql
    assert "drop policy if exists document_activity_log_tenant_delete" in sql


def test_activity_feed_mutation_is_row_owner_scoped() -> None:
    sql = _normalize(_read())
    # The old org-member-wide update/delete are gone; new policies require the
    # row owner (user_id = auth.uid()).
    assert "drop policy if exists activity_feed_tenant_update" in sql
    assert "drop policy if exists activity_feed_tenant_delete" in sql
    assert "create policy activity_feed_own_update" in sql
    assert "user_id = auth.uid()" in sql
    assert "create policy activity_feed_own_delete" in sql


def test_insert_and_select_policies_are_preserved() -> None:
    sql = _read().upper()
    # We only drop UPDATE/DELETE on the immutable tables — never INSERT/SELECT.
    assert "DROP POLICY IF EXISTS AUDIT_LOGS_TENANT_INSERT" not in sql
    assert "DROP POLICY IF EXISTS AUDIT_LOGS_TENANT_SELECT" not in sql
    assert "DROP POLICY IF EXISTS ACTIVITY_LOGS_TENANT_INSERT" not in sql
    assert "DROP POLICY IF EXISTS ACTIVITY_LOGS_TENANT_SELECT" not in sql
    assert "DROP POLICY IF EXISTS DOCUMENT_ACTIVITY_LOG_TENANT_INSERT" not in sql
    assert "DROP POLICY IF EXISTS DOCUMENT_ACTIVITY_LOG_TENANT_SELECT" not in sql


def test_non_destructive_and_does_not_touch_v3_audit_trail() -> None:
    sql = _read().upper()
    assert "DROP TABLE" not in sql
    assert "TRUNCATE" not in sql
    # The comment may reference audit_trail, but no statement may target it.
    assert "DROP POLICY" not in sql or "ON PUBLIC.AUDIT_TRAIL" not in sql
    assert "ALTER TABLE PUBLIC.AUDIT_TRAIL" not in sql
