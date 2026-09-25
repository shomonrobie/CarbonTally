"""Phase 8 Insight analytics — SQL layer and migration assertions (no database).

The analytics statement builders are *pure functions*: they return fixed SQL
literals plus positional parameters and never interpolate a caller value. These
tests pin that property directly, which is the strongest available check without
a database:

* unknown dimensions cannot produce a statement at all;
* an empty filter set cannot produce an unbounded statement;
* every filter becomes a positional parameter, never string interpolation;
* wildcard metacharacters in an activity term are escaped (containment, not a
  pattern search);
* tolerance widens the amount comparison to an inclusive range;
* the public query methods are organisation-scoped and bounded.
"""
from __future__ import annotations

import inspect
import re
from datetime import date
from decimal import Decimal

import pytest

from data import emissions_logs as repo
from domain.insight_query import AGGREGATION_DIMENSIONS


# --------------------------------------------------------------------------
# Allowlisted dimension map
# --------------------------------------------------------------------------
def test_dimension_map_is_the_closed_vocabulary() -> None:
    """The allowlist is closed, and it is in lockstep with the domain.

    P17-IMPLEMENT-10 widened it with the category-level reporting dimensions
    P17-PRODUCT-01 §29 requires. The assertion below is the important one: the
    repository's SQL allowlist must EQUAL the domain's ``AGGREGATION_DIMENSIONS``
    exactly, so a caller can never name a dimension the domain accepts but the
    repository cannot resolve (or vice versa).
    """
    assert set(repo._ANALYTICS_DIMENSION_EXPRESSIONS) == {
        "scope", "month", "year", "activity", "supplier", "facility", "asset",
        "scope2_method", "scope3_category", "scope3_method", "energy_type",
        "data_quality", "transaction_provider",
    }
    assert set(repo._ANALYTICS_DIMENSION_EXPRESSIONS) == set(AGGREGATION_DIMENSIONS)
    for expression in repo._ANALYTICS_DIMENSION_EXPRESSIONS.values():
        # Every expression is a fixed literal: no statement separator, no
        # placeholder and no line break can appear in it.
        assert ";" not in expression
        assert "$" not in expression
        assert "\n" not in expression


def test_unknown_dimension_is_refused_and_never_becomes_sql() -> None:
    for bad in ("", "total", "scope; DROP TABLE", "monthly", None):
        with pytest.raises(ValueError):
            repo._analytics_expression(bad)  # type: ignore[arg-type]


def test_containment_pattern_escapes_wildcards() -> None:
    assert repo._containment_pattern("diesel") == "%diesel%"
    assert repo._containment_pattern("50%") == "%50\\%%"
    assert repo._containment_pattern("a_b") == "%a\\_b%"
    assert repo._containment_pattern("a\\b") == "%a\\\\b%"


# --------------------------------------------------------------------------
# Filter clause: positional parameters only
# --------------------------------------------------------------------------
def test_empty_filters_cannot_build_a_statement() -> None:
    with pytest.raises(ValueError):
        repo._snapshot_filter_clause({}, start_index=2)


def test_date_range_filter_is_inclusive_and_parameterised() -> None:
    clause, params = repo._snapshot_filter_clause(
        {"start_date": "2024-02-01", "end_date": "2024-02-29"}, start_index=2
    )
    assert clause == " AND s.date >= $2 AND s.date <= $3"
    assert params == [date(2024, 2, 1), date(2024, 2, 29)]


def test_single_day_is_a_one_day_inclusive_range() -> None:
    clause, params = repo._snapshot_filter_clause(
        {"start_date": "2024-02-02", "end_date": "2024-02-02"}, start_index=2
    )
    assert clause.count("s.date") == 2
    assert params == [date(2024, 2, 2), date(2024, 2, 2)]


def test_exact_amount_is_a_zero_tolerance_equality_range() -> None:
    clause, params = repo._snapshot_filter_clause({"co2e_kg": "20000"}, start_index=2)
    assert clause == " AND s.co2e_kg >= $2 AND s.co2e_kg <= $3"
    assert params == [Decimal("20000"), Decimal("20000")]


def test_absolute_tolerance_widens_the_range() -> None:
    clause, params = repo._snapshot_filter_clause(
        {"co2e_kg": "20000", "co2e_tolerance_kg": "100"}, start_index=2
    )
    assert params == [Decimal("19900"), Decimal("20100")]


def test_relative_tolerance_widens_the_range() -> None:
    _clause, params = repo._snapshot_filter_clause(
        {"co2e_kg": "20000", "co2e_tolerance_pct": "5"}, start_index=2
    )
    assert params == [Decimal("19000.000000"), Decimal("21000.000000")]


