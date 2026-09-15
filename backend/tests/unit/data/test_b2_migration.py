"""Phase 8 B2 — migration structural tests (implementation tests, no DB).

Statically verifies the two B2 migrations against the ratified contract
(§7/§8/§9/§16/§18) and the closed B2 decisions (B2-D1, B2-D3, B2-D7, B2-D11).
The runtime/privilege behaviour is covered by
``tests/integration/test_evidence_line_items_b2_runtime.py``.
"""
from __future__ import annotations

import re
from pathlib import Path

MIGRATION_1 = "20260916000000_p8_b2_evidence_line_items.sql"
MIGRATION_2 = "20260916010000_p8_b2_provenance_line_links.sql"

#: The B1 files B2 must leave byte-identical (§18.3) — the two B1 migration-text
#: guards stay valid because these files never mention B2 objects.
B1_MIGRATIONS = (
    "20260914000000_p8_b1_disclosure_model_foundation.sql",
    "20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql",
)


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "supabase" / "migrations").is_dir():
            return parent
    raise AssertionError("could not locate repo root (supabase/migrations)")


def _read(name: str) -> str:
    return (_repo_root() / "supabase" / "migrations" / name).read_text(encoding="utf-8")


def _without_comments(sql: str) -> str:
    return "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    )


def _without_text_literals(sql: str) -> str:
    """Remove single-quoted literals so COMMENT prose cannot mask a statement."""
    return re.sub(r"'(?:[^']|'')*'", "''", sql)


SQL1 = _read(MIGRATION_1)
SQL2 = _read(MIGRATION_2)
CLEAN1 = _without_comments(SQL1)
CLEAN2 = _without_comments(SQL2)
STATEMENTS1 = _without_text_literals(CLEAN1)
STATEMENTS2 = _without_text_literals(CLEAN2)


# --- A. Transactional, additive, idempotent ---------------------------------


def test_both_migrations_are_single_transactions() -> None:
    for clean in (CLEAN1, CLEAN2):
        assert clean.count("BEGIN;") == 1 and clean.count("COMMIT;") == 1


def test_b2_1_creates_exactly_one_table() -> None:
    created = re.findall(r"CREATE TABLE IF NOT EXISTS public\.([a-z_]+)", CLEAN1)
    assert created == ["evidence_line_items"]


def test_no_destructive_or_data_statement_anywhere() -> None:
    for clean in (CLEAN1, CLEAN2):
        for statement in (
            "DROP ",
            "ALTER COLUMN",
            "RENAME",
            "UPDATE public.",
            "DELETE FROM",
            "TRUNCATE ",
        ):
            assert statement not in clean, statement


def test_b2_2_modifies_exactly_two_columns_on_two_existing_tables() -> None:
    altered = re.findall(r"ALTER TABLE public\.([a-z_]+)", CLEAN2)
    assert set(altered) == {"calculation_snapshots", "disclosure_value_evidence"}
    adds = re.findall(r"ADD COLUMN IF NOT EXISTS ([a-z_]+) uuid", CLEAN2)
    assert adds == ["source_line_item_id", "source_line_item_id"]  # one per table
    # additive on existing objects only: no grant/policy/RLS/table change
    for forbidden in (
        "GRANT ",
        "REVOKE ",
        "POLICY",
        "CREATE TABLE",
        "ENABLE ROW LEVEL SECURITY",
    ):
        assert forbidden not in CLEAN2, forbidden


# --- B. Table/column shape (§7.1) -------------------------------------------


def test_evidence_line_items_column_shape() -> None:
    for column in (
        "id                   uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4()",
        "organization_id      uuid NOT NULL",
        "source_item_id       uuid NOT NULL",
        "line_number          integer NOT NULL",
        "source_page          integer,",
        "row_reference        text,",
        "raw_description      text,",
        "raw_quantity         numeric,",
        "raw_unit             text,",
        "payload_hash         text NOT NULL",
        "extraction_method    varchar NOT NULL DEFAULT 'unknown'",
        "materialisation_kind varchar NOT NULL",
        "created_at           timestamptz NOT NULL DEFAULT now()",
    ):
        assert column in SQL1, column


def test_evidence_line_items_constraints() -> None:
    assert "UNIQUE (source_item_id, line_number)" in SQL1
    assert "CHECK (line_number >= 1)" in SQL1
    assert "CHECK (source_page IS NULL OR source_page >= 1)" in SQL1
    assert "CHECK (materialisation_kind IN ('FORWARD', 'BACKFILL'))" in SQL1
    # B2-D7: the extraction-method vocabulary is OPEN — no CHECK on that column.
    assert "CHECK (extraction_method" not in SQL1


