"""Phase 8 B1 — migration structural tests (implementation tests, no DB).

Statically verifies the B1 migration against the contract (§9/§10/§11/§22) and
the ratified PQ decisions (PQ-1…PQ-8). These are *implementation* tests; the
independent verification gate (V1) remains separate.
"""
from __future__ import annotations

import re
from pathlib import Path

MIGRATION_NAME = "20260914000000_p8_b1_disclosure_model_foundation.sql"


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "supabase" / "migrations").is_dir():
            return parent
    raise AssertionError("could not locate repo root (supabase/migrations)")


SQL = (_repo_root() / "supabase" / "migrations" / MIGRATION_NAME).read_text(encoding="utf-8")

#: SQL with ``--`` comment lines removed (a word in a comment is not a statement).
CLEAN = "\n".join(
    line for line in SQL.splitlines() if not line.lstrip().startswith("--")
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


# --- A. File + table scope --------------------------------------------------
def test_migration_file_exists() -> None:
    assert SQL.strip(), "migration must not be empty"


def test_exactly_eleven_b1_tables() -> None:
    created = re.findall(r"CREATE TABLE IF NOT EXISTS public\.(disclosure_[a-z_]+)", SQL)
    assert sorted(created) == sorted(B1_TABLES)
    assert len(created) == 11
    assert len(set(created)) == 11  # no 12th table, no duplicate


def test_no_b2_b3_b4_tables() -> None:
    # These are B2/B3/B4 concerns; B1 must not CREATE or reference them as tables.
    for forbidden in (
        "evidence_line_items",
        "disclosure_intensity_denominator_types",
        "disclosure_intensity_ratios",
        "disclosure_narratives",
        "disclosure_management_commentary",
        "disclosure_gases",
        "disclosure_base_year_records",
        "disclosure_targets",
        "disclosure_actions",
    ):
        assert f"public.{forbidden}" not in CLEAN, f"B1 must not introduce {forbidden}"


# --- B. No existing table modified -----------------------------------------
def test_no_alter_on_existing_tables() -> None:
    alters = re.findall(r"ALTER TABLE\s+public\.([a-z_]+)", CLEAN)
    for table in alters:
        assert table in B1_TABLES, f"B1 must not ALTER existing table: {table}"


def test_no_source_line_item_id_column() -> None:
    # B2 owns the additive column; B1 must not create it.
    assert "source_line_item_id" not in CLEAN


# --- C. PQ-3: value_status + effective_class -------------------------------
def test_value_status_is_materialisation_only() -> None:
    assert "value_status varchar NOT NULL DEFAULT 'PENDING'" in SQL
    m = re.search(r"disclosure_values_value_status_check\s*\n\s*CHECK \(value_status IN \(([^)]*)\)", SQL)
    assert m, "value_status CHECK not found"
    values = {v.strip().strip("'") for v in m.group(1).split(",")}
    assert values == {"PENDING", "RESOLVED", "UNRESOLVED"}
    for forbidden in ("CUSTOMER_INPUT_REQUIRED", "NOT_SUPPORTED", "NOT_APPLICABLE", "UNDETERMINED"):
        assert f"'{forbidden}'" not in m.group(1)


def test_effective_class_present_and_authoritative() -> None:
    assert "effective_class varchar NOT NULL" in SQL
    m = re.search(r"disclosure_values_effective_class_check\s*\n\s*CHECK \(effective_class IN \(([^)]*)\)", SQL)
    assert m
    assert "REQUIRED" in m.group(1)


def test_value_uniqueness_per_report_version_requirement() -> None:
    assert "CONSTRAINT disclosure_values_unique UNIQUE (report_version_id, requirement_version_id)" in SQL


# --- D. PQ-2 / DM-3: periods -------------------------------------------------
def test_both_period_tables_have_explicit_periods() -> None:
    for table in ("disclosure_applicability_assessments", "disclosure_report_instance_binding"):
        assert table in SQL
    assert SQL.count("reporting_period_start date NOT NULL") == 2
    assert SQL.count("reporting_period_end date NOT NULL") == 2
    assert SQL.count("CHECK (reporting_period_end >= reporting_period_start)") >= 2


def test_binding_is_unique_per_report() -> None:
    assert "UNIQUE (report_id)" in SQL


def test_consolidation_vocabulary() -> None:
    assert "OPERATIONAL_CONTROL" in SQL and "FINANCIAL_CONTROL" in SQL and "EQUITY_SHARE" in SQL


# --- E. Identifier safety + not-in-force ------------------------------------
def test_identifier_safety_check_present() -> None:
    assert (
        "CHECK (identifier_status = 'RESOLVED' OR official_identifier IS NULL)" in SQL
    )


def test_not_in_force_constraint_present() -> None:
    assert "CHECK (status <> 'ADOPTED_NOT_IN_FORCE' OR applicable_from IS NULL)" in SQL


def test_partial_unique_current_mapping() -> None:
    assert re.search(
        r"CREATE UNIQUE INDEX IF NOT EXISTS uq_drm_current\s*\n\s*ON public\.disclosure_requirement_mappings \(requirement_version_id\)\s*\n\s*WHERE is_current",
        SQL,
    )


# --- F. Idempotency + RLS + seeds -------------------------------------------
def test_idempotency_guards() -> None:
    assert "CREATE TABLE IF NOT EXISTS" in SQL
    assert "CREATE INDEX IF NOT EXISTS" in SQL
    assert "ON CONFLICT (code) DO NOTHING" in SQL


def test_all_tables_enable_rls_and_revoke_anon() -> None:
    rls_tables = set(
        re.findall(r"ALTER TABLE public\.(disclosure_[a-z_]+) ENABLE ROW LEVEL SECURITY", CLEAN)
    )
    for arr in re.findall(r"ARRAY\[(.*?)\]", CLEAN, re.S):
        rls_tables |= set(re.findall(r"'(disclosure_[a-z_]+)'", arr))
    assert rls_tables == set(B1_TABLES)
    assert "REVOKE ALL ON TABLE" in CLEAN
    assert "REVOKE ALL ON TABLE public.%I FROM anon" in CLEAN
    assert "FROM anon" in SQL


def test_seeds_seed_identities_only() -> None:
    assert "'GHG_PROTOCOL'" in SQL and "'UK_SECR'" in SQL and "'ESRS_E1'" in SQL
    assert "'ANNUAL_CARBON'" in SQL and "'MANAGEMENT'" in SQL and "'ESRS_E1_QUANT'" in SQL
    # No framework VERSION rows and no requirement/mapping content are seeded (PQ-6).
    assert "INSERT INTO public.disclosure_framework_versions" not in SQL
    assert "INSERT INTO public.disclosure_requirement_versions" not in SQL
    assert "INSERT INTO public.disclosure_requirement_mappings" not in SQL

