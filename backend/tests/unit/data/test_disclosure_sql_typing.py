"""Phase 8 B1 — SQL-typing, audit-wiring and correction-migration guards (static).

Gate **V1** (``CT-P8-B1-V1-INDEPENDENT-VERIFICATION-20260912-014``) confirmed two
PostgreSQL parameter-typing defects and a missing audit expectation that the
purely static tests could not detect at runtime. The **authoritative** coverage
is the runtime suite (``tests/integration/test_disclosure_b1_runtime.py``); these
cheap, no-database guards exist so that removing a required type cast, the
NULL-snapshot evidence branch or the audit wiring fails fast in the unit suite as
well — the "simplification" that would reintroduce the V1 defects.

Correction task: ``CT-P8-B1-CORRECTION-20260912-015``.
"""
from __future__ import annotations

import re
from pathlib import Path

from domain.audit import CAT_REPORT, classify_action
from domain.disclosure import AUDIT_ACTIONS

CORRECTION_MIGRATION = (
    "20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql"
)

B1_TABLES = (
    "disclosure_frameworks",
    "disclosure_framework_versions",
    "disclosure_requirement_versions",
    "disclosure_requirement_mappings",
    "disclosure_report_purposes",
    "disclosure_report_purpose_versions",
    "disclosure_purpose_requirements",
    "disclosure_applicability_assessments",
    "disclosure_report_instance_binding",
    "disclosure_values",
    "disclosure_value_evidence",
)

AUDIT_ACTION_CONSTANTS = (
    "AUDIT_FRAMEWORK_SEEDED",
    "AUDIT_PURPOSE_SEEDED",
    "AUDIT_APPLICABILITY_ASSESSED",
    "AUDIT_REPORT_BOUND",
    "AUDIT_VALUE_MATERIALISED",
    "AUDIT_EVIDENCE_LINKED",
)


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "supabase" / "migrations").is_dir():
            return parent
    raise AssertionError("could not locate repo root (supabase/migrations)")


ROOT = _repo_root()
DATA_SRC = (ROOT / "backend" / "data" / "disclosure.py").read_text(encoding="utf-8")
DOMAIN_SRC = (ROOT / "backend" / "domain" / "disclosure.py").read_text(
    encoding="utf-8"
)
MIGRATION_SRC = (ROOT / "supabase" / "migrations" / CORRECTION_MIGRATION).read_text(
    encoding="utf-8"
)
#: Migration text with ``--`` comment lines removed (a word in a comment is not a
#: statement) — the same helper convention as the B1 migration test.
MIGRATION_STATEMENTS = "\n".join(
    line for line in MIGRATION_SRC.splitlines() if not line.lstrip().startswith("--")
)


# --- F1: reused parameter typing ($9) --------------------------------------
def test_f1_assessment_reused_parameter_is_explicitly_typed() -> None:
    """``determined_by`` is reused as an ``IS NULL`` test and ``created_by``."""
    assert "CASE WHEN $9::uuid IS NULL THEN NULL ELSE now() END" in DATA_SRC
    assert not re.search(r"CASE WHEN \$9 IS NULL", DATA_SRC)
    assert (
        "VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6::jsonb, $7, $8, $9::uuid,"
        in DATA_SRC
    )


# --- F2: value_status typing ($6) ------------------------------------------
def test_f2_value_status_parameter_is_explicitly_typed() -> None:
    """``value_status`` is compared to a literal and assigned to a varchar column."""
    assert "CASE WHEN $6::varchar = 'RESOLVED' THEN now() ELSE NULL END" in DATA_SRC
    assert not re.search(r"CASE WHEN \$6 = 'RESOLVED'", DATA_SRC)


# --- F3: NULL-snapshot evidence-link idempotency ---------------------------
def test_f3_null_snapshot_evidence_branch_exists() -> None:
    """The NULL-snapshot reference is made idempotent explicitly (not by ON CONFLICT)."""
    assert "calculation_snapshot_id IS NULL" in DATA_SRC
    assert "AND emissions_log_id IS NOT DISTINCT FROM $5::uuid" in DATA_SRC
    assert "AND source_item_id IS NOT DISTINCT FROM $6::uuid" in DATA_SRC
    assert "AND source_file_id IS NOT DISTINCT FROM $7::uuid" in DATA_SRC
    # the non-NULL path keeps its B1 upsert semantics
    assert "ON CONFLICT (disclosure_value_id, calculation_snapshot_id) DO UPDATE SET" in DATA_SRC


# --- F5: audit wiring ------------------------------------------------------
def test_f5_audit_actions_are_declared_and_used() -> None:
    for constant in AUDIT_ACTION_CONSTANTS:
        assert constant in DOMAIN_SRC, f"{constant} missing from domain vocabulary"
        assert constant in DATA_SRC, f"{constant} not wired into the repository"
    # helper definition + exactly six write-path call sites (2 catalogue + 4 writes)
    assert DATA_SRC.count("await _record_audit(") == 6


