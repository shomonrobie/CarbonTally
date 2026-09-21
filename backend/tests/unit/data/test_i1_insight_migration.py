"""I1 — CarbonTally Insight persistence migration contract (DDL/RLS text).

Authorisation: CT-P8-I1-INSIGHT-PERSISTENCE-20260921-002.

The repository's established convention for schema-boundary tests is to assert
the migration text (``test_b2_migration.py``, ``test_disclosure_migration.py``),
so the declared boundary cannot drift silently. This module asserts the I1
boundary from D2:

* two Layer-1 tables exist under canonical ``carbontally_insight_*`` naming
  (D2 §3.2.1/§3.8) and no ``ask_*`` object is created;
* organisation scoping, creator identity, ordering, referential integrity,
  indexes and constraints are declared (D2 §24.2);
* an explicit RLS posture exists (D2 §24.6) with creator-private predicates
  (D2 §9.2) and no client UPDATE/DELETE (I1 has no such surface);
* the migration does **not** touch the human messaging domain (D2 §6.2) or the
  dormant ``ai_content_history`` table (D2 §22), and invents no I2–I8 fields.
"""
from __future__ import annotations

import pathlib
import re

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_MIGRATION = _REPO_ROOT / "supabase" / "migrations" / "20261001000000_p8_i1_insight_persistence.sql"


def _sql() -> str:
    assert _MIGRATION.exists(), f"I1 migration missing: {_MIGRATION}"
    return _MIGRATION.read_text(encoding="utf-8")


def _ddl() -> str:
    """SQL with comment lines removed (assertions target executable DDL)."""
    return "\n".join(
        line for line in _sql().splitlines() if not line.strip().startswith("--")
    )


def _ddl_structure() -> str:
    """Executable DDL with every single-quoted literal blanked out.

    The migration *documents* the I1 boundary in schema comments (e.g. "no
    retention/archival"), and comment bodies may contain semicolons, so boundary
    assertions must read declared structure only — never comment text.
    """
    return re.sub(r"'[^']*'", "''", _ddl(), flags=re.DOTALL)


def test_i1_migration_is_the_latest_migration() -> None:
    """The I1 migration must sort after every pre-existing migration."""
    names = sorted(p.name for p in (_REPO_ROOT / "supabase" / "migrations").glob("*.sql"))
    assert names[-1] == _MIGRATION.name, names[-3:]


def test_i1_migration_creates_canonical_insight_tables() -> None:
    ddl = _ddl()
    assert "CREATE TABLE IF NOT EXISTS public.carbontally_insight_conversations" in ddl
    assert "CREATE TABLE IF NOT EXISTS public.carbontally_insight_messages" in ddl
    assert "ask_conversations" not in ddl and "ask_messages" not in ddl
    assert not re.search(r"\bask_", ddl), "ask_* naming must not be introduced"


def test_i1_migration_scopes_every_row_to_an_organisation() -> None:
    ddl = _ddl()
    assert ddl.count("organization_id  uuid NOT NULL REFERENCES public.organizations(id)") == 2
    # A message must be structurally unable to disagree with its conversation's
    # organisation (composite FK), which also makes the RLS predicate expressible.
    assert "FOREIGN KEY (conversation_id, organization_id)" in ddl
    assert "REFERENCES public.carbontally_insight_conversations (id, organization_id)" in ddl
    assert "UNIQUE (id, organization_id)" in ddl


def test_i1_migration_declares_ordering_identity_and_constraints() -> None:
    ddl = _ddl()
    assert "CONSTRAINT ci_messages_ordinal_unique UNIQUE (conversation_id, ordinal)" in ddl
    assert "CONSTRAINT ci_messages_ordinal_check CHECK (ordinal >= 1)" in ddl
    assert "CONSTRAINT ci_messages_role_check CHECK (role IN ('user', 'insight'))" in ddl
    assert "CONSTRAINT ci_messages_content_check CHECK (length(content) > 0)" in ddl
    assert "CONSTRAINT ci_messages_user_has_author_check" in ddl
    for index in (
        "idx_ci_conversations_org_created",
        "idx_ci_conversations_org_creator_created",
        "idx_ci_messages_conversation_ordinal",
        "idx_ci_messages_org",
    ):
        assert index in ddl, index