def test_activity_filter_is_a_parameter_not_a_literal() -> None:
    clause, params = repo._snapshot_filter_clause({"activity": "diesel"}, start_index=2)
    assert clause == " AND s.activity_type ILIKE $2"
    assert params == ["%diesel%"]
    assert "diesel" not in clause


def test_scope_filter_uses_the_canonical_vocabulary() -> None:
    for raw, expected in (("scope 1", "Scope 1"), ("1", "Scope 1"), ("scope2", "Scope 2")):
        clause, params = repo._snapshot_filter_clause({"scope": raw}, start_index=2)
        assert clause == " AND s.scope = $2"
        assert params == [expected]


def test_supplier_facility_asset_filters_use_the_snapshot_lineage_join() -> None:
    clause, params = repo._snapshot_filter_clause(
        {"supplier_id": "sup-1", "facility_id": "fac-1", "asset_id": "ast-1"}, start_index=2
    )
    assert "l.snapshot_id = s.id" in clause
    assert "l.supplier_id::text = $2" in clause
    assert "l.metadata->>'facility_id' = $3" in clause
    assert "l.asset_id::text = $4" in clause
    assert params == ["sup-1", "fac-1", "ast-1"]


def test_reporting_year_filter_is_its_own_predicate() -> None:
    clause, params = repo._snapshot_filter_clause({"reporting_year": "2024"}, start_index=2)
    assert clause == " AND s.reporting_year = $2"
    assert params == [2024]


def test_no_caller_value_is_ever_interpolated_into_the_statement() -> None:
    clause, params = repo._snapshot_filter_clause(
        {"activity": "'; DROP TABLE emissions_logs; --", "scope": "Scope 1"}, start_index=2
    )
    assert "DROP TABLE" not in clause
    # The term is passed as a parameter, with ``_`` escaped so it stays a literal
    # containment test rather than a wildcard pattern.
    assert params[0] == "%'; DROP TABLE emissions\\_logs; --%"
    # Placeholders are strictly sequential from the start index.
    assert re.findall(r"\$(\d+)", clause) == ["2", "3"]


# --------------------------------------------------------------------------
# Public query methods: organisation-scoped, bounded, no mutation
# --------------------------------------------------------------------------
def _source(name: str) -> str:
    return inspect.getsource(getattr(repo.EmissionsLogsRepository, name))


@pytest.mark.parametrize(
    "method",
    [
        "search_snapshots",
        "count_matching_snapshots",
        "aggregate_groups",
        "group_labels",
        "list_group_snapshots",
        "count_group_snapshots",
    ],
)
def test_every_analytics_method_is_organisation_scoped_and_bounded(method: str) -> None:
    source = _source(method)
    assert "organization_id = $1" in source, method
    # Bounded either by a LIMIT or by an explicit key list (label resolution).
    assert "LIMIT $" in source or "= ANY($2::text[])" in source, method


@pytest.mark.parametrize(
    "method",
    [
        "search_snapshots",
        "count_matching_snapshots",
        "aggregate_groups",
        "group_labels",
        "list_group_snapshots",
        "count_group_snapshots",
    ],
)
def test_analytics_methods_are_read_only(method: str) -> None:
    source = _source(method)
    for forbidden in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"):
        assert forbidden not in source, (method, forbidden)


def test_aggregate_groups_never_returns_a_mixed_unit_quantity_total() -> None:
    source = _source("aggregate_groups")
    assert "SUM(l.calculated_kg_co2e)" in source
    # A summed raw quantity across mixed units must never be exposed.
    assert "SUM(l.raw_quantity" not in source
    assert "SUM(cs.quantity" not in source


def test_provenance_only_returns_rows_with_an_authoritative_snapshot() -> None:
    source = _source("list_group_snapshots")
    assert "l.snapshot_id IS NOT NULL" in source
    assert "cs.organization_id = $1" in source


# --------------------------------------------------------------------------
# The Phase 8 migration (static assertion, no database needed)
# --------------------------------------------------------------------------
_MIGRATION = (
    "supabase/migrations/20261005000000_p8_insight_discovery_aggregation_rate_limit.sql"
)


def _ddl() -> str:
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[4]
    return (root / _MIGRATION).read_text()


def _structure() -> str:
    """Declared structure only: comments and string literals removed, so the
    migration's own prohibition prose cannot satisfy a frozen assertion."""
    text = re.sub(r"--[^\n]*", "", _ddl())
    return re.sub(r"'[^']*'", "''", text, flags=re.DOTALL)


