"""P17 migrations — schema-boundary contract tests (DDL/RLS text).

The repository's established convention for schema-boundary tests is to assert
the migration TEXT (``test_b2_migration.py``, ``test_disclosure_migration.py``,
``test_i1_insight_migration.py``) so the declared boundary cannot drift silently.
These tests do the same for the four P17 migrations.

They assert only what the architecture commits to:

* the four P17 migrations exist, are strictly ordered after the P16 baseline and
  are numbered in the sequence the schema delta prescribes;
* every change is ADDITIVE — no ``DROP TABLE``, no ``DROP COLUMN``, no
  ``DELETE FROM``, no data rewrite, no destructive ``TRUNCATE``;
* the eight accounting dimensions, the boundary/origin discriminators and the
  acting-for columns are declared, with the vocabulary CHECKs the architecture
  fixed (four Scope 2 energy types, no ``fuel``; categories 1-15; five
  data-quality values);
* the mandatory-for-new-writes rules are ``NOT VALID`` so historical P16 rows
  are never rewritten;
* the two new tables and one new reference table carry the established RLS
  posture (RLS ENABLED, ``anon`` denied, policies reusing
  ``public.is_org_member``);
* the consultant ↔ organization linkage (ARCH-06 HIGH-01) and the composite
  cross-tenant instrument FK (DC-09) are declared.
"""
from __future__ import annotations

import pathlib
import re

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_MIGRATIONS_DIR = _REPO_ROOT / "supabase" / "migrations"

P17_A = _MIGRATIONS_DIR / "20261010000000_p17a_accounting_dimensions_and_factor_governance.sql"
P17_C = _MIGRATIONS_DIR / "20261011000000_p17c_contractual_instruments_and_allocations.sql"
P17_D = _MIGRATIONS_DIR / "20261012000000_p17d_scope3_category_taxonomy.sql"
P17_H = _MIGRATIONS_DIR / "20261013000000_p17h_estimation_and_assumption_records.sql"
#: P17-IMPLEMENT-10 — the product-contract reporting dimensions (scope3_method,
#: transaction_provider, the widened data-quality vocabulary).
P17_10 = (
    _MIGRATIONS_DIR
    / "20261014000000_p17_10_product_contract_reporting_dimensions.sql"
)

P17_MIGRATIONS = (P17_A, P17_C, P17_D, P17_H, P17_10)

#: The P16 baseline this series must follow (P16-R7 idempotency migration).
_P16_BASELINE = "20261009000000"

#: The P16 result-reportability columns that must NOT be touched by P17.
_P16_PRESERVED_COLUMNS = (
    "reportability_status",
    "invalidated_reason",
    "invalidated_by",
    "invalidated_at",
    "superseded_by_snapshot_id",
)


def _text(path: pathlib.Path) -> str:
    assert path.exists(), f"P17 migration missing: {path}"
    return path.read_text(encoding="utf-8")


def _code(path: pathlib.Path) -> str:
    """SQL with comment lines removed, so assertions target executable DDL."""
    return "\n".join(
        line for line in _text(path).splitlines() if not line.lstrip().startswith("--")
    )


def _all_p17() -> str:
    return "\n".join(_text(p) for p in P17_MIGRATIONS)


# ---------------------------------------------------------------------------
# Existence and ordering
# ---------------------------------------------------------------------------
def test_all_p17_migrations_exist_and_are_in_sequence() -> None:
    for path in P17_MIGRATIONS:
        assert path.exists(), path


def test_p17_migration_timestamps_follow_the_p16_baseline_and_increase() -> None:
    stamps = [p.name.split("_")[0] for p in P17_MIGRATIONS]
    assert stamps == sorted(stamps), stamps
    assert stamps[0] > _P16_BASELINE
    assert stamps == [
        "20261010000000",
        "20261011000000",
        "20261012000000",
        "20261013000000",
        "20261014000000",
    ]


def test_p17_does_not_reuse_or_edit_a_historical_timestamp() -> None:
    p17_names = {p.name for p in P17_MIGRATIONS}
    for existing in _MIGRATIONS_DIR.glob("*.sql"):
        stamp = existing.name.split("_")[0]
        if stamp > _P16_BASELINE:
            assert existing.name in p17_names, (
                f"unexpected migration after the P16 baseline: {existing.name}"
            )


