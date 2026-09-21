"""I4 — Layer-2 interaction migration (canonical namespace, append-only, RLS).

Authorization: PO I4 Implementation Authorization (2026-09-21) / PO Q1–Q14.
These assertions are structural: they pin the ratified boundaries in the DDL so a
later edit cannot silently widen I4 (no legacy table, no payload columns, no
retention/billing fields, creator-private policies, append-only triggers).
"""
from __future__ import annotations

import pathlib
import re

_MIGRATION = (
    pathlib.Path(__file__).resolve().parents[4]
    / "supabase"
    / "migrations"
    / "20261003000000_p8_i4_insight_interactions.sql"
)


def _structure() -> str:
    """Declared structure only: comments and string literals removed, so the
    migration's own prohibition prose cannot satisfy a frozen assertion."""
    text = re.sub(r"--[^\n]*", "", _ddl())
    return re.sub(r"'[^']*'", "''", text, flags=re.DOTALL)


def _ddl() -> str:
    text = _MIGRATION.read_text()
    return "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("--")
    )


def test_i4_migration_exists_and_uses_the_canonical_namespace() -> None:
    ddl = _ddl()
    assert "CREATE TABLE IF NOT EXISTS public.carbontally_insight_interactions" in ddl
    assert "CREATE TABLE IF NOT EXISTS public.carbontally_insight_tool_calls" in ddl
    assert "ask_" not in ddl


def test_i4_migration_does_not_touch_legacy_or_unrelated_schema() -> None:
    ddl = _structure()
    for forbidden in (
        "ai_content_history",
        "audit_trail",
        "audit_logs",
        "usage_tracking",
        "report_generation_queue",
        "public.conversations",
        "public.messages",
    ):
        assert forbidden not in ddl, forbidden
    # No DDL may alter or drop anything: I4 is purely additive.
    assert "ALTER TABLE public.ai" not in ddl
    assert "DROP TABLE" not in ddl
    assert "DROP COLUMN" not in ddl


def test_i4_migration_keeps_the_two_status_vocabularies_separate() -> None:
    ddl = _ddl()
    # I3 tool statuses (closed) on the tool-call evidence...
    for status in (
        "'success'",
        "'no_data'",
        "'not_authorized'",
        "'invalid_input'",
        "'provider_unavailable'",
        "'error'",
    ):
        assert status in ddl
    # ...and the fourteen I4 answer states on the interaction record.
    for status in (
        "'zero'",
        "'insufficient_data'",
        "'needs_clarification'",
        "'tool_failure'",
        "'partial'",
        "'rate_limited'",
        "'refused'",
        "'ungrounded'",
    ):
        assert status in ddl


def test_i4_migration_enforces_append_only_evidence() -> None:
    ddl = _ddl()
    assert "ci_tool_calls_immutable" in ddl
    assert "ci_interactions_immutable" in ddl
    assert "terminal interaction evidence is immutable" in ddl
    assert "is not a forward transition" in ddl


def test_i4_migration_declares_creator_private_rls() -> None:
    ddl = _ddl()
    assert "ENABLE ROW LEVEL SECURITY" in ddl
    assert "ci_interactions_creator_select" in ddl
    assert "ci_interactions_creator_insert" in ddl
    assert "ci_tool_calls_creator_select" in ddl
    assert "ci_tool_calls_creator_insert" in ddl
    assert "created_by = auth.uid()" in ddl
    assert "public.is_org_member(organization_id)" in ddl


def test_i4_migration_revokes_client_mutation() -> None:
    ddl = _ddl()
    assert "REVOKE ALL ON TABLE public.carbontally_insight_interactions FROM anon" in ddl
    assert "REVOKE ALL ON TABLE public.carbontally_insight_tool_calls   FROM anon" in ddl
    assert "REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, MAINTAIN" in ddl
    assert "GRANT SELECT, INSERT ON TABLE public.carbontally_insight_interactions TO authenticated" in ddl


def test_i4_migration_has_no_i5_i7_i8_surfaces() -> None:
    ddl = _structure()
    for forbidden in (
        "retention_days",
        "delete_at",
        "credit",
        "embedding",
        "vector",
        "context_window",
        "compaction",
    ):
        assert forbidden not in ddl.lower(), forbidden


def test_i4_migration_stores_hashes_not_raw_text() -> None:
    ddl = _ddl()
    assert "question_hash" in ddl
    assert "arguments_hash" in ddl
    assert "result_hash" in ddl
    # No raw-content columns are introduced on Layer 2 (PO Q4/Q6).
    for forbidden in ("content text", "prompt_text", "generated_content", "raw_payload"):
        assert forbidden not in ddl