def test_i1_migration_states_an_explicit_rls_posture() -> None:
    ddl = _ddl()
    assert ddl.count("ENABLE ROW LEVEL SECURITY") == 2
    assert "REVOKE ALL ON TABLE public.carbontally_insight_conversations FROM anon" in ddl
    assert "REVOKE ALL ON TABLE public.carbontally_insight_messages      FROM anon" in ddl
    assert "GRANT SELECT, INSERT ON TABLE public.carbontally_insight_conversations TO authenticated" in ddl
    assert "GRANT SELECT, INSERT ON TABLE public.carbontally_insight_messages      TO authenticated" in ddl
    assert "GRANT ALL ON TABLE public.carbontally_insight_conversations TO service_role" in ddl
    assert "GRANT ALL ON TABLE public.carbontally_insight_messages      TO service_role" in ddl
    # No client privilege statement grants UPDATE or DELETE in I1.
    grants = re.findall(r"GRANT[^;]*;", _ddl_structure())
    client_grants = [g for g in grants if "authenticated" in g]
    assert client_grants, "expected explicit client grants (RLS posture)"
    assert all("UPDATE" not in g for g in client_grants), client_grants
    assert all("DELETE" not in g for g in client_grants), client_grants
    assert any("SELECT, INSERT" in g for g in client_grants), client_grants
    assert any("service_role" in g for g in grants), grants


def test_i1_migration_policies_are_creator_private_and_org_scoped() -> None:
    ddl = _ddl()
    assert "CREATE POLICY ci_conversations_creator_select" in ddl
    assert "CREATE POLICY ci_conversations_creator_insert" in ddl
    assert "public.is_org_member(organization_id)" in ddl
    assert "created_by = auth.uid()" in ddl
    assert "CREATE POLICY ci_messages_conversation_creator_select" in ddl
    assert "CREATE POLICY ci_messages_conversation_creator_insert" in ddl
    # Messages inherit the parent conversation's creator (no sharing semantics).
    assert ddl.count("c.created_by = auth.uid()") == 2
    # No UPDATE/DELETE policy exists anywhere in I1.
    assert "FOR UPDATE" not in ddl and "FOR DELETE" not in ddl
    # Idempotent guard convention: one EXISTS check per declared policy.
    assert ddl.count("FROM pg_policies") == 4


def test_i1_migration_does_not_touch_messaging_or_dormant_ai_structures() -> None:
    ddl = _ddl()
    # D2 §6.2 — the human messaging domain is never coupled to Insight.
    for table in ("public.conversations", "public.messages", "public.message_activity_log"):
        assert table not in ddl, table
    # D2 §22 / prompt §8 — the dormant AI table is untouched.
    assert "ai_content_history" not in ddl
    assert "DROP TABLE" not in ddl.upper()


def test_i1_migration_does_not_invent_i2_to_i8_fields() -> None:
    ddl = _ddl_structure().lower()
    for forbidden in (
        "provider",
        "model",
        "prompt",
        "tokens",
        "retention",
        "archived_at",
        "deleted_at",
        "billing",
        "status",
        "audit_event",
        "result_hash",
    ):
        assert forbidden not in ddl, f"I1 must not introduce '{forbidden}'"


def test_i1_migration_records_the_i1_boundary_in_schema_comments() -> None:
    sql = _sql()
    assert "D2 §5.1/§7" in sql
    assert "creator-private" in sql
    assert "deferred by D2 §11.6" in sql
    assert "NOT an answer status" in sql
    assert "that is I4" in sql