# ---------------------------------------------------------------------------
# Additive-only discipline
# ---------------------------------------------------------------------------
def test_no_destructive_statement_appears_in_any_p17_migration() -> None:
    """Additive-only: nothing may drop, delete, truncate or rewrite.

    ``REVOKE TRUNCATE`` is a *privilege revocation* and is expected here, so
    REVOKE lines are removed before the check rather than the word being allowed
    everywhere.
    """
    code = "\n".join(
        line
        for line in _all_p17().upper().splitlines()
        if not line.lstrip().startswith("REVOKE")
    )
    for forbidden in (
        "DROP TABLE",
        "DROP COLUMN",
        "DELETE FROM",
        "TRUNCATE",
        "ALTER COLUMN",
    ):
        assert forbidden not in code, f"destructive statement found: {forbidden}"


def test_no_backfill_or_data_rewrite_of_historical_rows_occurs() -> None:
    """No UPDATE of an existing accounting table; new columns stay NULL for history."""
    code = _all_p17().upper()
    assert "UPDATE PUBLIC.CALCULATION_SNAPSHOTS" not in code
    assert "UPDATE PUBLIC.EMISSIONS_LOGS" not in code
    assert "UPDATE PUBLIC.EMISSION_FACTORS" not in code


def test_every_new_column_is_nullable_with_no_default() -> None:
    """A DEFAULT would fabricate a dimension for historical rows."""
    code = _all_p17()
    # Every ADD COLUMN IF NOT EXISTS clause offered here declares no DEFAULT.
    for match in re.finditer(r"ADD COLUMN IF NOT EXISTS (.+?)(?:,|;)", code, re.S):
        clause = match.group(1)
        assert "DEFAULT" not in clause.upper(), clause


def test_p16_reportability_columns_are_never_altered() -> None:
    code = _all_p17()
    for column in _P16_PRESERVED_COLUMNS:
        assert not re.search(
            rf"ALTER TABLE public\.(calculation_snapshots|emissions_logs)\s+"
            rf"ALTER COLUMN\s+{column}",
            code,
            re.I,
        ), column


# ---------------------------------------------------------------------------
# The eight accounting dimensions
# ---------------------------------------------------------------------------
_DIMENSION_COLUMNS = (
    "scope2_method",
    "scope3_category",
    "energy_type",
    "data_quality",
    "facility_id",
    "transport_boundary",
    "waste_origin",
    "source_snapshot_id",
)


def test_calculation_snapshots_gains_all_eight_dimensions() -> None:
    code = _text(P17_A)
    for column in _DIMENSION_COLUMNS:
        assert re.search(rf"ADD COLUMN IF NOT EXISTS {column}\b", code), column


def test_emissions_logs_mirrors_the_same_eight_dimensions() -> None:
    """Consumption-boundary parity: reporting filters without a join."""
    code = _text(P17_A)
    emissions_block = code.split("2. emissions_logs")[1].split("3. emission_factors")[0]
    for column in _DIMENSION_COLUMNS:
        assert re.search(rf"ADD COLUMN IF NOT EXISTS {column}\b", emissions_block), column


def test_energy_type_check_is_exactly_the_four_scope2_types_without_fuel() -> None:
    """ARCH-04 / ARCH-03 LOW-02: fuel is NOT a Scope 2 energy type."""
    code = _text(P17_A)
    match = re.search(
        r"energy_type IS NULL OR energy_type IN \(([^)]*)\)", code
    )
    assert match, "energy_type CHECK missing"
    allowed = {v.strip().strip("'") for v in match.group(1).split(",")}
    assert allowed == {"electricity", "heat", "steam", "cooling"}
    assert "fuel" not in allowed
    # 'fuel' must appear nowhere as an allowed value.
    assert "'fuel'," not in code and "'fuel')" not in code


def test_scope3_category_check_is_1_to_15() -> None:
    code = _text(P17_A)
    assert "scope3_category IS NULL OR scope3_category BETWEEN 1 AND 15" in code


def test_data_quality_check_lists_exactly_five_classifications() -> None:
    code = _text(P17_A)
    match = re.search(r"ADD CONSTRAINT calc_snapshots_data_quality_check\s+CHECK \(([^)]*)\)", code, re.S)
    assert match, "data_quality CHECK missing"
    allowed = set(re.findall(r"'([a-z_]+)'", match.group(1)))
    assert allowed == {
        "primary_measured",
        "primary_supplier",
        "secondary_estimated",
        "spend_based_estimated",
        "modelled",
    }


def test_boundary_vocabularies_are_declared() -> None:
    code = _text(P17_A)
    assert "transport_boundary IN ('upstream', 'downstream')" in code
    assert "waste_origin IN ('operations', 'sold_product_eol')" in code


