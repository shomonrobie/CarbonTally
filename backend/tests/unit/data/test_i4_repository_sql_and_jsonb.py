"""I4 remediation regression — reserved identifier + asyncpg JSONB decoding.

Authorization: PO I4 bounded remediation (2026-09-21), OHD I4 verification
D-1/D-2/D-3. These tests fail on the pre-remediation implementation:

* the shipped migration/application SQL used the bare reserved word
  ``references`` (PostgreSQL ``syntax error at or near "references"``);
* the row mappers coerced asyncpg's **text** jsonb values with ``dict()``
  (``ValueError: dictionary update sequence element #0 has length 1``).

They are deliberately not a substitute for executing the migration against a real
PostgreSQL: ``tests/integration/test_i4_live_migration_and_persistence.py`` does
that on a disposable database.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

from data import insight_interactions as repo

_ROOT = pathlib.Path(__file__).resolve().parents[4]
_MIGRATION = _ROOT / "supabase" / "migrations" / "20261003000000_p8_i4_insight_interactions.sql"

#: PostgreSQL reserved words that appear (or appeared) in the I4 DDL/SQL.
_RESERVED = ("references",)


def _migration_structure() -> str:
    text = _MIGRATION.read_text()
    text = re.sub(r"--[^\n]*", "", text)          # comments
    return re.sub(r"'[^']*'", "''", text, flags=re.DOTALL)   # string literals


@pytest.mark.parametrize("word", _RESERVED)
def test_migration_never_declares_a_reserved_identifier_unquoted(word: str) -> None:
    structure = _migration_structure()
    # A bare ``references`` in an identifier position (column list / definition)
    # aborts the migration. Quoted occurrences are fine.
    bare = re.findall(rf"(?<![\w\"])({word})(?![\w\"])", structure)
    assert bare == [], (
        f"unquoted reserved identifier {word!r} appears {len(bare)} time(s); "
        "it must be written as \"references\" (OHD D-1)"
    )
    assert f'"{word}"' in structure


def test_tool_call_sql_quotes_the_reserved_identifier() -> None:
    columns = repo._TOOL_CALL_COLUMNS
    insert = repo._RECORD_TOOL_CALL_SQL
    assert '"references"' in columns
    assert '"references"' in insert
    # The unquoted form must not survive anywhere in a SQL identifier position.
    for sql in (columns, repo._LIST_TOOL_CALLS_SQL, repo._GET_TOOL_CALL_BY_LOGICAL_SQL, insert):
        assert not re.search(r'(?<![\w"])references(?![\w"])', sql), sql


def test_placeholder_order_matches_the_insert_column_list() -> None:
    insert = repo._RECORD_TOOL_CALL_SQL
    columns = insert.split("(", 1)[1].split(")", 1)[0]
    names = [c.strip() for c in columns.replace("\n", " ").split(",") if c.strip()]
    values = insert.split("VALUES", 1)[1].split("ON CONFLICT", 1)[0]
    placeholders = re.findall(r"\$(\d+)", values)
    assert len(names) == len(placeholders)
    assert [int(p) for p in placeholders] == list(range(1, len(names) + 1))
    assert names[placeholders.index("9")] == '"references"'


# --------------------------------------------------------------------------
# D-3 — asyncpg returns jsonb as TEXT in this configuration
# --------------------------------------------------------------------------
def _interaction_row(**kw) -> dict:
    row = {
        "id": "11111111-1111-4111-8111-111111111111",
        "organization_id": "22222222-2222-4222-8222-222222222222",
        "conversation_id": "33333333-3333-4333-8333-333333333333",
        "created_by": "44444444-4444-4444-8444-444444444444",
        "lifecycle": "completed",
        "answer_status": "success",
        "message_id": "55555555-5555-4555-8555-555555555555",
        "audit_record_id": "66666666-6666-4666-8666-666666666666",
        "idempotency_key": "k-1",
        "question_hash": "a" * 64,
        "request_hash": "b" * 64,
        "intent": "report_lookup",
        "intent_source": "deterministic",
        "provider": None,
        "model": None,
        "model_version": None,
        "narration_state": "skipped",
        "tokens_used": None,
        "cost": None,
        "tool_call_count": 1,
        "reference_count": 1,
        "error_class": None,
        "metadata": json.dumps({"contract_version": "i4-layer2-v1"}),  # asyncpg TEXT
        "created_at": None,
        "completed_at": None,
    }
    row.update(kw)
    return row


def test_interaction_row_mapper_decodes_text_jsonb() -> None:
    mapped = repo._row_to_interaction(_interaction_row())
    assert mapped.metadata == {"contract_version": "i4-layer2-v1"}
    assert mapped.lifecycle == "completed"


def test_interaction_row_mapper_handles_null_jsonb() -> None:
    assert repo._row_to_interaction(_interaction_row(metadata=None)).metadata == {}


def test_tool_call_row_mapper_decodes_text_jsonb_and_references() -> None:
    row = {
        "id": "77777777-7777-4777-8777-777777777777",
        "interaction_id": "11111111-1111-4111-8111-111111111111",
        "organization_id": "22222222-2222-4222-8222-222222222222",
        "call_ordinal": 1,
        "tool_name": "report_lookup",
        "contract_version": "i3-6point-v1",
        "tool_status": "success",
        "arguments": json.dumps({"report_id": "88888888-8888-4888-8888-888888888888"}),
        "result_metadata": json.dumps({"status": "success", "item_count": 3}),
        "references": json.dumps([{"kind": "report", "id": "x"}]),
        "arguments_hash": "c" * 64,
        "result_hash": "d" * 64,
        "result_item_count": 3,
        "truncated": False,
        "duration_ms": 12,
        "created_at": None,
    }
    mapped = repo._row_to_tool_call(row)
    assert mapped.arguments == {"report_id": "88888888-8888-4888-8888-888888888888"}
    assert mapped.result_metadata == {"status": "success", "item_count": 3}
    assert mapped.references == ({"kind": "report", "id": "x"},)


def test_tool_call_row_mapper_handles_null_and_malformed_references() -> None:
    row = {
        "id": "99999999-9999-4999-8999-999999999999",
        "interaction_id": "11111111-1111-4111-8111-111111111111",
        "organization_id": "22222222-2222-4222-8222-222222222222",
        "call_ordinal": 1,
        "tool_name": "report_lookup",
        "contract_version": "i3-6point-v1",
        "tool_status": "no_data",
        "arguments": None,
        "result_metadata": None,
        "references": json.dumps(["not-a-dict"]),
        "arguments_hash": "c" * 64,
        "result_hash": "d" * 64,
        "result_item_count": 0,
        "truncated": False,
        "duration_ms": None,
        "created_at": None,
    }
    mapped = repo._row_to_tool_call(row)
    assert mapped.arguments == {}
    assert mapped.result_metadata == {}
    assert mapped.references == ()