def test_delete_semantics_match_the_closed_decisions() -> None:
    # B2-D1 — preservation-first parent link; CASCADE only for organization_id.
    assert "REFERENCES public.manual_extraction_items(id) ON DELETE RESTRICT" in SQL1
    assert "REFERENCES public.organizations(id) ON DELETE CASCADE" in SQL1
    assert "REFERENCES public.organization_files(id) ON DELETE SET NULL" in SQL1
    for name in (
        "calculation_snapshots_source_line_item_id_fkey",
        "disclosure_value_evidence_source_line_item_id_fkey",
    ):
        assert name in SQL2
    assert STATEMENTS2.count("ON DELETE SET NULL") == 2


def test_indexes_are_four_explicit_plus_one_constraint_backed() -> None:
    explicit1 = re.findall(r"CREATE INDEX IF NOT EXISTS ([a-z_]+)", CLEAN1)
    explicit2 = re.findall(r"CREATE INDEX IF NOT EXISTS ([a-z_]+)", CLEAN2)
    assert explicit1 == ["idx_eli_org", "idx_eli_source_file"]
    assert explicit2 == [
        "idx_calculation_snapshots_source_line_item",
        "idx_dve_source_line_item",
    ]
    assert len(explicit1) + len(explicit2) == 4
    # the identity index is the UNIQUE constraint, counted separately
    assert "evidence_line_items_identity_unique" in SQL1


def test_guarded_constraints_are_created_once_by_name() -> None:
    for name in (
        "calculation_snapshots_source_line_item_id_fkey",
        "disclosure_value_evidence_source_line_item_id_fkey",
    ):
        assert f"conname = '{name}'" in SQL2
    assert CLEAN2.count("ADD CONSTRAINT") == 2


# --- C. Security posture (§16) ----------------------------------------------


def test_b2_1_privilege_posture() -> None:
    assert "ALTER TABLE public.evidence_line_items ENABLE ROW LEVEL SECURITY;" in SQL1
    assert "REVOKE ALL ON TABLE public.evidence_line_items FROM anon;" in SQL1
    assert "GRANT SELECT ON TABLE public.evidence_line_items TO authenticated;" in SQL1
    assert (
        "REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, MAINTAIN"
        in SQL1
    )
    assert "GRANT ALL ON TABLE public.evidence_line_items TO service_role;" in SQL1


def test_exactly_two_select_policies_and_no_write_policy() -> None:
    policies = re.findall(r"CREATE POLICY ([a-z_]+)", CLEAN1)
    assert sorted(policies) == [
        "evidence_line_items_entity_select",
        "evidence_line_items_org_select",
    ]
    assert CLEAN1.count("FOR SELECT TO authenticated") == 2
    for cmd in ("FOR INSERT", "FOR UPDATE", "FOR DELETE"):
        assert cmd not in CLEAN1
    # the B1 helper is reused, never recreated
    assert "public.p8_disclosure_is_org_member(organization_id)" in CLEAN1
    assert "public.work_item_effective_entity(source_item_id) IS NOT NULL" in CLEAN1
    assert "public.is_entity_member(" in CLEAN1
    assert "CREATE OR REPLACE FUNCTION" not in CLEAN1


def test_b2_1_fails_loudly_when_b1_is_absent() -> None:
    assert "RAISE EXCEPTION" in CLEAN1
    assert "public.p8_disclosure_is_org_member(uuid)" in CLEAN1
    assert "to_regprocedure" in CLEAN1


def test_no_retention_or_trigger_artefact() -> None:
    for forbidden in (
        "CREATE TRIGGER",
        "deleted_at",
        "is_active",
        "anonymis",
        "purge",
        "DELETE FROM",
    ):
        assert forbidden not in STATEMENTS1, forbidden


# --- D. B1 files are untouched (§18.3) --------------------------------------


def test_b1_migration_files_still_carry_no_b2_object() -> None:
    """The two B1 migration-text guards remain valid: B1 is byte-identical."""
    for name in B1_MIGRATIONS:
        statements = _without_text_literals(_without_comments(_read(name)))
        assert "evidence_line_items" not in statements, name
        assert "source_line_item_id" not in statements, name