def test_scope2_method_vocabulary_reuses_the_frozen_b1_values() -> None:
    code = _text(P17_A)
    assert "scope2_method IN ('LOCATION_BASED', 'MARKET_BASED')" in code


# ---------------------------------------------------------------------------
# P17-IMPLEMENT-10 — product-contract reporting dimensions
# ---------------------------------------------------------------------------
def test_p17_10_adds_scope3_method_and_transaction_provider_narrowly() -> None:
    """Both columns are ADDITIVE and NULLABLE on both tables (no default)."""
    code = _code(P17_10)
    for table in ("public.calculation_snapshots", "public.emissions_logs"):
        assert f"ALTER TABLE {table}" in code
    assert code.count("ADD COLUMN IF NOT EXISTS scope3_method        text,") == 2
    assert code.count("ADD COLUMN IF NOT EXISTS transaction_provider text;") == 2
    # Nullable with no DEFAULT: history keeps its exact meaning.
    assert "NOT NULL" not in code.replace(
        "scope3_method IS NULL OR", ""
    ).replace("transaction_provider IS NULL", "")


def test_p17_10_data_quality_vocabulary_is_a_strict_superset() -> None:
    """The widened CHECK adds the product classifications and removes none.

    Asserting the superset (rather than an exact list) is what proves the change
    is non-destructive: every value P17-A allowed is still allowed, so no stored
    row can be invalidated by re-running the chain.
    """
    code = _text(P17_10)
    match = re.search(
        r"ADD CONSTRAINT calc_snapshots_data_quality_check\s+CHECK \(([^)]*)\)",
        code,
        re.S,
    )
    assert match, "widened data_quality CHECK missing"
    allowed = set(re.findall(r"'([a-z_]+)'", match.group(1)))
    assert {
        "primary_measured",
        "primary_supplier",
        "secondary_estimated",
        "spend_based_estimated",
        "modelled",
    } <= allowed, "a P17-A value was dropped — that would invalidate stored rows"
    assert {
        "activity_based",
        "estimated",
        "manual",
        "unresolved",
    } <= allowed, "a P17-PRODUCT-01 §29/§30 classification is missing"
    assert len(allowed) == 9, allowed


def test_p17_10_scope3_method_vocabulary_matches_the_domain_contract() -> None:
    """The DDL vocabulary and the domain vocabulary cannot drift apart."""
    from domain.scope3_contracts import SCOPE3_METHODS

    code = _text(P17_10)
    match = re.search(
        r"ADD CONSTRAINT calc_snapshots_scope3_method_check\s+CHECK "
        r"\(scope3_method IS NULL OR scope3_method IN\s+\(([^;]*)\)\);",
        code,
        re.S,
    )
    assert match, "scope3_method vocabulary CHECK missing"
    assert set(re.findall(r"'([a-z_]+)'", match.group(1))) == set(SCOPE3_METHODS)


def test_p17_10_scope3_method_is_scope_guarded_and_not_valid() -> None:
    code = _text(P17_10)
    assert "CHECK (scope3_method IS NULL OR scope = 'Scope 3') NOT VALID" in code
    assert code.count("CHECK (scope3_method IS NULL OR scope = 'Scope 3') NOT VALID") == 2
    # A blank provider is not a name: the shape guard rejects it.
    assert "length(btrim(transaction_provider)) BETWEEN 1 AND 200" in code


# ---------------------------------------------------------------------------
# Mandatory-for-new-writes rules must be NOT VALID (history exempt)
# ---------------------------------------------------------------------------
def test_scope_requirements_are_not_valid_so_history_is_exempt() -> None:
    code = _text(P17_A)
    for constraint in (
        "calc_snapshots_scope2_method_required",
        "calc_snapshots_scope3_category_required",
        "emissions_logs_scope2_method_required",
        "emissions_logs_scope3_category_required",
    ):
        assert constraint in code, constraint
        assert f"ADD CONSTRAINT {constraint}" in code
    # Every one of them must be declared NOT VALID.
    assert code.count("NOT VALID") >= 8


def test_cross_column_boundary_coherence_is_enforced_for_new_writes() -> None:
    code = _text(P17_A)
    assert "calc_snapshots_transport_boundary_scope_check" in code
    assert "calc_snapshots_waste_origin_scope_check" in code
    assert "calc_snapshots_energy_type_scope_check" in code


# ---------------------------------------------------------------------------
# DC-02 uniqueness / factor governance / consultant linkage
# ---------------------------------------------------------------------------
def test_dc02_partial_unique_index_prevents_a_second_category_3_derivation() -> None:
    code = _text(P17_A)
    assert "uq_calc_snapshots_cat3_source" in code
    assert "WHERE scope3_category = 3 AND source_snapshot_id IS NOT NULL" in code