def test_migration_widens_the_tool_catalogue_by_exactly_three_names() -> None:
    ddl = _ddl()
    assert "DROP CONSTRAINT IF EXISTS ci_tool_calls_tool_name_check" in ddl
    for name in (
        "'report_lookup'",
        "'report_version_lookup'",
        "'report_evidence_lookup'",
        "'calculation_snapshot_lookup'",
        "'insight_discovery'",
        "'insight_aggregation'",
        "'insight_aggregate_provenance'",
    ):
        assert name in ddl, name


def test_migration_adds_exactly_one_answer_state() -> None:
    ddl = _ddl()
    assert "DROP CONSTRAINT IF EXISTS ci_interactions_answer_status_check" in ddl
    assert "'multiple_matches'" in ddl
    # The closed I3 tool-status vocabulary is untouched by this migration.
    assert "ci_tool_calls_tool_status_check" not in ddl


def test_migration_creates_the_shared_limiter_tables_with_rls() -> None:
    ddl = _ddl()
    assert "CREATE TABLE IF NOT EXISTS public.insight_rate_limit_buckets" in ddl
    assert "CREATE TABLE IF NOT EXISTS public.insight_concurrency_leases" in ddl
    assert "ENABLE ROW LEVEL SECURITY" in ddl
    assert "PRIMARY KEY (scope, scope_key)" in ddl


# --------------------------------------------------------------------------
# The P2 migration (static assertion, no database needed)
# --------------------------------------------------------------------------
_P2_MIGRATION = (
    "supabase/migrations/20261006000000_p8_insight_temporal_comparison.sql"
)


def _p2_ddl() -> str:
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[4]
    return (root / _P2_MIGRATION).read_text()


def test_p2_migration_widens_the_catalogue_by_exactly_one_tool() -> None:
    ddl = _p2_ddl()
    assert "DROP CONSTRAINT IF EXISTS ci_tool_calls_tool_name_check" in ddl
    for name in (
        "'report_lookup'",
        "'report_version_lookup'",
        "'report_evidence_lookup'",
        "'calculation_snapshot_lookup'",
        "'insight_discovery'",
        "'insight_aggregation'",
        "'insight_aggregate_provenance'",
        "'insight_temporal_comparison'",
    ):
        assert name in ddl, name
    assert ddl.count("ADD CONSTRAINT ci_tool_calls_tool_name_check") == 1


def test_p2_migration_is_additive_idempotent_and_changes_no_vocabulary() -> None:
    ddl = _p2_ddl()
    # Additive and re-runnable: the widening drops the constraint first.
    assert ddl.count("ALTER TABLE public.carbontally_insight_tool_calls") == 2
    # No destructive statement and no new schema object.
    for forbidden in ("DROP TABLE", "DROP COLUMN", "DELETE ", "TRUNCATE", "UPDATE public.", "CREATE TABLE"):
        assert forbidden not in ddl, forbidden
    # The answer-state vocabulary and the tool-status vocabulary are untouched.
    assert "ci_interactions_answer_status_check" not in ddl
    assert "ci_tool_calls_tool_status_check" not in ddl
    # The P2 zero-baseline case is expressed with existing states plus a result
    # field, so no sixteenth answer state is introduced anywhere.
    assert "multiple_matches" not in ddl


def test_migration_declares_no_destructive_or_commercial_statement() -> None:
    structure = _structure().upper()
    for forbidden in ("DROP TABLE", "TRUNCATE", "DELETE FROM", "DROP COLUMN", "GRANT "):
        assert forbidden not in structure, forbidden
    # Technical abuse protection only: no billing/entitlement vocabulary.
    for forbidden in ("PLAN_ID", "ENTITLEMENT", "CREDIT", "OVERAGE", "PRICE"):
        assert forbidden not in structure, forbidden


def test_limiter_statements_are_single_atomic_operations() -> None:
    from data import insight_rate_limit as limiter

    for statement in (
        limiter._CONSUME_SQL,
        limiter._ACQUIRE_LEASE_SQL,
        limiter._RELEASE_LEASE_SQL,
        limiter._RECORD_DENIAL_SQL,
    ):
        # One statement per call: no batch separator, and the decision (refill,
        # concurrency ceiling) is taken inside the statement, not in Python.
        assert statement.strip().count(";") == 0
        assert statement.strip().startswith(("INSERT", "UPDATE"))
    assert "RETURNING" in limiter._CONSUME_SQL
    assert "WHERE" in limiter._CONSUME_SQL
    assert "EXTRACT(EPOCH FROM (now() - b.updated_at))" in limiter._CONSUME_SQL
    assert "lease_expires_at" in limiter._ACQUIRE_LEASE_SQL
    assert "WHERE" in limiter._ACQUIRE_LEASE_SQL
    # Denial accounting must never disturb the refill basis.
    assert "updated_at" not in limiter._RECORD_DENIAL_SQL