def test_f5_audit_reuses_the_existing_mechanism() -> None:
    """No new audit table/subsystem: the existing repository is reused."""
    assert "from data.audit import AuditRepository" in DATA_SRC
    assert "from domain.audit import ACTOR_SYSTEM, AuditEntry" in DATA_SRC
    assert "AuditRepository(pool).record(" in DATA_SRC
    # B1 never writes the ledger directly (no hand-rolled audit SQL).
    assert "INSERT INTO public.audit" not in DATA_SRC
    assert "UPDATE public.audit" not in DATA_SRC


def test_audit_actions_classify_as_report_category() -> None:
    """The existing taxonomy classifies every B1 action as ``CAT_REPORT``."""
    assert len(AUDIT_ACTIONS) == len(AUDIT_ACTION_CONSTANTS)
    for action in AUDIT_ACTIONS:
        assert classify_action(action) == CAT_REPORT, action


# --- B2/B3/B4 boundary in the data layer -----------------------------------
#: The SQL actually executed by the data layer. Only triple-quoted blocks that
#: contain a statement verb are considered, so prose (module/function docstrings)
#: cannot mask a real leak the way a bare word search would.
SQL_BLOCK_LIST = [
    block
    for block in re.findall(r'"""(.*?)"""', DATA_SRC, flags=re.S)
    if re.search(r"\b(INSERT INTO|SELECT|UPDATE|DELETE FROM)\b", block)
]
SQL_BLOCKS = "\n".join(SQL_BLOCK_LIST)


def test_no_b2_b3_b4_objects_in_the_repository() -> None:
    """The B1 data layer's SQL stays inside its sanctioned scope.

    **AMENDED for Phase 8 B2** (contract §20.6 / F-B2-13 — *amended, never
    deleted*): the former “no B2 object at all” assertions are replaced by the
    narrower, still-strict guarantee that B2 enters this repository **only**
    through the one ratified additive link (§9.3) — the
    ``disclosure_value_evidence`` link statement and its snapshot-derived read —
    and never as ``evidence_line_items`` DDL/DML. The B3/B4 guards are unchanged.
    """
    # B3/B4 remain barred (unchanged guards)
    assert "intensity" not in SQL_BLOCKS.lower()
    assert "narrative" not in SQL_BLOCKS.lower()
    assert "commentary" not in SQL_BLOCKS.lower()
    # B2 (amended): the B1 repository never touches the B2 table itself ...
    assert "evidence_line_items" not in SQL_BLOCKS
    # ... and the only B2 column it may mention is the sanctioned line link.
    assert "source_line_item_id" in SQL_BLOCKS
    for block in SQL_BLOCK_LIST:
        if "source_line_item_id" not in block:
            continue
        assert any(
            sanctioned in block
            for sanctioned in (
                # §9.3 — the sanctioned additive column on the evidence link
                "INSERT INTO public.disclosure_value_evidence",
                "UPDATE public.disclosure_value_evidence SET",
                # §9.2 — the snapshot-derived read that fills it honestly
                "SELECT source_line_item_id FROM public.calculation_snapshots",
            )
        ), block
        assert "evidence_line_items" not in block


# --- F4/F3: the additive correction migration ------------------------------
def test_correction_migration_is_additive_and_idempotent() -> None:
    """Additive, B1-scoped, no destructive statement, no existing table touched."""
    assert "CREATE UNIQUE INDEX IF NOT EXISTS uq_dve_reference_nullsafe" in MIGRATION_SRC
    for statement in MIGRATION_STATEMENTS.splitlines():
        stripped = statement.strip().upper()
        for forbidden in ("DROP ", "ALTER TABLE", "DELETE FROM", "TRUNCATE TABLE"):
            assert not stripped.startswith(forbidden), statement
    # the B1 migration must not be touched by the correction (a prose mention of
    # its filename in a comment is not a statement — checked on the SQL only)
    assert "20260914000000" not in MIGRATION_STATEMENTS


def test_correction_migration_privileges_cover_all_eleven_tables() -> None:
    for table in B1_TABLES:
        assert (
            f"GRANT ALL ON TABLE public.{table} TO service_role;"
            in MIGRATION_SRC
        ), f"missing service_role grant for {table}"
        assert (
            f"REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.{table}"
            in MIGRATION_SRC
        ), f"missing elevated-privilege revoke for {table}"
    assert MIGRATION_SRC.count("GRANT ALL ON TABLE public.disclosure_") == 11
    assert (
        MIGRATION_SRC.count(
            "REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_"
        )
        == 11
    )
    # no permissive write policy is introduced anywhere
    assert "USING (true)" not in MIGRATION_STATEMENTS