def test_factor_governance_columns_are_declared_without_adding_factor_rows() -> None:
    code = _text(P17_A)
    for column in ("scope2_method", "scope3_category_hint", "factor_type", "gas_coverage"):
        assert re.search(rf"ADD COLUMN IF NOT EXISTS {column}\b", code), column
    assert "INSERT INTO public.emission_factors" not in code
    assert "UPDATE public.emission_factors" not in code


def test_category_hint_is_documented_as_a_non_authoritative_proposal() -> None:
    code = _text(P17_A)
    assert "PROPOSAL only, never authoritative" in code


def test_consultant_profiles_gains_the_organization_linkage() -> None:
    """ARCH-06 HIGH-01: the documented gap, closed additively."""
    code = _text(P17_A)
    assert re.search(
        r"ALTER TABLE public\.consultant_profiles\s+ADD COLUMN IF NOT EXISTS organization_id uuid",
        code,
    )
    assert "consultant_profiles_organization_id_fkey" in code
    assert "REFERENCES public.organizations(id) ON DELETE SET NULL" in code


def test_organization_identity_and_consolidation_approach_are_declared() -> None:
    code = _text(P17_A)
    assert "consolidation_approach" in code
    assert "organization_type" in code
    assert "OPERATIONAL_CONTROL', 'FINANCIAL_CONTROL', 'EQUITY_SHARE" in code.replace("\n", " ")
    assert "'CUSTOMER', 'CONSULTANT', 'PROCESSING_ENTITY', 'CARBONTALLY_INTERNAL'" in code.replace("\n", " ")


# ---------------------------------------------------------------------------
# Acting-for columns on every ARCH-04 §10.3 path
# ---------------------------------------------------------------------------
_ACTING_FOR_PATHS = (
    "calculation_snapshots",
    "emissions_logs",
    "evidence_line_items",
    "audit_trail",
    "customer_documents",
    "suppliers",
    "review_audit_trail",
    "review_assignment_history",
    "report_versions",
)


def test_every_acting_for_path_carries_the_column() -> None:
    """ARCH-04 §10.3: every path marked '(A) additive implementation required'."""
    code = _text(P17_A)
    for table in _ACTING_FOR_PATHS:
        # The window is generous because the acting-for block sits well after the
        # dimension constraints for the two accounting tables.
        assert re.search(
            rf"ALTER TABLE public\.{table}\b[\s\S]{{0,9000}}?\bacting_for_organization_id\b",
            code,
        ), table


def test_audit_trail_is_documented_as_the_authoritative_acting_for_carrier() -> None:
    assert "authoritative acting-for carrier" in _text(P17_A)


def test_derivation_from_an_actor_column_is_documented_as_not_audit_safe() -> None:
    """Read-time derivation is rejected in the architecture and must stay so."""
    assert "not audit-safe" in _text(P17_A)


def test_ownership_is_never_repointed_at_acting_for() -> None:
    """Acting-for is context: no migration may move ownership onto it."""
    code = _all_p17()
    assert "organization_id = acting_for_organization_id" not in code
    assert "SET organization_id" not in code


# ---------------------------------------------------------------------------
# New tables, RLS posture and functions
# ---------------------------------------------------------------------------
def _assert_rls_posture(code: str, table: str) -> None:
    assert f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY" in code, table
    assert f"REVOKE ALL ON TABLE public.{table} FROM anon" in code, table
    assert f"GRANT ALL ON TABLE public.{table} TO service_role" in code, table
    assert (
        f"REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.{table} "
        f"FROM authenticated" in code
    ), table
    assert "public.is_org_member(organization_id)" in code, table


def test_contractual_instruments_carry_the_established_rls_posture() -> None:
    _assert_rls_posture(_text(P17_C), "contractual_instruments")


def test_instrument_allocations_carry_the_established_rls_posture() -> None:
    _assert_rls_posture(_text(P17_C), "instrument_allocations")


def test_estimation_records_carry_the_established_rls_posture() -> None:
    _assert_rls_posture(_text(P17_H), "estimation_records")


def test_scope3_categories_is_read_only_reference_data() -> None:
    code = _text(P17_D)
    assert "ALTER TABLE public.scope3_categories ENABLE ROW LEVEL SECURITY" in code
    assert "REVOKE ALL ON TABLE public.scope3_categories FROM anon" in code
    assert "GRANT SELECT ON TABLE public.scope3_categories TO authenticated" in code
    assert (
        "REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, MAINTAIN" in code
    )


def test_scope3_categories_seeds_exactly_fifteen_categories() -> None:
    code = _text(P17_D)
    # Column-aligned seed rows have variable spacing after the comma.
    seed = re.findall(r"^ \((\d+), +'", code, re.M)
    assert seed == [str(n) for n in range(1, 16)], seed
    assert "ON CONFLICT (category) DO NOTHING" in code


def test_scope3_reference_seed_does_not_imply_an_implemented_methodology() -> None:
    """A category row is reference data, not an implementation claim."""
    code = _code(P17_D)
    # No status column is created and no status value is inserted.
    assert "SUPPORTED" not in code
    assert "PARTIAL" not in code
    assert "DEFERRED" not in code
    assert "NOT_IMPLEMENTED" not in code
    assert "INSERT INTO public.scope3_categories (category, slug, name, is_downstream, description)" in code


# ---------------------------------------------------------------------------
# P17-C structural guarantees
# ---------------------------------------------------------------------------
def test_cross_tenant_instrument_claim_is_structurally_impossible() -> None:
    """DC-09: a composite FK, not merely a policy."""
    code = _text(P17_C)
    assert "instrument_allocations_instrument_org_fkey" in code
    assert "FOREIGN KEY (instrument_id, organization_id)" in code
    assert "REFERENCES public.contractual_instruments (id, organization_id)" in code
    assert (
        "CONSTRAINT contractual_instruments_id_org_unique UNIQUE (id, organization_id)"
        in code
    )


def test_instrument_identity_is_unique_per_tenant() -> None:
    assert (
        "UNIQUE (organization_id, instrument_type, identifier)" in _text(P17_C)
    )


def test_instrument_type_vocabulary_is_provider_neutral() -> None:
    code = _text(P17_C)
    for member in (
        "energy_attribute_certificate",
        "guarantee_of_origin",
        "supplier_specific_contract",
        "ppa",
        "rec",
        "green_tariff",
        "other",
    ):
        assert member in code, member


def test_retirement_status_lifecycle_is_declared() -> None:
    code = _text(P17_C)
    assert "retirement_status IN ('active', 'retired', 'cancelled')" in code


def test_over_allocation_is_stated_not_to_be_database_guaranteed() -> None:
    """The architecture requires this honesty rather than an implied guarantee."""
    code = _text(P17_C)
    assert "NOT guaranteed by a single-row CHECK" in code
    assert "p17_instrument_over_allocated" in code


def test_dc09_detector_is_read_only_and_pinned() -> None:
    code = _text(P17_C)
    assert "RETURNS boolean" in code
    assert "STABLE" in code
    assert "SECURITY DEFINER" in code
    assert "SET search_path = public" in code


# ---------------------------------------------------------------------------
# P17-H estimation + detectors
# ---------------------------------------------------------------------------
def test_estimation_records_refuse_an_unsubstantiated_record() -> None:
    code = _text(P17_H)
    assert "estimation_records_substantiated_check" in code
    assert "assumptions <> '{}'::jsonb OR inputs <> '{}'::jsonb" in code


def test_estimation_method_vocabulary_is_declared() -> None:
    code = _text(P17_H)
    for member in (
        "average_data",
        "proxy_data",
        "spend_based",
        "extrapolated",
        "supplier_specific",
        "modelled",
        "industry_average",
        "other",
    ):
        assert member in code, member


def test_one_estimation_record_per_snapshot() -> None:
    assert "uq_estimation_records_snapshot" in _text(P17_H)


def test_all_four_p17_detectors_are_declared_and_read_only() -> None:
    code = _text(P17_H)
    for function in (
        "p17_dc04_unclassified_transport",
        "p17_dc05_unclassified_waste",
        "p17_dc07_consolidation_missing",
        "p17_unsubstantiated_estimates",
    ):
        assert function in code, function
    # Read-only helpers: STABLE, SECURITY DEFINER, pinned search_path.
    assert code.count("RETURNS TABLE(snapshot_id uuid)") == 4
    assert code.count("STABLE") == 4
    assert code.count("SECURITY DEFINER") == 4
    assert code.count("SET search_path = public") == 4


def test_detectors_contain_no_write_statement() -> None:
    """A detector that mutates data would not be a detector."""
    code = _text(P17_H)
    body = code.split("2. Double-counting / boundary detectors")[1]
    for forbidden in ("INSERT INTO", "UPDATE public", "DELETE FROM"):
        assert forbidden not in body, forbidden